# -*- coding: utf-8 -*-
#!/usr/bin/env python

from datetime import datetime, timedelta
from API import APIBase
from StockInfo import KlineIndicator, StockInfo
import Config
from Database import StockDBUtils
import talib as tb
import numpy as np

def get_day_klines(name: str, start: datetime, end: datetime) -> list[APIBase.KlineData]:
    """获取一个股票的日k线"""
    stock_api = Config.STOCK_API_CLASS()
    return stock_api.get_day_klines(name, start, end)

def get_date_span(latest_date, span):
    """获取一个时间段内的时间"""
    latest_date_object = datetime.strptime(latest_date, "%Y-%m-%d")
    begin_date = latest_date_object + timedelta(days=1)
    end_date = latest_date_object + timedelta(days=101)
    return begin_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

def update_stock_klines(name: str)->int:
    """更新一个k线数据库"""

    stock_info = Config.global_stock_list[name]
    if stock_info == None:
        print("update_stock_klines error, invalid name: %s" % name)
        return 0

    stock_db = StockDBUtils.StockDB()
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

def update_socket_indicator(name: str)->int:
    stock_info = Config.global_stock_list[name]
    if stock_info == None:
        print("update_stock_db error, invalid name: %s" % name)
        return 0
    
    stock_db = StockDBUtils.StockDB()
    stock_db.create_indicator_table(name)

    kline_size, indicator_size = stock_db.get_stock_rows(name)

    #需要更新的指标条数
    update_size = kline_size - indicator_size
    read_size = update_size + 250  #最多250条k线可以把所有指标计算完
    klines = stock_db.get_latest_klines(name, read_size)

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
    sma5_list = tb.MA(close_np_array, 5)[-update_size:]
    sma10_list = tb.MA(close_np_array, 10)[-update_size:]
    sma20_list = tb.MA(close_np_array, 20)[-update_size:]
    sma30_list = tb.MA(close_np_array, 30)[-update_size:]
    sma60_list = tb.MA(close_np_array, 60)[-update_size:]
    sma120_list = tb.MA(close_np_array, 120)[-update_size:]
    sma250_list = tb.MA(close_np_array, 250)[-update_size:]

    #BOLL
    boll = tb.BBANDS(close_np_array, timeperiod=20)[-update_size:]
    upper, middle, lower = boll

    #KDJ, 计算方式https://xueqiu.com/1747761477/198676825
    k, d = tb.STOCH(np.array(kline_high), np.array(kline_low), close_np_array,
                     fastk_period=9, slowk_period=(3*2-1), slowk_matype=1, slowd_period=(3*2-1), slowd_matype=1)[-update_size:]
    j = np.subtract(np.multiply(k, 3), np.multiply(d, 2))

    #MACD
    dif, dea, macd = tb.MACD(close_np_array)[-update_size:]

    #RSI
    rsi1 = tb.RSI(close_np_array, 6)[-update_size:]
    rsi2 = tb.RSI(close_np_array, 12)[-update_size:]
    rsi3 = tb.RSI(close_np_array, 24)[-update_size:]

    #ADOSC
    adosc = tb.ADOSC(np.array(kline_high), np.array(kline_low), close_np_array, np.array(kline_volume))[-update_size:]

    #日期，升序
    kline_dates = [kline.date for kline in klines][-update_size:]
    kline_dates.reverse()

    for i in range(len(kline_dates)):
        indicator = KlineIndicator()
        indicator.date = kline_dates[i]
        indicator.ma5 = 0 if np.isnan(sma5_list[i]) else round(sma5_list[i], 2)
        indicator.ma10 = 0 if np.isnan(sma10_list[i]) else round(sma10_list[i], 2)
        indicator.ma20 = 0 if np.isnan(sma20_list[i]) else round(sma20_list[i], 2)
        indicator.ma30 = 0 if np.isnan(sma30_list[i]) else round(sma30_list[i], 2)
        indicator.ma60 = 0 if np.isnan(sma60_list[i]) else round(sma60_list[i], 2)
        indicator.ma120 = 0 if np.isnan(sma120_list[i]) else round(sma120_list[i], 2)
        indicator.ma250 = 0 if np.isnan(sma250_list[i]) else round(sma250_list[i], 2)

        indicator.boll_low = 0 if np.isnan(lower[i]) else round(lower[i], 2)
        indicator.boll_up = 0 if np.isnan(upper[i]) else round(upper[i], 2)

        indicator.k = 0 if np.isnan(k[i]) else round(k[i], 2)
        indicator.d = 0 if np.isnan(d[i]) else round(d[i], 2)
        indicator.j = 0 if np.isnan(j[i]) else round(j[i], 2)

        indicator.dif = 0 if np.isnan(dif[i]) else round(dif[i], 2)
        indicator.dea = 0 if np.isnan(dea[i]) else round(dea[i], 2)
        indicator.macd = 0 if np.isnan(macd[i]) else round(macd[i] * 2, 2)

        indicator.rsi1 = 0 if np.isnan(rsi1[i]) else round(rsi1[i], 2)
        indicator.rsi2 = 0 if np.isnan(rsi2[i]) else round(rsi2[i], 2)
        indicator.rsi3 = 0 if np.isnan(rsi3[i]) else round(rsi3[i], 2)

        indicator.adosc = 0 if np.isnan(adosc[i]) else round(adosc[i], 2)

        stock_db.write_raw_data(stock_db.get_indicator_table_name(name), stock_db.parse_indicator(indicator))

    #写入数据表
def get_yestoday()->str:
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

def update_stocket(stock_key:str):
    if (stock_key not in Config.global_stock_list):
        print("update_stocket error, cannot stock info by name: %s" % stock_key)
        return 0
    
    #更新股票数据
    update_stock_klines(stock_key)

    #衍生品不需要参数
    if (not Config.global_stock_list[stock_key].is_derivative):
        update_socket_indicator(stock_key)

def update_all_stocks():
    for stock_key in Config.global_stock_list:
        update_stocket(stock_key)

def get_ratio_data(denominator_key:str, numerator_key:str):
    stock_db = StockDBUtils.StockDB()
    result = stock_db.get_stock_ratio_data(denominator_key, numerator_key)
    for item in result:
        print(item)

