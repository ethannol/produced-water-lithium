# Produced-water lithium: where it is, and how much of that is the compilation

_Rendered by `cairn render` from `artifacts/numbers.json`; every figure below is a ledger
value. Do not edit `reports/report.md`. The analysis plan was frozen in `docs/prereg.md`
before any ranking or model fit; anything outside it is marked exploratory._

## Question

Which U.S. basins and formations in the USGS National Produced Waters Geochemical
Database v3.0 have produced-water lithium and major-ion chemistry that pass a
pre-registered screen (Li >= {{screen.floor_mg_l:g}} mg/L and Mg/Li <= {{screen.ceiling_mg_li:g}},
mass ratio), with uncertainty, and how much does that picture change when the known
biases of the compilation are accounted for? And where lithium was not measured, how well
can it be predicted from major-ion chemistry, depth and formation when the evaluation
holds out whole source datasets and whole basins rather than random rows?

## Data and comparability

One row is one compiled produced-water sample. The workbook ({{manifest.archive_bytes}}
bytes, SHA-256 `{{manifest.archive_sha256}}`, served with status `{{manifest.archive_http_status}}`)
has {{manifest.extract_rows}} rows and {{nondetect.dictionary_fields}} fields; the committed
extract keeps {{manifest.extract_columns}} columns. Rows profiled: {{profile.rows}}, in
{{profile.n_datasets}} input datasets (IDDB) and {{profile.n_basins}} basins;
{{profile.li_rows}} rows carry a lithium value.

**How non-detects are represented (finding).** The dictionary has
{{nondetect.dictionary_detection_fields}} detection-limit or qualifier fields. The Li column
has {{nondetect.Li.nonempty}} non-empty cells: {{nondetect.Li.non_numeric}} are non-numeric,
{{nondetect.Li.zero}} are zero, {{nondetect.Li.negative}} are negative and
{{nondetect.Li.lt_prefixed}} carry a "<" prefix; REMARKS mentions detection in
{{nondetect.remarks_detect_rows}} rows, none about lithium. The metadata's compilation
procedure describes negative codes for "none detected" in earlier versions, but none
survive in v3.0. A lithium result below detection is therefore an empty cell, which cannot
be told from "not analyzed". Every non-empty value is treated as a detected measurement.
The smallest value is {{nondetect.li_min}} mg/L, {{nondetect.li_n_below_1}} values are
below 1 mg/L, and {{nondetect.li_share_integer:.0%}} of values are whole numbers (reporting
precision of the older compilations, highest in the state and industry tables).

**Population.** Pre-registered exclusions, in order (rows): play type not produced water
(geothermal, injection) {{prepare.excl.playtype_not_produced_water}}; injection, water and
CO2 well types {{prepare.excl.welltype_injection_water_co2}}; injected-fluid formation
names {{prepare.excl.formation_injected_fluid}}; Canadian provinces
{{prepare.excl.non_us_state}}; no coordinates {{prepare.excl.no_coordinates}}; basin
unknown {{prepare.excl.basin_unknown}}; specific gravity outside the USGS regression range
{{prepare.excl.sg_out_of_range}}. {{prepare.rows_included}} of {{prepare.rows_raw}} rows
remain. The charge-balance tolerance of {{prepare.cb.tolerance:g}} percent then removes
{{prepare.cb.removed_rows}} rows, and {{prepare.cb.null_rows}} rows with no balance are set
aside, leaving {{prepare.cb.rows_kept_tol10}} rows ({{prepare.cb.rows_kept_tol5}} at a
tolerance of `5`, {{prepare.cb.rows_kept_tol15}} at `15`). Among rows with lithium the filter
removes {{prepare.cb.li_rows_removed}}.

**Two things the quality fields cannot see.** {{prepare.cb.balanced_by_construction_rows}}
included rows ({{prepare.cb.balanced_by_construction_li_rows}} with lithium) have a charge
balance of exactly zero because sodium was reported by difference; the balance cannot
judge them, and {{prepare.cb.balanced_by_construction_top_dataset_rows}} of them are in
{{prepare.cb.balanced_by_construction_top_dataset}}. And {{prepare.sg.estimated_rows}} rows
({{prepare.sg.share_estimated:.0%}}) carry a specific gravity estimated by regression rather
than measured; {{prepare.sg.ppm_estimated_rows}} of the {{prepare.sg.ppm_rows}} rows reported
in ppm were converted to mg/L with that estimate, {{prepare.sg.ppm_estimated_li_rows}} of
them with lithium ({{prepare.wells.li_wells_sg_estimated}} lithium wells).

