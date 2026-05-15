#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""股票综合分析工具 CLI。

用法::

    python -m tools.stock_advisor.stock_advisor Tencent
    python -m tools.stock_advisor.stock_advisor Alibaba --api eastmoney --top-k 80
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
except ImportError:
    from backtester import HorizonBacktester, MultiHorizonForecast  # type: ignore  # noqa: E402
    from fundamental_view import (  # type: ignore  # noqa: E402
        FundamentalSnapshot, build_snapshot,
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
                    fundamental: Optional[FundamentalSnapshot] = None) -> str:
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

    # ---- 风险提示 ----
    lines.append("## 5. 风险提示")
    lines.append("")
    lines.append("- 以上结果**主要由量价 + 流动性/资金面驱动**，"
                 "未纳入基本面、政策面、情绪面；")
    lines.append("- 历史相似态不代表未来必然重演，尤其除权除息日附近样本会失真；")
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
# 主流程
# ===========================================================================

def analyze_stock(name_key: str, *, api: str = "eastmoney",
                  db_path: Optional[str] = None,
                  top_k: int = 50,
                  write_report: bool = True,
                  report_dir: Optional[Path] = None,
                  force_refresh: bool = False) -> Optional[Path]:
    """对指定股票出预测报告。

    :return: 报告文件路径（write_report=True 时），否则 None
    """
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
    try:
        with closing(StockDB(db_path)) as db:
            fundamental = build_snapshot(name_key, db,
                                          as_of=quotes[-1].date)
    except Exception as e:  # noqa: BLE001
        # 财报模块是辅助信息，任何异常都不该阻断主分析
        _log.warning("[%s] 基本面快照失败: %s", name_key, e)

    # 5. 渲染 markdown，控制台打印 + 落盘
    md = _build_markdown(report, forecast, name_key,
                         backtest_n=bt.n, fundamental=fundamental)
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
    parser = argparse.ArgumentParser(
        description="股票综合分析工具：行情/因子/历史相似态预测",
    )
    parser.add_argument("stock", help="股票 name_key (如 Tencent)")
    parser.add_argument("--api", default="eastmoney",
                        help="数据源（缺数据时回源用），default: eastmoney")
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
