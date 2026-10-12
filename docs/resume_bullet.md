# Resume bullet (measured results only; rendered from the ledger)

- Built a pre-registered screening and prediction study of lithium in U.S. produced water
  on the USGS National Produced Waters Geochemical Database v3.0 (113135
  samples, 63 source datasets, 4141 lithium wells):
  literature-sourced thresholds, well-level deduplication, dataset-clustered bootstrap
  intervals, and a quantified missingness audit (lithium present on 5.5%
  of rows, predictable with AUC 0.75), run under a verification harness
  (13 tests, clean-rerun check, every reported number traced to a ledger).
- Showed that 100 of 4141 wells pass the screen, that
  within-basin dataset medians differ by up to 59-fold, and that a
  gradient boosted model of log lithium from major-ion chemistry degrades from RMSE
  0.37 (random folds by well) to 0.51
  when whole basins are held out, with precision at the screening floor falling from
  0.78 to 0.28.
