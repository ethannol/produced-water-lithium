# Pre-registration

Written before computing any basin ranking or fitting any model. Frozen by
`cairn freeze`; a changed hash fails verification. Anything not described here is
exploratory and must be labelled as such in the report. Numbers in this document are
thresholds and rules decided now, not results. Structural facts about the extract
quoted here (column types, what the metadata says) come from the first `python -I`
inspection and the USGS documentation, logged in `docs/decisions.md`.

## Question

Descriptive: which U.S. basins and simplified formations (FORMSIMPLE) in the USGS
National Produced Waters Geochemical Database v3.0 (December 2023) have produced-water
lithium concentrations and magnesium-to-lithium ratios that pass a screening definition
for extraction, with uncertainty that respects the well-within-dataset structure, and how
much does the ranking change when the datasets the version history names as
lithium-focused are removed and when the charge-balance tolerance changes.
Predictive: on wells where lithium was measured, how well can log10 lithium be predicted
from major-ion chemistry, total dissolved solids, depth and play type when the evaluation
holds out random wells, whole source datasets (IDDB) and whole basins. Period: every
sample in the database (sampling dates 1930s to 2010s). Units: mg/L.

## Primary quantity

Descriptive, per basin (and per FORMSIMPLE): (a) the median well-level lithium
concentration in mg/L with a 95% cluster bootstrap interval and (b) the fraction of
wells passing the primary screen (Li >= 100 mg/L and Mg/Li mass ratio <= 10) with the
same interval. Basins are presented ordered by (a) with the intervals shown; no point
ranking is published without them. Predictive: the root-mean-square error of out-of-sample
predictions of log10 Li (mg/L) under each of the three protocols, with spread across
folds, for a regularized linear model and a gradient boosted tree model.

## Unit of analysis

The unit is the well within its source dataset (IDDB). A row of the database is one
sample; some datasets hold repeated samples from one well (flowback time series,
resamples), and the same physical well can appear in two datasets. Rows are collapsed to
wells with this key, applied within IDDB in order: the 14-digit API number when present;
otherwise WELLNAME when present; otherwise, when coordinates are not flagged approximate
(COORDAPX empty), the triple (LATITUDE, LONGITUDE rounded to 4 decimals, DEPTHUPPER);
otherwise the row itself (IDUSGS), because rows with approximate coordinates and no well
identifier cannot be grouped. The number of rows in each key class and the number
collapsed are reported. Within a well, every numeric variable is the median across its
rows (lithium, each ion, TDS, depth, charge balance) and every categorical variable is
the most frequent value. Wells, never rows, are resampled in the bootstrap and are the
grouping unit in every cross-validation split. The same well appearing in two datasets is
two units; the leave-one-dataset-out protocol is what tests the consequence.

## Population and comparability

- Source: `data/raw/npwgd_v3_extract.csv`, a deterministic 68-column extract of the
  113,135-row workbook (`data/raw/manifest.json` holds the archive SHA-256, headers and
  row count). The extract is never edited; every exclusion below is logged with its row
  count in `data/derived/exclusion_log.csv`.
- Produced water means PLAYTYPE in {Sedimentary, Shale, Coal}: oil, gas and coal-bed
  methane reservoirs. Excluded: PLAYTYPE Geothermal and Injection; WELLTYPE in
  {Injection, Water, CO2}; rows whose FORMATION names an injected or fracturing fluid
  (matches, case-insensitive, "inject" or "frac water" or equals "Frac").
- U.S. only: STATE values that are U.S. states or "OffShore-" entries; Canadian
  provinces (Ontario, Saskatchewan) excluded. Rows with BASIN "Unknown" or without
  coordinates are excluded from basin tables.
- Unit conversion: rows reported in ppm were converted to mg/L by the USGS with a specific
  gravity that is observed (SPGRAV) or estimated by regression. Rows whose SG lies outside
  0.9 to 1.3 (the range the USGS used to fit that regression) are excluded. The number of
  retained rows and wells whose chemistry depends on an estimated SG (ppm with SPGRAV
  empty) is reported, overall and among wells with lithium.
- Charge balance: the primary population keeps rows with |CHARGEBAL| <= 10 percent;
  rows with CHARGEBAL empty are excluded from the screening tables (counted). Sensitivity:
  the basin tables are recomputed at tolerances 5, 15 and no filter. Diagnostic reported
  alongside: rows with |CHARGEBAL| < 0.05 percent are balanced by construction (sodium
  computed by difference in the source analysis) and the filter cannot judge them; their
  count by dataset is reported.
