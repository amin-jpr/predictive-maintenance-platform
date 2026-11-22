import pytest

from predictive_maintenance.data.splitting import SplitError, assert_split_isolation, engine_split


def test_engine_split_isolation_and_determinism() -> None:
    ids = list(range(1, 101))
    split = engine_split(ids, validation_fraction=0.2, seed=42)
    assert split["n_train_fit"] == 80
    assert split["n_validation"] == 20
    assert set(split["train_fit"]).isdisjoint(split["validation"])
    assert set(split["train_fit"]) | set(split["validation"]) == set(ids)
    assert engine_split(ids, 0.2, 42) == split


def test_split_isolation_rejects_overlap() -> None:
    with pytest.raises(SplitError):
        assert_split_isolation([1, 2], [2, 3], [1, 2, 3])


def test_split_requires_two_engines() -> None:
    with pytest.raises(SplitError):
        engine_split([1])
