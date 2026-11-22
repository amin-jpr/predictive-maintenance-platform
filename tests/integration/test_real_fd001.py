import pytest

from predictive_maintenance.config import find_project_root
from predictive_maintenance.data.loader import load_rul, load_test, load_train
from predictive_maintenance.data.validation import validate_subset


@pytest.mark.data_required
@pytest.mark.integration
def test_real_fd001_validation_and_loading() -> None:
    root = find_project_root()
    if not (root / "data/raw/cmaps/train_FD001.txt").is_file():
        pytest.skip("FD001 raw files not present")
    report = validate_subset(root, "FD001")
    assert report["status"] == "PASS"
    train = load_train(root, "FD001")
    test = load_test(root, "FD001")
    rul = load_rul(root, "FD001")
    assert train.shape == (20631, 26)
    assert test.shape == (13096, 26)
    assert rul.shape == (100,)
    assert train["engine_id"].nunique() == 100
    assert test["engine_id"].nunique() == 100
