# GitHub upload guide — predictive-maintenance-platform

This guide assumes you are starting with an empty GitHub repository and the downloaded project archive. It does **not** claim that a push has already occurred. Remote GitHub Actions and publication are pending until you perform them.

## A. Create the GitHub repository
1. Go to https://github.com/new (or GitHub → **+** → **New repository**).
2. Repository name: **`predictive-maintenance-platform`**.
3. Description: `Leakage-controlled NASA C-MAPSS FD001 data preparation for RUL prognostics (Milestones 0–4; no model training).`
4. Visibility: **Private recommended initially**. You may make it public after reviewing licensing, reports, and metadata. The code is MIT-licensed, but NASA benchmark data license is unspecified; do not publish raw/derived data by default.
5. Initialization options: **Do NOT** add a README, .gitignore, or license on GitHub. This project already contains them; initializing remotely can create an unrelated first commit.
6. Click **Create repository**.
7. Copy the repository URL, e.g. `https://github.com/<your-user>/predictive-maintenance-platform.git` (HTTPS) or `git@github.com:<your-user>/predictive-maintenance-platform.git` (SSH).

## B. Download and prepare local files
1. In the AI workspace, download **`predictive-maintenance-platform-milestones-0-4.zip`** (recommended) and the PDF report separately if desired.
2. Extract the ZIP to a local folder, e.g. `C:\Users\<you>\projects\` on Windows or `~/projects/` on Linux/macOS.
3. Confirm the extracted root contains: `README.md`, `PROJECT_SPEC.md`, `LICENSE`, `pyproject.toml`, `uv.lock`, `.gitignore`, `Makefile`, `configs/`, `src/`, `tests/`, `scripts/`, `docs/`, `notebooks/`, `reports/`, `.github/`, `GITHUB_UPLOAD_MANIFEST.md`, `DELIVERABLES_MANIFEST.md`.
4. Use the archive for the full project; do not manually recreate files. Individual files are only needed if you intentionally download a subset.
5. The archive excludes `.venv`, caches, `.git`, raw NASA data, and generated processed arrays by default. Regenerate data locally with the commands below.

## C. Dataset handling policy
| Item | Local path | Commit to GitHub? | Action |
|---|---|---|---|
| NASA archive | `data/raw/archives/CMAPSSData.zip` | **No** | Retrieve via `scripts/download_dataset.py` |
| Raw FD001 text/PDF/readme | `data/raw/cmaps/` | **No** | Retrieve via script; license unspecified |
| Interim labeled tables | `data/interim/` | **No** | Regenerate locally |
| Processed cycle/feature/scaled tables | `data/processed/{cycle_level,features,scaled}` | **No by default** | Regenerate locally |
| Sequences/windows | `data/processed/{sequences,windows}` | **No by default** | Regenerate locally |
| Window index | `data/processed/window_index.csv` | **No by default** | Regenerate locally |
| Provenance/checksums/manifests | `data/metadata/` | **Optional, reviewed** | Small metadata may be committed after review; no raw values |
| EDA reports/plots | `reports/eda/` | **Optional, reviewed** | Commit summaries/plots if you accept derived-report publication |
| Validation/preprocessing reports | `reports/{validation,preprocessing}/` | **Optional, reviewed** | Commit summaries after review |
| Execution logs | `reports/execution/` | **Optional, reviewed** | May contain local absolute paths; review before commit |
| Source/configs/tests/docs/notebooks | `src/`, `configs/`, `tests/`, `docs/`, `notebooks/`, `scripts/` | **Yes** | Required project code/documentation |
| Lockfile/tooling | `pyproject.toml`, `uv.lock`, `.github/`, `Makefile`, `.gitignore` | **Yes** | Required reproducibility/CI |
| Secrets/env | `.env`, credentials | **Never** | Excluded by `.gitignore` |
| Delivery ZIP/PDF | `*.zip`, PDF report | **Optional** | ZIP excluded by `.gitignore`; PDF optional handoff artifact |

## D. Exact Git commands
### Check Git and configure identity (all platforms)
```bash
git --version
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```
Use your GitHub email or GitHub-provided noreply email.

### Linux/macOS
```bash
cd ~/projects/predictive-maintenance-platform
git init -b main
git status
git add README.md PROJECT_SPEC.md LICENSE pyproject.toml uv.lock .gitignore Makefile
git add configs src tests scripts docs notebooks .github
git add GITHUB_UPLOAD_MANIFEST.md DELIVERABLES_MANIFEST.md
# Optional reviewed reports/metadata:
# git add reports/eda reports/validation reports/preprocessing data/metadata
git commit -m "Milestones 0-4: reproducible C-MAPSS FD001 data preparation platform"
git remote add origin https://github.com/<your-user>/predictive-maintenance-platform.git
git push -u origin main
git remote -v
git ls-remote --heads origin
```

### Windows PowerShell
```powershell
cd $HOME\projects\predictive-maintenance-platform
git init -b main
git status
git add README.md PROJECT_SPEC.md LICENSE pyproject.toml uv.lock .gitignore Makefile
git add configs src tests scripts docs notebooks .github
git add GITHUB_UPLOAD_MANIFEST.md DELIVERABLES_MANIFEST.md
# Optional reviewed reports/metadata:
# git add reports/eda reports/validation reports/preprocessing data/metadata
git commit -m "Milestones 0-4: reproducible C-MAPSS FD001 data preparation platform"
git remote add origin https://github.com/<your-user>/predictive-maintenance-platform.git
git push -u origin main
git remote -v
git ls-remote --heads origin
```
If the remote already exists, use `git remote set-url origin <URL>` instead of `git remote add`.

### Future updates
```bash
git status
git add <changed-files>
git commit -m "Describe the change"
git push
```

## E. Local verification before/after upload
```bash
uv sync --locked
uv run python scripts/check_environment.py
uv run python scripts/download_dataset.py --subset FD001
uv run python scripts/validate_dataset.py --subset FD001
uv run python scripts/run_eda.py --subset FD001
uv run python scripts/run_preprocessing.py --subset FD001
uv run python scripts/build_features.py --subset FD001
uv run python scripts/verify_artifacts.py --subset FD001
uv run pytest
```
CI runs lint/type/non-data tests without downloading NASA data. Full real-data acceptance is local.

## F. GitHub quality checks
1. **Structure:** confirm required directories/files appear in the repository root.
2. **README:** open the repo front page; confirm Markdown renders and links resolve.
3. **Actions:** open the **Actions** tab; confirm the CI workflow runs after push. Remote CI is not verified until this happens.
4. **Completeness:** compare against `GITHUB_UPLOAD_MANIFEST.md`.
5. **Dataset handling:** confirm `data/raw/`, `data/interim/`, and `data/processed/` are absent unless explicitly reviewed.
6. **Documentation links:** click key docs from README.
7. **License:** confirm `LICENSE` applies to code only and NASA data is not relicensed.
8. **Commit history:** `git log --oneline --decorate --graph`.

## G. Avoid accidental publication
- `.env`, credentials, keys, and tokens are excluded; never commit them.
- Raw NASA files and the original paper are excluded by default because the catalog license is unspecified.
- Processed arrays/tables are excluded by default; regenerate locally.
- Large ZIP archives are excluded by `.gitignore`.
- Caches, virtual environments, and temporary files are excluded.
- Review optional reports/metadata for local paths or derived data before committing.
- Reproducibility is preserved through `uv.lock`, pinned dataset checksums, configs, scripts, and tests.

## Final boundary
Do not add Milestone 5 model-training code to this repository as part of this assignment. No predictive model has been trained.
