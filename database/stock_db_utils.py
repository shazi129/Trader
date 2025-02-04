# -*- coding: utf-8 -*-

import os
import sqlite3
from api.api_base import KlineData, StockCode

class StockDB:

    #股票原始数据表
    _stock_raw_table= {
        "Date":         "DATE primary key",     #日期
        "Open":         "REAL",                 #开盘价
        "Close":        "REAL",                 #收盘价
        "High":         "REAL",                 #最高价                 
        "Low":          "REAL",                  #最低价
        "Volume":       "REAL",                 #成交量
        "Turnover":     "REAL",                 #成交额
        "TurnoverRate": "REAL"                  #换手率
    }

    #股票参数表
    _stock_param_table = {
        "Date":     "DATE primary key",     #日期
        "MA5":      "REAL",
        "MA10":     "REAL",
        "MA20":     "REAL",
        "MA30":     "REAL",
        "MA60":     "REAL",
        "MA120":    "REAL",
        "MA250":    "REAL"
    }

    def __init__(self) -> None:
        self._db_file = '%s/stock_data.db' % os.path.dirname(os.path.abspath(__file__))
        print("open db:" + self._db_file)

        self._connection = sqlite3.connect(self._db_file)
        if self._connection == None:
            print("connect db error")
        else:
            self._cursor = self._connection.cursor()

    def __del__(self):
        print("close db:" + self._db_file)
        if self._connection != None:
            self._connection.commit()
        if self._cursor != None:
            self._cursor.close()
        if self._connection != None:
            self._connection.close()

    def create_table(self, table_name: str, table_format: dict):
        sql = "CREATE TABLE IF NOT EXISTS %s(" % table_name
        for k, v in table_format.items():
            sql += "%s %s," % (k, v)
        if sql.endswith(","):
            sql = sql[:-1]
        sql += ")"
        print(sql)
        self._cursor.execute(sql)
        self._connection.commit()

    def create_stock_table(self, code: StockCode):
        #创建原始数据表
        self.create_table(code.name, self._stock_raw_table)

        #创建股票指标表
        self.create_table(code.name + "_Ind", self._stock_param_table)

    def write_raw_data(self, code: StockCode, data:KlineData):
        db_data= {
            "Date": data.date,
            "Open": data.open,
            "Close": data.close,
            "High": data.high,                
            "Low": data.low,
            "Volume": data.volume,
            "Turnover": data.turnover,
            "TurnoverRate":data.turnover_rate
        }

        cols = ""
        values = ""
        for k, v in db_data.items():
            prefix = ""
            if cols != "":
                prefix = ", "
            if isinstance(v, str):
                v = "'%s'" % v
            else:
                v = str(v)
            cols += prefix + k
            values += prefix + v

        sql = 'INSERT INTO %s(%s) VALUES(%s)' % (code.name, cols, values)
        print(sql)

        try:
            self._cursor.execute(sql)
            self._connection.commit()
        except sqlite3.IntegrityError as e:
            print("Insert error: ", e.sqlite_errorname)

    def get_lastest_date(self, code: StockCode)->str:
        sql = "SELECT MAX(Date) as RecentDate FROM %s" % code.name
        print(sql)

        try:
            self._cursor.execute(sql)
            row = self._cursor.fetchone()
            return row[0]
        except sqlite3.IntegrityError as e:
            print("Insert error: ", e.sqlite_errorname)
            return None
