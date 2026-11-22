"""Shared model plumbing: training, prediction, validation, and serialization.

Every Milestone 5 model is trained through :func:`train_model` so that training time,
train/validation metrics, and prediction validation are recorded identically. Models are
serialized with joblib (scikit-learn compatible) and must reload in a fresh process.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from predictive_maintenance.evaluation.metrics import evaluate_regression


@dataclass
class TrainedModel:
    """Result of fitting one regressor on the Milestone 4 training split."""

    name: str
    estimator: Any
    training_time_seconds: float
    train_metrics: dict[str, float]
    validation_metrics: dict[str, float]
    feature_names: list[str]
    config: dict[str, Any] = field(default_factory=dict)


def validate_predictions(predictions: np.ndarray, expected_n: int | None = None) -> None:
    """Raise ValueError unless predictions are non-empty, finite, and correctly sized."""
    arr = np.asarray(predictions, dtype=float).ravel()
    if arr.size == 0:
        raise ValueError("Predictions must contain at least one value.")
    if expected_n is not None and arr.shape[0] != expected_n:
        raise ValueError(
            f"Expected {expected_n} predictions (one per input row), got {arr.shape[0]}."
        )
    if not np.all(np.isfinite(arr)):
        raise ValueError("Predictions contain non-finite values (NaN or infinite).")


def predict_model(estimator: Any, X: np.ndarray) -> np.ndarray:
    """Predict with a fitted estimator and validate the output contract."""
    predictions = np.asarray(estimator.predict(X), dtype=float).ravel()
    validate_predictions(predictions, expected_n=len(X))
    return predictions


def train_model(
    name: str,
    estimator: Any,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_validation: np.ndarray,
    y_validation: np.ndarray,
    feature_names: list[str],
    config: dict[str, Any] | None = None,
) -> TrainedModel:
    """Fit an estimator on the training split and evaluate on train and validation.

    The estimator is fitted exclusively on ``X_train``/``y_train``. Validation data are
    used only for scoring. Training time is measured with a monotonic clock.
    """
    if len(X_train) == 0 or len(X_validation) == 0:
        raise ValueError("Training and validation inputs must be non-empty.")
    if len(X_train) != len(y_train) or len(X_validation) != len(y_validation):
        raise ValueError("Feature and target row counts must match within each split.")
    start = time.perf_counter()
    estimator.fit(X_train, y_train)
    elapsed = time.perf_counter() - start
    train_pred = predict_model(estimator, X_train)
    validation_pred = predict_model(estimator, X_validation)
    return TrainedModel(
        name=name,
        estimator=estimator,
        training_time_seconds=float(elapsed),
        train_metrics=evaluate_regression(y_train, train_pred),
        validation_metrics=evaluate_regression(y_validation, validation_pred),
        feature_names=list(feature_names),
        config=dict(config or {}),
    )


def save_model(estimator: Any, path: Path, compress: int = 3) -> Path:
    """Serialize a fitted estimator with joblib, creating parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(estimator, path, compress=compress)
    return path


def load_model(path: Path) -> Any:
    """Load a joblib-serialized estimator previously written by :func:`save_model`."""
    if not path.is_file():
        raise FileNotFoundError(f"Model artifact not found: {path}")
    return joblib.load(path)
