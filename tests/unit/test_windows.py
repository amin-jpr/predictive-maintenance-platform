import numpy as np
import pandas as pd

from predictive_maintenance.data.windows import engine_window_arrays


def _frame(length: int = 10) -> pd.DataFrame:
    cycles = np.arange(1, length + 1)
    return pd.DataFrame(
        {
            "engine_id": np.ones(length, dtype=int),
            "cycle": cycles,
            "f1": cycles.astype(float),
            "f2": (2 * cycles).astype(float),
            "rul": 100 - cycles,
            "rul_raw": 100 - cycles,
        }
    )


def test_window_dimensions_boundaries_and_targets() -> None:
    arrays = engine_window_arrays(_frame(), ["f1", "f2"], window_length=3)
    assert arrays is not None
    assert arrays["X"].shape == (8, 3, 2)
    assert arrays["start_cycle"].tolist() == list(range(1, 9))
    assert arrays["end_cycle"].tolist() == list(range(3, 11))
    assert arrays["y"].tolist() == (100 - np.arange(3, 11)).tolist()
    np.testing.assert_allclose(arrays["X"][0, :, 0], [1, 2, 3])


def test_future_mutation_does_not_change_earlier_windows() -> None:
    frame = _frame()
    baseline = engine_window_arrays(frame, ["f1", "f2"], 3)
    changed = frame.copy()
    changed.loc[changed["cycle"] == 10, "f1"] = 999.0
    mutated = engine_window_arrays(changed, ["f1", "f2"], 3)
    assert baseline is not None and mutated is not None
    np.testing.assert_allclose(baseline["X"][:-1], mutated["X"][:-1])


def test_short_engine_and_stride() -> None:
    assert engine_window_arrays(_frame(2), ["f1", "f2"], 3) is None
    arrays = engine_window_arrays(_frame(10), ["f1", "f2"], 3, stride=2)
    assert arrays is not None
    assert arrays["end_cycle"].tolist() == [3, 5, 7, 9]
