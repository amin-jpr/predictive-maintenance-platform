"""Random Forest regressor builder (config-driven, CPU-first)."""

from __future__ import annotations

from typing import Any

from sklearn.ensemble import RandomForestRegressor

_ALLOWED_KEYS = {
    "n_estimators",
    "max_depth",
    "min_samples_split",
    "min_samples_leaf",
    "max_features",
    "bootstrap",
    "random_state",
    "n_jobs",
}


def build_random_forest(params: dict[str, Any]) -> RandomForestRegressor:
    """Build a RandomForestRegressor from a validated parameter mapping.

    Unknown keys raise ValueError so configuration typos fail loudly instead of being
    silently ignored. ``n_estimators`` must be a positive integer.
    """
    unknown = sorted(set(params) - _ALLOWED_KEYS)
    if unknown:
        raise ValueError(f"Unknown RandomForest parameters: {unknown}")
    n_estimators = params.get("n_estimators", 100)
    if not isinstance(n_estimators, int) or n_estimators <= 0:
        raise ValueError(f"n_estimators must be a positive integer, got {n_estimators!r}.")
    return RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=params.get("max_depth"),
        min_samples_split=params.get("min_samples_split", 2),
        min_samples_leaf=params.get("min_samples_leaf", 2),
        max_features=params.get("max_features", 0.5),
        bootstrap=params.get("bootstrap", True),
        random_state=params.get("random_state", 42),
        n_jobs=params.get("n_jobs", -1),
    )
