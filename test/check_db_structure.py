#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看数据库表结构"""

import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'stock_data.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 获取所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print(f"数据库中的所有表 (共{len(tables)}个):\n")

for table in tables:
    table_name = table[0]
    print(f"{'='*60}")
    print(f"表名: {table_name}")
    print(f"{'='*60}")
    
    # 获取表结构
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    print("字段结构:")
    print(f"  {'ID':<5} {'字段名':<20} {'类型':<15} {'允许NULL':<10} {'默认值':<15} {'主键':<5}")
    print(f"  {'-'*5} {'-'*20} {'-'*15} {'-'*10} {'-'*15} {'-'*5}")
    
    for col in columns:
        cid, name, type_, notnull, dflt_value, pk = col
        null_allowed = "NO" if notnull else "YES"
        pk_str = "YES" if pk else "NO"
        print(f"  {cid:<5} {name:<20} {type_:<15} {null_allowed:<10} {str(dflt_value):<15} {pk_str:<5}")
    
    # 获取记录数
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    print(f"\n记录数: {count}")
    
    # 显示前3条记录
    if count > 0:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
        rows = cursor.fetchall()
        print(f"\n前3条记录示例:")
        for i, row in enumerate(rows, 1):
            print(f"  {i}. {row}")
    
    print()

conn.close()
print("\n完成！")
