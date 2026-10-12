# Data dictionary

Source: U.S. Geological Survey National Produced Waters Geochemical Database, version 3.0
(December 2023), doi:10.5066/P9DSRCZJ, public domain. Retrieved 2026-10-12 from the
ScienceBase item (URLs, headers and SHA-256 in `data/raw/manifest.json`). The full
209-field dictionary is `data/raw/data_dictionary.csv`; this file covers the extract.

## data/raw/npwgd_v3_extract.csv

- One row represents: one produced-water (or related) sample as compiled by the USGS;
  some datasets hold repeated samples from one well (TIMESERIES, DAY) and the same well
  can appear in more than one dataset.
- Key: IDUSGS (unique per row; changes between database versions). IDORIG is the id in
  the source dataset (a sample id). IDDB is the input dataset and the batch variable.
- Units: every chemistry column is mg/L (ppm converted by the USGS using SG). Depths in
  feet. TEMP in degrees C as combined by the USGS. CHARGEBAL in percent.
- Empty cell: not reported or not analyzed. There is no detection-limit convention in
  v3.0 (see `docs/decisions.md`): below-detection results are empty cells.

| Field | Meaning |
|---|---|
| IDUSGS, IDORIG | row id in this database; id in the source dataset |
| IDDB, SOURCE, REFERENCE, REMARKS | input dataset; compilation source; published reference; free text |
| PLAYTYPE | reservoir type by formation: Sedimentary, Shale, Coal, Geothermal, Injection (supersedes WELLTYPE) |
| WELLTYPE | legacy well type: Conventional Hydrocarbon, Shale Gas, Tight Oil, Tight Gas, CBM, Geothermal, Injection, Water, CO2, Undefined |
| BASIN, PROVINCE, REGION | basin as reported and standardized; USGS 1995 assessment province and region |
| FORMATION, FORMSIMPLE, GROUP, MEMBER | formation as reported; standardized formation name (first listed if several); group; member |
| ERA, PERIOD, EPOCH, LITHOLOGY | geologic age (from source or GEOLEX by FORMATION); lithology |
| STATE, COUNTY, FIELD | state (or province, or OffShore-State); county; field |
| LATITUDE, LONGITUDE, COORDAPX, COORDNEW | decimal degrees; text when the location is approximate (county, field, TRS or basin centroid); how the location changed from v2.3 |
| WELLNAME, API, NWIS, DATECOMP, ELEVATION | well name; 14-digit API; NWIS site; completion date; elevation (ft) |
| DEPTHUPPER, DEPTHLOWER | upper and lower perforation depth of the sampled interval, ft |
| TIMESERIES, DAY, DATESAMPLE, DATEANALYS | order and day of time-series samples; sample and analysis dates (YYYY-MM-DD) |
| METHOD, LAB | sampling method; laboratory |
| TEMP, PH, COND | combined temperature; pH; conductivity (uS/cm) |
| SG, SPGRAV | specific gravity used for conversion (reported or regression-estimated); reported specific gravity |
| UNITSORIG | original units, mg/L or ppm |
| TDS, TDSLAB, TDSCALC, TDSDESC | TDS used (mg/L) and its origin: reported measured, reported calculated, calculated from ions, missing |
| Li, Na, K, Ca, Mg, Sr, Ba, B, Cl, Br, I, SO4, HCO3, CO3, ALKALINITY, FeTot, Si, KNa | ions, mg/L; KNa is sodium plus potassium when reported combined |
| CHARGEBAL | percent charge balance of major ions computed by the USGS (cations Ca, Mg, Na, K, Ba, Sr; anions Cl, SO4, Br, HCO3) |

Known quirks: 46,565 rows have CHARGEBAL exactly 0 (sodium by difference); 44 percent of
rows use a regression-estimated SG; approximate coordinates on 32,651 rows; FORMSIMPLE
"Unknown" on 10,972 rows; DATESAMPLE present on 76 percent of rows.

## data/raw/data_dictionary.csv

The USGS dictionary (name, data type, description) for all 209 fields, converted from the
distributed xlsx without change.

## data/raw/USGS_NPWGDv3_metadata.xml, data/raw/version_history.txt

FGDC metadata with the v3.0 process steps (location updates, FORMSIMPLE and PLAYTYPE,
unit conversion and charge balance, error corrections) and the version history naming
the datasets added in each version.
