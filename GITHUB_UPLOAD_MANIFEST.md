# GitHub upload manifest

Repository: **predictive-maintenance-platform**. Classification: **Required** = commit for a functional repository; **Optional** = commit after review; **Generated locally** = regenerate, do not commit by default; **Excluded** = must not be committed.

| Path | Classification | Notes |
|---|---|---|
| `README.md` | Required | Quick start, scope, data policy |
| `PROJECT_SPEC.md` | Required | Authoritative specification |
| `LICENSE` | Required | MIT for original code only; not NASA data |
| `pyproject.toml` | Required | Package, dependencies, tooling |
| `uv.lock` | Required | Exact dependency resolution |
| `.gitignore` | Required | Excludes data/secrets/caches/archives |
| `Makefile` | Required | Command shortcuts |
| `GITHUB_UPLOAD_MANIFEST.md` | Required | This manifest |
| `DELIVERABLES_MANIFEST.md` | Required | Delivery inventory |
| `configs/project.yaml` | Required | Project config |
| `configs/dataset.yaml` | Required | Source URL, pinned checksums, subset catalog |
| `configs/preprocessing.yaml` | Required | RUL cap, split, sensor selection, scaling, windows |
| `configs/features.yaml` | Required | Explicit feature definitions |
| `.github/workflows/ci.yml` | Required | CI definition; remote run pending push |
| `src/predictive_maintenance/` | Required | All package modules |
| `scripts/` | Required | Acquisition, validation, EDA, preprocessing, verification, notebooks, report, package, clean |
| `tests/unit/` | Required | Unit/leakage tests |
| `tests/integration/` | Required | Synthetic and real-data integration tests |
| `tests/helpers.py` | Required | Synthetic fixtures |
| `docs/` | Required | Specification, decisions, contracts, guides, progress, reports |
| `notebooks/01_dataset_overview.ipynb` | Required | Executed reproducible notebook |
| `notebooks/02_sensor_analysis.ipynb` | Required | Executed reproducible notebook |
| `notebooks/03_degradation_analysis.ipynb` | Required | Executed reproducible notebook |
| `notebooks/04_rul_analysis.ipynb` | Required | Executed reproducible notebook |
| `reports/eda/summary.md`, `summary.json` | Optional | Derived EDA summary; review before publication |
| `reports/eda/figures/*.png` | Optional | Derived plots; review before publication |
| `reports/eda/tables/*.csv` | Optional | Derived tables; review before publication |
| `reports/validation/integrity.{json,md}` | Optional | Integrity report; no raw values |
| `reports/preprocessing/summary.{json,md}` | Optional | Processing summary |
| `reports/preprocessing/verification.{json,md}` | Optional | Independent verification report |
| `reports/execution/*.txt`, `*.log`, `*.json` | Optional | Execution evidence; may contain local paths |
| `data/metadata/acquisition.json` | Optional | Provenance; review |
| `data/metadata/source_manifest.json` | Optional | Checksums/provenance; review |
| `data/metadata/checksums.sha256` | Optional | Raw file hashes; no raw bytes |
| `data/metadata/validation_checksums.sha256` | Optional | Raw file hashes |
| `data/metadata/split.json` | Optional | Engine IDs/split seed; review |
| `data/metadata/scaler.json` | Optional | Fitted normalization parameters; review |
| `data/metadata/feature_names.json` | Optional | Feature order |
| `data/metadata/preprocessing.json` | Optional | Processing config/fingerprints |
| `data/metadata/artifact_manifest.json` | Optional | Derived artifact hashes/shapes |
| `data/metadata/processed_checksums.sha256` | Optional | Derived artifact hashes |
| `data/raw/` | Generated locally / Excluded | NASA archive/originals; license unspecified |
| `data/interim/` | Generated locally / Excluded | Regenerate with preprocessing |
| `data/processed/` | Generated locally / Excluded | Regenerate cycle/features/scaled/sequences/windows |
| `.venv/`, caches, `__pycache__/` | Excluded | Environment/build artifacts |
| `.env`, credentials, keys | Excluded | Secrets |
| `*.zip` | Excluded | Delivery archives |
| PDF engineering report | Optional | Handoff document; can be stored outside repo or in releases |

## Required source modules
`src/predictive_maintenance/__init__.py`, `config.py`, `io.py`; `data/schema.py`, `loader.py`, `acquisition.py`, `validation.py`, `metadata.py`, `labels.py`, `splitting.py`, `windows.py`; `analysis/eda.py`; `preprocessing/scaling.py`, `features/engineering.py`, `preprocessing/pipeline.py`, `preprocessing/artifacts.py`; `reporting/engineering_report.py`.

## Required scripts
`check_environment.py`, `download_dataset.py`, `validate_dataset.py`, `run_eda.py`, `create_notebooks.py`, `run_notebooks.py`, `run_preprocessing.py`, `build_features.py`, `verify_artifacts.py`, `generate_report.py`, `package_delivery.py`, `clean_generated.py`.

## Publication rule
Do not use `git add .` until you have reviewed optional reports/metadata and confirmed no raw/processed data or secrets are staged. Prefer explicit paths as shown in `docs/GITHUB_UPLOAD_GUIDE.md`.
