# -*- coding: utf-8 -*-
"""量价类指标：OBV / VPT / ADL / MFI / Force Index / Chaikin。"""

from __future__ import annotations

from typing import Sequence

from .primitives import ema


def obv(closes: Sequence[float], volumes: Sequence[float]) -> list[float]:
    n = len(closes)
    if n == 0:
        return []
    out = [0.0]
    for i in range(1, n):
        if closes[i] > closes[i - 1]:
            out.append(out[-1] + volumes[i])
        elif closes[i] < closes[i - 1]:
            out.append(out[-1] - volumes[i])
        else:
            out.append(out[-1])
    return out


def vpt(closes: Sequence[float], volumes: Sequence[float]) -> list[float]:
    """成交量价格趋势"""
    n = len(closes)
    if n == 0:
        return []
    out = [0.0]
    for i in range(1, n):
        prev = closes[i - 1]
        ret = (closes[i] - prev) / prev if prev else 0.0
        out.append(out[-1] + volumes[i] * ret)
    return out


def adl(highs: Sequence[float], lows: Sequence[float],
        closes: Sequence[float], volumes: Sequence[float]) -> list[float]:
    """积累/分配线"""
    n = len(closes)
    if n == 0:
        return []
    out = [0.0]
    for i in range(1, n):
        rng = highs[i] - lows[i]
        if rng == 0:
            clv = 0.0
        else:
            clv = ((closes[i] - lows[i]) - (highs[i] - closes[i])) / rng * volumes[i]
        out.append(out[-1] + clv)
    return out


def mfi(highs: Sequence[float], lows: Sequence[float],
        closes: Sequence[float], volumes: Sequence[float],
        period: int = 14) -> list[float]:
    n = len(closes)
    out = [0.0] * n
    if n < period:
        return out
    tp = [(highs[i] + lows[i] + closes[i]) / 3 for i in range(n)]
    for i in range(period - 1, n):
        pos_flow = 0.0
        neg_flow = 0.0
        for j in range(i - period + 1, i + 1):
            prev_tp = tp[j - 1] if j > 0 else tp[j]
            if tp[j] > prev_tp:
                pos_flow += tp[j] * volumes[j]
            else:
                neg_flow += tp[j] * volumes[j]
        if neg_flow == 0:
            out[i] = 100.0
        else:
            ratio = pos_flow / neg_flow
            out[i] = 100 - 100 / (1 + ratio)
    return out


def force_index(closes: Sequence[float], volumes: Sequence[float],
                period: int = 1) -> list[float]:
    """Elder Force Index（period=1 为原始；period>1 为窗口求和，保持原项目行为）。"""
    n = len(closes)
    out = [0.0] * n
    if period == 1:
        for i in range(1, n):
            out[i] = closes[i] - closes[i - 1]
        return out
    for i in range(period, n):
        out[i] = sum(closes[j] - closes[j - 1] for j in range(i - period + 1, i + 1))
    return out


def chaikin_oscillator(highs: Sequence[float], lows: Sequence[float],
                       closes: Sequence[float], volumes: Sequence[float],
                       fast: int = 3, slow: int = 10) -> list[float]:
    adl_seq = adl(highs, lows, closes, volumes)
    ema_fast = ema(adl_seq, fast)
    ema_slow = ema(adl_seq, slow)
    return [ema_fast[i] - ema_slow[i] for i in range(len(adl_seq))]
