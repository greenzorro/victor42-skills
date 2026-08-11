"""
File: basic.py
Project: routine
Created: 2024-11-05 12:57:35
Author: Victor Cheng
Email: hi@victor42.work
Description: 
"""

import os
import csv
import shutil
import subprocess
import re
from typing import Optional
from PIL import Image
import pillow_avif


def get_source_files(source_path, allowed_extensions=None, recursive=False):
    """Return source files from a file path or directory path.

    :param str source_path: Source file or directory path
    :param iterable allowed_extensions: Extensions with or without leading dots
    :param bool recursive: Whether to scan directories recursively
    :return list[str]: Sorted source file paths
    """
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"源路径不存在: {source_path}")

    allowed = None
    if allowed_extensions is not None:
        allowed = {
            ext.lower().lstrip(".")
            for ext in allowed_extensions
        }

    def is_allowed(path):
        name = os.path.basename(path)
        if name.startswith(".") or not os.path.isfile(path):
            return False
        if allowed is None:
            return True
        return os.path.splitext(name)[1][1:].lower() in allowed

    if os.path.isfile(source_path):
        return [source_path] if is_allowed(source_path) else []

    files = []
    if recursive:
        for root, dirs, filenames in os.walk(source_path):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for filename in filenames:
                path = os.path.join(root, filename)
                if is_allowed(path):
                    files.append(path)
    else:
        for filename in os.listdir(source_path):
            path = os.path.join(source_path, filename)
            if is_allowed(path):
                files.append(path)

    return sorted(files)


def sanitize_file_name_string(input_string):
    """从字符串中去除不能作为文件名的字符

    :param str input_string: 输入的字符串
    :return str: 清理后的字符串
    """
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*', '.', ',']
    for char in invalid_chars:
        input_string = input_string.replace(char, ' ')
    # 把多个连续的空格替换单个空格
    result = ' '.join(input_string.split())
    return result


def folder_ungroup(src_path, dst_path):
    """把文件里的文件夹拆开，取出全部文件

    :param str src_path: 源文件夹路径
    :param str dst_path: 目标文件夹路径
    """
    if not os.path.exists(dst_path):
        os.makedirs(dst_path)

    for root, dirs, files in os.walk(src_path):
        for file in files:
            src_file_path = os.path.join(root, file)
            dst_file_path = os.path.join(dst_path, file)
            shutil.copy(src_file_path, dst_file_path)


def rename_by_csv(csv_file, src_folder, dst_folder):
    """批量根据CSV重命名文件

    :param str csv_file: 包含新文件名的CSV文件
    :param str src_folder: 原始文件夹路径
    :param str dst_folder: 目标文件夹路径
    """
    # 读取csv文件
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        name_column = None
        for column in reader.fieldnames:
            if 'name' in column.lower():
                name_column = column
                break
        # 把对应列里每一行的值存到一个list里
        name_list = [row[name_column] for row in reader]

    # 清理name_list中的非法字符
    name_list = [sanitize_file_name_string(name) for name in name_list]

    # 判断文件数量与名称数量是否匹配
    if len(os.listdir(src_folder)) != len(name_list):
        print(f'There are {len(os.listdir(src_folder))} files and {len(name_list)} names. They do not match.')
        return

    # 遍历原始文件存入list
    src_files = []
    for filename in os.listdir(src_folder):
        # 忽略隐藏文件和文件夹
        if filename.startswith('.'):
            continue
        src_path = os.path.join(src_folder, filename)
        src_files.append(src_path)

    # 按文件名数字顺序排列
    src_files.sort(key=lambda x: int(re.findall(r'\d+', os.path.splitext(os.path.basename(x))[0])[-1]))

    # 批量重命名
    for i, src_path in enumerate(src_files):
        # 获取文件名和扩展名
        filename, ext = os.path.splitext(os.path.basename(src_path))
        # 获取新文件名
        new_filename = name_list[i] + ext
        # 拼接新文件路径
        dst_path = os.path.join(dst_folder, new_filename)
        # 复制文件
        shutil.copy(src_path, dst_path)

        # 打印输出结果
        if os.path.exists(dst_path):
            print(f'{src_path} renamed to {dst_path}')
        else:
            print(f'Failed to rename {src_path}')


