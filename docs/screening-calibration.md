# Exploratory screening coverage and domain calibration

The frozen screen divides known passes by all lithium wells: missing magnesium cannot establish a pass. The supplementary table distinguishes **pass**, **fail**, and **unknown**. A well below the Li floor fails regardless of Mg; only a well above the floor with missing Mg is unknown. Lower and upper fractions set every unknown to fail/pass respectively. These are identification bounds, not confidence intervals. The evaluable fraction omits unknowns and remains conditional on screening information; it must not replace the baseline fraction.

```sh
uv run python scripts/10_prepare.py
uv run python scripts/40_model.py  # remote only, if recorded OOF is absent
uv run python exploratory/screening_calibration.py
```

`reports/exploratory/screening_calibration/` contains basin coverage, rankings of lower/upper bounds, and held-out gradient-boosted reliability tables by basin and source dataset. Predictions and sigma come from the original nested held-out evaluation; no calibration is fitted to test labels. Calibration concerns lithium above the 100 mg/L floor only; it does not predict the joint magnesium-to-lithium screen. Fixed probability bins show counts, observed frequencies and Wilson intervals. These intervals quantify bin support conditional on predictions, not model/transport uncertainty; a sparse interval is no proof of calibrated prediction. Gaussian probabilities remain a modeling assumption. The source revision and coverage totals are recorded separately; baseline results, ranking rule and preregistration are unchanged.
