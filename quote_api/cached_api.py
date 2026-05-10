# -*- coding: utf-8 -*-
"""
带缓存的行情 API 包装器

实现"先读DB，缺失再拉取"的逻辑。
对调用者透明：使用方式与普通 QuoteAPI 完全一致。
"""

from __future__ import annotations

from typing import Optional

from quote_api.quote_base import (
    QuoteAPI,
    DailyQuote,
    StockFundamental,
    DateLike,
)
from utils.logger import get_logger

_log = get_logger(__name__)


class CachedQuoteAPI(QuoteAPI):
    """
    带数据库缓存的 API 包装器。

    用法（推荐用 ``with``，确保 DB 连接被关闭）::

        raw_api = QuoteAPIFactory.create("eastmoney")
        with CachedQuoteAPI(raw_api) as api:
            klines = api.get_klines("Tencent", limit=500)

    或显式调用 ``api.close()``。
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

    # ------------------------------------------------------------------
    # 资源管理
    # ------------------------------------------------------------------

    def close(self) -> None:
        """关闭内部数据库连接（可重入：再次调用是 no-op）。"""
        if self._db is not None:
            try:
                self._db.close()
            except Exception as e:  # pragma: no cover - defensive
                _log.warning("close cached db error: %s", e)
            self._db = None

    def __enter__(self) -> "CachedQuoteAPI":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __del__(self):  # 兜底
        try:
            self.close()
        except Exception:
            pass

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
        """获取 K 线（带数据库缓存）。

        策略（"按 [start, end] 区间，缺哪段补哪段"）：
        1. 没有任何过滤条件且没传 limit  →  直接看 DB 是否有数据，没有就全量拉。
        2. 指定了 start_date  →  比较 DB 已覆盖的最大日期，缺的尾段调上游补；
                                  然后再用 get_klines_in_range 返回完整区间。
        3. 只传 limit、不传日期  →  DB 取最近 N 条；不足则上游拉最新一段补齐。

        关键修复 vs 旧版：
        - 旧版只要 DB 里有 1 条就直接返回，**永远不补漏**。
        - 旧版限额硬编码 1000，与 start/end 的语义割裂。
        """
        db = self._get_db()
        sd = self._date_to_str(start_date)
        ed = self._date_to_str(end_date)
        wrapped_source = self._wrapped.SOURCE

        # ---- 分支 A: 指定了起止日期（最常见路径）----
        if sd is not None or ed is not None:
            latest_in_db = db.get_latest_date(name)

            need_fetch_from: Optional[str] = None
            if latest_in_db is None:
                # DB 完全没数据，整段从 sd（或上游默认起点）拉
                need_fetch_from = sd
            elif ed is None or latest_in_db < ed:
                # DB 有数据，但尾段不全
                # 取 max(sd, latest_in_db+1) 作为补拉起点
                from datetime import datetime, timedelta
                next_day = (
                    datetime.strptime(latest_in_db, "%Y-%m-%d") + timedelta(days=1)
                ).strftime("%Y-%m-%d")
                need_fetch_from = max(sd, next_day) if sd else next_day

            if need_fetch_from is not None and (ed is None or need_fetch_from <= ed):
                _log.info("%s: 补拉 %s ~ %s", name, need_fetch_from, ed or "latest")
                fresh = self._wrapped.get_klines(name, start_date=need_fetch_from, end_date=ed)
                if fresh:
                    db.write_kline_data_many(name, fresh)
                    _log.info("%s: 入库 %d 条", name, len(fresh))

            # 从 DB 读完整区间，统一来源标识
            result = db.get_klines_in_range(name, start_date=sd, end_date=ed)
            for q in result:
                q.source = wrapped_source
            if limit and len(result) > limit:
                result = result[-limit:]
            return result

        # ---- 分支 B: 没指定日期，按 limit 取最近 N 条 ----
        size = limit if (limit and limit > 0) else 1000
        cached = db.get_latest_klines(name, size)  # 已按 Date DESC
        if len(cached) >= size:
            cached.sort(key=lambda x: x.date)
            for q in cached:
                q.source = wrapped_source
            return cached

        # DB 不够：拉上游补齐到最新
        _log.info("%s: DB 现有 %d 条 < 需求 %d，调用上游补齐", name, len(cached), size)
        # 简单策略：直接全量拉 size 条最新（上游侧不支持回溯型增量）
        fresh = self._wrapped.get_klines(name, limit=size)
        if fresh:
            db.write_kline_data_many(name, fresh)
            _log.info("%s: 入库 %d 条", name, len(fresh))

        # 再从 DB 读最近 size 条，保证返回的是合并后的完整序列
        result = db.get_latest_klines(name, size)
        result.sort(key=lambda x: x.date)
        for q in result:
            q.source = wrapped_source
        return result

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

        if target:
            cached = db.get_daily_quote_by_date(name, target)
            if cached:
                cached.source = self._wrapped.SOURCE
                _log.info("从数据库返回单日数据: %s", target)
                return cached

        # 数据库没有，调用 API
        quote = self._wrapped.get_daily_quote(name, date)
        if quote:
            db.write_kline_data(name, quote)
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
