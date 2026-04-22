# -*- coding: utf-8 -*-
"""
行情接口包

提供统一抽象，支持从多个数据源获取股票 K 线 / 单日快照：
- 东方财富 (eastmoney)
- AkShare   (akshare)
- yfinance  (yfinance)
- 雪球       (xueqiu)
- 腾讯财经   (tencent)

使用示例：
    from quote_api import QuoteAPIFactory

    api = QuoteAPIFactory.create("akshare")
    quote = api.get_daily_quote("Tencent", "2025-02-04")
    klines = api.get_klines("Tencent", "2024-01-01", "2024-12-31")
"""

from quote_api.quote_base import DailyQuote, QuoteAPI, DateLike
from quote_api.quote_factory import QuoteAPIFactory, QuoteSource

__all__ = [
    "DailyQuote",
    "QuoteAPI",
    "DateLike",
    "QuoteAPIFactory",
    "QuoteSource",
]
