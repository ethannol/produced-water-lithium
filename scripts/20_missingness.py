"""Step 2: rows with lithium measured versus rows without (pre-registered comparison)."""

import numpy as np
import pandas as pd
from cairn import record

from pwlithium import missing, prepare
from pwlithium.util import DERIVED, TABLES

TABLES.mkdir(parents=True, exist_ok=True)
rows = pd.read_csv(DERIVED / "rows_included.csv", low_memory=False)
rows["li_measured"] = rows["Li"].notna()
rows["decade"] = rows["decade"].astype("Int64")
rows = prepare.well_key(rows)
m, u = rows.loc[rows["li_measured"]], rows.loc[~rows["li_measured"]]
record("miss.n_rows", len(rows), unit="rows")
record("miss.n_measured", len(m), unit="rows")
record("miss.n_not_measured", len(u), unit="rows")
record("miss.share_measured", float(rows["li_measured"].mean()))
record("miss.tds_median_measured", float(m["TDS"].median()), unit="mg/L")
record("miss.tds_median_not_measured", float(u["TDS"].median()), unit="mg/L")
record("miss.depth_median_measured", float(m["depth_mid_ft"].median()), unit="ft")
record("miss.depth_median_not_measured", float(u["depth_mid_ft"].median()), unit="ft")
record("miss.depth_missing_share_measured", float(m["depth_mid_ft"].isna().mean()))
record("miss.depth_missing_share_not_measured", float(u["depth_mid_ft"].isna().mean()))
record("miss.date_missing_share_measured", float(m["decade"].isna().mean()))
record("miss.date_missing_share_not_measured", float(u["decade"].isna().mean()))
record("miss.smd_log_tds", missing.smd(np.log10(m["TDS"].where(m["TDS"] > 0)),
                                       np.log10(u["TDS"].where(u["TDS"] > 0))))
record("miss.smd_log_depth", missing.smd(np.log10(m["depth_mid_ft"].where(m["depth_mid_ft"] > 0)),
                                         np.log10(u["depth_mid_ft"].where(u["depth_mid_ft"] > 0))))
record("miss.decade_median_measured", float(m["decade"].dropna().astype(float).median()))
record("miss.decade_median_not_measured", float(u["decade"].dropna().astype(float).median()))
for col, name in [("BASIN", "basin"), ("IDDB", "dataset"), ("PLAYTYPE", "playtype"), ("decade", "decade")]:
    t = missing.composition(rows, col, top=15 if col != "decade" else 12)
    t.to_csv(TABLES / f"missingness_{name}.csv", index=False)
    record(f"miss.{name}_top_measured", str(t.iloc[0, 0]))
    record(f"miss.{name}_top_measured_share", float(t.iloc[0]["share_measured"]))
    record(f"miss.{name}_top_measured_share_not", float(t.iloc[0]["share_not_measured"]))
# the datasets' share of their own rows with Li, to show measurement is a dataset property
by_ds = rows.groupby("IDDB")["li_measured"].agg(["mean", "size", "sum"]).rename(
    columns={"mean": "share_li", "size": "rows", "sum": "li_rows"}).sort_values("rows", ascending=False)
by_ds.to_csv(TABLES / "li_share_by_dataset.csv")
record("miss.datasets_all_measured", int((by_ds["share_li"] >= 0.99).sum()))
record("miss.datasets_none_measured", int((by_ds["share_li"] == 0).sum()))
record("miss.datasets_total", int(len(by_ds)))
record("miss.usgsbreit_share_li", float(by_ds.loc["USGSBREIT", "share_li"]))
record("miss.usgsbreit_rows", int(by_ds.loc["USGSBREIT", "rows"]))
by_basin_decade = rows.groupby(["BASIN", "decade"], dropna=False)["li_measured"].agg(["sum", "size"]).reset_index()
by_basin_decade.to_csv(TABLES / "li_measured_by_basin_decade.csv", index=False)
auc, aucs = missing.measured_auc(rows, seed=0)
record("miss.auc", auc, note="5-fold grouped-by-well logistic regression, lithium measured")
record("miss.auc_min", float(min(aucs)))
record("miss.auc_max", float(max(aucs)))
smd_tds = missing.smd(np.log10(m["TDS"].where(m["TDS"] > 0)), np.log10(u["TDS"].where(u["TDS"] > 0)))
smd_depth = missing.smd(np.log10(m["depth_mid_ft"].where(m["depth_mid_ft"] > 0)),
                        np.log10(u["depth_mid_ft"].where(u["depth_mid_ft"] > 0)))
not_random = bool(auc >= 0.70 or abs(smd_tds) >= 0.20 or abs(smd_depth) >= 0.20)
record("miss.verdict", "missing is not random" if not_random else
       "no evidence that lithium measurement depends on the compared variables")
print(f"AUC {auc:.3f}, SMD tds {smd_tds:.2f}, depth {smd_depth:.2f}")
