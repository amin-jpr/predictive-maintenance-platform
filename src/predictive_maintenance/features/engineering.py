"""Causal, engine-local feature engineering (no future observations)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class FeatureError(ValueError):
    """Raised when feature configuration or causality is violated."""


def _slope(values: np.ndarray) -> float:
    if len(values) < 2:
        return 0.0
    x = np.arange(len(values), dtype=np.float64)
    x_centered = x - x.mean()
    denominator = float(np.dot(x_centered, x_centered))
    if denominator == 0:
        return 0.0
    return float(np.dot(x_centered, values - values.mean()) / denominator)


def _rolling_feature(
    frame: pd.DataFrame, column: str, window: int, statistic: str, ddof: int
) -> pd.Series:
    grouped = frame.groupby("engine_id", sort=False)[column]
    roller = grouped.rolling(window=window, min_periods=1)
    if statistic == "mean":
        result = roller.mean()
    elif statistic == "std":
        result = roller.std(ddof=ddof).fillna(0.0)
    elif statistic == "min":
        result = roller.min()
    elif statistic == "max":
        result = roller.max()
    elif statistic == "slope":
        result = roller.apply(_slope, raw=True)
    else:
        raise FeatureError(f"Unknown rolling statistic: {statistic}")
    return result.droplevel(0).sort_index()


def feature_names_from_config(config: dict[str, Any]) -> list[str]:
    settings = list(config["selected_settings"])
    sensors = list(config["selected_sensors"])
    names = settings + sensors
    rolling = config.get("rolling", {})
    for window in rolling.get("windows", []):
        for statistic in rolling.get("statistics", []):
            names.extend(f"{sensor}_roll_{statistic}_{window}" for sensor in sensors)
    for order in config.get("differences", {}).get("orders", []):
        names.extend(f"{sensor}_diff_{order}" for sensor in sensors)
    optional = config.get("optional", {})
    if optional.get("rolling_min_max", False):
        for window in optional.get("min_max_windows", []):
            names.extend(f"{sensor}_roll_min_{window}" for sensor in sensors)
            names.extend(f"{sensor}_roll_max_{window}" for sensor in sensors)
    if optional.get("trend_slope", False):
        for window in optional.get("trend_windows", []):
            names.extend(f"{sensor}_trend_{window}" for sensor in sensors)
    return names


def build_feature_frame(
    cycle_data: pd.DataFrame, config: dict[str, Any]
) -> tuple[pd.DataFrame, list[str]]:
    settings = list(config["selected_settings"])
    sensors = list(config["selected_sensors"])
    required = ["engine_id", "cycle", *settings, *sensors]
    missing = [column for column in required if column not in cycle_data.columns]
    if missing:
        raise FeatureError(f"Missing feature input columns: {missing}")
    frame = cycle_data[required].sort_values(["engine_id", "cycle"]).reset_index(drop=True).copy()
    if not np.isfinite(frame[settings + sensors].to_numpy(dtype=np.float64)).all():
        raise FeatureError("Feature inputs contain non-finite values")

    rolling = config.get("rolling", {})
    ddof = int(rolling.get("std_ddof", 1))
    for window in rolling.get("windows", []):
        if int(window) < 1:
            raise FeatureError("Rolling window must be >= 1")
        for statistic in rolling.get("statistics", []):
            for sensor in sensors:
                frame[f"{sensor}_roll_{statistic}_{window}"] = _rolling_feature(
                    frame, sensor, int(window), statistic, ddof
                )

    for order in config.get("differences", {}).get("orders", []):
        if int(order) < 1:
            raise FeatureError("Difference order must be >= 1")
        for sensor in sensors:
            frame[f"{sensor}_diff_{order}"] = (
                frame.groupby("engine_id", sort=False)[sensor].diff(int(order)).fillna(0.0)
            )

    optional = config.get("optional", {})
    if optional.get("rolling_min_max", False):
        for window in optional.get("min_max_windows", []):
            for sensor in sensors:
                frame[f"{sensor}_roll_min_{window}"] = _rolling_feature(
                    frame, sensor, int(window), "min", ddof
                )
                frame[f"{sensor}_roll_max_{window}"] = _rolling_feature(
                    frame, sensor, int(window), "max", ddof
                )
    if optional.get("trend_slope", False):
        for window in optional.get("trend_windows", []):
            for sensor in sensors:
                frame[f"{sensor}_trend_{window}"] = _rolling_feature(
                    frame, sensor, int(window), "slope", ddof
                )

    feature_names = feature_names_from_config(config)
    expected = config.get("feature_count_expected")
    if expected is not None and len(feature_names) != int(expected):
        raise FeatureError(f"Feature count {len(feature_names)} != expected {expected}")
    feature_matrix = frame[feature_names].to_numpy(dtype=np.float64)
    if not np.isfinite(feature_matrix).all():
        raise FeatureError("Engineered features contain non-finite values after causal warmup")
    identifiers = ["engine_id", "cycle"]
    if "split" in cycle_data.columns:
        frame["split"] = (
            cycle_data.sort_values(["engine_id", "cycle"])
            .reset_index(drop=True)["split"]
            .to_numpy()
        )
        identifiers.append("split")
    return frame[identifiers + feature_names], feature_names
