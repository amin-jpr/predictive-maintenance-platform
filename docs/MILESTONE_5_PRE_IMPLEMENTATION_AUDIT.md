# Milestone 5 — Pre-Implementation Audit

Date: 2026-11-07 (workspace inspection, Arena.ai sandbox, Linux)
Project root: `/home/user/predictive-maintenance-platform`
Repository name: `predictive-maintenance-platform`

## 1. Blueprint availability

The task references an uploaded file named `Predictive Maintenance.txt` as the authoritative
blueprint. **That file was not found anywhere in the workspace** (searched `/home/user` to depth 4
and the full filesystem to depth 4). The Milestone 5 specification embedded in the task prompt
itself is therefore used as the source of truth for this milestone. No blueprint content was
invented; every requirement implemented here traces to the prompt's Milestone 5 sections
(objective, file structure, model order, metrics, Definition of Done).

## 2. Existing project structure (verified by inspection)

```text
predictive-maintenance-platform/
├── PROJECT_SPEC.md, README.md, LICENSE, Makefile, pyproject.toml, uv.lock, .gitignore
├── .github/workflows/ci.yml
├── configs/{project,dataset,preprocessing,features}.yaml
├── data/{raw,interim,processed,metadata}/          (generated, git-ignored)
├── docs/ (16 Markdown files, Milestones 0–4)
├── notebooks/01–04*.ipynb (executed)
├── reports/{eda,execution,figures,preprocessing,validation}/
├── scripts/ (12 scripts, Milestones 0–4)
├── src/predictive_maintenance/
│   ├── config.py, io.py
│   ├── data/{schema,loader,metadata,acquisition,validation,labels,splitting,windows}.py
│   ├── analysis/eda.py
│   ├── preprocessing/{scaling,artifacts,pipeline}.py
│   ├── features/engineering.py
│   └── reporting/engineering_report.py
└── tests/{unit (13 files), integration (3 files)} — 39 tests total
```

No `models/` or `evaluation/` package exists yet. No `configs/model_*.yaml` exists yet.
No `scripts/train.py` or `scripts/evaluate.py` exists yet. No `artifacts/` or `experiments/`
directory exists yet.

## 3. Milestone 4 outputs — verified present and valid

| Artifact | Location | Verified content |
|---|---|---|
| Scaled features (train_fit) | `data/processed/scaled/train_fit.parquet` | 16,779 rows × 95 cols (engine_id, cycle, split + **92 features**), 0 NaN, 0 inf |
| Scaled features (validation) | `data/processed/scaled/validation.parquet` | 3,852 rows × 95 cols, 0 NaN, 0 inf |
| Scaled features (official test) | `data/processed/scaled/test.parquet` | 13,096 rows × 95 cols — **not used in Milestone 5** |
| Labels (train_fit) | `data/processed/labels/train_fit.csv` | 16,779 rows; cols engine_id, cycle, rul_raw, **rul**, split, subset, endpoint_cycle |
| Labels (validation) | `data/processed/labels/validation.csv` | 3,852 rows, same schema |
| Labels (official test) | `data/processed/labels/test.csv` | 13,096 rows — **not used in Milestone 5** |
| Feature names | `data/metadata/feature_names.json` | 92 features, float32, order recorded |
| Split record | `data/metadata/split.json` | engine_shuffle, seed 42, 80 fit / 20 validation engines |
| Scaler record | `data/metadata/scaler.json` | StandardScaler fit on train_fit only (80 engines, 16,779 rows), sklearn 1.9.1 |
| Preprocessing record | `data/metadata/preprocessing.json` | cap 125, full config fingerprints |

Row alignment between scaled features and labels was verified programmatically for both
train_fit and validation: identical row counts and identical (engine_id, cycle) key sequences.
The target column `rul` is **not** among the 92 features (verified against
`feature_names.json`).

### Train/Validation engine separation (from `data/metadata/split.json`)

- train_fit (80 engines): 1, 2, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 23,
  24, 27, 29, 30, 31, 32, 33, 35, 36, 37, 38, 39, 40, 41, 42, 44, 45, 46, 47, 48, 49, 50, 54,
  55, 56, 58, 59, 61, 63, 64, 65, 66, 67, 68, 69, 70, 71, 73, 74, 75, 76, 77, 78, 79, 80, 81,
  83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 94, 95, 96, 97, 99
- validation (20 engines): 3, 5, 19, 22, 25, 26, 28, 34, 43, 51, 52, 53, 57, 60, 62, 72, 82, 93,
  98, 100
- Intersection: **empty** (verified). Official test engine IDs (1–100) live in a separate
  namespace/file and are never loaded by Milestone 5 code.

### Target statistics (capped RUL, cycles)

- train_fit: mean 87.45, median 104, min 0, max 125, fraction at cap 0.404
- validation: mean 84.11, median 96, min 0, max 125, fraction at cap 0.351

### Feature definition (from `configs/features.yaml` + `feature_names.json`)

92 causal features: 2 current settings (setting_1, setting_2) + 15 current sensors +
30 rolling means (windows 5/10) + 30 rolling stds + 15 first differences. All computed with
`min_periods=1` warmup (TD-024), scaled by the train_fit-fitted StandardScaler. The scaled
tables are the single approved Milestone 4 feature definition; Milestone 5 consumes them
unchanged so every model sees identical inputs.

## 4. Prediction unit decision

