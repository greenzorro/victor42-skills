"""
File: resizer.py
Project: routine
Created: 2024-11-05 06:39:43
Author: Victor Cheng
Email: hi@victor42.work
Description: 将图片调整为指定宽高，支持裁剪和留白模式
"""

import os
import argparse
import sys

current_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.dirname(current_dir))

from utils.image import resize_image
from utils.basic import get_param_value, get_source_files
from utils.path import get_platform, PATH_DOWNLOADS_FROM_WIN, PATH_DOWNLOADS


def main():
    parser = argparse.ArgumentParser(
        description="将图片调整为指定宽高，支持裁剪和留白模式"
    )
    parser.add_argument("--source", "-s", help="源图片文件或文件夹路径（必填）")
    parser.add_argument(
        "--output", "-o", help="输出文件夹路径（可选，默认：Img_resized）"
    )
    parser.add_argument("--width", "-w", type=int, help="目标宽度（必填）")
    parser.add_argument("--height", "-H", type=int, help="目标高度（必填）")
    parser.add_argument(
        "--mode",
        "-m",
        choices=["crop", "pad"],
        help="模式：crop-裁剪，pad-留白（必填）",
    )
    parser.add_argument(
        "--bg-color",
        help="pad模式背景色（默认：white），支持颜色名称或十六进制（如 #FF0000）",
    )
    args = parser.parse_args()

    SRC_PATH = get_param_value(args, "source", prompt_text="源图片文件或文件夹路径")

    platform_type = get_platform()
    if platform_type == "wsl":
        default_output = os.path.join(PATH_DOWNLOADS_FROM_WIN, "Img_resized")
    else:
        default_output = os.path.join(PATH_DOWNLOADS, "Img_resized")

    DST_FOLDER = get_param_value(args, "output", script_default=default_output)

    target_width = int(get_param_value(args, "width", prompt_text="目标宽度"))
    target_height = int(get_param_value(args, "height", prompt_text="目标高度"))
    mode = get_param_value(args, "mode", prompt_text="模式（crop/pad）")
    bg_color = get_param_value(args, "bg_color", script_default="white")

    if not os.path.exists(SRC_PATH):
        print(f"错误：源路径不存在: {SRC_PATH}")
        sys.exit(1)

    if not os.path.exists(DST_FOLDER):
        os.makedirs(DST_FOLDER)

    for src_path in get_source_files(SRC_PATH, allowed_extensions=["jpg", "jpeg", "png", "bmp", "gif"]):
        filename = os.path.basename(src_path)
        dst_path = os.path.join(DST_FOLDER, filename)

        resize_image(src_path, dst_path, target_width, target_height, mode, bg_color)

        if os.path.exists(dst_path):
            print(f"{src_path} resized")
        else:
            print(f"Failed to resize {src_path}")


if __name__ == "__main__":
    main()
