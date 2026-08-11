"""
File: video.py
Project: routine
Created: 2025-09-23 11:02:19
Author: Victor Cheng
Email: hi@victor42.work
Description: 
"""

import os
import subprocess
from pathlib import Path
from typing import List


def build_ffmpeg_command(image_files: List[str], 
                        output_path: str, 
                        resolution: str, 
                        fps: int, 
                        transition_duration: float,
                        image_duration: float) -> List[str]:
    """构建FFmpeg命令

    Args:
        image_files: 图片文件路径列表
        output_path: 输出视频文件路径
        resolution: 视频分辨率
        fps: 视频帧率
        transition_duration: 过渡效果时长
        image_duration: 每个画面持续时长

    Returns:
        List[str]: FFmpeg命令参数列表
    """
    print("正在生成FFmpeg命令...")
    
    command = ['ffmpeg', '-y']  # -y: 覆盖输出文件
    
    # 添加输入文件 - 每个输入流的时长需要包含过渡效果时间
    for i, image_path in enumerate(image_files):
        if i == 0 or i == len(image_files) - 1:
            # 第一个和最后一个输入：完整时长 + 过渡时长
            input_duration = image_duration + transition_duration
        else:
            # 中间的输入：完整时长 + 2 * 过渡时长（前后都有过渡）
            input_duration = image_duration + 2 * transition_duration
        
        command.extend(['-loop', '1'])  # 循环图片
        command.extend(['-t', str(input_duration)])  # 输入流时长
        command.extend(['-i', image_path])  # 输入文件
    
    # 构建滤镜图
    filter_parts = []
    
    # Part A: 预处理所有输入流
    width, height = resolution.split('x')
    for i in range(len(image_files)):
        filter_parts.append(
            f"[{i}:v]scale={resolution}:force_original_aspect_ratio=decrease,"
            f"pad=width={width}:height={height}:x=(ow-iw)/2:y=(oh-ih)/2:color=black,"
            f"setsar=1,format=yuv420p[v{i}]"
        )
    
    # Part B: 链接xfade滤镜
    if len(image_files) > 1:
        last_stream_label = "[v0]"
        
        for i in range(1, len(image_files)):
            current_stream_label = f"[v{i}]"
            output_stream_label = f"[vout{i}]"
            
            # 计算过渡偏移时间：每个画面的开始时间 = (i-1) * (image_duration + transition_duration)
            offset = (i - 1) * (image_duration + transition_duration) + image_duration
            
            filter_parts.append(
                f"{last_stream_label}{current_stream_label}xfade=transition=fade:"
                f"duration={transition_duration}:offset={offset}{output_stream_label}"
            )
            
            last_stream_label = output_stream_label
        
        final_output_label = last_stream_label
    else:
        final_output_label = "[v0]"
    
    # 组合滤镜图
    filter_complex = ";".join(filter_parts)
    command.extend(['-filter_complex', filter_complex])
    
    # 输出设置
    command.extend(['-map', final_output_label])
    command.extend(['-c:v', 'libx264'])
    command.extend(['-r', str(fps)])
    command.extend(['-pix_fmt', 'yuv420p'])
    # 计算总时长：总图片数 * 每个图片时长 + (总图片数-1) * 过渡时长
    total_duration = len(image_files) * image_duration + (len(image_files) - 1) * transition_duration
    command.extend(['-t', str(total_duration)])  # 设置总时长
    command.append(output_path)
    
    return command


def execute_ffmpeg_command(command: List[str]):
    """执行FFmpeg命令

    Args:
        command: FFmpeg命令参数列表

    Raises:
        RuntimeError: FFmpeg执行失败
    """
    print(f"执行FFmpeg命令: {' '.join(command[:10])}...")  # 显示命令前10个参数
    
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        print("视频生成成功！")
        
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg执行失败: {e.stderr}")
        raise RuntimeError(f"视频生成失败: {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError("未找到FFmpeg，请确保已安装FFmpeg并添加到系统路径")

