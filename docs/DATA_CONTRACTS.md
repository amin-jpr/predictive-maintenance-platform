# Data contracts between milestones

## C0 → C1: planning contract
Versioned YAML configs define subset, paths, RUL cap, split seed/fraction, window length, sensor selection, and feature definitions. Documentation defines semantics and acceptance gates. No code may silently change these values.

## C1 → C2: environment contract
`uv sync --locked` installs the package and declared dependencies. Public modules live under `src/predictive_maintenance`. Scripts are executable through `uv run`. Tests can run without NASA data using synthetic fixtures; real-data tests are explicitly marked.

## C2: raw ingestion contract
Input: original `train_FD001.txt`, `test_FD001.txt`, `RUL_FD001.txt` extracted from the verified NASA archive. Output: immutable raw files plus `data/metadata/source_manifest.json`, `acquisition.json`, `checksums.sha256`, and `reports/validation/integrity.json`/Markdown.

Required invariants:
1. Exactly 26 whitespace-separated numeric fields per observation.
2. `engine_id` and `cycle` are positive integer-valued; cycles start at 1 and increase by exactly 1 within each engine.
3. `(engine_id, cycle)` is unique; no duplicate rows/keys.
4. All settings/sensors are finite numeric values. No universal physical range is invented without authoritative limits.
5. Training and test engine counts match the subset catalog (FD001: 100/100). IDs are unique within each split; cross-split numeric overlap is allowed and expected.
6. RUL file has exactly one nonnegative integer per test engine, aligned to sorted test engine IDs. Official distributed IDs are contiguous and sorted; alignment is a documented source convention, not information contained in the RUL file itself.
7. Sequence lengths are positive and reported. Known FD001 totals are verified as regression checks, not hard-coded into generic algorithms.
8. Raw checksums match the verified acquisition manifest; preprocessing never writes raw paths.

Failure behavior: raise a descriptive exception and write a failed report where possible; do not produce downstream artifacts from invalid inputs.

## C2 → C3: validated frame contract
DataFrame columns: `engine_id`, `cycle`, `setting_1..3`, `s_1..21`. Identifier dtypes int64; measurements float64. Rows sorted by engine then cycle. No target columns are required for EDA. EDA may read the full official training set descriptively; this does not authorize fitting on validation engines.

## C3 → C4: sensor decision contract
EDA emits constant/near-constant statistics, correlations, trajectories, and RUL distributions. Sensor selection is explicit in `configs/preprocessing.yaml`. For FD001, globally constant sensors are excluded from features only; all 21 sensors remain in raw/cycle products. Near-constant but nonzero-variance s_6 is retained initially. Any change requires updating the decision record and config fingerprint.

## C4: label contract
Training: `failure_cycle = max(cycle)` per engine; `rul_raw = failure_cycle - cycle`; `rul = min(cap, rul_raw)`.
Test: read terminal RUL vector; `inferred_failure_cycle = max(cycle) + terminal_rul`; reconstruct all available cycles from that endpoint. Never treat test max cycle as failure.
Labels are nonnegative integers; training terminal label is zero; test terminal label equals the supplied ground truth before clipping. Raw and capped labels are both retained.

## C4: split contract
`train_fit` and `validation` partition official training engine IDs only. `train_fit ∩ validation = ∅`; union equals official training IDs. Official test IDs are stored separately and never enter either fit set. Seed, fraction, sorted ID lists, and config fingerprint are persisted.

## C4: scaler contract
Fit input: causal feature table for `train_fit` engines only, after warmup rows are excluded. Feature order is explicit and identical across splits. `StandardScaler(with_mean=True, with_std=True)` uses population variance (`ddof=0`); zero-variance columns are handled by sklearn's unit-scale convention but should be absent under the configured selection. Persist mean, scale, variance, feature names, sample count, fit engine IDs, source/config hashes, and sklearn version. Validation/test are transform-only. No pickle is required.

## C4: feature/window contract
Feature at cycle `e` depends only on that engine's rows with cycle <= `e`. Rolling calculations are trailing and causal with `min_periods=1` during warmup (TD-024); single-sample rolling std and first difference are defined as 0. First differences otherwise use the immediately preceding cycle. Default window `W=30` contains exactly cycles `e-29..e`, one engine, no padding, no future rows. Target is the label at `e`. Arrays are float32; labels/IDs/cycles are int64. Every window has start/end/engine/target metadata. Short engines may produce no windows and must be reported.

## C4 outputs
- `data/interim/labeled/{train,test}.parquet`: all original columns plus labels/endpoints.
- `data/processed/cycle_level/{train_fit,validation,test}.parquet`: split-specific cycle tables.
- `data/processed/features/{split}.parquet`: unscaled causal features + identifiers.
- `data/processed/scaled/{split}.parquet`: scaled features + identifiers.
- `data/processed/labels/{split}.csv`: identifiers, raw/capped labels, endpoint metadata.
- `data/processed/sequences/{split}.npz`: ordered per-engine float32 sequences and labels.
- `data/processed/windows/{split}/engine_XXXX.npz`: bounded per-engine window arrays.
- `data/processed/window_index.csv`: global window index with file checksums.
- `data/metadata/preprocessing.json`, `scaler.json`, `split.json`, `feature_names.json`, `artifact_manifest.json`: auditable processing state.
- `reports/preprocessing/summary.md` and `summary.json`: actual counts, shapes, exclusions, and checks.

## Manifest contract
Every artifact entry records relative path, role, source subset/split, shape/columns where applicable, dtype(s), byte size, SHA-256, generation timestamp, and configuration/source fingerprints. Numeric reproducibility checks exclude timestamps and absolute paths. A manifest is not a substitute for validating the actual bytes.

## Final handoff contract
No predictive estimator or training pipeline exists. Reports distinguish executed local evidence from pending remote CI/GitHub/local-machine actions. Raw NASA data and derived data are local-only by default because the catalog does not specify a redistribution license. The delivery archive contains code/docs/reports and small reviewed metadata; large data products are regenerated locally unless explicitly reviewed for size and permission.
