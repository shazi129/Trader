# -*- coding: utf-8 -*-
"""趋势 / 均线 / 布林带类因子。"""

from __future__ import annotations

import numpy as np

from quantitative.indicators.primitives import sma
from quantitative.indicators.trend import bollinger

from .base import BaseFactor, FactorContext, FactorOutput


class 均线多头排列(BaseFactor):
    """多头排列：MA5 > MA10 > MA20 > MA60，趋势向上，预测延续上涨。"""

    name = "均线多头排列"
    category = "trend"

    def detect(self, ctx: FactorContext) -> FactorOutput:
        if ctx.n < 65:
            return FactorOutput(name=self.name, category=self.category,
                                description="数据不足(<65日)")
        ma5 = sma(ctx.close, 5)[-1]
        ma10 = sma(ctx.close, 10)[-1]
        ma20 = sma(ctx.close, 20)[-1]
        ma60 = sma(ctx.close, 60)[-1]
        if any(np.isnan(x) for x in (ma5, ma10, ma20, ma60)):
            return FactorOutput(name=self.name, category=self.category,
                                description="均线计算未完成")
        triggered = ma5 > ma10 > ma20 > ma60
        direction = 1 if triggered else 0
        return FactorOutput(
            name=self.name, category=self.category,
            value=float(ma5 - ma60), signal=direction, direction=direction,
            description="均线多头排列" if triggered else "非多头排列",
            forecast=self._build_forecast(ctx, direction),
        )


class 均线空头排列(BaseFactor):
    """空头排列：MA5 < MA10 < MA20 < MA60，趋势向下，预测延续下跌。"""

    name = "均线空头排列"
    category = "trend"

    def detect(self, ctx: FactorContext) -> FactorOutput:
        if ctx.n < 65:
            return FactorOutput(name=self.name, category=self.category,
                                description="数据不足(<65日)")
        ma5 = sma(ctx.close, 5)[-1]
        ma10 = sma(ctx.close, 10)[-1]
        ma20 = sma(ctx.close, 20)[-1]
        ma60 = sma(ctx.close, 60)[-1]
        if any(np.isnan(x) for x in (ma5, ma10, ma20, ma60)):
            return FactorOutput(name=self.name, category=self.category,
                                description="均线计算未完成")
        triggered = ma5 < ma10 < ma20 < ma60
        direction = -1 if triggered else 0
        return FactorOutput(
            name=self.name, category=self.category,
            value=float(ma5 - ma60), signal=direction, direction=direction,
            description="均线空头排列" if triggered else "非空头排列",
            forecast=self._build_forecast(ctx, direction),
        )


class 布林带下轨支撑(BaseFactor):
    """价格触及/跌破布林带下轨：视为超卖支撑，预测反弹上涨。"""

    name = "布林带下轨支撑"
    category = "trend"

    def detect(self, ctx: FactorContext) -> FactorOutput:
        if ctx.n < 22:
            return FactorOutput(name=self.name, category=self.category,
                                description="数据不足")
        bb = bollinger(ctx.close, period=20, k=2.0)
        lower = bb.lower[-1]
        upper = bb.upper[-1]
        middle = bb.middle[-1]
        price = ctx.anchor_price
        if np.isnan(lower):
            return FactorOutput(name=self.name, category=self.category,
                                description="布林带未完成")
        # 触及下轨（价格在下轨以下 2% 或逼近）
        triggered = price <= lower * 1.02
        direction = 1 if triggered else 0
        return FactorOutput(
            name=self.name, category=self.category,
            value=float((price - lower) / middle if middle else 0),
            signal=direction, direction=direction,
            description=f"价/下轨={price/lower:.2f} 触及支撑" if triggered
            else f"价/下轨={price/lower:.2f} 未触及",
            forecast=self._build_forecast(ctx, direction),
        )


class 布林带上轨阻力(BaseFactor):
    """价格触及/突破布林带上轨：视为超买阻力，预测回落下跌。"""

    name = "布林带上轨阻力"
    category = "trend"

    def detect(self, ctx: FactorContext) -> FactorOutput:
        if ctx.n < 22:
            return FactorOutput(name=self.name, category=self.category,
                                description="数据不足")
        bb = bollinger(ctx.close, period=20, k=2.0)
        lower = bb.lower[-1]
        upper = bb.upper[-1]
        middle = bb.middle[-1]
        price = ctx.anchor_price
        if np.isnan(upper):
            return FactorOutput(name=self.name, category=self.category,
                                description="布林带未完成")
        triggered = price >= upper * 0.98
        direction = -1 if triggered else 0
        return FactorOutput(
            name=self.name, category=self.category,
            value=float((price - upper) / middle if middle else 0),
            signal=direction, direction=direction,
            description=f"价/上轨={price/upper:.2f} 触及阻力" if triggered
            else f"价/上轨={price/upper:.2f} 未触及",
            forecast=self._build_forecast(ctx, direction),
        )
