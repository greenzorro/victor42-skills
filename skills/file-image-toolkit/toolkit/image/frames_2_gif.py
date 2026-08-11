"""
File: frames_2_gif.py
Project: routine
Created: 2024-11-05 06:39:43
Author: Victor Cheng
Email: hi@victor42.work
Description: 将图片帧序列转换为GIF，不支持透明背景PNG序列
"""

import os
import sys
import argparse

current_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.dirname(current_dir))

from utils.image import frames_2_gif
from utils.basic import get_param_value
from utils.path import platform_type, PATH_DOWNLOADS_FROM_WIN, PATH_DOWNLOADS


def main():
    parser = argparse.ArgumentParser(
        description="将图片帧序列转换为GIF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--source", "-s", help="源文件夹路径（必填）")
    parser.add_argument(
        "--output",
        "-o",
        help="输出文件夹路径（可选，默认：PATH_DOWNLOADS/Converted_gif）",
    )
    parser.add_argument(
        "--duration",
        "-d",
        type=int,
        help="帧间隔时间（毫秒，默认：200）",
    )
    parser.add_argument(
        "--loop",
        "-l",
        type=int,
        help="是否循环播放（1为是，0为否，默认：0）",
    )

    args = parser.parse_args()

    SRC_FOLDER = get_param_value(args, "source", prompt_text="源文件夹路径")

    if platform_type == "wsl":
        default_output = os.path.join(PATH_DOWNLOADS_FROM_WIN, "Converted_gif")
    else:
        default_output = os.path.join(PATH_DOWNLOADS, "Converted_gif")
    DST_FOLDER = get_param_value(args, "output", script_default=default_output)

    duration = int(
        get_param_value(
            args, "duration", script_default=200, prompt_text="帧间隔时间（毫秒）"
        )
    )
    loop = int(
        get_param_value(
            args, "loop", script_default=0, prompt_text="是否循环播放（1为是，0为否）"
        )
    )

    if not os.path.exists(SRC_FOLDER):
        print(f"错误：源文件夹不存在: {SRC_FOLDER}")
        sys.exit(1)

    if not os.path.exists(DST_FOLDER):
        os.makedirs(DST_FOLDER)

    frames_2_gif(SRC_FOLDER, DST_FOLDER, duration=duration, loop=loop)
    print(f"GIF已生成并保存到:\n{DST_FOLDER}")


if __name__ == "__main__":
    main()
