"""Command line entry points for the quantitative domain."""

from __future__ import annotations

import argparse
import sys

from quote_api import QuoteAPIFactory
from quote_api.cached_api import CachedQuoteAPI
from quote_api.repository import MarketDataRepository
from quote_api.stock_meta import all_keys
from quantitative.analysis import QuantitativeAnalysisService
from quantitative.backtesting import (
    BacktestArtifact,
    BacktestArtifactRepository,
    SignalBacktester,
)
from quantitative.features.materialization import materialize_symbol


def _analyze(args) -> int:
    market_repository = MarketDataRepository(args.db)
    try:
        if args.api == "db":
            from quote_api.db_api import DbQuoteAPI
            api = DbQuoteAPI(repository=market_repository)
        else:
            raw = QuoteAPIFactory.create(args.api)
            api = CachedQuoteAPI(raw, repository=market_repository)
        service = QuantitativeAnalysisService(api)
        report = service.analyze(
            args.stock, anchor_date=args.date, lookback=args.lookback
        )
        if report is None:
            print("分析失败：没有可用行情")
            return 1
        print(report.summary)
        return 0
    finally:
        market_repository.close()


def _features(args) -> int:
    count = materialize_symbol(
        args.stock,
        source=args.api,
        db_path=args.db,
        force_refresh=args.force_refresh,
    )
    print(f"{args.stock}: 写入 {count} 个特征快照")
    return 0 if count else 1


def _resolve_backtest_symbols(stocks: str | None) -> list[str]:
    """Resolve an explicit comma-separated list or the registered stock pool."""
    candidates = (
        [item.strip() for item in stocks.split(",")]
        if stocks
        else all_keys()
    )
    # Preserve stock-pool order while removing blanks and duplicates.
    return list(dict.fromkeys(item for item in candidates if item))


def _render_backtest_results(
    artifact: BacktestArtifact,
    signal_names: dict[str, str],
) -> str:
    """Render one compact row per signal for terminal output."""
    horizons = tuple(sorted(artifact.horizons))
    lines = [
        "",
        "形态回测结果（背离按事件去重；成功率与个股周期基准比较）",
        f"模型: {artifact.model_version} | 截止日: {artifact.data_cutoff or '-'} "
        f"| 标的数: {len(artifact.universe)}",
        "",
        "| 形态 | "
        + " | ".join(
            f"{h}日：成功率 / 基准 / 样本 / 方向 / 权重"
            for h in horizons
        )
        + " |",
        "|---|" + "---|" * len(horizons),
    ]
    for signal_id in sorted(artifact.metrics):
        cells = []
        for horizon in horizons:
            metric = artifact.metric(signal_id, horizon)
            if metric is None or metric.samples == 0:
                cells.append("无样本")
            else:
                direction = {
                    1: "名义",
                    -1: "样本外反向",
                    0: "禁用",
                }[metric.direction_multiplier]
                cells.append(
                    f"{metric.success_rate:.1%} / "
                    f"{metric.baseline_success_rate:.1%} / "
                    f"{metric.samples} / {direction} / {metric.weight:.3f}"
                )
        label = signal_names.get(signal_id, signal_id)
        lines.append(f"| {label} (`{signal_id}`) | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _backtest(args) -> int:
    symbols = _resolve_backtest_symbols(args.stocks)
    datasets = {}
    with MarketDataRepository(args.db) as repository:
        for symbol in symbols:
            datasets[symbol] = repository.get_range(symbol)
    backtester = SignalBacktester(min_history=args.min_history)
    artifact = backtester.run(datasets)
    if not artifact.universe:
        print("回测失败：股票池中没有具备足够本地 K 线的标的")
        return 1
    repository = BacktestArtifactRepository(args.output)
    repository.save(artifact)
    signal_names = {rule.signal_id: rule.name for rule in backtester.engine.rules}
    print(_render_backtest_results(artifact, signal_names))
    print()
    skipped = [symbol for symbol in symbols if symbol not in artifact.universe]
    print(
        f"回测完成: {len(artifact.universe)}/{len(symbols)} 个标的，"
        f"结果写入 {repository.path}"
    )
    if skipped:
        print(f"跳过（本地数据不足）: {','.join(skipped)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Trader 量化分析")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="执行时点分析")
    analyze.add_argument("stock")
    analyze.add_argument("--date")
    analyze.add_argument("--lookback", type=int, default=500)
    analyze.add_argument("--api", default=QuoteAPIFactory.current_source(),
                         choices=QuoteAPIFactory.available_sources())
    analyze.add_argument("--db")
    analyze.set_defaults(handler=_analyze)

    features = subparsers.add_parser("features", help="计算并保存特征")
    features.add_argument("stock")
    features.add_argument("--api", default=QuoteAPIFactory.current_source(),
                          choices=QuoteAPIFactory.available_sources())
    features.add_argument("--db")
    features.add_argument("--force-refresh", action="store_true")
    features.set_defaults(handler=_features)

    backtest = subparsers.add_parser("backtest", help="回测形态信号")
    backtest.add_argument(
        "--stocks",
        help="逗号分隔的标的名；不传时回测 STOCK_META 中的全部股票",
    )
    backtest.add_argument("--db")
    backtest.add_argument("--min-history", type=int, default=120)
    backtest.add_argument("--output")
    backtest.set_defaults(handler=_backtest)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.handler(args)
    finally:
        QuoteAPIFactory.clear_cache()


if __name__ == "__main__":
    sys.exit(main())
