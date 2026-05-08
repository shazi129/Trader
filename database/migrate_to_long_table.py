# -*- coding: utf-8 -*-
"""
旧 -> 新 数据库结构迁移脚本

旧结构（每只股票一组分表）：
    Tencent / Tencent_Ind / Tencent_Trend / Tencent_Momentum /
    Tencent_Volume / Tencent_Risk / Tencent_MA_Ratio

新结构（统一长表 + (Symbol, Date) 复合主键）：
    kline_daily / factor_indicator / factor_trend / factor_momentum /
    factor_volume / factor_risk / factor_ma_ratio

用法
----
    python database/migrate_to_long_table.py
    # 或指定路径
    python database/migrate_to_long_table.py --src d:/GitHub/Trader/database/stock_data.db
                                              --dst d:/GitHub/Trader/database/stock_data_new.db

默认行为
--------
1. 把 ``database/stock_data.db`` 备份为 ``stock_data.db.bak_<时间戳>``
2. 在原路径生成新结构数据库（同名覆盖）
3. 把旧表中所有数据按 Symbol 维度搬入新长表，幂等（INSERT OR REPLACE）
"""

from __future__ import annotations

import argparse
import os
import shutil
import sqlite3
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from database.stock_db_utils import StockDB  # noqa: E402


# 旧后缀 -> 新表名 + 旧表的列（不含 Symbol，源是分表所以无）
SUFFIX_MAPPING: List[Tuple[str, str]] = [
    ("",          StockDB.TABLE_KLINE),       # 原始K线（无后缀）
    ("_Ind",      StockDB.TABLE_INDICATOR),
    ("_Trend",    StockDB.TABLE_TREND),
    ("_Momentum", StockDB.TABLE_MOMENTUM),
    ("_Volume",   StockDB.TABLE_VOLUME),
    ("_Risk",     StockDB.TABLE_RISK),
    ("_MA_Ratio", StockDB.TABLE_MA_RATIO),
]

# 新表已知列（用于做列对齐，避免旧表偶尔多/缺一列时炸掉）
NEW_TABLE_COLUMNS: Dict[str, List[str]] = {
    StockDB.TABLE_KLINE:     list(StockDB._kline_columns.keys()),
    StockDB.TABLE_INDICATOR: list(StockDB._indicator_columns.keys()),
    StockDB.TABLE_TREND:     list(StockDB._trend_columns.keys()),
    StockDB.TABLE_MOMENTUM:  list(StockDB._momentum_columns.keys()),
    StockDB.TABLE_VOLUME:    list(StockDB._volume_columns.keys()),
    StockDB.TABLE_RISK:      list(StockDB._risk_columns.keys()),
    StockDB.TABLE_MA_RATIO:  list(StockDB._ma_ratio_columns.keys()),
}


