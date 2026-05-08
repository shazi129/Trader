# -*- coding: utf-8 -*-
"""
带缓存的行情 API 包装器

实现"先读DB，缺失再拉取"的逻辑。
对调用者透明：使用方式与普通 QuoteAPI 完全一致。
"""

from __future__ import annotations

import datetime
from typing import Optional
from pathlib import Path

from quote_api.quote_base import (
    QuoteAPI,
    DailyQuote,
    StockFundamental,
    DateLike,
)


class CachedQuoteAPI(QuoteAPI):
    """
    带数据库缓存的 API 包装器。

    用法：
        raw_api = QuoteAPIFactory.create("eastmoney")
        api = CachedQuoteAPI(raw_api)
        klines = api.get_klines("Tencent", limit=500)  # 自动缓存
    """

    def __init__(self, wrapped_api: QuoteAPI):
        """
        :param wrapped_api: 被包装的真实 API 实例
        """
        super().__init__()
        self.SOURCE = wrapped_api.SOURCE + "_cached"
        self._wrapped = wrapped_api
        self._db = None  # 懒加载

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _get_db(self):
        """懒加载数据库连接"""
        if self._db is None:
            from database.stock_db_utils import StockDB
            self._db = StockDB()
        return self._db

    def _date_to_str(self, date: DateLike) -> Optional[str]:
        """日期转字符串"""
        return QuoteAPI.normalize_date(date)

    def _convert_to_kline_data(self, quote: DailyQuote):
        """DailyQuote -> KlineData"""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from stock_info import KlineData
        kline = KlineData()
        kline.date = quote.date
        kline.open = quote.open
        kline.close = quote.close
        kline.high = quote.high
        kline.low = quote.low
        kline.volume = quote.volume
        kline.turnover = quote.turnover  # DailyQuote.turnover -> KlineData.turnover
        kline.turnover_rate = 0.0  # DailyQuote 无此字段
        kline.pe = 0.0
        return kline

    def _convert_to_daily_quote(self, kline) -> DailyQuote:
        """KlineData -> DailyQuote"""
        from quote_api.quote_base import DailyQuote
        quote = DailyQuote()
        quote.date = kline.date
        quote.open = kline.open
        quote.close = kline.close
        quote.high = kline.high
        quote.low = kline.low
        quote.volume = kline.volume
        quote.turnover = kline.turnover  # KlineData.turnover -> DailyQuote.turnover
        quote.source = self._wrapped.SOURCE
        return quote

    # ------------------------------------------------------------------
    # 重写：带缓存的 get_klines
    # ------------------------------------------------------------------

    def get_klines(
        self,
        name: str,
        start_date: DateLike = None,
        end_date: DateLike = None,
        limit: Optional[int] = None,
    ) -> list[DailyQuote]:
        """
        获取 K 线（带数据库缓存）。

        逻辑：
        1. 检查数据库中是否已有足够数据
        2. 如果已有，直接从 DB 返回
        3. 如果缺失，调用真实 API 拉取
        4. 拉取后存入 DB，再返回
        """
        db = self._get_db()

        # 确保表存在
        db.create_all_tables(name)

        # 获取请求范围
        start_str = self._date_to_str(start_date)
        end_str = self._date_to_str(end_date)

        # 查询数据库
        print(f"[CachedAPI] 查询数据库: {name}, 范围: {start_str} ~ {end_str}")
        db_data = db.get_latest_klines(name, limit or 1000)

        if db_data and len(db_data) > 0:
            # 有缓存数据，直接返回
            print(f"[CachedAPI] 从数据库返回 {len(db_data)} 条数据")
            result = [self._convert_to_daily_quote(k) for k in db_data]
            result.sort(key=lambda x: x.date)

            # 按日期范围过滤
            if start_str:
                result = [r for r in result if r.date >= start_str]
            if end_str:
                result = [r for r in result if r.date <= end_str]
            if limit and len(result) > limit:
                result = result[-limit:]

            if result:
                return result

        # 数据库无数据，调用真实 API
        print(f"[CachedAPI] 数据库无数据，调用 API: {self._wrapped.SOURCE}")
        quotes = self._wrapped.get_klines(name, start_date, end_date, limit)

        if not quotes:
            return []

        # 存入数据库
        print(f"[CachedAPI] 存储 {len(quotes)} 条数据到数据库")
        for q in quotes:
            kline = self._convert_to_kline_data(q)
            db.write_kline_data(name, kline)

        return quotes

    # ------------------------------------------------------------------
    # 重写：带缓存的 get_daily_quote
    # ------------------------------------------------------------------

    def get_daily_quote(
        self,
        name: str,
        date: DateLike = None,
    ) -> Optional[DailyQuote]:
        """
        获取单日行情（带缓存）。
        """
        target = self._date_to_str(date)

        # 先查数据库
        db = self._get_db()
        db.create_all_tables(name)

        if target:
            # 查询指定日期（长表：按 Symbol+Date 过滤）
            sql = (
                "SELECT Date, Open, Close, High, Low, Volume, Turnover, TurnoverRate, PE "
                f"FROM {db.TABLE_KLINE} WHERE Symbol=? AND Date=? LIMIT 1"
            )
            try:
                db._cursor.execute(sql, (name, target))
                row = db._cursor.fetchone()
                if row:
                    import sys
                    from pathlib import Path
                    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
                    from stock_info import KlineData
                    kline = KlineData()
                    if kline.parse(tuple(row)):
                        print(f"[CachedAPI] 从数据库返回单日数据: {target}")
                        return self._convert_to_daily_quote(kline)
            except Exception as e:
                print(f"[CachedAPI] 查询单日数据失败: {e}")

        # 数据库没有，调用 API
        quote = self._wrapped.get_daily_quote(name, date)
        if quote:
            # 存入数据库
            kline = self._convert_to_kline_data(quote)
            db.write_kline_data(name, kline)
        return quote

    # ------------------------------------------------------------------
    # 基本面数据（直接透传）
    # ------------------------------------------------------------------

    def get_fundamentals(self, name: str) -> Optional[StockFundamental]:
        """基本面数据暂不缓存，直接透传"""
        return self._wrapped.get_fundamentals(name)

    # ------------------------------------------------------------------
    # 支持性检查（透传）
    # ------------------------------------------------------------------

    def is_supported(self, name_key: str) -> bool:
        return self._wrapped.is_supported(name_key)
