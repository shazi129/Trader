# -*- coding: utf-8 -*-
"""因子结果数据模型。

把原本 175 行的"上帝对象" `KlineIndicator` 按因子类别切成 6 组
dataclass mixin，再用多继承组装成同名类。对外行为完全兼容：

- 仍然可以 ``KlineIndicator()`` 无参构造
- 所有字段名一字不差（``ma5`` / ``adx`` / ``obv`` / ``hv20`` ...）
- ``getattr(ind, attr)`` 访问保持不变（数据库写入层依赖此方式）

模块划分：

- ``basic``     : MA / 布林 / KDJ / MACD / RSI / ADOSC
- ``trend``     : EMA / MACD_HIST / ADX / ATR
- ``momentum``  : MOM / ROC / CCI / Williams %R
- ``volume``    : OBV / VPT / ADL / MFI / Force Index
- ``risk``      : HV / 最大回撤 / Sharpe / Sortino / Calmar / 偏度 / 峰度 / Volatility
- ``ma_ratio``  : MA_Ratio_5/10/20/60/200 / MA200 / 周线均线
"""

from __future__ import annotations

from .kline_indicator import KlineIndicator
from .basic import BasicFields
from .trend import TrendFields
from .momentum import MomentumFields
from .volume import VolumeFields
from .risk import RiskFields
from .ma_ratio import MARatioFields

__all__ = [
    "KlineIndicator",
    "BasicFields",
    "TrendFields",
    "MomentumFields",
    "VolumeFields",
    "RiskFields",
    "MARatioFields",
]
