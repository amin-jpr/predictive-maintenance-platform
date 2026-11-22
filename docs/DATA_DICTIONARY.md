# Data dictionary

## Original benchmark columns (26; no header)
| Position | Name | Type | Meaning | Units / note |
|---:|---|---|---|---|
| 1 | engine_id | int64 | Engine/unit within a subset and split | Not globally unique across splits/subsets |
| 2 | cycle | int64 | Operational cycle, one-based | cycles |
| 3 | setting_1 | float64 | Operational setting 1 | Not explicitly named in benchmark readme |
| 4 | setting_2 | float64 | Operational setting 2 | Not explicitly named in benchmark readme |
| 5 | setting_3 | float64 | Operational setting 3 | Commonly interpreted as altitude-related; verify before physical claims |
| 6–26 | s_1 … s_21 | float64 | 21 sensor measurements | See table below |

NASA's benchmark prose incorrectly ends its column list with `sensor measurement 26`; the actual contract is 21 sensors and 26 total columns. The original files are authoritative.

## Sensor definitions
Definitions/units were verified against Table 2 of the original Saxena et al. PHM08 paper included in the NASA archive (`Damage Propagation Modeling.pdf`); they are not inferred from column names.

| Sensor | Description | Unit |
|---|---|---|
| s_1 | Total temperature at fan inlet | °R |
| s_2 | Total temperature at LPC outlet | °R |
| s_3 | Total temperature at HPC outlet | °R |
| s_4 | Total temperature at LPT outlet | °R |
| s_5 | Pressure at fan inlet | psia |
| s_6 | Total pressure in bypass-duct | psia |
| s_7 | Total pressure at HPC outlet | psia |
| s_8 | Physical fan speed | rpm |
| s_9 | Physical core speed | rpm |
| s_10 | Engine pressure ratio (P50/P2) | dimensionless |
| s_11 | Static pressure at HPC outlet | psia |
| s_12 | Ratio of fuel flow to Ps30 | pps/psia |
| s_13 | Corrected fan speed | rpm |
| s_14 | Corrected core speed | rpm |
| s_15 | Bypass ratio | dimensionless |
| s_16 | Burner fuel-air ratio | dimensionless |
| s_17 | Bleed enthalpy | unit not specified in source table |
| s_18 | Demanded fan speed | rpm |
| s_19 | Demanded corrected fan speed | rpm |
| s_20 | HPT coolant bleed | lbm/s |
| s_21 | LPT coolant bleed | lbm/s |

## Derived cycle-level fields
| Field | Type | Definition |
|---|---|---|
| rul_raw | int64 | Remaining cycles without cap |
| rul | int64 | `min(rul_max, rul_raw)`; target column |
| failure_cycle | int64 | Training only: final observed cycle, benchmark failure endpoint |
| inferred_failure_cycle | int64 | Test only: final observed test cycle + ground-truth terminal RUL |
| split | string | `train_fit`, `validation`, or `test` |
| subset | string | `FD001` in initial execution |

## Feature naming
- Current inputs: original `setting_*` / `s_*` names.
- `{sensor}_roll_mean_{w}`: arithmetic mean over the current and previous `w-1` cycles.
- `{sensor}_roll_std_{w}`: sample standard deviation (`ddof=1`) over the same causal window; full history required.
- `{sensor}_roll_min_{w}` / `{sensor}_roll_max_{w}`: optional causal extrema (disabled initially).
- `{sensor}_diff_1`: `x[t] - x[t-1]`, units per cycle.
- `{sensor}_trend_{w}`: optional ordinary least-squares slope against equally spaced cycle indices in a trailing window, units per cycle (disabled initially).

Initial feature count: 17 current values (15 sensors + 2 settings) + 15×2×2 rolling mean/std + 15 differences = **92**. Identifiers, RUL, failure endpoints, and split labels are metadata/targets, never features. Scaled columns retain the same names in a separate scaled product and are dimensionless z-scores.

## Window artifact fields
Per-engine NPZ contains `X` `(n_windows, 30, n_features)` float32, `y` `(n_windows,)` int64 capped RUL, `y_raw` int64, `engine_id`, `end_cycle`, `start_cycle`, and `cycle` arrays. A global CSV index records split, engine, start/end, target, row count, file path, shape, and checksum. Feature order is stored once in metadata and applies to every window.

## Missing-value policy
Original numeric fields must be finite. Missing/non-finite raw values cause validation failure; no silent imputation. Initial rolling/difference warmups are NaN by design and are excluded from complete windows. No forward/backward filling across engines or from future observations is used.
