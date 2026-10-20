"""
File: image.py
Project: toolkit
Author: Victor Cheng
Email: hi@victor42.work
Description: 图像处理函数（裁剪、缩放、指纹、去重、GIF 转换）
"""

import os
import shutil
import numpy as np
import imagehash
from PIL import Image
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field
from .basic import extract_number_from_filename


SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff"}


def validate_image_file(image_path: str) -> bool:
    """验证图片文件是否有效

    Args:
        image_path: 图片文件路径

    Returns:
        bool: 验证是否通过

    Raises:
        ValueError: 不支持的图片格式
        FileNotFoundError: 图片文件不存在
        IOError: 图片文件损坏或无法读取
    """
    # 检查文件扩展名
    ext = Path(image_path).suffix.lower()
    if ext not in SUPPORTED_IMAGE_FORMATS:
        raise ValueError(
            f"不支持的图片格式: {ext}。支持的格式: {SUPPORTED_IMAGE_FORMATS}"
        )

    # 检查文件是否存在
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"图片文件不存在: {image_path}")

    # 验证图片完整性
    try:
        with Image.open(image_path) as img:
            img.verify()
    except Exception as e:
        raise IOError(f"图片文件损坏或无法读取 {image_path}: {str(e)}")

    return True


def validate_images(image_files: List[str]):
    """验证所有图片文件

    Args:
        image_files: 图片文件路径列表

    Raises:
        ValueError: 图片验证失败或数量不足
    """
    print("正在验证图片文件...")

    if len(image_files) < 2:
        raise ValueError("至少需要2张图片才能创建过渡效果")

    for i, image_path in enumerate(image_files):
        print(f"正在验证图片 {i + 1}/{len(image_files)}: {Path(image_path).name}")
        validate_image_file(image_path)

    print("所有图片验证通过")


def get_sorted_image_files(
    images_folder: str, supported_formats: set = None
) -> List[str]:
    """获取图片文件夹中按数字排序的图片文件

    Args:
        images_folder: 图片文件夹路径
        supported_formats: 支持的图片格式集合，默认使用SUPPORTED_IMAGE_FORMATS

    Returns:
        List[str]: 排序后的图片文件路径列表

    Raises:
        ValueError: 没有找到支持的图片文件
    """
    if supported_formats is None:
        supported_formats = SUPPORTED_IMAGE_FORMATS

    print(f"正在扫描图片文件夹: {images_folder}")

    image_files = []
    for filename in os.listdir(images_folder):
        filepath = os.path.join(images_folder, filename)
        if os.path.isfile(filepath):
            ext = Path(filepath).suffix.lower()
            if ext in supported_formats:
                image_files.append(filepath)

    if not image_files:
        raise ValueError(
            f"图片文件夹中没有找到支持的图片文件。支持的格式: {supported_formats}"
        )

    # 按数字大小排序，确保1<2<11，数字相同的按文件名自然排序
    image_files.sort(
        key=lambda x: (extract_number_from_filename(Path(x).name), Path(x).name)
    )

    # 打印排序后的文件名
    print(f"找到 {len(image_files)} 张图片，按数字排序:")
    for i, filepath in enumerate(image_files):
        filename = Path(filepath).name
        number = extract_number_from_filename(filename)
        print(f"  {i + 1}. {filename} (数字: {number})")

    return image_files


