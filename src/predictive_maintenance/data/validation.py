"""Scientific and structural validation of original C-MAPSS subsets."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from predictive_maintenance.config import find_project_root, load_config
from predictive_maintenance.data.loader import load_rul, load_test, load_train
from predictive_maintenance.data.metadata import file_record, write_checksums
from predictive_maintenance.data.schema import (
    COLUMN_NAMES,
    MEASUREMENT_COLUMNS,
    SENSOR_COLUMNS,
    raw_paths,
    subset_info,
)
from predictive_maintenance.io import atomic_write_json, atomic_write_text, ensure_dir, utc_now_iso


@dataclass
class CheckResult:
    name: str
    passed: bool
    details: dict[str, Any]
    severity: str = "error"


def _sequence_summary(frame: pd.DataFrame) -> dict[str, Any]:
    lengths = frame.groupby("engine_id")["cycle"].agg(["min", "max", "count"])
    return {
        "engines": int(frame["engine_id"].nunique()),
        "observations": int(len(frame)),
        "min_cycle": int(frame["cycle"].min()),
        "max_cycle": int(frame["cycle"].max()),
        "min_sequence_length": int(lengths["count"].min()),
        "max_sequence_length": int(lengths["count"].max()),
        "mean_sequence_length": float(lengths["count"].mean()),
    }


def _sensor_summary(frame: pd.DataFrame) -> dict[str, Any]:
    stats = frame[SENSOR_COLUMNS].agg(["mean", "std", "min", "max"]).T
    # Use unique-value count for exact constants: floating-point std can be ~1e-15
    # even when every observation is identical (e.g., s_5/s_16 in FD001).
    constant = [col for col in SENSOR_COLUMNS if int(frame[col].nunique()) <= 1]
    near_constant = []
    for col in SENSOR_COLUMNS:
        if col in constant:
            continue
        std = float(frame[col].std(ddof=0))
        mean = float(frame[col].mean())
        if std > 0 and abs(mean) > 0 and std / abs(mean) < 1e-4:
            near_constant.append(col)
    return {
        "constant_sensors": constant,
        "near_constant_sensors": near_constant,
        "statistics": {
            col: {key: float(value) for key, value in row.items()} for col, row in stats.iterrows()
        },
    }


def _check_frame(frame: pd.DataFrame, name: str, expected_engines: int, expected_rows: int | None) -> list[CheckResult]:
    checks: list[CheckResult] = []
    checks.append(CheckResult(f"{name}_columns", list(frame.columns) == COLUMN_NAMES, {"columns": list(frame.columns)}))
    checks.append(
        CheckResult(
            f"{name}_dtypes",
            all(str(frame[col].dtype) == expected for col, expected in {"engine_id": "int64", "cycle": "int64"}.items()),
            {col: str(frame[col].dtype) for col in frame.columns},
        )
    )
    checks.append(CheckResult(f"{name}_finite", bool(np.isfinite(frame[MEASUREMENT_COLUMNS].to_numpy()).all()), {}))
    checks.append(CheckResult(f"{name}_engine_count", int(frame["engine_id"].nunique()) == expected_engines, {"actual": int(frame["engine_id"].nunique()), "expected": expected_engines}))
    if expected_rows is not None:
        checks.append(CheckResult(f"{name}_row_count", len(frame) == expected_rows, {"actual": len(frame), "expected": expected_rows}))
    duplicate_keys = int(frame.duplicated(["engine_id", "cycle"]).sum())
    duplicate_rows = int(frame.duplicated().sum())
    checks.append(CheckResult(f"{name}_duplicate_keys", duplicate_keys == 0, {"duplicate_keys": duplicate_keys}))
    checks.append(CheckResult(f"{name}_duplicate_rows", duplicate_rows == 0, {"duplicate_rows": duplicate_rows}))

    ordering_errors: list[dict[str, Any]] = []
    for engine_id, group in frame.groupby("engine_id", sort=True):
        cycles = group["cycle"].to_numpy()
        if cycles[0] != 1 or not np.all(np.diff(cycles) == 1):
            ordering_errors.append({"engine_id": int(str(engine_id)), "first_cycle": int(cycles[0]), "n": len(cycles)})
    checks.append(CheckResult(f"{name}_cycle_ordering", not ordering_errors, {"errors": ordering_errors[:20], "error_count": len(ordering_errors)}))
    checks.append(CheckResult(f"{name}_positive_lengths", bool((frame.groupby("engine_id").size() > 0).all()), {}))
    return checks


def validate_subset(root: Path, subset: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = config or load_config("dataset", root)
    info = subset_info(subset)
    subset_cfg = cfg.get("subsets", {}).get(subset, {})
    paths = raw_paths(root, subset)
    checks: list[CheckResult] = []
    report: dict[str, Any] = {
        "generated_at_utc": utc_now_iso(),
        "subset": subset,
        "status": "FAIL",
        "checks": [],
        "files": {},
        "train_summary": {},
        "test_summary": {},
        "sensor_summary": {},
        "rul_summary": {},
    }
    missing = [key for key, path in paths.items() if not path.is_file()]
    checks.append(CheckResult("required_files_exist", not missing, {"missing": missing}))
    if missing:
        report["checks"] = [asdict(check) for check in checks]
        return report

    try:
        train = load_train(root, subset)
        test = load_test(root, subset)
        rul = load_rul(root, subset)
    except Exception as exc:  # noqa: BLE001 - convert ingestion failure into structured report
        checks.append(CheckResult("loader", False, {"error": f"{type(exc).__name__}: {exc}"}))
        report["checks"] = [asdict(check) for check in checks]
        return report

    checks.extend(_check_frame(train, "train", info.train_engines, subset_cfg.get("expected_train_rows")))
    checks.extend(_check_frame(test, "test", info.test_engines, subset_cfg.get("expected_test_rows")))

    test_ids = sorted(int(value) for value in test["engine_id"].unique())
    checks.append(CheckResult("rul_length", len(rul) == len(test_ids), {"rul_values": len(rul), "test_engines": len(test_ids)}))
    checks.append(CheckResult("rul_nonnegative_integer", bool(np.all(rul >= 0)), {"min": int(rul.min()), "max": int(rul.max())}))
    checks.append(
        CheckResult(
            "rul_alignment_convention",
            test_ids == list(range(1, len(test_ids) + 1)),
            {"note": "RUL file has no engine IDs; aligned to sorted test engine IDs per NASA convention", "test_ids_sorted_contiguous": test_ids == list(range(1, len(test_ids) + 1))},
        )
    )
    numeric_id_overlap = sorted(set(train["engine_id"].unique()) & set(test["engine_id"].unique()))
    checks.append(
        CheckResult(
            "train_test_numeric_id_overlap_allowed",
            True,
            {"note": "Train/test engine IDs are separate namespaces; numeric overlap is expected", "overlap_count": len(numeric_id_overlap)},
            severity="info",
        )
    )

    expected_hashes = cfg.get("file_sha256", {}).get(subset, {})
    file_records = []
    for key, path in paths.items():
        record = file_record(path, root, role=f"raw_{key}")
        file_records.append(record)
        expected = expected_hashes.get(path.name)
        if expected is not None:
            checks.append(CheckResult(f"sha256_{path.name}", record["sha256"] == expected, {"expected": expected, "actual": record["sha256"]}))
    report["files"] = {key: file_record(path, root, role=f"raw_{key}") for key, path in paths.items()}
    report["train_summary"] = _sequence_summary(train)
    report["test_summary"] = _sequence_summary(test)
    report["sensor_summary"] = _sensor_summary(train)
    report["rul_summary"] = {
        "count": int(len(rul)),
        "min": int(rul.min()),
        "max": int(rul.max()),
        "mean": float(rul.mean()),
        "terminal_test_rul_aligned_to_sorted_engine_ids": True,
    }
    report["checks"] = [asdict(check) for check in checks]
    report["status"] = "PASS" if all(check.passed for check in checks if check.severity == "error") else "FAIL"
    return report


def write_validation_report(root: Path, report: dict[str, Any]) -> dict[str, Path]:
    out_dir = ensure_dir(root / "reports" / "validation")
    json_path = out_dir / "integrity.json"
    atomic_write_json(json_path, report)
    lines = [
        f"# C-MAPSS integrity report — {report['subset']}",
        "",
        f"Generated: {report['generated_at_utc']}",
        f"Status: **{report['status']}**",
        "",
        "## Checks",
        "",
        "| Check | Result | Severity | Details |",
        "|---|---|---|---|",
    ]
    for check in report["checks"]:
        details = str(check["details"]).replace("|", "\\|")
        lines.append(f"| {check['name']} | {'PASS' if check['passed'] else 'FAIL'} | {check['severity']} | {details} |")
    lines.extend(["", "## Summary", "", f"Train: {report['train_summary']}", f"Test: {report['test_summary']}", f"RUL: {report['rul_summary']}", f"Constant sensors: {report['sensor_summary'].get('constant_sensors', [])}", f"Near-constant sensors: {report['sensor_summary'].get('near_constant_sensors', [])}"])
    md_path = out_dir / "integrity.md"
    atomic_write_text(md_path, "\n".join(lines) + "\n")
    if report.get("files"):
        write_checksums(list(report["files"].values()), root / "data" / "metadata" / "validation_checksums.sha256")
    return {"json": json_path, "markdown": md_path}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate original C-MAPSS files and write integrity reports.")
    parser.add_argument("--subset", default="FD001")
    args = parser.parse_args(argv)
    root = find_project_root()
    report = validate_subset(root, args.subset)
    paths = write_validation_report(root, report)
    print(f"Validation {report['status']} for {args.subset}")
    print(f"JSON: {paths['json']}")
    print(f"Markdown: {paths['markdown']}")
    failed = [check['name'] for check in report['checks'] if not check['passed'] and check['severity'] == 'error']
    if failed:
        print("Failed checks:", failed)
        return 1
    print(f"Train: {report['train_summary']}")
    print(f"Test: {report['test_summary']}")
    print(f"RUL: {report['rul_summary']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
