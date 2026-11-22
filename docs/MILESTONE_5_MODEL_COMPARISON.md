# Milestone 5 — Model Comparison and Error Analysis

All numbers below are the **actual recorded results** of run
`experiments/milestone_05/run_001` (validation = 20 held-out engines, 3,852 cycle-level
observations; train = 80 engines, 16,779 observations; seed 42; official NASA test never
used). Machine-readable source: `reports/tables/baseline_comparison.csv`.

## 1. Validation results

| Model | MAE ↓ | RMSE ↓ | NASA S ↓ | Mean NASA ↓ | MedAE | ±10 cyc | ±20 cyc | Early/Late | Train time |
|---|---|---|---|---|---|---|---|---|---|
| median_baseline | 36.810 | 46.310 | 6,909,743 | 1793.81 | 21.00 | 10.90% | 21.29% | 0.45/0.54 | 0.01 s |
| cycle_trend_baseline | 19.466 | 25.340 | 141,350 | 36.70 | 15.07 | 38.58% | 60.85% | 0.40/0.60 | 0.001 s |
| linear_regression (optional) | 16.599 | 20.588 | **38,748** | **10.06** | 14.21 | 36.11% | 66.25% | 0.43/0.57 | 0.07 s |
| **random_forest** | **12.333** | **18.176** | 59,424 | 15.43 | 8.05 | 56.54% | 80.04% | 0.56/0.43 | 20.86 s |
| hist_gradient_boosting | 12.550 | 18.528 | 62,688 | 16.27 | **7.90** | **57.11%** | 79.36% | 0.52/0.48 | 4.32 s |

**Best by MAE/RMSE: Random Forest** (12.33 / 18.18). HistGradientBoosting is statistically
tied (12.55 / 18.53) at ~5× lower training cost. **Best by total NASA score: Linear
Regression** (38,748) — see §4.

## 2. Improvements over the baselines are meaningful

- RF reduces MAE by **66.5%** vs the median constant (36.81 → 12.33) and **36.6%** vs the
  cycle-trend heuristic (19.47 → 12.33).
- Fraction of predictions within ±10 cycles rises 10.9% → 56.5% (median baseline → RF).
- Both ensembles beat every simple model on MAE, RMSE, MedAE, and both within-tolerance
  percentages. The margin (≥4 MAE cycles over linear) far exceeds the noise suggested by
  per-engine spread, so the ranking is not a tie — except RF vs HGB, which is.

## 3. Bias–variance behavior (train vs validation)

| Model | Train MAE | Val MAE | Gap | Reading |
|---|---|---|---|---|
| median_baseline | 35.518 | 36.810 | +1.29 | High bias, zero variance |
| cycle_trend_baseline | 21.788 | 19.466 | −2.32 | High bias; validation fleet slightly easier for a global trend |
| linear_regression | 16.306 | 16.599 | +0.29 | High bias, low variance — very stable |
| random_forest | 3.535 | 12.333 | +8.80 | Low bias on train, clear overfitting |
| hist_gradient_boosting | 5.956 | 12.550 | +6.59 | Same pattern, milder |

The ensembles memorize training trajectories (train MAE 3.5–6.0) yet generalize to ~12.3–12.6:
classic low-bias/high-variance behavior with 17k samples of 92 correlated features. Bagging
and boosting reduce but do not eliminate the gap. The simple models sit at the opposite pole.
This bracket is the reference frame for Milestone 6 comparisons. Further regularization or
tuning belongs to Milestone 7 — no tuning was performed here, and the chosen parameters are
**not** claimed optimal.

## 4. The NASA-score disagreement (metric matters)

Linear Regression has the *worst-ensemble-beating* MAE but the **best total NASA score**
(38,748 vs RF 59,424 and HGB 62,688). Reason: the asymmetric score punishes late
predictions (d>0, `exp(d/10)−1`) more steeply than early ones (d<0, `exp(−d/13)−1`), and
the ensembles err slightly late on average (RF late-ratio 0.43 with positive error mean
+2.50; LR error mean +3.01 but a thinner right tail — error std 20.4 vs 18.0 for RF, and
fewer extreme late outliers). Practically: an operator weighting missed-failure (late) risk
heavily could rationally prefer the linear model despite its worse MAE. Model ranking is
metric-dependent — both views are reported; neither is hidden.

## 5. Feature importance (Random Forest, impurity-based)

Top 10 (`reports/tables/random_forest_feature_importance.csv`):

| # | Feature | Importance |
|---|---|---|
| 1 | s_4_roll_mean_10 | 0.3706 |
| 2 | s_11_roll_mean_10 | 0.0987 |
| 3 | s_4_roll_mean_5 | 0.0986 |
| 4 | s_15_roll_mean_10 | 0.0621 |
| 5 | s_11_roll_mean_5 | 0.0424 |
| 6 | s_21_roll_mean_10 | 0.0339 |
| 7 | s_9_roll_mean_5 | 0.0338 |
| 8 | s_9_roll_mean_10 | 0.0334 |
| 9 | s_3_roll_mean_10 | 0.0186 |
| 10 | s_14_roll_mean_10 | 0.0139 |

`s_4` (total temperature at the low-pressure-compressor outlet) dominates via its rolling
means — consistent with the Milestone 3 EDA, which found s_4 to be the strongest degradation
trend (+20.1% normalized drift). Smoothed aggregates outweigh raw instantaneous sensors:
the forest prefers denoised trend features. **Importance measures split frequency/impurity
reduction — it does not prove causality.**

## 6. Per-engine error analysis (RF, validation)

`reports/tables/per_engine_validation_error.csv` — MAE ranges **3.72 → 30.59** cycles
(median 11.53, IQR 6.64–18.29):

- Hardest engines: 57 (30.59), 93 (24.22), 98 (23.69).
- Easiest engines: 51 (3.72), 82 (4.68), 25 (6.02).

An 8× spread between engines means aggregate MAE hides substantially harder individual
engines — typically trajectories with atypical degradation slopes or short observation
runs. This is a deployment-relevant caveat: fleet-level averages understate worst-case risk.

## 7. Error concentration by RUL range

Residual plots (`reports/figures/residual_distribution.png`,
`actual_vs_predicted.png`) show errors concentrate in two regions:

1. **High true RUL (capped plateau, rul = 125):** features carry little remaining-life
   information early in life; all models regress toward the middle. The cap itself
   flattens discrimination here — errors are partly an artifact of the target definition.
2. **Near end-of-life (low RUL):** the ensembles sometimes predict late (under-estimate
   degradation speed), exactly the region the NASA score punishes most.

## 8. Claims explicitly NOT made

- Feature importance does **not** prove causality.
- The best validation model is **not** necessarily the best model for real industrial
  equipment (single-condition FD001; metric-dependent ranking; per-engine spread).
- Configured parameters are reasonable defaults, **not** optimal (no search performed).
- RF vs HGB differences (<0.3 MAE cycles) are **not** meaningful with 20 validation engines.
