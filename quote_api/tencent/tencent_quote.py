# -*- coding: utf-8 -*-
"""腾讯财经：K 线 / 单日行情实现

两个接口协同：
- 实时快照：https://qt.gtimg.cn/q=<symbol>
    返回形如 v_hk00700="~腾讯控股~00700~507.000~503.500~...";
    字段分隔符 ~，最新价在 fields[3]，昨收 fields[4]，今开 fields[5]
    涨跌额 fields[31]，涨跌幅 fields[32]，最高 fields[33]，最低 fields[34]

- 历史 K 线：https://web.ifzq.gtimg.cn/appstock/app/fqkline/get
    param: ?param=<symbol>,day,<start>,<end>,<count>,qfq
    返回 data[<symbol>].qfqday / day 数组；行：[date, open, close, high, low, volume, info]

symbol 规则（小写前缀 + 代码）：
    A 股：sh600519 / sz000001
    港股：hk00700        (HK 5 位数代码)
    美股：usAAPL         (暂不在 global_stock_list 内，预留)
    COMEX 等期货在腾讯财经无统一覆盖，返回空。
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


class TencentQuoteAPI(QuoteAPI):
    SOURCE = "tencent"

    _RT_URL = "https://qt.gtimg.cn/q="
    _KLINE_URL = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"

    _HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Referer": "https://finance.qq.com",
    }

    def __init__(self) -> None:
        super().__init__()
        self._session = requests.Session()
        self._session.headers.update(self._HEADERS)

    # ------------------------------------------------------------------
    def _tencent_symbol(self, market: StockMarket, code: str) -> Optional[str]:
        if market == StockMarket.SH:
            return "sh%s" % code
        if market == StockMarket.SZ:
            return "sz%s" % code
        if market == StockMarket.HK:
            return "hk%s" % code.zfill(5)
        # COMEX 等在腾讯财经不支持
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
            print("[TencentQuoteAPI] unknown stock: %s" % name)
            return []

        symbol = self._tencent_symbol(stock.market, stock.code)
        if symbol is None:
            print("[TencentQuoteAPI] market not supported: %s" % stock.market)
            return []

        sd = self.normalize_date(start_date)
        ed = self.normalize_date(end_date)

        # 腾讯 K 线接口 count 上限约 640；区间型查询优先用 start/end
        count = limit if (limit is not None and limit > 0) else 640

        params = {
            "param": "%s,day,%s,%s,%d,qfq"
            % (symbol, sd or "", ed or "", count),
            "_var": "",
        }

        try:
            resp = self._session.get(
                self._KLINE_URL, params=params, timeout=self.DEFAULT_TIMEOUT
            )
            payload = json.loads(resp.text)
        except Exception as e:
            print("[TencentQuoteAPI] kline request error: %s" % e)
            return []

        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            return []
        bucket = data.get(symbol) or {}
        rows = bucket.get("qfqday") or bucket.get("day") or []
        if not rows:
            return []

        results: list[DailyQuote] = []
        for row in rows:
            q = self._row_to_quote(row, name, symbol)
            if q is not None:
                results.append(q)

        return self.sort_and_trim(results, start_date=sd, end_date=ed, limit=limit)

    # ------------------------------------------------------------------
    # override：最新一条直接走实时接口，避免拉一批 K 线
    def get_daily_quote(
        self,
        name: str,
        date: DateLike = None,
    ) -> Optional[DailyQuote]:
        target = self.normalize_date(date)
        # 只有"取最新"时用实时接口
        if target is None:
            snap = self._fetch_realtime(name)
            if snap is not None:
                return snap
            # 降级到 K 线末尾一条
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
        symbol = self._tencent_symbol(stock.market, stock.code)
        if symbol is None:
            return None

        try:
            resp = self._session.get(
                self._RT_URL + symbol, timeout=self.DEFAULT_TIMEOUT
            )
            raw = resp.content.decode("gbk", errors="ignore")
        except Exception as e:
            print("[TencentQuoteAPI] realtime request error: %s" % e)
            return None

        m = re.search(r'"([^"]+)"', raw)
        if not m:
            return None
        fields = m.group(1).split("~")
        if len(fields) < 35:
            return None

        def f(idx: int, default: float = 0.0) -> float:
            try:
                return float(fields[idx])
            except (ValueError, IndexError):
                return default

        q = DailyQuote()
        q.source = self.SOURCE
        q.name = name
        q.code = symbol
        # 接口只给 "最新时间"（fields[30] 形如 20260422153000），取日期部分
        ts = fields[30] if len(fields) > 30 else ""
        if len(ts) >= 8 and ts[:8].isdigit():
            q.date = "%s-%s-%s" % (ts[:4], ts[4:6], ts[6:8])
        else:
            q.date = datetime.datetime.now().strftime("%Y-%m-%d")

        q.close = f(3)           # 最新价当作收盘
        q.pre_close = f(4)
        q.open = f(5)
        q.volume = f(6) * 100    # 腾讯返回单位是"手"，换算为股
        q.high = f(33)
        q.low = f(34)
        # turnover 字段为万元，转换为元
        q.turnover = f(37) * 10000 if len(fields) > 37 else 0.0
        if q.close <= 0:
            return None
        return q

    # ------------------------------------------------------------------
    @staticmethod
    def _row_to_quote(row: list, name: str, symbol: str) -> Optional[DailyQuote]:
        # 行结构：[date, open, close, high, low, volume, extra...]
        if not row or len(row) < 6:
            return None
        try:
            q = DailyQuote()
            q.source = TencentQuoteAPI.SOURCE
            q.name = name
            q.code = symbol
            q.date = str(row[0])[:10]
            q.open = float(row[1])
            q.close = float(row[2])
            q.high = float(row[3])
            q.low = float(row[4])
            q.volume = float(row[5]) * 100  # 腾讯 K 线成交量单位"手"
            # 部分行第 7 位是 dict，含 amount
            if len(row) >= 8 and isinstance(row[7], dict):
                try:
                    q.turnover = float(row[7].get("amount") or 0)
                except Exception:
                    q.turnover = 0.0
            return q
        except Exception:
            return None
