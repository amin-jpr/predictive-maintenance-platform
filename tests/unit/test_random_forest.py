"""Unit tests for the Random Forest builder and training contract."""

from __future__ import annotations

import numpy as np
import pytest

from predictive_maintenance.models import build_random_forest, predict_model, train_model


def _synthetic(n: int = 120, n_features: int = 6, seed: int = 7) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, n_features))
    y = 50.0 + 3.0 * X[:, 0] - 2.0 * X[:, 1] + rng.normal(scale=0.5, size=n)
    return X, y


def test_build_random_forest_rejects_unknown_params() -> None:
    with pytest.raises(ValueError, match="Unknown RandomForest parameters"):
        build_random_forest({"n_estimators": 5, "bogus_param": 1})


def test_build_random_forest_rejects_nonpositive_trees() -> None:
    with pytest.raises(ValueError, match="positive integer"):
        build_random_forest({"n_estimators": 0})


def test_random_forest_shapes_and_finite_predictions() -> None:
    X, y = _synthetic()
    model = build_random_forest({"n_estimators": 5, "random_state": 42, "n_jobs": 1})
    model.fit(X, y)
    predictions = predict_model(model, X[:10])
    assert predictions.shape == (10,)
    assert np.all(np.isfinite(predictions))


def test_random_forest_reproducible_under_fixed_seed() -> None:
    X, y = _synthetic()
    params = {"n_estimators": 5, "random_state": 123, "n_jobs": 1}
    first = build_random_forest(params)
    second = build_random_forest(params)
    first.fit(X, y)
    second.fit(X, y)
    assert np.allclose(predict_model(first, X), predict_model(second, X))


def test_random_forest_through_train_model() -> None:
    X, y = _synthetic()
    trained = train_model(
        "random_forest",
        build_random_forest({"n_estimators": 5, "random_state": 42, "n_jobs": 1}),
        X[:100],
        y[:100],
        X[100:],
        y[100:],
        [f"f{i}" for i in range(X.shape[1])],
    )
    assert trained.validation_metrics["n_samples"] == 20.0
    assert trained.validation_metrics["mae"] < 5.0
    assert hasattr(trained.estimator, "feature_importances_")