One training example = **one engine at one observation cycle**, represented by the 92
cycle-level scaled features available at that cycle (current settings/sensors + causal
rolling statistics + first differences). Engine ID, cycle, split, and target are identifiers/
metadata, never inputs. The 30-cycle sliding windows from Milestone 4 are sequence inputs
reserved for Milestone 6 (deep learning) and are **not** used by these tabular classical
models; this is documented, not an omission.

## 5. Dependencies (verified after `uv sync --locked`)

Python 3.13.16 (venv), scikit-learn **1.9.1**, numpy 2.5.4, pandas 2.3.3, matplotlib 3.11.2,
seaborn 0.13.2, pyarrow 23.0.1, PyYAML 6.0.3, pytest 8.4.2, ruff 0.17.4, mypy 1.20.2,
reportlab 4.5.1, joblib (bundled with scikit-learn). `uv` 0.13.9 reinstalled via pip and
`uv sync --locked` re-executed successfully (129 locked packages). **No new dependency is
required for Milestone 5**: scikit-learn and joblib are already present, satisfying the
blueprint's `uv add scikit-learn` step (already satisfied; lockfile unchanged).

**XGBoost decision:** not installed and not added. The required set (median baseline, simple
baseline, Random Forest, HistGradientBoosting) plus the optional interpretable Linear
Regression already spans the bias–variance spectrum the milestone must demonstrate.
Adding XGBoost would introduce a new dependency and maintenance surface without changing
the scientific question of Milestone 5. Documented as a deliberate, justified exclusion.

## 6. Existing tests and status

Baseline run before any Milestone 5 change: `uv run pytest -m "not data_required"` →
**37 passed, 2 deselected**. Full suite (with real FD001 data present): 39 passed
(Milestone 4 record).

**Required test change:** `tests/unit/test_no_training.py` scans `src/` for forbidden tokens
including `RandomForestRegressor`, `LinearRegression`, `sklearn.ensemble`,
`sklearn.linear_model`, and `model.fit(`. That guard enforced the Milestones 0–4
no-training boundary and **must be updated for Milestone 5**, where classical model training
is the assignment. It will be replaced by a deep-learning guard (forbidding LSTM/GRU/
Transformer/torch/tensorflow/keras tokens) so the Milestone 6 boundary remains enforced.
This is a documented, intentional change — not a silent weakening.

## 7. Git status — environment limitation

`.git/` exists but is a **skeleton**: it contains only `HEAD`, `description`, `hooks/`,
and `info/` — there are no `objects/`, `refs/`, `index`, or config files. Every git command
fails with `fatal: not a git repository`. Consequences:

- No commits exist (consistent with the Milestone 4 record: "no commits yet").
- No `git status`/`git add`/`git commit` can be executed in this workspace.
- The user must run `git init` (or clone) on their own machine and apply the exact commands
  in `docs/MILESTONE_5_GITHUB_UPLOAD_GUIDE.md`. No push is claimed or implied.

## 8. Missing components required for Milestone 5

1. `src/predictive_maintenance/models/` — base, baseline, random_forest, gradient_boosting
   (+ linear, dataset loader).
2. `src/predictive_maintenance/evaluation/metrics.py` — MAE, RMSE, NASA/PHM08 score,
   diagnostics.
3. `configs/model_rf.yaml`, `model_hgb.yaml`, `model_baseline.yaml`, `model_linear.yaml`,
   `model_experiment.yaml`.
4. `scripts/train.py`, `scripts/evaluate.py`.
5. Tests: `test_metrics`, `test_baseline`, `test_random_forest`, `test_gradient_boosting`,
   `test_model_serialization`, integration `test_classical_ml_pipeline`; update
   `test_no_training.py` → deep-learning guard.
6. Outputs: `reports/tables/baseline_comparison.csv`, `reports/figures/*.png`,
   `artifacts/classical_ml/`, `experiments/milestone_05/`.
7. Documentation, PDF report, GitHub guide, manifests, ZIP package.

## 9. Risks and inconsistencies discovered

| # | Finding | Impact / mitigation |
|---|---|---|
| R1 | Blueprint file `Predictive Maintenance.txt` absent from workspace | Prompt text used as spec; recorded here. |
| R2 | `.git` skeleton broken; git unusable in workspace | No commits/push claimed; exact user commands provided. |
| R3 | `test_no_training.py` forbids the very models Milestone 5 requires | Replaced with deep-learning-only guard; documented. |
| R4 | Random Forest artifact size unknown (100–200 trees × 16,779 rows) | Conservative config (100 trees); size measured after training; joblib compression; GitHub guidance adjusted to measured size. |
| R5 | `configs/project.yaml` still declares `milestone_boundary: 4` and `no_predictive_training: true` | Updated to boundary 5 with Milestone 5 entry; `no_predictive_training` flag replaced by explicit scope fields. |
| R6 | `pyproject.toml` description says "Milestones 0-4; no predictive model training" | Description updated to reflect Milestone 5 classical baselines (deep learning still excluded). |
| R7 | Official test files exist in the same directories as train/validation files | Milestone 5 loader reads only `train_fit`/`validation` paths; a test asserts the test split is never loaded. |
| R8 | Scaled (not raw) features are the M4 product | All models consume the identical scaled matrix — fair comparison; tree models are scale-invariant, linear model benefits. Documented. |

## 10. Audit conclusion

Milestone 4 outputs are **complete and valid** as Milestone 5 inputs: 92 leakage-controlled
features, capped RUL target, engine-disjoint 80/20 split, train-only scaler. No data
regeneration is required. Implementation proceeds on the existing architecture without
redesign. No Milestone 6 (deep learning) component will be created.
