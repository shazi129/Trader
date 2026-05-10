# -*- coding: utf-8 -*-
"""KlineIndicator —— 多组因子字段的总装类。

历史背景：原 ``KlineIndicator`` 是一个 175 行的"上帝对象"，把 60+
字段平铺在一个类中。本次重构把字段按业务类别拆成 6 个 mixin
dataclass，再用多继承（基于 ``@dataclass``）组装回同名类，对外行为
完全兼容：

- 仍然可以 ``KlineIndicator()`` 无参构造（所有字段都有默认值 0.0）
- 所有原字段名保留不变（``ma5`` / ``adx`` / ``obv`` ...）
- 通过 ``getattr(ind, attr)`` 访问的代码不需任何改动
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Dict

from .basic import BasicFields
from .trend import TrendFields
from .momentum import MomentumFields
from .volume import VolumeFields
from .risk import RiskFields
from .ma_ratio import MARatioFields


@dataclass
class KlineIndicator(
    BasicFields,
    TrendFields,
    MomentumFields,
    VolumeFields,
    RiskFields,
    MARatioFields,
):
    """k 线参数信息（单日全部因子的载体）。"""

    date: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """把所有字段平铺成 dict，便于序列化或调试。"""
        return {f.name: getattr(self, f.name) for f in fields(self)}
