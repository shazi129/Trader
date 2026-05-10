# -*- coding: utf-8 -*-
"""趋势类指标：MACD / ATR / ADX / DMI / 布林带。

返回值统一为同长度的 list（不足窗口的位置写 0.0 或 NaN，文档里说明）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .primitives import (
    NAN,
    ema,
    rolling_std,
    true_range,
    plus_dm,
    minus_dm,
    wilder_smooth,
)


# ---------- MACD ----------

@dataclass
class MACDResult:
    ema_fast: list[float]
    ema_slow: list[float]
    dif: list[float]
    dea: list[float]
    hist: list[float]


def macd(closes: Sequence[float], fast: int = 12, slow: int = 26,
         signal: int = 9) -> MACDResult:
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    dif = [ema_fast[i] - ema_slow[i] for i in range(len(closes))]
    dea = ema(dif, signal)
    hist = [dif[i] - dea[i] for i in range(len(closes))]
    return MACDResult(ema_fast, ema_slow, dif, dea, hist)


# ---------- ATR ----------

@dataclass
class ATRResult:
    tr: list[float]
    atr: list[float]
    atr_pct: list[float]  # ATR / Close * 100


def atr(highs: Sequence[float], lows: Sequence[float],
        closes: Sequence[float], period: int = 14) -> ATRResult:
    tr_seq = true_range(highs, lows, closes)
    atr_seq = wilder_smooth(tr_seq, period)
    pct = [
        (atr_seq[i] / closes[i] * 100) if closes[i] else 0.0
        for i in range(len(closes))
    ]
    return ATRResult(tr_seq, atr_seq, pct)


# ---------- ADX / DMI ----------

@dataclass
class ADXResult:
    plus_di: list[float]
    minus_di: list[float]
    adx: list[float]


def adx(highs: Sequence[float], lows: Sequence[float],
        closes: Sequence[float], period: int = 14) -> ADXResult:
    n = len(closes)
    tr_seq = true_range(highs, lows, closes)
    pdm_raw = plus_dm(highs, lows)
    mdm_raw = minus_dm(highs, lows)
    tr_n = wilder_smooth(tr_seq, period)
    pdm_n = wilder_smooth(pdm_raw, period)
    mdm_n = wilder_smooth(mdm_raw, period)

    pdi = [(pdm_n[i] / tr_n[i] * 100) if tr_n[i] else 0.0 for i in range(n)]
    mdi = [(mdm_n[i] / tr_n[i] * 100) if tr_n[i] else 0.0 for i in range(n)]
    dx = []
    for i in range(n):
        denom = pdi[i] + mdi[i]
        dx.append(100 * abs(pdi[i] - mdi[i]) / denom if denom else 0.0)
    adx_seq = wilder_smooth(dx, period)
    return ADXResult(pdi, mdi, adx_seq)


# ---------- 布林带 ----------

@dataclass
class BollingerResult:
    upper: list[float]
    lower: list[float]
    middle: list[float]


def bollinger(closes: Sequence[float], period: int = 20,
              k: float = 2.0) -> BollingerResult:
    n = len(closes)
    upper = [NAN] * n
    lower = [NAN] * n
    middle = [NAN] * n
    if n < period:
        return BollingerResult(upper, lower, middle)
    std_seq = rolling_std(closes, period, ddof=0)
    for i in range(period - 1, n):
        m = sum(closes[i - period + 1:i + 1]) / period
        s = std_seq[i]
        if s != s:  # nan
            continue
        middle[i] = m
        upper[i] = m + k * s
        lower[i] = m - k * s
    return BollingerResult(upper, lower, middle)
