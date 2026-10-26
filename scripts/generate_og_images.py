#!/usr/bin/env python3
"""Generate OG share images (1200x630) for the skills portal.

Outputs:
  assets/og-image.png          — generic brand card (for homepage + fallback)
  assets/og-<slug>.png         — per-skill card (same layout; skill name + install)

Design mirrors site style: primary #2A9D8F full-bleed gradient, left-aligned type.
"""

from __future__ import annotations

import json
import subprocess
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


def _fontconfig_cjk() -> str | None:
    """Ask fontconfig for a Chinese-capable font (Linux and other fontconfig systems)."""
    try:
        result = subprocess.run(
            ["fc-match", "-f", "%{file}", "sans-serif:lang=zh"],
            capture_output=True, text=True, timeout=5, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    candidate = result.stdout.strip()
    return candidate if candidate and Path(candidate).exists() else None


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Pick a CJK-capable font across macOS, Linux and Windows; fall back to fontconfig, then default."""
    candidates = [
        ("/System/Library/Fonts/PingFang.ttc", 0),
        ("/System/Library/Fonts/STHeiti Medium.ttc", 0),
        ("/System/Library/Fonts/Hiragino Sans GB.ttc", 0),
        ("/Library/Fonts/Arial Unicode.ttf", 0),
        ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 0),
        ("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc", 0),
        ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 0),
        ("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc", 0),
        ("/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf", 0),
        ("C:/Windows/Fonts/msyh.ttc", 0),
        ("C:/Windows/Fonts/simhei.ttf", 0),
        ("C:/Windows/Fonts/simsun.ttc", 0),
    ]
    if bold:
        candidates = [
            ("/System/Library/Fonts/PingFang.ttc", 1),  # ttc includes the bold variant
            ("/System/Library/Fonts/STHeiti Medium.ttc", 1),
            ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 0),
            ("/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc", 0),
            ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 0),
            ("C:/Windows/Fonts/msyhbd.ttc", 0),
            ("C:/Windows/Fonts/simhei.ttf", 0),
        ]
    for path, index in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size, index=index)
            except Exception:
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    continue
    discovered = _fontconfig_cjk()
    if discovered:
        try:
            return ImageFont.truetype(discovered, size)
        except Exception:
            pass
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


def _draw_base(title: str, subtitle: str, line1: str, line2: str) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Full-bleed primary gradient
    _gradient(draw, 0, 0, W, H, PRIMARY, PRIMARY_DARK)

    # Brand mark — small label top-left
    brand_font = _font(26, bold=True)
    draw.text((80, 70), "VICTOR42 · AGENT SKILLS", font=brand_font, fill=WHITE)

    title_font = _font(96, bold=True)
    draw.text((80, 220), title, font=title_font, fill=WHITE)

    sub_font = _font(46)
    draw.text((80, 350), subtitle, font=sub_font, fill=(220, 245, 240))

    tag_font = _font(28)
    draw.text((80, 440), line1, font=tag_font, fill=WHITE)
    draw.text((80, 485), line2, font=tag_font, fill=(220, 245, 240))

    return img


def main() -> None:
    # Generic brand image
    generic = _draw_base(
        "Agent Skills",
        "能力包 · Capability Packs",
        "npx skills add greenzorro/victor42-skills",
        "Install with the skills CLI",
    )
    generic_path = ASSETS_DIR / "og-image.png"
    generic.save(generic_path, "PNG", optimize=True)
    print(f"wrote {generic_path.relative_to(ROOT)}")

    # Per-skill images — same layout as homepage
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    for skill in data["skills"]:
        slug = skill["slug"]
        name_zh = skill["name"].get("zh", "")
        name_en = skill["name"].get("en", "")
        img = _draw_base(
            name_zh,
            name_en,
            f"npx skills add greenzorro/victor42-skills --skill {slug}",
            "Install with the skills CLI",
        )
        out = ASSETS_DIR / f"og-{slug}.png"
        img.save(out, "PNG", optimize=True)
        print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
