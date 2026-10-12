"""Step 5: figures from the derived tables (no new numbers except figure counts)."""

import pandas as pd
from cairn import load_ledger, record

from pwlithium import figures
from pwlithium.util import CEILING, DERIVED, FIGURES, FLOOR, TABLES

FIGURES.mkdir(parents=True, exist_ok=True)
L = load_ledger()
basin = pd.read_csv(TABLES / "basin_primary.csv")
adj = pd.read_csv(TABLES / "basin_without_li_focused.csv")
ranked = basin.loc[basin["ranked"]].sort_values("median_li", ascending=False)
lw = pd.read_csv(DERIVED / "li_wells_primary.csv", low_memory=False)
rows = pd.read_csv(DERIVED / "rows_included.csv", low_memory=False)
rows["li_measured"] = rows["Li"].notna()

figures.coverage(pd.read_csv(TABLES / "li_measured_by_basin_decade.csv"), ranked["BASIN"].tolist(),
                 FIGURES / "fig1_coverage_basin_decade.png")
figures.basin_ranking(basin, adj, FLOOR, FIGURES / "fig2_basin_ranking.png")
figures.mgli_vs_li(lw, FLOOR, CEILING, FIGURES / "fig3_mgli_vs_li.png", ranked["BASIN"].head(3).tolist())
figures.missingness(rows, FIGURES / "fig4_missingness.png")
folds = pd.read_csv(TABLES / "cv_folds_model.csv")
ctrl = pd.read_csv(TABLES / "cv_folds_control.csv")
figures.headline_errors(folds, L["model.target_sd"]["value"], FIGURES / "fig5_prediction_error.png",
                        "Out-of-sample error of log10 Li under three protocols (each dot one held-out fold)",
                        ctrl, L["control.target_sd"]["value"])
figures.calibration({p: pd.read_csv(TABLES / f"calibration_hgb_{p}.csv") for p in ("random", "lodo", "lobo")},
                    FIGURES / "fig6_calibration.png")
figures.well_map(lw, FLOOR, FIGURES / "fig7_map.png")
record("figures.n", len(list(FIGURES.glob("fig*.png"))))
print("figures written")
