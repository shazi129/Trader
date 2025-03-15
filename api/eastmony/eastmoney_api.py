
# -*- coding: utf-8 -*-

"""
东方财富api
https://so.eastmoney.com/web/s?keyword=00700
https://push2.eastmoney.com/api/qt/stock/get?ut=6d2ffaa6a585d612eda28417681d58fb&fields=f57,f58,f59,f152,f43,f169,f170,f60,f44,f45,f168,f50,f47,f48,f49,f46,f78,f85,f86,f169,f117,f107,f111,f116,f117,f118,f163,f171,f113,f114,f115,f161,f162,f164,f168,f172,f177,f180,f181,f292,f751,f752&secid=116.00700&invt=2&_=1738833820289
https://push2his.eastmoney.com/api/qt/stock/kline/get?fields1=f1,f2,f3,f4,f5,f6,f7,f8&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65&ut=fa5fd1943c7b386f172d6893dbfba10b&secid=116.00700&dect=1&klt=101&lmt=70&fqt=1&forcect=1&end=20500000&wbp2u=1849325530509956|0|1|0|web&cb=__jp0
https://push2.eastmoney.com/api/qt/stock/trends2/get?fields1=f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13,f14,f17&fields2=f51,f52,f53,f54,f55,f58&dect=1&mpi=1000&ut=fa5fd1943c7b386f172d6893dbfba10b&secid=116.00700&ndays=1&iscr=0&iscca=0&wbp2u=1849325530509956|0|1|0|web&cb=miniquotechart_jp0
"""

import datetime
import requests
import json
from api.api_base import StockAPI
from basic.stock_types import KlineData, StockList, StockMarket

class EastMoneyAPI(StockAPI):
    def __init__(self):
        self._fields = [
            'f51', #日期
            'f52', #开盘价
            'f53', #收盘价
            'f54', #最高
            'f55', #最低
            'f56', #成交量
            'f57', #成交额
            'f58', #振幅
            'f59', #涨跌幅
            'f60', #涨跌额
            'f61'  #换手率
        ]
        self._kline_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        self._kline_param = {
            "secid": '101.SI00Y', #股票代码, 0深股 1沪股
            "beg": "20230101",  #开始时间
            "end": "20240101",  #结束时间
            "klt":101,    # k线周期，1：1分钟，5：5分钟， 101：日，102：周
            "fqt":1,        #复权方式，0: 不复权，1：前复权，2：后复权
            "fields1" : 'f1,f2,f3,f4,f5',
            "fields2": ','.join(self._fields),
            "lmt":58,
            "ut": "fa5fd1943c7b386f172d6893dbfba10b"
        }

    def get_secid(self, name:str)-> str:
        stock = StockList[name]
        match stock.market:
            case StockMarket.SH:
                return "0.%s" % stock.code
            case StockMarket.SZ:
                return "1.%s" % stock.code
            case StockMarket.COMEX:
                return "101.%s" % stock.code
            case StockMarket.HK:
                return "116.%s" % stock.code
        return None

    def get_day_klines(self, name: str, start: datetime.datetime, end:datetime.datetime) -> list[KlineData]:
        #获取secid
        secid = self.get_secid(name)
        if secid == None:
            print("eastmony api cannot get secid by " + name)
            return []

        self._kline_param["secid"] = secid
        self._kline_param["beg"] = start.strftime("%Y%m%d")
        self._kline_param["end"] = end.strftime("%Y%m%d")

        #拼接get参数
        get_param_str = ""
        for k, v in self._kline_param.items():
            if get_param_str == "":
                get_param_str += "%s=%s" % (k, v)
            else:
                get_param_str += "&%s=%s" % (k, v)

        #拼接请求url
        request =  "%s?%s" % (self._kline_url, get_param_str)

        #http请求
        response = requests.get(request).text
        response = json.loads(response)

        result:list[KlineData] = []
        if response["data"] == None or response["data"]["klines"] == None:
            print("response is null!!!!!")
            return result

        for str_kline in response["data"]["klines"]:
            fields = str_kline.split(",")
            if (len(fields) < len(self._fields)):
                print("invalid %s kline info: %s" % (name, str_kline))
                continue
            kline_data = KlineData()
            kline_data.date = fields[0]
            kline_data.open = float(fields[1])
            kline_data.close = float(fields[2])
            kline_data.high = float(fields[3])
            kline_data.low = float(fields[4])
            kline_data.volume = float(fields[5])
            kline_data.turnover = float(fields[6])
            kline_data.turnover_rate = float(fields[10])
            result.append(kline_data)
        
        return result
