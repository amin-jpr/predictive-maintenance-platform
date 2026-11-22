"""Unit tests for model serialization round-trips (joblib)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from predictive_maintenance.models import (
    build_baseline,
    build_random_forest,
    load_model,
    predict_model,
    save_model,
)


def test_serialization_roundtrip_reproduces_predictions(tmp_path: Path) -> None:
    rng = np.random.default_rng(3)
    X = rng.normal(size=(40, 4))
    y = 20.0 + X[:, 0]
    model = build_random_forest({"n_estimators": 3, "random_state": 42, "n_jobs": 1})
    model.fit(X, y)
    path = save_model(model, tmp_path / "rf" / "model.joblib")
    assert path.is_file()
    loaded = load_model(path)
    assert np.allclose(predict_model(loaded, X), predict_model(model, X))


def test_serialization_roundtrip_baseline(tmp_path: Path) -> None:
    model = build_baseline()
    model.fit(np.zeros((5, 2)), np.array([1.0, 2.0, 3.0, 4.0, 5.0]))
    path = save_model(model, tmp_path / "baseline.joblib")
    loaded = load_model(path)
    assert np.allclose(predict_model(loaded, np.zeros((2, 2))), np.array([3.0, 3.0]))


def test_load_model_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="not found"):
        load_model(tmp_path / "does_not_exist.joblib")
