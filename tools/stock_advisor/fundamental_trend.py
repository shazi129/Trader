# -*- coding: utf-8 -*-
"""长期基本面趋势分析 + 外推预测 + 当前价格隐含估值。

设计要点
========
1. **回看 20 期 / 预测 4 期**：5 年历史足以覆盖一个完整周期（含监管 / 疫情等
   外生冲击），4 期外推（1 年）以内统计可靠性较高，再远不可信。
2. **双方法投票预测**：
   - 同比承接法（YoY）：`forecast = same_q_last_year * (1 + median_yoy_recent_4)`
     抗噪、保留季节性，但跟不上加速 / 减速；
   - 线性外推法：用近 8 期最小二乘拟合趋势线
     跟得上趋势但季节性强的指标会失真。
   两个预测取均值，残差标准差作置信区间宽度。
3. **隐含估值**：
   - 最新已发行股数从 `EPS_Basic` 反推（=NetIncomeAttr / EPS_Basic）；
     注：EPS 用的是加权平均股数，与期末股数有 ~1% 误差，对 PE 估值影响可忽略。
   - TTM 净利润 = 最近 4 期 NetIncomeAttr 之和；
   - 当前 PE = 市值 / TTM 净利；
   - 隐含 PE = 市值 / 未来 4 期预测净利之和（forward PE）；
   - 公允价格区间 = 历史 PE 中位数 × 预测 EPS（再 ±20% 估值带）。
4. **纯 Python**：项目无 numpy / pandas，自实现回归 / 中位数 / 标准差。

输出模型
========
``FundamentalTrend`` —— 一个 dataclass，包含：历史轨迹表 / 趋势归纳 /
4 期预测 / 隐含估值四个子结果。渲染层负责 markdown。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from statistics import median
from typing import Optional

from utils.logger import get_logger

_log = get_logger(__name__)


# ===========================================================================
# 配置
# ===========================================================================

LOOKBACK_QUARTERS = 20      # 回看 5 年（20 个季度）
FORECAST_QUARTERS = 4       # 外推未来 4 个季度（1 年）
TREND_FIT_QUARTERS = 8      # 线性回归取最近 8 期（避开 2022 年监管影响）
YOY_MEDIAN_WINDOW = 4       # 同比承接法取最近 4 期 YoY 中位数
PE_HISTORY_WINDOW = 12      # 历史 PE 中位数取最近 12 期（3 年），避免早期
                            # 高成长高估值期拉偏中枢


# ===========================================================================
# 数据结构
# ===========================================================================

@dataclass
class HistoryPoint:
    """单期财报的精简切片，用于历史轨迹展示。"""
    period_end: str             # YYYY-MM-DD
    period_label: str           # "2025-Q3" 等
    revenue: Optional[float]
    net_income_attr: Optional[float]
    revenue_yoy: Optional[float]
    net_income_yoy: Optional[float]
    gross_margin: Optional[float]
    net_margin: Optional[float]
    roe: Optional[float]
    debt_to_assets: Optional[float]


@dataclass
class TrendInsight:
    """单个指标的趋势归纳（基于近 N 期数据）。"""
    metric: str                 # 指标显示名
    central_value: float        # 中枢值（中位数）
    slope_per_year: float       # 年化斜率（指标单位/年）
    direction: str              # "改善" / "恶化" / "稳定" / "加速" / "减速"
    description: str            # 一句话叙事


@dataclass
class ForecastPoint:
    """单个未来季度的预测结果。"""
    period_label: str           # "2026-Q2"
    revenue_forecast: Optional[float]      # 元
    net_income_forecast: Optional[float]   # 元
    confidence_pct: float       # 残差 std / 均值的相对置信度（越小越准）


@dataclass
class ImpliedValuation:
    """基于当前价格 + 预测净利的隐含估值。"""
    shares_outstanding: float           # 股（从 EPS 反推）
    market_cap: float                   # 元
    ttm_net_income: float               # TTM 归母净利
    forward_net_income: float           # 未来 4 期预测净利之和
    pe_ttm: Optional[float]             # 当前 PE_TTM
    pe_forward: Optional[float]         # 远期 PE（基于预测）
    pe_history_median: Optional[float]  # 历史 PE 中位数（近 N 期）
    fair_price_low: Optional[float]     # 公允价格区间下限
    fair_price_high: Optional[float]    # 公允价格区间上限
    fair_price_mid: Optional[float]     # 公允价格中值
    upside_pct: Optional[float]         # 当前价相对 mid 的上涨空间（小数）


@dataclass
class FundamentalTrend:
    """长期基本面分析报告完整结果。"""
    period_count: int                              # 实际可用期数
    history: list[HistoryPoint] = field(default_factory=list)
    trends: list[TrendInsight] = field(default_factory=list)
    forecast: list[ForecastPoint] = field(default_factory=list)
    valuation: Optional[ImpliedValuation] = None
    summary: str = ""                              # 综合判断段落
    warnings: list[str] = field(default_factory=list)


# ===========================================================================
# 主入口
# ===========================================================================

def analyze_long_term(rows: list[dict],
                      current_price: Optional[float] = None,
                      *,
                      lookback: int = LOOKBACK_QUARTERS,
                      forecast_n: int = FORECAST_QUARTERS,
                      price_history: Optional[dict[str, float]] = None,
                      ) -> Optional[FundamentalTrend]:
    """从财报历史 rows 算长期趋势 + 预测 + 隐含估值。

    :param rows: ``FinancialReportRepository.get_reports()`` 的返回值（按 PeriodEnd 升序，
        已 PIT 过滤）。
    :param current_price: 当前股价。None 时跳过隐含估值计算。
    :param lookback: 回看期数；rows 不足时取全部。
    :param forecast_n: 外推几期。
    :param price_history: 可选。``{date: close}`` 字典，用于算历史 PE 中位数。
        建议传入 ``announce_date → close`` 映射（每份财报公告日的真实收盘价）。
        缺省时降级用「当前价 / 历史 NI_TTM」近似。
    :return: ``FundamentalTrend`` 或 None（数据不足）
    """
    if not rows:
        return None

    # 1. 截取最近 lookback 期
    recent = rows[-lookback:] if len(rows) > lookback else list(rows)
    if len(recent) < 4:
        _log.info("财报数据不足 4 期，长期分析跳过")
        return None

    result = FundamentalTrend(period_count=len(recent))

    # 2. 历史轨迹（每期一行）
    yoy_lookup = _build_yoy_lookup(rows)   # 用全量 rows 找上年同期，更准
    result.history = [_build_history_point(r, yoy_lookup) for r in recent]

    # 3. 趋势归纳
    result.trends = _compute_trends(result.history)

    # 4. 外推预测
    result.forecast = _forecast_future(result.history, n=forecast_n)

    # 5. 隐含估值
    if current_price is not None:
        result.valuation = _compute_valuation(
            rows, current_price, result.forecast,
            price_history=price_history,
        )

    # 6. 综合叙事
    result.summary = _build_summary(result)

    return result


# ===========================================================================
# 历史轨迹
# ===========================================================================

def _build_yoy_lookup(rows: list[dict]) -> dict[str, dict]:
    """建立 PeriodEnd → row 的 lookup，用于查上年同期。"""
    return {r["PeriodEnd"]: r for r in rows if r.get("PeriodEnd")}


def _yoy_period(pe: str) -> Optional[str]:
    """``"2025-09-30"`` → ``"2024-09-30"``；解析失败返回 None。"""
    try:
        d = date.fromisoformat(pe)
    except (ValueError, TypeError):
        return None
    return f"{d.year - 1:04d}-{d.month:02d}-{d.day:02d}"


def _quarter_label(pe: str) -> str:
    """``"2025-09-30"`` → ``"2025-Q3"``。"""
    try:
        d = date.fromisoformat(pe)
    except (ValueError, TypeError):
        return pe
    q = {3: "Q1", 6: "Q2", 9: "Q3", 12: "Q4"}.get(d.month, "?")
    return f"{d.year:04d}-{q}"


def _f(v) -> Optional[float]:
    if v is None or v == "":
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f


def _safe_ratio(num: Optional[float], den: Optional[float]) -> Optional[float]:
    if num is None or den is None or den == 0:
        return None
    return num / den


def _safe_yoy(curr: Optional[float], prev: Optional[float]) -> Optional[float]:
    if curr is None or prev is None or prev <= 0:
        return None
    return curr / prev - 1.0


def _build_history_point(r: dict, lookup: dict[str, dict]) -> HistoryPoint:
    pe = r["PeriodEnd"]
    rev = _f(r.get("Revenue"))
    ni = _f(r.get("NetIncomeAttr"))
    gp = _f(r.get("GrossProfit"))
    tl = _f(r.get("TotalLiabilities"))
    ta = _f(r.get("TotalAssets"))
    teq = _f(r.get("TotalEquityAttr")) or _f(r.get("TotalEquity"))

    yoy_pe = _yoy_period(pe)
    prev = lookup.get(yoy_pe) if yoy_pe else None
    rev_yoy = _safe_yoy(rev, _f(prev.get("Revenue")) if prev else None)
    ni_yoy = _safe_yoy(ni, _f(prev.get("NetIncomeAttr")) if prev else None)

    return HistoryPoint(
        period_end=pe,
        period_label=_quarter_label(pe),
        revenue=rev,
        net_income_attr=ni,
        revenue_yoy=rev_yoy,
        net_income_yoy=ni_yoy,
        gross_margin=_safe_ratio(gp, rev),
        net_margin=_safe_ratio(ni, rev),
        roe=_safe_ratio(ni, teq),
        debt_to_assets=_safe_ratio(tl, ta),
    )


# ===========================================================================
# 趋势归纳：线性回归 + 中位数
# ===========================================================================

def _linear_regress(values: list[Optional[float]]) -> Optional[tuple[float, float]]:
    """对一段时间序列做最小二乘拟合 y = a*t + b（t=0,1,2,...），返回 (a, b)。

    None 值会被跳过；样本不足 3 个返回 None。
    """
    pairs = [(i, v) for i, v in enumerate(values) if v is not None]
    if len(pairs) < 3:
        return None
    n = len(pairs)
    sum_t = sum(i for i, _ in pairs)
    sum_y = sum(v for _, v in pairs)
    sum_tt = sum(i * i for i, _ in pairs)
    sum_ty = sum(i * v for i, v in pairs)
    denom = n * sum_tt - sum_t * sum_t
    if denom == 0:
        return None
    a = (n * sum_ty - sum_t * sum_y) / denom
    b = (sum_y - a * sum_t) / n
    return a, b


def _median_or_none(vals: list[Optional[float]]) -> Optional[float]:
    clean = [v for v in vals if v is not None]
    return median(clean) if clean else None


def _compute_trends(history: list[HistoryPoint]) -> list[TrendInsight]:
    """对核心比率指标算趋势。

    重要：YoY 类指标对基数效应极敏感（如 2023Q4 减值损失反转造成的 -74%
    YoY 完全是基数效应而非真实减速），所以 YoY 不做趋势线，只在叙事里
    用「近 4 期 YoY 中位数 vs 近 8 期 YoY 中位数」对比来判定加速/减速。
    """
    fit_window = history[-TREND_FIT_QUARTERS:] if len(history) >= TREND_FIT_QUARTERS \
        else history

    results: list[TrendInsight] = []

    def _fit_ratio(metric: str, attr: str, *,
                    tag_improve: str, tag_worsen: str) -> None:
        """对比率类指标（毛利率 / 净利率 / ROE / 负债率）做线性回归。"""
        series = [getattr(h, attr) for h in fit_window]
        central = _median_or_none(series)
        ab = _linear_regress(series)
        if central is None or ab is None:
            return
        a, _ = ab
        slope_per_year = a * 4   # 4 个季度 = 1 年
        threshold = abs(central) * 0.02 if central else 0.005
        if slope_per_year > threshold:
            direction = tag_improve
        elif slope_per_year < -threshold:
            direction = tag_worsen
        else:
            direction = "稳定"

        desc = (f"中枢 {central * 100:.2f}%，年化斜率 "
                f"{slope_per_year * 100:+.2f}pct/年 → {direction}")
        results.append(TrendInsight(
            metric=metric,
            central_value=central,
            slope_per_year=slope_per_year,
            direction=direction,
            description=desc,
        ))

    _fit_ratio("毛利率", "gross_margin",
               tag_improve="改善 ↑", tag_worsen="恶化 ↓")
    _fit_ratio("净利率", "net_margin",
               tag_improve="改善 ↑", tag_worsen="恶化 ↓")
    _fit_ratio("ROE（单期）", "roe",
               tag_improve="改善 ↑", tag_worsen="恶化 ↓")
    _fit_ratio("资产负债率", "debt_to_assets",
               tag_improve="上升 ↑", tag_worsen="下降 ↓")

    # YoY 类指标：用「近 4 期中位数 vs 近 8 期中位数」对比，避免基数效应误判
    _yoy_compare(results, history, "营收 YoY", "revenue_yoy")
    _yoy_compare(results, history, "归母净利 YoY", "net_income_yoy")

    return results


def _yoy_compare(out: list[TrendInsight], history: list[HistoryPoint],
                  metric: str, attr: str) -> None:
    """用「近 4 期 vs 近 8 期」中位数对比法判断 YoY 加速/减速。

    这个方法对基数效应免疫——因为基数异常季度在两个窗口里都会出现，
    取中位数后影响互相抵消。
    """
    recent_4 = [getattr(h, attr) for h in history[-4:]]
    recent_8 = [getattr(h, attr) for h in history[-8:]]
    med_4 = _median_or_none(recent_4)
    med_8 = _median_or_none(recent_8)
    if med_4 is None or med_8 is None:
        return
    diff = med_4 - med_8
    threshold = 0.02   # 2pct 以上的中位数差异才算明显
    if diff > threshold:
        direction = "加速 ↑"
    elif diff < -threshold:
        direction = "减速 ↓"
    else:
        direction = "稳定"
    desc = (f"近 4 期中位数 {med_4 * 100:+.2f}% vs 近 8 期 {med_8 * 100:+.2f}% "
            f"→ {direction}")
    out.append(TrendInsight(
        metric=metric,
        central_value=med_4,
        slope_per_year=diff * 4,   # 复用字段；展示层会用 description
        direction=direction,
        description=desc,
    ))


# ===========================================================================
# 外推预测：双方法投票
# ===========================================================================

def _forecast_future(history: list[HistoryPoint],
                      n: int) -> list[ForecastPoint]:
    """外推未来 n 期的 Revenue / NetIncomeAttr。

    方法 A（YoY 承接）：取近 4 期 YoY 中位数承接到上年同期。
    方法 B（线性外推）：用近 8 期数据拟合直线外推。
    最终预测 = (A + B) / 2；置信区间宽度 = abs(A - B) / mean。
    """
    if len(history) < 5:
        return []

    # 1. 准备数据
    revenues = [h.revenue for h in history]
    net_incomes = [h.net_income_attr for h in history]
    period_labels = [h.period_label for h in history]
    period_ends = [h.period_end for h in history]

    # 2. 近 4 期 YoY 中位数（同比承接法用）
    rev_yoys = [h.revenue_yoy for h in history[-YOY_MEDIAN_WINDOW:]]
    ni_yoys = [h.net_income_yoy for h in history[-YOY_MEDIAN_WINDOW:]]
    med_rev_yoy = _median_or_none(rev_yoys)
    med_ni_yoy = _median_or_none(ni_yoys)

    # 3. 近 8 期线性回归（线性外推法用）
    fit_rev = _linear_regress(revenues[-TREND_FIT_QUARTERS:])
    fit_ni = _linear_regress(net_incomes[-TREND_FIT_QUARTERS:])

    forecasts: list[ForecastPoint] = []
    last_idx = len(history) - 1

    for i in range(1, n + 1):
        future_pe = _next_quarter_end(period_ends[last_idx], i)
        future_label = _quarter_label(future_pe)

        # 方法 A：同比承接（找上年同期实际值）
        same_q_last_year = _find_same_quarter_last_year(
            history, future_pe
        )
        rev_a = (same_q_last_year.revenue * (1 + med_rev_yoy)
                 if (same_q_last_year and same_q_last_year.revenue
                     and med_rev_yoy is not None) else None)
        ni_a = (same_q_last_year.net_income_attr * (1 + med_ni_yoy)
                if (same_q_last_year and same_q_last_year.net_income_attr
                    and med_ni_yoy is not None) else None)

        # 方法 B：线性外推
        t_future = TREND_FIT_QUARTERS - 1 + i
        # ↑ 线性回归坐标：拟合窗口的最后一个点是 t=window-1，再往后 +i
        rev_b = (fit_rev[0] * t_future + fit_rev[1]) if fit_rev else None
        ni_b = (fit_ni[0] * t_future + fit_ni[1]) if fit_ni else None

        rev_pred, rev_conf = _vote(rev_a, rev_b)
        ni_pred, ni_conf = _vote(ni_a, ni_b)

        forecasts.append(ForecastPoint(
            period_label=future_label,
            revenue_forecast=rev_pred,
            net_income_forecast=ni_pred,
            # 置信度用两预测分歧度（越大越不准）；取均值代表整体
            confidence_pct=max(rev_conf, ni_conf),
        ))

    return forecasts


def _vote(a: Optional[float], b: Optional[float]) -> tuple[Optional[float], float]:
    """投票合并两个预测值，返回 (mean, divergence_pct)。

    - 都有：mean = (a+b)/2, divergence = |a-b|/mean
    - 只有 a 或 b：返回那个值，divergence = 0.15（默认中等不确定度）
    - 都没有：返回 (None, 1.0)
    """
    if a is not None and b is not None:
        m = (a + b) / 2
        if m == 0:
            return m, 0.5
        return m, abs(a - b) / abs(m)
    if a is not None:
        return a, 0.15
    if b is not None:
        return b, 0.15
    return None, 1.0


def _next_quarter_end(pe: str, n: int) -> str:
    """``"2026-03-31"``, n=1 → ``"2026-06-30"``；季末日历精确处理。"""
    try:
        d = date.fromisoformat(pe)
    except (ValueError, TypeError):
        return pe
    # 只用月份索引推进
    month_to_q = {3: 1, 6: 2, 9: 3, 12: 4}
    q = month_to_q.get(d.month, 1)
    new_q = q + n
    new_year = d.year + (new_q - 1) // 4
    new_q = ((new_q - 1) % 4) + 1
    new_month = {1: 3, 2: 6, 3: 9, 4: 12}[new_q]
    new_day = {3: 31, 6: 30, 9: 30, 12: 31}[new_month]
    return f"{new_year:04d}-{new_month:02d}-{new_day:02d}"


def _find_same_quarter_last_year(history: list[HistoryPoint],
                                  future_pe: str) -> Optional[HistoryPoint]:
    """在 history 中找与 future_pe 同月日、年份-1 的那期。"""
    target = _yoy_period(future_pe)
    if not target:
        return None
    for h in history:
        if h.period_end == target:
            return h
    return None


# ===========================================================================
# 隐含估值
# ===========================================================================

def _compute_valuation(rows: list[dict], current_price: float,
                       forecast: list[ForecastPoint],
                       *,
                       price_history: Optional[dict[str, float]] = None,
                       ) -> Optional[ImpliedValuation]:
    """基于当前价 + 预测净利，算 PE_TTM、远期 PE、公允价格区间。

    股数估算：用最新一期 NetIncomeAttr / EPS_Basic（EPS 是加权平均股数，
    误差 ~1%，对 PE 估值影响可忽略）。
    """
    # 1. 最新股数
    shares = _estimate_shares(rows)
    if shares is None:
        return None

    # 2. TTM 净利（最近 4 期）
    last_4 = rows[-4:] if len(rows) >= 4 else rows
    ttm_ni_vals = [_f(r.get("NetIncomeAttr")) for r in last_4]
    ttm_ni_clean = [v for v in ttm_ni_vals if v is not None]
    if len(ttm_ni_clean) < 4:
        return None
    ttm_ni = sum(ttm_ni_clean)

    market_cap = current_price * shares
    pe_ttm = market_cap / ttm_ni if ttm_ni > 0 else None

    # 3. 远期 PE（用未来 4 期预测净利之和）
    forward_ni_vals = [f.net_income_forecast for f in forecast
                       if f.net_income_forecast is not None]
    forward_ni = sum(forward_ni_vals) if len(forward_ni_vals) >= 4 else 0.0
    pe_forward = (market_cap / forward_ni
                  if forward_ni > 0 else None)

    # 4. 历史 PE 中位数：优先用真实历史股价，缺失时用近似法
    pe_history = _compute_historical_pe_distribution(
        rows, current_price, shares, price_history=price_history,
    )
    # 只取最近 PE_HISTORY_WINDOW 期（避免早期高成长高估值期拉偏中位数）
    pe_history_recent = pe_history[-PE_HISTORY_WINDOW:] if pe_history else []
    pe_med = _median_or_none(pe_history_recent) if pe_history_recent else None

    # 5. 公允价格区间
    fair_low = fair_high = fair_mid = None
    upside = None
    if pe_med is not None and forward_ni > 0:
        eps_forward = forward_ni / shares
        fair_mid = pe_med * eps_forward
        fair_low = fair_mid * 0.8
        fair_high = fair_mid * 1.2
        upside = fair_mid / current_price - 1.0

    return ImpliedValuation(
        shares_outstanding=shares,
        market_cap=market_cap,
        ttm_net_income=ttm_ni,
        forward_net_income=forward_ni,
        pe_ttm=pe_ttm,
        pe_forward=pe_forward,
        pe_history_median=pe_med,
        fair_price_low=fair_low,
        fair_price_high=fair_high,
        fair_price_mid=fair_mid,
        upside_pct=upside,
    )


def _estimate_shares(rows: list[dict]) -> Optional[float]:
    """从最新一期的 NetIncomeAttr / EPS_Basic 反推股数。

    若 EPS 缺失，向前找直到有为止。
    """
    for r in reversed(rows):
        ni = _f(r.get("NetIncomeAttr"))
        eps = _f(r.get("EPS_Basic"))
        if ni and eps and eps > 0:
            return ni / eps
    return None


def _compute_historical_pe_distribution(rows: list[dict],
                                         current_price: float,
                                         shares: float,
                                         *,
                                         price_history: Optional[dict[str, float]] = None,
                                         ) -> list[float]:
    """近 N 期的历史 PE_TTM 列表（用于求中位数作为估值锚）。

    优先策略：``price_history``（``announce_date → close``）传入时，用每份
    财报公告日的真实收盘价 / 该期 NI_TTM 算 PE，最准确。

    降级策略：未传入历史股价时，用「当前股价 / 历史 NI_TTM」近似——这等价于
    假设股价中枢稳定，对腾讯这种股价波动大的标的会**严重偏差**（当前价低
    时算出来的历史 PE 偏低，反之偏高）。仅作为兜底。
    """
    pe_list: list[float] = []
    n = len(rows)
    # 滚动窗口：每个时间点用其前 4 期算 NI_TTM
    for end_idx in range(4, n + 1):
        window = rows[end_idx - 4:end_idx]
        ttm = [_f(r.get("NetIncomeAttr")) for r in window]
        ttm_clean = [v for v in ttm if v is not None]
        if len(ttm_clean) != 4 or sum(ttm_clean) <= 0:
            continue
        ni_ttm = sum(ttm_clean)

        # 取该期对应的"参考股价"
        if price_history is not None:
            announce = window[-1].get("AnnounceDate")
            ref_price = price_history.get(announce) if announce else None
            if ref_price is None:
                continue
        else:
            # 降级：用当前股价（带偏差，仅做兜底）
            ref_price = current_price

        market_cap_at_t = ref_price * shares
        pe_list.append(market_cap_at_t / ni_ttm)
    return pe_list


# ===========================================================================
# 综合判断（自动叙事）
# ===========================================================================

def _build_summary(t: FundamentalTrend) -> str:
    """根据 trends + forecast + valuation 拼一段自然语言总结。"""
    parts: list[str] = []

    # 趋势汇总
    improve = [tr.metric for tr in t.trends
               if "改善" in tr.direction or "加速" in tr.direction]
    worsen = [tr.metric for tr in t.trends
              if "恶化" in tr.direction or "减速" in tr.direction]
    stable = [tr.metric for tr in t.trends if tr.direction == "稳定"]

    n_improve = len(improve)
    n_worsen = len(worsen)
    if n_improve >= n_worsen + 2 and n_worsen == 0:
        parts.append(
            f"近 5 年呈现 **「全面向好」** 特征："
            f"{('、'.join(improve))} 持续改善，无指标恶化。"
        )
    elif n_worsen >= n_improve + 2 and n_improve == 0:
        parts.append(
            f"近 5 年呈现 **「全面承压」** 特征："
            f"{('、'.join(worsen))} 持续恶化，需高度警惕。"
        )
    elif improve and worsen:
        if n_improve > n_worsen:
            tone = "**「改善为主、局部承压」**"
        elif n_worsen > n_improve:
            tone = "**「承压为主、局部改善」**"
        else:
            tone = "**「分化」**"
        parts.append(
            f"近 5 年呈现 {tone} 特征："
            f"{('、'.join(improve))} 改善，{('、'.join(worsen))} 恶化"
            f"{(f'；{'、'.join(stable)} 稳定' if stable else '')}。"
        )
    else:
        parts.append("近 5 年各项指标基本稳定，无明显趋势性变化。")

    # 预测可信度
    if t.forecast:
        valid_fc = [f for f in t.forecast
                    if f.net_income_forecast is not None]
        if valid_fc:
            high_conf = sum(1 for f in valid_fc if f.confidence_pct < 0.05)
            if high_conf >= 3:
                parts.append(
                    "未来 4 个季度的预测**可信度较高**（两种方法基本一致），"
                    "趋势延续概率大。"
                )
            elif high_conf <= 1:
                parts.append(
                    "未来 4 个季度的预测**两种方法分歧较大**，可能正处于"
                    "趋势变化的拐点附近，需重点关注下一份业绩公告。"
                )

    # 估值判断
    if t.valuation and t.valuation.upside_pct is not None:
        upside = t.valuation.upside_pct
        pe_ttm = t.valuation.pe_ttm
        pe_med = t.valuation.pe_history_median

        pe_ratio = pe_ttm / pe_med if (pe_ttm and pe_med) else None
        pe_clue = ""
        if pe_ratio is not None:
            if pe_ratio < 0.85:
                pe_clue = f"（当前 PE_TTM {pe_ttm:.1f}x 显著低于 3 年中枢 {pe_med:.1f}x）"
            elif pe_ratio > 1.15:
                pe_clue = f"（当前 PE_TTM {pe_ttm:.1f}x 高于 3 年中枢 {pe_med:.1f}x）"

        if upside > 0.20:
            parts.append(
                f"基于近 3 年 PE 中枢 + 远期盈利预测，**当前股价较公允中值低约 "
                f"{upside * 100:.1f}%**，估值偏低{pe_clue}。"
            )
        elif upside < -0.20:
            parts.append(
                f"基于近 3 年 PE 中枢 + 远期盈利预测，**当前股价较公允中值高约 "
                f"{-upside * 100:.1f}%**，估值偏贵{pe_clue}。"
            )
        else:
            parts.append(
                f"基于近 3 年 PE 中枢 + 远期盈利预测，当前股价处于公允区间内"
                f"（偏离 {upside * 100:+.1f}%）{pe_clue}。"
            )

    parts.append("")
    parts.append("> **注**：以上预测基于近期趋势的简单外推，**不能预测拐点**。"
                 "遇到监管 / 政策 / 突发事件等外生冲击，结论会显著偏离。"
                 "估值结论假设市场仍按近 3 年估值水平定价。")

    return "\n\n".join(parts)
