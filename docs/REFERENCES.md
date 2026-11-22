# References and source investigation

Access date for online investigation: **2026-11-07**. URLs below were observed in fetched pages/search results; no download link, checksum, or bibliographic detail is invented. Full archive verification is recorded separately after execution.

## Primary and authoritative data sources
1. NASA Open Data Portal, **C-MAPSS Aircraft Engine Simulator Data**: https://data.nasa.gov/dataset/c-mapss-aircraft-engine-simulator-data . Accessible, but describes simulator software/full-flight recordings, carries a software-unavailability notice, lists no data resources, and says license not specified. Not used as the benchmark file source.
2. NASA Open Data Portal, **CMAPSS Jet Engine Simulated Data** (PCoE): https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data . Public benchmark catalog describing FD001–FD004, run-to-failure train/censored test structure, and 26-column observations.
3. NASA benchmark resource page: https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data/resource/5224bcd1-ad61-490b-93b9-2817288accb8 .
4. Official archive linked by that catalog: https://data.nasa.gov/docs/legacy/CMAPSSData.zip . Streaming GET returned HTTP 200 and ZIP content from NASA's S3 backend during investigation; exact bytes/hash are verified in Milestone 2.
5. Data.gov catalog mirror of NASA benchmark metadata: https://catalog.data.gov/dataset/cmapss-jet-engine-simulated-data .
6. NASA DASHlink, **Turbofan engine degradation simulation data set**, Saxena & Goebel (2008): https://c3.ndc.nasa.gov/dashlink/resources/139/ . Citation: A. Saxena and K. Goebel, “Turbofan Engine Degradation Simulation Data Set,” NASA Ames Prognostics Data Repository, NASA Ames, Moffett Field, CA, 2008.
7. NASA DASHlink publication record: https://c3.ndc.nasa.gov/dashlink/resources/740/ ; Data.gov record: https://catalog.data.gov/dataset/damage-propagation-modeling-for-aircraft-engine-run-to-failure-simulation . A. Saxena, K. Goebel, D. Simon, N. Eklund, “Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation,” Proceedings of the 1st International Conference on Prognostics and Health Management (PHM08), Denver, CO, October 2008. The original paper is included in the verified NASA archive as `Damage Propagation Modeling.pdf` (9 pages; SHA-256 `e7aaef80c177333f400a4c1099fe76e67d244569b9397c937ec4cd3ed5b44a27`). Its Table 2 was inspected to confirm the 21 participant-available sensor descriptions/units.

## Licensing and redistribution
The NASA benchmark catalog/resource metadata says **License not specified**. Public access is not treated as a blanket redistribution license. NASA's general web policy was consulted: https://www.nasa.gov/nasa-web-privacy-policy-and-important-notices/ . It does not resolve a specific license for this benchmark archive. Conservative policy: do not commit or redistribute raw NASA files or derived data products by default; provide the official acquisition script, exact checksums, and local regeneration instructions. Original project code is MIT-licensed; that license does not relicense NASA data or third-party documents. If the user obtains explicit permission, distribution can be reconsidered and documented.

## Software documentation
- Python: https://docs.python.org/3/
- uv: https://docs.astral.sh/uv/
- NumPy: https://numpy.org/doc/stable/
- pandas: https://pandas.pydata.org/docs/
- pandas rolling windows: https://pandas.pydata.org/docs/reference/window.html
- scikit-learn StandardScaler: https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html
- scikit-learn leakage guidance: https://scikit-learn.org/stable/common_pitfalls.html
- pytest: https://docs.pytest.org/en/stable/
- Ruff: https://docs.astral.sh/ruff/
- mypy: https://mypy.readthedocs.io/en/stable/
- Git: https://git-scm.com/doc
- GitHub repository creation: https://docs.github.com/en/repositories/creating-and-managing-repositories/quickstart-for-repositories
- GitHub Actions: https://docs.github.com/en/actions
- PyArrow/Parquet: https://arrow.apache.org/docs/python/parquet.html
- Matplotlib: https://matplotlib.org/stable/
- Seaborn: https://seaborn.pydata.org/
- Jupyter/nbclient: https://nbclient.readthedocs.io/en/latest/
- ReportLab: https://docs.reportlab.com/

## Documentation corrections
- The benchmark has **21 sensors**, not 26 sensors; total columns are 26. NASA's prose list ending in `sensor measurement 26` is inconsistent with its own 26-column statement and the actual files.
- The supplied simulator page's 1 Hz/full-flight description is not the cycle-level benchmark schema.
- RUL ground truth contains one value per test engine, not one value per test row.
- Test sequence end is censoring, not failure.

## Evidence locations
- `data/metadata/acquisition.json`: actual download/verification record.
- `data/metadata/source_manifest.json`: archive and extracted file hashes/sizes.
- `reports/validation/integrity.md`: executed validation results.
- `reports/execution/`: command logs and environment/test evidence.
- `docs/IMPLEMENTATION_PROGRESS.md`: milestone status and limitations.
