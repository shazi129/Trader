#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stock_advisor 的 Web API 桥接脚本。

供 OpenWorkspace 网站模块（Website/modules/tools/server/index.mjs）通过
``subprocess`` 调用，输出 **纯 JSON**，供前端图表 / 报告下载使用。

支持两个子命令：

    python web_api.py trend  <name_key> [--days 30] [--db PATH]
    python web_api.py report <name_key> [--date YYYY-MM-DD] [--db PATH]
    python web_api.py list

``trend`` 返回最近 ``--days`` 个交易日的：
    - 收盘价序列（close）
    - 逐日多空强度（bullish_strength ∈ [-1, 1]，正=偏多，负=偏空）

``report`` 返回指定交易日（默认最新）的综合分析报告 Markdown 文本。
多空强度的算法与 ``stock_advisor.analyze_stock`` 完全一致（同一个
特征、形态与回测权重模型），只是把
"最新一天"扩展成"截至每个交易日"的逐点快照。

注意：本脚本只读数据库，不触发特征物化 / 不回源拉取数据。若 DB 中缺少
该股票数据，返回空结果（前端应提示先物化量化特征）。
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import sys
from contextlib import closing
from pathlib import Path
from typing import Optional

# 让脚本既能 ``python -m tools.stock_advisor.web_api`` 也能直跑
_THIS_DIR = Path(__file__).resolve().parent
_ROOT = _THIS_DIR.parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config  # noqa: E402
from financial_reports.repository import FinancialReportRepository  # noqa: E402
from financial_reports.analysis import build_snapshot  # noqa: E402
from quote_api import QuoteAPIFactory  # noqa: E402
from quote_api.repository import MarketDataRepository  # noqa: E402
from quantitative.analysis import QuantitativeAnalysisService  # noqa: E402
from quantitative.analysis.aggregation import aggregate_signals  # noqa: E402
from quantitative.backtesting import BacktestArtifactRepository  # noqa: E402
from quantitative.features import FeatureCalculator  # noqa: E402
from quantitative.signals import SignalContext, SignalEngine  # noqa: E402
from quote_api.quote_base import DailyQuote  # noqa: E402

# 复用 stock_advisor 的 markdown 渲染（报告生成用）
try:
    from .stock_advisor import (  # noqa: E402
        _build_markdown,
        _load_or_build,
    )
    from .backtester import HorizonBacktester  # noqa: E402
    from .fundamental_trend import analyze_long_term  # noqa: E402
except ImportError:  # 直接运行 web_api.py 时（非 -m）
    from stock_advisor import (  # type: ignore  # noqa: E402
        _build_markdown,
        _load_or_build,
    )
    from backtester import HorizonBacktester  # type: ignore  # noqa: E402
    from fundamental_trend import analyze_long_term  # type: ignore  # noqa: E402


# ===========================================================================
# 逐日多空强度
# ===========================================================================

def _compute_daily_strength(quotes: list[DailyQuote], days: int
                            ) -> list[dict]:
    """对最近 ``days`` 个交易日，逐日计算多空强度。

    做法：对每个交易日 i，用 ``quotes[:i+1]`` 的历史切片构造信号上下文，
    复用统一特征、形态与回测权重模型，
    得到该日 prob_up ∈ [0.15, 0.85]。再映射成有符号强度：

        strength = (prob_up - 0.5) / 0.35  →  [-1, 1]

    将 20 日上涨概率中心化为强度，
    正值 = 偏多（红柱向上），负值 = 偏空（绿柱向下）。

    只计算最后 ``days`` 根 K 线；更早的历史仅用于满足特征窗口。
    """
    n = len(quotes)
    if n == 0:
        return []

    calculator = FeatureCalculator()
    features = calculator.compute("series", quotes)
    engine = SignalEngine()
    artifact = BacktestArtifactRepository().load()
    start = max(0, n - days)
    out: list[dict] = []
    for i in range(start, n):
        q = quotes[i]
        window = quotes[: i + 1]
        try:
            feature_window = features[:i + 1]
            context = SignalContext("series", window, feature_window)
            signals = engine.evaluate(context)
            horizons = aggregate_signals(signals, artifact)
            primary = horizons[20]
            prob_up = primary.probability_up
            prob_down = primary.probability_down
            trend = primary.trend
            strength = (prob_up - 0.5) / 0.35
            strength = max(-1.0, min(1.0, strength))
            period_net = {
                "short": round(horizons[5].probability_up * 2 - 1, 4),
                "medium": round(horizons[20].probability_up * 2 - 1, 4),
                "long": round(horizons[60].probability_up * 2 - 1, 4),
            }
        except Exception:  # noqa: BLE001
            # 早期窗口特征不足等异常，强度记为 0（中性）
            prob_up, prob_down, trend = 0.5, 0.5, "数据不足"
            strength = 0.0
            period_net = {"short": 0.0, "medium": 0.0, "long": 0.0}

        out.append({
            "date": q.date,
            "close": round(float(q.close), 4),
            "prob_up": round(prob_up, 4),
            "prob_down": round(prob_down, 4),
            # 净多空差值（看多减看空），∈ [-0.7, 0.7]
            # 正数=净偏多（红柱向上），负数=净偏空（绿柱向下）
            "net_strength": round(prob_up - prob_down, 4),
            # 归一化信号（保留兼容，与 net_strength 同号，仅尺度不同）
            "strength": round(strength, 4),
            # 分周期净强度（短/中/长），供前端渲染三根红绿柱
            "period_net": period_net,
            "trend": trend,
        })
    return out