VIDEO_FORMATS = {'mp4', 'avi', 'wmv', 'mov', 'flv', 'm4a', 'mkv', 'webm', 'm4v'}
AUDIO_FORMATS = {'mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'opus'}
IMAGE_FORMATS = {'jpg', 'jpeg', 'png', 'bmp', 'gif', 'tiff', 'webp', 'avif'}

VIDEO_CODEC_OPTIONS = {
    'mp4': ['-c:v', 'libx264', '-preset', 'slow', '-crf', '22', '-c:a', 'aac', '-b:a', '192k'],
    'mov': ['-c:v', 'libx264', '-preset', 'slow', '-crf', '22', '-c:a', 'aac', '-b:a', '192k'],
    'm4v': ['-c:v', 'libx264', '-preset', 'slow', '-crf', '22', '-c:a', 'aac', '-b:a', '192k'],
    'mkv': ['-c:v', 'libx264', '-preset', 'slow', '-crf', '22', '-c:a', 'aac', '-b:a', '192k'],
    'avi': ['-c:v', 'mpeg4', '-q:v', '5', '-c:a', 'libmp3lame', '-q:a', '2'],
    'webm': ['-c:v', 'libvpx-vp9', '-crf', '32', '-b:v', '0', '-c:a', 'libopus', '-b:a', '128k'],
    'flv': ['-c:v', 'libx264', '-preset', 'slow', '-crf', '24', '-c:a', 'aac', '-b:a', '160k'],
    'wmv': ['-c:v', 'wmv2', '-c:a', 'wmav2'],
}

AUDIO_CODEC_OPTIONS = {
    'mp3': ['-vn', '-c:a', 'libmp3lame', '-q:a', '2'],
    'wav': ['-vn', '-c:a', 'pcm_s16le'],
    'flac': ['-vn', '-c:a', 'flac'],
    'aac': ['-vn', '-c:a', 'aac', '-b:a', '192k'],
    'm4a': ['-vn', '-c:a', 'aac', '-b:a', '192k'],
    'ogg': ['-vn', '-c:a', 'libvorbis', '-q:a', '5'],
    'opus': ['-vn', '-c:a', 'libopus', '-b:a', '128k'],
}


def convert_format(src_path, dst_path, dst_format):
    """文件格式转换

    :param str src_path: 源文件路径
    :param str dst_path: 目标文件路径
    :param str dst_format: 目标格式
    """
    # 参数验证
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"源文件未找到: {src_path}")
    
    if not dst_format or not isinstance(dst_format, str):
        raise ValueError(f"目标格式必须是非空字符串，当前值: {dst_format}")
    
    # 确保目标目录存在
    dst_dir = os.path.dirname(dst_path)
    if dst_dir and not os.path.exists(dst_dir):
        os.makedirs(dst_dir, exist_ok=True)
    
    src_format = os.path.splitext(src_path)[1][1:].lower()
    dst_format = dst_format.lower().lstrip('.')
    
    try:
        # 如果源格式和目标格式一样，直接复制文件
        if src_format == dst_format:
            shutil.copy(src_path, dst_path)
            print(f'{src_path} copied to {dst_path}')
            return
        
        # 处理视频文件的转换
        if src_format in VIDEO_FORMATS:
            if dst_format == 'gif':
                # 视频→GIF：使用调色板优化的一步法
                result = subprocess.run([
                    'ffmpeg', '-i', src_path,
                    '-vf', 'fps=15,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse',
                    '-y', dst_path
                ], capture_output=True, text=True)
                if result.returncode != 0:
                    raise RuntimeError(f"视频转GIF失败: {result.stderr}")
            elif dst_format in AUDIO_FORMATS:
                result = subprocess.run(['ffmpeg', '-i', src_path, *AUDIO_CODEC_OPTIONS[dst_format], dst_path],
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    raise RuntimeError(f"视频转音频失败: {result.stderr}")
            elif dst_format in VIDEO_CODEC_OPTIONS:
                result = subprocess.run(['ffmpeg', '-i', src_path, *VIDEO_CODEC_OPTIONS[dst_format], dst_path],
                                      capture_output=True, text=True)
            else:
                raise ValueError(f"不支持的视频目标格式: {dst_format}")
            if result.returncode != 0:
                raise RuntimeError(f"视频格式转换失败: {result.stderr}")
        
        # 处理音频文件的转换
        elif src_format in AUDIO_FORMATS:
            if dst_format not in AUDIO_CODEC_OPTIONS:
                raise ValueError(f"不支持的音频目标格式: {dst_format}")
            result = subprocess.run(['ffmpeg', '-i', src_path, *AUDIO_CODEC_OPTIONS[dst_format], dst_path],
                                  capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"音频格式转换失败: {result.stderr}")
        
        # 处理图片文件的转换
        elif src_format in IMAGE_FORMATS:
            # 检查目标格式是否支持
            if dst_format not in IMAGE_FORMATS:
                raise ValueError(f"不支持的图片目标格式: {dst_format}")
            
            try:
                with Image.open(src_path) as img:
                    # JPEG 不支持 P/PA/LA/RGBA 等模式，需要统一转为 RGB
                    # L 模式（灰度）可以保存为 JPEG，其他模式需要转换
                    if img.mode not in ('RGB', 'L'):
                        img = img.convert('RGB')
                    img.save(dst_path)
            except Exception as img_e:
                raise RuntimeError(f"图片格式转换失败: {img_e}")
        
        else:
            raise ValueError(f"不支持的源文件格式: {src_format}")
        
        # 验证转换结果
        if not os.path.exists(dst_path):
            raise RuntimeError(f"转换失败，目标文件未生成: {dst_path}")
        
        # 打印转换结果
        print(f'{src_path} converted to {dst_path}')
        
    except FileNotFoundError:
        raise
    except ValueError:
        raise
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f'转换过程中发生未预期的错误: {e}')


