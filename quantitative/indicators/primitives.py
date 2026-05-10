# -*- coding: utf-8 -*-
"""基础原语。

`nan` 用 `float('nan')` 表示；调用方按需要决定是把 nan 段当 0 处理
还是过滤掉。所有函数都接收 `Sequence[float]`，返回 `list[float]`，
长度与输入一致。
"""

from __future__ import annotations

import math
from typing import Sequence

NAN = float("nan")


def sma(data: Sequence[float], period: int) -> list[float]:
    """简单移动平均；前 period-1 个位置为 NaN。"""
    n = len(data)
    out = [NAN] * n
    if period <= 0 or n < period:
        return out
    s = sum(data[:period])
    out[period - 1] = s / period
    for i in range(period, n):
        s += data[i] - data[i - period]
        out[i] = s / period
    return out


def ema(data: Sequence[float], period: int) -> list[float]:
    """指数移动平均；从首个数据点起递推（与原项目实现一致）。"""
    n = len(data)
    if n == 0:
        return []
    multiplier = 2.0 / (period + 1)
    out = [data[0]]
    for i in range(1, n):
        out.append(data[i] * multiplier + out[-1] * (1 - multiplier))
    return out


def rolling_std(data: Sequence[float], period: int,
                ddof: int = 0) -> list[float]:
    """滚动标准差；前 period-1 个位置为 NaN。"""
    n = len(data)
    out = [NAN] * n
    if period <= 0 or n < period:
        return out
    for i in range(period - 1, n):
        window = data[i - period + 1:i + 1]
        mean = sum(window) / period
        var = sum((x - mean) ** 2 for x in window) / max(period - ddof, 1)
        out[i] = math.sqrt(var)
    return out


def true_range(highs: Sequence[float], lows: Sequence[float],
               closes: Sequence[float]) -> list[float]:
    """真实波幅 TR_t = max(H_t, C_{t-1}) - min(L_t, C_{t-1})

    第一根 K 线没有前收，按 C_0 自填以保持长度。
    """
    n = len(closes)
    out: list[float] = []
    for i in range(n):
        c_prev = closes[i - 1] if i > 0 else closes[i]
        out.append(max(highs[i], c_prev) - min(lows[i], c_prev))
    return out


def plus_dm(highs: Sequence[float], lows: Sequence[float]) -> list[float]:
    """+DM 原始序列（未平滑）。"""
    n = len(highs)
    out = [0.0] * n
    for i in range(1, n):
        up = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]
        out[i] = max(up, 0.0) if up > down else 0.0
    return out


def minus_dm(highs: Sequence[float], lows: Sequence[float]) -> list[float]:
    """-DM 原始序列（未平滑）。"""
    n = len(highs)
    out = [0.0] * n
    for i in range(1, n):
        up = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]
        out[i] = max(down, 0.0) if down > up else 0.0
    return out


def wilder_smooth(data: Sequence[float], period: int) -> list[float]:
    """Wilder 平滑：S_t = S_{t-1} - S_{t-1}/period + X_t

    与项目原实现一致（首值取 X_0，未做窗口求和）；用于 ATR / +DI / -DI / ADX。
    """
    n = len(data)
    if n == 0:
        return []
    out = [data[0]]
    s = data[0]
    for i in range(1, n):
        s = s - s / period + data[i]
        out.append(s)
    return out


def simple_returns(closes: Sequence[float], period: int = 1) -> list[float]:
    """简单收益率 r_t = C_t / C_{t-period} - 1；前 period 个位置为 0.0。"""
    n = len(closes)
    out = [0.0] * n
    for i in range(period, n):
        prev = closes[i - period]
        out[i] = (closes[i] / prev - 1) if prev != 0 else 0.0
    return out


def log_returns(closes: Sequence[float], period: int = 1) -> list[float]:
    """对数收益率 ln(C_t / C_{t-period})；前 period 个位置为 0.0。"""
    n = len(closes)
    out = [0.0] * n
    for i in range(period, n):
        prev = closes[i - period]
        if prev > 0 and closes[i] > 0:
            out[i] = math.log(closes[i] / prev)
    return out
