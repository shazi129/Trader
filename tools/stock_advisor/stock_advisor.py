#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""股票综合分析工具 CLI。

用法::

    python -m tools.stock_advisor.stock_advisor Tencent
    python -m tools.stock_advisor.stock_advisor Alibaba --top-k 80
    python -m tools.stock_advisor.stock_advisor Tencent --no-write   # 只看不落盘

流程：
1. 从行情仓储读取 K 线，从量化仓储读取特征快照
2. 若特征缺失或落后，仅使用本地 K 线重新物化；K 线为空则失败
3. 用形态信号和回测统计生成多周期概率
4. 用 ``HorizonBacktester`` 跑历史相似态匹配，得 5/20/60 日上涨概率
5. 按各自经过样本外校准的可靠性融合两个子模型
6. 把上述结果合成一份 markdown，控制台打印 + 落盘到 reports/
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
from financial_reports.repository import FinancialReportRepository  # noqa: E402
from financial_reports.analysis import FundamentalSnapshot, build_snapshot  # noqa: E402
from quote_api.db_api import DbQuoteAPI  # noqa: E402
from quote_api.repository import MarketDataRepository  # noqa: E402
from quantitative.analysis import (  # noqa: E402
    QuantitativeAnalysisService,
    QuantitativeReport,
)
from quantitative.analysis.aggregation import signal_contributions  # noqa: E402
from quantitative.backtesting import (  # noqa: E402
    BacktestArtifact,
    BacktestArtifactRepository,
    SignalBacktester,
)
from quantitative.features import (  # noqa: E402
    FeatureRepository,
    FeatureSnapshot,
    materialize_symbol,
)
from quote_api.quote_base import DailyQuote  # noqa: E402
from utils.logger import get_logger  # noqa: E402

# 直接跑文件（python stock_advisor.py）时 __package__ 为空，相对 import 会失败；
# 走 -m 时 __package__ 为 "tools.stock_advisor"，相对 import 才有效。
# 用 try/except 兼容两种入口。
try:
    from .backtester import HorizonBacktester, MultiHorizonForecast  # noqa: E402
    from .fusion import FusedForecast, fuse_forecasts  # noqa: E402
    from .fundamental_trend import (  # noqa: E402
        FundamentalTrend, analyze_long_term,
    )
except ImportError:
    from backtester import HorizonBacktester, MultiHorizonForecast  # type: ignore  # noqa: E402
    from fusion import FusedForecast, fuse_forecasts  # type: ignore  # noqa: E402
    from fundamental_trend import (  # type: ignore  # noqa: E402
        FundamentalTrend, analyze_long_term,
    )

_log = get_logger(__name__)

DEFAULT_REPORT_DIR = _THIS_DIR / "reports"


# ===========================================================================
# 数据加载（本地行情 + 按需物化特征）
# ===========================================================================

def _load_or_build(name_key: str, db_path: Optional[str],
                   rebuild_features: bool = False
                   ) -> tuple[list[DailyQuote], list[FeatureSnapshot]]:
    """只读本地行情；特征缺失或落后时基于本地 K 线重建。

    判定策略：
    - K 线最新日期 == 特征最新日期 → 直接读仓储
    - 特征缺失或落后 → 使用 ``source="db"`` 重新物化完整特征序列
    - K 线为空 → 直接失败，绝不访问线上 provider
    - ``rebuild_features=True`` 强制用本地 K 线重建特征
    """
    with closing(MarketDataRepository(db_path)) as market_repository:
        kline_latest = market_repository.latest_date(name_key)
    with closing(FeatureRepository(db_path)) as feature_repository:
        feature_latest = feature_repository.latest_date(name_key)

    if kline_latest is None:
        _log.error(
            "[%s] 本地数据库没有 K 线；请先运行 kline_fetcher 更新行情",
            name_key,
        )
        return [], []

    need_recompute = rebuild_features or feature_latest != kline_latest

    if need_recompute:
        reason = (
            "强制重建本地特征"
            if rebuild_features
            else f"特征(latest={feature_latest}) ≠ K线(latest={kline_latest})"
        )
        _log.info("[%s] 触发重算: %s", name_key, reason)
        count = materialize_symbol(
            name_key,
            source="db",
            db_path=db_path,
        )
        if not count:
            _log.error("[%s] 重算失败", name_key)
            return [], []
    else:
        _log.info("[%s] 仓储已最新（K线=特征=%s），直接读", name_key, kline_latest)

    # 重算完再读一次（重算逻辑里已写库），保证调用方拿到的是 DB 视图
    with closing(MarketDataRepository(db_path)) as market_repository:
        quotes = market_repository.get_range(name_key)
    with closing(FeatureRepository(db_path)) as feature_repository:
        features = feature_repository.get_range(name_key)
    return quotes, features


