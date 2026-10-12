# Resume bullet (measured results only; rendered from the ledger)

- Built a pre-registered screening and prediction study of lithium in U.S. produced water
  on the USGS National Produced Waters Geochemical Database v3.0 ({{manifest.extract_rows}}
  samples, {{profile.n_datasets}} source datasets, {{prepare.wells.n_wells_li}} lithium wells):
  literature-sourced thresholds, well-level deduplication, dataset-clustered bootstrap
  intervals, and a quantified missingness audit (lithium present on {{miss.share_measured:.1%}}
  of rows, predictable with AUC {{miss.auc:.2f}}), run under a verification harness
  ({{tests.n_tests}} tests, clean-rerun check, every reported number traced to a ledger).
- Showed that {{screen.n_pass_primary}} of {{screen.n_li_wells}} wells pass the screen, that
  within-basin dataset medians differ by up to {{screen.ds.max_ratio:.0f}}-fold, and that a
  gradient boosted model of log lithium from major-ion chemistry degrades from RMSE
  {{model.random.hgb.rmse_pooled:.2f}} (random folds by well) to {{model.lobo.hgb.rmse_pooled:.2f}}
  when whole basins are held out, with precision at the screening floor falling from
  {{model.random.hgb.cls_precision:.2f}} to {{model.lobo.hgb.cls_precision:.2f}}.
