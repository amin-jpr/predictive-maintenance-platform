# EDA summary — FD001

Generated: 2026-11-07T06:43:10+00:00

## Dataset overview
- Training engines: 100; observations: 20631.
- Test engines: 100; observations: 13096.
- Columns: 26 = 2 identifiers + 3 settings + 21 sensors.
- Training sequence length: min 128, max 362, mean 206.31.
- Test sequence length: min 31, max 303, mean 130.96.

## Sensor findings
- Exact constant sensors: ['s_1', 's_5', 's_10', 's_16', 's_18', 's_19'].
- Near-constant sensors (CV < 1e-4, not exact constant): ['s_6', 's_8', 's_13'].
- Missing values: 0 in validated raw data.
- Constant sensors are excluded from initial model-input features but retained in raw/cycle products.
- Near-constant sensors are not automatically removed; s_6 is retained initially, while s_8/s_13 are reviewed with degradation evidence.

## Degradation interpretation
- Several temperature/pressure/speed channels show systematic early-to-late shifts across engines, consistent with simulated HPC degradation.
- Engine-to-engine variation is substantial; initial wear/manufacturing variation is normal per NASA documentation.
- Low global correlation alone is not used as a removal criterion; temporal and engine-level behavior are inspected.

## RUL findings
- Training raw RUL range: 0–361 cycles; mean 107.81.
- Fraction of training observations above cap 125: 0.389.
- Official test terminal RUL range: 7–145 cycles; mean 75.52.
- Test sequences are censored before failure; terminal RUL comes from the separate ground-truth vector.

## Scientific caution
These are descriptive statistics from a simulated benchmark, not causal physical diagnosis or predictive performance. FD001 has one operating condition and one HPC fault mode; conclusions do not automatically transfer to FD002–FD004 or real aircraft.

## Generated figures
- `figures/engine_lifetime_histogram.png`
- `figures/sequence_length_distribution.png`
- `figures/sensor_distributions.png`
- `figures/sensor_correlation_heatmap.png`
- `figures/degradation_trajectories.png`
- `figures/degradation_summary.png`
- `figures/rul_distribution.png`
- `figures/rul_clipping_effect.png`
- `figures/train_test_comparison.png`
- `figures/setting_relationships.png`
