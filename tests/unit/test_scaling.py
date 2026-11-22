from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from predictive_maintenance.preprocessing.scaling import (
    ScalingError,
    fit_scaler,
    load_scaler_state,
    save_scaler_state,
    transform_features,
)


def _features() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "engine_id": [1, 1, 2, 2, 3, 3],
            "cycle": [1, 2, 1, 2, 1, 2],
            "split": [
                "train_fit",
                "train_fit",
                "train_fit",
                "train_fit",
                "validation",
                "validation",
            ],
            "f1": [1.0, 2.0, 3.0, 4.0, 100.0, 200.0],
            "f2": [10.0, 20.0, 30.0, 40.0, 1000.0, 2000.0],
        }
    )


def test_scaler_fits_only_train_fit() -> None:
    frame = _features()
    scaler, state = fit_scaler(frame, ["f1", "f2"], [1, 2])
    expected_mean = frame[frame["split"] == "train_fit"][["f1", "f2"]].to_numpy().mean(axis=0)
    np.testing.assert_allclose(state["mean"], expected_mean)
    assert state["n_samples_seen"] == 4
    changed = frame.copy()
    changed.loc[changed["split"] == "validation", ["f1", "f2"]] *= 10
    _, state_changed = fit_scaler(changed, ["f1", "f2"], [1, 2])
    assert state["mean"] == state_changed["mean"]
    assert state["scale"] == state_changed["scale"]


def test_scaler_json_roundtrip_and_transform(tmp_path: Path) -> None:
    frame = _features()
    scaler, state = fit_scaler(frame, ["f1", "f2"], [1, 2])
    path = save_scaler_state(tmp_path / "scaler.json", state)
    loaded, loaded_state = load_scaler_state(path)
    assert loaded_state["feature_names"] == ["f1", "f2"]
    original = transform_features(frame, scaler, ["f1", "f2"])
    restored = transform_features(frame, loaded, ["f1", "f2"])
    np.testing.assert_allclose(original[["f1", "f2"]], restored[["f1", "f2"]])


def test_feature_order_mismatch_rejected() -> None:
    frame = _features()
    scaler, _ = fit_scaler(frame, ["f1", "f2"], [1, 2])
    with pytest.raises(ScalingError):
        transform_features(frame, scaler, ["f2", "f1"])
