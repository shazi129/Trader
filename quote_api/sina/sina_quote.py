# -*- coding: utf-8 -*-
"""新浪财经：K 线 / 单日行情实现

接口说明：

1) 实时快照（A 股 / 港股）
   https://hq.sinajs.cn/list=<symbol>
   - A 股 symbol：sh600519 / sz000001
   - 港股 symbol：rt_hk00700  （港股必须用 rt_ 前缀）
   - 必须带 Referer=https://finance.sina.com.cn，否则 403
   - 响应是 GBK 编码的 JS 片段：
       var hq_str_sh600519="贵州茅台,1680.00,1699.00,1705.50,...";
     A 股字段顺序：[0]=名称 [1]=今开 [2]=昨收 [3]=最新价 [4]=最高 [5]=最低
                   [8]=成交量(股) [9]=成交额(元) [30]=日期 [31]=时间
     港股字段顺序（rt_hk）:
       [0]=英文名 [1]=中文名 [2]=今开 [3]=昨收 [4]=最高 [5]=最低
       [6]=最新价 [7]=涨跌额 [8]=涨跌幅 ... [10]=成交量 [11]=成交额
       [17]=日期 [18]=时间

2) 历史 K 线
   - A 股：
     https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData
       ?symbol=sh600519&scale=240&ma=no&datalen=<n>
     scale=240 即日线；返回 JSON 数组：
       [{"day":"2025-02-04","open":"...","high":"...","low":"...","close":"...","volume":"..."}]
   - 港股：
     https://finance.sina.com.cn/staticdata/hk/<CODE>.js   （较旧接口，不稳定）
     备选：
     https://quotes.sina.cn/hk/api/jsonp_v2.php/var%20_hk<code>_<scale>_=/KC_MarketDataService.getKLineData
       ?symbol=hk<code>&scale=240&datalen=<n>
   - COMEX：新浪无统一接口，返回空。
"""

from __future__ import annotations

import datetime
import json
import re
from typing import Optional

import requests

import config
from stock_info import StockMarket
from quote_api.quote_base import DailyQuote, QuoteAPI, DateLike


