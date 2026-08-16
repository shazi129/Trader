# -*- coding: utf-8 -*-
"""database 模块单元测试

覆盖 StockDB 的所有核心功能：
1. 建表 / 删表
2. K 线数据写入 / 读取
3. 因子数据写入
4. 查询功能
5. 精度控制
6. 边界条件
7. 多股票隔离性
"""

import os
import sys
import pytest

# 将项目根目录加入 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from database.stock_db_utils import StockDB
from quote_api.quote_base import DailyQuote
from quantitative.factor_data import KlineIndicator


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def db_path(tmp_path):
    """返回临时 db 文件路径，测试结束后自动清理"""
    return str(tmp_path / "test_stock.db")


@pytest.fixture
def db(db_path):
    """创建一个 StockDB 实例，测试结束后自动关闭"""
    db = StockDB(db_path)
    yield db
    db.close()


def make_kline(date, open_price, close_price, high=None, low=None,
                volume=1000000, turnover=100000000, turnover_rate=1.5):
    """快速构造一条日 K 线（统一使用 DailyQuote 模型）"""
    q = DailyQuote()
    q.date = date
    q.open = open_price
    q.close = close_price
    q.high = high or close_price
    q.low = low or open_price
    q.volume = volume
    q.turnover = turnover
    # DailyQuote 没有原生 turnover_rate，但 StockDB.parse_kline 用 getattr 兜底取
    q.turnover_rate = turnover_rate
    return q


def make_indicator(date="2026-05-09"):
    """快速构造 KlineIndicator 对象（只设置部分字段，其余保持 0）"""
    ind = KlineIndicator()
    ind.date = date
    # 基础指标
    ind.ma5 = 100.0
    ind.ma10 = 101.0
    ind.ma20 = 102.0
    ind.ma30 = 103.0
    ind.ma60 = 104.0
    ind.ma120 = 105.0
    ind.ma250 = 106.0
    ind.boll_up = 110.0
    ind.boll_low = 90.0
    ind.k = 50.0
    ind.d = 45.0
    ind.j = 60.0
    ind.dif = 1.0
    ind.dea = 0.5
    ind.macd = 0.5
    ind.rsi1 = 55.0
    ind.rsi2 = 50.0
    ind.rsi3 = 52.0
    ind.adosc = 1000.0
    # 趋势因子
    ind.ema12 = 100.0
    ind.ema26 = 102.0
    ind.ema50 = 105.0
    ind.macd_hist = 0.5
    ind.adx = 25.0
    ind.plus_di = 30.0
    ind.minus_di = 20.0
    ind.tr = 1.5
    ind.atr = 1.2
    ind.atr_pct = 1.2
    # 动量因子
    ind.mom1w = 0.01
    ind.mom2w = 0.02
    ind.mom1m = 0.05
    ind.mom3m = 0.10
    ind.mom6m = 0.20
    ind.mom9m = 0.30
    ind.mom12m = 0.40
    ind.roc1w = 0.01
    ind.roc2w = 0.02
    ind.roc1m = 0.05
    ind.roc3m = 0.10
    ind.roc6m = 0.20
    ind.roc9m = 0.30
    ind.roc12m = 0.40
    ind.cci = 50.0
    ind.williams_r = -20.0
    # 成交量因子
    ind.obv = 1000000.0
    ind.vpt = 2000000.0
    ind.adl = 3000000.0
    ind.mfi = 50.0
    ind.force_index1 = 1000.0
    ind.force_index13 = 13000.0
    ind.force_index21 = 21000.0
    # 风险因子
    ind.hv20 = 0.2
    ind.hv60 = 0.25
    ind.max_drawdown = -0.1
    ind.volatility = 0.2
    ind.sharpe = 1.5
    ind.sortino = 2.0
    ind.calmar = 1.8
    ind.skewness = 0.1
    ind.kurtosis = 3.0
    # 均线比率
    ind.ma_ratio_5 = 1.01
    ind.ma_ratio_10 = 1.02
    ind.ma_ratio_20 = 1.05
    ind.ma_ratio_60 = 1.10
    ind.ma_ratio_200 = 1.20
    ind.ma200 = 90.0
    ind.ma30w = 95.0
    ind.ma75w = 90.0
    ind.ma_ratio_30w_75w = 1.05
    ind.ma_ratio_5w_30w = 1.02
    return ind


