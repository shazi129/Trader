# -*- coding: utf-8 -*-
"""
量化因子模块

包含各类量化因子计算：
- 动量因子 (Momentum)
- 趋势因子 (Trend)
- 波动率因子 (Volatility)
- 成交量因子 (Volume)
- 风险因子 (Risk)
"""

from .momentum import calculate_momentum_factors
from .trend import calculate_trend_factors
from .volatility import calculate_volatility_factors
from .volume import calculate_volume_factors
from .risk import calculate_risk_factors

__all__ = [
    'calculate_momentum_factors',
    'calculate_trend_factors',
    'calculate_volatility_factors',
    'calculate_volume_factors',
    'calculate_risk_factors',
]