class SinaQuoteAPI(QuoteAPI):
    SOURCE = "sina"

    _RT_URL = "https://hq.sinajs.cn/list="
    _KLINE_CN_URL = (
        "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/"
        "CN_MarketData.getKLineData"
    )

    _HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Referer": "https://finance.sina.com.cn",
    }

    def __init__(self) -> None:
        super().__init__()
        self._session = requests.Session()
        self._session.headers.update(self._HEADERS)

    # ------------------------------------------------------------------
    def _sina_symbol(self, market: StockMarket, code: str, realtime: bool = False) -> Optional[str]:
        """生成新浪接口使用的 symbol。

        realtime=True 用于实时行情：港股需要 rt_ 前缀。
        """
        if market == StockMarket.SH:
            return "sh%s" % code
        if market == StockMarket.SZ:
            return "sz%s" % code
        if market == StockMarket.HK:
            hk_code = code.zfill(5)
            return ("rt_hk%s" % hk_code) if realtime else ("hk%s" % hk_code)
        # COMEX 等在新浪财经不统一支持
        return None

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
            print("[SinaQuoteAPI] unknown stock: %s" % name)
            return []

        symbol = self._sina_symbol(stock.market, stock.code, realtime=False)
        if symbol is None:
            print("[SinaQuoteAPI] market not supported: %s" % stock.market)
            return []

        sd = self.normalize_date(start_date)
        ed = self.normalize_date(end_date)

        # 新浪 K 线只能用 datalen 限定最新 N 条，没有 start/end 参数。
        # 如果用户指定了 start_date，扩大 datalen 然后本地过滤。
        count = limit if (limit is not None and limit > 0) else 240
        if sd is not None:
            # 粗略估算：从 sd 到今天的自然日数上取整 + 10 作为缓冲
            try:
                d0 = datetime.datetime.strptime(sd, "%Y-%m-%d")
                days = (datetime.datetime.now() - d0).days + 10
                count = max(count, min(days, 1000))
            except Exception:
                pass

        rows = self._fetch_kline_rows(stock.market, symbol, count)
        if not rows:
            return []

        results: list[DailyQuote] = []
        for row in rows:
            q = self._row_to_quote(row, name, symbol)
            if q is not None:
                results.append(q)

        return self.sort_and_trim(results, start_date=sd, end_date=ed, limit=limit)

    # ------------------------------------------------------------------
    def _fetch_kline_rows(
        self, market: StockMarket, symbol: str, count: int
    ) -> list[dict]:
        try:
            if market in (StockMarket.SH, StockMarket.SZ):
                params = {
                    "symbol": symbol,
                    "scale": 240,
                    "ma": "no",
                    "datalen": count,
                }
                resp = self._session.get(
                    self._KLINE_CN_URL, params=params, timeout=self.DEFAULT_TIMEOUT
                )
                text = resp.text.strip()
                # 新浪返回有时是带 var 的 JS，有时直接是 JSON
                m = re.search(r"(\[.*\])", text, re.S)
                raw = m.group(1) if m else text
                data = json.loads(raw)
                if not isinstance(data, list):
                    return []
                return data

            if market == StockMarket.HK:
                # 新浪财经已下线公开的港股历史 K 线接口，仅实时快照可用。
                # 如需港股历史 K 线，请改用 tencent / eastmoney / akshare 等数据源。
                print(
                    "[SinaQuoteAPI] HK kline is not available on Sina; "
                    "please use another source (tencent/eastmoney/akshare)."
                )
                return []
        except Exception as e:
            print("[SinaQuoteAPI] kline request error: %s" % e)
            return []
        return []

    # ------------------------------------------------------------------
    # override：最新一条直接走实时接口
    def get_daily_quote(
        self,
        name: str,
        date: DateLike = None,
    ) -> Optional[DailyQuote]:
        target = self.normalize_date(date)
        if target is None:
            snap = self._fetch_realtime(name)
            if snap is not None:
                return snap
            items = self.get_klines(name, limit=1)
            return items[-1] if items else None

        items = self.get_klines(name, start_date=target, end_date=target, limit=1)
        if not items:
            return None
        for q in items:
            if q.date == target:
                return q
        return items[-1]

    # ------------------------------------------------------------------
    def _fetch_realtime(self, name: str) -> Optional[DailyQuote]:
        stock = config.global_stock_list.get(name)
        if stock is None:
            return None
        symbol = self._sina_symbol(stock.market, stock.code, realtime=True)
        if symbol is None:
            return None

        try:
            resp = self._session.get(
                self._RT_URL + symbol, timeout=self.DEFAULT_TIMEOUT
            )
            raw = resp.content.decode("gbk", errors="ignore")
        except Exception as e:
            print("[SinaQuoteAPI] realtime request error: %s" % e)
            return None

        m = re.search(r'"([^"]*)"', raw)
        if not m:
            return None
        payload = m.group(1)
        if not payload:
            return None
        fields = payload.split(",")

        if stock.market == StockMarket.HK:
            return self._parse_realtime_hk(fields, name, symbol)
        return self._parse_realtime_cn(fields, name, symbol)

    # ------------------------------------------------------------------
    @staticmethod
    def _safe_float(v, default: float = 0.0) -> float:
        try:
            return float(v)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _normalize_sina_date(raw: str) -> str:
        """把新浪返回的日期统一为 'YYYY-MM-DD'。
        新浪 A 股用 '-', 港股有时用 '/'。
        """
        if not raw:
            return datetime.datetime.now().strftime("%Y-%m-%d")
        s = raw.strip().replace("/", "-")
        return s[:10]

    # ------------------------------------------------------------------
    def _parse_realtime_cn(self, fields: list, name: str, symbol: str) -> Optional[DailyQuote]:
        # A 股字段顺序（新浪 hq_str_shXXXXXX）：
        # 0: 名称 1: 今开 2: 昨收 3: 最新价 4: 最高 5: 最低
        # 6: 竞买价 7: 竞卖价 8: 成交量(股) 9: 成交额(元)
        # ... 30: 日期 31: 时间
        if len(fields) < 10:
            return None
        q = DailyQuote()
        q.source = self.SOURCE
        q.name = name
        q.code = symbol
        q.open = self._safe_float(fields[1])
        q.pre_close = self._safe_float(fields[2])
        q.close = self._safe_float(fields[3])  # 最新价当收盘
        q.high = self._safe_float(fields[4])
        q.low = self._safe_float(fields[5])
        q.volume = self._safe_float(fields[8])  # 已经是"股"
        q.turnover = self._safe_float(fields[9])
        q.date = self._normalize_sina_date(fields[30] if len(fields) > 30 else "")
        if q.close <= 0:
            return None
        return q

    # ------------------------------------------------------------------
    def _parse_realtime_hk(self, fields: list, name: str, symbol: str) -> Optional[DailyQuote]:
        # 港股 rt_hkXXXXX 字段顺序：
        # 0: 英文名 1: 中文名 2: 今开 3: 昨收 4: 最高 5: 最低
        # 6: 最新价 7: 涨跌额 8: 涨跌幅 9: 买一价 ...
        # 10: 成交量 11: 成交额 ... 17: 日期 18: 时间
        if len(fields) < 12:
            return None
        q = DailyQuote()
        q.source = self.SOURCE
        q.name = name
        q.code = symbol
        q.open = self._safe_float(fields[2])
        q.pre_close = self._safe_float(fields[3])
        q.high = self._safe_float(fields[4])
        q.low = self._safe_float(fields[5])
        q.close = self._safe_float(fields[6])
        q.volume = self._safe_float(fields[10])
        q.turnover = self._safe_float(fields[11])
        q.date = self._normalize_sina_date(fields[17] if len(fields) > 17 else "")
        if q.close <= 0:
            return None
        return q

    # ------------------------------------------------------------------
    @staticmethod
    def _row_to_quote(row: dict, name: str, symbol: str) -> Optional[DailyQuote]:
        if not isinstance(row, dict):
            return None
        try:
            q = DailyQuote()
            q.source = SinaQuoteAPI.SOURCE
            q.name = name
            q.code = symbol
            q.date = str(row.get("day") or row.get("date") or "")[:10]
            q.open = float(row.get("open") or 0)
            q.close = float(row.get("close") or 0)
            q.high = float(row.get("high") or 0)
            q.low = float(row.get("low") or 0)
            q.volume = float(row.get("volume") or 0)
            # 新浪 K 线接口没有直接返回金额，留 0
            q.turnover = float(row.get("amount") or 0)
            if not q.date or q.close <= 0:
                return None
            return q
        except Exception:
            return None
