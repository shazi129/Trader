from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

import quote_api.futu.futu_quote as futu_quote_module
from quote_api.futu import FutuQuoteAPI, FutuQuoteError
from quote_api.quote_base import KlineAdjustment
from quote_api.quote_factory import QuoteAPIFactory
from quote_api.stock_meta import STOCK_META, StockInfo, StockMarket


class _FakeSDK:
    RET_OK = 0
    KLType = SimpleNamespace(K_DAY="K_DAY")
    AuType = SimpleNamespace(NONE="none", QFQ="qfq", HFQ="hfq")
    KL_FIELD = SimpleNamespace(ALL="")


class _PagedContext:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def request_history_kline(self, code, **kwargs):
        self.calls.append({"code": code, **kwargs})
        if kwargs["page_req_key"] is None:
            data = pd.DataFrame(
                [
                    {
                        "time_key": "2026-08-10 00:00:00",
                        "open": 479.0,
                        "close": 481.4,
                        "high": 483.6,
                        "low": 476.4,
                        "last_close": 478.8,
                        "volume": 15508724.0,
                        "turnover": 7437285186.0,
                        "turnover_rate": 0.00171,
                        "change_rate": 0.543024,
                    },
                    {
                        "time_key": "2026-08-11 00:00:00",
                        "open": 481.2,
                        "close": 470.8,
                        "high": 483.8,
                        "low": 469.6,
                        "last_close": 481.4,
                        "volume": 19558079.0,
                        "turnover": 9250170997.0,
                        "turnover_rate": 0.00215,
                        "change_rate": -2.201911,
                    },
                ]
            )
            return self.RET_OK, data, b"page-2"

        data = pd.DataFrame(
            [
                {
                    "time_key": "2026-08-12 00:00:00",
                    "open": 471.0,
                    "close": 475.0,
                    "high": 477.0,
                    "low": 469.0,
                    "last_close": 470.8,
                    "volume": 123.0,
                    "turnover": 456.0,
                    "turnover_rate": 0.003,
                    "change_rate": 0.0,
                }
            ]
        )
        return self.RET_OK, data, None

    RET_OK = 0


def test_get_klines_maps_fields_and_follows_pages(monkeypatch):
    monkeypatch.setattr(futu_quote_module, "_load_futu_sdk", lambda: _FakeSDK)
    context = _PagedContext()
    api = FutuQuoteAPI(quote_context=context)

    result = api.get_klines(
        "Tencent", start_date="20260810", end_date="2026-08-12", limit=2
    )

    assert [quote.date for quote in result] == ["2026-08-11", "2026-08-12"]
    assert len(context.calls) == 2
    assert context.calls[0]["code"] == "HK.00700"
    assert context.calls[0]["start"] == "2026-08-10"
    assert context.calls[0]["autype"] == "none"
    assert context.calls[1]["page_req_key"] == b"page-2"

    quote = result[-1]
    assert quote.source == "futu"
    assert quote.code == "HK.00700"
    assert quote.currency == "HKD"
    assert quote.pre_close == pytest.approx(470.8)
    assert quote.change == pytest.approx(4.2)
    assert quote.change_pct == pytest.approx(4.2 / 470.8 * 100.0)
    assert quote.turnover_rate == pytest.approx(0.3)


@pytest.mark.parametrize(
    ("adjustment", "expected_autype"),
    [
        (KlineAdjustment.NONE, "none"),
        (KlineAdjustment.QFQ, "qfq"),
        (KlineAdjustment.HFQ, "hfq"),
    ],
)
def test_history_adjustment_maps_to_futu_autype(
    monkeypatch, adjustment, expected_autype
):
    monkeypatch.setattr(futu_quote_module, "_load_futu_sdk", lambda: _FakeSDK)
    context = _PagedContext()
    api = FutuQuoteAPI(quote_context=context, adjustment=adjustment)

    quotes = api.get_klines("Tencent", limit=1)

    assert context.calls[0]["autype"] == expected_autype


