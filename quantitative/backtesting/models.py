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


@dataclass
class BacktestArtifact:
    model_version: str = "signal_model_v1"
    generated_at: str = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )
    horizons: tuple[int, ...] = HORIZONS
    universe: tuple[str, ...] = ()
    data_cutoff: str | None = None
    # signal_id -> horizon string -> SignalMetric
    metrics: dict[str, dict[str, SignalMetric]] = field(default_factory=dict)

    def metric(self, signal_id: str, horizon: int) -> SignalMetric | None:
        return self.metrics.get(signal_id, {}).get(str(horizon))

    def to_dict(self) -> dict:
        return {
            "model_version": self.model_version,
            "generated_at": self.generated_at,
            "horizons": list(self.horizons),
            "universe": list(self.universe),
            "data_cutoff": self.data_cutoff,
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
            metrics={
                signal_id: {
                    str(horizon): SignalMetric(**metric)
                    for horizon, metric in by_horizon.items()
                }
                for signal_id, by_horizon in (data.get("metrics") or {}).items()
            },
        )
