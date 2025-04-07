import mplfinance as mpf
 
# 示例数据，通常你会从pandas DataFrame获取这些数据
# 假设df是一个包含'Open', 'High', 'Low', 'Close', 'Volume'的DataFrame
import pandas as pd
import numpy as np
 
# 创建一个示例DataFrame
np.random.seed(42)
dates = pd.date_range('20230101', periods=100)
df = pd.DataFrame({
    'Open': 100 + np.random.normal(0, 10, 100).cumsum(),
    'High': 105 + np.random.normal(0, 5, 100).cumsum(),
    'Low': 95 + np.random.normal(0, 10, 100).cumsum(),
    'Close': 102 + np.random.normal(0, 8, 100).cumsum(),
    'Volume': np.random.randint(100, 1000, 100)
}, index=dates)
 
# 绘制K线图
mpf.plot(df, type='candle', style='charles', title='Example Candlestick Chart', ylabel='Price')