Produced water is the salty water that comes up a well along with oil and gas, and in some basins it carries lithium. Whether it is worth recovering is a live question, because extraction methods that work on brine have made oilfield water a candidate feedstock, and the water is already being lifted to the surface and disposed of. I wanted to know which U.S. basins have produced water that clears a sensible screening rule, and how far the public evidence for that can be trusted.

The place to start is the USGS National Produced Waters Geochemical Database, version 3.0 (December 2023). It is the one public compilation that puts lithium beside major ions, depth, formation and location nationwide, with {{profile.rows:,}} analyses from {{profile.n_datasets}} source datasets across {{profile.n_basins}} basins. Anyone asking where oilfield lithium is will reach for it first, so its habits need understanding before its numbers are quoted.

## Reading the version history before the data

Before I opened the data I read the metadata, the data dictionary and the version history, because a compiled database is a record of what other people chose to measure and what the compilers chose to include. The entry for version 3.0 says the compilers focused on high-lithium datasets and names four of them. That is sensible for a compiler and awkward for an analyst, because a database enriched on purpose with lithium-rich sources will show lithium wherever the compilers looked. This is compilation bias, and it set up the first thing to test, whether the basin ranking survives removing those four datasets. I wrote that test down before computing any ranking.

## Finding that a non-detect cannot be written down

The next thing I wanted to know was how the database records a result below the laboratory's detection limit, a non-detect, because every median and screening count depends on it. I expected a qualifier field or a less-than prefix, as most water-quality databases have.

I inspected every cell of the lithium column and the dictionary. The lithium column has {{nondetect.Li.nonempty:,}} non-empty cells, {{nondetect.Li.zero}} zeros, {{nondetect.Li.negative}} negative values and {{nondetect.Li.lt_prefixed}} less-than prefixes, and the dictionary has {{nondetect.dictionary_detection_fields}} detection-limit fields among its {{nondetect.dictionary_fields}}. The metadata says earlier versions used negative codes for "none detected", but none survive.

So a lithium result below detection is an empty cell, and an empty cell is also what "never analyzed" looks like. There is no way to tell them apart and nothing to substitute. I recorded that as a finding and fixed its consequences in the plan: every non-empty lithium value is a detected measurement, "lithium measured" means the cell is non-empty, and no imputation is made. Every median that follows is a median of reported values, which could sit above the truth in datasets with high detection limits. It is a limitation I can state, not one I can fix.

## Choosing the thresholds and freezing the plan

A screening rule needs a lithium floor and a magnesium-to-lithium ceiling, because magnesium competes with lithium in extraction and a high ratio makes recovery costlier. I wanted both from the literature rather than from the data, so that the rule could not drift toward whatever looked interesting.

I took the floor of 100 mg/L from Knierim and others, who use it as the concentration often cited as the minimum for commercial extraction, and the Mg/Li mass-ratio ceiling of 10 from Dugamin and others, who find extraction more favourable below it; Mackey and others treat ratios above six as high. None gives a cutoff on total dissolved solids, so salinity is reported, not screened on. A sensitivity grid of looser and tighter floors and ceilings was fixed at the same time.

With thresholds, population rules, unit of analysis and decision rules written down, I froze the plan under the harness before any ranking or model fit. Three rules matter for what follows. The ranking is robust to compilation bias if removing the four named datasets keeps at least four of the top five basins and reverses no pair of basins whose intervals do not overlap. Measurement is not missing at random if a classifier separates measured from unmeasured rows with an AUC of at least 0.70. Prediction is useful out of basin if the leave-one-basin-out R-squared is at least 0.30 and the AUC at the screening floor at least 0.75. Anything outside the plan is exploratory, and I say so where it appears.

## Deciding what one unit is

Before counting anything I had to decide what one observation is, because the answer changes every interval. A row of the database is one sample, and some datasets hold flowback time series or repeat samples from one well, so counting rows would let one heavily sampled well stand in for dozens.

The unit of analysis is the well within its source dataset. I collapsed rows to wells by API number, otherwise well name, otherwise exact coordinates with depth, and otherwise the row itself, and took the median of each chemistry value within a well. After the pre-registered exclusions and a charge-balance tolerance of {{prepare.cb.tolerance:.0f}} percent, {{prepare.wells.rows_in:,}} rows become {{prepare.wells.n_wells:,}} wells, and {{prepare.wells.li_rows_in:,}} lithium rows become {{prepare.wells.n_wells_li:,}} lithium wells.

