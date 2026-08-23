"""A single-layer LSTM for sequence (past-30-day OHLCV) return regression.

Implemented in pure NumPy, consistent with the rest of the ML domain (no
torch).  The forward pass runs an LSTM over the time axis and feeds the final
hidden state into a linear output head that predicts the forward return.

The backward pass is backpropagation through time (BPTT) with full gradients,
using L2 weight decay.  To keep the small financial dataset from overfitting,
training stops early when the validation MSE stops improving.

Reference implementation note: the LSTM cell follows the standard
input/forget/output + candidate gate formulation (no peephole connections).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _tanh(x: np.ndarray) -> np.ndarray:
    return np.tanh(x)


@dataclass
class LSTMModel:
    """Single-layer LSTM -> linear head, trained with Adam + BPTT."""

    hidden_units: int = 32
    learning_rate: float = 1e-3
    epochs: int = 50
    weight_decay: float = 1e-4
    seed: int = 0
    val_frac: float = 0.2
    patience: int = 10

    # Fitted state.
    _W: np.ndarray = field(default=None, repr=False, init=False)  # (4H, in+H)
    _b: np.ndarray = field(default=None, repr=False, init=False)  # (4H,)
    _Wy: np.ndarray = field(default=None, repr=False, init=False)  # (H,)
    _by: float = field(default=0.0, repr=False, init=False)
    _target_mean: float = field(default=0.0, repr=False, init=False)
    _target_scale: float = field(default=1.0, repr=False, init=False)

    # -- forward -----------------------------------------------------------
    def _forward_one(self, x: np.ndarray, h: np.ndarray, c: np.ndarray):
        """One LSTM timestep. Returns new h, c, and cached gates."""
        z = np.concatenate([x, h], axis=1) @ self._W + self._b  # (n, 4H)
        i = _sigmoid(z[:, 0:self.hidden_units])
        f = _sigmoid(z[:, self.hidden_units:2 * self.hidden_units])
        o = _sigmoid(z[:, 2 * self.hidden_units:3 * self.hidden_units])
        g = _tanh(z[:, 3 * self.hidden_units:4 * self.hidden_units])
        c_new = f * c + i * g
        h_new = o * _tanh(c_new)
        # cache: (i, f, o, g, z, c_prev, h_prev, c_new)
        return h_new, c_new, (i, f, o, g, z, c, h, c_new)

    def _forward(self, X: np.ndarray) -> tuple[np.ndarray, list]:
        """Run the LSTM over a batch of sequences. Returns outputs + caches."""
        n, T, _ = X.shape
        H = self.hidden_units
        h = np.zeros((n, H))
        c = np.zeros((n, H))
        caches = []
        for t in range(T):
            h, c, cache = self._forward_one(X[:, t, :], h, c)
            caches.append(cache)
        y = h @ self._Wy + self._by
        return y, caches

    # -- fit ---------------------------------------------------------------
    def fit(self, X: np.ndarray, y: np.ndarray) -> "LSTMModel":
        X = np.asarray(X, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        n, T, D = X.shape

        self._target_mean = float(y.mean())
        self._target_scale = float(y.std()) or 1.0
        y_std = (y - self._target_mean) / self._target_scale

        self._init_weights(D)

        # Chronological validation split (no shuffle) to avoid lookahead.
        n_val = int(n * self.val_frac)
        X_train, y_train = X[:-n_val], y_std[:-n_val]
        X_val, y_val = X[-n_val:], y_std[-n_val:]

        # Adam state.
        m_w = {k: np.zeros_like(v) for k, v in self._params().items()}
        v_w = {k: np.zeros_like(v) for k, v in self._params().items()}
        t_step = 0
        best_val = float("inf")
        best_params = None
        stale = 0

        for _epoch in range(self.epochs):
            pred, _ = self._forward(X_train)
            loss, grads = self._backward(X_train, y_train, pred)
            self._adam_update(grads, m_w, v_w, t_step := t_step + 1)

            val_pred, _ = self._forward(X_val)
            val_mse = float(((val_pred - y_val) ** 2).mean())
            if val_mse < best_val:
                best_val = val_mse
                best_params = {k: v.copy() for k, v in self._params().items()}
                stale = 0
            else:
                stale += 1
                if stale >= self.patience:
                    break

        if best_params is not None:
            self._set_params(best_params)
        return self

    def _init_weights(self, D: int) -> None:
        H = self.hidden_units
        rng = np.random.default_rng(self.seed)
        limit = np.sqrt(6.0 / (D + H))
        self._W = rng.uniform(-limit, limit, size=(D + H, 4 * H))
        self._b = np.zeros(4 * H)
        self._b[H:2 * H] = 1.0  # forget gate bias -> 1 (remember by default)
        self._Wy = rng.uniform(-0.5, 0.5, size=(H,))
        self._by = 0.0

    def _params(self) -> dict[str, np.ndarray]:
        return {"W": self._W, "b": self._b, "Wy": self._Wy, "by": np.asarray(self._by)}

    def _set_params(self, params: dict) -> None:
        self._W = params["W"]
        self._b = params["b"]
        self._Wy = params["Wy"]
        self._by = float(params["by"])

    # -- backward (BPTT) ---------------------------------------------------
    def _backward(self, X, y, pred):
        n, T, D = X.shape
        H = self.hidden_units

        # Re-run forward, keeping all gate caches.
        h = np.zeros((n, H))
        c = np.zeros((n, H))
        caches = []
        for t in range(T):
            h, c, cache = self._forward_one(X[:, t, :], h, c)
            caches.append(cache)

        # Output layer gradient: d/dpred mean((pred-y)^2) = 2*(pred-y)/n
        # No L2 on the output head: it must learn dispersion, not be shrunk.
        dy = 2.0 * (pred - y) / n
        g_Wy = h.T @ dy
        g_by = float(dy.sum())

        dh = np.outer(dy, self._Wy)  # (n, H) gradient w.r.t. final h
        dc = np.zeros((n, H))
        g_W = np.zeros_like(self._W)
        g_b = np.zeros_like(self._b)

        for t in reversed(range(T)):
            x_t = X[:, t, :]
            i, f, o, g, z, c_prev, h_prev, c_new = caches[t]

            # Back through h_new = o * tanh(c_new)
            do = dh * np.tanh(c_new)
            dc = dc + dh * o * (1.0 - np.tanh(c_new) ** 2)

            # Back through c_new = f * c_prev + i * g
            di = dc * g
            dg = dc * i
            df = dc * c_prev
            dc_prev = dc * f

            d_i = di * i * (1.0 - i)
            d_f = df * f * (1.0 - f)
            d_o = do * o * (1.0 - o)
            d_g = dg * (1.0 - g ** 2)

            dz = np.concatenate([d_i, d_f, d_o, d_g], axis=1)  # (n, 4H)
            zcat = np.concatenate([x_t, h_prev], axis=1)  # (n, D+H)
            g_W += zcat.T @ dz
            g_b += dz.sum(axis=0)

            dh = dz @ self._W.T  # (n, D+H)
            dh = dh[:, D:]  # only the h part propagates back in time
            dc = dc_prev

        g_W += self.weight_decay * self._W
        grads = {"W": g_W, "b": g_b, "Wy": g_Wy, "by": np.asarray(g_by)}
        return float(((pred - y) ** 2).mean()), grads

    # -- optimizer ---------------------------------------------------------
    def _adam_update(self, grads, m, v, t_step, beta1=0.9, beta2=0.999, eps=1e-8):
        for key in self._params():
            grad = grads[key]
            m[key] = beta1 * m[key] + (1 - beta1) * grad
            v[key] = beta2 * v[key] + (1 - beta2) * (grad ** 2)
            m_hat = m[key] / (1 - beta1 ** t_step)
            v_hat = v[key] / (1 - beta2 ** t_step)
            update = self.learning_rate * m_hat / (np.sqrt(v_hat) + eps)
            if key == "by":
                self._by -= float(update)
            elif key == "Wy":
                self._Wy -= update
            elif key == "W":
                self._W -= update
            else:
                self._b -= update

    # -- predict / persist -------------------------------------------------
    def predict(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=np.float64)
        pred, _ = self._forward(X)
        return pred * self._target_scale + self._target_mean

    def save(self, path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(
            path,
            hidden_units=self.hidden_units,
            W=self._W,
            b=self._b,
            Wy=self._Wy,
            by=np.asarray(self._by),
            target_mean=np.asarray(self._target_mean),
            target_scale=np.asarray(self._target_scale),
        )

    @classmethod
    def load(cls, path) -> "LSTMModel":
        data = np.load(path, allow_pickle=False)
        model = cls(hidden_units=int(data["hidden_units"]))
        model._W = data["W"]
        model._b = data["b"]
        model._Wy = data["Wy"]
        model._by = float(data["by"])
        model._target_mean = float(data["target_mean"])
        model._target_scale = float(data["target_scale"])
        return model


__all__ = ["LSTMModel"]
