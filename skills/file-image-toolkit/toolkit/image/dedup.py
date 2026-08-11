"""
File: dedup.py
Project: routine
Created: 2026-03-12 09:33:28
Author: Victor Cheng
Email: hi@victor42.work
Description: 智能图像去重工具：识别并清理文件夹中的重复/相似图片，保留分辨率最高、质量最优的版本。
"""

import os
import sys
import shutil
import argparse
import random

current_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.dirname(current_dir))

from utils.image import get_sorted_image_files, get_image_fingerprint, find_similar_image_groups
from utils.basic import get_param_value
from utils.path import platform_type, PATH_DOWNLOADS_FROM_WIN


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="智能图像去重工具：识别并清理文件夹中的重复/相似图片，保留分辨率最高、质量最优的版本。支持缩放和裁剪变体的识别。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("-s", "--source", help="源图片文件夹路径")
    parser.add_argument("-o", "--output", help="重复图片移动到的目标文件夹路径")
    parser.add_argument(
        "-t", "--threshold", type=int, default=6, help="哈希匹配阈值（越小越严格，默认6）"
    )
    parser.add_argument(
        "-c",
        "--crop-similarity",
        type=float,
        default=0.85,
        help="裁剪检测相似度阈值（0-1，默认0.85）",
    )
    parser.add_argument(
        "-e", "--execute", action="store_true", help="实际执行移动操作（默认仅预览）"
    )

    args = parser.parse_args()

    # 获取参数值
    source_dir = get_param_value(args, "source", prompt_text="请输入源图片文件夹路径")
    if not source_dir or not os.path.exists(source_dir):
        print(f"❌ 错误：源文件夹不存在: {source_dir}")
        return

    # 默认输出路径：WSL 环境下输出到 Windows 下载目录，其他环境下输出到源目录同级的 Duplicates
    default_output = os.path.join(os.path.dirname(source_dir), "Duplicates")
    if platform_type == "wsl":
        default_output = os.path.join(PATH_DOWNLOADS_FROM_WIN, "Duplicates")

    output_dir = get_param_value(args, "output", script_default=default_output)
    threshold = get_param_value(args, "threshold", script_default=6)
    crop_similarity = get_param_value(args, "crop_similarity", script_default=0.85)
    execute = args.execute

    # 使用 utils 中的标准函数获取图片列表，已处理格式过滤和数字排序
    try:
        image_files = get_sorted_image_files(source_dir)
    except ValueError as e:
        print(f"⚠️  {e}")
        return

    # 1. 提取所有图片的视觉指纹
    print(f"🔍 正在提取 {len(image_files)} 张图片的视觉指纹...")
    fingerprints = []
    for i, file_path_str in enumerate(image_files, 1):
        file_name = os.path.basename(file_path_str)
        print(
            f"\r  进度 [{i}/{len(image_files)}]: {file_name[:40]:<40}",
            end="",
            flush=True,
        )
        fp = get_image_fingerprint(file_path_str)
        if fp:
            fingerprints.append(fp)
    print(f"\n✅ 成功处理 {len(fingerprints)} 张图片")

    # 2. 识别相似分组
    print(f"\n🕵️ 正在识别相似图片组（阈值: hash={threshold}, sim={crop_similarity}）...")
    groups = find_similar_image_groups(fingerprints, threshold, crop_similarity)

    if not groups:
        print("✨ 未发现重复图片。")
        return

    # 3. 处理分组结果并预生成执行计划
    action_plan = []  # 存储 (src_path, dst_name, is_best) 的元组列表
    total_duplicates = 0
    total_saved_bytes = 0

    print("\n" + "=" * 60)
    print(f"📊 识别到 {len(groups)} 组重复图片")
    print("=" * 60)

    for i, group in enumerate(groups, 1):
        # 选择最佳图片（像素最高，其次是文件大小）
        best = max(group, key=lambda x: (x.pixels, x.size_bytes))
        duplicates = sorted(
            [img for img in group if img.path != best.path],
            key=lambda x: x.pixels,
            reverse=True,
        )

        group_saved = sum(img.size_bytes for img in duplicates)
        total_saved_bytes += group_saved
        total_duplicates += len(duplicates)

        print(f"\n【第 {i} 组】")
        print(f"  ✅ 保留: {best.path.name}")
        print(f"          {best.resolution_str} ({best.size_bytes/1024:.1f} KB)")

        for img in duplicates:
            print(f"  ❌ 移除: {img.path.name}")
            print(f"             {img.resolution_str} ({img.size_bytes/1024:.1f} KB)")
            action_plan.append(img.path)

    print("\n" + "-" * 60)
    print(f"📈 统计信息：")
    print(f"   重复组数: {len(groups)}")
    print(f"   冗余文件: {total_duplicates}")
    print(f"   可节省空间: {total_saved_bytes/1024/1024:.2f} MB")
    print("=" * 60)

    # 4. 执行移动或预览
    if not execute:
        print("\n⚠️  当前为预览模式，未移动任何文件。")
        print("💡 提示：添加 --execute 参数可正式执行去重操作。")
    else:
        print(f"\n🗑️ 正在将重复图片移动到: {output_dir}")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        moved_count = 0
        for src_path in action_plan:
            file_name = src_path.name
            src = str(src_path)
            dst = os.path.join(output_dir, file_name)
            
            # 处理重名冲突
            if os.path.exists(dst):
                name, ext = os.path.splitext(file_name)
                dst = os.path.join(output_dir, f"{name}_{random.randint(1,999)}{ext}")

            try:
                shutil.move(src, dst)
                moved_count += 1
            except Exception as e:
                print(f"  [Error] 移动 {file_name} 失败: {e}")

        print(f"✅ 成功移动 {moved_count} 个重复文件。")


if __name__ == "__main__":
    main()
