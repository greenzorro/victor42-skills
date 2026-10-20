"""
File: folder_ungroup.py
Project: toolkit
Created: 2026-01-23 06:00:26
Author: Victor Cheng
Email: hi@victor42.work
Description: 把文件里的文件夹拆开，取出全部文件
"""

import os
import sys
import argparse
from utils.basic import get_param_value, folder_ungroup, plan_folder_ungroup
from utils.path import platform_type, PATH_DOWNLOADS_FROM_WIN, PATH_DOWNLOADS


def main():
    """主函数：执行文件夹解组操作"""
    parser = argparse.ArgumentParser(
        description="把文件里的文件夹拆开，取出全部文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # 添加参数
    parser.add_argument("--source", "-s", help="源文件夹路径")
    parser.add_argument(
        "--output", "-o", help="输出文件夹路径（默认：PATH_DOWNLOADS/Ungrouped）"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="演练模式：只列出将要复制的文件，不创建目录或写入文件",
    )

    # 解析参数
    args = parser.parse_args()

    # 获取源文件夹路径（必填参数，无默认值时询问用户）
    SRC_FOLDER = get_param_value(args, "source", prompt_text="源文件夹路径")

    # 验证源路径存在
    if not os.path.exists(SRC_FOLDER):
        print(f"错误：源路径不存在: {SRC_FOLDER}")
        sys.exit(1)

    # 获取目标文件夹路径（可选参数，有脚本默认值，不问用户）
    if platform_type == "wsl":
        default_output = os.path.join(PATH_DOWNLOADS_FROM_WIN, "Ungrouped")
    else:
        default_output = os.path.join(PATH_DOWNLOADS, "Ungrouped")
    DST_FOLDER = get_param_value(args, "output", script_default=default_output)

    if args.dry_run:
        print("当前为 dry-run 演练模式，不会创建目录或写入文件")
    elif not os.path.exists(DST_FOLDER):
        os.makedirs(DST_FOLDER)

    # 执行解组操作
    if args.dry_run:
        for src_file_path, dst_file_path in plan_folder_ungroup(
            SRC_FOLDER, DST_FOLDER
        ):
            print(f"[dry-run] 将复制: {src_file_path} -> {dst_file_path}")
        print(f"dry-run output folder:\n{DST_FOLDER}")
        return

    folder_ungroup(SRC_FOLDER, DST_FOLDER)
    print(f"ungrouped to:\n{DST_FOLDER}")


if __name__ == "__main__":
    main()
