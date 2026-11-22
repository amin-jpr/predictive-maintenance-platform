"""CLI: prepare validated cycle-level data, RUL labels, and engine splits."""

from __future__ import annotations

import argparse

from predictive_maintenance.config import find_project_root
from predictive_maintenance.preprocessing.pipeline import prepare_cycle_level


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare C-MAPSS cycle-level data and labels (no model training)."
    )
    parser.add_argument("--subset", default="FD001")
    args = parser.parse_args(argv)
    root = find_project_root()
    result = prepare_cycle_level(root, args.subset)
    print(f"Cycle-level preparation complete for {args.subset}")
    print(f"RUL cap: {result['cap']}")
    print(
        f"Split: {result['split']['n_train_fit']} fit / {result['split']['n_validation']} validation"
    )
    print(f"Counts: {result['counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
