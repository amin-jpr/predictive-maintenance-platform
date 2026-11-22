"""Load the approved Milestone 4 inputs for classical ML training.

Milestone 5 consumes exactly one feature definition: the 92 causal cycle-level features
in ``data/processed/scaled/`` (StandardScaler fitted on train_fit engines only during
Milestone 4), joined row-for-row with the capped RUL target in
``data/processed/labels/``. The official NASA test split is never read here.

Prediction unit: one engine at one observation cycle. Identifiers (engine_id, cycle,
split) and the target are never part of the feature matrix.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from predictive_maintenance.config import load_config

IDENTIFIER_COLUMNS = ("engine_id", "cycle", "split")
KEY_COLUMNS = ("engine_id", "cycle")


@dataclass
class Milestone4Dataset:
    """Train/validation matrices, targets, and provenance for Milestone 5."""

    X_train: np.ndarray
    y_train: np.ndarray
    X_validation: np.ndarray
    y_validation: np.ndarray
    feature_names: list[str]
    train_engines: list[int]
    validation_engines: list[int]
    train_cycles: np.ndarray
    validation_cycles: np.ndarray
    validation_keys: pd.DataFrame
    metadata: dict[str, Any]


def _load_split(
    root: Path, features_dir: Path, labels_dir: Path, split: str, target_column: str
) -> tuple[pd.DataFrame, pd.DataFrame]:
    features_path = features_dir / f"{split}.parquet"
    labels_path = labels_dir / f"{split}.csv"
    if not features_path.is_file():
        raise FileNotFoundError(
            f"Missing Milestone 4 features for split '{split}': {features_path}. "
            "Run scripts/run_preprocessing.py and scripts/build_features.py first."
        )
    if not labels_path.is_file():
        raise FileNotFoundError(f"Missing Milestone 4 labels for split '{split}': {labels_path}")
    features = pd.read_parquet(features_path)
    labels = pd.read_csv(labels_path)
    if target_column not in labels.columns:
        raise ValueError(f"Target column '{target_column}' missing from {labels_path}.")
    if len(features) != len(labels):
        raise ValueError(
            f"Row count mismatch for split '{split}': {len(features)} features vs "
            f"{len(labels)} labels."
        )
    if not (features[list(KEY_COLUMNS)].to_numpy() == labels[list(KEY_COLUMNS)].to_numpy()).all():
        raise ValueError(f"Feature/label key misalignment in split '{split}'.")
    return features, labels


def load_milestone4_dataset(root: Path) -> Milestone4Dataset:
    """Load and validate the Milestone 4 train_fit/validation inputs.

    Raises ValueError on any contract violation: feature-order drift, engine overlap
    between splits, target leakage into features, or non-finite feature values.
    """
    experiment = load_config("model_experiment", root)
    dataset_cfg = experiment["dataset"]
    target_column = str(experiment["target"]["column"])
    features_dir = root / str(dataset_cfg["features_dir"])
    labels_dir = root / str(dataset_cfg["labels_dir"])
    train_split = str(dataset_cfg["train_split"])
    validation_split = str(dataset_cfg["validation_split"])

    feature_names_path = root / str(dataset_cfg["feature_names_file"])
    with feature_names_path.open("r", encoding="utf-8") as handle:
        feature_names = list(json.load(handle)["feature_names"])

    train_features, train_labels = _load_split(
        root, features_dir, labels_dir, train_split, target_column
    )
    val_features, val_labels = _load_split(
        root, features_dir, labels_dir, validation_split, target_column
    )

    for split, frame in ((train_split, train_features), (validation_split, val_features)):
        present = [c for c in frame.columns if c not in IDENTIFIER_COLUMNS]
        if present != feature_names:
            raise ValueError(
                f"Feature order drift in split '{split}': expected the 92 features from "
                f"{feature_names_path.name} in recorded order."
            )
    if target_column in feature_names:
        raise ValueError(f"Target leakage: '{target_column}' appears in the feature list.")
    for name in IDENTIFIER_COLUMNS:
        if name in feature_names:
            raise ValueError(f"Identifier '{name}' must not be a predictive feature.")

    train_engines = sorted(int(e) for e in train_features["engine_id"].unique())
    validation_engines = sorted(int(e) for e in val_features["engine_id"].unique())
    overlap = sorted(set(train_engines) & set(validation_engines))
    if overlap:
        raise ValueError(f"Engine overlap between train and validation splits: {overlap}")

    X_train = train_features[feature_names].to_numpy(dtype=float)
    X_validation = val_features[feature_names].to_numpy(dtype=float)
    for label, matrix in ((train_split, X_train), (validation_split, X_validation)):
        if not np.all(np.isfinite(matrix)):
            raise ValueError(f"Non-finite feature values in split '{label}'.")

    split_path = root / str(dataset_cfg["split_file"])
    with split_path.open("r", encoding="utf-8") as handle:
        split_record = json.load(handle)

    metadata = {
        "subset": experiment.get("subset", "FD001"),
        "feature_set": experiment["feature_set"]["id"],
        "target_column": target_column,
        "target_cap": experiment["target"]["cap"],
        "train_split": train_split,
        "validation_split": validation_split,
        "n_train": int(len(X_train)),
        "n_validation": int(len(X_validation)),
        "n_features": len(feature_names),
        "train_engines": train_engines,
        "validation_engines": validation_engines,
        "split_record": split_record,
        "official_test_used": False,
    }
    return Milestone4Dataset(
        X_train=X_train,
        y_train=train_labels[target_column].to_numpy(dtype=float),
        X_validation=X_validation,
        y_validation=val_labels[target_column].to_numpy(dtype=float),
        feature_names=feature_names,
        train_engines=train_engines,
        validation_engines=validation_engines,
        train_cycles=train_features["cycle"].to_numpy(dtype=int),
        validation_cycles=val_features["cycle"].to_numpy(dtype=int),
        validation_keys=val_features[list(KEY_COLUMNS)].copy(),
        metadata=metadata,
    )
