"""Create the delivery ZIP, excluding raw/processed data, environments, caches, and secrets."""

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
PDF_NAME = "Predictive_Maintenance_Milestones_00_04_Engineering_Report.pdf"


def _excluded(path: Path) -> bool:
    return any(part in EXCLUDE_PARTS for part in path.parts) or path.suffix == ".zip"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Package project deliverables into a ZIP archive.")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    root = find_project_root()
    output = args.output or root.parent / "predictive-maintenance-platform-milestones-0-4.zip"
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
    pdf = root.parent / PDF_NAME
    count = 0
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(set(files)):
            arcname = Path("predictive-maintenance-platform") / path.relative_to(root)
            info = zipfile.ZipInfo(str(arcname), date_time=(2026, 11, 7, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
            count += 1
        if pdf.is_file():
            info = zipfile.ZipInfo(PDF_NAME, date_time=(2026, 11, 7, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, pdf.read_bytes())
            count += 1
    print(f"Created {output}")
    print(f"Files: {count}; bytes: {output.stat().st_size}; SHA-256: {sha256_file(output)}")
    print("Excluded: raw/interim/processed data, .venv, caches, .git, secrets, ZIP archives.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
