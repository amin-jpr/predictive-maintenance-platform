"""Train Milestone 5 classical ML baselines on the Milestone 4 inputs.

Trains, in order: constant median baseline, cycle-trend simple baseline, optional
Linear Regression, Random Forest, HistGradientBoosting. Every model is fitted on the
train_fit split only and scored on the validation split. The official NASA test split
is never loaded.

Outputs (see configs/model_experiment.yaml):
  artifacts/classical_ml/<model>/<model>.joblib + metadata.json
  experiments/milestone_05/run_001/{config.yaml, metrics.json, metadata.json, predictions.csv}
  reports/tables/baseline_comparison.csv

Run: uv run python scripts/train.py
"""

from __future__ import annotations

import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import sklearn
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from predictive_maintenance.config import find_project_root, load_config  # noqa: E402
from predictive_maintenance.io import atomic_write_json, utc_now_iso  # noqa: E402
from predictive_maintenance.models import (  # noqa: E402
    build_baseline,
    build_cycle_trend_baseline,
    build_gradient_boosting,
    build_linear_regression,
    build_random_forest,
    predict_model,
    save_model,
    train_model,
)
from predictive_maintenance.models.dataset import load_milestone4_dataset  # noqa: E402

MODEL_CONFIG_FILES = {
    "median_baseline": "model_baseline.yaml",
    "cycle_trend_baseline": "model_baseline.yaml",
    "linear_regression": "model_linear.yaml",
    "random_forest": "model_rf.yaml",
    "hist_gradient_boosting": "model_hgb.yaml",
}
ARTIFACT_NAMES = {
    "median_baseline": "median_baseline.joblib",
    "cycle_trend_baseline": "cycle_trend_baseline.joblib",
    "linear_regression": "linear_regression.joblib",
    "random_forest": "random_forest.joblib",
    "hist_gradient_boosting": "hist_gradient_boosting.joblib",
}


