# -*- coding: utf-8 -*-
"""
带缓存的行情 API 包装器

实现"先读DB，缺失再拉取"的逻辑。
对调用者透明：使用方式与普通 QuoteAPI 完全一致。
"""

from __future__ import annotations

from datetime import datetime, date as _date, timedelta
from typing import Optional

from quote_api.quote_base import (
    QuoteAPI,
    DailyQuote,
    StockFundamental,
    DateLike,
)
from quote_api.stock_meta import get_meta
from utils.logger import get_logger

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# 分批拉取窗口（按交易日数计）
#
# 各上游单次拉取的物理上限：
#   - 腾讯  count 上限 ≈ 640（最弱）
#   - 新浪  datalen 上限 1000
#   - 东方财富  lmt 上限 ~100000（基本不限）
#
# 取最弱源的安全值：600 交易日 ≈ 840 日历日（约 2.3 年），保证三家都稳。
# ---------------------------------------------------------------------------
BATCH_TRADING_DAYS = 600
# 交易日 → 日历日的安全换算（每周 5 个交易日，向上取整再加缓冲）
BATCH_CALENDAR_DAYS = int(BATCH_TRADING_DAYS * 7 / 5) + 7


def _split_into_batches(start: str, end: str,
                        batch_days: int = BATCH_CALENDAR_DAYS
                        ) -> list[tuple[str, str]]:
    """把 [start, end] 按 batch_days 个日历日切片，返回 [(s1,e1), (s2,e2), ...]。

    切片从 start 起向后推进，最后一段对齐到 end。所有边界含两端。
    """
    s = datetime.strptime(start, "%Y-%m-%d").date()
    e = datetime.strptime(end, "%Y-%m-%d").date()
    if s > e:
        return []
    batches: list[tuple[str, str]] = []
    cur = s
    while cur <= e:
        nxt = min(cur + timedelta(days=batch_days - 1), e)
        batches.append((cur.strftime("%Y-%m-%d"), nxt.strftime("%Y-%m-%d")))
        cur = nxt + timedelta(days=1)
    return batches


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

        统一策略 —— **按 [start_date, end_date] 区间补齐**：

        1. 算出 *目标区间* ``[sd_target, ed_target]``：
           - ``sd_target`` 优先级： ``start_date`` 参数 > ``meta.listing_date``。
           - ``ed_target`` 优先级： ``end_date`` 参数 > 今天。
           - 若调用方传了 ``limit`` 但没传日期，则把 ``limit`` 当作"取最近 N 条"
             的上限：仅在最终返回时切片，**拉取范围仍按完整区间**算（即从
             ``meta.listing_date`` 开始）。这样 DB 一旦填满，后续无论传多少
             ``limit`` 都不会再触发上游请求。
        2. 比较 DB 已有最大日期 ``latest_in_db``：
           - DB 全空     → 补拉 ``[sd_target, ed_target]`` 全部
           - DB 有数据   → 仅补拉 ``[max(sd_target, latest_in_db+1), ed_target]``
        3. 若需要补拉的跨度 > 单批安全窗口（``BATCH_CALENDAR_DAYS``，约 840 日历
           日），按窗口切片**逐批向上游请求并入库**，避免一次拉爆 / 触发上游限流。
           小区间（≤ 一个窗口）则一次性拉完。
        4. 最终从 DB 读 ``[sd_target, ed_target]`` 完整序列返回；
           若传了 ``limit``，再取尾部 N 条。
        """
        db = self._get_db()
        sd = self._date_to_str(start_date)
        ed = self._date_to_str(end_date)
        wrapped_source = self._wrapped.SOURCE

        # ---- 1) 计算目标区间 ---------------------------------------------
        today_str = _date.today().strftime("%Y-%m-%d")
        ed_target = ed or today_str

        if sd:
            sd_target = sd
        else:
            # 未指定起始 → 从 meta.listing_date 开始（用户规则 1）
            meta = get_meta(name)
            if meta and meta.listing_date:
                sd_target = meta.listing_date
            else:
                # meta 缺失：保守起点（足够覆盖大多数因子的最长窗口）
                sd_target = (
                    _date.today() - timedelta(days=BATCH_CALENDAR_DAYS)
                ).strftime("%Y-%m-%d")

        if sd_target > ed_target:
            return []

        # ---- 2) 确定补拉起点 ---------------------------------------------
        latest_in_db = db.get_latest_date(name)
        if latest_in_db is None:
            need_fetch_from: Optional[str] = sd_target
        elif latest_in_db < ed_target:
            next_day = (
                datetime.strptime(latest_in_db, "%Y-%m-%d") + timedelta(days=1)
            ).strftime("%Y-%m-%d")
            # 若 DB 最新日期 >= sd_target，说明区间头部已覆盖，只补尾部
            need_fetch_from = max(sd_target, next_day)
        else:
            need_fetch_from = None  # DB 已覆盖到 ed_target，无需上游

        # ---- 3) 分批拉取（如需要）---------------------------------------
        if need_fetch_from is not None and need_fetch_from <= ed_target:
            batches = _split_into_batches(need_fetch_from, ed_target)
            _log.info(
                "%s: 区间补齐 %s ~ %s（共 %d 批）",
                name, need_fetch_from, ed_target, len(batches),
            )
            for i, (b_s, b_e) in enumerate(batches, 1):
                try:
                    fresh = self._wrapped.get_klines(
                        name, start_date=b_s, end_date=b_e
                    )
                except Exception as exc:
                    _log.warning("%s: 第 %d/%d 批 %s~%s 拉取失败: %s",
                                 name, i, len(batches), b_s, b_e, exc)
                    continue
                if fresh:
                    db.write_kline_data_many(name, fresh)
                    _log.info(
                        "%s: 第 %d/%d 批 %s~%s 入库 %d 条",
                        name, i, len(batches), b_s, b_e, len(fresh),
                    )

        # ---- 4) 从 DB 读完整区间 ----------------------------------------
        result = db.get_klines_in_range(name, start_date=sd_target,
                                        end_date=ed_target)
        for q in result:
            q.source = wrapped_source
        # limit 仅做尾部截断，不影响上游拉取范围
        if limit and limit > 0 and len(result) > limit:
            result = result[-limit:]
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
