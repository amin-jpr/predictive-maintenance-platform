import numpy as np
import pandas as pd
import pytest

from predictive_maintenance.data.labels import LabelError, add_test_labels, add_train_labels


def test_train_labels_and_cap() -> None:
    train = pd.DataFrame({"engine_id": [1, 1, 1, 2, 2, 2, 2, 2], "cycle": [1, 2, 3, 1, 2, 3, 4, 5]})
    labeled = add_train_labels(train, cap=2)
    assert labeled["rul_raw"].tolist() == [2, 1, 0, 4, 3, 2, 1, 0]
    assert labeled["rul"].tolist() == [2, 1, 0, 2, 2, 2, 1, 0]
    assert labeled["failure_cycle"].tolist() == [3, 3, 3, 5, 5, 5, 5, 5]


def test_test_labels_use_terminal_ground_truth() -> None:
    test = pd.DataFrame({"engine_id": [1, 1, 2, 2], "cycle": [1, 2, 1, 2]})
    labeled = add_test_labels(test, np.array([5, 7]), cap=2)
    assert labeled["inferred_failure_cycle"].tolist() == [7, 7, 9, 9]
    assert labeled["rul_raw"].tolist() == [6, 5, 8, 7]
    assert labeled["rul"].tolist() == [2, 2, 2, 2]
    terminal = labeled.groupby("engine_id").tail(1)["rul_raw"].tolist()
    assert terminal == [5, 7]


def test_test_rul_length_mismatch() -> None:
    test = pd.DataFrame({"engine_id": [1, 1], "cycle": [1, 2]})
    with pytest.raises(LabelError):
        add_test_labels(test, np.array([5, 6]))
