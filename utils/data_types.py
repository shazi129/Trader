# -*- coding: utf-8 -*-
"""通用工具数据类型。"""

from __future__ import annotations


class DataValue:
    """通用 (date, value) 二元组。"""

    def __init__(self, date: str, value: float) -> None:
        self.date = date
        self.value = value

    def __str__(self) -> str:
        return "date:%s, value:%f" % (self.date, self.value)
