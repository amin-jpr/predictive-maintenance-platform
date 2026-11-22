"""Create the Milestone 5 delivery ZIP.

Includes source, configs, scripts, tests, docs, reports, experiment records, approved
model artifacts, and both PDF reports. Excludes datasets (NASA license unspecified),
environments, caches, and ZIPs. Deterministic entries (fixed timestamps) so the archive
hash is stable for a given content set.
"""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

from predictive_maintenance.config import find_project_root
from predictive_maintenance.io import sha256_file

INCLUDE_FILES = [
    "README.md",
    "PROJECT_SPEC.md",
    "LICENSE",
    "pyproject.toml",
    "uv.lock",
    ".gitignore",
    "Makefile",
    "GITHUB_UPLOAD_MANIFEST.md",
    "DELIVERABLES_MANIFEST.md",
    "GITHUB_UPLOAD_MANIFEST_MILESTONE_05.md",
    "DELIVERABLES_MANIFEST_MILESTONE_05.md",
]
INCLUDE_DIRS = [
    "configs",
    "src",
    "tests",
    "scripts",
    "docs",
    "notebooks",
    "reports",
    ".github",
    "data/metadata",
    "experiments/milestone_05",
    "artifacts/classical_ml",
]
EXCLUDE_PARTS = {
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".ipynb_checkpoints",
    ".git",
    "node_modules",
}
PARENT_FILES = [
    "Predictive_Maintenance_Milestone_05_Classical_ML_Report.pdf",
    "Predictive_Maintenance_Milestones_00_04_Engineering_Report.pdf",
]
OUTPUT_NAME = "predictive-maintenance-platform-milestone-05.zip"


def _excluded(path: Path) -> bool:
    return any(part in EXCLUDE_PARTS for part in path.parts) or path.suffix == ".zip"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Package Milestone 5 deliverables into a ZIP archive."
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    root = find_project_root()
    output = args.output or root.parent / OUTPUT_NAME
    files: list[Path] = []
    for name in INCLUDE_FILES:
        path = root / name
        if path.is_file():
            files.append(path)
    for directory in INCLUDE_DIRS:
        base = root / directory
        if base.exists():
            files.extend(
                path
                for path in sorted(base.rglob("*"))
                if path.is_file() and not _excluded(path.relative_to(root))
            )
    count = 0
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(set(files)):
            arcname = Path("predictive-maintenance-platform") / path.relative_to(root)
            info = zipfile.ZipInfo(str(arcname), date_time=(2026, 11, 21, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
            count += 1
        for name in PARENT_FILES:
            path = root.parent / name
            if path.is_file():
                info = zipfile.ZipInfo(name, date_time=(2026, 11, 21, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, path.read_bytes())
                count += 1
    digest = sha256_file(output)
    size = output.stat().st_size
    print(f"ZIP: {output}")
    print(f"entries: {count}")
    print(f"size_bytes: {size}")
    print(f"sha256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
