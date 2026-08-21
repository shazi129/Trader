"""Trend, band, and crossover signal rules."""

from __future__ import annotations

from .base import SignalContext, SignalRule


def _numbers(snapshot, *keys):
    values = tuple(snapshot.get(key) for key in keys)
    return values if all(value is not None for value in values) else None


def _previous_and_current(context: SignalContext, *keys):
    if context.previous is None:
        return None
    previous = _numbers(context.previous, *keys)
    current = _numbers(context.latest, *keys)
    if previous is None or current is None:
        return None
    return previous, current


def _bollinger_squeeze_before_latest(
    context: SignalContext,
    *,
    lookback: int = 60,
    percentile: float = 0.2,
) -> bool:
    """Whether the previous bar's bandwidth was historically compressed."""
    widths = context.feature_series("boll_width")
    if len(widths) < 3 or widths[-2] is None:
        return False
    history = [
        float(value)
        for value in widths[:-2][-lookback:]
        if value is not None
    ]
    if len(history) < 20:
        return False
    rank = sum(value <= float(widths[-2]) for value in history) / len(history)
    return rank <= percentile


def _standard_adx(value: float, period: int = 14) -> float:
    """Normalize the persisted Wilder sum to the conventional ADX scale."""
    return value / period


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


class PriceMA20CrossUp(SignalRule):
    signal_id = "price_ma_20_cross_up"
    name = "价格上穿MA20"
    category = "crossover"

    def evaluate(self, context: SignalContext):
        values = _previous_and_current(context, "price_to_ma_20")
        if values is None:
            return self.result(False, 0, description="价格/MA20数据不足")
        previous, current = values
        active = previous[0] <= 1.0 and current[0] > 1.0
        return self.result(
            active,
            1,
            value=current[0],
            description="收盘价向上穿越MA20" if active else "未上穿MA20",
        )


class PriceMA20CrossDown(SignalRule):
    signal_id = "price_ma_20_cross_down"
    name = "价格下穿MA20"
    category = "crossover"

    def evaluate(self, context: SignalContext):
        values = _previous_and_current(context, "price_to_ma_20")
        if values is None:
            return self.result(False, 0, description="价格/MA20数据不足")
        previous, current = values
        active = previous[0] >= 1.0 and current[0] < 1.0
        return self.result(
            active,
            -1,
            value=current[0],
            description="收盘价向下穿越MA20" if active else "未下穿MA20",
        )


class MALongTermGoldenCross(SignalRule):
    signal_id = "ma_60_200_golden_cross"
    name = "MA60/MA200金叉"
    category = "crossover"

    def evaluate(self, context: SignalContext):
        values = _previous_and_current(context, "ma_60", "ma_200")
        if values is None:
            return self.result(False, 0, description="中长期均线数据不足")
        previous, current = values
        active = previous[0] <= previous[1] and current[0] > current[1]
        return self.result(
            active,
            1,
            value=current[0] - current[1],
            description="MA60向上穿越MA200" if active else "未形成中长期金叉",
        )


class MALongTermDeathCross(SignalRule):
    signal_id = "ma_60_200_death_cross"
    name = "MA60/MA200死叉"
    category = "crossover"

    def evaluate(self, context: SignalContext):
        values = _previous_and_current(context, "ma_60", "ma_200")
        if values is None:
            return self.result(False, 0, description="中长期均线数据不足")
        previous, current = values
        active = previous[0] >= previous[1] and current[0] < current[1]
        return self.result(
            active,
            -1,
            value=current[0] - current[1],
            description="MA60向下穿越MA200" if active else "未形成中长期死叉",
        )


class DMIBullishCross(SignalRule):
    signal_id = "dmi_bullish_cross"
    name = "DMI多头交叉"
    category = "crossover"

    def evaluate(self, context: SignalContext):
        values = _previous_and_current(
            context, "plus_di_14", "minus_di_14", "adx_14"
        )
        if values is None:
            return self.result(False, 0, description="DMI/ADX数据不足")
        previous, current = values
        current_adx = _standard_adx(current[2])
        active = (
            previous[0] <= previous[1]
            and current[0] > current[1]
            and current_adx >= 25.0
        )
        return self.result(
            active,
            1,
            value=current_adx,
            description="+DI上穿-DI且ADX确认" if active else "DMI多头交叉未确认",
        )


class DMIBearishCross(SignalRule):
    signal_id = "dmi_bearish_cross"
    name = "DMI空头交叉"
    category = "crossover"

    def evaluate(self, context: SignalContext):
        values = _previous_and_current(
            context, "plus_di_14", "minus_di_14", "adx_14"
        )
        if values is None:
            return self.result(False, 0, description="DMI/ADX数据不足")
        previous, current = values
        current_adx = _standard_adx(current[2])
        active = (
            previous[0] >= previous[1]
            and current[0] < current[1]
            and current_adx >= 25.0
        )
        return self.result(
            active,
            -1,
            value=current_adx,
            description="-DI上穿+DI且ADX确认" if active else "DMI空头交叉未确认",
        )


class MACDZeroCrossUp(SignalRule):
    signal_id = "macd_zero_cross_up"
    name = "MACD上穿零轴"
    category = "crossover"

    def evaluate(self, context: SignalContext):
        values = _previous_and_current(context, "macd_dif")
        if values is None:
            return self.result(False, 0, description="MACD DIF数据不足")
        previous, current = values
        active = previous[0] <= 0.0 and current[0] > 0.0
        return self.result(
            active, 1, value=current[0],
            description="DIF向上穿越零轴" if active else "DIF未上穿零轴",
        )


