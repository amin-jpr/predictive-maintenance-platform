"""Executed exploratory data analysis for C-MAPSS (descriptive only; no predictive fitting)."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from predictive_maintenance.config import find_project_root
from predictive_maintenance.data.loader import load_rul, load_test, load_train
from predictive_maintenance.data.schema import SENSOR_COLUMNS, SETTING_COLUMNS
from predictive_maintenance.data.validation import validate_subset
from predictive_maintenance.io import atomic_write_json, atomic_write_text, ensure_dir, utc_now_iso

sns.set_theme(style="whitegrid", context="notebook")
TRAJECTORY_SENSORS = ["s_2", "s_3", "s_4", "s_7", "s_11", "s_12", "s_14", "s_21"]
TRAJECTORY_ENGINES = [1, 20, 40, 60, 80, 100]
EARLY_LATE_CYCLES = 30


def load_eda_data(root: Path, subset: str) -> dict[str, Any]:
    report = validate_subset(root, subset)
    if report["status"] != "PASS":
        raise RuntimeError(f"Refusing EDA on invalid subset {subset}; run validation first")
    return {
        "train": load_train(root, subset),
        "test": load_test(root, subset),
        "rul": load_rul(root, subset),
    }


def _length_stats(frame: pd.DataFrame) -> dict[str, Any]:
    lengths = frame.groupby("engine_id").size()
    return {
        "engines": int(frame["engine_id"].nunique()),
        "observations": int(len(frame)),
        "min_cycle": int(frame["cycle"].min()),
        "max_cycle": int(frame["cycle"].max()),
        "min_length": int(lengths.min()),
        "max_length": int(lengths.max()),
        "mean_length": float(lengths.mean()),
        "median_length": float(lengths.median()),
        "std_length": float(lengths.std(ddof=1)),
    }


def dataset_overview(train: pd.DataFrame, test: pd.DataFrame, rul: np.ndarray) -> dict[str, Any]:
    return {
        "train": _length_stats(train),
        "test": _length_stats(test),
        "n_settings": len(SETTING_COLUMNS),
        "n_sensors": len(SENSOR_COLUMNS),
        "n_columns": train.shape[1],
        "rul_vector_length": int(len(rul)),
        "train_information": "Run-to-failure sequences; final observed cycle is benchmark failure endpoint.",
        "test_information": "Right-censored sequences; separate terminal RUL vector; final observed cycle is not failure.",
    }


def engine_lengths(train: pd.DataFrame, test: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split, frame in [("train", train), ("test", test)]:
        grouped = frame.groupby("engine_id")["cycle"].agg(["min", "max", "count"]).reset_index()
        grouped["split"] = split
        grouped = grouped.rename(columns={"count": "length", "max": "last_cycle"})
        rows.append(grouped)
    return pd.concat(rows, ignore_index=True)[["split", "engine_id", "length", "min", "last_cycle"]]


def sensor_statistics(train: pd.DataFrame) -> pd.DataFrame:
    records = []
    for col in SENSOR_COLUMNS:
        series = train[col]
        nunique = int(series.nunique())
        std = float(series.std(ddof=0))
        mean = float(series.mean())
        constant = nunique <= 1
        near = (not constant) and std > 0 and abs(mean) > 0 and std / abs(mean) < 1e-4
        records.append(
            {
                "sensor": col,
                "mean": mean,
                "std": std,
                "min": float(series.min()),
                "max": float(series.max()),
                "nunique": nunique,
                "missing": int(series.isna().sum()),
                "constant": constant,
                "near_constant": near,
            }
        )
    return pd.DataFrame(records)


def constant_sensor_report(stats: pd.DataFrame) -> pd.DataFrame:
    return stats[stats["constant"] | stats["near_constant"]].copy()


def correlation_matrix(train: pd.DataFrame) -> pd.DataFrame:
    return train[SETTING_COLUMNS + SENSOR_COLUMNS].corr(numeric_only=True)


def setting_statistics(train: pd.DataFrame) -> pd.DataFrame:
    records = []
    for col in SETTING_COLUMNS:
        series = train[col]
        records.append(
            {
                "setting": col,
                "mean": float(series.mean()),
                "std": float(series.std(ddof=0)),
                "min": float(series.min()),
                "max": float(series.max()),
                "nunique": int(series.nunique()),
            }
        )
    return pd.DataFrame(records)


def degradation_summary(
    train: pd.DataFrame, sensors: list[str] | None = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    sensors = sensors or SENSOR_COLUMNS
    per_engine_rows = []
    for engine_id, group in train.groupby("engine_id", sort=True):
        ordered = group.sort_values("cycle")
        early = ordered.head(EARLY_LATE_CYCLES)
        late = ordered.tail(EARLY_LATE_CYCLES)
        row: dict[str, Any] = {"engine_id": int(str(engine_id))}
        for sensor in sensors:
            early_mean = float(early[sensor].mean())
            late_mean = float(late[sensor].mean())
            row[f"{sensor}_early_mean"] = early_mean
            row[f"{sensor}_late_mean"] = late_mean
            row[f"{sensor}_late_minus_early"] = late_mean - early_mean
        per_engine_rows.append(row)
    per_engine = pd.DataFrame(per_engine_rows)
    summary_rows = []
    for sensor in sensors:
        diff = per_engine[f"{sensor}_late_minus_early"]
        summary_rows.append(
            {
                "sensor": sensor,
                "early_mean": float(per_engine[f"{sensor}_early_mean"].mean()),
                "late_mean": float(per_engine[f"{sensor}_late_mean"].mean()),
                "late_minus_early_mean": float(diff.mean()),
                "late_minus_early_std": float(diff.std(ddof=1)),
                "fraction_engines_positive": float((diff > 0).mean()),
            }
        )
    return pd.DataFrame(summary_rows), per_engine


def rul_analysis(
    train: pd.DataFrame, test: pd.DataFrame, rul: np.ndarray, cap: int = 125
) -> dict[str, Any]:
    failure_cycle = train.groupby("engine_id")["cycle"].transform("max")
    raw = (failure_cycle - train["cycle"]).to_numpy(dtype=np.int64)
    clipped = np.minimum(raw, cap)
    train_rul = pd.DataFrame(
        {
            "engine_id": train["engine_id"],
            "cycle": train["cycle"],
            "rul_raw": raw,
            "rul_clipped": clipped,
        }
    )
    lifetimes = train.groupby("engine_id")["cycle"].max().rename("lifetime")
    test_lengths = test.groupby("engine_id").size().rename("test_length")
    test_terminal = pd.DataFrame(
        {"engine_id": sorted(test["engine_id"].unique()), "terminal_rul": rul}
    )
    return {
        "cap": cap,
        "train_rul": train_rul,
        "lifetimes": lifetimes.reset_index(),
        "test_terminal": test_terminal,
        "test_lengths": test_lengths.reset_index(),
        "stats": {
            "train_raw_min": int(raw.min()),
            "train_raw_max": int(raw.max()),
            "train_raw_mean": float(raw.mean()),
            "train_clipped_mean": float(clipped.mean()),
            "fraction_capped": float((raw > cap).mean()),
            "test_terminal_min": int(rul.min()),
            "test_terminal_max": int(rul.max()),
            "test_terminal_mean": float(rul.mean()),
        },
    }


def save_figure(fig: plt.Figure, path: Path) -> Path:
    ensure_dir(path.parent)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_engine_lifetimes(lifetimes: pd.DataFrame, path: Path | None = None) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(lifetimes["lifetime"], bins=30, color="#2b6cb0", edgecolor="white")
    ax.set_xlabel("Training engine lifetime (cycles)")
    ax.set_ylabel("Number of engines")
    ax.set_title("FD001 training engine lifetime distribution")
    if path:
        save_figure(fig, path)
    return fig


def plot_sequence_lengths(lengths: pd.DataFrame, path: Path | None = None) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8, 5))
    for split, color in [("train", "#2b6cb0"), ("test", "#dd6b20")]:
        subset = lengths[lengths["split"] == split]["length"]
        ax.hist(subset, bins=30, alpha=0.6, label=split, color=color, edgecolor="white")
    ax.set_xlabel("Sequence length (cycles)")
    ax.set_ylabel("Number of engines")
    ax.set_title("Train vs test sequence length distribution")
    ax.legend()
    if path:
        save_figure(fig, path)
    return fig


def plot_sensor_distributions(train: pd.DataFrame, path: Path | None = None) -> plt.Figure:
    fig, axes = plt.subplots(7, 3, figsize=(16, 18))
    for ax, sensor in zip(axes.flat, SENSOR_COLUMNS, strict=False):
        ax.hist(train[sensor], bins=40, color="#3182ce", edgecolor="white")
        ax.set_title(sensor)
        ax.tick_params(labelsize=8)
    fig.suptitle("FD001 sensor distributions (training observations)", y=1.01)
    fig.tight_layout()
    if path:
        save_figure(fig, path)
    return fig


def plot_correlation_heatmap(corr: pd.DataFrame, path: Path | None = None) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(14, 12))
    sns.heatmap(
        corr,
        cmap="vlag",
        center=0,
        vmin=-1,
        vmax=1,
        square=True,
        ax=ax,
        cbar_kws={"label": "Pearson r"},
    )
    ax.set_title("FD001 operational-setting and sensor correlation matrix")
    if path:
        save_figure(fig, path)
    return fig


def plot_degradation_trajectories(
    train: pd.DataFrame,
    path: Path | None = None,
    sensors: list[str] | None = None,
    engines: list[int] | None = None,
) -> plt.Figure:
    sensors = sensors or TRAJECTORY_SENSORS
    engines = engines or TRAJECTORY_ENGINES
    fig, axes = plt.subplots(4, 2, figsize=(14, 14))
    for ax, sensor in zip(axes.flat, sensors, strict=False):
        for engine in engines:
            group = train[train["engine_id"] == engine].sort_values("cycle")
            ax.plot(group["cycle"], group[sensor], label=f"engine {engine}", alpha=0.8)
        ax.set_title(sensor)
        ax.set_xlabel("Cycle")
    axes.flat[0].legend(fontsize=8, loc="best")
    fig.suptitle("Example engine degradation trajectories", y=1.01)
    fig.tight_layout()
    if path:
        save_figure(fig, path)
    return fig


def plot_degradation_summary(summary: pd.DataFrame, path: Path | None = None) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 6))
    ordered = summary.sort_values("late_minus_early_mean")
    colors = ["#c53030" if value < 0 else "#2f855a" for value in ordered["late_minus_early_mean"]]
    ax.barh(ordered["sensor"], ordered["late_minus_early_mean"], color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Mean late-life minus early-life sensor value")
    ax.set_title("Average early-to-late sensor change across engines")
    if path:
        save_figure(fig, path)
    return fig


def plot_rul_distribution(result: dict[str, Any], path: Path | None = None) -> plt.Figure:
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
    train_rul = result["train_rul"]
    axes[0].hist(train_rul["rul_raw"], bins=50, color="#2b6cb0", edgecolor="white")
    axes[0].set_title("Training raw RUL")
    axes[1].hist(train_rul["rul_clipped"], bins=50, color="#3182ce", edgecolor="white")
    axes[1].set_title(f"Training RUL clipped at {result['cap']}")
    axes[2].hist(
        result["test_terminal"]["terminal_rul"], bins=30, color="#dd6b20", edgecolor="white"
    )
    axes[2].set_title("Official test terminal RUL")
    for ax in axes:
        ax.set_xlabel("RUL (cycles)")
        ax.set_ylabel("Count")
    fig.tight_layout()
    if path:
        save_figure(fig, path)
    return fig


def plot_rul_clipping(result: dict[str, Any], path: Path | None = None) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(6, 5))
    train_rul = result["train_rul"]
    ax.scatter(train_rul["rul_raw"], train_rul["rul_clipped"], s=2, alpha=0.2, color="#2b6cb0")
    ax.set_xlabel("Raw RUL (cycles)")
    ax.set_ylabel("Clipped RUL (cycles)")
    ax.set_title(f"Effect of RUL clipping at {result['cap']} cycles")
    if path:
        save_figure(fig, path)
    return fig


def plot_train_test_comparison(overview: dict[str, Any], path: Path | None = None) -> plt.Figure:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    metrics = [
        ("engines", "Engines"),
        ("observations", "Observations"),
        ("mean_length", "Mean sequence length"),
    ]
    for ax, (key, title) in zip(axes, metrics, strict=False):
        values = [overview["train"][key], overview["test"][key]]
        ax.bar(["train", "test"], values, color=["#2b6cb0", "#dd6b20"])
        ax.set_title(title)
    fig.tight_layout()
    if path:
        save_figure(fig, path)
    return fig


def plot_setting_relationships(train: pd.DataFrame, path: Path | None = None) -> plt.Figure:
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for ax, setting in zip(axes, SETTING_COLUMNS, strict=False):
        ax.hist(train[setting], bins=40, color="#805ad5", edgecolor="white")
        ax.set_title(setting)
    fig.suptitle("Operational-setting distributions (FD001)", y=1.02)
    fig.tight_layout()
    if path:
        save_figure(fig, path)
    return fig


def _write_summary_md(path: Path, summary: dict[str, Any]) -> None:
    stats = summary["sensor_stats"]
    constants = stats[stats["constant"]]["sensor"].tolist()
    near = stats[stats["near_constant"]]["sensor"].tolist()
    rul_stats = summary["rul_stats"]
    overview = summary["overview"]
    lines = [
        f"# EDA summary — {summary['subset']}",
        "",
        f"Generated: {summary['generated_at_utc']}",
        "",
        "## Dataset overview",
        f"- Training engines: {overview['train']['engines']}; observations: {overview['train']['observations']}.",
        f"- Test engines: {overview['test']['engines']}; observations: {overview['test']['observations']}.",
        f"- Columns: {overview['n_columns']} = 2 identifiers + {overview['n_settings']} settings + {overview['n_sensors']} sensors.",
        f"- Training sequence length: min {overview['train']['min_length']}, max {overview['train']['max_length']}, mean {overview['train']['mean_length']:.2f}.",
        f"- Test sequence length: min {overview['test']['min_length']}, max {overview['test']['max_length']}, mean {overview['test']['mean_length']:.2f}.",
        "",
        "## Sensor findings",
        f"- Exact constant sensors: {constants}.",
        f"- Near-constant sensors (CV < 1e-4, not exact constant): {near}.",
        "- Missing values: 0 in validated raw data.",
        "- Constant sensors are excluded from initial model-input features but retained in raw/cycle products.",
        "- Near-constant sensors are not automatically removed; s_6 is retained initially, while s_8/s_13 are reviewed with degradation evidence.",
        "",
        "## Degradation interpretation",
        "- Several temperature/pressure/speed channels show systematic early-to-late shifts across engines, consistent with simulated HPC degradation.",
        "- Engine-to-engine variation is substantial; initial wear/manufacturing variation is normal per NASA documentation.",
        "- Low global correlation alone is not used as a removal criterion; temporal and engine-level behavior are inspected.",
        "",
        "## RUL findings",
        f"- Training raw RUL range: {rul_stats['train_raw_min']}–{rul_stats['train_raw_max']} cycles; mean {rul_stats['train_raw_mean']:.2f}.",
        f"- Fraction of training observations above cap {summary['cap']}: {rul_stats['fraction_capped']:.3f}.",
        f"- Official test terminal RUL range: {rul_stats['test_terminal_min']}–{rul_stats['test_terminal_max']} cycles; mean {rul_stats['test_terminal_mean']:.2f}.",
        "- Test sequences are censored before failure; terminal RUL comes from the separate ground-truth vector.",
        "",
        "## Scientific caution",
        "These are descriptive statistics from a simulated benchmark, not causal physical diagnosis or predictive performance. FD001 has one operating condition and one HPC fault mode; conclusions do not automatically transfer to FD002–FD004 or real aircraft.",
        "",
        "## Generated figures",
    ]
    for figure in summary["figures"]:
        lines.append(f"- `{figure}`")
    atomic_write_text(path, "\n".join(lines) + "\n")


def run_eda(
    root: Path, subset: str = "FD001", output_dir: Path | None = None, cap: int = 125
) -> dict[str, Any]:
    data = load_eda_data(root, subset)
    train, test, rul = data["train"], data["test"], data["rul"]
    out = ensure_dir(output_dir or root / "reports" / "eda")
    tables = ensure_dir(out / "tables")
    figures = ensure_dir(out / "figures")

    overview = dataset_overview(train, test, rul)
    lengths = engine_lengths(train, test)
    stats = sensor_statistics(train)
    constants = constant_sensor_report(stats)
    corr = correlation_matrix(train)
    settings = setting_statistics(train)
    degradation, per_engine = degradation_summary(train)
    rul_result = rul_analysis(train, test, rul, cap=cap)

    lengths.to_csv(tables / "engine_lengths.csv", index=False)
    stats.to_csv(tables / "sensor_statistics.csv", index=False)
    constants.to_csv(tables / "constant_sensors.csv", index=False)
    corr.to_csv(tables / "correlation_matrix.csv")
    settings.to_csv(tables / "setting_statistics.csv", index=False)
    degradation.to_csv(tables / "degradation_summary.csv", index=False)
    per_engine.to_csv(tables / "degradation_per_engine.csv", index=False)
    rul_result["train_rul"].to_csv(tables / "train_rul_descriptive.csv", index=False)
    rul_result["lifetimes"].to_csv(tables / "engine_lifetimes.csv", index=False)
    rul_result["test_terminal"].to_csv(tables / "test_terminal_rul.csv", index=False)
    pd.DataFrame(
        [overview["train"] | {"split": "train"}, overview["test"] | {"split": "test"}]
    ).to_csv(tables / "train_test_comparison.csv", index=False)

    figure_paths = {
        "engine_lifetime_histogram.png": plot_engine_lifetimes(
            rul_result["lifetimes"], figures / "engine_lifetime_histogram.png"
        ),
        "sequence_length_distribution.png": plot_sequence_lengths(
            lengths, figures / "sequence_length_distribution.png"
        ),
        "sensor_distributions.png": plot_sensor_distributions(
            train, figures / "sensor_distributions.png"
        ),
        "sensor_correlation_heatmap.png": plot_correlation_heatmap(
            corr, figures / "sensor_correlation_heatmap.png"
        ),
        "degradation_trajectories.png": plot_degradation_trajectories(
            train, figures / "degradation_trajectories.png"
        ),
        "degradation_summary.png": plot_degradation_summary(
            degradation, figures / "degradation_summary.png"
        ),
        "rul_distribution.png": plot_rul_distribution(rul_result, figures / "rul_distribution.png"),
        "rul_clipping_effect.png": plot_rul_clipping(
            rul_result, figures / "rul_clipping_effect.png"
        ),
        "train_test_comparison.png": plot_train_test_comparison(
            overview, figures / "train_test_comparison.png"
        ),
        "setting_relationships.png": plot_setting_relationships(
            train, figures / "setting_relationships.png"
        ),
    }
    summary = {
        "generated_at_utc": utc_now_iso(),
        "subset": subset,
        "cap": cap,
        "overview": overview,
        "sensor_stats": stats.to_dict(orient="records"),
        "constant_sensors": stats[stats["constant"]]["sensor"].tolist(),
        "near_constant_sensors": stats[stats["near_constant"]]["sensor"].tolist(),
        "rul_stats": rul_result["stats"],
        "degradation_summary": degradation.to_dict(orient="records"),
        "figures": [f"figures/{name}" for name in figure_paths],
        "tables": [f"tables/{path.name}" for path in sorted(tables.glob("*.csv"))],
    }
    # Store DataFrame-free JSON summary.
    json_summary = {key: value for key, value in summary.items() if key != "sensor_stats"}
    json_summary["sensor_statistics_file"] = "tables/sensor_statistics.csv"
    atomic_write_json(out / "summary.json", json_summary)
    _write_summary_md(out / "summary.md", summary | {"sensor_stats": stats})
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run descriptive C-MAPSS EDA and generate reports/plots."
    )
    parser.add_argument("--subset", default="FD001")
    parser.add_argument("--cap", type=int, default=125)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    root = find_project_root()
    summary = run_eda(root, args.subset, args.output_dir, args.cap)
    print(f"EDA complete for {args.subset}")
    print(f"Figures: {len(summary['figures'])}; tables: {len(summary['tables'])}")
    print(f"Constant sensors: {summary['constant_sensors']}")
    print(f"Near-constant sensors: {summary['near_constant_sensors']}")
    print(f"RUL stats: {summary['rul_stats']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
