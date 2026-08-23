"""Command line entry points for the ML return-forecast domain.

Usage:

    python -m quantitative.ml.cli train --horizon 20
    python -m quantitative.ml.cli predict Tencent --horizon 20
"""

from __future__ import annotations

import argparse
import sys

from quantitative.features import FeatureCalculator, FeatureRepository
from quantitative.ml.service import make_signal_rule, train_return_model
from quantitative.signals import SignalContext, SignalEngine
from quote_api.repository import MarketDataRepository


def _train(args) -> int:
    result = train_return_model(
        horizon=args.horizon,
        symbols=args.symbols.split(",") if args.symbols else None,
        db_path=args.db,
        hidden_units=args.hidden_units,
        epochs=args.epochs,
        n_folds=args.folds,
    )
    print(result.summary())
    print(f"IC per fold: {[round(v, 4) for v in result.evaluation.ic]}")
    return 0


def _predict(args) -> int:
    # Train (or reuse) a model, then score a single symbol at its latest date.
    result = train_return_model(horizon=args.horizon, db_path=args.db)
    rule = make_signal_rule(result.model)

    with MarketDataRepository(args.db) as market:
        quotes = market.get_range(args.stock)
    if not quotes:
        print("没有可用行情")
        return 1
    features = FeatureCalculator().compute(args.stock, quotes)
    context = SignalContext(symbol=args.stock, quotes=quotes, features=features)
    signal = rule.evaluate(context)
    print(
        f"{args.stock}: {signal.name} active={signal.active} "
        f"direction={signal.direction} value={signal.value:.4f}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ML 收益率预测")
    subparsers = parser.add_subparsers(dest="command", required=True)

    train = subparsers.add_parser("train", help="训练并评估模型")
    train.add_argument("--horizon", type=int, default=5)
    train.add_argument("--symbols", help="逗号分隔，默认全部")
    train.add_argument("--db")
    train.add_argument("--hidden-units", type=int, default=64)
    train.add_argument("--epochs", type=int, default=50)
    train.add_argument("--folds", type=int, default=5)
    train.set_defaults(handler=_train)

    predict = subparsers.add_parser("predict", help="预测单标的未来收益")
    predict.add_argument("stock")
    predict.add_argument("--horizon", type=int, default=5)
    predict.add_argument("--db")
    predict.set_defaults(handler=_predict)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
