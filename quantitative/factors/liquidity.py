# -*- coding: utf-8 -*-
"""流动性 / 资金面（B 类：从行情派生）因子字段。

对应数据表 ``factor_liquidity``。字段与
``quantitative.indicators.liquidity`` 中的算子一一对应。

口径说明：
- 所有"成交额"字段使用 ``DailyQuote.turnover``（单位：元）。
- ``turnover_rate`` 直接取自数据源；个别源（腾讯/新浪 部分 ADR 等）
  不提供时为 0，衍生的 MA/Z 分也会随之为 0。
- 本类字段**不参与评分**，仅入库供分析/横截面查询。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LiquidityFields:
    """对应数据表 ``factor_liquidity``。"""

    # 换手率（当日 + 多周期均值 + Z 分）
    turnover_rate: float = 0.0
    turnover_rate_ma5: float = 0.0
    turnover_rate_ma20: float = 0.0
    turnover_rate_z20: float = 0.0

    # 成交额派生（ADTV）
    amount_ma5: float = 0.0
    amount_ma20: float = 0.0
    amount_ratio_5_20: float = 0.0

    # 非流动性 / 流动性分位
    amihud: float = 0.0
    illiquidity_rank: float = 0.0

    # 量价关系
    vol_price_corr_20: float = 0.0
    money_flow_strength: float = 0.0
