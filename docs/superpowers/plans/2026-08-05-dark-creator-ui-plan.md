# 章鱼带货全站深色创作者工具 UI 改版 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task with review checkpoints.

**Goal:** 在不改变页面内容和现有功能的前提下，将章鱼带货官网统一改为深色创作者工具风格。

**Architecture:** 继续使用静态 HTML、单个全站 CSS 文件和单个全站 JS 文件。视觉升级集中在 CSS 变量和组件样式，交互升级集中在已有 `site.js`，不引入框架、构建工具或第三方运行时。

**Tech Stack:** 原生 HTML、CSS、JavaScript；现有 WebP/PNG 截图资源；PowerShell 静态检查；浏览器桌面和手机视口检查。

## Global Constraints

- 全站统一深色：页面底色 `#0d1117`，面板使用深蓝灰，品牌橙是唯一强调色。
- 保留现有版本更新、SEO 文案、下载链接、微信联系方式、算法包链接、图片资源和页面 URL。
- 不使用紫蓝渐变、光球或装饰性背景图，不引入第三方依赖。
- 保持图片 lightbox、更新数据加载和下载点击记录的现有行为。
- 桌面端和移动端不得出现横向溢出；键盘 focus 和 `prefers-reduced-motion` 必须可用。
- 之前未提交的版本更新文件属于既有改动，UI 提交只能包含本计划涉及的文件。

---

### Task 1: 建立深色视觉系统和全站组件样式

**Files:**
- Modify: `assets/site.css`
- Test: `assets/site.css` 静态变量、媒体查询和选择器检查

**Interfaces:**
- Consumes: 现有页面使用的 `.site-header`、`.nav`、`.hero`、`.card`、`.feature-card`、`.download-panel`、`.faq-item`、`.article-*`、`.image-lightbox` 类。
- Produces: 所有现有页面共享的深色主题、交互状态和响应式规则。

- [ ] **Step 1: Replace the color and typography tokens**

  在 `:root` 中将浅色背景变量替换为深煤灰页面底色、深蓝灰面板、暖白主文字、灰蓝辅助文字和低对比边框；保留品牌橙作为唯一强调色。加入 500/600 字重、`text-wrap: balance`/`pretty` 和 tabular number 设置。

- [ ] **Step 2: Restyle the page shell**

  更新 body、header、navigation、section、band、footer 和 container 的颜色、边框、间距和阴影。导航保持 sticky，但改为深色半透明面板；全局链接、按钮、`.btn.primary` 和 `.btn.ghost` 使用统一橙色强调和深色对比。

- [ ] **Step 3: Restyle hero, updates, cards, tables, downloads and reading surfaces**

  让首页首屏、版本更新、功能卡片、截图卡片、流程块、下载面板、FAQ、时间轴、文章目录和正文使用统一深色面板。用 CSS Grid 调整首屏和更新区的留白、层次和不对称比例；给表格加深色表头、行 hover；保留 8px 左右圆角。

- [ ] **Step 4: Add interaction and responsive states in CSS**

  为按钮、导航链接、截图、文章链接和表格行添加 hover/active/focus-visible 状态；补充 `prefers-reduced-motion: reduce`。在 980px 和 640px 断点下检查首屏、导航、更新记录、表格、按钮和页脚的单列布局，并确保 `overflow-x` 不产生横向滚动。

- [ ] **Step 5: Run CSS sanity checks**

  运行：`Select-String -Path assets/site.css -Pattern '#ffffff|#f6f7f9|#000000|gradient|prefers-reduced-motion|focus-visible'`

  预期：浅色旧主题只保留在必要的图片/文本对比场景；存在 focus 和减少动画规则；没有紫蓝渐变或无关新增依赖。

### Task 2: Improve navigation and accessibility behavior

**Files:**
- Modify: `assets/site.js`
- Test: `assets/site.js` syntax check and static behavior review

**Interfaces:**
- Consumes: 当前页面 URL、现有 `[data-download]`、`[data-updates]`、`.feature-card img` 元素。
- Produces: 当前导航标记、保留的更新加载、下载记录和图片 lightbox 行为。

- [ ] **Step 1: Add current navigation state**

  根据 `window.location.pathname` 匹配 `index.html`、`features.html`、`tutorial.html`、`articles.html`、`download.html`、`faq.html` 和 `changelog.html`，为匹配的导航链接添加 `aria-current="page"` 和 `.is-current` 类；首页路径 `/` 与 `index.html` 视为同一页。

- [ ] **Step 2: Preserve and harden existing interactions**

  保留更新数据加载、下载点击记录和图片 lightbox。为 lightbox 增加空图片源保护、关闭时恢复焦点、点击遮罩关闭和 `prefers-reduced-motion` 兼容，不改变现有图片原图路径映射。

- [ ] **Step 3: Run JavaScript syntax checks**

  运行：`node --check assets/site.js`

  预期：命令退出码为 0，文件不引入第三方模块，不出现语法错误。

### Task 3: Verify the complete static site

**Files:**
- Test: `index.html`, `features.html`, `download.html`, `faq.html`, `changelog.html`, `tutorial.html`, `articles.html`, `assets/site.css`, `assets/site.js`

**Interfaces:**
- Consumes: Task 1 的视觉系统和 Task 2 的导航/交互状态。
- Produces: 可在桌面和移动视口访问的统一深色官网。

- [ ] **Step 1: Run content and structure checks**

  检查所有 HTML 是否仍引用 `assets/site.css` 和 `assets/site.js`；解析首页、下载页、FAQ 的 JSON-LD；检查现有版本内容、下载链接、文章链接、ICP备案和图片 alt 文本仍存在。

- [ ] **Step 2: Run a local static server**

  在仓库目录启动静态服务器，使用浏览器访问首页、功能页、下载页、FAQ、更新日志、教程和文章页；确认 CSS、JS、图片和 `updates.json` 返回成功。

- [ ] **Step 3: Capture desktop and mobile checks**

  使用浏览器检查 1440px 桌面视口和 390px 手机视口，确认导航、首屏、更新区、功能表、截图放大、下载按钮、FAQ 和页脚没有溢出或文字遮挡。

- [ ] **Step 4: Review the final diff**

  运行：`git diff --check` 和 `git diff --stat -- assets/site.css assets/site.js`

  预期：只有计划范围内的 CSS/JS 被改动，版本更新文件保持原有工作区状态。