**Wells, not rows.** The unit is the well within its dataset. {{prepare.wells.rows_in}}
rows collapse to {{prepare.wells.n_wells}} wells ({{prepare.wells.rows_collapsed}} rows were
repeats); among lithium rows, {{prepare.wells.li_rows_in}} rows become
{{prepare.wells.n_wells_li}} wells, {{prepare.wells.li_wells_multi_row}} of them with more
than one sample (up to {{prepare.wells.li_max_rows_per_well}}). Key classes for lithium
wells: API {{prepare.wells.li_wells_key_api}}, well name {{prepare.wells.li_wells_key_wellname}},
exact coordinates plus depth {{prepare.wells.li_wells_key_coords}}, and
{{prepare.wells.li_wells_key_row}} single rows with approximate coordinates and no
identifier that could not be grouped (a known limit: they may over-count wells).
{{prepare.wells.li_wells_share_coord_approx:.0%}} of lithium wells have approximate
(county, field or basin centroid) coordinates, so no spatial claim below basin scale is
made. {{prepare.wells.li_wells_without_mg}} lithium wells lack magnesium and enter only the
lithium-only summaries.

## Method

Pre-registered screen per well: Li >= {{screen.floor_mg_l:g}} mg/L and Mg/Li <=
{{screen.ceiling_mg_li:g}} (sources in `docs/prereg.md`: Knierim and others 2024 for the
floor; Dugamin and others 2021 for the ceiling, corroborated by Mackey and others 2024).
Per basin with at least {{screen.min_wells_basin}} lithium wells (and per FORMSIMPLE with
at least {{screen.min_wells_formation}}): the median well lithium and the screened fraction,
each with a `95%` percentile interval from {{screen.n_boot}} bootstrap resamples of wells,
clustered by dataset where a basin has more than one (seed {{screen.seed}}). The ranking is
recomputed without the datasets the version history names as lithium-focused
({{screen.adj.datasets}}) and at charge-balance tolerances of `5`, `15` and none; a threshold
grid of {{screen.grid.n_cells}} cells is reported. Prediction: log10 Li on wells with
lithium, features = centred log-ratios of Na, K, Ca, Mg and Cl, log10 TDS, log10 depth
midpoint with a missing indicator, play type and era; ridge and histogram gradient
boosting with small grids chosen inside each training fold; random five-fold by well (three
repetitions), leave-one-dataset-out and leave-one-basin-out.

## Result: where the lithium is, with the uncertainty shown

{{screen.n_li_wells}} wells have lithium; {{screen.n_above_floor}}
({{screen.share_above_floor:.1%}}) are at or above the floor, and
{{screen.n_pass_primary}} ({{screen.share_pass_primary:.1%}}) also meet the Mg/Li ceiling:
{{screen.n_above_floor_high_mgli}} of the high-lithium wells have too much magnesium for the
primary screen. The median well is {{screen.li_median_all_wells:g}} mg/L with Mg/Li
{{screen.mgli_median_all_wells:.0f}}; the 90th percentile is {{screen.li_q90_all_wells:g}} mg/L.
{{screen.n_basins_ranked}} of {{screen.n_basins_with_li}} basins reach the reporting
threshold ({{screen.n_basins_ranked_wells}} wells); {{screen.n_basins_any_pass}} of them
contain at least one passing well and {{screen.n_basins_frac_interval_excludes_zero}} have a
screened-fraction interval that excludes zero.

![Basin ranking](figures/fig2_basin_ranking.png)

Ordered by median lithium (`95%` cluster bootstrap intervals; well and dataset counts):

