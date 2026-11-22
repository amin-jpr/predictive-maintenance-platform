"""Provenance, checksums, and artifact metadata helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from predictive_maintenance.io import atomic_write_json, atomic_write_text, sha256_file, utc_now_iso


def file_record(path: Path, root: Path, role: str = "artifact") -> dict[str, Any]:
    return {
        "path": path.resolve().relative_to(root.resolve()).as_posix(),
        "role": role,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "recorded_at_utc": utc_now_iso(),
    }


def write_checksums(records: list[dict[str, Any]], path: Path) -> Path:
    lines = [f"{record['sha256']}  {record['path']}" for record in records]
    return atomic_write_text(path, "\n".join(lines) + "\n")


def verify_checksums(manifest_path: Path, root: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative = line.split(maxsplit=1)
        target = root / relative.strip()
        actual = sha256_file(target) if target.is_file() else None
        results.append(
            {
                "path": relative.strip(),
                "expected_sha256": expected,
                "actual_sha256": actual,
                "passed": actual == expected,
            }
        )
    return results


def build_source_manifest(
    root: Path,
    subset: str,
    archive_record: dict[str, Any],
    extracted_records: list[dict[str, Any]],
    source_config: dict[str, Any],
) -> dict[str, Any]:
    return {
        "generated_at_utc": utc_now_iso(),
        "subset": subset,
        "source": source_config,
        "archive": archive_record,
        "extracted_files": extracted_records,
        "license_note": (
            "NASA benchmark catalog says license not specified. Raw and derived data are "
            "local-only by default; this manifest records provenance, not redistribution permission."
        ),
    }


def write_source_manifest(root: Path, manifest: dict[str, Any]) -> Path:
    path = root / "data" / "metadata" / "source_manifest.json"
    atomic_write_json(path, manifest)
    records = [manifest["archive"], *manifest["extracted_files"]]
    write_checksums(records, root / "data" / "metadata" / "checksums.sha256")
    return path
