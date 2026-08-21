# -*- coding: utf-8 -*-
"""因子注册表：自动发现并实例化所有 BaseFactor 子类。"""

from __future__ import annotations

import importlib
import os
import pkgutil
from typing import Dict, List, Type

from .base import BaseFactor

# 自动扫描的因子子模块（本目录下的 *.py，排除 base / registry / manager / __init__）
_THIS_DIR = os.path.dirname(__file__)
_EXCLUDED = {"base", "registry", "manager", "__init__"}

# 缓存：name -> class
_REGISTRY: Dict[str, Type[BaseFactor]] = {}
_SCANNED = False


def _discover() -> None:
    global _SCANNED
    if _SCANNED:
        return
    for mod_info in pkgutil.iter_modules([_THIS_DIR]):
        mod_name = mod_info.name
        if mod_name in _EXCLUDED:
            continue
        try:
            module = importlib.import_module(f"{__name__.rsplit('.', 1)[0]}.{mod_name}")
        except Exception as e:  # pragma: no cover - 单个因子模块出错不应阻断整体
            print(f"[registry] 跳过模块 {mod_name}: {e}")
            continue
        for attr in dir(module):
            obj = getattr(module, attr)
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseFactor)
                and obj is not BaseFactor
            ):
                _REGISTRY[obj.name] = obj
    _SCANNED = True


def all_factors() -> Dict[str, Type[BaseFactor]]:
    """返回 name -> 因子类 的字典（全部已发现因子）。"""
    _discover()
    return dict(_REGISTRY)


def get_factor_class(name: str) -> Type[BaseFactor]:
    _discover()
    return _REGISTRY.get(name)


def instantiate_all() -> List[BaseFactor]:
    """实例化所有因子（默认构造，无参）。"""
    return [cls() for cls in all_factors().values()]


def factor_names() -> List[str]:
    _discover()
    return sorted(_REGISTRY.keys())