# ===========================================================================
# 报告渲染
# ===========================================================================

_HORIZON_ICONS = {True: "[+]", False: "[-]", None: "[ ]"}


def _direction_label(prob_up: Optional[float]) -> str:
    if prob_up is None:
        return "数据不足"
    if prob_up >= 0.60:
        return "偏多"
    if prob_up <= 0.40:
        return "偏空"
    return "中性"


def _direction_icon(prob_up: Optional[float]) -> str:
    if prob_up is None:
        return _HORIZON_ICONS[None]
    if prob_up >= 0.60:
        return _HORIZON_ICONS[True]
    if prob_up <= 0.40:
        return _HORIZON_ICONS[False]
    return _HORIZON_ICONS[None]


def _markdown_cell(value: object) -> str:
    """Escape text that would otherwise break a Markdown table cell."""
    return str(value).replace("|", "\\|").replace("\n", " ")


def _render_fused_forecast(forecast: Optional[FusedForecast]) -> list[str]:
    """Render the reliability-weighted result of both quantitative models."""
    out = [
        "### 1.1 综合概率（可靠性加权融合）",
        "",
        "> 综合模型使用凸组合：`P综合 = w形态 × P形态 + w相似态 × P相似态`。"
        "两类模型共享技术指标，因此不采用会假设证据独立的赔率相乘，避免重复信息"
        "造成过度自信。",
        "",
        "> 形态权重来自触发信号的平均回测可靠性；相似态权重同时考虑距离质量、"
        "有效样本量，以及非重叠历史锚点上的逐时点 Brier 校准。校准无正技能时，"
        "相似态权重为 0，不进入综合概率。",
        "",
    ]
    if forecast is None or not forecast.horizons:
        out.extend(["> 缺少可融合的模型结果。", ""])
        return out
    out.append(
        "| 周期 | 综合上涨概率 | 综合下跌概率 | 趋势 | 形态概率 / 权重占比 "
        "| 相似态概率 / 权重占比 | 模型关系 | 综合置信度 |"
    )
    out.append(
        "|------|--------------|--------------|------|---------------------"
        "|-------------------------|----------|------------|"
    )
    for horizon, item in sorted(forecast.horizons.items()):
        similarity = (
            f"{item.similarity_probability_up:.1%} / "
            f"{item.similarity_weight_share:.1%}"
            if item.similarity_probability_up is not None
            else "不可用 / 0.0%"
        )
        relationship = "方向相反" if item.models_disagree else "方向一致"
        out.append(
            f"| {_direction_icon(item.probability_up)} {horizon}日 "
            f"| **{item.probability_up:.1%}** "
            f"| {item.probability_down:.1%} "
            f"| {item.trend} "
            f"| {item.signal_probability_up:.1%} / {item.signal_weight_share:.1%} "
            f"| {similarity} "
            f"| {relationship} "
            f"| {item.confidence:.1%} |"
        )
    out.append("")
    return out


