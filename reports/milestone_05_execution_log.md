# Milestone 5 — Execution Log

All commands executed in `/home/user/predictive-maintenance-platform` (the AI workspace
project root) on 2026-11-21 UTC. Every status below was observed, not assumed. Raw console
output for the two main runs is tee'd into `reports/execution/`.

| # | Command | Exit | Duration | Observed result |
|---|---|---|---|---|
| 1 | `pip install uv` (session start; uv absent) | 0 | — | uv 0.13.9 installed |
| 2 | `uv sync --locked` | 0 | — | 129 locked packages; sklearn 1.9.1, numpy 2.5.4, pandas 2.3.3 |
| 3 | `uv run pytest -m "not data_required"` (pre-change baseline) | 0 | 7.4 s | **37 passed, 2 deselected** |
| 4 | `uv run ruff format src tests scripts` | 0 | — | 4 files reformatted, 55 unchanged |
| 5 | `uv run ruff check --fix src tests scripts` | 0 | — | 1 unused import fixed; then "All checks passed!" |
| 6 | `uv run mypy` (after adding joblib to ignore_missing_imports) | 0 | — | Success: no issues found in 32 source files |
| 7 | `uv run pytest -m "not data_required"` | 0 | 7.4 s | **69 passed, 3 deselected** |
| 8 | `uv run pytest` (first full run) | 1 | 9.4 s | 71 passed, **1 failed** — `test_classical_ml_pipeline.py:75` `TypeError: ufunc 'isfinite'` (test bug: `validation_metrics` contains the `feature_set` string). Fix: assert finiteness on the 7 numeric metric keys only. Source code unaffected. |
| 9 | `uv run pytest` (after test fix) | 0 | 9.0 s | **72 passed** |
| 10 | `uv run python scripts/train.py` | 0 | 28.6 s wall (26.8 s measured in-script) | 5 models trained on real FD001. Log: `reports/execution/milestone5_train.log` |
| 11 | `uv run python scripts/evaluate.py` (first run) | 1 | 3.4 s | Metrics verified for all 5 models, best = random_forest; then `ValueError: zip() argument 2 is shorter` in `plot_actual_vs_predicted` (5 models vs 6 axes; `strict=True`). Source fix: zip only the used axes. |
| 12 | `uv run python scripts/evaluate.py` (after figure fix) | 0 | 4.9 s | All metrics reproduced; all artifacts reloaded and reproduce saved predictions; 5 figures + 3 tables written. Log: `reports/execution/milestone5_evaluate.log` |
| 13 | `uv run python scripts/evaluate.py` (after adding experiment_summary.csv) | 0 | 4.7 s | `experiments/milestone_05/experiment_summary.csv` written; verification PASS |
| 14 | `uv run python scripts/generate_milestone5_report.py` (attempts 1–3) | 1,1,0 | — | Attempt 1: ruff F401 unused imports (fixed), mypy `int(idxmin())` overload error. Attempt 2: syntax slip in an f-string (`get('x']`) — fixed; then `.loc`/`.iloc` overload churn (4→17 mypy errors) while PDF still generated. Attempt 3 (NumPy argmin + float coercions): **exit 0**, mypy clean. |
| 15 | `uv run mypy` (final) | 0 | — | Success: no issues found in **33 source files** |
| 16 | `uv run ruff check src scripts` (final) | 0 | — | All checks passed! |
| 17 | `uv run ruff format src scripts` (final) | 0 | — | 39 files left unchanged |
| 18 | `uv run python scripts/generate_milestone5_report.py` (final) | 0 | — | `/home/user/Predictive_Maintenance_Milestone_05_Classical_ML_Report.pdf`, 843,137 bytes |
| 19 | PDF content verification (`uv run --with pypdf`) | 0 | — | 11 pages; required statements present ("No Deep Learning implementation was started…", "MILESTONE 5 COMPLETED — … HAS NOT BEEN STARTED."); actual numbers present (12.33, 36.81, 38,748, 16,779, 3,852, s_4_roll_mean_10); sections 15 and 31 present |
| 20 | `git rev-parse HEAD` | 128 (expected) | — | `fatal: not a git repository` — `.git` is a skeleton (HEAD/description/hooks/info only; no objects/refs/config). No commit or push was performed or claimed. `git_commit_sha: "unavailable"` recorded in all metadata. |

