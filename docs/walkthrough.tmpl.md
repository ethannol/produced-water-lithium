# Five-minute walkthrough

_Rendered from the ledger by `scripts/60_docs.py`; do not edit `walkthrough.md`._

**The question (30 s).** Produced water from oil and gas wells sometimes carries lithium.
The USGS compiled {{manifest.extract_rows}} analyses from {{profile.n_datasets}} sources into
one database. Where is the lithium, and how much of that map is really a map of who
sampled what, when, and which papers got compiled?

**The first trap (30 s).** Before any analysis I checked how "below detection" is stored.
It is not. {{nondetect.Li.nonempty}} lithium values, {{nondetect.Li.zero}} zeros,
{{nondetect.Li.negative}} negatives, no flags, {{nondetect.dictionary_detection_fields}}
detection fields in the dictionary. A non-detect is an empty cell, the same as "never
analyzed". So every median in this study is a median of reported values. That is a
limitation I can state, not one I can fix.

**The method (45 s).** I pre-registered and froze the plan before computing anything:
produced-water rows only, U.S. only, charge balance within {{prepare.cb.tolerance:g}} percent,
one unit per well within its source dataset, a screen of Li at or above
{{screen.floor_mg_l:g}} mg/L with Mg/Li at or below {{screen.ceiling_mg_li:g}} from published
screening papers, and bootstrap intervals that resample wells and cluster by dataset.
{{prepare.wells.li_rows_in}} lithium rows become {{prepare.wells.n_wells_li}} wells.

**The ranking (60 s).** {{screen.n_pass_primary}} of {{screen.n_li_wells}} wells pass.
By median lithium the top basin is {{screen.basin1.name}} at {{screen.basin1.median_li:.0f}} mg/L,
but that is {{screen.basin1.n_wells}} wells from one dataset, every location a centroid,
with an interval from {{screen.basin1.median_lo:.0f}} to {{screen.basin1.median_hi:.0f}}.
{{screen.basin2.name}} ({{screen.basin2.n_wells}} wells, {{screen.basin2.n_datasets}} datasets)
sits at {{screen.basin2.median_li:.0f}} mg/L and {{screen.basin3.name}}
({{screen.basin3.n_wells}} wells, {{screen.basin3.n_datasets}} datasets) at
{{screen.basin3.median_li:.0f}}. Only {{screen.n_basins_frac_interval_excludes_zero}} basins
have a screened fraction whose interval excludes zero. The USGS named four datasets it
added because they were lithium-rich; they hold {{screen.adj.n_li_wells_removed}} wells and
removing them changes nothing. The real dataset effect is elsewhere: where a basin has
several sources, their medians differ by a median factor of {{screen.ds.median_ratio:.1f}}
and up to {{screen.ds.max_ratio:.0f}}. And lithium was measured on {{miss.share_measured:.1%}}
of rows, {{miss.decade_top_measured_share:.0%}} of them from the 1960s; a model guesses
which rows have it with AUC {{miss.auc:.2f}}. So the ranking is of the wells someone chose to
analyze.

**The model (60 s).** Can chemistry stand in for a lithium analysis? Gradient boosting on
major-ion log-ratios, TDS, depth, play type and era. Random folds by well: RMSE
{{model.random.hgb.rmse_pooled:.2f}} in log10 units, R-squared {{model.random.hgb.r2_pooled:.2f}}.
Leave a whole dataset out: {{model.lodo.hgb.rmse_pooled:.2f}}. Leave a whole basin out:
{{model.lobo.hgb.rmse_pooled:.2f}}, with folds from {{model.lobo.hgb.rmse_fold_min:.2f}} to
{{model.lobo.hgb.rmse_fold_max:.2f}}. The pooled out-of-basin R-squared is still
{{model.lobo.hgb.r2_pooled:.2f}}, which passes the rule I froze, but precision at the floor
drops from {{model.random.hgb.cls_precision:.2f}} to {{model.lobo.hgb.cls_precision:.2f}} and
only {{model.lobo.hgb.n_basins_r2_ge_0_3}} of {{model.n_basins_heldout}} held-out basins are
predicted usefully on their own. The model knows which basins are brine-rich; it does not
know which wells in a new basin will clear the floor. The positive control, TDS from the
same features, scores {{control.random.hgb.r2_pooled:.2f}}, so the pipeline is fine.

**The sentence to leave with (15 s).** The public database says lithium-rich produced
water exists in a handful of basins, but the number it gives any basin is mostly a number
about which datasets were compiled and which wells were analyzed; a new field needs its
own lithium analyses, and chemistry alone will not substitute for them across basins.
Every number here is pre-registered, recorded in a ledger, and re-executed by the harness.
