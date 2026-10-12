"""Supplementary coverage and held-domain calibration from recorded predictions."""
import json
import subprocess
from pathlib import Path

import pandas as pd

from pwlithium.domain_calibration import domain_reliability
from pwlithium.screen_coverage import screening_coverage

ROOT = Path(__file__).resolve().parents[1]


def main():
    wells = pd.read_csv(ROOT / "data/derived/wells_primary.csv")
    out = ROOT / "reports/exploratory/screening_calibration"
    out.mkdir(parents=True, exist_ok=True)
    coverage = screening_coverage(wells)
    coverage.to_csv(out / "screening_coverage.csv", index=False)
    # Rankings of bounds show how missing Mg could affect screening order.
    coverage.assign(rank_lower=coverage.fraction_lower.rank(method="min", ascending=False),
                    rank_upper=coverage.fraction_upper.rank(method="min", ascending=False)).to_csv(
                        out / "screening_rank_bounds.csv", index=False)
    oof = pd.read_csv(ROOT / "data/derived/oof_model.csv")
    for protocol, domain in [("lobo", "BASIN"), ("lodo", "IDDB")]:
        subset = oof.loc[(oof.protocol == protocol) & (oof.model == "hgb")]
        domain_reliability(subset, domain).to_csv(out / f"calibration_{protocol}_by_domain.csv", index=False)
    payload = dict(exploratory=True, n_pass=int(coverage.n_pass.sum()),
                   n_unknown=int(coverage.n_unknown.sum()), n_fail=int(coverage.n_fail.sum()),
                   n_li_wells=int(coverage.n_li_wells.sum()),
                   source_revision=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                   caveat=("Wilson intervals describe held-domain bin support, "
                           "not model or transport uncertainty; no recalibration fitted"),
                   baseline_unchanged=True)
    (out / "results.json").write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
