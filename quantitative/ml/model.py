"""A small, dependency-free multi-layer perceptron for return regression.

Implemented in pure NumPy so the machine-learning domain stays consistent with
the rest of the codebase (no torch/scikit-learn).  The model standardizes
inputs on ``fit``, uses a single hidden layer with ReLU activation, and trains
with mini-batch gradient descent and L2 weight decay to keep the small
financial dataset from overfitting.

Numerical notes:

- Targets are standardized to zero mean / unit variance so the MSE loss is
  well scaled across stocks with very different volatility.
- Feature standardization is fitted on the training split only, then applied
  to validation/test, preventing leakage.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class MLPRegressor:
    """Single-hidden-layer ReLU network trained with mini-batch SGD."""

    hidden_units: int = 64
    learning_rate: float = 1e-3
    epochs: int = 50
    batch_size: int = 256
    weight_decay: float = 1e-4
    seed: int = 0

    # Fitted state.
    _input_mean: np.ndarray = field(default=None, repr=False, init=False)
    _input_scale: np.ndarray = field(default=None, repr=False, init=False)
    _target_mean: float = field(default=0.0, repr=False, init=False)
    _target_scale: float = field(default=1.0, repr=False, init=False)
    _W1: np.ndarray = field(default=None, repr=False, init=False)
    _b1: np.ndarray = field(default=None, repr=False, init=False)
    _W2: np.ndarray = field(default=None, repr=False, init=False)
    _b2: np.ndarray = field(default=None, repr=False, init=False)

    def _init_weights(self, n_features: int) -> None:
        rng = np.random.default_rng(self.seed)
        # He initialization for ReLU activations.
        limit = np.sqrt(6.0 / max(n_features, 1))
        self._W1 = rng.uniform(-limit, limit, size=(n_features, self.hidden_units))
        self._b1 = np.zeros(self.hidden_units)
        # Output layer uses a smaller scale.
        self._W2 = rng.uniform(-0.1, 0.1, size=(self.hidden_units,))
        self._b2 = np.zeros(1)

    def _standardize(self, X: np.ndarray, fit: bool) -> np.ndarray:
        if fit:
            self._input_mean = X.mean(axis=0)
            self._input_scale = X.std(axis=0)
            self._input_scale[self._input_scale == 0] = 1.0
        return (X - self._input_mean) / self._input_scale

    @staticmethod
    def _relu(z: np.ndarray) -> np.ndarray:
        return np.maximum(z, 0.0)

    def _forward(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        z1 = X @ self._W1 + self._b1
        a1 = self._relu(z1)
        return a1, (a1 @ self._W2 + self._b2).reshape(-1)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "MLPRegressor":
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        n_samples, n_features = X.shape

        self._target_mean = float(y.mean())
        self._target_scale = float(y.std()) or 1.0
        y_std = (y - self._target_mean) / self._target_scale

        X_std = self._standardize(X, fit=True)
        self._init_weights(n_features)

        n_batches = max(1, int(np.ceil(n_samples / self.batch_size)))
        rng = np.random.default_rng(self.seed)
        for _epoch in range(self.epochs):
            order = rng.permutation(n_samples)
            for start in range(0, n_samples, self.batch_size):
                idx = order[start:start + self.batch_size]
                Xb = X_std[idx]
                yb = y_std[idx]
                m = Xb.shape[0]

                z1 = Xb @ self._W1 + self._b1
                a1 = self._relu(z1)
                pred = (a1 @ self._W2 + self._b2).reshape(-1)
                error = pred - yb

                # Gradients of MSE with L2 weight decay.
                grad_W2 = a1.T @ error / m + self.weight_decay * self._W2
                grad_b2 = error.mean()
                d_hidden = np.outer(error, self._W2) * (z1 > 0)
                grad_W1 = Xb.T @ d_hidden / m + self.weight_decay * self._W1
                grad_b1 = d_hidden.mean(axis=0)

                self._W1 -= self.learning_rate * grad_W1
                self._b1 -= self.learning_rate * grad_b1
                self._W2 -= self.learning_rate * grad_W2
                self._b2 -= self.learning_rate * grad_b2

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=np.float64)
        X_std = self._standardize(X, fit=False)
        _, pred = self._forward(X_std)
        return pred * self._target_scale + self._target_mean

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def save(self, path) -> None:
        """Persist all fitted parameters to a ``.npz`` file."""
        from pathlib import Path

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(
            path,
            hidden_units=self.hidden_units,
            input_mean=self._input_mean,
            input_scale=self._input_scale,
            target_mean=np.asarray(self._target_mean),
            target_scale=np.asarray(self._target_scale),
            W1=self._W1,
            b1=self._b1,
            W2=self._W2,
            b2=self._b2,
        )

    @classmethod
    def load(cls, path) -> "MLPRegressor":
        """Restore a previously saved model."""
        data = np.load(path, allow_pickle=False)
        model = cls(hidden_units=int(data["hidden_units"]))
        model._input_mean = data["input_mean"]
        model._input_scale = data["input_scale"]
        model._target_mean = float(data["target_mean"])
        model._target_scale = float(data["target_scale"])
        model._W1 = data["W1"]
        model._b1 = data["b1"]
        model._W2 = data["W2"]
        model._b2 = data["b2"]
        return model


__all__ = ["MLPRegressor"]