| basin | wells | datasets | median Li, mg/L | screened fraction | Mg/Li median | approximate coordinates |
|---|---|---|---|---|---|---|
| {{screen.basin1.name}} | {{screen.basin1.n_wells}} | {{screen.basin1.n_datasets}} | {{screen.basin1.median_li:.0f}} ({{screen.basin1.median_lo:.0f}} to {{screen.basin1.median_hi:.0f}}) | {{screen.basin1.frac_pass:.2f}} ({{screen.basin1.frac_lo:.2f}} to {{screen.basin1.frac_hi:.2f}}) | {{screen.basin1.mgli_median:.0f}} | {{screen.basin1.share_coord_approx:.0%}} |
| {{screen.basin2.name}} | {{screen.basin2.n_wells}} | {{screen.basin2.n_datasets}} | {{screen.basin2.median_li:.0f}} ({{screen.basin2.median_lo:.0f}} to {{screen.basin2.median_hi:.0f}}) | {{screen.basin2.frac_pass:.2f}} ({{screen.basin2.frac_lo:.2f}} to {{screen.basin2.frac_hi:.2f}}) | {{screen.basin2.mgli_median:.0f}} | {{screen.basin2.share_coord_approx:.0%}} |
| {{screen.basin3.name}} | {{screen.basin3.n_wells}} | {{screen.basin3.n_datasets}} | {{screen.basin3.median_li:.0f}} ({{screen.basin3.median_lo:.0f}} to {{screen.basin3.median_hi:.0f}}) | {{screen.basin3.frac_pass:.2f}} ({{screen.basin3.frac_lo:.2f}} to {{screen.basin3.frac_hi:.2f}}) | {{screen.basin3.mgli_median:.0f}} | {{screen.basin3.share_coord_approx:.0%}} |
| {{screen.basin4.name}} | {{screen.basin4.n_wells}} | {{screen.basin4.n_datasets}} | {{screen.basin4.median_li:.0f}} ({{screen.basin4.median_lo:.0f}} to {{screen.basin4.median_hi:.0f}}) | {{screen.basin4.frac_pass:.2f}} ({{screen.basin4.frac_lo:.2f}} to {{screen.basin4.frac_hi:.2f}}) | {{screen.basin4.mgli_median:.0f}} | {{screen.basin4.share_coord_approx:.0%}} |
| {{screen.basin5.name}} | {{screen.basin5.n_wells}} | {{screen.basin5.n_datasets}} | {{screen.basin5.median_li:.0f}} ({{screen.basin5.median_lo:.0f}} to {{screen.basin5.median_hi:.0f}}) | {{screen.basin5.frac_pass:.2f}} ({{screen.basin5.frac_lo:.2f}} to {{screen.basin5.frac_hi:.2f}}) | {{screen.basin5.mgli_median:.0f}} | {{screen.basin5.share_coord_approx:.0%}} |
| {{screen.basin6.name}} | {{screen.basin6.n_wells}} | {{screen.basin6.n_datasets}} | {{screen.basin6.median_li:.0f}} ({{screen.basin6.median_lo:.0f}} to {{screen.basin6.median_hi:.0f}}) | {{screen.basin6.frac_pass:.2f}} ({{screen.basin6.frac_lo:.2f}} to {{screen.basin6.frac_hi:.2f}}) | {{screen.basin6.mgli_median:.0f}} | {{screen.basin6.share_coord_approx:.0%}} |
| {{screen.basin7.name}} | {{screen.basin7.n_wells}} | {{screen.basin7.n_datasets}} | {{screen.basin7.median_li:.0f}} ({{screen.basin7.median_lo:.0f}} to {{screen.basin7.median_hi:.0f}}) | {{screen.basin7.frac_pass:.2f}} ({{screen.basin7.frac_lo:.2f}} to {{screen.basin7.frac_hi:.2f}}) | {{screen.basin7.mgli_median:.0f}} | {{screen.basin7.share_coord_approx:.0%}} |
| {{screen.basin8.name}} | {{screen.basin8.n_wells}} | {{screen.basin8.n_datasets}} | {{screen.basin8.median_li:.0f}} ({{screen.basin8.median_lo:.0f}} to {{screen.basin8.median_hi:.0f}}) | {{screen.basin8.frac_pass:.2f}} ({{screen.basin8.frac_lo:.2f}} to {{screen.basin8.frac_hi:.2f}}) | {{screen.basin8.mgli_median:.0f}} | {{screen.basin8.share_coord_approx:.0%}} |

