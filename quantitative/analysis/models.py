"""Public output models for quantitative analysis."""

from __future__ import annotations

from dataclasses import dataclass, field

from quantitative.signals import SignalResult


@dataclass(frozen=True)
class HorizonAnalysis:
    horizon_days: int
    probability_up: float
    probability_down: float
    confidence: float
    contributing_signals: int

    @property
    def trend(self) -> str:
        if self.probability_up >= 0.6:
            return "偏多"
        if self.probability_up <= 0.4:
            return "偏空"
        return "中性"


@dataclass
class QuantitativeReport:
    symbol: str
    name: str
    anchor_date: str
    anchor_price: float
    data_source: str
    data_days: int
    signals: list[SignalResult] = field(default_factory=list)
    horizons: dict[int, HorizonAnalysis] = field(default_factory=dict)
    summary: str = ""

    @property
    def active_signals(self) -> list[SignalResult]:
        return [signal for signal in self.signals if signal.active]

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "anchor_date": self.anchor_date,
            "anchor_price": self.anchor_price,
            "data_source": self.data_source,
            "data_days": self.data_days,
            "horizons": {
                str(days): {
                    "probability_up": result.probability_up,
                    "probability_down": result.probability_down,
                    "confidence": result.confidence,
                    "contributing_signals": result.contributing_signals,
                    "trend": result.trend,
                }
                for days, result in self.horizons.items()
            },
            "signals": [signal.to_dict() for signal in self.signals],
            "summary": self.summary,
        }