def resize_image(
    src_path,
    dst_path,
    target_width,
    target_height,
    mode: str = "crop",
    background_color: str = "white",
):
    """把不同比例图片统一成特定尺寸

    :param str src_path: 源图片路径
    :param str dst_path: 目标图片路径
    :param int target_width: 目标宽度
    :param int target_height: 目标高度
    :param str mode: 模式，'crop'-裁剪，'pad'-留白
    :param str background_color: pad模式的背景色（默认："white"），支持颜色名称或十六进制
    """
    # 参数验证
    if target_width <= 0 or target_height <= 0:
        raise ValueError(
            f"目标宽度和高度必须大于0，当前值: width={target_width}, height={target_height}"
        )
    if mode not in ["crop", "pad"]:
        raise ValueError(f"模式必须是 'crop' 或 'pad'，当前值: {mode}")

    try:
        image = Image.open(src_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"源图片未找到: {src_path}")
    except Exception as e:
        raise IOError(f"打开图片时出错 {src_path}: {e}")

    # 检查是否为GIF动图
    is_animated_gif = False
    # 特殊处理MPO格式 - 强制作为静态图片处理
    if image.format != "MPO":
        try:
            is_animated_gif = hasattr(image, "n_frames") and image.n_frames > 1
        except Exception:
            pass

    # 如果是动画GIF，进行特殊处理
    if is_animated_gif:
        # 逐帧处理
        frames = []
        durations = []

        # 获取GIF的循环信息（如果有）
        loop_info = image.info.get("loop", 0)

        for i in range(image.n_frames):
            image.seek(i)
            frame = image.copy()
            width, height = frame.size

            # 计算原始和目标的长宽比
            ratio = width / height
            target_ratio = target_width / target_height

            # 根据不同的模式进行缩放和裁剪或留白
            if mode == "crop":
                # 裁剪模式
                if ratio > target_ratio:
                    # 原图过宽，先按照高度缩放，再裁剪左右两边多余部分
                    new_width = int(target_height * ratio)
                    new_frame = frame.resize((new_width, target_height))
                    left = (new_width - target_width) // 2
                    right = left + target_width
                    new_frame = new_frame.crop((left, 0, right, target_height))
                else:
                    # 原图过窄，先按照宽度缩放，再裁剪上下两边多余部分
                    new_height = int(target_width / ratio)
                    new_frame = frame.resize((target_width, new_height))
                    top = (new_height - target_height) // 2
                    bottom = top + target_height
                    new_frame = new_frame.crop((0, top, target_width, bottom))

            elif mode == "pad":
                # 留白模式
                if ratio > target_ratio:
                    # 原图过宽，先按照宽度缩放，再在上下两边填充背景
                    new_height = int(target_width / ratio)
                    new_frame = frame.resize((target_width, new_height))
                    bg_color = background_color
                    background = Image.new(
                        "RGB", (target_width, target_height), bg_color
                    )

                    # 将新图片粘贴到背景中间位置
                    top = (target_height - new_height) // 2
                    background.paste(new_frame, (0, top))
                    new_frame = background

                else:
                    # 原图过窄 ，先按照高度缩放 ，再在左右两边填充背景
                    new_width = int(target_height * ratio)
                    new_frame = frame.resize((new_width, target_height))
                    bg_color = background_color
                    background = Image.new(
                        "RGB", (target_width, target_height), bg_color
                    )

                    # 将新图片粘贴到背景中间位置
                    left = (target_width - new_width) // 2
                    background.paste(new_frame, (left, 0))
                    new_frame = background

            frames.append(new_frame)
            # 获取当前帧的持续时间
            durations.append(image.info.get("duration", 100))

        # 保存为GIF动画
        if frames:
            # 确保目标文件扩展名是.gif
            if not dst_path.lower().endswith(".gif"):
                dst_path = os.path.splitext(dst_path)[0] + ".gif"

            frames[0].save(
                dst_path,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                duration=durations,
                loop=loop_info,
                optimize=False,
                disposal=2,
            )
            return

    width, height = image.size

    # 计算原始和目标的长宽比
    ratio = width / height
    target_ratio = target_width / target_height

    # 根据不同的模式进行缩放和裁剪或留白
    if mode == "crop":
        # 裁剪模式
        if ratio > target_ratio:
            # 原图过宽，先按照高度缩放，再裁剪左右两边多余部分
            new_width = int(target_height * ratio)
            new_image = image.resize((new_width, target_height))
            left = (new_width - target_width) // 2
            right = left + target_width
            new_image = new_image.crop((left, 0, right, target_height))
        else:
            # 原图过窄，先按照宽度缩放，再裁剪上下两边多余部分
            new_height = int(target_width / ratio)
            new_image = image.resize((target_width, new_height))
            top = (new_height - target_height) // 2
            bottom = top + target_height
            new_image = new_image.crop((0, top, target_width, bottom))

    elif mode == "pad":
        # 留白模式
        if ratio > target_ratio:
            # 原图过宽，先按照宽度缩放，再在上下两边填充背景
            new_height = int(target_width / ratio)
            new_image = image.resize((target_width, new_height))
            bg_color = background_color
            background = Image.new("RGB", (target_width, target_height), bg_color)

            # 将新图片粘贴到背景中间位置
            top = (target_height - new_height) // 2
            background.paste(new_image, (0, top))
            new_image = background

        else:
            # 原图过窄 ，先按照高度缩放 ，再在左右两边填充背景
            new_width = int(target_height * ratio)
            new_image = image.resize((new_width, target_height))
            bg_color = background_color
            background = Image.new("RGB", (target_width, target_height), bg_color)

            # 将新图片粘贴到背景中间位置
            left = (target_width - new_width) // 2
            background.paste(new_image, (left, 0))
            new_image = background

    # 输出文件
    new_image.save(dst_path)


