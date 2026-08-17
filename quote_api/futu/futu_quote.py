# -*- coding: utf-8 -*-
"""富途 OpenAPI：日 K 线实现。

富途 Python SDK 并不直接访问公网行情接口，而是连接已经登录的 OpenD：

    Python SDK -> OpenD (默认 127.0.0.1:11111) -> 富途行情服务

环境变量：
    FUTU_OPEND_HOST    OpenD 地址，默认 127.0.0.1
    FUTU_OPEND_PORT    OpenD API 端口，默认 11111

代码格式：
    A 股：SH.600519 / SZ.000001
    港股：HK.00700
    美股：US.NVDA
白银 ``AG`` 当前表示 iShares Silver Trust，在本数据源中映射为
``US.SLV``。
"""

from __future__ import annotations

import math
import os
from typing import Any, Optional

from quote_api.quote_base import DailyQuote, DateLike, KlineAdjustment, QuoteAPI
from quote_api.stock_meta import StockMarket, get_meta
from utils.logger import get_logger

_log = get_logger(__name__)


class FutuQuoteError(RuntimeError):
    """OpenD 连接或富途行情请求失败。"""


def _load_futu_sdk():
    """延迟导入 SDK，避免可选依赖缺失时影响其他行情源。"""
    try:
        import futu
    except ImportError as exc:  # pragma: no cover - 取决于本机环境
        raise FutuQuoteError(
            "futu-api is not installed; run: python -m pip install futu-api"
        ) from exc
    return futu


def _to_float(value: Any, default: float = 0.0) -> float:
    """把 DataFrame 字段安全转成有限浮点数。"""
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


