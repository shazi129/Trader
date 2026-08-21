"""Feature-domain data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class FeatureSnapshot:
    """All materialized feature values for one symbol and trading date.

    A mapping is used instead of an ever-growing dataclass with dozens of
    fields.  Feature names are defined centrally in :mod:`catalog`.
    """

    symbol: str
    date: str
    values: dict[str, float | None] = field(default_factory=dict)

    def get(self, key: str, default=None):
        return self.values.get(key, default)

    def __getitem__(self, key: str) -> float | None:
        return self.values[key]

    def __contains__(self, key: str) -> bool:
        return key in self.values

    def items(self) -> Iterator[tuple[str, float | None]]:
        return iter(self.values.items())

    def to_dict(self) -> dict:
        return {"symbol": self.symbol, "date": self.date, **self.values}
