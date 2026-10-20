"""
File: __init__.py
Project: toolkit
Author: Victor Cheng
Email: hi@victor42.work
Description: utils 包入口，采用惰性加载。

    `import utils` 不再预先导入任何子模块；`utils.<子模块名>` 在首次访问时才导入。
    推荐显式导入，如 `from utils.basic import get_param_value`。
"""

import importlib

# 子模块登记表
_submodules = [
    'path',
    'basic',
    'image',
    'video',
]


def __getattr__(name):
    """按需导入子模块，使 `import utils; utils.basic` 可用但不预加载。"""
    if name in _submodules:
        return importlib.import_module(f'.{name}', __name__)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    """让 dir(utils) 列出子模块，避免惰性加载破坏自省。"""
    return sorted(set(globals()) | set(_submodules))
