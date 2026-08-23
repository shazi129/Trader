"""Build supervised (X, y) datasets for forward-return regression.

The target is the forward ``horizon``-day simple return computed from the
*market-data* repository (``kline_daily``), not from features, so labels never
leak through the feature pipeline.  Features come from ``FeatureRepository``
and are aligned by ``(symbol, date)``.

Design constraints inherited from the existing backtesting domain:

- No random shuffling: rows are ordered by date so callers can do temporal
  train/validation splits without lookahead.
- A row is kept only if the forward close exists, otherwise the label cannot
  be observed and the row would inject bias.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from quantitative.features import FeatureRepository
from quantitative.features.catalog import FEATURE_KEYS
from quote_api.repository import MarketDataRepository


@dataclass
class ReturnDataset:
    """Aligned feature matrix, target vector, and metadata."""

    X: np.ndarray
    y: np.ndarray
    feature_names: tuple[str, ...]
    symbols: list[str]
    dates: list[str]

    @property
    def n_samples(self) -> int:
        return int(self.X.shape[0])

    @property
    def n_features(self) -> int:
        return int(self.X.shape[1])


@dataclass
class ReturnDatasetBuilder:
    """Materialize a pooled panel of features and forward-return labels."""

    horizon: int = 5
    feature_names: tuple[str, ...] = FEATURE_KEYS
    db_path: str | None = None

    _feature_index: dict[str, int] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self._feature_index = {name: i for i, name in enumerate(self.feature_names)}

    def _feature_row(self, snapshot) -> list[float | None]:
        return [snapshot.get(name) for name in self.feature_names]

    def build(
        self,
        symbols: list[str] | None = None,
    ) -> ReturnDataset:
        """Build the pooled dataset across ``symbols`` (default: all in DB)."""
        with FeatureRepository(self.db_path) as features, \
                MarketDataRepository(self.db_path) as market:
            symbol_list = symbols or market.list_symbols()

            rows: list[list[float]] = []
            labels: list[float] = []
            row_symbols: list[str] = []
            row_dates: list[str] = []

            for symbol in symbol_list:
                quotes = market.get_range(symbol)
                if len(quotes) <= self.horizon:
                    continue
                # date -> close, for forward-return lookup.
                close_by_date = {q.date: float(q.close) for q in quotes}
                snapshots = features.get_range(symbol)
                for snapshot in snapshots:
                    forward_date = self._forward_date(
                        snapshot.date, quotes, self.horizon
                    )
                    if forward_date is None:
                        continue
                    anchor_close = close_by_date.get(snapshot.date)
                    forward_close = close_by_date.get(forward_date)
                    if anchor_close in (None, 0) or forward_close in (None, 0):
                        continue
                    feature_row = self._feature_row(snapshot)
                    if any(value is None for value in feature_row):
                        continue
                    rows.append([float(v) for v in feature_row])
                    labels.append(forward_close / anchor_close - 1.0)
                    row_symbols.append(symbol)
                    row_dates.append(snapshot.date)

            if not rows:
                raise ValueError("no valid (feature, forward-return) rows found")

            return ReturnDataset(
                X=np.asarray(rows, dtype=np.float64),
                y=np.asarray(labels, dtype=np.float64),
                feature_names=self.feature_names,
                symbols=row_symbols,
                dates=row_dates,
            )

    @staticmethod
    def _forward_date(anchor_date: str, quotes, horizon: int) -> str | None:
        """Return the trading date ``horizon`` bars after ``anchor_date``."""
        dates = [q.date for q in quotes]
        if anchor_date not in dates:
            return None
        index = dates.index(anchor_date)
        target = index + horizon
        return dates[target] if target < len(dates) else None


__all__ = ["ReturnDataset", "ReturnDatasetBuilder"]
