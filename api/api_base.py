# -*- coding: utf-8 -*-
#!/usr/bin/env python

import datetime
from StockInfo import KlineData

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
