# -*- coding: utf-8 -*-
"""
行情接口包

提供统一抽象，从 ``QuoteAPIFactory`` 当前注册的数据源获取股票 K 线 / 单日快照。
可用源调用 ``QuoteAPIFactory.available_sources()``，当前默认源调用
``QuoteAPIFactory.current_source()``，调用方不维护数据源名单。

使用示例：
    from quote_api import QuoteAPIFactory

    # 不带缓存
    api = QuoteAPIFactory.create()
    quotes = api.get_klines("Tencent", limit=500)

    # 带数据库缓存（推荐）
    api = QuoteAPIFactory.create_with_cache()
    quotes = api.get_klines("Tencent", limit=500)  # 自动缓存
"""

from quote_api.quote_base import (
    DailyQuote,
    QuoteAPI,
    DateLike,
    StockFundamental,
    KlineAdjustment,
)
from quote_api.quote_factory import QuoteAPIFactory, QuoteSource
from quote_api.cached_api import CachedQuoteAPI
from quote_api.futu import FutuQuoteAPI, FutuQuoteError
from quote_api.stock_meta import (
    STOCK_META,
    StockInfo,
    StockMarket,
    get_meta,
    all_keys,
    register,
    has,
)

__all__ = [
    "DailyQuote",
    "StockFundamental",
    "QuoteAPI",
    "DateLike",
    "KlineAdjustment",
    "QuoteAPIFactory",
    "QuoteSource",
    "CachedQuoteAPI",
    "FutuQuoteAPI",
    "FutuQuoteError",
    "STOCK_META",
    "StockInfo",
    "StockMarket",
    "get_meta",
    "all_keys",
    "register",
    "has",
]
