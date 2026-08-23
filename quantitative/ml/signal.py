"""Bridge the fitted ML model into the rule-based signal pipeline.

``MLSignalRule`` implements the same ``SignalRule`` contract as the hand-written
pattern rules, so a trained model participates in ``SignalEngine`` evaluation,
``SignalBacktester`` backtesting, and ``aggregate_signals`` aggregation without
modifying any of those components.

The rule produces a directional signal from the model's predicted forward
return: a prediction above the positive threshold is bullish, below the
negative threshold is bearish, otherwise neutral.  ``value`` carries the raw
predicted return and ``strength`` the normalized confidence.
"""

from __future__ import annotations

import numpy as np

from quantitative.features.catalog import FEATURE_KEYS
from quantitative.signals.base import SignalContext, SignalRule

from .model import MLPRegressor


class MLSignalRule(SignalRule):
    signal_id = "ml_return_forecast"
    name = "ML收益率预测"
    category = "ml"

    def __init__(
        self,
        model: MLPRegressor,
        *,
        positive_threshold: float = 0.0,
        negative_threshold: float = 0.0,
        feature_names: tuple[str, ...] = FEATURE_KEYS,
    ) -> None:
        self.model = model
        self.positive_threshold = positive_threshold
        self.negative_threshold = negative_threshold
        self.feature_names = feature_names

    def _feature_vector(self, context: SignalContext) -> np.ndarray:
        values = [context.latest.get(name) for name in self.feature_names]
        return np.asarray(values, dtype=np.float64).reshape(1, -1)

    def evaluate(self, context: SignalContext):
        row = self._feature_vector(context)
        if np.any(np.isnan(row)):
            return self.result(False, 0, description="特征不完整，无法预测")

        predicted = float(self.model.predict(row)[0])
        if predicted > self.positive_threshold:
            direction = 1
        elif predicted < self.negative_threshold:
            direction = -1
        else:
            direction = 0

        active = direction != 0
        strength = min(1.0, abs(predicted))
        return self.result(
            active,
            direction,
            value=predicted,
            strength=strength if strength > 0 else 0.01,
            description=f"预测未来收益={predicted:.4f}",
        )


__all__ = ["MLSignalRule"]
