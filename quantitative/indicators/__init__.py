# -*- coding: utf-8 -*-
"""可复用的技术指标算法。

所有指标实现为**纯函数**（输入序列，输出序列），与具体的数据结构
（DailyQuote / KlineIndicator）解耦。FactorSeriesEngine（批量写库）
和 QuantFactorEngine（单点信号）共享同一份实现，避免重复。

模块划分：
- primitives  : SMA/EMA/STD/TR/+DM/-DM/Wilder smoothing 等基础原语
- trend       : MACD/ADX/DMI/ATR
- momentum    : RSI/KDJ/MOM/ROC/CCI/Williams %R
- volume      : OBV/VPT/ADL/MFI/Force Index/Chaikin
- risk        : 波动率/回撤/Sharpe/Sortino/偏度/峰度/Amihud/GK/Parkinson/RS
"""

from .primitives import (
    sma,
    ema,
    rolling_std,
    true_range,
    plus_dm,
    minus_dm,
    wilder_smooth,
    log_returns,
    simple_returns,
)

__all__ = [
    "sma",
    "ema",
    "rolling_std",
    "true_range",
    "plus_dm",
    "minus_dm",
    "wilder_smooth",
    "log_returns",
    "simple_returns",
]
