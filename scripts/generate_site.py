#!/usr/bin/env python3
"""Generate skill detail pages, sitemap.xml from data.json.

Each detail page is a self-contained static HTML with full SEO metadata:
canonical, hreflang (zh-CN / en / x-default), Open Graph + Twitter Card
images (summary_large_image), and SoftwareApplication structured data.
OG images are produced by generate_og_images.py.
"""

from __future__ import annotations

import html
import json
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data.json"
ASSET_VERSION = "20260730"
SITE_NAME = "Victor42 · Agent Skills"


def load_data() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def pick(obj: dict, lang: str) -> str:
    return obj.get(lang) or obj.get("zh") or ""


def hreflang_for(url: str) -> str:
    """Emit self-referencing hreflang for a single bilingual URL.

    Since this is one URL with JS-based language switching (not separate
    zh/ and en/ URLs), we point both alternates back to the same URL and
    signal the two locales. This tells Google the page is bilingual rather
    than a duplicate of itself.
    """
    safe = escape(url)
    return "\n    ".join([
        f'<link rel="alternate" hreflang="zh-CN" href="{safe}">',
        f'<link rel="alternate" hreflang="en" href="{safe}">',
        '<link rel="alternate" hreflang="x-default" href="{url}">'.format(url=safe),
    ])


def build_install_prompt(skill: dict, site: dict, lang: str) -> str:
    name = pick(skill["name"], lang)
    zip_url = f"{site['cdnBase'].rstrip('/')}/{skill['zipFile']}"
    install_dir = skill["installDir"]

    if lang == "zh":
        return (
            f"请帮我安装 Victor42 的 {name} skill：\n"
            f"1. 下载 {zip_url}\n"
            f"2. 解压到你当前环境的 skills 目录下，文件夹名为 {install_dir}\n"
            f"3. 确认其中存在 SKILL.md 后告诉我安装完成"
        )

    return (
        f"Please install Victor42's {name} skill:\n"
        f"1. Download {zip_url}\n"
        f"2. Extract into your current environment's skills directory as a folder named {install_dir}\n"
        f"3. Confirm SKILL.md exists, then tell me installation is complete"
    )


def render_triggers(triggers: dict, lang: str) -> str:
    tags = triggers.get(lang) or triggers.get("zh") or []
    return "\n".join(f"    <li>{html.escape(tag)}</li>" for tag in tags)


def render_capabilities(capabilities: dict, lang: str) -> str:
    sections = capabilities.get(lang) or capabilities.get("zh") or []
    blocks: list[str] = []
    for section in sections:
        heading = html.escape(section["heading"])
        items = section["items"]
        lis = "\n".join(f"        <li>{html.escape(item)}</li>" for item in items)
        blocks.append(
            "\n".join(
                [
                    '    <section class="capability-block">',
                    f"      <h3>{heading}</h3>",
                    "      <ul>",
                    lis,
                    "      </ul>",
                    "    </section>",
                ]
            )
        )
    return "\n".join(blocks)


