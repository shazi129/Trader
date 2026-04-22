# -*- coding: utf-8 -*-
"""东方财富：K 线 / 单日行情实现

接口：https://push2his.eastmoney.com/api/qt/stock/kline/get
"""

from __future__ import annotations

import json
from typing import Optional

import requests

import config
from stock_info import StockMarket
from quote_api.quote_base import DailyQuote, QuoteAPI, DateLike


class EastMoneyQuoteAPI(QuoteAPI):
    SOURCE = "eastmoney"

    _KLINE_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"

    # f51~f61：日期、开、收、高、低、成交量、成交额、振幅、涨跌幅、涨跌额、换手率
    _FIELDS = "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"

    _DEFAULT_BEG = "19900101"
    _DEFAULT_END = "20500101"

    def __init__(self) -> None:
        super().__init__()

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
            resp = requests.get(
                self._KLINE_URL, params=params, timeout=self.DEFAULT_TIMEOUT
            )
            payload = json.loads(resp.text)
        except Exception as e:
            print("[EastMoneyQuoteAPI] request error: %s" % e)
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
    # override：单日直接用 beg=end，比走全量再过滤更高效
    def get_daily_quote(
        self,
        name: str,
        date: DateLike = None,
    ) -> Optional[DailyQuote]:
        target = self.normalize_date(date)
        if target is None:
            items = self.get_klines(name, limit=1)
            return items[-1] if items else None
        items = self.get_klines(name, start_date=target, end_date=target, limit=1)
        if not items:
            return None
        for q in items:
            if q.date == target:
                return q
        return items[-1]
