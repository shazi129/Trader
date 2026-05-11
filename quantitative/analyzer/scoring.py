# -*- coding: utf-8 -*-
"""因子结果 / 综合评分。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FactorResult:
    """单个因子的计算结果。"""
    name: str
    category: str   # momentum / technical / trend / volatility / reversal /
                    # pattern / valuation / quality / growth / dividend / size
    value: float
    signal: int     # +1=看涨, 0=中性, -1=看跌
    weight: float = 1.0
    description: str = ""


@dataclass
class AnalysisReport:
    """综合分析报告。"""
    stock_name: str
    name_key: str
    data_source: str
    data_days: int
    latest_price: float
    factors: list[FactorResult] = field(default_factory=list)
    bullish_score: float = 0.0
    bearish_score: float = 0.0
    trend: str = ""
    probability_up: float = 0.0
    probability_down: float = 0.0
    summary: str = ""


def compute_probability(factors: list[FactorResult]) -> tuple[float, float, str]:
    """基于因子加权信号计算涨跌概率。

    返回 (上涨概率, 下跌概率, 趋势描述)。
    映射策略：weighted_signal / total_weight ∈ [-1, 1]
              → prob_up ∈ [0.15, 0.85]（线性 + clip）。
    """
    if not factors:
        return 0.5, 0.5, "数据不足"

    total_weight = sum(f.weight for f in factors)
    weighted_signal = sum(f.signal * f.weight for f in factors)
    normalized = weighted_signal / total_weight if total_weight > 0 else 0.0

    prob_up = 0.5 + normalized * 0.35
    prob_up = max(0.15, min(0.85, prob_up))
    prob_down = 1.0 - prob_up

    if normalized > 0.3:
        trend = "上涨趋势"
    elif normalized < -0.3:
        trend = "下跌趋势"
    else:
        trend = "震荡整理"

    return round(prob_up, 3), round(prob_down, 3), trend
