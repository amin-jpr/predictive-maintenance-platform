"""Print the actual Python/package environment and project paths."""

from __future__ import annotations

import importlib.metadata
import platform
import sys

from predictive_maintenance.config import find_project_root


def main() -> None:
    root = find_project_root()
    print("Project root:", root)
    print("Python:", sys.version.replace("\n", " "))
    print("Platform:", platform.platform())
    for package in [
        "predictive-maintenance-platform",
        "numpy",
        "pandas",
        "matplotlib",
        "seaborn",
        "scikit-learn",
        "PyYAML",
        "pyarrow",
        "requests",
        "pytest",
        "ruff",
        "mypy",
        "nbformat",
        "nbclient",
        "jupyterlab",
        "reportlab",
    ]:
        try:
            print(f"{package}: {importlib.metadata.version(package)}")
        except importlib.metadata.PackageNotFoundError:
            print(f"{package}: NOT INSTALLED")
    for relative in ["configs", "src/predictive_maintenance", "tests", "scripts", "docs"]:
        print(f"{relative}: {'present' if (root / relative).exists() else 'MISSING'}")


if __name__ == "__main__":
    main()
