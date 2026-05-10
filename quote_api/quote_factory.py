# -*- coding: utf-8 -*-
"""行情数据源工厂

通过配置字符串创建具体的 QuoteAPI 实例。

设计要点：
- ``create()`` / ``create_with_cache()`` 默认走**单例缓存**：同一进程
  内同一 source 复用同一个上游 API 实例，避免重复实例化和多份 DB
  连接（``CachedQuoteAPI`` 内部会懒加载 ``StockDB``，每个新实例都
  会开一个新连接）。
- 如需绕过缓存（例如测试场景），传 ``cached=False`` 即可。
- ``clear_cache()`` 用于显式释放（主要给测试和长时进程使用）。
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from quote_api.quote_base import QuoteAPI
from quote_api.eastmoney import EastMoneyQuoteAPI
from quote_api.tencent import TencentQuoteAPI
from quote_api.sina import SinaQuoteAPI
from quote_api.cached_api import CachedQuoteAPI


class QuoteSource(str, Enum):
    """支持的数据源枚举"""
    EASTMONEY = "eastmoney"
    TENCENT = "tencent"
    SINA = "sina"


class QuoteAPIFactory:
    """
    行情 API 工厂。

    用法：
        api = QuoteAPIFactory.create("eastmoney")
        api = QuoteAPIFactory.create(QuoteSource.SINA)
        api = QuoteAPIFactory.create()                # 用 config.QUOTE_SOURCE
        api = QuoteAPIFactory.create_with_cache(...)  # 带 DB 缓存
    """

    _REGISTRY: dict[str, type[QuoteAPI]] = {
        QuoteSource.EASTMONEY.value: EastMoneyQuoteAPI,
        QuoteSource.TENCENT.value: TencentQuoteAPI,
        QuoteSource.SINA.value: SinaQuoteAPI,
    }

    # 进程级实例缓存（懒加载、按 source 单例）
    _RAW_INSTANCES: dict[str, QuoteAPI] = {}
    _CACHED_INSTANCES: dict[str, CachedQuoteAPI] = {}

    # ------------------------------------------------------------------
    @classmethod
    def create(cls, source: Optional[str | QuoteSource] = None,
               cached: bool = True) -> QuoteAPI:
        """创建（或返回已缓存的）原始 API 实例。

        :param cached: True 时返回单例（默认）；False 时每次新建。
        """
        key = cls._resolve_key(source)
        impl = cls._REGISTRY.get(key)
        if impl is None:
            raise ValueError(
                "unsupported quote source: %s, available: %s"
                % (key, list(cls._REGISTRY.keys()))
            )
        if not cached:
            return impl()
        inst = cls._RAW_INSTANCES.get(key)
        if inst is None:
            inst = impl()
            cls._RAW_INSTANCES[key] = inst
        return inst

    # ------------------------------------------------------------------
    @classmethod
    def available_sources(cls) -> list[str]:
        return list(cls._REGISTRY.keys())

    # ------------------------------------------------------------------
    @classmethod
    def register(cls, source: str, impl: type[QuoteAPI]) -> None:
        """允许外部扩展新的数据源"""
        cls._REGISTRY[source] = impl
        # 注册时清掉同名旧缓存，避免读到过期实现
        cls._RAW_INSTANCES.pop(source, None)
        cls._CACHED_INSTANCES.pop(source, None)

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

    # ------------------------------------------------------------------
    @classmethod
    def create_with_cache(cls, source: Optional[str | QuoteSource] = None,
                          cached: bool = True) -> CachedQuoteAPI:
        """创建（或返回已缓存的）带 DB 缓存的 API 实例。

        :param cached: True 时返回单例（默认）；False 时每次新建（含新 DB 连接）。
        """
        key = cls._resolve_key(source)
        if not cached:
            return CachedQuoteAPI(cls.create(key, cached=False))
        inst = cls._CACHED_INSTANCES.get(key)
        if inst is None:
            inst = CachedQuoteAPI(cls.create(key, cached=True))
            cls._CACHED_INSTANCES[key] = inst
        return inst

    # ------------------------------------------------------------------
    @classmethod
    def clear_cache(cls) -> None:
        """释放所有缓存的实例（CachedQuoteAPI 会关闭其 DB 连接）。"""
        for inst in cls._CACHED_INSTANCES.values():
            try:
                inst.close()
            except Exception:
                pass
        cls._CACHED_INSTANCES.clear()
        cls._RAW_INSTANCES.clear()
