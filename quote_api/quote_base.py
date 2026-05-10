# -*- coding: utf-8 -*-
"""行情接口基类与统一数据模型"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Optional


class DailyQuote:
    """单日行情快照（与数据源无关的统一模型）"""

    def __init__(self) -> None:
        self.name: str = ""          # 股票中文名/代码标识
        self.code: str = ""          # 交易所原始代码
        self.date: str = ""          # 日期, 格式: YYYY-MM-DD
        self.open: float = 0.0       # 开盘价
        self.close: float = 0.0      # 收盘价
        self.high: float = 0.0       # 最高价
        self.low: float = 0.0        # 最低价
        self.pre_close: float = 0.0  # 昨收价（可选，部分接口提供）
        self.volume: float = 0.0     # 成交量（股/手，按源决定，实现内统一为"股"）
        self.turnover: float = 0.0   # 成交额（元）
        self.turnover_rate: float = 0.0  # 换手率 %（部分数据源不提供时为 0）
        self.source: str = ""        # 数据来源标识
        self.change: float = 0.0     # 涨跌额（派生字段，可由上层计算后填入）
        self.change_pct: float = 0.0 # 涨跌幅 %（派生字段）
        self.currency: str = ""      # 币种（派生字段，如 CNY/HKD/USD）

    def is_valid(self) -> bool:
        """简单校验：至少要有日期和收盘价"""
        return bool(self.date) and self.close > 0

    def __str__(self) -> str:
        return (
            "DailyQuote(source=%s, name=%s, code=%s, date=%s, "
            "open=%.4f, close=%.4f, high=%.4f, low=%.4f, "
            "pre_close=%.4f, volume=%.0f, turnover=%.2f, turnover_rate=%.4f)"
            % (
                self.source, self.name, self.code, self.date,
                self.open, self.close, self.high, self.low,
                self.pre_close, self.volume, self.turnover, self.turnover_rate,
            )
        )


class StockFundamental:
    """股票基本面数据（低频更新：季度/年度）"""

    def __init__(self) -> None:
        # 标识
        self.name: str = ""          # 股票名称/键
        self.code: str = ""          # 交易所代码
        self.date: str = ""          # 报告期 YYYY-MM-DD
        
        # 估值类
        self.pe_ttm: float = 0.0    # 市盈率 TTM
        self.pb: float = 0.0        # 市净率
        self.ps_ttm: float = 0.0     # 市销率 TTM
        self.pcf_ttm: float = 0.0   # 市现率 TTM
        self.ev_ebitda: float = 0.0 # EV/EBITDA
        
        # 盈利类
        self.eps_ttm: float = 0.0    # 每股收益 TTM
        self.eps: float = 0.0        # 最新季度 EPS
        self.roe_ttm: float = 0.0    # 净资产收益率 TTM %
        self.roa: float = 0.0        # 资产回报率 %
        self.roc: float = 0.0        # 资本回报率 %
        
        # 成长类
        self.eps_growth_ttm: float = 0.0  # EPS同比增长率 %
        self.revenue_growth_ttm: float = 0.0  # 营收同比增长率 %
        self.profit_growth_ttm: float = 0.0   # 净利润同比增长率 %
        
        # 股息类
        self.dividend_yield: float = 0.0  # 股息率 %
        self.dividend_per_share: float = 0.0  # 每股股息
        
        # 规模类
        self.market_cap: float = 0.0   # 总市值（元/当地货币）
        self.circulating_market_cap: float = 0.0  # 流通市值
        
        # 财务健康类
        self.debt_to_equity: float = 0.0  # 资产负债率 %
        self.current_ratio: float = 0.0    # 流动比率
        
        # 评级类（可选）
        self.analyst_rating: float = 0.0   # 分析师评级均值（1-5）
        self.target_price: float = 0.0     # 目标价
        
        self.source: str = ""      # 数据来源

    def is_valid(self) -> bool:
        """简单校验"""
        return bool(self.name) and (self.pe_ttm > 0 or self.pb > 0 or self.market_cap > 0)

    def __str__(self) -> str:
        return (
            "StockFundamental(name=%s, code=%s, date=%s, "
            "PE=%.2f, PB=%.2f, EPS=%.4f, ROE=%.2f%%, MarketCap=%.0f)"
            % (self.name, self.code, self.date,
               self.pe_ttm, self.pb, self.eps_ttm, self.roe_ttm, self.market_cap)
        )


# 日期入参统一类型别名
DateLike = Optional[datetime.datetime | str]


class QuoteAPI:
    """所有行情数据源的抽象基类

    子类必须实现：
        get_klines(name, start_date, end_date, limit) -> list[DailyQuote]

    基类提供默认的 get_daily_quote 实现：内部复用 get_klines。
    子类若有更高效的"按日"接口，可单独 override。
    """

    # 子类需覆盖：数据源标识
    SOURCE: str = "base"

    # 统一 HTTP 超时
    DEFAULT_TIMEOUT: int = 8

    def __init__(self) -> None:
        self._api_stocks: dict[str, str] = {}  # name_key -> stock_code
        self._load_api_config()

    # ------------------------------------------------------------------
    def _load_api_config(self) -> None:
        """从子类所在目录的 config.json 加载 name_key -> stock_code 映射。

        config.json 格式: {"stocks": {"Tencent": "hk00700", ...}}
        """
        try:
            # 取子类文件所在目录
            import inspect
            cls_file = inspect.getfile(type(self))
            cfg_path = Path(cls_file).parent / "config.json"
            if cfg_path.exists():
                with open(cfg_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                stocks = data.get("stocks")
                if isinstance(stocks, dict):
                    self._api_stocks = {str(k): str(v) for k, v in stocks.items()}
        except Exception as e:
            print(f"[{self.SOURCE}] load api config error: {e}")

    # ------------------------------------------------------------------
    def is_supported(self, name_key: str) -> bool:
        """判断当前 API 是否支持指定的 name_key。

        以本数据源的 config.json（即 self._api_stocks）为权威清单。
        子类如有更复杂规则，可自行 override。
        """
        return name_key in self._api_stocks

    def get_stock_code(self, name_key: str) -> Optional[str]:
        """获取 name_key 对应的 API 专属 stock_code；不支持则返回 None。"""
        return self._api_stocks.get(name_key)

    # ------------------------------------------------------------------
    # 子类必须实现：批量 K 线
    # ------------------------------------------------------------------
    def get_klines(
        self,
        name: str,
        start_date: DateLike = None,
        end_date: DateLike = None,
        limit: Optional[int] = None,
    ) -> list[DailyQuote]:
        """
        批量获取一段区间的日 K 线。

        :param name:        config.global_stock_list 中的键
        :param start_date:  起始日期（含），支持 datetime / "YYYY-MM-DD" / "YYYYMMDD"；
                            None 表示数据源的默认最早日期
        :param end_date:    结束日期（含），同上；None 表示最新交易日
        :param limit:       最多返回多少条（None 表示不限制，取全部）；
                            当 start_date/end_date 未给出时，可只靠 limit 控制条数
        :return: DailyQuote 列表，按日期升序；无数据返回 []
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # 默认按单日实现：复用 get_klines
    # ------------------------------------------------------------------
    def get_daily_quote(
        self,
        name: str,
        date: DateLike = None,
    ) -> Optional[DailyQuote]:
        """
        获取某只股票在指定日期的行情快照。

        :param name: config.global_stock_list 中的键
        :param date: 目标日期；支持 datetime 或 "YYYY-MM-DD"；None 表示最新交易日
        :return: DailyQuote；获取失败返回 None
        """
        target = self.normalize_date(date)
        if target is None:
            # 最近一条
            items = self.get_klines(name, limit=1)
            return items[-1] if items else None

        items = self.get_klines(name, start_date=target, end_date=target, limit=1)
        if not items:
            return None
        # 精确匹配，防止数据源把 end_date 当成开区间导致错配
        for q in items:
            if q.date == target:
                return q
        return items[-1]

    # ------------------------------------------------------------------
    # 基本面数据（子类可选实现）
    # ------------------------------------------------------------------
    def get_fundamentals(self, name: str) -> Optional[StockFundamental]:
        """
        获取股票基本面数据。
        
        :param name: config.global_stock_list 中的键
        :return: StockFundamental；获取失败返回 None
        """
        # 默认实现：返回 None，子类可 override
        return None

    # ------------------------------------------------------------------
    # 工具方法（子类可复用）
    # ------------------------------------------------------------------
    @staticmethod
    def normalize_date(date: DateLike) -> Optional[str]:
        """把日期统一成 'YYYY-MM-DD'；None 原样返回"""
        if date is None:
            return None
        if isinstance(date, datetime.datetime):
            return date.strftime("%Y-%m-%d")
        if isinstance(date, str):
            # 允许 '20250204' 或 '2025-02-04'
            s = date.strip().replace("/", "-")
            if len(s) == 8 and s.isdigit():
                return "%s-%s-%s" % (s[:4], s[4:6], s[6:8])
            return s
        raise TypeError("unsupported date type: %s" % type(date))

    # ------------------------------------------------------------------
    @staticmethod
    def sort_and_trim(
        quotes: list[DailyQuote],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[DailyQuote]:
        """按日期升序排序、按 [start_date, end_date] 过滤、按 limit 截取末尾 N 条。"""
        items = [q for q in quotes if q and q.date]
        items.sort(key=lambda x: x.date)
        if start_date:
            items = [q for q in items if q.date >= start_date]
        if end_date:
            items = [q for q in items if q.date <= end_date]
        if limit is not None and limit > 0:
            items = items[-limit:]
        return items
