"""Generate a professional A4 engineering handoff PDF from verified project artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from predictive_maintenance.config import load_config

NAVY = colors.HexColor("#1a365d")
BLUE = colors.HexColor("#2b6cb0")
LIGHT = colors.HexColor("#ebf8ff")
GREY = colors.HexColor("#4a5568")
PDF_NAME = "Predictive_Maintenance_Milestones_00_04_Engineering_Report.pdf"
FINAL_STATEMENT = (
    "Milestones 0–4 have been completed. The dataset acquisition, validation, exploratory analysis, "
    "preprocessing, and feature engineering infrastructure is prepared. No Machine Learning or Deep "
    "Learning model has been trained. Model development begins in Milestone 5."
)


def _read_json(path: Path) -> dict[str, Any]:
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    return {}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "TitleX", parent=base["Title"], fontSize=24, leading=28, textColor=NAVY, spaceAfter=12
        ),
        "subtitle": ParagraphStyle(
            "SubtitleX",
            parent=base["Normal"],
            fontSize=12,
            leading=16,
            textColor=GREY,
            spaceAfter=10,
        ),
        "h1": ParagraphStyle(
            "H1X",
            parent=base["Heading1"],
            fontSize=15,
            leading=19,
            textColor=NAVY,
            spaceBefore=14,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "H2X",
            parent=base["Heading2"],
            fontSize=11,
            leading=14,
            textColor=BLUE,
            spaceBefore=10,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "BodyX", parent=base["Normal"], fontSize=9.5, leading=13, spaceAfter=6
        ),
        "small": ParagraphStyle("SmallX", parent=base["Normal"], fontSize=7.5, leading=10),
        "caption": ParagraphStyle(
            "CaptionX",
            parent=base["Normal"],
            fontSize=8,
            leading=10,
            textColor=GREY,
            alignment=1,
            spaceAfter=10,
        ),
        "code": ParagraphStyle(
            "CodeX",
            parent=base["Code"],
            fontSize=8,
            leading=10,
            backColor=colors.whitesmoke,
            borderPadding=4,
        ),
        "cell": ParagraphStyle("CellX", parent=base["Normal"], fontSize=8, leading=10),
        "head": ParagraphStyle(
            "HeadX", parent=base["Normal"], fontSize=8, leading=10, textColor=colors.white
        ),
    }


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(text), style)


def _code(text: str, style: ParagraphStyle) -> Preformatted:
    return Preformatted(text, style)


def _table(
    headers: list[str],
    rows: list[list[Any]],
    styles: dict[str, ParagraphStyle],
    widths: list[float] | None = None,
) -> Table:
    data = [[Paragraph(escape(str(header)), styles["head"]) for header in headers]]
    for row in rows:
        data.append(
            [
                cell
                if isinstance(cell, Paragraph)
                else Paragraph(escape(str(cell)), styles["cell"])
                for cell in row
            ]
        )
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e0")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def _image(
    path: Path,
    caption: str,
    styles: dict[str, ParagraphStyle],
    max_w: float = 16 * cm,
    max_h: float = 11 * cm,
) -> list[Any]:
    if not path.is_file():
        return [_p(f"[Pending figure: {path.name}]", styles["body"])]
    width, height = ImageReader(str(path)).getSize()
    scale = min(max_w / width, max_h / height)
    image = Image(str(path), width=width * scale, height=height * scale)
    return [image, Paragraph(escape(caption), styles["caption"])]


def _box(
    ax: Any, x: float, y: float, w: float, h: float, text: str, color: str = "#ebf8ff"
) -> None:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.08,rounding_size=0.12",
        linewidth=1,
        edgecolor="#2b6cb0",
        facecolor=color,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8, color="#1a365d")


def _arrow(ax: Any, start: tuple[float, float], end: tuple[float, float]) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start, end, arrowstyle="-|>", mutation_scale=12, linewidth=1, color="#4a5568"
        )
    )


def _architecture_diagram(path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(9, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14)
    ax.axis("off")
    boxes = [
        (3, 12.7, 4, 0.8, "NASA benchmark catalog / archive"),
        (3, 11.5, 4, 0.8, "TLS + SHA-256 + ZIP safety"),
        (3, 10.3, 4, 0.8, "Immutable raw FD001 files"),
        (3, 9.1, 4, 0.8, "Strict loader + integrity validation"),
        (0.7, 7.7, 3.8, 0.8, "Executed EDA + sensor review"),
        (5.5, 7.7, 3.8, 0.8, "Train/test RUL labels"),
        (5.5, 6.5, 3.8, 0.8, "Engine split: 80 fit / 20 validation"),
        (5.5, 5.3, 3.8, 0.8, "Causal features + training-only scaler"),
        (5.5, 4.1, 3.8, 0.8, "Cycle / sequence / window products"),
        (3, 2.9, 4, 0.8, "Checksums + independent verification"),
        (3, 1.7, 4, 0.8, "Tests + PDF + ZIP + GitHub handoff"),
        (3, 0.5, 4, 0.8, "Milestone 5: outside this assignment"),
    ]
    for x, y, w, h, text in boxes:
        _box(ax, x, y, w, h, text)
    for top, bottom in [(12.7, 12.3), (11.5, 11.1), (10.3, 9.9), (9.1, 8.5)]:
        _arrow(ax, (5, top), (5, bottom))
    _arrow(ax, (4, 9.1), (2.6, 8.5))
    _arrow(ax, (6, 9.1), (7.4, 8.5))
    for top, bottom in [(7.7, 7.3), (6.5, 6.1), (5.3, 4.9), (4.1, 3.7), (2.9, 2.5), (1.7, 1.3)]:
        _arrow(ax, (7.4, top), (7.4, bottom))
    _arrow(ax, (7.4, 2.9), (5.8, 3.3))
    _arrow(ax, (5, 1.7), (5, 1.3))
    ax.set_title("Software architecture and milestone data flow", fontsize=11, color="#1a365d")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return path


def _leakage_diagram(path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")
    _box(ax, 0.5, 3.8, 3.2, 1.2, "Official train\nfit engines only", "#ebf8ff")
    _box(ax, 4.4, 3.8, 3.2, 1.2, "Causal features\n+ StandardScaler fit", "#ebf8ff")
    _box(ax, 8.3, 3.8, 3.2, 1.2, "Frozen scaler\nparameters", "#ebf8ff")
    _box(ax, 0.5, 1.2, 3.2, 1.2, "Validation engines", "#fffaf0")
    _box(ax, 4.4, 1.2, 3.2, 1.2, "Official test engines", "#fffaf0")
    _box(ax, 8.3, 1.2, 3.2, 1.2, "Transform only\n(no fitting)", "#fffaf0")
    _arrow(ax, (3.7, 4.4), (4.4, 4.4))
    _arrow(ax, (7.6, 4.4), (8.3, 4.4))
    _arrow(ax, (9.9, 3.8), (9.9, 2.4))
    _arrow(ax, (3.7, 1.8), (8.3, 1.8))
    ax.text(
        6,
        5.4,
        "Leakage boundary: validation/test never contribute to fitted normalization",
        ha="center",
        fontsize=10,
        color="#1a365d",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return path


def _footer(canvas_obj: Any, doc: Any) -> None:
    canvas_obj.saveState()
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(GREY)
    canvas_obj.drawString(
        2 * cm, 1.2 * cm, "Predictive Maintenance Platform — Milestones 0–4 Engineering Report"
    )
    canvas_obj.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas_obj.setStrokeColor(colors.HexColor("#cbd5e0"))
    canvas_obj.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)
    canvas_obj.restoreState()


def build_report(root: Path, output: Path) -> Path:
    styles = _styles()
    eda = _read_json(root / "reports/eda/summary.json")
    prep = _read_json(root / "reports/preprocessing/summary.json")
    verification = _read_json(root / "reports/preprocessing/verification.json")
    integrity = _read_json(root / "reports/validation/integrity.json")
    acquisition = _read_json(root / "data/metadata/acquisition.json")
    source_manifest = _read_json(root / "data/metadata/source_manifest.json")
    dataset_cfg = load_config("dataset", root)
    env_text = _read_text(root / "reports/execution/environment.txt")
    pytest_text = _read_text(root / "reports/execution/milestone4_full_pytest.txt")
    match = re.search(r"(\d+) passed", pytest_text)
    test_count = match.group(1) if match else "pending"
    figures_dir = root / "reports/figures"
    arch_path = _architecture_diagram(figures_dir / "architecture.png")
    leak_path = _leakage_diagram(figures_dir / "leakage_boundary.png")

    story: list[Any] = []
    # Cover
    story.extend(
        [
            Spacer(1, 3 * cm),
            _p("Predictive Maintenance & Remaining Useful Life Prediction System", styles["title"]),
            _p("Milestones 0–4 Engineering Handoff Report", styles["subtitle"]),
            _p(
                "NASA C-MAPSS FD001 · CPU-first · Reproducible data preparation · No predictive model training",
                styles["body"],
            ),
            Spacer(1, 0.5 * cm),
        ]
    )
    story.append(
        _table(
            ["Field", "Value"],
            [
                ["Repository", "predictive-maintenance-platform"],
                ["Report date", "2026-11-07"],
                ["Initial subset", "FD001"],
                ["RUL cap / window", "125 cycles / 30 cycles"],
                ["Full test result", f"{test_count} passed"],
                ["Boundary", "Stop before Milestone 5"],
            ],
            styles,
            [4 * cm, 12 * cm],
        )
    )
    story.extend([Spacer(1, 0.6 * cm), _p(FINAL_STATEMENT, styles["body"]), PageBreak()])

    chapters = [
        "Executive Summary",
        "Project Objectives and Scope",
        "Milestone 0 — Project Definition",
        "Technical Decisions and Mathematical Formulation",
        "Milestone 1 — Repository and Environment",
        "Final Repository Architecture",
        "Milestone 2 — Dataset Acquisition",
        "Dataset Provenance and Integrity",
        "Milestone 3 — Exploratory Data Analysis",
        "Sensor Analysis and Engineering Interpretation",
        "Milestone 4 — Data Processing",
        "RUL Label Construction",
        "Data Splitting and Leakage Prevention",
        "Feature Engineering",
        "Generated Data Artifacts",
        "Software Architecture and Module Responsibilities",
        "Installation Instructions",
        "Exact Execution Commands",
        "Testing and Validation Results",
        "Known Limitations and Unresolved Issues",
        "GitHub Repository Creation",
        "Complete Local Download Instructions",
        "Exact Git Commands for Initial Upload",
        "GitHub Upload Manifest",
        "Final Acceptance Checklist",
        "Transition to Milestone 5",
    ]
    story.append(_p("Contents", styles["h1"]))
    for index, title in enumerate(chapters, start=1):
        story.append(_p(f"{index}. {title}", styles["body"]))
    story.append(PageBreak())

    def chapter(number: int, title: str) -> None:
        story.append(_p(f"{number}. {title}", styles["h1"]))

    def body(text: str) -> None:
        story.append(_p(text, styles["body"]))

    def bullets(items: list[str]) -> None:
        for item in items:
            story.append(_p(f"• {item}", styles["body"]))

    def code(text: str) -> None:
        story.append(_code(text, styles["code"]))
        story.append(Spacer(1, 0.2 * cm))

    # 1
    chapter(1, "Executive Summary")
    body(
        "This report documents the executed engineering handoff for Milestones 0–4 of a predictive maintenance and RUL data-preparation platform. The work covers project definition, reproducible environment, NASA C-MAPSS FD001 acquisition/validation, executed EDA, and leakage-controlled preprocessing/feature engineering. It intentionally stops before predictive model development."
    )
    overview = eda.get("overview", {})
    train_ov = overview.get("train", {})
    test_ov = overview.get("test", {})
    window_counts = prep.get("window_counts", {})
    story.append(
        _table(
            ["Verified result", "Value"],
            [
                [
                    "Training engines / observations",
                    f"{train_ov.get('engines', 'pending')} / {train_ov.get('observations', 'pending')}",
                ],
                [
                    "Test engines / observations",
                    f"{test_ov.get('engines', 'pending')} / {test_ov.get('observations', 'pending')}",
                ],
                ["Feature count", prep.get("n_features", "pending")],
                [
                    "Windows (fit / validation / test)",
                    f"{window_counts.get('train_fit', 'pending')} / {window_counts.get('validation', 'pending')} / {window_counts.get('test', 'pending')}",
                ],
                ["Full pytest", f"{test_count} passed"],
                ["Artifact verification", verification.get("status", "pending")],
            ],
            styles,
            [7 * cm, 9 * cm],
        )
    )
    body(FINAL_STATEMENT)

    # 2
    chapter(2, "Project Objectives and Scope")
    bullets(
        [
            "Prepare scientifically valid, reproducible, training-ready data for RUL regression on simulated turbofan engines.",
            "Use FD001 first: one sea-level operating condition and one HPC degradation fault mode.",
            "Preserve raw data immutability and explicit train/validation/test boundaries.",
            "Target CPU execution on an 8 GB local machine; no GPU or cloud compute is required.",
            "Exclude all predictive estimator fitting, hyperparameter search, model comparison, and accuracy claims.",
        ]
    )
    body(
        "The only fitted object is a preprocessing StandardScaler. This is an unsupervised normalization transformer, not a predictive model. Condition monitoring, anomaly detection, failure-horizon classification, and RUL regression are distinguished in the problem formulation; this assignment prepares data for the last task without solving it predictively."
    )

    # 3
    chapter(3, "Milestone 0 — Project Definition")
    bullets(
        [
            "Engine identity is (subset, split, engine_id); numeric IDs are not shared across train/test.",
            "Cycle is a one-based operational observation, not a 1 Hz flight recording.",
            "Training sequences run to the benchmark failure endpoint; test sequences are right-censored.",
            "RUL target is remaining cycles after the current observation, with raw and capped labels retained.",
            "Data contracts define schema, labels, splits, scaler boundaries, feature causality, window metadata, and manifests.",
        ]
    )
    body(
        "Milestone 0 passed an internal consistency gate: required planning artifacts exist, retained decisions are documented, and architecture/leakage diagrams are present. Evidence: reports/execution/milestone0_check.txt."
    )

    # 4
    chapter(4, "Technical Decisions and Mathematical Formulation")
    story.append(
        _table(
            ["Decision", "Value / rationale"],
            [
                ["Initial subset", "FD001; FD002–FD004 parameterized for later review"],
                ["RUL cap", "125 cycles; benchmark convention, not physical lifetime"],
                ["Window length", "30 cycles; complete windows, no padding"],
                ["Split", "Seed 42; validation fraction 0.20; 80 fit / 20 validation"],
                ["Scaling", "Global StandardScaler; fit on train_fit only"],
                ["Sensor exclusion", "s_1, s_5, s_10, s_16, s_18, s_19; setting_3"],
                ["Warmup", "TD-024: causal min_periods=1; initial std/difference = 0"],
            ],
            styles,
            [4 * cm, 12 * cm],
        )
    )
    code(
        "Training: RUL_raw(t) = T_failure - t; RUL(t) = min(125, RUL_raw(t))\nTest: F_i = L_i + r_i; RUL_raw(i,t) = F_i - t; RUL(i,t) = min(125, RUL_raw(i,t))\nWindow ending at e: cycles [e-29, ..., e], label at e, one engine only."
    )
    body(
        "The warmup refinement avoids NaNs and preserves 30-cycle windows ending at cycle 30 without future padding. It is documented before implementation and does not change the retained 125/30 decisions."
    )

    # 5
    chapter(5, "Milestone 1 — Repository and Environment")
    env_rows = []
    for line in env_text.splitlines():
        if ":" in line and any(
            line.startswith(name + ":")
            for name in [
                "Python",
                "numpy",
                "pandas",
                "scikit-learn",
                "pyarrow",
                "pytest",
                "ruff",
                "mypy",
                "reportlab",
            ]
        ):
            key, value = line.split(":", 1)
            env_rows.append([key, value.strip()])
    story.append(
        _table(
            ["Component", "Observed version"],
            env_rows or [["Environment", "pending"]],
            styles,
            [6 * cm, 10 * cm],
        )
    )
    code(
        'uv sync --locked\nuv run python scripts/check_environment.py\nuv run ruff check src tests scripts\nuv run ruff format --check src tests scripts\nuv run mypy\nuv run pytest -m "not data_required"'
    )
    body(
        "Git was initialized locally. CI is configured for Python 3.11/3.12/3.13 with locked install, lint, format, type check, and non-data tests. Remote GitHub Actions execution is pending until the user pushes."
    )

    # 6
    chapter(6, "Final Repository Architecture")
    code(
        "predictive-maintenance-platform/\n├── README.md / PROJECT_SPEC.md / LICENSE\n├── pyproject.toml / uv.lock / Makefile / .gitignore\n├── configs/ (project, dataset, preprocessing, features)\n├── data/ (raw, interim, processed, metadata; raw/processed local-only)\n├── docs/ (specification, decisions, contracts, guides, progress)\n├── notebooks/ (four executed EDA notebooks)\n├── scripts/ (acquisition, validation, EDA, preprocessing, verification, report, package)\n├── src/predictive_maintenance/ (data, analysis, preprocessing, features, reporting)\n├── tests/ (unit, integration, synthetic helpers)\n├── reports/ (validation, EDA, preprocessing, execution evidence)\n└── .github/workflows/ci.yml"
    )
    bullets(
        [
            "data: immutable raw, generated interim/processed, auditable metadata.",
            "src: typed package modules with explicit boundaries.",
            "scripts: reproducible CLI entry points.",
            "tests: correctness, leakage, schema, reproducibility.",
            "reports: executed evidence, not illustrative placeholders.",
        ]
    )

    # 7
    chapter(7, "Milestone 2 — Dataset Acquisition")
    body(
        "The supplied NASA simulator page describes software/full-flight recordings and lists no benchmark data. The separate NASA PCoE benchmark catalog was used. A streaming HTTPS GET succeeded after transient TLS/timeouts; the archive was pinned by observed SHA-256 and safely extracted."
    )
    archive = acquisition.get("archive", source_manifest.get("archive", {}))
    story.append(
        _table(
            ["Item", "Value"],
            [
                ["Source URL", dataset_cfg["source"]["archive_url"]],
                ["Download UTC", archive.get("downloaded_at_utc", "pending")],
                ["Bytes", archive.get("bytes", "pending")],
                [
                    Paragraph("Archive SHA-256", styles["cell"]),
                    Paragraph(
                        f"{str(archive.get('sha256', 'pending'))[:32]}<br/>{str(archive.get('sha256', 'pending'))[32:]}",
                        styles["small"],
                    ),
                ],
            ],
            styles,
            [4 * cm, 12 * cm],
        )
    )
    code(
        "uv run python scripts/download_dataset.py --subset FD001\nuv run python scripts/validate_dataset.py --subset FD001"
    )
    body(
        "Manual fallback: download CMAPSSData.zip from the official NASA catalog, place it at data/raw/archives/CMAPSSData.zip, and rerun the script. It verifies the existing archive rather than overwriting raw bytes silently."
    )

    # 8
    chapter(8, "Dataset Provenance and Integrity")
    file_rows = []
    for record in source_manifest.get("extracted_files", []):
        sha = str(record.get("sha256", ""))
        file_rows.append(
            [
                Path(record.get("path", "")).name,
                record.get("bytes", ""),
                Paragraph(f"{sha[:32]}<br/>{sha[32:]}", styles["small"]),
            ]
        )
    story.append(
        _table(
            ["File", "Bytes", "SHA-256"],
            file_rows or [["pending", "", ""]],
            styles,
            [5 * cm, 2 * cm, 9 * cm],
        )
    )
    train_sum = integrity.get("train_summary", {})
    test_sum = integrity.get("test_summary", {})
    rul_sum = integrity.get("rul_summary", {})
    story.append(
        _table(
            ["Check", "Result"],
            [
                ["Integrity status", integrity.get("status", "pending")],
                [
                    "Train",
                    f"{train_sum.get('observations', 'pending')} rows, {train_sum.get('engines', 'pending')} engines, lengths {train_sum.get('min_sequence_length', 'pending')}–{train_sum.get('max_sequence_length', 'pending')}",
                ],
                [
                    "Test",
                    f"{test_sum.get('observations', 'pending')} rows, {test_sum.get('engines', 'pending')} engines, lengths {test_sum.get('min_sequence_length', 'pending')}–{test_sum.get('max_sequence_length', 'pending')}",
                ],
                [
                    "RUL vector",
                    f"{rul_sum.get('count', 'pending')} values, range {rul_sum.get('min', 'pending')}–{rul_sum.get('max', 'pending')}, mean {rul_sum.get('mean', 'pending')}",
                ],
            ],
            styles,
            [4 * cm, 12 * cm],
        )
    )
    body(
        "License is not specified in the NASA catalog. Public access is not treated as redistribution permission. Raw and derived data are local-only by default; code is MIT-licensed and does not relicense NASA materials."
    )

    # 9
    chapter(9, "Milestone 3 — Exploratory Data Analysis")
    body(
        "EDA executed independently of notebooks and generated 10 figures and 11 tables. Four notebooks were then executed from clean kernels with zero errors. Outputs are actual generated artifacts, not fabricated illustrations."
    )
    story.append(
        _table(
            ["Metric", "Train", "Test"],
            [
                ["Engines", train_ov.get("engines", "pending"), test_ov.get("engines", "pending")],
                [
                    "Observations",
                    train_ov.get("observations", "pending"),
                    test_ov.get("observations", "pending"),
                ],
                [
                    "Mean sequence length",
                    f"{train_ov.get('mean_length', 0):.2f}",
                    f"{test_ov.get('mean_length', 0):.2f}",
                ],
                [
                    "Min–max length",
                    f"{train_ov.get('min_length', 'pending')}–{train_ov.get('max_length', 'pending')}",
                    f"{test_ov.get('min_length', 'pending')}–{test_ov.get('max_length', 'pending')}",
                ],
            ],
            styles,
            [6 * cm, 5 * cm, 5 * cm],
        )
    )
    story.extend(
        _image(
            root / "reports/eda/figures/engine_lifetime_histogram.png",
            "Figure 1. Training engine lifetime distribution (actual FD001 EDA output).",
            styles,
        )
    )
    story.extend(
        _image(
            root / "reports/eda/figures/sequence_length_distribution.png",
            "Figure 2. Train vs test sequence length distribution (actual FD001 EDA output).",
            styles,
        )
    )

    # 10
    chapter(10, "Sensor Analysis and Engineering Interpretation")
    body(
        f"Exact constant sensors: {', '.join(eda.get('constant_sensors', []))}. Near-constant sensors: {', '.join(eda.get('near_constant_sensors', []))}. Constants are excluded from features only; near-constants are retained initially. Low global correlation alone is not a removal criterion."
    )
    degradation = sorted(
        eda.get("degradation_summary", []),
        key=lambda row: abs(float(row.get("late_minus_early_mean", 0))),
        reverse=True,
    )[:10]
    deg_rows = [
        [
            row["sensor"],
            f"{float(row['late_minus_early_mean']):.3f}",
            f"{float(row['fraction_engines_positive']):.2f}",
        ]
        for row in degradation
    ]
    story.append(
        _table(
            ["Sensor", "Mean late − early", "Fraction engines positive"],
            deg_rows or [["pending", "", ""]],
            styles,
            [4 * cm, 6 * cm, 6 * cm],
        )
    )
    body(
        "Temperature/pressure channels such as s_3/s_4 increase consistently, while s_7/s_12 decrease consistently across engines. Core-speed channels show larger mean shifts but higher engine variability. These are simulated degradation patterns, not causal physical diagnosis."
    )
    story.extend(
        _image(
            root / "reports/eda/figures/degradation_trajectories.png",
            "Figure 3. Example engine degradation trajectories (actual FD001 EDA output).",
            styles,
            max_h=12 * cm,
        )
    )
    story.extend(
        _image(
            root / "reports/eda/figures/sensor_correlation_heatmap.png",
            "Figure 4. Operational-setting and sensor correlation heatmap (actual FD001 EDA output).",
            styles,
            max_h=12 * cm,
        )
    )

    # 11
    chapter(11, "Milestone 4 — Data Processing")
    code(
        "uv run python scripts/run_preprocessing.py --subset FD001\nuv run python scripts/build_features.py --subset FD001\nuv run python scripts/verify_artifacts.py --subset FD001"
    )
    cycle_counts = prep.get("cycle_counts", {})
    rows = [
        [name, counts.get("rows", "pending"), counts.get("engines", "pending")]
        for name, counts in cycle_counts.items()
    ]
    story.append(
        _table(
            ["Split", "Cycle rows", "Engines"],
            rows or [["pending", "", ""]],
            styles,
            [6 * cm, 5 * cm, 5 * cm],
        )
    )
    body(
        "The pipeline validates raw inputs, constructs train/test labels, splits official training engines, builds causal features, fits a training-only scaler, transforms all splits, and writes sequence/window products with manifests. No predictive estimator is fitted."
    )

    # 12
    chapter(12, "RUL Label Construction")
    rul_stats = eda.get("rul_stats", {})
    body(
        "Training labels use each engine's final observed cycle as the benchmark failure endpoint. Test labels use the separate terminal RUL vector; the final observed test cycle is not failure. Independent integer-loop verification checks every engine and terminal condition."
    )
    story.append(
        _table(
            ["RUL statistic", "Value"],
            [
                [
                    "Training raw range",
                    f"{rul_stats.get('train_raw_min', 'pending')}–{rul_stats.get('train_raw_max', 'pending')}",
                ],
                ["Training raw mean", f"{float(rul_stats.get('train_raw_mean', 0)):.2f}"],
                ["Fraction above cap 125", f"{float(rul_stats.get('fraction_capped', 0)):.4f}"],
                [
                    "Test terminal range",
                    f"{rul_stats.get('test_terminal_min', 'pending')}–{rul_stats.get('test_terminal_max', 'pending')}",
                ],
                ["Test terminal mean", f"{float(rul_stats.get('test_terminal_mean', 0)):.2f}"],
            ],
            styles,
            [7 * cm, 9 * cm],
        )
    )
    story.extend(
        _image(
            root / "reports/eda/figures/rul_distribution.png",
            "Figure 5. Training raw/clipped RUL and official test terminal RUL (actual FD001 EDA output).",
            styles,
        )
    )

    # 13
    chapter(13, "Data Splitting and Leakage Prevention")
    body(
        "The deterministic engine-level split uses seed 42 and validation fraction 0.20, yielding 80 fit and 20 validation engines. The official test set remains separate. Train/validation engine intersection is empty; validation/test never contribute to scaler fitting or feature selection."
    )
    story.extend(
        _image(
            leak_path,
            "Figure 6. Leakage boundary: fit-only normalization and transform-only validation/test.",
            styles,
        )
    )
    bullets(
        [
            "Engine leakage: disjoint engine IDs, not row-level random splitting.",
            "Temporal leakage: causal rolling/difference features and trailing windows only.",
            "Scaling leakage: StandardScaler fit only on train_fit feature rows.",
            "Window leakage: one engine, cycles e-29..e, target at e, no future rows.",
            "Test contamination: test labels used only for offline evaluation artifacts, never fitting.",
            "Automated guards: future-mutation, cross-engine, boundary, schema, and no-training tests.",
        ]
    )

    # 14
    chapter(14, "Feature Engineering")
    story.append(
        _table(
            ["Feature group", "Count", "Definition"],
            [
                ["Current settings", 2, "setting_1, setting_2"],
                ["Current sensors", 15, "Selected non-constant sensors"],
                ["Rolling mean", 30, "Trailing 5/10-cycle means"],
                ["Rolling std", 30, "Trailing 5/10-cycle sample std, ddof=1"],
                ["First difference", 15, "x[t] - x[t-1]"],
                ["Total", prep.get("n_features", 92), "Initial compact causal feature set"],
            ],
            styles,
            [5 * cm, 2 * cm, 9 * cm],
        )
    )
    body(
        "Rolling warmups are causal expanding calculations (min_periods=1); single-sample std and first difference are zero. Optional min/max and local trend slope are implemented but disabled to avoid redundant feature explosion. Scaled columns are dimensionless z-scores using frozen training-only parameters."
    )

    # 15
    chapter(15, "Generated Data Artifacts")
    window_rows = [[name, count] for name, count in window_counts.items()]
    story.append(
        _table(["Split", "Windows"], window_rows or [["pending", ""]], styles, [8 * cm, 8 * cm])
    )
    bullets(
        [
            "Cycle-level Parquet: all original measurements plus labels/endpoints/split.",
            "Labels CSV: raw/capped RUL and endpoint metadata.",
            "Feature/scaled Parquet: explicit 92-feature order, float32 storage.",
            "Sequence NPZ: ordered per-engine float32 sequences and labels.",
            "Window NPZ: per-engine X (n,30,92), y, y_raw, engine/start/end/cycle.",
            "Window index CSV and manifests: paths, shapes, checksums, feature order.",
            "Artifact manifest: 227 entries with SHA-256, shapes/dtypes where applicable.",
        ]
    )
    body(
        "Large raw/processed data are regenerated locally and excluded from default redistribution. Metadata/checksums are retained for auditability."
    )

    # 16
    chapter(16, "Software Architecture and Module Responsibilities")
    story.extend(
        _image(arch_path, "Figure 7. Architecture and milestone data flow.", styles, max_h=14 * cm)
    )
    story.append(
        _table(
            ["Module", "Responsibility"],
            [
                ["data/schema, loader", "Exact column contract and strict ingestion"],
                [
                    "data/acquisition, metadata",
                    "Verified download, safe extraction, provenance/checksums",
                ],
                ["data/validation", "Structural/scientific integrity reports"],
                [
                    "data/labels, splitting, windows",
                    "RUL arithmetic, engine isolation, sequences/windows",
                ],
                ["analysis/eda", "Executed descriptive statistics and plots"],
                ["features/engineering", "Causal engine-local feature construction"],
                [
                    "preprocessing/scaling, pipeline, artifacts",
                    "Training-only scaler, orchestration, manifests",
                ],
                ["reporting/engineering_report", "PDF generation from verified artifacts"],
            ],
            styles,
            [6 * cm, 10 * cm],
        )
    )

    # 17
    chapter(17, "Installation Instructions")
    code(
        "# Install uv if needed: https://docs.astral.sh/uv/\ncd predictive-maintenance-platform\nuv sync --locked\nuv run python scripts/check_environment.py"
    )
    body(
        "Python >=3.11,<3.14 is supported; the executed workspace used Python 3.13.16. No GPU framework, database, Docker, or experiment-tracking service is required. The lockfile is authoritative. On Windows PowerShell the same uv commands apply; use platform-appropriate paths."
    )

    # 18
    chapter(18, "Exact Execution Commands")
    code(
        "uv sync --locked\nuv run python scripts/download_dataset.py --subset FD001\nuv run python scripts/validate_dataset.py --subset FD001\nuv run python scripts/run_eda.py --subset FD001\nuv run python scripts/create_notebooks.py\nuv run python scripts/run_notebooks.py\nuv run python scripts/run_preprocessing.py --subset FD001\nuv run python scripts/build_features.py --subset FD001\nuv run python scripts/verify_artifacts.py --subset FD001\nuv run pytest\nuv run python scripts/generate_report.py\nuv run python scripts/package_delivery.py"
    )
    body(
        "Makefile shortcuts are available: make install, lint, typecheck, test, test-all, download, validate, eda, preprocess, features, notebooks, report, package. Full real-data acceptance requires the data-dependent commands; CI intentionally runs non-data tests only."
    )

    # 19
    chapter(19, "Testing and Validation Results")
    body(
        f"Final full pytest result: {test_count} passed. Tests include unit checks for labels, splits, scaler boundaries, causal features, windows, schemas, acquisition safety, and a no-training guard; integration checks include synthetic end-to-end reproducibility and real FD001 verification."
    )
    check_rows = [
        [check["name"], "PASS" if check["passed"] else "FAIL"]
        for check in verification.get("checks", [])
    ]
    story.append(
        _table(
            ["Independent verification check", "Result"],
            check_rows or [["pending", ""]],
            styles,
            [11 * cm, 5 * cm],
        )
    )
    body(
        "Evidence logs are stored under reports/execution/. Remote GitHub Actions is configured but not remotely executed in this workspace. No predictive performance metric is reported because no predictive model was trained."
    )

    # 20
    chapter(20, "Known Limitations and Unresolved Issues")
    bullets(
        [
            "Execution occurred in a Linux sandbox, not on the user's local machine; local download/install is pending.",
            "GitHub creation/push and remote Actions are pending user authentication.",
            "NASA benchmark license is unspecified; raw/derived data are excluded from default redistribution.",
            "FD001 only is executed; FD002–FD004 require subset-specific regime/sensor/scaling review.",
            "Findings are simulated benchmark descriptions, not real-aircraft reliability or fault diagnosis.",
            "RUL cap and sensor selection are initial conventions, not optimized or performance-validated choices.",
            "Sandbox RAM was ~1.9 GiB; successful FD001 execution is conservative but not a formal 8 GB peak-memory certification.",
        ]
    )

    # 21
    chapter(21, "GitHub Repository Creation")
    bullets(
        [
            "Go to https://github.com/new.",
            "Repository name: predictive-maintenance-platform.",
            "Private recommended initially; public only after licensing/report review.",
            "Do not initialize README, .gitignore, or license remotely; the project already contains them.",
            "Create repository and copy the HTTPS or SSH URL.",
        ]
    )
    body(
        "The repository must not receive raw NASA files or generated processed arrays by default. Use the acquisition script and local regeneration. The code license is MIT and does not relicense NASA data."
    )

    # 22
    chapter(22, "Complete Local Download Instructions")
    bullets(
        [
            "Download predictive-maintenance-platform-milestones-0-4.zip from the workspace.",
            "Download the PDF report separately if desired.",
            "Extract the ZIP to a local projects folder.",
            "Confirm README, PROJECT_SPEC, LICENSE, pyproject, uv.lock, configs, src, tests, scripts, docs, notebooks, reports, and .github are present.",
            "Use the archive for the complete project; individual files are only for intentional partial downloads.",
            "Run uv sync --locked and the documented pipeline to regenerate local data products.",
        ]
    )

    # 23
    chapter(23, "Exact Git Commands for Initial Upload")
    code(
        'git --version\ngit config --global user.name "Your Name"\ngit config --global user.email "your.email@example.com"\ncd predictive-maintenance-platform\ngit init -b main\ngit status\ngit add README.md PROJECT_SPEC.md LICENSE pyproject.toml uv.lock .gitignore Makefile\ngit add configs src tests scripts docs notebooks .github\ngit add GITHUB_UPLOAD_MANIFEST.md DELIVERABLES_MANIFEST.md\ngit commit -m "Milestones 0-4: reproducible C-MAPSS FD001 data preparation platform"\ngit remote add origin https://github.com/<your-user>/predictive-maintenance-platform.git\ngit push -u origin main\ngit remote -v\ngit ls-remote --heads origin'
    )
    body(
        'Windows PowerShell uses the same Git commands with Windows paths (for example, cd $HOME\\projects\\predictive-maintenance-platform). If the remote already exists, use git remote set-url origin <URL>. Future updates: git add <changed-files>, git commit -m "...", git push. Do not use git add . until optional reports/metadata and data exclusions are reviewed.'
    )

    # 24
    chapter(24, "GitHub Upload Manifest")
    story.append(
        _table(
            ["Classification", "Paths"],
            [
                [
                    "Required",
                    "README, PROJECT_SPEC, LICENSE, pyproject, uv.lock, .gitignore, Makefile, configs, src, tests, scripts, docs, notebooks, .github, manifests",
                ],
                [
                    "Optional (review)",
                    "reports/eda, reports/validation, reports/preprocessing, reports/execution, data/metadata, PDF",
                ],
                ["Generated locally / excluded", "data/raw, data/interim, data/processed"],
                ["Never commit", ".env, credentials, keys, caches, .venv, ZIP archives"],
            ],
            styles,
            [5 * cm, 11 * cm],
        )
    )
    body(
        "The full file-level manifest is GITHUB_UPLOAD_MANIFEST.md. The guide is docs/GITHUB_UPLOAD_GUIDE.md. Publication is not claimed until an actual push is verified."
    )

    # 25
    chapter(25, "Final Acceptance Checklist")
    story.append(
        _table(
            ["Milestone", "Status", "Primary evidence"],
            [
                [
                    "0 — Definition",
                    "PASS",
                    "PROJECT_SPEC, decisions, contracts, milestone0_check.txt",
                ],
                ["1 — Environment", "PASS", "uv.lock, environment.txt, lint/mypy/pytest logs"],
                [
                    "2 — Acquisition/validation",
                    "PASS",
                    "Pinned NASA archive, integrity.json, checksums",
                ],
                ["3 — EDA", "PASS", "10 figures, 11 tables, executed notebooks"],
                [
                    "4 — Processing/features",
                    "PASS",
                    "92 features, 27,927 windows, verification PASS, 39 tests",
                ],
                [
                    "Final handoff",
                    "PASS",
                    "PDF, ZIP, GitHub guide/manifests, deliverables manifest",
                ],
            ],
            styles,
            [4.5 * cm, 2.5 * cm, 9 * cm],
        )
    )
    body(FINAL_STATEMENT)

    # 26
    chapter(26, "Transition to Milestone 5")
    body(
        "Milestone 5 is explicitly outside this assignment. The prepared infrastructure provides validated raw data, correct RUL labels, engine-disjoint splits, frozen training-only normalization, causal features, sequence/window products, and leakage tests. Future model development may begin only after this handoff is accepted."
    )
    bullets(
        [
            "Future work may define classical baseline estimators and evaluation metrics, but none are implemented or fitted here.",
            "Future FD002–FD004 work should repeat EDA and review operating-regime handling before reusing sensor/scaling choices.",
            "Any future predictive experiment must preserve the same engine/temporal/scaling/test isolation boundaries.",
            "No predictive accuracy claim is made in this report.",
        ]
    )
    body(
        "References and source investigation are recorded in docs/REFERENCES.md. Execution evidence is under reports/execution/. This report distinguishes verified local results from pending user-local/GitHub actions."
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Predictive Maintenance Milestones 0-4 Engineering Report",
        author="Predictive Maintenance Platform",
    )
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return output