def get_table_names(db):
    """查询当前数据库中所有用户表的名称"""
    db._cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )
    return [row[0] for row in db._cursor.fetchall()]


def get_index_names(db):
    """查询当前数据库中所有索引的名称"""
    db._cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
    )
    return [row[0] for row in db._cursor.fetchall()]


# ============================================================
# 测试类
# ============================================================

class TestTableCreation:
    """测试建表功能"""

    def test_tables_created_on_init(self, db):
        """StockDB 初始化时应创建全部长表和财报事件表。"""
        assert set(get_table_names(db)) == {
            *db._TABLE_SCHEMA.keys(),
            db.TABLE_FINANCIAL,
        }

    def test_table_columns_kline(self, db):
        """kline_daily 表的列应正确"""
        db._cursor.execute("PRAGMA table_info(kline_daily)")
        cols = {row[1] for row in db._cursor.fetchall()}
        assert "Symbol" in cols
        assert "Date" in cols
        assert "Open" in cols
        assert "Close" in cols
        assert "High" in cols
        assert "Low" in cols
        assert "Volume" in cols
        assert "Turnover" in cols
        assert "TurnoverRate" in cols
        # PE 应已被移除
        assert "PE" not in cols

    def test_date_index_created(self, db):
        """每张日频长表应有 Date 索引。"""
        for table in db._TABLE_SCHEMA:
            idx_name = f"idx_{table}_date"
            assert idx_name in get_index_names(db), f"索引 {idx_name} 未被创建"

    def test_create_idempotent(self, db):
        """重复调用 _ensure_schema 不应报错"""
        try:
            db._ensure_schema()
        except Exception as e:
            pytest.fail(f"重复建表抛出异常: {e}")


class TestDropAllTables:
    """测试删表功能"""

    def test_drop_all_tables(self, db):
        """drop_all_tables 应删除所有长表"""
        assert set(get_table_names(db)) == {
            *db._TABLE_SCHEMA.keys(),
            db.TABLE_FINANCIAL,
        }
        db.drop_all_tables()
        assert get_table_names(db) == [db.TABLE_FINANCIAL]

    def test_drop_then_recreate(self, db):
        """删表后应能重新建表"""
        db.drop_all_tables()
        assert get_table_names(db) == [db.TABLE_FINANCIAL]
        db._ensure_schema()
        assert set(get_table_names(db)) == {
            *db._TABLE_SCHEMA.keys(),
            db.TABLE_FINANCIAL,
        }

    def test_drop_idempotent(self, db):
        """对空库重复删表不报错"""
        db.drop_all_tables()
        try:
            db.drop_all_tables()
        except Exception as e:
            pytest.fail(f"重复删表抛出异常: {e}")

    def test_drop_removes_indexes(self, db):
        """删表应同时删除索引"""
        assert set(get_index_names(db)) == {
            *(f"idx_{table}_date" for table in db._TABLE_SCHEMA),
            f"idx_{db.TABLE_FINANCIAL}_announce",
        }
        db.drop_all_tables()
        assert get_index_names(db) == [f"idx_{db.TABLE_FINANCIAL}_announce"]


class TestKlineWrite:
    """测试 K 线数据写入"""

    def test_write_kline_single(self, db):
        """写入单条 K 线，行数应 +1"""
        kline = make_kline("2026-05-09", 100.0, 101.0)
        db.write_kline_data("000001", kline)
        assert db.get_row_count("000001") == 1

    def test_write_kline_many(self, db):
        """批量写入多条 K 线"""
        klines = [
            make_kline("2026-05-09", 100.0, 101.0),
            make_kline("2026-05-10", 101.0, 102.0),
            make_kline("2026-05-11", 102.0, 103.0),
        ]
        db.write_kline_data_many("000001", klines)
        assert db.get_row_count("000001") == 3

    def test_write_kline_upsert(self, db):
        """相同 Symbol + Date 应替换，不是新增"""
        k1 = make_kline("2026-05-09", 100.0, 101.0)
        k2 = make_kline("2026-05-09", 100.0, 102.0)  # 相同日期，不同收盘价
        db.write_kline_data("000001", k1)
        db.write_kline_data("000001", k2)
        assert db.get_row_count("000001") == 1
        # 验证数据已被替换
        db._cursor.execute(
            "SELECT Close FROM kline_daily WHERE Symbol=? AND Date=?",
            ("000001", "2026-05-09"),
        )
        assert db._cursor.fetchone()[0] == pytest.approx(102.0, abs=0.0001)


