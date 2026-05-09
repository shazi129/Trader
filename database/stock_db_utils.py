# -*- coding: utf-8 -*-
"""
股票数据库管理类 - 长表存储方案

设计要点
========
1. 一个 SQLite 文件管理全部标的，避免 N 个 db 文件 / N*7 张分表的维护负担。
2. 同类因子放在同一张"长表"中，使用复合主键 ``(Symbol, Date)``：
   - kline_daily        : 原始K线（替代旧的 ``<Name>``       表）
   - factor_indicator   : 基础指标 （替代旧的 ``<Name>_Ind``  表）
   - factor_trend       : 趋势因子 （替代旧的 ``<Name>_Trend``）
   - factor_momentum    : 动量因子 （替代旧的 ``<Name>_Momentum``）
   - factor_volume      : 成交量因子（替代旧的 ``<Name>_Volume``）
   - factor_risk        : 风险因子 （替代旧的 ``<Name>_Risk`` ）
   - factor_ma_ratio    : 均线比率 （替代旧的 ``<Name>_MA_Ratio``）
3. 在 ``Date`` 上额外建索引，方便横截面（同日全市场）查询。
4. 对外方法签名保持兼容：仍然接受 ``name`` 作为股票 key，调用方无需感知列变化。
"""

import os
import sqlite3
from typing import List, Optional

from stock_info import DataValue, KlineData, KlineIndicator


