# -*- coding: utf-8 -*-
#!/usr/bin/env python

from api.api_base import KlineData, StockCode
from config import STOCK_API_CLASS
from database import stock_db_utils


def get_day_klines(code: StockCode, start: str, end: str) -> list[KlineData]:
    """获取一个股票的日k线"""
    api = STOCK_API_CLASS()
    return api.get_day_klines(code, start, end)


def update_stock_db(code: StockCode):
    """更新一个k线数据库"""
    stock_db = stock_db_utils.StockDB()
    stock_db.create_stock_table(code)
    klines = get_day_klines(StockCode.AG, "20250124", "20250204")
    for kline in klines:
        stock_db.write_raw_data(code, kline)

if __name__ == "__main__":
    #print("\n".join([str(item) for item in get_day_klines(StockCode.AG, "20250124", "20250204")]))
    #update_stock_db(StockCode.AG)
    stock_db = stock_db_utils.StockDB()
    print (stock_db.get_lastest_date(StockCode.AG))