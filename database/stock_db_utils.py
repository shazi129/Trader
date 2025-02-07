# -*- coding: utf-8 -*-

import os
import sqlite3
from api.api_base import KlineData

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
        "TurnoverRate": "REAL",                  #换手率
        "PE":           "REAL"                  #市盈率
    }

    #股票参数表
    _stock_indicator_table = {
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

    def get_indicator_table_name(self, name:str):
        return name + "_Ind"

    def create_stock_table(self, name: str):
        #创建原始数据表
        self.create_table(name, self._stock_raw_table)

        #创建股票指标表
        self.create_table(self.get_indicator_table_name(name), self._stock_indicator_table)

    def write_raw_data(self, name:str, data:KlineData):
        db_data= {
            "Date": data.date,
            "Open": data.open,
            "Close": data.close,
            "High": data.high,                
            "Low": data.low,
            "Volume": data.volume,
            "Turnover": data.turnover,
            "TurnoverRate":data.turnover_rate,
            "PE": data.pe
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

        sql = 'INSERT INTO %s(%s) VALUES(%s)' % (name, cols, values)
        print(sql)

        try:
            self._cursor.execute(sql)
            self._connection.commit()
        except sqlite3.IntegrityError as e:
            print("Insert error: ", e.sqlite_errorname)

    def get_latest_date(self, name:str)->str:
        sql = "SELECT MAX(Date) as RecentDate FROM %s" % name
        print(sql)

        try:
            self._cursor.execute(sql)
            row = self._cursor.fetchone()
            return row[0]
        except sqlite3.IntegrityError as e:
            print("Insert error: ", e.sqlite_errorname)
            return None

    def get_latest_klines(self, name:str, size:int)->list[KlineData]:
        sql = "SELECT * FROM %s ORDER BY Date DESC LIMIT %d" % (name, size)
        print(sql)

        try:
            self._cursor.execute(sql)
            result: list[KlineData] = []
            for row in self._cursor.fetchall():
                kline = KlineData()
                if kline.parse(row):
                    result.append(kline)
            return result
        except sqlite3.IntegrityError as e:
            print("get_latest_klines error: ", e.sqlite_errorname)
            return None
        
    def get_row_num(self, table_name:str)->int:
        sql = "SELECT COUNT(*) FROM %s" % table_name
        print(sql)
        try:
            self._cursor.execute(sql)
            row = self._cursor.fetchone()
            return row[0]
        except sqlite3.IntegrityError as e:
            print("get_row_num error: ", e.sqlite_errorname)
            return None
        
    def get_stock_rows(self, name:str)->tuple[int, int]:
        kline_size = self.get_row_num(name)
        indicator_size = self.get_row_num(self.get_indicator_table_name(name))
        return (kline_size, indicator_size)
