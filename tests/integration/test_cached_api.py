# -*- coding: utf-8 -*-
"""真实行情接口与本地缓存的集成测试。

默认测试集不会执行本模块；显式运行时会访问当前配置的行情接口，但使用
pytest 临时目录中的数据库，不会修改 ``database/stock_data.db``。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from database.stock_db_utils import StockDB  # noqa: E402
from quote_api import QuoteAPIFactory  # noqa: E402
from quote_api.cached_api import CachedQuoteAPI  # noqa: E402

pytestmark = pytest.mark.integration


def _use_temporary_db(api: CachedQuoteAPI, tmp_path: Path) -> CachedQuoteAPI:
    api._db = StockDB(str(tmp_path / "cached_quote.db"))
    return api


def test_cached_api_reuses_downloaded_data(tmp_path):
    raw_api = QuoteAPIFactory.create(cached=False)
    api = _use_temporary_db(CachedQuoteAPI(raw_api), tmp_path)

    with api:
        first = api.get_klines("Tencent", limit=100)
        second = api.get_klines("Tencent", limit=100)

    assert first
    assert [(q.date, q.close) for q in second] == [
        (q.date, q.close) for q in first
    ]


def test_factory_cached_api_can_fetch_quotes(tmp_path):
    api = QuoteAPIFactory.create_with_cache(cached=False)
    _use_temporary_db(api, tmp_path)

    with api:
        quotes = api.get_klines("Tencent", limit=50)

    assert quotes
