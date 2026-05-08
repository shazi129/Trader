# -*- coding: utf-8 -*-

import os
import sqlite3

from stock_info import DataValue, KlineData, KlineIndicator


class StockDB:
    """股票数据库管理类 - 方案B：分表存储"""

    # ============================================================
    # 表结构定义
    # ============================================================

    # 股票原始数据表
    _stock_raw_table = {
        "Date": "DATE primary key",  # 日期
        "Open": "REAL",  # 开盘价
        "Close": "REAL",  # 收盘价
        "High": "REAL",  # 最高价
        "Low": "REAL",  # 最低价
        "Volume": "REAL",  # 成交量
        "Turnover": "REAL",  # 成交额
        "TurnoverRate": "REAL",  # 换手率
        "PE": "REAL",  # 市盈率
    }

    # 股票基础技术指标表
    _stock_indicator_table = {
        "Date": "DATE primary key",
        "MA5": "REAL", "MA10": "REAL", "MA20": "REAL",
        "MA30": "REAL", "MA60": "REAL", "MA120": "REAL", "MA250": "REAL",
        "BollUp": "REAL", "BollLow": "REAL",
        "K": "REAL", "D": "REAL", "J": "REAL",
        "Dif": "REAL", "Dea": "REAL", "MACD": "REAL",
        "RSI1": "REAL", "RSI2": "REAL", "RSI3": "REAL",
        "ADOSC": "REAL",
    }

    # 趋势类因子表
    _stock_trend_table = {
        "Date": "DATE primary key",
        "EMA12": "REAL", "EMA26": "REAL", "EMA50": "REAL",
        "MACD_HIST": "REAL",
        "ADX": "REAL", "Plus_DI": "REAL", "Minus_DI": "REAL",
        "TR": "REAL", "ATR": "REAL", "ATR_PCT": "REAL",
    }

    # 动量类因子表
    _stock_momentum_table = {
        "Date": "DATE primary key",
        "MOM1W": "REAL", "MOM2W": "REAL", "MOM1M": "REAL",
        "MOM3M": "REAL", "MOM6M": "REAL", "MOM9M": "REAL", "MOM12M": "REAL",
        "ROC1W": "REAL", "ROC2W": "REAL", "ROC1M": "REAL",
        "ROC3M": "REAL", "ROC6M": "REAL", "ROC9M": "REAL", "ROC12M": "REAL",
        "CCI": "REAL", "WilliamsR": "REAL",
    }

    # 成交量类因子表
    _stock_volume_table = {
        "Date": "DATE primary key",
        "OBV": "REAL", "VPT": "REAL", "ADL": "REAL",
        "MFI": "REAL",
        "ForceIndex1": "REAL", "ForceIndex13": "REAL", "ForceIndex21": "REAL",
    }

    # 波动率与风险指标表
    _stock_risk_table = {
        "Date": "DATE primary key",
        "HV20": "REAL", "HV60": "REAL",
        "MaxDrawdown": "REAL", "Volatility": "REAL",
        "Sharpe": "REAL", "Sortino": "REAL", "Calmar": "REAL",
        "Skewness": "REAL", "Kurtosis": "REAL",
    }

    # 均线比率与周线因子表
    _stock_ma_ratio_table = {
        "Date": "DATE primary key",
        "MA_Ratio_5": "REAL", "MA_Ratio_10": "REAL", "MA_Ratio_20": "REAL",
        "MA_Ratio_60": "REAL", "MA_Ratio_200": "REAL", "MA200": "REAL",
        "MA30W": "REAL", "MA75W": "REAL",
        "MA_Ratio_30W_75W": "REAL", "MA_Ratio_5W_30W": "REAL",
    }

    # ============================================================
    # 表名后缀常量
    # ============================================================
    SUFFIX_RAW = ""           # 原始数据表（无后缀）
    SUFFIX_IND = "_Ind"      # 基础指标表
    SUFFIX_TREND = "_Trend"  # 趋势因子表
    SUFFIX_MOM = "_Momentum" # 动量因子表
    SUFFIX_VOL = "_Volume"    # 成交量因子表
    SUFFIX_RISK = "_Risk"    # 风险指标表
    SUFFIX_MA = "_MA_Ratio"  # 均线比率表

    # ============================================================
    # 初始化与销毁
    # ============================================================

    def __init__(self, db_path: str = None) -> None:
        """构造时连接数据库"""
        if db_path is None:
            self._db_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stock_data.db')
        else:
            self._db_file = db_path

        print("open db:" + self._db_file)
        self._connection = sqlite3.connect(self._db_file)
        if self._connection is None:
            print("connect db error")
        else:
            self._cursor = self._connection.cursor()

    def close(self):
        """显式关闭数据库连接"""
        try:
            if self._connection is not None:
                self._connection.commit()
                self._connection.close()
                self._connection = None
                self._cursor = None
                print("close db:" + self._db_file)
        except Exception as e:
            print("close db error: %s" % e)

    def __del__(self):
        """析构时断开数据库"""
        self.close()

    # ============================================================
    # 通用表操作方法
    # ============================================================

    def create_table(self, table_name: str, table_format: dict):
        """创建表"""
        sql = "CREATE TABLE IF NOT EXISTS %s(" % table_name
        for k, v in table_format.items():
            sql += "%s %s," % (k, v)
        if sql.endswith(","):
            sql = sql[:-1]
        sql += ")"
        print(sql)
        self._cursor.execute(sql)
        self._connection.commit()

    def write_row(self, table_name: str, data: dict):
        """写入一行数据（INSERT OR REPLACE）"""
        keys = ",".join(data.keys())
        values = ",".join([f'\'{item}\'' if isinstance(item, str) else str(item) for item in data.values()])
        sql = 'INSERT OR REPLACE INTO %s(%s) VALUES(%s)' % (table_name, keys, values)
        try:
            self._cursor.execute(sql)
            self._connection.commit()
        except sqlite3.IntegrityError as e:
            print("Insert error: ", e.sqlite_errorname)

    def get_latest_date(self, table_name: str) -> str:
        """获取表中的最新日期"""
        sql = "SELECT MAX(Date) as RecentDate FROM %s" % table_name
        try:
            self._cursor.execute(sql)
            row = self._cursor.fetchone()
            return row[0] if row else None
        except sqlite3.Error as e:
            print("get_latest_date error: ", e)
            return None

    def get_row_count(self, table_name: str) -> int:
        """获取表中的行数"""
        sql = "SELECT COUNT(*) FROM %s" % table_name
        try:
            self._cursor.execute(sql)
            row = self._cursor.fetchone()
            return row[0] if row else 0
        except sqlite3.Error as e:
            print("get_row_count error: ", e)
            return 0

    # ============================================================
    # 表名生成方法
    # ============================================================

    def get_raw_table_name(self, name: str) -> str:
        """获取原始数据表名"""
        return name

    def get_indicator_table_name(self, name: str) -> str:
        """获取基础指标表名"""
        return name + self.SUFFIX_IND

    def get_trend_table_name(self, name: str) -> str:
        """获取趋势因子表名"""
        return name + self.SUFFIX_TREND

    def get_momentum_table_name(self, name: str) -> str:
        """获取动量因子表名"""
        return name + self.SUFFIX_MOM

    def get_volume_table_name(self, name: str) -> str:
        """获取成交量因子表名"""
        return name + self.SUFFIX_VOL

    def get_risk_table_name(self, name: str) -> str:
        """获取风险指标表名"""
        return name + self.SUFFIX_RISK

    def get_ma_ratio_table_name(self, name: str) -> str:
        """获取均线比率表名"""
        return name + self.SUFFIX_MA

    # ============================================================
    # 创建所有表
    # ============================================================

    def create_all_tables(self, name: str):
        """为指定股票创建所有表"""
        self.create_table(name, self._stock_raw_table)
        self.create_table(self.get_indicator_table_name(name), self._stock_indicator_table)
        self.create_table(self.get_trend_table_name(name), self._stock_trend_table)
        self.create_table(self.get_momentum_table_name(name), self._stock_momentum_table)
        self.create_table(self.get_volume_table_name(name), self._stock_volume_table)
        self.create_table(self.get_risk_table_name(name), self._stock_risk_table)
        self.create_table(self.get_ma_ratio_table_name(name), self._stock_ma_ratio_table)

    # ============================================================
    # 原始数据表操作
    # ============================================================

    def parse_kline(self, kline: KlineData) -> dict:
        """将KlineData解析为字典"""
        return {
            "Date": kline.date,
            "Open": kline.open,
            "Close": kline.close,
            "High": kline.high,
            "Low": kline.low,
            "Volume": kline.volume,
            "Turnover": kline.turnover,
            "TurnoverRate": kline.turnover_rate,
            "PE": kline.pe,
        }

    def write_kline_data(self, name: str, kline: KlineData):
        """写入K线数据"""
        data = self.parse_kline(kline)
        self.write_row(name, data)

    def get_latest_klines(self, name: str, size: int) -> list:
        """获取最新的K线数据"""
        sql = "SELECT * FROM %s ORDER BY Date DESC LIMIT %d" % (name, size)
        try:
            self._cursor.execute(sql)
            result = []
            for row in self._cursor.fetchall():
                kline = KlineData()
                if kline.parse(row):
                    result.append(kline)
            return result
        except sqlite3.Error as e:
            print("get_latest_klines error: ", e)
            return []

    # ============================================================
    # 基础指标表操作
    # ============================================================

    def parse_indicator(self, indicator: KlineIndicator) -> dict:
        """将KlineIndicator解析为字典（基础指标）"""
        return {
            "Date": indicator.date,
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

    def write_indicator_data(self, name: str, indicator: KlineIndicator):
        """写入基础指标数据"""
        data = self.parse_indicator(indicator)
        self.write_row(self.get_indicator_table_name(name), data)

    # ============================================================
    # 趋势因子表操作
    # ============================================================

    def parse_trend(self, indicator: KlineIndicator) -> dict:
        """解析趋势类因子"""
        return {
            "Date": indicator.date,
            "EMA12": indicator.ema12,
            "EMA26": indicator.ema26,
            "EMA50": indicator.ema50,
            "MACD_HIST": indicator.macd_hist,
            "ADX": indicator.adx,
            "Plus_DI": indicator.plus_di,
            "Minus_DI": indicator.minus_di,
            "TR": indicator.tr,
            "ATR": indicator.atr,
            "ATR_PCT": indicator.atr_pct,
        }

    def write_trend_data(self, name: str, indicator: KlineIndicator):
        """写入趋势因子数据"""
        data = self.parse_trend(indicator)
        self.write_row(self.get_trend_table_name(name), data)

    # ============================================================
    # 动量因子表操作
    # ============================================================

    def parse_momentum(self, indicator: KlineIndicator) -> dict:
        """解析动量类因子"""
        return {
            "Date": indicator.date,
            "MOM1W": indicator.mom1w,
            "MOM2W": indicator.mom2w,
            "MOM1M": indicator.mom1m,
            "MOM3M": indicator.mom3m,
            "MOM6M": indicator.mom6m,
            "MOM9M": indicator.mom9m,
            "MOM12M": indicator.mom12m,
            "ROC1W": indicator.roc1w,
            "ROC2W": indicator.roc2w,
            "ROC1M": indicator.roc1m,
            "ROC3M": indicator.roc3m,
            "ROC6M": indicator.roc6m,
            "ROC9M": indicator.roc9m,
            "ROC12M": indicator.roc12m,
            "CCI": indicator.cci,
            "WilliamsR": indicator.williams_r,
        }

    def write_momentum_data(self, name: str, indicator: KlineIndicator):
        """写入动量因子数据"""
        data = self.parse_momentum(indicator)
        self.write_row(self.get_momentum_table_name(name), data)

    # ============================================================
    # 成交量因子表操作
    # ============================================================

    def parse_volume(self, indicator: KlineIndicator) -> dict:
        """解析成交量类因子"""
        return {
            "Date": indicator.date,
            "OBV": indicator.obv,
            "VPT": indicator.vpt,
            "ADL": indicator.adl,
            "MFI": indicator.mfi,
            "ForceIndex1": indicator.force_index1,
            "ForceIndex13": indicator.force_index13,
            "ForceIndex21": indicator.force_index21,
        }

    def write_volume_data(self, name: str, indicator: KlineIndicator):
        """写入成交量因子数据"""
        data = self.parse_volume(indicator)
        self.write_row(self.get_volume_table_name(name), data)

    # ============================================================
    # 风险指标表操作
    # ============================================================

    def parse_risk(self, indicator: KlineIndicator) -> dict:
        """解析波动率与风险指标"""
        return {
            "Date": indicator.date,
            "HV20": indicator.hv20,
            "HV60": indicator.hv60,
            "MaxDrawdown": indicator.max_drawdown,
            "Volatility": indicator.volatility,
            "Sharpe": indicator.sharpe,
            "Sortino": indicator.sortino,
            "Calmar": indicator.calmar,
            "Skewness": indicator.skewness,
            "Kurtosis": indicator.kurtosis,
        }

    def write_risk_data(self, name: str, indicator: KlineIndicator):
        """写入风险指标数据"""
        data = self.parse_risk(indicator)
        self.write_row(self.get_risk_table_name(name), data)

    # ============================================================
    # 均线比率表操作
    # ============================================================

    def parse_ma_ratio(self, indicator: KlineIndicator) -> dict:
        """解析均线比率与周线因子"""
        return {
            "Date": indicator.date,
            "MA_Ratio_5": indicator.ma_ratio_5,
            "MA_Ratio_10": indicator.ma_ratio_10,
            "MA_Ratio_20": indicator.ma_ratio_20,
            "MA_Ratio_60": indicator.ma_ratio_60,
            "MA_Ratio_200": indicator.ma_ratio_200,
            "MA200": indicator.ma200,
            "MA30W": indicator.ma30w,
            "MA75W": indicator.ma75w,
            "MA_Ratio_30W_75W": indicator.ma_ratio_30w_75w,
            "MA_Ratio_5W_30W": indicator.ma_ratio_5w_30w,
        }

    def write_ma_ratio_data(self, name: str, indicator: KlineIndicator):
        """写入均线比率数据"""
        data = self.parse_ma_ratio(indicator)
        self.write_row(self.get_ma_ratio_table_name(name), data)

    # ============================================================
    # 批量写入（一次计算，写入所有表）
    # ============================================================

    def write_all_indicators(self, name: str, indicator: KlineIndicator):
        """一次性写入所有指标数据到各个表"""
        self.write_indicator_data(name, indicator)
        self.write_trend_data(name, indicator)
        self.write_momentum_data(name, indicator)
        self.write_volume_data(name, indicator)
        self.write_risk_data(name, indicator)
        self.write_ma_ratio_data(name, indicator)

    # ============================================================
    # 查询方法
    # ============================================================

    def get_stock_row_counts(self, name: str) -> dict:
        """获取股票所有表的数据行数"""
        return {
            "raw": self.get_row_count(name),
            "indicator": self.get_row_count(self.get_indicator_table_name(name)),
            "trend": self.get_row_count(self.get_trend_table_name(name)),
            "momentum": self.get_row_count(self.get_momentum_table_name(name)),
            "volume": self.get_row_count(self.get_volume_table_name(name)),
            "risk": self.get_row_count(self.get_risk_table_name(name)),
            "ma_ratio": self.get_row_count(self.get_ma_ratio_table_name(name)),
        }

    def get_stock_ratio_data(self, denominator_key: str, numerator_key: str) -> list:
        """获取股票收盘价的比值数据"""
        sql = f"SELECT {denominator_key}.Date, {denominator_key}.Close/{numerator_key}.Close FROM {denominator_key} INNER JOIN {numerator_key} ON {denominator_key}.Date = {numerator_key}.Date"
        try:
            self._cursor.execute(sql)
            all_data = self._cursor.fetchall()
            result = []
            for row in all_data:
                data = DataValue(str(row[0]), row[1])
                result.append(data)
            return result
        except sqlite3.Error as e:
            print("get_stock_ratio_data error: ", e)
            return []
