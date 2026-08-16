# -*- coding: utf-8 -*-
"""财报解析器的公共接口。"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from financial_reports.models import FinancialReport


class ParserError(Exception):
    """解析失败时抛出。包含足够上下文便于排查。"""


class FinancialParser:
    """所有 PDF 解析器的抽象基类。

    子类必须实现：
    - ``SOURCE_TAG``：标识符，写入 DB 的 ``Source`` 列；
    - ``can_parse(pdf_path)``：扫第一页判断本解析器能否处理；
    - ``parse(pdf_path, name_key)``：返回 ``FinancialReport``。
    """

    SOURCE_TAG: str = "base"

    def can_parse(self, pdf_path: Path) -> bool:
        raise NotImplementedError

    def parse(self, pdf_path: Path, name_key: str,
              period_hint: Optional[str] = None) -> FinancialReport:
        """解析 PDF。

        :param period_hint: 可选的报告期提示，格式 ``"YYYYQ1"`` / ``"YYYYQ2"`` /
            ``"YYYYQ3"`` / ``"YYYYQ4"``。当 PDF 内没有标准 "截至XX止" 句式
            时（早期/部分年份），用此提示推断 ``period_end``。
            一般由调用方从文件名（如 ``2019Q1.pdf``）解析后传入。
        """
        raise NotImplementedError