def test_symbol_mapping_and_supported_markets(monkeypatch):
    monkeypatch.setitem(
        STOCK_META,
        "Moutai",
        StockInfo("贵州茅台", "600519", StockMarket.SH, "2001-08-27"),
    )
    monkeypatch.setitem(
        STOCK_META,
        "PingAnBank",
        StockInfo("平安银行", "000001", StockMarket.SZ, "1991-04-03"),
    )
    api = FutuQuoteAPI(quote_context=object())

    assert api._futu_symbol("Tencent") == "HK.00700"
    assert api._futu_symbol("Alibaba") == "HK.09988"
    assert api._futu_symbol("NVIDIA") == "US.NVDA"
    assert api._futu_symbol("AG") == "US.SLV"
    assert api._futu_symbol("Moutai") == "SH.600519"
    assert api._futu_symbol("PingAnBank") == "SZ.000001"
    assert api.is_supported("Tencent") is True
    assert api.is_supported("Moutai") is True
    assert api.is_supported("AG") is True


def test_latest_quote_uses_market_snapshot(monkeypatch):
    monkeypatch.setattr(futu_quote_module, "_load_futu_sdk", lambda: _FakeSDK)

    class SnapshotContext:
        def __init__(self) -> None:
            self.codes = None

        def get_market_snapshot(self, codes):
            self.codes = codes
            return self.RET_OK, pd.DataFrame(
                [
                    {
                        "update_time": "2026-08-14 19:59:04.852",
                        "last_price": 58.48,
                        "open_price": 58.83,
                        "high_price": 59.365,
                        "low_price": 58.42,
                        "prev_close_price": 58.16,
                        "volume": 10303467.0,
                        "turnover": 605542782.0,
                        "turnover_rate": 1.889,
                    }
                ]
            )

        RET_OK = 0

    context = SnapshotContext()
    api = FutuQuoteAPI(quote_context=context)

    quote = api.get_daily_quote("AG")

    assert context.codes == ["US.SLV"]
    assert quote is not None
    assert quote.code == "US.SLV"
    assert quote.date == "2026-08-14"
    assert quote.close == pytest.approx(58.48)
    assert quote.change == pytest.approx(0.32)
    assert quote.change_pct == pytest.approx(0.32 / 58.16 * 100.0)
    assert quote.turnover_rate == pytest.approx(1.889)
    assert quote.currency == "USD"


def test_request_error_is_not_reported_as_empty_data(monkeypatch):
    monkeypatch.setattr(futu_quote_module, "_load_futu_sdk", lambda: _FakeSDK)

    class FailedContext:
        def request_history_kline(self, code, **kwargs):
            return -1, "no quote right", None

    api = FutuQuoteAPI(quote_context=FailedContext())
    with pytest.raises(FutuQuoteError, match="no quote right"):
        api.get_klines("Tencent", "2026-08-10", "2026-08-12")


def test_factory_registers_futu_without_opening_connection():
    api = QuoteAPIFactory.create("futu", cached=False)
    try:
        assert isinstance(api, FutuQuoteAPI)
        assert api._quote_context is None
        assert "futu" in QuoteAPIFactory.available_sources()
    finally:
        api.close()


def test_factory_exposes_current_and_available_sources(monkeypatch):
    import config

    monkeypatch.setattr(config, "QUOTE_SOURCE", "tencent")
    assert QuoteAPIFactory.current_source() == "tencent"
    assert QuoteAPIFactory.available_sources() == ["futu", "tencent", "sina"]

    monkeypatch.setattr(config, "QUOTE_SOURCE", "removed-provider")
    assert QuoteAPIFactory.current_source() == "futu"

    monkeypatch.setattr(config, "KLINE_ADJUSTMENT", "hfq")
    assert QuoteAPIFactory.current_adjustment() == KlineAdjustment.HFQ
    api = QuoteAPIFactory.create("futu", cached=False)
    assert api.adjustment == KlineAdjustment.HFQ


def test_eastmoney_source_is_removed():
    assert "eastmoney" not in QuoteAPIFactory.available_sources()
    with pytest.raises(ValueError, match="unsupported quote source"):
        QuoteAPIFactory.create("eastmoney", cached=False)