The full tables are `tables/basin_primary.csv` ({{screen.n_basins_ranked}} ranked basins
plus the small groups in `tables/basin_small_groups.csv`) and `tables/formation_primary.csv`
({{screen.n_formations_ranked}} formations). The leader by median,
{{screen.basin1.name}}, rests on {{screen.basin1.n_wells}} wells from
{{screen.basin1.n_datasets}} dataset with {{screen.basin1.share_coord_approx:.0%}} approximate
coordinates and an interval from {{screen.basin1.median_lo:.0f}} to
{{screen.basin1.median_hi:.0f}} mg/L; it is a lead, not a resource. By screened fraction
the order is {{screen.pass1.name}} ({{screen.pass1.n_pass}} of {{screen.pass1.n_wells}},
{{screen.pass1.frac_lo:.2f}} to {{screen.pass1.frac_hi:.2f}}), {{screen.pass2.name}}
({{screen.pass2.n_pass}} of {{screen.pass2.n_wells}}, {{screen.pass2.frac_lo:.2f}} to
{{screen.pass2.frac_hi:.2f}}), {{screen.pass3.name}} ({{screen.pass3.n_pass}} of
{{screen.pass3.n_wells}}, {{screen.pass3.frac_lo:.2f}} to {{screen.pass3.frac_hi:.2f}}),
{{screen.pass4.name}} ({{screen.pass4.n_pass}} of {{screen.pass4.n_wells}}) and
{{screen.pass5.name}} ({{screen.pass5.n_pass}} of {{screen.pass5.n_wells}}); the last two
intervals include zero. Of the {{screen.n_ranked_pairs}} basin pairs,
{{screen.n_separable_pairs}} have non-overlapping median intervals.

Formations with the highest medians (at least {{screen.min_wells_formation}} wells):
{{screen.form1.name}} ({{screen.form1.n_wells}} wells, {{screen.form1.median_li:.0f}} mg/L,
{{screen.form1.median_lo:.0f}} to {{screen.form1.median_hi:.0f}}, screened fraction
{{screen.form1.frac_pass:.2f}}), {{screen.form2.name}} ({{screen.form2.n_wells}},
{{screen.form2.median_li:.0f}}, {{screen.form2.median_lo:.0f}} to {{screen.form2.median_hi:.0f}}),
{{screen.form3.name}} ({{screen.form3.n_wells}}, {{screen.form3.median_li:.0f}},
{{screen.form3.median_lo:.0f}} to {{screen.form3.median_hi:.0f}}), {{screen.form4.name}}
({{screen.form4.n_wells}}, {{screen.form4.median_li:.0f}}, {{screen.form4.median_lo:.0f}} to
{{screen.form4.median_hi:.0f}}, screened fraction {{screen.form4.frac_pass:.2f}}) and
{{screen.form5.name}} ({{screen.form5.n_wells}} wells in {{screen.form5.n_datasets}} datasets,
{{screen.form5.median_li:.0f}} mg/L, {{screen.form5.median_lo:.0f}} to
{{screen.form5.median_hi:.0f}}, screened fraction {{screen.form5.frac_pass:.2f}},
{{screen.form5.frac_lo:.2f}} to {{screen.form5.frac_hi:.2f}}). {{screen.form6.name}} has
{{screen.form6.n_wells}} wells at {{screen.form6.median_li:.0f}} mg/L
({{screen.form6.median_lo:.0f}} to {{screen.form6.median_hi:.0f}}).

![Mg/Li against Li](figures/fig3_mgli_vs_li.png)

## Result: how much of the ranking is the compilation

**The named lithium-focused datasets barely matter; dataset effects in general do.**
The four datasets the version history names ({{screen.adj.datasets}}) contribute
{{screen.adj.n_li_wells_removed}} of the {{screen.n_li_wells}} lithium wells
({{screen.adj.basins_touched}}). Removing them leaves the top five unchanged
({{screen.adj.top5_overlap}} of `5` in common) and reverses {{screen.adj.n_reversed_pairs}}
separable pairs: by the pre-registered test the ranking is **{{screen.adj.robust}}** to
that adjustment, and basins that moved: {{screen.adj.moved}}. The by-dataset view tells a
different story. Among the {{screen.ds.n_basins_two_datasets_ge5}} ranked basins with at
least two datasets of five or more wells, the ratio between the highest and lowest
dataset median within the same basin has a median of {{screen.ds.median_ratio:.1f}};
{{screen.ds.n_basins_ratio_ge2}} basins differ by a factor of `2` or more and
{{screen.ds.n_basins_ratio_ge5}} by `5` or more, up to {{screen.ds.max_ratio:.0f}} in
{{screen.ds.max_ratio_basin}} (`tables/basin_by_dataset.csv`). A basin's number depends on
which datasets happened to be compiled for it, even though the four datasets the USGS
flagged as lithium-motivated are too small to move anything.

