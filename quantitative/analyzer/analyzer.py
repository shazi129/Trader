# -*- coding: utf-8 -*-
"""量化分析器 `QuantAnalyzer`：编排 数据获取 → 因子计算 → 评分 → 报告。"""

from __future__ import annotations

from typing import Optional

import config
from quote_api import QuoteAPIFactory
from utils.logger import get_logger

from .factors import QuantFactorEngine
from .scoring import AnalysisReport, compute_probability
from .report import generate_summary

_log = get_logger(__name__)


class QuantAnalyzer:
    """量化分析器。"""

    def __init__(self, api: str = "tencent", use_cache: bool = True):
        """
        :param api: 数据源名称 (tencent/eastmoney/sina)
        :param use_cache: 是否使用数据库缓存
        """
        self.api = api
        self.use_cache = use_cache

        # 走 Factory 单例缓存（同一进程同 source 复用 raw + cached 实例与 DB 连接）
        if use_cache:
            self.impl = QuoteAPIFactory.create_with_cache(api)
            _log.info("使用带缓存的API: %s", self.impl.SOURCE)
        else:
            self.impl = QuoteAPIFactory.create(api)
            _log.info("使用原始API: %s", self.impl.SOURCE)

    def analyze(self, name_key: str, days: int = 500) -> Optional[AnalysisReport]:
        """对指定股票进行多因子分析。"""
        if not self.impl.is_supported(name_key):
            _log.warning("api '%s' does not support '%s'", self.api, name_key)
            return None

        _log.info("正在获取 %s 最近 %d 天K线数据 (api=%s)...",
                  name_key, days, self.api)
        quotes = self.impl.get_klines(name_key, limit=days)
        if not quotes:
            _log.warning("无法获取K线数据")
            return None

        _log.info("获取到 %d 条数据，区间: %s ~ %s",
                  len(quotes), quotes[0].date, quotes[-1].date)

        # 基本面（可选）
        fundamentals = None
        try:
            _log.info("正在获取 %s 基本面数据...", name_key)
            fundamentals = self.impl.get_fundamentals(name_key)
            if fundamentals:
                _log.info("获取到基本面数据: PE=%.2f, PB=%.2f",
                          fundamentals.pe_ttm, fundamentals.pb)
            else:
                _log.info("无基本面数据，将跳过基本面因子")
        except Exception as e:
            _log.warning("获取基本面数据失败: %s", e)

        engine = QuantFactorEngine(quotes, fundamentals)
        factors = engine.compute_all()

        prob_up, prob_down, trend = compute_probability(factors)

        stock_info = config.global_stock_list.get(name_key)
        report = AnalysisReport(
            stock_name=stock_info.name if stock_info else name_key,
            name_key=name_key,
            data_source=self.api,
            data_days=len(quotes),
            latest_price=quotes[-1].close,
            factors=factors,
            bullish_score=round(prob_up * 100, 1),
            bearish_score=round(prob_down * 100, 1),
            trend=trend,
            probability_up=prob_up,
            probability_down=prob_down,
        )
        report.summary = generate_summary(report)
        return report
