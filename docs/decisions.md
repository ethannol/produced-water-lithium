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
