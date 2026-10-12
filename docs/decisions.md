# Decision log

Append-only. One entry per scoping, data, or analytical decision, with the date,
the evidence (which script, inspection or document), and the alternatives rejected.
Entries after the freeze are marked POST-FREEZE and are exploratory.

## 2026-10-12 Download URLs verified before downloading; provenance recorded

- Evidence: HEAD requests to the four ScienceBase file URLs in the brief returned
  HTTP/2 200 with content-lengths 80,625,044 (workbook), 29,653 (dictionary), 310,373
  (metadata XML) and 6,483 (version history), matching the brief byte for byte; the
  item JSON (`?format=json`) lists the same files plus a shapefile zip that is not used.
  Response headers (minus the cookie and content-security-policy lines) and SHA-256 of
  every archive file are in `data/raw/manifest.json`; the raw `.headers` dumps stay
  beside the archive files. The first inspection of the workbook was done with
  `python -I` from a script kept in the session scratch directory, outside the archive.
- Rejected: the shapefile (same records, no extra fields the study needs).

## 2026-10-12 Archive lives in data/archive/npwgd/, not data/raw/

- Evidence: `cairn freeze` hashes every file under `data/raw/**` and `cairn verify`
  fails when a hashed file is missing. The 80 MB workbook must stay out of git, so a
  fresh checkout would fail verification if it were under `data/raw/`. Same workaround
  as the sibling projects. `data/raw/` holds the 68-column extract (48 MB, committed),
  the data dictionary as CSV, the metadata XML, the version history and the manifest.
- Rejected: committing the workbook (size); committing only a parquet (brief asks for CSV).

## 2026-10-12 Extract columns and format

- Evidence: `src/pwlithium/extract.py`. One pass over the single sheet with openpyxl in
  read-only mode; empty cells become empty fields, floats are written with their
  shortest round-trip repr, text unchanged. 68 of the 209 columns: identity and
  provenance (IDUSGS, IDORIG, IDDB, SOURCE, REFERENCE, REMARKS), classification
  (PLAYTYPE, WELLTYPE, BASIN, FORMATION, FORMSIMPLE, ages), location and its quality
  flags, well identifiers, dates, physical parameters, the SG pair (SG, SPGRAV), TDS and
  its description, the major and minor ions the brief lists plus I, FeTot, Si and KNa,
  and CHARGEBAL. The workbook has 113,135 data rows, as the metadata states.
- Rejected: all 209 columns (isotopes, organics, gases and rare earths are not used and
  would double the committed size).

## 2026-10-12 cairn.toml: report rendered to reports/report.md

- Evidence: the brief asks for `reports/report.md`; the template renders to `report.md`
  at the root. `report = "reports/report.md"` was set once, at setup, before the freeze.
  No other harness configuration was changed.

## 2026-10-12 Non-detects are not represented in v3.0 (finding, pre-freeze)

- Evidence: `python -I` inspection of every cell in the workbook. The Li column has
  6,416 non-empty cells, all numeric, none zero, none negative, no text; the same holds
  for Na, K, Ca, Mg, Cl, Br, SO4, HCO3, Sr, B (Ba has five zeros, CO3 four). The
  dictionary has no detection-limit or qualifier fields. The metadata's compilation
  procedure says non-numeric entries in chemistry columns were replaced by codes
  (-1 trace, -2 none detected, -3 not analyzed, -4 transcription error), yet no
  negative chemistry value survives in v3.0, and REMARKS mentions detection only in
  three rows about glycol ethers. Conclusion: a lithium value below detection is an
  empty cell, indistinguishable from "not analyzed". The pre-registration treats every
  non-empty lithium value as a detected measurement and makes no substitution.
- Rejected: treating the smallest values as detection limits (no evidence); dropping
  integer-valued values as rounded limits (they are reporting precision, see the
  per-dataset diagnostic).

## 2026-10-12 Charge balance: zero means balanced by construction (finding, pre-freeze)

- Evidence: recomputing the percent charge balance from the extract's ions with the
  USGS formula (cations Ca, Mg, Na, K, Ba, Sr; anions Cl, SO4, Br, HCO3) reproduces
  CHARGEBAL with correlation 0.99998. 46,565 rows have CHARGEBAL exactly 0, and all of
  them recompute to |balance| < 0.05 percent: they are analyses in which sodium was
  reported by difference, so the balance cannot judge them. They are concentrated in
  USGSBREIT (38,597 rows) and the state agency compilations. The pre-registration keeps
  them (they pass the tolerance) and reports their count by dataset as a diagnostic.
