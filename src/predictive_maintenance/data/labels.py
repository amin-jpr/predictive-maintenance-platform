"""Mathematically correct C-MAPSS RUL label construction and independent verification."""

from __future__ import annotations

import numpy as np
import pandas as pd


class LabelError(ValueError):
    """Raised when RUL labels violate benchmark semantics."""


def add_train_labels(train: pd.DataFrame, cap: int = 125) -> pd.DataFrame:
    if cap < 0:
        raise LabelError("RUL cap must be nonnegative")
    frame = train.copy()
    failure_cycle = frame.groupby("engine_id")["cycle"].transform("max").astype(np.int64)
    frame["failure_cycle"] = failure_cycle
    frame["rul_raw"] = (failure_cycle - frame["cycle"]).astype(np.int64)
    frame["rul"] = np.minimum(frame["rul_raw"].to_numpy(), cap).astype(np.int64)
    verify_train_labels(frame, cap)
    return frame


def add_test_labels(test: pd.DataFrame, terminal_rul: np.ndarray, cap: int = 125) -> pd.DataFrame:
    if cap < 0:
        raise LabelError("RUL cap must be nonnegative")
    frame = test.copy()
    engine_ids = sorted(int(value) for value in frame["engine_id"].unique())
    terminal = np.asarray(terminal_rul, dtype=np.int64)
    if len(terminal) != len(engine_ids):
        raise LabelError(f"RUL vector length {len(terminal)} != test engines {len(engine_ids)}")
    if np.any(terminal < 0):
        raise LabelError("Terminal test RUL must be nonnegative")
    terminal_by_engine = dict(zip(engine_ids, terminal.tolist(), strict=True))
    last_cycle = frame.groupby("engine_id")["cycle"].transform("max").astype(np.int64)
    terminal_series = frame["engine_id"].map(terminal_by_engine).astype(np.int64)
    frame["inferred_failure_cycle"] = (last_cycle + terminal_series).astype(np.int64)
    frame["rul_raw"] = (frame["inferred_failure_cycle"] - frame["cycle"]).astype(np.int64)
    frame["rul"] = np.minimum(frame["rul_raw"].to_numpy(), cap).astype(np.int64)
    verify_test_labels(frame, terminal_by_engine, cap)
    return frame


def verify_train_labels(frame: pd.DataFrame, cap: int = 125) -> None:
    """Independent integer-loop verification (does not reuse vectorized construction)."""
    for engine_id, group in frame.groupby("engine_id", sort=True):
        cycles = group["cycle"].to_numpy(dtype=np.int64)
        failure = int(cycles.max())
        raw = group["rul_raw"].to_numpy(dtype=np.int64)
        clipped = group["rul"].to_numpy(dtype=np.int64)
        expected_raw = np.asarray([failure - int(t) for t in cycles], dtype=np.int64)
        expected_clipped = np.minimum(expected_raw, cap)
        if not np.array_equal(raw, expected_raw) or not np.array_equal(clipped, expected_clipped):
            raise LabelError(f"Training RUL mismatch for engine {engine_id}")
        if int(clipped[-1]) != 0:
            raise LabelError(f"Training terminal RUL must be zero for engine {engine_id}")
        if "failure_cycle" in group and not np.all(group["failure_cycle"].to_numpy() == failure):
            raise LabelError(f"Training failure_cycle mismatch for engine {engine_id}")


def verify_test_labels(frame: pd.DataFrame, terminal_by_engine: dict[int, int], cap: int = 125) -> None:
    for engine_id, group in frame.groupby("engine_id", sort=True):
        cycles = group["cycle"].to_numpy(dtype=np.int64)
        last = int(cycles.max())
        terminal = int(terminal_by_engine[int(str(engine_id))])
        failure = last + terminal
        expected_raw = np.asarray([failure - int(t) for t in cycles], dtype=np.int64)
        expected_clipped = np.minimum(expected_raw, cap)
        if not np.array_equal(group["rul_raw"].to_numpy(dtype=np.int64), expected_raw):
            raise LabelError(f"Test raw RUL mismatch for engine {engine_id}")
        if not np.array_equal(group["rul"].to_numpy(dtype=np.int64), expected_clipped):
            raise LabelError(f"Test clipped RUL mismatch for engine {engine_id}")
        if int(group["rul_raw"].to_numpy()[-1]) != terminal:
            raise LabelError(f"Test terminal raw RUL must equal ground truth for engine {engine_id}")
        if "inferred_failure_cycle" in group and not np.all(group["inferred_failure_cycle"].to_numpy() == failure):
            raise LabelError(f"Test inferred_failure_cycle mismatch for engine {engine_id}")
