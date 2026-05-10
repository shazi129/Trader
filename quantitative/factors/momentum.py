# -*- coding: utf-8 -*-
"""动量类因子字段：MOM / ROC / CCI / Williams %R。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MomentumFields:
    """对应数据表 ``factor_momentum``。"""

    # 多周期动量 (price[t] - price[t-N])
    mom1w: float = 0.0
    mom2w: float = 0.0
    mom1m: float = 0.0
    mom3m: float = 0.0
    mom6m: float = 0.0
    mom9m: float = 0.0
    mom12m: float = 0.0

    # 多周期变动率（%）
    roc1w: float = 0.0
    roc2w: float = 0.0
    roc1m: float = 0.0
    roc3m: float = 0.0
    roc6m: float = 0.0
    roc9m: float = 0.0
    roc12m: float = 0.0

    # CCI / Williams %R
    cci: float = 0.0
    williams_r: float = 0.0
