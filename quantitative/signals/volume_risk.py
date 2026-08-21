"""Volume, liquidity, and volatility signal rules."""

from __future__ import annotations

from .base import SignalContext, SignalRule


class VolumeExpansion(SignalRule):
    signal_id = "bullish_volume_expansion"
    name = "上涨放量"
    category = "volume"

    def evaluate(self, context: SignalContext):
        ratio = context.latest.get("volume_ratio_20")
        momentum = context.latest.get("momentum_5")
        if ratio is None or momentum is None:
            return self.result(False, 0, description="量价数据不足")
        active = ratio > 1.2 and momentum > 0
        return self.result(
            active,
            1,
            value=ratio,
            description=f"量比={ratio:.2f}, 5日动量={momentum:.2f}%",
        )


class VolatilityContraction(SignalRule):
    signal_id = "volatility_contraction"
    name = "波动率收敛"
    category = "volatility"

    def evaluate(self, context: SignalContext):
        series = [
            value for value in context.feature_series("historical_volatility_20")
            if value is not None
        ]
        momentum = context.latest.get("momentum_10")
        if len(series) < 25 or momentum is None:
            return self.result(False, 0, description="波动率历史不足")
        current = series[-1]
        history = series[-25:-1]
        percentile = sum(value <= current for value in history) / len(history)
        contracting = percentile < 0.3 and current < series[-10]
        direction = 1 if momentum > 0 else -1 if momentum < 0 else 0
        active = contracting and direction != 0
        return self.result(
            active,
            direction,
            value=current,
            description=f"HV20={current:.2f}%, 历史分位={percentile:.1%}",
        )