**Charge-balance tolerance.** At tolerances `5`, `15` and none the lithium-well counts are
{{screen.cb.tol5.n_li_wells}}, {{screen.cb.tol15.n_li_wells}} and
{{screen.cb.none.n_li_wells}} (primary {{screen.cb.primary_n_li_wells}}); the top five
overlaps are {{screen.cb.tol5.top5_overlap}}, {{screen.cb.tol15.top5_overlap}} and
{{screen.cb.none.top5_overlap}} with {{screen.cb.tol5.n_reversed_pairs}},
{{screen.cb.tol15.n_reversed_pairs}} and {{screen.cb.none.n_reversed_pairs}} reversed
pairs: **{{screen.cb.robust}}**.

**Threshold grid.** Across floors of `50`, `100` and `200` mg/L, ceilings of `6`, `10` and `20` and a
brine-only variant, the number of passing wells runs from {{screen.grid.n_pass_min}} to
{{screen.grid.n_pass_max}} ({{screen.grid.share_pass_min:.1%}} to
{{screen.grid.share_pass_max:.1%}} of lithium wells); the loosest cell passes
{{screen.grid.loose_n_pass}}, the strictest {{screen.grid.strict_n_pass}}, and requiring
brine salinity at the primary thresholds passes {{screen.grid.brine_n_pass}}. The top `3`
basins by screened fraction take {{screen.grid.n_distinct_top3}} distinct forms across the
{{screen.grid.n_cells}} cells (`tables/threshold_grid.csv`).

**Missing is not random, and it is a dataset property.** {{miss.n_measured}} of
{{miss.n_rows}} included rows ({{miss.share_measured:.1%}}) have lithium. Rows with lithium
have a median TDS of {{miss.tds_median_measured:.0f}} mg/L against
{{miss.tds_median_not_measured:.0f}} without (standardized difference on the log scale
{{miss.smd_log_tds:.2f}}), a median depth of {{miss.depth_median_measured:.0f}} ft against
{{miss.depth_median_not_measured:.0f}} ({{miss.smd_log_depth:.2f}}), and come from the 1960s
far more often ({{miss.decade_top_measured_share:.0%}} of dated rows with lithium against
{{miss.decade_top_measured_share_not:.0%}} without). {{miss.datasets_none_measured}} of
{{miss.datasets_total}} datasets never report lithium and {{miss.datasets_all_measured}}
report it on every row; the largest dataset, USGSBREIT, reports it on
{{miss.usgsbreit_share_li:.1%}} of its {{miss.usgsbreit_rows}} rows. A logistic model of
"lithium present" on TDS, depth, decade, play type and basin has a cross-validated AUC of
{{miss.auc:.2f}} ({{miss.auc_min:.2f}} to {{miss.auc_max:.2f}} across folds), so by the
pre-registered rule: **{{miss.verdict}}**. The basin ranking describes the wells someone
chose to analyze for lithium, not the basins.

![Coverage](figures/fig1_coverage_basin_decade.png)

![Missingness](figures/fig4_missingness.png)

## Result: can lithium be predicted where it was not measured?

{{model.n_wells}} wells have lithium and the full feature set ({{model.n_features}}
features); the standard deviation of log10 Li, which is the error of a mean predictor, is
{{model.target_sd:.2f}}. {{model.n_datasets_heldout}} datasets and
{{model.n_basins_heldout}} basins are large enough to be held out.

![Three-protocol error](figures/fig5_prediction_error.png)

Gradient boosting, held-out RMSE of log10 Li (pooled; fold median; fold range):

