# -*- coding: utf-8 -*-
"""分析因子新体系（基于 BaseFactor）。

相对旧 ``analyzer.factors.QuantFactorEngine`` 的重构：

- 每个因子一个类，继承自 ``BaseFactor``
- 因子通过 ``FactorContext`` 取数（由 ``FactorManager`` 预读）
- 每个因子输出未来 5 / 30 / 60 日相对 anchor_price 的涨跌预测（bool×3）
- 回测准确率记录在 ``accuracy.json``，分析时按准确率加权
"""

from __future__ import annotations

from .base import BaseFactor, FactorContext, FactorOutput, FORECAST_HORIZONS
from .registry import all_factors, get_factor_class, instantiate_all, factor_names
from .manager import FactorManager, FactorAnalysisResult

__all__ = [
    "BaseFactor",
    "FactorContext",
    "FactorOutput",
    "FORECAST_HORIZONS",
    "all_factors",
    "get_factor_class",
    "instantiate_all",
    "factor_names",
    "FactorManager",
    "FactorAnalysisResult",
]
