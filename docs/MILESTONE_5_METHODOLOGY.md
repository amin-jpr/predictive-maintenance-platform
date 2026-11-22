# Milestone 5 — Methodology

## 1. Problem and prediction unit

Task: Remaining Useful Life (RUL) regression on NASA C-MAPSS FD001.

**One example = one engine at one observation cycle.** The input is the 92-dimensional
causal feature vector available at that cycle (history up to and including it only); the
output is the capped RUL at that cycle: `rul = clip(rul_raw, 0, 125)` (cap decided in
Milestone 4, unchanged).

- Train examples: **16,779** rows from **80** engines.
- Validation examples: **3,852** rows from **20** engines.
- The 30-cycle sliding-window sequences built in Milestone 4 are reserved for Milestone 6
  and are not used by any Milestone 5 model.

## 2. Inputs (actual Milestone 4 outputs, unmodified)

| Input | File |
|---|---|
| Scaled features (train) | `data/processed/scaled/train_fit.parquet` (16,779 × 95) |
| Scaled features (validation) | `data/processed/scaled/validation.parquet` (3,852 × 95) |
| Labels | `data/processed/labels/{train_fit,validation}.csv` (columns: engine_id, cycle, rul_raw, rul, split, subset, endpoint_cycle) |
| Feature order | `data/metadata/feature_names.json` (92 features) |
| Split identity | `data/metadata/split.json` (seed 42, engine-level 80/20) |

Identifier columns (`engine_id`, `cycle`, `split`) are dropped before modeling; the target
(`rul`) is never part of the feature matrix. Both facts are asserted at load time in
`models/dataset.py` and covered by tests. The official NASA test files are never opened by
any Milestone 5 code path.

Feature set `milestone4_scaled_92`: 2 flight settings + 15 raw sensors (constant sensors
removed in Milestone 3) + 75 derived causal features (`*_roll_mean_5`, `*_roll_std_5`,
`*_roll_mean_10`, `*_roll_std_10`, `*_diff_1` per sensor). All values were standardized by
a `StandardScaler` **fit on train_fit only** in Milestone 4 (check `scaler_fit_boundary`
PASS).

## 3. Train/Validation separation

The Milestone 4 engine-level split is preserved exactly:

- `G_train ∩ G_val = ∅` — asserted in `load_milestone4_dataset()` and tested in
  `tests/integration/test_classical_ml_pipeline.py`.
- Train engines (80): 1, 2, 4, 6–18, 20, 21, 23, 24, 27, 29–33, 35–42, 44–50, 54–56, 58,
  59, 61, 63–71, 73–79, 80, 81, 83–92, 94–97, 99.
- Validation engines (20): 3, 5, 19, 22, 25, 26, 28, 34, 43, 51–53, 57, 60, 62, 72, 82,
  93, 98, 100.

No row-level random splitting, no windows crossing the boundary, no per-model datasets.
Every model consumed byte-identical X_train/y_train/X_val/y_val arrays.

## 4. Models

### 4.1 Constant Median Predictor
`DummyRegressor(strategy="median")`, fit on training targets only. Predicts the training
median for every example. Reference floor.

### 4.2 Simple baseline — global cycle-trend (documented substitution)
A literal "last-value" predictor does not exist for RUL: the target is not an observable
that persists between cycles. The defensible simple alternative in this data representation
is the global linear cycle trend:

```
RUL_hat(c) = max(0, a + b·c),   (a, b) = argmin Σ_train (a + b·c_i − rul_i)²
```

- Input: the scalar observation cycle `c` (declared explicitly in `configs/model_baseline.yaml`;
  never mixed into the 92-feature contract of the other models).
- Assumptions: one global monotone linear relationship; no engine individuality; no sensors.
- Limitations: reference heuristic, not a true predictive model — cannot distinguish
  fast- from slow-degrading engines.
- Fitted on train split only; predictions clipped at 0 (RUL is non-negative).
- Uses no future information and no target-derived features (cycle is known at prediction time).

### 4.3 Random Forest
`RandomForestRegressor` with parameters from `configs/model_rf.yaml`:
`n_estimators=100`, `min_samples_leaf=2`, `max_features=0.5`, `max_depth=null`,
`min_samples_split=2`, `random_state=42`, `n_jobs=2` (conservative CPU/memory setting for
the ~1.9 GiB sandbox). Reasonable initial values — **not** optimized; no hyperparameter
search was performed (Milestone 7 scope).

### 4.4 HistGradientBoosting
`HistGradientBoostingRegressor` from `configs/model_hgb.yaml`: `learning_rate=0.06`,
`max_iter=300`, `max_leaf_nodes=31`, `min_samples_leaf=20`, `l2_regularization=1.0`,
`early_stopping=False`, `random_state=42`. Early stopping is disabled deliberately so the
fit never touches validation data.

### 4.5 Linear Regression (optional)
`LinearRegression` on the same 92 features — interpretable comparator; also the model with
the best NASA score (see comparison doc).

### 4.6 XGBoost (optional — not implemented)
Excluded with justification: required learners already cover bagging + boosting; not in the
locked dependency environment; adds no new scientific conclusion. Recorded in the
pre-implementation audit §5.

## 5. Metrics

With `d_i = ŷ_i − y_i` (predicted minus actual):

```
MAE  = (1/N) Σ |d_i|
RMSE = sqrt((1/N) Σ d_i²)

s_i = exp(−d_i/13) − 1   if d_i < 0   (early prediction)
s_i = exp( d_i/10) − 1   if d_i ≥ 0   (late prediction)
S        = Σ s_i                 (total NASA/PHM08 score)
mean_S   = S / N
```

Late predictions are penalized more steeply (denominator 10 vs 13). Supplementary
diagnostics: median AE, error mean/std, early ratio (`d<0`), late ratio (`d>0`), % within
±10 and ±20 cycles. Implemented in `evaluation/metrics.py`; unit-tested against
hand-calculated values (e.g. `d=−13 → e−1`, `d=+10 → e−1`, zero error → 0, sums over
multiple observations), plus shape/empty/non-finite rejection.

## 6. Fair-comparison protocol

Identical for all models: train examples, validation examples, target (`rul`, cap 125),
feature contract (`milestone4_scaled_92`; cycle-trend baseline excepted with a single
declared input), metric implementations, seed 42. Models are fit on train only; validation
is used solely for reporting. No model selection or hyperparameter decision used the
official NASA test set — it was never loaded.

## 7. Reproducibility

- Seed 42 everywhere (`configs/model_experiment.yaml`).
- `train_model()` times each fit with `time.perf_counter()`.
- Artifacts: joblib + per-model `metadata.json` (config, feature names/order, target, split
  engine IDs, seed, Python/sklearn/platform versions, UTC timestamp, Git SHA status, times,
  train + validation metrics).
- Run record: `experiments/milestone_05/run_001/{config.yaml, metrics.json, metadata.json,
  predictions.csv}` + `experiment_summary.csv`.
- `scripts/evaluate.py` independently recomputes all metrics from `predictions.csv`,
  cross-checks against `metrics.json`, reloads every artifact, and asserts the reloaded
  models reproduce the saved predictions exactly.
- Commands: `uv sync --locked` → `uv run python scripts/train.py` → `uv run python
  scripts/evaluate.py` → `uv run pytest`.

Known limit: joblib pickles are scikit-learn-version-sensitive (pinned 1.9.1 via
`uv.lock`); serialization success alone does not prove reproducibility — the reload-and-
compare check does.
