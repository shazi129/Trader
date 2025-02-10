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
        print("update_stock_klines error, invalid name: %s" % name)
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
            stock_db.write_raw_data(name, stock_db.parse_kline(kline))

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

    #需要更新的指标条数
    update_size = table_size[0] - table_size[1]
    read_size = update_size + 250  #最多250条k线可以把所有指标计算完
    klines = stock_db.get_latest_klines(name, read_size)

    #日期，升序
    kline_dates = [kline.date for kline in klines]
    kline_dates.reverse()

    #收盘价
    kline_closes = [kline.close for kline in klines]
    kline_closes.reverse()

    kline_open = [kline.open for kline in klines]
    kline_open.reverse()

    kline_high = [kline.high for kline in klines]
    kline_high.reverse()

    kline_low = [kline.low for kline in klines]
    kline_low.reverse()

    kline_volume = [kline.volume for kline in klines]
    kline_volume.reverse()

    #MA
    close_np_array = np.array(kline_closes)
    sma5_list = tb.SMA(close_np_array, 5)[-update_size:]
    sma10_list = tb.SMA(close_np_array, 10)[-update_size:]
    sma20_list = tb.SMA(close_np_array, 20)[-update_size:]
    sma30_list = tb.SMA(close_np_array, 30)[-update_size:]
    sma60_list = tb.SMA(close_np_array, 60)[-update_size:]
    sma120_list = tb.SMA(close_np_array, 120)[-update_size:]
    sma250_list = tb.SMA(close_np_array, 250)[-update_size:]

    upper, middle, lower = tb.BBANDS(close_np_array)[-update_size:]
    dif, dea, macd = tb.MACD(close_np_array)[-update_size:]

    rsi1 = tb.RSI(close_np_array, 6)[-update_size:]
    rsi2 = tb.RSI(close_np_array, 12)[-update_size:]
    rsi3 = tb.RSI(close_np_array, 24)[-update_size:]

    adosc = tb.ADOSC(np.array(kline_high), np.array(kline_low), close_np_array, np.array(kline_volume))[-update_size:]

    print(range(-update_size))
    for i in range(len(kline_dates)):
        indicator = api_base.KlineIndicator()
        indicator.date = kline_dates

    #写入数据表
def get_yestoday()->str:
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
