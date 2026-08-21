# -*- coding: utf-8 -*-
"""流动性 / 资金面（B 类：从行情派生）指标。

所有函数均为 **纯函数**（序列输入 → 同长度序列输出），与
`indicators.volume` 同风格；前置不足窗口的位置写 0.0。

输出由 ``quantitative.features.FeatureCalculator`` 统一命名并物化。
"""

from __future__ import annotations

import math
from typing import Sequence


# ---------------------------------------------------------------------------
# 基础：滚动均值 / 滚动标准差（仅供本模块使用，不影响 primitives 的 NaN 语义）
# ---------------------------------------------------------------------------

def _rolling_mean_zero(data: Sequence[float], period: int) -> list[float]:
    """滚动均值；不足窗口位置写 0.0（非 NaN），便于入库。"""
    n = len(data)
    out = [0.0] * n
    if period <= 0 or n < period:
        return out
    s = sum(data[:period])
    out[period - 1] = s / period
    for i in range(period, n):
        s += data[i] - data[i - period]
        out[i] = s / period
    return out


def _rolling_std_zero(data: Sequence[float], period: int,
                      ddof: int = 0) -> list[float]:
    """滚动标准差；不足窗口位置写 0.0。"""
    n = len(data)
    out = [0.0] * n
    if period <= 0 or n < period:
        return out
    denom = max(period - ddof, 1)
    for i in range(period - 1, n):
        window = data[i - period + 1:i + 1]
        mean = sum(window) / period
        var = sum((x - mean) ** 2 for x in window) / denom
        out[i] = math.sqrt(var)
    return out


# ---------------------------------------------------------------------------
# 换手率派生
# ---------------------------------------------------------------------------

def turnover_rate_ma(turnover_rates: Sequence[float],
                     period: int) -> list[float]:
    """N 日换手率均值。"""
    return _rolling_mean_zero(turnover_rates, period)


def turnover_rate_zscore(turnover_rates: Sequence[float],
                         period: int = 20) -> list[float]:
    """当日换手率相对 N 日窗口的 Z 分：(today - μ) / σ。

    识别异常放量/缩量。σ=0 时写 0.0（窗口内完全平稳）。
    """
    n = len(turnover_rates)
    out = [0.0] * n
    if n < period:
        return out
    for i in range(period - 1, n):
        window = turnover_rates[i - period + 1:i + 1]
        mean = sum(window) / period
        var = sum((x - mean) ** 2 for x in window) / period
        std = math.sqrt(var)
        if std <= 0:
            continue
        out[i] = (turnover_rates[i] - mean) / std
    return out


# ---------------------------------------------------------------------------
# 成交额派生（ADTV = Average Daily Traded Value）
# ---------------------------------------------------------------------------

def amount_ma(turnovers: Sequence[float], period: int) -> list[float]:
    """N 日成交额均值 (ADTV_N)。"""
    return _rolling_mean_zero(turnovers, period)


def amount_ratio(turnovers: Sequence[float],
                 fast: int = 5, slow: int = 20) -> list[float]:
    """ADTV_fast / ADTV_slow；反映资金堆积速度。分母为 0 时写 0.0。"""
    fast_ma = _rolling_mean_zero(turnovers, fast)
    slow_ma = _rolling_mean_zero(turnovers, slow)
    n = len(turnovers)
    out = [0.0] * n
    for i in range(n):
        if slow_ma[i] > 0:
            out[i] = fast_ma[i] / slow_ma[i]
    return out


# ---------------------------------------------------------------------------
# Amihud 非流动性（滚动均值版）
# ---------------------------------------------------------------------------

