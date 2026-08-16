# -*- coding: utf-8 -*-
"""PDF 解析器子包。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from financial_reports.parsers.hk_ifrs import HKIfrsParser


def __getattr__(name: str) -> Any:
    """按需加载具体解析器，纯工具模块无需加载 PDF 依赖。"""
    if name == "HKIfrsParser":
        from financial_reports.parsers.hk_ifrs import HKIfrsParser
        return HKIfrsParser
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["HKIfrsParser"]
