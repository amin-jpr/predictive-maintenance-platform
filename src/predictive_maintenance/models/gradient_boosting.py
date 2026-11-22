"""HistGradientBoosting regressor builder (config-driven, CPU-first)."""

from __future__ import annotations

from typing import Any

from sklearn.ensemble import HistGradientBoostingRegressor

_ALLOWED_KEYS = {
    "learning_rate",
    "max_iter",
    "max_leaf_nodes",
    "max_depth",
    "min_samples_leaf",
    "l2_regularization",
    "random_state",
    "early_stopping",
}


def build_gradient_boosting(params: dict[str, Any]) -> HistGradientBoostingRegressor:
    """Build a HistGradientBoostingRegressor from a validated parameter mapping.

    Unknown keys raise ValueError. ``max_iter`` must be a positive integer and
    ``learning_rate`` must be positive.
    """
    unknown = sorted(set(params) - _ALLOWED_KEYS)
    if unknown:
        raise ValueError(f"Unknown HistGradientBoosting parameters: {unknown}")
    max_iter = params.get("max_iter", 300)
    if not isinstance(max_iter, int) or max_iter <= 0:
        raise ValueError(f"max_iter must be a positive integer, got {max_iter!r}.")
    learning_rate = float(params.get("learning_rate", 0.06))
    if learning_rate <= 0:
        raise ValueError(f"learning_rate must be positive, got {learning_rate!r}.")
    return HistGradientBoostingRegressor(
        learning_rate=learning_rate,
        max_iter=max_iter,
        max_leaf_nodes=params.get("max_leaf_nodes", 31),
        max_depth=params.get("max_depth"),
        min_samples_leaf=params.get("min_samples_leaf", 20),
        l2_regularization=params.get("l2_regularization", 0.0),
        random_state=params.get("random_state", 42),
        early_stopping=params.get("early_stopping", False),
    )
