#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""股票综合分析工具 CLI。

用法::

    python -m tools.stock_advisor.stock_advisor Tencent
    python -m tools.stock_advisor.stock_advisor Alibaba --top-k 80
    python -m tools.stock_advisor.stock_advisor Tencent --no-write   # 只看不落盘

流程：
1. 读 DB 中该股票的 K 线 + 6 张因子表
2. 若 K 线为空 / 因子最新日期 ≠ K 线最新日期 → 调
   ``compute_and_save_factors`` 重新拉算并写回
3. 用 ``QuantAnalyzer`` 跑一次单点多因子打分（短期信号判断）
4. 用 ``HorizonBacktester`` 跑历史相似态匹配，得 5/20/60 日上涨概率
5. 把上述结果合成一份 markdown，控制台打印 + 落盘到 reports/
"""

from __future__ import annotations

import argparse
import datetime
import sys
from contextlib import closing
from pathlib import Path
from typing import Optional

# 让脚本既能 ``python -m tools.stock_advisor.stock_advisor`` 也能直跑
_THIS_DIR = Path(__file__).resolve().parent
_ROOT = _THIS_DIR.parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config  # noqa: E402
from database.stock_db_utils import StockDB  # noqa: E402
from quantitative.analyzer import (  # noqa: E402
    AnalysisReport,
    QuantFactorEngine,
    compute_probability,
    generate_summary,
)
from quantitative.factor_batch import compute_and_save_factors  # noqa: E402
from quote_api import QuoteAPIFactory  # noqa: E402
from quote_api.quote_base import DailyQuote  # noqa: E402
from quantitative.factor_data import KlineIndicator  # noqa: E402
from utils.logger import get_logger  # noqa: E402

# 直接跑文件（python stock_advisor.py）时 __package__ 为空，相对 import 会失败；
# 走 -m 时 __package__ 为 "tools.stock_advisor"，相对 import 才有效。
# 用 try/except 兼容两种入口。
try:
    from .backtester import HorizonBacktester, MultiHorizonForecast  # noqa: E402
    from .fundamental_view import (  # noqa: E402
        FundamentalSnapshot, build_snapshot,
    )
    from .fundamental_trend import (  # noqa: E402
        FundamentalTrend, analyze_long_term,
    )
except ImportError:
    from backtester import HorizonBacktester, MultiHorizonForecast  # type: ignore  # noqa: E402
    from fundamental_view import (  # type: ignore  # noqa: E402
        FundamentalSnapshot, build_snapshot,
    )
    from fundamental_trend import (  # type: ignore  # noqa: E402
        FundamentalTrend, analyze_long_term,
    )

_log = get_logger(__name__)

DEFAULT_REPORT_DIR = _THIS_DIR / "reports"


# ===========================================================================
# 数据加载（"没读到就算"的核心）
# ===========================================================================

def _load_or_build(name_key: str, api: str, db_path: Optional[str],
                   force_refresh: bool = False
                   ) -> tuple[list[DailyQuote], list[KlineIndicator]]:
    """读 DB；若 K 线为空 / 因子表落后于 K 线 → 重算后再读。

    判定策略（用户需求 ②A）：
    - K 线最新日期 == 因子表最新日期 → 直接用 DB
    - 否则 → 调 ``compute_and_save_factors`` 完整重算入库
    - ``force_refresh=True`` 强制重算（绕过缓存）
    """
    with closing(StockDB(db_path)) as db:
        kline_latest = db.get_latest_date(name_key)
        ind_latest = db.get_latest_indicator_date(name_key)

    need_recompute = (
        force_refresh
        or kline_latest is None
        or ind_latest != kline_latest
    )

    if need_recompute:
        reason = (
            "强制刷新"
            if force_refresh
            else ("DB 无该股票数据" if kline_latest is None
                  else f"因子表(latest={ind_latest}) ≠ K线(latest={kline_latest})")
        )
        _log.info("[%s] 触发重算: %s", name_key, reason)
        ok = compute_and_save_factors(
            name_key, api_name=api, db_path=db_path,
            limit=5000, force_refresh=force_refresh,
        )
        if not ok:
            _log.error("[%s] 重算失败", name_key)
            return [], []
    else:
        _log.info("[%s] DB 已最新（K线=因子=%s），直接读", name_key, kline_latest)

    # 重算完再读一次（重算逻辑里已写库），保证调用方拿到的是 DB 视图
    with closing(StockDB(db_path)) as db:
        quotes = db.get_klines_in_range(name_key)
        indicators = db.read_all_indicators_in_range(name_key)
    return quotes, indicators


# ===========================================================================
# 报告渲染
# ===========================================================================

_HORIZON_ICONS = {True: "[+]", False: "[-]", None: "[ ]"}


def _direction_icon(prob_up: Optional[float]) -> str:
    if prob_up is None:
        return _HORIZON_ICONS[None]
    if prob_up >= 0.55:
        return _HORIZON_ICONS[True]
    if prob_up <= 0.45:
        return _HORIZON_ICONS[False]
    return _HORIZON_ICONS[None]


def _build_markdown(report: AnalysisReport,
                    forecast: Optional[MultiHorizonForecast],
                    name_key: str,
                    backtest_n: Optional[int] = None,
                    fundamental: Optional[FundamentalSnapshot] = None,
                    fundamental_trend: Optional[FundamentalTrend] = None) -> str:
    """组合 markdown 报告。"""
    lines: list[str] = []
    lines.append(f"# {report.stock_name}({name_key}) 综合分析报告")
    lines.append("")
    lines.append(f"- 数据源: {report.data_source}")
    lines.append(f"- 数据量: {report.data_days} 天")
    if backtest_n is not None and backtest_n != report.data_days:
        # 回测器剔除了非正收盘价后的可用样本数，明确标出避免误解
        lines.append(f"- 回测可用样本: {backtest_n} 天"
                     f"（已剔除前复权溢出的 {report.data_days - backtest_n} 条）")
    lines.append(f"- 最新价: {report.latest_price:.2f}")
    lines.append(f"- 生成时间: "
                 f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # ---- 当前状态评分（来自 QuantAnalyzer）----
    # 注意：这一节是"此刻强弱"的快照，不是对未来涨跌的预测。
    # 与下一节「多周期预测」结论可能相反，两者互补（详见本节末尾说明）。
    lines.append("## 1. 当前状态评分（多因子加权快照）")
    lines.append("")
    lines.append(f"- 趋势: **{report.trend}**")
    lines.append(f"- 当前因子加权偏多强度: **{report.probability_up * 100:.1f}%**")
    lines.append(f"- 当前因子加权偏空强度: **{report.probability_down * 100:.1f}%**")
    lines.append("")
    lines.append("> **这不是涨跌预测**，而是把当前这一天的全部因子打分加权后，"
                 "线性映射到 [0.15, 0.85] 得到的**此刻多空力量对比快照**，"
                 "无期限含义。下一节的"
                 "「多周期预测」才是基于历史相似态给出的未来 N 天上涨概率。")
    lines.append("")

    # ---- 多周期预测（来自 HorizonBacktester）----
    lines.append("## 2. 多周期涨跌预测（历史相似态回测）")
    lines.append("")
    lines.append("> 做法：找出历史上与当前因子组合最相似的 top-K 天，"
                 "统计这些历史日 N 天后的真实涨跌。"
                 "**与第 1 节可能相反是正常的** —— "
                 "比如当前超卖（第 1 节偏空），但历史上每次跌到此位后"
                 "多数是反弹（第 2 节偏多），这是均值回归。")
    lines.append("")
    if forecast is None:
        lines.append("> 数据不足，无法跑历史相似态回测（至少需要 ~160 个有效交易日）。")
        lines.append("")
    else:
        lines.append("| 周期 | 上涨概率 | 期望收益 | 上涨样本均值 | 下跌样本均值 | 样本数 |")
        lines.append("|------|----------|----------|--------------|--------------|--------|")
        for fc in [forecast.short, forecast.medium, forecast.long]:
            if fc is None:
                continue
            icon = _direction_icon(fc.prob_up)
            lines.append(
                f"| {icon} {fc.label} "
                f"| {fc.prob_up * 100:.1f}% "
                f"| {fc.expected_return * 100:+.2f}% "
                f"| {fc.avg_positive * 100:+.2f}% "
                f"| {fc.avg_negative * 100:+.2f}% "
                f"| {fc.sample_size} |"
            )
        lines.append("")

        lines.append("### 预测原因（相似态触发条件）")
        lines.append("")
        for fc in [forecast.short, forecast.medium, forecast.long]:
            if fc is None:
                continue
            lines.append(f"- **{fc.label}**：{fc.reason}")
        lines.append("")

        lines.append("### 当前因子的「极端度」（z 分数绝对值，越大越偏离历史均值）")
        lines.append("")
        contrib_sorted = sorted(
            forecast.feature_contribution.items(),
            key=lambda x: x[1], reverse=True,
        )
        lines.append("| 因子 | |z| | 解读 |")
        lines.append("|------|-----|------|")
        for name, z in contrib_sorted:
            tag = "极端" if z > 2 else ("偏离" if z > 1 else "正常")
            lines.append(f"| {name} | {z:.2f} | {tag} |")
        lines.append("")

        if forecast.top_similar_dates:
            lines.append("### 命中的历史相似日（top 10）")
            lines.append("")
            lines.append(", ".join(forecast.top_similar_dates))
            lines.append("")

    # ---- 因子明细（直接复用 QuantAnalyzer 的 summary，但去掉头部）----
    lines.append("## 3. 因子明细（单点信号）")
    lines.append("")
    lines.append("```")
    lines.append(report.summary)
    lines.append("```")
    lines.append("")

    # ---- 基本面快照（来自最新一份已公告财报）----
    lines.append("## 4. 基本面快照（最新已公告财报）")
    lines.append("")
    lines.append("> 来自 `financial_report` 表。**季度级低频信息**，不参与上方"
                 "回测的 z-score 相似度匹配；仅作为辅助判断。")
    lines.append("")
    lines.extend(_render_fundamental(fundamental))
    lines.append("")

    # ---- 长期基本面分析与预测 ----
    lines.append("## 5. 长期基本面分析与预测")
    lines.append("")
    lines.append("> 基于近 20 期（5 年）财报历史，识别趋势 + 外推未来 4 个季度，"
                 "并结合当前股价计算隐含估值。**仅做定量参考，无法预测拐点。**")
    lines.append("")
    lines.extend(_render_fundamental_trend(fundamental_trend))
    lines.append("")

    # ---- 风险提示 ----
    lines.append("## 6. 风险提示")
    lines.append("")
    lines.append("- 以上结果**主要由量价 + 流动性/资金面驱动**，"
                 "未纳入基本面、政策面、情绪面；")
    lines.append("- 历史相似态不代表未来必然重演，尤其除权除息日附近样本会失真;")
    lines.append("- 长期基本面预测基于趋势外推，**不能预测拐点 / 监管 / 突发事件**；")
    lines.append("- 概率值仅供参考，**不构成任何投资建议**。")
    lines.append("")
    return "\n".join(lines)


# ===========================================================================
# 基本面渲染（独立成函数，便于单测 / 后续替换）
# ===========================================================================

def _fmt_money_yi(v: Optional[float]) -> str:
    """元 → 亿元，保留 2 位小数。None → 'N/A'。"""
    if v is None:
        return "N/A"
    return f"{v / 1e8:,.2f} 亿"


def _fmt_pct(v: Optional[float], plus_sign: bool = False) -> str:
    """小数 → 百分比字符串。None → 'N/A'。"""
    if v is None:
        return "N/A"
    fmt = f"{v * 100:+.2f}%" if plus_sign else f"{v * 100:.2f}%"
    return fmt


def _fmt_eps(v: Optional[float]) -> str:
    if v is None:
        return "N/A"
    return f"{v:.3f} 元/股"


def _fmt_ratio(v: Optional[float], unit: str = "") -> str:
    if v is None:
        return "N/A"
    return f"{v:.2f}{unit}"


def _render_fundamental(snap: Optional[FundamentalSnapshot]) -> list[str]:
    """把 FundamentalSnapshot 渲染成 markdown 行列表。"""
    if snap is None:
        return ["> _暂无财报数据_（该股票未通过 `financial_fetcher` 入库，"
                "或截至当前交易日无已公告财报）。"]

    out: list[str] = []
    audited = "经审计" if snap.audited else "未经审计"
    out.append(f"- 报告期: **{snap.period_end}**（{snap.period_type}, "
               f"{audited}, 币种 {snap.currency}）")
    out.append(f"- 公告日: {snap.announce_date}")
    out.append("")

    # 规模
    out.append("### 规模")
    out.append("")
    out.append("| 项目 | 数值 |")
    out.append("|------|------|")
    out.append(f"| 营业收入 | {_fmt_money_yi(snap.revenue)} |")
    out.append(f"| 归母净利润（IFRS） | {_fmt_money_yi(snap.net_income_attr)} |")
    if snap.net_income_attr_nonifrs is not None:
        out.append(
            f"| 归母净利润（Non-IFRS） | "
            f"{_fmt_money_yi(snap.net_income_attr_nonifrs)} |"
        )
    out.append(f"| 总资产 | {_fmt_money_yi(snap.total_assets)} |")
    out.append(f"| 归母权益 | {_fmt_money_yi(snap.total_equity_attr)} |")
    out.append(f"| 经营性现金流 | {_fmt_money_yi(snap.operating_cash_flow)} |")
    if snap.free_cash_flow is not None:
        out.append(f"| 自由现金流 | {_fmt_money_yi(snap.free_cash_flow)} |")
    out.append("")

    # 盈利能力
    out.append("### 盈利能力")
    out.append("")
    out.append("| 指标 | 数值 |")
    out.append("|------|------|")
    out.append(f"| 毛利率 | {_fmt_pct(snap.gross_margin)} |")
    out.append(f"| 净利率（归母 / 营收） | {_fmt_pct(snap.net_margin)} |")
    out.append(f"| 单期 ROE（归母净利 / 归母权益） | "
               f"{_fmt_pct(snap.roe_quarterly)} |")
    out.append(f"| 基本 EPS | {_fmt_eps(snap.eps_basic)} |")
    if snap.eps_basic_nonifrs is not None:
        out.append(f"| 基本 EPS（Non-IFRS） | "
                   f"{_fmt_eps(snap.eps_basic_nonifrs)} |")
    out.append("")
    out.append("> 说明：单期 ROE 是**当期口径**，不是年化 / TTM。年报数据可"
               "近似看作年度 ROE；季报口径偏低，仅做横向对比。")
    out.append("")

    # 成长性
    out.append("### 成长性（同比）")
    out.append("")
    if (snap.revenue_yoy is None and snap.net_income_yoy is None
            and snap.net_income_nonifrs_yoy is None):
        out.append("> 未找到上年同期数据，同比指标暂缺。")
        out.append("")
    else:
        out.append("| 指标 | 同比 |")
        out.append("|------|------|")
        out.append(f"| 营收 YoY | {_fmt_pct(snap.revenue_yoy, plus_sign=True)} |")
        out.append(f"| 归母净利 YoY（IFRS） | "
                   f"{_fmt_pct(snap.net_income_yoy, plus_sign=True)} |")
        if snap.net_income_nonifrs_yoy is not None:
            out.append(f"| 归母净利 YoY（Non-IFRS） | "
                       f"{_fmt_pct(snap.net_income_nonifrs_yoy, plus_sign=True)} |")
        out.append("")

    # 财务健康
    out.append("### 财务健康")
    out.append("")
    out.append("| 指标 | 数值 | 解读 |")
    out.append("|------|------|------|")
    da = snap.debt_to_assets
    da_tag = "—"
    if da is not None:
        da_tag = "稳健" if da < 0.5 else ("中等" if da < 0.7 else "偏高")
    out.append(f"| 资产负债率 | {_fmt_pct(da)} | {da_tag} |")
    cn = snap.cash_to_net_income
    cn_tag = "—"
    if cn is not None:
        cn_tag = ("利润含金量高" if cn >= 1.0
                  else "现金流弱于利润" if cn >= 0.5
                  else "盈利质量待观察")
    out.append(f"| OCF / 归母净利 | {_fmt_ratio(cn)} | {cn_tag} |")
    out.append("")

    if snap.warnings:
        out.append("> 提示：")
        for w in snap.warnings:
            out.append(f"> - {w}")
        out.append("")

    return out


# ===========================================================================
# 长期基本面渲染
# ===========================================================================

def _render_fundamental_trend(t: Optional[FundamentalTrend]) -> list[str]:
    """渲染长期趋势分析的 markdown 段落。"""
    if t is None:
        return ["> _财报数据不足，无法做长期分析（至少需要 4 期）_"]

    out: list[str] = []
    out.append(f"_基于 **{t.period_count}** 期历史财报数据_")
    out.append("")

    # ---- 5.1 历史轨迹 ----
    out.append("### 5.1 关键指标历史轨迹（近 12 期摘要）")
    out.append("")
    # 太长会影响阅读，只展示最近 12 期
    show_history = t.history[-12:] if len(t.history) > 12 else t.history
    out.append("| 期次 | 营收(亿) | 营收 YoY | 归母净利(亿) | 归母 YoY "
               "| 毛利率 | 净利率 |")
    out.append("|------|---------|----------|-------------|---------"
               "|--------|--------|")
    for h in show_history:
        out.append(
            f"| {h.period_label} "
            f"| {_fmt_yi_value(h.revenue)} "
            f"| {_fmt_pct(h.revenue_yoy, plus_sign=True)} "
            f"| {_fmt_yi_value(h.net_income_attr)} "
            f"| {_fmt_pct(h.net_income_yoy, plus_sign=True)} "
            f"| {_fmt_pct(h.gross_margin)} "
            f"| {_fmt_pct(h.net_margin)} |"
        )
    out.append("")
    if len(t.history) > 12:
        out.append(f"_完整 {len(t.history)} 期数据已用于趋势计算，"
                   f"此处仅展示最近 12 期_")
        out.append("")

    # ---- 5.2 趋势归纳 ----
    out.append("### 5.2 趋势归纳")
    out.append("")
    if not t.trends:
        out.append("> 数据不足，趋势分析跳过。")
        out.append("")
    else:
        out.append("> 比率类指标（毛利率/净利率/ROE/负债率）用近 8 期最小二乘拟合；"
                   "YoY 类指标对基数效应敏感，改用「近 4 期 vs 近 8 期中位数对比」"
                   "判断加速/减速。")
        out.append("")
        out.append("| 指标 | 关键观察 | 方向 |")
        out.append("|------|---------|------|")
        for tr in t.trends:
            out.append(f"| {tr.metric} | {tr.description} | {tr.direction} |")
        out.append("")

    # ---- 5.3 未来 4 期预测 ----
    out.append("### 5.3 未来 4 个季度预测（YoY 承接 + 线性外推 投票）")
    out.append("")
    if not t.forecast:
        out.append("> 数据不足，预测跳过。")
        out.append("")
    else:
        out.append("| 期次 | 预测营收(亿) | 预测归母净利(亿) | 不确定度 |")
        out.append("|------|-------------|-----------------|----------|")
        for fc in t.forecast:
            conf_tag = ("高" if fc.confidence_pct < 0.05
                        else "中" if fc.confidence_pct < 0.15
                        else "低")
            out.append(
                f"| {fc.period_label} "
                f"| {_fmt_yi_value(fc.revenue_forecast)} "
                f"| {_fmt_yi_value(fc.net_income_forecast)} "
                f"| {conf_tag}（分歧 {fc.confidence_pct * 100:.1f}%） |"
            )
        out.append("")
        out.append("> **不确定度**：两种预测方法的分歧度。**高** = 两法基本一致，"
                   "可信度高；**低** = 两法分歧大，趋势可能拐点附近。")
        out.append("")

    # ---- 5.4 隐含估值 ----
    if t.valuation is not None:
        v = t.valuation
        out.append("### 5.4 当前股价的隐含估值")
        out.append("")
        out.append("| 项目 | 数值 |")
        out.append("|------|------|")
        out.append(f"| 推算流通股数 | {v.shares_outstanding / 1e8:.2f} 亿股 |")
        out.append(f"| 当前总市值 | {v.market_cap / 1e8:,.2f} 亿元 |")
        out.append(f"| TTM 归母净利 | {v.ttm_net_income / 1e8:,.2f} 亿元 |")
        if v.pe_ttm is not None:
            out.append(f"| **当前 PE_TTM** | **{v.pe_ttm:.2f}x** |")
        if v.forward_net_income > 0:
            out.append(
                f"| 远期 4 期预测净利 | {v.forward_net_income / 1e8:,.2f} 亿元 |"
            )
        if v.pe_forward is not None:
            out.append(f"| **远期 PE（forward）** | **{v.pe_forward:.2f}x** |")
        if v.pe_history_median is not None:
            out.append(f"| 历史 PE 中位数（近 12 期） "
                       f"| {v.pe_history_median:.2f}x |")
        out.append("")
        if (v.fair_price_low is not None and v.fair_price_high is not None
                and v.fair_price_mid is not None):
            out.append("**公允价格区间**（历史 PE 中位数 × 远期 EPS, ±20% 估值带）：")
            out.append("")
            out.append(f"- 下沿: **{v.fair_price_low:.2f}**")
            out.append(f"- 中值: **{v.fair_price_mid:.2f}**")
            out.append(f"- 上沿: **{v.fair_price_high:.2f}**")
            if v.upside_pct is not None:
                tag = ("**低估**" if v.upside_pct > 0.20
                       else "**高估**" if v.upside_pct < -0.20
                       else "公允区间")
                out.append(f"- 当前价相对中值: **{v.upside_pct * 100:+.1f}%** "
                           f"({tag})")
            out.append("")
        out.append("> **估值方法局限**：")
        out.append("> - 股数从 EPS 反推（加权平均，与期末值有 ~1% 误差）；")
        out.append("> - 历史 PE 用每份财报**公告日真实收盘价 / 该期 NI_TTM** 算出，"
                   "再取近 12 期（3 年）中位数作为估值锚；")
        out.append("> - PE 中位数 × 远期 EPS 假设市场仍按近 3 年估值水平定价，"
                   "**不适用于商业模式 / 成长性发生质变的公司**；")
        out.append("> - 早期高成长高估值期（如 2015~2018 PE 35x+）已剔除，"
                   "防止拉偏中枢。")
        out.append("")

    # ---- 综合判断 ----
    out.append("### 5.5 综合判断")
    out.append("")
    out.append(t.summary)
    out.append("")

    return out


def _fmt_yi_value(v: Optional[float]) -> str:
    """元 → 亿元（不带单位字，节约表格宽度）。"""
    if v is None:
        return "N/A"
    return f"{v / 1e8:,.0f}"


def _build_price_map(quotes: list[DailyQuote],
                     rows_pit: list[dict]) -> dict[str, float]:
    """为每份财报的 announce_date 找一个最接近的有效收盘价。

    财报公告日通常落在交易日，但偶尔会是周末（港股盘后公告也算公告日）。
    策略：取 announce_date 当日 close，若不存在则取该日**之后**的第一个
    交易日 close（公告之后的市场反应价更能体现"市场如何看待这份财报"）。
    """
    # 用 (date, close) 列表二分查找
    valid = [(q.date, q.close) for q in quotes
             if q.close is not None and q.close > 0 and q.date]
    if not valid:
        return {}
    valid.sort(key=lambda x: x[0])
    dates = [d for d, _ in valid]

    out: dict[str, float] = {}
    for r in rows_pit:
        ad = r.get("AnnounceDate")
        if not ad:
            continue
        # bisect: 找第一个 >= ad 的位置
        lo, hi = 0, len(dates)
        while lo < hi:
            mid = (lo + hi) // 2
            if dates[mid] < ad:
                lo = mid + 1
            else:
                hi = mid
        if lo < len(valid):
            out[ad] = valid[lo][1]
    return out


# ===========================================================================
# 主流程
# ===========================================================================

def analyze_stock(name_key: str, *, api: Optional[str] = None,
                  db_path: Optional[str] = None,
                  top_k: int = 50,
                  write_report: bool = True,
                  report_dir: Optional[Path] = None,
                  force_refresh: bool = False) -> Optional[Path]:
    """对指定股票出预测报告。

    :return: 报告文件路径（write_report=True 时），否则 None
    """
    api = api or QuoteAPIFactory.current_source()
    stock_info = config.global_stock_list.get(name_key)
    if stock_info is None:
        _log.error("[%s] 未在 config.global_stock_list 中登记", name_key)
        return None

    # 1. 读 / 算 数据
    quotes, indicators = _load_or_build(name_key, api, db_path,
                                         force_refresh=force_refresh)
    if not quotes:
        _log.error("[%s] 无法获取行情数据", name_key)
        return None
    if not indicators:
        _log.error("[%s] 无法获取因子数据", name_key)
        return None

    # 2. QuantAnalyzer 等价的多因子打分（直接复用底层引擎，避免再发一次 API）
    engine = QuantFactorEngine(quotes, fundamentals=None)
    factors = engine.compute_all()
    prob_up, prob_down, trend = compute_probability(factors)

    report = AnalysisReport(
        stock_name=stock_info.name,
        name_key=name_key,
        data_source=api,
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

    # 3. 多周期相似态回测
    bt = HorizonBacktester(quotes, indicators)
    forecast = bt.run(top_k=top_k)

    # 4. 基本面快照（最新一份已公告财报；缺数据自动 fallback 到 None）
    #    传 as_of=最新交易日，确保 PIT 合规（不会拿到未公告的数据）。
    fundamental: Optional[FundamentalSnapshot] = None
    fundamental_trend: Optional[FundamentalTrend] = None
    try:
        with closing(StockDB(db_path)) as db:
            fundamental = build_snapshot(name_key, db,
                                          as_of=quotes[-1].date)
            # 长期分析需要全量历史 rows + 当前价 + 历史股价
            rows = db.get_financial_reports(name_key)
            cutoff = quotes[-1].date
            rows_pit = [r for r in rows
                        if r.get("AnnounceDate") and r["AnnounceDate"] <= cutoff]
            if rows_pit:
                # 构建 announce_date → close 映射，用真实历史股价算历史 PE
                # （没找到的日期会从公告后第一个交易日就近回填）
                price_map = _build_price_map(quotes, rows_pit)
                fundamental_trend = analyze_long_term(
                    rows_pit, current_price=quotes[-1].close,
                    price_history=price_map,
                )
    except Exception as e:  # noqa: BLE001
        # 财报模块是辅助信息，任何异常都不该阻断主分析
        _log.warning("[%s] 基本面分析失败: %s", name_key, e)

    # 5. 渲染 markdown，控制台打印 + 落盘
    md = _build_markdown(report, forecast, name_key,
                         backtest_n=bt.n,
                         fundamental=fundamental,
                         fundamental_trend=fundamental_trend)
    print("\n" + md + "\n")

    if not write_report:
        return None

    target_dir = report_dir or DEFAULT_REPORT_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    fname = (
        f"{name_key}_"
        f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    )
    fpath = target_dir / fname
    fpath.write_text(md, encoding="utf-8")
    _log.info("报告已保存: %s", fpath)
    return fpath


# ===========================================================================
# CLI
# ===========================================================================

def main() -> int:
    current_api = QuoteAPIFactory.current_source()
    available_apis = QuoteAPIFactory.available_sources()
    parser = argparse.ArgumentParser(
        description="股票综合分析工具：行情/因子/历史相似态预测",
    )
    parser.add_argument("stock", help="股票 name_key (如 Tencent)")
    parser.add_argument(
        "--api",
        choices=available_apis,
        default=current_api,
        help="数据源（缺数据时回源用，default: %(default)s）",
    )
    parser.add_argument("--db", help="数据库路径（不指定走默认）")
    parser.add_argument("--top-k", type=int, default=50,
                        help="历史相似日数量，default: 50")
    parser.add_argument("--no-write", action="store_true",
                        help="不落盘 markdown，仅控制台输出")
    parser.add_argument("--force-refresh", action="store_true",
                        help="强制从 API 重新拉算因子（忽略 DB 缓存）")
    parser.add_argument("--report-dir", help="自定义报告目录")
    args = parser.parse_args()

    report_dir = Path(args.report_dir) if args.report_dir else None

    try:
        path = analyze_stock(
            args.stock,
            api=args.api,
            db_path=args.db,
            top_k=args.top_k,
            write_report=not args.no_write,
            report_dir=report_dir,
            force_refresh=args.force_refresh,
        )
    finally:
        QuoteAPIFactory.clear_cache()

    return 0 if path is not None or args.no_write else 1


if __name__ == "__main__":
    sys.exit(main())
