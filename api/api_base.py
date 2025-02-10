# -*- coding: utf-8 -*-
#!/usr/bin/env python

import datetime
from enum import Enum

class StockMarket(Enum):
    NONE        = 0
    SH          = 1     #上证
    SZ          = 2     #深证
    HK          = 3     #港证
    COMEX       = 4     #纽约商品交易所

class StockInfo:
    def __init__(self, code:str, market: StockMarket, listing_date:str) -> None:
        self.code:str = code #股票代码
        self.market: StockMarket = market #所属市场
        self.listing_date:str = listing_date #上市日期

    def get_list_date(self)->datetime.datetime:
        return datetime.datetime.strptime(self.listing_date, "%Y-%m-%d")

StockList: dict[str, StockInfo] = {
    "Tencent": StockInfo('00700',  StockMarket.HK, "2004-06-16"),
    "Alibaba": StockInfo('09988', StockMarket.HK, "2019-11-26"),
    "COMEX_AG": StockInfo('SI00Y', StockMarket.COMEX, "2011-07-22")
}

class KlineData:
    def __init__(self):
        self.date:str = ""         #日期, 格式: 2025-02-04
        self.open:float = 0      #开盘价
        self.close:float = 0       #收盘价
        self.high:float = 0         #最高价
        self.low:float = 0          #最低价
        self.volume:float = 0       #成交量
        self.turnover:float = 0     #成交额
        self.turnover_rate:float = 0    #换手率
        self.pe:float = 0 #市盈率

    def FIELD_NUM():
        return 9
    
    def parse(self, v: tuple)->bool:
        if len(v) != 9 or not isinstance(v, tuple):
            print("KlineData parse error, invalud v:%s" % str(v))
            return False
        self.date = str(v[0])
        self.open = float(v[1])
        self.close = float(v[2])
        self.high = float(v[3])
        self.low = float(v[4])
        self.volume = float(v[5])
        self.turnover = float(v[6])
        self.turnover_rate = float(v[7])
        self.pe = float(v[8])
        return True

    def __str__(self) -> str:
        return "date:%s, open:%f, close:%f, high:%f, low:%f, volume:%f, turnover:%f, turnover_rate:%f, pe:%f" % (
            self.date, self.open, self.close, self.high, self.low, self.volume, self.turnover, self.turnover_rate, self.pe
        )
    
class KlineIndicator:
    def __init__(self) -> None:
        self.date:str = ""         #日期, 格式: 2025-02-04

        #均线
        self.ma5:float =     0
        self.ma10:float =     0
        self.ma20:float =     0
        self.ma30:float =     0
        self.ma60:float =     0
        self.ma120:float =     0
        self.ma250:float =     0

        #布林带, 中线是20均线
        self.boll_up:float = 0
        self.boll_low:float = 0

        #KDJ
        self.k = 0
        self.d = 0
        self.j = 0

        #MACD
        self.dif = 0
        self.dea = 0
        self.macd = 0

        #RSI
        self.rsi1 = 0
        self.rsi2 = 0
        self.rsi3 = 0

        #ADOSC
        self.adosc = 0


class StockAPI:
    """所有API的基类"""
    def __init__(self):
        pass

    def get_day_klines(self, name: str, start: datetime.datetime, end:datetime.datetime)->list[KlineData]:
        """
        获取一段时间内的日k线
        code: 股票代码
        start: 开始日期，格式: 20250204
        end: 结束日期, 格式与start相同

        return: KlineData列表
        """
        pass
