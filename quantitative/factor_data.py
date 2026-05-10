# -*- coding: utf-8 -*-
"""向后兼容的 re-export。

原 175 行 "上帝对象" ``KlineIndicator`` 已按因子类别拆分到
``quantitative.factors`` 包下：

- ``factors.basic``     基础指标
- ``factors.trend``     趋势因子
- ``factors.momentum``  动量因子
- ``factors.volume``    成交量因子
- ``factors.risk``      风险因子
- ``factors.ma_ratio``  均线比率
- ``factors.kline_indicator`` 多继承组装的总装类

本模块仅保留 ``KlineIndicator`` 的旧导入路径，外部代码无需修改。
"""

from __future__ import annotations

from quantitative.factors import KlineIndicator

__all__ = ["KlineIndicator"]
