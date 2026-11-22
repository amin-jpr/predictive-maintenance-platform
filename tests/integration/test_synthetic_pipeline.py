from pathlib import Path

import pytest
from tests.helpers import minimal_config, write_synthetic_subset

from predictive_maintenance.config import find_project_root, load_config
from predictive_maintenance.io import sha256_file
from predictive_maintenance.preprocessing.pipeline import (
    build_feature_products,
    prepare_cycle_level,
)


@pytest.mark.integration
def test_synthetic_end_to_end_and_reproducibility(tmp_path: Path) -> None:
    real_root = find_project_root()
    preproc = load_config("preprocessing", real_root)
    features = load_config("features", real_root)
    dataset = minimal_config()
    write_synthetic_subset(tmp_path, n_train=100, n_test=100, train_len=40, test_len=35)
    prepared = prepare_cycle_level(tmp_path, "FD001", preproc, dataset, features)
    assert prepared["split"]["n_train_fit"] == 80
    summary = build_feature_products(tmp_path, "FD001", preproc, features, dataset)
    assert summary["n_features"] == 92
    assert summary["window_counts"] == {"train_fit": 880, "validation": 220, "test": 600}
    assert summary["no_predictive_model_trained"] is True
    window_file = tmp_path / "data/processed/windows/train_fit/engine_0001.npz"
    first_hash = sha256_file(window_file)
    build_feature_products(tmp_path, "FD001", preproc, features, dataset)
    assert sha256_file(window_file) == first_hash
    assert (tmp_path / "data/metadata/artifact_manifest.json").is_file()
    assert (tmp_path / "data/metadata/scaler.json").is_file()
