"""Exact C-MAPSS column schema and subset catalog."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ID_COLUMNS = ["engine_id", "cycle"]
SETTING_COLUMNS = ["setting_1", "setting_2", "setting_3"]
SENSOR_COLUMNS = [f"s_{i}" for i in range(1, 22)]
COLUMN_NAMES = ID_COLUMNS + SETTING_COLUMNS + SENSOR_COLUMNS
MEASUREMENT_COLUMNS = SETTING_COLUMNS + SENSOR_COLUMNS
N_COLUMNS = len(COLUMN_NAMES)

DTYPES = {
    "engine_id": "int64",
    "cycle": "int64",
    **{name: "float64" for name in MEASUREMENT_COLUMNS},
}


@dataclass(frozen=True)
class SubsetInfo:
    name: str
    train_engines: int
    test_engines: int
    conditions: int
    fault_modes: tuple[str, ...]


SUBSETS: dict[str, SubsetInfo] = {
    "FD001": SubsetInfo("FD001", 100, 100, 1, ("HPC Degradation",)),
    "FD002": SubsetInfo("FD002", 260, 259, 6, ("HPC Degradation",)),
    "FD003": SubsetInfo("FD003", 100, 100, 1, ("HPC Degradation", "Fan Degradation")),
    "FD004": SubsetInfo("FD004", 248, 249, 6, ("HPC Degradation", "Fan Degradation")),
}


class SchemaError(ValueError):
    """Raised when an original file violates the C-MAPSS schema."""


def subset_info(subset: str) -> SubsetInfo:
    try:
        return SUBSETS[subset]
    except KeyError as exc:
        raise ValueError(f"Unknown subset {subset!r}; expected one of {sorted(SUBSETS)}") from exc


def raw_paths(root: Path, subset: str) -> dict[str, Path]:
    subset_info(subset)
    base = root / "data" / "raw" / "cmaps"
    return {
        "train": base / f"train_{subset}.txt",
        "test": base / f"test_{subset}.txt",
        "rul": base / f"RUL_{subset}.txt",
    }


def validate_column_names(columns: list[str]) -> None:
    if columns != COLUMN_NAMES:
        raise SchemaError(f"Expected columns {COLUMN_NAMES}, got {columns}")
