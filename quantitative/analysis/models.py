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


@dataclass(frozen=True)
class SignalContribution:
    """One active signal's transparent contribution to a horizon forecast."""

    signal_id: str
    name: str
    category: str
    nominal_direction: int
    success_rate: float
    samples: int
    backtest_weight: float
    effective_probability_up: float
    effective_weight: float
    weight_share: float
    probability_point_contribution: float
    used_fallback: bool = False

    @property
    def nominal_direction_text(self) -> str:
        if self.nominal_direction > 0:
            return "看多"
        if self.nominal_direction < 0:
            return "看空"
        return "中性"

    @property
    def effective_direction_text(self) -> str:
        if self.effective_probability_up > 0.5:
            return "有效看多"
        if self.effective_probability_up < 0.5:
            return "有效看空"
        return "有效中性"

    @property
    def is_reversed(self) -> bool:
        effective_direction = (
            1 if self.effective_probability_up > 0.5
            else -1 if self.effective_probability_up < 0.5
            else 0
        )
        return (
            self.nominal_direction != 0
            and effective_direction != 0
            and self.nominal_direction != effective_direction
        )

    def to_dict(self) -> dict:
        return {
            "signal_id": self.signal_id,
            "name": self.name,
            "category": self.category,
            "nominal_direction": self.nominal_direction,
            "nominal_direction_text": self.nominal_direction_text,
            "success_rate": self.success_rate,
            "samples": self.samples,
            "backtest_weight": self.backtest_weight,
            "effective_probability_up": self.effective_probability_up,
            "effective_direction_text": self.effective_direction_text,
            "effective_weight": self.effective_weight,
            "weight_share": self.weight_share,
            "probability_point_contribution": self.probability_point_contribution,
            "is_reversed": self.is_reversed,
            "used_fallback": self.used_fallback,
        }


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
