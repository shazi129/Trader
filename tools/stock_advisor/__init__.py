# -*- coding: utf-8 -*-
"""股票综合分析工具 stock_advisor。

入口：``python -m tools.stock_advisor.stock_advisor <stock_name>``

流程：
1. 用户指定一只股票（``name_key``）
2. 从数据库读 K 线 + 6 张因子表
3. 若因子表最新日期 < K 线最新日期，则调用 ``compute_and_save_factors``
   重算并写回；若 K 线本身缺失，先调用 kline_fetcher 抓数据
4. 用 ``QuantAnalyzer`` 出多因子信号判断；用 ``HorizonBacktester`` 跑
   历史相似态匹配，得出 5/20/60 日上涨概率
5. 输出 markdown 到 ``tools/stock_advisor/reports/``
"""

from .backtester import HorizonBacktester, HorizonForecast  # noqa: F401

__all__ = ["HorizonBacktester", "HorizonForecast"]
