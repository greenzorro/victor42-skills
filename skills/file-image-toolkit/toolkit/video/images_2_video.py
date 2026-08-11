"""
File: images_2_video.py
Project: routine
Created: 2025-09-19 06:09:15
Author: Victor Cheng
Email: hi@victor42.work
Description: 将图片文件夹中的所有图片合成为带有交叉淡入淡出效果的视频。
"""

import os
import sys
import argparse

current_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.dirname(current_dir))

from utils.image import get_sorted_image_files, validate_images
from utils.video import build_ffmpeg_command, execute_ffmpeg_command
from utils.basic import get_param_value
from utils.path import platform_type, PATH_DOWNLOADS_FROM_WIN, PATH_DOWNLOADS


def create_video_from_images(
    images_folder: str,
    output_path: str,
    resolution: str,
    transition_duration: float,
    image_duration: float,
    fps: int,
) -> str:
    """
    将图片文件夹中的图片合成为带有交叉淡入淡出效果的视频

    Args:
        images_folder: 图片文件夹路径
        output_path: 输出视频路径
        resolution: 视频分辨率（如：1920x1080）
        transition_duration: 过渡时长（秒）
        image_duration: 每个画面时长（秒）
        fps: 视频帧率

    Returns:
        str: 生成的视频文件路径

    Raises:
        FileNotFoundError: 图片文件夹不存在
        ValueError: 图片验证失败或参数无效
        RuntimeError: FFmpeg执行失败
    """
    print(f"=== 图片视频合成业务脚本 ===")
    print(f"图片文件夹: {images_folder}")
    print(f"输出文件: {output_path}")
    print(f"分辨率: {resolution}")
    print(f"每个画面时长: {image_duration}秒")
    print(f"过渡时长: {transition_duration}秒")
    print(f"帧率: {fps}fps")
    print()

    # 验证输入文件夹
    if not os.path.exists(images_folder):
        raise FileNotFoundError(f"图片文件夹不存在: {images_folder}")

    # 获取并验证图片文件
    image_files = get_sorted_image_files(images_folder)
    validate_images(image_files)

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        print(f"📁 输出目录不存在，正在创建: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
        print(f"✅ 输出目录创建成功")

    # 生成FFmpeg命令
    command = build_ffmpeg_command(
        image_files,
        output_path,
        resolution,
        fps,
        transition_duration,
        image_duration,
    )

    # 执行FFmpeg命令
    execute_ffmpeg_command(command)

    # 计算视频信息
    total_duration = (
        len(image_files) * image_duration + (len(image_files) - 1) * transition_duration
    )
    print(f"\n✅ 视频生成成功!")
    print(f"输出文件: {output_path}")
    print(f"视频时长: {total_duration:.1f}秒")
    print(f"画面数量: {len(image_files)}张")

    return output_path


def main():
    """主函数 - 业务脚本入口"""
    parser = argparse.ArgumentParser(
        description="将图片文件夹中的所有图片合成为带有交叉淡入淡出效果的视频",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--source", "-s", help="图片文件夹路径（必填）")
    parser.add_argument(
        "--output", "-o", help="输出视频路径（可选，默认：PATH_DOWNLOADS/test.mp4）"
    )
    parser.add_argument(
        "--resolution", "-r", default="1920x1080", help="分辨率（默认：1920x1080）"
    )
    parser.add_argument(
        "--duration",
        "-d",
        type=float,
        default=3.0,
        help="每个画面持续时长（秒，默认：3.0）",
    )
    parser.add_argument(
        "--transition", "-t", type=float, default=0.3, help="过渡时长（秒，默认：0.3）"
    )
    parser.add_argument(
        "--fps", "-f", type=int, default=25, help="视频帧率（默认：25）"
    )

    args = parser.parse_args()

    IMAGES_FOLDER = get_param_value(args, "source", prompt_text="图片文件夹路径")

    if not os.path.exists(IMAGES_FOLDER):
        print(f"错误：图片文件夹不存在: {IMAGES_FOLDER}")
        sys.exit(1)

    if platform_type == "wsl":
        default_output = os.path.join(PATH_DOWNLOADS_FROM_WIN, "test.mp4")
    else:
        default_output = os.path.join(PATH_DOWNLOADS, "test.mp4")
    OUTPUT_PATH = get_param_value(args, "output", script_default=default_output)
    assert OUTPUT_PATH is not None, "输出路径不能为None"

    RESOLUTION = args.resolution
    TRANSITION_DURATION = args.transition
    IMAGE_DURATION = args.duration
    FPS = args.fps

    try:
        create_video_from_images(
            IMAGES_FOLDER,
            OUTPUT_PATH,
            RESOLUTION,
            TRANSITION_DURATION,
            IMAGE_DURATION,
            FPS,
        )
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
