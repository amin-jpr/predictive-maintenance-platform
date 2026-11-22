# Technical decision record

Status legend: **Retained** = explicit assignment decision; **New** = default introduced because no earlier file was available; **Correction** = source inconsistency resolved.

| ID | Decision | Status / rationale | Consequence |
|---|---|---|---|
| TD-001 | FD001 first | Retained; one condition, one HPC fault mode | Shared code parameterized by subset; only FD001 executed initially |
| TD-002 | RUL cap 125 cycles | Retained; common benchmark convention, no performance tuning here | Store `rul_raw` and capped `rul`; cap is configurable |
| TD-003 | Window length 30 cycles | Retained; sufficient initial history without excessive memory | Drop first 29 cycles per engine; no padding by default |
| TD-004 | Seed 42, validation fraction 0.20 | New explicit default | Deterministic engine-level permutation; 80 fit / 20 validation for FD001 |
| TD-005 | Python >=3.11,<3.14; CPU | New compatible range | Actual tested version and lockfile recorded; no GPU dependency |
| TD-006 | uv + pyproject + lockfile | Retained requirement | `uv sync --locked` is the reproducible install path |
| TD-007 | Raw immutability and local-only NASA data | New conservative distribution policy | NASA catalog says license not specified; do not commit/redistribute raw or derived data by default |
| TD-008 | Official NASA benchmark archive | Correction | Supplied simulator page has no data and a software-availability notice; separate NASA PCoE benchmark catalog exposes `CMAPSSData.zip` |
| TD-009 | 26 columns = 2 IDs + 3 settings + 21 sensors | Correction | NASA prose's final `sensor measurement 26` is a typo; verify actual files |
| TD-010 | Strict whitespace ingestion | New | No headers; exact column count; integer-valued IDs/cycles; finite numeric values; reject ragged rows |
| TD-011 | RUL file aligned by sorted test engine IDs | New documented benchmark convention | Validate vector length and official test ID order; preserve source vector; no invented engine IDs in RUL file |
| TD-012 | Exclude globally constant sensors s_1,s_5,s_10,s_16,s_18,s_19 from features | New, subject to real EDA verification | Retain them in raw/cycle data; do not remove merely for low correlation |
| TD-013 | Retain s_6 initially despite near-constant behavior | New conservative choice | Document low variance; StandardScaler handles nonzero variance; no silent deletion |
| TD-014 | Retain setting_1/setting_2; exclude constant setting_3 from features | New FD001-specific choice | Context retained; revisit for FD002/FD004 regimes |
| TD-015 | Global StandardScaler | New initial choice justified by FD001 single-condition scope | Fit only `train_fit`; transform validation/test; no regime clustering without demonstrated need |
| TD-016 | Causal rolling mean/std (5,10) and first difference | New compact initial feature set | 17 current inputs + 60 rolling + 15 differences = 92 features; min/max/slope supported but disabled |
| TD-017 | Rolling sample standard deviation ddof=1 | New explicit convention | Full window required; distinguish from StandardScaler population ddof=0 |
| TD-018 | Complete windows only; no padding | New leakage-safe default | Short sequences may yield zero windows; report exclusions |
| TD-019 | float32 window/sequence arrays, float64 intermediate calculations | New memory policy | Labels/IDs integer; document cast tolerance; checksums and shapes retained |
| TD-020 | JSON scaler parameters, Parquet tables, NPZ arrays | New auditable formats | No pickle dependency for preprocessing state; explicit feature order |
| TD-021 | No predictive estimator fitting | Retained absolute restriction | Only preprocessing statistics are estimated; no M5 code |
| TD-022 | Conservative GitHub publication | New | Commit code/docs/lock/configs and small reviewed reports; exclude data, caches, credentials, environments, and large arrays |
| TD-023 | Report actual execution evidence only | Retained | Logs include commands, versions, hashes, test counts, timestamps; remote CI/push/local-machine checks remain pending until performed |
| TD-024 | Causal rolling warmup: `min_periods=1`, initial rolling std/difference = 0 | New refinement before M4 | Full rolling history would make cycles 1–9 NaN and either break 30-cycle windows or shift the first window to cycle 39. Expanding warmups use only current/past data, preserve complete 30-cycle windows ending at cycle 30, and avoid future padding. Cap 125 and window 30 unchanged. |

## Review policy
Changing a retained decision requires a documented technical reason, configuration version change, regenerated artifacts, and rerun acceptance tests. No change to 125/30 is made in this implementation. Sensor exclusions are verified against actual FD001 EDA before Milestone 4; if the evidence differs, this record must be amended before processing.

## Source investigation at planning time
On 2026-11-07, the supplied NASA simulator page was accessible but explicitly said C-MAPSS/C-MAPSS40K software were unavailable for download and listed no data resources. The separate NASA `CMAPSS Jet Engine Simulated Data` catalog was accessible, public, and described all four benchmark subsets. A streaming HTTPS GET of its linked archive returned HTTP 200, content length 12,425,978 bytes, and ZIP magic bytes from NASA's S3 backend. An initial HEAD attempt failed with TLS EOF; a subsequent GET succeeded. This is recorded as a transient transport issue, not evidence that the benchmark is unavailable. Full archive checksum/content verification is a Milestone 2 gate, not assumed here.
