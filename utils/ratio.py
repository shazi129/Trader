# -*- coding: utf-8 -*-
"""股票比值工具：取两只股票收盘价的比值时间序列"""

from __future__ import annotations

from typing import List

from database.stock_db_utils import StockDB
from utils.data_types import DataValue


def get_ratio_data(denominator_key: str, numerator_key: str) -> List[DataValue]:
    """返回 denominator.Close / numerator.Close 的时间序列（升序）。"""
    db = StockDB()
    try:
        return db.get_stock_ratio_data(denominator_key, numerator_key)
    finally:
        db.close()
