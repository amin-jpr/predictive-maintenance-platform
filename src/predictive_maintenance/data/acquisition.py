"""Reproducible NASA C-MAPSS acquisition with integrity and safe extraction."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import stat
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from predictive_maintenance.config import find_project_root, load_config
from predictive_maintenance.data.metadata import build_source_manifest, file_record, write_source_manifest
from predictive_maintenance.data.schema import raw_paths, subset_info
from predictive_maintenance.io import atomic_write_json, ensure_dir, safe_relative_path, sha256_file, utc_now_iso

MAX_MEMBER_BYTES = 200 * 1024 * 1024
SUPPORTED_MEMBERS = {"readme.txt", "Damage Propagation Modeling.pdf"}


class AcquisitionError(RuntimeError):
    """Raised when download or extraction cannot be verified."""


def _required_members(subset: str) -> list[str]:
    return [f"train_{subset}.txt", f"test_{subset}.txt", f"RUL_{subset}.txt", *sorted(SUPPORTED_MEMBERS)]


def download_archive(config: dict[str, Any], root: Path, retries: int = 3) -> dict[str, Any]:
    source = config["source"]
    archive_dir = ensure_dir(root / config["paths"]["archive_dir"])
    archive_path = archive_dir / source["archive_name"]
    expected_sha = source["archive_sha256"]
    expected_bytes = int(source["archive_bytes"])

    if archive_path.exists():
        actual_sha = sha256_file(archive_path)
        if actual_sha != expected_sha or archive_path.stat().st_size != expected_bytes:
            raise AcquisitionError(
                f"Existing archive {archive_path} does not match pinned SHA-256/size. "
                "Refusing to overwrite raw data silently."
            )
        return {
            "path": archive_path.resolve().relative_to(root.resolve()).as_posix(),
            "bytes": archive_path.stat().st_size,
            "sha256": actual_sha,
            "downloaded_at_utc": source.get("observed_download_utc", utc_now_iso()),
            "verified_at_utc": utc_now_iso(),
            "source_url": source["archive_url"],
            "download_skipped_existing_verified": True,
        }

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        tmp_path: Path | None = None
        try:
            with requests.get(
                source["archive_url"], stream=True, timeout=(30, 180), headers={"User-Agent": "predictive-maintenance-platform/1.0"}
            ) as response:
                response.raise_for_status()
                final_host = urlparse(response.url).netloc
                fd, tmp_name = tempfile.mkstemp(prefix=".CMAPSSData.", suffix=".part", dir=archive_dir)
                tmp_path = Path(tmp_name)
                size = 0
                with open(fd, "wb") as handle:
                    for chunk in response.iter_content(1024 * 1024):
                        if chunk:
                            handle.write(chunk)
                            size += len(chunk)
                            if size > expected_bytes * 2:
                                raise AcquisitionError("Download exceeded expected size guard")
            actual_sha = sha256_file(tmp_path)
            if actual_sha != expected_sha or size != expected_bytes:
                raise AcquisitionError(
                    f"Downloaded archive mismatch: sha256={actual_sha}, bytes={size}; expected {expected_sha}/{expected_bytes}"
                )
            shutil.move(str(tmp_path), str(archive_path))
            tmp_path = None
            return {
                "path": archive_path.resolve().relative_to(root.resolve()).as_posix(),
                "bytes": size,
                "sha256": actual_sha,
                "downloaded_at_utc": utc_now_iso(),
                "verified_at_utc": utc_now_iso(),
                "source_url": source["archive_url"],
                "final_host": final_host,
                "attempt": attempt,
                "download_skipped_existing_verified": False,
            }
        except Exception as exc:  # noqa: BLE001 - record and retry transport/integrity failures
            last_error = exc
            if tmp_path is not None and tmp_path.exists():
                tmp_path.unlink()
            if attempt < retries:
                time.sleep(2 * attempt)
    raise AcquisitionError(f"Failed to download verified archive after {retries} attempts: {last_error}")


def _safe_members(archive: zipfile.ZipFile, required: list[str]) -> list[zipfile.ZipInfo]:
    names = set(archive.namelist())
    missing = [name for name in required if name not in names]
    if missing:
        raise AcquisitionError(f"Archive missing required members: {missing}")
    bad = archive.testzip()
    if bad is not None:
        raise AcquisitionError(f"Archive CRC failure in member: {bad}")
    selected: list[zipfile.ZipInfo] = []
    for info in archive.infolist():
        if info.filename not in required:
            continue
        if info.is_dir():
            raise AcquisitionError(f"Unexpected directory member: {info.filename}")
        safe_relative_path(Path("."), info.filename)
        mode = info.external_attr >> 16
        if stat.S_ISLNK(mode):
            raise AcquisitionError(f"Refusing symlink member: {info.filename}")
        if info.file_size > MAX_MEMBER_BYTES:
            raise AcquisitionError(f"Member too large: {info.filename}")
        selected.append(info)
    return selected


def extract_subset(config: dict[str, Any], root: Path, subset: str, archive_path: Path) -> list[dict[str, Any]]:
    raw_dir = ensure_dir(root / config["paths"]["raw_dir"])
    required = _required_members(subset)
    expected_hashes = config.get("file_sha256", {}).get(subset, {})
    records: list[dict[str, Any]] = []
    with zipfile.ZipFile(archive_path) as archive:
        for info in _safe_members(archive, required):
            target = safe_relative_path(raw_dir, info.filename)
            data = archive.read(info)
            if len(data) != info.file_size:
                raise AcquisitionError(f"Extracted size mismatch for {info.filename}")
            actual_sha = hashlib.sha256(data).hexdigest()
            expected = expected_hashes.get(info.filename)
            if expected is not None and actual_sha != expected:
                raise AcquisitionError(f"SHA-256 mismatch for {info.filename}: {actual_sha} != {expected}")
            if target.exists():
                if sha256_file(target) != actual_sha:
                    raise AcquisitionError(f"Refusing to overwrite existing raw file with different bytes: {target}")
            else:
                target.write_bytes(data)
            target.chmod(0o444)
            records.append(file_record(target, root, role="raw_original"))
    return records


def acquire(root: Path, subset: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    subset_info(subset)
    cfg = config or load_config("dataset", root)
    archive_record = download_archive(cfg, root)
    archive_path = root / archive_record["path"]
    extracted = extract_subset(cfg, root, subset, archive_path)
    manifest = build_source_manifest(root, subset, archive_record, extracted, cfg["source"])
    manifest_path = write_source_manifest(root, manifest)
    acquisition_record = {
        "generated_at_utc": utc_now_iso(),
        "subset": subset,
        "archive": archive_record,
        "extracted_files": extracted,
        "source_manifest": manifest_path.resolve().relative_to(root.resolve()).as_posix(),
        "raw_paths": {key: str(path.resolve().relative_to(root.resolve())) for key, path in raw_paths(root, subset).items()},
        "license_note": manifest["license_note"],
    }
    atomic_write_json(root / "data" / "metadata" / "acquisition.json", acquisition_record)
    return acquisition_record


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download/verify and safely extract NASA C-MAPSS files.")
    parser.add_argument("--subset", default="FD001", choices=sorted(["FD001", "FD002", "FD003", "FD004"]))
    args = parser.parse_args(argv)
    root = find_project_root()
    record = acquire(root, args.subset)
    print(f"Acquisition verified for {args.subset}")
    print(f"Archive SHA-256: {record['archive']['sha256']}")
    for item in record["extracted_files"]:
        print(f"  {item['path']}  {item['bytes']} bytes  {item['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
