"""Temporal (walk-forward) evaluation for the return-regression model.

The dataset is ordered by date, so a simple time split is leak-free.  Each fold
trains on data strictly before the validation block and predicts on the block.
Reported metrics are standard quantitative research statistics:

- ``IC``: rank (Spearman) correlation between predicted and realized return.
- ``ICIR``: IC mean over IC standard deviation across folds.
- ``long_short``: annualized-ish mean return of top-minus-bottom quintile.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .dataset import ReturnDataset
from .model import MLPRegressor


@dataclass
class EvaluationResult:
    folds: int = 0
    ic: list[float] = field(default_factory=list)
    ic_mean: float = 0.0
    icir: float = 0.0
    long_short: list[float] = field(default_factory=list)
    long_short_mean: float = 0.0

    def summary(self) -> str:
        return (
            f"folds={self.folds} | IC mean={self.ic_mean:.4f} "
            f"ICIR={self.icir:.3f} | long-short mean={self.long_short_mean:.4f}"
        )


def _rank_ic(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Spearman rank correlation between two equal-length vectors."""
    if y_true.size < 2:
        return 0.0
    true_rank = np.argsort(np.argsort(y_true)).astype(np.float64)
    pred_rank = np.argsort(np.argsort(y_pred)).astype(np.float64)
    true_rank -= true_rank.mean()
    pred_rank -= pred_rank.mean()
    denominator = np.sqrt((true_rank ** 2).sum() * (pred_rank ** 2).sum())
    if denominator == 0:
        return 0.0
    return float((true_rank * pred_rank).sum() / denominator)


def _long_short(y_true: np.ndarray, y_pred: np.ndarray, quintiles: int = 5) -> float:
    """Mean return of the top quintile minus the bottom quintile."""
    if y_true.size < quintiles * 2:
        return 0.0
    order = np.argsort(y_pred)
    split = np.array_split(order, quintiles)
    bottom = y_true[split[0]].mean()
    top = y_true[split[-1]].mean()
    return float(top - bottom)


@dataclass
class WalkForwardEvaluator:
    """Chronological walk-forward validation with a fixed number of folds."""

    n_folds: int = 5
    model: MLPRegressor | None = None

    def __post_init__(self) -> None:
        self.model = self.model or MLPRegressor()

    def evaluate(self, dataset: ReturnDataset) -> EvaluationResult:
        n = dataset.n_samples
        if n < self.n_folds * 2:
            raise ValueError("not enough samples for walk-forward evaluation")

        boundaries = np.linspace(0, n, self.n_folds + 1).astype(int)
        result = EvaluationResult()
        for fold in range(self.n_folds):
            train_start, train_end = boundaries[fold], boundaries[fold + 1]
            val_end = boundaries[fold + 2] if fold + 2 <= self.n_folds else n
            if train_end >= val_end:
                continue

            train_mask = np.zeros(n, dtype=bool)
            train_mask[train_start:train_end] = True
            val_mask = np.zeros(n, dtype=bool)
            val_mask[train_end:val_end] = True

            model = MLPRegressor(
                hidden_units=self.model.hidden_units,
                learning_rate=self.model.learning_rate,
                epochs=self.model.epochs,
                batch_size=self.model.batch_size,
                weight_decay=self.model.weight_decay,
                seed=self.model.seed + fold,
            )
            model.fit(dataset.X[train_mask], dataset.y[train_mask])
            y_pred = model.predict(dataset.X[val_mask])
            y_true = dataset.y[val_mask]

            ic = _rank_ic(y_true, y_pred)
            ls = _long_short(y_true, y_pred)
            result.ic.append(ic)
            result.long_short.append(ls)
            result.folds += 1

        result.ic_mean = float(np.mean(result.ic)) if result.ic else 0.0
        ic_std = float(np.std(result.ic)) if result.ic else 1.0
        result.icir = result.ic_mean / ic_std if ic_std else 0.0
        result.long_short_mean = (
            float(np.mean(result.long_short)) if result.long_short else 0.0
        )
        return result


__all__ = ["EvaluationResult", "WalkForwardEvaluator", "_rank_ic", "_long_short"]
