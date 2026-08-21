"""Momentum and overbought/oversold signal rules."""

from __future__ import annotations

from .base import SignalContext, SignalRule


def _previous_and_current(context: SignalContext, *keys):
    if context.previous is None:
        return None
    previous = tuple(context.previous.get(key) for key in keys)
    current = tuple(context.latest.get(key) for key in keys)
    if any(value is None for value in previous + current):
        return None
    return previous, current


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


class KDJOversoldGoldenCross(SignalRule):
    signal_id = "kdj_oversold_golden_cross"
    name = "KDJ低位金叉"
    category = "crossover"

    def evaluate(self, context: SignalContext):
        values = _previous_and_current(context, "kdj_k", "kdj_d")
        if values is None:
            return self.result(False, 0, description="KDJ数据不足")
        previous, current = values
        active = previous[0] <= previous[1] and current[0] > current[1] and previous[0] < 20
        return self.result(
            active, 1, value=current[0] - current[1],
            description="K值在低位向上穿越D值" if active else "未形成KDJ低位金叉",
        )


class KDJOverboughtDeathCross(SignalRule):
    signal_id = "kdj_overbought_death_cross"
    name = "KDJ高位死叉"
    category = "crossover"

    def evaluate(self, context: SignalContext):
        values = _previous_and_current(context, "kdj_k", "kdj_d")
        if values is None:
            return self.result(False, 0, description="KDJ数据不足")
        previous, current = values
        active = previous[0] >= previous[1] and current[0] < current[1] and previous[0] > 80
        return self.result(
            active, -1, value=current[0] - current[1],
            description="K值在高位向下穿越D值" if active else "未形成KDJ高位死叉",
        )


class RSIOversoldExit(SignalRule):
    signal_id = "rsi_14_oversold_exit"
    name = "RSI离开超卖区"
    category = "reversal"

    def evaluate(self, context: SignalContext):
        values = _previous_and_current(context, "rsi_14")
        if values is None:
            return self.result(False, 0, description="RSI数据不足")
        previous, current = values
        active = previous[0] <= 30.0 and current[0] > 30.0
        return self.result(
            active, 1, value=current[0],
            description="RSI向上离开超卖区" if active else "RSI未离开超卖区",
        )


class RSIOverboughtExit(SignalRule):
    signal_id = "rsi_14_overbought_exit"
    name = "RSI离开超买区"
    category = "reversal"

    def evaluate(self, context: SignalContext):
        values = _previous_and_current(context, "rsi_14")
        if values is None:
            return self.result(False, 0, description="RSI数据不足")
        previous, current = values
        active = previous[0] >= 70.0 and current[0] < 70.0
        return self.result(
            active, -1, value=current[0],
            description="RSI向下离开超买区" if active else "RSI未离开超买区",
        )


class MFIOversoldExit(SignalRule):
    signal_id = "mfi_14_oversold_exit"
    name = "MFI离开超卖区"
    category = "reversal"

    def evaluate(self, context: SignalContext):
        values = _previous_and_current(context, "mfi_14")
        if values is None:
            return self.result(False, 0, description="MFI数据不足")
        previous, current = values
        active = previous[0] <= 20.0 and current[0] > 20.0
        return self.result(
            active, 1, value=current[0],
            description="MFI向上离开超卖区" if active else "MFI未离开超卖区",
        )


class MFIOverboughtExit(SignalRule):
    signal_id = "mfi_14_overbought_exit"
    name = "MFI离开超买区"
    category = "reversal"

    def evaluate(self, context: SignalContext):
        values = _previous_and_current(context, "mfi_14")
        if values is None:
            return self.result(False, 0, description="MFI数据不足")
        previous, current = values
        active = previous[0] >= 80.0 and current[0] < 80.0
        return self.result(
            active, -1, value=current[0],
            description="MFI向下离开超买区" if active else "MFI未离开超买区",
        )


class CCITrendBreakoutUp(SignalRule):
    signal_id = "cci_20_breakout_up"
    name = "CCI上穿+100"
    category = "breakout"

    def evaluate(self, context: SignalContext):
        values = _previous_and_current(context, "cci_20")
        if values is None:
            return self.result(False, 0, description="CCI数据不足")
        previous, current = values
        active = previous[0] <= 100.0 and current[0] > 100.0
        return self.result(
            active, 1, value=current[0],
            description="CCI向上突破+100" if active else "CCI未上穿+100",
        )


class CCITrendBreakoutDown(SignalRule):
    signal_id = "cci_20_breakout_down"
    name = "CCI下穿-100"
    category = "breakout"

    def evaluate(self, context: SignalContext):
        values = _previous_and_current(context, "cci_20")
        if values is None:
            return self.result(False, 0, description="CCI数据不足")
        previous, current = values
        active = previous[0] >= -100.0 and current[0] < -100.0
        return self.result(
            active, -1, value=current[0],
            description="CCI向下突破-100" if active else "CCI未下穿-100",
        )


class CCIOversoldExit(SignalRule):
    signal_id = "cci_20_oversold_exit"
    name = "CCI离开超卖区"
    category = "reversal"

    def evaluate(self, context: SignalContext):
        values = _previous_and_current(context, "cci_20")
        if values is None:
            return self.result(False, 0, description="CCI数据不足")
        previous, current = values
        active = previous[0] <= -100.0 and current[0] > -100.0
        return self.result(
            active, 1, value=current[0],
            description="CCI向上离开-100" if active else "CCI未离开超卖区",
        )


class CCIOverboughtExit(SignalRule):
    signal_id = "cci_20_overbought_exit"
    name = "CCI离开超买区"
    category = "reversal"

    def evaluate(self, context: SignalContext):
        values = _previous_and_current(context, "cci_20")
        if values is None:
            return self.result(False, 0, description="CCI数据不足")
        previous, current = values
        active = previous[0] >= 100.0 and current[0] < 100.0
        return self.result(
            active, -1, value=current[0],
            description="CCI向下离开+100" if active else "CCI未离开超买区",
        )


class WilliamsROversoldExit(SignalRule):
    signal_id = "williams_r_14_oversold_exit"
    name = "Williams %R离开超卖区"
    category = "reversal"

    def evaluate(self, context: SignalContext):
        values = _previous_and_current(context, "williams_r_14")
        if values is None:
            return self.result(False, 0, description="Williams %R数据不足")
        previous, current = values
        active = previous[0] <= -80.0 and current[0] > -80.0
        return self.result(
            active, 1, value=current[0],
            description="Williams %R向上离开超卖区" if active else "未离开超卖区",
        )


class WilliamsROverboughtExit(SignalRule):
    signal_id = "williams_r_14_overbought_exit"
    name = "Williams %R离开超买区"
    category = "reversal"

    def evaluate(self, context: SignalContext):
        values = _previous_and_current(context, "williams_r_14")
        if values is None:
            return self.result(False, 0, description="Williams %R数据不足")
        previous, current = values
        active = previous[0] >= -20.0 and current[0] < -20.0
        return self.result(
            active, -1, value=current[0],
            description="Williams %R向下离开超买区" if active else "未离开超买区",
        )