def render_skill_page(skill: dict, data: dict) -> str:
    site = data["site"]
    origin = site["origin"].rstrip("/")
    slug = skill["slug"]
    zip_url = f"{site['cdnBase'].rstrip('/')}/{skill['zipFile']}"
    page_url = f"{origin}/{slug}/"
    install_dir = skill["installDir"]

    name_zh = pick(skill["name"], "zh")
    name_en = pick(skill["name"], "en")
    summary_zh = pick(skill["summary"], "zh")
    summary_en = pick(skill["summary"], "en")
    capabilities = skill["capabilities"]
    caps_zh = render_capabilities(capabilities, "zh")
    caps_en = render_capabilities(capabilities, "en")
    triggers_zh = render_triggers(skill["triggers"], "zh")
    triggers_en = render_triggers(skill["triggers"], "en")
    install_zh = html.escape(build_install_prompt(skill, site, "zh"))
    install_en = html.escape(build_install_prompt(skill, site, "en"))
    updated = skill["updated"]
    emoji = html.escape(skill["emoji"])
    page_title = f"{name_zh} - {SITE_NAME}"
    og_image_url = f"{origin}/assets/og-{slug}.png"
    hreflang_tags = hreflang_for(page_url)

    json_ld = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": name_en,
        "alternateName": name_zh,
        "description": summary_en,
        "url": page_url,
        "downloadUrl": zip_url,
        "codeRepository": site["github"],
        "applicationCategory": "DeveloperApplication",
        "operatingSystem": "Cross-platform (AI agent runtime)",
        "author": {"@type": "Person", "name": "Victor42", "url": site["parentSite"]},
        "image": og_image_url,
        "dateModified": updated,
    }

    site_json = json.dumps(site, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(page_title)}</title>

    <meta name="description" content="{html.escape(summary_zh)}">
    <meta name="author" content="Victor42">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="{html.escape(page_url)}">

    {hreflang_tags}

    <meta name="skill:slug" content="{html.escape(slug)}">
    <meta name="skill:download-url" content="{html.escape(zip_url)}">
    <meta name="skill:install-dir" content="{html.escape(install_dir)}">

    <link rel="alternate" type="application/zip" href="{html.escape(zip_url)}" title="{html.escape(name_en)} skill package">

    <meta property="og:type" content="website">
    <meta property="og:title" content="{html.escape(page_title)}">
    <meta property="og:description" content="{html.escape(summary_zh)}">
    <meta property="og:url" content="{html.escape(page_url)}">
    <meta property="og:site_name" content="{SITE_NAME}">
    <meta property="og:locale" content="zh_CN">
    <meta property="og:locale:alternate" content="en_US">
    <meta property="og:image" content="{html.escape(og_image_url)}">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:image:alt" content="{html.escape(name_zh)} skill cover">

    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{html.escape(name_zh)}">
    <meta name="twitter:description" content="{html.escape(summary_zh)}">
    <meta name="twitter:image" content="{html.escape(og_image_url)}">

    <meta name="theme-color" content="#2A9D8F">
    <link rel="icon" type="image/x-icon" href="https://victor42.work/assets/images/favicon.ico">

    <script src="../assets/analytics.js"></script>

    <script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
    </script>

    <link rel="stylesheet" href="../assets/style.css?v={ASSET_VERSION}">

    <script>
    (function() {{
        const urlParams = new URLSearchParams(window.location.search);
        const urlTheme = urlParams.get('theme');
        if (urlTheme === 'dark' || urlTheme === 'light') {{
            localStorage.setItem('theme', urlTheme);
        }}
        const savedTheme = localStorage.getItem('theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        const theme = savedTheme || (prefersDark ? 'dark' : 'light');
        if (theme === 'dark') {{
            document.documentElement.setAttribute('data-theme', 'dark');
        }}
    }})();
    </script>

    <script type="application/json" id="site-data">{site_json}</script>
</head>
<body>
    <button class="theme-toggle" id="theme-toggle" aria-label="切换深色模式" type="button">
        <span class="theme-icon" aria-hidden="true">🌙</span>
    </button>

    <button class="lang-toggle" id="lang-toggle" aria-label="切换语言" type="button">
        <span class="lang-icon" aria-hidden="true">🌐</span>
        <span class="lang-text">EN</span>
    </button>

    <div class="container">
        <header class="skill-detail-header">
            <a class="back-link" href="../">← {html.escape(SITE_NAME)}</a>
            <div class="detail-emoji" aria-hidden="true">{emoji}</div>
            <h1 class="detail-title" data-lang="zh">{html.escape(name_zh)}</h1>
            <h1 class="detail-title" data-lang="en" hidden>{html.escape(name_en)}</h1>
            <p class="detail-summary" data-lang="zh">{html.escape(summary_zh)}</p>
            <p class="detail-summary" data-lang="en" hidden>{html.escape(summary_en)}</p>
        </header>

        <section class="panel">
            <h2 data-lang="zh">触发词</h2>
            <h2 data-lang="en" hidden>Triggers</h2>
            <ul class="tag-list" data-lang="zh">
{triggers_zh}
            </ul>
            <ul class="tag-list" data-lang="en" hidden>
{triggers_en}
            </ul>
        </section>

        <section class="panel capabilities-panel" data-lang="zh">
            <h2>能力</h2>
{caps_zh}
        </section>
        <section class="panel capabilities-panel" data-lang="en" hidden>
            <h2>Capabilities</h2>
{caps_en}
        </section>

        <section class="panel install-block">
            <h2 id="install-title">给 AI 的安装指令</h2>
            <p class="copy-hint">
                <span data-lang="zh">把下面这段发给你的 Agent，或</span>
                <span data-lang="en" hidden>Send the block below to your agent, or </span>
                <button type="button" class="copy-link" id="copy-btn">
                    <span data-lang="zh">复制安装指令</span>
                    <span data-lang="en" hidden>copy the install prompt</span>
                </button>
                <span data-lang="zh">。</span>
                <span data-lang="en" hidden>.</span>
            </p>
            <div id="install-zh" data-lang="zh">
                <pre>{install_zh}</pre>
            </div>
            <div id="install-en" data-lang="en" hidden>
                <pre>{install_en}</pre>
            </div>
        </section>

        <footer class="footer">
            <p id="footer-text"></p>
        </footer>
    </div>

    <script src="../assets/shared.js?v={ASSET_VERSION}"></script>
    <script src="../assets/skill.js?v={ASSET_VERSION}"></script>
</body>
</html>
"""


def build_sitemap(data: dict, lastmod: str) -> str:
    origin = data["site"]["origin"].rstrip("/") + "/"
    entries = [
        "\n".join(
            [
                "  <url>",
                f"    <loc>{escape(origin)}</loc>",
                f"    <lastmod>{lastmod}</lastmod>",
                "    <changefreq>monthly</changefreq>",
                "    <priority>1.0</priority>",
                "  </url>",
            ]
        )
    ]

    for skill in data["skills"]:
        loc = f"{data['site']['origin'].rstrip('/')}/{skill['slug']}/"
        entries.append(
            "\n".join(
                [
                    "  <url>",
                    f"    <loc>{escape(loc)}</loc>",
                    f"    <lastmod>{skill['updated']}</lastmod>",
                    "    <changefreq>monthly</changefreq>",
                    "    <priority>0.9</priority>",
                    "  </url>",
                ]
            )
        )

    body = "\n".join(entries)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n"
        "</urlset>\n"
    )


def main() -> None:
    data = load_data()
    skills = data["skills"]
    if not skills:
        raise SystemExit("data.json: skills array is empty")

    for skill in skills:
        slug = skill["slug"]
        out_dir = ROOT / slug
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "index.html"
        out_path.write_text(render_skill_page(skill, data), encoding="utf-8")
        print(f"wrote {out_path.relative_to(ROOT)}")

    lastmod = date.today().isoformat()
    sitemap_path = ROOT / "sitemap.xml"
    sitemap_path.write_text(build_sitemap(data, lastmod), encoding="utf-8")
    print(f"wrote {sitemap_path.relative_to(ROOT)} ({1 + len(skills)} urls)")


if __name__ == "__main__":
    main()
