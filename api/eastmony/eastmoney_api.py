
# -*- coding: utf-8 -*-

"""
东方财富api
"""

import requests
import json
from api.api_base import KlineData, StockAPI, StockCode

class EastMoneyAPI(StockAPI):
    def __init__(self):
        self._kline_url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
        self._kline_param = {
            "secid": '122.XAG', #股票代码
            "beg": "20230101",  #开始时间
            "end": "20240101",  #结束时间
            "klt":101,    # k线周期，1：1分钟，5：5分钟， 101：日，102：周
            "fqt":1,        #复权方式，0: 不复权，1：前复权，2：后复权
            "fields1" : 'f1,f2,f3,f4,f5',
            "fields2": 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61', #f51-f61: 日期，开盘价，收盘价，最高，最低，成交量，成交额，振幅，涨跌幅，涨跌额，换手率
            "lmt":58,
            "ut": "fa5fd1943c7b386f172d6893dbfba10b"
        }

    def get_day_klines(self, code: StockCode, start: str, end: str) -> list[KlineData]:
        self._kline_param["secid"] = self.get_real_stock_code(code)
        self._kline_param["beg"] = start
        self._kline_param["end"] = end

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
            if (len(fields) < 5):
                print("invalid kline info:" + str_kline)
                continue
            kline_data = KlineData()
            kline_data.date = fields[0]
            kline_data.open = float(fields[1])
            kline_data.close = float(fields[2])
            kline_data.high = float(fields[3])
            kline_data.low = float(fields[4])
            result.append(kline_data)
        
        return result

    
    def get_real_stock_code(self, code: StockCode) -> str:
        match code:
            case StockCode.AG:
                return '122.XAG'
        return super().get_real_stock_code(code)
