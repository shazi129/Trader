"""Build sequence (past-30-day OHLCV) datasets for the LSTM model.

Each sample is a window of the most recent ``lookback`` trading days ending on
an anchor date.  The label is the forward ``horizon``-day simple return
computed from the *market-data* repository, matching the label semantics of
:mod:`quantitative.ml.dataset` exactly.

Fields per bar (in order):

    open, high, low, close, volume, turnover, turnover_rate

Prices are normalized per window by dividing by the anchor close, and volume /
turnover by their window mean, so the network sees relative (stationary)
shapes rather than raw scale.  Returns in the label are raw simple returns.

As with the tabular builder, rows are ordered chronologically (no shuffling)
so temporal train/validation splits stay leak-free.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from quote_api.repository import MarketDataRepository

# Bar fields and their order in the sequence feature dimension.
BAR_FIELDS = ("open", "high", "low", "close", "volume", "turnover", "turnover_rate")


@dataclass
class SequenceDataset:
    """Aligned 3-D feature tensor, target vector, and metadata."""

    X: np.ndarray  # shape (n_samples, lookback, n_fields)
    y: np.ndarray  # shape (n_samples,)
    symbols: list[str]
    dates: list[str]
    lookback: int
    field_names: tuple[str, ...]

    @property
    def n_samples(self) -> int:
        return int(self.X.shape[0])

    @property
    def n_fields(self) -> int:
        return int(self.X.shape[2])


def _quote_row(quote) -> list[float]:
    """Extract the raw bar fields as floats (missing turnover_rate -> 0)."""
    return [
        float(quote.open),
        float(quote.high),
        float(quote.low),
        float(quote.close),
        float(quote.volume),
        float(quote.turnover),
        float(getattr(quote, "turnover_rate", 0.0) or 0.0),
    ]


@dataclass
class SequenceDatasetBuilder:
    """Materialize pooled windows of raw bars and forward-return labels."""

    lookback: int = 30
    horizon: int = 5
    db_path: str | None = None

    def build(self, symbols: list[str] | None = None) -> SequenceDataset:
        with MarketDataRepository(self.db_path) as market:
            symbol_list = symbols or market.list_symbols()

            windows: list[np.ndarray] = []
            labels: list[float] = []
            row_symbols: list[str] = []
            row_dates: list[str] = []

            for symbol in symbol_list:
                quotes = market.get_range(symbol)
                if len(quotes) <= self.lookback + self.horizon:
                    continue

                n = len(quotes)
                # raw matrix: (n, n_fields)
                matrix = np.asarray(
                    [_quote_row(q) for q in quotes], dtype=np.float64
                )
                closes = matrix[:, 3]

                for index in range(self.lookback - 1, n - self.horizon):
                    anchor_close = closes[index]
                    if anchor_close <= 0:
                        continue
                    forward_close = closes[index + self.horizon]
                    if forward_close <= 0:
                        continue

                    window = matrix[index - self.lookback + 1:index + 1]
                    if window.shape[0] != self.lookback:
                        continue
                    window = self._normalize(window)

                    windows.append(window)
                    labels.append(forward_close / anchor_close - 1.0)
                    row_symbols.append(symbol)
                    row_dates.append(quotes[index].date)

            if not windows:
                raise ValueError("no valid sequence windows found")

            X = np.stack(windows, axis=0)
            y = np.asarray(labels, dtype=np.float64)

            # Sort the pooled panel chronologically by anchor date so that a
            # simple time split is a valid (leak-free) train/validation split.
            order = np.argsort(row_dates, kind="stable")
            return SequenceDataset(
                X=X[order],
                y=y[order],
                symbols=[row_symbols[i] for i in order],
                dates=[row_dates[i] for i in order],
                lookback=self.lookback,
                field_names=BAR_FIELDS,
            )

    @staticmethod
    def _normalize(window: np.ndarray) -> np.ndarray:
        """Scale prices by anchor close, volume/turnover by window mean."""
        out = window.copy()
        anchor_close = window[-1, 3]
        # price fields: open, high, low, close -> ratio to anchor close
        for col in (0, 1, 2, 3):
            if anchor_close > 0:
                out[:, col] = window[:, col] / anchor_close
        # volume / turnover fields -> ratio to their window mean (guard zero)
        for col in (4, 5, 6):
            mean = window[:, col].mean()
            if mean > 0:
                out[:, col] = window[:, col] / mean
            else:
                out[:, col] = 0.0
        return out


__all__ = [
    "SequenceDataset",
    "SequenceDatasetBuilder",
    "BAR_FIELDS",
]
