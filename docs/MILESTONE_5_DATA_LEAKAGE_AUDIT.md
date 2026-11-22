# Milestone 5 — Data Leakage Audit

Audit of every leakage vector named in the milestone specification, with the control and
the evidence actually executed. Date: 2026-11-21.

## 1. Checklist

| # | Leakage risk | Status | Control | Evidence |
|---|---|---|---|---|
| 1 | RUL target inside the feature matrix | **CLEAN** | `load_milestone4_dataset()` asserts no column named `rul`/`rul_raw` in features; identifiers (`engine_id`, `cycle`, `split`) dropped before modeling | `models/dataset.py`; integration test asserts `"rul" not in feature_names` |
| 2 | Future sensor observations used | **CLEAN** | Only Milestone 4 causal features (rolling mean/std over past 5/10 cycles, backward 1-cycle diffs); no forward-looking operation was added in M5 | `docs/FEATURE_ENGINEERING.md`; M4 `window_boundaries` check PASS; feature set unchanged |
| 3 | Validation info used to fit preprocessing | **CLEAN** | Preprocessing/scaler frozen in Milestone 4, fit on train_fit only; M5 performs no fitting of any transformer | M4 `scaler_fit_boundary` PASS; M5 code contains no scaler/fit-on-validation path |
| 4 | Official Test info used anywhere | **CLEAN** | Loader opens only `scaled/{train_fit,validation}.parquet` and `labels/{train_fit,validation}.csv`; test files never read; `official_test_used: false` recorded in run + artifact metadata | `models/dataset.py`; `experiments/milestone_05/run_001/metadata.json`; each `artifacts/classical_ml/*/metadata.json` |
| 5 | Engine ID / cycle identifier as predictive feature | **CLEAN** | Feature matrix = the 92 approved features only. Exception, declared: the cycle-trend baseline's single input *is* the scalar cycle — by design, documented in its config and in the methodology (§4.2); it is never mixed into the 92-feature contract | `configs/model_baseline.yaml`; `models/baseline.py` (`CycleTrendRegressor` rejects multi-column input) |
| 6 | Model-specific preprocessing creating unfair comparison | **CLEAN** | One shared loader, one feature list from `data/metadata/feature_names.json`, identical arrays for all models; per-model configs contain estimator params only | `models/dataset.py`; `configs/model_experiment.yaml` |
| 7 | Train/Validation engine overlap | **CLEAN** | Disjointness asserted at load time; automated test | `test_classical_ml_pipeline.py` (real FD001: `set(train) & set(val) == ∅`) |
| 8 | Hyperparameters/model selection via Test or via tuning on Validation | **CLEAN** | No hyperparameter search performed at all; validation used only for reporting; boosting `early_stopping=False` so the fit never inspects validation | `configs/model_hgb.yaml`; methodology §4.4 |
| 9 | Row-level random split leaking engine identity across splits | **CLEAN** | Milestone 4 engine-level split reused unchanged (seed 42, 80/20); no re-splitting in M5 | `data/metadata/split.json`; run metadata records both engine-ID lists |
| 10 | Windows overlapping the split boundary | **N/A** | 30-cycle windows are not used by any M5 model (reserved for M6) | methodology §1 |

## 2. Automated tests covering leakage risks

- `tests/integration/test_classical_ml_pipeline.py::test_real_fd001_milestone4_inputs_and_small_models`
  (`data_required`): loads the real products; asserts shapes (16,779×92 / 3,852×92), 80/20
  engine counts, **disjoint engine sets**, `rul` absent from features,
  `official_test_used is False`.
- `tests/unit/test_baseline.py`: median computed from train targets only; cycle-trend
  rejects unexpected inputs; clipping keeps predictions ≥ 0 without touching targets.
- `tests/unit/test_no_deep_learning.py`: scope guard (no deep-learning tokens in `src/`).
- `scripts/evaluate.py` runtime assertions: saved predictions match the freshly loaded
  Milestone 4 validation targets exactly (`np.array_equal`), preventing silent dataset drift
  between training and evaluation.

## 3. Residual risks (not leakage, but honesty items)

1. **Capped target plateau.** 40.4% of train and 35.1% of validation rows sit at the cap
   (rul = 125). This is a Milestone 4 target-definition choice, not leakage, but it means
   plateau-region metrics partly measure the cap, not model skill.
2. **Validation-based reporting.** The best model is identified on the same 20 engines used
   for reporting. With no tuning performed the exposure is minimal, but the official Test
   set (deferred to the final project stage) remains the only untouched estimate.
3. **Correlated rolling features.** Overlapping 5/10-cycle windows within one engine are
   autocorrelated; this inflates effective sample size for confidence-interval purposes
   (none are claimed here).

**Conclusion:** no leakage vector from the specification list was found open. Every control
is code-enforced and test-covered, not merely documented.