| protocol | RMSE pooled | fold median | fold min to max | R-squared pooled | AUC at floor | precision at floor | recall |
|---|---|---|---|---|---|---|---|
| random by well | {{model.random.hgb.rmse_pooled:.3f}} | {{model.random.hgb.rmse_fold_median:.3f}} | {{model.random.hgb.rmse_fold_min:.3f}} to {{model.random.hgb.rmse_fold_max:.3f}} | {{model.random.hgb.r2_pooled:.2f}} | {{model.random.hgb.cls_auc:.2f}} | {{model.random.hgb.cls_precision:.2f}} | {{model.random.hgb.cls_recall:.2f}} |
| leave-one-dataset-out | {{model.lodo.hgb.rmse_pooled:.3f}} | {{model.lodo.hgb.rmse_fold_median:.3f}} | {{model.lodo.hgb.rmse_fold_min:.3f}} to {{model.lodo.hgb.rmse_fold_max:.3f}} | {{model.lodo.hgb.r2_pooled:.2f}} | {{model.lodo.hgb.cls_auc:.2f}} | {{model.lodo.hgb.cls_precision:.2f}} | {{model.lodo.hgb.cls_recall:.2f}} |
| leave-one-basin-out | {{model.lobo.hgb.rmse_pooled:.3f}} | {{model.lobo.hgb.rmse_fold_median:.3f}} | {{model.lobo.hgb.rmse_fold_min:.3f}} to {{model.lobo.hgb.rmse_fold_max:.3f}} | {{model.lobo.hgb.r2_pooled:.2f}} | {{model.lobo.hgb.cls_auc:.2f}} | {{model.lobo.hgb.cls_precision:.2f}} | {{model.lobo.hgb.cls_recall:.2f}} |

Ridge: RMSE {{model.random.ridge.rmse_pooled:.3f}} (random), {{model.lodo.ridge.rmse_pooled:.3f}}
(dataset), {{model.lobo.ridge.rmse_pooled:.3f}} (basin); R-squared {{model.random.ridge.r2_pooled:.2f}},
{{model.lodo.ridge.r2_pooled:.2f}}, {{model.lobo.ridge.r2_pooled:.2f}}. Its AUC at the floor is
{{model.random.ridge.cls_auc:.2f}} to {{model.lobo.ridge.cls_auc:.2f}} but it almost never
predicts a value above the floor (precision {{model.random.ridge.cls_precision:.2f}} random,
{{model.lodo.ridge.cls_precision:.2f}} dataset, {{model.lobo.ridge.cls_precision:.2f}} basin):
a shrunk linear fit ranks wells but does not call them. The random-fold result is stable
across repetitions ({{model.random.hgb.rmse_rep_min:.3f}} to {{model.random.hgb.rmse_rep_max:.3f}}).

**Reading it.** Holding out a dataset or a basin raises the boosted model's error by a
factor of {{model.rmse_ratio_lodo_random_hgb:.2f}} and {{model.rmse_ratio_lobo_random_hgb:.2f}},
and the spread across folds widens from {{model.random.hgb.rmse_fold_min:.2f}} to
{{model.random.hgb.rmse_fold_max:.2f}} (random) to {{model.lobo.hgb.rmse_fold_min:.2f}} to
{{model.lobo.hgb.rmse_fold_max:.2f}} (basins) and {{model.lodo.hgb.rmse_fold_min:.2f}} to
{{model.lodo.hgb.rmse_fold_max:.2f}} (datasets; worst {{model.lodo.hgb.worst_dataset}}).
Out of basin the pooled R-squared is still {{model.lobo.hgb.r2_pooled:.2f}} and the AUC
{{model.lobo.hgb.cls_auc:.2f}}, so the pre-registered rule returns
**"{{model.verdict}}"**. That verdict needs its caveat stated plainly: for the screening
use, precision at the floor falls from {{model.random.hgb.cls_precision:.2f}} within basin to
{{model.lobo.hgb.cls_precision:.2f}} out of basin and recall from
{{model.random.hgb.cls_recall:.2f}} to {{model.lobo.hgb.cls_recall:.2f}}; only
{{model.lobo.hgb.n_basins_r2_ge_0_3}} of {{model.n_basins_heldout}} held-out basins reach an
R-squared of `0.30` on their own and {{model.lobo.hgb.n_basins_r2_positive}} are positive at
all; the median absolute basin-level bias is {{model.lobo.hgb.bias_abs_median:.2f}} log10
units and the worst is {{model.lobo.hgb.bias_abs_max:.2f}} ({{model.lobo.hgb.bias_max_basin}},
the basin with the highest median, R-squared {{model.lobo.hgb.worst_basin_r2:.2f}} when held
out). The pooled R-squared survives because the model learns the large between-basin
contrast in salinity and composition, not because it ranks wells within a new basin.
For someone deciding whether to sample a new field, the model says which basins are
brine-rich; it does not say which wells in an unsampled basin will clear the floor.

