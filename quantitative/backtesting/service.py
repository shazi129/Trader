"""No-lookahead backtesting for registered signal rules."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence

from quote_api.quote_base import DailyQuote
from quantitative.features import FeatureCalculator
from quantitative.signals import SignalContext, SignalEngine

from .models import HORIZONS, BacktestArtifact, SignalMetric


class SignalBacktester:
    def __init__(
        self,
        calculator: FeatureCalculator | None = None,
        engine: SignalEngine | None = None,
        horizons: tuple[int, ...] = HORIZONS,
        min_history: int = 120,
    ) -> None:
        self.calculator = calculator or FeatureCalculator()
        self.engine = engine or SignalEngine()
        self.horizons = horizons
        self.min_history = min_history

    def run(
        self, datasets: Mapping[str, Sequence[DailyQuote]]
    ) -> BacktestArtifact:
        successes = defaultdict(lambda: defaultdict(int))
        totals = defaultdict(lambda: defaultdict(int))
        max_horizon = max(self.horizons)
        universe: list[str] = []
        data_cutoff: str | None = None

        for symbol, source_quotes in datasets.items():
            quotes = sorted(source_quotes, key=lambda quote: quote.date)
            if len(quotes) < self.min_history + max_horizon + 1:
                continue
            universe.append(symbol)
            if quotes[-1].date and (
                data_cutoff is None or quotes[-1].date > data_cutoff
            ):
                data_cutoff = quotes[-1].date
            features = self.calculator.compute(symbol, quotes)
            last_anchor = len(quotes) - max_horizon - 1
            for index in range(self.min_history - 1, last_anchor + 1):
                start = max(0, index - 374)
                context = SignalContext(
                    symbol=symbol,
                    quotes=quotes[start:index + 1],
                    features=features[start:index + 1],
                )
                active = [
                    signal
                    for signal in self.engine.evaluate(context)
                    if signal.active
                ]
                if not active:
                    continue
                anchor_price = float(quotes[index].close)
                if anchor_price <= 0:
                    continue
                for signal in active:
                    for horizon in self.horizons:
                        future_price = float(quotes[index + horizon].close)
                        actual_direction = 1 if future_price > anchor_price else -1
                        totals[signal.signal_id][horizon] += 1
                        if actual_direction == signal.direction:
                            successes[signal.signal_id][horizon] += 1

        artifact = BacktestArtifact(
            horizons=self.horizons,
            universe=tuple(sorted(universe)),
            data_cutoff=data_cutoff,
        )
        signal_ids = {rule.signal_id for rule in self.engine.rules}
        for signal_id in sorted(signal_ids):
            artifact.metrics[signal_id] = {}
            for horizon in self.horizons:
                samples = totals[signal_id][horizon]
                hits = successes[signal_id][horizon]
                rate = hits / samples if samples else 0.5
                # Reliability combines edge and sample-size shrinkage.
                weight = abs(rate - 0.5) * 2.0 * (samples / (samples + 50.0))
                artifact.metrics[signal_id][str(horizon)] = SignalMetric(
                    samples=samples,
                    successes=hits,
                    success_rate=round(rate, 6),
                    weight=round(weight, 6),
                )
        return artifact


__all__ = ["SignalBacktester"]
