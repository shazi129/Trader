"""Backtest result models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime

HORIZONS = (5, 20, 60)


@dataclass(frozen=True)
class SignalMetric:
    samples: int
    successes: int
    success_rate: float
    weight: float
    baseline_success_rate: float = 0.5
    excess_success_rate: float = 0.0
    direction_multiplier: int = 0
    z_score: float = 0.0
    p_value: float = 1.0
    oos_samples: int = 0
    oos_success_rate: float = 0.0
    oos_baseline_success_rate: float = 0.0
    oos_excess_success_rate: float = 0.0
    oos_z_score: float = 0.0
    oos_positive_folds: int = 0
    oos_total_folds: int = 0


@dataclass
class BacktestArtifact:
    model_version: str = "signal_model_v2"
    generated_at: str = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )
    horizons: tuple[int, ...] = HORIZONS
    universe: tuple[str, ...] = ()
    data_cutoff: str | None = None
    # symbol -> horizon string -> unconditional probability of an up move.
    baselines: dict[str, dict[str, float]] = field(default_factory=dict)
    # Pooled fallback used when an analyzed symbol was not in the backtest pool.
    pooled_baselines: dict[str, float] = field(default_factory=dict)
    # signal_id -> horizon string -> SignalMetric
    metrics: dict[str, dict[str, SignalMetric]] = field(default_factory=dict)

    def metric(self, signal_id: str, horizon: int) -> SignalMetric | None:
        return self.metrics.get(signal_id, {}).get(str(horizon))

    def baseline_probability_up(self, symbol: str | None, horizon: int) -> float:
        if symbol:
            value = self.baselines.get(symbol, {}).get(str(horizon))
            if value is not None:
                return value
        return self.pooled_baselines.get(str(horizon), 0.5)

    def to_dict(self) -> dict:
        return {
            "model_version": self.model_version,
            "generated_at": self.generated_at,
            "horizons": list(self.horizons),
            "universe": list(self.universe),
            "data_cutoff": self.data_cutoff,
            "baselines": self.baselines,
            "pooled_baselines": self.pooled_baselines,
            "metrics": {
                signal_id: {
                    horizon: asdict(metric)
                    for horizon, metric in by_horizon.items()
                }
                for signal_id, by_horizon in self.metrics.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BacktestArtifact":
        return cls(
            model_version=data.get("model_version", "signal_model_v1"),
            generated_at=data.get("generated_at", ""),
            horizons=tuple(data.get("horizons") or HORIZONS),
            universe=tuple(data.get("universe") or ()),
            data_cutoff=data.get("data_cutoff"),
            baselines={
                str(symbol): {
                    str(horizon): float(probability)
                    for horizon, probability in by_horizon.items()
                }
                for symbol, by_horizon in (data.get("baselines") or {}).items()
            },
            pooled_baselines={
                str(horizon): float(probability)
                for horizon, probability in (
                    data.get("pooled_baselines") or {}
                ).items()
            },
            metrics={
                signal_id: {
                    str(horizon): SignalMetric(**metric)
                    for horizon, metric in by_horizon.items()
                }
                for signal_id, by_horizon in (data.get("metrics") or {}).items()
            },
        )
