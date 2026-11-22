"""CLI: generate the Milestone 5 classical ML PDF report from actual experiment records."""

from __future__ import annotations

import argparse
from pathlib import Path

from predictive_maintenance.config import find_project_root
from predictive_maintenance.reporting.milestone5_report import PDF_NAME, build_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the Milestone 5 engineering PDF report.")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    root = find_project_root()
    output = args.output or root.parent / PDF_NAME
    path = build_report(root, output)
    print(f"PDF report generated: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
