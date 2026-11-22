"""CLI: build causal features, training-only scaler, sequences, and windows."""

from __future__ import annotations

import argparse

from predictive_maintenance.config import find_project_root
from predictive_maintenance.preprocessing.pipeline import build_feature_products


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build causal feature products (no predictive model training)."
    )
    parser.add_argument("--subset", default="FD001")
    args = parser.parse_args(argv)
    root = find_project_root()
    summary = build_feature_products(root, args.subset)
    print(f"Feature products complete for {args.subset}")
    print(f"Features: {summary['n_features']}; windows: {summary['window_counts']}")
    print(
        f"Scaler fit engines: {len(summary['scaler_fit_engines'])}; rows seen: {summary['scaler_n_samples_seen']}"
    )
    print(f"Artifacts: {summary['artifact_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
