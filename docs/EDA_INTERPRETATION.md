# EDA interpretation and sensor-selection review (FD001)

This document interprets executed Milestone 3 outputs. It is descriptive, not predictive. Source tables/figures are in `reports/eda/`.

## Dataset structure
- Training: 100 engines, 20,631 observations; sequence lengths 128–362 cycles, mean 206.31.
- Test: 100 engines, 13,096 observations; sequence lengths 31–303 cycles, mean 130.96.
- Schema: 26 columns = 2 identifiers + 3 operational settings + 21 sensors.
- Training sequences are run-to-failure. Test sequences are right-censored; terminal RUL is supplied separately.

## Operational settings
| Setting | Mean | Std | Min | Max | Unique values |
|---|---:|---:|---:|---:|---:|
| setting_1 | -0.000009 | 0.002187 | -0.0087 | 0.0087 | 158 |
| setting_2 | 0.000002 | 0.000293 | -0.0006 | 0.0006 | 13 |
| setting_3 | 100.0 | 0.0 | 100.0 | 100.0 | 1 |

FD001 is documented as one sea-level operating condition. The small variations in settings 1/2 are retained as context; setting 3 is constant and excluded from initial features. No operating-regime clustering is justified for FD001. FD002/FD004 require a separate regime review.

## Constant and near-constant sensors
Exact constants (unique-value count = 1): `s_1, s_5, s_10, s_16, s_18, s_19`. These provide no within-FD001 variation and are excluded from initial model-input features, but remain in raw/cycle-level products.

Near-constants (CV < 1e-4, not exact constant): `s_6, s_8, s_13`.
- `s_6` has only two observed values (21.60/21.61); retained initially as a conservative choice, not silently discarded.
- `s_8` and `s_13` are corrected/physical fan-speed channels with small but nonzero variation and some early-to-late shift; retained initially and monitored. StandardScaler handles nonzero variance.

No sensor is removed solely because global correlation is low.

## Degradation evidence
Early-life vs late-life means (first/last 30 cycles per engine) show consistent simulated degradation patterns:

| Sensor | Mean late − early | Fraction of engines positive | Interpretation |
|---|---:|---:|---|
| s_4 (LPT outlet temperature) | +20.13 | 1.00 | Strong consistent increase |
| s_3 (HPC outlet temperature) | +11.91 | 1.00 | Strong consistent increase |
| s_17 (bleed enthalpy) | +3.12 | 1.00 | Consistent increase |
| s_7 (HPC outlet total pressure) | -1.91 | 0.00 | Consistent decrease |
| s_12 (fuel flow/Ps30 ratio) | -1.63 | 0.00 | Consistent decrease |
| s_2 (LPC outlet temperature) | +1.00 | 1.00 | Consistent increase |
| s_11 (HPC outlet static pressure) | +0.61 | 1.00 | Consistent increase |
| s_20 (HPT coolant bleed) | -0.38 | 0.00 | Consistent decrease |
| s_21 (LPT coolant bleed) | -0.23 | 0.00 | Consistent decrease |
| s_9 (physical core speed) | +31.53 | 0.71 | Large mean shift but high engine variability |
| s_14 (corrected core speed) | +22.06 | 0.58 | Large mean shift but high engine variability |

These patterns are consistent with the benchmark's HPC degradation scenario, but they are not a physical fault diagnosis. Engine-to-engine variation is substantial and expected from initial wear/manufacturing variation.

## RUL characteristics
- Training raw RUL: 0–361 cycles, mean 107.81.
- Clipping at 125 cycles affects 38.93% of training observations; clipped mean 86.83.
- Official test terminal RUL: 7–145 cycles, mean 75.52.
- The cap is a benchmark modeling convention, not a physical lifetime limit. Both raw and capped labels are retained.

## Sensor-selection decision for Milestone 4
Retain 15 non-constant sensors: `s_2, s_3, s_4, s_6, s_7, s_8, s_9, s_11, s_12, s_13, s_14, s_15, s_17, s_20, s_21`. Retain `setting_1`, `setting_2`. Exclude exact constants and `setting_3` from features only. This matches TD-012 after EDA verification and keeps near-constants under review rather than silently deleting them.

## Limitations
Simulated single-condition/single-fault benchmark; descriptive statistics only; no predictive accuracy is estimated. Correlation does not imply causation. FD002–FD004 may require different sensor/regime/scaling decisions.
