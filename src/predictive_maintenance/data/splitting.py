"""Deterministic engine-level splitting with strict isolation."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class SplitError(ValueError):
    """Raised when an engine-level split is invalid."""


def engine_split(engine_ids: list[int] | np.ndarray, validation_fraction: float = 0.20, seed: int = 42) -> dict[str, Any]:
    ids = sorted({int(value) for value in engine_ids})
    if len(ids) < 2:
        raise SplitError("At least two engines are required for an engine-level split")
    if not 0 < validation_fraction < 1:
        raise SplitError("validation_fraction must be between 0 and 1")
    n_val = max(1, int(round(len(ids) * validation_fraction)))
    n_val = min(n_val, len(ids) - 1)
    rng = np.random.default_rng(seed)
    permutation = rng.permutation(np.asarray(ids, dtype=np.int64))
    validation = sorted(int(value) for value in permutation[:n_val])
    train_fit = sorted(int(value) for value in permutation[n_val:])
    assert_split_isolation(train_fit, validation, ids)
    return {
        "method": "engine_shuffle",
        "seed": seed,
        "validation_fraction": validation_fraction,
        "train_fit": train_fit,
        "validation": validation,
        "n_train_fit": len(train_fit),
        "n_validation": len(validation),
    }


def assert_split_isolation(train_fit: list[int], validation: list[int], all_train_ids: list[int] | None = None) -> None:
    fit_set = set(train_fit)
    val_set = set(validation)
    if fit_set & val_set:
        raise SplitError(f"Engine leakage: intersection {sorted(fit_set & val_set)}")
    if not fit_set or not val_set:
        raise SplitError("Both fit and validation splits must be nonempty")
    if all_train_ids is not None and fit_set | val_set != set(all_train_ids):
        raise SplitError("Split union does not equal official training engine IDs")


def assign_split(train_labeled: pd.DataFrame, split: dict[str, Any]) -> pd.DataFrame:
    fit_ids = set(split["train_fit"])
    val_ids = set(split["validation"])
    frame = train_labeled.copy()
    conditions = [frame["engine_id"].isin(fit_ids), frame["engine_id"].isin(val_ids)]
    frame["split"] = np.select(conditions, ["train_fit", "validation"], default="unknown")
    if (frame["split"] == "unknown").any():
        raise SplitError("Some training engines were not assigned to a split")
    return frame
