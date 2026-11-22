"""Milestone 4 orchestration: cycle-level preparation and feature products (no predictive fitting)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from predictive_maintenance.config import fingerprint, load_config
from predictive_maintenance.data.labels import add_test_labels, add_train_labels
from predictive_maintenance.data.loader import load_rul, load_test, load_train
from predictive_maintenance.data.schema import SENSOR_COLUMNS, SETTING_COLUMNS
from predictive_maintenance.data.splitting import assign_split, engine_split
from predictive_maintenance.data.validation import validate_subset
from predictive_maintenance.data.windows import build_windows, write_sequences
from predictive_maintenance.features.engineering import (
    build_feature_frame,
    feature_names_from_config,
)
from predictive_maintenance.io import (
    atomic_write_json,
    atomic_write_text,
    ensure_dir,
    read_json,
    utc_now_iso,
)
from predictive_maintenance.preprocessing.artifacts import (
    build_artifact_manifest,
    write_artifact_manifest,
)
from predictive_maintenance.preprocessing.scaling import (
    fit_scaler,
    save_scaler_state,
    transform_features,
)

SPLITS = ["train_fit", "validation", "test"]


def _config_fingerprints(
    preproc: dict[str, Any], features: dict[str, Any], dataset: dict[str, Any]
) -> dict[str, str]:
    return {
        "preprocessing": fingerprint(preproc),
        "features": fingerprint(features),
        "dataset": fingerprint(dataset),
    }


def _write_parquet(frame: pd.DataFrame, path: Path) -> None:
    ensure_dir(path.parent)
    frame.to_parquet(path, index=False)


def prepare_cycle_level(
    root: Path,
    subset: str = "FD001",
    preproc: dict[str, Any] | None = None,
    dataset: dict[str, Any] | None = None,
    features_cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    preproc = preproc or load_config("preprocessing", root)
    dataset = dataset or load_config("dataset", root)
    features_cfg = features_cfg or load_config("features", root)
    report = validate_subset(root, subset, config=dataset)
    if report["status"] != "PASS":
        raise RuntimeError(f"Cannot preprocess invalid subset {subset}")
    cap = int(preproc["rul"]["cap"])
    train = add_train_labels(load_train(root, subset), cap)
    test = add_test_labels(load_test(root, subset), load_rul(root, subset), cap)
    split = engine_split(
        train["engine_id"].unique().tolist(),
        validation_fraction=float(preproc["split"]["validation_fraction"]),
        seed=int(preproc["split"]["seed"]),
    )
    train = assign_split(train, split)
    test["split"] = "test"
    train["subset"] = subset
    test["subset"] = subset
    split["official_test_engine_ids"] = sorted(int(value) for value in test["engine_id"].unique())
    split["subset"] = subset
    split["config_fingerprint"] = fingerprint(preproc)

    interim = ensure_dir(root / preproc["paths"]["interim_dir"] / "labeled")
    processed = ensure_dir(root / preproc["paths"]["processed_dir"])
    metadata = ensure_dir(root / preproc["paths"]["metadata_dir"])
    _write_parquet(train, interim / "train.parquet")
    _write_parquet(test, interim / "test.parquet")

    split_frames = {
        "train_fit": train[train["split"] == "train_fit"].reset_index(drop=True),
        "validation": train[train["split"] == "validation"].reset_index(drop=True),
        "test": test.reset_index(drop=True),
    }
    counts = {}
    for name, frame in split_frames.items():
        _write_parquet(frame, processed / "cycle_level" / f"{name}.parquet")
        endpoint = "failure_cycle" if name != "test" else "inferred_failure_cycle"
        labels = frame[["engine_id", "cycle", "rul_raw", "rul", "split", "subset", endpoint]].copy()
        labels = labels.rename(columns={endpoint: "endpoint_cycle"})
        ensure_dir(processed / "labels")
        labels.to_csv(processed / "labels" / f"{name}.csv", index=False)
        counts[name] = {"rows": len(frame), "engines": int(frame["engine_id"].nunique())}

    atomic_write_json(metadata / "split.json", split)
    preprocessing_record = {
        "generated_at_utc": utc_now_iso(),
        "stage": "cycle_level",
        "subset": subset,
        "cap": cap,
        "config_fingerprints": _config_fingerprints(preproc, features_cfg, dataset),
        "preprocessing_config": preproc,
        "source_file_sha256": dataset.get("file_sha256", {}).get(subset, {}),
        "counts": counts,
        "no_predictive_model_trained": True,
    }
    atomic_write_json(metadata / "preprocessing.json", preprocessing_record)
    return {"subset": subset, "cap": cap, "split": split, "counts": counts}


def _check_sensor_selection(preproc: dict[str, Any], features: dict[str, Any]) -> None:
    expected_sensors = sorted(
        set(SENSOR_COLUMNS) - set(preproc["sensor_selection"]["excluded_sensors"])
    )
    expected_settings = sorted(
        set(SETTING_COLUMNS) - set(preproc["sensor_selection"]["excluded_settings"])
    )
    if sorted(features["selected_sensors"]) != expected_sensors:
        raise ValueError("features.yaml selected_sensors does not match preprocessing exclusions")
    if sorted(features["selected_settings"]) != expected_settings:
        raise ValueError("features.yaml selected_settings does not match preprocessing exclusions")


def build_feature_products(
    root: Path,
    subset: str = "FD001",
    preproc: dict[str, Any] | None = None,
    features_cfg: dict[str, Any] | None = None,
    dataset: dict[str, Any] | None = None,
) -> dict[str, Any]:
    preproc = preproc or load_config("preprocessing", root)
    features_cfg = features_cfg or load_config("features", root)
    dataset = dataset or load_config("dataset", root)
    _check_sensor_selection(preproc, features_cfg)
    processed = root / preproc["paths"]["processed_dir"]
    metadata = ensure_dir(root / preproc["paths"]["metadata_dir"])
    split = read_json(metadata / "split.json")
    feature_names = feature_names_from_config(features_cfg)

    cycle_frames = {
        name: pd.read_parquet(processed / "cycle_level" / f"{name}.parquet") for name in SPLITS
    }
    feature_frames: dict[str, pd.DataFrame] = {}
    for name, frame in cycle_frames.items():
        built, names = build_feature_frame(frame, features_cfg)
        if names != feature_names:
            raise ValueError("Feature order differs across splits")
        feature_frames[name] = built
        stored = built.copy()
        stored[feature_names] = stored[feature_names].astype(np.float32)
        _write_parquet(stored, processed / "features" / f"{name}.parquet")

    scaler, scaler_state = fit_scaler(
        feature_frames["train_fit"],
        feature_names,
        split["train_fit"],
        fit_split=preproc["scaling"]["fit_split"],
        metadata={"subset": subset, "config_fingerprint": fingerprint(features_cfg)},
    )
    save_scaler_state(metadata / "scaler.json", scaler_state)
    atomic_write_json(
        metadata / "feature_names.json",
        {"feature_names": feature_names, "n_features": len(feature_names), "dtype": "float32"},
    )

    window_indices = []
    window_manifests = {}
    sequence_manifests = {}
    window_length = int(preproc["windows"]["length"])
    stride = int(preproc["windows"]["stride"])
    for name in SPLITS:
        scaled = transform_features(feature_frames[name], scaler, feature_names)
        stored = scaled.copy()
        stored[feature_names] = stored[feature_names].astype(np.float32)
        _write_parquet(stored, processed / "scaled" / f"{name}.parquet")
        labels = cycle_frames[name][["engine_id", "cycle", "rul", "rul_raw"]]
        merged = scaled.merge(labels, on=["engine_id", "cycle"], how="left", validate="one_to_one")
        if merged[["rul", "rul_raw"]].isna().any().any():
            raise ValueError("Missing labels after scaled/label merge")
        sequence_manifests[name] = write_sequences(
            merged, feature_names, processed / "sequences", name
        )
        index, manifest = build_windows(
            merged,
            feature_names,
            processed / "windows" / name,
            name,
            window_length=window_length,
            stride=stride,
            root=root,
        )
        window_indices.append(index)
        window_manifests[name] = manifest

    window_index = pd.concat(window_indices, ignore_index=True)
    ensure_dir(processed)
    window_index.to_csv(processed / "window_index.csv", index=False)
    atomic_write_json(
        processed / "windows" / "manifest.json",
        {"splits": window_manifests, "window_length": window_length, "stride": stride},
    )

    fingerprints = _config_fingerprints(preproc, features_cfg, dataset)
    window_counts = {name: manifest_["n_windows"] for name, manifest_ in window_manifests.items()}
    # Update metadata before hashing the manifest so checksums describe final bytes.
    preprocessing_record = read_json(metadata / "preprocessing.json")
    preprocessing_record.update(
        {
            "generated_at_utc": utc_now_iso(),
            "stage": "feature_products",
            "feature_config": features_cfg,
            "config_fingerprints": fingerprints,
            "n_features": len(feature_names),
            "window_counts": window_counts,
            "scaler_fit_engines": scaler_state["fit_engine_ids"],
        }
    )
    atomic_write_json(metadata / "preprocessing.json", preprocessing_record)
    manifest = build_artifact_manifest(
        root,
        [root / preproc["paths"]["interim_dir"], processed, metadata],
        subset,
        fingerprints,
    )
    write_artifact_manifest(root, manifest)

    summary = {
        "generated_at_utc": utc_now_iso(),
        "subset": subset,
        "stage": "feature_products",
        "cap": int(preproc["rul"]["cap"]),
        "window_length": window_length,
        "stride": stride,
        "n_features": len(feature_names),
        "feature_names": feature_names,
        "scaler_fit_split": scaler_state["fit_split"],
        "scaler_fit_engines": scaler_state["fit_engine_ids"],
        "scaler_n_samples_seen": scaler_state["n_samples_seen"],
        "cycle_counts": {
            name: {"rows": len(frame), "engines": int(frame["engine_id"].nunique())}
            for name, frame in cycle_frames.items()
        },
        "feature_table_counts": {name: len(frame) for name, frame in feature_frames.items()},
        "window_counts": {
            name: manifest_["n_windows"] for name, manifest_ in window_manifests.items()
        },
        "dropped_short_engines": {
            name: manifest_["dropped_short_engines"] for name, manifest_ in window_manifests.items()
        },
        "sequence_files": sequence_manifests,
        "artifact_count": manifest["artifact_count"],
        "no_predictive_model_trained": True,
    }
    report_dir = ensure_dir(root / preproc["paths"]["report_dir"])
    atomic_write_json(report_dir / "summary.json", summary)
    _write_preprocessing_summary_md(report_dir / "summary.md", summary)

    return summary


def _write_preprocessing_summary_md(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        f"# Preprocessing summary — {summary['subset']}",
        "",
        f"Generated: {summary['generated_at_utc']}",
        "",
        f"- RUL cap: {summary['cap']} cycles",
        f"- Window length / stride: {summary['window_length']} / {summary['stride']}",
        f"- Feature count: {summary['n_features']}",
        f"- Scaler fit split: {summary['scaler_fit_split']} ({len(summary['scaler_fit_engines'])} engines; {summary['scaler_n_samples_seen']} rows)",
        "- No predictive model trained.",
        "",
        "## Cycle counts",
    ]
    for name, counts in summary["cycle_counts"].items():
        lines.append(f"- {name}: {counts['rows']} rows, {counts['engines']} engines")
    lines.extend(["", "## Window counts"])
    for name, count in summary["window_counts"].items():
        lines.append(
            f"- {name}: {count} windows; dropped short engines: {summary['dropped_short_engines'][name]}"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            f"- Manifest artifact count: {summary['artifact_count']}",
            "- See `data/metadata/artifact_manifest.json` and `processed_checksums.sha256`.",
        ]
    )
    atomic_write_text(path, "\n".join(lines) + "\n")
