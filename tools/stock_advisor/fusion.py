"""Conservative fusion of signal-pattern and historical-similarity forecasts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from quantitative.analysis import QuantitativeReport

try:
    from .backtester import HorizonForecast, MultiHorizonForecast
except ImportError:  # direct execution from tools/stock_advisor
    from backtester import HorizonForecast, MultiHorizonForecast  # type: ignore


@dataclass(frozen=True)
class FusedHorizonForecast:
    horizon_days: int
    probability_up: float
    probability_down: float
    confidence: float
    signal_probability_up: float
    similarity_probability_up: Optional[float]
    signal_weight: float
    similarity_weight: float
    signal_weight_share: float
    similarity_weight_share: float
    models_disagree: bool

    @property
    def trend(self) -> str:
        if self.probability_up >= 0.6:
            return "偏多"
        if self.probability_up <= 0.4:
            return "偏空"
        return "中性"


@dataclass(frozen=True)
class FusedForecast:
    horizons: dict[int, FusedHorizonForecast]

    def get(self, horizon: int) -> Optional[FusedHorizonForecast]:
        return self.horizons.get(horizon)


def _similarity_by_horizon(
    forecast: Optional[MultiHorizonForecast],
) -> dict[int, HorizonForecast]:
    if forecast is None:
        return {}
    return {
        item.horizon_days: item
        for item in (forecast.short, forecast.medium, forecast.long)
        if item is not None
    }


def fuse_forecasts(
    report: QuantitativeReport,
    similarity: Optional[MultiHorizonForecast],
) -> FusedForecast:
    """Blend model probabilities by validated reliability using a linear pool.

    A convex linear pool is intentional: the two models reuse technical inputs,
    so multiplying odds would incorrectly assume independent evidence and create
    overconfident probabilities.
    """
    similarity_map = _similarity_by_horizon(similarity)
    result: dict[int, FusedHorizonForecast] = {}
    for horizon, signal_result in sorted(report.horizons.items()):
        similar = similarity_map.get(horizon)
        signal_probability = signal_result.probability_up
        signal_weight = max(signal_result.confidence, 0.0)
        similarity_probability = similar.prob_up if similar is not None else None
        similarity_weight = max(similar.confidence, 0.0) if similar else 0.0
        total_weight = signal_weight + similarity_weight
        if total_weight > 0:
            signal_share = signal_weight / total_weight
            similarity_share = similarity_weight / total_weight
            probability_up = (
                signal_probability * signal_share
                + (
                    similarity_probability
                    if similarity_probability is not None else 0.5
                ) * similarity_share
            )
        else:
            signal_share = 0.0
            similarity_share = 0.0
            probability_up = 0.5

        models_disagree = (
            similarity_probability is not None
            and (signal_probability - 0.5) * (similarity_probability - 0.5) < 0
        )
        disagreement = (
            abs(signal_probability - similarity_probability)
            if similarity_probability is not None else 0.0
        )
        weighted_reliability = (
            signal_share * signal_weight
            + similarity_share * similarity_weight
        )
        confidence = min(1.0, weighted_reliability * (1.0 - disagreement))
        probability_up = max(0.05, min(0.95, probability_up))
        result[horizon] = FusedHorizonForecast(
            horizon_days=horizon,
            probability_up=round(probability_up, 4),
            probability_down=round(1.0 - probability_up, 4),
            confidence=round(confidence, 4),
            signal_probability_up=signal_probability,
            similarity_probability_up=similarity_probability,
            signal_weight=round(signal_weight, 4),
            similarity_weight=round(similarity_weight, 4),
            signal_weight_share=round(signal_share, 4),
            similarity_weight_share=round(similarity_share, 4),
            models_disagree=models_disagree,
        )
    return FusedForecast(result)


__all__ = ["FusedForecast", "FusedHorizonForecast", "fuse_forecasts"]
