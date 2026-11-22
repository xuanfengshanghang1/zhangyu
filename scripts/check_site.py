#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""章鱼带货官网站点一致性校验（纯标准库，无第三方依赖）。

用法:
    python scripts/check_site.py              # 全部检查（含线上 HTTP 探测）
    python scripts/check_site.py --offline    # 跳过 HTTP，只做仓库内一致性
    python scripts/check_site.py --timeout 20 # 单个 URL 超时秒数，默认 12

检查项:
    1) 版本号一致：首页 JSON-LD / download JSON-LD / download 可见文案 / changelog 最新一条 / llms.txt
    2) sitemap 里的 URL：全部返回 200，且都被至少一个「其它页面」内链引到
    3) 每页 JSON-LD 可解析（JSON 语法 + 必须有 @context/@type）
    4) llms.txt 里列出的页面 URL 都真实存在（站内看文件，外链看 HTTP）
    5) 每页 canonical 与 sitemap 一致（双向：页面 canonical 在 sitemap 里；sitemap 的 HTML 项都有人认领）

退出码: 0 = 全绿；1 = 存在不一致项。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

SITE = "https://www.zhangyudaihuo.cn"
SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
LD_RE = re.compile(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', re.S | re.I)
CANON_RE = re.compile(r'<link[^>]+rel="canonical"[^>]+href="([^"]+)"', re.I)
NOINDEX_RE = re.compile(r'<meta[^>]+name="robots"[^>]+content="[^"]*noindex', re.I)
VER = r"\d+\.\d+\.\d+"
HREF_RE = re.compile(r'<a\b[^>]*href="([^"]*)"', re.I)

ISSUES: list[str] = []
UA = {"User-Agent": "zhangyu-site-check/1.0 (+https://www.zhangyudaihuo.cn/)"}


def url_of(rel_path: str) -> str:
    """仓库相对路径 -> 站点 URL；index.html 视为根。"""
    if rel_path in ("index.html", "./index.html"):
        return SITE + "/"
    return f"{SITE}/{rel_path.lstrip('./')}"


def norm(u: str) -> str:
    u = urllib.parse.urldefrag(u)[0]
    if u.endswith("/index.html"):
        u = u[: -len("index.html")]
    return u.rstrip("/") if u.rstrip("/") else u


def line_of(text: str, needle: str) -> int:
    i = text.find(needle)
    return 0 if i < 0 else text.count("\n", 0, i) + 1


class Fetcher:
    def __init__(self, timeout: float, offline: bool):
        self.timeout = timeout
        self.offline = offline
        self.cache: dict[str, tuple[int, str]] = {}

    def status(self, url: str) -> tuple[int, str]:
        if self.offline:
            return (0, "skipped(--offline)")
        if url in self.cache:
            return self.cache[url]
        try:
            req = urllib.request.Request(url, headers=UA, method="GET")
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = (resp.status, "")
        except urllib.error.HTTPError as exc:
            result = (exc.code, exc.reason or "")
        except Exception as exc:  # noqa: BLE001 - 网络错误统一按失败处理
            result = (-1, f"{type(exc).__name__}: {exc}")
        self.cache[url] = result
        return result


def load_pages(repo: Path) -> dict[str, str]:
    pages = {}
    for p in sorted(repo.glob("**/*.html")):
        if ".git" in p.parts:
            continue
        pages[p.relative_to(repo).as_posix()] = p.read_text(encoding="utf-8")
    return pages


# --------------------------------------------------------------------- check 1
def check_version(repo: Path, pages: dict[str, str]) -> None:
    print("[1/5] 版本号一致性（5 处）")
    found: list[tuple[str, int, str, str]] = []  # (来源, 行号, 值, 说明)

    def from_jsonld(path: str) -> None:
        for block in LD_RE.findall(pages[path]):
            try:
                obj = json.loads(block)
            except ValueError:
                continue
            if obj.get("@type") == "SoftwareApplication" and "softwareVersion" in obj:
                v = str(obj["softwareVersion"])
                found.append((path, line_of(pages[path], '"softwareVersion"'), v, "JSON-LD softwareVersion"))

    for page in ("index.html", "download.html"):
        from_jsonld(page)

    m = re.search(r"软件版本：\s*v?(" + VER + ")", pages["download.html"])
    if m:
        found.append(("download.html", line_of(pages["download.html"], m.group(0)), m.group(1), "页面可见文案"))
    m = re.search(r"Windows x64 v(" + VER + ")", pages["changelog.html"])
    if m:
        found.append(("changelog.html", line_of(pages["changelog.html"], m.group(0)), m.group(1), "最新一条版本"))
    llms = (repo / "llms.txt").read_text(encoding="utf-8")
    for label, pattern in (("当前资料安装包", r"当前资料安装包：Windows x64 v(" + VER + ")"),
                           ("当前资料版本", r"当前资料版本：Windows x64 v(" + VER + ")")):
        m = re.search(pattern, llms)
        if m:
            found.append(("llms.txt", line_of(llms, m.group(0)), m.group(1), label))
        else:
            ISSUES.append(f"[版本] llms.txt 找不到「{label}」的版本号")

    if len({v for _, _, v, _ in found}) > 1:
        ISSUES.append("[版本] 版本号不一致：" + ", ".join(f"{s}:{ln}={v}" for s, ln, v, _ in found))
    for src, ln, val, note in found:
        print(f"  {src}:{ln:<4} {val:<8} {note}")
    print(f"  ==> {'一致' if len({v for _, _, v, _ in found}) <= 1 else '不一致'}\n")


# --------------------------------------------------------------------- check 2
def check_sitemap(repo: Path, pages: dict[str, str], fetcher: Fetcher) -> None:
    print("[2/5] sitemap URL：可访问性 + 内链覆盖")
    root = ET.parse(repo / "sitemap.xml").getroot()
    locs = [e.text.strip() for e in root.iter(SITEMAP_NS + "loc") if e.text]
    print(f"  sitemap loc 数 = {len(locs)}")

    inbound: dict[str, set[str]] = {}
    for page, text in pages.items():
        base = url_of(page)
        for href in HREF_RE.findall(text):
            href = href.strip()
            if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue
            target = norm(urllib.parse.urljoin(base, href))
            if target.startswith(norm(SITE)):
                inbound.setdefault(target, set()).add(page)

    bad_status, no_inlink = [], []
    for loc in locs:
        code, err = fetcher.status(loc)
        if fetcher.offline:
            pass
        elif code != 200:
            bad_status.append(f"{loc} -> {code} {err}".strip())
        srcs = {p for p in inbound.get(norm(loc), set()) if url_of(p) != norm(loc)}
        if not srcs:
            no_inlink.append(loc)
    print(f"  HTTP: {'跳过(--offline)' if fetcher.offline else f'{len(locs) - len(bad_status)}/{len(locs)} 返回 200'}")
    print(f"  内链: {len(locs) - len(no_inlink)}/{len(locs)} 至少被一个其它页面引到")
    for b in bad_status:
        ISSUES.append(f"[sitemap] HTTP 非 200: {b}")
    for n in no_inlink:
        ISSUES.append(f"[sitemap] 无其它页面内链: {n}")
    print(f"  ==> {'通过' if not bad_status and not no_inlink else '有问题'}\n")


# --------------------------------------------------------------------- check 3
def check_jsonld(pages: dict[str, str]) -> None:
    print("[3/5] 每页 JSON-LD 可解析")
    total, bad = 0, 0
    for page, text in pages.items():
        blocks = LD_RE.findall(text)
        for i, block in enumerate(blocks, 1):
            total += 1
            try:
                obj = json.loads(block)
            except ValueError as exc:
                bad += 1
                ISSUES.append(f"[JSON-LD] {page} 第{i}块解析失败: {exc}")
                continue
            if "@context" not in obj or "@type" not in obj:
                bad += 1
                ISSUES.append(f"[JSON-LD] {page} 第{i}块缺 @context 或 @type")
    print(f"  页面数={len(pages)} JSON-LD 块={total} 失败={bad}")
    print(f"  ==> {'全部可解析' if bad == 0 else f'{bad} 处失败'}\n")


# --------------------------------------------------------------------- check 4
def check_llms(repo: Path, fetcher: Fetcher) -> None:
    print("[4/5] llms.txt 里列出的页面 URL 是否真实存在")
    text = (repo / "llms.txt").read_text(encoding="utf-8")
    urls: list[tuple[int, str]] = []
    for ln, line in enumerate(text.splitlines(), 1):
        for u in re.findall(r"https?://[^\s，。）)]+", line):
            urls.append((ln, u))
        rest = re.sub(r"https?://[^\s，。）)]+", " ", line)
        for u in re.findall(r"(?<![\w/])/([A-Za-z0-9._/-]+\.html)", rest):
            urls.append((ln, SITE + "/" + u))
    missing = 0
    for ln, u in urls:
        if u.startswith(SITE):
            rel = urllib.parse.urlparse(u).path.lstrip("/") or "index.html"
            ok = (repo / rel).is_file()
            how = "文件存在" if ok else "文件缺失"
        else:
            code, err = fetcher.status(u)
            ok = fetcher.offline or code == 200
            how = "跳过" if fetcher.offline else f"HTTP {code} {err}".strip()
        if not ok:
            missing += 1
            ISSUES.append(f"[llms] 第{ln}行 {u} -> {how}")
    print(f"  列出 URL 数 = {len(urls)}，缺失 = {missing}")
    print(f"  ==> {'全部存在' if missing == 0 else f'{missing} 个缺失'}\n")


# --------------------------------------------------------------------- check 5
def check_canonical(repo: Path, pages: dict[str, str]) -> None:
    print("[5/5] canonical 与 sitemap 一致")
    root = ET.parse(repo / "sitemap.xml").getroot()
    locs = {norm(e.text.strip()) for e in root.iter(SITEMAP_NS + "loc") if e.text}
    missing_canon, not_in_sitemap, claimed = [], [], set()
    for page, text in pages.items():
        own = norm(url_of(page))
        m = CANON_RE.search(text)
        if not m:
            if not NOINDEX_RE.search(text):
                missing_canon.append(page)
            continue
        canon = norm(m.group(1))
        if canon != own:
            ISSUES.append(f"[canonical] {page} 的 canonical 指向 {canon}，与自身地址 {own} 不一致")
        if canon not in locs:
            if not NOINDEX_RE.search(text):
                not_in_sitemap.append(f"{page} -> {canon}")
        claimed.add(canon)
    for n in missing_canon:
        ISSUES.append(f"[canonical] {n} 缺 canonical（且不是 noindex 页）")
    for n in not_in_sitemap:
        ISSUES.append(f"[canonical] canonical 不在 sitemap 里: {n}")
    html_locs = {u for u in locs if u.endswith(".html") or u == norm(SITE + "/")}
    orphan_locs = sorted(u for u in html_locs if u not in claimed)
    for o in orphan_locs:
        ISSUES.append(f"[canonical] sitemap 里有该 URL，但没有页面声明它为 canonical: {o}")
    print(f"  有 canonical 的页面 = {len(claimed)}，sitemap HTML 项 = {len(html_locs)}")
    print(f"  ==> {'一致' if not (missing_canon or not_in_sitemap or orphan_locs) else '有不一致'}\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="章鱼带货官网站点一致性校验")
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent), help="仓库根目录")
    ap.add_argument("--offline", action="store_true", help="跳过所有 HTTP 探测")
    ap.add_argument("--timeout", type=float, default=12.0, help="单个 URL 超时秒数")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    if not (repo / "sitemap.xml").is_file():
        print(f"找不到 {repo / 'sitemap.xml'}，--repo 指错了？")
        return 1
    pages = load_pages(repo)
    fetcher = Fetcher(args.timeout, args.offline)
    print(f"仓库: {repo}")
    print(f"页面: {len(pages)} 个 HTML | 模式: {'offline' if args.offline else 'online'}\n")

    check_version(repo, pages)
    check_sitemap(repo, pages, fetcher)
    check_jsonld(pages)
    check_llms(repo, fetcher)
    check_canonical(repo, pages)

    if ISSUES:
        print(f"==== 发现 {len(ISSUES)} 项不一致 ====")
        for i, issue in enumerate(ISSUES, 1):
            print(f"  {i:>2}. {issue}")
        return 1
    print("==== 全绿：5 项检查全部通过 ====")
    return 0


if __name__ == "__main__":
    sys.exit(main())
