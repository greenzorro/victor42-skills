# Toolkit AI使用手册

本手册面向AI助手，说明 toolkit 中所有脚本的功能和用途，便于AI作为工具执行具体任务。

## 项目概述

`toolkit` 提供文件管理、格式转换、图像处理、视频处理与下载工具。所有脚本均支持命令行参数调用，可被AI直接执行。

**核心特性：**
- 🤖 **AI友好**：所有脚本支持命令行参数，适合AI调用
- 🔄 **双模式**：命令行模式（主要）+ 交互模式（备用）
- 🛡️ **不覆盖**：批量操作遇同名文件自动加序号；关键工具支持 `--dry-run` 演练
- 📦 **模块化**：核心功能封装在utils库中
- 🌐 **跨平台**：支持Windows/WSL/Linux/macOS

**同步基线：** 本目录仅保留文件/图像/视频域的脚本，Capability Introduction 所列即全部能力。

## 目录结构

```
toolkit/
├── 根目录脚本/      - 文件管理、格式转换
├── image/          - 图像处理工具集
├── video/          - 视频处理与下载工具集
├── utils/          - 核心工具函数库
    ├── path.py     - 跨平台路径配置
    ├── basic.py    - 文件处理、格式转换等基础函数
    ├── image.py    - 图像处理函数（裁剪、缩放、指纹、去重、GIF转换）
    └── video.py    - FFmpeg命令构建
└── requirements.txt - 依赖列表
```

## 使用方式

### 命令行参数模式（推荐）

所有脚本支持标准命令行参数，具体参数用法请用 `--help` 查看。

### 查看帮助

```bash
python script.py --help
python script.py -h
```

### 交互式模式

不带任何参数运行脚本，会进入交互模式询问必需参数：

```bash
python script.py
```

---

## 根目录工具

### 格式转换工具

#### `convertor.py` - 通用格式转换器
**功能：** 批量转换文件格式（基于ffmpeg和Pillow）
**输入：** 支持单个文件或文件夹；文件夹模式会递归处理
**输出：** 默认 `PATH_DOWNLOADS/Converted`；递归扁平化输出，遇同名自动加序号
**参数：** `--source` `--output` `--format` `--dry-run`

**支持的格式转换：**

**图片格式转换（支持任意互转）：**
- 源格式：jpg, jpeg, jfif, png, bmp, gif, tiff, webp, avif
- 目标格式：上述格式任意互转
- jpg / jpeg / jfif 之间互转直接复制文件，不重新编码
- 转 png / webp / avif 等支持透明的格式会保留 alpha 通道

**音频格式转换：**
- 源格式：mp3, wav, flac, aac, ogg, m4a, opus
- 目标格式：mp3, wav, flac, aac, ogg, m4a, opus

**视频格式转换：**
- 源格式：mp4, avi, wmv, mov, flv, m4a, mkv, webm, m4v
- 目标格式：mp4, mov, m4v, mkv, avi, webm, flv, wmv
- 视频转音频：可转换为 mp3, wav, flac, aac, ogg, m4a, opus
- 视频转GIF：使用调色板优化一步法（fps=15，宽度800px），体积更小、色带更少

---

### 文件管理工具

#### `folder_ungroup.py` - 文件夹解组工具
**功能：** 将嵌套文件夹中的所有文件提取到单一文件夹中
**输出：** 默认 `PATH_DOWNLOADS/Ungrouped`；遇同名自动加序号，不覆盖
**参数：** `--source` `--output` `--dry-run`

---

#### `rename_by_csv.py` - CSV批量重命名工具
**功能：** 根据CSV文件中的映射关系批量重命名文件
**CSV文件格式：** 必须包含 `name` 列，源文件名需要包含数字序号
**参数：** `--csv` `--source` `--output` `--dry-run`
**说明：** 只复制并重命名，不改动源文件；文件数与名称数不匹配时会提示并退出

---

## 图像处理工具（image/）

### `resizer.py` - 图片尺寸调整工具
**功能：** 智能调整图片尺寸，支持裁剪和留白模式
**输入：** 支持单张图片或图片文件夹
**参数：** `--source` `--output` `--width` `--height` `--mode`（crop/pad）`--bg-color`（pad模式背景色）

---

### `scaler.py` - 图片比例缩放工具
**功能：** 按比例缩放图片，限制在指定尺寸内
**输入：** 支持单张图片或图片文件夹
**参数：** `--source` `--output` `--max-size` `--mode`（long/short）`--min-width`
**说明：** `long` 只缩小长边超限的图，`short` 会把短边放大到目标值

---

### `avatar_cropper.py` - 批量头像裁剪工具
**功能：** 批量将包含人脸的照片裁剪为指定尺寸的头像（支持圆形或方形）
**输入：** 支持单张图片或图片文件夹
**参数：** `--source` `--output` `--shape` `--size` `--padding`
**依赖：** 需要 `opencv-python`

---

### `dedup.py` - 智能图片去重工具
**功能：** 自动识别文件夹中的相似图片（包括缩放变体和裁剪变体），并保留分辨率最高的一个版本。
**参数：** `--source` `--output` `--threshold` `--crop-similarity` `--execute`
**说明：** 默认只预览；加 `--execute` 才真正把重复件移动到 `--output`。**不删除任何文件。**

---

### `frames_2_gif.py` - GIF合成工具
**功能：** 将多张图片转换为GIF动画（不支持透明背景PNG序列）
**参数：** `--source` `--output` `--duration` `--loop`

---

### `gif_2_frames.py` - GIF分解工具
**功能：** 将GIF分解为单独图片帧
**输入：** 支持单个 GIF 文件或包含 GIF 文件的文件夹
**参数：** `--source` `--output`

---

## 视频处理工具（video/）

### `images_2_video.py` - 图片转视频工具
**功能：** 图片序列合成视频，支持交叉淡入淡出效果
**参数：** `--source` `--output` `--resolution` `--duration` `--transition` `--fps`
**依赖：** 需要 ffmpeg

---

### `wechat_article_video_dl.py` - 微信公众号文章视频下载工具
**功能：** 下载微信公众号文章正文内嵌的视频（mpvideo 类型，即 `wxv_*`），按文章顺序以视频标题命名落盘
**输入：** 微信公众号文章 URL
**输出：** 默认 `PATH_DOWNLOADS/WeChatVideos`
**参数：** `--source` `--output` `--quality`（best/all）`--list`
**依赖：** 系统 `curl`
**说明：**
- 同一视频含多档清晰度，`--quality best` 取最高清，`all` 取全部
- `--list`（等价于 `--dry-run`）只列出视频与清晰度，不下载
- 视频号视频（`export_id` 形式）不支持，需登录链路，脚本会显式提示并跳过

---

## 附录

### 工具链关系

```
脚本（业务逻辑）
    ↓
utils（核心函数库：path, basic, image, video）
    ↓
基础依赖（FFmpeg、curl、Pillow等）
```

### 外部依赖

- **FFmpeg**：convertor.py（音频/视频/视频转GIF）和 images_2_video.py 需要 ffmpeg 命令行工具
- **curl**：wechat_article_video_dl.py 需要系统 curl（macOS/Linux/Win10 1803+ 自带）
- **OpenCV**：avatar_cropper.py 需要 opencv-python（pip安装，约40MB，可选）

### 跨平台支持

所有脚本支持以下平台：
- Windows
- WSL (Windows Subsystem for Linux)
- Linux
- macOS
