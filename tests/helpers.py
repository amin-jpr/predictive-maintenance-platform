"""Synthetic C-MAPSS fixtures for tests (not NASA data)."""

from __future__ import annotations

from pathlib import Path


def make_table_text(n_engines: int, length: int, start_engine: int = 1) -> str:
    lines = []
    for engine in range(start_engine, start_engine + n_engines):
        for cycle in range(1, length + 1):
            values = [engine, cycle, 0.001 * cycle, -0.0002 * cycle, 100.0]
            values += [500.0 + engine + cycle + i for i in range(21)]
            lines.append(" ".join(str(value) for value in values))
    return "\n".join(lines) + "\n"


def write_synthetic_subset(
    root: Path,
    subset: str = "FD001",
    n_train: int = 100,
    n_test: int = 100,
    train_len: int = 3,
    test_len: int = 2,
) -> dict[str, Path]:
    base = root / "data" / "raw" / "cmaps"
    base.mkdir(parents=True, exist_ok=True)
    paths = {
        "train": base / f"train_{subset}.txt",
        "test": base / f"test_{subset}.txt",
        "rul": base / f"RUL_{subset}.txt",
    }
    paths["train"].write_text(make_table_text(n_train, train_len), encoding="ascii")
    paths["test"].write_text(make_table_text(n_test, test_len), encoding="ascii")
    paths["rul"].write_text(
        "\n".join(str(5 + i % 3) for i in range(n_test)) + "\n", encoding="ascii"
    )
    return paths


def minimal_config() -> dict:
    return {"subsets": {"FD001": {}}, "file_sha256": {}}