def scale_image(src_path, dst_path, max_size, min_width, mode: str = "long"):
    """等比缩放图片，根据模式选择缩放长边或短边

    :param str src_path: 源图片路径
    :param str dst_path: 目标图片路径
    :param int max_size: 最大尺寸值
    :param int min_width: 长图的最小宽度（仅对纵向图片生效）
    :param str mode: 模式，'long'-长边缩放到最大值，'short'-短边缩放到最大值
    """
    # 参数验证
    if max_size <= 0:
        raise ValueError(f"最大尺寸必须大于0，当前值: {max_size}")
    if min_width < 0:
        raise ValueError(f"最小宽度不能小于0，当前值: {min_width}")
    if mode not in ["long", "short"]:
        raise ValueError(f"模式必须是 'long' 或 'short'，当前值: {mode}")

    try:
        image = Image.open(src_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"源图片未找到: {src_path}")
    except Exception as e:
        raise IOError(f"打开图片时出错 {src_path}: {e}")

    width, height = image.size

    # 特殊处理MPO格式 - 强制作为静态图片处理
    if image.format == "MPO":
        is_animated_gif = False
        # 防止除零错误
        if width <= 0 or height <= 0:
            raise ValueError(f"图片尺寸无效: width={width}, height={height}")

        # 确定长边和短边
        long_side = max(width, height)
        short_side = min(width, height)
    else:
        # 防止除零错误
        if width <= 0 or height <= 0:
            raise ValueError(f"图片尺寸无效: width={width}, height={height}")

        # 确定长边和短边
        long_side = max(width, height)
        short_side = min(width, height)

        # 检查是否为GIF动图
        is_animated_gif = False
        try:
            is_animated_gif = hasattr(image, "n_frames") and image.n_frames > 1
        except Exception:
            pass

    # 如果是动画GIF，检查是否需要处理
    if is_animated_gif:
        # 检查是否需要处理
        needs_processing = False

        # 模式long：只有长边大于max_size才需要处理
        if mode == "long":
            if long_side > max_size:
                needs_processing = True
            else:
                # 检查是否所有帧都不需要处理
                try:
                    for i in range(image.n_frames):
                        image.seek(i)
                        frame_width, frame_height = image.size
                        frame_long_side = max(frame_width, frame_height)
                        if frame_long_side > max_size:
                            needs_processing = True
                            break
                        # 检查是否需要调整最小宽度（仅对纵向图片）
                        if frame_height > frame_width and frame_width < min_width:
                            needs_processing = True
                            break
                except Exception:
                    needs_processing = True  # 如果检查失败，保守处理
        else:
            # 模式short：总是需要处理
            needs_processing = True

        if not needs_processing:
            # 直接复制原文件，避免不必要的重编码
            try:
                shutil.copy2(src_path, dst_path)
                # 验证文件是否成功复制
                if not os.path.exists(dst_path):
                    raise FileNotFoundError(f"复制文件失败: {dst_path}")
            except Exception as e:
                raise IOError(f"复制文件时出错 {src_path} -> {dst_path}: {e}")
            return

    # 如果是动画GIF，进行特殊处理
    if is_animated_gif:
        # 逐帧处理
        frames = []
        durations = []

        # 获取GIF的循环信息（如果有）
        loop_info = image.info.get("loop", 0)

        for i in range(image.n_frames):
            image.seek(i)
            frame = image.copy()
            width, height = frame.size

            # 防止除零错误
            if width <= 0 or height <= 0:
                raise ValueError(f"图片尺寸无效: width={width}, height={height}")

            # 确定长边和短边
            long_side = max(width, height)
            short_side = min(width, height)

            # 根据不同模式计算缩放比例
            if mode == "long":
                # 模式long：长边缩放到最大值
                if long_side > max_size:
                    ratio = max_size / long_side
                    new_width = int(width * ratio)
                    new_height = int(height * ratio)

                    # 仅对纵向图片检查最小宽度
                    if height > width and new_width < min_width:
                        # 调整缩放后的宽度和高度（保持原比例）
                        new_width = min_width
                        new_height = int(min_width / width * height)

                    # 缩放图片
                    new_frame = frame.resize((new_width, new_height))
                else:
                    new_frame = frame

            elif mode == "short":
                # 模式short：短边缩放到最大值
                if short_side > max_size:
                    ratio = max_size / short_side
                    new_width = int(width * ratio)
                    new_height = int(height * ratio)
                else:
                    # 如果短边小于最大值，则放大到最大值
                    ratio = max_size / short_side
                    new_width = int(width * ratio)
                    new_height = int(height * ratio)

                # 仅对纵向图片检查最小宽度
                if height > width and new_width < min_width:
                    # 调整缩放后的宽度和高度（保持原比例）
                    new_width = min_width
                    new_height = int(min_width / width * height)

                # 缩放图片
                new_frame = frame.resize((new_width, new_height))
            else:
                new_frame = frame

            frames.append(new_frame)
            # 获取当前帧的持续时间
            durations.append(image.info.get("duration", 100))

        # 保存为GIF动画
        if frames:
            # 确保目标文件扩展名是.gif
            if not dst_path.lower().endswith(".gif"):
                dst_path = os.path.splitext(dst_path)[0] + ".gif"

            frames[0].save(
                dst_path,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                duration=durations,
                loop=loop_info,
                optimize=False,
                disposal=2,
            )
            return

    # 静态图片处理逻辑
    # 检查是否需要处理（模式long且长边不超过最大值，且不违反最小宽度要求）
    if mode == "long" and long_side <= max_size:
        if not (height > width and width < min_width):
            # 不需要处理，直接复制原文件到目标路径
            try:
                shutil.copy2(src_path, dst_path)
                # 验证文件是否成功复制
                if not os.path.exists(dst_path):
                    raise FileNotFoundError(f"复制文件失败: {dst_path}")
            except Exception as e:
                raise IOError(f"复制文件时出错 {src_path} -> {dst_path}: {e}")
            return

    # 根据不同模式计算缩放比例
    if mode == "long":
        # 模式long：长边缩放到最大值
        if long_side > max_size:
            ratio = max_size / long_side
            new_width = int(width * ratio)
            new_height = int(height * ratio)

            # 仅对纵向图片检查最小宽度
            if height > width and new_width < min_width:
                # 调整缩放后的宽度和高度（保持原比例）
                new_width = min_width
                new_height = int(min_width / width * height)

            # 缩放图片
            image = image.resize((new_width, new_height))

    elif mode == "short":
        # 模式short：短边缩放到最大值
        if short_side > max_size:
            ratio = max_size / short_side
            new_width = int(width * ratio)
            new_height = int(height * ratio)
        else:
            # 如果短边小于最大值，则放大到最大值
            ratio = max_size / short_side
            new_width = int(width * ratio)
            new_height = int(height * ratio)

        # 仅对纵向图片检查最小宽度
        if height > width and new_width < min_width:
            # 调整缩放后的宽度和高度（保持原比例）
            new_width = min_width
            new_height = int(min_width / width * height)

        # 缩放图片
        image = image.resize((new_width, new_height))

    # 输出文件，明确指定格式
    file_ext = os.path.splitext(dst_path)[1].lower()

    try:
        # 确保图像转换为RGB模式（对于JPEG格式）
        if image.mode != "RGB":
            image = image.convert("RGB")

        if file_ext == ".jpg" or file_ext == ".jpeg":
            image.save(dst_path, format="JPEG", quality=95)
        elif file_ext == ".png":
            image.save(dst_path, format="PNG")
        elif file_ext == ".webp":
            image.save(dst_path, format="WEBP", quality=95)
        else:
            # 默认JPEG格式
            image.save(dst_path, format="JPEG", quality=95)

    except Exception as save_error:
        raise save_error


