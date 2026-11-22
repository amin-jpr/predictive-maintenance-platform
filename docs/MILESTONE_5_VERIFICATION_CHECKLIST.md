# Milestone 5 — Verification Checklist

Each item lists how it is verified and the evidence actually produced. Items marked
**(automated)** are enforced by code/tests, not just prose.

## Models and training

- [x] All required models exist — median baseline, simple (cycle-trend) baseline, Random
      Forest, HistGradientBoosting; optional Linear Regression implemented; XGBoost
      excluded with documented justification. *(code: `src/predictive_maintenance/models/`)*
- [x] Training runs actually completed — `scripts/train.py` exit 0 on real FD001;
      console log `reports/execution/milestone5_train.log`; per-model timings recorded. **(automated)**
- [x] Simple baseline defensible and documented — substitution rationale (no literal
      last-value exists for RUL) in methodology §4.2 and PDF §11.

## Fair comparison

- [x] All models used the same split, target, features, metrics — single shared loader;
      comparison CSV shows identical train/validation sample counts for every row. **(automated: `models/dataset.py` + `evaluate.py` cross-check)**
- [x] No Train/Validation engine overlap — asserted at load; tested on real data.
      **(automated: `test_classical_ml_pipeline.py`)**
- [x] No target leakage — `rul`/`rul_raw` absent from feature matrix; identifiers dropped.
      **(automated: load-time assertion + integration test)**
- [x] Official Test not used for anything — loader never opens test files;
      `official_test_used: false` in run and artifact metadata. **(automated)**
- [x] No hyperparameter selection on validation or test — no search performed at all;
      HGB `early_stopping=False`. *(configs + methodology §4.4)*

## Metrics

- [x] MAE, RMSE, NASA score (total + mean) computed from actual predictions —
      hand-calculated unit tests for the formula (negative/zero/positive errors,
      multi-observation sums, invalid inputs). **(automated: `test_metrics.py`, 11 tests)**
- [x] Reports match saved experiment results — `evaluate.py` recomputes every metric from
      `predictions.csv` and asserts agreement with `metrics.json`; asserts reloaded
      artifacts reproduce saved predictions. Ran: "Evaluation verification: PASS". **(automated)**
- [x] Predictions finite — checked in metric layer (non-finite rejected) and in model
      tests. **(automated)**

## Artifacts and records

- [x] Model artifacts load successfully — all 5 `.joblib` files reloaded in
      `evaluate.py` and in `test_model_serialization.py`. **(automated)**
- [x] Artifact metadata complete — config, feature order, split engine IDs, seed,
      versions, timestamp, Git SHA status (`unavailable`, honestly recorded), metrics:
      `artifacts/classical_ml/*/metadata.json`.
- [x] Experiment records complete — `experiments/milestone_05/run_001/{config.yaml,
      metrics.json, metadata.json, predictions.csv}` + `experiment_summary.csv`.

## Quality gates

- [x] Tests pass — `uv run pytest`: **72 passed, 0 failed** (69 non-data + 3 real-data). **(automated)**
- [x] `uv run ruff check src tests scripts` — All checks passed. **(automated)**
- [x] `uv run ruff format` — no changes needed. **(automated)**
- [x] `uv run mypy` — Success: no issues found in 33 source files. **(automated)**
- [x] Execution commands work — `train.py`, `evaluate.py`, `pytest` all exit 0 (log §10–13).

## Deliverables

- [x] `reports/tables/baseline_comparison.csv` — all required columns present, real values.
- [x] `reports/figures/model_comparison.png` + actual-vs-predicted, residuals, RF feature
      importance, per-engine error — 5 PNGs generated from real predictions.
- [x] PDF report — 11 pages; 31 sections; required statements verified by text
      extraction ("No Deep Learning implementation was started…"; final handoff statement).
- [x] Documentation set — 8 `docs/MILESTONE_5_*.md` files + 2 root manifests.
- [x] ZIP package — `predictive-maintenance-platform-milestone-05.zip` with SHA-256
      recorded in `DELIVERABLES_MANIFEST_MILESTONE_05.md`; forbidden-content scan clean.

## Known environment limitation (cannot be verified here)

- [ ] **Git commit/push** — NOT performed: `.git` is a broken skeleton in this workspace
      (no objects/refs/config). Nothing was claimed as committed or pushed. The user must
      run, locally:
      `git init -b main` (or clone the existing repo) → stage per
      `docs/MILESTONE_5_GITHUB_UPLOAD_GUIDE.md` → `git commit -m "feat(ml): implement
      classical RUL baselines"` → push only when authorized. Evidence needed afterwards:
      `git log --oneline -1` and `git status` output.
