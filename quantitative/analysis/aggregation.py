"""Aggregate active signals with point-in-time backtest statistics."""

from __future__ import annotations

from quantitative.backtesting.models import BacktestArtifact, HORIZONS
from quantitative.signals import SignalResult

from .models import HorizonAnalysis


def aggregate_signals(
    signals: list[SignalResult],
    artifact: BacktestArtifact,
    horizons: tuple[int, ...] = HORIZONS,
) -> dict[int, HorizonAnalysis]:
    active = [signal for signal in signals if signal.active]
    result: dict[int, HorizonAnalysis] = {}
    for horizon in horizons:
        numerator = 0.0
        denominator = 0.0
        contributors = 0
        for signal in active:
            metric = artifact.metric(signal.signal_id, horizon)
            if metric is None or metric.samples == 0:
                success_rate = 0.55
                weight = 0.05
            else:
                success_rate = metric.success_rate
                weight = metric.weight
            if weight <= 0:
                continue
            probability_up = (
                success_rate if signal.direction > 0 else 1.0 - success_rate
            )
            effective_weight = weight * max(signal.strength, 0.0)
            numerator += probability_up * effective_weight
            denominator += effective_weight
            contributors += 1
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


__all__ = ["aggregate_signals"]
