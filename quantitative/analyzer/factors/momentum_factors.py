# -*- coding: utf-8 -*-
"""动量 / 超买超卖类因子。"""

from __future__ import annotations

import numpy as np

from quantitative.indicators.momentum import rsi, momentum_pct
from quantitative.indicators.primitives import sma

from .base import BaseFactor, FactorContext, FactorOutput


class RSI超卖反弹(BaseFactor):
    """RSI 超卖：RSI < 30 视为超卖，预测未来反弹上涨。"""

    name = "RSI超卖反弹"
    category = "momentum"

    def detect(self, ctx: FactorContext) -> FactorOutput:
        if ctx.n < 20:
            return FactorOutput(name=self.name, category=self.category,
                                description="数据不足")
        rsi_vals = rsi(ctx.close, period=14)
        r = rsi_vals[-1]
        if np.isnan(r):
            r = 50.0
        triggered = r < 30
        direction = 1 if triggered else 0
        return FactorOutput(
            name=self.name, category=self.category,
            value=float(r), signal=direction, direction=direction,
            description=f"RSI={r:.1f}{' 超卖' if triggered else ''}" if triggered
            else f"RSI={r:.1f} 未超卖",
            forecast=self._build_forecast(ctx, direction),
        )


class RSI超买回落(BaseFactor):
    """RSI 超买：RSI > 70 视为超买，预测未来回落下跌。"""

    name = "RSI超买回落"
    category = "momentum"

    def detect(self, ctx: FactorContext) -> FactorOutput:
        if ctx.n < 20:
            return FactorOutput(name=self.name, category=self.category,
                                description="数据不足")
        rsi_vals = rsi(ctx.close, period=14)
        r = rsi_vals[-1]
        if np.isnan(r):
            r = 50.0
        triggered = r > 70
        direction = -1 if triggered else 0
        return FactorOutput(
            name=self.name, category=self.category,
            value=float(r), signal=direction, direction=direction,
            description=f"RSI={r:.1f} 超买" if triggered
            else f"RSI={r:.1f} 未超买",
            forecast=self._build_forecast(ctx, direction),
        )


class 动量向上(BaseFactor):
    """N 日价格动量为正：近期上涨动能，预测延续上涨。"""

    name = "动量向上"
    category = "momentum"

    def detect(self, ctx: FactorContext) -> FactorOutput:
        if ctx.n < 25:
            return FactorOutput(name=self.name, category=self.category,
                                description="数据不足")
        mom = momentum_pct(ctx.close, period=20)[-1]
        # 同时看短期均线方向
        ma5 = sma(ctx.close, 5)[-1]
        ma20 = sma(ctx.close, 20)[-1]
        triggered = mom > 0 and (not np.isnan(ma5)) and ma5 >= ma20
        direction = 1 if triggered else 0
        return FactorOutput(
            name=self.name, category=self.category,
            value=float(mom), signal=direction, direction=direction,
            description=f"20日动量={mom:.1f}%{' 向上' if triggered else ''}",
            forecast=self._build_forecast(ctx, direction),
        )


class 动量向下(BaseFactor):
    """N 日价格动量为负：近期下跌动能，预测延续下跌。"""

    name = "动量向下"
    category = "momentum"

    def detect(self, ctx: FactorContext) -> FactorOutput:
        if ctx.n < 25:
            return FactorOutput(name=self.name, category=self.category,
                                description="数据不足")
        mom = momentum_pct(ctx.close, period=20)[-1]
        ma5 = sma(ctx.close, 5)[-1]
        ma20 = sma(ctx.close, 20)[-1]
        triggered = mom < 0 and (not np.isnan(ma5)) and ma5 <= ma20
        direction = -1 if triggered else 0
        return FactorOutput(
            name=self.name, category=self.category,
            value=float(mom), signal=direction, direction=direction,
            description=f"20日动量={mom:.1f}%{' 向下' if triggered else ''}",
            forecast=self._build_forecast(ctx, direction),
        )
