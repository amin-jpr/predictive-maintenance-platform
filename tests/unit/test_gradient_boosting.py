"""Unit tests for the HistGradientBoosting builder and training contract."""

from __future__ import annotations

import numpy as np
import pytest

from predictive_maintenance.models import (
    build_gradient_boosting,
    predict_model,
    train_model,
)


def _synthetic(n: int = 120, n_features: int = 6, seed: int = 11) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, n_features))
    y = 40.0 + 2.0 * X[:, 0] + rng.normal(scale=0.5, size=n)
    return X, y


def test_build_gradient_boosting_rejects_unknown_params() -> None:
    with pytest.raises(ValueError, match="Unknown HistGradientBoosting parameters"):
        build_gradient_boosting({"max_iter": 5, "bogus_param": 1})


def test_build_gradient_boosting_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="positive integer"):
        build_gradient_boosting({"max_iter": 0})
    with pytest.raises(ValueError, match="positive"):
        build_gradient_boosting({"learning_rate": -0.1})


def test_gradient_boosting_shapes_and_finite_predictions() -> None:
    X, y = _synthetic()
    model = build_gradient_boosting({"max_iter": 10, "random_state": 42})
    model.fit(X, y)
    predictions = predict_model(model, X[:8])
    assert predictions.shape == (8,)
    assert np.all(np.isfinite(predictions))


def test_gradient_boosting_reproducible_under_fixed_seed() -> None:
    X, y = _synthetic()
    params = {"max_iter": 10, "random_state": 99}
    first = build_gradient_boosting(params)
    second = build_gradient_boosting(params)
    first.fit(X, y)
    second.fit(X, y)
    assert np.allclose(predict_model(first, X), predict_model(second, X))


def test_gradient_boosting_through_train_model() -> None:
    X, y = _synthetic()
    trained = train_model(
        "hist_gradient_boosting",
        build_gradient_boosting({"max_iter": 10, "random_state": 42}),
        X[:100],
        y[:100],
        X[100:],
        y[100:],
        [f"f{i}" for i in range(X.shape[1])],
    )
    assert trained.validation_metrics["n_samples"] == 20.0
    assert trained.validation_metrics["mae"] < 5.0
