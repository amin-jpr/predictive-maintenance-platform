"""Generate Milestone 5 evaluation figures from actual experiment results.

Every figure is derived from saved validation predictions and metrics — no illustrative
data. Figures are saved as PNG at 150 dpi with titles, axis labels, and units.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

MODEL_ORDER = [
    "median_baseline",
    "cycle_trend_baseline",
    "linear_regression",
    "random_forest",
    "hist_gradient_boosting",
]
MODEL_LABELS = {
    "median_baseline": "Median baseline",
    "cycle_trend_baseline": "Cycle-trend baseline",
    "linear_regression": "Linear regression",
    "random_forest": "Random forest",
    "hist_gradient_boosting": "HistGradientBoosting",
}


def _save(fig: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_model_comparison(comparison: pd.DataFrame, path: Path) -> Path:
    """Grouped bar comparison of MAE, RMSE, and mean NASA score (validation)."""
    ordered = comparison.set_index("model_name").reindex(
        [m for m in MODEL_ORDER if m in set(comparison["model_name"])]
    )
    labels = [MODEL_LABELS.get(name, name) for name in ordered.index]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    for ax, column, title, ylabel in (
        (axes[0], "mae", "MAE (validation)", "MAE [cycles]"),
        (axes[1], "rmse", "RMSE (validation)", "RMSE [cycles]"),
        (axes[2], "mean_nasa_score", "Mean NASA score (validation)", "Mean NASA score"),
    ):
        values = ordered[column].to_numpy(dtype=float)
        ax.bar(labels, values, color="#2b6cb0")
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.tick_params(axis="x", rotation=30)
        for bar, value in zip(ax.patches, values, strict=True):
            ax.annotate(
                f"{value:.2f}",
                (bar.get_x() + bar.get_width() / 2, value),
                ha="center",
                va="bottom",
                fontsize=8,
            )
    fig.suptitle("Milestone 5 model comparison on validation engines (FD001)")
    return _save(fig, path)


def plot_actual_vs_predicted(
    y_true: np.ndarray, predictions: dict[str, np.ndarray], path: Path
) -> Path:
    """Actual vs predicted RUL scatter, one panel per model (validation)."""
    names = [m for m in MODEL_ORDER if m in predictions]
    n_panels = len(names)
    n_cols = 3
    n_rows = int(np.ceil(n_panels / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(13, 4.2 * n_rows))
    axes_flat = np.atleast_1d(axes).ravel()
    limit = 130.0
    for ax, name in zip(axes_flat[:n_panels], names, strict=True):
        ax.scatter(y_true, predictions[name], s=4, alpha=0.35, color="#2b6cb0")
        ax.plot([0, limit], [0, limit], "r--", linewidth=1, label="ideal")
        ax.set_xlim(0, limit)
        ax.set_ylim(0, limit)
        ax.set_xlabel("Actual RUL [cycles]")
        ax.set_ylabel("Predicted RUL [cycles]")
        ax.set_title(MODEL_LABELS.get(name, name))
        ax.legend(fontsize=8)
    for ax in axes_flat[n_panels:]:
        ax.axis("off")
    fig.suptitle("Actual vs predicted RUL on validation engines (FD001)")
    return _save(fig, path)


def plot_residual_distribution(
    y_true: np.ndarray, predictions: dict[str, np.ndarray], path: Path
) -> Path:
    """Residual (predicted - actual) distributions per model (validation)."""
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for name in [m for m in MODEL_ORDER if m in predictions]:
        residuals = predictions[name] - y_true
        ax.hist(
            residuals,
            bins=60,
            alpha=0.45,
            label=MODEL_LABELS.get(name, name),
            density=True,
        )
    ax.axvline(0, color="black", linewidth=1)
    ax.set_xlabel("Residual = predicted - actual [cycles]")
    ax.set_ylabel("Density")
    ax.set_title("Validation residual distributions by model (FD001)")
    ax.legend(fontsize=8)
    return _save(fig, path)


def plot_feature_importance(importance: pd.DataFrame, path: Path, top_n: int = 20) -> Path:
    """Horizontal bar chart of the top Random Forest feature importances."""
    top = importance.head(top_n).iloc[::-1]
    fig, ax = plt.subplots(figsize=(10, max(4.0, 0.35 * len(top))))
    ax.barh(top["feature"], top["importance"], color="#2b6cb0")
    ax.set_xlabel("Random Forest impurity importance")
    ax.set_title(f"Top {top_n} Random Forest feature importances (validation-trained model)")
    return _save(fig, path)


def plot_per_engine_error(per_engine: pd.DataFrame, path: Path) -> Path:
    """Per-engine validation MAE for the best model, sorted by error."""
    ordered = per_engine.sort_values("mae")
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.bar(
        [f"engine {int(e)}" for e in ordered["engine_id"]],
        ordered["mae"].to_numpy(dtype=float),
        color="#2b6cb0",
    )
    ax.set_xlabel("Validation engine (official train fleet, held-out engines)")
    ax.set_ylabel("MAE [cycles]")
    ax.set_title("Per-engine validation MAE (best model, FD001)")
    ax.tick_params(axis="x", rotation=45)
    return _save(fig, path)