def gif_2_frames(src_path, dst_path):
    """将GIF转换为帧图片

    :param str src_path: 源GIF文件或文件夹路径
    :param str dst_path: 目标帧图片文件夹路径
    """
    if os.path.isfile(src_path):
        gif_files = [src_path] if src_path.lower().endswith(".gif") else []
    else:
        gif_files = []
        for filename in os.listdir(src_path):
            if filename.startswith("."):
                continue
            gif_path = os.path.join(src_path, filename)
            if filename.lower().endswith(".gif"):
                gif_files.append(gif_path)

    gif_count = len(gif_files)

    for gif_path in sorted(gif_files):
        filename = os.path.basename(gif_path)
        image = Image.open(gif_path)
        frames = image.n_frames

        if gif_count > 1:
            frame_path = os.path.join(dst_path, os.path.splitext(filename)[0])
        else:
            frame_path = dst_path
        os.makedirs(frame_path, exist_ok=True)

        for i in range(frames):
            image.seek(i)
            frame_file_path = os.path.join(
                frame_path, f"{os.path.splitext(filename)[0]}_{i}.png"
            )
            image.save(frame_file_path)

        if os.path.exists(frame_path):
            print(f"{gif_path} converted")
        else:
            print(f"Failed to convert {gif_path}")


def frames_2_gif(src_path, dst_path, duration=100, loop=1):
    """将帧图片转换为GIF

    :param str src_path: 源帧图片文件夹路径
    :param str dst_path: 目标GIF文件夹路径
    :param int duration: 帧间隔时间（毫秒）
    :param int loop: 是否循环播放（1为是，0为否）
    """
    # 遍历输入文件夹中的图片
    images = []
    for filename in os.listdir(src_path):
        # 忽略隐藏文件和文件夹
        if filename.startswith("."):
            continue
        src_format = (os.path.splitext(filename)[1])[1:]
        if src_format in ["jpg", "jpeg", "png", "bmp"]:
            # 打开图片并获取动画帧
            frame_path = os.path.join(src_path, filename)
            try:
                image = Image.open(frame_path)
                images.append(image)
            except Exception as e:
                print(f"Failed to open {frame_path}: {e}")

    # 按文件名数字顺序排列
    images.sort(key=lambda x: extract_number_from_filename(x.filename))

    # 检查图片尺寸是否一致
    size_set = set([img.size for img in images])
    if len(size_set) > 1:
        print("Error: Images have different sizes")
        return

    # 检查是否有图片被加载
    if not images:
        print("Error: No images found in the source directory")
        return

    # 拼合图片序列成gif动画
    duration = int(duration)
    loop = int(loop)
    images[0].save(
        os.path.join(dst_path, "output.gif"),
        save_all=True,
        optimize=False,
        compress_level=0,
        append_images=images[1:],
        duration=duration,
        loop=loop,
    )

    # 打印输出结果
    gif_path = os.path.join(dst_path, "output.gif")
    if os.path.exists(gif_path):
        print(f"{src_path} converted to gif")
    else:
        print(f"Failed to convert {src_path}")


