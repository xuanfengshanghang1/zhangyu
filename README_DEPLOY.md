# 章鱼带货官网部署说明

这是一个低成本静态官网，可以直接部署到静态空间、对象存储、CDN、宝塔静态站、Cloudflare Pages、Netlify、Vercel 或 Nginx 静态目录。

## 上线前必须替换

1. 将 HTML、`sitemap.xml`、`robots.txt` 中的 `https://xuanfengshanghang1.github.io/zhangyu/` 替换为正式域名。
2. 确认下载链接是否继续使用：
   `https://sso.zhangyumofang.com/zydh_v1.3.10_x64.exe`
3. 确认微信联系方式是否仍为：`aff22g`。
4. 若软件版本更新，修改 `download.html`、`changelog.html`、`llms.txt` 和结构化数据中的版本号。

## 下载埋点方案

当前站点提供两个下载入口：

- `download/`：下载跳转页，适合统计访问来源。
- `https://sso.zhangyumofang.com/zydh_v1.3.10_x64.exe`：直接下载链接。

低成本统计方式：

- 查看服务器访问日志或 CDN 日志中的 `/download/` 访问量。
- 广告或公众号链接使用参数，例如 `/download/?from=wechat`、`/download/?from=ad`。
- 后续也可以在 `download/index.html` 中接入百度统计、Google Analytics、Umami 或 Plausible。

## 视频省流量建议

当前教程视频已放在：

`assets/video/tutorial-5-14.mp4`

页面使用 `preload="metadata"`，不会在打开页面时完整加载视频。正式上线如果担心带宽成本，可以把视频上传到对象存储、视频云或 B 站/腾讯视频，再替换 `tutorial.html` 里的视频地址。

## SEO / GEO 已包含

- 每个页面都有独立 title、description 和 canonical。
- 首页包含 SoftwareApplication 结构化数据。
- FAQ 页面包含 FAQPage 结构化数据。
- 站点包含 `robots.txt`、`sitemap.xml` 和 `llms.txt`。
- 核心内容以 HTML 文本呈现，不依赖图片或前端渲染。
- 功能页、FAQ、更新日志分别承接不同搜索词。

## 高频更新怎么发

首页已预留“实时更新”模块。快速发更新时优先修改：

`updates.json`

格式如下：

```json
[
  {
    "date": "2026-06-22",
    "title": "更新标题",
    "summary": "一句话说明更新内容。",
    "url": "changelog.html"
  }
]
```

上线后首页会自动读取 `updates.json` 的前 4 条。为了 SEO，重要更新建议同步写入：

- `index.html` 的实时更新兜底内容
- `changelog.html` 的长期更新记录
- `llms.txt` 的 AI 摘要
- `sitemap.xml` 的 lastmod 日期

## 建议后续新增内容

- 用户案例页：例如快手矩阵团队如何从选品到发布复盘。
- 教程文章页：每个功能模块单独一篇图文教程。
- 合规说明页：单独说明平台规则、隐私、安全和免责声明。
