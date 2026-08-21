"""Momentum and overbought/oversold signal rules."""

from __future__ import annotations

from .base import SignalContext, SignalRule


class RSIOversold(SignalRule):
    signal_id = "rsi_14_oversold"
    name = "RSI超卖"
    category = "momentum"

    def evaluate(self, context: SignalContext):
        value = context.latest.get("rsi_14")
        if value is None:
            return self.result(False, 0, description="RSI数据不足")
        active = value < 30
        return self.result(active, 1, value=value, description=f"RSI14={value:.2f}")


class RSIOverbought(SignalRule):
    signal_id = "rsi_14_overbought"
    name = "RSI超买"
    category = "momentum"

    def evaluate(self, context: SignalContext):
        value = context.latest.get("rsi_14")
        if value is None:
            return self.result(False, 0, description="RSI数据不足")
        active = value > 70
        return self.result(active, -1, value=value, description=f"RSI14={value:.2f}")


class PositiveMomentum(SignalRule):
    signal_id = "momentum_20_positive"
    name = "20日动量向上"
    category = "momentum"

    def evaluate(self, context: SignalContext):
        momentum = context.latest.get("momentum_20")
        ma5 = context.latest.get("ma_5")
        ma20 = context.latest.get("ma_20")
        if None in (momentum, ma5, ma20):
            return self.result(False, 0, description="动量数据不足")
        active = momentum > 0 and ma5 >= ma20
        return self.result(
            active, 1, value=momentum, description=f"20日动量={momentum:.2f}%"
        )


class NegativeMomentum(SignalRule):
    signal_id = "momentum_20_negative"
    name = "20日动量向下"
    category = "momentum"

    def evaluate(self, context: SignalContext):
        momentum = context.latest.get("momentum_20")
        ma5 = context.latest.get("ma_5")
        ma20 = context.latest.get("ma_20")
        if None in (momentum, ma5, ma20):
            return self.result(False, 0, description="动量数据不足")
        active = momentum < 0 and ma5 <= ma20
        return self.result(
            active, -1, value=momentum, description=f"20日动量={momentum:.2f}%"
        )
