# -*- coding: utf-8 -*-
"""量能 / 波动率类因子。"""

from __future__ import annotations

import numpy as np

from quantitative.indicators.volume import obv, vpt
from quantitative.indicators.primitives import sma
from quantitative.indicators.risk import historical_volatility_series
from quantitative.indicators.momentum import momentum_pct

from .base import BaseFactor, FactorContext, FactorOutput


class 量能放大配合(BaseFactor):
    """量价配合：价格上涨 + 放量（OBV/VPT 上行且成交量高于均值），看涨。"""

    name = "量能放大配合"
    category = "volume"

    def detect(self, ctx: FactorContext) -> FactorOutput:
        if ctx.n < 20:
            return FactorOutput(name=self.name, category=self.category,
                                description="数据不足")
        obv_seq = obv(ctx.close, ctx.volume)
        vpt_seq = vpt(ctx.close, ctx.volume)
        if len(obv_seq) < 2:
            return FactorOutput(name=self.name, category=self.category,
                                description="量能数据不足")
        # OBV / VPT 近 5 日趋势
        obv_slope = obv_seq[-1] - obv_seq[-6] if len(obv_seq) >= 6 else 0.0
        vpt_slope = vpt_seq[-1] - vpt_seq[-6] if len(vpt_seq) >= 6 else 0.0
        # 成交量是否高于 20 日均量
        vol_ma = sma(ctx.volume, 20)[-1]
        vol_ratio = ctx.volume.iloc[-1] / vol_ma if vol_ma and vol_ma > 0 else 1.0
        price_up = momentum_pct(ctx.close, 5)[-1] > 0
        triggered = (obv_slope > 0 or vpt_slope > 0) and vol_ratio > 1.2 and price_up
        direction = 1 if triggered else 0
        return FactorOutput(
            name=self.name, category=self.category,
            value=float(vol_ratio), signal=direction, direction=direction,
            description=f"量比={vol_ratio:.1f} 量价{'配合' if triggered else '不配合'}",
            forecast=self._build_forecast(ctx, direction),
        )


class 波动率收敛突破(BaseFactor):
    """波动率收敛：HV 处于低位且持续下降，往往酝酿突破。

    突破方向由近期短动量决定（涨→向上突破看多，跌→向下突破看空）。
    """

    name = "波动率收敛突破"
    category = "volatility"

    def detect(self, ctx: FactorContext) -> FactorOutput:
        if ctx.n < 45:
            return FactorOutput(name=self.name, category=self.category,
                                description="数据不足")
        hv = historical_volatility_series(ctx.close, period=20, annualize=252)
        if len(hv) < 25 or np.isnan(hv[-1]):
            return FactorOutput(name=self.name, category=self.category,
                                description="HV 未完成")
        cur_hv = hv[-1]
        # 相对过去 20 日 HV 的分位
        hist = hv[-25:-1]
        hist = [x for x in hist if not np.isnan(x)]
        if not hist:
            return FactorOutput(name=self.name, category=self.category,
                                description="HV 历史不足")
        pct_rank = sum(1 for x in hist if x >= cur_hv) / len(hist)
        # 收敛：当前 HV 处于低位（< 历史 30% 分位）且近期 HV 下降
        hv_trend_down = hv[-1] < hv[-10]
        converged = pct_rank < 0.3 and hv_trend_down
        if not converged:
            direction = 0
        else:
            # 方向由 10 日动量决定
            mom10 = momentum_pct(ctx.close, 10)[-1]
            direction = 1 if mom10 > 0 else (-1 if mom10 < 0 else 0)
        return FactorOutput(
            name=self.name, category=self.category,
            value=float(cur_hv), signal=direction, direction=direction,
            description=f"HV={cur_hv:.0f}% 分位={pct_rank*100:.0f}% "
            f"{'收敛' if converged else '未收敛'}",
            forecast=self._build_forecast(ctx, direction),
        )
