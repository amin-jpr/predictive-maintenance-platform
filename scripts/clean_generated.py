"""Remove generated data/reports while preserving raw NASA files and source code."""

from __future__ import annotations

import argparse
import shutil

from predictive_maintenance.config import find_project_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Clean generated artifacts (raw data is preserved)."
    )
    parser.add_argument(
        "--include-reports",
        action="store_true",
        help="Also remove generated EDA/preprocessing/validation reports",
    )
    parser.add_argument("--yes", action="store_true", help="Do not prompt for confirmation")
    args = parser.parse_args(argv)
    root = find_project_root()
    targets = [root / "data/interim", root / "data/processed", root / "data/metadata"]
    if args.include_reports:
        targets.extend(
            [root / "reports/eda", root / "reports/preprocessing", root / "reports/validation"]
        )
    existing = [path for path in targets if path.exists()]
    if not existing:
        print("No generated targets found.")
        return 0
    print("Will remove:")
    for path in existing:
        print(f"  {path}")
    if not args.yes:
        answer = input("Proceed? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            return 1
    for path in existing:
        shutil.rmtree(path)
    print("Clean complete. Raw data under data/raw was preserved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
