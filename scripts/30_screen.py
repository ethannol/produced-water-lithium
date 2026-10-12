"""Step 3: basin and formation tables with cluster bootstrap intervals; the bias-adjusted
view; the charge-balance and threshold sensitivities; the pre-registered robustness tests."""

import json

import pandas as pd
from cairn import record

from pwlithium import prepare, screen
from pwlithium.util import (
    CEILING,
    DERIVED,
    FLOOR,
    LI_FOCUSED,
    MIN_WELLS_BASIN,
    MIN_WELLS_FORMATION,
    N_BOOT,
    SEED,
    TABLES,
    commas,
    slug,
)

TABLES.mkdir(parents=True, exist_ok=True)
rows = pd.read_csv(DERIVED / "rows_included.csv", low_memory=False)
wells = pd.read_csv(DERIVED / "wells_primary.csv", low_memory=False)
record("screen.floor_mg_l", FLOOR, unit="mg/L")
record("screen.ceiling_mg_li", CEILING)
record("screen.n_boot", N_BOOT)
record("screen.seed", SEED)
record("screen.min_wells_basin", MIN_WELLS_BASIN)
record("screen.min_wells_formation", MIN_WELLS_FORMATION)

lw = wells.loc[wells["li_measured"]].copy()
lw["ok"] = screen.passes_screen(lw["Li"], lw["Mg"])
record("screen.n_li_wells", len(lw))
record("screen.n_pass_primary", int(lw["ok"].sum()))
record("screen.share_pass_primary", float(lw["ok"].mean()))
record("screen.n_above_floor", int((lw["Li"] >= FLOOR).sum()))
record("screen.share_above_floor", float((lw["Li"] >= FLOOR).mean()))
record("screen.n_above_floor_high_mgli", int(((lw["Li"] >= FLOOR) & (lw["mg_li"] > CEILING)).sum()))
record("screen.li_median_all_wells", float(lw["Li"].median()), unit="mg/L")
record("screen.li_q90_all_wells", float(lw["Li"].quantile(0.9)), unit="mg/L")
record("screen.mgli_median_all_wells", float(lw["mg_li"].median()))

# --- primary basin table
basin = screen.group_table(wells, "BASIN", MIN_WELLS_BASIN)
basin.to_csv(TABLES / "basin_primary.csv", index=False)
ranked = basin.loc[basin["ranked"]].reset_index(drop=True)
record("screen.n_basins_with_li", len(basin))
record("screen.n_basins_ranked", len(ranked))
record("screen.n_basins_ranked_wells", int(ranked["n_wells"].sum()))
for i, r in ranked.head(8).iterrows():
    k = f"screen.basin{i + 1}"
    record(f"{k}.name", r["BASIN"])
    record(f"{k}.n_wells", int(r["n_wells"]))
    record(f"{k}.n_datasets", int(r["n_datasets"]))
    record(f"{k}.median_li", r["median_li"], unit="mg/L")
    record(f"{k}.median_lo", r["median_lo"], unit="mg/L")
    record(f"{k}.median_hi", r["median_hi"], unit="mg/L")
    record(f"{k}.frac_pass", r["frac_pass"])
    record(f"{k}.frac_lo", r["frac_lo"])
    record(f"{k}.frac_hi", r["frac_hi"])
    record(f"{k}.n_pass", int(r["n_pass"]))
    record(f"{k}.mgli_median", r["mgli_median"])
    record(f"{k}.share_sg_estimated", r["share_sg_estimated"])
    record(f"{k}.share_coord_approx", r["share_coord_approx"])
by_pass = ranked.sort_values("frac_pass", ascending=False).reset_index(drop=True)
for i, r in by_pass.head(5).iterrows():
    k = f"screen.pass{i + 1}"
    record(f"{k}.name", r["BASIN"])
    record(f"{k}.n_wells", int(r["n_wells"]))
    record(f"{k}.frac_pass", r["frac_pass"])
    record(f"{k}.frac_lo", r["frac_lo"])
    record(f"{k}.frac_hi", r["frac_hi"])
    record(f"{k}.n_pass", int(r["n_pass"]))
