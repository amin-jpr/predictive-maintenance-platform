# Project specification — Predictive Maintenance & RUL Prediction System

**Repository:** `predictive-maintenance-platform`  
**Specification version:** 1.0.0  
**Planning date:** 2026-11-07 (UTC execution clock; user timezone Asia/Tehran)  
**Implementation boundary:** Milestones 0–4 inclusive. Milestone 5 is not implemented.

## 1. Scientific objective
Prepare a reproducible, leakage-controlled data engineering and scientific validation foundation for remaining useful life (RUL) regression on simulated turbofan engines. The initial target is NASA C-MAPSS FD001: one operating condition and high-pressure-compressor (HPC) degradation. The system must turn immutable run-to-failure training sequences and censored official test sequences into documented cycle-level targets, engine-disjoint splits, causal features, fitted preprocessing parameters, and sliding windows.

This is a **simulated prognostics benchmark**, not a certified aircraft maintenance system. No claim of field reliability, physical failure diagnosis, or predictive accuracy is made.

## 2. Starting specification and workspace inspection
The workspace was inspected before implementation and was empty. No attached blueprint or earlier project files were available. Explicit decisions in the assignment are retained: FD001 first; initial RUL cap 125 cycles; initial window length 30 cycles; CPU-first; 8 GB local RAM; Python-first modular architecture. Additional defaults introduced here are recorded as new decisions, not as recovered historical decisions.

## 3. Problem and entities
- **Engine/unit:** one independently simulated engine trajectory. `(subset, split, engine_id)` is its identity; training engine 1 and test engine 1 are different engines.
- **Cycle:** one ordered operational observation, not a raw 1 Hz flight recording.
- **Inputs:** three operational settings and 21 sensor measurements, plus identifiers used only for grouping and temporal alignment.
- **Target:** integer cycles remaining after the current observation, optionally capped for training and evaluation conventions.
- **Training sequence:** observed through the benchmark failure endpoint.
- **Test sequence:** right-censored before failure; separate ground truth gives RUL at its final observed cycle.
- **Prediction origin:** the ending cycle of a causal history window.

## 4. Scope
In scope: source investigation; acquisition and integrity verification; strict ingestion; scientific EDA; train/test RUL construction; explicit sensor selection; engine-level splitting; training-only scaler fitting; causal feature engineering; sequence and window products; automated correctness tests; documentation; reproducible notebooks; GitHub handoff; engineering PDF and delivery archive.

Out of scope: fitting any predictive model, model selection, hyperparameter optimization, predictive performance comparison, deployment services, databases, experiment tracking, GPU frameworks, and real-aircraft certification. A preprocessing scaler is an unsupervised transformation, not a predictive model.

## 5. Functional requirements
1. Acquire the official NASA archive or accept a manually downloaded identical archive; verify TLS, ZIP safety, inventory, CRC, and observed SHA-256 pins.
2. Preserve raw bytes; extract only supported original files; never overwrite raw data silently.
3. Validate 26 numeric columns, integer identifiers/cycles, contiguous per-engine cycles, unique engine-cycle keys, finite values, sequence lengths, and RUL vector alignment.
4. Produce descriptive EDA independently of notebooks, with actual plots and machine-readable tables.
5. Generate raw and capped RUL labels with different training/test failure-endpoint logic.
6. Split official training engines deterministically into fit/validation groups; never include official test engines in fitting.
7. Select sensors explicitly in configuration; preserve all original measurements in raw and cycle-level products.
8. Compute only backward-looking features; fit StandardScaler only on the designated training-fit engines.
9. Generate complete, unpadded 30-cycle windows by default; retain engine, start/end cycle, label, feature order, shape, and dtype metadata.
10. Write checksums and manifests for source and derived artifacts; support regeneration from configuration.
11. Test label arithmetic, split isolation, scaler boundaries, causality, window boundaries, schemas, and reproducibility.

## 6. Non-functional requirements
- Python >=3.11,<3.14; actual tested version recorded in the environment report.
- CPU only; no GPU requirement. Target <=8 GB RAM; process one engine/split at a time for large products.
- `uv` lockfile and `uv sync --locked`; no reliance on globally installed packages for the documented workflow.
- Deterministic ordering and seeds; atomic output writes where practical; no in-place raw modification.
- Typed public interfaces, Ruff lint/format, mypy, pytest, and basic GitHub Actions CI.
- No credentials required. No automatic GitHub push or publication of NASA data.

## 7. Milestone sequence and gates
| Milestone | Deliverable | Independent acceptance gate |
|---|---|---|
| 0 | Specification, formulation, decisions, architecture, dictionary, contracts, evaluation plan | Document review and contract consistency check |
| 1 | Git repository, Python package, uv lock, tooling, CI, README | Install, lint, type check, and synthetic tests execute |
| 2 | Verified FD001 files, acquisition code, loader, validation, provenance | Real archive/files inspected; checksums and integrity checks pass |
| 3 | Executed EDA, plots, tables, interpretation, reproducible notebooks | Scripts and notebooks execute against real FD001; outputs inspected |
| 4 | Labels, splits, causal features, scaler, sequences, windows, manifests | Real pipeline executes; unit/integration/leakage tests pass |

A later milestone cannot be marked complete until its gate has evidence. Execution limitations remain pending, never inferred from code existence.

## 8. Initial technical decisions
See `docs/TECHNICAL_DECISIONS.md`. Defaults: RUL cap 125; window 30; seed 42; validation fraction 0.20; global StandardScaler; six globally constant FD001 sensors excluded from model-input features but retained in raw/cycle data; operational settings 1 and 2 retained, constant setting 3 excluded from features; rolling mean/std at 5 and 10 cycles plus first differences. These are initial engineering choices, not optimized or performance-validated choices.

## 9. Required handoff statement
The final report and README must state:

> Milestones 0–4 have been completed. The dataset acquisition, validation, exploratory analysis, preprocessing, and feature engineering infrastructure is prepared. No Machine Learning or Deep Learning model has been trained. Model development begins in Milestone 5.

This statement may be inserted only after the actual acceptance evidence supports it.

## 10. Deliverables
Source, configs, tests, scripts, executed notebooks, EDA/preprocessing reports, provenance/checksums, dependency lockfile, GitHub guide and upload manifest, deliverables manifest, A4 PDF engineering report, and a ZIP delivery archive. Large generated window arrays may be local-only if size makes distribution impractical; exact regeneration commands and checksums must accompany that decision.