**Calibration.** The screening probability is reasonably calibrated within basin
(largest decile gap {{model.random.hgb.calib_max_gap:.2f}}) and across datasets
({{model.lodo.hgb.calib_max_gap:.2f}}) but not across basins (largest gap
{{model.lobo.hgb.calib_max_gap:.2f}}): wells given a high probability of clearing the floor
in a held-out basin mostly did not. Brier scores {{model.random.hgb.cls_brier:.3f}},
{{model.lodo.hgb.cls_brier:.3f}}, {{model.lobo.hgb.cls_brier:.3f}}.

![Calibration](figures/fig6_calibration.png)

**Positive control.** The same pipeline with log10 TDS as the target and TDS removed from
the features, on {{control.n_wells}} wells: boosted R-squared {{control.random.hgb.r2_pooled:.2f}}
random, {{control.lodo.hgb.r2_pooled:.2f}} leave-one-dataset-out,
{{control.lobo.hgb.r2_pooled:.2f}} leave-one-basin-out (RMSE
{{control.random.hgb.rmse_pooled:.2f}}, {{control.lodo.hgb.rmse_pooled:.2f}},
{{control.lobo.hgb.rmse_pooled:.2f}} against a mean-predictor error of
{{control.target_sd:.2f}}). The pre-registered pass criterion
(random R-squared of at least `0.80`) **{{control.passes}}**: the pipeline learns what is
learnable, and the lithium result is a property of lithium, not of the code.

![Map](figures/fig7_map.png)

## Caveats next to the claims they affect

- The ranking is of wells that someone chose to analyze for lithium ({{miss.share_measured:.1%}}
  of rows; AUC {{miss.auc:.2f}} for predicting that choice). It is not a basin property.
- Non-detects are invisible in v3.0; a dataset that analyzed for lithium and reported
  nothing below its limit looks identical to one that never analyzed. Medians are
  therefore medians of reported values and could be biased upward in datasets with high
  limits.
- {{screen.basin1.name}}: {{screen.basin1.n_wells}} wells, one dataset, every coordinate a
  centroid; the interval is {{screen.basin1.median_lo:.0f}} to {{screen.basin1.median_hi:.0f}} mg/L.
- {{prepare.wells.li_wells_key_row}} lithium rows could not be grouped into wells and are
  counted as wells, which can inflate counts in the Appalachian and Michigan tables.
- {{prepare.cb.balanced_by_construction_li_rows}} lithium rows have a charge balance that
  cannot fail; the charge-balance sensitivity is reassuring only about the rows it can see.
- Specific gravity was estimated for {{prepare.wells.li_wells_sg_estimated}} lithium wells
  reported in ppm; the conversion error is a few percent and does not move a log10 ranking.
- The same physical well in two datasets is two units; the leave-one-dataset-out protocol
  shows what that costs (worst held-out dataset {{model.lodo.hgb.worst_dataset}},
  RMSE {{model.lodo.hgb.worst_dataset_rmse:.2f}}).
- No spatial claim is made below basin scale; {{prepare.wells.li_wells_share_coord_approx:.0%}}
  of lithium wells have centroid coordinates and the map has no basemap.
- Thresholds are literature screening values, not an economic assessment of any site.

## Exploratory findings (not pre-registered)

None beyond what is marked above. Post-freeze decisions (output directories, a key-format
bug fixed before any result was read, single-threaded fits in parallel processes, the
control as its own step) are logged in `docs/decisions.md` and changed no model, grid or
protocol.

## Verification

{{tests.n_passed}} of {{tests.n_tests}} tests pass ({{tests.n_failed}} failures). `cairn verify`
re-executes every step from a clean ledger and compares every value. cairn commit
`{{env.cairn_commit}}`.

## Decision log

See `docs/decisions.md`.
