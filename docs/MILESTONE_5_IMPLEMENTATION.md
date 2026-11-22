# Milestone 5 — Implementation Record

**Status:** COMPLETE · **Date:** 2026-11-21 (UTC) · **Run:** `experiments/milestone_05/run_001`

## 1. What was implemented

| Component | Location | Notes |
|---|---|---|
| Evaluation layer | `src/predictive_maintenance/evaluation/metrics.py` | MAE, RMSE, NASA/PHM08 score (total + mean), median AE, error mean/std, early/late ratios, within ±10/±20 cycles; strict input validation |
| Evaluation figures | `src/predictive_maintenance/evaluation/figures.py` | 5 figure builders, all from real predictions |
| Model base | `src/predictive_maintenance/models/base.py` | `TrainedModel` record, `train_model()`, `predict_model()`, `save_model()`/`load_model()` (joblib) |
| Dataset contract | `src/predictive_maintenance/models/dataset.py` | `load_milestone4_dataset()` — loads only train_fit + validation scaled features/labels, asserts feature order, disjoint engines, no target column, finite values |
| Baselines | `src/predictive_maintenance/models/baseline.py` | `build_baseline()` = `DummyRegressor(strategy="median")`; `CycleTrendRegressor` + `build_cycle_trend_baseline()` |
| Random Forest | `src/predictive_maintenance/models/random_forest.py` | `build_random_forest()` — validated, config-driven |
| Boosting | `src/predictive_maintenance/models/gradient_boosting.py` | `build_gradient_boosting()` — `HistGradientBoostingRegressor`, validated, config-driven |
| Linear (optional) | `src/predictive_maintenance/models/linear.py` | `build_linear_regression()` |
| Train CLI | `scripts/train.py` | Trains all 5 models, writes artifacts, metadata, predictions, comparison CSV, run records |
| Evaluate CLI | `scripts/evaluate.py` | Recomputes + verifies metrics, reloads artifacts, verifies prediction identity, writes tables/figures/summary |
| Report CLI | `scripts/generate_milestone5_report.py` | 31-section PDF from run records |
| Configs | `configs/model_experiment.yaml`, `model_baseline.yaml`, `model_rf.yaml`, `model_hgb.yaml`, `model_linear.yaml` | Shared experiment contract + per-model parameters; no hardcoded params in scripts |
| Tests | `tests/unit/test_{metrics,baseline,random_forest,gradient_boosting,model_serialization,no_deep_learning}.py`, `tests/integration/test_classical_ml_pipeline.py` | 72 tests pass in full suite |
| Report module | `src/predictive_maintenance/reporting/milestone5_report.py` | PDF builder |

**XGBoost:** evaluated and deliberately NOT implemented — see pre-implementation audit §5
and PDF report §14. Not in the locked environment; no added scientific value over the two
required learner families.

## 2. Modified existing files

| File | Change | Reason |
|---|---|---|
| `configs/project.yaml` | `milestone_boundary: 5`; `no_predictive_training: true` → `classical_ml_training: true` + `deep_learning_training: false`; added milestone 5 entry | Reflects the new boundary honestly |
| `pyproject.toml` | Description updated; ruff per-file-ignore E402 for `evaluation/figures.py`; mypy ignore for `joblib` (no stubs) | matplotlib Agg backend import order; untyped dependency |
| `tests/unit/test_no_training.py` | **Retired** (deleted), replaced by `tests/unit/test_no_deep_learning.py` | The old guard forbade all training tokens (`RandomForestRegressor`, `sklearn.ensemble`, `model.fit(`…) which Milestone 5 legitimately requires. The new guard forbids only deep-learning tokens (LSTM/GRU/Transformer/torch/tensorflow/keras) in `src/`, preserving the Milestone 6 boundary. Documented, intentional. |

No Milestone 0–4 module logic was changed. No dataset or feature definition was touched.

## 3. Implementation order (as specified)

1. Constant Median Predictor (`DummyRegressor(strategy="median")`) — fit on train targets only.
2. Simple baseline: literal "last value" is undefined for RUL (target is not a carried-forward
   observable). Implemented **global cycle-trend baseline** `RUL_hat(c) = max(0, a + b·c)`,
   least-squares on training `(cycle, RUL)` pairs — the simplest statistically defensible
   predictor in this data representation. Single declared input (`cycle`); reference heuristic,
   not a true predictive model. Full rationale: PDF §11, methodology doc §4.
3. `RandomForestRegressor` — config-driven, seeded, `n_jobs=2` (conservative for ~1.9 GiB RAM).
4. `HistGradientBoostingRegressor` — config-driven, seeded, `early_stopping=False` (no
   validation peeking during fit).
5. `LinearRegression` — optional, implemented as an interpretable comparator.
6. XGBoost — optional, excluded with justification.

## 4. Execution evidence

| Command | Result |
|---|---|
| `uv run python scripts/train.py` | exit 0 — 5 models trained on real FD001 (log: `reports/execution/milestone5_train.log`) |
| `uv run python scripts/evaluate.py` | exit 0 — metrics reproduced, artifacts reload and match saved predictions (log: `reports/execution/milestone5_evaluate.log`) |
| `uv run pytest` | **72 passed** (incl. 3 `data_required` on real FD001) |
| `uv run ruff check src tests scripts` | All checks passed |
| `uv run ruff format` | No changes needed |
| `uv run mypy` | Success: no issues found in 33 source files |
| `uv run python scripts/generate_milestone5_report.py` | PDF generated, 11 pages, required statements + actual numbers verified via text extraction |

Environment: Python 3.13.18, scikit-learn 1.9.1, NumPy 2.5.4, pandas 2.3.3, joblib 1.6.0,
matplotlib 3.11.2, pyarrow 23.0.1; Linux x86_64; seed 42; Git SHA unavailable (broken `.git`
skeleton in workspace — see limitations).
