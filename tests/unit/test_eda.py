import numpy as np
import pandas as pd

from predictive_maintenance.analysis.eda import (
    dataset_overview,
    degradation_summary,
    rul_analysis,
    sensor_statistics,
)
from predictive_maintenance.data.schema import COLUMN_NAMES


def _frame(n_engines: int = 3, length: int = 40) -> pd.DataFrame:
    rows = []
    for engine in range(1, n_engines + 1):
        for cycle in range(1, length + 1):
            row = [engine, cycle, 0.0, 0.0, 100.0]
            row += [500.0 + i + (cycle if i == 2 else 0) for i in range(21)]
            rows.append(row)
    return pd.DataFrame(rows, columns=COLUMN_NAMES)


def test_overview_and_sensor_stats() -> None:
    train = _frame()
    test = _frame(2, 20)
    rul = np.array([5, 6])
    overview = dataset_overview(train, test, rul)
    assert overview["train"]["engines"] == 3
    assert overview["n_sensors"] == 21
    stats = sensor_statistics(train)
    assert stats["constant"].sum() >= 1
    assert stats["missing"].sum() == 0


def test_degradation_and_rul() -> None:
    train = _frame()
    test = _frame(2, 20)
    rul = np.array([5, 6])
    summary, per_engine = degradation_summary(train, sensors=["s_3"])
    assert len(per_engine) == 3
    assert summary.iloc[0]["late_minus_early_mean"] > 0
    result = rul_analysis(train, test, rul, cap=10)
    assert result["stats"]["train_raw_min"] == 0
    assert result["stats"]["fraction_capped"] > 0
    assert result["test_terminal"]["terminal_rul"].tolist() == [5, 6]