def extract_number_from_filename(filename: str) -> int:
    """从文件名中提取数字部分，用于排序

    Args:
        filename: 文件名

    Returns:
        int: 提取的数字，如果没有数字返回999999
    """
    # 移除文件扩展名
    name_without_ext = os.path.splitext(filename)[0]
    
    # 查找文件名中的数字部分
    numbers = re.findall(r'\d+', name_without_ext)
    
    if numbers:
        # 取第一个数字（最前面一段纯数字的部分）
        return int(numbers[0])
    else:
        # 如果没有数字，返回一个很大的数确保排在最后
        return 999999


def get_param_value(args, arg_name, script_default=None, prompt_text=None):
    """获取参数值，按优先级：
    1. 命令行参数
    2. 脚本提供的默认值
    3. 用户输入（可选）

    Args:
        args: argparse 解析后的参数对象
        arg_name: 参数名称
        script_default: 脚本预先计算好的默认值
        prompt_text: 提供此参数才询问用户

    Returns:
        参数值

    设计理念：
    - 基建只做一件事：参数优先级判断
    - 脚本负责计算默认值（可以是复杂、异步、依赖状态的逻辑）
    - prompt_text 是可选的：不提供 = 不问用户，直接用默认值
    """
    # 优先级1：命令行参数
    value = getattr(args, arg_name, None)
    if value is not None:
        return value

    # 优先级2：脚本默认值
    if script_default is not None:
        return script_default

    # 优先级3：用户输入（可选）
    if prompt_text is not None:
        return input(prompt_text + ": ")

    return None
