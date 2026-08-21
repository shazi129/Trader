# -*- coding: utf-8 -*-
"""股票数据更新工具

替代旧的 trader_utils.py 中相关功能：
- 通过 quote_api（行情统一抽象）拉取 K 线
- 写入行情域 ``MarketDataRepository``（kline_daily）
- 增量更新：从数据库最新日期 + 1 开始拉

量化特征的计算和存储由 quantitative/ 模块负责，本模块只关心 K 线。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import config
from quote_api import QuoteAPIFactory, DailyQuote, StockMarket
from quote_api.repository import MarketDataRepository


# ---------------------------------------------------------------------------
# 单只股票更新
# ---------------------------------------------------------------------------
def update_stocket(stock_key: str, source: Optional[str] = None) -> int:
    """更新单只股票的日 K 线，返回新增条数。"""
    if stock_key not in config.global_stock_list:
        print(f"update_stocket error, unknown stock_key: {stock_key}")
        return 0

    stock_info = config.global_stock_list[stock_key]
    api = QuoteAPIFactory.create(source)

    if not api.is_supported(stock_key):
        print(f"update_stocket skip: {stock_key} not supported by {api.SOURCE}")
        return 0

    repository = MarketDataRepository()
    try:
        # 起点：DB 最新日期 + 1，否则从上市日期
        latest = repository.latest_date(stock_key)
        if latest:
            begin = datetime.strptime(latest, "%Y-%m-%d") + timedelta(days=1)
        else:
            begin = stock_info.get_list_date()

        # 终点：今天前一天；港股 16:00 后、A 股 17:00 后用今天
        now = datetime.now()
        end = now - timedelta(days=1)
        if stock_info.market == StockMarket.HK and now.hour >= 16:
            end = now
        if stock_info.market in (StockMarket.SH, StockMarket.SZ) and now.hour >= 17:
            end = now

        if (end - begin).days < 0:
            print(f"update_stocket {stock_key}: already up to date ({latest})")
            return 0

        quotes = api.get_klines(stock_key, start_date=begin, end_date=end)
        if not quotes:
            print(f"update_stocket {stock_key}: no new data")
            return 0

        repository.save_many(stock_key, quotes)
        print(f"update_stocket {stock_key}: +{len(quotes)} klines "
              f"({quotes[0].date} ~ {quotes[-1].date})")
        return len(quotes)
    finally:
        repository.close()


# ---------------------------------------------------------------------------
# 全量更新
# ---------------------------------------------------------------------------
def update_all_stocks(source: Optional[str] = None) -> int:
    total = 0
    for key in config.global_stock_list:
        total += update_stocket(key, source=source)
    return total


if __name__ == "__main__":
    update_all_stocks()
