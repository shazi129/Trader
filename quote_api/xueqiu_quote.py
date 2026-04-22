# -*- coding: utf-8 -*-
"""雪球：K 线 / 单日行情实现

接口：https://stock.xueqiu.com/v5/stock/chart/kline.json
特点：
- A/港/美一套代码体系，JSON 返回纯净
- 必须先访问一次 xueqiu.com 拿到 Cookie（xq_a_token），否则 400
- count 参数支持正/负：正数=从 begin 向后取；负数=从 begin 向前取

仅使用 requests，无需第三方 SDK。
"""

from __future__ import annotations

import datetime
import json
from typing import Optional

import requests

import config
from stock_info import StockMarket
from quote_api.quote_base import DailyQuote, QuoteAPI, DateLike


class XueqiuQuoteAPI(QuoteAPI):
    SOURCE = "xueqiu"

    _KLINE_URL = "https://stock.xueqiu.com/v5/stock/chart/kline.json"
    _HOME_URL = "https://xueqiu.com/"

    # 雪球单次最大返回量（官方未公布，实测 ~1000 条安全）
    _MAX_COUNT_PER_REQUEST = 1000

    def __init__(self) -> None:
        super().__init__()
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
        })
        self._cookie_ready = False

    # ------------------------------------------------------------------
    def _ensure_cookie(self) -> None:
        if self._cookie_ready:
            return
        try:
            self._session.get(self._HOME_URL, timeout=self.DEFAULT_TIMEOUT)
            self._cookie_ready = True
        except Exception as e:
            print("[XueqiuQuoteAPI] warm-up cookie failed: %s" % e)

    # ------------------------------------------------------------------
    def _xq_symbol(self, market: StockMarket, code: str) -> Optional[str]:
        if market == StockMarket.SH:
            return "SH%s" % code
        if market == StockMarket.SZ:
            return "SZ%s" % code
        if market == StockMarket.HK:
            return code.zfill(5)
        return None  # 无商品期货

    # ------------------------------------------------------------------
    def get_klines(
        self,
        name: str,
        start_date: DateLike = None,
        end_date: DateLike = None,
        limit: Optional[int] = None,
    ) -> list[DailyQuote]:
        stock = config.global_stock_list.get(name)
        if stock is None:
            print("[XueqiuQuoteAPI] unknown stock: %s" % name)
            return []

        symbol = self._xq_symbol(stock.market, stock.code)
        if symbol is None:
            print("[XueqiuQuoteAPI] market not supported: %s" % stock.market)
            return []

        self._ensure_cookie()

        sd = self.normalize_date(start_date)
        ed = self.normalize_date(end_date)

        # 策略：以 end_date（或 now）为 begin，向前循环拉取，直到跨过 start_date 或达到 limit
        if ed:
            end_dt = datetime.datetime.strptime(ed, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59
            )
        else:
            end_dt = datetime.datetime.now()

        # 目标总条数
        if limit is not None and limit > 0:
            target_total = limit
        elif sd:
            # 起止区间：按自然日估算，保留缓冲（考虑周末节假日）
            start_dt = datetime.datetime.strptime(sd, "%Y-%m-%d")
            target_total = max(1, (end_dt - start_dt).days + 5)
        else:
            target_total = self._MAX_COUNT_PER_REQUEST

        collected: list[DailyQuote] = []
        cursor_ms = int(end_dt.timestamp() * 1000)
        remaining = target_total
        start_ts = (
            int(datetime.datetime.strptime(sd, "%Y-%m-%d").timestamp() * 1000)
            if sd else None
        )

        while remaining > 0:
            batch = min(remaining, self._MAX_COUNT_PER_REQUEST)
            items, columns = self._request_page(symbol, cursor_ms, -batch)
            if not items:
                break

            idx_ts = columns.index("timestamp") if "timestamp" in columns else 0
            for row in items:
                q = self._row_to_quote(row, columns, name, symbol)
                if q is not None:
                    collected.append(q)

            # 本页最早的一条时间戳
            earliest_ts = min(r[idx_ts] for r in items if r[idx_ts] is not None)
            # 下页 begin 要比 earliest_ts 更早，否则会无限循环
            next_cursor = earliest_ts - 1

            if len(items) < batch:
                break
            if start_ts is not None and earliest_ts <= start_ts:
                break
            if next_cursor >= cursor_ms:
                break
            cursor_ms = next_cursor
            remaining -= len(items)

        return self.sort_and_trim(collected, start_date=sd, end_date=ed, limit=limit)

    # ------------------------------------------------------------------
    def _request_page(
        self, symbol: str, begin_ms: int, count: int
    ) -> tuple[list, list[str]]:
        params = {
            "symbol": symbol,
            "begin": begin_ms,
            "period": "day",
            "type": "before",   # 前复权
            "count": count,     # 负数=向前取
            "indicator": "kline",
        }
        try:
            resp = self._session.get(
                self._KLINE_URL, params=params, timeout=self.DEFAULT_TIMEOUT
            )
            payload = json.loads(resp.text)
        except Exception as e:
            print("[XueqiuQuoteAPI] request error: %s" % e)
            return [], []

        data = payload.get("data") if isinstance(payload, dict) else None
        if not data:
            return [], []
        return data.get("item") or [], data.get("column") or []

    # ------------------------------------------------------------------
    @staticmethod
    def _row_to_quote(
        row: list, columns: list[str], name: str, symbol: str
    ) -> Optional[DailyQuote]:
        def col(key: str, default: float = 0.0) -> float:
            if key not in columns:
                return default
            v = row[columns.index(key)]
            try:
                return float(v) if v is not None else default
            except Exception:
                return default

        idx_ts = columns.index("timestamp") if "timestamp" in columns else 0
        ts = row[idx_ts]
        if ts is None:
            return None
        try:
            date_str = datetime.datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d")
        except Exception:
            return None

        q = DailyQuote()
        q.source = XueqiuQuoteAPI.SOURCE
        q.name = name
        q.code = symbol
        q.date = date_str
        q.open = col("open")
        q.close = col("close")
        q.high = col("high")
        q.low = col("low")
        q.volume = col("volume")
        q.turnover = col("amount")
        return q
