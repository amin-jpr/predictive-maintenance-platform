# Scientific validation and evaluation plan (Milestones 0–4)

## Acceptance philosophy
Evaluate software correctness, data integrity, temporal/scientific validity, and reproducibility. **Do not evaluate predictive accuracy.** No predictive model is fitted, so RMSE/MAE/model comparisons are not acceptance criteria and are not reported.

## Independent checks
1. **Source integrity:** compare downloaded archive SHA-256 to the observed pinned value; verify ZIP CRC and safe member paths; compare extracted file hashes; retain original readme/paper for provenance.
2. **Schema:** independent line-level field count and numeric parsing checks; exact column contract; integer-valued IDs/cycles.
3. **Sequence integrity:** per-engine contiguous cycles, unique keys, positive lengths, expected subset counts, finite measurements.
4. **RUL arithmetic:** independent Python integer-loop reference for train and test labels; verify terminal training zero and test terminal ground truth; verify raw labels decrease by one per cycle.
5. **Split isolation:** set intersection empty; union equals official training IDs; official test absent from fit/validation; deterministic seed reproduction.
6. **Scaler boundary:** independently compute training-fit mean/std; compare persisted scaler; perturb validation/test values and verify scaler state unchanged; verify transform uses frozen parameters.
7. **Causality:** mutate future rows and verify earlier features unchanged; mutate another engine and verify no cross-engine influence; check rolling/difference warmups.
8. **Window boundaries:** exact shape `(n, W, F)`; start=end-W+1; contiguous cycles; single engine; target equals ending-cycle label; no incomplete windows; future-row perturbation leaves earlier windows unchanged.
9. **Output schema:** feature order, dtypes, finite values, label ranges, metadata consistency, manifest checksums.
10. **Reproducibility:** regenerate numerical outputs from the same raw/config and compare hashes excluding provenance timestamps; execute notebooks from clean kernels.
11. **No-training guard:** inspect dependencies/code for predictive estimator fitting; only StandardScaler is fitted. Tests assert no model artifacts/training entry points are introduced.

## Test layers
- Unit tests: small deterministic synthetic engines with known endpoints, short sequences, duplicates, gaps, non-finite values, wrong column counts, RUL vector mismatches, scaler leakage attempts, and feature/window boundary cases.
- Integration tests: synthetic end-to-end pipeline; real FD001 pipeline when raw files exist; artifact manifest verification; independent label reconstruction on real data.
- CI: lint, format, type check, and non-data tests on supported Python versions. CI does not silently download external data or claim full real-data acceptance.
- Local full acceptance: `uv run pytest` after acquisition, plus documented preprocessing/EDA commands and notebook execution.

## Evidence policy
Every claimed pass must come from an executed command whose output was inspected. Store terminal logs, pytest results, validation JSON, EDA tables, preprocessing summaries, and checksums. Remote GitHub Actions, GitHub push, and user-local installation are separate pending actions until actually verified. Failed/pending items remain visible in `IMPLEMENTATION_PROGRESS.md`.

## Future Milestone 5 evaluation (plan only; not executed)
Only after this handoff may predictive models be trained. Proposed metrics then include RMSE, MAE, and the PHM asymmetric scoring function on official test data, with engine-disjoint validation for model selection. Clipped/raw target conventions must be declared. These are future plans, not results of this assignment.
