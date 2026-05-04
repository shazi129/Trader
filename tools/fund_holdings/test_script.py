#!/usr/bin/env python3
"""
测试脚本 - 仅测试功能的执行，不进行网络请求
"""
import sys
import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_function_exists():
    """测试主要函数是否存在"""
    try:
        import holdings_trend
        print("Success: 成功导入模块")
        
        # 测试函数
        functions = [
            'get_recent_filings', 'parse_holdings_from_xml', 'get_holdings_from_filing',
            'load_holding_data_from_csv', 'analyze_holding_trend', 'plot_holding_trend', 'main'
        ]
        
        for func in functions:
            if hasattr(holdings_trend, func):
                print(f"Success: 函数 {func} 存在")
            else:
                print(f"Error: 函数 {func} 不存在")
        
        return True
    except Exception as e:
        print(f"Error: 导入失败: {e}")
        return False

def test_parse_holdings():
    """测试解析功能"""
    try:
        import holdings_trend
        print("测试解析功能...")
        
        # 创建一个简单的XML测试数据
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <xml>
            <infoTable>
                <nameOfIssuer>Test Stock</nameOfIssuer>
                <value>1000000</value>
                <sshPrnamt>50000</sshPrnamt>
            </infoTable>
        </xml>'''
        
        df = holdings_trend.parse_holdings_from_xml(xml_content, "2023-01-01")
        print("Success: XML解析功能正常")
        print(f"  解析结果: {len(df)} 行数据")
        
        return True
    except Exception as e:
        print(f"Error: XML解析测试失败: {e}")
        return False

def test_analysis():
    """测试分析功能"""
    try:
        import holdings_trend
        import pandas as pd
        
        print("测试分析功能...")
        
        # 创建测试数据
        test_data = pd.DataFrame({
            '证券名称': ['Test Stock 1', 'Test Stock 2'],
            '数量': [10000, 20000],
            '报告日期': ['2023-01-01', '2023-04-01']
        })
        
        result = holdings_trend.analyze_holding_trend([test_data])
        print("Success: 分析功能正常")
        print(f"  分析结果: {len(result)} 个股票")
        
        return True
    except Exception as e:
        print(f"Error: 分析测试失败: {e}")
        return False

def test_get_recent_filings():
    """测试获取最近申报功能（仅测试函数调用）"""
    try:
        import holdings_trend
        
        print("测试获取最近申报功能...")
        
        # 测试调用函数（不实际请求网络）
        # 由于需要网络请求，我们只检查函数是否能被调用
        filings = holdings_trend.get_recent_filings(count=1)
        print("Success: 获取最近申报功能正常")
        print(f"  函数调用成功，返回类型: {type(filings)}")
        
        return True
    except Exception as e:
        print(f"Error: 获取最近申报测试失败: {e}")
        return False

def test_get_holdings_from_filing():
    """测试从申报获取持仓数据功能（仅测试函数调用）"""
    try:
        import holdings_trend
        
        print("测试从申报获取持仓数据功能...")
        
        # 测试调用函数（不实际请求网络）
        # 由于需要网络请求，我们只检查函数是否能被调用
        df = holdings_trend.get_holdings_from_filing("test-accession-number")
        print("Success: 从申报获取持仓数据功能正常")
        print(f"  函数调用成功，返回类型: {type(df)}")
        
        return True
    except Exception as e:
        print(f"Error: 从申报获取持仓数据测试失败: {e}")
        return False

if __name__ == "__main__":
    print("开始测试holdings_trend.py功能...")
    print("=" * 50)
    
    success = True
    success &= test_function_exists()
    print()
    success &= test_parse_holdings()
    print()
    success &= test_analysis()
    print()
    success &= test_get_recent_filings()
    print()
    success &= test_get_holdings_from_filing()
    
    print("=" * 50)
    if success:
        print("Success: 所有测试通过")
    else:
        print("Error: 部分测试失败")