record("screen.n_basins_frac_interval_excludes_zero", int((ranked["frac_lo"] > 0).sum()))
record("screen.n_basins_any_pass", int((ranked["n_pass"] > 0).sum()))
record("screen.n_separable_pairs", len(screen.separable_pairs(basin, "BASIN")))
record("screen.n_ranked_pairs", len(ranked) * (len(ranked) - 1) // 2)
record("screen.top5_primary", commas(screen.top_set(basin, "BASIN")))
record("screen.n_basins_multi_dataset", int((ranked["n_datasets"] > 1).sum()))

# --- formation table (primary)
form = screen.group_table(wells, "FORMSIMPLE", MIN_WELLS_FORMATION)
form.to_csv(TABLES / "formation_primary.csv", index=False)
fr = form.loc[form["ranked"]].reset_index(drop=True)
record("screen.n_formations_ranked", len(fr))
for i, r in fr.head(8).iterrows():
    k = f"screen.form{i + 1}"
    record(f"{k}.name", r["FORMSIMPLE"])
    record(f"{k}.n_wells", int(r["n_wells"]))
    record(f"{k}.n_datasets", int(r["n_datasets"]))
    record(f"{k}.median_li", r["median_li"], unit="mg/L")
    record(f"{k}.median_lo", r["median_lo"], unit="mg/L")
    record(f"{k}.median_hi", r["median_hi"], unit="mg/L")
    record(f"{k}.frac_pass", r["frac_pass"])
    record(f"{k}.frac_lo", r["frac_lo"])
    record(f"{k}.frac_hi", r["frac_hi"])
    record(f"{k}.mgli_median", r["mgli_median"])

# --- bias-adjusted view: drop the lithium-focused datasets named in the version history
w_adj = wells.loc[~wells["IDDB"].isin(LI_FOCUSED)]
basin_adj = screen.group_table(w_adj, "BASIN", MIN_WELLS_BASIN)
basin_adj.to_csv(TABLES / "basin_without_li_focused.csv", index=False)
rb = screen.robustness(basin, basin_adj, "BASIN")
record("screen.adj.n_li_wells_removed", int(lw["IDDB"].isin(LI_FOCUSED).sum()))
record("screen.adj.datasets", commas(LI_FOCUSED))
record("screen.adj.top5_overlap", rb["top5_overlap"])
record("screen.adj.n_reversed_pairs", rb["n_reversed_pairs"])
record("screen.adj.robust", "robust" if rb["robust"] else "partly an artifact of which datasets were compiled")
record("screen.adj.moved", commas(rb["moved"]) if rb["moved"] else "none")
record("screen.adj.n_basins_ranked", int(basin_adj["ranked"].sum()))
adj_idx = basin_adj.set_index("BASIN")
for i, r in ranked.head(8).iterrows():
    k = f"screen.basin{i + 1}.adj"
    if r["BASIN"] in adj_idx.index:
        a = adj_idx.loc[r["BASIN"]]
        record(f"{k}.n_wells", int(a["n_wells"]))
        record(f"{k}.median_li", a["median_li"], unit="mg/L")
        record(f"{k}.median_lo", a["median_lo"], unit="mg/L")
        record(f"{k}.median_hi", a["median_hi"], unit="mg/L")
        record(f"{k}.frac_pass", a["frac_pass"])
    else:
        record(f"{k}.n_wells", 0)
        for f in ("median_li", "median_lo", "median_hi", "frac_pass"):
            record(f"{k}.{f}", float("nan"))
# which basins the focused datasets touch
touched = lw.loc[lw["IDDB"].isin(LI_FOCUSED)].groupby("BASIN").size()
record("screen.adj.basins_touched", commas(f"{b} ({n})" for b, n in touched.items()) or "none")

# --- by dataset within basin (basins with > 1 dataset)
recs = []
for b, g in lw.groupby("BASIN"):
    if g["IDDB"].nunique() < 2 or len(g) < MIN_WELLS_BASIN:
        continue
    for d, gd in g.groupby("IDDB"):
        recs.append({"BASIN": b, "IDDB": d, "n_wells": len(gd), "median_li": gd["Li"].median(),
                     "li_q25": gd["Li"].quantile(0.25), "li_q75": gd["Li"].quantile(0.75),
                     "frac_pass": gd["ok"].mean(), "mgli_median": gd["mg_li"].median(),
                     "sample_year_median": gd["sample_year"].median()})
ds = pd.DataFrame(recs)
ds.to_csv(TABLES / "basin_by_dataset.csv", index=False)
spread = ds.groupby("BASIN").apply(lambda g: g.loc[g["n_wells"] >= 5, "median_li"].max() /
                                   g.loc[g["n_wells"] >= 5, "median_li"].min()
                                   if (g["n_wells"] >= 5).sum() >= 2 else float("nan"),
                                   include_groups=False).dropna().sort_values(ascending=False)
record("screen.ds.n_basins_multi", int(ds["BASIN"].nunique()))
record("screen.ds.n_basins_two_datasets_ge5", int(len(spread)))
record("screen.ds.max_ratio_basin", str(spread.index[0]))
record("screen.ds.max_ratio", float(spread.iloc[0]))
record("screen.ds.median_ratio", float(spread.median()))
record("screen.ds.n_basins_ratio_ge2", int((spread >= 2).sum()))
record("screen.ds.n_basins_ratio_ge5", int((spread >= 5).sum()))

# --- charge-balance sensitivity
cb_results = {}
for tol, label in [(5, "tol5"), (15, "tol15"), (None, "none")]:
    w_t = prepare.wells_at_tolerance(rows, tol)
    t = screen.group_table(w_t, "BASIN", MIN_WELLS_BASIN)
    t.to_csv(TABLES / f"basin_cb_{label}.csv", index=False)
    r = screen.robustness(basin, t, "BASIN")
    cb_results[label] = r
    record(f"screen.cb.{label}.n_li_wells", int(w_t["li_measured"].sum()))
    record(f"screen.cb.{label}.n_basins_ranked", int(t["ranked"].sum()))
    record(f"screen.cb.{label}.top5_overlap", r["top5_overlap"])
    record(f"screen.cb.{label}.n_reversed_pairs", r["n_reversed_pairs"])
    record(f"screen.cb.{label}.moved", commas(r["moved"]) if r["moved"] else "none")
record("screen.cb.robust", "robust" if all(r["robust"] for r in cb_results.values())
       else "sensitive to the charge-balance tolerance")
record("screen.cb.primary_n_li_wells", len(lw))

# --- threshold sensitivity grid (counts and shares, no bootstrap)
grid = []
for floor in (50, 100, 200):
    for ceiling in (6, 10, 20):
        for tds_min in (None, 1e5):
            ok = screen.passes_screen(lw["Li"], lw["Mg"], floor, ceiling, lw["TDS"], tds_min)
            t = screen.group_table(wells, "BASIN", MIN_WELLS_BASIN, floor, ceiling, tds_min, bootstrap=False)
            top = screen.top_set(t.assign(median_li=t["frac_pass"]), "BASIN", 3)
            grid.append({"floor": floor, "ceiling": ceiling, "tds_min": tds_min or 0,
                         "n_pass": int(ok.sum()), "share_pass": float(ok.mean()),
                         "n_basins_any_pass": int((t.loc[t["ranked"], "n_pass"] > 0).sum()),
                         "top3_by_frac_pass": commas(top)})
grid = pd.DataFrame(grid)
grid.to_csv(TABLES / "threshold_grid.csv", index=False)
record("screen.grid.n_cells", len(grid))
record("screen.grid.n_pass_min", int(grid["n_pass"].min()))
record("screen.grid.n_pass_max", int(grid["n_pass"].max()))
record("screen.grid.share_pass_min", float(grid["share_pass"].min()))
record("screen.grid.share_pass_max", float(grid["share_pass"].max()))
loose = grid.loc[(grid["floor"] == 50) & (grid["ceiling"] == 20) & (grid["tds_min"] == 0)].iloc[0]
strict = grid.loc[(grid["floor"] == 200) & (grid["ceiling"] == 6) & (grid["tds_min"] == 0)].iloc[0]
record("screen.grid.loose_n_pass", int(loose["n_pass"]))
record("screen.grid.strict_n_pass", int(strict["n_pass"]))
brine = grid.loc[(grid["floor"] == 100) & (grid["ceiling"] == 10) & (grid["tds_min"] > 0)].iloc[0]
record("screen.grid.brine_n_pass", int(brine["n_pass"]))
# top-3-by-fraction stability across the grid
tops = grid["top3_by_frac_pass"].str.split(", ")
record("screen.grid.n_distinct_top3", int(tops.apply(tuple).nunique()))
# smaller groups appendix
basin.loc[~basin["ranked"]].to_csv(TABLES / "basin_small_groups.csv", index=False)
lw.to_csv(DERIVED / "li_wells_primary.csv", index=False)
(TABLES / "robustness.json").write_text(json.dumps({"li_focused": rb, "charge_balance": cb_results},
                                                    indent=2, default=str) + "\n")
print(ranked[["BASIN", "n_wells", "n_datasets", "median_li", "median_lo", "median_hi", "frac_pass", "frac_lo", "frac_hi"]].head(10).to_string())
print("slug check", slug("Gulf Coast"))
