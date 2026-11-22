# Known limitations and unresolved issues

## Execution boundaries
- The project was executed in an Arena.ai Linux sandbox, not on the user's local computer. Local installation/download is not assumed.
- GitHub repository creation, authentication, push, and remote Actions execution have not occurred. Exact instructions are provided.
- The sandbox reported ~1.9 GiB RAM, less than the user's 8 GB target. FD001 executed successfully, but this is not a formal peak-memory certification on the user's hardware.

## Dataset and licensing
- The supplied NASA simulator page is not the benchmark file source and carries a software-unavailability notice. The separate NASA PCoE benchmark catalog was used.
- Initial network attempts encountered transient TLS/timeouts; a retry succeeded. The archive is pinned by observed SHA-256.
- NASA benchmark license is **not specified**. Raw files, original paper, and derived data products are excluded from default GitHub publication and the delivery archive. Regeneration commands and checksums are provided.
- RUL ground-truth alignment uses the documented convention of sorted test engine IDs; the RUL file itself contains no engine IDs.

## Scientific scope
- FD001 only is executed. FD002–FD004 are cataloged and architecturally supported but require subset-specific EDA/regime/scaling review before processing.
- Findings are from simulated data, not real aircraft. No physical fault diagnosis or field reliability claim is made.
- RUL clipping at 125 is a benchmark convention, not a physical lifetime limit.
- Sensor selection is an initial explicit configuration, not an optimized or performance-validated choice.
- Near-constant sensors are retained initially; their utility is not established by predictive performance in these milestones.

## Technical refinements
- Constant-sensor detection uses unique-value count because floating-point std can be nonzero for exact constants.
- Rolling warmups use causal `min_periods=1` and zero initial std/difference (TD-024) to preserve 30-cycle windows without future information.
- NPZ files are written with fixed ZIP timestamps for deterministic checksums.
- Verification joins include split because train/test engine IDs are separate namespaces.
- Artifact manifests are generated after final metadata updates.

## Not done (by design)
- No predictive model training, hyperparameter optimization, model comparison, model selection, or accuracy claims.
- No deployment service, database, MLflow, Docker, or GPU framework.
- No Milestone 5 implementation.
