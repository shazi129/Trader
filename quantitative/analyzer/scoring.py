# -*- coding: utf-8 -*-
"""因子结果 / 综合评分。"""

from __future__ import annotations

import os
import json
from dataclasses import dataclass, field
from typing import Optional


# 因子 -> 周期桶 映射（与 optimize_period_weights.py 保持一致）
FACTOR_BUCKET = {
    # 短线（≤20 交易日）
    "RSI": "short",
    "CCI": "short",
    "随机指标": "short",
    "乖离率": "short",
    "威廉指标": "short",
    "布林带宽度": "short",
    "PVT能量潮": "short",
    "OBV能量潮": "short",
    "5日动量": "short",
    "ATR波动率": "short",
    # 中线（≤60 交易日）
    "1M动量": "medium",
    "3M动量": "medium",
    "12M+1M反转": "medium",
    "MACD柱状图": "medium",
    "市盈率分位": "medium",
    "市净率分位": "medium",
    "PEG估值": "medium",
    "KAMA自适应均线": "medium",
    "短期反转": "medium",
    "成交量变化率": "medium",
    # 长线（>60 交易日）
    "6M动量": "long",
    "12M动量": "long",
    "市盈率": "long",
    "市净率": "long",
    "ROE": "long",
    "营收增长率": "long",
    "利润增长率": "long",
    "EV/EBITDA": "long",
    "52周位置": "long",
}

# 分周期权重文件路径（由 optimize_period_weights.py 生成）
_WEIGHTS_FILE = os.path.join(os.path.dirname(__file__), "period_weights.json")


def _load_period_weights():
    """读取 period_weights.json：{bucket: {factor_name: weight}}。不存在返回 None。"""
    if not os.path.exists(_WEIGHTS_FILE):
        return None
    try:
        with open(_WEIGHTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _bucket_of(name: str) -> str:
    return FACTOR_BUCKET.get(name, "medium")


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
    period_probs: Optional[dict] = None  # {short/medium/long: {...}}
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


def _prob_from_normalized(normalized: float) -> tuple[float, float, str]:
    """与 compute_probability 一致的线性映射（含 clip）。"""
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


def compute_period_probabilities(
    factors: list[FactorResult],
) -> dict[str, dict]:
    """分别按短 / 中 / 长 三个周期桶聚合因子，给出各自的净强度与涨跌概率。

    返回: {period: {"net_strength": float, "prob_up": float,
                    "prob_down": float, "trend": str, "signal": int}}
    signal: +1 偏多 / 0 中性 / -1 偏空
    当未生成 period_weights.json 时，回退到因子自带的 weight 字段。
    """
    pw = _load_period_weights()

    result: dict[str, dict] = {}
    for period in ("short", "medium", "long"):
        bucket_factors = [f for f in factors if _bucket_of(f.name) == period]
        if not bucket_factors:
            result[period] = {
                "net_strength": 0.0,
                "prob_up": 0.5,
                "prob_down": 0.5,
                "trend": "数据不足",
                "signal": 0,
            }
            continue

        total_weight = 0.0
        weighted_signal = 0.0
        for f in bucket_factors:
            if pw is not None and period in pw and f.name in pw[period]:
                w = pw[period][f.name]
            else:
                w = f.weight
            total_weight += w
            weighted_signal += f.signal * w

        normalized = weighted_signal / total_weight if total_weight > 0 else 0.0
        prob_up, prob_down, trend = _prob_from_normalized(normalized)
        signal = 0
        if normalized > 0.05:
            signal = 1
        elif normalized < -0.05:
            signal = -1

        result[period] = {
            "net_strength": round(normalized, 4),
            "prob_up": prob_up,
            "prob_down": prob_down,
            "trend": trend,
            "signal": signal,
        }

    return result
