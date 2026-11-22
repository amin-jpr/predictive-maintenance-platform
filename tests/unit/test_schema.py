from predictive_maintenance.data.schema import (
    COLUMN_NAMES,
    N_COLUMNS,
    SENSOR_COLUMNS,
    SETTING_COLUMNS,
    subset_info,
)


def test_column_contract() -> None:
    assert N_COLUMNS == 26
    assert len(SENSOR_COLUMNS) == 21
    assert len(SETTING_COLUMNS) == 3
    assert COLUMN_NAMES[:5] == ["engine_id", "cycle", "setting_1", "setting_2", "setting_3"]
    assert COLUMN_NAMES[-1] == "s_21"


def test_subset_catalog() -> None:
    assert subset_info("FD001").train_engines == 100
    assert subset_info("FD002").test_engines == 259
    assert subset_info("FD004").conditions == 6
