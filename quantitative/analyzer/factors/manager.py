# -*- coding: utf-8 -*-
"""因子管理器：预读数据 + 载入准确率 + 驱动因子 + 综合预测。

使用示例：
    from quantitative.analyzer.factors.manager import FactorManager
    mgr = FactorManager(api="futu", use_cache=True)
    result = mgr.analyze("Tencent", anchor_date="2026-08-19", lookback=120)
    print(result.summary)
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd

from quote_api import QuoteAPIFactory
from utils.logger import get_logger

from .base import FactorContext, FactorOutput, FORECAST_HORIZONS
from .registry import instantiate_all

_log = get_logger(__name__)

_ACCURACY_FILE = os.path.join(os.path.dirname(__file__), "accuracy.json")


@dataclass
class FactorAnalysisResult:
    name_key: str
    anchor_date: str
    anchor_price: float
    lookback: int
    outputs: List[FactorOutput] = field(default_factory=list)
    # 加权综合预测概率 {5: p_up, 30: p_up, 60: p_up}
    composite_prob_up: Dict[int, float] = field(default_factory=dict)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "name_key": self.name_key,
            "anchor_date": self.anchor_date,
            "anchor_price": self.anchor_price,
            "lookback": self.lookback,
            "composite_prob_up": self.composite_prob_up,
            "factors": [o.to_dict() for o in self.outputs],
        }


class FactorManager:
    """预读数据并运行全部因子。"""

    def __init__(self, api: Optional[str] = None, use_cache: bool = True,
                 accuracy_file: str = _ACCURACY_FILE):
        self.api = api or QuoteAPIFactory.current_source()
        self.use_cache = use_cache
        if use_cache:
            self.impl = QuoteAPIFactory.create_with_cache(self.api)
        else:
            self.impl = QuoteAPIFactory.create(self.api)
        self.accuracy = self._load_accuracy(accuracy_file)

    @staticmethod
    def _load_accuracy(path: str) -> Dict[str, Dict[str, float]]:
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data.pop("_comment", None)
            return data
        except Exception as e:
            _log.warning("载入 accuracy.json 失败: %s", e)
            return {}

    # ------------------------------------------------------------------
    def _build_context(self, name_key: str, anchor_date: str,
                       lookback: int) -> Optional[FactorContext]:
        """从数据库预读截至 anchor_date 的日线，构造 FactorContext。"""
        if not self.impl.is_supported(name_key):
            _log.warning("api '%s' 不支持 '%s'", self.api, name_key)
            return None

        # get_klines 取最近 N 天；这里多取以支持未来窗口回测验证
        quotes = self.impl.get_klines(name_key, limit=lookback + 60)
        if not quotes:
            _log.warning("无法获取K线数据: %s", name_key)
            return None

        rows = [q.__dict__ if hasattr(q, "__dict__") else q for q in quotes]
        df = pd.DataFrame(rows)
        # 规范化列名
        for col in ("date", "open", "high", "low", "close", "volume", "amount"):
            if col not in df.columns:
                # 尝试常见别名
                for alias in (col.upper(), col.capitalize()):
                    if alias in df.columns:
                        df[col] = df[alias]
                        break
        df = df.sort_values("date").reset_index(drop=True)
        df["close"] = df["close"].astype(float)

        # 截断到 anchor_date（含）
        if anchor_date in set(df["date"]):
            df = df[df["date"] <= anchor_date].reset_index(drop=True)
        else:
            _log.warning("anchor_date %s 不在数据区间，使用最新日期 %s",
                         anchor_date, df["date"].iloc[-1])
            anchor_date = df["date"].iloc[-1]

        full_df = df.copy()  # 含未来窗口，供 future_close 使用
        df = df.tail(lookback).reset_index(drop=True)

        return FactorContext(
            name_key=name_key,
            anchor_date=anchor_date,
            df=df,
            full_df=full_df,
        )

    # ------------------------------------------------------------------
    def analyze(self, name_key: str, anchor_date: str,
                lookback: int = 120) -> Optional[FactorAnalysisResult]:
        ctx = self._build_context(name_key, anchor_date, lookback)
        if ctx is None:
            return None

        outputs: List[FactorOutput] = []
        for factor in instantiate_all():
            try:
                out = factor.detect(ctx)
            except Exception as e:  # 单个因子失败不应中断
                _log.warning("因子 %s 计算失败: %s", factor.name, e)
                continue
            # 注入回测准确率
            acc = self.accuracy.get(factor.name, {})
            out.accuracy = (
                acc.get("5", 0.5),
                acc.get("30", 0.5),
                acc.get("60", 0.5),
            )
            outputs.append(out)

        result = FactorAnalysisResult(
            name_key=name_key,
            anchor_date=ctx.anchor_date,
            anchor_price=ctx.anchor_price,
            lookback=lookback,
            outputs=outputs,
        )
        result.composite_prob_up = self._composite(outputs)
        result.summary = self._render_summary(result)
        return result

    # ------------------------------------------------------------------
    @staticmethod
    def _composite(outputs: List[FactorOutput]) -> Dict[int, float]:
        """按各因子在对应周期的回测准确率加权，得到综合上涨概率。

        对周期 h：p_up(h) = Σ(acc_h * [forecast_h?1:0]) / Σ(acc_h)
        无有效因子时回退 0.5。
        """
        prob: Dict[int, float] = {}
        for i, h in enumerate(FORECAST_HORIZONS):
            num = 0.0
            den = 0.0
            for o in outputs:
                a = o.accuracy[i]
                num += a * (1.0 if o.forecast[i] else 0.0)
                den += a
            prob[h] = round(num / den, 4) if den > 0 else 0.5
        return prob

    @staticmethod
    def _render_summary(result: FactorAnalysisResult) -> str:
        lines = []
        lines.append(f"[因子分析] {result.name_key} @ {result.anchor_date}")
        lines.append(f"   基准价(anchor): {result.anchor_price:.2f} | 回看: {result.lookback}日")
        cp = result.composite_prob_up
        lines.append(
            f"   综合上涨概率  5日={cp.get(5, 0.5)*100:.1f}%  "
            f"30日={cp.get(30, 0.5)*100:.1f}%  "
            f"60日={cp.get(60, 0.5)*100:.1f}%"
        )
        lines.append(f"\n=== 因子明细 ({len(result.outputs)}个) ===")
        for o in result.outputs:
            f5 = "涨" if o.forecast[0] else "跌"
            f30 = "涨" if o.forecast[1] else "跌"
            f60 = "涨" if o.forecast[2] else "跌"
            acc = "/".join(f"{a*100:.0f}" for a in o.accuracy)
            lines.append(
                f"   [{o.category}] {o.name}: {o.description}\n"
                f"       预测 5日{f5}/30日{f30}/60日{f60} | 准确率 {acc}%"
            )
        return "\n".join(lines)
