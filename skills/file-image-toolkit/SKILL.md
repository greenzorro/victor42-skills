---
name: file-image-toolkit
description: Use when processing files, converting formats, resizing/scaling/deduplicating images, composing GIFs, converting video, downloading videos embedded in WeChat articles, or managing bulk file operations. Provides CLI tools for image, video, and general file manipulation.
---

# File-Image Toolkit

## Capability Introduction

When a user asks about this skill's capabilities or it's the first interaction, read `SKILL_DIR/INTRO.md` and present its content to the user. This file is maintained separately for easy iteration.

---

## Overview

A CLI-based toolkit for file management, image processing, video composition, and WeChat article video download. All tools support command-line arguments for AI-direct invocation.

## ⚠️ Pre-flight Check (MUST DO BEFORE FIRST USE)

**Before invoking any toolkit script, you MUST verify prerequisites are met. If missing, install them automatically.**

All scripts need **Python 3.8+**. Resolve the interpreter once and reuse it for every check and every script run:

```bash
PY=$(command -v python3 || command -v python)
"$PY" --version
```

On Windows, run these checks in WSL or Git Bash (PowerShell equivalents work too, but the commands below use POSIX syntax).

### Step 1: Check Python packages (required by every script)

```bash
cd SKILL_DIR/toolkit && "$PY" -c "import PIL; import pillow_avif; import imagehash; import numpy; print('All packages OK')"
```

**If import fails → install missing packages:**
```bash
cd SKILL_DIR/toolkit && "$PY" -m pip install -r requirements.txt
```

Use `npx` for npm packages, `pip` for Python packages.

**If pip refuses with `error: externally-managed-environment` (PEP 668)** — common on Homebrew Python, Ubuntu 23.04+, Debian 12 — the system Python blocks global installs. Two options:
- Append `--break-system-packages` (simplest; these packages don't modify system files)
- Or create a dedicated venv and use **its** interpreter for both the checks and the scripts

### Step 2: Check FFmpeg (audio/video only)

```bash
ffmpeg -version
ffmpeg -hide_banner -filters | grep -E ' (xfade|palettegen|paletteuse) '
```

The second command must list all three filters. A missing `xfade` means FFmpeg is older than 4.3 and `images_2_video.py` will fail.

**If not found or too old → install/upgrade FFmpeg:**
- macOS: `brew install ffmpeg`
- Linux/WSL: `sudo apt install ffmpeg` or `conda install ffmpeg`（发行版自带版本偏旧时，用 https://johnvansickle.com/ffmpeg/ 的静态包）
- Windows: Download from https://ffmpeg.org/download.html and add to PATH

**FFmpeg is NOT required** for image-only tasks (resize, scale, dedup, avatar crop, GIF compose). Only required when using `convertor.py` with audio/video formats (including video→GIF), or `video/images_2_video.py`.

### Step 3: Check curl (WeChat article video download only)

```bash
curl --version
```

`video/wechat_article_video_dl.py` shells out to system `curl` on purpose: Python's stdlib TLS fingerprint gets flagged by WeChat's risk control.

**If not found → install curl:**
- macOS / Linux / WSL: built in
- Windows 10 1803+: built in (`curl.exe`); otherwise enable it in Settings → Apps → Optional features, or use the one bundled with Git for Windows.

### Step 4: Check opencv-python (avatar crop only)

```bash
"$PY" -c "import cv2; print('opencv OK')"
```

**If import fails → install it** (约 40MB，只有人脸检测需要）:
```bash
"$PY" -m pip install opencv-python
```

On Linux, may also need system libs: `sudo apt install libgl1-mesa-glx libglib2.0-0`

**opencv-python is NOT required** unless using `image/avatar_cropper.py` (face detection). All other image tools work with just Pillow.

### Prerequisite Matrix

All scripts require Python 3.8+ and the Pillow stack.

| Script | FFmpeg | curl | opencv | Pillow stack |
|--------|:------:|:----:|:------:|:------------:|
| convertor (image) | ❌ | ❌ | ❌ | ✅ |
| convertor (audio/video) | ✅ | ❌ | ❌ | ✅ |
| convertor (video→GIF) | ✅ | ❌ | ❌ | ✅ |
| folder_ungroup | ❌ | ❌ | ❌ | ✅ |
| rename_by_csv | ❌ | ❌ | ❌ | ✅ |
| resizer / scaler / dedup | ❌ | ❌ | ❌ | ✅ |
| frames_2_gif / gif_2_frames | ❌ | ❌ | ❌ | ✅ |
| avatar_cropper | ❌ | ❌ | ✅ | ✅ |
| images_2_video | ✅ | ❌ | ❌ | ✅ |
| wechat_article_video_dl | ❌ | ✅ | ❌ | ✅ |

## Toolkit Location

All scripts are at `SKILL_DIR/toolkit/`. Run from that directory:

```bash
cd SKILL_DIR/toolkit && python <script> --help
```

## Quick Reference

| Task | Script | Key Args |
|------|--------|----------|
| Format conversion (img/audio/video) | `convertor.py` | `--source`, `--output`, `--format`, `--dry-run` |
| Flatten nested folders | `folder_ungroup.py` | `--source`, `--output`, `--dry-run` |
| Batch rename by CSV | `rename_by_csv.py` | `--csv`, `--source`, `--output`, `--dry-run` |
| Resize image (crop/pad) | `image/resizer.py` | `--source`, `--output`, `--width`, `--height`, `--mode` |
| Scale image proportionally | `image/scaler.py` | `--source`, `--output`, `--max-size`, `--mode`, `--min-width` |
| Crop avatar from face | `image/avatar_cropper.py` | `--source`, `--output`, `--shape`, `--size`, `--padding` |
| Deduplicate similar images | `image/dedup.py` | `--source`, `--output`, `--threshold`, `--execute` |
| Frames → GIF | `image/frames_2_gif.py` | `--source`, `--output`, `--duration`, `--loop` |
| GIF → frames | `image/gif_2_frames.py` | `--source`, `--output` |
| Images → video (crossfade) | `video/images_2_video.py` | `--source`, `--output`, `--resolution`, `--duration`, `--fps` |
| WeChat article videos → mp4 | `video/wechat_article_video_dl.py` | `--source`, `--output`, `--quality`, `--list` |

## Supported Formats

**Image:** jpg, jpeg, jfif, png, bmp, gif, tiff, webp, avif (any-to-any conversion)
**Audio:** mp3, wav, flac, aac, ogg, m4a, opus
**Video:** mp4, avi, wmv, mov, flv, mkv, webm, m4v + video-to-audio extraction + video-to-GIF

## Key Patterns

### Batch Processing
All scripts accept single file or folder. Folder mode processes all matching files recursively.

### Dry Run
`convertor.py`, `folder_ungroup.py`, and `rename_by_csv.py` accept `--dry-run` to list the planned work without creating directories or writing files. Prefer it when the user is unsure about the output.

### No Silent Overwrites
When recursive folder processing would produce colliding filenames, the toolkit appends `_2`, `_3`, … instead of overwriting. No input file is ever lost.

### Default Output
Most scripts default output to the system Downloads directory. Override with `--output`.

### Interactive Fallback
Run without args for interactive mode (prompt for required parameters).

## Detailed Reference

For complete documentation of all tools, see `SKILL_DIR/toolkit/user_guide.md`.
