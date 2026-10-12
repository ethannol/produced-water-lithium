"""Raw extract -> included rows (with an exclusion log) -> wells.

Everything here implements the frozen pre-registration (docs/prereg.md): what counts as
produced water, U.S. only, SG range, charge-balance tolerance, the well key and the
collapse of repeated samples to one well.
"""

from __future__ import annotations

import re

import pandas as pd

from pwlithium.util import CB_TOL, RAW

NUMERIC = [
    "LATITUDE", "LONGITUDE", "DEPTHUPPER", "DEPTHLOWER", "ELEVATION", "TIMESERIES", "DAY",
    "TEMP", "SG", "SPGRAV", "PH", "COND", "TDS", "TDSLAB", "TDSCALC",
    "Li", "Na", "K", "Ca", "Mg", "Sr", "Ba", "B", "Cl", "Br", "I", "SO4", "HCO3", "CO3",
    "ALKALINITY", "FeTot", "Si", "KNa", "CHARGEBAL",
]
IONS = ["Li", "Na", "K", "Ca", "Mg", "Sr", "Ba", "B", "Cl", "Br", "I", "SO4", "HCO3", "CO3"]
PRODUCED_PLAYTYPES = {"Sedimentary", "Shale", "Coal"}
EXCLUDED_WELLTYPES = {"Injection", "Water", "CO2"}
NON_US_STATES = {"Ontario", "Saskatchewan"}
INJECTED_RE = re.compile(r"inject|frac water|^frac$", re.I)
SG_MIN, SG_MAX = 0.9, 1.3


def load_raw(path=None) -> pd.DataFrame:
    df = pd.read_csv(path or RAW / "npwgd_v3_extract.csv", low_memory=False, dtype=str)
    for c in NUMERIC:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["IDUSGS"] = pd.to_numeric(df["IDUSGS"], errors="coerce").astype("int64")
    return df


