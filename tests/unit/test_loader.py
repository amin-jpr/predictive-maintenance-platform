from pathlib import Path

import pytest
from tests.helpers import make_table_text

from predictive_maintenance.data.loader import load_cmaps_table, load_rul_vector
from predictive_maintenance.data.schema import SchemaError


def test_load_valid_table(tmp_path: Path) -> None:
    path = tmp_path / "train_FD001.txt"
    path.write_text(make_table_text(2, 3), encoding="ascii")
    frame = load_cmaps_table(path)
    assert len(frame) == 6
    assert frame["engine_id"].dtype == "int64"
    assert frame["cycle"].dtype == "int64"
    assert list(frame.columns)[-1] == "s_21"


def test_ragged_row_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.txt"
    path.write_text("1 1 0.0\n", encoding="ascii")
    with pytest.raises(SchemaError, match="expected 26"):
        load_cmaps_table(path)


def test_nonfinite_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.txt"
    line = make_table_text(1, 1).strip().split()
    line[5] = "nan"
    path.write_text(" ".join(line) + "\n", encoding="ascii")
    with pytest.raises(SchemaError, match="non-finite"):
        load_cmaps_table(path)


def test_noninteger_cycle_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.txt"
    line = make_table_text(1, 1).strip().split()
    line[1] = "1.5"
    path.write_text(" ".join(line) + "\n", encoding="ascii")
    with pytest.raises(SchemaError, match="integer-valued"):
        load_cmaps_table(path)


def test_rul_vector(tmp_path: Path) -> None:
    path = tmp_path / "RUL_FD001.txt"
    path.write_text("112\n98\n0\n", encoding="ascii")
    assert load_rul_vector(path).tolist() == [112, 98, 0]
    path.write_text("-1\n", encoding="ascii")
    with pytest.raises(SchemaError):
        load_rul_vector(path)
    path.write_text("1.5\n", encoding="ascii")
    with pytest.raises(SchemaError):
        load_rul_vector(path)