def _render_directional_signals(
    report: QuantitativeReport,
    artifact: Optional[BacktestArtifact],
) -> list[str]:
    """Group signals and explain their effective, backtest-weighted direction."""
    bullish = [signal for signal in report.active_signals if signal.direction > 0]
    bearish = [signal for signal in report.active_signals if signal.direction < 0]
    neutral = [signal for signal in report.active_signals if signal.direction == 0]

    out = [
        f"- 当前触发：**看多 {len(bullish)} 个 / 看空 {len(bearish)} 个"
        + (f" / 中性 {len(neutral)} 个**" if neutral else "**"),
        "",
        "> 此处方向是指标形态本身的名义方向；第 1 节还会结合各形态的"
        "历史成功率和权重，因此最终概率可能与简单数量对比不同。",
        "",
    ]

    def append_group(title: str, signals: list) -> None:
        out.append(f"### {title}（{len(signals)}）")
        out.append("")
        if not signals:
            out.append("> 当前没有触发。")
            out.append("")
            return
        out.append("| 指标形态 | 分类 | 触发依据 |")
        out.append("|----------|------|----------|")
        for signal in signals:
            out.append(
                f"| {_markdown_cell(signal.name)} "
                f"| `{_markdown_cell(signal.category)}` "
                f"| {_markdown_cell(signal.description or '已触发')} |"
            )
        out.append("")

    append_group("3.1 看多指标形态", bullish)
    append_group("3.2 看空指标形态", bearish)
    if neutral:
        append_group("3.3 中性/待确认指标形态", neutral)

    detail_number = "3.4" if neutral else "3.3"
    out.append(f"### {detail_number} 回测后的有效方向与概率贡献")
    out.append("")
    if artifact is None:
        out.append("> 回测统计不可用，无法解释各形态的实际概率贡献。")
        out.append("")
        return out

    universe = "、".join(artifact.universe) if artifact.universe else "未记录"
    out.extend([
        "> **形态数量不是投票数。** 背离按独立事件去重；每个信号的命中率"
        "与对应股票、对应周期的无条件基准比较，只有单侧 95% 显著优于"
        "基准时才获得权重。",
        "",
        "> 命中率低于基准不会自动反转。只有扩展窗口训练后，在至少两个后续"
        "走步样本外区间保持正向且合并结果显著的反向关系，才允许标记为"
        "反向指标；否则权重为 0。",
        "",
        "> 最终上涨概率是已验证信号概率的加权平均；没有有效信号时返回该股票"
        "对应周期的历史上涨基准。下表贡献均相对该基准计算。",
        "",
        f"> 回测模型：`{artifact.model_version}`；截止日："
        f"{artifact.data_cutoff or '未记录'}；股票池：{universe}。",
        "",
    ])

    for horizon in sorted(report.horizons):
        contributions = signal_contributions(
            report.signals,
            artifact,
            horizon,
            symbol=report.symbol,
        )
        out.append(f"#### {horizon}日贡献明细")
        out.append("")
        if not contributions:
            baseline = report.horizons[horizon].baseline_probability_up
            out.append(
                f"> 没有通过显著性验证的触发形态，使用历史上涨基准 "
                f"**{baseline:.1%}**。"
            )
            out.append("")
            continue
        out.append(
            "| 指标形态 | 名义方向 | 回测有效方向 | 命中率 / 基准 | 超额命中 "
            "| 样本数 | 有效上涨概率 | 模型权重 | 权重占比 | 概率贡献 |"
        )
        out.append(
            "|----------|----------|--------------|---------------|----------:"
            "|--------:|--------------:|---------:|---------:|---------:|"
        )
        for item in contributions:
            effective = item.effective_direction_text
            if item.is_reversed:
                effective += "（反向）"
            out.append(
                f"| {_markdown_cell(item.name)} "
                f"| {item.nominal_direction_text} "
                f"| **{effective}** "
                f"| {item.success_rate:.1%} / {item.baseline_success_rate:.1%} "
                f"| {item.excess_success_rate:+.1%} "
                f"| {item.samples} "
                f"| {item.effective_probability_up:.1%} "
                f"| {item.backtest_weight:.3f} "
                f"| {item.weight_share:.1%} "
                f"| {item.probability_point_contribution * 100:+.2f} 个百分点 |"
            )
        out.append("")
        horizon_result = report.horizons[horizon]
        out.append(
            f"> 本周期历史上涨基准为 "
            f"**{horizon_result.baseline_probability_up:.1%}**；"
            f"信号调整后变化 "
            f"{(horizon_result.probability_up - horizon_result.baseline_probability_up) * 100:+.2f} 个百分点，"
            f"因此上涨概率为 **{horizon_result.probability_up:.1%}**。"
        )
        out.append("")
    return out


