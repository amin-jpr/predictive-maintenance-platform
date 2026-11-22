# Problem formulation and RUL semantics

## Task distinctions
- **Condition monitoring:** estimate/track current health from observations; does not necessarily predict time to failure.
- **Anomaly detection:** identify deviations from normal behavior; an anomaly is not automatically a failure or a RUL estimate.
- **Failure prediction:** classify whether failure occurs within a specified horizon; horizon and class definitions matter.
- **RUL regression:** predict remaining operational cycles from a prediction origin. This project prepares data for this last task but does not fit a predictor.

## Indexing convention
Cycles are one-based: `t in {1,...,T}`. Engine identity is `(subset, split, engine_id)`. The same numeric ID in train and test does not identify the same physical/simulated engine. Each row is one cycle-level snapshot. The supplied primary NASA simulator page describes 1 Hz full-flight recordings; that description is **not** the schema of this benchmark. The benchmark catalog and original files govern this project.

## Training endpoint
For a run-to-failure training engine, let `T_failure` be its final observed cycle. The benchmark defines this endpoint as failure. Raw remaining life after cycle `t` is:

```text
RUL_raw(t) = T_failure - t
RUL(t) = min(RUL_max, T_failure - t)
RUL_max = 125 cycles
```

At the final training cycle the label is zero. Early-life labels are capped at 125. The cap limits the influence of an arbitrary long healthy plateau and implements a common PHM benchmark convention; it is not a physical maximum lifetime. The original dataset does not require clipping: both raw and capped labels are retained. No model-performance evidence is used to choose 125 in these milestones.

## Test endpoint and reconstruction
The final observed test cycle `L_i` is **not** failure. Let `r_i` be the corresponding entry in `RUL_FD001.txt`, aligned to test engines in their official order (verified as sorted numeric IDs for the distributed files). Then:

```text
F_i = L_i + r_i                 # inferred failure cycle on the test engine's cycle axis
RUL_raw(i,t) = F_i - t = r_i + (L_i - t)
RUL(i,t) = min(125, RUL_raw(i,t))
```

`F_i` is an inferred benchmark endpoint, not an observed test failure. Every available test observation receives a reconstructed label for offline evaluation only. Test labels never participate in fitting, feature selection, scaler fitting, or split selection. Test windows are generated only from test measurements available through their ending cycle.

## Window prediction origin
A length-`W` window ending at `e` contains cycles `[e-W+1, ..., e]`, all from one engine. Its target is the label at `e`. Default `W=30`. No centered windows, forward fill from future observations, backward filling, interpolation using future values, or cross-engine rolling is allowed. Incomplete initial windows are dropped by default rather than padded with future information.

## Censoring and interpretation
Training sequences are run-to-failure; test sequences are right-censored at `L_i`. The ground-truth vector supplies the missing remaining life for benchmark evaluation. This is not a general survival-analysis solution for arbitrary censored field data. RUL is conditional on the simulated degradation process and benchmark endpoint, not a guaranteed safe operating interval for a real engine.

## Leakage boundaries
- Engine leakage: fit and validation engine sets must be disjoint.
- Temporal leakage: a feature/window at `e` may use only rows with cycle <= `e` from that engine.
- Preprocessing leakage: scaler statistics come only from official-train engines assigned to `train_fit`.
- Selection leakage: initial sensor exclusions are fixed in a versioned config after descriptive FD001 EDA; no automatic validation/test-driven selection is performed.
- Test contamination: official test data are never concatenated into fit/validation data.
- Target leakage: RUL, failure endpoints, split labels, and future measurements are never feature columns.

## Scientific acceptance
Correctness is established by independent arithmetic checks, schema checks, boundary tests, perturbation tests, and reproducibility checks—not by predictive performance.
