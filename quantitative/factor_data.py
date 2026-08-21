# -*- coding: utf-8 -*-
"""向后兼容的 re-export。

原 175 行 "上帝对象" ``KlineIndicator`` 已按因子类别拆分到
``quantitative.fields`` 包下：

- ``fields.basic``      基础指标
- ``fields.trend``      趋势因子
- ``fields.momentum``   动量因子
- ``fields.volume``     成交量因子
- ``fields.risk``       风险因子
- ``fields.ma_ratio``   均线比率
- ``fields.liquidity``  流动性 / 资金面（B 类，从 K 线派生）
- ``fields.kline_indicator`` 多继承组装的总装类

本模块仅保留 ``KlineIndicator`` 的旧导入路径，外部代码无需修改。
"""

from __future__ import annotations

from quantitative.fields import KlineIndicator

__all__ = ["KlineIndicator"]
