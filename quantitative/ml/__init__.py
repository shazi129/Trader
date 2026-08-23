"""Machine-learning forecasting domain.

This domain learns a mapping from materialized quantitative features to a
forward return target, then exposes the fitted model through the same
``SignalRule`` contract used by the rule-based signals.  It deliberately
depends only on ``quantitative.features`` and ``quote_api`` so it slots into
the existing layered architecture without new third-party dependencies.
"""

from .dataset import ReturnDataset, ReturnDatasetBuilder
from .evaluation import EvaluationResult, WalkForwardEvaluator
from .lstm_model import LSTMModel
from .model import MLPRegressor
from .sequence_dataset import SequenceDataset, SequenceDatasetBuilder
from .service import MLTrainingResult, make_signal_rule, train_return_model
from .signal import MLSignalRule

__all__ = [
    "EvaluationResult",
    "LSTMModel",
    "MLPRegressor",
    "MLSignalRule",
    "MLTrainingResult",
    "ReturnDataset",
    "ReturnDatasetBuilder",
    "SequenceDataset",
    "SequenceDatasetBuilder",
    "WalkForwardEvaluator",
    "make_signal_rule",
    "train_return_model",
]
