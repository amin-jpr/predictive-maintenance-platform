.PHONY: help install lock lint format typecheck test test-unit test-all download validate eda preprocess features notebooks report package clean

help:
	@echo "Targets: install lock lint format typecheck test test-unit test-all download validate eda preprocess features notebooks report package clean"

install:
	uv sync --locked

lock:
	uv lock

lint:
	uv run ruff check src tests scripts
	uv run ruff format --check src tests scripts

format:
	uv run ruff format src tests scripts
	uv run ruff check --fix src tests scripts

typecheck:
	uv run mypy

test:
	uv run pytest -m "not data_required"

test-unit:
	uv run pytest tests/unit -m "not data_required"

test-all:
	uv run pytest

download:
	uv run python scripts/download_dataset.py --subset FD001

validate:
	uv run python scripts/validate_dataset.py --subset FD001

eda:
	uv run python scripts/run_eda.py --subset FD001

preprocess:
	uv run python scripts/run_preprocessing.py --subset FD001

features:
	uv run python scripts/build_features.py --subset FD001

notebooks:
	uv run python scripts/run_notebooks.py

report:
	uv run python scripts/generate_report.py

package:
	uv run python scripts/package_delivery.py

clean:
	uv run python scripts/clean_generated.py
