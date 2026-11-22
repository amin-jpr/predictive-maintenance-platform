"""Milestone 5 scope guard: deep learning (Milestone 6) must not appear in src/.

Replaces the Milestones 0-4 ``test_no_training.py`` guard, which forbade all predictive
training. Classical ML training is now the assignment; deep learning remains strictly
out of scope until Milestone 6.
"""

from predictive_maintenance.config import find_project_root


def test_no_deep_learning_code() -> None:
    root = find_project_root()
    forbidden = [
        "LSTM",
        "GRU",
        "Transformer",
        "import torch",
        "from torch",
        "import tensorflow",
        "from tensorflow",
        "keras",
        "PyTorch",
    ]
    offenders = []
    for path in (root / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append((str(path), token))
    assert not offenders, f"Deep learning code found (Milestone 6 scope): {offenders}"
