# -*- coding: utf-8 -*-
"""动量/超买超卖类指标：RSI / KDJ / MOM / ROC / CCI / Williams %R。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .primitives import NAN


# ---------- RSI ----------

def rsi(closes: Sequence[float], period: int = 14,
        mode: str = "wilder") -> list[float]:
    """RSI（相对强弱指标）。

    :param mode:
        - ``"wilder"`` (默认)：标准 Wilder 递推平滑（教科书定义，更准确）。
        - ``"simple"``：每根 bar 用窗口内简单平均。

    返回长度为 ``len(closes)`` 的列表，前 ``period`` 个位置为 NaN。
    """
    n = len(closes)
    out = [NAN] * n
    if n <= period:
        return out
    gains = [0.0]
    losses = [0.0]
    for i in range(1, n):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))

    if mode == "simple":
        # 旧版兼容：每根 bar 用最近 period 根的简单平均
        for i in range(period, n):
            ag = sum(gains[i - period + 1:i + 1]) / period
            al = sum(losses[i - period + 1:i + 1]) / period
            out[i] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
        return out

    if mode != "wilder":
        raise ValueError(f"unknown rsi mode: {mode!r}, expected 'wilder' or 'simple'")

    # Wilder：首段用简单平均做种子，后续递推
    avg_gain = sum(gains[1:period + 1]) / period
    avg_loss = sum(losses[1:period + 1]) / period
    out[period] = 100.0 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss)
    for i in range(period + 1, n):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        out[i] = 100.0 if avg_loss == 0 else 100 - 100 / (1 + avg_gain / avg_loss)
    return out


# ---------- KDJ ----------

@dataclass
class KDJResult:
    k: list[float]
    d: list[float]
    j: list[float]


def kdj(highs: Sequence[float], lows: Sequence[float],
        closes: Sequence[float], period: int = 9) -> KDJResult:
    n = len(closes)
    k_vals: list[float] = []
    d_vals: list[float] = []
    j_vals: list[float] = []
    k_prev, d_prev = 50.0, 50.0
    for i in range(n):
        if i < period - 1:
            rsv = 50.0
        else:
            low_n = min(lows[i - period + 1:i + 1])
            high_n = max(highs[i - period + 1:i + 1])
            rsv = 50.0 if high_n == low_n else (closes[i] - low_n) / (high_n - low_n) * 100
        k_now = 2.0 / 3 * k_prev + 1.0 / 3 * rsv
        d_now = 2.0 / 3 * d_prev + 1.0 / 3 * k_now
        j_now = 3 * k_now - 2 * d_now
        k_vals.append(k_now)
        d_vals.append(d_now)
        j_vals.append(j_now)
        k_prev, d_prev = k_now, d_now
    return KDJResult(k_vals, d_vals, j_vals)


# ---------- 动量 / ROC ----------

def momentum_pct(closes: Sequence[float], period: int) -> list[float]:
    """N 日价格变化百分比 = (C_t / C_{t-N} - 1) * 100；不足为 0.0。"""
    n = len(closes)
    out = [0.0] * n
    for i in range(period, n):
        prev = closes[i - period]
        if prev:
            out[i] = (closes[i] / prev - 1) * 100
    return out


# ROC 与 momentum_pct 同义。
roc = momentum_pct


# ---------- CCI ----------

def cci(highs: Sequence[float], lows: Sequence[float],
        closes: Sequence[float], period: int = 20) -> list[float]:
    n = len(closes)
    tp = [(highs[i] + lows[i] + closes[i]) / 3 for i in range(n)]
    out = [0.0] * n
    for i in range(period - 1, n):
        window = tp[i - period + 1:i + 1]
        ma_tp = sum(window) / period
        md = sum(abs(x - ma_tp) for x in window) / period
        out[i] = (tp[i] - ma_tp) / (0.015 * md) if md else 0.0
    return out


# ---------- Williams %R ----------

def williams_r(highs: Sequence[float], lows: Sequence[float],
               closes: Sequence[float], period: int = 14) -> list[float]:
    """所有 bar 都返回有效值；窗口起步阶段用可用范围。"""
    n = len(closes)
    out: list[float] = []
    for i in range(n):
        start = max(0, i - period + 1)
        high_n = max(highs[start:i + 1])
        low_n = min(lows[start:i + 1])
        if high_n == low_n:
            out.append(-50.0)
        else:
            out.append((high_n - closes[i]) / (high_n - low_n) * -100)
    return out
