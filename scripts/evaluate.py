"""Evaluate Milestone 5 models from saved predictions and artifacts.

Reloads the validation predictions written by scripts/train.py, recomputes every metric
with the shared evaluation layer, verifies agreement with the saved metrics.json, reloads
each serialized model in-process to confirm it predicts finite values, and generates the
comparison table, per-engine error table, Random Forest feature-importance table, and all
figures under reports/.

Run: uv run python scripts/evaluate.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from predictive_maintenance.config import find_project_root, load_config  # noqa: E402
from predictive_maintenance.evaluation.figures import (  # noqa: E402
    plot_actual_vs_predicted,
    plot_feature_importance,
    plot_model_comparison,
    plot_per_engine_error,
    plot_residual_distribution,
)
from predictive_maintenance.evaluation.metrics import evaluate_regression  # noqa: E402
from predictive_maintenance.models import load_model, predict_model  # noqa: E402
from predictive_maintenance.models.dataset import load_milestone4_dataset  # noqa: E402

TOLERANCE = 1e-9


def main() -> int:
    root = find_project_root()
    experiment = load_config("model_experiment", root)
    outputs = experiment["outputs"]
    run_dir = root / str(outputs["experiments_dir"]) / str(outputs["run_id"])
    predictions_path = run_dir / "predictions.csv"
    metrics_path = run_dir / "metrics.json"
    if not predictions_path.is_file() or not metrics_path.is_file():
        raise FileNotFoundError(
            f"Missing training outputs in {run_dir}. Run scripts/train.py first."
        )

    dataset = load_milestone4_dataset(root)
    predictions_frame = pd.read_csv(predictions_path)
    with metrics_path.open("r", encoding="utf-8") as handle:
        saved_metrics = json.load(handle)

    y_true = predictions_frame["rul_actual"].to_numpy(dtype=float)
    if not np.array_equal(y_true, dataset.y_validation):
        raise ValueError("Saved predictions do not match the Milestone 4 validation targets.")
    model_names = [str(m) for m in experiment["models"]]
    predictions: dict[str, np.ndarray] = {}
    rows: list[dict[str, object]] = []
    for name in model_names:
        column = f"pred_{name}"
        if column not in predictions_frame.columns:
            raise ValueError(f"Missing prediction column '{column}' in {predictions_path}.")
        pred = predictions_frame[column].to_numpy(dtype=float)
        predictions[name] = pred
        metrics = evaluate_regression(y_true, pred)
        saved = saved_metrics["models"][name]["validation"]
        for key in ("mae", "rmse", "nasa_score", "mean_nasa_score"):
            if not np.isclose(metrics[key], saved[key], rtol=TOLERANCE, atol=1e-9):
                raise ValueError(
                    f"Metric mismatch for {name}/{key}: recomputed {metrics[key]} vs "
                    f"saved {saved[key]}."
                )
        artifact = root / str(saved_metrics["models"][name]["artifact_file"])
        estimator = load_model(artifact)
        if name == "cycle_trend_baseline":
            probe = predict_model(estimator, dataset.validation_cycles.reshape(-1, 1).astype(float))
        else:
            probe = predict_model(estimator, dataset.X_validation)
        if not np.allclose(probe, pred, rtol=1e-9, atol=1e-9):
            raise ValueError(f"Reloaded model '{name}' does not reproduce saved predictions.")
        rows.append(
            {
                "model_name": name,
                "dataset": dataset.metadata["subset"],
                "feature_set": dataset.metadata["feature_set"],
                "train_samples": dataset.metadata["n_train"],
                "validation_samples": dataset.metadata["n_validation"],
                "mae": metrics["mae"],
                "rmse": metrics["rmse"],
                "nasa_score": metrics["nasa_score"],
                "mean_nasa_score": metrics["mean_nasa_score"],
                "median_absolute_error": metrics["median_absolute_error"],
                "error_mean": metrics["error_mean"],
                "error_std": metrics["error_std"],
                "early_ratio": metrics["early_ratio"],
                "late_ratio": metrics["late_ratio"],
                "within_10_cycles": metrics["within_10_cycles"],
                "within_20_cycles": metrics["within_20_cycles"],
                "training_time_seconds": saved_metrics["models"][name]["training_time_seconds"],
                "random_seed": experiment["random_seed"],
                "model_artifact": saved_metrics["models"][name]["artifact_file"],
            }
        )
        print(f"{name}: verified MAE={metrics['mae']:.3f} RMSE={metrics['rmse']:.3f}")

    comparison = pd.DataFrame(rows)
    comparison_path = root / str(outputs["comparison_table"])
    comparison.to_csv(comparison_path, index=False)

    summary = comparison[
        [
            "model_name",
            "mae",
            "rmse",
            "nasa_score",
            "mean_nasa_score",
            "within_10_cycles",
            "training_time_seconds",
            "random_seed",
            "model_artifact",
        ]
    ].copy()
    summary["status"] = "success"
    summary_path = run_dir.parent / "experiment_summary.csv"
    summary.to_csv(summary_path, index=False)

    best_name = str(comparison.loc[comparison["mae"].idxmin(), "model_name"])
    print(f"Best validation model by MAE: {best_name}")

    per_engine_rows: list[dict[str, object]] = []
    keys = predictions_frame[["engine_id", "cycle"]].copy()
    keys["abs_error"] = np.abs(predictions[best_name] - y_true)
    grouped = keys.groupby("engine_id")["abs_error"]
    for engine_id, group in grouped:
        per_engine_rows.append(
            {
                "engine_id": int(engine_id),
                "n_cycles": int(len(group)),
                "mae": float(group.mean()),
            }
        )
    per_engine = pd.DataFrame(per_engine_rows)
    per_engine_path = root / str(outputs["per_engine_table"])
    per_engine.to_csv(per_engine_path, index=False)

    rf_artifact = root / str(saved_metrics["models"]["random_forest"]["artifact_file"])
    rf_estimator = load_model(rf_artifact)
    importances = np.asarray(rf_estimator.feature_importances_, dtype=float)
    importance_frame = pd.DataFrame(
        {"feature": dataset.feature_names, "importance": importances}
    ).sort_values("importance", ascending=False)
    importance_path = root / str(outputs["feature_importance_table"])
    importance_frame.to_csv(importance_path, index=False)

    figures_dir = root / str(outputs["figures_dir"])
    plot_model_comparison(comparison, figures_dir / "model_comparison.png")
    plot_actual_vs_predicted(y_true, predictions, figures_dir / "actual_vs_predicted.png")
    plot_residual_distribution(y_true, predictions, figures_dir / "residual_distribution.png")
    plot_feature_importance(importance_frame, figures_dir / "feature_importance.png")
    plot_per_engine_error(per_engine, figures_dir / "per_engine_validation_error.png")
    print(f"Figures written to {figures_dir}")
    print(f"Comparison table: {comparison_path}")
    print("Evaluation verification: PASS (metrics reproduced, artifacts reload and match)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
