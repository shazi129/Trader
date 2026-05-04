#!/usr/bin/env python3
"""
简单验证脚本 - 检查holdings_trend.py是否能正常运行
"""
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # 尝试导入工具模块
    import holdings_trend
    print("Success: 成功导入holdings_trend模块")
    
    # 检查主要函数是否存在
    functions = ['get_recent_filings', 'parse_holdings_from_xml', 'get_holdings_from_filing', 
                'load_holding_data_from_csv', 'analyze_holding_trend', 'plot_holding_trend', 'main']
    
    for func in functions:
        if hasattr(holdings_trend, func):
            print(f"Success: 函数 {func} 存在")
        else:
            print(f"Error: 函数 {func} 不存在")
    
    print("\nSuccess: 模块结构检查完成")
    
except ImportError as e:
    print(f"Error: 导入错误: {e}")
except Exception as e:
    print(f"Error: 其他错误: {e}")