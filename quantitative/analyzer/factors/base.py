# -*- coding: utf-8 -*-
"""因子基类与数据上下文。

新因子体系设计要点（相对旧 QuantFactorEngine 的重构）：

1. 每个因子是一个独立的类，继承自 :class:`BaseFactor`。
2. 因子通过 :class:`FactorContext` 获取数据，不需要自己读数据库。
   FactorContext 由 :class:`FactorManager` 预读并构造。
3. 每个因子在 ``detect`` 中基于当前形态 / 状态，输出对未来
   5 / 30 / 60 个交易日价格的涨跌预测（相对于 ``anchor_price``）：

       forecast = (up_5, up_30, up_60)  每个元素为 bool
       up_5  == True 表示「第 5 个交易日后收盘价 > anchor_price」

   anchor_price 默认取截止日收盘价（即「现在」的价格）。
4. 因子同时保留旧的截面语义（value / signal / direction），用于解释与回测。
5. 各因子的历史回测准确率记录在 ``accuracy.json``，由 Manager 载入，
   分析时按准确率对 forecast 加权。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence, Tuple

import pandas as pd

# 预测的三个目标周期（交易日）
FORECAST_HORIZONS = (5, 30, 60)
Horizon = Tuple[bool, bool, bool]


@dataclass
class FactorContext:
    """一次分析所需的全部数据，由 FactorManager 预读后注入各因子。

    Attributes:
        name_key:   股票标识（如 Tencent）
        anchor_date: 截止日（含），格式 'YYYY-MM-DD'
        df:         截至 anchor_date 的日线 DataFrame，按日期升序
                    列至少包含 open/high/low/close/volume/amount
        full_df:    更长窗口的日线（用于回看 / 验证），可为 None
    """

    name_key: str
    anchor_date: str
    df: pd.DataFrame
    full_df: Optional[pd.DataFrame] = None

    # ---- 便捷访问 ----
    @property
    def close(self) -> pd.Series:
        return self.df["close"]

    @property
    def high(self) -> pd.Series:
        return self.df["high"]

    @property
    def low(self) -> pd.Series:
        return self.df["low"]

    @property
    def open(self) -> pd.Series:
        return self.df["open"]

    @property
    def volume(self) -> pd.Series:
        return self.df["volume"]

    @property
    def anchor_price(self) -> float:
        """「现在」的价格，默认取截止日收盘价。"""
        return float(self.df["close"].iloc[-1])

    @property
    def n(self) -> int:
        return len(self.df)

    def future_close(self, horizon: int) -> Optional[float]:
        """返回 anchor_date 之后第 ``horizon`` 个交易日的收盘价（用于回测）。

        若数据不足返回 None。full_df 优先，否则在 df 内寻找。
        """
        target_idx = self.n - 1 + horizon
        src = self.full_df if self.full_df is not None else self.df
        if target_idx < len(src):
            return float(src["close"].iloc[target_idx])
        return None


@dataclass
class FactorOutput:
    """单个因子的计算结果。"""

    name: str
    category: str
    # 截面语义（解释 / 回测用）
    value: float = 0.0
    signal: int = 0          # +1 看涨, 0 中性, -1 看跌
    direction: int = 0       # +1 上涨预测倾向, -1 下跌预测倾向
    description: str = ""

    # 核心输出：未来 5 / 30 / 60 日相对 anchor_price 的涨跌预测
    forecast: Horizon = field(default_factory=lambda: (False, False, False))

    # 该因子在三个周期上的历史回测准确率 (0~1)，由 Manager 注入
    accuracy: Horizon = field(default_factory=lambda: (0.5, 0.5, 0.5))

    @property
    def triggered(self) -> bool:
        """形态 / 信号是否触发。

        direction 为 0 表示中性（未触发），回测中这类样本不参与该因子的
        准确率统计，避免把"未触发"错误地当作"预测下跌"计入，从而系统性压低命中率。
        """
        return self.direction != 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "value": round(self.value, 4),
            "signal": self.signal,
            "direction": self.direction,
            "description": self.description,
            "forecast": {
                "5": self.forecast[0],
                "30": self.forecast[1],
                "60": self.forecast[2],
            },
            "accuracy": {
                "5": round(self.accuracy[0], 4),
                "30": round(self.accuracy[1], 4),
                "60": round(self.accuracy[2], 4),
            },
        }


class BaseFactor:
    """所有因子的抽象基类。

    子类只需实现 :meth:`detect`，在内部基于 ``ctx`` 计算并填充
    :class:`FactorOutput`。可重写 ``name`` / ``category`` 类属性。
    """

    #: 因子唯一名（与 accuracy.json 的 key 对应）
    name: str = "BaseFactor"
    #: 因子分类（pattern / momentum / trend / volatility / reversal ...）
    category: str = "pattern"

    def detect(self, ctx: FactorContext) -> FactorOutput:
        """基于 ctx 计算因子，返回 FactorOutput。

        子类必须重写。默认返回中性占位结果。
        """
        return FactorOutput(
            name=self.name,
            category=self.category,
            description="未实现",
        )

    # ------------------------------------------------------------------
    # 工具方法：子类 detect 中可调用，便于生成 forecast
    # ------------------------------------------------------------------
    @staticmethod
    def _forecast_from_direction(
        ctx: FactorContext, direction: int
    ) -> Horizon:
        """朴素预测：给定方向（+1/-1），假设该方向在三个周期都成立。

        仅作为无历史数据时的回退；真实预测应由子类结合形态给出。
        """
        if direction > 0:
            return (True, True, True)
        if direction < 0:
            return (False, False, False)
        return (ctx.anchor_price is not None,
                ctx.anchor_price is not None,
                ctx.anchor_price is not None)

    @staticmethod
    def _build_forecast(ctx: FactorContext, direction: int) -> Horizon:
        """基于 anchor_price 与（推断的）未来价生成 forecast。

        direction>0 视为看涨（未来价更高），<0 看跌。
        中性（direction==0）返回 (None, None, None) 表示"无方向观点"，
        回测中对应的未触发样本会被跳过，不计入准确率。
        """
        if direction > 0:
            return (True, True, True)
        if direction < 0:
            return (False, False, False)
        return (None, None, None)
