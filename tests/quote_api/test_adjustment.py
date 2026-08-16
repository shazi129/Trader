from __future__ import annotations

import json

import pytest

from quote_api.quote_base import KlineAdjustment
from quote_api.sina import SinaQuoteAPI
from quote_api.tencent import TencentQuoteAPI


class _Response:
    def __init__(self, text: str, status_code: int = 200) -> None:
        self.text = text
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError("HTTP %d" % self.status_code)


@pytest.mark.parametrize(
    ("mode", "bucket_key"),
    [("none", "day"), ("qfq", "qfqday"), ("hfq", "hfqday")],
)
def test_tencent_uses_configured_adjustment(monkeypatch, mode, bucket_key):
    api = TencentQuoteAPI(adjustment=mode)
    captured = {}

    def fake_get(url, params, timeout):
        captured["param"] = params["param"]
        payload = {
            "data": {
                "sh600519": {
                    bucket_key: [
                        ["2026-08-14", "10", "11", "12", "9", "100"]
                    ]
                }
            }
        }
        return _Response(json.dumps(payload))

    monkeypatch.setattr(api._session, "get", fake_get)

    quotes = api.get_klines("MaoTai", limit=1)

    assert captured["param"].endswith("," + mode)


@pytest.mark.parametrize(
    ("mode", "adjusted_close", "direction"),
    [("qfq", 50.0, "q"), ("hfq", 200.0, "h")],
)
def test_sina_applies_official_adjusted_close(
    monkeypatch, mode, adjusted_close, direction
):
    api = SinaQuoteAPI(adjustment=mode)
    requested_urls = []
    raw_rows = [
        {
            "day": "2026-08-14",
            "open": "90",
            "high": "110",
            "low": "80",
            "close": "100",
            "volume": "1000",
        }
    ]

    def fake_get(url, params=None, timeout=None):
        requested_urls.append(url)
        if "getKLineData" in url:
            return _Response(json.dumps(raw_rows))
        return _Response(
            'var sh600519%sfq=[{total:1,data:{_2026_08_14:"%s"}}];'
            % (direction, adjusted_close)
        )

    monkeypatch.setattr(api._session, "get", fake_get)

    quotes = api.get_klines("MaoTai", limit=1)

    assert requested_urls[-1].endswith("/p%sfq.js" % direction)
    assert quotes[0].close == pytest.approx(adjusted_close)
    assert quotes[0].open == pytest.approx(90 * adjusted_close / 100)


def test_invalid_adjustment_is_rejected():
    with pytest.raises(ValueError, match="unsupported K-line adjustment"):
        TencentQuoteAPI(adjustment="invalid")
