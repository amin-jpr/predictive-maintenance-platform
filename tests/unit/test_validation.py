from pathlib import Path

from tests.helpers import minimal_config, write_synthetic_subset

from predictive_maintenance.data.validation import validate_subset


def test_valid_synthetic_subset_passes(tmp_path: Path) -> None:
    write_synthetic_subset(tmp_path)
    report = validate_subset(tmp_path, "FD001", config=minimal_config())
    assert report["status"] == "PASS"
    assert report["train_summary"]["engines"] == 100
    assert report["rul_summary"]["count"] == 100


def test_duplicate_key_fails(tmp_path: Path) -> None:
    paths = write_synthetic_subset(tmp_path)
    text = paths["train"].read_text()
    paths["train"].write_text(text + text.splitlines()[0] + "\n")
    report = validate_subset(tmp_path, "FD001", config=minimal_config())
    assert report["status"] == "FAIL"


def test_cycle_gap_fails(tmp_path: Path) -> None:
    paths = write_synthetic_subset(tmp_path)
    lines = paths["train"].read_text().splitlines()
    tokens = lines[1].split()
    tokens[1] = "3"  # engine 1 cycles 1,3 -> gap
    lines[1] = " ".join(tokens)
    paths["train"].write_text("\n".join(lines) + "\n")
    report = validate_subset(tmp_path, "FD001", config=minimal_config())
    assert report["status"] == "FAIL"


def test_rul_length_mismatch_fails(tmp_path: Path) -> None:
    paths = write_synthetic_subset(tmp_path)
    paths["rul"].write_text("5\n6\n")
    report = validate_subset(tmp_path, "FD001", config=minimal_config())
    assert report["status"] == "FAIL"


def test_missing_file_fails(tmp_path: Path) -> None:
    report = validate_subset(tmp_path, "FD001", config=minimal_config())
    assert report["status"] == "FAIL"
