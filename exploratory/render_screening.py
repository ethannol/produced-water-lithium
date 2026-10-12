"""Render recorded coverage/calibration diagnostics; no model fits."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT / "reports/exploratory/screening_calibration"
    measured = json.loads((out / "results.json").read_text())
    coverage = pd.read_csv(out / "screening_coverage.csv")
    summary = dict(measured)
    summary["fraction_lower"] = measured["n_pass"] / measured["n_li_wells"]
    summary["fraction_upper"] = (measured["n_pass"] + measured["n_unknown"]) / measured["n_li_wells"]
    lines = ["# Recorded screening coverage and held-domain calibration", "",
             f"Of {measured['n_li_wells']:,} lithium wells, {measured['n_pass']:,} pass, "
             f"{measured['n_fail']:,} fail and {measured['n_unknown']:,} is unknown for the joint screen. "
             f"Treating every unknown as fail/pass bounds the overall fraction at "
             f"{summary['fraction_lower']:.3%} to {summary['fraction_upper']:.3%}.", "",
             "| Basin with unknown screening status | Lithium wells | Unknown | Lower fraction | Upper fraction |",
             "| --- | --- | --- | --- | --- |"]
    for _, row in coverage.loc[coverage.n_unknown > 0].iterrows():
        lines.append(f"| {row.BASIN} | {row.n_li_wells} | {row.n_unknown} | "
                     f"{row.fraction_lower:.3%} | {row.fraction_upper:.3%} |")
    lines += ["", "Missing magnesium changes the screen little in this snapshot; missingness auditing remains "
              "necessary because a future snapshot could differ. The baseline screen denominator is unchanged.",
              "", "## Held-domain probability diagnostics", "",
              "These probabilities concern lithium above the floor alone, not the joint Mg/Li screen. "
              "The following are the largest absolute observed-minus-predicted gaps among bins with at least "
              "20 wells (an exploratory support filter); extremes are diagnostics, not a formal calibration test.",
              "", "| Holdout | Domain | Bin support | Mean prediction | Observed fraction | Wilson interval |",
              "| --- | --- | --- | --- | --- | --- |"]
    for proto in ["lobo", "lodo"]:
        bins = pd.read_csv(out / f"calibration_{proto}_by_domain.csv")
        bins["gap"] = (bins.observed - bins.mean_probability).abs()
        eligible = bins.loc[bins.n >= 20].sort_values("gap", ascending=False)
        worst = eligible.iloc[0]
        summary[f"worst_{proto}"] = dict(domain=worst.domain, n=int(worst.n),
                                         predicted=float(worst.mean_probability), observed=float(worst.observed),
                                         lo=float(worst.observed_lo), hi=float(worst.observed_hi))
        for _, row in eligible.head(3).iterrows():
            lines.append(f"| {proto} | {row.domain} | {row.n} | {row.mean_probability:.1%} | "
                         f"{row.observed:.1%} | {row.observed_lo:.1%} to {row.observed_hi:.1%} |")
    lines += ["", "Domain-level gaps warn against treating Gaussian probabilities as reliably transported "
              "screening confidence. Intervals describe bin support conditional on recorded predictions; "
              "they omit model and transport uncertainty. No held-out labels were used to recalibrate the model.", "",
              f"Recorded source `{measured['source_revision']}`. "
              "[Methods](screening-calibration.md), "
              "[basin coverage](../reports/exploratory/screening_calibration/screening_coverage.csv), "
              "[basin bins](../reports/exploratory/screening_calibration/calibration_lobo_by_domain.csv), "
              "[dataset bins](../reports/exploratory/screening_calibration/calibration_lodo_by_domain.csv).", ""]
    (out / "summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    (ROOT / "docs/screening-results.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
