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

from quote_api.financial.financial_base import (
    FinancialReport,
    FinancialParser,
    ParserError,
)
from quote_api.financial.parser_factory import ParserFactory

__all__ = [
    "FinancialReport",
    "FinancialParser",
    "ParserError",
    "ParserFactory",
]
