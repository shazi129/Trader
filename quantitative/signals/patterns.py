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


class MACDTopDivergence(SignalRule):
    signal_id = "macd_top_divergence"
    name = "MACD顶背离"
    category = "divergence"

    def evaluate(self, context: SignalContext):
        closes = [float(quote.close) for quote in context.quotes]
        dif = context.feature_series("macd_dif")
        points = _extrema(closes, 5, True)
        points = [index for index in points if dif[index] is not None]
        if len(points) < 2:
            return self.result(False, 0, description="有效高点不足")
        first, second = points[-2:]
        active = (
            _is_recent(second, len(closes))
            and closes[second] > closes[first]
            and dif[second] < dif[first]
        )
        value = float(dif[second] - dif[first])
        return self.result(
            active, -1, value=value,
            description="价格创新高但DIF降低" if active else "未出现顶背离",
        )


class MACDBottomDivergence(SignalRule):
    signal_id = "macd_bottom_divergence"
    name = "MACD底背离"
    category = "divergence"

    def evaluate(self, context: SignalContext):
        closes = [float(quote.close) for quote in context.quotes]
        dif = context.feature_series("macd_dif")
        points = _extrema(closes, 5, False)
        points = [index for index in points if dif[index] is not None]
        if len(points) < 2:
            return self.result(False, 0, description="有效低点不足")
        first, second = points[-2:]
        active = (
            _is_recent(second, len(closes))
            and closes[second] < closes[first]
            and dif[second] > dif[first]
        )
        value = float(dif[second] - dif[first])
        return self.result(
            active, 1, value=value,
            description="价格创新低但DIF抬高" if active else "未出现底背离",
        )


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