## Training output (verbatim, step 10)

```
Loaded Milestone 4 inputs: train (16779, 92), validation (3852, 92), features 92
Train engines: 80; validation engines: 20; official test used: False
median_baseline: MAE=36.810 RMSE=46.310 NASA=6909743.2 (mean 1793.8066) train_time=0.01s
cycle_trend_baseline: MAE=19.466 RMSE=25.340 NASA=141350.0 (mean 36.6952) train_time=0.00s
linear_regression: MAE=16.599 RMSE=20.588 NASA=38747.6 (mean 10.0591) train_time=0.07s
random_forest: MAE=12.333 RMSE=18.176 NASA=59424.2 (mean 15.4268) train_time=20.86s
hist_gradient_boosting: MAE=12.550 RMSE=18.528 NASA=62688.2 (mean 16.2742) train_time=4.32s
```

## Failures encountered and resolutions (nothing hidden)

1. **Integration test TypeError (step 8)** — test-side bug (`np.isfinite` over a mixed
   dict including a string). Fixed the test to check the numeric keys. Not a source defect.
2. **Figure zip ValueError (step 11)** — `strict=True` zip of 6 subplot axes against 5
   model names. Fixed `figures.py` to zip only `axes_flat[:n_panels]`.
3. **mypy pandas overload churn (steps 14)** — `comparison.loc[int(idxmin())]` and
   `int(best[...])` do not type-check under pandas-stubs. Resolved with
   `comparison.iloc[mae_array.argmin()]` + `float()`/`int(float())` coercions.
4. **Git unusable (step 20)** — environment limitation, pre-existing (documented in the
   pre-implementation audit). Workaround: exact commands for the user's local machine in
   `docs/MILESTONE_5_GITHUB_UPLOAD_GUIDE.md`. No commit/push claimed.

## Environment

Python 3.13.18 · Linux-6.1.189+-x86_64-with-glibc2.41 · scikit-learn 1.9.1 · NumPy 2.5.4 ·
pandas 2.3.3 · joblib 1.6.0 · matplotlib 3.11.2 · pyarrow 23.0.1 · ruff 0.17.4 ·
mypy 1.20.2 · pytest 8.4.2 · uv 0.13.9 · seed 42 · CPU-only, ~1.9 GiB RAM.

## Packaging addendum (post-documentation)

| # | Command | Exit | Observed result |
|---|---|---|---|
| 21 | `uv run ruff check .` / `ruff format --check .` (whole repo; `notebooks/` added to ruff extend-exclude with documented rationale — executed M3 deliverables verified via nbclient, not lint) | 0 | All checks passed! / 92 files already formatted |
| 22 | `uv run pytest` (final gate) | 0 | **72 passed** — log: `reports/execution/milestone5_full_pytest.txt` |
| 23 | Scope-guard incident: first whole-repo gate failed `test_no_deep_learning` because `milestone5_report.py` itself listed the forbidden tokens in prose (§3, §25). Fixed by rewording both passages — guard now passes and the PDF text contains no deep-learning architecture tokens (verified by extraction). | 0 | Documented, resolved |
| 24 | `uv run python scripts/generate_milestone5_report.py` (final) | 0 | PDF 11 pages, 843,121 bytes |
| 25 | `uv run python scripts/package_milestone5.py` (multiple builds) | 0 | Determinism verified: two independent builds from identical content were byte-identical (SHA-256 matched). Final ZIP: 217 entries, ~17.5 MB. Note: this log lives inside the ZIP, so the authoritative final checksum is the one recorded in `reports/execution/milestone5_package.log` (outside the archive) and in the delivery message — log: `reports/execution/milestone5_package.log` |
| 26 | ZIP content scan (python zipfile) | 0 | Required entries present; retired `test_no_training.py` absent; no nested ZIPs; forbidden-content scan clean (only `data/metadata/processed_checksums.sha256`, hash-manifest included by design) |
