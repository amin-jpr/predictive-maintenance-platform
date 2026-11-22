"""CLI: generate the A4 engineering PDF report from verified artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

from predictive_maintenance.config import find_project_root
from predictive_maintenance.reporting.engineering_report import build_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate the Milestones 0-4 engineering PDF report."
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    root = find_project_root()
    output = (
        args.output
        or root.parent / "Predictive_Maintenance_Milestones_00_04_Engineering_Report.pdf"
    )
    path = build_report(root, output)
    print(f"PDF report generated: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
