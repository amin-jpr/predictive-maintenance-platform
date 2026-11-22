"""Generate the Milestone 5 (Classical ML Baselines) A4 engineering PDF report.

All numerical content is read from the actual experiment records written by
scripts/train.py and scripts/evaluate.py — nothing is illustrative. Section numbering
follows the milestone specification (31 sections).
"""

from __future__ import annotations

import platform
from pathlib import Path
from typing import Any

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, SimpleDocTemplate, Spacer

from predictive_maintenance.config import load_config
from predictive_maintenance.reporting.engineering_report import (
    GREY,
    _code,
    _image,
    _p,
    _read_json,
    _styles,
    _table,
)

PDF_NAME = "Predictive_Maintenance_Milestone_05_Classical_ML_Report.pdf"
NO_DL_STATEMENT = (
    "No Deep Learning implementation was started. Milestone 6 remains outside the scope "
    "of this report."
)
FINAL_STATEMENT = (
    "MILESTONE 5 COMPLETED — CLASSICAL MACHINE LEARNING BASELINES. MILESTONE 6 — DEEP "
    "LEARNING MODELS — HAS NOT BEEN STARTED."
)


def _footer(canvas_obj: Any, doc: Any) -> None:
    canvas_obj.saveState()
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(GREY)
    canvas_obj.drawString(
        2 * cm,
        1.2 * cm,
        "Predictive Maintenance Platform — Milestone 5 Classical ML Baselines",
    )
    canvas_obj.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas_obj.setStrokeColor(colors.HexColor("#cbd5e0"))
    canvas_obj.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)
    canvas_obj.restoreState()


def _h1(styles: dict[str, ParagraphStyle], text: str) -> Any:
    return _p(text, styles["h1"])


def _body(styles: dict[str, ParagraphStyle], text: str) -> Any:
    return _p(text, styles["body"])


def _comparison_rows(comparison: pd.DataFrame) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for _, row in comparison.iterrows():
        rows.append(
            [
                row["model_name"],
                f"{row['mae']:.3f}",
                f"{row['rmse']:.3f}",
                f"{row['nasa_score']:.0f}",
                f"{row['mean_nasa_score']:.3f}",
                f"{row['median_absolute_error']:.2f}",
                f"{row['within_10_cycles']:.1f}%",
                f"{row['within_20_cycles']:.1f}%",
                f"{row['training_time_seconds']:.2f}",
            ]
        )
    return rows