def list_old_tables(conn: sqlite3.Connection) -> List[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    return [r[0] for r in rows]


def parse_old_table_name(table: str) -> Tuple[str, str] | None:
    """把旧表名解析为 (symbol, new_table_name)。无法识别则返回 None。"""
    # 先匹配带后缀的，再匹配无后缀（以避免把 "Tencent_Ind" 当成股票名 "Tencent_Ind"）
    sorted_mapping = sorted(SUFFIX_MAPPING, key=lambda kv: -len(kv[0]))
    for suffix, new_table in sorted_mapping:
        if suffix == "":
            # 任意名都可能是 K 线表，留到最后
            continue
        if table.endswith(suffix):
            symbol = table[: -len(suffix)]
            if symbol:
                return symbol, new_table
    # 走到这里说明是 K 线（无后缀）
    return table, StockDB.TABLE_KLINE


def get_table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    return [r[1] for r in conn.execute(f'PRAGMA table_info("{table}")').fetchall()]


def migrate_table(
    src_conn: sqlite3.Connection,
    dst_conn: sqlite3.Connection,
    src_table: str,
    symbol: str,
    new_table: str,
):
    """把 src_table 的所有行插入到 dst_table，附带 Symbol 列"""
    src_cols = get_table_columns(src_conn, src_table)
    new_cols = NEW_TABLE_COLUMNS[new_table]

    # 取交集列（保持 new_cols 的顺序）；Symbol 单独加
    common_cols = [c for c in new_cols if c != "Symbol" and c in src_cols]
    if "Date" not in common_cols:
        print(f"  [WARN] {src_table}: 没有 Date 列，跳过")
        return 0

    # 读取
    src_rows = src_conn.execute(
        f'SELECT {",".join(common_cols)} FROM "{src_table}"'
    ).fetchall()
    if not src_rows:
        return 0

    # 写入
    insert_cols = ["Symbol"] + common_cols
    placeholders = ",".join(["?"] * len(insert_cols))
    sql = (
        f"INSERT OR REPLACE INTO {new_table}({','.join(insert_cols)}) "
        f"VALUES({placeholders})"
    )
    rows_to_write = [(symbol,) + tuple(row) for row in src_rows]
    dst_conn.executemany(sql, rows_to_write)
    dst_conn.commit()
    return len(rows_to_write)


def migrate(src_path: str, dst_path: str, backup: bool = True):
    src_path = os.path.abspath(src_path)
    dst_path = os.path.abspath(dst_path)
    print(f"[Migrate] 源: {src_path}")
    print(f"[Migrate] 目标: {dst_path}")

    if not os.path.isfile(src_path):
        raise FileNotFoundError(f"源数据库不存在: {src_path}")

    # 备份
    if backup and os.path.abspath(src_path) == os.path.abspath(dst_path):
        ts = time.strftime("%Y%m%d_%H%M%S")
        backup_path = f"{src_path}.bak_{ts}"
        shutil.copy2(src_path, backup_path)
        print(f"[Migrate] 已备份: {backup_path}")

    # 当 src == dst 时，先把源拷到临时位置作为只读源，再重置目标 db
    if os.path.abspath(src_path) == os.path.abspath(dst_path):
        tmp_src = f"{src_path}.migrating_src"
        if os.path.exists(tmp_src):
            os.remove(tmp_src)
        shutil.copy2(src_path, tmp_src)
        os.remove(dst_path)        # 让 StockDB 创建一个全新的长表 db
        real_src = tmp_src
        cleanup_tmp = True
    else:
        real_src = src_path
        cleanup_tmp = False
        if os.path.exists(dst_path):
            print(f"[Migrate] 目标已存在，删除以重建: {dst_path}")
            os.remove(dst_path)

    # 创建新 db（StockDB 会建好所有长表 + 索引）
    db = StockDB(dst_path)

    src_conn = sqlite3.connect(real_src)
    src_conn.text_factory = str

    try:
        # 加速：迁移期间放宽 fsync（用 connection.execute 并 fetchall，避免遗留游标）
        db._connection.execute("PRAGMA synchronous=OFF").fetchall()
        db._connection.execute("PRAGMA journal_mode=MEMORY").fetchall()

        all_tables = list_old_tables(src_conn)
        print(f"[Migrate] 旧库共有 {len(all_tables)} 张表")

        # 优先迁 K 线（无后缀），再迁因子表，避免长后缀股票名（如 Tencent_14136）被错误识别
        # 先把已知后缀的归类，剩下的当成 K 线
        suffix_set = {s for s, _ in SUFFIX_MAPPING if s}
        kline_tables: List[str] = []
        factor_tables: List[Tuple[str, str, str]] = []  # (src_table, symbol, new_table)

        for t in all_tables:
            matched_suffix = None
            for suffix in sorted(suffix_set, key=len, reverse=True):
                if t.endswith(suffix):
                    matched_suffix = suffix
                    break
            if matched_suffix is None:
                kline_tables.append(t)
            else:
                symbol = t[: -len(matched_suffix)]
                new_table = dict(SUFFIX_MAPPING)[matched_suffix]
                if symbol:
                    factor_tables.append((t, symbol, new_table))

        total = 0
        # 1) K 线
        for t in kline_tables:
            n = migrate_table(src_conn, db._connection, t, t, StockDB.TABLE_KLINE)
            print(f"  [Kline]   {t:<30} -> {StockDB.TABLE_KLINE:<18} {n} rows")
            total += n

        # 2) 因子
        for src_t, symbol, new_t in factor_tables:
            n = migrate_table(src_conn, db._connection, src_t, symbol, new_t)
            print(f"  [Factor]  {src_t:<30} -> {new_t:<18} {n} rows  (symbol={symbol})")
            total += n

        print(f"[Migrate] 总计写入: {total} 行")

    finally:
        # 恢复正常 fsync
        try:
            db._connection.execute("PRAGMA synchronous=NORMAL").fetchall()
            db._connection.execute("PRAGMA journal_mode=WAL").fetchall()
        except sqlite3.Error:
            pass
        src_conn.close()
        db.close()
        if cleanup_tmp:
            try:
                os.remove(real_src)
            except OSError:
                pass


def main():
    default_db = str(_HERE / "stock_data.db")
    parser = argparse.ArgumentParser(description="迁移旧分表结构到新长表结构")
    parser.add_argument("--src", default=default_db, help="源数据库路径")
    parser.add_argument("--dst", default=default_db, help="目标数据库路径（默认与源相同，原地迁移）")
    parser.add_argument("--no-backup", action="store_true", help="原地迁移时不创建备份")
    args = parser.parse_args()

    migrate(args.src, args.dst, backup=not args.no_backup)
    print("[Migrate] 完成")


if __name__ == "__main__":
    main()
