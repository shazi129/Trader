"""Application entry points for computing and persisting feature series."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from quote_api import QuoteAPIFactory
from quote_api.cached_api import CachedQuoteAPI
from quote_api.repository import MarketDataRepository
from quote_api.stock_meta import get_meta

from .calculator import FeatureCalculator
from .repository import FeatureRepository


def materialize_symbol(
    symbol: str,
    *,
    source: str | None = None,
    db_path: str | Path | None = None,
    force_refresh: bool = False,
) -> int:
    """Load market data once, calculate all features, and persist snapshots."""

    source = source or QuoteAPIFactory.current_source()
    with MarketDataRepository(db_path) as market_repository:
        if source == "db":
            quotes = market_repository.get_range(symbol)
        else:
            raw = QuoteAPIFactory.create(source, cached=not force_refresh)
            if force_refresh:
                meta = get_meta(symbol)
                quotes = raw.get_klines(
                    symbol,
                    start_date=meta.listing_date if meta else None,
                    end_date=date.today(),
                )
                if quotes:
                    market_repository.save_many(symbol, quotes)
            else:
                cached = CachedQuoteAPI(raw, repository=market_repository)
                quotes = cached.get_klines(symbol)
                cached.close()
        if not quotes:
            return 0

    snapshots = FeatureCalculator().compute(symbol, quotes)
    with FeatureRepository(db_path) as feature_repository:
        feature_repository.save_many(snapshots)
    return len(snapshots)


__all__ = ["materialize_symbol"]
