# Recorded screening coverage and held-domain calibration

Of 4,141 lithium wells, 100 pass, 4,040 fail and 1 is unknown for the joint screen. Treating every unknown as fail/pass bounds the overall fraction at 2.415% to 2.439%.

| Basin with unknown screening status | Lithium wells | Unknown | Lower fraction | Upper fraction |
| --- | --- | --- | --- | --- |
| Greater Green River | 313 | 1 | 0.319% | 0.639% |

Missing magnesium changes the screen little in this snapshot; missingness auditing remains necessary because a future snapshot could differ. The baseline screen denominator is unchanged.

## Held-domain probability diagnostics

These probabilities concern lithium above the floor alone, not the joint Mg/Li screen. The following are the largest absolute observed-minus-predicted gaps among bins with at least 20 wells (an exploratory support filter); extremes are diagnostics, not a formal calibration test.

| Holdout | Domain | Bin support | Mean prediction | Observed fraction | Wilson interval |
| --- | --- | --- | --- | --- | --- |
| lobo | Amarillo Arch | 27 | 3.1% | 59.3% | 40.7% to 75.5% |
| lobo | Arkla | 30 | 48.7% | 100.0% | 88.6% to 100.0% |
| lobo | Gulf Coast | 26 | 69.6% | 19.2% | 8.5% to 37.9% |
| lodo | MISSISSIPPI | 20 | 49.7% | 0.0% | 0.0% to 16.1% |
| lodo | OHBRINE | 20 | 43.3% | 75.0% | 53.1% to 88.8% |
| lodo | MICHIGAN | 58 | 30.5% | 0.0% | 0.0% to 6.2% |

Domain-level gaps warn against treating Gaussian probabilities as reliably transported screening confidence. Intervals describe bin support conditional on recorded predictions; they omit model and transport uncertainty. No held-out labels were used to recalibrate the model.

Recorded source `17b278482619837debceb3a1429bc069dc184885`. [Methods](screening-calibration.md), [basin coverage](../reports/exploratory/screening_calibration/screening_coverage.csv), [basin bins](../reports/exploratory/screening_calibration/calibration_lobo_by_domain.csv), [dataset bins](../reports/exploratory/screening_calibration/calibration_lodo_by_domain.csv).
