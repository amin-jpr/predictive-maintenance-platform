from predictive_maintenance.config import find_project_root


def test_no_deep_learning_or_xgboost_code() -> None:
    root = find_project_root()

    forbidden = [
        "XGBRegressor",
        "LSTM",
        "GRU",
        "Transformer",
        "import torch",
        "import tensorflow",
    ]

    offenders = []

    for path in (root / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")

        for token in forbidden:
            if token in text:
                offenders.append((str(path), token))

    assert not offenders, f"Out-of-scope Deep Learning or XGBoost code found: {offenders}"
