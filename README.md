# Predictive Maintenance & Remaining Useful Life Prediction System

**Repository:** `predictive-maintenance-platform`  
**Scope:** Milestones 0–5. CPU-first, reproducible data preparation and classical ML baselines for NASA C-MAPSS FD001.

> Classical ML baselines (Milestone 5) are trained and evaluated. No Deep Learning model exists in this repository; Milestone 6 is explicitly outside the current scope.

## What this project does
- Acquires and verifies the official NASA C-MAPSS benchmark archive.
- Validates the original FD001 train/test/RUL files without modifying raw data.
- Generates executed EDA plots, tables, and reproducible notebooks.
- Constructs mathematically correct training/test RUL labels.
- Creates deterministic engine-level train/validation splits.
- Fits a **training-only StandardScaler** and builds causal rolling/difference features.
- Produces documented cycle-level, sequence, and sliding-window datasets with checksums.
- Tests leakage prevention, temporal boundaries, schemas, and reproducibility.
- Trains and fairly compares classical RUL baselines (median, cycle-trend, linear, Random Forest, HistGradientBoosting) on the engine-level validation split, with MAE/RMSE/NASA score, artifacts, and experiment records.

## Quick start
Requires Python 3.11–3.13 and [uv](https://docs.astral.sh/uv/). Run commands from the repository root.

```bash
uv sync --locked
uv run python scripts/check_environment.py
uv run python scripts/download_dataset.py --subset FD001
uv run python scripts/validate_dataset.py --subset FD001
uv run python scripts/run_eda.py --subset FD001
uv run python scripts/run_preprocessing.py --subset FD001
uv run python scripts/build_features.py --subset FD001
uv run python scripts/verify_artifacts.py --subset FD001
uv run python scripts/train.py
uv run python scripts/evaluate.py
uv run pytest
```

`make help` lists shortcuts. CI runs lint/type/unit checks without downloading NASA data. Full acceptance requires the real-data commands above.

## Initial technical defaults
| Setting | Value |
|---|---|
| Initial subset | FD001 |
| RUL cap | 125 cycles |
| Window length | 30 cycles |
| Split seed / validation fraction | 42 / 0.20 |
| Scaler | Global StandardScaler, fit on `train_fit` engines only |
| Initial features | 92 causal features (current values, rolling mean/std at 5/10, first differences) |

## Data policy
The NASA benchmark catalog says **license not specified**. Raw NASA files and derived data products are **not committed or redistributed by default**. Use the acquisition script and regenerate locally. Original project code is MIT-licensed; that does not relicense NASA data.

## Key documents
- [Project specification](PROJECT_SPEC.md)
- [Technical decisions](docs/TECHNICAL_DECISIONS.md)
- [Problem formulation](docs/PROBLEM_FORMULATION.md)
- [Data contracts](docs/DATA_CONTRACTS.md)
- [Feature engineering](docs/FEATURE_ENGINEERING.md)
- [Implementation progress](docs/IMPLEMENTATION_PROGRESS.md)
- [GitHub upload guide](docs/GITHUB_UPLOAD_GUIDE.md)
- [GitHub upload manifest](GITHUB_UPLOAD_MANIFEST.md)
- [Deliverables manifest](DELIVERABLES_MANIFEST.md)
- [Milestone 5 methodology](docs/MILESTONE_5_METHODOLOGY.md)
- [Milestone 5 model comparison](docs/MILESTONE_5_MODEL_COMPARISON.md)
- [Milestone 5 data leakage audit](docs/MILESTONE_5_DATA_LEAKAGE_AUDIT.md)
- [Milestone 5 GitHub upload guide](docs/MILESTONE_5_GITHUB_UPLOAD_GUIDE.md)
- [Milestone 5 upload manifest](GITHUB_UPLOAD_MANIFEST_MILESTONE_05.md)
- [Milestone 5 deliverables manifest](DELIVERABLES_MANIFEST_MILESTONE_05.md)

## Status
Milestones 0–5 are complete and verified on real FD001 data. Final full test suite: **72 passed**. Independent artifact verification (M4): **PASS**. Milestone 5 validation results (20 held-out engines, 3,852 observations, seed 42): median baseline MAE 36.81 · cycle-trend 19.47 · linear 16.60 (best NASA score 38,748) · **Random Forest 12.33 (best MAE/RMSE)** · HistGradientBoosting 12.55 — see `reports/tables/baseline_comparison.csv`. Official NASA Test set remains untouched for the final project stage. GitHub push and user-local installation are not performed by this workspace.

> MILESTONE 5 COMPLETED — CLASSICAL MACHINE LEARNING BASELINES. MILESTONE 6 — DEEP LEARNING MODELS — HAS NOT BEEN STARTED.
