from __future__ import annotations

from pathlib import Path

import pytest

from predictive_maintenance.config import canonical_json, fingerprint
from predictive_maintenance.io import (
    atomic_write_json,
    atomic_write_text,
    read_json,
    safe_relative_path,
    sha256_bytes,
)


def test_fingerprint_is_key_order_independent() -> None:
    assert fingerprint({"b": 2, "a": 1}) == fingerprint({"a": 1, "b": 2})
    assert canonical_json({"a": 1}) == '{"a":1}'


def test_sha256_bytes_known_vector() -> None:
    assert (
        sha256_bytes(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_atomic_write_and_read_json(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "data.json"
    atomic_write_json(path, {"x": 1})
    assert read_json(path) == {"x": 1}
    atomic_write_text(path.with_suffix(".txt"), "hello")
    assert path.with_suffix(".txt").read_text() == "hello"


def test_safe_relative_path_rejects_escape(tmp_path: Path) -> None:
    assert safe_relative_path(tmp_path, "a/b.txt") == tmp_path / "a/b.txt"
    with pytest.raises(ValueError):
        safe_relative_path(tmp_path, "../escape.txt")
    with pytest.raises(ValueError):
        safe_relative_path(tmp_path, "/absolute.txt")
