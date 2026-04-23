# -*- coding: utf-8 -*-
"""东方财富：K 线 / 单日行情实现

接口：
- 实时快照：https://push2.eastmoney.com/api/qt/stock/get
    返回 JSON，字段值均为整数（价格 * 1000，涨跌幅 * 100 等），需除以对应因子还原。
    f43=最新价, f44=最高, f45=最低, f46=今开, f47=成交量(手), f48=成交额(元),
    f60=昨收, f170=涨跌幅(*100), f171=涨跌额(*1000)

- 历史 K 线：https://push2his.eastmoney.com/api/qt/stock/kline/get
    ⚠ 该域名近期频繁被反爬拦截（服务端直接断连），仅作为降级通道保留。
"""

from __future__ import annotations

import datetime
import json
from typing import Optional

import requests

import config
from stock_info import StockMarket
from quote_api.quote_base import DailyQuote, QuoteAPI, DateLike


class EastMoneyQuoteAPI(QuoteAPI):
    SOURCE = "eastmoney"

    _RT_URL = "https://push2.eastmoney.com/api/qt/stock/get"
    _KLINE_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"

    # f51~f61：日期、开、收、高、低、成交量、成交额、振幅、涨跌幅、涨跌额、换手率
    _FIELDS = "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"

    _DEFAULT_BEG = "19900101"
    _DEFAULT_END = "20500101"

    _HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Referer": "https://quote.eastmoney.com/",
    }

    def __init__(self) -> None:
        super().__init__()
        self._session = requests.Session()
        self._session.headers.update(self._HEADERS)

    # ------------------------------------------------------------------
    def _get_secid(self, name: str) -> Optional[str]:
        stock = config.global_stock_list.get(name)
        if stock is None:
            return None
        match stock.market:
            case StockMarket.SH:
                return "1.%s" % stock.code
            case StockMarket.SZ:
                return "0.%s" % stock.code
            case StockMarket.HK:
                return "116.%s" % stock.code
            case StockMarket.COMEX:
                return "101.%s" % stock.code
        return None

    # ------------------------------------------------------------------
    def get_klines(
        self,
        name: str,
        start_date: DateLike = None,
        end_date: DateLike = None,
        limit: Optional[int] = None,
    ) -> list[DailyQuote]:
        secid = self._get_secid(name)
        if secid is None:
            print("[EastMoneyQuoteAPI] cannot resolve secid: %s" % name)
            return []

        sd = self.normalize_date(start_date)
        ed = self.normalize_date(end_date)
        beg = sd.replace("-", "") if sd else self._DEFAULT_BEG
        end = ed.replace("-", "") if ed else self._DEFAULT_END
        # 东方财富接口 lmt 是最大返回条数；从末尾向前截取
        lmt = limit if (limit is not None and limit > 0) else 100000

        params = {
            "secid": secid,
            "fields1": "f1,f2,f3,f4,f5",
            "fields2": self._FIELDS,
            "klt": 101,    # 日线
            "fqt": 1,      # 前复权
            "beg": beg,
            "end": end,
            "lmt": lmt,
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
        }

        try:
            resp = self._session.get(
                self._KLINE_URL, params=params, timeout=self.DEFAULT_TIMEOUT
            )
            payload = json.loads(resp.text)
        except Exception as e:
            print("[EastMoneyQuoteAPI] kline request error: %s" % e)
            return []

        data = payload.get("data") if isinstance(payload, dict) else None
        if not data:
            return []
        klines = data.get("klines") or []
        if not klines:
            return []

        code = str(data.get("code", ""))
        results: list[DailyQuote] = []
        for line in klines:
            fields = line.split(",")
            if len(fields) < 7:
                continue
            try:
                q = DailyQuote()
                q.source = self.SOURCE
                q.name = name
                q.code = code
                q.date = fields[0]
                q.open = float(fields[1])
                q.close = float(fields[2])
                q.high = float(fields[3])
                q.low = float(fields[4])
                q.volume = float(fields[5])
                q.turnover = float(fields[6])
                results.append(q)
            except Exception:
                continue

        # 接口返回已按升序，这里再用 sort_and_trim 做一层保险
        return self.sort_and_trim(results, start_date=sd, end_date=ed, limit=limit)

    # ------------------------------------------------------------------
    # override：优先走 push2 实时接口；降级到 K 线
    def get_daily_quote(
        self,
        name: str,
        date: DateLike = None,
    ) -> Optional[DailyQuote]:
        target = self.normalize_date(date)
        # 只有 "取最新" 时走实时接口
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
        """通过 push2.eastmoney.com 实时快照接口获取最新行情。

        返回的字段值均为整数（价格 × 1000，涨跌幅 × 100 等），需除以对应因子。
        """
        secid = self._get_secid(name)
        if secid is None:
            return None

        # 请求字段说明：
        # f43=最新价 f44=最高 f45=最低 f46=今开 f47=成交量(手) f48=成交额(元)
        # f57=股票代码 f58=股票名称 f60=昨收 f116=总市值 f117=流通市值
        # f170=涨跌幅 f171=涨跌额
        params = {
            "secid": secid,
            "fields": "f43,f44,f45,f46,f47,f48,f57,f58,f60,f170",
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
        }

        try:
            resp = self._session.get(
                self._RT_URL, params=params, timeout=self.DEFAULT_TIMEOUT
            )
            payload = json.loads(resp.text)
        except Exception as e:
            print("[EastMoneyQuoteAPI] realtime request error: %s" % e)
            return None

        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            return None

        def _v(key: str, divisor: float = 1000.0) -> float:
            """取字段值并除以因子，返回浮点；字段缺失或为 '-' 返回 0.0"""
            raw = data.get(key)
            if raw is None or raw == "-":
                return 0.0
            try:
                return float(raw) / divisor
            except (ValueError, TypeError):
                return 0.0

        close = _v("f43")            # 最新价 / 1000
        if close <= 0:
            return None

        q = DailyQuote()
        q.source = self.SOURCE
        q.name = name
        q.code = str(data.get("f57", ""))
        q.date = datetime.datetime.now().strftime("%Y-%m-%d")
        q.close = close
        q.open = _v("f46")           # 今开 / 1000
        q.high = _v("f44")           # 最高 / 1000
        q.low = _v("f45")            # 最低 / 1000
        q.pre_close = _v("f60")      # 昨收 / 1000
        q.volume = _v("f47", 1.0)    # 成交量（手），不需要除因子
        q.turnover = _v("f48", 1.0)  # 成交额（元），不需要除因子
        return q
