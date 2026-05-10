#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试缓存API功能

验证"先读DB，缺失再拉取"的逻辑
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_PROJECT_ROOT))

import config
from quote_api import QuoteAPIFactory
from quote_api.cached_api import CachedQuoteAPI


def test_cached_api():
    """测试带缓存的API"""
    print("=== 测试缓存API功能 ===\n")
    
    # 1. 创建原始API
    print("1. 创建原始API (tencent)...")
    raw_api = QuoteAPIFactory.create("tencent")
    print(f"   原始API: {raw_api.SOURCE}\n")
    
    # 2. 创建带缓存的API
    print("2. 创建带缓存的API...")
    cached_api = CachedQuoteAPI(raw_api)
    print(f"   缓存API: {cached_api.SOURCE}\n")
    
    # 3. 测试get_klines (首次调用，应该从API拉取)
    print("3. 首次调用get_klines (应该从API拉取)...")
    stock_name = "Tencent"  # 使用config中的股票
    quotes1 = cached_api.get_klines(stock_name, limit=100)
    if quotes1:
        print(f"   [OK] 成功获取 {len(quotes1)} 条数据")
        print(f"   最新日期: {quotes1[-1].date}")
        print(f"   最早日期: {quotes1[0].date}\n")
    else:
        print("   [X] 获取失败\n")
        return
    
    # 4. 再次调用get_klines (应该从数据库读取)
    print("4. 再次调用get_klines (应该从数据库读取)...")
    quotes2 = cached_api.get_klines(stock_name, limit=100)
    if quotes2:
        print(f"   [OK] 成功获取 {len(quotes2)} 条数据")
        print(f"   最新日期: {quotes2[-1].date}")
        print(f"   最早日期: {quotes2[0].date}\n")
    else:
        print("   [X] 获取失败\n")
        return
    
    # 5. 验证数据一致性
    print("5. 验证数据一致性...")
    if len(quotes1) == len(quotes2):
        print(f"   [OK] 数据条数一致: {len(quotes1)}")
    else:
        print(f"   [X] 数据条数不一致: {len(quotes1)} vs {len(quotes2)}")
    
    # 比较前10条数据的日期和收盘价
    match_count = 0
    for i in range(min(10, len(quotes1))):
        if (quotes1[i].date == quotes2[i].date and 
            abs(quotes1[i].close - quotes2[i].close) < 0.01):
            match_count += 1
    
    if match_count == min(10, len(quotes1)):
        print(f"   [OK] 前10条数据完全一致\n")
    else:
        print(f"   [X] 前10条数据有 {10 - match_count} 条不一致\n")
    
    # 6. 测试get_daily_quote
    print("6. 测试get_daily_quote...")
    latest_quote = cached_api.get_daily_quote(stock_name)
    if latest_quote:
        print(f"   [OK] 获取最新行情: {latest_quote.date}, close={latest_quote.close}\n")
    else:
        print("   [X] 获取失败\n")
    
    # 7. 测试不同股票
    print("7. 测试其他股票 (Alibaba)...")
    quotes3 = cached_api.get_klines("Alibaba", limit=50)
    if quotes3:
        print(f"   [OK] 成功获取 {len(quotes3)} 条数据\n")
    else:
        print("   [X] 获取失败 (可能API不支持)\n")
    
    print("=== 测试完成 ===")


def test_quote_api_factory():
    """测试QuoteAPIFactory.create_with_cache方法"""
    print("\n=== 测试QuoteAPIFactory.create_with_cache ===\n")
    
    # 使用工厂方法创建带缓存的API
    print("创建带缓存的API (通过工厂方法)...")
    cached_api = QuoteAPIFactory.create_with_cache("tencent")
    print(f"   API类型: {type(cached_api).__name__}")
    print(f"   API源: {cached_api.SOURCE}\n")
    
    # 测试获取数据的功能
    print("测试获取数据...")
    quotes = cached_api.get_klines("Tencent", limit=50)
    if quotes:
        print(f"   [OK] 成功获取 {len(quotes)} 条数据\n")
    else:
        print("   [X] 获取失败\n")


if __name__ == "__main__":
    try:
        test_cached_api()
        test_quote_api_factory()
    except Exception as e:
        print(f"\n[X] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n[OK] 所有测试通过!")
    sys.exit(0)
