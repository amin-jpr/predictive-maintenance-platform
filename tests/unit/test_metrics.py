"""Unit tests for RUL regression metrics, including hand-calculated NASA scores."""

from __future__ import annotations

import math

import numpy as np
import pytest

from predictive_maintenance.evaluation.metrics import (
    compute_mae,
    compute_rmse,
    evaluate_regression,
    mean_nasa_score,
    nasa_score,
)


def test_mae_hand_calculated() -> None:
    y_true = np.array([10.0, 20.0, 30.0])
    y_pred = np.array([12.0, 18.0, 30.0])
    assert compute_mae(y_true, y_pred) == pytest.approx(4.0 / 3.0)


def test_rmse_hand_calculated() -> None:
    y_true = np.array([10.0, 20.0, 30.0])
    y_pred = np.array([12.0, 18.0, 30.0])
    assert compute_rmse(y_true, y_pred) == pytest.approx(math.sqrt(8.0 / 3.0))


def test_nasa_score_zero_error_is_zero() -> None:
    y_true = np.array([50.0, 0.0, 125.0])
    assert nasa_score(y_true, y_true.copy()) == 0.0
    assert mean_nasa_score(y_true, y_true.copy()) == 0.0


def test_nasa_score_negative_error_early() -> None:
    # d = pred - actual = -13 -> exp(13/13) - 1 = e - 1
    assert nasa_score(np.array([100.0]), np.array([87.0])) == pytest.approx(math.e - 1.0)


def test_nasa_score_positive_error_late() -> None:
    # d = +10 -> exp(10/10) - 1 = e - 1 (steeper penalty than early at same |d|)
    assert nasa_score(np.array([100.0]), np.array([110.0])) == pytest.approx(math.e - 1.0)
    late = nasa_score(np.array([100.0]), np.array([110.0]))
    early = nasa_score(np.array([100.0]), np.array([90.0]))
    assert late > early


def test_nasa_score_multiple_observations() -> None:
    y_true = np.array([100.0, 50.0, 0.0])
    y_pred = np.array([87.0, 60.0, 0.0])
    expected = (math.e - 1.0) + (math.e - 1.0) + 0.0
    assert nasa_score(y_true, y_pred) == pytest.approx(expected)
    assert mean_nasa_score(y_true, y_pred) == pytest.approx(expected / 3.0)


def test_evaluate_regression_keys_and_diagnostics() -> None:
    y_true = np.array([100.0, 50.0, 10.0, 0.0])
    y_pred = np.array([90.0, 55.0, 10.0, 5.0])
    result = evaluate_regression(y_true, y_pred)
    assert result["n_samples"] == 4.0
    assert result["mae"] == pytest.approx((10.0 + 5.0 + 0.0 + 5.0) / 4.0)
    assert result["median_absolute_error"] == pytest.approx(5.0)
    assert result["error_mean"] == pytest.approx((-10.0 + 5.0 + 0.0 + 5.0) / 4.0)
    assert result["early_ratio"] == pytest.approx(0.25)
    assert result["late_ratio"] == pytest.approx(0.5)
    assert result["within_10_cycles"] == pytest.approx(100.0)
    assert result["within_20_cycles"] == pytest.approx(100.0)
    assert result["nasa_score"] == pytest.approx(nasa_score(y_true, y_pred))


def test_metrics_reject_shape_mismatch() -> None:
    with pytest.raises(ValueError, match="identical shapes"):
        compute_mae(np.array([1.0, 2.0]), np.array([1.0]))


def test_metrics_reject_empty() -> None:
    with pytest.raises(ValueError, match="at least one sample"):
        compute_rmse(np.array([]), np.array([]))


def test_metrics_reject_non_finite() -> None:
    with pytest.raises(ValueError, match="non-finite"):
        nasa_score(np.array([1.0]), np.array([np.nan]))
    with pytest.raises(ValueError, match="non-finite"):
        evaluate_regression(np.array([np.inf]), np.array([1.0]))


def test_nasa_score_rejects_nonpositive_denominators() -> None:
    with pytest.raises(ValueError, match="positive"):
        nasa_score(np.array([1.0]), np.array([1.0]), early_denominator=0.0)
