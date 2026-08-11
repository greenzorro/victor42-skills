---
name: file-image-toolkit
description: Use when processing files, converting formats, resizing/scaling/deduplicating images, composing GIFs, converting video, or managing bulk file operations. Provides CLI tools for image, video, and general file manipulation.
---

# File-Image Toolkit

## Capability Introduction

When a user asks about this skill's capabilities or it's the first interaction, read `SKILL_DIR/INTRO.md` and present its content to the user. This file is maintained separately for easy iteration.

---

## Overview

A CLI-based toolkit for file management, image processing, and video composition. All tools support command-line arguments for AI-direct invocation.

## ⚠️ Pre-flight Check (MUST DO BEFORE FIRST USE)

**Before invoking any toolkit script, you MUST verify prerequisites are met. If missing, install them automatically.**

### Step 1: Check Python packages

```bash
cd SKILL_DIR/toolkit && python -c "import PIL; import pillow_avif; import imagehash; import numpy; import cv2; print('All packages OK')"
```

**If import fails → install missing packages:**
```bash
cd SKILL_DIR/toolkit && pip install -r requirements.txt
```

Use `npx` for npm packages, `pip` for Python packages. Always install into the global environment (no venv).

### Step 2: Check FFmpeg (required for audio/video conversion only)

```bash
ffmpeg -version
```

**If not found → install FFmpeg:**
- macOS: `brew install ffmpeg`
- Linux/WSL: `sudo apt install ffmpeg` or `conda install ffmpeg`
- Windows: Download from https://ffmpeg.org/download.html and add to PATH

**FFmpeg is NOT required** for image-only tasks (resize, scale, dedup, avatar crop, GIF). Only required when using `convertor.py` with audio/video formats, or `video/images_2_video.py`.

### Step 3: Check opencv-python (required for avatar crop only)

`opencv-python` is a heavy package (~40MB). If `import cv2` fails:
```bash
pip install opencv-python
```

On Linux, may also need system libs: `sudo apt install libgl1-mesa-glx libglib2.0-0`

**opencv-python is NOT required** unless using `image/avatar_cropper.py` (face detection). All other image tools work with just Pillow.

### Prerequisite Matrix

| Script | FFmpeg | opencv | Pillow+basic packages |
|--------|:------:|:------:|:---------------------:|
| convertor (image) | ❌ | ❌ | ✅ |
| convertor (audio/video) | ✅ | ❌ | ✅ |
| convertor (video→GIF) | ✅ | ❌ | ✅ |
| folder_ungroup | ❌ | ❌ | ✅ |
| rename_by_csv | ❌ | ❌ | ✅ |
| resizer / scaler / dedup | ❌ | ❌ | ✅ |
| frames_2_gif / gif_2_frames | ❌ | ❌ | ✅ |
| avatar_cropper | ❌ | ✅ | ✅ |
| images_2_video | ✅ | ❌ | ✅ |

## Toolkit Location

All scripts are at `SKILL_DIR/toolkit/`. Run from that directory:

```bash
cd SKILL_DIR/toolkit && python <script> --help
```

## Quick Reference

| Task | Script | Key Args |
|------|--------|----------|
| Format conversion (img/audio/video) | `convertor.py` | `--source`, `--output`, `--format` |
| Flatten nested folders | `folder_ungroup.py` | `--source`, `--output` |
| Batch rename by CSV | `rename_by_csv.py` | `--csv`, `--source`, `--output` |
| Resize image (crop/pad) | `image/resizer.py` | `--source`, `--output`, `--width`, `--height`, `--mode` |
| Scale image proportionally | `image/scaler.py` | `--source`, `--output`, `--max-size`, `--mode` |
| Crop avatar from face | `image/avatar_cropper.py` | `--source`, `--output`, `--shape`, `--size` |
| Deduplicate similar images | `image/dedup.py` | `--source`, `--output`, `--threshold` |
| Frames → GIF | `image/frames_2_gif.py` | `--source`, `--output`, `--duration`, `--loop` |
| GIF → frames | `image/gif_2_frames.py` | `--source`, `--output` |
| Images → video (crossfade) | `video/images_2_video.py` | `--source`, `--output`, `--resolution`, `--duration`, `--fps` |

## Supported Formats

**Image:** jpg, jpeg, png, bmp, gif, tiff, webp, avif (any-to-any conversion)
**Audio:** mp3, wav, flac, aac, ogg, m4a, opus
**Video:** mp4, avi, wmv, mov, flv, mkv, webm, m4v + video-to-audio extraction

## Key Patterns

### Batch Processing
All scripts accept single file or folder. Folder mode processes all matching files recursively.

### Default Output
Most scripts default output to the system Downloads directory. Override with `--output`.

### Interactive Fallback
Run without args for interactive mode (prompt for required parameters).

## Detailed Reference

For complete documentation of all tools, see `SKILL_DIR/toolkit/user_guide.md`.