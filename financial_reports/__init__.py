# -*- coding: utf-8 -*-
"""财报数据抽象包。

职责：从 PDF（A 股 / 港股 / 美股，未来可扩）解析三大财务报表，
统一为 ``FinancialReport`` 数据模型，单位归一到「元」。

外层调用流程：
    1. ``ParserFactory.detect(pdf_path)`` 自动选解析器；
    2. ``parser.parse(pdf_path, name_key)`` → ``FinancialReport``；
    3. ``StockDB.write_financial_report(report)`` 入库；
    4. （后续）``PITBuilder`` 按 ``announce_date`` 生成日频 PIT 派生表，
       接入 ``KlineIndicator``。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from financial_reports.models import FinancialReport
from financial_reports.parser_base import FinancialParser, ParserError

if TYPE_CHECKING:
    from financial_reports.parser_factory import ParserFactory


def __getattr__(name: str) -> Any:
    """按需加载解析器工厂，避免领域模型强制依赖 PDF 解析库。"""
    if name == "ParserFactory":
        from financial_reports.parser_factory import ParserFactory
        return ParserFactory
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "FinancialReport",
    "FinancialParser",
    "ParserError",
    "ParserFactory",
]