class StockDB:
    """股票数据库管理类（长表版）"""

    # ============================================================
    # 精度控制
    # ============================================================

    # 不同数据类型的精度（小数位数）
    PRECISION_PRICE = 4      # 价格类（Open/Close/High/Low）
    PRECISION_FACTOR = 6     # 因子指标类（MA, MACD, RSI等）
    PRECISION_RATIO = 6      # 比率类（MA_Ratio, ROC等）
    PRECISION_VOLATILITY = 6  # 波动率/风险类

    # ============================================================
    # 长表名 & schema 定义
    # ============================================================

    TABLE_KLINE = "kline_daily"
    TABLE_INDICATOR = "factor_indicator"
    TABLE_TREND = "factor_trend"
    TABLE_MOMENTUM = "factor_momentum"
    TABLE_VOLUME = "factor_volume"
    TABLE_RISK = "factor_risk"
    TABLE_MA_RATIO = "factor_ma_ratio"

    @staticmethod
    def _round(value, precision: int):
        """四舍五入保留指定小数位数"""
        if value is None:
            return None
        try:
            return round(float(value), precision)
        except (ValueError, TypeError):
            return value

    def _round_kline(self, data: dict) -> dict:
        """K线数据四舍五入（价格保留4位）"""
        p = self.PRECISION_PRICE
        for key in ["Open", "Close", "High", "Low", "Turnover"]:
            if key in data:
                data[key] = self._round(data[key], p)
        return data

    def _round_factor(self, data: dict) -> dict:
        """因子数据四舍五入（因子保留6位）"""
        p = self.PRECISION_FACTOR
        for key in data:
            if key not in ["Symbol", "Date"]:
                data[key] = self._round(data[key], p)
        return data

    # 原始K线表
    _kline_columns = {
        "Symbol": "TEXT NOT NULL",
        "Date": "DATE NOT NULL",
        "Open": "REAL",
        "Close": "REAL",
        "High": "REAL",
        "Low": "REAL",
        "Volume": "REAL",
        "Turnover": "REAL",
        "TurnoverRate": "REAL",
    }

    # 基础技术指标
    _indicator_columns = {
        "Symbol": "TEXT NOT NULL",
        "Date": "DATE NOT NULL",
        "MA5": "REAL", "MA10": "REAL", "MA20": "REAL",
        "MA30": "REAL", "MA60": "REAL", "MA120": "REAL", "MA250": "REAL",
        "BollUp": "REAL", "BollLow": "REAL",
        "K": "REAL", "D": "REAL", "J": "REAL",
        "Dif": "REAL", "Dea": "REAL", "MACD": "REAL",
        "RSI1": "REAL", "RSI2": "REAL", "RSI3": "REAL",
        "ADOSC": "REAL",
    }

    # 趋势因子
    _trend_columns = {
        "Symbol": "TEXT NOT NULL",
        "Date": "DATE NOT NULL",
        "EMA12": "REAL", "EMA26": "REAL", "EMA50": "REAL",
        "MACD_HIST": "REAL",
        "ADX": "REAL", "Plus_DI": "REAL", "Minus_DI": "REAL",
        "TR": "REAL", "ATR": "REAL", "ATR_PCT": "REAL",
    }

    # 动量因子
    _momentum_columns = {
        "Symbol": "TEXT NOT NULL",
        "Date": "DATE NOT NULL",
        "MOM1W": "REAL", "MOM2W": "REAL", "MOM1M": "REAL",
        "MOM3M": "REAL", "MOM6M": "REAL", "MOM9M": "REAL", "MOM12M": "REAL",
        "ROC1W": "REAL", "ROC2W": "REAL", "ROC1M": "REAL",
        "ROC3M": "REAL", "ROC6M": "REAL", "ROC9M": "REAL", "ROC12M": "REAL",
        "CCI": "REAL", "WilliamsR": "REAL",
    }

    # 成交量因子
    _volume_columns = {
        "Symbol": "TEXT NOT NULL",
        "Date": "DATE NOT NULL",
        "OBV": "REAL", "VPT": "REAL", "ADL": "REAL",
        "MFI": "REAL",
        "ForceIndex1": "REAL", "ForceIndex13": "REAL", "ForceIndex21": "REAL",
    }

    # 风险因子
    _risk_columns = {
        "Symbol": "TEXT NOT NULL",
        "Date": "DATE NOT NULL",
        "HV20": "REAL", "HV60": "REAL",
        "MaxDrawdown": "REAL", "Volatility": "REAL",
        "Sharpe": "REAL", "Sortino": "REAL", "Calmar": "REAL",
        "Skewness": "REAL", "Kurtosis": "REAL",
    }

    # 均线比率 & 周线
    _ma_ratio_columns = {
        "Symbol": "TEXT NOT NULL",
        "Date": "DATE NOT NULL",
        "MA_Ratio_5": "REAL", "MA_Ratio_10": "REAL", "MA_Ratio_20": "REAL",
        "MA_Ratio_60": "REAL", "MA_Ratio_200": "REAL", "MA200": "REAL",
        "MA30W": "REAL", "MA75W": "REAL",
        "MA_Ratio_30W_75W": "REAL", "MA_Ratio_5W_30W": "REAL",
    }

    # 表 -> schema 映射
    _TABLE_SCHEMA = None  # 延迟在 __init__ 中赋值（依赖类属性）

    # ============================================================
    # 初始化与销毁
    # ============================================================

    def __init__(self, db_path: str = None) -> None:
        """构造时连接数据库，并保证全部长表存在"""
        if db_path is None:
            self._db_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "stock_data.db"
            )
        else:
            self._db_file = db_path

        print("open db:" + self._db_file)
        self._connection = sqlite3.connect(self._db_file)
        self._cursor = self._connection.cursor()

        # 传统模式：DELETE journal，关闭 WAL
        try:
            self._cursor.execute("PRAGMA journal_mode=DELETE")
            self._cursor.fetchall()
        except sqlite3.Error:
            pass

        self._TABLE_SCHEMA = {
            self.TABLE_KLINE: self._kline_columns,
            self.TABLE_INDICATOR: self._indicator_columns,
            self.TABLE_TREND: self._trend_columns,
            self.TABLE_MOMENTUM: self._momentum_columns,
            self.TABLE_VOLUME: self._volume_columns,
            self.TABLE_RISK: self._risk_columns,
            self.TABLE_MA_RATIO: self._ma_ratio_columns,
        }

        self._ensure_schema()

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
        try:
            self.close()
        except Exception:
            pass

    # ============================================================
    # 通用建表 / 索引
    # ============================================================

    def drop_all_tables(self):
        """删除所有长表（测试或重置时使用）"""
        tables = list(self._TABLE_SCHEMA.keys())
        for table in tables:
            try:
                self._cursor.execute(f"DROP TABLE IF EXISTS {table}")
                # 同时删除对应的 date 索引（表删了索引也会自动删，但保险起见）
                self._cursor.execute(f"DROP INDEX IF EXISTS idx_{table}_date")
            except sqlite3.Error as e:
                print(f"drop table {table} error: {e}")
        self._connection.commit()

    def _ensure_schema(self):
        """创建所有长表与索引（IF NOT EXISTS）"""
        for table, cols in self._TABLE_SCHEMA.items():
            self._create_long_table(table, cols)
            # 横截面查询索引（按日期定位全市场）
            self._cursor.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{table}_date ON {table}(Date)"
            )
        self._connection.commit()

    def _create_long_table(self, table_name: str, columns: dict):
        cols_sql = ", ".join(f"{k} {v}" for k, v in columns.items())
        sql = (
            f"CREATE TABLE IF NOT EXISTS {table_name} ("
            f"{cols_sql}, "
            f"PRIMARY KEY (Symbol, Date))"
        )
        self._cursor.execute(sql)

    # ============================================================
    # 通用写入（参数化，避免 SQL 注入 & 引号问题）
    # ============================================================

    def _upsert(self, table_name: str, data: dict):
        """INSERT OR REPLACE 一行"""
        if not data:
            return
        keys = list(data.keys())
        cols = ",".join(keys)
        placeholders = ",".join(["?"] * len(keys))
        values = [data[k] for k in keys]
        sql = f"INSERT OR REPLACE INTO {table_name}({cols}) VALUES({placeholders})"
        try:
            self._cursor.execute(sql, values)
            self._connection.commit()
        except sqlite3.Error as e:
            print(f"[StockDB] upsert error on {table_name}: {e}")

    def _upsert_many(self, table_name: str, rows: List[dict]):
        """批量 INSERT OR REPLACE，相同列结构"""
        if not rows:
            return
        keys = list(rows[0].keys())
        cols = ",".join(keys)
        placeholders = ",".join(["?"] * len(keys))
        sql = f"INSERT OR REPLACE INTO {table_name}({cols}) VALUES({placeholders})"
        values = [[row.get(k) for k in keys] for row in rows]
        try:
            self._cursor.executemany(sql, values)
            self._connection.commit()
        except sqlite3.Error as e:
            print(f"[StockDB] upsert_many error on {table_name}: {e}")

    # ============================================================
    # 基础查询
    # ============================================================

    def get_latest_date(self, name: str, table_name: str = None) -> Optional[str]:
        """获取指定股票在某张表中的最新日期，默认是 K 线表"""
        if table_name is None:
            table_name = self.TABLE_KLINE
        sql = f"SELECT MAX(Date) FROM {table_name} WHERE Symbol=?"
        try:
            self._cursor.execute(sql, (name,))
            row = self._cursor.fetchone()
            return row[0] if row and row[0] else None
        except sqlite3.Error as e:
            print("get_latest_date error: ", e)
            return None

    def get_row_count(self, name: str, table_name: str = None) -> int:
        """获取指定股票在某张表中的行数"""
        if table_name is None:
            table_name = self.TABLE_KLINE
        sql = f"SELECT COUNT(*) FROM {table_name} WHERE Symbol=?"
        try:
            self._cursor.execute(sql, (name,))
            row = self._cursor.fetchone()
            return row[0] if row else 0
        except sqlite3.Error as e:
            print("get_row_count error: ", e)
            return 0

    def list_symbols(self, table_name: str = None) -> List[str]:
        """列出表中出现过的所有股票符号"""
        if table_name is None:
            table_name = self.TABLE_KLINE
        try:
            self._cursor.execute(
                f"SELECT DISTINCT Symbol FROM {table_name} ORDER BY Symbol"
            )
            return [row[0] for row in self._cursor.fetchall()]
        except sqlite3.Error as e:
            print("list_symbols error: ", e)
            return []

    # ============================================================
    # K线表操作
    # ============================================================

    def parse_kline(self, kline: KlineData) -> dict:
        data = {
            "Date": kline.date,
            "Open": kline.open,
            "Close": kline.close,
            "High": kline.high,
            "Low": kline.low,
            "Volume": kline.volume,
            "Turnover": kline.turnover,
            "TurnoverRate": kline.turnover_rate,
        }
        return self._round_kline(data)

    def write_kline_data(self, name: str, kline: KlineData):
        """写入一条K线数据（带 Symbol）"""
        data = self.parse_kline(kline)
        data["Symbol"] = name
        self._upsert(self.TABLE_KLINE, data)

    def write_kline_data_many(self, name: str, klines: List[KlineData]):
        """批量写入K线"""
        rows = []
        for k in klines:
            r = self.parse_kline(k)
            r["Symbol"] = name
            rows.append(r)
        self._upsert_many(self.TABLE_KLINE, rows)

    def get_latest_klines(self, name: str, size: int) -> List[KlineData]:
        """获取最新的 N 条K线（按日期降序，再 parse 为 KlineData）"""
        sql = (
            "SELECT Date, Open, Close, High, Low, Volume, Turnover, TurnoverRate "
            f"FROM {self.TABLE_KLINE} WHERE Symbol=? ORDER BY Date DESC LIMIT ?"
        )
        try:
            self._cursor.execute(sql, (name, size))
            result = []
            for row in self._cursor.fetchall():
                kline = KlineData()
                if kline.parse(tuple(row)):
                    result.append(kline)
            return result
        except sqlite3.Error as e:
            print("get_latest_klines error: ", e)
            return []

    def get_klines_in_range(
        self, name: str, start_date: str = None, end_date: str = None
    ) -> List[KlineData]:
        """按日期区间取K线（升序）"""
        sql = (
            "SELECT Date, Open, Close, High, Low, Volume, Turnover, TurnoverRate "
            f"FROM {self.TABLE_KLINE} WHERE Symbol=?"
        )
        params: list = [name]
        if start_date:
            sql += " AND Date>=?"
            params.append(start_date)
        if end_date:
            sql += " AND Date<=?"
            params.append(end_date)
        sql += " ORDER BY Date ASC"
        try:
            self._cursor.execute(sql, params)
            result = []
            for row in self._cursor.fetchall():
                kline = KlineData()
                if kline.parse(tuple(row)):
                    result.append(kline)
            return result
        except sqlite3.Error as e:
            print("get_klines_in_range error: ", e)
            return []

    # ============================================================
    # 因子表 - parse 函数（与旧版一致）
    # ============================================================

    def parse_indicator(self, indicator: KlineIndicator) -> dict:
        data = {
            "Date": indicator.date,
            "MA5": indicator.ma5, "MA10": indicator.ma10, "MA20": indicator.ma20,
            "MA30": indicator.ma30, "MA60": indicator.ma60,
            "MA120": indicator.ma120, "MA250": indicator.ma250,
            "BollUp": indicator.boll_up, "BollLow": indicator.boll_low,
            "K": indicator.k, "D": indicator.d, "J": indicator.j,
            "Dif": indicator.dif, "Dea": indicator.dea, "MACD": indicator.macd,
            "RSI1": indicator.rsi1, "RSI2": indicator.rsi2, "RSI3": indicator.rsi3,
            "ADOSC": indicator.adosc,
        }
        return self._round_factor(data)

    def parse_trend(self, indicator: KlineIndicator) -> dict:
        data = {
            "Date": indicator.date,
            "EMA12": indicator.ema12, "EMA26": indicator.ema26, "EMA50": indicator.ema50,
            "MACD_HIST": indicator.macd_hist,
            "ADX": indicator.adx, "Plus_DI": indicator.plus_di, "Minus_DI": indicator.minus_di,
            "TR": indicator.tr, "ATR": indicator.atr, "ATR_PCT": indicator.atr_pct,
        }
        return self._round_factor(data)

    def parse_momentum(self, indicator: KlineIndicator) -> dict:
        data = {
            "Date": indicator.date,
            "MOM1W": indicator.mom1w, "MOM2W": indicator.mom2w, "MOM1M": indicator.mom1m,
            "MOM3M": indicator.mom3m, "MOM6M": indicator.mom6m,
            "MOM9M": indicator.mom9m, "MOM12M": indicator.mom12m,
            "ROC1W": indicator.roc1w, "ROC2W": indicator.roc2w, "ROC1M": indicator.roc1m,
            "ROC3M": indicator.roc3m, "ROC6M": indicator.roc6m,
            "ROC9M": indicator.roc9m, "ROC12M": indicator.roc12m,
            "CCI": indicator.cci, "WilliamsR": indicator.williams_r,
        }
        return self._round_factor(data)

    def parse_volume(self, indicator: KlineIndicator) -> dict:
        data = {
            "Date": indicator.date,
            "OBV": indicator.obv, "VPT": indicator.vpt, "ADL": indicator.adl,
            "MFI": indicator.mfi,
            "ForceIndex1": indicator.force_index1,
            "ForceIndex13": indicator.force_index13,
            "ForceIndex21": indicator.force_index21,
        }
        return self._round_factor(data)

    def parse_risk(self, indicator: KlineIndicator) -> dict:
        data = {
            "Date": indicator.date,
            "HV20": indicator.hv20, "HV60": indicator.hv60,
            "MaxDrawdown": indicator.max_drawdown, "Volatility": indicator.volatility,
            "Sharpe": indicator.sharpe, "Sortino": indicator.sortino, "Calmar": indicator.calmar,
            "Skewness": indicator.skewness, "Kurtosis": indicator.kurtosis,
        }
        return self._round_factor(data)

    def parse_ma_ratio(self, indicator: KlineIndicator) -> dict:
        data = {
            "Date": indicator.date,
            "MA_Ratio_5": indicator.ma_ratio_5, "MA_Ratio_10": indicator.ma_ratio_10,
            "MA_Ratio_20": indicator.ma_ratio_20, "MA_Ratio_60": indicator.ma_ratio_60,
            "MA_Ratio_200": indicator.ma_ratio_200, "MA200": indicator.ma200,
            "MA30W": indicator.ma30w, "MA75W": indicator.ma75w,
            "MA_Ratio_30W_75W": indicator.ma_ratio_30w_75w,
            "MA_Ratio_5W_30W": indicator.ma_ratio_5w_30w,
        }
        return self._round_factor(data)

    # ============================================================
    # 因子表 - 写入函数
    # ============================================================

    def _write_factor(self, table: str, name: str, parsed: dict):
        parsed["Symbol"] = name
        self._upsert(table, parsed)

    def write_indicator_data(self, name: str, indicator: KlineIndicator):
        self._write_factor(self.TABLE_INDICATOR, name, self.parse_indicator(indicator))

    def write_trend_data(self, name: str, indicator: KlineIndicator):
        self._write_factor(self.TABLE_TREND, name, self.parse_trend(indicator))

    def write_momentum_data(self, name: str, indicator: KlineIndicator):
        self._write_factor(self.TABLE_MOMENTUM, name, self.parse_momentum(indicator))

    def write_volume_data(self, name: str, indicator: KlineIndicator):
        self._write_factor(self.TABLE_VOLUME, name, self.parse_volume(indicator))

    def write_risk_data(self, name: str, indicator: KlineIndicator):
        self._write_factor(self.TABLE_RISK, name, self.parse_risk(indicator))

    def write_ma_ratio_data(self, name: str, indicator: KlineIndicator):
        self._write_factor(self.TABLE_MA_RATIO, name, self.parse_ma_ratio(indicator))

    def write_all_indicators(self, name: str, indicator: KlineIndicator):
        """一次性写入所有因子（同 K 线一起调用更高效）"""
        self.write_indicator_data(name, indicator)
        self.write_trend_data(name, indicator)
        self.write_momentum_data(name, indicator)
        self.write_volume_data(name, indicator)
        self.write_risk_data(name, indicator)
        self.write_ma_ratio_data(name, indicator)

    # ============================================================
    # 兼容旧 API（让上层代码不用改）
    # ============================================================

    def create_all_tables(self, name: str):
        """旧接口：曾经为每只股票创建独立表。现在长表已在 __init__ 建好，
        本方法保留为 no-op，仅为兼容旧调用。"""
        return

    def get_raw_table_name(self, name: str) -> str:        return self.TABLE_KLINE
    def get_indicator_table_name(self, name: str) -> str:  return self.TABLE_INDICATOR
    def get_trend_table_name(self, name: str) -> str:      return self.TABLE_TREND
    def get_momentum_table_name(self, name: str) -> str:   return self.TABLE_MOMENTUM
    def get_volume_table_name(self, name: str) -> str:     return self.TABLE_VOLUME
    def get_risk_table_name(self, name: str) -> str:       return self.TABLE_RISK
    def get_ma_ratio_table_name(self, name: str) -> str:   return self.TABLE_MA_RATIO

    # ============================================================
    # 综合查询
    # ============================================================

    def get_stock_row_counts(self, name: str) -> dict:
        """指定股票在各张长表中的行数"""
        return {
            "raw":       self.get_row_count(name, self.TABLE_KLINE),
            "indicator": self.get_row_count(name, self.TABLE_INDICATOR),
            "trend":     self.get_row_count(name, self.TABLE_TREND),
            "momentum":  self.get_row_count(name, self.TABLE_MOMENTUM),
            "volume":    self.get_row_count(name, self.TABLE_VOLUME),
            "risk":      self.get_row_count(name, self.TABLE_RISK),
            "ma_ratio":  self.get_row_count(name, self.TABLE_MA_RATIO),
        }

    def get_stock_ratio_data(self, denominator_key: str, numerator_key: str) -> List[DataValue]:
        """返回 denominator.Close / numerator.Close 的时间序列"""
        sql = f"""
        SELECT a.Date, a.Close * 1.0 / b.Close
        FROM {self.TABLE_KLINE} a
        INNER JOIN {self.TABLE_KLINE} b
                ON a.Date = b.Date
        WHERE a.Symbol = ? AND b.Symbol = ? AND b.Close <> 0
        ORDER BY a.Date ASC
        """
        try:
            self._cursor.execute(sql, (denominator_key, numerator_key))
            return [DataValue(str(row[0]), row[1]) for row in self._cursor.fetchall()]
        except sqlite3.Error as e:
            print("get_stock_ratio_data error: ", e)
            return []

    # ============================================================
    # 横截面查询（新方案的核心红利）
    # ============================================================

    def cross_section_rank(
        self,
        table: str,
        column: str,
        date: str,
        top_n: int = 50,
        ascending: bool = False,
    ) -> List[tuple]:
        """同一日期下按指定因子列对全市场排序（选股 / 选标的）"""
        order = "ASC" if ascending else "DESC"
        sql = (
            f"SELECT Symbol, {column} FROM {table} "
            f"WHERE Date=? AND {column} IS NOT NULL "
            f"ORDER BY {column} {order} LIMIT ?"
        )
        try:
            self._cursor.execute(sql, (date, top_n))
            return self._cursor.fetchall()
        except sqlite3.Error as e:
            print("cross_section_rank error: ", e)
            return []
