"""Execute EDA notebooks from clean kernels and save actual outputs."""

from __future__ import annotations

import argparse

import nbformat
from nbclient import NotebookClient

from predictive_maintenance.config import find_project_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute project notebooks reproducibly.")
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args(argv)
    root = find_project_root()
    notebooks = sorted((root / "notebooks").glob("*.ipynb"))
    if not notebooks:
        raise FileNotFoundError("No notebooks found; run scripts/create_notebooks.py first")
    for path in notebooks:
        print(f"Executing {path.name}", flush=True)
        nb = nbformat.read(path, as_version=4)
        client = NotebookClient(
            nb,
            timeout=args.timeout,
            kernel_name="python3",
            resources={"metadata": {"path": str(root)}},
        )
        client.execute()
        nbformat.write(nb, path)
        print(f"Saved executed outputs: {path.name}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
