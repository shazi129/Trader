# -*- coding: utf-8 -*-
"""风险/波动类指标。

这些函数面向"单点取值"场景（quant_analyzer 的因子）也面向"序列计算"
场景（factor_batch 的批量回填），分别提供 `_point` 和 `_series` 两类
入口。Series 函数返回与 closes 同长度的列表，前置不足窗口的位置写 0.0。
"""

from __future__ import annotations

import math
from typing import Sequence


# ===========================================================================
# 单点：用于 QuantFactorEngine
# ===========================================================================

def historical_volatility_point(closes: Sequence[float], period: int = 20,
                                annualize: int = 252) -> float | None:
    """历史波动率（年化，%）。数据不足返回 None。"""
    n = len(closes)
    if n < period + 1:
        return None
    rets = []
    for i in range(n - period, n):
        if closes[i - 1] <= 0:
            return None
        rets.append(math.log(closes[i] / closes[i - 1]))
    mean_r = sum(rets) / period
    var = sum((r - mean_r) ** 2 for r in rets) / max(period - 1, 1)
    return math.sqrt(var) * math.sqrt(annualize) * 100


def max_drawdown_point(closes: Sequence[float]) -> float:
    """最大回撤（%）。"""
    n = len(closes)
    if n < 2:
        return 0.0
    peak = closes[0]
    md = 0.0
    for c in closes:
        if c > peak:
            peak = c
        if peak:
            dd = (peak - c) / peak
            if dd > md:
                md = dd
    return md * 100


def downside_deviation_point(closes: Sequence[float], period: int,
                             mar: float = 0.0) -> float:
    """下行偏差（用于 Sortino）。"""
    n = len(closes)
    if n < period + 1:
        return 0.0
    downsides = []
    for i in range(n - period, n):
        prev = closes[i - 1]
        if prev <= 0:
            continue
        ret = (closes[i] - prev) / prev
        if ret < mar:
            downsides.append((ret - mar) ** 2)
    if not downsides:
        return 0.0
    return math.sqrt(sum(downsides) / len(downsides))


def sharpe_point(closes: Sequence[float], period: int = 252,
                 risk_free: float = 0.0) -> float | None:
    n = len(closes)
    if n < period + 1:
        return None
    rets = []
    for i in range(n - period, n):
        prev = closes[i - 1]
        if prev <= 0:
            return None
        rets.append((closes[i] - prev) / prev)
    mean_r = sum(rets) / period
    var = sum((r - mean_r) ** 2 for r in rets) / max(period - 1, 1)
    std = math.sqrt(var)
    if std == 0:
        return None
    return (mean_r - risk_free / 252) / std * math.sqrt(252)


def sortino_point(closes: Sequence[float], period: int = 252,
                  risk_free: float = 0.0, mar: float = 0.0) -> float | None:
    n = len(closes)
    if n < period + 1:
        return None
    rets = []
    for i in range(n - period, n):
        prev = closes[i - 1]
        if prev <= 0:
            return None
        rets.append((closes[i] - prev) / prev)
    mean_r = sum(rets) / period
    dd = downside_deviation_point(closes, period, mar)
    if dd == 0:
        return None
    return (mean_r - risk_free / 252) / dd * math.sqrt(252)


def skewness_point(values: Sequence[float], period: int) -> float:
    if len(values) < period:
        return 0.0
    window = values[-period:]
    n = len(window)
    mean = sum(window) / n
    var = sum((x - mean) ** 2 for x in window) / n
    if var == 0:
        return 0.0
    std = math.sqrt(var)
    return sum((x - mean) ** 3 for x in window) / n / (std ** 3)


def kurtosis_point(values: Sequence[float], period: int) -> float:
    """超额峰度（excess kurtosis）。"""
    if len(values) < period:
        return 0.0
    window = values[-period:]
    n = len(window)
    mean = sum(window) / n
    var = sum((x - mean) ** 2 for x in window) / n
    if var == 0:
        return 0.0
    std = math.sqrt(var)
    return sum((x - mean) ** 4 for x in window) / n / (std ** 4) - 3


def amihud_illiquidity_point(closes: Sequence[float],
                             volumes: Sequence[float],
                             period: int = 20,
                             scale: float = 1e8) -> float:
    n = len(closes)
    if n < period + 1:
        return 0.0
    vals = []
    for i in range(n - period, n):
        if i == 0 or volumes[i] == 0:
            vals.append(0.0)
            continue
        prev = closes[i - 1]
        if prev <= 0:
            continue
        ret = abs((closes[i] - prev) / prev)
        vals.append(ret / volumes[i] * scale)
    return sum(vals) / len(vals) if vals else 0.0


def garman_klass_volatility_point(highs: Sequence[float], lows: Sequence[float],
                                  closes: Sequence[float], period: int = 20,
                                  annualize: int = 252) -> float | None:
    n = len(closes)
    if n < period:
        return None
    vals = []
    for i in range(n - period, n):
        if i == 0 or closes[i - 1] <= 0 or lows[i] <= 0:
            vals.append(0.0)
            continue
        log_hl = math.log(highs[i] / lows[i]) ** 2
        log_co = math.log(closes[i] / closes[i - 1]) ** 2
        vals.append(0.5 * log_hl - (2 * math.log(2) - 1) * log_co)
    return math.sqrt(sum(vals) / period) * math.sqrt(annualize) * 100


def parkinson_volatility_point(highs: Sequence[float], lows: Sequence[float],
                               period: int = 20,
                               annualize: int = 252) -> float | None:
    n = len(highs)
    if n < period:
        return None
    vals = []
    for i in range(n - period, n):
        if lows[i] <= 0:
            vals.append(0.0)
            continue
        vals.append(math.log(highs[i] / lows[i]) ** 2)
    return math.sqrt(sum(vals) / (4 * math.log(2) * period)) * math.sqrt(annualize) * 100


