"""Baseline-aware, event-aware signal backtesting without lookahead."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from quote_api.quote_base import DailyQuote
from quantitative.features import FeatureCalculator
from quantitative.signals import SignalContext, SignalEngine

from .models import HORIZONS, BacktestArtifact, SignalMetric


SIGNIFICANCE_Z = 1.6448536269514722  # one-sided 95%
WALK_FORWARD_FOLDS = 3
INITIAL_TRAIN_FRACTION = 0.5


@dataclass(frozen=True)
class _BaselineObservation:
    anchor_date: str
    outcome_date: str
    went_up: bool


@dataclass(frozen=True)
class _SignalObservation:
    anchor_date: str
    outcome_date: str
    symbol: str
    nominal_direction: int
    nominal_success: bool


@dataclass(frozen=True)
class _RateSummary:
    samples: int = 0
    successes: int = 0
    success_rate: float = 0.5
    baseline_success_rate: float = 0.5
    excess_success_rate: float = 0.0
    z_score: float = 0.0
    p_value: float = 1.0


def _summary_from_pairs(pairs: list[tuple[bool, float]]) -> _RateSummary:
    if not pairs:
        return _RateSummary()
    samples = len(pairs)
    successes = sum(int(success) for success, _ in pairs)
    expected = sum(baseline for _, baseline in pairs)
    variance = sum(baseline * (1.0 - baseline) for _, baseline in pairs)
    success_rate = successes / samples
    baseline_rate = expected / samples
    excess = success_rate - baseline_rate
    z_score = (successes - expected) / math.sqrt(variance) if variance > 0 else 0.0
    p_value = 0.5 * math.erfc(z_score / math.sqrt(2.0))
    return _RateSummary(
        samples=samples,
        successes=successes,
        success_rate=success_rate,
        baseline_success_rate=baseline_rate,
        excess_success_rate=excess,
        z_score=z_score,
        p_value=p_value,
    )


def _summarize(
    observations: list[_SignalObservation],
    baseline_up_by_symbol: Mapping[str, float],
    direction_multiplier: int,
) -> _RateSummary:
    pairs: list[tuple[bool, float]] = []
    for observation in observations:
        baseline_up = baseline_up_by_symbol.get(observation.symbol, 0.5)
        nominal_baseline = (
            baseline_up
            if observation.nominal_direction > 0
            else 1.0 - baseline_up
        )
        if direction_multiplier > 0:
            pairs.append((observation.nominal_success, nominal_baseline))
        else:
            pairs.append((not observation.nominal_success, 1.0 - nominal_baseline))
    return _summary_from_pairs(pairs)


def _known_baselines(
    history: Mapping[str, list[_BaselineObservation]],
    cutoff: str,
) -> dict[str, float]:
    result: dict[str, float] = {}
    for symbol, observations in history.items():
        known = [item for item in observations if item.outcome_date < cutoff]
        if known:
            result[symbol] = sum(item.went_up for item in known) / len(known)
    return result


def _walk_forward_reverse_validation(
    observations: list[_SignalObservation],
    baseline_history: Mapping[str, list[_BaselineObservation]],
) -> tuple[bool, _RateSummary, int, int]:
    """Validate a reverse interpretation only on later, unseen date blocks."""
    unique_dates = sorted({item.anchor_date for item in observations})
    first_validation = max(1, int(len(unique_dates) * INITIAL_TRAIN_FRACTION))
    remaining = len(unique_dates) - first_validation
    if remaining < WALK_FORWARD_FOLDS:
        return False, _RateSummary(), 0, 0

    boundaries = [
        first_validation + round(remaining * fold / WALK_FORWARD_FOLDS)
        for fold in range(WALK_FORWARD_FOLDS + 1)
    ]
    validation_pairs: list[tuple[bool, float]] = []
    positive_folds = 0
    evaluated_folds = 0

    for fold in range(WALK_FORWARD_FOLDS):
        start_index, end_index = boundaries[fold], boundaries[fold + 1]
        if start_index >= end_index:
            continue
        start_date = unique_dates[start_index]
        end_date = unique_dates[end_index] if end_index < len(unique_dates) else None
        baselines = _known_baselines(baseline_history, start_date)
        training = [
            item for item in observations
            if item.outcome_date < start_date
        ]
        training_summary = _summarize(training, baselines, -1)
        if (
            training_summary.excess_success_rate <= 0
            or training_summary.z_score < SIGNIFICANCE_Z
        ):
            continue

        validation = [
            item for item in observations
            if item.anchor_date >= start_date
            and (end_date is None or item.anchor_date < end_date)
        ]
        if not validation:
            continue
        fold_pairs: list[tuple[bool, float]] = []
        for item in validation:
            baseline_up = baselines.get(item.symbol, 0.5)
            nominal_baseline = (
                baseline_up if item.nominal_direction > 0 else 1.0 - baseline_up
            )
            fold_pairs.append((not item.nominal_success, 1.0 - nominal_baseline))
        fold_summary = _summary_from_pairs(fold_pairs)
        evaluated_folds += 1
        if fold_summary.excess_success_rate > 0:
            positive_folds += 1
        validation_pairs.extend(fold_pairs)

    combined = _summary_from_pairs(validation_pairs)
    stable = (
        evaluated_folds >= 2
        and positive_folds >= 2
        and positive_folds / evaluated_folds >= 2 / 3
        and combined.excess_success_rate > 0
        and combined.z_score >= SIGNIFICANCE_Z
    )
    return stable, combined, positive_folds, evaluated_folds


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
        max_horizon = max(self.horizons)
        prepared: dict[str, tuple[list[DailyQuote], list]] = {}
        baseline_history: dict[
            int, dict[str, list[_BaselineObservation]]
        ] = {horizon: {} for horizon in self.horizons}
        universe: list[str] = []
        data_cutoff: str | None = None

        # First pass: calculate causal features and each symbol/horizon base rate.
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
            prepared[symbol] = (quotes, features)
            last_anchor = len(quotes) - max_horizon - 1
            for horizon in self.horizons:
                history: list[_BaselineObservation] = []
                for index in range(self.min_history - 1, last_anchor + 1):
                    anchor_price = float(quotes[index].close)
                    if anchor_price <= 0:
                        continue
                    history.append(_BaselineObservation(
                        anchor_date=quotes[index].date,
                        outcome_date=quotes[index + horizon].date,
                        went_up=float(quotes[index + horizon].close) > anchor_price,
                    ))
                baseline_history[horizon][symbol] = history

        baselines: dict[str, dict[str, float]] = {}
        pooled_baselines: dict[str, float] = {}
        for symbol in universe:
            baselines[symbol] = {}
            for horizon in self.horizons:
                history = baseline_history[horizon][symbol]
                baselines[symbol][str(horizon)] = round(
                    sum(item.went_up for item in history) / len(history), 6
                )
        for horizon in self.horizons:
            pooled = [
                item
                for symbol in universe
                for item in baseline_history[horizon][symbol]
            ]
            pooled_baselines[str(horizon)] = round(
                sum(item.went_up for item in pooled) / len(pooled), 6
            ) if pooled else 0.5

        # Second pass: collect predictive observations. Divergences are events,
        # so a continuous active window contributes only on its first active day.
        observations: dict[str, dict[int, list[_SignalObservation]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for symbol, (quotes, features) in prepared.items():
            last_anchor = len(quotes) - max_horizon - 1
            previous_predictive: dict[str, bool] = {}
            for index in range(self.min_history - 1, last_anchor + 1):
                start = max(0, index - 374)
                context = SignalContext(
                    symbol=symbol,
                    quotes=quotes[start:index + 1],
                    features=features[start:index + 1],
                )
                signals = self.engine.evaluate(context)
                current_predictive = {
                    signal.signal_id: signal.active and signal.direction != 0
                    for signal in signals
                }
                anchor_price = float(quotes[index].close)
                if anchor_price > 0:
                    for signal in signals:
                        if not signal.active or signal.direction == 0:
                            continue
                        if (
                            signal.category == "divergence"
                            and previous_predictive.get(signal.signal_id, False)
                        ):
                            continue
                        for horizon in self.horizons:
                            future_price = float(quotes[index + horizon].close)
                            actual_direction = 1 if future_price > anchor_price else -1
                            observations[signal.signal_id][horizon].append(
                                _SignalObservation(
                                    anchor_date=quotes[index].date,
                                    outcome_date=quotes[index + horizon].date,
                                    symbol=symbol,
                                    nominal_direction=signal.direction,
                                    nominal_success=actual_direction == signal.direction,
                                )
                            )
                previous_predictive = current_predictive

        artifact = BacktestArtifact(
            horizons=self.horizons,
            universe=tuple(sorted(universe)),
            data_cutoff=data_cutoff,
            baselines=baselines,
            pooled_baselines=pooled_baselines,
        )
        signal_ids = {rule.signal_id for rule in self.engine.rules}
        for signal_id in sorted(signal_ids):
            artifact.metrics[signal_id] = {}
            for horizon in self.horizons:
                items = observations[signal_id][horizon]
                baseline_up = {
                    symbol: baselines[symbol][str(horizon)]
                    for symbol in universe
                }
                nominal = _summarize(items, baseline_up, 1)
                direction_multiplier = 0
                effective = nominal
                oos = _RateSummary()
                positive_folds = 0
                evaluated_folds = 0

                if (
                    nominal.excess_success_rate > 0
                    and nominal.z_score >= SIGNIFICANCE_Z
                ):
                    direction_multiplier = 1
                else:
                    reverse = _summarize(items, baseline_up, -1)
                    if (
                        reverse.excess_success_rate > 0
                        and reverse.z_score >= SIGNIFICANCE_Z
                    ):
                        (
                            reverse_validated,
                            oos,
                            positive_folds,
                            evaluated_folds,
                        ) = _walk_forward_reverse_validation(
                            items,
                            baseline_history[horizon],
                        )
                        if reverse_validated:
                            direction_multiplier = -1
                            effective = reverse

                reliability = nominal.samples / (nominal.samples + 50.0)
                weight = (
                    min(1.0, effective.excess_success_rate * 2.0 * reliability)
                    if direction_multiplier != 0
                    else 0.0
                )
                artifact.metrics[signal_id][str(horizon)] = SignalMetric(
                    samples=nominal.samples,
                    successes=nominal.successes,
                    success_rate=round(nominal.success_rate, 6),
                    weight=round(weight, 6),
                    baseline_success_rate=round(
                        nominal.baseline_success_rate, 6
                    ),
                    excess_success_rate=round(
                        nominal.excess_success_rate, 6
                    ),
                    direction_multiplier=direction_multiplier,
                    z_score=round(
                        nominal.z_score * direction_multiplier
                        if direction_multiplier != 0 else nominal.z_score,
                        6,
                    ),
                    p_value=round(
                        effective.p_value if direction_multiplier != 0 else 1.0,
                        8,
                    ),
                    oos_samples=oos.samples,
                    oos_success_rate=round(oos.success_rate, 6),
                    oos_baseline_success_rate=round(
                        oos.baseline_success_rate, 6
                    ),
                    oos_excess_success_rate=round(
                        oos.excess_success_rate, 6
                    ),
                    oos_z_score=round(oos.z_score, 6),
                    oos_positive_folds=positive_folds,
                    oos_total_folds=evaluated_folds,
                )
        return artifact


__all__ = ["SignalBacktester"]
