"""
File: __init__.py
Project: routine
Created: 2024-11-05 10:34:36
Author: Victor Cheng
Email: hi@victor42.work
Description:
"""

import importlib
import warnings

_submodules = [
    'path',
    'basic',
    'image',
    'video',
]

_skipped = []


def _is_missing_optional_dependency(exc):
    """Return True only for missing third-party modules during bulk import."""
    if not isinstance(exc, ModuleNotFoundError) or not exc.name:
        return False

    missing_root = exc.name.split('.')[0]
    package_root = __name__.split('.')[0]
    if missing_root == package_root:
        return False
    if missing_root in _submodules:
        return False
    return True

for _mod_name in _submodules:
    try:
        _mod = importlib.import_module(f'.{_mod_name}', __name__)
    except ModuleNotFoundError as exc:
        if not _is_missing_optional_dependency(exc):
            raise
        _skipped.append(f"{_mod_name} ({exc.name})")
        continue
    for _name in getattr(_mod, '__all__', [n for n in vars(_mod) if not n.startswith('_')]):
        globals()[_name] = getattr(_mod, _name)

if _skipped:
    warnings.warn(
        f"utils: skipped modules with missing dependencies: {', '.join(_skipped)}",
        stacklevel=2,
    )


def __getattr__(name):
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
