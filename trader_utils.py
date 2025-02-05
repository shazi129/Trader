# -*- coding: utf-8 -*-
#!/usr/bin/env python

from datetime import datetime, timedelta
from api.api_base import KlineData, StockCode
from config import STOCK_API_CLASS
from database import stock_db_utils


def get_day_klines(code: StockCode, start: str, end: str) -> list[KlineData]:
    """获取一个股票的日k线"""
    api = STOCK_API_CLASS()
    return api.get_day_klines(code, start, end)

def get_date_span(latest_date, span):
    """获取一个时间段内的时间"""
    latest_date_object = datetime.strptime(latest_date, "%Y-%m-%d")
    begin_date = latest_date_object + timedelta(days=1)
    end_date = latest_date_object + timedelta(days=101)
    return begin_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

def update_stock_db(code: StockCode):
    """更新一个k线数据库"""
    stock_db = stock_db_utils.StockDB()
    stock_db.create_stock_table(code)

    #拿到开始时间与结束时间
    begin_date = stock_db.get_lastest_date(code)
    if (begin_date == None):
        begin_date = "1990-01-01"
    begin_date = datetime.strptime(begin_date, "%Y-%m-%d")

    #结束时间为昨天
    yesdoday = datetime.now() - timedelta(days=1)

    while(begin_date < yesdoday):
        delta_day = (yesdoday - begin_date).days
        end_date = yesdoday
        if delta_day > 200:
            end_date = begin_date + timedelta(days=200)

        #拉数据并写入数据库
        klines = get_day_klines(code, begin_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d"))
        for kline in klines:
            stock_db.write_raw_data(code, kline)

        begin_date = end_date + timedelta(days=1)

def get_yestoday()->str:
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

if __name__ == "__main__":
    #print("\n".join([str(item) for item in get_day_klines(StockCode.COMEX_AG, "20250124", "20250204")]))
    update_stock_db(StockCode.TX)
    #stock_db = stock_db_utils.StockDB()
    #print (stock_db.get_lastest_date(StockCode.AG))
    #print(get_date_span("1990-01-01", 100))
    #print((datetime.strptime("2025-02-04", "%Y-%m-%d") < datetime.strptime("2025-02-05", "%Y-%m-%d")))