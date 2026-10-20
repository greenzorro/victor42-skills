"""
File: rename_by_csv.py
Project: toolkit
Created: 2024-01-16 10:34:07
Author: Victor Cheng
Email: hi@victor42.work
Description: CSV批量重命名工具 - 根据CSV文件中的名称列批量重命名文件
"""

import os
import argparse
import sys
import csv
import re
from utils.basic import get_param_value, rename_by_name_list, sanitize_file_name_string
from utils.path import get_platform, PATH_DOWNLOADS_FROM_WIN, PATH_DOWNLOADS


def read_name_list_from_csv(csv_file):
    """从 CSV 中读取第一个包含 name 的列"""
    with open(csv_file, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        name_column = None
        for column in reader.fieldnames or []:
            if "name" in column.lower():
                name_column = column
                break
        if not name_column:
            raise ValueError("CSV文件缺少 name 列")
        return [row[name_column] for row in reader]


def preview_rename_by_name_list(name_list, src_folder, dst_folder):
    """打印批量重命名计划，不复制文件"""
    name_list = [sanitize_file_name_string(name) for name in name_list]

    src_files = []
    for filename in os.listdir(src_folder):
        if filename.startswith("."):
            continue
        src_path = os.path.join(src_folder, filename)
        if os.path.isfile(src_path):
            src_files.append(src_path)

    if len(src_files) != len(name_list):
        print(f"There are {len(src_files)} files and {len(name_list)} names. They do not match.")
        return

    src_files.sort(key=lambda x: int(re.findall(r"\d+", os.path.splitext(os.path.basename(x))[0])[-1]))
    for i, src_path in enumerate(src_files):
        ext = os.path.splitext(os.path.basename(src_path))[1]
        dst_path = os.path.join(dst_folder, name_list[i] + ext)
        print(f"[dry-run] 将复制并重命名: {src_path} -> {dst_path}")


def main():
    parser = argparse.ArgumentParser(
        description="根据CSV文件批量重命名文件（CSV需包含name列，文件名需含数字序号）"
    )
    parser.add_argument("--csv", "-c", help="CSV文件路径（必填）")
    parser.add_argument("--source", "-s", help="源文件夹路径（必填）")
    parser.add_argument("--output", "-o", help="输出文件夹路径（可选，默认：Renamed）")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="演练模式：只列出将要复制并重命名的文件，不创建目录或写入文件",
    )
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

    if args.dry_run:
        print("当前为 dry-run 演练模式，不会创建目录或写入文件")
        try:
            name_list = read_name_list_from_csv(CSV_FILE)
        except ValueError as e:
            print(f"错误：{e}")
            sys.exit(1)
        preview_rename_by_name_list(name_list, SRC_FOLDER, DST_FOLDER)
        return

    if not os.path.exists(DST_FOLDER):
        os.makedirs(DST_FOLDER)

    try:
        name_list = read_name_list_from_csv(CSV_FILE)
    except ValueError as e:
        print(f"错误：{e}")
        sys.exit(1)
    rename_by_name_list(name_list, SRC_FOLDER, DST_FOLDER)


if __name__ == "__main__":
    main()
