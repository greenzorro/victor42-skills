"""
File: convertor.py
Project: toolkit
Created: 2025-11-01 10:24:26
Author: Victor Cheng
Email: hi@victor42.work
Description: 通用格式转换器
"""

import os
import sys
import argparse
from utils.basic import (
    get_param_value, convert_format, get_source_files,
    plan_flattened_destinations,
    IMAGE_FORMATS, AUDIO_FORMATS, VIDEO_FORMATS,
    VIDEO_CODEC_OPTIONS,
)
from utils.path import platform_type, PATH_DOWNLOADS_FROM_WIN, PATH_DOWNLOADS


def main():
    """主函数"""
    # 动态生成格式说明
    img = ', '.join(sorted(IMAGE_FORMATS))
    aud = ', '.join(sorted(AUDIO_FORMATS))
    vid_src = ', '.join(sorted(VIDEO_FORMATS))
    vid_dst = ', '.join(sorted(VIDEO_CODEC_OPTIONS))

    epilog = f"""\
支持的格式转换:
  图片 (互转):  {img}
  音频 (互转):  {aud}
  视频 (源):    {vid_src}
  视频 (目标):  {vid_dst}
  视频 → 音频:  视频源 → 上述音频格式
  视频 → GIF:   视频源 → gif (fps=15, 宽度480px)
"""

    parser = argparse.ArgumentParser(
        description="批量转换文件格式（支持图片、音频、视频）",
        epilog=epilog,
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
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="演练模式：只列出将要转换的文件，不创建目录或写入文件",
    )

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

    if args.dry_run:
        print("当前为 dry-run 演练模式，不会创建目录或写入文件")
    elif not os.path.exists(DST_FOLDER):
        os.makedirs(DST_FOLDER)

    # 获取目标文件格式（必填参数，无默认值时询问用户）
    DST_FORMAT = get_param_value(args, "format", prompt_text="目标格式")

    source_files = get_source_files(SRC_PATH, recursive=True)
    conversion_plan = plan_flattened_destinations(
        source_files,
        DST_FOLDER,
        dst_extension=DST_FORMAT,
    )
    for src_path, dst_path in conversion_plan:
        if args.dry_run:
            print(f"[dry-run] 将转换: {src_path} -> {dst_path}")
            continue
        convert_format(src_path, dst_path, DST_FORMAT)


if __name__ == "__main__":
    main()
