# -*- coding: utf-8 -*-
"""AkShare：K 线 / 单日行情实现

统一走 AkShare 的日线历史接口，再按 [start_date, end_date] 过滤：
- A 股(SH/SZ): ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
- 港股(HK):    ak.stock_hk_hist(symbol=code, period="daily", adjust="qfq")
- COMEX:       ak.futures_foreign_hist(symbol=...)

依赖：pip install akshare
"""

from __future__ import annotations

from typing import Optional

import config
from stock_info import StockMarket
from quote_api.quote_base import DailyQuote, QuoteAPI, DateLike


class AkShareQuoteAPI(QuoteAPI):
    SOURCE = "akshare"

    def __init__(self) -> None:
        super().__init__()
        try:
            import akshare as ak  # noqa: F401
            self._ak = ak
        except ImportError:
            self._ak = None
            print("[AkShareQuoteAPI] akshare not installed, run: pip install akshare")

    # ------------------------------------------------------------------
    def get_klines(
        self,
        name: str,
        start_date: DateLike = None,
        end_date: DateLike = None,
        limit: Optional[int] = None,
    ) -> list[DailyQuote]:
        if self._ak is None:
            return []

        stock = config.global_stock_list.get(name)
        if stock is None:
            print("[AkShareQuoteAPI] unknown stock: %s" % name)
            return []

        sd = self.normalize_date(start_date)
        ed = self.normalize_date(end_date)

        df = self._fetch_history(stock.market, stock.code, sd, ed)
        if df is None or len(df) == 0:
            return []

        date_col = self._pick_column(df, ["日期", "date", "Date"])
        if date_col is None:
            return []

        results: list[DailyQuote] = []
        for _, row in df.iterrows():
            try:
                results.append(self._row_to_quote(row, date_col, name, stock.code))
            except Exception:
                continue

        return self.sort_and_trim(results, start_date=sd, end_date=ed, limit=limit)

    # ------------------------------------------------------------------
    def _fetch_history(
        self,
        market: StockMarket,
        code: str,
        start_date: Optional[str],
        end_date: Optional[str],
    ):
        ak = self._ak
        # A 股日线支持 start_date / end_date 参数（格式 YYYYMMDD）
        sd = start_date.replace("-", "") if start_date else None
        ed = end_date.replace("-", "") if end_date else None
        try:
            if market in (StockMarket.SH, StockMarket.SZ):
                kwargs = {"symbol": code, "period": "daily", "adjust": "qfq"}
                if sd:
                    kwargs["start_date"] = sd
                if ed:
                    kwargs["end_date"] = ed
                return ak.stock_zh_a_hist(**kwargs)
            if market == StockMarket.HK:
                kwargs = {"symbol": code, "period": "daily", "adjust": "qfq"}
                if sd:
                    kwargs["start_date"] = sd
                if ed:
                    kwargs["end_date"] = ed
                return ak.stock_hk_hist(**kwargs)
            if market == StockMarket.COMEX:
                try:
                    return ak.futures_foreign_hist(symbol=code)
                except Exception:
                    return None
        except Exception as e:
            print("[AkShareQuoteAPI] fetch history error: %s" % e)
        return None

    # ------------------------------------------------------------------
    @staticmethod
    def _pick_column(df, candidates: list[str]) -> Optional[str]:
        cols = list(df.columns)
        for c in candidates:
            if c in cols:
                return c
        return None

    # ------------------------------------------------------------------
    def _row_to_quote(self, row, date_col: str, name: str, code: str) -> DailyQuote:
        def fget(keys: list[str], default: float = 0.0) -> float:
            for k in keys:
                if k in row.index:
                    try:
                        return float(row[k])
                    except Exception:
                        continue
            return default

        q = DailyQuote()
        q.source = self.SOURCE
        q.name = name
        q.code = code
        q.date = str(row[date_col])[:10]
        q.open = fget(["开盘", "open", "Open"])
        q.close = fget(["收盘", "close", "Close"])
        q.high = fget(["最高", "high", "High"])
        q.low = fget(["最低", "low", "Low"])
        q.pre_close = fget(["昨收", "pre_close"])
        q.volume = fget(["成交量", "volume", "Volume"])
        q.turnover = fget(["成交额", "amount", "turnover"])
        return q
