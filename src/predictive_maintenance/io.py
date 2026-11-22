"""Filesystem helpers: hashing, safe paths, and atomic writes."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_relative_path(base: Path, relative: str | Path) -> Path:
    """Resolve a relative path and ensure it stays inside base (ZIP/path traversal guard)."""
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"Unsafe path: {relative}")
    target = (base / rel).resolve()
    base_resolved = base.resolve()
    if not target.is_relative_to(base_resolved):
        raise ValueError(f"Path escapes base directory: {relative}")
    return target


def atomic_write_text(path: Path, text: str) -> Path:
    ensure_dir(path.parent)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(tmp_name, path)
    except BaseException:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise
    return path


def atomic_write_json(path: Path, data: Any) -> Path:
    return atomic_write_text(path, json.dumps(data, indent=2, sort_keys=True, default=str) + "\n")


def atomic_write_yaml(path: Path, data: Any) -> Path:
    return atomic_write_text(path, yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
