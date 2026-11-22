"""Configuration loading and deterministic fingerprints."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


def find_project_root(start: Path | None = None) -> Path:
    """Find the repository root by looking for pyproject.toml and configs/project.yaml."""
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "pyproject.toml").is_file() and (
            candidate / "configs/project.yaml"
        ).is_file():
            return candidate
    raise FileNotFoundError(
        "Could not locate project root (pyproject.toml + configs/project.yaml). "
        "Run commands from the repository root."
    )


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML mapping, rejecting empty/non-mapping documents."""
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping in {path}, got {type(data).__name__}")
    return data


def load_config(name: str, root: Path | None = None) -> dict[str, Any]:
    """Load configs/<name>.yaml from the project root."""
    base = root or find_project_root()
    return load_yaml(base / "configs" / f"{name}.yaml")


def canonical_json(data: Any) -> str:
    """Stable JSON used for configuration/source fingerprints."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def fingerprint(data: Any) -> str:
    """SHA-256 of canonical JSON."""
    return hashlib.sha256(canonical_json(data).encode("utf-8")).hexdigest()
