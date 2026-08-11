"""
File: convertor.py
Project: routine
Created: 2025-11-01 10:24:26
Author: Victor Cheng
Email: hi@victor42.work
Description: 通用格式转换器
"""

import os
import sys
import argparse
from utils.basic import get_param_value, convert_format, get_source_files
from utils.path import platform_type, PATH_DOWNLOADS_FROM_WIN, PATH_DOWNLOADS


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="批量转换文件格式（支持图片、音频、视频）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # 添加参数
    parser.add_argument("--source", "-s", help="源文件或文件夹路径")
    parser.add_argument(
        "--output",
        "-o",
        help="输出文件夹路径（默认：PATH_DOWNLOADS/Converted）",
    )
    parser.add_argument("--format", "-f", help="目标格式（如：mp3, jpg, webp）")

    # 解析参数
    args = parser.parse_args()

    # 获取源路径（必填参数，无默认值时询问用户）
    SRC_PATH = get_param_value(args, "source", prompt_text="源文件或文件夹路径")

    # 验证源路径存在
    if not os.path.exists(SRC_PATH):
        print(f"错误：源路径不存在: {SRC_PATH}")
        sys.exit(1)

    # 获取目标文件夹路径（可选参数，有脚本默认值，不问用户）
    if platform_type == "wsl":
        default_output = os.path.join(PATH_DOWNLOADS_FROM_WIN, "Converted")
    else:
        default_output = os.path.join(PATH_DOWNLOADS, "Converted")
    DST_FOLDER = get_param_value(args, "output", script_default=default_output)

    # 确保目标目录存在
    if not os.path.exists(DST_FOLDER):
        os.makedirs(DST_FOLDER)

    # 获取目标文件格式（必填参数，无默认值时询问用户）
    DST_FORMAT = get_param_value(args, "format", prompt_text="目标格式")

    for src_path in get_source_files(SRC_PATH, recursive=True):
        filename = os.path.basename(src_path)
        dst_name = os.path.splitext(filename)[0] + "." + DST_FORMAT
        dst_path = os.path.join(DST_FOLDER, dst_name)
        convert_format(src_path, dst_path, DST_FORMAT)


if __name__ == "__main__":
    main()