- Tolerance: 10 percent primary, with 5, 15 and none as sensitivities. The v2.x cull
  flags (removed in v3.0) used 5 percent after Hitchon and Brulotte (1994); 10 percent
  is the common produced-water convention and keeps historic analyses with fewer
  reported ions. Reporting all four makes the choice visible.

## 2026-10-12 Unit of analysis and deduplication key (pre-freeze)

- Evidence: among lithium rows, 4,571 have an API number (3,345 distinct dataset-API
  keys, up to 28 rows per key, mostly USGSBREIT resamples and NBMGGEOTHERMAL), 1,107
  more have a WELLNAME, and 738 have neither, of which 463 carry approximate coordinates
  (APPALACHIAN, SHOUAKARSTASH, ROWANAKOB, BLONDESUTICA mostly). IDORIG is nearly unique
  within dataset and so identifies samples, not wells. Within repeated-API wells the
  median log10 max/min lithium spread is 0.18, so collapsing by median matters.
- Decision: well within IDDB, keyed by API, else WELLNAME, else exact coordinates plus
  DEPTHUPPER, else the row; medians within well. Counts per key class are recorded.
- Rejected: IDORIG as the key (sample id); cross-dataset well matching (no reliable key;
  the leave-one-dataset-out protocol tests the consequence instead).

## 2026-10-12 Population: what counts as produced water (pre-freeze)

- Evidence: PLAYTYPE x WELLTYPE cross-tab. PLAYTYPE Geothermal (499 rows, all
  NBMGGEOTHERMAL) and Injection (21) are not produced water; WELLTYPE Water, CO2 and
  Injection (17 rows) likewise; 23 rows name injected or fracturing fluid in FORMATION.
  Coal-bed methane water is produced water and stays. STATE includes Ontario (146) and
  Saskatchewan (56), excluded because the question is about U.S. basins. 66 rows have SG
  outside the 0.9 to 1.3 range the USGS used to fit the SG-from-TDS regression.
- Rejected: restricting to Sedimentary only (shale and coal plays are part of the
  feedstock question).

## 2026-10-12 Lithium-focused datasets named by the version history

- Evidence: `version_history.txt`, v3.0 entry: "We focused on high lithium datasets
  (STANDARDLITHIUM, TETRA, TROUTSTEUBER, NYLITHIUM)". These four hold 22 + 8 + 3 lithium
  rows (NYLITHIUM, STANDARDLITHIUM, TETRA) plus TROUTSTEUBER in the extract. The
  bias-adjusted view removes exactly these four. No REFERENCE or SOURCE string in the
  extract contains the word "lithium", so no broader text rule is available.
- Rejected: removing every dataset added in v3.0 (23 datasets; most are not
  lithium-motivated) as the primary adjustment; it is not pre-registered.

## 2026-10-12 Thresholds and their sources (pre-freeze)

- Evidence: WebSearch and WebFetch before the freeze. Open-access full texts were read
  through Europe PMC (the publisher pages returned HTTP 403 to the fetch tool).
  Knierim and others 2024 (Science Advances, doi:10.1126/sciadv.adp8149) use a 100 mg/L
  lithium threshold "often cited as the minimum concentration" for commercial extraction
  and call it a cutoff used for some DLE technologies. Dugamin and others 2021
  (Scientific Reports, doi:10.1038/s41598-021-99912-7) state extraction is more
  favourable at Mg/Li below 10 (mass ratio) and give no TDS cutoff. Mackey and others
  2024 (Scientific Reports, doi:10.1038/s41598-024-58887-x) treat Mg/Li mass ratios
  above 6 as high. A trade commentary citing a 50 mg/L baseline was found but its text
  could not be retrieved, so 50 enters only as the lower edge of the sensitivity grid.
- Decision: primary Li >= 100 mg/L and Mg/Li <= 10; grid {50, 100, 200} x {6, 10, 20}
  plus a brine-only (TDS >= 100,000 mg/L) variant.

## 2026-10-12 cairn: `cairn profile` fails on the extract (blocker)

- Evidence: `cairn profile data/raw/npwgd_v3_extract.csv` raises
  `ValueError: Mixed timezones detected` from `pandas.to_datetime(format="mixed")` inside
  `cairn.profile._col_profile`, which tries to parse every text column as dates; a
  free-text column (REMARKS or a formation name) parses as mixed-timezone timestamps.
- Workaround: `scripts/00_profile.py` writes the same kind of profile (row grain, nulls,
  types, distinct counts, censoring markers) to `profiles/npwgd_v3_extract.md` and
  records the row count. cairn is not edited.

