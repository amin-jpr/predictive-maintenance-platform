"""Artifact descriptions, manifests, and checksum verification."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from predictive_maintenance.data.metadata import write_checksums
from predictive_maintenance.io import atomic_write_json, sha256_file, utc_now_iso


def describe_artifact(path: Path) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": path.as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "generated_at_utc": utc_now_iso(),
    }
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        frame = pd.read_parquet(path)
        record.update(
            {
                "format": "parquet",
                "shape": list(frame.shape),
                "columns": list(frame.columns),
                "dtypes": {column: str(dtype) for column, dtype in frame.dtypes.items()},
            }
        )
    elif suffix == ".csv":
        frame = pd.read_csv(path)
        record.update(
            {
                "format": "csv",
                "shape": list(frame.shape),
                "columns": list(frame.columns),
                "dtypes": {column: str(dtype) for column, dtype in frame.dtypes.items()},
            }
        )
    elif suffix == ".npz":
        with np.load(path, allow_pickle=False) as arrays:
            record.update(
                {
                    "format": "npz",
                    "arrays": {
                        key: {"shape": list(arrays[key].shape), "dtype": str(arrays[key].dtype)}
                        for key in arrays.files
                    },
                }
            )
    elif suffix == ".json":
        record["format"] = "json"
    elif suffix in {".md", ".txt", ".sha256"}:
        record["format"] = "text"
    else:
        record["format"] = suffix.lstrip(".") or "unknown"
    return record


def build_artifact_manifest(
    root: Path,
    directories: list[Path],
    subset: str,
    fingerprints: dict[str, str],
    exclude_names: set[str] | None = None,
) -> dict[str, Any]:
    exclude = exclude_names or {"artifact_manifest.json", "processed_checksums.sha256"}
    entries = []
    for directory in directories:
        if not directory.exists():
            continue
        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.name not in exclude:
                record = describe_artifact(path)
                record["path"] = path.resolve().relative_to(root.resolve()).as_posix()
                record["source_subset"] = subset
                record["config_fingerprints"] = fingerprints
                entries.append(record)
    manifest = {
        "generated_at_utc": utc_now_iso(),
        "subset": subset,
        "config_fingerprints": fingerprints,
        "artifact_count": len(entries),
        "artifacts": entries,
    }
    return manifest


def write_artifact_manifest(root: Path, manifest: dict[str, Any]) -> Path:
    path = root / "data" / "metadata" / "artifact_manifest.json"
    atomic_write_json(path, manifest)
    records = [
        {"sha256": entry["sha256"], "path": entry["path"]} for entry in manifest["artifacts"]
    ]
    write_checksums(records, root / "data" / "metadata" / "processed_checksums.sha256")
    return path


def verify_artifact_manifest(root: Path, manifest_path: Path) -> list[dict[str, Any]]:
    from predictive_maintenance.io import read_json

    manifest = read_json(manifest_path)
    results = []
    for entry in manifest["artifacts"]:
        path = root / entry["path"]
        actual = sha256_file(path) if path.is_file() else None
        results.append(
            {
                "path": entry["path"],
                "expected_sha256": entry["sha256"],
                "actual_sha256": actual,
                "passed": actual == entry["sha256"],
            }
        )
    return results
