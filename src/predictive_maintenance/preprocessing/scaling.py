"""Training-only StandardScaler fitting, JSON persistence, and transform."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sklearn
from sklearn.preprocessing import StandardScaler

from predictive_maintenance.io import atomic_write_json, read_json, utc_now_iso


class ScalingError(ValueError):
    """Raised when scaling boundaries or feature contracts are violated."""


def fit_scaler(
    features: pd.DataFrame,
    feature_names: list[str],
    fit_engine_ids: list[int],
    fit_split: str = "train_fit",
    metadata: dict[str, Any] | None = None,
) -> tuple[StandardScaler, dict[str, Any]]:
    if "split" in features.columns:
        selected = features[
            features["engine_id"].isin(fit_engine_ids) & (features["split"] == fit_split)
        ]
    else:
        selected = features[features["engine_id"].isin(fit_engine_ids)]
    if selected.empty:
        raise ScalingError("No rows available for scaler fitting")
    if "split" in selected.columns and not (selected["split"] == fit_split).all():
        raise ScalingError("Scaler fit data contains a non-fit split")
    matrix = selected[feature_names].to_numpy(dtype=np.float64)
    if not np.isfinite(matrix).all():
        raise ScalingError("Scaler fit matrix contains non-finite values")
    scaler = StandardScaler(with_mean=True, with_std=True)
    scaler.fit(selected[feature_names])
    state = scaler_state(scaler, feature_names, fit_engine_ids, fit_split, metadata)
    return scaler, state


def scaler_state(
    scaler: StandardScaler,
    feature_names: list[str],
    fit_engine_ids: list[int],
    fit_split: str = "train_fit",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "generated_at_utc": utc_now_iso(),
        "method": "StandardScaler",
        "sklearn_version": sklearn.__version__,
        "fit_split": fit_split,
        "fit_engine_ids": sorted(int(value) for value in fit_engine_ids),
        "n_fit_engines": len(fit_engine_ids),
        "n_samples_seen": int(scaler.n_samples_seen_),
        "n_features_in": int(scaler.n_features_in_),
        "feature_names": list(feature_names),
        "with_mean": True,
        "with_std": True,
        "mean": scaler.mean_.tolist(),
        "scale": scaler.scale_.tolist(),
        "var": scaler.var_.tolist(),
        "metadata": metadata or {},
    }


def save_scaler_state(path: Path, state: dict[str, Any]) -> Path:
    return atomic_write_json(path, state)


def load_scaler_state(path: Path) -> tuple[StandardScaler, dict[str, Any]]:
    state = read_json(path)
    scaler = StandardScaler(with_mean=state["with_mean"], with_std=state["with_std"])
    scaler.mean_ = np.asarray(state["mean"], dtype=np.float64)
    scaler.scale_ = np.asarray(state["scale"], dtype=np.float64)
    scaler.var_ = np.asarray(state["var"], dtype=np.float64)
    scaler.n_features_in_ = int(state["n_features_in"])
    scaler.n_samples_seen_ = int(state["n_samples_seen"])
    scaler.feature_names_in_ = np.asarray(state["feature_names"], dtype=object)
    return scaler, state


def transform_features(
    features: pd.DataFrame, scaler: StandardScaler, feature_names: list[str]
) -> pd.DataFrame:
    expected = list(getattr(scaler, "feature_names_in_", feature_names))
    if expected != feature_names:
        raise ScalingError("Feature order does not match fitted scaler")
    matrix = features[feature_names].to_numpy(dtype=np.float64)
    if not np.isfinite(matrix).all():
        raise ScalingError("Transform matrix contains non-finite values")
    scaled = scaler.transform(features[feature_names])
    result = features[["engine_id", "cycle"]].copy()
    if "split" in features.columns:
        result["split"] = features["split"].to_numpy()
    scaled_frame = pd.DataFrame(scaled, columns=feature_names, index=features.index)
    return pd.concat([result, scaled_frame], axis=1)
