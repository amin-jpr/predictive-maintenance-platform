# Milestone 5 — GitHub Upload Guide

Target repository: **predictive-maintenance-platform** (existing; Milestones 0–4 files must
be preserved).

> **Workspace limitation (verified, not assumed):** the AI workspace `.git` directory is a
> broken skeleton (`HEAD`, `description`, `hooks/`, `info/` only — no `objects/`, `refs/`,
> or `config`). Every git command fails with `fatal: not a git repository`. Therefore **no
> commit was created and nothing was pushed from this workspace**, and no Git SHA could be
> recorded (`git_commit_sha: "unavailable"` in all metadata). Perform the steps below on
> your own machine.

## 1. What changed in Milestone 5

**New source/config/scripts/tests**

```
src/predictive_maintenance/models/__init__.py
src/predictive_maintenance/models/base.py
src/predictive_maintenance/models/baseline.py
src/predictive_maintenance/models/random_forest.py
src/predictive_maintenance/models/gradient_boosting.py
src/predictive_maintenance/models/linear.py
src/predictive_maintenance/models/dataset.py
src/predictive_maintenance/evaluation/__init__.py
src/predictive_maintenance/evaluation/metrics.py
src/predictive_maintenance/evaluation/figures.py
src/predictive_maintenance/reporting/milestone5_report.py
scripts/train.py
scripts/evaluate.py
scripts/generate_milestone5_report.py
scripts/package_milestone5.py
configs/model_experiment.yaml
configs/model_baseline.yaml
configs/model_rf.yaml
configs/model_hgb.yaml
configs/model_linear.yaml
tests/unit/test_metrics.py
tests/unit/test_baseline.py
tests/unit/test_random_forest.py
tests/unit/test_gradient_boosting.py
tests/unit/test_model_serialization.py
tests/unit/test_no_deep_learning.py
tests/integration/test_classical_ml_pipeline.py
```

**Modified**

```
configs/project.yaml      (milestone_boundary 5; scope flags; milestone list)
pyproject.toml            (description; ruff per-file-ignore; mypy joblib ignore)
docs/IMPLEMENTATION_PROGRESS.md
```

**Retired:** `tests/unit/test_no_training.py` (deleted — replaced by
`tests/unit/test_no_deep_learning.py`; rationale in
`docs/MILESTONE_5_IMPLEMENTATION.md` §2). In Git terms: stage the deletion.

**New documentation / manifests**

```
docs/MILESTONE_5_PRE_IMPLEMENTATION_AUDIT.md
docs/MILESTONE_5_IMPLEMENTATION.md
docs/MILESTONE_5_METHODOLOGY.md
docs/MILESTONE_5_MODEL_COMPARISON.md
docs/MILESTONE_5_DATA_LEAKAGE_AUDIT.md
docs/MILESTONE_5_LIMITATIONS.md
docs/MILESTONE_5_EXECUTION_LOG.md
docs/MILESTONE_5_GITHUB_UPLOAD_GUIDE.md
docs/MILESTONE_5_VERIFICATION_CHECKLIST.md
GITHUB_UPLOAD_MANIFEST_MILESTONE_05.md
DELIVERABLES_MANIFEST_MILESTONE_05.md
```

**Generated results — commit these (small, reproducible evidence)**

```
reports/tables/baseline_comparison.csv
reports/tables/per_engine_validation_error.csv
reports/tables/random_forest_feature_importance.csv
reports/figures/model_comparison.png
reports/figures/actual_vs_predicted.png
reports/figures/residual_distribution.png
reports/figures/feature_importance.png
reports/figures/per_engine_validation_error.png
reports/milestone_05_execution_log.md
reports/execution/milestone5_train.log
reports/execution/milestone5_evaluate.log
experiments/milestone_05/run_001/{config.yaml,metrics.json,metadata.json,predictions.csv}
experiments/milestone_05/experiment_summary.csv
```

**Model artifacts — policy decision**

