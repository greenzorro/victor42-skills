# Agent Skills 门户 — 项目备忘录

## 1. 目的

记录 `projects/victor42-skills`（线上 https://skills.victor42.work/）的结构与维护约定，供本人与 Agent 后续改站时对齐。

**定位：** 小玩意创造营地下 Agent 类创造物的交付端点。`victor42.work` 首页仅放一张合集卡片指向本站。

**约定：** 改功能或数据结构后，同步更新本文，使其持续描述当前实现。

## 2. 项目概述

静态门户：JSON 驱动目录页；各 skill 落地页由脚本生成。支持中英切换与深/浅色主题。无构建步骤，适合 Cloudflare Pages。zip 包托管于 R2，本站只做发现与安装引导。

### 2.1 技术栈

- **HTML5**：目录页壳、SEO meta（canonical / hreflang / OG / Twitter Card）、JSON-LD；落地页为预渲染静态 HTML
- **CSS3**：响应式双列卡片、CSS 变量主题、`:focus-visible`
- **JavaScript (ES6)**：目录页 `fetch` 加载数据并渲染；落地页负责复制安装指令、主题/语言；GA 路由追踪
- **JSON**：`data.json` 为唯一内容源（文案双语；数组顺序 = 展示顺序）
- **LocalStorage**：主题 `theme`、语言 `language`
- **Python**：`generate_site.py` 生成 `{slug}/index.html` 与 `sitemap.xml`；`generate_og_images.py` 生成 OG 分享图

### 2.2 文件结构

```
victor42-skills/
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

**文件分发：** R2 桶 `cloud`，前缀 `skills/` → `https://cloud.victor42.work/skills/{slug}.zip`。

## 3. 功能模块

### 3.1 目录页

- `fetch('./data.json?v=…')` → 渲染回链「← 小玩意」、标题、简介、skill 卡片、页脚
- 卡片链到 `./{slug}/`；顺序即 `skills` 数组顺序
- 壳层 UI 文案在 `shared.js` 的 `UI_TEXT`；内容文案在 `data.json`

### 3.2 落地页（脚本生成）

对人展示：触发词、能力分块、「给 AI 的安装指令」（内联文字链复制）。

对 Agent（无需 JS）：

- `meta name="skill:download-url"` / `skill:install-dir`（仅文件夹名，不写死绝对路径）
- `<link rel="alternate" type="application/zip">`
- JSON-LD `SoftwareApplication`（含 `downloadUrl` / `applicationCategory` / `image`）

安装指令由 `build_install_prompt()` 用现有字段拼接（`name`、`cdnBase`+`zipFile`、`installDir`），无需额外配置。

### 3.3 SEO 措施

- **OG / Twitter 图**：每页 `og:image` + `twitter:image`（`summary_large_image`）；图由 `scripts/generate_og_images.py` 生成于 `assets/og-image.png`（首页通用）与 `assets/og-<slug>.png`（每 skill 一张）。改了 brand 或 skill 名称后重跑该脚本。
- **hreflang**：单 URL + JS 切语言场景，每页自指 `hreflang="zh-CN"` / `en` / `x-default` 三条，避免 Google 判重复内容。
- **canonical / sitemap**：每页 canonical 指自身 URL；`sitemap.xml` 的 `lastmod` 用 `data.json` 中各 skill 的 `updated` 字段。
- **GA 路由追踪**：`analytics.js` 在每页首次加载与语言切换后触发 `page_view`，并记 `language_change` 事件。

### 3.4 语言与主题

- 语言：`?lang=` > localStorage > 默认 `zh`；切换后 `replaceState` 写回 URL
- 主题：`?theme=` > localStorage > `prefers-color-scheme`；head 内联脚本防 FOUC
- 主色 `#2A9D8F`，与小玩意一致；页脚格式对齐 album：`Created by Victor42 & Vik | Code`

## 4. 新增 / 更新 skill

1. 维护 skill 源码，打 zip 上传 R2：`skills/{slug}.zip`
2. 在 `data.json` 追加或更新条目（调顺序即调门户顺序）
3. 运行 `python3 scripts/generate_og_images.py`（刷新 OG 图）
4. 运行 `python3 scripts/generate_site.py`（生成落地页 + sitemap）
5. 部署（推送后 Cloudflare Pages 发布）

## 5. 与小玩意关系

| 层 | 职责 |
|----|------|
| `victor42.work` | 发现：一张「Agent Skills」卡片 |
| `skills.victor42.work` | 交付：目录 + per-skill 页 |
| `cloud.victor42.work/skills/` | CDN：zip |

分享链接格式：`https://skills.victor42.work/{slug}/`

## 6. 部署

Cloudflare Pages 绑定 `greenzorro/victor42-skills`，自定义域名 `skills.victor42.work`。无构建步骤；推送前确保已运行 `generate_site.py`。