@dataclass
class ImageFingerprint:
    """存储单个图片的指纹和元数据。"""

    path: Path
    size_bytes: int
    width: int
    height: int
    phash: str
    dhash: str
    color_hist: np.ndarray = field(default=None, repr=False)

    @property
    def pixels(self) -> int:
        return self.width * self.height

    @property
    def resolution_str(self) -> str:
        return f"{self.width}×{self.height}"


def calculate_color_histogram(img: Image.Image, bins: int = 16) -> np.ndarray:
    """计算归一化的颜色直方图。"""
    img_array = np.array(img)
    # 处理 2 维数组（灰度图）或 4 维（带 Alpha）
    if len(img_array.shape) == 2:
        img_array = np.stack([img_array] * 3, axis=-1)
    elif len(img_array.shape) == 3 and img_array.shape[2] > 3:
        img_array = img_array[:, :, :3]

    hist = []
    for i in range(3):  # R, G, B 通道
        h, _ = np.histogram(img_array[:, :, i], bins=bins, range=(0, 256))
        hist.extend(h)
    hist = np.array(hist, dtype=np.float32)
    hist = hist / (hist.sum() + 1e-6)  # 归一化
    return hist


def get_image_fingerprint(
    image_path: str, hash_size: int = 16
) -> Optional[ImageFingerprint]:
    """获取图片的视觉指纹（Hash + Histogram）及元数据。"""
    try:
        # 使用统一函数进行验证（格式支持、存在性、完整性）
        validate_image_file(image_path)
        
        path = Path(image_path)
        with Image.open(path) as img:
            # 如有必要，转换为 RGB
            if img.mode not in ("RGB",):
                img = img.convert("RGB")

            width, height = img.size
            # 计算哈希
            phash = str(imagehash.phash(img, hash_size=hash_size))
            dhash = str(imagehash.dhash(img, hash_size=hash_size))
            # 计算颜色直方图
            color_hist = calculate_color_histogram(img)

            return ImageFingerprint(
                path=path,
                size_bytes=path.stat().st_size,
                width=width,
                height=height,
                phash=phash,
                dhash=dhash,
                color_hist=color_hist,
            )
    except Exception as e:
        print(f"  [ERROR] 无法处理图片 {image_path}: {e}")
        return None