def derive(df: pd.DataFrame) -> pd.DataFrame:
    """Columns the analysis uses, added without changing any source value."""
    out = df.copy()
    out["li_measured"] = out["Li"].notna()
    out["depth_mid_ft"] = out[["DEPTHUPPER", "DEPTHLOWER"]].mean(axis=1)
    out["sample_year"] = pd.to_datetime(out["DATESAMPLE"], errors="coerce").dt.year
    out["decade"] = (out["sample_year"] // 10 * 10).astype("Int64")
    out["sg_estimated"] = out["SG"].notna() & out["SPGRAV"].isna()
    out["ppm_estimated_sg"] = out["sg_estimated"] & (out["UNITSORIG"].str.lower() == "ppm")
    out["coord_approx"] = out["COORDAPX"].notna()
    out["cb_abs"] = out["CHARGEBAL"].abs()
    out["balanced_by_construction"] = out["cb_abs"] < 0.05
    out["mg_li"] = out["Mg"] / out["Li"]
    return out


def apply_inclusion(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Pre-registered population filters except the charge-balance tolerance.

    Rules run in order on what the previous rules kept, so a row is counted once.
    Returns (kept rows, exclusion log with one line per rule in order).
    """
    rules = [
        ("playtype_not_produced_water", lambda k: ~k["PLAYTYPE"].isin(PRODUCED_PLAYTYPES),
         "PLAYTYPE not in Sedimentary, Shale, Coal (Geothermal, Injection)"),
        ("welltype_injection_water_co2", lambda k: k["WELLTYPE"].isin(EXCLUDED_WELLTYPES),
         "WELLTYPE in Injection, Water, CO2"),
        ("formation_injected_fluid", lambda k: k["FORMATION"].fillna("").str.contains(INJECTED_RE),
         "FORMATION names an injected or fracturing fluid"),
        ("non_us_state", lambda k: k["STATE"].isin(NON_US_STATES), "STATE is a Canadian province"),
        ("no_coordinates", lambda k: k["LATITUDE"].isna() | k["LONGITUDE"].isna(),
         "no latitude or longitude"),
        ("basin_unknown", lambda k: k["BASIN"].fillna("Unknown").eq("Unknown"), "BASIN Unknown"),
        ("sg_out_of_range", lambda k: k["SG"].notna() & ((k["SG"] < SG_MIN) | (k["SG"] > SG_MAX)),
         "SG outside 0.9 to 1.3"),
    ]
    log: list[dict] = []
    kept = df
    for step, fn, rule in rules:
        mask = fn(kept).fillna(False).astype(bool)
        log.append({"step": step, "rule": rule, "rows_before": len(kept),
                    "rows_removed": int(mask.sum()), "rows_after": int((~mask).sum())})
        kept = kept.loc[~mask]
    return kept.copy(), pd.DataFrame(log)


def charge_balance_filter(rows: pd.DataFrame, tol: float | None = CB_TOL) -> pd.DataFrame:
    """Keep rows with |CHARGEBAL| <= tol; rows with no CHARGEBAL are dropped. None = no filter."""
    if tol is None:
        return rows.copy()
    return rows.loc[rows["CHARGEBAL"].notna() & (rows["CHARGEBAL"].abs() <= tol)].copy()


def well_key(df: pd.DataFrame) -> pd.DataFrame:
    """Pre-registered key within IDDB: API, else WELLNAME, else exact coords+depth, else row."""
    out = df.copy()
    api = out["API"].notna() & (out["API"].astype(str).str.strip() != "")
    name = ~api & out["WELLNAME"].notna() & (out["WELLNAME"].astype(str).str.strip() != "")
    exact = ~api & ~name & ~out["coord_approx"]
    row = ~api & ~name & ~exact
    key_class = pd.Series("row", index=out.index)
    key_class[exact] = "coords"
    key_class[name] = "wellname"
    key_class[api] = "api"
    key = pd.Series("", index=out.index, dtype=object)
    key[api] = "api:" + out.loc[api, "API"].astype(str).str.strip()
    key[name] = "name:" + out.loc[name, "WELLNAME"].astype(str).str.strip()
    # formatted explicitly: pandas keeps NaN as missing through astype(str), which would
    # turn a well without a depth into a missing key
    key[exact] = [
        f"xy:{lat:.4f},{lon:.4f},{'nodepth' if pd.isna(d) else f'{d:.1f}'}"
        for lat, lon, d in zip(out.loc[exact, "LATITUDE"], out.loc[exact, "LONGITUDE"],
                               out.loc[exact, "DEPTHUPPER"], strict=True)
    ]
    key[row] = "row:" + out.loc[row, "IDUSGS"].astype(str)
    out["key_class"] = key_class
    out["well_id"] = out["IDDB"].astype(str) + "|" + key
    if out["well_id"].isna().any():
        raise ValueError("well_id could not be built for some rows")
    return out


def _modes(rows: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Most frequent non-null value per well for each column (ties: first in sorted order)."""
    out = {}
    for c in cols:
        vc = rows.groupby(["well_id", c]).size().reset_index(name="n")
        vc = vc.sort_values(["well_id", "n", c], ascending=[True, False, True])
        out[c] = vc.drop_duplicates("well_id").set_index("well_id")[c]
    return pd.DataFrame(out)


CATEGORICAL = ["IDDB", "BASIN", "FORMSIMPLE", "FORMATION", "PLAYTYPE", "WELLTYPE", "STATE",
               "ERA", "PERIOD", "COORDAPX", "key_class", "UNITSORIG", "TDSDESC"]
WELL_NUMERIC = ["LATITUDE", "LONGITUDE", "DEPTHUPPER", "DEPTHLOWER", "depth_mid_ft", "TEMP",
                "SG", "PH", "TDS", "CHARGEBAL", "sample_year", *IONS]


def collapse_wells(rows: pd.DataFrame) -> pd.DataFrame:
    """One row per well_id: medians of numeric columns, mode of categoricals, counts."""
    if "well_id" not in rows:
        rows = well_key(rows)
    g = rows.groupby("well_id", sort=True)
    num = g[WELL_NUMERIC].median()
    cat = _modes(rows, CATEGORICAL).reindex(num.index)
    extra = pd.DataFrame({
        "n_rows": g.size(),
        "n_li_rows": g["Li"].count(),
        "sg_estimated": g["ppm_estimated_sg"].any(),
        "coord_approx": g["coord_approx"].any(),
        "balanced_by_construction": g["balanced_by_construction"].any(),
        "first_idusgs": g["IDUSGS"].min(),
    })
    wells = pd.concat([cat, num, extra], axis=1).reset_index()
    wells["li_measured"] = wells["Li"].notna()
    wells["mg_li"] = wells["Mg"] / wells["Li"]
    wells["decade"] = (wells["sample_year"] // 10 * 10).astype("Int64")
    return wells


def wells_at_tolerance(rows: pd.DataFrame, tol: float | None) -> pd.DataFrame:
    return collapse_wells(well_key(charge_balance_filter(rows, tol)))