The same choice governs the uncertainty. Wells from one source dataset share a laboratory, a sampling campaign and a reporting convention, so they are not independent. The bootstrap, which estimates uncertainty by resampling the data and recomputing the statistic, therefore resamples wells clustered by dataset, drawing datasets with replacement first and then wells within each drawn dataset, {{screen.n_boot:,}} times. A basin with one dataset cannot show between-dataset variation at all, so I report the dataset count beside every basin.

## The ranking, with the intervals shown

Now I could ask the descriptive question. Of {{screen.n_li_wells:,}} lithium wells, {{screen.n_above_floor}} ({{screen.share_above_floor:.1%}}) reach the floor and {{screen.n_pass_primary}} ({{screen.share_pass_primary:.1%}}) also meet the ceiling. The median lithium well is {{screen.li_median_all_wells}} mg/L.

![Basins with at least twenty lithium wells, ordered by median well lithium with dataset-clustered bootstrap intervals, and the fraction of wells passing the screen.](reports/figures/fig2_basin_ranking.png)

The left panel orders basins by median lithium and the right panel gives the screened fraction. {{screen.n_basins_ranked}} of {{screen.n_basins_with_li}} basins have enough wells to be ranked, {{screen.n_basins_any_pass}} contain at least one passing well, and only {{screen.n_basins_frac_interval_excludes_zero}} have a screened fraction whose interval excludes zero. Those three are {{screen.pass1.name}}, where {{screen.pass1.n_pass}} of {{screen.pass1.n_wells}} wells pass, {{screen.pass2.name}} ({{screen.pass2.n_pass}} of {{screen.pass2.n_wells}}) and {{screen.pass3.name}} ({{screen.pass3.n_pass}} of {{screen.pass3.n_wells}}). Williston and Gulf Coast have passing wells, but their intervals reach zero, which by the rule I froze is no evidence of screen-passing wells.

The leader needs to be read carefully. {{screen.basin1.name}} has a median of {{screen.basin1.median_li:.0f}} mg/L and a screened fraction of {{screen.basin1.frac_pass:.0%}}, but that rests on {{screen.basin1.n_wells}} wells from {{screen.basin1.n_datasets}} dataset, with {{screen.basin1.share_coord_approx:.0%}} of the locations recorded as centroid coordinates, the centre of a county or field rather than the well, and a median interval from {{screen.basin1.median_lo:.0f}} to {{screen.basin1.median_hi:.0f}} mg/L. It is a lead, not a viability claim. {{screen.basin2.name}} follows at {{screen.basin2.median_li:.0f}} mg/L on {{screen.basin2.n_wells}} wells from {{screen.basin2.n_datasets}} datasets, and {{screen.basin3.name}} at {{screen.basin3.median_li:.0f}} mg/L on {{screen.basin3.n_wells}} wells from {{screen.basin3.n_datasets}} datasets, with narrower intervals.

![Magnesium-to-lithium ratio against lithium for every well, with the three passing basins coloured and the screening box shaded.](reports/figures/fig3_mgli_vs_li.png)

The scatter shows why the ceiling matters. Mg/Li falls as lithium rises, but a band of Appalachian and Arkla wells sits just above the floor with ratios in the tens, and those are the {{screen.n_above_floor_high_mgli}} that the primary rule rejects. The vertical stripes at round values are reporting precision, since {{nondetect.li_share_integer:.0%}} of lithium values are whole numbers. This answered the descriptive question and raised the one I had set up at the start, how much of the picture is the compilation.

## Removing the lithium-focused datasets, and what moved instead

The pre-registered test removes the four datasets the version history names and recomputes everything. I expected them to matter.

They barely exist in the screening population. The four hold {{screen.adj.n_li_wells_removed}} of the {{screen.n_li_wells:,}} lithium wells, in {{screen.adj.basins_touched}}. Removing them keeps {{screen.adj.top5_overlap}} of the top five basins and reverses {{screen.adj.n_reversed_pairs}} separable pairs. By the rule I froze, the ranking is robust to the named compilation bias, and it is equally unmoved by a tighter or looser charge-balance tolerance.

That could have closed the question, but the pre-registration also asked for a by-dataset view within each basin, and it told a different story. Among the {{screen.ds.n_basins_two_datasets_ge5}} ranked basins with at least two datasets of five or more wells, the ratio between the highest and lowest dataset median within the same basin has a median of {{screen.ds.median_ratio:.1f}}, and the worst, {{screen.ds.max_ratio_basin}}, differs by a factor of {{screen.ds.max_ratio:.0f}}. The compilers' four additions are too small to move anything, but which datasets happened to be compiled for a basin sets its number all the same. The threshold grid says the same from another side: across its {{screen.grid.n_cells}} cells the top three basins take {{screen.grid.n_distinct_top3}} distinct forms. So the ranking is of the wells someone chose to analyze for lithium, and that raised the next question, whether the choice was anything like random.