class TestKlineRead:
    """测试 K 线数据读取"""

    def test_get_latest_date(self, db):
        """获取最新日期"""
        db.write_kline_data("000001", make_kline("2026-05-09", 100.0, 101.0))
        db.write_kline_data("000001", make_kline("2026-05-10", 101.0, 102.0))
        assert db.get_latest_date("000001") == "2026-05-10"

    def test_get_latest_date_empty(self, db):
        """空表查询最新日期应返回 None"""
        assert db.get_latest_date("999999") is None

    def test_get_latest_klines(self, db):
        """获取最新的 N 条 K 线"""
        for i in range(5):
            db.write_kline_data(
                "000001",
                make_kline(f"2026-05-0{i+1}", 100.0 + i, 101.0 + i),
            )
        result = db.get_latest_klines("000001", 3)
        assert len(result) == 3
        assert result[0].date == "2026-05-05"
        assert result[1].date == "2026-05-04"
        assert result[2].date == "2026-05-03"

    def test_get_klines_in_range(self, db):
        """按日期区间查询 K 线"""
        for i in range(5):
            db.write_kline_data(
                "000001",
                make_kline(f"2026-05-0{i+1}", 100.0 + i, 101.0 + i),
            )
        result = db.get_klines_in_range("000001", "2026-05-02", "2026-05-04")
        assert len(result) == 3
        assert result[0].date == "2026-05-02"
        assert result[-1].date == "2026-05-04"

    def test_get_klines_in_range_open(self, db):
        """开区间查询（只有开始日期）"""
        for i in range(5):
            db.write_kline_data(
                "000001",
                make_kline(f"2026-05-0{i+1}", 100.0 + i, 101.0 + i),
            )
        result = db.get_klines_in_range("000001", start_date="2026-05-03")
        assert len(result) == 3
        assert result[0].date == "2026-05-03"

    def test_get_klines_in_range_close(self, db):
        """开区间查询（只有结束日期）"""
        for i in range(5):
            db.write_kline_data(
                "000001",
                make_kline(f"2026-05-0{i+1}", 100.0 + i, 101.0 + i),
            )
        result = db.get_klines_in_range("000001", end_date="2026-05-03")
        assert len(result) == 3
        assert result[-1].date == "2026-05-03"


class TestKlinePrecision:
    """测试 K 线数据精度控制（价格保留 4 位小数）"""

    def test_write_kline_precision(self, db):
        """价格应保留 4 位小数"""
        kline = make_kline("2026-05-09", 100.12345, 101.56789)
        db.write_kline_data("000001", kline)

        db._cursor.execute(
            "SELECT Open, Close, High, Low, Turnover FROM kline_daily WHERE Symbol=? AND Date=?",
            ("000001", "2026-05-09"),
        )
        row = db._cursor.fetchone()
        assert row[0] == pytest.approx(100.1235, abs=0.0001)
        assert row[1] == pytest.approx(101.5679, abs=0.0001)
        assert row[2] == pytest.approx(101.5679, abs=0.0001)
        assert row[3] == pytest.approx(100.1235, abs=0.0001)
        assert row[4] == pytest.approx(100000000.0, abs=0.0001)

    def test_round_kline_helper(self, db):
        """_round_kline 辅助方法应正确四舍五入"""
        data = {"Open": 100.12345, "Close": 101.56789, "Turnover": 123.45678}
        rounded = db._round_kline(data)
        assert rounded["Open"] == pytest.approx(100.1235, abs=0.0001)
        assert rounded["Close"] == pytest.approx(101.5679, abs=0.0001)
        assert rounded["Turnover"] == pytest.approx(123.4568, abs=0.0001)


