"""Train the LSTM sequence model on past-30-day OHLCV, save, and predict.

One-shot usage:

    python -m quantitative.ml.train_lstm

Outputs:
- ``database/ml_lstm_model.npz``   the persisted LSTM model
- a per-stock prediction table on stdout

The dataset is sorted chronologically (see ``SequenceDatasetBuilder``), so a
simple time split is a valid leak-free train/validation split: every fold
trains only on data before its validation block.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from quantitative.ml.evaluation import _rank_ic
from quantitative.ml.lstm_model import LSTMModel
from quantitative.ml.sequence_dataset import SequenceDatasetBuilder
from quote_api.repository import MarketDataRepository

MODEL_PATH = (
    Path(__file__).resolve().parents[2] / "database" / "ml_lstm_model.npz"
)


def _walk_forward(dataset, n_folds: int = 5, **model_kwargs) -> dict:
    """Chronological walk-forward: train on earlier dates, test on later ones."""
    n = dataset.n_samples
    boundaries = np.linspace(0, n, n_folds + 1).astype(int)
    ic_list: list[float] = []
    pred_stds: list[float] = []
    for fold in range(n_folds):
        train_start, train_end = boundaries[fold], boundaries[fold + 1]
        val_end = boundaries[fold + 2] if fold + 2 <= n_folds else n
        if train_end >= val_end:
            continue
        model = LSTMModel(seed=model_kwargs.get("seed", 0) + fold, **{
            k: v for k, v in model_kwargs.items() if k != "seed"
        })
        model.fit(dataset.X[train_start:train_end], dataset.y[train_start:train_end])
        y_pred = model.predict(dataset.X[train_end:val_end])
        y_true = dataset.y[train_end:val_end]
        ic_list.append(_rank_ic(y_true, y_pred))
        pred_stds.append(float(y_pred.std()))
    return {"ic": ic_list, "pred_std": pred_stds}


def main() -> int:
    lookback, horizon = 30, 5
    builder = SequenceDatasetBuilder(lookback=lookback, horizon=horizon)
    dataset = builder.build()
    print(
        f"样本={dataset.n_samples} 窗口={dataset.lookback}日 "
        f"字段={dataset.n_fields} 预测={horizon}日"
    )
    print(f"目标收益: 均值={dataset.y.mean():.4f} 标准差={dataset.y.std():.4f}")
    print()

    result = _walk_forward(
        dataset, n_folds=5, hidden_units=32, epochs=50, patience=10
    )
    ic_list = result["ic"]
    ic_mean = float(np.mean(ic_list)) if ic_list else 0.0
    ic_std = float(np.std(ic_list)) if ic_list else 1.0
    print(f"IC per fold: {[round(v, 4) for v in ic_list]}")
    print(f"预测std per fold: {[round(v, 5) for v in result['pred_std']]}")
    print(f"IC mean={ic_mean:.4f} ICIR={ic_mean / ic_std:.3f}")
    print()

    # Final model trained on all data (chronologically split internally).
    final = LSTMModel(hidden_units=32, epochs=50, seed=42, patience=10)
    final.fit(dataset.X, dataset.y)
    final.save(MODEL_PATH)
    print(f"模型已保存: {MODEL_PATH}")
    print()

    # Predict the latest anchor for every stock.
    print("| 标的 | 预测5日收益 | 方向 |")
    print("|---|---|---|")
    with MarketDataRepository() as market:
        rows: list[tuple[str, float, int]] = []
        for symbol in market.list_symbols():
            quotes = market.get_range(symbol)
            if len(quotes) < lookback:
                continue
            matrix = np.asarray(
                [[
                    float(q.open), float(q.high), float(q.low), float(q.close),
                    float(q.volume), float(q.turnover),
                    float(getattr(q, "turnover_rate", 0.0) or 0.0),
                ] for q in quotes],
                dtype=np.float64,
            )
            window = SequenceDatasetBuilder._normalize(matrix[-lookback:])
            pred = float(final.predict(window[np.newaxis, :, :])[0])
            direction = 1 if pred > 0 else -1 if pred < 0 else 0
            rows.append((symbol, pred, direction))
            label = {1: "看多", -1: "看空", 0: "中性"}[direction]
            print(f"| {symbol} | {pred:.4f} | {label} |")

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
