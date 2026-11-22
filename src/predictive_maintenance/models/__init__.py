"""Model layer: classical machine learning baselines for RUL regression (Milestone 5)."""

from predictive_maintenance.models.base import (
    TrainedModel,
    load_model,
    predict_model,
    save_model,
    train_model,
    validate_predictions,
)
from predictive_maintenance.models.baseline import (
    CycleTrendRegressor,
    build_baseline,
    build_cycle_trend_baseline,
)
from predictive_maintenance.models.gradient_boosting import build_gradient_boosting
from predictive_maintenance.models.linear import build_linear_regression
from predictive_maintenance.models.random_forest import build_random_forest

__all__ = [
    "CycleTrendRegressor",
    "TrainedModel",
    "build_baseline",
    "build_cycle_trend_baseline",
    "build_gradient_boosting",
    "build_linear_regression",
    "build_random_forest",
    "load_model",
    "predict_model",
    "save_model",
    "train_model",
    "validate_predictions",
]
