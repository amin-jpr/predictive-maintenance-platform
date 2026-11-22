"""Independent verification of generated artifacts, labels, splits, and checksums."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from predictive_maintenance.config import find_project_root, load_config
from predictive_maintenance.data.labels import add_test_labels, add_train_labels
from predictive_maintenance.data.loader import load_rul, load_test, load_train
from predictive_maintenance.data.splitting import assert_split_isolation
from predictive_maintenance.io import atomic_write_json, atomic_write_text, read_json
from predictive_maintenance.preprocessing.artifacts import verify_artifact_manifest


def verify(root: Path, subset: str = "FD001") -> dict:
    preproc = load_config("preprocessing", root)
    processed = root / preproc["paths"]["processed_dir"]
    metadata = root / preproc["paths"]["metadata_dir"]
    checks: list[dict] = []

    manifest_path = metadata / "artifact_manifest.json"
    manifest_results = verify_artifact_manifest(root, manifest_path)
    checks.append(
        {
            "name": "artifact_checksums",
            "passed": all(item["passed"] for item in manifest_results),
            "details": {
                "artifacts": len(manifest_results),
                "failed": [item["path"] for item in manifest_results if not item["passed"]],
            },
        }
    )

    cap = int(preproc["rul"]["cap"])
    train_labels = add_train_labels(load_train(root, subset), cap)
    test_labels = add_test_labels(load_test(root, subset), load_rul(root, subset), cap)
    split = read_json(metadata / "split.json")
    assert_split_isolation(
        split["train_fit"], split["validation"], sorted(train_labels["engine_id"].unique().tolist())
    )
    checks.append(
        {
            "name": "split_isolation",
            "passed": True,
            "details": {"fit": len(split["train_fit"]), "validation": len(split["validation"])},
        }
    )

    train_processed = pd.concat(
        [
            pd.read_csv(processed / "labels" / "train_fit.csv"),
            pd.read_csv(processed / "labels" / "validation.csv"),
        ],
        ignore_index=True,
    )
    merged = train_processed.merge(
        train_labels[["engine_id", "cycle", "rul_raw", "rul"]],
        on=["engine_id", "cycle"],
        suffixes=("_stored", "_expected"),
        validate="one_to_one",
    )
    train_ok = bool(
        (merged["rul_raw_stored"] == merged["rul_raw_expected"]).all()
        and (merged["rul_stored"] == merged["rul_expected"]).all()
    )
    checks.append(
        {"name": "train_labels_independent", "passed": train_ok, "details": {"rows": len(merged)}}
    )

    test_processed = pd.read_csv(processed / "labels" / "test.csv")
    merged_test = test_processed.merge(
        test_labels[["engine_id", "cycle", "rul_raw", "rul"]],
        on=["engine_id", "cycle"],
        suffixes=("_stored", "_expected"),
        validate="one_to_one",
    )
    test_ok = bool(
        (merged_test["rul_raw_stored"] == merged_test["rul_raw_expected"]).all()
        and (merged_test["rul_stored"] == merged_test["rul_expected"]).all()
    )
    checks.append(
        {
            "name": "test_labels_independent",
            "passed": test_ok,
            "details": {"rows": len(merged_test)},
        }
    )

    scaler_state = read_json(metadata / "scaler.json")
    scaler_ok = scaler_state["fit_split"] == "train_fit" and scaler_state[
        "fit_engine_ids"
    ] == sorted(split["train_fit"])
    checks.append(
        {
            "name": "scaler_fit_boundary",
            "passed": scaler_ok,
            "details": {
                "fit_split": scaler_state["fit_split"],
                "n_fit_engines": scaler_state["n_fit_engines"],
            },
        }
    )

    window_index = pd.read_csv(processed / "window_index.csv")
    window_length = int(preproc["windows"]["length"])
    boundary_ok = bool(
        (window_index["start_cycle"] == window_index["end_cycle"] - window_length + 1).all()
    )
    checks.append(
        {
            "name": "window_boundaries",
            "passed": boundary_ok,
            "details": {"windows": len(window_index)},
        }
    )

    # Engine IDs are local to train/test namespaces; include split in the join key.
    label_lookup = pd.concat(
        [
            pd.read_csv(processed / "labels" / f"{name}.csv")
            for name in ["train_fit", "validation", "test"]
        ],
        ignore_index=True,
    )[["split", "engine_id", "cycle", "rul"]]
    target_check = window_index.merge(
        label_lookup,
        left_on=["split", "engine_id", "end_cycle"],
        right_on=["split", "engine_id", "cycle"],
        how="left",
        validate="many_to_one",
    )
    target_ok = bool((target_check["rul_x"] == target_check["rul_y"]).all())
    checks.append(
        {
            "name": "window_targets_match_ending_cycle",
            "passed": target_ok,
            "details": {"windows": len(target_check)},
        }
    )

    sample_ok = True
    sample_details = {}
    for split_name in ["train_fit", "validation", "test"]:
        files = sorted((processed / "windows" / split_name).glob("engine_*.npz"))
        if files:
            with np.load(files[0], allow_pickle=False) as arrays:
                shape = arrays["X"].shape
                sample_ok = (
                    sample_ok
                    and shape[1] == window_length
                    and shape[2] == scaler_state["n_features_in"]
                )
                sample_details[split_name] = {"file": files[0].name, "X_shape": list(shape)}
    checks.append(
        {"name": "window_array_dimensions", "passed": sample_ok, "details": sample_details}
    )

    passed = all(check["passed"] for check in checks)
    report = {"subset": subset, "status": "PASS" if passed else "FAIL", "checks": checks}
    out = root / preproc["paths"]["report_dir"]
    atomic_write_json(out / "verification.json", report)
    lines = [f"# Artifact verification — {subset}", "", f"Status: **{report['status']}**", ""]
    for check in checks:
        lines.append(
            f"- {check['name']}: {'PASS' if check['passed'] else 'FAIL'} — {check['details']}"
        )
    atomic_write_text(out / "verification.md", "\n".join(lines) + "\n")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify generated preprocessing artifacts independently."
    )
    parser.add_argument("--subset", default="FD001")
    args = parser.parse_args(argv)
    root = find_project_root()
    report = verify(root, args.subset)
    print(f"Artifact verification {report['status']}")
    for check in report["checks"]:
        print(f"  {check['name']}: {'PASS' if check['passed'] else 'FAIL'}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
