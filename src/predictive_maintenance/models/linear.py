"""Optional interpretable Linear Regression baseline (high-bias reference)."""

from __future__ import annotations

from typing import Any

from sklearn.linear_model import LinearRegression

_ALLOWED_KEYS = {"fit_intercept"}


def build_linear_regression(params: dict[str, Any]) -> LinearRegression:
    """Build a LinearRegression from a validated parameter mapping."""
    unknown = sorted(set(params) - _ALLOWED_KEYS)
    if unknown:
        raise ValueError(f"Unknown LinearRegression parameters: {unknown}")
    return LinearRegression(fit_intercept=params.get("fit_intercept", True))
