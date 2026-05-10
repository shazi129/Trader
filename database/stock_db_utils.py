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

from quote_api.quote_base import DailyQuote
from quantitative.factor_data import KlineIndicator
from utils.data_types import DataValue
from utils.logger import get_logger

_log = get_logger(__name__)


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

        _log.debug("open db: %s", self._db_file)
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
                _log.debug("close db: %s", self._db_file)
        except Exception as e:
            _log.warning("close db error: %s", e)

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
                _log.warning("drop table %s error: %s", table, e)
        self._connection.commit()

    def _ensure_schema(self):
        """创建所有长表与索引（IF NOT EXISTS）。

        若长表已存在但缺少新增列，会自动 ``ALTER TABLE ADD COLUMN`` 补齐，
        以便代码升级后无需手动迁移历史 DB。
        """
        for table, cols in self._TABLE_SCHEMA.items():
            self._create_long_table(table, cols)
            self._migrate_add_missing_columns(table, cols)
            # 横截面查询索引（按日期定位全市场）
            self._cursor.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{table}_date ON {table}(Date)"
            )
        self._connection.commit()

    def _migrate_add_missing_columns(self, table_name: str, columns: dict):
        """对已存在的表，比较实际列与 schema，缺什么补什么（ALTER TABLE ADD COLUMN）。"""
        try:
            self._cursor.execute(f"PRAGMA table_info({table_name})")
            existing = {row[1] for row in self._cursor.fetchall()}
        except sqlite3.Error as e:
            _log.warning("read table_info(%s) error: %s", table_name, e)
            return
        if not existing:
            return  # 表刚被 CREATE，列肯定齐
        for col, decl in columns.items():
            if col in existing:
                continue
            # SQLite 的 ADD COLUMN 不允许带 PRIMARY KEY / NOT NULL without default 等约束，
            # 所以这里把声明里的非空约束去掉，仅保留类型部分。
            type_only = decl.split()[0]
            try:
                self._cursor.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN {col} {type_only}"
                )
                _log.info("migrate: add column %s.%s %s", table_name, col, type_only)
            except sqlite3.Error as e:
                _log.warning("ALTER TABLE %s ADD %s error: %s", table_name, col, e)

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
            _log.error("upsert error on %s: %s", table_name, e)

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
            _log.error("upsert_many error on %s: %s", table_name, e)

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
            _log.warning("get_latest_date error: %s", e)
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
            _log.warning("get_row_count error: %s", e)
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
            _log.warning("list_symbols error: %s", e)
            return []

    # ============================================================
    # K线表操作
    # ============================================================

    def parse_kline(self, quote: DailyQuote) -> dict:
        """DailyQuote -> kline_daily 行 dict（带 4 位小数舍入）。

        ``TurnoverRate`` 在数据源未提供时回落到 0.0。
        ``pre_close`` 不入库——前复权序列下 ``pre_close = 上一行 close``，
        属可派生字段，分析层按需现算即可。
        """
        data = {
            "Date": quote.date,
            "Open": quote.open,
            "Close": quote.close,
            "High": quote.high,
            "Low": quote.low,
            "Volume": quote.volume,
            "Turnover": quote.turnover,
            "TurnoverRate": getattr(quote, "turnover_rate", 0.0),
        }
        return self._round_kline(data)

    def write_kline_data(self, name: str, quote: DailyQuote):
        """写入一条K线数据（带 Symbol）"""
        data = self.parse_kline(quote)
        data["Symbol"] = name
        self._upsert(self.TABLE_KLINE, data)

    def write_kline_data_many(self, name: str, quotes: List[DailyQuote]):
        """批量写入K线"""
        rows = []
        for q in quotes:
            r = self.parse_kline(q)
            r["Symbol"] = name
            rows.append(r)
        self._upsert_many(self.TABLE_KLINE, rows)

    # 统一一次 SELECT 列序，便于多个查询接口复用 _row_to_quote
    _KLINE_SELECT_COLS = (
        "Date, Open, Close, High, Low, Volume, Turnover, TurnoverRate"
    )

    def _row_to_quote(self, row: tuple, source: str = "db") -> DailyQuote:
        """把 SELECT(_KLINE_SELECT_COLS) 行解码为 DailyQuote。"""
        q = DailyQuote()
        q.date = str(row[0])
        q.open = float(row[1]) if row[1] is not None else 0.0
        q.close = float(row[2]) if row[2] is not None else 0.0
        q.high = float(row[3]) if row[3] is not None else 0.0
        q.low = float(row[4]) if row[4] is not None else 0.0
        q.volume = float(row[5]) if row[5] is not None else 0.0
        q.turnover = float(row[6]) if row[6] is not None else 0.0
        q.turnover_rate = float(row[7]) if len(row) > 7 and row[7] is not None else 0.0
        q.source = source
        return q

    def get_latest_klines(self, name: str, size: int) -> List[DailyQuote]:
        """获取最新的 N 条K线（按日期降序，返回 DailyQuote 列表）"""
        sql = (
            f"SELECT {self._KLINE_SELECT_COLS} "
            f"FROM {self.TABLE_KLINE} WHERE Symbol=? ORDER BY Date DESC LIMIT ?"
        )
        try:
            self._cursor.execute(sql, (name, size))
            return [self._row_to_quote(row) for row in self._cursor.fetchall()]
        except sqlite3.Error as e:
            _log.warning("get_latest_klines error: %s", e)
            return []

    def get_klines_in_range(
        self, name: str, start_date: str = None, end_date: str = None
    ) -> List[DailyQuote]:
        """按日期区间取K线（升序）"""
        sql = (
            f"SELECT {self._KLINE_SELECT_COLS} "
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
            return [self._row_to_quote(row) for row in self._cursor.fetchall()]
        except sqlite3.Error as e:
            _log.warning("get_klines_in_range error: %s", e)
            return []

    def get_daily_quote_by_date(self, name: str, date: str) -> Optional[DailyQuote]:
        """按 (Symbol, Date) 取单条 K 线"""
        sql = (
            f"SELECT {self._KLINE_SELECT_COLS} "
            f"FROM {self.TABLE_KLINE} WHERE Symbol=? AND Date=? LIMIT 1"
        )
        try:
            self._cursor.execute(sql, (name, date))
            row = self._cursor.fetchone()
            return self._row_to_quote(row) if row else None
        except sqlite3.Error as e:
            _log.warning("get_daily_quote_by_date error: %s", e)
            return None


    # ============================================================
    # 因子表 - 元数据驱动的 parse / 写入
    # ============================================================
    #
    # `_FACTOR_FIELD_MAP` 把每张因子表的 (列名 -> KlineIndicator 属性名)
    # 集中在一处，消掉之前 6 套 parse_xxx + 6 套 write_xxx_data 的样板代码。
    # 新增因子时只需在这里加一行，无需再改 parse/write 函数。
    # ============================================================

    _FACTOR_FIELD_MAP = {
        "TABLE_INDICATOR": [
            ("MA5", "ma5"), ("MA10", "ma10"), ("MA20", "ma20"),
            ("MA30", "ma30"), ("MA60", "ma60"),
            ("MA120", "ma120"), ("MA250", "ma250"),
            ("BollUp", "boll_up"), ("BollLow", "boll_low"),
            ("K", "k"), ("D", "d"), ("J", "j"),
            ("Dif", "dif"), ("Dea", "dea"), ("MACD", "macd"),
            ("RSI1", "rsi1"), ("RSI2", "rsi2"), ("RSI3", "rsi3"),
            ("ADOSC", "adosc"),
        ],
        "TABLE_TREND": [
            ("EMA12", "ema12"), ("EMA26", "ema26"), ("EMA50", "ema50"),
            ("MACD_HIST", "macd_hist"),
            ("ADX", "adx"), ("Plus_DI", "plus_di"), ("Minus_DI", "minus_di"),
            ("TR", "tr"), ("ATR", "atr"), ("ATR_PCT", "atr_pct"),
        ],
        "TABLE_MOMENTUM": [
            ("MOM1W", "mom1w"), ("MOM2W", "mom2w"), ("MOM1M", "mom1m"),
            ("MOM3M", "mom3m"), ("MOM6M", "mom6m"),
            ("MOM9M", "mom9m"), ("MOM12M", "mom12m"),
            ("ROC1W", "roc1w"), ("ROC2W", "roc2w"), ("ROC1M", "roc1m"),
            ("ROC3M", "roc3m"), ("ROC6M", "roc6m"),
            ("ROC9M", "roc9m"), ("ROC12M", "roc12m"),
            ("CCI", "cci"), ("WilliamsR", "williams_r"),
        ],
        "TABLE_VOLUME": [
            ("OBV", "obv"), ("VPT", "vpt"), ("ADL", "adl"),
            ("MFI", "mfi"),
            ("ForceIndex1", "force_index1"),
            ("ForceIndex13", "force_index13"),
            ("ForceIndex21", "force_index21"),
        ],
        "TABLE_RISK": [
            ("HV20", "hv20"), ("HV60", "hv60"),
            ("MaxDrawdown", "max_drawdown"), ("Volatility", "volatility"),
            ("Sharpe", "sharpe"), ("Sortino", "sortino"), ("Calmar", "calmar"),
            ("Skewness", "skewness"), ("Kurtosis", "kurtosis"),
        ],
        "TABLE_MA_RATIO": [
            ("MA_Ratio_5", "ma_ratio_5"), ("MA_Ratio_10", "ma_ratio_10"),
            ("MA_Ratio_20", "ma_ratio_20"), ("MA_Ratio_60", "ma_ratio_60"),
            ("MA_Ratio_200", "ma_ratio_200"), ("MA200", "ma200"),
            ("MA30W", "ma30w"), ("MA75W", "ma75w"),
            ("MA_Ratio_30W_75W", "ma_ratio_30w_75w"),
            ("MA_Ratio_5W_30W", "ma_ratio_5w_30w"),
        ],
    }

    def _factor_table_specs(self) -> List[tuple]:
        """返回 [(table_name, field_pairs), ...]，供批量遍历使用"""
        return [
            (getattr(self, key), pairs)
            for key, pairs in self._FACTOR_FIELD_MAP.items()
        ]

    def _indicator_to_row(self, indicator: KlineIndicator,
                          field_pairs: list) -> dict:
        """通用：根据字段映射把 KlineIndicator 转成一行 dict"""
        data = {"Date": indicator.date}
        for col, attr in field_pairs:
            data[col] = getattr(indicator, attr, None)
        return self._round_factor(data)

    # ---------- 公开 parse_xxx（保留旧接口，委托到通用实现）----------

    def parse_indicator(self, indicator: KlineIndicator) -> dict:
        return self._indicator_to_row(indicator, self._FACTOR_FIELD_MAP["TABLE_INDICATOR"])

    def parse_trend(self, indicator: KlineIndicator) -> dict:
        return self._indicator_to_row(indicator, self._FACTOR_FIELD_MAP["TABLE_TREND"])

    def parse_momentum(self, indicator: KlineIndicator) -> dict:
        return self._indicator_to_row(indicator, self._FACTOR_FIELD_MAP["TABLE_MOMENTUM"])

    def parse_volume(self, indicator: KlineIndicator) -> dict:
        return self._indicator_to_row(indicator, self._FACTOR_FIELD_MAP["TABLE_VOLUME"])

    def parse_risk(self, indicator: KlineIndicator) -> dict:
        return self._indicator_to_row(indicator, self._FACTOR_FIELD_MAP["TABLE_RISK"])

    def parse_ma_ratio(self, indicator: KlineIndicator) -> dict:
        return self._indicator_to_row(indicator, self._FACTOR_FIELD_MAP["TABLE_MA_RATIO"])

    # ============================================================
    # 因子表 - 写入函数（单条 / 批量）
    # ============================================================

    def _write_factor(self, table: str, name: str, parsed: dict):
        parsed["Symbol"] = name
        self._upsert(table, parsed)

    def _write_factor_many(self, table: str, name: str,
                           indicators: List[KlineIndicator],
                           field_pairs: list):
        """批量写一张因子表（一次事务）"""
        rows = []
        for ind in indicators:
            if not ind.date:
                continue
            row = self._indicator_to_row(ind, field_pairs)
            row["Symbol"] = name
            rows.append(row)
        self._upsert_many(table, rows)

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
        """一次性写入所有因子表（单条版，保留旧接口）。"""
        for table, pairs in self._factor_table_specs():
            row = self._indicator_to_row(indicator, pairs)
            row["Symbol"] = name
            self._upsert(table, row)

    def write_all_indicators_many(self, name: str,
                                  indicators: List[KlineIndicator]):
        """批量写入所有因子表（推荐：每张表一次 executemany + commit）。"""
        for table, pairs in self._factor_table_specs():
            self._write_factor_many(table, name, indicators, pairs)

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
            _log.warning("get_stock_ratio_data error: %s", e)
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
            _log.warning("cross_section_rank error: %s", e)
            return []
