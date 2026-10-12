"""Step 1: pre-registered population -> included rows, exclusion log, wells at the primary
charge-balance tolerance. Records every count the report quotes about data quality."""

import pandas as pd
from cairn import censored_values, record, recount, unique_key

from pwlithium import prepare
from pwlithium.util import CB_TOL, DERIVED, LI_FOCUSED

DERIVED.mkdir(parents=True, exist_ok=True)
raw = prepare.derive(prepare.load_raw())
unique_key(raw, "IDUSGS")
rows, log = prepare.apply_inclusion(raw)
recount(raw, rows, "inclusion", expect="fewer")
for _, r in log.iterrows():
    record(f"prepare.excl.{r['step']}", int(r["rows_removed"]), unit="rows", note=r["rule"])
record("prepare.rows_raw", len(raw), unit="rows")
record("prepare.rows_included", len(rows), unit="rows")
record("prepare.rows_excluded", len(raw) - len(rows), unit="rows")

# charge balance at the primary tolerance (null CHARGEBAL dropped, counted)
cb_null = int(rows["CHARGEBAL"].isna().sum())
primary_rows = prepare.charge_balance_filter(rows, CB_TOL)
record("prepare.cb.null_rows", cb_null, unit="rows")
record("prepare.cb.removed_rows", len(rows) - len(primary_rows) - cb_null, unit="rows",
       note=f"|CHARGEBAL| > {CB_TOL}")
record("prepare.cb.tolerance", CB_TOL, unit="percent")
li_rows = rows.loc[rows["li_measured"]]
record("prepare.cb.li_rows_removed", int(((li_rows["cb_abs"] > CB_TOL) | li_rows["CHARGEBAL"].isna()).sum()))
for tol in (5, 10, 15):
    record(f"prepare.cb.rows_kept_tol{tol}", int((rows["cb_abs"] <= tol).sum()), unit="rows")
record("prepare.cb.balanced_by_construction_rows", int(rows["balanced_by_construction"].sum()))
record("prepare.cb.balanced_by_construction_li_rows", int(li_rows["balanced_by_construction"].sum()))
bbc = rows.loc[rows["balanced_by_construction"], "IDDB"].value_counts()
record("prepare.cb.balanced_by_construction_top_dataset", str(bbc.index[0]))
record("prepare.cb.balanced_by_construction_top_dataset_rows", int(bbc.iloc[0]))
log = pd.concat([log, pd.DataFrame([{
    "step": "charge_balance", "rule": f"|CHARGEBAL| > {CB_TOL} or CHARGEBAL missing",
    "rows_before": len(rows), "rows_removed": len(rows) - len(primary_rows),
    "rows_after": len(primary_rows)}])], ignore_index=True)
log.to_csv(DERIVED / "exclusion_log.csv", index=False)

# specific gravity
record("prepare.sg.estimated_rows", int(rows["sg_estimated"].sum()), unit="rows")
record("prepare.sg.ppm_estimated_rows", int(rows["ppm_estimated_sg"].sum()), unit="rows",
       note="ppm rows converted with a regression-estimated SG")
record("prepare.sg.ppm_rows", int((rows["UNITSORIG"].str.lower() == "ppm").sum()), unit="rows")
record("prepare.sg.ppm_estimated_li_rows", int(li_rows["ppm_estimated_sg"].sum()), unit="rows")
record("prepare.sg.share_estimated", float(rows["sg_estimated"].mean()))

# censoring sensor (the column holds no markers; the sensor documents that)
censored_values(rows["Li"].astype("string"), name="censored_values(Li)")

# wells
keyed = prepare.well_key(primary_rows)
wells = prepare.collapse_wells(keyed)
unique_key(wells, "well_id")
recount(keyed, wells, "collapse_rows_to_wells", expect="fewer")
record("prepare.wells.rows_in", len(keyed), unit="rows")
record("prepare.wells.n_wells", len(wells))
record("prepare.wells.rows_collapsed", len(keyed) - len(wells), unit="rows")
record("prepare.wells.n_wells_li", int(wells["li_measured"].sum()))
li_keyed = keyed.loc[keyed["li_measured"]]
record("prepare.wells.li_rows_in", len(li_keyed), unit="rows")
record("prepare.wells.li_rows_collapsed", len(li_keyed) - int(wells["li_measured"].sum()), unit="rows")
record("prepare.wells.li_wells_multi_row", int((wells["n_li_rows"] > 1).sum()))
record("prepare.wells.li_max_rows_per_well", int(wells["n_li_rows"].max()))
for cls, n in li_keyed["key_class"].value_counts().items():
    record(f"prepare.wells.li_rows_key_{cls}", int(n), unit="rows")
for cls, n in wells.loc[wells["li_measured"], "key_class"].value_counts().items():
    record(f"prepare.wells.li_wells_key_{cls}", int(n))
lw = wells.loc[wells["li_measured"]]
record("prepare.wells.li_wells_sg_estimated", int(lw["sg_estimated"].sum()))
record("prepare.wells.li_wells_coord_approx", int(lw["coord_approx"].sum()))
record("prepare.wells.li_wells_share_coord_approx", float(lw["coord_approx"].mean()))
record("prepare.wells.li_wells_with_mg", int(lw["Mg"].notna().sum()))
record("prepare.wells.li_wells_without_mg", int(lw["Mg"].isna().sum()))
record("prepare.wells.li_wells_n_datasets", int(lw["IDDB"].nunique()))
record("prepare.wells.li_wells_n_basins", int(lw["BASIN"].nunique()))
record("prepare.wells.li_wells_in_li_focused", int(lw["IDDB"].isin(LI_FOCUSED).sum()))
record("prepare.wells.li_wells_tds_brine_share", float((lw["TDS"] >= 1e5).mean()))
rows.to_csv(DERIVED / "rows_included.csv", index=False)
wells.to_csv(DERIVED / "wells_primary.csv", index=False)
print(f"included rows {len(rows)}, primary rows {len(primary_rows)}, wells {len(wells)}, Li wells {len(lw)}")
