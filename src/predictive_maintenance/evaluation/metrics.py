"""Regression metrics for remaining-useful-life (RUL) evaluation.

Required metrics: mean absolute error (MAE), root mean squared error (RMSE), and the
NASA/PHM08 asymmetric score. Supplementary diagnostics (median absolute error, error
mean/std, early/late ratios, within-tolerance percentages) support error analysis but
never replace the required metrics.

NASA/PHM08 score convention (Milestone 5 specification):
    d_i = predicted_RUL_i - actual_RUL_i
    s_i = exp(-d_i / 13) - 1   if d_i < 0   (early prediction)
    s_i = exp(d_i / 10) - 1    if d_i >= 0  (late prediction)
    S   = sum_i s_i
Late predictions (d > 0) are penalized more steeply because the denominator 10 is
smaller than 13. The sign convention is implemented exactly as specified and must not
be reversed.
"""

from __future__ import annotations

import numpy as np

EARLY_DENOMINATOR = 13.0
LATE_DENOMINATOR = 10.0


def _validate_pair(
    y_true: np.ndarray | list[float], y_pred: np.ndarray | list[float]
) -> tuple[np.ndarray, np.ndarray]:
    """Coerce inputs to finite, equal-length 1-D float arrays or raise ValueError."""
    true_arr = np.asarray(y_true, dtype=float).ravel()
    pred_arr = np.asarray(y_pred, dtype=float).ravel()
    if true_arr.shape != pred_arr.shape:
        raise ValueError(
            f"y_true and y_pred must have identical shapes, got {true_arr.shape} and "
            f"{pred_arr.shape}."
        )
    if true_arr.size == 0:
        raise ValueError("y_true and y_pred must contain at least one sample.")
    if not np.all(np.isfinite(true_arr)):
        raise ValueError("y_true contains non-finite values.")
    if not np.all(np.isfinite(pred_arr)):
        raise ValueError("y_pred contains non-finite values.")
    return true_arr, pred_arr


def compute_mae(y_true: np.ndarray | list[float], y_pred: np.ndarray | list[float]) -> float:
    """Mean absolute error in cycles: mean(|predicted - actual|)."""
    true_arr, pred_arr = _validate_pair(y_true, y_pred)
    return float(np.mean(np.abs(pred_arr - true_arr)))


def compute_rmse(y_true: np.ndarray | list[float], y_pred: np.ndarray | list[float]) -> float:
    """Root mean squared error in cycles: sqrt(mean((predicted - actual)^2))."""
    true_arr, pred_arr = _validate_pair(y_true, y_pred)
    return float(np.sqrt(np.mean((pred_arr - true_arr) ** 2)))


def nasa_score(
    y_true: np.ndarray | list[float],
    y_pred: np.ndarray | list[float],
    early_denominator: float = EARLY_DENOMINATOR,
    late_denominator: float = LATE_DENOMINATOR,
) -> float:
    """Total NASA/PHM08 asymmetric score (sum over samples; lower is better)."""
    if early_denominator <= 0 or late_denominator <= 0:
        raise ValueError("NASA score denominators must be positive.")
    true_arr, pred_arr = _validate_pair(y_true, y_pred)
    errors = pred_arr - true_arr
    scores = np.where(
        errors < 0,
        np.exp(-errors / early_denominator) - 1.0,
        np.exp(errors / late_denominator) - 1.0,
    )
    return float(np.sum(scores))


def mean_nasa_score(
    y_true: np.ndarray | list[float],
    y_pred: np.ndarray | list[float],
    early_denominator: float = EARLY_DENOMINATOR,
    late_denominator: float = LATE_DENOMINATOR,
) -> float:
    """Mean NASA/PHM08 score per evaluated example (total score divided by N)."""
    true_arr, pred_arr = _validate_pair(y_true, y_pred)
    return nasa_score(true_arr, pred_arr, early_denominator, late_denominator) / true_arr.size


def evaluate_regression(
    y_true: np.ndarray | list[float],
    y_pred: np.ndarray | list[float],
    early_denominator: float = EARLY_DENOMINATOR,
    late_denominator: float = LATE_DENOMINATOR,
) -> dict[str, float]:
    """Compute required metrics plus supplementary diagnostics.

    Returns a dict with keys: n_samples, mae, rmse, nasa_score, mean_nasa_score,
    median_absolute_error, error_mean, error_std, early_ratio, late_ratio,
    within_10_cycles, within_20_cycles. Error is defined as predicted - actual.
    ``early_ratio`` is the fraction with error < 0, ``late_ratio`` the fraction with
    error > 0 (exact-zero errors count in neither). ``within_*`` values are
    percentages (0-100) of predictions with |error| <= tolerance cycles.
    """
    true_arr, pred_arr = _validate_pair(y_true, y_pred)
    errors = pred_arr - true_arr
    abs_errors = np.abs(errors)
    total = nasa_score(true_arr, pred_arr, early_denominator, late_denominator)
    return {
        "n_samples": float(true_arr.size),
        "mae": float(np.mean(abs_errors)),
        "rmse": float(np.sqrt(np.mean(errors**2))),
        "nasa_score": total,
        "mean_nasa_score": total / true_arr.size,
        "median_absolute_error": float(np.median(abs_errors)),
        "error_mean": float(np.mean(errors)),
        "error_std": float(np.std(errors)),
        "early_ratio": float(np.mean(errors < 0)),
        "late_ratio": float(np.mean(errors > 0)),
        "within_10_cycles": float(100.0 * np.mean(abs_errors <= 10.0)),
        "within_20_cycles": float(100.0 * np.mean(abs_errors <= 20.0)),
    }
