# -*- coding: utf-8 -*-
#!/usr/bin/env python

from datetime import datetime, timedelta
from api import api_base
from config import STOCK_API_CLASS
from database import stock_db_utils
import talib as tb
import numpy as np

def get_day_klines(name: str, start: datetime, end: datetime) -> list[api_base.KlineData]:
    """获取一个股票的日k线"""
    stock_api = STOCK_API_CLASS()
    return stock_api.get_day_klines(name, start, end)

def get_date_span(latest_date, span):
    """获取一个时间段内的时间"""
    latest_date_object = datetime.strptime(latest_date, "%Y-%m-%d")
    begin_date = latest_date_object + timedelta(days=1)
    end_date = latest_date_object + timedelta(days=101)
    return begin_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

def update_stock_klines(name: str)->int:
    """更新一个k线数据库"""

    stock_info = api_base.StockList[name]
    if stock_info == None:
        print("update_stock_db error, invalid name: %s" % name)
        return 0

    stock_db = stock_db_utils.StockDB()
    stock_db.create_stock_table(name)

    #拿到开始时间与结束时间
    begin_date = stock_db.get_latest_date(name)
    if (begin_date == None):
        begin_date = "1990-01-01"
    begin_date = datetime.strptime(begin_date, "%Y-%m-%d") + timedelta(days=1)
    listing_date = stock_info.get_list_date() #开始时间要从上市日期算
    if begin_date < listing_date:
        begin_date = listing_date

    #结束时间为昨天
    yesdoday = datetime.now() - timedelta(days=1)

    count:int = 0
    while((yesdoday - begin_date).days >= 0):
        delta_day = (yesdoday - begin_date).days
        end_date = yesdoday
        if delta_day > 200:
            end_date = begin_date + timedelta(days=200)

        #拉数据并写入数据库
        klines = get_day_klines(name, begin_date, end_date)
        count += len(klines)
        for kline in klines:
            stock_db.write_raw_data(name, kline)

        begin_date = end_date + timedelta(days=1)


def update_all_klines():
    for stock_name in api_base.StockList:
        update_stock_klines(stock_name)

def update_socket_indicator(name: str)->int:
    stock_info = api_base.StockList[name]
    if stock_info == None:
        print("update_stock_db error, invalid name: %s" % name)
        return 0
    
    stock_db = stock_db_utils.StockDB()
    table_size = stock_db.get_stock_rows(name)
    read_size = table_size[0] - table_size[1] + 250
    klines = stock_db.get_latest_klines(name, read_size)

    kline_dates = [kline.date for kline in klines]
    kline_dates.reverse()

    kline_closes = [kline.close for kline in klines]
    kline_closes.reverse()

    sma5_list = tb.SMA(np.array(kline_closes), 5)
    sma10_list = tb.SMA(np.array(kline_closes), 10)
    sma20_list = tb.SMA(np.array(kline_closes), 20)
    sma30_list = tb.SMA(np.array(kline_closes), 30)
    sma60_list = tb.SMA(np.array(kline_closes), 60)
    sma120_list = tb.SMA(np.array(kline_closes), 120)
    sma250_list = tb.SMA(np.array(kline_closes), 250)


    print([(date, round(float(sma5), 2),
                  round(float(sma10), 2),
                  round(float(sma20), 2),
                  round(float(sma30), 2),
                  round(float(sma60), 2),
                  round(float(sma120), 2),
                  round(float(sma250), 2),)
         for date, sma5, sma10, sma20, sma30, sma60, sma120, sma250
         in zip(kline_dates, sma5_list, sma10_list, sma20_list, sma30_list, sma60_list, sma120_list, sma250_list)][-5:])

    #写入数据表
def get_yestoday()->str:
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
