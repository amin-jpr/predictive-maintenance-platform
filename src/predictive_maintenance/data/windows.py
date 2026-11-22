"""Memory-efficient per-engine sliding windows and sequence products."""

from __future__ import annotations

import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from numpy.lib import format as np_format
from numpy.lib.stride_tricks import sliding_window_view

from predictive_maintenance.io import ensure_dir, sha256_file, utc_now_iso


class WindowError(ValueError):
    """Raised when window boundaries or inputs are invalid."""


def save_npz_deterministic(path: Path, arrays: dict[str, np.ndarray]) -> None:
    """Write NPZ with fixed ZIP timestamps so identical arrays have identical SHA-256."""
    ensure_dir(path.parent)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for key, value in arrays.items():
            buffer = BytesIO()
            np_format.write_array(buffer, np.asarray(value), allow_pickle=False)
            info = zipfile.ZipInfo(filename=f"{key}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, buffer.getvalue())


def engine_window_arrays(
    engine_frame: pd.DataFrame,
    feature_names: list[str],
    window_length: int,
    stride: int = 1,
    label_column: str = "rul",
    raw_label_column: str = "rul_raw",
) -> dict[str, np.ndarray] | None:
    if window_length < 1 or stride < 1:
        raise WindowError("window_length and stride must be >= 1")
    ordered = engine_frame.sort_values("cycle")
    cycles = ordered["cycle"].to_numpy(dtype=np.int64)
    if len(cycles) < window_length:
        return None
    if not np.all(np.diff(cycles) == 1):
        raise WindowError("Window cycles must be contiguous within an engine")
    engine_ids = ordered["engine_id"].unique()
    if len(engine_ids) != 1:
        raise WindowError("A window may contain only one engine")
    values = ordered[feature_names].to_numpy(dtype=np.float32)
    windows = sliding_window_view(values, window_shape=window_length, axis=0).transpose(0, 2, 1)
    windows = np.ascontiguousarray(windows[::stride])
    end_indices = np.arange(window_length - 1, len(cycles), stride, dtype=np.int64)
    end_cycle = cycles[end_indices]
    start_cycle = end_cycle - window_length + 1
    return {
        "X": windows,
        "y": ordered[label_column].to_numpy(dtype=np.int64)[end_indices],
        "y_raw": ordered[raw_label_column].to_numpy(dtype=np.int64)[end_indices],
        "engine_id": np.full(len(end_indices), int(engine_ids[0]), dtype=np.int64),
        "start_cycle": start_cycle,
        "end_cycle": end_cycle,
        "cycle": end_cycle,
    }


def write_sequences(
    split_frame: pd.DataFrame,
    feature_names: list[str],
    output_dir: Path,
    split: str,
) -> dict[str, Any]:
    ensure_dir(output_dir)
    path = output_dir / f"{split}.npz"
    arrays: dict[str, np.ndarray] = {}
    engine_ids = []
    lengths = []
    for engine_id, group in split_frame.groupby("engine_id", sort=True):
        ordered = group.sort_values("cycle")
        key = f"engine_{int(str(engine_id)):04d}"
        arrays[key] = ordered[feature_names].to_numpy(dtype=np.float32)
        arrays[f"{key}_y"] = ordered["rul"].to_numpy(dtype=np.int64)
        arrays[f"{key}_y_raw"] = ordered["rul_raw"].to_numpy(dtype=np.int64)
        arrays[f"{key}_cycle"] = ordered["cycle"].to_numpy(dtype=np.int64)
        engine_ids.append(int(str(engine_id)))
        lengths.append(len(ordered))
    arrays["engine_ids"] = np.asarray(engine_ids, dtype=np.int64)
    arrays["lengths"] = np.asarray(lengths, dtype=np.int64)
    save_npz_deterministic(path, arrays)
    return {
        "path": path.as_posix(),
        "split": split,
        "n_engines": len(engine_ids),
        "feature_names": feature_names,
        "dtype": "float32",
        "sha256": sha256_file(path),
        "generated_at_utc": utc_now_iso(),
    }


def build_windows(
    split_frame: pd.DataFrame,
    feature_names: list[str],
    output_dir: Path,
    split: str,
    window_length: int = 30,
    stride: int = 1,
    root: Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    ensure_dir(output_dir)
    index_rows: list[dict[str, Any]] = []
    dropped: list[int] = []
    total_windows = 0
    for engine_id, group in split_frame.groupby("engine_id", sort=True):
        arrays = engine_window_arrays(group, feature_names, window_length, stride)
        if arrays is None:
            dropped.append(int(str(engine_id)))
            continue
        path = output_dir / f"engine_{int(str(engine_id)):04d}.npz"
        save_npz_deterministic(path, arrays)
        checksum = sha256_file(path)
        total_windows += len(arrays["y"])
        relative = path.resolve().relative_to(root.resolve()).as_posix() if root else path.as_posix()
        for window_id in range(len(arrays["y"])):
            index_rows.append(
                {
                    "split": split,
                    "engine_id": int(str(engine_id)),
                    "window_id": window_id,
                    "start_cycle": int(arrays["start_cycle"][window_id]),
                    "end_cycle": int(arrays["end_cycle"][window_id]),
                    "rul": int(arrays["y"][window_id]),
                    "rul_raw": int(arrays["y_raw"][window_id]),
                    "n_cycles": window_length,
                    "path": relative,
                    "sha256": checksum,
                }
            )
    index = pd.DataFrame(index_rows)
    manifest = {
        "generated_at_utc": utc_now_iso(),
        "split": split,
        "window_length": window_length,
        "stride": stride,
        "padding": "none",
        "dtype": "float32",
        "feature_names": feature_names,
        "n_features": len(feature_names),
        "n_windows": total_windows,
        "n_engine_files": len(list(output_dir.glob("engine_*.npz"))),
        "dropped_short_engines": dropped,
        "array_keys": ["X", "y", "y_raw", "engine_id", "start_cycle", "end_cycle", "cycle"],
        "X_shape_per_engine": "(n_windows, window_length, n_features)",
    }
    return index, manifest
