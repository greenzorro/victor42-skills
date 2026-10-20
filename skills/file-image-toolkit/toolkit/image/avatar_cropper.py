"""
File: avatar_cropper.py
Project: toolkit
Created: 2026-03-23
Author: Victor Cheng
Email: hi@victor42.work
Description: 批量将包含人脸的照片裁剪为指定尺寸的头像（支持圆形或方形）
"""

import os
import argparse
import sys

current_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.dirname(current_dir))

from utils.image import detect_faces, SUPPORTED_IMAGE_FORMATS
from utils.basic import get_param_value, get_source_files
from utils.path import get_platform, PATH_DOWNLOADS_FROM_WIN, PATH_DOWNLOADS

# 导入额外需要的库（人脸检测需要）
import cv2
from PIL import Image, ImageDraw

def process_avatar(input_path, output_path, shape='circle', size=500, padding=1.0):
    # 使用 cv2 直接读取图片（支持中文路径）
    img_cv = cv2.imread(input_path)

    if img_cv is None:
        print(f"无法读取图片: {input_path}")
        return False

    # 使用 utils 中的人脸检测函数
    face_result = detect_faces(input_path, min_face_size=100)
    if not face_result:
        print(f"人脸检测失败: {input_path}")
        return False

    center_x, center_y, face_radius = face_result
    # 应用 padding 扩展比例
    radius = int(face_radius * padding)
    h_orig, w_orig = img_cv.shape[:2]

    # 计算理想的裁剪区域
    left = int(center_x - radius)
    top = int(center_y - radius)
    right = int(center_x + radius)
    bottom = int(center_y + radius)

    # 自动调整边界，确保裁剪区域不超出图片（优先级高于 padding）
    # 计算可用的最大半径（到最近边界的距离）
    max_radius_left = min(center_x, center_y)
    max_radius_right = min(w_orig - center_x, h_orig - center_y)
    max_available_radius = min(max_radius_left, max_radius_right)

    # 如果计算出的 radius 会超出边界，使用最大可用半径
    if radius > max_available_radius:
        radius = max_available_radius
        # 重新计算裁剪区域
        left = int(center_x - radius)
        top = int(center_y - radius)
        right = int(center_x + radius)
        bottom = int(center_y + radius)

    # 将 cv2 图像转换为 PIL 格式（避免重复加载）
    img_pil = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGBA))

    # 建立带透明通道的画布
    processed = Image.new("RGBA", (radius * 2, radius * 2), (0, 0, 0, 0))

    src_left = max(0, left)
    src_top = max(0, top)
    src_right = min(w_orig, right)
    src_bottom = min(h_orig, bottom)

    if src_left < src_right and src_top < src_bottom:
        dst_left = src_left - left
        dst_top = src_top - top
        cropped_part = img_pil.crop((src_left, src_top, src_right, src_bottom))
        processed.paste(cropped_part, (dst_left, dst_top))

    # 缩放到目标尺寸
    processed = processed.resize((size, size), Image.Resampling.LANCZOS)
    
    if shape == 'circle':
        # 制作圆形遮罩
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        
        final = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        final.paste(processed, (0, 0), mask=mask)
        
        final.save(output_path, "PNG")
    else:  # square
        # 对于方形，如果原本边缘存在透明填充，底层我们给它铺成白色
        final = Image.new("RGB", (size, size), (255, 255, 255))
        final.paste(processed, (0, 0), mask=processed)
        final.save(output_path, "JPEG", quality=95)
        
    print(f"成功保存: {os.path.basename(output_path)}")
    return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="批量将包含人脸的照片裁剪为指定尺寸的头像"
    )
    parser.add_argument("-s", "--source", help="源图片文件或文件夹路径（必填）")
    parser.add_argument("-o", "--output", help="输出文件夹路径（可选，默认：Avatars）")
    parser.add_argument("--shape", choices=['circle', 'square'], help="头像形状")
    parser.add_argument("--size", type=int, help="输出尺寸（默认500）")
    parser.add_argument("--padding", type=float, help="裁剪扩展比例（默认1.0，1.5=宽松头像，2.0=全身照）")

    args = parser.parse_args()

    # 使用 utils 的 get_param_value 统一参数处理
    source = get_param_value(
        args, 'source',
        prompt_text="请输入源图片文件或目录路径"
    )

    # 计算默认输出路径（与其他脚本保持一致，默认到下载目录）
    platform_type = get_platform()
    if platform_type == "wsl":
        default_output = os.path.join(PATH_DOWNLOADS_FROM_WIN, "avatars")
    else:
        default_output = os.path.join(PATH_DOWNLOADS, "avatars")

    output = get_param_value(
        args, 'output',
        script_default=default_output,
        prompt_text=f"请输入输出目录路径 [默认: {default_output}]"
    )

    shape = get_param_value(
        args, 'shape',
        script_default='circle',
        prompt_text="请选择头像形状 (circle/square) [默认: circle]"
    )

    size = get_param_value(
        args, 'size',
        script_default=500
    )

    padding = get_param_value(
        args, 'padding',
        script_default=1.0
    )

    if not os.path.exists(source):
        print(f"错误：源路径不存在 {source}")
        return

    os.makedirs(output, exist_ok=True)

    # 使用 utils 的 SUPPORTED_IMAGE_FORMATS 常量（转换为 tuple）
    valid_exts = tuple(SUPPORTED_IMAGE_FORMATS)
    processed_count = 0

    for input_path in get_source_files(source, allowed_extensions=valid_exts):
        filename = os.path.basename(input_path)
        ext = ".png" if shape == 'circle' else ".jpg"
        output_filename = os.path.splitext(filename)[0] + ext
        output_path = os.path.join(output, output_filename)

        if input_path == output_path:
            print(f"跳过相同文件: {filename}")
            continue

        if process_avatar(input_path, output_path, shape, size, padding):
            processed_count += 1

    print(f"\n处理完成！共处理了 {processed_count} 张图片。")
    print(f"输出目录: {output}")

if __name__ == "__main__":
    main()
