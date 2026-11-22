# Project scope and milestone boundary

## Included
Milestone 0: scientific/technical definition. Milestone 1: reproducible repository/environment. Milestone 2: FD001 acquisition, immutable ingestion, validation. Milestone 3: executed EDA and scientific interpretation. Milestone 4: labels, engine splits, preprocessing, causal features, sequences, windows, artifacts, and leakage tests.

## Explicitly excluded
No Random Forest, Linear Regression, XGBoost, neural network, LSTM, GRU, CNN, Transformer, or any other predictive estimator is fitted. No hyperparameter search, model comparison, model selection, accuracy claim, or model-training pipeline is implemented. No preliminary predictive experiment is permitted. `sklearn.preprocessing.StandardScaler` is permitted because it estimates feature normalization parameters, not RUL predictions.

## Dataset scope
FD001 is the initial implementation and execution target. FD002–FD004 are investigated and represented in subset metadata and parameterized paths. Their ingestion uses the same 26-column contract. Their different operating regimes/fault modes require a later documented review of sensor selection, regime handling, scaling, and split policy before execution; the architecture must not hard-code FD001 engine counts or sensor choices into shared algorithms.

## Why FD001 first
One nominal sea-level condition and one HPC fault mode reduce confounding while establishing correct RUL semantics, temporal boundaries, and leakage controls. It is large enough for meaningful engine-level validation (100 training and 100 official test engines) but small enough for CPU/8 GB workflows.

## Future extension strategy
1. Add/verify subset-specific source checksums and expected engine counts.
2. Run the same strict loader and integrity checks.
3. Perform subset-specific EDA, including operating-regime clustering/conditional behavior.
4. Record a new versioned preprocessing/sensor configuration; do not reuse FD001 constants blindly.
5. Re-run engine-disjoint splitting, training-only scaling, causal features, and leakage tests.
6. Keep official test data isolated. Never pool engine identities across subsets/splits without namespace qualifiers.

## Operational boundary
This assignment delivers local data preparation software, not a deployed maintenance service. No cloud compute is required. GitHub publication requires the user's account and is not performed here. Local installation on the user's computer is not assumed from workspace execution.
