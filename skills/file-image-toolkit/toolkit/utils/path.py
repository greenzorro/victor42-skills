"""
File: path.py
Project: toolkit
Created: 2024-11-02
Author: Victor Cheng
Email: hi@victor42.work
Description: 跨平台路径配置系统
"""

import os
import platform


def get_platform():
    """检测当前操作系统平台"""
    system = platform.system().lower()
    if system == 'windows':
        return 'windows'
    elif system == 'darwin':
        return 'macos'
    else:
        # 检查是否在 WSL 环境
        try:
            with open('/proc/version', 'r') as f:
                if 'microsoft' in f.read().lower():
                    return 'wsl'
        except FileNotFoundError:
            pass
        return 'linux'


platform_type = get_platform()

# 系统路径
HOME = os.path.expanduser('~')

# 跨平台下载目录
if platform_type == 'windows':
    PATH_DOWNLOADS = os.path.join(HOME, 'Downloads')
elif platform_type == 'macos':
    PATH_DOWNLOADS = os.path.join(HOME, 'Downloads')
elif platform_type == 'wsl':
    # WSL 默认输出到 Windows 下载目录便于跨系统访问
    windows_username = os.environ.get('USERPROFILE', '').split('\\')[-1] or os.environ.get('USERNAME', 'user')
    PATH_DOWNLOADS = f'/mnt/c/Users/{windows_username}/Downloads'
else:
    PATH_DOWNLOADS = '/tmp'

PATH_DOWNLOADS_FROM_WIN = PATH_DOWNLOADS

# 确保核心目录存在
for p in [PATH_DOWNLOADS]:
    try:
        os.makedirs(p, exist_ok=True)
    except Exception:
        pass
