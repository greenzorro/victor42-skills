# Agent Skills 门户 — 项目备忘录

## 1. 目的

记录 `projects/victor42-skills`（线上 https://skills.victor42.work/）的结构与维护约定，供本人与 Agent 后续改站时对齐。

**定位：** 小玩意创造营地下 Agent 类创造物的交付端点。`victor42.work` 首页仅放一张合集卡片指向本站。本仓同时是 [skills CLI](https://github.com/vercel-labs/skills) 可安装的 skill 源。

**约定：** 改功能或数据结构后，同步更新本文，使其持续描述当前实现。

## 2. 项目概述

静态门户 + 标准 skill 源：JSON 驱动目录页；各 skill 落地页由脚本生成；可安装内容在 `skills/<slug>/`。支持中英切换与深/浅色主题。无构建步骤，适合 Cloudflare Pages。

### 2.1 技术栈

- **HTML5**：目录页壳、SEO meta（canonical / hreflang / OG / Twitter Card）、JSON-LD；落地页为预渲染静态 HTML
- **CSS3**：响应式双列卡片、CSS 变量主题、`:focus-visible`
- **JavaScript (ES6)**：目录页 `fetch` 加载数据并渲染；落地页负责复制安装指令、主题/语言；GA 路由追踪
- **JSON**：`data.json` 为门户内容源（文案双语；数组顺序 = 展示顺序）
- **LocalStorage**：主题 `theme`、语言 `language`
- **Python**：`generate_site.py` 生成 `{slug}/index.html` 与 `sitemap.xml`；`generate_og_images.py` 生成 OG 分享图

### 2.2 文件结构

```
victor42-skills/
├── skills/                 # skills CLI 源（SKILL.md + 附属文件）
│   ├── handoff/
│   ├── file-image-toolkit/
│   ├── poem-six-lens/
│   └── cognition-shaper/
├── index.html              # 目录页壳、SEO、主题 FOUC、GA
├── data.json               # 标题 / 简介 / skill 列表（中英）
├── {slug}/index.html       # 落地页（脚本生成，勿手改）
├── assets/
│   ├── shared.js           # 主题、语言、页脚、复制
│   ├── main.js             # 目录页加载与渲染
│   ├── skill.js            # 落地页复制安装指令
│   ├── style.css
│   ├── analytics.js        # GA4 page_view / language_change
│   ├── og-image.png        # 首页通用 OG 图（脚本生成）
│   └── og-<slug>.png       # per-skill OG 图（脚本生成）
├── scripts/
│   ├── generate_site.py    # 从 data.json 生成落地页 + sitemap
│   └── generate_og_images.py  # 生成 OG 分享图
├── sitemap.xml             # 脚本生成
├── robots.txt
├── notes.md                # 本备忘录
├── README.md
└── LICENSE                 # MIT
```

### 2.3 分发合同

| 通道 | 内容 | 说明 |
|------|------|------|
| **主** | GitHub `skills/<slug>/` | `npx skills add greenzorro/victor42-skills [--skill <slug>] -g` |
| **备选** | R2 `cloud` / `skills/<slug>.zip` | `https://cloud.victor42.work/skills/{slug}.zip`；无 Node 时用 |

公开仓 `skills/` 为**通用化副本**（可分享）；私人本机 Skills 目录可另有私有版，发版时再同步进仓。

**Zip 形态：** 顶层目录名为 `<slug>/`（内含 `SKILL.md` 等），不含 `__MACOSX` / `.DS_Store` / `__pycache__` / `*.pyc`。CDN（`cloud.victor42.work`）对 zip 有缓存（常见 `max-age=14400`）；R2 对象更新后，边缘命中旧包会在 TTL 内自然失效。

## 3. 功能模块

### 3.1 目录页

- `fetch('./data.json?v=…')` → 渲染回链「← 小玩意」、标题、简介、skill 卡片、页脚
- 卡片链到 `./{slug}/`；顺序即 `data.json` 中 `skills` 数组顺序
- 壳层 UI 文案在 `shared.js` 的 `UI_TEXT`；内容文案在 `data.json`
- `index.html` 内含目录内容的静态预渲染（简介、卡片网格、完整 ItemList JSON-LD），供无 JS 环境与搜索引擎抓取；JS 加载 `data.json` 后以相同结构重绘。增删 skill 或改文案时，`data.json` 与 `index.html` 的静态块需同步更新

### 3.2 落地页（脚本生成）

对人展示：触发词、能力分块、「给 AI 的安装指令」（文案为 **复制安装指令**发给 AI）。

对 Agent（无需 JS）：

- `meta name="skill:cli-install"` / `skill:download-url` / `skill:install-dir`
- `<link rel="alternate" type="application/zip">`
- JSON-LD `SoftwareApplication`（含 `downloadUrl` / `applicationCategory` / `image`）

安装正文由 `build_install_prompt()` 生成：步骤 1 为 `npx skills add … --skill <slug> -g`；步骤 2 为无 Node 时的 zip 备选。

### 3.3 SEO 与 OG 图

- **OG / Twitter 图**：每页 `og:image` + `twitter:image`（`summary_large_image`）。`generate_og_images.py` 输出 `assets/og-image.png` 与 `assets/og-<slug>.png`。版式统一：青绿满幅渐变、左上 brand、大标题、副标题、两行说明（CLI 命令 + `Install with the skills CLI`）；无水印、无右上装饰圆。首页标题为「Agent Skills」；单 skill 页标题为中文名、副标题为英文名、命令带 `--skill <slug>`。中文字体解析顺序：用户字体目录里的 Noto Sans CJK SC → 各系统 CJK 字体 → `fc-match` 发现 → PIL 默认；WSL 与 Windows 两侧都已装 Noto Sans CJK SC（Regular / Bold），在这两处生成结果一致。
- **OG 图不要无脑重跑后提交**：`generate_og_images.py` 的 PNG 编码不可字节复现，同一版式重跑后像素一致但体积会变（实测某张 37 KB → 47 KB）。只在该 skill 的**名称或安装命令**变化时才需要重新生成；仅改简介/能力文案时不要跑，或跑完后用 `git checkout --` 回滚 PNG。
- **hreflang**：单 URL + JS 切语言；每页自指 `zh-CN` / `en` / `x-default`。
- **canonical / sitemap**：canonical 指自身；`sitemap.xml` 的 `lastmod` 用各 skill 的 `updated`。
- **GA**：`analytics.js` 记 `page_view` 与 `language_change`。

### 3.4 语言与主题

- 语言：`?lang=` > localStorage > 默认 `zh`；切换后 `replaceState` 写回 URL
- 主题：`?theme=` > localStorage > `prefers-color-scheme`；head 内联脚本防 FOUC
- 主色 `#2A9D8F`，与小玩意一致；页脚：`Created by Victor42 & Vik | Code`

## 4. 新增 / 更新 skill

1. 将通用化后的内容写入 `skills/<slug>/`（保持干净目录，无打包噪音文件）；handoff 另有同步约定，见 §4.2
2. 在 `data.json` 追加或更新条目（数组顺序 = 门户顺序；刷新 `updated`）
3. 目录页 `index.html` 的静态预渲染块（卡片 `skill-summary` + ItemList JSON-LD 的 `description`）同步该条目的 `summary`，两份文案必须一致
4. （可选）从 `skills/` 打 zip（顶层目录 `<slug>/`，排除 `.DS_Store` / `__pycache__` / `*.pyc`）并上传 `cloud/skills/<slug>.zip`。当环境没有 `zip` 命令时用 Python `zipfile` 构建，命令与校验见 §4.2 第 5–6 步
5. `python3 scripts/generate_og_images.py`
6. `python3 scripts/generate_site.py`
7. 推送后 Cloudflare Pages 发布门户；已装用户可用 `npx skills update`

### 4.1 file-image-toolkit 的内部同步

`skills/file-image-toolkit/toolkit/` 是 `routine` 同名工具集的手工裁剪脱敏副本：只保留文件 / 图像 / 视频三域脚本，`utils/` 按目标脚本集的依赖闭包裁剪，`utils/path.py` 去掉个人路径（个人 Windows 用户名改为从环境变量推导）。

**routine 侧更新后需手工重新同步**，替换脚本与 utils，再按上面的裁剪边界重新裁剪、脱敏。

**同步基线：** routine `2e6743e`（2026-10-15）。

**本副本有意领先 routine 的两处改动，重新同步时不要被覆盖回去：**

1. `utils/basic.py` → `convert_format()` 的视频转GIF分支用调色板优化一步法（`palettegen`/`paletteuse`，fps=15、宽 800px），routine 仍是 `-c:v gif` + 480px
2. `utils/basic.py` → `convert_format()` 开头检测 `ffmpeg` 是否可用，缺失时抛出带安装指引的 `RuntimeError`，避免暴露 `Errno 2`

### 4.2 handoff 的私有版 → 公开版同步

`handoff` 的**正向源是本机 Skills 目录里的私有版**（行为以它为准）；仓里 `skills/handoff/` 是脱敏副本。两版的方法论、通道判定、notes.md 模板、禁止项必须一字不差，只有下表 6 项允许不同。

公开版固定由 4 个文件构成：`SKILL.md`、`references/config.md`、`references/r2.md`、`scripts/r2.py`。**`scripts/r2.py` 两版逐字节一致**——改脚本时两边同时替换，不要为公开版单独改代码。

**同步基线（2026-10-26）。以下 6 项差异是有意的，重新同步时不要被覆盖回去：**

| # | 项 | 私有版 | 公开版 |
|---|----|--------|--------|
| 1 | `provider` | `cloudflare-r2` | `none`（默认只走本地通道） |
| 2 | `account_id` / `token` | 真值 | 必须为空 |
| 3 | `bucket` / `prefix` | `lab` / `handoff/` | `handoff` / `handoff/` |
| 4 | 暂存目录 | 可提 `PATH_DOWNLOADS/temp` | 只用 `mktemp -d` |
| 5 | 路径示例 | 保留 WSL / Windows 具体写法 | 写"对方能打开的路径" |
| 6 | 文档语言 | 中文 `references/` | 英文 `references/` |

**公开版发版流程：**

1. 用 `skill` 的 `skill-genericizer` 跑 `scan_skill.py skills/handoff`；命中逐条人工判定，只接受误报（`Authorization` 头、`file=sys.stderr`、表格分隔线、空 `token =` 等）
2. `grep -rniE "cfat_|3f847438|\blab\b|artifacts" skills/handoff` 必须为空；产品名（Cursor/Claude/GPT/ChatGPT）也必须为 0——接收方按能力分类（能否在本机跑命令 / 是否有文件系统），不按产品名
3. 改 `data.json` 的 `updated` 与能力文案；`index.html` 里该条的静态 `summary` 同步（两份文案必须一致）
4. `python3 scripts/generate_site.py`
5. 从 `skills/` 打 zip：顶层目录 `handoff/`，排除 `.DS_Store` / `__pycache__` / `*.pyc`。本机没有 `zip` 命令，用 Python `zipfile` 构建（固定时间戳，可复现）
6. `wrangler r2 object put cloud/skills/handoff.zip --file=<zip> --content-type=application/zip --remote`
7. 提交推送 → Pages 自动发布；用带随机 query 的 URL 验证页面文案，下载 zip 校验 `sha256` 与本地一致

**发版后自检：** zip 内应恰好 4 个文件；`SKILL.md` 约 18 KB；`references/config.md` 的 `token =` 行尾为空。

## 5. 与小玩意关系

| 层 | 职责 |
|----|------|
| `victor42.work` | 发现：一张「Agent Skills」卡片 |
| `skills.victor42.work` | 交付：目录 + per-skill 页 + 安装引导 |
| GitHub `skills/` | 主分发：skills CLI |
| `cloud.victor42.work/skills/` | 备选 CDN：zip |

分享链接：`https://skills.victor42.work/{slug}/`

## 6. 部署

Cloudflare Pages 绑定 `greenzorro/victor42-skills`，域名 `skills.victor42.work`。无构建步骤；推送前跑过 `generate_site.py`（及需要时的 `generate_og_images.py`）。
