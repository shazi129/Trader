# -*- coding: utf-8 -*-
"""行情数据源工厂

通过配置字符串创建具体的 QuoteAPI 实例。
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from quote_api.quote_base import QuoteAPI
from quote_api.eastmoney_quote import EastMoneyQuoteAPI
from quote_api.akshare_quote import AkShareQuoteAPI
from quote_api.yfinance_quote import YFinanceQuoteAPI
from quote_api.xueqiu_quote import XueqiuQuoteAPI
from quote_api.tencent_quote import TencentQuoteAPI


class QuoteSource(str, Enum):
    """支持的数据源枚举"""
    EASTMONEY = "eastmoney"
    AKSHARE = "akshare"
    YFINANCE = "yfinance"
    XUEQIU = "xueqiu"
    TENCENT = "tencent"


class QuoteAPIFactory:
    """
    行情 API 工厂。

    用法：
        api = QuoteAPIFactory.create("akshare")
        api = QuoteAPIFactory.create(QuoteSource.YFINANCE)
        api = QuoteAPIFactory.create()   # 使用 config.QUOTE_SOURCE 默认值
    """

    _REGISTRY: dict[str, type[QuoteAPI]] = {
        QuoteSource.EASTMONEY.value: EastMoneyQuoteAPI,
        QuoteSource.AKSHARE.value: AkShareQuoteAPI,
        QuoteSource.YFINANCE.value: YFinanceQuoteAPI,
        QuoteSource.XUEQIU.value: XueqiuQuoteAPI,
        QuoteSource.TENCENT.value: TencentQuoteAPI,
    }

    # ------------------------------------------------------------------
    @classmethod
    def create(cls, source: Optional[str | QuoteSource] = None) -> QuoteAPI:
        key = cls._resolve_key(source)
        impl = cls._REGISTRY.get(key)
        if impl is None:
            raise ValueError(
                "unsupported quote source: %s, available: %s"
                % (key, list(cls._REGISTRY.keys()))
            )
        return impl()

    # ------------------------------------------------------------------
    @classmethod
    def available_sources(cls) -> list[str]:
        return list(cls._REGISTRY.keys())

    # ------------------------------------------------------------------
    @classmethod
    def register(cls, source: str, impl: type[QuoteAPI]) -> None:
        """允许外部扩展新的数据源"""
        cls._REGISTRY[source] = impl

    # ------------------------------------------------------------------
    @classmethod
    def _resolve_key(cls, source: Optional[str | QuoteSource]) -> str:
        if isinstance(source, QuoteSource):
            return source.value
        if isinstance(source, str) and source:
            return source.lower()
        # 未指定：读 config.QUOTE_SOURCE，兜底东方财富
        try:
            import config
            return str(getattr(config, "QUOTE_SOURCE", QuoteSource.EASTMONEY.value)).lower()
        except Exception:
            return QuoteSource.EASTMONEY.value