- Screening population: wells with lithium measured. The Mg/Li screen uses wells with
  both lithium and magnesium; wells with lithium but no magnesium are counted and appear
  only in the lithium-only summaries.
- Reporting thresholds: a basin enters the ranking table with at least 20 wells with
  lithium; a FORMSIMPLE enters the formation table with at least 10 wells, and "Unknown"
  is excluded from the formation table. Smaller groups are listed in an appendix table
  without a rank.
- Bias-adjusted view: the same tables recomputed after removing the four datasets the
  v3.0 version history names as the lithium-focused additions (STANDARDLITHIUM, TETRA,
  TROUTSTEUBER, NYLITHIUM), and a by-dataset-within-basin table for every basin with
  more than one dataset contributing lithium wells.
- Missingness comparison, on the included rows before collapsing: rows with lithium
  versus rows without, compared on TDS, depth, sampling decade, play type, basin mix and
  dataset mix (medians, standardized mean differences on log10 TDS and log10 depth, and
  composition tables), plus a 5-fold cross-validated logistic regression of
  "lithium present" on log10 TDS, log10 depth (with missing indicators), decade, play type
  and basin, reporting its AUC.

## Handling of missing and censored values

Finding from the first inspection, recorded before any analysis: the Li column (and every
other chemistry column) holds only positive numbers; there are no zeros, negative values,
text flags or "<" prefixes, and the dictionary has no detection-limit fields. The
metadata's compilation procedure describes negative codes for earlier versions (-1 trace,
-2 none detected, -3 not analyzed, -4 transcription error), but no negative chemistry
values remain in v3.0. Therefore a value below detection is stored as an empty cell,
indistinguishable from "not analyzed". Consequences, fixed now: every non-empty lithium
value is treated as a detected measurement; "lithium measured" means Li non-empty;
no substitution of any kind is made for empty cells; the share of lithium values that are
integer-valued is reported by dataset as a reporting-precision diagnostic, and the
smallest reported values are listed, but neither is used to filter. The missingness
comparison above quantifies how non-random "not measured" is; its results are reported as
limits on the descriptive ranking, not corrected for. Missing magnesium excludes a well
from the Mg/Li screen only. Missing depth in the model is handled by a missing indicator
plus the training-fold median. Wells lacking any of Na, K, Ca, Mg, Cl or TDS are excluded
from the model (counted).

## Viability thresholds

Primary screen, per well: Li >= 100 mg/L and Mg/Li (mass ratio, mg/L over mg/L) <= 10.
Sources, found before this freeze:

- Lithium floor 100 mg/L: Knierim, K.J., and others, 2024, Evaluation of the lithium
  resource in the Smackover Formation brines of southern Arkansas using machine learning,
  Science Advances 10(39), eadp8149, doi:10.1126/sciadv.adp8149. The methods use
  "a threshold of 100 mg/liter for lithium, which is often cited as the minimum
  concentration" for commercial extraction, and the discussion calls it "a concentration
  cutoff used for some direct lithium extraction technologies".
- Mg/Li ceiling 10 (mass ratio): Dugamin, E.J.M., and others, 2021, Groundwater in
  sedimentary basins as potential lithium resource: a global prospective study, Scientific
  Reports 11, 21091, doi:10.1038/s41598-021-99912-7: "lithium extraction is more
  favourable when Mg/Li ratio is lower than 10" (their compiled database reports Mg/Li
  as a mass ratio).
- Corroborating Mg/Li source: Mackey, J., and others, 2024, Estimates of lithium mass
  yields from produced water sourced from the Devonian-aged Marcellus Shale, Scientific
  Reports 14, doi:10.1038/s41598-024-58887-x, who treat Mg/Li mass ratios above 6 as
  high and associate them with less efficient, costlier extraction.
- TDS: none of the sources gives a TDS cutoff for extraction; Dugamin and others note that
  lithium correlates positively with TDS and classify brines as TDS > 100,000 mg/L. TDS is
  therefore reported, not screened on, in the primary definition.

Sensitivity grid (all reported): lithium floor in {50, 100, 200} mg/L; Mg/Li ceiling in
{6, 10, 20} (6 from Mackey and others; 20 is a deliberately loose bound, not from a
citation); and one additional variant that also requires TDS >= 100,000 mg/L (brine
class). The primary is floor 100, ceiling 10, no TDS requirement.

Uncertainty: a 95% percentile bootstrap with 1000 resamples, seed 20261012, resampling
wells. In a basin with more than one dataset contributing wells the bootstrap is
clustered: datasets are resampled with replacement first, then wells within each drawn
dataset. In a basin with one dataset, wells are resampled directly. The same procedure
gives intervals for the median and for the screened fraction.

