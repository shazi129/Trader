# -*- coding: utf-8 -*-
#!/usr/bin/env python

from enum import Enum
from api.eastmony.eastmoney_api import EastMoneyAPI
from stock_info import StockInfo, StockMarket

STOCK_API_CLASS = EastMoneyAPI

#当前用到的股票信息配置
global_stock_list: dict[str, StockInfo] = {
    "Tencent": StockInfo('腾讯', '00700',  StockMarket.HK, "2004-06-16"),
    "Tencent_14136": StockInfo('腾讯法兴六乙沽', '14136',  StockMarket.HK, "2025-02-25", True),
    "Tencent_14210": StockInfo('腾讯花旗六乙沽', '14210',  StockMarket.HK, "2025-02-26", True),
    "Tencent_27124": StockInfo('腾讯瑞银五乙沽', '27124',  StockMarket.HK, "2024-09-03", True),

    "Alibaba": StockInfo('阿里-港', '09988', StockMarket.HK, "2019-11-26"),
    "COMEX_AG": StockInfo('Comex白银', 'SI00Y', StockMarket.COMEX, "2011-07-22"),
}

def create_show_data():
    return {"date": [], "values": {}}

#全局事件id
class EventID(Enum):
    NONE        = 0

    """
    展示数据，数据格式：
    {
        "date": ["2012-01-01", "2012-01-02", ...],
        "values": {
            "ratio": [0.1, 0.2, ...],
            "value1": [0.1, 0.2, ...],
        },
    }
    """
    SHOW_DATA          = 1 