def hamming_distance(hash1: str, hash2: str) -> int:
    """计算两个哈希之间的汉明距离。"""
    if len(hash1) != len(hash2):
        return float("inf")
    return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))


def histogram_similarity(hist1: np.ndarray, hist2: np.ndarray) -> float:
    """计算直方图相交相似度 (0-1)。"""
    return np.minimum(hist1, hist2).sum()


def find_similar_image_groups(
    images: List[ImageFingerprint], threshold: int = 6, crop_similarity: float = 0.85
) -> List[List[ImageFingerprint]]:
    """
    使用严格簇匹配对相似图片进行分组：
    1. 不再使用并查集（防止 A像B, B像C 导致 A,B,C 链式归为一组）
    2. 每张图作为簇心，寻找与其极度接近的”副本”
    """
    n = len(images)
    processed = [False] * n
    groups = []

    # 预先按分辨率降序排列，保证簇心是最高质量的那张
    sorted_indices = sorted(range(n), key=lambda i: (images[i].pixels, images[i].size_bytes), reverse=True)

    for i in sorted_indices:
        if processed[i]:
            continue

        current_group = [images[i]]
        processed[i] = True

        for j in sorted_indices:
            if processed[j]:
                continue

            # 第一阶段：Hash 严格匹配
            phash_dist = hamming_distance(images[i].phash, images[j].phash)
            dhash_dist = hamming_distance(images[i].dhash, images[j].dhash)

            # 第二阶段：直方图严格匹配
            sim = histogram_similarity(images[i].color_hist, images[j].color_hist)

            # 必须同时满足 Hash 相似且直方图极高相似，才判定为”同一张图的副本”
            # 或者 Hash 极度接近 (距离 <= 2)
            is_duplicate = (
                (phash_dist <= threshold and dhash_dist <= threshold and sim >= crop_similarity) or
                (phash_dist <= 2 or dhash_dist <= 2)
            )

            if is_duplicate:
                current_group.append(images[j])
                processed[j] = True

        if len(current_group) > 1:
            groups.append(current_group)

    return groups


def detect_faces(image_path: str, min_face_size: int = 100) -> Optional[tuple]:
    """
    使用 OpenCV Haar Cascade 检测图片中的人脸

    Args:
        image_path: 图片文件路径
        min_face_size: 最小人脸尺寸（默认100）

    Returns:
        Optional[tuple]: (center_x, center_y, radius) 如果检测到人脸
                        None 如果未检测到人脸或加载失败
    """
    try:
        import cv2
    except ImportError:
        print("[ERROR] 需要安装 opencv-python: pip install opencv-python")
        return None

    # 直接读取图片（支持中文路径）
    img_cv = cv2.imread(image_path)
    if img_cv is None:
        print(f"[ERROR] 无法读取图片: {image_path}")
        return None

    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # 加载人脸识别模型
    face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(face_cascade_path)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(min_face_size, min_face_size)
    )

    h_orig, w_orig = img_cv.shape[:2]

    if len(faces) == 0:
        # 未检测到人脸，返回中心裁剪
        center_x = w_orig // 2
        center_y = h_orig // 2
        radius = min(w_orig, h_orig) // 2
    else:
        # 取最大的人脸
        faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        x, y, w_face, h_face = faces[0]

        center_x = x + w_face // 2
        center_y = y + h_face // 2

        # 人脸高度占圆直径的比例，约 55%
        radius = int(h_face / 1.1)

        # 稍微下移中心点（即裁剪框上移），保留头发部分
        center_y += int(h_face * 0.05)

        # 如果裁剪框超出了顶部边界，则向下偏移以尽量保留头发
        if center_y - radius < 0:
            center_y = radius

    # 确保返回 Python int 类型（而不是 numpy.int32）
    return (int(center_x), int(center_y), int(radius))