class TestFactorWrite:
    """测试因子数据写入（所有 6 张因子表）"""

    def test_write_indicator(self, db):
        ind = make_indicator()
        db.write_indicator_data("000001", ind)
        assert db.get_row_count("000001", db.TABLE_INDICATOR) == 1

    def test_write_trend(self, db):
        ind = make_indicator()
        db.write_trend_data("000001", ind)
        assert db.get_row_count("000001", db.TABLE_TREND) == 1

    def test_write_momentum(self, db):
        ind = make_indicator()
        db.write_momentum_data("000001", ind)
        assert db.get_row_count("000001", db.TABLE_MOMENTUM) == 1

    def test_write_volume(self, db):
        ind = make_indicator()
        db.write_volume_data("000001", ind)
        assert db.get_row_count("000001", db.TABLE_VOLUME) == 1

    def test_write_risk(self, db):
        ind = make_indicator()
        db.write_risk_data("000001", ind)
        assert db.get_row_count("000001", db.TABLE_RISK) == 1

    def test_write_ma_ratio(self, db):
        ind = make_indicator()
        db.write_ma_ratio_data("000001", ind)
        assert db.get_row_count("000001", db.TABLE_MA_RATIO) == 1

    def test_write_all_indicators(self, db):
        """一次性写入所有因子"""
        ind = make_indicator()
        db.write_all_indicators("000001", ind)
        counts = db.get_stock_row_counts("000001")
        assert counts["indicator"] == 1
        assert counts["trend"] == 1
        assert counts["momentum"] == 1
        assert counts["volume"] == 1
        assert counts["risk"] == 1
        assert counts["ma_ratio"] == 1

    def test_factor_precision(self, db):
        """因子数据应保留 6 位小数"""
        ind = make_indicator()
        ind.ma5 = 100.1234567
        db.write_indicator_data("000001", ind)

        db._cursor.execute(
            "SELECT MA5 FROM factor_indicator WHERE Symbol=? AND Date=?",
            ("000001", ind.date),
        )
        row = db._cursor.fetchone()
        assert row[0] == pytest.approx(100.123457, abs=0.000001)


class TestQueries:
    """测试查询功能"""

    def test_get_row_count_empty(self, db):
        """空表查询行数应返回 0"""
        assert db.get_row_count("999999") == 0

    def test_list_symbols(self, db):
        """列出所有股票代码"""
        db.write_kline_data("000001", make_kline("2026-05-09", 100.0, 101.0))
        db.write_kline_data("000002", make_kline("2026-05-09", 200.0, 201.0))
        symbols = db.list_symbols()
        assert set(symbols) == {"000001", "000002"}

    def test_list_symbols_empty(self, db):
        """空表查询 symbol 列表应返回空列表"""
        assert db.list_symbols() == []

    def test_get_stock_row_counts(self, db):
        """查询股票在各表中的行数"""
        db.write_kline_data("000001", make_kline("2026-05-09", 100.0, 101.0))
        db.write_indicator_data("000001", make_indicator())
        counts = db.get_stock_row_counts("000001")
        assert counts["raw"] == 1
        assert counts["indicator"] == 1

    def test_get_stock_ratio_data(self, db):
        """测试股价比值查询"""
        db.write_kline_data("000001", make_kline("2026-05-09", 100.0, 101.0))
        db.write_kline_data("000002", make_kline("2026-05-09", 200.0, 202.0))
        result = db.get_stock_ratio_data("000001", "000002")  # 101 / 202
        assert len(result) == 1
        assert result[0].value == pytest.approx(101 / 202, abs=0.001)

    def test_get_stock_ratio_data_divide_by_zero(self, db):
        """除数为 0 时应不报错并返回空列表"""
        db.write_kline_data("000001", make_kline("2026-05-09", 100.0, 101.0))
        db.write_kline_data("000002", make_kline("2026-05-09", 200.0, 0.0))
        result = db.get_stock_ratio_data("000001", "000002")
        assert result == []

    def test_cross_section_rank(self, db):
        """横截面排序（按 Close 降序）"""
        db.write_kline_data("000001", make_kline("2026-05-09", 100.0, 101.0))
        db.write_kline_data("000002", make_kline("2026-05-09", 200.0, 201.0))
        db.write_kline_data("000003", make_kline("2026-05-09", 50.0, 51.0))
        result = db.cross_section_rank("kline_daily", "Close", "2026-05-09", top_n=2)
        assert len(result) == 2
        assert result[0][0] == "000002"  # Close=201 最高
        assert result[1][0] == "000001"  # Close=101 第二

    def test_cross_section_rank_ascending(self, db):
        """横截面排序（升序）"""
        db.write_kline_data("000001", make_kline("2026-05-09", 100.0, 101.0))
        db.write_kline_data("000002", make_kline("2026-05-09", 200.0, 201.0))
        result = db.cross_section_rank(
            "kline_daily", "Close", "2026-05-09", top_n=2, ascending=True
        )
        assert result[0][0] == "000001"  # Close=101 最低
        assert result[1][0] == "000002"  # Close=201 第二低


