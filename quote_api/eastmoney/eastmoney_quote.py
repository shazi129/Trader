# -*- coding: utf-8 -*-
"""东方财富：K 线 / 单日行情 / 基本面数据实现


东方财富api
https://so.eastmoney.com/web/s?keyword=00700
https://push2.eastmoney.com/api/qt/stock/get?ut=6d2ffaa6a585d612eda28417681d58fb&fields=f57,f58,f59,f152,f43,f169,f170,f60,f44,f45,f168,f50,f47,f48,f49,f46,f78,f85,f86,f169,f117,f107,f111,f116,f117,f118,f163,f171,f113,f114,f115,f161,f162,f164,f168,f172,f177,f180,f181,f292,f751,f752&secid=116.00700&invt=2&_=1738833820289
https://push2his.eastmoney.com/api/qt/stock/kline/get?fields1=f1,f2,f3,f4,f5,f6,f7,f8&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65&ut=fa5fd1943c7b386f172d6893dbfba10b&secid=116.00700&dect=1&klt=101&lmt=70&fqt=1&forcect=1&end=20500000&wbp2u=1849325530509956|0|1|0|web&cb=__jp0
https://push2.eastmoney.com/api/qt/stock/trends2/get?fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13,f14,f17&fields2=f51,f52,f53,f54,f55,f58&dect=1&mpi=1000&ut=fa5fd1943c7b386f172d6893dbfba10b&secid=116.00700&ndays=1&iscr=0&iscca=0&wbp2u=1849325530509956|0|1|0|web&cb=miniquotechart_jp0


接口：
- 实时快照：https://push2.eastmoney.com/api/qt/stock/get
    返回 JSON，字段值均为整数（价格 * 1000，涨跌幅 * 100 等），需除以对应因子还原。
    f43=最新价, f44=最高, f45=最低, f46=今开, f47=成交量(手), f48=成交额(元),
    f60=昨收, f170=涨跌幅(*100), f171=涨跌额(*1000)

- 基本面数据：同一接口，通过 fields 参数获取 PE、PB、市值等
    f9=PE动态, f23=PB, f116=总市值, f117=流通市值

- 历史 K 线：https://push2his.eastmoney.com/api/qt/stock/kline/get
    ⚠ 该域名近期频繁被反爬拦截（服务端直接断连），仅作为降级通道保留。
"""

from __future__ import annotations

import datetime
import json
from typing import Optional

import requests

from quote_api.stock_meta import StockMarket
from quote_api.quote_base import DailyQuote, QuoteAPI, DateLike, StockFundamental
from quote_api.stock_meta import get_meta


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
        stock = get_meta(name)
        code = self.get_stock_code(name)
        if stock is None or code is None:
            return None
        match stock.market:
            case StockMarket.SH:
                return "1.%s" % code
            case StockMarket.SZ:
                return "0.%s" % code
            case StockMarket.HK:
                return "116.%s" % code
            case StockMarket.COMEX:
                return "101.%s" % code
            case StockMarket.NASDAQ:
                return "105.%s" % code
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
                # fields 顺序: 日期,开,收,高,低,成交量,成交额,振幅,涨跌幅,涨跌额,换手率
                # 换手率 fields[10]，单位 %（与东财页面展示一致）
                if len(fields) > 10:
                    try:
                        q.turnover_rate = float(fields[10])
                    except (ValueError, TypeError):
                        q.turnover_rate = 0.0
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

    # ------------------------------------------------------------------
    def get_fundamentals(self, name: str) -> Optional[StockFundamental]:
        """获取股票基本面数据（东方财富实现）
        
        使用 push2.eastmoney.com/api/qt/stock/get 接口获取估值数据
        字段：f9=PE动态 f23=PB f116=总市值 f117=流通市值
        """
        secid = self._get_secid(name)
        if secid is None:
            return None
        
        try:
            fund = StockFundamental()
            fund.name = name
            fund.code = secid
            fund.source = self.SOURCE
            
            # 1. 获取基本估值数据
            params = {
                "secid": secid,
                "fields": "f9,f23,f116,f117",
                "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            }
            
            resp = self._session.get(self._RT_URL, params=params, timeout=self.DEFAULT_TIMEOUT)
            payload = json.loads(resp.text)
            data = payload.get("data") if isinstance(payload, dict) else None
            
            if data:
                # PE动态（市盈率）f162=PE×100
                pe_raw = data.get("f162")
                if pe_raw is not None and pe_raw != "-":
                    try:
                        fund.pe_ttm = float(pe_raw) / 100.0  # API返回PE×100
                    except (ValueError, TypeError):
                        pass
                
                # PB（市净率）f163=PB×100
                pb_raw = data.get("f163")
                if pb_raw is not None and pb_raw != "-":
                    try:
                        fund.pb = float(pb_raw) / 100.0  # API返回PB×100
                    except (ValueError, TypeError):
                        pass
                
                # 总市值（元）f116
                mcap_raw = data.get("f116")
                if mcap_raw is not None and mcap_raw != "-":
                    try:
                        fund.market_cap = float(mcap_raw)
                    except (ValueError, TypeError):
                        pass
                
                # 流通市值（元）f117
                circ_mcap_raw = data.get("f117")
                if circ_mcap_raw is not None and circ_mcap_raw != "-":
                    try:
                        fund.circulating_market_cap = float(circ_mcap_raw)
                    except (ValueError, TypeError):
                        pass
            
            # 2. 尝试获取财务数据（ROE、营收等）
            # 使用东方财富的财务摘要接口
            try:
                # 通过股票代码获取财务数据
                code = self.get_stock_code(name)
                if code:
                    # 构造请求获取财务摘要
                    fin_params = {
                        "type": "0",  # 0=按年度
                        "code": code,
                    }
                    # 注意：这个接口可能需要不同的URL，这里先留作扩展
                    # 可以后续添加 ak.stock_financial_abstract_ths 的直连版本
            except Exception:
                pass
            
            fund.date = datetime.datetime.now().strftime("%Y-%m-%d")
            
            # 只要有一部分数据就返回，不要求全部有效
            if fund.pe_ttm > 0 or fund.pb > 0 or fund.market_cap > 0:
                return fund
            return None
            
        except Exception as e:
            print("[EastMoneyQuoteAPI] get_fundamentals error: %s" % e)
            return None
