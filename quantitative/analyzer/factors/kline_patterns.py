# -*- coding: utf-8 -*-
"""K 线形态类因子：双顶 / 双底 等。"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .base import BaseFactor, FactorContext, FactorOutput


class DoubleTop(BaseFactor):
    """K 线双顶：价格两次上探相近高位后回落，中间有显著回撤 → 看跌。"""

    name = "K线双顶"
    category = "pattern"

    def detect(self, ctx: FactorContext) -> FactorOutput:
        look = min(ctx.n, 60)
        if look < 20:
            return FactorOutput(name=self.name, category=self.category,
                                description="数据不足")
        close = ctx.close.values[-look:]
        highs, _ = _local_highs(pd.Series(close), order=3)
        hp = np.where(highs.values)[0]
        if len(hp) < 2:
            return FactorOutput(name=self.name, category=self.category,
                                signal=0, description="未检测到双顶形态")

        # 取最后两个高点
        i1, i2 = hp[-2], hp[-1]
        p1, p2 = close[i1], close[i2]
        peak_avg = (p1 + p2) / 2.0
        # 两顶高度接近（偏差 < 3%）
        similar = abs(p1 - p2) / peak_avg < 0.03
        # 中间有显著回撤（谷底比两顶低 > 3%）
        trough = close[i1:i2 + 1].min()
        pullback = (peak_avg - trough) / peak_avg
        # 第二顶后已回落（当前价低于第二顶）
        declined = close[-1] < p2 * 0.99

        triggered = bool(similar and pullback > 0.03 and declined)
        direction = -1 if triggered else 0
        return FactorOutput(
            name=self.name,
            category=self.category,
            value=float(pullback),
            signal=direction,
            direction=direction,
            description=(
                f"双顶形态(回撤{pullback*100:.1f}%)" if triggered
                else "未出现双顶形态"
            ),
            forecast=self._build_forecast(ctx, direction),
        )


def _local_highs(series: pd.Series, order: int = 3) -> tuple[pd.Series, pd.Series]:
    if len(series) < order * 2 + 1:
        return series * False, series * False
    roll_max = series.rolling(order * 2 + 1, center=True, min_periods=1).max()
    roll_min = series.rolling(order * 2 + 1, center=True, min_periods=1).min()
    highs = series.eq(roll_max) & series.ne(series.shift(1))
    lows = series.eq(roll_min) & series.ne(series.shift(1))
    return highs, lows
