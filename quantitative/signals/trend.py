"""Trend, band, and crossover signal rules."""

from __future__ import annotations

from .base import SignalContext, SignalRule


def _numbers(snapshot, *keys):
    values = tuple(snapshot.get(key) for key in keys)
    return values if all(value is not None for value in values) else None


class BullishMAAlignment(SignalRule):
    signal_id = "ma_alignment_bullish"
    name = "均线多头排列"
    category = "trend"

    def evaluate(self, context: SignalContext):
        values = _numbers(context.latest, "ma_5", "ma_10", "ma_20", "ma_60")
        if values is None:
            return self.result(False, 0, description="均线数据不足")
        active = values[0] > values[1] > values[2] > values[3]
        return self.result(
            active,
            1,
            value=values[0] - values[3],
            description="MA5>MA10>MA20>MA60" if active else "未形成多头排列",
        )


class BearishMAAlignment(SignalRule):
    signal_id = "ma_alignment_bearish"
    name = "均线空头排列"
    category = "trend"

    def evaluate(self, context: SignalContext):
        values = _numbers(context.latest, "ma_5", "ma_10", "ma_20", "ma_60")
        if values is None:
            return self.result(False, 0, description="均线数据不足")
        active = values[0] < values[1] < values[2] < values[3]
        return self.result(
            active,
            -1,
            value=values[0] - values[3],
            description="MA5<MA10<MA20<MA60" if active else "未形成空头排列",
        )


class BollingerLowerTouch(SignalRule):
    signal_id = "bollinger_lower_touch"
    name = "布林带下轨支撑"
    category = "reversal"

    def evaluate(self, context: SignalContext):
        lower = context.latest.get("boll_lower")
        if lower in (None, 0):
            return self.result(False, 0, description="布林带数据不足")
        ratio = context.anchor_price / lower
        active = ratio <= 1.02
        return self.result(
            active, 1, value=ratio, description=f"价格/下轨={ratio:.3f}"
        )


class BollingerUpperTouch(SignalRule):
    signal_id = "bollinger_upper_touch"
    name = "布林带上轨阻力"
    category = "reversal"

    def evaluate(self, context: SignalContext):
        upper = context.latest.get("boll_upper")
        if upper in (None, 0):
            return self.result(False, 0, description="布林带数据不足")
        ratio = context.anchor_price / upper
        active = ratio >= 0.98
        return self.result(
            active, -1, value=ratio, description=f"价格/上轨={ratio:.3f}"
        )


class MAGoldenCross(SignalRule):
    signal_id = "ma_5_20_golden_cross"
    name = "MA5/MA20金叉"
    category = "crossover"

    def evaluate(self, context: SignalContext):
        if context.previous is None:
            return self.result(False, 0, description="前一交易日数据不足")
        previous = _numbers(context.previous, "ma_5", "ma_20")
        current = _numbers(context.latest, "ma_5", "ma_20")
        if previous is None or current is None:
            return self.result(False, 0, description="均线数据不足")
        active = previous[0] <= previous[1] and current[0] > current[1]
        return self.result(active, 1, value=current[0] - current[1], description="MA5向上穿越MA20" if active else "未金叉")


class MADeathCross(SignalRule):
    signal_id = "ma_5_20_death_cross"
    name = "MA5/MA20死叉"
    category = "crossover"

    def evaluate(self, context: SignalContext):
        if context.previous is None:
            return self.result(False, 0, description="前一交易日数据不足")
        previous = _numbers(context.previous, "ma_5", "ma_20")
        current = _numbers(context.latest, "ma_5", "ma_20")
        if previous is None or current is None:
            return self.result(False, 0, description="均线数据不足")
        active = previous[0] >= previous[1] and current[0] < current[1]
        return self.result(active, -1, value=current[0] - current[1], description="MA5向下穿越MA20" if active else "未死叉")


class MACDGoldenCross(SignalRule):
    signal_id = "macd_golden_cross"
    name = "MACD金叉"
    category = "crossover"

    def evaluate(self, context: SignalContext):
        if context.previous is None:
            return self.result(False, 0, description="前一交易日数据不足")
        previous = _numbers(context.previous, "macd_dif", "macd_dea")
        current = _numbers(context.latest, "macd_dif", "macd_dea")
        if previous is None or current is None:
            return self.result(False, 0, description="MACD数据不足")
        active = previous[0] <= previous[1] and current[0] > current[1]
        return self.result(active, 1, value=current[0] - current[1], description="DIF向上穿越DEA" if active else "未金叉")


class MACDDeathCross(SignalRule):
    signal_id = "macd_death_cross"
    name = "MACD死叉"
    category = "crossover"

    def evaluate(self, context: SignalContext):
        if context.previous is None:
            return self.result(False, 0, description="前一交易日数据不足")
        previous = _numbers(context.previous, "macd_dif", "macd_dea")
        current = _numbers(context.latest, "macd_dif", "macd_dea")
        if previous is None or current is None:
            return self.result(False, 0, description="MACD数据不足")
        active = previous[0] >= previous[1] and current[0] < current[1]
        return self.result(active, -1, value=current[0] - current[1], description="DIF向下穿越DEA" if active else "未死叉")
