# -*- coding: utf-8 -*-

import os
import sqlite3

from StockInfo import DataValue, KlineData, KlineIndicator


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
        "MA250":    "REAL",

        "BollUp":   "REAL",
        "BollLow":  "REAL",

        "K":        "REAL",
        "D":        "REAL",
        "J":        "REAL",

        "Dif":      "REAL",
        "Dea":      "REAL",
        "MACD":     "REAL",

        "RSI1":     "REAL",
        "RSI2":     "REAL",
        "RSI3":     "REAL",

        "ADOSC":    "REAL",
    }

    def __init__(self) -> None:
        """构造时连上数据库"""
        self._db_file = '%s/stock_data.db' % os.path.dirname(os.path.abspath(__file__))
        print("open db:" + self._db_file)

        self._connection = sqlite3.connect(self._db_file)
        if self._connection == None:
            print("connect db error")
        else:
            self._cursor = self._connection.cursor()

    def __del__(self):
        """析构时断开数据库"""
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
        return self.create_table(name, self._stock_raw_table)
    
    def create_indicator_table(self, name:str):
        return self.create_table(self.get_indicator_table_name(name), self._stock_indicator_table)

    def parse_kline(self, kline: KlineData)->dict:
        row_data= {
            "Date": kline.date,
            "Open": kline.open,
            "Close": kline.close,
            "High": kline.high,                
            "Low": kline.low,
            "Volume": kline.volume,
            "Turnover": kline.turnover,
            "TurnoverRate":kline.turnover_rate,
            "PE": kline.pe
        }
        return row_data
    
    def parse_indicator(self, indicator: KlineIndicator)->dict:
        row_data={
            "Date": indicator.date,     #日期
            "MA5": indicator.ma5,
            "MA10": indicator.ma10,
            "MA20": indicator.ma20,
            "MA30": indicator.ma30,
            "MA60": indicator.ma60,
            "MA120": indicator.ma120,
            "MA250": indicator.ma250,

            "BollUp": indicator.boll_up,
            "BollLow": indicator.boll_low,

            "K": indicator.k,
            "D": indicator.d,
            "J": indicator.j,

            "Dif": indicator.dif,
            "Dea": indicator.dea,
            "MACD": indicator.macd,

            "RSI1": indicator.rsi1,
            "RSI2": indicator.rsi2,
            "RSI3": indicator.rsi3,

            "ADOSC": indicator.adosc,
        }
        return row_data

    def write_raw_data(self, name:str, data:dict):
        keys = ",".join(data.keys())
        values = ",".join([f'\'{item}\'' if isinstance(item, str) else str(item) for item in data.values()])
        sql = 'INSERT OR REPLACE INTO %s(%s) VALUES(%s)' % (name, keys, values)
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
        """获取一个表的K线数目和参数数目"""
        kline_size = self.get_row_num(name)
        indicator_size = self.get_row_num(self.get_indicator_table_name(name))
        return (kline_size, indicator_size)
    
    def get_stock_ratio_data(self, denominator_key:str, numerator_key:str)->list[DataValue]:
        """获取股票收盘价的比值数据"""
        sql = f"SELECT {denominator_key}.Date, {denominator_key}.Close/{numerator_key}.Close FROM {denominator_key} INNER JOIN {numerator_key} ON {denominator_key}.Date = {numerator_key}.Date"
        print(sql)
        try:
            self._cursor.execute(sql)
            all_data = self._cursor.fetchall()
            result: list[DataValue] = []
            for row in all_data:
                data = DataValue(str(row[0]), row[1])
                result.append(data)
            return result
        except sqlite3.IntegrityError as e:
            print("get_stock_ratio_data error: ", e.sqlite_errorname)
            return None
