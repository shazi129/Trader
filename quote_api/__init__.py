# -*- coding: utf-8 -*-
"""
行情接口包

提供统一抽象，支持从多个数据源获取股票 K 线 / 单日快照：
- 新浪财经   (sina)
- 腾讯财经   (tencent)
- 东方财富   (eastmoney)

使用示例：
    from quote_api import QuoteAPIFactory

    # 不带缓存
    api = QuoteAPIFactory.create("eastmoney")
    quotes = api.get_klines("Tencent", limit=500)

    # 带数据库缓存（推荐）
    api = QuoteAPIFactory.create_with_cache("eastmoney")
    quotes = api.get_klines("Tencent", limit=500)  # 自动缓存
"""

from quote_api.quote_base import DailyQuote, QuoteAPI, DateLike
from quote_api.quote_factory import QuoteAPIFactory, QuoteSource
from quote_api.cached_api import CachedQuoteAPI

__all__ = [
    "DailyQuote",
    "QuoteAPI",
    "DateLike",
    "QuoteAPIFactory",
    "QuoteSource",
    "CachedQuoteAPI",
]
