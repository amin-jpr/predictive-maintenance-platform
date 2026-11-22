# Development environment and actual tested versions

## Reproducible install
```bash
uv sync --locked
uv run python scripts/check_environment.py
```
The lockfile is the authoritative dependency resolution. The project supports Python >=3.11,<3.14. CPU only; no GPU framework is required.

## Versions observed in the execution workspace
Recorded from `reports/execution/environment.txt` after `uv sync --locked`:

| Component | Version |
|---|---|
| Python | 3.13.16 |
| uv | 0.13.7 |
| Git | 2.47.3 |
| numpy | 2.5.4 |
| pandas | 2.3.3 |
| matplotlib | 3.11.2 |
| seaborn | 0.13.2 |
| scikit-learn | 1.9.1 |
| PyYAML | 6.0.3 |
| pyarrow | 23.0.1 |
| requests | 2.34.2 |
| pytest | 8.4.2 |
| ruff | 0.17.4 |
| mypy | 1.20.2 |
| nbformat | 5.11.1 |
| nbclient | 0.11.0 |
| jupyterlab | 4.6.6 |
| reportlab | 4.5.1 |

Platform: Linux x86_64 sandbox. The sandbox reported approximately 1.9 GiB total RAM, which is less than the user's 8 GB target; this makes successful FD001 execution a conservative compatibility check, not a formal peak-memory certification.

## Tooling
- Ruff: lint and format (`src`, `tests`, `scripts`).
- mypy: typed package checks; third-party plotting/sklearn/reportlab imports use missing-import overrides where stubs are unavailable.
- pytest: strict markers; `data_required` tests need real FD001 files and are skipped in CI when data are absent.
- GitHub Actions: Python 3.11/3.12/3.13 matrix, locked install, lint, format check, mypy, non-data tests. Remote execution is pending until the user pushes.

## Commands
```bash
make install      # uv sync --locked
make lint         # ruff check + format --check
make typecheck    # mypy
make test         # pytest -m "not data_required"
make test-all     # pytest (includes real-data tests when present)
```
