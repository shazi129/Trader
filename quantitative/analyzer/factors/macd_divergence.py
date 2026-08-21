# -*- coding: utf-8 -*-
"""MACD 背离类因子：顶背离 / 底背离。"""

from __future__ import annotations

import numpy as np
import pandas as pd

from quantitative.indicators.trend import macd

from .base import BaseFactor, FactorContext, FactorOutput


def _extrema(series: pd.Series, order: int = 5) -> tuple[pd.Series, pd.Series]:
    """返回局部极大 / 极小点（布尔掩码）。order 为左右窗口大小。"""
    if len(series) < order * 2 + 1:
        return series * False, series * False
    roll_max = series.rolling(order * 2 + 1, center=True, min_periods=1).max()
    roll_min = series.rolling(order * 2 + 1, center=True, min_periods=1).min()
    highs = series.eq(roll_max) & series.ne(series.shift(1))
    lows = series.eq(roll_min) & series.ne(series.shift(1))
    return highs, lows


class MACDTopDivergence(BaseFactor):
    """MACD 顶背离：价格创新高，但 MACD(DIF) 未创新高 → 看跌。"""

    name = "MACD顶背离"
    category = "pattern"

    def detect(self, ctx: FactorContext) -> FactorOutput:
        if ctx.n < 35:
            return FactorOutput(name=self.name, category=self.category,
                                description="数据不足")
        close = ctx.close.values
        macd_res = macd(ctx.df["close"], fast=12, slow=26, signal=9)
        dif = np.asarray(macd_res.dif, dtype=float)

        highs, _ = _extrema(pd.Series(close), order=5)
        hp = np.where(highs.values)[0]
        if len(hp) < 2:
            return FactorOutput(name=self.name, category=self.category,
                                value=0.0, signal=0,
                                description="未检测到有效价格高点")

        # 取最近两个高点
        i1, i2 = hp[-2], hp[-1]
        price_higher = close[i2] > close[i1]
        macd_lower = dif[i2] < dif[i1]

        triggered = bool(price_higher and macd_lower)
        direction = -1 if triggered else 0
        return FactorOutput(
            name=self.name,
            category=self.category,
            value=float(dif[i2] - dif[i1]),
            signal=direction,
            direction=direction,
            description=(
                "价格新高而MACD未新高，顶背离" if triggered
                else "未出现MACD顶背离"
            ),
            forecast=self._build_forecast(ctx, direction),
        )


class MACDBottomDivergence(BaseFactor):
    """MACD 底背离：价格创新低，但 MACD(DIF) 未创新低 → 看涨。"""

    name = "MACD底背离"
    category = "pattern"

    def detect(self, ctx: FactorContext) -> FactorOutput:
        if ctx.n < 35:
            return FactorOutput(name=self.name, category=self.category,
                                description="数据不足")
        close = ctx.close.values
        macd_res = macd(ctx.df["close"], fast=12, slow=26, signal=9)
        dif = np.asarray(macd_res.dif, dtype=float)

        _, lows = _extrema(pd.Series(close), order=5)
        lp = np.where(lows.values)[0]
        if len(lp) < 2:
            return FactorOutput(name=self.name, category=self.category,
                                value=0.0, signal=0,
                                description="未检测到有效价格低点")

        i1, i2 = lp[-2], lp[-1]
        price_lower = close[i2] < close[i1]
        macd_higher = dif[i2] > dif[i1]

        triggered = bool(price_lower and macd_higher)
        direction = 1 if triggered else 0
        return FactorOutput(
            name=self.name,
            category=self.category,
            value=float(dif[i2] - dif[i1]),
            signal=direction,
            direction=direction,
            description=(
                "价格新低而MACD未新低，底背离" if triggered
                else "未出现MACD底背离"
            ),
            forecast=self._build_forecast(ctx, direction),
        )