def rogers_satchell_volatility_point(highs: Sequence[float], lows: Sequence[float],
                                     closes: Sequence[float], period: int = 20,
                                     annualize: int = 252) -> float | None:
    n = len(closes)
    if n < period + 1:
        return None
    vals = []
    for i in range(n - period, n):
        if lows[i] <= 0 or closes[i - 1] <= 0:
            vals.append(0.0)
            continue
        log_hc = math.log(highs[i] / closes[i - 1])
        log_lo = math.log(lows[i] / closes[i - 1])
        vals.append(
            log_hc * math.log(highs[i] / closes[i])
            + log_lo * math.log(lows[i] / closes[i])
        )
    return math.sqrt(sum(vals) / period) * math.sqrt(annualize) * 100


def downside_volatility_point(closes: Sequence[float], period: int = 20,
                              annualize: int = 252) -> float:
    n = len(closes)
    if n < period + 1:
        return 0.0
    downsides = []
    for i in range(n - period, n):
        prev = closes[i - 1]
        if prev <= 0:
            continue
        ret = (closes[i] - prev) / prev
        if ret < 0:
            downsides.append(ret ** 2)
    if not downsides:
        return 0.0
    return math.sqrt(sum(downsides) / len(downsides)) * math.sqrt(annualize) * 100


# ===========================================================================
# 序列：用于 FactorSeriesEngine 批量回填
# ===========================================================================

def historical_volatility_series(closes: Sequence[float], period: int,
                                 annualize: int = 252) -> list[float]:
    """每根 K 线的滚动 HV（年化 %），不足窗口写 0.0。"""
    n = len(closes)
    out = [0.0] * n
    if n < period + 1:
        return out
    for i in range(period, n):
        rets = []
        ok = True
        for j in range(i - period + 1, i + 1):
            if closes[j - 1] <= 0:
                ok = False
                break
            rets.append(math.log(closes[j] / closes[j - 1]))
        if not ok or not rets:
            continue
        # 与原 factor_batch 实现保持一致：按 (n-1) 分母
        denom = period - 1 if period > 1 else 1
        std = (sum(r ** 2 for r in rets) / denom) ** 0.5
        out[i] = std * (annualize ** 0.5) * 100
    return out


def max_drawdown_series(closes: Sequence[float]) -> list[float]:
    """每根 K 线对应的"截至当下的最大回撤（%）"。"""
    n = len(closes)
    out = [0.0] * n
    if n == 0:
        return out
    peak = closes[0]
    for i, c in enumerate(closes):
        if c > peak:
            peak = c
        if peak:
            out[i] = (peak - c) / peak * 100
    return out


def rolling_sharpe_sortino_calmar(closes: Sequence[float],
                                  drawdown_series: Sequence[float],
                                  period: int = 252,
                                  annualize: int = 252):
    """滚动夏普 / 索提诺 / 卡玛；返回 (sharpe, sortino, calmar) 三个等长 list。

    与原 factor_batch.compute_risk_factors 行为对齐：
    - 需要 (period+1) 根 K 线起算；
    - sharpe 用 std (period-1) 分母，sortino 用 downsides 总数取均方再开方；
    - calmar = (close_t / close_{t-period} - 1) * 100 / max_drawdown[t]。
    """
    n = len(closes)
    sharpe = [0.0] * n
    sortino = [0.0] * n
    calmar = [0.0] * n
    if n < period + 1:
        return sharpe, sortino, calmar
    for i in range(period, n):
        rets = []
        for j in range(i - period + 1, i + 1):
            prev = closes[j - 1]
            if prev <= 0:
                rets = []
                break
            rets.append(closes[j] / prev - 1)
        if len(rets) != period:
            continue
        mean_r = sum(rets) / period
        denom = period - 1 if period > 1 else 1
        std_r = (sum((r - mean_r) ** 2 for r in rets) / denom) ** 0.5
        if std_r:
            sharpe[i] = (mean_r / std_r) * (annualize ** 0.5)
        downsides = [r ** 2 for r in rets if r < 0]
        dd = (sum(downsides) / period) ** 0.5 if downsides else 0.0
        if dd:
            sortino[i] = (mean_r / dd) * (annualize ** 0.5)
        if i >= period:
            prev_p = closes[i - period]
            ann_ret = (closes[i] / prev_p - 1) * 100 if prev_p else 0.0
            md = drawdown_series[i] if i < len(drawdown_series) else 0.0
            if md:
                calmar[i] = ann_ret / md
    return sharpe, sortino, calmar


def rolling_skew_kurt(closes: Sequence[float], period: int = 252):
    """滚动偏度 / 超额峰度，返回两个等长 list。"""
    n = len(closes)
    skew_out = [0.0] * n
    kurt_out = [0.0] * n
    if n < period + 1:
        return skew_out, kurt_out
    for i in range(period, n):
        rets = []
        ok = True
        for j in range(i - period + 1, i + 1):
            prev = closes[j - 1]
            if prev <= 0:
                ok = False
                break
            rets.append(closes[j] / prev - 1)
        if not ok:
            continue
        mean_r = sum(rets) / period
        var = sum((r - mean_r) ** 2 for r in rets) / period
        if var <= 0:
            continue
        std = var ** 0.5
        skew_out[i] = sum((r - mean_r) ** 3 for r in rets) / period / (std ** 3)
        kurt_out[i] = sum((r - mean_r) ** 4 for r in rets) / period / (std ** 4) - 3
    return skew_out, kurt_out
