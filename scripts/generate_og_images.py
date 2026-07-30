#!/usr/bin/env python3
"""Generate OG share images (1200x630) for the skills portal.

Outputs:
  assets/og-image.png          — generic brand card (for homepage + fallback)
  assets/og-<slug>.png         — per-skill card (emoji + name overlaid)

Design mirrors site style: primary #2A9D8F, soft bg #f5f5fa, hero gradient.
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data.json"
ASSETS_DIR = ROOT / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

W, H = 1200, 630
PRIMARY = (42, 157, 143)          # #2A9D8F
PRIMARY_DARK = (33, 151, 137)     # #219789
BG = (245, 245, 250)              # #f5f5fa
WHITE = (255, 255, 255)
TEXT_HEADING = (44, 62, 80)       # #2c3e50
TEXT_BODY = (85, 85, 85)          # #555
TEXT_MUTED = (127, 140, 141)      # #7f8c8d


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Pick a CJK-capable font available on macOS; fall back to default."""
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    if bold:
        candidates = [
            "/System/Library/Fonts/PingFang.ttc",  # ttc includes bold variant
            "/System/Library/Fonts/STHeiti Medium.ttc",
        ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size, index=1 if bold and path.endswith(".ttc") else 0)
            except Exception:
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    continue
    return ImageFont.load_default()


def _gradient(draw: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int,
              c0: tuple, c1: tuple) -> None:
    """Fill a horizontal linear gradient rectangle."""
    for x in range(x0, x1):
        t = (x - x0) / max(1, (x1 - x0 - 1))
        r = int(c0[0] + (c1[0] - c0[0]) * t)
        g = int(c0[1] + (c1[1] - c0[1]) * t)
        b = int(c0[2] + (c1[2] - c0[2]) * t)
        draw.line([(x, y0), (x, y1 - 1)], fill=(r, g, b))


def _draw_base(emoji: str | None, name_zh: str, name_en: str,
               tagline_zh: str, tagline_en: str) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Hero gradient band across the top half
    _gradient(draw, 0, 0, W, H, PRIMARY, PRIMARY_DARK)

    # Subtle decorative circle (echo of portal hero card)
    draw.ellipse([(W - 380, -120), (W + 120, 380)],
                 fill=(255, 255, 255, 0), outline=None)

    # Brand mark — small label top-left
    brand_font = _font(26, bold=True)
    draw.text((80, 70), "VICTOR42 · AGENT SKILLS", font=brand_font, fill=WHITE)

    if emoji and name_zh:
        # Per-skill card
        emoji_font = _font(150)
        draw.text((80, 160), emoji, font=emoji_font, fill=WHITE)

        name_font = _font(86, bold=True)
        draw.text((80, 360), name_zh, font=name_font, fill=WHITE)

        sub_font = _font(40)
        draw.text((80, 470), name_en, font=sub_font, fill=(220, 245, 240))

        # Tagline at the bottom on the soft bg strip
        tag_font = _font(26)
        draw.text((80, 555), tagline_zh, font=tag_font, fill=WHITE)
    else:
        # Generic homepage card
        title_font = _font(96, bold=True)
        draw.text((80, 220), "Agent Skills", font=title_font, fill=WHITE)

        sub_font = _font(46)
        draw.text((80, 350), "能力包 · Capability Packs", font=sub_font,
                  fill=(220, 245, 240))

        tag_font = _font(28)
        draw.text((80, 440),
                  "把链接丢给你的 AI，让它帮你下载安装",
                  font=tag_font, fill=WHITE)
        draw.text((80, 485),
                  "Share a link — let your agent install it",
                  font=tag_font, fill=(220, 245, 240))

    # Bottom-right small url mark
    url_font = _font(24)
    draw.text((W - 340, H - 50), "skills.victor42.work",
              font=url_font, fill=(255, 255, 255))

    return img


def main() -> None:
    # Generic brand image
    generic = _draw_base(None, "", "", "", "")
    generic_path = ASSETS_DIR / "og-image.png"
    generic.save(generic_path, "PNG", optimize=True)
    print(f"wrote {generic_path.relative_to(ROOT)}")

    # Per-skill images
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    for skill in data["skills"]:
        slug = skill["slug"]
        name_zh = skill["name"].get("zh", "")
        name_en = skill["name"].get("en", "")
        summary_zh = skill["summary"].get("zh", "")[:60]
        summary_en = skill["summary"].get("en", "")[:70]
        img = _draw_base(skill["emoji"], name_zh, name_en, summary_zh, summary_en)
        out = ASSETS_DIR / f"og-{slug}.png"
        img.save(out, "PNG", optimize=True)
        print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
