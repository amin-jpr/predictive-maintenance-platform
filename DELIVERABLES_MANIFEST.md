# Deliverables manifest

Project: **Predictive Maintenance & Remaining Useful Life Prediction System**  
Repository: **predictive-maintenance-platform**  
Boundary: **Milestones 0–4 only; no predictive model training.**

## Primary downloadable deliverables
| Deliverable | Filename | Purpose |
|---|---|---|
| Complete project archive | `predictive-maintenance-platform-milestones-0-4.zip` | Source, configs, tests, docs, scripts, executed notebooks, reports, metadata, lockfile, GitHub handoff |
| Engineering PDF report | `Predictive_Maintenance_Milestones_00_04_Engineering_Report.pdf` | Comprehensive A4 technical handoff with verified results, diagrams, plots, commands, tests, GitHub instructions |
| GitHub upload guide | `docs/GITHUB_UPLOAD_GUIDE.md` | Step-by-step repository creation, local preparation, dataset policy, Git commands, quality checks |
| GitHub upload manifest | `GITHUB_UPLOAD_MANIFEST.md` | Required/optional/generated/excluded classification |
| Deliverables manifest | `DELIVERABLES_MANIFEST.md` | This inventory |
| Implementation progress | `docs/IMPLEMENTATION_PROGRESS.md` | Milestone status, commands, tests, issues, limitations |
| Acceptance checklist | `docs/ACCEPTANCE_CHECKLIST.md` | Final acceptance evidence |

## Archive contents
Included: `README.md`, `PROJECT_SPEC.md`, `LICENSE`, `pyproject.toml`, `uv.lock`, `.gitignore`, `Makefile`, `configs/`, `src/`, `tests/`, `scripts/`, `docs/`, `notebooks/`, `reports/`, `.github/`, `data/metadata/`, `GITHUB_UPLOAD_MANIFEST.md`, `DELIVERABLES_MANIFEST.md`, and the PDF report if present at packaging time.

Excluded by design: `.venv/`, Python/tool caches, `.git/`, temporary files, credentials, `*.zip`, `data/raw/`, `data/interim/`, and `data/processed/`. NASA benchmark license is unspecified; raw and derived data are regenerated locally rather than redistributed by default. Small provenance/checksum metadata is included for auditability.

## Source modules
| Area | Files | Purpose |
|---|---|---|
| Core | `config.py`, `io.py` | Config loading, fingerprints, safe IO, hashing |
| Data schema/ingestion | `data/schema.py`, `data/loader.py` | Exact 26-column contract, strict loading |
| Acquisition/provenance | `data/acquisition.py`, `data/metadata.py` | Download, safe extraction, checksums, manifests |
| Validation | `data/validation.py` | Structural/scientific integrity checks |
| Labels/splits/windows | `data/labels.py`, `data/splitting.py`, `data/windows.py` | RUL arithmetic, engine isolation, causal windows/sequences |
| EDA | `analysis/eda.py` | Executed descriptive analysis and plots |
| Preprocessing | `preprocessing/scaling.py`, `preprocessing/pipeline.py`, `preprocessing/artifacts.py` | Training-only scaler, orchestration, artifact manifests |
| Features | `features/engineering.py` | Causal rolling/difference/trend features |
| Reporting | `reporting/engineering_report.py` | PDF generation from verified artifacts |

## Configs
`configs/project.yaml`, `configs/dataset.yaml`, `configs/preprocessing.yaml`, `configs/features.yaml`.

## Scripts
`check_environment.py`, `download_dataset.py`, `validate_dataset.py`, `run_eda.py`, `create_notebooks.py`, `run_notebooks.py`, `run_preprocessing.py`, `build_features.py`, `verify_artifacts.py`, `generate_report.py`, `package_delivery.py`, `clean_generated.py`.

## Tests
Unit tests for config/IO, schema, loader, acquisition, validation, EDA, labels, splitting, scaling, features, windows, and no-training guard. Integration tests for synthetic end-to-end reproducibility and real FD001 validation/preprocessing verification.

## Reports and evidence
| Path | Purpose |
|---|---|
| `reports/validation/integrity.{json,md}` | Real FD001 integrity checks |
| `reports/eda/summary.{json,md}` | EDA summary |
| `reports/eda/figures/` | 10 actual generated plots |
| `reports/eda/tables/` | 11 actual generated tables |
| `reports/preprocessing/summary.{json,md}` | Processing/feature/window summary |
| `reports/preprocessing/verification.{json,md}` | Independent artifact verification |
| `reports/execution/` | Command logs, environment, pytest results, download probe |
| `data/metadata/` | Acquisition/source manifests, checksums, split/scaler/feature/artifact metadata |

## Generated local data (not redistributed by default)
`data/raw/`, `data/interim/labeled/`, `data/processed/cycle_level/`, `data/processed/labels/`, `data/processed/features/`, `data/processed/scaled/`, `data/processed/sequences/`, `data/processed/windows/`, `data/processed/window_index.csv`. Regenerate with the documented commands.

## Recommended download order
1. Download `predictive-maintenance-platform-milestones-0-4.zip` and extract it.
2. Download the PDF engineering report for the full handoff narrative.
3. Read `docs/GITHUB_UPLOAD_GUIDE.md` and `GITHUB_UPLOAD_MANIFEST.md` before publishing.
4. Run `uv sync --locked` and the documented data pipeline locally to regenerate FD001 data products.

## Final confirmation
Milestones 0–4 have been completed. The dataset acquisition, validation, exploratory analysis, preprocessing, and feature engineering infrastructure is prepared. No Machine Learning or Deep Learning model has been trained. Model development begins in Milestone 5.
