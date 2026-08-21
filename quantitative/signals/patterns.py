"""Price and indicator divergence pattern rules."""

from __future__ import annotations

from .base import SignalContext, SignalRule


def _extrema(values: list[float], order: int, find_high: bool) -> list[int]:
    points: list[int] = []
    for index in range(order, len(values) - order):
        window = values[index - order:index + order + 1]
        target = max(window) if find_high else min(window)
        if values[index] == target:
            points.append(index)
    return points


def _is_recent(index: int, size: int, bars: int = 20) -> bool:
    """Keep event-style patterns from remaining active indefinitely."""
    return index >= size - bars


def _indicator_divergence(
    context: SignalContext,
    feature_key: str,
    *,
    find_high: bool,
) -> tuple[bool, float, int, int] | None:
    closes = [float(quote.close) for quote in context.quotes]
    indicator = context.feature_series(feature_key)
    points = _extrema(closes, 5, find_high)
    points = [index for index in points if indicator[index] is not None]
    if len(points) < 2:
        return None
    first, second = points[-2:]
    price_diverges = (
        closes[second] > closes[first]
        if find_high
        else closes[second] < closes[first]
    )
    indicator_diverges = (
        float(indicator[second]) < float(indicator[first])
        if find_high
        else float(indicator[second]) > float(indicator[first])
    )
    active = (
        _is_recent(second, len(closes))
        and price_diverges
        and indicator_diverges
    )
    return (
        active,
        float(indicator[second]) - float(indicator[first]),
        first,
        second,
    )


def _divergence_confirmation(
    context: SignalContext,
    first: int,
    second: int,
    *,
    find_high: bool,
) -> tuple[bool, str]:
    """Require a neckline break and MA20/momentum trend confirmation."""
    closes = [float(quote.close) for quote in context.quotes]
    latest = closes[-1]
    between = closes[first:second + 1]
    price_to_ma_20 = context.latest.get("price_to_ma_20")
    momentum_20 = context.latest.get("momentum_20")
    if price_to_ma_20 is None or momentum_20 is None:
        return False, "趋势确认特征不足"
    if find_high:
        neckline = min(between)
        price_confirmed = latest < neckline
        trend_confirmed = price_to_ma_20 < 1.0 and momentum_20 < 0
        label = "跌破颈线且收盘低于MA20、20日动量转负"
    else:
        neckline = max(between)
        price_confirmed = latest > neckline
        trend_confirmed = price_to_ma_20 > 1.0 and momentum_20 > 0
        label = "突破颈线且收盘高于MA20、20日动量转正"
    return price_confirmed and trend_confirmed, label


class _IndicatorDivergence(SignalRule):
    feature_key = ""
    indicator_name = ""
    find_high = False

    def evaluate(self, context: SignalContext):
        result = _indicator_divergence(
            context,
            self.feature_key,
            find_high=self.find_high,
        )
        if result is None:
            return self.result(False, 0, description="有效价格极值点不足")
        active, value, first, second = result
        if self.find_high:
            active_description = f"价格创新高但{self.indicator_name}降低"
            inactive_description = f"未出现{self.indicator_name}顶背离"
        else:
            active_description = f"价格创新低但{self.indicator_name}抬高"
            inactive_description = f"未出现{self.indicator_name}底背离"
        if not active:
            return self.result(False, 0, value=value,
                               description=inactive_description)
        confirmed, confirmation = _divergence_confirmation(
            context,
            first,
            second,
            find_high=self.find_high,
        )
        description = (
            f"{active_description}；{confirmation}"
            if confirmed
            else f"风险提示：{active_description}；尚未得到价格与趋势确认"
        )
        return self.result(
            True,
            (-1 if self.find_high else 1) if confirmed else 0,
            value=value,
            description=description,
        )


class MACDTopDivergence(_IndicatorDivergence):
    signal_id = "macd_top_divergence"
    name = "MACD顶背离"
    category = "divergence"

    feature_key = "macd_dif"
    indicator_name = "DIF"
    find_high = True


class MACDBottomDivergence(_IndicatorDivergence):
    signal_id = "macd_bottom_divergence"
    name = "MACD底背离"
    category = "divergence"

    feature_key = "macd_dif"
    indicator_name = "DIF"


class RSITopDivergence(_IndicatorDivergence):
    signal_id = "rsi_top_divergence"
    name = "RSI顶背离"
    category = "divergence"
    feature_key = "rsi_14"
    indicator_name = "RSI"
    find_high = True


class RSIBottomDivergence(_IndicatorDivergence):
    signal_id = "rsi_bottom_divergence"
    name = "RSI底背离"
    category = "divergence"
    feature_key = "rsi_14"
    indicator_name = "RSI"


class MFITopDivergence(_IndicatorDivergence):
    signal_id = "mfi_top_divergence"
    name = "MFI顶背离"
    category = "divergence"
    feature_key = "mfi_14"
    indicator_name = "MFI"
    find_high = True


class MFIBottomDivergence(_IndicatorDivergence):
    signal_id = "mfi_bottom_divergence"
    name = "MFI底背离"
    category = "divergence"
    feature_key = "mfi_14"
    indicator_name = "MFI"


class OBVTopDivergence(_IndicatorDivergence):
    signal_id = "obv_top_divergence"
    name = "OBV顶背离"
    category = "divergence"
    feature_key = "obv"
    indicator_name = "OBV"
    find_high = True


class OBVBottomDivergence(_IndicatorDivergence):
    signal_id = "obv_bottom_divergence"
    name = "OBV底背离"
    category = "divergence"
    feature_key = "obv"
    indicator_name = "OBV"


class DoubleTop(SignalRule):
    signal_id = "price_double_top"
    name = "双顶"
    category = "price_pattern"

    def evaluate(self, context: SignalContext):
        closes = [float(quote.close) for quote in context.quotes[-60:]]
        points = _extrema(closes, 3, True)
        if len(points) < 2:
            return self.result(False, 0, description="有效高点不足")
        first, second = points[-2:]
        p1, p2 = closes[first], closes[second]
        average = (p1 + p2) / 2
        trough = min(closes[first:second + 1])
        pullback = (average - trough) / average if average else 0.0
        active = (
            average > 0
            and _is_recent(second, len(closes), bars=15)
            and abs(p1 - p2) / average < 0.03
            and pullback > 0.03
            and closes[-1] < trough * 0.99
        )
        return self.result(
            active, -1, value=pullback,
            description=f"双顶中间回撤={pullback:.1%}" if active else "未出现双顶",
        )


class DoubleBottom(SignalRule):
    signal_id = "price_double_bottom"
    name = "双底"
    category = "price_pattern"

    def evaluate(self, context: SignalContext):
        closes = [float(quote.close) for quote in context.quotes[-60:]]
        points = _extrema(closes, 3, False)
        if len(points) < 2:
            return self.result(False, 0, description="有效低点不足")
        first, second = points[-2:]
        p1, p2 = closes[first], closes[second]
        average = (p1 + p2) / 2
        peak = max(closes[first:second + 1])
        rebound = (peak - average) / average if average else 0.0
        active = (
            average > 0
            and _is_recent(second, len(closes), bars=15)
            and abs(p1 - p2) / average < 0.03
            and rebound > 0.03
            and closes[-1] > peak * 1.01
        )
        return self.result(
            active, 1, value=rebound,
            description=f"双底中间反弹={rebound:.1%}" if active else "未出现双底",
        )
