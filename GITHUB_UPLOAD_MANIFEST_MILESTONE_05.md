# GitHub Upload Manifest — Milestone 5

Repository: **predictive-maintenance-platform** · Milestone 5 (Classical ML Baselines) ·
2026-11-21. Status legend: **New** (created in M5), **Modified** (existing file changed),
**Generated** (produced by executed runs), **Existing** (untouched M0–M4 file).
Action legend: **Commit** (stage & push), **Keep local** (never upload).

## A. Required source files

| File Path | Status | GitHub Action | Reason |
|---|---|---|---|
| src/predictive_maintenance/models/__init__.py | New | Commit | Public model API (build_*/train_model/predict_model/save/load) |
| src/predictive_maintenance/models/base.py | New | Commit | TrainedModel record; train/predict/serialize core |
| src/predictive_maintenance/models/baseline.py | New | Commit | Median + cycle-trend baselines |
| src/predictive_maintenance/models/random_forest.py | New | Commit | RandomForest builder |
| src/predictive_maintenance/models/gradient_boosting.py | New | Commit | HistGradientBoosting builder |
| src/predictive_maintenance/models/linear.py | New | Commit | Optional LinearRegression builder |
| src/predictive_maintenance/models/dataset.py | New | Commit | Milestone-4 dataset loader with leakage assertions |
| src/predictive_maintenance/evaluation/__init__.py | New | Commit | Evaluation API exports |
| src/predictive_maintenance/evaluation/metrics.py | New | Commit | MAE/RMSE/NASA score + diagnostics |
| src/predictive_maintenance/evaluation/figures.py | New | Commit | Figure builders from real predictions |
| src/predictive_maintenance/reporting/milestone5_report.py | New | Commit | 31-section PDF report builder |
| scripts/train.py | New | Commit | Training CLI (required command) |
| scripts/evaluate.py | New | Commit | Evaluation/verification CLI (required command) |
| scripts/generate_milestone5_report.py | New | Commit | PDF CLI |
| scripts/package_milestone5.py | New | Commit | ZIP packaging CLI |
| configs/model_experiment.yaml | New | Commit | Shared experiment contract (seed, paths, model list) |
| configs/model_baseline.yaml | New | Commit | Baseline parameters |
| configs/model_rf.yaml | New | Commit | Random Forest parameters (required file) |
| configs/model_hgb.yaml | New | Commit | HistGradientBoosting parameters |
| configs/model_linear.yaml | New | Commit | Linear Regression parameters |
| configs/project.yaml | Modified | Commit | milestone_boundary 5; scope flags; milestone list |
| pyproject.toml | Modified | Commit | Description; ruff/mypy config for new modules |
| uv.lock | Existing | Keep (already committed in M1) | Pinned 129-package environment |
| tests/unit/test_metrics.py | New | Commit | Metric correctness incl. hand-calculated NASA score |
| tests/unit/test_baseline.py | New | Commit | Baseline behavior tests |
| tests/unit/test_random_forest.py | New | Commit | RF contract tests |
| tests/unit/test_gradient_boosting.py | New | Commit | HGB contract tests |
| tests/unit/test_model_serialization.py | New | Commit | joblib round-trip tests |
| tests/unit/test_no_deep_learning.py | New | Commit | Milestone 6 scope guard |
| tests/unit/test_no_training.py | **Deleted** | Commit the deletion (`git rm`) | Superseded by scope guard; rationale documented |
| tests/integration/test_classical_ml_pipeline.py | New | Commit | Synthetic + real-FD001 pipeline tests |

## B. Reports, documentation, and visualizations