```
artifacts/classical_ml/*/metadata.json          → commit (small, essential provenance)
artifacts/classical_ml/median_baseline/*.joblib         (~4 KB)  → commit
artifacts/classical_ml/cycle_trend_baseline/*.joblib    (~4 KB)  → commit
artifacts/classical_ml/linear_regression/*.joblib       (~5 KB)  → commit
artifacts/classical_ml/hist_gradient_boosting/*.joblib  (~550 KB) → commit
artifacts/classical_ml/random_forest/*.joblib           (~11 MB)  → commit IF repository
    policy allows binary artifacts; otherwise keep local (retrainable in ~21 s via
    scripts/train.py with identical results under the pinned environment)
```

**Keep local / never upload**

```
data/**                (raw NASA files + all derived datasets; license unspecified)
.venv/  __pycache__/  .mypy_cache/  .pytest_cache/  .ruff_cache/
*.zip                  (delivery packages)
/home/user/Predictive_Maintenance_Milestone_05_Classical_ML_Report.pdf
    → optional: publish via GitHub Releases rather than in-tree (843 KB binary)
```

No credentials, API keys, or private configuration exist in this project.

## 2. Upload sequence

1. Open the existing repository `predictive-maintenance-platform` (create it only if it
   truly does not exist — do not assume a URL; verify with `git remote -v`).
2. On your machine, clone it (or use your existing checkout containing Milestones 0–4):
   `git clone <your-repo-url> && cd predictive-maintenance-platform`
3. Download the Milestone 5 ZIP from the AI workspace
   (`predictive-maintenance-platform-milestone-05.zip`) and extract it over the repository
   root — paths match 1:1. Alternatively copy the file lists from §1 manually.
4. Preserve existing Milestone 0–4 files (the ZIP contains only new/modified paths plus
   generated reports; extraction never deletes).
5. Apply the deletion: `git rm tests/unit/test_no_training.py`
6. Install dependencies: `uv sync --locked`
7. Get the dataset per `docs/DATASET_ACQUISITION.md` (data/ stays out of Git).
8. Run tests: `uv run pytest` → expect **72 passed** (3 require the real dataset).
9. Optional reproduction: `uv run python scripts/train.py && uv run python
   scripts/evaluate.py` (≈35 s total; regenerates identical metrics under the pinned env).
10. Stage, inspect, commit, push (push only when you authorize it).

## 3. Exact commands

**Linux / macOS**

```bash
cd predictive-maintenance-platform
git status
git add src configs tests scripts docs reports experiments artifacts/classical_ml \
        pyproject.toml GITHUB_UPLOAD_MANIFEST_MILESTONE_05.md \
        DELIVERABLES_MANIFEST_MILESTONE_05.md
git rm --cached --ignore-unmatch tests/unit/test_no_training.py
git rm tests/unit/test_no_training.py 2>/dev/null || true
git diff --cached --stat
git commit -m "feat(ml): implement classical RUL baselines"
git log --oneline -1          # verify the commit exists
git push origin main          # only when authorized
```

**Windows PowerShell**

```powershell
cd predictive-maintenance-platform
git status
git add src configs tests scripts docs reports experiments artifacts/classical_ml `
        pyproject.toml GITHUB_UPLOAD_MANIFEST_MILESTONE_05.md `
        DELIVERABLES_MANIFEST_MILESTONE_05.md
git rm --cached --ignore-unmatch tests/unit/test_no_training.py
git diff --cached --stat
git commit -m "feat(ml): implement classical RUL baselines"
git log --oneline -1
git push origin main   # only when authorized
```

If the local repository was never initialized (as in this workspace):

```bash
git init -b main
git add -A        # .gitignore already excludes data/, .venv/, caches, *.zip
git commit -m "chore: milestones 0-5 baseline import"
```

## 4. Verification after upload

```bash
git log --oneline -3
git status                       # expect: clean (except local-only data/)
git show --stat HEAD | head -40  # expect the Milestone 5 paths
```

On GitHub: confirm the commit appears on the default branch, `reports/tables/
baseline_comparison.csv` renders, and `tests/unit/test_no_training.py` is gone while
`tests/unit/test_no_deep_learning.py` exists. **Do not consider the upload successful
until you have observed these.**