class TestEdgeCases:
    """测试边界条件"""

    def test_write_kline_none_values(self, db):
        """写入包含 None 的数据应不报错"""
        q = DailyQuote()
        q.date = "2026-05-09"
        q.open = None
        q.close = 100.0
        q.high = None
        q.low = None
        q.volume = None
        q.turnover = None
        q.turnover_rate = None
        try:
            db.write_kline_data("000001", q)
        except Exception as e:
            pytest.fail(f"写入 None 值抛出异常: {e}")

    def test_write_kline_empty_date(self, db):
        """日期为空字符串时应不报错（SQLite 会接受）"""
        k = make_kline("", 100.0, 101.0)
        try:
            db.write_kline_data("000001", k)
        except Exception as e:
            pytest.fail(f"日期为空时抛出异常: {e}")

    def test_compatible_api(self, db):
        """兼容旧 API：get_raw_table_name 等应返回正确的表名"""
        assert db.get_raw_table_name("000001") == "kline_daily"
        assert db.get_indicator_table_name("000001") == "factor_indicator"
        assert db.get_trend_table_name("000001") == "factor_trend"

    def test_compatible_api_create_all_tables_noop(self, db):
        """兼容旧 API：create_all_tables 应不报错（no-op）"""
        try:
            db.create_all_tables("000001")
        except Exception as e:
            pytest.fail(f"create_all_tables 抛出异常: {e}")


class TestMultiSymbol:
    """测试多股票隔离性"""

    def test_symbols_isolated(self, db):
        """不同股票的数据应隔离"""
        db.write_kline_data("000001", make_kline("2026-05-09", 100.0, 101.0))
        db.write_kline_data("000002", make_kline("2026-05-09", 200.0, 201.0))
        assert db.get_row_count("000001") == 1
        assert db.get_row_count("000002") == 1
        assert db.get_latest_date("000001") == "2026-05-09"
        assert db.get_latest_date("000002") == "2026-05-09"

    def test_same_date_diff_symbols(self, db):
        """相同日期不同股票应分别存储"""
        db.write_kline_data("000001", make_kline("2026-05-09", 100.0, 101.0))
        db.write_kline_data("000002", make_kline("2026-05-09", 200.0, 201.0))
        assert db.get_row_count("000001") == 1
        assert db.get_row_count("000002") == 1
        # 总表行数应为 2
        db._cursor.execute("SELECT COUNT(*) FROM kline_daily")
        total = db._cursor.fetchone()[0]
        assert total == 2

    def test_factor_data_isolated(self, db):
        """不同股票的因子数据应隔离"""
        ind1 = make_indicator()
        ind2 = make_indicator()
        db.write_indicator_data("000001", ind1)
        db.write_indicator_data("000002", ind2)
        assert db.get_row_count("000001", db.TABLE_INDICATOR) == 1
        assert db.get_row_count("000002", db.TABLE_INDICATOR) == 1
