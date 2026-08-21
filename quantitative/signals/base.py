"""Contracts shared by every signal rule."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence

from quote_api.quote_base import DailyQuote
from quantitative.features.models import FeatureSnapshot


@dataclass(frozen=True)
class SignalContext:
    symbol: str
    quotes: Sequence[DailyQuote]
    features: Sequence[FeatureSnapshot]

    def __post_init__(self) -> None:
        if not self.quotes or not self.features:
            raise ValueError("signal context requires quotes and features")
        if self.quotes[-1].date != self.features[-1].date:
            raise ValueError("quotes and features must share the same anchor date")

    @property
    def anchor_date(self) -> str:
        return self.quotes[-1].date

    @property
    def anchor_price(self) -> float:
        return float(self.quotes[-1].close)

    @property
    def latest(self) -> FeatureSnapshot:
        return self.features[-1]

    @property
    def previous(self) -> FeatureSnapshot | None:
        return self.features[-2] if len(self.features) >= 2 else None

    def feature_series(self, key: str) -> list[float | None]:
        return [snapshot.get(key) for snapshot in self.features]


@dataclass(frozen=True)
class SignalResult:
    signal_id: str
    name: str
    category: str
    active: bool
    direction: int
    value: float | None = None
    strength: float = 1.0
    description: str = ""

    def __post_init__(self) -> None:
        if self.direction not in (-1, 0, 1):
            raise ValueError("signal direction must be -1, 0, or 1")
        if not self.active and self.direction != 0:
            raise ValueError("inactive signal must have neutral direction")

    def to_dict(self) -> dict:
        return {
            "id": self.signal_id,
            "name": self.name,
            "category": self.category,
            "active": self.active,
            "direction": self.direction,
            "value": self.value,
            "strength": self.strength,
            "description": self.description,
        }


class SignalRule(ABC):
    signal_id = "base"
    name = "Base Signal"
    category = "other"

    @abstractmethod
    def evaluate(self, context: SignalContext) -> SignalResult:
        raise NotImplementedError

    def result(
        self,
        active: bool,
        direction: int,
        *,
        value: float | None = None,
        strength: float = 1.0,
        description: str = "",
    ) -> SignalResult:
        return SignalResult(
            signal_id=self.signal_id,
            name=self.name,
            category=self.category,
            active=active,
            direction=direction if active else 0,
            value=value,
            strength=strength,
            description=description,
        )