class MACDZeroCrossDown(SignalRule):
    signal_id = "macd_zero_cross_down"
    name = "MACD下穿零轴"
    category = "crossover"

    def evaluate(self, context: SignalContext):
        values = _previous_and_current(context, "macd_dif")
        if values is None:
            return self.result(False, 0, description="MACD DIF数据不足")
        previous, current = values
        active = previous[0] >= 0.0 and current[0] < 0.0
        return self.result(
            active, -1, value=current[0],
            description="DIF向下穿越零轴" if active else "DIF未下穿零轴",
        )


class MACDBullishHistogramReexpand(SignalRule):
    signal_id = "macd_hist_bullish_reexpand"
    name = "MACD红柱重新放大"
    category = "momentum_change"

    def evaluate(self, context: SignalContext):
        if len(context.features) < 3:
            return self.result(False, 0, description="MACD柱历史不足")
        values = [snapshot.get("macd_hist") for snapshot in context.features[-3:]]
        if any(value is None for value in values):
            return self.result(False, 0, description="MACD柱数据不足")
        older, previous, current = (float(value) for value in values)
        active = older > previous > 0.0 and current > previous
        return self.result(
            active, 1, value=current,
            description="红柱缩短后重新放大" if active else "红柱未重新放大",
        )


class MACDBearishHistogramReexpand(SignalRule):
    signal_id = "macd_hist_bearish_reexpand"
    name = "MACD绿柱重新放大"
    category = "momentum_change"

    def evaluate(self, context: SignalContext):
        if len(context.features) < 3:
            return self.result(False, 0, description="MACD柱历史不足")
        values = [snapshot.get("macd_hist") for snapshot in context.features[-3:]]
        if any(value is None for value in values):
            return self.result(False, 0, description="MACD柱数据不足")
        older, previous, current = (float(value) for value in values)
        active = older < previous < 0.0 and current < previous
        return self.result(
            active, -1, value=current,
            description="绿柱缩短后重新放大" if active else "绿柱未重新放大",
        )


class BollingerSqueezeBreakoutUp(SignalRule):
    signal_id = "bollinger_squeeze_breakout_up"
    name = "布林带收口向上突破"
    category = "breakout"

    def evaluate(self, context: SignalContext):
        if context.previous is None or len(context.quotes) < 2:
            return self.result(False, 0, description="布林带历史不足")
        bands = _previous_and_current(context, "boll_upper", "boll_width")
        if bands is None:
            return self.result(False, 0, description="布林带数据不足")
        previous, current = bands
        previous_close = float(context.quotes[-2].close)
        current_close = context.anchor_price
        active = (
            _bollinger_squeeze_before_latest(context)
            and previous_close <= previous[0]
            and current_close > current[0]
        )
        return self.result(
            active, 1, value=current[1],
            description="低带宽后收盘价突破上轨" if active else "未形成收口向上突破",
        )


class BollingerSqueezeBreakoutDown(SignalRule):
    signal_id = "bollinger_squeeze_breakout_down"
    name = "布林带收口向下突破"
    category = "breakout"

    def evaluate(self, context: SignalContext):
        if context.previous is None or len(context.quotes) < 2:
            return self.result(False, 0, description="布林带历史不足")
        bands = _previous_and_current(context, "boll_lower", "boll_width")
        if bands is None:
            return self.result(False, 0, description="布林带数据不足")
        previous, current = bands
        previous_close = float(context.quotes[-2].close)
        current_close = context.anchor_price
        active = (
            _bollinger_squeeze_before_latest(context)
            and previous_close >= previous[0]
            and current_close < current[0]
        )
        return self.result(
            active, -1, value=current[1],
            description="低带宽后收盘价跌破下轨" if active else "未形成收口向下突破",
        )


class BollingerLowerReentry(SignalRule):
    signal_id = "bollinger_lower_reentry"
    name = "布林带下轨假跌破回归"
    category = "reversal"

    def evaluate(self, context: SignalContext):
        if context.previous is None or len(context.quotes) < 2:
            return self.result(False, 0, description="布林带历史不足")
        bands = _previous_and_current(context, "boll_lower")
        if bands is None:
            return self.result(False, 0, description="布林带数据不足")
        previous, current = bands
        active = (
            float(context.quotes[-2].close) < previous[0]
            and context.anchor_price >= current[0]
        )
        return self.result(
            active, 1, value=context.anchor_price / current[0] if current[0] else None,
            description="跌破下轨后重新收回带内" if active else "未形成下轨回归",
        )


class BollingerUpperReentry(SignalRule):
    signal_id = "bollinger_upper_reentry"
    name = "布林带上轨假突破回归"
    category = "reversal"

    def evaluate(self, context: SignalContext):
        if context.previous is None or len(context.quotes) < 2:
            return self.result(False, 0, description="布林带历史不足")
        bands = _previous_and_current(context, "boll_upper")
        if bands is None:
            return self.result(False, 0, description="布林带数据不足")
        previous, current = bands
        active = (
            float(context.quotes[-2].close) > previous[0]
            and context.anchor_price <= current[0]
        )
        return self.result(
            active, -1, value=context.anchor_price / current[0] if current[0] else None,
            description="突破上轨后重新落回带内" if active else "未形成上轨回归",
        )
