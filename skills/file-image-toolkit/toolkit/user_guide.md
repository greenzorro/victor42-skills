# Toolkit AI使用手册

本手册面向AI助手，说明 toolkit 中所有脚本的功能和用途，便于AI作为工具执行具体任务。

## 项目概述

`toolkit` 是日常开发的文件与图像处理工具集，提供文件管理、数据转换、图像处理、视频合成等工具。所有脚本均支持命令行参数调用，可被AI直接执行。

**核心特性：**
- 🤖 **AI友好**：所有脚本支持命令行参数，适合AI调用
- 🔄 **双模式**：命令行模式（主要）+ 交互模式（备用）
- 📦 **模块化**：核心功能封装在utils库中
- 🌐 **跨平台**：支持Windows/WSL/Linux/macOS

## 目录结构

```
toolkit/
├── 根目录脚本/      - 文件管理、数据转换
├── image/          - 图像处理工具集
├── video/          - 视频处理工具集
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

**支持的格式转换：**

**图片格式转换（支持任意互转）：**
- 源格式：jpg, jpeg, png, bmp, gif, tiff, webp, avif
- 目标格式：上述格式任意互转

**音频格式转换：**
- 源格式：mp3, wav, flac, aac, ogg, m4a, opus
- 目标格式：mp3, wav, flac, aac, ogg, m4a, opus

**视频格式转换：**
- 源格式：mp4, avi, wmv, mov, flv, m4a, mkv, webm, m4v
- 目标格式：mp4, mov, m4v, mkv, avi, webm, flv, wmv
- 视频转音频：可转换为 mp3, wav, flac, aac, ogg, m4a, opus

---

### 文件管理工具

#### `folder_ungroup.py` - 文件夹解组工具
**功能：** 将嵌套文件夹中的所有文件提取到单一文件夹中

---

#### `rename_by_csv.py` - CSV批量重命名工具
**功能：** 根据CSV文件中的映射关系批量重命名文件
**CSV文件格式：** 必须包含 `name` 列，源文件名需要包含数字序号

---

## 图像处理工具（image/）

### `resizer.py` - 图片尺寸调整工具
**功能：** 智能调整图片尺寸，支持裁剪和留白模式
**输入：** 支持单张图片或图片文件夹

---

### `scaler.py` - 图片比例缩放工具
**功能：** 按比例缩放图片，限制在指定尺寸内
**输入：** 支持单张图片或图片文件夹

---

### `avatar_cropper.py` - 批量头像裁剪工具
**功能：** 批量将包含人脸的照片裁剪为指定尺寸的头像（支持圆形或方形）
**输入：** 支持单张图片或图片文件夹

---

### `dedup.py` - 智能图片去重工具
**功能：** 自动识别文件夹中的相似图片（包括缩放变体和裁剪变体），并保留分辨率最高的一个版本。

---

### `frames_2_gif.py` - GIF合成工具
**功能：** 将多张图片转换为GIF动画（不支持透明背景PNG序列）

---

### `gif_2_frames.py` - GIF分解工具
**功能：** 将GIF分解为单独图片帧
**输入：** 支持单个 GIF 文件或包含 GIF 文件的文件夹

---

## 视频处理工具（video/）

### `images_2_video.py` - 图片转视频工具
**功能：** 图片序列合成视频，支持交叉淡入淡出效果

---

## 附录

### 工具链关系

```
脚本（业务逻辑）
    ↓
utils（核心函数库：path, basic, image, video）
    ↓
基础依赖（FFmpeg、Pillow等）
```

### 外部依赖

- **FFmpeg**：convertor.py 和 images_2_video.py 需要 ffmpeg 命令行工具
- **OpenCV**：avatar_cropper.py 需要 opencv-python（pip安装）

### 跨平台支持

所有脚本支持以下平台：
- Windows
- WSL (Windows Subsystem for Linux)
- Linux
- macOS