def _git_sha(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        sha = result.stdout.strip()
        return sha if result.returncode == 0 and sha else "unavailable"
    except (OSError, subprocess.SubprocessError):
        return "unavailable"


def _build_estimator(name: str, root: Path) -> tuple[Any, dict[str, Any]]:
    config = load_config(MODEL_CONFIG_FILES[name].removesuffix(".yaml"), root)
    if name == "median_baseline":
        return build_baseline("median"), config
    if name == "cycle_trend_baseline":
        params = config["models"]["cycle_trend_baseline"]
        return build_cycle_trend_baseline(bool(params.get("fit_intercept", True))), config
    params = dict(config["params"])
    if name == "linear_regression":
        return build_linear_regression(params), config
    if name == "random_forest":
        return build_random_forest(params), config
    return build_gradient_boosting(params), config


def main() -> int:
    root = find_project_root()
    experiment = load_config("model_experiment", root)
    outputs = experiment["outputs"]
    artifacts_dir = root / str(outputs["artifacts_dir"])
    run_dir = root / str(outputs["experiments_dir"]) / str(outputs["run_id"])
    run_dir.mkdir(parents=True, exist_ok=True)

    dataset = load_milestone4_dataset(root)
    print(
        f"Loaded Milestone 4 inputs: train {dataset.X_train.shape}, "
        f"validation {dataset.X_validation.shape}, features {len(dataset.feature_names)}"
    )
    print(
        f"Train engines: {len(dataset.train_engines)}; validation engines: "
        f"{len(dataset.validation_engines)}; official test used: False"
    )

    model_names = [str(m) for m in experiment["models"]]
    comparison_rows: list[dict[str, Any]] = []
    predictions: dict[str, np.ndarray] = {}
    all_metrics: dict[str, Any] = {}
    started = time.perf_counter()

    for name in model_names:
        estimator, model_config = _build_estimator(name, root)
        if name == "cycle_trend_baseline":
            X_train = dataset.train_cycles.reshape(-1, 1).astype(float)
            X_val = dataset.validation_cycles.reshape(-1, 1).astype(float)
            feature_names = ["cycle"]
        else:
            X_train, X_val = dataset.X_train, dataset.X_validation
            feature_names = dataset.feature_names
        trained = train_model(
            name=name,
            estimator=estimator,
            X_train=X_train,
            y_train=dataset.y_train,
            X_validation=X_val,
            y_validation=dataset.y_validation,
            feature_names=feature_names,
            config=model_config,
        )
        val_pred = predict_model(trained.estimator, X_val)
        predictions[name] = val_pred
        artifact_path = artifacts_dir / name / ARTIFACT_NAMES[name]
        save_model(trained.estimator, artifact_path)
        metadata = {
            "model_name": name,
            "config": model_config,
            "feature_names": feature_names,
            "feature_order": feature_names,
            "target": dataset.metadata["target_column"],
            "target_cap": dataset.metadata["target_cap"],
            "dataset_identity": {
                "subset": dataset.metadata["subset"],
                "feature_set": dataset.metadata["feature_set"],
                "train_split": dataset.metadata["train_split"],
                "validation_split": dataset.metadata["validation_split"],
                "n_train": dataset.metadata["n_train"],
                "n_validation": dataset.metadata["n_validation"],
                "train_engines": dataset.train_engines,
                "validation_engines": dataset.validation_engines,
                "official_test_used": False,
            },
            "random_seed": experiment["random_seed"],
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "sklearn_version": sklearn.__version__,
            "created_at_utc": utc_now_iso(),
            "git_commit_sha": _git_sha(root),
            "training_time_seconds": trained.training_time_seconds,
            "train_metrics": trained.train_metrics,
            "validation_metrics": trained.validation_metrics,
            "artifact_file": str(artifact_path.relative_to(root)),
        }
        atomic_write_json(artifacts_dir / name / "metadata.json", metadata)
        all_metrics[name] = {
            "train": trained.train_metrics,
            "validation": trained.validation_metrics,
            "training_time_seconds": trained.training_time_seconds,
            "artifact_file": str(artifact_path.relative_to(root)),
        }
        vm = trained.validation_metrics
        comparison_rows.append(
            {
                "model_name": name,
                "dataset": dataset.metadata["subset"],
                "feature_set": dataset.metadata["feature_set"],
                "train_samples": dataset.metadata["n_train"],
                "validation_samples": dataset.metadata["n_validation"],
                "mae": vm["mae"],
                "rmse": vm["rmse"],
                "nasa_score": vm["nasa_score"],
                "mean_nasa_score": vm["mean_nasa_score"],
                "median_absolute_error": vm["median_absolute_error"],
                "error_mean": vm["error_mean"],
                "error_std": vm["error_std"],
                "early_ratio": vm["early_ratio"],
                "late_ratio": vm["late_ratio"],
                "within_10_cycles": vm["within_10_cycles"],
                "within_20_cycles": vm["within_20_cycles"],
                "training_time_seconds": trained.training_time_seconds,
                "random_seed": experiment["random_seed"],
                "model_artifact": str(artifact_path.relative_to(root)),
            }
        )
        print(
            f"{name}: MAE={vm['mae']:.3f} RMSE={vm['rmse']:.3f} "
            f"NASA={vm['nasa_score']:.1f} (mean {vm['mean_nasa_score']:.4f}) "
            f"train_time={trained.training_time_seconds:.2f}s"
        )

    predictions_frame = dataset.validation_keys.copy()
    predictions_frame["rul_actual"] = dataset.y_validation
    for name in model_names:
        predictions_frame[f"pred_{name}"] = predictions[name]
    predictions_frame.to_csv(run_dir / "predictions.csv", index=False)

    comparison = pd.DataFrame(comparison_rows)
    comparison_path = root / str(outputs["comparison_table"])
    comparison_path.parent.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(comparison_path, index=False)

    atomic_write_json(
        run_dir / "metrics.json",
        {
            "run_id": str(outputs["run_id"]),
            "generated_at_utc": utc_now_iso(),
            "models": all_metrics,
            "dataset": dataset.metadata,
        },
    )
    atomic_write_json(
        run_dir / "metadata.json",
        {
            "run_id": str(outputs["run_id"]),
            "generated_at_utc": utc_now_iso(),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "sklearn_version": sklearn.__version__,
            "git_commit_sha": _git_sha(root),
            "total_elapsed_seconds": time.perf_counter() - started,
            "dataset": dataset.metadata,
            "experiment_config": experiment,
        },
    )
    with (run_dir / "config.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(experiment, handle, sort_keys=False)
    print(f"Comparison table: {comparison_path}")
    print(f"Experiment records: {run_dir}")
    print(f"Artifacts: {artifacts_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
