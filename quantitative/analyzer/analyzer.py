# -*- coding: utf-8 -*-
"""量化分析器 `QuantAnalyzer`：编排 数据获取 → 因子计算 → 评分 → 报告。"""

from __future__ import annotations

from typing import Optional

import config
from quote_api import QuoteAPIFactory
from utils.logger import get_logger

from .factors import FactorManager
from .scoring import AnalysisReport, compute_probability
from .report import generate_summary

_log = get_logger(__name__)


class QuantAnalyzer:
    """量化分析器。"""

    def __init__(self, api: Optional[str] = None, use_cache: bool = True):
        """
        :param api: 数据源名称；不传时使用 QuoteAPIFactory 当前默认源
        :param use_cache: 是否使用数据库缓存
        """
        self.api = api or QuoteAPIFactory.current_source()
        self.use_cache = use_cache

        # 走 Factory 单例缓存（同一进程同 source 复用 raw + cached 实例与 DB 连接）
        if use_cache:
            self.impl = QuoteAPIFactory.create_with_cache(self.api)
            _log.info("使用带缓存的API: %s", self.impl.SOURCE)
        else:
            self.impl = QuoteAPIFactory.create(self.api)
            _log.info("使用原始API: %s", self.impl.SOURCE)

    def analyze(self, name_key: str, days: int = 500,
                 anchor_date: Optional[str] = None) -> Optional[AnalysisReport]:
        """对指定股票进行多因子分析（基于新因子体系）。

        :param days: 历史回看天数（用于 FactorManager 预读窗口）
        :param anchor_date: 截止日（含）；不传时取数据最新日
        """
        from quote_api import QuoteAPIFactory as _QAF
        # 取最新日期作为默认 anchor
        if anchor_date is None:
            if not self.impl.is_supported(name_key):
                _log.warning("api '%s' does not support '%s'", self.api, name_key)
                return None
            q = self.impl.get_klines(name_key, limit=1)
            if not q:
                _log.warning("无法获取K线数据: %s", name_key)
                return None
            anchor_date = q[-1].date

        _log.info("分析 %s @ %s (回看%d日, api=%s)",
                  name_key, anchor_date, days, self.api)
        mgr = FactorManager(api=self.api, use_cache=self.use_cache)
        fres = mgr.analyze(name_key, anchor_date=anchor_date, lookback=days)
        if fres is None:
            _log.warning("因子分析失败: %s", name_key)
            return None

        # 综合上涨概率 → 映射为旧式 prob_up/down/trend
        cp = fres.composite_prob_up
        prob_up = round((cp.get(30, 0.5) + cp.get(60, 0.5)) / 2.0, 3)
        prob_up = max(0.15, min(0.85, prob_up))
        prob_down = round(1.0 - prob_up, 3)
        if prob_up > 0.65:
            trend = "上涨趋势"
        elif prob_up < 0.35:
            trend = "下跌趋势"
        else:
            trend = "震荡整理"

        # 用旧 FactorResult 形态包装（signal 由 forecast 方向推导），保持 report 兼容
        from .scoring import FactorResult
        factors = [
            FactorResult(
                name=o.name,
                category=o.category,
                value=o.value,
                signal=o.direction,
                description=o.description,
            )
            for o in fres.outputs
        ]

        stock_info = config.global_stock_list.get(name_key)
        report = AnalysisReport(
            stock_name=stock_info.name if stock_info else name_key,
            name_key=name_key,
            data_source=self.api,
            data_days=fres.lookback,
            latest_price=fres.anchor_price,
            factors=factors,
            bullish_score=round(prob_up * 100, 1),
            bearish_score=round(prob_down * 100, 1),
            trend=trend,
            probability_up=prob_up,
            probability_down=prob_down,
        )
        report.summary = generate_summary(report) + "\n\n" + fres.summary
        return report