def amihud_illiquidity_series(closes: Sequence[float],
                              turnovers: Sequence[float],
                              period: int = 20,
                              scale: float = 1e8) -> list[float]:
    """滚动 Amihud 非流动性：mean_{t-N+1..t}( |R_s| / Amount_s ) * scale。

    使用成交额 (turnover) 而非成交量 (volume) 做分母，量纲更稳定
    （跨股可比）。scale 默认 1e8 与 `risk.amihud_illiquidity_point`
    对齐。前 period 个位置写 0.0。
    """
    n = len(closes)
    out = [0.0] * n
    if n < period + 1:
        return out
    # 逐日 |R| / Amount
    daily = [0.0] * n
    for i in range(1, n):
        prev = closes[i - 1]
        amt = turnovers[i]
        if prev <= 0 or amt <= 0:
            continue
        daily[i] = abs(closes[i] / prev - 1) / amt * scale
    # 滚动均值
    for i in range(period, n):
        out[i] = sum(daily[i - period + 1:i + 1]) / period
    return out


def illiquidity_rank_series(amihud_values: Sequence[float],
                            lookback: int = 252) -> list[float]:
    """Amihud 在自身 `lookback` 日窗口内的百分位排名 ∈ [0, 1]。

    数值越大 → 当下越缺流动性（越不容易吃大单）。
    不足 `lookback` 个有效值时写 0.0。
    """
    n = len(amihud_values)
    out = [0.0] * n
    if n < lookback:
        return out
    for i in range(lookback - 1, n):
        window = amihud_values[i - lookback + 1:i + 1]
        cur = amihud_values[i]
        # 排名：当前值 ≤ window 中多少比例 → 等同百分位
        # 这里按"严格小于 + 等于一半"的 midrank 近似，避免并列值扎堆
        less = sum(1 for v in window if v < cur)
        equal = sum(1 for v in window if v == cur)
        out[i] = (less + 0.5 * equal) / lookback
    return out


# ---------------------------------------------------------------------------
# 量价关系
# ---------------------------------------------------------------------------

def vol_price_corr(closes: Sequence[float], turnovers: Sequence[float],
                   period: int = 20) -> list[float]:
    """滚动 N 日 (收益率, 成交额) 相关系数，∈ [-1, 1]。

    反映量价同向（放量上涨/缩量下跌 → 正相关）还是背离。
    不足窗口或方差为 0 时写 0.0。
    """
    n = len(closes)
    out = [0.0] * n
    if n < period + 1:
        return out
    # 先算 daily return 与 daily amount（amount 直接用 turnovers[i]）
    rets = [0.0] * n
    for i in range(1, n):
        prev = closes[i - 1]
        if prev > 0:
            rets[i] = closes[i] / prev - 1
    for i in range(period, n):
        r_win = rets[i - period + 1:i + 1]
        a_win = turnovers[i - period + 1:i + 1]
        m_r = sum(r_win) / period
        m_a = sum(a_win) / period
        cov = sum((r_win[k] - m_r) * (a_win[k] - m_a) for k in range(period)) / period
        var_r = sum((x - m_r) ** 2 for x in r_win) / period
        var_a = sum((x - m_a) ** 2 for x in a_win) / period
        denom = math.sqrt(var_r * var_a)
        if denom > 0:
            out[i] = cov / denom
    return out


def money_flow_strength(closes: Sequence[float], turnovers: Sequence[float],
                        period: int = 20) -> list[float]:
    """净资金强度（滚动 N 日）：

        Σ sign(R_t) * Amount_t / Σ Amount_t   ∈ [-1, 1]

    - 收盘涨 → 全部成交额记为流入；跌 → 全部记为流出；平 → 不计。
    - 是 MFI 的"简化 + 符号版"，但分母用成交额（单位元）而非
      成交量（股），跨股可比。
    """
    n = len(closes)
    out = [0.0] * n
    if n < period + 1:
        return out
    signed = [0.0] * n
    abs_amt = [0.0] * n
    for i in range(1, n):
        if closes[i] > closes[i - 1]:
            signed[i] = turnovers[i]
        elif closes[i] < closes[i - 1]:
            signed[i] = -turnovers[i]
        abs_amt[i] = turnovers[i]
    for i in range(period, n):
        num = sum(signed[i - period + 1:i + 1])
        den = sum(abs_amt[i - period + 1:i + 1])
        if den > 0:
            out[i] = num / den
    return out
