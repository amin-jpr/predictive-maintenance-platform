"""Strict, reusable ingestion of original C-MAPSS text files.

The loader performs schema/finite/integer checks only. Scientific integrity
checks (sequence ordering, duplicates, catalog counts, RUL alignment) live in
validation.py. Raw files are never modified.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from predictive_maintenance.data.schema import (
    COLUMN_NAMES,
    DTYPES,
    ID_COLUMNS,
    N_COLUMNS,
    SchemaError,
    raw_paths,
)


def _parse_numeric_line(line: str, line_number: int, path: Path, expected: int) -> list[float]:
    tokens = line.split()
    if len(tokens) != expected:
        raise SchemaError(
            f"{path}:{line_number}: expected {expected} whitespace-separated fields, got {len(tokens)}"
        )
    try:
        return [float(token) for token in tokens]
    except ValueError as exc:
        raise SchemaError(f"{path}:{line_number}: non-numeric token: {exc}") from exc


def load_cmaps_table(path: Path) -> pd.DataFrame:
    """Load a 26-column train/test file with exact field counts and finite values."""
    if not path.is_file():
        raise FileNotFoundError(f"Missing C-MAPSS file: {path}")
    rows: list[list[float]] = []
    with path.open("r", encoding="ascii") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            rows.append(_parse_numeric_line(line, line_number, path, N_COLUMNS))
    if not rows:
        raise SchemaError(f"{path}: no observations found")
    frame = pd.DataFrame(rows, columns=COLUMN_NAMES)
    if not np.isfinite(frame.to_numpy(dtype=np.float64)).all():
        raise SchemaError(f"{path}: non-finite value detected")
    for column in ID_COLUMNS:
        values = frame[column].to_numpy(dtype=np.float64)
        if not np.all(values == np.floor(values)):
            raise SchemaError(f"{path}: column {column} must be integer-valued")
        if np.any(values < 1):
            raise SchemaError(f"{path}: column {column} must be positive")
        frame[column] = values.astype(np.int64)
    frame = frame.astype(DTYPES)
    return frame


def load_rul_vector(path: Path) -> np.ndarray:
    """Load one nonnegative integer RUL per test engine."""
    if not path.is_file():
        raise FileNotFoundError(f"Missing RUL file: {path}")
    values: list[int] = []
    with path.open("r", encoding="ascii") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            tokens = line.split()
            if len(tokens) != 1:
                raise SchemaError(f"{path}:{line_number}: expected exactly one RUL value")
            try:
                value = float(tokens[0])
            except ValueError as exc:
                raise SchemaError(f"{path}:{line_number}: non-numeric RUL: {exc}") from exc
            if not np.isfinite(value) or value != np.floor(value) or value < 0:
                raise SchemaError(f"{path}:{line_number}: RUL must be a nonnegative integer")
            values.append(int(value))
    if not values:
        raise SchemaError(f"{path}: empty RUL vector")
    return np.asarray(values, dtype=np.int64)


def load_train(root: Path, subset: str) -> pd.DataFrame:
    return load_cmaps_table(raw_paths(root, subset)["train"])


def load_test(root: Path, subset: str) -> pd.DataFrame:
    return load_cmaps_table(raw_paths(root, subset)["test"])


def load_rul(root: Path, subset: str) -> np.ndarray:
    return load_rul_vector(raw_paths(root, subset)["rul"])


def load_subset(root: Path, subset: str) -> dict[str, pd.DataFrame | np.ndarray]:
    return {
        "train": load_train(root, subset),
        "test": load_test(root, subset),
        "rul": load_rul(root, subset),
    }