## Who measured lithium, and when

The missingness audit compares included rows that have a lithium value with rows that do not, on salinity, depth, sampling decade, play type, basin and dataset. If measurement had been representative, the two groups would look alike.

![Rows with and without lithium measured, compared on total dissolved solids, depth and sampling decade.](reports/figures/fig4_missingness.png)

Lithium is on {{miss.share_measured:.1%}} of included rows. The measured rows are a little saltier and a little deeper, and neither difference reaches the bar I had set. The decade panel is where the groups part: {{miss.decade_top_measured_share:.0%}} of dated rows with lithium are from the 1960s against {{miss.decade_top_measured_share_not:.0%}} of rows without. Measurement is also a dataset property, since {{miss.datasets_none_measured}} of {{miss.datasets_total}} datasets never report lithium and {{miss.datasets_all_measured}} report it on every row.

The pre-registered test is a cross-validated logistic regression, a model that gives the probability of a yes-or-no outcome from a weighted sum of its inputs, predicting "lithium present" from salinity, depth, decade, play type and basin. Its AUC, the chance that it ranks a random measured row above a random unmeasured one, is {{miss.auc:.2f}}, above the 0.70 bar, so the verdict is that missing is not random. The ranking describes wells whose selection is predictable from when and by whom they were sampled, not basins. That is the reason to try prediction: if the chemistry measured on almost every row could stand in for a lithium analysis, the gaps would matter less.

## Predicting lithium where it was not measured

The predictive question is whether log10 lithium can be predicted from major-ion chemistry, salinity, depth and play type, and the whole point lies in how the evaluation is split. Random folds, which shuffle wells into held-out subsets, say how well the model does on wells like the ones it saw. Holding out a whole source dataset asks whether it learned chemistry or a laboratory's habits. Holding out a whole basin, leave-one-group-out cross-validation with the basin as the group, asks what the model says about a basin nobody has sampled for lithium, which is what a geologist actually wants to know.

I fitted two models on the {{model.n_wells:,}} wells with lithium and the full feature set: ridge regression, a linear fit with its coefficients shrunk toward zero, and gradient boosting, a sum of many small decision trees each fitted to the errors of the last. The features are centred log-ratios of the major ions, which remove the closure of compositional data while log10 total dissolved solids carries the scale, plus log10 depth, play type and era. Tuning happens inside each training fold, grouped the same way as the outer split. The protocols hold out random wells, {{model.n_datasets_heldout}} datasets in turn, and {{model.n_basins_heldout}} basins in turn, and a predictor that always returns the mean has an error of {{model.target_sd:.2f}} log10 units.

![Held-out RMSE of log10 lithium for every fold under the three protocols, beside the positive control predicting total dissolved solids.](reports/figures/fig5_prediction_error.png)

Each dot in the left panel is one held-out fold. Under random folds the boosted model's pooled RMSE, the typical size of its errors, is {{model.random.hgb.rmse_pooled:.2f}} log10 units, with folds from {{model.random.hgb.rmse_fold_min:.2f}} to {{model.random.hgb.rmse_fold_max:.2f}} and an R-squared of {{model.random.hgb.r2_pooled:.2f}}. Hold out datasets and the pooled error rises to {{model.lodo.hgb.rmse_pooled:.2f}}; hold out basins and it is {{model.lobo.hgb.rmse_pooled:.2f}} with folds from {{model.lobo.hgb.rmse_fold_min:.2f}} to {{model.lobo.hgb.rmse_fold_max:.2f}}. The pooled error grows by a factor of {{model.rmse_ratio_lobo_random_hgb:.2f}}, but the spread is the real message: several held-out groups sit above the mean predictor, and the worst dataset, {{model.lodo.hgb.worst_dataset}}, is predicted worse than the average. Ridge is close on RMSE but almost never calls a well above the floor.

The right panel is the positive control, run so that a weak lithium result could be read as a property of lithium and not of the code. The same pipeline predicting log10 total dissolved solids, with salinity removed from the features, reaches an R-squared of {{control.random.hgb.r2_pooled:.2f}} under random folds and {{control.lobo.hgb.r2_pooled:.2f}} out of basin, above the bar I had set for it. The pipeline learns what is learnable.

## Reading the usefulness rule honestly

Now the pre-registered rule. Out of basin the pooled R-squared is {{model.lobo.hgb.r2_pooled:.2f}} and the AUC at the floor is {{model.lobo.hgb.cls_auc:.2f}}, both above the thresholds I wrote down, so the verdict the plan returns is "useful out of basin". I report that verdict as the frozen result, and then I have to say why I think the rule was too loose.