def _build_markdown(report: QuantitativeReport,
                    forecast: Optional[MultiHorizonForecast],
                    name_key: str,
                    backtest_n: Optional[int] = None,
                    fundamental: Optional[FundamentalSnapshot] = None,
                    fundamental_trend: Optional[FundamentalTrend] = None,
                    signal_artifact: Optional[BacktestArtifact] = None,
                    fused_forecast: Optional[FusedForecast] = None) -> str:
    """组合 markdown 报告。"""
    lines: list[str] = []
    lines.append(f"# {report.name}({name_key}) 综合分析报告")
    lines.append("")
    lines.append(f"- 数据源: {report.data_source}")
    lines.append(f"- 数据量: {report.data_days} 天")
    if backtest_n is not None and backtest_n != report.data_days:
        # 回测器剔除了非正收盘价后的可用样本数，明确标出避免误解
        lines.append(f"- 回测可用样本: {backtest_n} 天"
                     f"（已剔除前复权溢出的 {report.data_days - backtest_n} 条）")
    lines.append(f"- 分析时点: {report.anchor_date}")
    lines.append(f"- 基准价: {report.anchor_price:.2f}")
    lines.append(f"- 生成时间: "
                 f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    lines.append("## 1. 综合预测与指标形态子模型")
    lines.append("")
    lines.extend(_render_fused_forecast(fused_forecast))

    lines.append("### 1.2 指标形态子模型")
    lines.append("")
    lines.append("> 只聚合当前实际触发的形态；权重和方向成功率来自无未来函数回测。")
    lines.append("> 趋势文字与 `[+]`/`[-]` 图标使用统一门槛：上涨概率 ≥60% 为偏多，"
                 "≤40% 为偏空，其余为中性。")
    lines.append("")
    lines.append("| 周期 | 上涨概率 | 下跌概率 | 趋势 | 有效信号 |")
    lines.append("|------|----------|----------|------|----------|")
    for days, result in sorted(report.horizons.items()):
        lines.append(
            f"| {_direction_icon(result.probability_up)} {days}日 "
            f"| {result.probability_up:.1%} | {result.probability_down:.1%} "
            f"| {result.trend} | {result.contributing_signals} |"
        )
    lines.append("")

    # ---- 多周期预测（来自 HorizonBacktester）----
    lines.append("## 2. 多周期涨跌预测（历史相似态回测）")
    lines.append("")
    lines.append("> 做法：找出历史上与当前特征向量最相似的 top-K 天，"
                 "按距离赋予核权重，再统计这些历史日 N 天后的真实涨跌。"
                 "原始概率会按有效样本量和相似度质量向 50% 收缩，并通过逐时点"
                 "Brier 校准得到进入第 1.1 节综合概率的可靠性权重。")
    lines.append("")
    if forecast is None:
        lines.append("> 数据不足，无法跑历史相似态回测（至少需要 ~160 个有效交易日）。")
        lines.append("")
    else:
        lines.append(
            "| 周期 | 距离加权原始概率 | 收缩后上涨概率 | 期望收益 "
            "| 上涨/下跌样本均值 | 有效样本/样本数 | Brier/校准数 "
            "| 校准技能 | 融合可靠性 |"
        )
        lines.append(
            "|------|------------------|----------------|----------"
            "|-------------------|-----------------|--------------"
            "|----------|------------|"
        )
        for fc in [forecast.short, forecast.medium, forecast.long]:
            if fc is None:
                continue
            icon = _direction_icon(fc.prob_up)
            brier = (
                f"{fc.calibration_brier:.3f}/{fc.calibration_samples}"
                if fc.calibration_brier is not None else "不可用"
            )
            lines.append(
                f"| {icon} {fc.label} "
                f"| {fc.raw_prob_up:.1%} "
                f"| **{fc.prob_up:.1%}** "
                f"| {fc.expected_return * 100:+.2f}% "
                f"| {fc.avg_positive * 100:+.2f}% / "
                f"{fc.avg_negative * 100:+.2f}% "
                f"| {fc.effective_sample_size:.1f}/{fc.sample_size} "
                f"| {brier} "
                f"| {fc.calibration_skill:.1%} "
                f"| {fc.confidence:.1%} |"
            )
        lines.append("")

        lines.append("### 预测原因（相似态触发条件）")
        lines.append("")
        for fc in [forecast.short, forecast.medium, forecast.long]:
            if fc is None:
                continue
            lines.append(f"- **{fc.label}**：{fc.reason}")
        lines.append("")

        lines.append("### 当前特征的「极端度」（z 分数绝对值，越大越偏离历史均值）")
        lines.append("")
        contrib_sorted = sorted(
            forecast.feature_contribution.items(),
            key=lambda x: x[1], reverse=True,
        )
        lines.append("| 特征 | |z| | 解读 |")
        lines.append("|------|-----|------|")
        for name, z in contrib_sorted:
            tag = "极端" if z > 2 else ("偏离" if z > 1 else "正常")
            lines.append(f"| {name} | {z:.2f} | {tag} |")
        lines.append("")

        if forecast.top_similar_dates:
            lines.append("### 各周期命中的历史相似日（top 10）")
            lines.append("")
            if forecast.similar_dates_by_horizon:
                for horizon, dates in sorted(
                    forecast.similar_dates_by_horizon.items()
                ):
                    lines.append(f"- **{horizon}日**：{', '.join(dates)}")
            else:
                lines.append(", ".join(forecast.top_similar_dates))
            lines.append("")

        lines.append("### 两个子模型对照")
        lines.append("")
        lines.append(
            "> 指标形态模型只看当前触发规则及其全股票池回测权重；"
            "历史相似态模型比较完整特征向量。两者回答的问题不同，"
            "这里并列展示；它们按校准可靠性进入第 1.1 节的综合概率。"
        )
        lines.append("")
        lines.append("| 周期 | 指标形态模型 | 历史相似态模型 | 概率差 | 关系 |")
        lines.append("|------|--------------|----------------|--------|------|")
        for fc in [forecast.short, forecast.medium, forecast.long]:
            if fc is None or fc.horizon_days not in report.horizons:
                continue
            shape_probability = report.horizons[fc.horizon_days].probability_up
            opposite = (shape_probability - 0.5) * (fc.prob_up - 0.5) < 0
            relation = "方向相反" if opposite else "方向一致"
            lines.append(
                f"| {fc.horizon_days}日 "
                f"| {shape_probability:.1%}（{_direction_label(shape_probability)}） "
                f"| {fc.prob_up:.1%}（{_direction_label(fc.prob_up)}） "
                f"| {(shape_probability - fc.prob_up) * 100:+.1f} 个百分点 "
                f"| **{relation}** |"
            )
        lines.append("")

    lines.append("## 3. 当前触发的指标形态：看多与看空")
    lines.append("")
    lines.extend(_render_directional_signals(report, signal_artifact))

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

def analyze_stock(name_key: str, *, db_path: Optional[str] = None,
                  top_k: int = 50,
                  write_report: bool = True,
                  report_dir: Optional[Path] = None,
                  rebuild_features: bool = False) -> Optional[Path]:
    """对指定股票出预测报告。

    :return: 报告文件路径（write_report=True 时），否则 None
    """
    stock_info = config.global_stock_list.get(name_key)
    if stock_info is None:
        _log.error("[%s] 未在 config.global_stock_list 中登记", name_key)
        return None

    # 1. 读 / 算 数据
    quotes, features = _load_or_build(
        name_key,
        db_path,
        rebuild_features=rebuild_features,
    )
    if not quotes:
        _log.error("[%s] 无法获取行情数据", name_key)
        return None
    if not features:
        _log.error("[%s] 无法获取量化特征", name_key)
        return None

    # 2. 统一量化服务：特征 → 形态 → 回测权重 → 多周期概率
    quote_impl = DbQuoteAPI(db_path=db_path)
    artifact_repository = BacktestArtifactRepository()
    try:
        service = QuantitativeAnalysisService(
            quote_impl,
            artifact_repository=artifact_repository,
        )
        report = service.analyze_quotes(name_key, quotes)
    finally:
        quote_impl.close()
    if report is None:
        _log.error("[%s] 量化分析失败", name_key)
        return None

    # 3. 多周期相似态回测
    bt = HorizonBacktester(quotes, features)
    forecast = bt.run(top_k=top_k)
    fused_forecast = fuse_forecasts(report, forecast)

    # 4. 基本面快照（最新一份已公告财报；缺数据自动 fallback 到 None）
    #    传 as_of=最新交易日，确保 PIT 合规（不会拿到未公告的数据）。
    fundamental: Optional[FundamentalSnapshot] = None
    fundamental_trend: Optional[FundamentalTrend] = None
    try:
        with closing(FinancialReportRepository(db_path)) as repository:
            fundamental = build_snapshot(name_key, repository,
                                          as_of=quotes[-1].date)
            # 长期分析需要全量历史 rows + 当前价 + 历史股价
            rows = repository.get_reports(name_key)
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
                         fundamental_trend=fundamental_trend,
                         signal_artifact=artifact_repository.load(),
                         fused_forecast=fused_forecast)
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
# 权重重生成
# ===========================================================================

