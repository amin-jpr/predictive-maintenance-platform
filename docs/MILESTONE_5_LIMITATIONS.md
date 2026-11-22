# Milestone 5 — Limitations

Honest scope of what the recorded results support. Nothing here invalidates the run; it
bounds the claims.

## Data and task

1. **Single subset, single condition, single fault mode.** FD001 has one flight condition
   and one HPC fault mode. Results do not transfer to FD002–FD004 (multi-condition) or to
   real fleets without re-validation.
2. **Capped RUL target (125).** ~35–40% of rows sit on the cap; early-life discrimination
   is flattened by construction, and plateau-region error partly measures the cap.
3. **Cycle-level tabular representation.** Temporal structure beyond the 5/10-cycle rolling
   statistics is not exploited; the Milestone 4 window sequences are reserved for
   Milestone 6.

## Models and tuning

4. **No hyperparameter optimization.** RF (100 trees, leaf 2, max_features 0.5) and HGB
   (lr 0.06, 300 iters, 31 leaves, L2 1.0) are reasonable initial configurations. They are
   **not** optimal and are not claimed to be; tuning is Milestone 7 scope.
5. **Visible overfitting in the ensembles.** Train MAE 3.5 (RF) / 6.0 (HGB) vs validation
   12.3 / 12.6. Regularization reduces but does not close the gap at this sample size.
6. **RF vs HGB difference is not meaningful.** 0.22 MAE cycles on 20 validation engines is
   within run-to-run/engine-sampling noise; treat them as tied.
7. **XGBoost excluded.** Documented decision (audit §5); no third boosting family was added.

## Evaluation

8. **Small validation fleet.** 20 engines; per-engine MAE ranges 3.7–30.6 (8×). Aggregate
   metrics hide hard engines; no confidence intervals are claimed.
9. **Metric-dependent ranking.** Best by MAE/RMSE: Random Forest. Best by total NASA score:
   Linear Regression. Any "winner" statement must name its metric; operational cost
   asymmetry should drive final selection, not validation MAE alone.
10. **Validation doubles as reporting set.** With zero tuning the exposure is minimal, but
    the official NASA Test evaluation (deliberately deferred) remains the only untouched
    performance estimate.
11. **Best validation model ≠ best deployed model.** No claim is made about industrial
    suitability, alarm costs, or maintenance scheduling.

## Interpretation

12. **Feature importance ≠ causality.** Impurity importance says the forest splits on
    s_4-rolling means often; it does not prove s_4 causes degradation (it is a simulated
    HPC fault signature).
13. **Cycle-trend baseline is a reference heuristic**, not a true predictive baseline: one
    global line, no engine individuality, no sensors.

## Engineering and environment

14. **joblib artifacts bind to scikit-learn 1.9.1** (pinned in `uv.lock`). Loading with a
    different sklearn version may fail or silently change predictions; `evaluate.py`'s
    reload-and-compare check is the guard.
15. **No Git history in this workspace.** `.git` is a broken skeleton (no objects/refs), so
    `git_commit_sha` is recorded as `unavailable` in all metadata, and no commit/push was
    performed or claimed. Exact local commands: `docs/MILESTONE_5_GITHUB_UPLOAD_GUIDE.md`.
16. **Single-run results.** Seed 42, one run per model. Multi-seed variance was not
    measured (out of scope; would not change baseline-vs-ensemble conclusions).
17. **CPU-only sandbox (~1.9 GiB RAM).** `n_jobs=2` and 100 trees were chosen for this
    envelope; larger configurations were neither needed nor tested.
