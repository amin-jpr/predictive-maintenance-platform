# Feature engineering and preprocessing (Milestone 4)

## Boundary
This milestone prepares training-ready data only. No predictive model is fitted. The only fitted object is `sklearn.preprocessing.StandardScaler`, an unsupervised normalization transformer.

## RUL labels
Training: `failure_cycle = max(cycle)` per engine; `rul_raw = failure_cycle - cycle`; `rul = min(125, rul_raw)`. Terminal training label is zero.
Test: terminal ground truth `r_i` from `RUL_FD001.txt`; `inferred_failure_cycle = max(test cycle) + r_i`; reconstruct all available test cycles from that endpoint. Test sequence end is not failure. Both raw and capped labels are retained and independently verified.

## Sensor selection
Explicit configuration after FD001 EDA:
- Excluded exact constants: `s_1, s_5, s_10, s_16, s_18, s_19`.
- Excluded constant setting: `setting_3`.
- Retained sensors: `s_2, s_3, s_4, s_6, s_7, s_8, s_9, s_11, s_12, s_13, s_14, s_15, s_17, s_20, s_21`.
- Retained settings: `setting_1, setting_2`.
All original measurements remain in raw and cycle-level products. Near-constants `s_6, s_8, s_13` are retained initially, not silently removed.

## Initial feature set (92 features)
| Group | Count | Definition | Units/interpretation |
|---|---:|---|---|
| Current settings | 2 | `setting_1`, `setting_2` | Original operational context |
| Current sensors | 15 | Selected raw sensor values | Original sensor units |
| Rolling mean | 30 | Mean over trailing 5/10 cycles for each selected sensor | Same units; local level |
| Rolling std | 30 | Sample std (`ddof=1`) over trailing 5/10 cycles | Same units; local variability |
| First difference | 15 | `x[t] - x[t-1]` | Units per cycle; local change |

Optional rolling min/max and local trend slope are implemented but disabled by default to avoid redundant feature explosion.

## Causal warmup (TD-024)
Rolling calculations use `min_periods=1`: during the first cycles they expand over available current/past observations only. Single-sample rolling std is defined as 0. First difference at an engine's first cycle is defined as 0. This avoids NaNs and preserves complete 30-cycle windows ending at cycle 30 without future padding or backfill. No centered windows, forward fill from future rows, backward fill, or cross-engine rolling is used.

## Scaling
Global `StandardScaler(with_mean=True, with_std=True)` is fit **only** on `train_fit` engine feature rows. Validation and official test are transform-only. FD001 has one operating condition, so conditional/regime scaling is not justified initially. Scaler state is persisted as auditable JSON (mean, scale, variance, feature names, fit engine IDs, sample count, sklearn version), not pickle. Scaled columns are dimensionless z-scores.

## Engine split
Deterministic engine-level shuffle: seed 42, validation fraction 0.20. For FD001 this yields 80 fit engines and 20 validation engines. `train_fit ∩ validation = ∅`; official test remains separate. Split IDs and seed are persisted.

## Sliding windows
Default length 30, stride 1, no padding. A window ending at cycle `e` contains exactly cycles `e-29..e` from one engine and uses the label at `e`. Engines shorter than 30 cycles produce no windows and are reported. Arrays are float32 with shape `(n_windows, 30, 92)`; labels/IDs/cycles are int64. Windows are generated per engine and saved as compressed NPZ files to bound memory. A global `window_index.csv` records split, engine, start/end, target, path, and checksum.

## Data products
- Cycle-level: `data/processed/cycle_level/{train_fit,validation,test}.parquet`
- Labels: `data/processed/labels/{split}.csv`
- Unscaled causal feature tables: `data/processed/features/{split}.parquet`
- Scaled feature tables: `data/processed/scaled/{split}.parquet`
- Engine sequences: `data/processed/sequences/{split}.npz`
- Sliding windows: `data/processed/windows/{split}/engine_XXXX.npz`
- Window index/manifest: `data/processed/window_index.csv`, `data/processed/windows/manifest.json`
- Preprocessing state: `data/metadata/{preprocessing,split,scaler,feature_names,artifact_manifest}.json`
- Reports: `reports/preprocessing/{summary,verification}.{json,md}`

## Commands
```bash
uv run python scripts/run_preprocessing.py --subset FD001
uv run python scripts/build_features.py --subset FD001
uv run python scripts/verify_artifacts.py --subset FD001
uv run pytest
```

## Leakage safeguards
Engine-level split isolation; training-only scaler fitting; causal engine-local features; no future rows in windows; test labels never used for fitting/selection; target/endpoint/split columns excluded from features; independent label reconstruction; checksum and boundary verification; automated future-mutation and cross-engine tests.
