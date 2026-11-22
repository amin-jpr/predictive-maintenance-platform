"""Simple reference baselines for RUL regression.

Two baselines are provided:

1. :func:`build_baseline` — constant median predictor (``DummyRegressor``). Fitted only
   on training targets; ignores all inputs. This is the reference performance floor.
2. :class:`CycleTrendRegressor` — ordinary least squares of capped RUL on the single
   input ``cycle`` (the current cycle index, known at prediction time). This is the
   defensible "simple baseline" for the available data representation: no sensor-to-RUL
   formula is invented, no future information is used, and the model is a true predictive
   baseline (it maps an observed quantity to RUL) rather than a heuristic.

Why no sensor-based "last value" predictor: C-MAPSS provides no direct RUL sensor, so any
mapping from sensor values to RUL must be learned from data — that is exactly what the
regression models in this milestone do. A hand-written sensor formula would be arbitrary
and indefensible. The cycle-trend baseline is documented as a genuine (if weak) predictive
baseline with explicit assumptions: RUL decreases approximately linearly with cycle
index on average across the training fleet.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.dummy import DummyRegressor


def build_baseline(strategy: str = "median") -> DummyRegressor:
    """Build the constant-median baseline. Only ``strategy="median"`` is supported."""
    if strategy != "median":
        raise ValueError(
            f"Unsupported baseline strategy '{strategy}'. Milestone 5 specifies the "
            "constant median predictor only."
        )
    return DummyRegressor(strategy="median")


class CycleTrendRegressor(BaseEstimator, RegressorMixin):
    """Least-squares line of RUL against cycle index (single-column input).

    ``X`` must be a 2-D array with exactly one column containing cycle values.
    Predictions are clipped to be non-negative (RUL cannot be negative).
    """

    def __init__(self, fit_intercept: bool = True) -> None:
        self.fit_intercept = fit_intercept

    @staticmethod
    def _as_cycle_column(X: Any) -> np.ndarray:
        arr = np.asarray(X, dtype=float)
        if arr.ndim == 1:
            arr = arr.reshape(-1, 1)
        if arr.ndim != 2 or arr.shape[1] != 1:
            raise ValueError(
                "CycleTrendRegressor expects a single-column input of cycle values, "
                f"got shape {arr.shape}."
            )
        if not np.all(np.isfinite(arr)):
            raise ValueError("Cycle input contains non-finite values.")
        return arr.ravel()

    def fit(self, X: Any, y: Any) -> CycleTrendRegressor:
        cycles = self._as_cycle_column(X)
        target = np.asarray(y, dtype=float).ravel()
        if cycles.shape[0] != target.shape[0] or cycles.size == 0:
            raise ValueError("Cycle input and target must be non-empty and aligned.")
        if not np.all(np.isfinite(target)):
            raise ValueError("Target contains non-finite values.")
        if self.fit_intercept:
            design = np.column_stack([cycles, np.ones_like(cycles)])
            coef, *_ = np.linalg.lstsq(design, target, rcond=None)
            self.slope_ = float(coef[0])
            self.intercept_ = float(coef[1])
        else:
            self.slope_ = float(np.sum(cycles * target) / np.sum(cycles**2))
            self.intercept_ = 0.0
        self.n_features_in_ = 1
        return self

    def predict(self, X: Any) -> np.ndarray:
        if not hasattr(self, "slope_"):
            raise ValueError("CycleTrendRegressor must be fitted before predict.")
        cycles = self._as_cycle_column(X)
        return np.maximum(self.slope_ * cycles + self.intercept_, 0.0)


def build_cycle_trend_baseline(fit_intercept: bool = True) -> CycleTrendRegressor:
    """Build the cycle-trend simple baseline (OLS of RUL on cycle index)."""
    return CycleTrendRegressor(fit_intercept=fit_intercept)
