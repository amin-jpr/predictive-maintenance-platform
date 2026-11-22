# Dataset acquisition and provenance

## Official source
- Benchmark catalog: https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data
- Resource page: https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data/resource/5224bcd1-ad61-490b-93b9-2817288accb8
- Archive: https://data.nasa.gov/docs/legacy/CMAPSSData.zip
- Original supplied simulator page (not the benchmark file source): https://data.nasa.gov/dataset/c-mapss-aircraft-engine-simulator-data

The supplied simulator page describes C-MAPSS software/full-flight recordings and carries a software-unavailability notice. The separate NASA PCoE benchmark catalog is the authoritative source for the FD001–FD004 cycle-level benchmark used here.

## Reproducible command
```bash
uv run python scripts/download_dataset.py --subset FD001
uv run python scripts/validate_dataset.py --subset FD001
```
The script verifies TLS HTTPS, pinned archive SHA-256/size, ZIP CRC, safe member paths, no symlinks, extracted file hashes, and refuses to silently overwrite different raw bytes. Extracted originals are set read-only.

## Observed archive pin
| Item | Value |
|---|---|
| Download date (UTC) | 2026-11-07T06:32:12+00:00 |
| Archive bytes | 12,425,978 |
| Archive SHA-256 | `74bef434a34db25c7bf72e668ea4cd52afe5f2cf8e44367c55a82bfd91a5a34f` |
| ZIP CRC check | PASS (no bad member) |
| Final storage host | NASA S3 backend (`data-nasa-bucket-production.s3.us-east-1.amazonaws.com`) |

An initial HEAD/GET attempt encountered transient TLS/timeouts; a retry succeeded. This is recorded in `reports/execution/download_probe.json` and does not change the source URL.

## FD001 extracted file pins
| File | Bytes | SHA-256 |
|---|---:|---|
| train_FD001.txt | 3,515,356 | `963b5e22825b34d8b21c69e1aeb4af3e647050eb672ee8834ba4b5d91d2de0f8` |
| test_FD001.txt | 2,228,855 | `3cda7109ce17bafb5443f2ac926cfcf88154b941b8c4cf95eb55d1ddd6f52851` |
| RUL_FD001.txt | 429 | `a19c8ec94931949d0485bdc35118206e9c81c4547b422efb9cf86f4ceddbceca` |
| readme.txt | 2,442 | `4f5270554b775c67e73aff383c5436fd329d6e4cc3d3a116913276fae511269b` |
| Damage Propagation Modeling.pdf | 434,158 | `e7aaef80c177333f400a4c1099fe76e67d244569b9397c937ec4cd3ed5b44a27` |

## Manual fallback
If the script cannot reach NASA from your network:
1. Open the benchmark catalog/resource page in a browser.
2. Download `CMAPSSData.zip` from the official NASA link above.
3. Place it at `data/raw/archives/CMAPSSData.zip`.
4. Run `uv run python scripts/download_dataset.py --subset FD001`; it will verify the existing archive and extract safely.
5. If the hash differs, do not proceed; investigate the source and update the pin only after documented review.

## Storage layout
```text
data/raw/archives/CMAPSSData.zip
data/raw/cmaps/train_FD001.txt
data/raw/cmaps/test_FD001.txt
data/raw/cmaps/RUL_FD001.txt
data/raw/cmaps/readme.txt
data/raw/cmaps/Damage Propagation Modeling.pdf
data/metadata/acquisition.json
data/metadata/source_manifest.json
data/metadata/checksums.sha256
reports/validation/integrity.json
reports/validation/integrity.md
```
Raw files are never modified by preprocessing. FD002–FD004 use the same flat naming convention and can be extracted later with `--subset FD002` etc., after subset-specific scientific review.

## License and redistribution
The NASA catalog/resource metadata says **License not specified**. Public access is not treated as permission to redistribute. Do not commit raw NASA files, the original paper, or derived data products to GitHub by default. The acquisition script, checksums, and regeneration commands are the reproducible handoff. Original project code is MIT-licensed and does not relicense NASA materials.