## Decision rule

Descriptive ranking, decided now:

1. The headline table lists basins (>= 20 lithium wells) ordered by median well lithium
   with intervals, the screened fraction with intervals, well count, dataset count and
   the Mg/Li median and interquartile range.
2. "Ranking robust to compilation bias" if, after removing the four lithium-focused
   datasets, the set of the five highest-median basins is unchanged in at least four of
   five members and no pair of basins with non-overlapping primary intervals changes
   order. Otherwise "ranking partly an artifact of which datasets were compiled", and the
   basins that move are named.
3. "Ranking robust to the charge-balance tolerance" by the same test across tolerances
   5, 10, 15 and none.
4. "Missing is not random" if the cross-validated AUC of the lithium-present model is
   >= 0.70 or either standardized mean difference (log10 TDS, log10 depth) is >= 0.20 in
   absolute value. Otherwise "no evidence that lithium measurement depends on the
   compared variables".
5. A basin with fewer than 20 lithium wells receives no rank. A screened fraction whose
   interval includes zero is reported as "no evidence of screen-passing wells", not as a
   small fraction.

Predictive model, decided now. Target: log10 Li (mg/L) on wells with lithium measured
(all treated as detected, see above). Features: centred log-ratios of the subcomposition
{Na, K, Ca, Mg, Cl} (compositional; the closure is removed and the scale is carried
separately by TDS), log10 TDS, log10 depth midpoint (mean of DEPTHUPPER and DEPTHLOWER,
or whichever is present) with a missing indicator and training-fold median imputation,
PLAYTYPE one-hot, and ERA one-hot with a "missing" level. Models: ridge regression on
standardized features with alpha in {0.01, 0.1, 1, 10, 100}; HistGradientBoostingRegressor
with learning_rate in {0.05, 0.1}, max_leaf_nodes in {7, 15, 31}, max_iter 300,
min_samples_leaf 20. The grid point is chosen inside each training fold by 3-fold grouped
cross-validation (grouped by the same variable as the outer protocol: well, dataset or
basin) on RMSE. No feature selection on the full data; the scaler and imputer are fitted
on the training fold only.

Protocols: (1) random 5-fold grouped by well, three repetitions (seeds 0, 1, 2);
(2) leave-one-dataset-out, every IDDB with at least 20 modelling wells held out in turn,
trained on all other wells; (3) leave-one-basin-out, every BASIN with at least 20
modelling wells held out in turn. Metrics per fold and pooled over out-of-fold
predictions: RMSE and MAE of log10 Li, R-squared (pooled: 1 - SSE/SST over all
out-of-fold predictions, SST about the mean of the held-out targets; per fold the same
within the fold). Spread: minimum, median and maximum across folds, and the
interquartile range. Screening quality at the pre-registered floor (100 mg/L): AUC of the
predicted log10 Li as a score for actual Li >= 100; precision and recall when a well is
called positive if predicted Li >= 100; calibration of the probability
P = 1 - Phi((log10 100 - prediction) / sigma) with sigma the RMSE of the inner
cross-validation on the training fold, summarised as a reliability table by probability
decile and the Brier score. Positive control: the same pipeline with log10 TDS as the
target and TDS removed from the features, both models, all three protocols.

Conclusions for the predictive question:

- "Useful out of basin" if the gradient boosted model's pooled leave-one-basin-out
  R-squared >= 0.30 and AUC at the floor >= 0.75.
- "Useful within basin only" if the random-fold pooled R-squared >= 0.30 but the
  leave-one-basin-out criterion fails; the leave-one-dataset-out result is reported as
  the batch-effect check between them.
- "Not usefully predictable" if the random-fold pooled R-squared < 0.30.
- The positive control must reach random-fold R-squared >= 0.80 for TDS; if it does not,
  the pipeline is treated as broken and no predictive conclusion is drawn.
- Abstain from the predictive question if fewer than 500 modelling wells remain after
  exclusions.

## Confirmatory vs exploratory

Confirmatory: the basin and formation tables with cluster bootstrap intervals; the
bias-adjusted and charge-balance sensitivity views and the robustness tests above; the
sensitivity grid of thresholds; the missingness comparison and its AUC; the three-protocol
prediction comparison with both models and the positive control; the SG-estimated,
balanced-by-construction and deduplication counts. Exploratory, labelled so wherever
reported: any additional feature (optional ions such as Br, Sr, SO4, HCO3; formation
identity), any model or grid not listed, per-dataset-within-basin interpretation beyond
the tables, permutation importance, maps, and anything decided after the freeze.