A pooled R-squared across held-out basins rewards a model for knowing which basins are saltier and more lithium-rich than others. It does not ask whether the model ranks wells within a basin it has never seen. Only {{model.lobo.hgb.n_basins_r2_ge_0_3}} of {{model.n_basins_heldout}} held-out basins reach an R-squared of 0.30 on their own, and the worst basin bias, {{model.lobo.hgb.bias_abs_max:.2f}} log10 units, is in {{model.lobo.hgb.bias_max_basin}}, the basin at the top of the ranking. For screening, precision at the floor, the share of wells the model flags that really clear it, falls from {{model.random.hgb.cls_precision:.2f}} under random folds to {{model.lobo.hgb.cls_precision:.2f}} out of basin, and recall from {{model.random.hgb.cls_recall:.2f}} to {{model.lobo.hgb.cls_recall:.2f}}.

![Reliability of the boosted model's probability of clearing the floor, by predicted-probability bin, under the three protocols.](reports/figures/fig6_calibration.png)

Calibration tells the same story. Within basin and across datasets the predicted probability of clearing the floor tracks the observed share reasonably, with largest bin gaps of {{model.random.hgb.calib_max_gap:.2f}} and {{model.lodo.hgb.calib_max_gap:.2f}}. Across basins the curve bends over, wells given a high probability in a held-out basin mostly did not clear the floor, and the largest gap is {{model.lobo.hgb.calib_max_gap:.2f}}. The model knows which basins are brine-rich. It does not know which wells in a new basin will clear the floor, and a pass on the pooled rule is not a licence to screen an unsampled field with it. Had I written the rule again I would have required a per-basin criterion, and I say so rather than quietly changing the rule after the fact.

## An exploratory look at coverage and calibration

This part is exploratory. I decided to do it after seeing the primary results, and it changes no frozen number.

Two loose ends bothered me. The frozen screen divides passes by all lithium wells, so a well above the floor with no magnesium value cannot pass, and I wanted to know how many wells that affected. {{screen.n_pass_primary}} wells pass, {{screen_coverage.n_fail:,}} fail and {{screen_coverage.n_unknown}} is unknown, so bounding the unknown as fail or as pass moves the overall fraction only from {{screen_coverage.fraction_lower:.3%}} to {{screen_coverage.fraction_upper:.3%}}. Missing magnesium does not matter in this snapshot.

The second was where the calibration failure was concentrated. I binned the existing out-of-fold predictions by held-out basin and dataset, with Wilson intervals, which are confidence intervals for a proportion that behave well at small counts, and fitted nothing to the held-out labels. The largest supported gap is in {{domain_calibration.worst_lobo.domain}}, where the mean predicted probability of clearing the floor is {{domain_calibration.worst_lobo.predicted:.1%}} against an observed {{domain_calibration.worst_lobo.observed:.1%}} on {{domain_calibration.worst_lobo.n}} wells, with a Wilson interval from {{domain_calibration.worst_lobo.lo:.1%}} to {{domain_calibration.worst_lobo.hi:.1%}}. A model trained on every other basin gives the top-ranked basin almost no chance of clearing the floor. These are diagnostics of bin support, not a calibration test, and they concern the lithium floor alone rather than the joint screen.

## What I concluded

The public database says that lithium-rich produced water exists and that it is concentrated in a handful of basins, but the number it gives any basin is mostly a number about which datasets were compiled for it and which wells someone chose to analyze. The compilers' deliberate additions are not the problem; the ordinary disagreement between source datasets is. A new field needs its own lithium analyses, and major-ion chemistry will not substitute for them across basins.

## What I would not claim

No resource estimate and no economic conclusion follow from a literature screening rule. I make no claim about any company, any site, or any location below basin scale, since {{prepare.wells.li_wells_share_coord_approx:.0%}} of lithium wells carry centroid coordinates. {{screen.basin1.name}} is a lead from one dataset, not a viable basin. No non-detect was handled, because the database cannot represent one. And the pooled "useful out of basin" verdict stands as the pre-registered result while meaning less than its name suggests.

## What I would do next with another week

I would go to the source publications behind the datasets that disagree most within a basin and recover their detection limits and methods, since the empty cells are the largest unknown in the study. I would rewrite the predictive rule around per-basin performance and pre-register it before refitting anything. And I would test whether the within-basin disagreement is chemistry or laboratory by finding the physical wells that appear in two datasets, which the leave-one-dataset-out protocol only approximates.
