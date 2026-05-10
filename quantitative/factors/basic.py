# -*- coding: utf-8 -*-
"""基础指标字段：MA / 布林 / KDJ / MACD / RSI / ADOSC。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BasicFields:
    """对应数据表 ``factor_indicator``。"""

    # 均线（多周期收盘均价）
    ma5: float = 0.0
    ma10: float = 0.0
    ma20: float = 0.0
    ma30: float = 0.0
    ma60: float = 0.0
    ma120: float = 0.0
    ma250: float = 0.0

    # 布林带（中线即 ma20）
    boll_up: float = 0.0
    boll_low: float = 0.0

    # KDJ
    k: float = 0.0
    d: float = 0.0
    j: float = 0.0

    # MACD（DIF / DEA / 柱）
    dif: float = 0.0
    dea: float = 0.0
    macd: float = 0.0

    # 多周期 RSI
    rsi1: float = 0.0
    rsi2: float = 0.0
    rsi3: float = 0.0

    # 累积/震荡型成交量摆动指标 ADOSC
    adosc: float = 0.0
