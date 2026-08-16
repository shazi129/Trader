# -*- coding: utf-8 -*-
"""行情数据源工厂

通过配置字符串创建具体的 QuoteAPI 实例。

设计要点：
- ``create()`` / ``create_with_cache()`` 默认走**单例缓存**：同一进程
  内同一 source + adjustment 复用同一个上游 API 实例，避免重复实例化和多份 DB
  连接（``CachedQuoteAPI`` 内部会懒加载 ``StockDB``，每个新实例都
  会开一个新连接）。
- 如需绕过缓存（例如测试场景），传 ``cached=False`` 即可。
- ``clear_cache()`` 用于显式释放（主要给测试和长时进程使用）。
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from quote_api.quote_base import KlineAdjustment, QuoteAPI
from quote_api.futu import FutuQuoteAPI
from quote_api.tencent import TencentQuoteAPI
from quote_api.sina import SinaQuoteAPI
from quote_api.cached_api import CachedQuoteAPI


class QuoteSource(str, Enum):
    """支持的数据源枚举"""
    FUTU = "futu"
    TENCENT = "tencent"
    SINA = "sina"


class QuoteAPIFactory:
    """
    行情 API 工厂。

    用法：
        api = QuoteAPIFactory.create()                # 当前默认源
        names = QuoteAPIFactory.available_sources()   # 全部已注册源
        current = QuoteAPIFactory.current_source()    # 当前默认源名称
        api = QuoteAPIFactory.create_with_cache(...)  # 带 DB 缓存
    """

    _REGISTRY: dict[str, type[QuoteAPI]] = {
        QuoteSource.FUTU.value: FutuQuoteAPI,
        QuoteSource.TENCENT.value: TencentQuoteAPI,
        QuoteSource.SINA.value: SinaQuoteAPI,
    }

    # 进程级实例缓存（懒加载、按 source + adjustment 单例）
    _RAW_INSTANCES: dict[tuple[str, str], QuoteAPI] = {}
    _CACHED_INSTANCES: dict[tuple[str, str], CachedQuoteAPI] = {}

    # ------------------------------------------------------------------
    @classmethod
    def create(cls, source: Optional[str | QuoteSource] = None,
               cached: bool = True,
               adjustment: Optional[str | KlineAdjustment] = None) -> QuoteAPI:
        """创建（或返回已缓存的）原始 API 实例。

        :param cached: True 时返回单例（默认）；False 时每次新建。
        :param adjustment: 复权方式；None 时读取全局配置。
        """
        key = cls._resolve_key(source)
        mode = KlineAdjustment.parse(
            adjustment if adjustment is not None else cls.current_adjustment()
        )
        cache_key = (key, mode.value)
        impl = cls._REGISTRY.get(key)
        if impl is None:
            raise ValueError(
                "unsupported quote source: %s, available: %s"
                % (key, list(cls._REGISTRY.keys()))
            )
        if not cached:
            return impl(adjustment=mode)
        inst = cls._RAW_INSTANCES.get(cache_key)
        if inst is None:
            inst = impl(adjustment=mode)
            cls._RAW_INSTANCES[cache_key] = inst
        return inst

    # ------------------------------------------------------------------
    @classmethod
    def available_sources(cls) -> list[str]:
        """返回当前已注册的全部行情源；供菜单、CLI choices 等直接使用。"""
        return list(cls._REGISTRY.keys())

    # ------------------------------------------------------------------
    @classmethod
    def current_source(cls) -> str:
        """返回当前默认行情源。

        默认值只从 ``config.QUOTE_SOURCE`` 和注册表解析。配置缺失或指向已卸载
        的 provider 时，回退到注册表中的第一个实现，调用方无需维护第二份名单。
        """
        try:
            import config
            configured = str(getattr(config, "QUOTE_SOURCE", "")).lower()
        except Exception:
            configured = ""
        if configured in cls._REGISTRY:
            return configured
        try:
            return next(iter(cls._REGISTRY))
        except StopIteration as exc:  # pragma: no cover - 注册表通常不会为空
            raise RuntimeError("no quote source is registered") from exc

    # ------------------------------------------------------------------
    @classmethod
    def current_adjustment(cls) -> KlineAdjustment:
        """返回 ``config.KLINE_ADJUSTMENT`` 指定的历史 K 线复权方式。"""
        try:
            import config
            configured = getattr(config, "KLINE_ADJUSTMENT", None)
        except Exception:
            configured = None
        return KlineAdjustment.parse(configured)

    # ------------------------------------------------------------------
    @classmethod
    def register(cls, source: str, impl: type[QuoteAPI]) -> None:
        """允许外部扩展新的数据源"""
        cls._REGISTRY[source] = impl
        # 注册时清掉同名旧缓存，避免读到过期实现
        for cache_key in [key for key in cls._CACHED_INSTANCES if key[0] == source]:
            cls._CACHED_INSTANCES.pop(cache_key).close()
        for cache_key in [key for key in cls._RAW_INSTANCES if key[0] == source]:
            cls._RAW_INSTANCES.pop(cache_key).close()

    # ------------------------------------------------------------------
    @classmethod
    def _resolve_key(cls, source: Optional[str | QuoteSource]) -> str:
        if isinstance(source, QuoteSource):
            return source.value
        if isinstance(source, str) and source:
            return source.lower()
        return cls.current_source()

    # ------------------------------------------------------------------
    @classmethod
    def create_with_cache(cls, source: Optional[str | QuoteSource] = None,
                          cached: bool = True,
                          adjustment: Optional[str | KlineAdjustment] = None,
                          ) -> CachedQuoteAPI:
        """创建（或返回已缓存的）带 DB 缓存的 API 实例。

        :param cached: True 时返回单例（默认）；False 时每次新建（含新 DB 连接）。
        """
        key = cls._resolve_key(source)
        mode = KlineAdjustment.parse(
            adjustment if adjustment is not None else cls.current_adjustment()
        )
        cache_key = (key, mode.value)
        if not cached:
            return CachedQuoteAPI(
                cls.create(key, cached=False, adjustment=mode)
            )
        inst = cls._CACHED_INSTANCES.get(cache_key)
        if inst is None:
            inst = CachedQuoteAPI(
                cls.create(key, cached=True, adjustment=mode)
            )
            cls._CACHED_INSTANCES[cache_key] = inst
        return inst

    # ------------------------------------------------------------------
    @classmethod
    def clear_cache(cls) -> None:
        """释放所有缓存实例及其 DB / 上游连接。"""
        for inst in cls._CACHED_INSTANCES.values():
            try:
                inst.close()
            except Exception:
                pass
        cls._CACHED_INSTANCES.clear()
        for inst in cls._RAW_INSTANCES.values():
            try:
                inst.close()
            except Exception:
                pass
        cls._RAW_INSTANCES.clear()
