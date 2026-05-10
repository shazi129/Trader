# -*- coding: utf-8 -*-
"""趋势类因子字段：EMA / MACD 柱 / ADX / ATR。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TrendFields:
    """对应数据表 ``factor_trend``。"""

    # 多周期 EMA
    ema12: float = 0.0
    ema26: float = 0.0
    ema50: float = 0.0

    # MACD 柱状图（与 ``BasicFields.macd`` 同源，单独存储以方便子表查询）
    macd_hist: float = 0.0

    # ADX / DMI
    adx: float = 0.0
    plus_di: float = 0.0
    minus_di: float = 0.0

    # ATR 系列
    tr: float = 0.0
    atr: float = 0.0
    atr_pct: float = 0.0
