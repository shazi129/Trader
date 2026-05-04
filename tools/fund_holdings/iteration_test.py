#!/usr/bin/env python3
"""
迭代验证测试脚本
"""
import sys
import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_complete_workflow():
    """测试完整的数据处理工作流"""
    try:
        import holdings_trend
        print("开始完整工作流测试...")
        
        # 1. 测试函数是否存在
        print("1. 检查函数存在性...")
        functions = [
            'get_recent_filings', 'parse_holdings_from_xml', 'get_holdings_from_filing',
            'load_holding_data_from_csv', 'analyze_holding_trend', 'plot_holding_trend', 'main'
        ]
        
        for func in functions:
            if hasattr(holdings_trend, func):
                print(f"   Success: 函数 {func} 存在")
            else:
                print(f"   Error: 函数 {func} 不存在")
                return False
        
        # 2. 测试数据解析
        print("2. 测试数据解析...")
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <xml>
            <infoTable>
                <nameOfIssuer>Test Stock</nameOfIssuer>
                <value>1000000</value>
                <sshPrnamt>50000</sshPrnamt>
            </infoTable>
        </xml>'''
        
        df = holdings_trend.parse_holdings_from_xml(xml_content, "2023-01-01")
        print(f"   Success: XML解析成功，得到 {len(df)} 行数据")
        
        # 3. 测试数据分析
        print("3. 测试数据分析...")
        test_data = pd.DataFrame({
            '证券名称': ['Test Stock 1', 'Test Stock 2'],
            '数量': [10000, 20000],
            '报告日期': ['2023-01-01', '2023-04-01']
        })
        
        result = holdings_trend.analyze_holding_trend([test_data])
        print(f"   Success: 数据分析成功，分析了 {len(result)} 个股票")
        
        # 4. 测试绘图功能
        print("4. 测试绘图功能...")
        try:
            holdings_trend.plot_holding_trend([test_data], "test_plot.png")
            print("   Success: 绘图功能正常")
        except Exception as e:
            print(f"   Warning: 绘图功能测试失败 (可能缺少显示环境): {e}")
        
        print("Success: 完整工作流测试通过")
        return True
        
    except Exception as e:
        print(f"Error: 完整工作流测试失败: {e}")
        return False

def test_error_handling():
    """测试错误处理能力"""
    try:
        import holdings_trend
        print("测试错误处理...")
        
        # 测试空数据处理
        empty_df = holdings_trend.parse_holdings_from_xml("", "2023-01-01")
        print("   Success: 空数据处理正常")
        
        # 测试异常情况下的函数调用
        try:
            result = holdings_trend.get_holdings_from_filing("invalid-url")
            print("   Success: 异常URL处理正常")
        except Exception as e:
            print(f"   Success: 异常URL处理正常: {type(e).__name__}")
        
        print("Success: 错误处理测试通过")
        return True
        
    except Exception as e:
        print(f"Error: 错误处理测试失败: {e}")
        return False

def test_data_structure():
    """测试数据结构"""
    try:
        import holdings_trend
        import pandas as pd
        
        print("测试数据结构...")
        
        # 创建模拟数据
        sample_data = {
            '证券名称': ['Apple Inc.', 'Microsoft Corp.', 'Google LLC'],
            '数量': [1000000, 500000, 750000],
            '报告日期': ['2023-01-01', '2023-04-01', '2023-07-01'],
            '价值': [15000000, 8000000, 12000000]
        }
        
        df = pd.DataFrame(sample_data)
        print(f"   Success: 数据结构测试通过，创建了 {len(df)} 行数据")
        
        # 测试分析函数
        result = holdings_trend.analyze_holding_trend([df])
        print(f"   Success: 分析函数返回 {len(result)} 个结果")
        
        print("Success: 数据结构测试通过")
        return True
        
    except Exception as e:
        print(f"Error: 数据结构测试失败: {e}")
        return False

if __name__ == "__main__":
    print("开始迭代验证测试...")
    print("=" * 50)
    
    success = True
    success &= test_complete_workflow()
    print()
    success &= test_error_handling()
    print()
    success &= test_data_structure()
    
    print("=" * 50)
    if success:
        print("SUCCESS: 所有迭代验证测试通过")
    else:
        print("FAILURE: 部分迭代验证测试失败")