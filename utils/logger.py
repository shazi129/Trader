# -*- coding: utf-8 -*-
"""轻量日志辅助。

提供 ``get_logger(name)`` 给项目内各模块使用，避免每个文件重复
``logging.basicConfig`` 之类的样板。

设计原则：
- **库代码不主动配置根 logger**：本模块仅在第一次被导入时给项目根
  logger ``trader`` 装一个 StreamHandler（仅当未配置过），日志级别
  默认 INFO。CLI 入口（如 ``factor_batch.main``、``quant_analyzer.main``）
  可调用 ``configure_root_level`` 显式调整。
- 调用方统一用 ``get_logger(__name__)``，输出会在 ``[模块] 信息`` 形式下
  显示，方便定位。
"""

from __future__ import annotations

import logging
import os
import sys

_ROOT_NAME = "trader"
_DEFAULT_FORMAT = "[%(asctime)s] [%(name)s] %(levelname)s  %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_INITIALIZED = False

# 项目根目录 = utils/ 的父目录
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _ensure_root_handler() -> None:
    global _INITIALIZED
    if _INITIALIZED:
        return
    root = logging.getLogger(_ROOT_NAME)

    if not root.handlers:
        # 控制台输出：INFO 及以上
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(logging.Formatter(
            "[%(name)s] %(message)s"
        ))
        root.addHandler(stream_handler)

        # 文件输出：DEBUG 及以上，写入 logs/ 目录
        log_dir = os.path.join(_PROJECT_ROOT, "logs")
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(
            os.path.join(log_dir, "trader.log"),
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            _DEFAULT_FORMAT, datefmt=_DATE_FORMAT,
        ))
        root.addHandler(file_handler)

        root.setLevel(logging.DEBUG)
        # 不向 Python 根 logger 冒泡，避免双输出
        root.propagate = False
    _INITIALIZED = True


def get_logger(name: str) -> logging.Logger:
    """返回项目命名空间下的 logger（``trader.<name>``）。"""
    _ensure_root_handler()
    # 把外部传入的 ``foo.bar`` 接到 ``trader.foo.bar``，避免污染 Python root
    suffix = name if name else "app"
    return logging.getLogger(f"{_ROOT_NAME}.{suffix}")


def configure_root_level(level: int | str) -> None:
    """调整项目根 logger 的级别（CLI 入口可用）。"""
    _ensure_root_handler()
    logging.getLogger(_ROOT_NAME).setLevel(level)