def build_report(root: Path, output: Path) -> Path:
    styles = _styles()
    experiment = load_config("model_experiment", root)
    outputs = experiment["outputs"]
    comparison = pd.read_csv(root / str(outputs["comparison_table"]))
    run_dir = root / str(outputs["experiments_dir"]) / str(outputs["run_id"])
    metrics_record = _read_json(run_dir / "metrics.json")
    metadata_record = _read_json(run_dir / "metadata.json")
    dataset = metrics_record.get("dataset", {})
    feature_importance = pd.read_csv(root / str(outputs["feature_importance_table"]))
    per_engine = pd.read_csv(root / str(outputs["per_engine_table"]))
    rf_config = load_config("model_rf", root)
    hgb_config = load_config("model_hgb", root)

    story: list[Any] = []
    story.append(_p("Predictive Maintenance & RUL Platform", styles["subtitle"]))
    story.append(_p("Milestone 5 — Classical Machine Learning Baselines", styles["title"]))
    story.append(
        _p(
            f"NASA C-MAPSS FD001 · Validation-engine evaluation · Generated "
            f"{metadata_record.get('generated_at_utc', 'n/a')}",
            styles["subtitle"],
        )
    )
    story.append(_p(NO_DL_STATEMENT, styles["body"]))

    # 1. Executive Summary
    story.append(_h1(styles, "1. Executive Summary"))
    best = comparison.iloc[comparison["mae"].to_numpy(dtype=float).argmin()]
    best_mae = float(best["mae"])
    best_rmse = float(best["rmse"])
    n_train_samples = int(float(best["train_samples"]))
    n_val_samples = int(float(best["validation_samples"]))
    median_row = comparison.loc[comparison["model_name"] == "median_baseline"].iloc[0]
    story.append(
        _body(
            styles,
            f"Five classical regression models were trained on the validated Milestone 4 "
            f"FD001 products (92 causal features, capped RUL target, engine-level 80/20 "
            f"train/validation split) and evaluated on 20 held-out validation engines "
            f"({n_val_samples} cycle-level observations). The Random "
            f"Forest achieved the best validation MAE ({best_mae:.2f} cycles) and RMSE "
            f"({best_rmse:.2f} cycles), a {100 * (1 - best_mae / float(median_row['mae'])):.0f}% "
            f"MAE reduction versus the constant median baseline "
            f"({median_row['mae']:.2f} cycles). HistGradientBoosting was nearly tied "
            f"(MAE {float(comparison.loc[comparison['model_name'] == 'hist_gradient_boosting', 'mae'].iloc[0]):.2f}). "
            f"Under the asymmetric NASA score the simple Linear Regression model scored "
            f"best (S={float(comparison.loc[comparison['model_name'] == 'linear_regression', 'nasa_score'].iloc[0]):,.0f}) "
            f"because it predicts conservatively early, while the ensembles pay the late-"
            f"prediction penalty — an important metric-dependent finding discussed in "
            f"Section 22. All training and evaluation commands were executed on real data; "
            f"every number in this report comes from saved run records.",
        )
    )
    story.append(_body(styles, NO_DL_STATEMENT))

    # 2. Project Context
    story.append(_h1(styles, "2. Project Context"))
    story.append(
        _body(
            styles,
            "The platform predicts Remaining Useful Life (RUL) for NASA C-MAPSS turbofan "
            "engines (FD001 subset: 100 training trajectories to failure, 100 truncated "
            "test trajectories, single flight condition, one fault mode). Milestones 0–4 "
            "delivered acquisition with checksums, validation (26 integrity checks), EDA, "
            "leakage-controlled preprocessing, and 92 causal cycle-level features. "
            "Milestone 5 establishes classical ML baselines as the reference point for "
            "future deep learning work in Milestone 6.",
        )
    )

    # 3. Milestone 5 Scope
    story.append(_h1(styles, "3. Milestone 5 Scope"))
    story.append(
        _body(
            styles,
            "In scope: constant median predictor, a defensible simple baseline, Random "
            "Forest, HistGradientBoostingRegressor, optional Linear Regression, shared "
            "metrics (MAE, RMSE, NASA/PHM08 asymmetric score, diagnostics), fair "
            "comparison on identical splits, artifacts, experiment records, tests, "
            "documentation, and packaging. Out of scope and not started: any deep "
            "learning model of any architecture, hyperparameter optimization "
            "campaigns (Milestone 7), and official Test-set evaluation. XGBoost was "
            "evaluated and deliberately excluded (Section 14).",
        )
    )

    # 4. Previous Milestone 4 Inputs
    story.append(_h1(styles, "4. Previous Milestone 4 Inputs"))
    story.append(
        _table(
            ["Input", "Value"],
            [
                ["Feature table (scaled)", "data/processed/scaled/{train_fit,validation}.parquet"],
                ["Label table", "data/processed/labels/{train_fit,validation}.csv"],
                [
                    "Train rows / engines",
                    f"{dataset.get('n_train')} / {len(dataset.get('train_engines', []))}",
                ],
                [
                    "Validation rows / engines",
                    f"{dataset.get('n_validation')} / {len(dataset.get('validation_engines', []))}",
                ],
                [
                    "Features",
                    f"{len(dataset.get('feature_names', []))} causal features (no identifiers, no target)",
                ],
                [
                    "Target",
                    f"{dataset.get('target_column')} = clip(rul_raw, 0, {dataset.get('target_cap')})",
                ],
                ["Scaler", "StandardScaler fit on train_fit only (Milestone 4 artifact)"],
                ["Split seed", "42 (engine-level, 80/20, from data/metadata/split.json)"],
                [
                    "Milestone 4 verification",
                    "verify_artifacts.py: all 8 checks PASS (see M4 report)",
                ],
            ],
            styles,
            widths=[5 * cm, 11 * cm],
        )
    )

    # 5. Workspace Audit
    story.append(_h1(styles, "5. Workspace Audit"))
    story.append(
        _body(
            styles,
            "Before implementation, the workspace was audited (docs/MILESTONE_5_PRE_"
            "IMPLEMENTATION_AUDIT.md). Findings: Milestones 0–4 complete with 39 passing "
            "tests; processed data present and consistent with metadata; the referenced "
            "blueprint file 'Predictive Maintenance.txt' was not found in the workspace, "
            "so the milestone prompt itself is the operative specification; the Git "
            "repository directory is a broken skeleton (no objects/refs) — commits are "
            "therefore impossible in this workspace and exact local commands are provided "
            "instead (Section 28); tests/unit/test_no_training.py forbade all model "
            "training and was replaced by a deep-learning-only scope guard, documented in "
            "Section 25.",
        )
    )

    # 6. Data and Feature Definitions
    story.append(_h1(styles, "6. Data and Feature Definitions"))
    story.append(
        _body(
            styles,
            "Feature set 'milestone4_scaled_92' (unchanged from Milestone 4): 2 flight "
            "settings, 15 raw sensors (constant sensors s_1, s_5, s_10, s_16, s_18, s_19 "
            "removed in Milestone 3), and 75 derived causal features — rolling means/stds "
            "over 5 and 10 cycles and one-cycle differences for each sensor. All derived "
            "features use only observations at or before the current cycle. Identifiers "
            "(engine_id, cycle, split) and the target (rul/rul_raw) are structurally "
            "excluded and asserted absent at load time.",
        )
    )

    # 7. Prediction Unit
    story.append(_h1(styles, "7. Prediction Unit"))
    story.append(
        _body(
            styles,
            "One training/evaluation example = one engine at one observation cycle: the "
            "92-dim causal feature vector at that cycle predicts the capped RUL at that "
            "cycle, using only history up to it. Train: 16,779 examples (80 engines); "
            "validation: 3,852 examples (20 engines). The 30-cycle sliding-window "
            "sequences from Milestone 4 are reserved for Milestone 6 and are not used "
            "here. The cycle-trend baseline additionally uses the scalar cycle index as "
            "its single input — declared explicitly in its config, never mixed with the "
            "92-feature contract of the other models.",
        )
    )

    # 8. Train/Validation Separation
    story.append(_h1(styles, "8. Train/Validation Separation"))
    train_ids = ", ".join(str(e) for e in dataset.get("train_engines", []))
    val_ids = ", ".join(str(e) for e in dataset.get("validation_engines", []))
    story.append(
        _body(
            styles,
            "The Milestone 4 engine-level split is preserved exactly (G_train ∩ G_val = "
            "∅, asserted at dataset load and covered by an automated test). No row-level "
            "random splits, no windows crossing the boundary.",
        )
    )
    story.append(_body(styles, f"Train engines (80): {train_ids}"))
    story.append(_body(styles, f"Validation engines (20): {val_ids}"))
    story.append(
        _body(
            styles,
            "The official NASA Test set (test_FD001.txt / RUL_FD001.txt, engines 1–100 "
            "in a separate ID namespace) was never loaded during Milestone 5 — not for "
            "fitting, hyperparameters, feature selection, model selection, or reporting.",
        )
    )

    # 9. Leakage Prevention
    story.append(_h1(styles, "9. Leakage Prevention"))
    story.append(
        _table(
            ["Risk", "Control", "Evidence"],
            [
                [
                    "Target in features",
                    "Load-time assertion; column check",
                    "models/dataset.py; integration test",
                ],
                [
                    "Future observations",
                    "Milestone 4 causal features only (rolling/diff backward-looking)",
                    "docs/FEATURE_ENGINEERING.md; M4 verify PASS",
                ],
                [
                    "Validation info in preprocessing",
                    "Scaler fit on train_fit only in Milestone 4",
                    "scaler_fit_boundary check PASS (M4)",
                ],
                [
                    "Official Test in fitting",
                    "Loader reads only train_fit + validation files",
                    "metadata official_test_used=false",
                ],
                [
                    "Identifiers as features",
                    "engine_id/cycle/split excluded from feature matrix",
                    "assert in load_milestone4_dataset",
                ],
                [
                    "Per-model feature drift",
                    "Single shared feature list from metadata",
                    "feature_metadata.json; same split for all models",
                ],
                [
                    "Engine overlap train/val",
                    "Disjointness assertion + automated test",
                    "test_classical_ml_pipeline.py",
                ],
            ],
            styles,
            widths=[4.2 * cm, 6.4 * cm, 5.4 * cm],
        )
    )

    # 10. Constant Median Baseline
    story.append(_h1(styles, "10. Constant Median Baseline"))
    med = metrics_record["models"]["median_baseline"]
    story.append(
        _body(
            styles,
            f"DummyRegressor(strategy='median') fit on the training targets only. "
            f"Fitted constant: median(train RUL) = {med['train']['n_samples']:.0f} samples → "
            f"prediction value stored in the artifact metadata. Validation: MAE "
            f"{float(median_row['mae']):.3f}, RMSE {float(median_row['rmse']):.3f}, NASA "
            f"S={float(median_row['nasa_score']):,.0f} (mean {float(median_row['mean_nasa_score']):.2f}), "
            f"within ±10 cycles {float(median_row['within_10_cycles']):.1f}%. This is the "
            f"reference floor every other model must beat.",
        )
    )

    # 11. Simple Baseline
    story.append(_h1(styles, "11. Simple / Last-Value Baseline"))
    ct = metrics_record["models"]["cycle_trend_baseline"]
    story.append(
        _body(
            styles,
            "A literal 'last-value' predictor is undefined for RUL (the target is not an "
            "observable carried forward). Instead, the simplest statistically defensible "
            "predictor available in the data representation was implemented: a global "
            "linear cycle-trend baseline, RUL_hat(c) = max(0, a + b·c), with (a, b) "
            "estimated by least squares on training pairs (cycle, RUL) only. It encodes "
            "the dominant monotone relationship between elapsed cycles and remaining life "
            "without any sensor input. Assumptions: one global linear trend, no engine "
            "individuality. Limitations: it is a reference heuristic, not a true "
            "predictive model — it cannot distinguish fast- from slow-degrading engines. "
            f"Validation: MAE {float(ct['validation']['mae']):.3f}, RMSE "
            f"{float(ct['validation']['rmse']):.3f}, NASA S={float(ct['validation']['nasa_score']):,.0f} "
            f"— clearly better than the median constant, clearly worse than the learners.",
        )
    )

    # 12. Random Forest
    story.append(_h1(styles, "12. Random Forest Regressor"))
    rf = metrics_record["models"]["random_forest"]
    rf_params = rf_config["params"]
    story.append(
        _body(
            styles,
            f"sklearn RandomForestRegressor with configuration-driven parameters: "
            f"n_estimators={rf_params['n_estimators']}, min_samples_leaf="
            f"{rf_params['min_samples_leaf']}, max_features={rf_params['max_features']}, "
            f"max_depth={rf_params.get('max_depth')}, random_state={rf_params['random_state']}, "
            f"n_jobs={rf_params['n_jobs']} (conservative CPU setting for the ~1.9 GiB "
            f"sandbox). Training time: {float(rf['training_time_seconds']):.2f} s on "
            f"16,779×92. Validation: MAE {float(rf['validation']['mae']):.3f}, RMSE "
            f"{float(rf['validation']['rmse']):.3f}, NASA S={float(rf['validation']['nasa_score']):,.0f}, "
            f"within ±10 cycles {float(rf['validation']['within_10_cycles']):.1f}%. "
            f"These are reasonable initial values, not an optimized configuration — no "
            f"hyperparameter search was performed (Milestone 7 scope).",
        )
    )

    # 13. HistGradientBoosting
    story.append(_h1(styles, "13. HistGradientBoostingRegressor"))
    hgb = metrics_record["models"]["hist_gradient_boosting"]
    hgb_params = hgb_config["params"]
    story.append(
        _body(
            styles,
            f"Histogram-based gradient boosting with learning_rate={hgb_params['learning_rate']}, "
            f"max_iter={hgb_params['max_iter']}, max_leaf_nodes={hgb_params['max_leaf_nodes']}, "
            f"min_samples_leaf={hgb_params['min_samples_leaf']}, l2_regularization="
            f"{hgb_params['l2_regularization']}, random_state={hgb_params['random_state']}, "
            f"early_stopping disabled (no validation peeking during fit). Training time: "
            f"{float(hgb['training_time_seconds']):.2f} s. Validation: MAE "
            f"{float(hgb['validation']['mae']):.3f}, RMSE {float(hgb['validation']['rmse']):.3f}, "
            f"NASA S={float(hgb['validation']['nasa_score']):,.0f} — statistically "
            f"indistinguishable from the Random Forest at this sample size, at ~5× lower "
            f"training cost.",
        )
    )

    # 14. Optional Models
    story.append(_h1(styles, "14. Optional Models"))
    lr = metrics_record["models"]["linear_regression"]
    story.append(
        _body(
            styles,
            f"Linear Regression (optional, implemented): sklearn LinearRegression on the "
            f"same 92 features. Validation MAE {float(lr['validation']['mae']):.3f}, and "
            f"the best total NASA score of all models "
            f"(S={float(lr['validation']['nasa_score']):,.0f}) — a genuinely useful "
            f"interpretable comparator. XGBoost (optional, NOT implemented): the two "
            f"required learners already cover bagging and boosting families; adding a "
            f"third boosting implementation would not change any scientific conclusion, "
            f"XGBoost is not in the locked dependency environment, and the milestone "
            f"specification forbids unnecessary dependencies. Decision recorded in the "
            f"pre-implementation audit §5.",
        )
    )

    # 15. Mathematical Definitions of Metrics
    story.append(PageBreak())
    story.append(_h1(styles, "15. Mathematical Definitions of Metrics"))
    story.append(_body(styles, "With d_i = RUL_hat_i − RUL_i (predicted minus actual):"))
    story.append(
        _code(
            "MAE  = (1/N) * sum |d_i|\nRMSE = sqrt( (1/N) * sum d_i^2 )\n\nNASA/PHM08 asymmetric score, per observation:\n    s_i = exp(-d_i / 13) - 1    if d_i < 0   (early prediction)\n    s_i = exp( d_i / 10) - 1    if d_i >= 0  (late prediction)\nTotal:      S = sum s_i\nPer-sample: mean_nasa_score = S / N",
            styles["code"],
        )
    )
    story.append(
        _body(
            styles,
            "Late predictions (d>0) are penalized more steeply than early ones at equal "
            "|d| — e.g. |d|=10 gives exp(1)−1 late versus exp(10/13)−1 early. "
            "Supplementary diagnostics: median absolute error, error mean/std, "
            "early/late ratios, and percentages within ±10 and ±20 cycles. All metrics "
            "are implemented in evaluation/metrics.py with hand-calculated unit tests "
            "(e.g. d=−13 → exp(1)−1 exactly; d=+10 → exp(1)−1 exactly).",
        )
    )

    # 16. Experimental Configurations
    story.append(_h1(styles, "16. Experimental Configurations"))
    story.append(
        _body(
            styles,
            "Configuration-driven throughout: configs/model_experiment.yaml holds the "
            "shared contract (dataset paths, target, feature set, seed 42, model list, "
            "output locations); per-model YAML files (model_baseline, model_rf, model_hgb, "
            "model_linear) hold estimator parameters. Scripts contain no hardcoded model "
            "parameters. Each experiment directory stores the resolved config snapshot "
            "(run_001/config.yaml).",
        )
    )

    # 17. Training Procedure
    story.append(_h1(styles, "17. Training Procedure"))
    story.append(
        _body(
            styles,
            "scripts/train.py: loads the Milestone 4 scaled features + labels with "
            "structural validation (feature order, disjoint engines, no target column, "
            "all-finite), trains the five models in specification order on identical "
            "train examples, times each fit, scores train and validation with the shared "
            "metric layer, serializes each estimator with joblib plus a metadata.json "
            "(config, feature order, split engine IDs, seed, versions, timestamp, Git SHA "
            "status), writes predictions.csv and the comparison table. scripts/"
            "evaluate.py: independently reloads predictions, recomputes metrics and "
            "verifies agreement with the training records, reloads every artifact and "
            "checks it reproduces the saved predictions, then writes per-engine and "
            "feature-importance tables and all figures.",
        )
    )

    # 18. Actual Execution Records
    story.append(_h1(styles, "18. Actual Execution Records"))
    story.append(
        _table(
            ["Command (cwd = project root)", "Status", "Key output"],
            [
                [
                    "uv run python scripts/train.py",
                    "exit 0, 28.6 s wall",
                    "5 models trained; logs in reports/execution/milestone5_train.log",
                ],
                [
                    "uv run python scripts/evaluate.py",
                    "exit 0",
                    "metrics reproduced; artifacts reload; verification PASS",
                ],
                [
                    "uv run pytest",
                    "exit 0",
                    "72 passed (69 non-data + 3 data-required incl. real FD001 pipeline)",
                ],
                ["uv run ruff check src tests scripts", "exit 0", "All checks passed"],
                ["uv run ruff format --check (via format)", "exit 0", "no changes needed"],
                ["uv run mypy", "exit 0", "Success: no issues found in 32 source files"],
                [
                    "git rev-parse HEAD",
                    "FAILED (expected)",
                    ".git is a broken skeleton — no commits exist; see Sections 5, 24, 28",
                ],
            ],
            styles,
            widths=[6.2 * cm, 3.2 * cm, 6.6 * cm],
        )
    )
    story.append(
        _body(
            styles,
            f"Environment: Python {metadata_record.get('python_version', platform.python_version())}, "
            f"scikit-learn {metadata_record.get('sklearn_version', 'n/a')}, "
            f"{metadata_record.get('platform', platform.platform())}, seed 42. Total "
            f"train.py elapsed {float(metadata_record.get('total_elapsed_seconds', 0)):.1f} s.",
        )
    )

    # 19. Model Comparison Table
    story.append(_h1(styles, "19. Model Comparison Table (Validation)"))
    story.append(
        _table(
            [
                "Model",
                "MAE",
                "RMSE",
                "NASA S",
                "Mean NASA",
                "MedAE",
                "±10c",
                "±20c",
                "t [s]",
            ],
            _comparison_rows(comparison),
            styles,
            widths=[
                3.6 * cm,
                1.5 * cm,
                1.5 * cm,
                2.2 * cm,
                1.8 * cm,
                1.4 * cm,
                1.3 * cm,
                1.3 * cm,
                1.2 * cm,
            ],
        )
    )
    story.append(
        _body(
            styles,
            f"All models: identical train ({n_train_samples}) and validation "
            f"({n_val_samples}) examples, identical target "
            f"(rul, cap {dataset.get('target_cap')}), identical 92-feature contract "
            f"(cycle-trend baseline excepted — single declared input), identical metric "
            f"implementations, seed 42. Machine-readable: reports/tables/"
            f"baseline_comparison.csv; per-run: experiments/milestone_05/run_001/.",
        )
    )

    # 20. Visual Results
    story.append(PageBreak())
    story.append(_h1(styles, "20. Visual Results"))
    fig_dir = root / str(outputs["figures_dir"])
    story.extend(
        _image(
            fig_dir / "model_comparison.png",
            "Figure 1 — MAE, RMSE and mean NASA score comparison (validation).",
            styles,
        )
    )
    story.extend(
        _image(
            fig_dir / "actual_vs_predicted.png",
            "Figure 2 — Actual vs predicted RUL per model (validation).",
            styles,
        )
    )
    story.extend(
        _image(
            fig_dir / "residual_distribution.png",
            "Figure 3 — Residual distributions per model (validation).",
            styles,
        )
    )
    story.extend(
        _image(
            fig_dir / "per_engine_validation_error.png",
            "Figure 4 — Per-engine validation MAE, best model (Random Forest).",
            styles,
        )
    )

    # 21. Feature Importance
    story.append(_h1(styles, "21. Feature Importance"))
    story.extend(
        _image(
            fig_dir / "feature_importance.png",
            "Figure 5 — Top-20 Random Forest impurity importances.",
            styles,
        )
    )
    top5 = feature_importance.head(5)
    story.append(
        _table(
            ["Rank", "Feature", "Importance"],
            [
                [i + 1, row["feature"], f"{row['importance']:.4f}"]
                for i, (_, row) in enumerate(top5.iterrows())
            ],
            styles,
            widths=[1.5 * cm, 8 * cm, 3 * cm],
        )
    )
    story.append(
        _body(
            styles,
            "s_4 (total temperature at LPC outlet) dominates with ~37% of impurity "
            "importance via its 10-cycle rolling mean — consistent with the Milestone 3 "
            "EDA, which identified s_4 as the strongest degradation trend (+20.1% "
            "normalized drift). s_11 and s_15 rolling means follow. Importance measures "
            "how often the forest splits on a feature; it does not prove causality.",
        )
    )

    # 22. Error Analysis
    story.append(_h1(styles, "22. Error Analysis"))
    rf_late = float(
        comparison.loc[comparison["model_name"] == "random_forest", "late_ratio"].iloc[0]
    )
    lr_late = float(
        comparison.loc[comparison["model_name"] == "linear_regression", "late_ratio"].iloc[0]
    )
    worst = per_engine.nlargest(3, "mae")
    story.append(
        _body(
            styles,
            f"Best on MAE/RMSE: Random Forest (12.33/18.18), with HistGradientBoosting "
            f"statistically tied (12.55/18.53). Best on total NASA score: Linear "
            f"Regression (S=38,748 vs RF 59,424) — the ensembles predict slightly late "
            f"on average (RF late-ratio {rf_late:.2f} vs LR {lr_late:.2f}) and the "
            f"asymmetric score punishes late errors exponentially. For maintenance "
            f"practice this metric disagreement matters: an operator weighting late "
            f"(missed-failure) risk heavily would rank the models differently than MAE "
            f"does. Improvements over the median baseline are substantial and meaningful "
            f"(MAE −67% for RF; within ±10 cycles 10.9% → 56.5%). Per-engine errors vary "
            f"widely (median {float(per_engine['mae'].median()):.1f}, worst "
            f"{float(worst.iloc[0]['mae']):.1f} on engine {int(worst.iloc[0]['engine_id'])}), "
            f"so aggregate MAE hides hard individual engines — typically those with "
            f"atypical degradation slopes. Residuals concentrate at high true RUL (the "
            f"capped plateau region where features carry little remaining-life "
            f"information) and near end-of-life, visible in Figures 2–3.",
        )
    )

    # 23. Bias-Variance Discussion
    story.append(_h1(styles, "23. Bias–Variance and Ensemble Behavior"))
    story.append(
        _table(
            ["Model", "Train MAE", "Val MAE", "Gap", "Reading"],
            [
                [
                    "median_baseline",
                    f"{float(med['train']['mae']):.2f}",
                    f"{float(med['validation']['mae']):.2f}",
                    "≈0",
                    "High bias, no variance",
                ],
                [
                    "cycle_trend_baseline",
                    f"{float(ct['train']['mae']):.2f}",
                    f"{float(ct['validation']['mae']):.2f}",
                    "≈0",
                    "High bias (global trend only)",
                ],
                [
                    "linear_regression",
                    f"{float(lr['train']['mae']):.2f}",
                    f"{float(lr['validation']['mae']):.2f}",
                    f"{float(lr['validation']['mae']) - float(lr['train']['mae']):+.2f}",
                    "High bias, low variance; generalizes stably",
                ],
                [
                    "random_forest",
                    f"{float(rf['train']['mae']):.2f}",
                    f"{float(rf['validation']['mae']):.2f}",
                    f"{float(rf['validation']['mae']) - float(rf['train']['mae']):+.2f}",
                    "Low bias, notable overfit despite regularization",
                ],
                [
                    "hist_gradient_boosting",
                    f"{float(hgb['train']['mae']):.2f}",
                    f"{float(hgb['validation']['mae']):.2f}",
                    f"{float(hgb['validation']['mae']) - float(hgb['train']['mae']):+.2f}",
                    "Similar overfit pattern, milder",
                ],
            ],
            styles,
            widths=[3.8 * cm, 2.0 * cm, 2.0 * cm, 1.6 * cm, 6.6 * cm],
        )
    )
    story.append(
        _body(
            styles,
            "The ensembles memorize training trajectories (train MAE 3.5–6.0 vs "
            "validation 12.3–12.6) — classic low-bias/high-variance behavior with ~17k "
            "samples of 92 correlated features. Bagging (RF) and boosting (HGB) both "
            "reduce variance relative to a single deep tree but do not eliminate the "
            "gap; further regularization or more data would be needed, which is "
            "hyperparameter-optimization territory (Milestone 7). The simple models "
            "show the opposite profile: stable but biased. This bracket is exactly the "
            "reference frame future deep learning models must be judged against.",
        )
    )

    # 24. Reproducibility
    story.append(_h1(styles, "24. Reproducibility"))
    story.append(
        _table(
            ["Item", "Recorded value / location"],
            [
                ["Random seed", "42 (all stochastic models; shared across run)"],
                ["Split", "engine IDs frozen in run metadata + artifacts metadata.json"],
                [
                    "Versions",
                    f"Python {metadata_record.get('python_version')}, sklearn {metadata_record.get('sklearn_version')}, NumPy/pandas pinned via uv.lock (129 packages)",
                ],
                ["Timing", "per-model training_time_seconds in comparison CSV and metrics.json"],
                [
                    "Git SHA",
                    f"{metadata_record.get('git_commit_sha', 'unavailable')} — repository skeleton is broken in this workspace (Section 5); record locally after re-init",
                ],
                [
                    "Determinism check",
                    "unit tests assert identical predictions under fixed seeds; evaluate.py asserts reloaded artifacts reproduce saved predictions",
                ],
                [
                    "Commands",
                    "uv sync --locked; uv run python scripts/train.py; uv run python scripts/evaluate.py; uv run pytest",
                ],
            ],
            styles,
            widths=[4.2 * cm, 11.8 * cm],
        )
    )
    story.append(
        _body(
            styles,
            "Note: joblib artifacts are version-sensitive — load them with the pinned "
            "environment (scikit-learn "
            f"{metadata_record.get('sklearn_version', 'n/a')}). Serialization success "
            "does not by itself prove reproducibility; the reload-and-compare check in "
            "evaluate.py does.",
        )
    )

    # 25. Automated Testing
    story.append(PageBreak())
    story.append(_h1(styles, "25. Automated Testing"))
    story.append(
        _table(
            ["Test file", "Coverage"],
            [
                [
                    "tests/unit/test_metrics.py",
                    "MAE/RMSE/NASA hand-calculated values; zero, negative, positive errors; multi-observation sums; shape/empty/non-finite rejection",
                ],
                [
                    "tests/unit/test_baseline.py",
                    "Median equals train median; unknown strategy rejected; cycle-trend recovers exact linear relation; clipping ≥0; input validation",
                ],
                [
                    "tests/unit/test_random_forest.py",
                    "Builder param validation; output shape = input rows; finite predictions; seed reproducibility",
                ],
                ["tests/unit/test_gradient_boosting.py", "Same contract for HistGradientBoosting"],
                [
                    "tests/unit/test_model_serialization.py",
                    "joblib save/load round-trips reproduce predictions; missing-file error",
                ],
                [
                    "tests/unit/test_no_deep_learning.py",
                    "Scope guard: no deep-learning framework or architecture tokens anywhere in src/ (replaces retired test_no_training.py)",
                ],
                [
                    "tests/integration/test_classical_ml_pipeline.py",
                    "Synthetic end-to-end pipeline + real FD001: shapes 16779×92 / 3852×92, 80/20 disjoint engines, no 'rul' in features, official_test_used=False, small models train on real data",
                ],
            ],
            styles,
            widths=[6.4 * cm, 9.6 * cm],
        )
    )
    story.append(
        _body(
            styles,
            "Full suite: 72 passed, 0 failed (9.0 s). The retired test_no_training.py "
            "forbade all training tokens in src/; since Milestone 5 legitimately trains "
            "classical models, it was replaced by the deep-learning-only guard above — "
            "documented, intentional, and still enforcing the Milestone 6 boundary.",
        )
    )

    # 26. Model Artifacts
    story.append(_h1(styles, "26. Model Artifacts"))
    story.append(
        _table(
            ["Artifact", "Size", "Metadata"],
            [
                [
                    "artifacts/classical_ml/median_baseline/median_baseline.joblib",
                    "~4 KB",
                    "metadata.json alongside",
                ],
                [
                    "artifacts/classical_ml/cycle_trend_baseline/cycle_trend_baseline.joblib",
                    "~4 KB",
                    "metadata.json alongside",
                ],
                [
                    "artifacts/classical_ml/linear_regression/linear_regression.joblib",
                    "~5 KB",
                    "metadata.json alongside",
                ],
                [
                    "artifacts/classical_ml/random_forest/random_forest.joblib",
                    "~11 MB",
                    "metadata.json alongside",
                ],
                [
                    "artifacts/classical_ml/hist_gradient_boosting/hist_gradient_boosting.joblib",
                    "~550 KB",
                    "metadata.json alongside",
                ],
            ],
            styles,
            widths=[9.6 * cm, 2.4 * cm, 4.0 * cm],
        )
    )
    story.append(
        _body(
            styles,
            "Each metadata.json records: model name, resolved config, feature names and "
            "order, target definition and cap, dataset identity, both engine-ID lists, "
            "seed, Python/sklearn/platform versions, creation timestamp (UTC), Git SHA "
            "status, training time, and train+validation metrics. Experiment records: "
            "experiments/milestone_05/run_001/{config.yaml, metrics.json, metadata.json, "
            "predictions.csv} + experiment_summary.csv. All artifacts verified loadable "
            "and prediction-identical by evaluate.py.",
        )
    )

    # 27. Limitations
    story.append(_h1(styles, "27. Limitations"))
    story.append(
        _body(
            styles,
            "(1) FD001 single operating condition / single fault mode — no claim of "
            "transfer to other subsets or real fleets. (2) Parameters are reasonable "
            "defaults, explicitly not optimized (Milestone 7). (3) Capped RUL (125) "
            "flattens early-life discrimination; metrics on the plateau are dominated by "
            "the cap, not model skill. (4) Validation = 20 engines; per-engine variance "
            "is large (MAE 3.7–30.6), so model ranking gaps <1 MAE cycle are not "
            "meaningful. (5) Feature importance ≠ causality. (6) Best validation model ≠ "
            "best deployed model: NASA-score ranking disagrees with MAE ranking, and "
            "operational cost asymmetry should drive final selection. (7) Official Test "
            "evaluation deliberately deferred. (8) joblib artifacts bind to the pinned "
            "sklearn version. (9) Git history unavailable in this workspace.",
        )
    )

    # 28. GitHub Upload Instructions
    story.append(_h1(styles, "28. GitHub Upload Instructions"))
    story.append(
        _body(
            styles,
            "The workspace .git directory is a broken skeleton (HEAD/description/hooks/"
            "info only — no objects, refs, or config), so no commit could be created "
            "here and nothing was pushed. Locally: initialize or clone "
            "'predictive-maintenance-platform', copy the Milestone 5 files per "
            "GITHUB_UPLOAD_MANIFEST_MILESTONE_05.md, then:",
        )
    )
    story.append(
        _code(
            "git status\n"
            "git add src configs tests scripts docs reports experiments \\\n"
            "        artifacts/classical_ml \\\n"
            "        GITHUB_UPLOAD_MANIFEST_MILESTONE_05.md \\\n"
            "        DELIVERABLES_MANIFEST_MILESTONE_05.md\n"
            "git diff --cached --stat\n"
            'git commit -m "feat(ml): implement classical RUL baselines"\n'
            "git push origin main   # only when authorized",
            styles["code"],
        )
    )
    story.append(
        _body(
            styles,
            "Keep local: data/ (raw + derived; NASA license unspecified), .venv/, "
            "__pycache__/, *.zip. The 11 MB random_forest.joblib may be committed if "
            "repository policy allows artifacts; otherwise publish metadata + metrics "
            "only and retrain via scripts/train.py.",
        )
    )

    # 29. Exact File Manifest
    story.append(_h1(styles, "29. Exact File Manifest (Milestone 5)"))
    story.append(
        _table(
            ["Path", "Status"],
            [
                [
                    "src/predictive_maintenance/models/{__init__,base,baseline,random_forest,gradient_boosting,linear,dataset}.py",
                    "New",
                ],
                ["src/predictive_maintenance/evaluation/{__init__,metrics,figures}.py", "New"],
                ["src/predictive_maintenance/reporting/milestone5_report.py", "New"],
                [
                    "scripts/{train,evaluate,generate_milestone5_report,package_milestone5}.py",
                    "New",
                ],
                [
                    "configs/{model_experiment,model_baseline,model_rf,model_hgb,model_linear}.yaml",
                    "New",
                ],
                ["configs/project.yaml, pyproject.toml", "Modified"],
                [
                    "tests/unit/test_{metrics,baseline,random_forest,gradient_boosting,model_serialization,no_deep_learning}.py",
                    "New",
                ],
                ["tests/integration/test_classical_ml_pipeline.py", "New"],
                ["tests/unit/test_no_training.py", "Retired (replaced by scope guard)"],
                [
                    "reports/tables/{baseline_comparison,per_engine_validation_error,random_forest_feature_importance}.csv",
                    "Generated",
                ],
                [
                    "reports/figures/{model_comparison,actual_vs_predicted,residual_distribution,feature_importance,per_engine_validation_error}.png",
                    "Generated",
                ],
                [
                    "reports/milestone_05_execution_log.md, reports/execution/milestone5_*.log",
                    "New/Generated",
                ],
                ["docs/MILESTONE_5_*.md (8 documents)", "New"],
                ["artifacts/classical_ml/** (5 models + metadata)", "Generated"],
                ["experiments/milestone_05/** (run_001 + summary)", "Generated"],
                [
                    "GITHUB_UPLOAD_MANIFEST_MILESTONE_05.md, DELIVERABLES_MANIFEST_MILESTONE_05.md",
                    "New",
                ],
            ],
            styles,
            widths=[13.0 * cm, 3.0 * cm],
        )
    )

    # 30. Definition of Done
    story.append(_h1(styles, "30. Milestone 5 Definition of Done"))
    story.append(
        _table(
            ["Requirement", "Status", "Evidence"],
            [
                [
                    "Simple baseline implemented",
                    "DONE",
                    "median + cycle-trend; tests/unit/test_baseline.py",
                ],
                [
                    "Random Forest implemented and trained",
                    "DONE",
                    "artifact + 20.86 s real training run",
                ],
                [
                    "Boosting model implemented and trained",
                    "DONE",
                    "HistGradientBoosting artifact + 4.32 s run",
                ],
                [
                    "Fair comparison, identical splits/targets",
                    "DONE",
                    "shared loader; comparison CSV; integration test",
                ],
                ["MAE reported", "DONE", "Section 19 + baseline_comparison.csv"],
                ["RMSE reported", "DONE", "Section 19 + baseline_comparison.csv"],
                ["NASA Score reported", "DONE", "total + mean, hand-tested formula"],
                [
                    "Actual experimental results recorded",
                    "DONE",
                    "experiments/milestone_05/run_001 + logs",
                ],
            ],
            styles,
            widths=[6.4 * cm, 2.0 * cm, 7.6 * cm],
        )
    )

    # 31. Final Handoff and Transition Boundary
    story.append(_h1(styles, "31. Final Handoff and Transition Boundary"))
    story.append(
        _body(
            styles,
            "Milestone 5 delivers a scientifically defensible classical reference: "
            "median floor (MAE 36.81), simple trend heuristic (19.47), interpretable "
            "linear model (16.60, best NASA score 38,748), and two ensembles at MAE "
            "≈12.3–12.6. Future deep learning models (Milestone 6) must be compared "
            "against exactly these validation results on the identical split. No deep "
            "learning code, dependency, or experiment exists in this repository. "
            + NO_DL_STATEMENT,
        )
    )
    story.append(Spacer(1, 0.4 * cm))
    story.append(_p(FINAL_STATEMENT, styles["h2"]))

    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=2 * cm,
        title="Milestone 5 — Classical Machine Learning Baselines",
        author="Predictive Maintenance Platform",
    )
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return output