def _cmd_trend(name_key: str, days: int, db_path: Optional[str]) -> dict:
    """返回趋势 JSON 数据结构。"""
    stock_info = config.global_stock_list.get(name_key)
    if stock_info is None:
        return {"ok": False, "error": f"未登记股票: {name_key}"}

    with closing(MarketDataRepository(db_path)) as repository:
        quotes = repository.get_range(name_key)

    if not quotes:
        return {
            "ok": False,
            "error": f"数据库无 {name_key} 的 K 线数据，请先运行 kline_fetcher",
        }

    series = _compute_daily_strength(quotes, days)
    return {
        "ok": True,
        "name_key": name_key,
        "name": stock_info.name,
        "days": len(series),
        "series": series,
    }


# ===========================================================================
# 报告生成（复用 stock_advisor 内部逻辑）
# ===========================================================================

def _cmd_report(name_key: str, date: Optional[str], db_path: Optional[str],
                api: Optional[str] = None) -> dict:
    """生成某日（默认最新）的综合分析报告，返回 Markdown 文本。

    复用 stock_advisor 的 ``_load_or_build`` + 评分 + ``_build_markdown``。
    当指定 ``--date`` 时，把数据截断到该交易日，再生成"截至该日"的报告
    （特征 / 信号 / 回测 / 基本面都以该日为最新，符合 point-in-time）。
    """
    stock_info = config.global_stock_list.get(name_key)
    if stock_info is None:
        return {"ok": False, "error": f"未登记股票: {name_key}"}

    api = api or "futu"
    quotes, features = _load_or_build(name_key, api, db_path, force_refresh=False)
    if not quotes:
        return {"ok": False, "error": f"无法获取 {name_key} 行情数据"}

    if date:
        # 截断到目标交易日（含）
        cutoff = date.strip()
        quotes = [q for q in quotes if q.date <= cutoff]
        if not quotes:
            return {"ok": False, "error": f"{cutoff} 之前无有效行情"}
        features = [snapshot for snapshot in features if snapshot.date <= cutoff]

    service = QuantitativeAnalysisService(QuoteAPIFactory.create(api))
    report = service.analyze_quotes(name_key, quotes)
    if report is None:
        return {"ok": False, "error": f"无法分析 {name_key}"}

    # 回测 + 基本面（异常兜底，不阻断主流程）
    forecast = None
    fundamental = None
    fundamental_trend = None
    try:
        bt = HorizonBacktester(quotes, features)
        forecast = bt.run(top_k=50)
    except Exception:  # noqa: BLE001
        forecast = None
    try:
        with closing(FinancialReportRepository(db_path)) as repository:
            fundamental = build_snapshot(name_key, repository, as_of=quotes[-1].date)
            rows = repository.get_reports(name_key)
            rows_pit = [r for r in rows
                        if r.get("AnnounceDate") and r["AnnounceDate"] <= quotes[-1].date]
            if rows_pit:
                from stock_advisor import _build_price_map  # type: ignore
                price_map = _build_price_map(quotes, rows_pit)
                fundamental_trend = analyze_long_term(
                    rows_pit, current_price=quotes[-1].close,
                    price_history=price_map,
                )
    except Exception:  # noqa: BLE001
        fundamental = None
        fundamental_trend = None

    md = _build_markdown(report, forecast, name_key,
                         backtest_n=None,
                         fundamental=fundamental,
                         fundamental_trend=fundamental_trend)
    return {
        "ok": True,
        "name_key": name_key,
        "name": stock_info.name,
        "date": quotes[-1].date,
        "markdown": md,
    }


def _cmd_list() -> dict:
    """返回所有已登记股票清单。"""
    items = [
        {"name_key": k, "name": v.name}
        for k, v in config.global_stock_list.items()
    ]
    return {"ok": True, "stocks": items}


# ===========================================================================
# CLI
# ===========================================================================

def main() -> int:
    # 关键：把 trader.* logger 的 StreamHandler 重定向到 stderr，
    # 避免子进程 stdout 被混入 JSON 输出，导致 Node 端 JSON.parse 失败。
    # （utils/logger.py 默认 StreamHandler(sys.stdout)）
    for h in logging.getLogger("trader").handlers:
        if isinstance(h, logging.StreamHandler):
            h.stream = sys.stderr

    parser = argparse.ArgumentParser(description="stock_advisor Web API 桥")
    sub = parser.add_subparsers(dest="command", required=True)

    p_trend = sub.add_parser("trend", help="返回最近 N 日收盘价 + 逐日多空强度")
    p_trend.add_argument("name_key")
    p_trend.add_argument("--days", type=int, default=30)
    p_trend.add_argument("--db", default=None)

    p_report = sub.add_parser("report", help="生成综合分析报告 Markdown")
    p_report.add_argument("name_key")
    p_report.add_argument("--date", default=None)
    p_report.add_argument("--db", default=None)

    sub.add_parser("list", help="列出所有股票")

    args = parser.parse_args()

    if args.command == "list":
        result = _cmd_list()
    elif args.command == "trend":
        result = _cmd_trend(args.name_key, args.days, args.db)
    elif args.command == "report":
        result = _cmd_report(args.name_key, args.date, args.db)
    else:
        result = {"ok": False, "error": f"未知命令: {args.command}"}

    # 用 ensure_ascii=True（默认）输出 \uXXXX 转义，避免 Windows 下
    # stdout 管道编码问题导致中文乱码；Node 端 JSON.parse 后浏览器
    # fetch().json() 会自动转回 UTF-8 字符串。
    print(json.dumps(result, ensure_ascii=True))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
