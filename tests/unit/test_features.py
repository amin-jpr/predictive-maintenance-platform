import numpy as np
import pandas as pd

from predictive_maintenance.features.engineering import build_feature_frame


def _config() -> dict:
    return {
        "selected_settings": [],
        "selected_sensors": ["s_1", "s_2"],
        "rolling": {"windows": [3], "statistics": ["mean", "std"], "std_ddof": 1},
        "differences": {"orders": [1]},
    }


def _frame() -> pd.DataFrame:
    rows = []
    for engine in [1, 2]:
        for cycle in range(1, 11):
            rows.append(
                {
                    "engine_id": engine,
                    "cycle": cycle,
                    "s_1": float(cycle),
                    "s_2": float(2 * cycle + engine),
                }
            )
    return pd.DataFrame(rows)


def test_feature_values_and_warmup() -> None:
    features, names = build_feature_frame(_frame(), _config())
    assert len(names) == 8
    row = features[(features["engine_id"] == 1) & (features["cycle"] == 5)].iloc[0]
    assert row["s_1_roll_mean_3"] == 4.0
    assert np.isclose(row["s_1_roll_std_3"], 1.0)
    assert row["s_1_diff_1"] == 1.0
    first = features[(features["engine_id"] == 1) & (features["cycle"] == 1)].iloc[0]
    assert first["s_1_diff_1"] == 0.0
    assert first["s_1_roll_std_3"] == 0.0
    assert np.isfinite(features[names].to_numpy()).all()


def test_future_mutation_does_not_change_past_features() -> None:
    frame = _frame()
    baseline, names = build_feature_frame(frame, _config())
    changed = frame.copy()
    changed.loc[(changed["engine_id"] == 1) & (changed["cycle"] == 8), "s_1"] = 999.0
    mutated, _ = build_feature_frame(changed, _config())
    past_baseline = baseline[(baseline["engine_id"] == 1) & (baseline["cycle"] <= 7)].reset_index(
        drop=True
    )
    past_mutated = mutated[(mutated["engine_id"] == 1) & (mutated["cycle"] <= 7)].reset_index(
        drop=True
    )
    pd.testing.assert_frame_equal(past_baseline, past_mutated)


def test_cross_engine_isolation() -> None:
    frame = _frame()
    baseline, _ = build_feature_frame(frame, _config())
    changed = frame.copy()
    changed.loc[changed["engine_id"] == 2, "s_1"] += 1000.0
    mutated, _ = build_feature_frame(changed, _config())
    engine1_baseline = baseline[baseline["engine_id"] == 1].reset_index(drop=True)
    engine1_mutated = mutated[mutated["engine_id"] == 1].reset_index(drop=True)
    pd.testing.assert_frame_equal(engine1_baseline, engine1_mutated)