def _rebuild_signal_statistics(db_path: Optional[str] = None) -> bool:
    """重新回测全部注册形态并生成版本化成功率/权重。"""
    try:
        with MarketDataRepository(db_path) as repository:
            datasets = {
                symbol: repository.get_range(symbol)
                for symbol in config.global_stock_list
            }
        artifact = SignalBacktester().run(datasets)
        BacktestArtifactRepository().save(artifact)
    except Exception as e:  # noqa: BLE001
        _log.error("形态回测执行异常: %s", e)
        return False
    return True


# ===========================================================================
# CLI
# ===========================================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="股票综合分析工具：行情/形态信号/历史相似态预测",
    )
    parser.add_argument("stock", help="股票 name_key (如 Tencent)")
    parser.add_argument("--db", help="数据库路径（不指定走默认）")
    parser.add_argument("--top-k", type=int, default=50,
                        help="历史相似日数量，default: 50")
    parser.add_argument("--no-write", action="store_true",
                        help="不落盘 markdown，仅控制台输出")
    parser.add_argument("--rebuild-features", action="store_true",
                        help="仅使用本地 K 线强制重建量化特征")
    parser.add_argument("--rebuild-signal-stats", action="store_true",
                        help="重新回测形态成功率、样本量和权重后再出报告")
    parser.add_argument("--report-dir", help="自定义报告目录")
    args = parser.parse_args()

    report_dir = Path(args.report_dir) if args.report_dir else None

    if args.rebuild_signal_stats:
        _rebuild_signal_statistics(args.db)
        print("\n形态回测统计已重建，继续出报告……\n")

    path = analyze_stock(
        args.stock,
        db_path=args.db,
        top_k=args.top_k,
        write_report=not args.no_write,
        report_dir=report_dir,
        rebuild_features=args.rebuild_features,
    )

    return 0 if path is not None or args.no_write else 1


if __name__ == "__main__":
    sys.exit(main())
