"""Unit tests for the constant-median and cycle-trend baselines."""

from __future__ import annotations

import numpy as np
import pytest

from predictive_maintenance.models import (
    build_baseline,
    build_cycle_trend_baseline,
    predict_model,
    train_model,
)


def test_median_baseline_returns_training_median() -> None:
    X_train = np.zeros((5, 3))
    y_train = np.array([10.0, 20.0, 30.0, 40.0, 100.0])
    model = build_baseline()
    model.fit(X_train, y_train)
    predictions = predict_model(model, np.zeros((4, 3)))
    assert predictions.shape == (4,)
    assert np.allclose(predictions, 30.0)


def test_median_baseline_rejects_unknown_strategy() -> None:
    with pytest.raises(ValueError, match="Unsupported baseline strategy"):
        build_baseline("mean")


def test_cycle_trend_recovers_linear_relation() -> None:
    cycles = np.arange(1, 51, dtype=float).reshape(-1, 1)
    y = 120.0 - 0.8 * cycles.ravel()
    model = build_cycle_trend_baseline()
    model.fit(cycles, y)
    predictions = predict_model(model, cycles)
    assert np.allclose(predictions, y, atol=1e-8)
    assert model.slope_ == pytest.approx(-0.8)
    assert model.intercept_ == pytest.approx(120.0)


def test_cycle_trend_clips_negative_predictions() -> None:
    cycles = np.arange(1, 11, dtype=float).reshape(-1, 1)
    y = 10.0 - 2.0 * cycles.ravel()
    model = build_cycle_trend_baseline()
    model.fit(cycles, y)
    assert np.all(predict_model(model, cycles) >= 0.0)


def test_cycle_trend_rejects_multi_column_input() -> None:
    model = build_cycle_trend_baseline()
    with pytest.raises(ValueError, match="single-column"):
        model.fit(np.zeros((5, 2)), np.zeros(5))


def test_cycle_trend_predict_before_fit_raises() -> None:
    model = build_cycle_trend_baseline()
    with pytest.raises(ValueError, match="must be fitted"):
        model.predict(np.zeros((3, 1)))


def test_baselines_through_train_model() -> None:
    X_train = np.zeros((6, 2))
    y_train = np.array([5.0, 15.0, 25.0, 35.0, 45.0, 55.0])
    X_val = np.zeros((3, 2))
    y_val = np.array([10.0, 20.0, 30.0])
    trained = train_model(
        "median_baseline", build_baseline(), X_train, y_train, X_val, y_val, ["f1", "f2"]
    )
    assert trained.validation_metrics["mae"] == pytest.approx((20.0 + 10.0 + 0.0) / 3.0)
    assert trained.training_time_seconds >= 0.0
