"""Application entry points for training and using the ML return model."""

from __future__ import annotations

from dataclasses import dataclass

from .dataset import ReturnDataset, ReturnDatasetBuilder
from .evaluation import EvaluationResult, WalkForwardEvaluator
from .model import MLPRegressor
from .signal import MLSignalRule


@dataclass
class MLTrainingResult:
    model: MLPRegressor
    evaluation: EvaluationResult
    dataset: ReturnDataset

    def summary(self) -> str:
        return (
            f"样本={self.dataset.n_samples} 特征={self.dataset.n_features} | "
            f"{self.evaluation.summary()}"
        )


def train_return_model(
    *,
    horizon: int = 5,
    symbols: list[str] | None = None,
    db_path: str | None = None,
    hidden_units: int = 64,
    epochs: int = 50,
    n_folds: int = 5,
) -> MLTrainingResult:
    """Build the dataset, walk-forward evaluate, and fit a final model on all data."""
    builder = ReturnDatasetBuilder(horizon=horizon, db_path=db_path)
    dataset = builder.build(symbols)

    base = MLPRegressor(hidden_units=hidden_units, epochs=epochs)
    evaluator = WalkForwardEvaluator(n_folds=n_folds, model=base)
    evaluation = evaluator.evaluate(dataset)

    final = MLPRegressor(hidden_units=hidden_units, epochs=epochs, seed=42)
    final.fit(dataset.X, dataset.y)

    return MLTrainingResult(model=final, evaluation=evaluation, dataset=dataset)


def make_signal_rule(model: MLPRegressor) -> MLSignalRule:
    """Wrap a fitted model as a signal rule for the existing pipeline."""
    return MLSignalRule(model)


__all__ = ["MLTrainingResult", "train_return_model", "make_signal_rule"]
