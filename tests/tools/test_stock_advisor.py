"""Offline data-loading contracts for stock_advisor."""

from quote_api.quote_base import DailyQuote
from quote_api.repository import MarketDataRepository
from tools.stock_advisor.stock_advisor import _load_or_build


def _quote(index: int) -> DailyQuote:
    quote = DailyQuote()
    quote.date = f"2025-{index // 28 + 1:02d}-{index % 28 + 1:02d}"
    quote.open = 100 + index
    quote.close = 100.5 + index
    quote.high = 101 + index
    quote.low = 99 + index
    quote.volume = 1000 + index
    quote.turnover = quote.volume * quote.close
    quote.turnover_rate = 1.0
    return quote


def test_load_or_build_materializes_features_from_local_quotes(tmp_path):
    db_path = tmp_path / "trader.db"
    source_quotes = [_quote(index) for index in range(90)]
    with MarketDataRepository(db_path) as repository:
        repository.save_many("Example", source_quotes)

    quotes, features = _load_or_build("Example", str(db_path))

    assert len(quotes) == len(source_quotes)
    assert len(features) == len(source_quotes)
    assert features[-1].date == quotes[-1].date


def test_load_or_build_does_not_fetch_when_local_quotes_are_missing(tmp_path):
    quotes, features = _load_or_build("Example", str(tmp_path / "empty.db"))

    assert quotes == []
    assert features == []
