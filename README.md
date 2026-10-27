# Produced-Water Lithium

Where is lithium in U.S. oil and gas produced water, and how much of that picture is an
artifact of what was sampled, measured and compiled? A pre-registered screening and
prediction study on the USGS National Produced Waters Geochemical Database v3.0, built and
verified under the [cairn](https://github.com/ethannol/cairn) harness.

## What the analysis shows

The database can support an initial screen of measured wells, but it cannot establish
how much lithium a basin contains. Few measured wells meet both screening criteria,
and model performance varies substantially when predicting a new basin. Missing
measurements and differences between source datasets constrain the conclusions.

This study combines a data-quality audit, basin comparisons with uncertainty, and
prediction evaluated on held-out wells, datasets, and basins.

[Read the report](reports/report.md) · [Five-minute walkthrough](docs/walkthrough.md) · [Reproduce the analysis](#setup)

![Prediction error when holding out wells, datasets, or basins](reports/figures/fig5_prediction_error.png)

<details>
<summary>Detailed findings and estimates</summary>

All estimates below are rendered from the recorded results in `artifacts/numbers.json`.


- **Non-detects cannot be identified in v3.0.** The lithium column has 6416
  values, 0 zeros, 0 negatives and
  0 flags; the dictionary has 0
  detection-limit fields. A result below detection is an empty cell, indistinguishable
  from "not analyzed".
- **Few wells pass.** Of 4141 wells with lithium, 261
  reach 100 mg/L and 100
  (2.4%) also meet Mg/Li <= 10.
  22 basins have at least 20 lithium wells;
  3 have a screened fraction whose interval
  excludes zero: Amarillo Arch (10 of 27
  wells), Arkla (23 of 255) and
  Appalachian (27 of 564). By median
  lithium the leader is Amarillo Arch at 181 mg/L, but
  on 27 wells from one dataset with centroid coordinates and an
  interval of 34 to 299; then
  Arkla (67, 21 to
  111, 255 wells) and Appalachian
  (55, 48 to
  67, 564 wells).
- **The named compilation bias is small; dataset effects are large.** The four datasets
  the USGS version history calls lithium-focused hold 11
  lithium wells; removing them changes nothing (5 of `5` top
  basins kept, 0 reversals). But within basins that have
  more than one dataset, dataset medians differ by a median factor of
  4.1 and up to 59.
- **Missing is not random.** Lithium was measured on 5.5% of rows;
  25 of 62 datasets never measured it,
  46% of dated lithium rows are from the 1960s, and a
  model predicts whether a row has lithium with AUC 0.75.
- **Prediction works within basin, degrades across datasets and basins.** Gradient
  boosting on major-ion log-ratios, TDS, depth, play type and era: RMSE of log10 Li
  0.37 under random folds by well (folds
  0.33 to 0.41),
  0.51 leaving one dataset out (0.18
  to 1.77), 0.51 leaving one
  basin out (0.27 to 1.19);
  a mean predictor scores 0.76. R-squared 0.76,
  0.53, 0.55. The pre-registered rule
  returns "useful out of basin", but precision at the floor falls from
  0.78 to 0.28 out of basin
  and only 6 of 22 held-out
  basins are predicted usefully on their own. Positive control (TDS from the same
  features): R-squared 0.83, passes.

Read the [full report](reports/report.md) or the [five-minute walkthrough](docs/walkthrough.md).

![Basin ranking](reports/figures/fig2_basin_ranking.png)

</details>

## What is not claimed

No resource estimate, no economic conclusion, no claim about any company or site. No claim
below basin scale (25% of lithium wells have
centroid coordinates). The ranking describes wells that were analyzed for lithium, not
basins. Thresholds are literature screening values. Non-detects cannot be recovered from
this version of the database.

## Setup

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/). From the cloned repository:

```bash
python3 scripts/bootstrap.py
```

This installs dependencies from the lockfile and checks out Cairn at the study's
recorded revision (`1d6e81093eeb4f81cd36d77fa1a47903f0e3be91`) in `../cairn-lithium-baseline`.
It leaves existing checkouts untouched and refuses a baseline folder with a different
revision or uncommitted changes. The initial installation needs network access.

To reproduce the analysis after installation:

```bash
uv run pytest                # focused tests of every component
uv run cairn run             # scripts/00..60 in order, offline, from the committed extract
uv run cairn verify          # frozen plan, checks, lint, placeholders, clean rerun
uv run cairn render          # reports/report.md from report.tmpl.md and the ledger
uv run python scripts/download.py   # ONLY to refresh the archive and extract (network); re-freeze after
```

After installation, the analysis runs offline from the committed extract.
The model steps set `OMP_NUM_THREADS=1` and run folds in parallel processes.

## Data provenance

- U.S. Geological Survey National Produced Waters Geochemical Database, version 3.0
  (December 2023), doi:10.5066/P9DSRCZJ, public domain. Citation in `data/raw/manifest.json`.
- The 80625044-byte workbook (SHA-256 `f201cdfdab7e3a29b4e3422a74af8e116db347730a4e0e00e0e11c53d17f7c79`) stays in
  `data/archive/` (gitignored). `data/raw/npwgd_v3_extract.csv` is a deterministic
  113135-row, 68-column extract written once by
  `scripts/download.py`; the manifest holds the URLs, HTTP headers, sizes and SHA-256 of
  every archive file and of the extract. The extract is hashed by `cairn freeze` and is
  never modified; all cleaning happens downstream with `data/derived/exclusion_log.csv`.
- Metadata XML, version history and the data dictionary are committed beside the extract.
  Field notes: `docs/data_dictionary.md`.

## Layout

```
src/pwlithium/   acquire, extract, prepare, screen, features, models, cv, missing, figures, util
scripts/         00_profile 10_prepare 20_missingness 30_screen 40_model 45_control 50_figures 60_docs; download.py
data/raw/        committed extract, manifest, metadata, version history, dictionary (frozen)
data/derived/    included rows, wells, lithium wells, exclusion log, out-of-fold predictions
artifacts/       numbers.json (ledger), checks.jsonl
reports/         report.md (rendered), figures/, tables/
docs/            prereg.md (frozen), decisions.md, data_dictionary.md, walkthrough.md, resume_bullet.md
tests/           13 pytest tests
```

## How AI was used

This project was built in a Claude Code session with Claude Fable 5.1 from the project
brief: the agent verified the download URLs, inspected the archive, found and cited the
threshold sources, wrote the pre-registration, the code, the tests and the templates, and
ran the pipeline under cairn. The author reviewed the pre-registration, the tests and the
findings. No language model is called by the pipeline.

## License

MIT for the code. The USGS data are public domain.


## Practical applicability and supplementary coverage

Passing the frozen pooled usefulness rule does not establish reliable screening in each new basin. Held-out screening precision is 0.28, and only 6 of 22 basins meet the R-squared bar. These limits govern application of predictions to unmeasured wells.

The [supplementary screening and calibration audit](docs/screening-calibration.md) separates missing-Mg unknowns from failures and reports reliability by held-out basin and dataset with bin support. Its outputs are exploratory and do not change the frozen screen denominator or model verdict.
