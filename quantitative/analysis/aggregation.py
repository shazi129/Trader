"""Aggregate only statistically validated signals over symbol base rates."""

from __future__ import annotations

from quantitative.backtesting.models import BacktestArtifact, HORIZONS
from quantitative.signals import SignalResult

from .models import HorizonAnalysis, SignalContribution


def signal_contributions(
    signals: list[SignalResult],
    artifact: BacktestArtifact,
    horizon: int,
    *,
    symbol: str | None = None,
) -> list[SignalContribution]:
    """Explain each validated active signal using production aggregation math."""
    baseline_probability_up = artifact.baseline_probability_up(symbol, horizon)
    prepared: list[
        tuple[SignalResult, float, int, float, float, float, float, int]
    ] = []
    denominator = 0.0
    for signal in (item for item in signals if item.active and item.direction != 0):
        metric = artifact.metric(signal.signal_id, horizon)
        if (
            metric is None
            or metric.samples == 0
            or metric.weight <= 0
            or metric.direction_multiplier not in (-1, 1)
        ):
            continue

        effective_direction = signal.direction * metric.direction_multiplier
        effective_excess = (
            metric.excess_success_rate * metric.direction_multiplier
        )
        if effective_excess <= 0:
            continue
        baseline_effective_success = (
            baseline_probability_up
            if effective_direction > 0
            else 1.0 - baseline_probability_up
        )
        effective_success = max(
            0.05,
            min(0.95, baseline_effective_success + effective_excess),
        )
        probability_up = (
            effective_success
            if effective_direction > 0
            else 1.0 - effective_success
        )
        effective_weight = metric.weight * max(signal.strength, 0.0)
        denominator += effective_weight
        prepared.append((
            signal,
            metric.success_rate,
            metric.samples,
            metric.weight,
            metric.baseline_success_rate,
            effective_excess,
            probability_up,
            effective_direction,
        ))

    result: list[SignalContribution] = []
    for (
        signal,
        success_rate,
        samples,
        weight,
        baseline_success_rate,
        effective_excess,
        probability_up,
        effective_direction,
    ) in prepared:
        effective_weight = weight * max(signal.strength, 0.0)
        weight_share = effective_weight / denominator if denominator else 0.0
        result.append(SignalContribution(
            signal_id=signal.signal_id,
            name=signal.name,
            category=signal.category,
            nominal_direction=signal.direction,
            success_rate=success_rate,
            samples=samples,
            backtest_weight=weight,
            effective_probability_up=probability_up,
            effective_weight=effective_weight,
            weight_share=weight_share,
            probability_point_contribution=(
                probability_up - baseline_probability_up
            ) * weight_share,
            baseline_success_rate=baseline_success_rate,
            excess_success_rate=effective_excess,
            effective_direction=effective_direction,
        ))
    return result


def aggregate_signals(
    signals: list[SignalResult],
    artifact: BacktestArtifact,
    horizons: tuple[int, ...] = HORIZONS,
    *,
    symbol: str | None = None,
) -> dict[int, HorizonAnalysis]:
    result: dict[int, HorizonAnalysis] = {}
    for horizon in horizons:
        baseline_probability_up = artifact.baseline_probability_up(symbol, horizon)
        contributions = signal_contributions(
            signals,
            artifact,
            horizon,
            symbol=symbol,
        )
        denominator = sum(item.effective_weight for item in contributions)
        numerator = sum(
            item.effective_probability_up * item.effective_weight
            for item in contributions
        )
        contributors = len(contributions)
        probability_up = (
            numerator / denominator if denominator else baseline_probability_up
        )
        probability_up = max(0.05, min(0.95, probability_up))
        confidence = min(1.0, denominator / max(contributors, 1))
        result[horizon] = HorizonAnalysis(
            horizon_days=horizon,
            probability_up=round(probability_up, 4),
            probability_down=round(1.0 - probability_up, 4),
            confidence=round(confidence, 4),
            contributing_signals=contributors,
            baseline_probability_up=round(baseline_probability_up, 4),
        )
    return result


__all__ = ["aggregate_signals", "signal_contributions"]
