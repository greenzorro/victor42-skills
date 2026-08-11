"""
File: rename_by_csv.py
Project: routine
Created: 2024-01-16 10:34:07
Author: Victor Cheng
Email: hi@victor42.work
Description: CSV批量重命名工具 - 根据CSV文件中的名称列批量重命名文件
"""

import os
import argparse
import sys
from utils.basic import get_param_value, rename_by_csv
from utils.path import get_platform, PATH_DOWNLOADS_FROM_WIN, PATH_DOWNLOADS


def main():
    parser = argparse.ArgumentParser(
        description="根据CSV文件批量重命名文件（CSV需包含name列，文件名需含数字序号）"
    )
    parser.add_argument("--csv", "-c", help="CSV文件路径（必填）")
    parser.add_argument("--source", "-s", help="源文件夹路径（必填）")
    parser.add_argument("--output", "-o", help="输出文件夹路径（可选，默认：Renamed）")
    args = parser.parse_args()

    CSV_FILE = get_param_value(args, "csv", prompt_text="CSV文件路径")
    SRC_FOLDER = get_param_value(args, "source", prompt_text="源文件夹路径")

    platform_type = get_platform()
    if platform_type == "wsl":
        default_output = os.path.join(PATH_DOWNLOADS_FROM_WIN, "Renamed")
    else:
        default_output = os.path.join(PATH_DOWNLOADS, "Renamed")

    DST_FOLDER = get_param_value(args, "output", script_default=default_output)

    if not os.path.exists(CSV_FILE):
        print(f"错误：CSV文件不存在: {CSV_FILE}")
        sys.exit(1)

    if not os.path.exists(SRC_FOLDER):
        print(f"错误：源文件夹不存在: {SRC_FOLDER}")
        sys.exit(1)

    if not os.path.exists(DST_FOLDER):
        os.makedirs(DST_FOLDER)

    rename_by_csv(CSV_FILE, SRC_FOLDER, DST_FOLDER)


if __name__ == "__main__":
    main()
