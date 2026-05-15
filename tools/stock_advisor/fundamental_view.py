# -*- coding: utf-8 -*-
"""基本面快照视图：从 ``financial_report`` 表派生关键比率/增速指标，
供 stock_advisor 报告的「基本面」节使用。

设计要点
========
1. **不参与回测 z-score 空间**：财报是季度级数据（同季度内 60 天值不变），
   塞进 K 维 z-score 会破坏相似态匹配的统计假设。所以这里独立成节，
   只做「最新一份已公告 + 同比对比」的快照展示。
2. **PIT 合规**：只读 ``announce_date <= 当前最新交易日`` 的财报，
   避免出现"还没公告但解析时已入库"的未来函数（虽然实操中数据已公告才会
   入库，但接口层面仍按 PIT 严格过滤更稳）。
3. **NULL 容错**：港股 Q1/Q3 现金流字段经常 NULL，我们在每个派生指标里
   独立判 None，缺啥少啥即可，不抛异常。
4. **双口径展示**：港股科技股的 IFRS / Non-IFRS 双口径都展示；前者是会计
   准则口径，后者是市场主流"经调整"口径。

输出模型
========
``FundamentalSnapshot`` 是一个纯 dataclass，所有指标都允许 ``None``，渲染
层负责把 None 显示为 "N/A"。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

from database.stock_db_utils import StockDB
from utils.logger import get_logger

_log = get_logger(__name__)


# ===========================================================================
# 数据结构
# ===========================================================================

@dataclass
class FundamentalSnapshot:
    """单只股票的最新一份已公告财报派生指标。

    单位约定：
    - 比率（roe / 毛利率 / 资产负债率 / 增速等）：**小数**，0.05 = 5%；
    - 金额（revenue / net_income_attr / total_assets 等）：**元**；
    - 缺失字段一律 None，由渲染层统一显示为 "N/A"。
    """

    # ---- 元信息 ----
    period_end: str                              # 报告期末 YYYY-MM-DD
    period_type: str                             # Q1 / H1 / Q3 / ANNUAL
    announce_date: str                           # 公告日 YYYY-MM-DD
    currency: str                                # CNY / HKD / USD
    audited: bool                                # 是否经审计

    # ---- 规模（绝对值，亿元单位由渲染层除）----
    revenue: Optional[float] = None              # 营收（元）
    net_income_attr: Optional[float] = None      # 归母净利润（元）
    net_income_attr_nonifrs: Optional[float] = None  # Non-IFRS 归母（港股）
    total_assets: Optional[float] = None         # 总资产
    total_equity_attr: Optional[float] = None    # 归母权益
    operating_cash_flow: Optional[float] = None  # 经营性现金流

    # ---- 盈利能力（小数）----
    gross_margin: Optional[float] = None         # 毛利率 = GrossProfit / Revenue
    net_margin: Optional[float] = None           # 净利率 = NetIncomeAttr / Revenue
    roe_quarterly: Optional[float] = None        # 单期 ROE = NetIncomeAttr / TotalEquityAttr
    eps_basic: Optional[float] = None            # 基本 EPS（元/股）
    eps_basic_nonifrs: Optional[float] = None    # Non-IFRS 基本 EPS（港股）

    # ---- 成长性（同比，小数）----
    revenue_yoy: Optional[float] = None          # 营收同比
    net_income_yoy: Optional[float] = None       # 归母同比
    net_income_nonifrs_yoy: Optional[float] = None  # Non-IFRS 归母同比

    # ---- 财务健康 ----
    debt_to_assets: Optional[float] = None       # 资产负债率 = TotalLiabilities / TotalAssets
    cash_to_net_income: Optional[float] = None   # 盈利质量 = OCF / NetIncomeAttr
    free_cash_flow: Optional[float] = None       # 自由现金流（元，港股直接给）

    # ---- 警告（缺字段、异常值等）----
    warnings: list[str] = field(default_factory=list)


# ===========================================================================
# 主入口
# ===========================================================================

def build_snapshot(name_key: str,
                   db: StockDB,
                   *,
                   as_of: Optional[str] = None) -> Optional[FundamentalSnapshot]:
    """读 DB 算最新一份财报快照。

    :param name_key: 股票 name_key（如 ``Tencent``）
    :param db: 已打开的 ``StockDB`` 实例（调用方负责生命周期）
    :param as_of: 可选的 PIT 截止日 ``YYYY-MM-DD``。只取
        ``announce_date <= as_of`` 的财报；不传则用今天（系统时间）。
        回测时建议传当前交易日，避免拿到未公告的数据。
    :return: ``FundamentalSnapshot`` 或 None（数据库无该股票财报时）
    """
    rows = db.get_financial_reports(name_key)
    if not rows:
        _log.info("[%s] 数据库无财报数据", name_key)
        return None

    # PIT 过滤：只保留已公告的
    cutoff = as_of or datetime.now().strftime("%Y-%m-%d")
    rows = [r for r in rows if r.get("AnnounceDate")
            and r["AnnounceDate"] <= cutoff]
    if not rows:
        _log.info("[%s] 截至 %s 无已公告财报", name_key, cutoff)
        return None

    # rows 已按 PeriodEnd ASC 排序（来自 get_financial_reports），最末一份就是最新
    latest = rows[-1]

    # 找上年同期：PeriodEnd 月日相同、年份-1。容错：找不到就把同比指标置 None。
    yoy_row = _find_yoy_row(rows, latest)

    snap = FundamentalSnapshot(
        period_end=latest["PeriodEnd"],
        period_type=latest.get("PeriodType") or "",
        announce_date=latest["AnnounceDate"],
        currency=latest.get("Currency") or "",
        audited=bool(latest.get("Audited")),
    )

    # ---- 规模 ----
    snap.revenue = _f(latest.get("Revenue"))
    snap.net_income_attr = _f(latest.get("NetIncomeAttr"))
    snap.net_income_attr_nonifrs = _f(latest.get("NetIncomeAttr_NonIFRS"))
    snap.total_assets = _f(latest.get("TotalAssets"))
    snap.total_equity_attr = _f(latest.get("TotalEquityAttr"))
    # 港股没有 TotalEquityAttr 时回落到 TotalEquity（含少数股东，略偏大但能用）
    if snap.total_equity_attr is None:
        snap.total_equity_attr = _f(latest.get("TotalEquity"))
    snap.operating_cash_flow = _f(latest.get("OperatingCashFlow"))
    snap.free_cash_flow = _f(latest.get("FreeCashFlow"))
    snap.eps_basic = _f(latest.get("EPS_Basic"))
    snap.eps_basic_nonifrs = _f(latest.get("EPS_Basic_NonIFRS"))

    # ---- 盈利能力（比率，小数）----
    gp = _f(latest.get("GrossProfit"))
    if gp is not None and snap.revenue:
        snap.gross_margin = gp / snap.revenue
    if snap.net_income_attr is not None and snap.revenue:
        snap.net_margin = snap.net_income_attr / snap.revenue
    if snap.net_income_attr is not None and snap.total_equity_attr:
        snap.roe_quarterly = snap.net_income_attr / snap.total_equity_attr

    # ---- 财务健康 ----
    tl = _f(latest.get("TotalLiabilities"))
    if tl is not None and snap.total_assets:
        snap.debt_to_assets = tl / snap.total_assets
    if snap.operating_cash_flow is not None and snap.net_income_attr \
            and snap.net_income_attr != 0:
        snap.cash_to_net_income = snap.operating_cash_flow / snap.net_income_attr

    # ---- 同比增速 ----
    if yoy_row is not None:
        snap.revenue_yoy = _yoy(snap.revenue, _f(yoy_row.get("Revenue")))
        snap.net_income_yoy = _yoy(
            snap.net_income_attr, _f(yoy_row.get("NetIncomeAttr"))
        )
        snap.net_income_nonifrs_yoy = _yoy(
            snap.net_income_attr_nonifrs,
            _f(yoy_row.get("NetIncomeAttr_NonIFRS")),
        )
    else:
        snap.warnings.append(
            f"未找到 {latest['PeriodEnd']} 的上年同期财报，同比指标缺失"
        )

    return snap


# ===========================================================================
# 内部工具
# ===========================================================================

def _f(v) -> Optional[float]:
    """安全转 float；None / 空串 / 转换失败 → None。"""
    if v is None or v == "":
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f != f:  # NaN
        return None
    return f


def _yoy(curr: Optional[float], prev: Optional[float]) -> Optional[float]:
    """同比增速（小数，0.05 = +5%）。

    - 任一为 None → None
    - 上年同期为 0 或负 → None（同比口径不适用）
    """
    if curr is None or prev is None:
        return None
    if prev <= 0:
        return None
    return curr / prev - 1.0


def _find_yoy_row(rows: list[dict], latest: dict) -> Optional[dict]:
    """在历史财报里找到与 latest 同月日、年份-1 的那一份。

    例：latest.PeriodEnd = '2025-09-30' → 找 '2024-09-30'。
    找不到（早期年份 / 当年缺一期）返回 None。
    """
    pe = latest.get("PeriodEnd") or ""
    try:
        d = date.fromisoformat(pe)
    except ValueError:
        return None
    target = f"{d.year - 1:04d}-{d.month:02d}-{d.day:02d}"
    for r in rows:
        if r.get("PeriodEnd") == target:
            return r
    return None
