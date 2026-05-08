# -*- coding: utf-8 -*-
"""yfinance：K 线 / 单日行情实现

面向港股 / 美股 / 外汇 / 商品期货等全球标的，数据来自 Yahoo Finance。

标的代码映射：
- HK:    {code}.HK   (港股 5 位数代码)
- SH:    {code}.SS   (上证)
- SZ:    {code}.SZ   (深证)
- COMEX: 期货连续合约代码；"SI00Y" 等项目内部代码已在 _COMEX_MAP 中映射。

依赖：pip install yfinance
"""

from __future__ import annotations

import datetime
import time
from typing import Optional

import config
from stock_info import StockMarket
from quote_api.quote_base import DailyQuote, QuoteAPI, DateLike


# COMEX 常见合约映射（项目内部代码 -> yfinance 代码）
_COMEX_MAP = {
    "SI00Y": "SI=F",   # 白银
    "GC00Y": "GC=F",   # 黄金
    "HG00Y": "HG=F",   # 铜
    "CL00Y": "CL=F",   # 原油
}


class YFinanceQuoteAPI(QuoteAPI):
    SOURCE = "yfinance"

    def __init__(self) -> None:
        super().__init__()
        try:
            import yfinance as yf  # noqa: F401
            self._yf = yf
        except ImportError:
            self._yf = None
            print("[YFinanceQuoteAPI] yfinance not installed, run: pip install yfinance")
        
        # 重试参数
        self._retry_count = 3
        self._retry_delay = 5  # 秒

    # ------------------------------------------------------------------
    def _yahoo_symbol(self, market: StockMarket, code: str) -> Optional[str]:
        if market == StockMarket.HK:
            return "%s.HK" % code.zfill(5)
        if market == StockMarket.SH:
            return "%s.SS" % code
        if market == StockMarket.SZ:
            return "%s.SZ" % code
        if market == StockMarket.COMEX:
            return _COMEX_MAP.get(code, code)
        # 美股市场（NASDAQ/NYSE/US）直接使用代码
        if market in (StockMarket.NASDAQ, StockMarket.NYSE, StockMarket.US):
            return code
        return None

    # ------------------------------------------------------------------
    def get_klines(
        self,
        name: str,
        start_date: DateLike = None,
        end_date: DateLike = None,
        limit: Optional[int] = None,
    ) -> list[DailyQuote]:
        if self._yf is None:
            return []

        stock = config.global_stock_list.get(name)
        if stock is None:
            print("[YFinanceQuoteAPI] unknown stock: %s" % name)
            return []

        symbol = self._yahoo_symbol(stock.market, stock.code)
        if symbol is None:
            print("[YFinanceQuoteAPI] unsupported market: %s" % stock.market)
            return []

        sd = self.normalize_date(start_date)
        ed = self.normalize_date(end_date)

        # 构造 history() 参数
        kwargs = {"interval": "1d", "auto_adjust": False}
        if sd or ed:
            # start / end 都是字符串 YYYY-MM-DD，Yahoo 的 end 是开区间，需要 +1
            if sd:
                kwargs["start"] = sd
            if ed:
                ed_dt = datetime.datetime.strptime(ed, "%Y-%m-%d") + datetime.timedelta(days=1)
                kwargs["end"] = ed_dt.strftime("%Y-%m-%d")
            if not sd:
                # 只给了 end：默认回溯 5 年
                five_y = (datetime.datetime.strptime(ed, "%Y-%m-%d")
                          - datetime.timedelta(days=365 * 5))
                kwargs["start"] = five_y.strftime("%Y-%m-%d")
        else:
            # 未给区间：由 limit 决定周期
            if limit is not None and limit > 0:
                # 近似取天数，再交给 sort_and_trim 截尾
                kwargs["period"] = self._limit_to_period(limit)
            else:
                kwargs["period"] = "max"

        # 添加重试逻辑
        df = None
        for attempt in range(self._retry_count):
            try:
                if attempt > 0:
                    wait_time = self._retry_delay * (attempt + 1)
                    print("[YFinanceQuoteAPI] Retry %s/%s, waiting %s seconds..." % (attempt + 1, self._retry_count, wait_time))
                    time.sleep(wait_time)
                else:
                    time.sleep(self._retry_delay)
                
                ticker = self._yf.Ticker(symbol)
                df = ticker.history(**kwargs)
                break  # 成功，跳出循环
            except Exception as e:
                error_msg = str(e)
                if "Rate limit" in error_msg and attempt < self._retry_count - 1:
                    wait_time = self._retry_delay * (attempt + 2)
                    print("[YFinanceQuoteAPI] Rate limited, waiting %s seconds (attempt %s/%s)..." % (wait_time, attempt + 1, self._retry_count))
                    time.sleep(wait_time)
                elif attempt < self._retry_count - 1:
                    print("[YFinanceQuoteAPI] Attempt %s failed: %s" % (attempt + 1, e))
                else:
                    print("[YFinanceQuoteAPI] All attempts failed: %s" % e)
                    return []
        
        if df is None or len(df) == 0:
            return []

        if df is None or len(df) == 0:
            return []

        results: list[DailyQuote] = []
        for idx, row in df.iterrows():
            try:
                date_str = idx.strftime("%Y-%m-%d")
            except Exception:
                date_str = str(idx)[:10]
            q = DailyQuote()
            q.source = self.SOURCE
            q.name = name
            q.code = symbol
            q.date = date_str
            q.open = float(row.get("Open", 0) or 0)
            q.close = float(row.get("Close", 0) or 0)
            q.high = float(row.get("High", 0) or 0)
            q.low = float(row.get("Low", 0) or 0)
            q.volume = float(row.get("Volume", 0) or 0)
            q.turnover = q.volume * q.close   # Yahoo 不直接返回成交额，估算
            results.append(q)

        return self.sort_and_trim(results, start_date=sd, end_date=ed, limit=limit)

    # ------------------------------------------------------------------
    @staticmethod
    def _limit_to_period(limit: int) -> str:
        """把条数换算成 yfinance 的 period 字符串（按交易日约 250/年 估算）"""
        if limit <= 5:
            return "5d"
        if limit <= 30:
            return "1mo"
        if limit <= 90:
            return "3mo"
        if limit <= 180:
            return "6mo"
        if limit <= 260:
            return "1y"
        if limit <= 520:
            return "2y"
        if limit <= 1300:
            return "5y"
        if limit <= 2600:
            return "10y"
        return "max"
