# -*- coding: utf-8 -*-
"""均线比率/周线均线类因子字段。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MARatioFields:
    """对应数据表 ``factor_ma_ratio``。"""

    # 收盘价 / MA_N
    ma_ratio_5: float = 0.0
    ma_ratio_10: float = 0.0
    ma_ratio_20: float = 0.0
    ma_ratio_60: float = 0.0
    ma_ratio_200: float = 0.0
    ma200: float = 0.0

    # 周线均线 + 比率
    ma30w: float = 0.0
    ma75w: float = 0.0
    ma_ratio_30w_75w: float = 0.0
    ma_ratio_5w_30w: float = 0.0
