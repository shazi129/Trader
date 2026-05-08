#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check database table structure (English output)"""

import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'stock_data.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print(f"Total tables in database: {len(tables)}\n")

# Group tables by stock name
stock_tables = {}
for table in tables:
    table_name = table[0]
    # Extract stock name (part before _ or the whole name if no _)
    if '_' in table_name:
        stock_name = table_name.split('_')[0]
    else:
        stock_name = table_name
    
    if stock_name not in stock_tables:
        stock_tables[stock_name] = []
    stock_tables[stock_name].append(table_name)

# Print grouped tables
for stock_name in sorted(stock_tables.keys()):
    print(f"{'='*70}")
    print(f"Stock: {stock_name}")
    print(f"{'='*70}")
    
    for table_name in sorted(stock_tables[stock_name]):
        # Get record count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        
        # Get latest date
        try:
            cursor.execute(f"SELECT Date FROM {table_name} ORDER BY Date DESC LIMIT 1")
            latest = cursor.fetchone()
            latest_str = latest[0] if latest else "N/A"
        except:
            latest_str = "N/A"
        
        # Get earliest date
        try:
            cursor.execute(f"SELECT Date FROM {table_name} ORDER BY Date ASC LIMIT 1")
            earliest = cursor.fetchone()
            earliest_str = earliest[0] if earliest else "N/A"
        except:
            earliest_str = "N/A"
        
        print(f"  Table: {table_name:<30} | Records: {count:>6} | Date range: {earliest_str} ~ {latest_str}")
    
    print()

conn.close()
print("Done!")