| File Path | Status | GitHub Action | Reason |
|---|---|---|---|
| reports/tables/baseline_comparison.csv | Generated | Commit | Required comparison table (actual values) |
| reports/tables/per_engine_validation_error.csv | Generated | Commit | Per-engine error analysis |
| reports/tables/random_forest_feature_importance.csv | Generated | Commit | Feature importance record |
| reports/figures/model_comparison.png | Generated | Commit | Required figure |
| reports/figures/actual_vs_predicted.png | Generated | Commit | Required figure |
| reports/figures/residual_distribution.png | Generated | Commit | Required figure |
| reports/figures/feature_importance.png | Generated | Commit | Required figure |
| reports/figures/per_engine_validation_error.png | Generated | Commit | Required figure |
| reports/milestone_05_execution_log.md | New | Commit | Required execution log |
| reports/execution/milestone5_train.log | Generated | Commit | Raw training console output |
| reports/execution/milestone5_evaluate.log | Generated | Commit | Raw evaluation console output |
| experiments/milestone_05/run_001/config.yaml | Generated | Commit | Resolved experiment config |
| experiments/milestone_05/run_001/metrics.json | Generated | Commit | Train+validation metrics per model |
| experiments/milestone_05/run_001/metadata.json | Generated | Commit | Env/versions/timing/split identity |
| experiments/milestone_05/run_001/predictions.csv | Generated | Commit | 3,852-row validation predictions (~370 KB) |
| experiments/milestone_05/experiment_summary.csv | Generated | Commit | Run summary |
| docs/MILESTONE_5_PRE_IMPLEMENTATION_AUDIT.md | New | Commit | Required audit |
| docs/MILESTONE_5_IMPLEMENTATION.md | New | Commit | Required doc |
| docs/MILESTONE_5_METHODOLOGY.md | New | Commit | Required doc |
| docs/MILESTONE_5_MODEL_COMPARISON.md | New | Commit | Required doc |
| docs/MILESTONE_5_DATA_LEAKAGE_AUDIT.md | New | Commit | Required doc |
| docs/MILESTONE_5_LIMITATIONS.md | New | Commit | Required doc |
| docs/MILESTONE_5_EXECUTION_LOG.md | New | Commit | Required doc (copy of reports log) |
| docs/MILESTONE_5_GITHUB_UPLOAD_GUIDE.md | New | Commit | Required guide |
| docs/MILESTONE_5_VERIFICATION_CHECKLIST.md | New | Commit | Required checklist |
| docs/IMPLEMENTATION_PROGRESS.md | Modified | Commit | Milestone 5 marked complete |
| GITHUB_UPLOAD_MANIFEST_MILESTONE_05.md | New | Commit | This file |
| DELIVERABLES_MANIFEST_MILESTONE_05.md | New | Commit | Deliverable register |
| Predictive_Maintenance_Milestone_05_Classical_ML_Report.pdf (workspace parent dir) | Generated | Optional — GitHub **Release** asset preferred | 843 KB binary; in-tree only if policy allows |

## C. Model artifacts

| File Path | Status | GitHub Action | Reason |
|---|---|---|---|
| artifacts/classical_ml/median_baseline/median_baseline.joblib (~4 KB) | Generated | Commit | Reproducible reference baseline |
| artifacts/classical_ml/cycle_trend_baseline/cycle_trend_baseline.joblib (~4 KB) | Generated | Commit | Simple baseline artifact |
| artifacts/classical_ml/linear_regression/linear_regression.joblib (~5 KB) | Generated | Commit | Optional model artifact |
| artifacts/classical_ml/hist_gradient_boosting/hist_gradient_boosting.joblib (~550 KB) | Generated | Commit | Required boosting model |
| artifacts/classical_ml/random_forest/random_forest.joblib (~11 MB) | Generated | Commit **if** binary-artifact policy allows; else Keep local | Retrained identically in ~21 s via scripts/train.py |
| artifacts/classical_ml/*/metadata.json (×5) | Generated | Commit | Provenance: config, features, split IDs, seed, versions, metrics |

## D. Local-only files

| File Path | Status | GitHub Action | Reason |
|---|---|---|---|
| data/raw/**, data/interim/**, data/processed/**, data/metadata/** | Existing | Keep local | NASA C-MAPSS license unspecified; derived data large; already .gitignored |
| .venv/, __pycache__/, .mypy_cache/, .pytest_cache/, .ruff_cache/ | Generated | Keep local | Environment/caches; .gitignored |
| *.zip (delivery packages) | Generated | Keep local | Transfer artifacts, not repo content; .gitignored |
| notebooks/.ipynb_checkpoints | Generated | Keep local | Editor state |

## E. Files that must not be uploaded

None exist in this project: no credentials, API keys, `.env`, or private configuration were
ever created. (Verified by workspace scan; `.gitignore` additionally blocks common secret
paths.) The signed NASA download URL is transient and was never persisted.

## Upload sequence

See `docs/MILESTONE_5_GITHUB_UPLOAD_GUIDE.md` §2–§4 for the full 14-step procedure and
exact PowerShell / bash commands. Short form:

```bash
git status
git add src configs tests scripts docs reports experiments artifacts/classical_ml \
        pyproject.toml GITHUB_UPLOAD_MANIFEST_MILESTONE_05.md DELIVERABLES_MANIFEST_MILESTONE_05.md
git rm tests/unit/test_no_training.py
git diff --cached --stat
git commit -m "feat(ml): implement classical RUL baselines"
git push origin main   # only when authorized
```
