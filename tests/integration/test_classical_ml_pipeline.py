"""Integration tests for the Milestone 5 classical ML pipeline.

The synthetic test exercises the full train -> evaluate -> serialize -> reload flow on
small deterministic data. The real-data test (marked ``data_required``) loads the actual
Milestone 4 FD001 products and trains small models to prove the production path works.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from predictive_maintenance.config import find_project_root
from predictive_maintenance.evaluation.metrics import evaluate_regression
from predictive_maintenance.models import (
    build_baseline,
    build_gradient_boosting,
    build_random_forest,
    load_model,
    predict_model,
    save_model,
    train_model,
)
from predictive_maintenance.models.dataset import load_milestone4_dataset

pytestmark = pytest.mark.integration


def test_synthetic_pipeline_end_to_end(tmp_path: Path) -> None:
    rng = np.random.default_rng(21)
    X = rng.normal(size=(200, 8))
    y = 60.0 + 4.0 * X[:, 0] - 3.0 * X[:, 2] + rng.normal(scale=1.0, size=200)
    feature_names = [f"f{i}" for i in range(8)]
    builders = {
        "median_baseline": build_baseline(),
        "random_forest": build_random_forest({"n_estimators": 5, "random_state": 42, "n_jobs": 1}),
        "hist_gradient_boosting": build_gradient_boosting({"max_iter": 10, "random_state": 42}),
    }
    for name, estimator in builders.items():
        trained = train_model(name, estimator, X[:150], y[:150], X[150:], y[150:], feature_names)
        assert trained.validation_metrics["n_samples"] == 50.0
        path = save_model(trained.estimator, tmp_path / name / "model.joblib")
        reloaded = load_model(path)
        predictions = predict_model(reloaded, X[150:])
        metrics = evaluate_regression(y[150:], predictions)
        assert metrics["mae"] == pytest.approx(trained.validation_metrics["mae"])
        assert np.all(np.isfinite(predictions))


@pytest.mark.data_required
def test_real_fd001_milestone4_inputs_and_small_models() -> None:
    root = find_project_root()
    dataset = load_milestone4_dataset(root)
    assert dataset.X_train.shape == (16779, 92)
    assert dataset.X_validation.shape == (3852, 92)
    assert len(dataset.feature_names) == 92
    assert len(dataset.train_engines) == 80
    assert len(dataset.validation_engines) == 20
    assert not (set(dataset.train_engines) & set(dataset.validation_engines))
    assert "rul" not in dataset.feature_names
    assert dataset.metadata["official_test_used"] is False

    small_rf = build_random_forest({"n_estimators": 3, "random_state": 42, "n_jobs": 1})
    trained_rf = train_model(
        "random_forest",
        small_rf,
        dataset.X_train,
        dataset.y_train,
        dataset.X_validation,
        dataset.y_validation,
        dataset.feature_names,
    )
    numeric_keys = [
        "mae",
        "rmse",
        "nasa_score",
        "mean_nasa_score",
        "median_absolute_error",
        "error_mean",
        "error_std",
    ]
    assert np.all(np.isfinite([trained_rf.validation_metrics[key] for key in numeric_keys]))
    small_hgb = build_gradient_boosting({"max_iter": 5, "random_state": 42})
    trained_hgb = train_model(
        "hist_gradient_boosting",
        small_hgb,
        dataset.X_train,
        dataset.y_train,
        dataset.X_validation,
        dataset.y_validation,
        dataset.feature_names,
    )
    assert trained_hgb.validation_metrics["mae"] > 0.0
