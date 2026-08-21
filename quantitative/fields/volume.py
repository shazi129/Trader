# -*- coding: utf-8 -*-
"""成交量类因子字段：OBV / VPT / ADL / MFI / Force Index。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VolumeFields:
    """对应数据表 ``factor_volume``。"""

    obv: float = 0.0
    vpt: float = 0.0
    adl: float = 0.0
    mfi: float = 0.0

    # 多周期 Force Index
    force_index1: float = 0.0
    force_index13: float = 0.0
    force_index21: float = 0.0
