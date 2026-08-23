"""Train a return-forecast MLP on the full stock pool, save it, and predict.

One-shot usage:

    python -m quantitative.ml.train_model

Outputs:
- ``database/ml_return_model.npz``   the persisted model
- a per-stock prediction table on stdout
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from quantitative.features import FeatureCalculator
from quantitative.ml import (
    MLSignalRule,
    ReturnDatasetBuilder,
    train_return_model,
)
from quantitative.signals import SignalContext
from quote_api.repository import MarketDataRepository

MODEL_PATH = (
    Path(__file__).resolve().parents[2] / "database" / "ml_return_model_5d.npz"
)


def main() -> int:
    horizon = 5
    result = train_return_model(horizon=horizon, epochs=100, n_folds=5)
    print(result.summary())
    print(f"IC per fold: {[round(v, 4) for v in result.evaluation.ic]}")
    print()

    result.model.save(MODEL_PATH)
    print(f"模型已保存: {MODEL_PATH}")
    print()

    # Predict the latest anchor for every stock in the pool.
    rule = MLSignalRule(result.model)
    print("| 标的 | 预测未来收益 | 方向 |")
    print("|---|---|---|")
    with MarketDataRepository() as market:
        symbols = market.list_symbols()
        rows: list[tuple[str, float, int]] = []
        for symbol in symbols:
            quotes = market.get_range(symbol)
            if not quotes:
                continue
            features = FeatureCalculator().compute(symbol, quotes)
            if not features:
                continue
            context = SignalContext(
                symbol=symbol, quotes=quotes, features=features
            )
            signal = rule.evaluate(context)
            rows.append((symbol, signal.value, signal.direction))
            direction = {1: "看多", -1: "看空", 0: "中性"}[signal.direction]
            print(f"| {symbol} | {signal.value:.4f} | {direction} |")

    if rows:
        values = np.array([r[1] for r in rows])
        print()
        print(
            f"全池预测: 均值={values.mean():.4f} 标准差={values.std():.4f} "
            f"看多 {sum(r[2] > 0 for r in rows)} 只 / 看空 "
            f"{sum(r[2] < 0 for r in rows)} 只"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
