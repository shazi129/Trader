"""Aggregate active signals with point-in-time backtest statistics."""

from __future__ import annotations

from quantitative.backtesting.models import BacktestArtifact, HORIZONS
from quantitative.signals import SignalResult

from .models import HorizonAnalysis, SignalContribution


def signal_contributions(
    signals: list[SignalResult],
    artifact: BacktestArtifact,
    horizon: int,
) -> list[SignalContribution]:
    """Explain each active signal using exactly the production aggregation math."""
    prepared: list[tuple[SignalResult, float, int, float, float, float, bool]] = []
    denominator = 0.0
    for signal in (item for item in signals if item.active):
        metric = artifact.metric(signal.signal_id, horizon)
        used_fallback = metric is None or metric.samples == 0
        if used_fallback:
            success_rate = 0.55
            samples = 0
            weight = 0.05
            calibrated_success_rate = success_rate
        else:
            success_rate = metric.success_rate
            samples = metric.samples
            weight = metric.weight
            sample_reliability = samples / (samples + 50.0)
            calibrated_success_rate = (
                0.5 + (success_rate - 0.5) * sample_reliability
            )
        if weight <= 0:
            continue
        probability_up = (
            calibrated_success_rate
            if signal.direction > 0
            else 1.0 - calibrated_success_rate
        )
        effective_weight = weight * max(signal.strength, 0.0)
        denominator += effective_weight
        prepared.append((
            signal,
            success_rate,
            samples,
            weight,
            probability_up,
            effective_weight,
            used_fallback,
        ))

    result: list[SignalContribution] = []
    for (
        signal,
        success_rate,
        samples,
        weight,
        probability_up,
        effective_weight,
        used_fallback,
    ) in prepared:
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
            probability_point_contribution=(probability_up - 0.5) * weight_share,
            used_fallback=used_fallback,
        ))
    return result


def aggregate_signals(
    signals: list[SignalResult],
    artifact: BacktestArtifact,
    horizons: tuple[int, ...] = HORIZONS,
) -> dict[int, HorizonAnalysis]:
    result: dict[int, HorizonAnalysis] = {}
    for horizon in horizons:
        contributions = signal_contributions(signals, artifact, horizon)
        denominator = sum(item.effective_weight for item in contributions)
        numerator = sum(
            item.effective_probability_up * item.effective_weight
            for item in contributions
        )
        contributors = len(contributions)
        probability_up = numerator / denominator if denominator else 0.5
        probability_up = max(0.05, min(0.95, probability_up))
        confidence = min(1.0, denominator / max(contributors, 1))
        result[horizon] = HorizonAnalysis(
            horizon_days=horizon,
            probability_up=round(probability_up, 4),
            probability_down=round(1.0 - probability_up, 4),
            confidence=round(confidence, 4),
            contributing_signals=contributors,
        )
    return result


__all__ = ["aggregate_signals", "signal_contributions"]
