# -*- coding: utf-8 -*-

"""
东方财富接口字段映射 + 统一解析器
支持以下三类响应：
1) /api/qt/stock/get      -> 快照行情
2) /api/qt/stock/kline/get -> K线历史
3) /api/qt/stock/trends2/get -> 分时走势

可解析 JSON 或 JSONP 文本。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
import json
import re


# =========================
# 字段映射字典
# =========================

SNAPSHOT_FIELD_MAP: dict[str, str] = {
    "f57": "code",                  # 证券代码
    "f58": "name",                  # 证券名称
    "f43": "last_price",            # 最新价
    "f44": "high",                  # 最高价
    "f45": "low",                   # 最低价
    "f46": "open",                  # 今开
    "f47": "volume",                # 成交量
    "f48": "amount",                # 成交额
    "f49": "outside_volume",        # 外盘(部分市场)
    "f50": "volume_ratio",          # 量比/相关比率(口径随市场变化)
    "f59": "market_type",           # 市场标识
    "f60": "pre_close",             # 昨收
    "f78": "turnover_rate",         # 换手率(部分市场)
    "f85": "total_market_value",    # 总市值
    "f86": "circulating_market_value",  # 流通市值
    "f107": "market",               # 市场代码
    "f111": "trade_status",         # 交易状态
    "f116": "total_capital",        # 总股本/总市值相关(按市场口径)
    "f117": "circulating_capital",  # 流通股本/流通市值相关(按市场口径)
    "f118": "industry_type",        # 行业或分类标识
    "f152": "price_state",          # 价格状态/方向标识
    "f161": "trade_count",          # 成交笔数/扩展统计
    "f162": "pe_dynamic",           # 动态市盈率(部分市场可能为'-')
    "f163": "rise_count",           # 涨家数/上涨笔数(扩展)
    "f164": "fall_count",           # 跌家数/下跌笔数(扩展)
    "f168": "amplitude",            # 振幅
    "f169": "change_amount",        # 涨跌额
    "f170": "change_percent",       # 涨跌幅
    "f171": "speed",                # 涨速/扩展字段
    "f172": "currency",             # 币种
    "f177": "pb",                   # 市净率(部分市场)
    "f180": "is_suspended",         # 停牌相关状态
    "f181": "committee_ratio",      # 委比/扩展字段
    "f292": "security_type",        # 证券类型
    "f751": "inner_code",           # 内部代码
    "f752": "inner_market",         # 内部市场代码
}

# K线 fields2 对应：f51~f65
KLINE_FIELD_MAP: dict[str, str] = {
    "f51": "date",
    "f52": "open",
    "f53": "close",
    "f54": "high",
    "f55": "low",
    "f56": "volume",
    "f57": "amount",
    "f58": "amplitude",
    "f59": "change_percent",
    "f60": "change_amount",
    "f61": "turnover_rate",
    "f62": "ext_62",
    "f63": "ext_63",
    "f64": "ext_64",
    "f65": "ext_65",
}

KLINE_FIELDS2_DEFAULT: list[str] = [
    "f51", "f52", "f53", "f54", "f55", "f56", "f57", "f58", "f59", "f60", "f61", "f62", "f63", "f64", "f65"
]

# 分时 fields2 常见：f51,f52,f53,f54,f55,f58
# 与 trends 单条字符串通常一一对应：time, open, close, high, low, avg_price
TRENDS_FIELD_MAP: dict[str, str] = {
    "f51": "time",
    "f52": "open",
    "f53": "close",
    "f54": "high",
    "f55": "low",
    "f58": "avg_price",
}

TRENDS_FIELDS2_DEFAULT: list[str] = ["f51", "f52", "f53", "f54", "f55", "f58"]


# =========================
# 结构化对象
# =========================

@dataclass
class SnapshotQuote:
    code: str = ""
    name: str = ""
    last_price: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    pre_close: Optional[float] = None
    volume: Optional[float] = None
    amount: Optional[float] = None
    change_amount: Optional[float] = None
    change_percent: Optional[float] = None
    amplitude: Optional[float] = None
    turnover_rate: Optional[float] = None
    currency: str = ""
    raw: dict[str, Any] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class KlineBar:
    date: str = ""
    open: Optional[float] = None
    close: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[float] = None
    amount: Optional[float] = None
    amplitude: Optional[float] = None
    change_percent: Optional[float] = None
    change_amount: Optional[float] = None
    turnover_rate: Optional[float] = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class TrendPoint:
    time: str = ""
    open: Optional[float] = None
    close: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    avg_price: Optional[float] = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class UnifiedQuoteData:
    """统一输出对象，三类响应都可汇总到这里。"""

    code: str = ""
    name: str = ""
    market: Optional[int] = None
    snapshot: Optional[SnapshotQuote] = None
    klines: list[KlineBar] = field(default_factory=list)
    trends: list[TrendPoint] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)


# =========================
# 解析器
# =========================

class EastMoneyParser:
    _JSONP_PATTERN = re.compile(r"^\s*([\w$]+)\((.*)\)\s*;?\s*$", re.S)

    @staticmethod
    def parse_payload(payload: str | bytes | dict[str, Any]) -> dict[str, Any]:
        """
        输入可以是：
        - 原始 JSON 字符串
        - 原始 JSONP 字符串
        - 已反序列化 dict
        """
        if isinstance(payload, dict):
            return payload

        if isinstance(payload, bytes):
            payload = payload.decode("utf-8", errors="ignore")

        text = payload.strip()
        if not text:
            return {}

        # JSONP: callback({...});
        m = EastMoneyParser._JSONP_PATTERN.match(text)
        if m:
            text = m.group(2).strip()

        return json.loads(text)

    @staticmethod
    def parse_snapshot(payload: str | bytes | dict[str, Any], price_scale: Optional[float] = None) -> SnapshotQuote:
        """
        解析 /api/qt/stock/get

        price_scale: 可选价格缩放。例如部分市场字段若为“厘/千分单位”可传 1000。
                     若不传，默认不做缩放。
        """
        root = EastMoneyParser.parse_payload(payload)
        data = root.get("data") or {}

        mapped: dict[str, Any] = {}
        extra: dict[str, Any] = {}

        for f_key, f_val in data.items():
            name = SNAPSHOT_FIELD_MAP.get(f_key)
            if name:
                mapped[name] = f_val
            else:
                extra[f_key] = f_val

        def _num(v: Any) -> Optional[float]:
            if v in (None, "-"):
                return None
            try:
                return float(v)
            except (TypeError, ValueError):
                return None

        def _scaled(v: Any) -> Optional[float]:
            n = _num(v)
            if n is None:
                return None
            if price_scale:
                return n / price_scale
            return n

        quote = SnapshotQuote(
            code=str(mapped.get("code", "") or ""),
            name=str(mapped.get("name", "") or ""),
            last_price=_scaled(mapped.get("last_price")),
            open=_scaled(mapped.get("open")),
            high=_scaled(mapped.get("high")),
            low=_scaled(mapped.get("low")),
            pre_close=_scaled(mapped.get("pre_close")),
            volume=_num(mapped.get("volume")),
            amount=_num(mapped.get("amount")),
            change_amount=_scaled(mapped.get("change_amount")),
            change_percent=_num(mapped.get("change_percent")),
            amplitude=_num(mapped.get("amplitude")),
            turnover_rate=_num(mapped.get("turnover_rate")),
            currency=str(mapped.get("currency", "") or ""),
            raw=data,
            extra=extra,
        )
        return quote

    @staticmethod
    def parse_kline(
        payload: str | bytes | dict[str, Any],
        fields2: Optional[list[str]] = None,
    ) -> tuple[list[KlineBar], dict[str, Any]]:
        """
        解析 /api/qt/stock/kline/get

        返回: (klines, meta)
        """
        root = EastMoneyParser.parse_payload(payload)
        data = root.get("data") or {}
        raw_klines = data.get("klines") or []

        fields = fields2 or KLINE_FIELDS2_DEFAULT
        col_names = [KLINE_FIELD_MAP.get(f, f) for f in fields]

        bars: list[KlineBar] = []
        for row in raw_klines:
            if not isinstance(row, str):
                continue
            parts = row.split(",")
            if len(parts) < len(col_names):
                continue

            kv: dict[str, Any] = {}
            for i, col in enumerate(col_names):
                kv[col] = parts[i]

            def _f(name: str) -> Optional[float]:
                v = kv.get(name)
                if v in (None, "-"):
                    return None
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return None

            bar = KlineBar(
                date=str(kv.get("date", "") or ""),
                open=_f("open"),
                close=_f("close"),
                high=_f("high"),
                low=_f("low"),
                volume=_f("volume"),
                amount=_f("amount"),
                amplitude=_f("amplitude"),
                change_percent=_f("change_percent"),
                change_amount=_f("change_amount"),
                turnover_rate=_f("turnover_rate"),
                extra={k: v for k, v in kv.items() if k.startswith("ext_")},
            )
            bars.append(bar)

        meta = {
            "code": data.get("code"),
            "name": data.get("name"),
            "market": data.get("market"),
            "decimal": data.get("decimal"),
            "pre_close": data.get("prePrice") if "prePrice" in data else data.get("preKPrice"),
            "raw": {k: v for k, v in data.items() if k != "klines"},
        }
        return bars, meta

    @staticmethod
    def parse_trends(
        payload: str | bytes | dict[str, Any],
        fields2: Optional[list[str]] = None,
    ) -> tuple[list[TrendPoint], dict[str, Any]]:
        """
        解析 /api/qt/stock/trends2/get

        返回: (trends, meta)
        """
        root = EastMoneyParser.parse_payload(payload)
        data = root.get("data") or {}
        raw_trends = data.get("trends") or []

        fields = fields2 or TRENDS_FIELDS2_DEFAULT
        col_names = [TRENDS_FIELD_MAP.get(f, f) for f in fields]

        points: list[TrendPoint] = []
        for row in raw_trends:
            if not isinstance(row, str):
                continue
            parts = row.split(",")
            if len(parts) < len(col_names):
                continue

            kv: dict[str, Any] = {}
            for i, col in enumerate(col_names):
                kv[col] = parts[i]

            def _f(name: str) -> Optional[float]:
                v = kv.get(name)
                if v in (None, "-"):
                    return None
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return None

            point = TrendPoint(
                time=str(kv.get("time", "") or ""),
                open=_f("open"),
                close=_f("close"),
                high=_f("high"),
                low=_f("low"),
                avg_price=_f("avg_price"),
                extra={k: v for k, v in kv.items() if k not in {"time", "open", "close", "high", "low", "avg_price"}},
            )
            points.append(point)

        meta = {
            "code": data.get("code"),
            "name": data.get("name"),
            "market": data.get("market"),
            "decimal": data.get("decimal"),
            "pre_close": data.get("preClose"),
            "time": data.get("time"),
            "trends_total": data.get("trendsTotal"),
            "trade_periods": data.get("tradePeriods"),
            "raw": {k: v for k, v in data.items() if k != "trends"},
        }
        return points, meta

    @staticmethod
    def parse_unified(
        snapshot_payload: str | bytes | dict[str, Any] | None = None,
        kline_payload: str | bytes | dict[str, Any] | None = None,
        trends_payload: str | bytes | dict[str, Any] | None = None,
        snapshot_price_scale: Optional[float] = None,
    ) -> UnifiedQuoteData:
        """
        三类响应统一汇总。
        任意 payload 可为空。
        """
        result = UnifiedQuoteData()

        if snapshot_payload is not None:
            snapshot = EastMoneyParser.parse_snapshot(snapshot_payload, price_scale=snapshot_price_scale)
            result.snapshot = snapshot
            result.code = snapshot.code or result.code
            result.name = snapshot.name or result.name

        if kline_payload is not None:
            klines, k_meta = EastMoneyParser.parse_kline(kline_payload)
            result.klines = klines
            result.code = result.code or str(k_meta.get("code") or "")
            result.name = result.name or str(k_meta.get("name") or "")
            if result.market is None and k_meta.get("market") is not None:
                result.market = int(k_meta["market"])
            result.meta["kline"] = k_meta

        if trends_payload is not None:
            trends, t_meta = EastMoneyParser.parse_trends(trends_payload)
            result.trends = trends
            result.code = result.code or str(t_meta.get("code") or "")
            result.name = result.name or str(t_meta.get("name") or "")
            if result.market is None and t_meta.get("market") is not None:
                result.market = int(t_meta["market"])
            result.meta["trends"] = t_meta

        return result


# =========================
# 使用示例
# =========================

if __name__ == "__main__":
    # 这里只演示调用方式，不发请求。
    snapshot_text = '{"rc":0,"data":{"f57":"00700","f58":"腾讯控股","f43":562500,"f44":564000,"f45":543500,"f46":551000,"f47":13754474,"f48":7635420416,"f60":547500,"f169":15000,"f170":274,"f168":374,"f172":"HKD"}}'

    kline_jsonp = '__jp0({"rc":0,"data":{"code":"00700","market":116,"name":"腾讯控股","klines":["2026-03-16,551.000,562.500,564.000,543.500,13754474,7635420416.000,3.74,2.74,15.000,0.15,0,0,0,0.000"]}});'

    trends_jsonp = 'miniquotechart_jp0({"rc":0,"data":{"code":"00700","market":116,"name":"腾讯控股","trends":["2026-03-16 09:30,551.000,551.000,551.500,551.000,551.0000"]}});'

    unified = EastMoneyParser.parse_unified(
        snapshot_payload=snapshot_text,
        kline_payload=kline_jsonp,
        trends_payload=trends_jsonp,
        snapshot_price_scale=1000,  # 若快照价格字段放大1000，可在此统一缩放
    )

    print(unified)
