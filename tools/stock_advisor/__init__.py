# -*- coding: utf-8 -*-
"""股票综合分析工具 stock_advisor。

入口：``python -m tools.stock_advisor.stock_advisor <stock_name>``

流程：
1. 用户指定一只股票（``name_key``）
2. 从行情仓储读 K 线、从量化仓储读特征快照
3. 特征落后于行情时，通过 ``FeatureCalculator`` 统一重算并写回
4. 用 ``QuantitativeAnalysisService`` 判断形态；用 ``HorizonBacktester`` 跑
   历史相似态匹配，得出 5/20/60 日上涨概率
5. 输出 markdown 到 ``tools/stock_advisor/reports/``
"""

from .backtester import HorizonBacktester, HorizonForecast  # noqa: F401

__all__ = ["HorizonBacktester", "HorizonForecast"]
