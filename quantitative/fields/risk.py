# -*- coding: utf-8 -*-
"""风险/波动率/风险调整收益类因子字段。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskFields:
    """对应数据表 ``factor_risk``。"""

    # 历史波动率
    hv20: float = 0.0
    hv60: float = 0.0

    # 回撤与综合波动率
    max_drawdown: float = 0.0
    volatility: float = 0.0

    # 风险调整收益
    sharpe: float = 0.0
    sortino: float = 0.0
    calmar: float = 0.0

    # 收益率分布形状
    skewness: float = 0.0
    kurtosis: float = 0.0
