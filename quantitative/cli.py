"""Command line entry points for the quantitative domain."""

from __future__ import annotations

import argparse
import sys

from quote_api import QuoteAPIFactory
from quote_api.cached_api import CachedQuoteAPI
from quote_api.repository import MarketDataRepository
from quantitative.analysis import QuantitativeAnalysisService
from quantitative.backtesting import BacktestArtifactRepository, SignalBacktester
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


def _backtest(args) -> int:
    symbols = [item.strip() for item in args.stocks.split(",") if item.strip()]
    datasets = {}
    with MarketDataRepository(args.db) as repository:
        for symbol in symbols:
            datasets[symbol] = repository.get_range(symbol)
    artifact = SignalBacktester(min_history=args.min_history).run(datasets)
    repository = BacktestArtifactRepository(args.output)
    repository.save(artifact)
    print(f"回测完成: {len(symbols)} 个标的，结果写入 {repository.path}")
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
    backtest.add_argument("--stocks", required=True, help="逗号分隔的标的名")
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
