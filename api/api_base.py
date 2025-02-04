# -*- coding: utf-8 -*-
#!/usr/bin/env python

from enum import Enum
from dataclasses import dataclass

#股票代码枚举，统一对外接口
class StockCode(Enum):
    AG      = 1          #白银
    AU      = 2          #黄金
    TX      = 3          #腾讯
    ALI     = 4          #阿里港股

class KlineData:
    def __init__(self):
        self.date:str = ""         #日期
        self.open:float = 0      #开盘价
        self.close:float = 0       #收盘价
        self.high:float = 0         #最高价
        self.low:float = 0          #最低价
        self.volume:float = 0       #成交量
        self.turnover:float = 0     #成交额
        self.turnover_rate:float = 0    #换手率

    def __str__(self) -> str:
        return "date:%s, open:%f, close:%f, high:%f, low:%f, volume:%f, turnover:%f, turnover_rate:%f" % (
            self.date, self.open, self.close, self.high, self.low, self.volume, self.turnover, self.turnover_rate
        )

class StockAPI:
    def __init__(self):
        pass

    def get_day_klines(self, code: StockCode, start: str, end:str)->list[KlineData]:
        """
        获取一段时间内的日k线
        code: 股票代码
        start: 开始日期，格式: 20250204
        end: 结束日期, 格式与start相同

        return: KlineData列表
        """
        pass

    def get_real_stock_code(self, code: StockCode)->str:
        match code:
            case StockCode.TX:
                return "00700"
            case StockCode.ALI:
                return "09988"
        return ""
