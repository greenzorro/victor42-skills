"""
File: path.py
Project: toolkit
Author: Victor Cheng
Email: hi@victor42.work
Description: 跨平台路径配置（下载目录与平台识别）

约定：
- `PATH_DOWNLOADS`        本机（Linux/macOS 侧）下载目录
- `PATH_DOWNLOADS_FROM_WIN` Windows 侧下载目录；在 WSL 下脚本用它做默认输出，
  便于结果直接落到 Windows 可见的位置
"""

import os
import platform


def get_platform():
    """检测当前运行平台

    :return str: 'windows' / 'wsl' / 'mac' / 'linux'
    """
    system = platform.system()

    if system == 'Windows':
        return 'windows'
    if system == 'Darwin':
        return 'mac'
    if system == 'Linux':
        # 通过 /proc/version 判断是否为 WSL
        try:
            with open('/proc/version', 'r') as f:
                version_info = f.read().lower()
            if 'microsoft' in version_info or 'wsl' in version_info:
                return 'wsl'
            return 'linux'
        except FileNotFoundError:
            return 'linux'
    return 'linux'


platform_type = get_platform()

HOME = os.path.expanduser('~')
PATH_DOWNLOADS = os.path.join(HOME, 'Downloads')


def _detect_windows_username():
    """在 WSL 下推断 Windows 用户名，用于定位 Windows 下载目录。

    优先读环境变量（WSL 默认会注入 USERPROFILE / USERNAME），
    读不到时扫描 /mnt/c/Users 找第一个非系统账户，避免硬编码用户名。
    """
    for var in ('USERPROFILE', 'USERNAME'):
        value = os.environ.get(var, '').strip()
        if not value:
            continue
        name = os.path.basename(value.replace('\\', '/').rstrip('/'))
        if name:
            return name

    system_accounts = {'public', 'default', 'default user', 'all users'}
    base = '/mnt/c/Users'
    if os.path.isdir(base):
        for entry in sorted(os.listdir(base)):
            if entry.lower() in system_accounts:
                continue
            if os.path.isdir(os.path.join(base, entry)):
                return entry

    return os.environ.get('USER', 'user')


# WSL 下指向 Windows 下载目录；其他平台退回本机下载目录，
# 使调用方无需再判断平台。
if platform_type == 'wsl':
    windows_username = _detect_windows_username()
    PATH_DOWNLOADS_FROM_WIN = f'/mnt/c/Users/{windows_username}/Downloads'
else:
    # 仅 WSL 下有意义，其他平台置空以免误用
    windows_username = None
    PATH_DOWNLOADS_FROM_WIN = PATH_DOWNLOADS