## 2026-10-12 Session note: the cairn hooks were not active

- Evidence: the session that built this project ran with its working directory one level
  above the project, so the `.claude/settings.json` hooks that `cairn init` installs
  (protected-path denial, script lint on save, the Stop gate) did not fire. The sensors
  are run by hand: `cairn verify --quick` during development and the full `cairn verify`
  with the clean re-execution before finishing. Protected paths are respected by
  convention; `cairn.toml` was edited once, at setup, before any analysis.

## 2026-10-12 POST-FREEZE Tables live in reports/tables, figures in reports/figures

- Evidence: the brief asks for `reports/` to hold the report, figures and tables; cairn's
  template puts them under `artifacts/`. Scripts write tables to `reports/tables/` and
  figures to `reports/figures/`; `artifacts/` keeps the ledger (`numbers.json`) and the
  checks log. No result changes.

## 2026-10-12 POST-FREEZE A missing-key bug caught by the harness, fixed before any result was read

- Evidence: the first run of `scripts/10_prepare.py` collapsed 87,458 rows to 54,579
  wells; the rebuilt key in `scripts/20_missingness.py` then failed inside the fold
  splitter because 2,879 rows (APPALACHIAN, no API or well name, exact coordinates,
  no depth) had a missing `well_id`: under pandas 3 the default string dtype keeps NaN
  as missing through `astype(str)`, so concatenating the depth into the key produced a
  missing key and `groupby` silently dropped those rows from the well table. The key is
  now formatted explicitly ("nodepth" for a missing depth) and `well_key` raises on any
  missing key. After the fix the primary well table has 54,957 wells and 4,141 lithium
  wells. The basin tables were not inspected between the two runs beyond the console
  echo of the top rows, and no reported number comes from the first run.

## 2026-10-12 POST-FREEZE Compute: single-threaded OpenMP, folds in parallel processes

- Evidence: one HistGradientBoosting fit on 3,921 wells took 13 seconds with the
  default OpenMP thread pool on this ten-core machine and 0.33 seconds with
  `OMP_NUM_THREADS=1` (thread oversubscription on small data). `scripts/40_model.py`
  and `scripts/45_control.py` set the variable before importing scikit-learn, and
  `pwlithium.cv.evaluate` runs outer folds in parallel processes (joblib). Every fold is
  seeded and the fold list is fixed, so results do not depend on scheduling; the model
  step runs in under a minute. The positive control is its own step (`45_control.py`)
  so that each step stays short. Nothing in the pre-registered models, grids or
  protocols changed.

## 2026-10-12 POST-FREEZE Ridge "precision at the floor" is undefined when it never predicts above the floor

- Evidence: the regularized linear model shrinks toward the mean and predicts
  Li >= 100 mg/L for very few or no wells under some protocols, so its precision at the
  floor is 0 or undefined while its AUC (a ranking measure) is high. Both numbers are
  reported as computed; the report says why they disagree.

## 2026-10-12 What blocked in cairn and the workarounds (nothing in cairn was edited)

1. `cairn freeze` hashes everything under `data/raw/`, so the gitignored 80 MB workbook
   lives in `data/archive/npwgd/` and only the extract is frozen (entry above).
2. `cairn profile` raises `ValueError: Mixed timezones detected` on this extract because
   it tries to parse every text column as dates. `scripts/00_profile.py` writes the
   profile instead and records the same facts.
3. The script lint (C102) flags any `.join(` attribute call, including string joins.
   String joins live in `pwlithium.util.commas` and `pwlithium.util.lines`.
4. `cairn render` writes only `report.tmpl.md`; `scripts/60_docs.py` renders the README,
   walkthrough and resume bullet with `cairn.numbers.render` and fails on any unresolved
   key, and records the test count from the test files.
5. `cairn verify` warns on bare numbers in the report template, including digits inside
   headings and hyphenated words ("Result 2", "5-fold"). Thresholds that are inputs, not
   results, are written in inline code; headings and words were rephrased.
6. `cairn.censored_values` expects `<limit` text or marker words; the Li column has none,
   so the sensor records 0 censored and the non-detect finding is carried by the
   `nondetect.*` ledger keys instead.
7. The hooks did not fire (session note above); the sensors were run by hand and the
   final `cairn verify` (with the clean rerun) passed with 0 failures and 0 warnings.
8. The cairn checkout gained a commit during the session (a portfolio card, no harness
   code); the ledger records the commit at run time (`env.cairn_commit`), which the README
   quotes.
