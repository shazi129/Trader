# -*- coding: utf-8 -*-
"""自动选解析器：扫第一页内容判断 PDF 属于哪个市场，返回对应解析器实例。

新增市场只需在 ``_PARSERS`` 列表里加上一个解析器类。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from quote_api.financial.financial_base import FinancialParser
from quote_api.financial.parsers.pdf_hk_ifrs import HKIfrsParser

_log = logging.getLogger(__name__)


class ParserFactory:
    """按 PDF 内容自动选择解析器。"""

    _PARSERS: list[type[FinancialParser]] = [
        HKIfrsParser,
        # AShareParser,   # TODO: A 股季报解析器
        # USSecParser,    # TODO: 美股 SEC 10-Q/10-K 解析器
    ]

    @classmethod
    def detect(cls, pdf_path: Path) -> Optional[FinancialParser]:
        """返回能处理该 PDF 的解析器实例；找不到返回 None。"""
        for cls_ in cls._PARSERS:
            try:
                p = cls_()
                if p.can_parse(pdf_path):
                    return p
            except Exception as e:  # noqa: BLE001
                _log.warning("parser %s probe failed: %s", cls_.__name__, e)
                continue
        return None