class FutuQuoteAPI(QuoteAPI):
    """通过本机或远程 OpenD 获取日 K 线。"""

    SOURCE = "futu"

    DEFAULT_HOST = "127.0.0.1"
    DEFAULT_PORT = 22222
    PAGE_SIZE = 1000

    _MARKET_PREFIX = {
        StockMarket.SH: "SH",
        StockMarket.SZ: "SZ",
        StockMarket.HK: "HK",
        StockMarket.NASDAQ: "US",
        StockMarket.NYSE: "US",
        StockMarket.US: "US",
    }

    _CURRENCY = {
        StockMarket.SH: "CNY",
        StockMarket.SZ: "CNY",
        StockMarket.HK: "HKD",
        StockMarket.NASDAQ: "USD",
        StockMarket.NYSE: "USD",
        StockMarket.US: "USD",
    }

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        quote_context: Any = None,
        adjustment: KlineAdjustment | str = KlineAdjustment.NONE,
    ) -> None:
        """创建富途行情源。

        ``quote_context`` 主要用于测试或由调用方复用已有上下文；传入时其生命周期
        仍由调用方管理。正常使用无需传入，连接会在第一次请求时延迟创建。
        """
        super().__init__(adjustment=adjustment)
        self._host = host or os.getenv("FUTU_OPEND_HOST", self.DEFAULT_HOST)
        raw_port = port if port is not None else os.getenv(
            "FUTU_OPEND_PORT", str(self.DEFAULT_PORT)
        )
        try:
            self._port = int(raw_port)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid FUTU_OPEND_PORT: %r" % raw_port) from exc

        self._quote_context = quote_context
        self._owns_context = quote_context is None

    # ------------------------------------------------------------------
    def _get_context(self):
        if self._quote_context is None:
            sdk = _load_futu_sdk()
            try:
                self._quote_context = sdk.OpenQuoteContext(
                    host=self._host, port=self._port
                )
                self._owns_context = True
            except Exception as exc:
                raise FutuQuoteError(
                    "cannot connect to Futu OpenD at %s:%s: %s"
                    % (self._host, self._port, exc)
                ) from exc
        return self._quote_context

    def close(self) -> None:
        """关闭由当前实例创建的 OpenD 连接，可重复调用。"""
        context = self._quote_context
        self._quote_context = None
        if context is not None and self._owns_context:
            try:
                context.close()
            except Exception as exc:  # pragma: no cover - defensive
                _log.warning("close Futu OpenD context error: %s", exc)

    def __enter__(self) -> "FutuQuoteAPI":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __del__(self):  # pragma: no cover - 解释器退出时的兜底
        try:
            self.close()
        except Exception:
            pass

    # ------------------------------------------------------------------
    def is_supported(self, name_key: str) -> bool:
        if not super().is_supported(name_key):
            return False
        stock = get_meta(name_key)
        return stock is not None and stock.market in self._MARKET_PREFIX

    def _futu_symbol(self, name: str) -> Optional[str]:
        stock = get_meta(name)
        code = self.get_stock_code(name)
        if stock is None or code is None:
            return None

        # 允许 config.json 直接提供完整富途代码。
        code = code.strip()
        if "." in code:
            prefix, symbol = code.split(".", 1)
            if prefix.upper() in set(self._MARKET_PREFIX.values()) and symbol:
                return "%s.%s" % (prefix.upper(), symbol.upper())
            return None

        prefix = self._MARKET_PREFIX.get(stock.market)
        if prefix is None:
            return None
        if stock.market == StockMarket.HK:
            code = code.zfill(5)
        elif stock.market in (StockMarket.SH, StockMarket.SZ):
            code = code.zfill(6)
        elif prefix == "US":
            code = code.upper()
        return "%s.%s" % (prefix, code)

    # ------------------------------------------------------------------
    def get_daily_quote(
        self,
        name: str,
        date: DateLike = None,
    ) -> Optional[DailyQuote]:
        """获取指定日期或最新实时快照。

        指定 ``date`` 时仍通过历史 K 线精确查询；不指定时使用
        OpenD 市场快照，避免把最近一根日 K 误当成实时价。
        """
        target = self.normalize_date(date)
        if target is not None:
            return super().get_daily_quote(name, target)

        stock = get_meta(name)
        symbol = self._futu_symbol(name)
        if stock is None or symbol is None:
            _log.warning("unknown or unsupported Futu stock: %s", name)
            return None

        sdk = _load_futu_sdk()
        context = self._get_context()
        try:
            ret, data = context.get_market_snapshot([symbol])
        except Exception as exc:
            raise FutuQuoteError(
                "Futu market snapshot request failed for %s: %s"
                % (symbol, exc)
            ) from exc

        if ret != sdk.RET_OK:
            raise FutuQuoteError(
                "Futu market snapshot request failed for %s: %s"
                % (symbol, data)
            )
        if not hasattr(data, "iterrows"):
            raise FutuQuoteError(
                "Futu returned unexpected snapshot payload for %s: %r"
                % (symbol, type(data).__name__)
            )

        for _, row in data.iterrows():
            return self._snapshot_to_quote(row, name, symbol, stock.market)
        return None

    # ------------------------------------------------------------------
    def get_klines(
        self,
        name: str,
        start_date: DateLike = None,
        end_date: DateLike = None,
        limit: Optional[int] = None,
    ) -> list[DailyQuote]:
        stock = get_meta(name)
        symbol = self._futu_symbol(name)
        if stock is None or symbol is None:
            _log.warning("unknown or unsupported Futu stock: %s", name)
            return []

        sd = self.normalize_date(start_date)
        ed = self.normalize_date(end_date)
        if sd and ed and sd > ed:
            return []

        sdk = _load_futu_sdk()
        context = self._get_context()
        autype = {
            KlineAdjustment.NONE: sdk.AuType.NONE,
            KlineAdjustment.QFQ: sdk.AuType.QFQ,
            KlineAdjustment.HFQ: sdk.AuType.HFQ,
        }[self.adjustment]
        page_req_key = None
        seen_page_keys: set[bytes] = set()
        results: list[DailyQuote] = []

        while True:
            try:
                ret, data, next_page_key = context.request_history_kline(
                    symbol,
                    start=sd,
                    end=ed,
                    ktype=sdk.KLType.K_DAY,
                    autype=autype,
                    fields=[sdk.KL_FIELD.ALL],
                    max_count=self.PAGE_SIZE,
                    page_req_key=page_req_key,
                    extended_time=False,
                )
            except Exception as exc:
                raise FutuQuoteError(
                    "Futu history kline request failed for %s: %s"
                    % (symbol, exc)
                ) from exc

            if ret != sdk.RET_OK:
                raise FutuQuoteError(
                    "Futu history kline request failed for %s: %s"
                    % (symbol, data)
                )
            if not hasattr(data, "iterrows"):
                raise FutuQuoteError(
                    "Futu returned unexpected kline payload for %s: %r"
                    % (symbol, type(data).__name__)
                )

            for _, row in data.iterrows():
                quote = self._row_to_quote(row, name, symbol, stock.market)
                if quote is not None:
                    results.append(quote)

            if next_page_key is None:
                break
            if next_page_key in seen_page_keys:
                raise FutuQuoteError(
                    "Futu returned a repeated page key for %s" % symbol
                )
            seen_page_keys.add(next_page_key)
            page_req_key = next_page_key

        # 防御性去重：分页边界或上游异常时，同一交易日只保留最后一条。
        deduplicated = {quote.date: quote for quote in results}
        return self.sort_and_trim(
            list(deduplicated.values()),
            start_date=sd,
            end_date=ed,
            limit=limit,
        )

    # ------------------------------------------------------------------
    @classmethod
    def _snapshot_to_quote(
        cls,
        row: Any,
        name: str,
        symbol: str,
        market: StockMarket,
    ) -> Optional[DailyQuote]:
        date = str(row.get("update_time", ""))[:10]
        close = _to_float(row.get("last_price"))
        if len(date) != 10 or close <= 0:
            return None

        q = DailyQuote()
        q.source = cls.SOURCE
        q.name = name
        q.code = symbol
        q.date = date
        q.open = _to_float(row.get("open_price"))
        q.close = close
        q.high = _to_float(row.get("high_price"))
        q.low = _to_float(row.get("low_price"))
        q.pre_close = _to_float(row.get("prev_close_price"))
        q.volume = _to_float(row.get("volume"))
        q.turnover = _to_float(row.get("turnover"))
        # 市场快照的 turnover_rate 已是百分数，不再乘 100。
        q.turnover_rate = _to_float(row.get("turnover_rate"))
        if q.pre_close > 0:
            q.change = q.close - q.pre_close
            q.change_pct = q.change / q.pre_close * 100.0
        q.currency = cls._CURRENCY.get(market, "")
        return q

    # ------------------------------------------------------------------
    @classmethod
    def _row_to_quote(
        cls,
        row: Any,
        name: str,
        symbol: str,
        market: StockMarket,
    ) -> Optional[DailyQuote]:
        date = str(row.get("time_key", ""))[:10]
        close = _to_float(row.get("close"))
        if len(date) != 10 or close <= 0:
            return None

        q = DailyQuote()
        q.source = cls.SOURCE
        q.name = name
        q.code = symbol
        q.date = date
        q.open = _to_float(row.get("open"))
        q.close = close
        q.high = _to_float(row.get("high"))
        q.low = _to_float(row.get("low"))
        q.pre_close = _to_float(row.get("last_close"))
        q.volume = _to_float(row.get("volume"))
        q.turnover = _to_float(row.get("turnover"))

        # 富途 turnover_rate 返回比例（如 0.00171），统一成项目约定的百分数。
        q.turnover_rate = _to_float(row.get("turnover_rate")) * 100.0
        q.change_pct = _to_float(row.get("change_rate"))
        if q.pre_close > 0:
            q.change = q.close - q.pre_close
            if not q.change_pct:
                q.change_pct = q.change / q.pre_close * 100.0
        q.currency = cls._CURRENCY.get(market, "")
        return q
