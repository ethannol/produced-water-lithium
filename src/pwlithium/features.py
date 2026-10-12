"""Pre-registered feature set for the lithium model (well level)."""

from __future__ import annotations

import numpy as np
import pandas as pd

SUBCOMP = ["Na", "K", "Ca", "Mg", "Cl"]
PLAYTYPES = ["Sedimentary", "Shale", "Coal"]
ERAS = ["Paleozoic", "Mesozoic", "Cenozoic", "Precambrian"]


def modelling_mask(wells: pd.DataFrame, target: str = "Li") -> pd.Series:
    """Wells usable for the model: target present and positive, subcomposition and TDS present."""
    need = [target, *SUBCOMP, "TDS"]
    m = wells[need].notna().all(axis=1)
    for c in need:
        m &= wells[c] > 0
    return m


def clr(df: pd.DataFrame, cols: list[str] = SUBCOMP) -> pd.DataFrame:
    logs = np.log10(df[cols].astype(float))
    return (logs.sub(logs.mean(axis=1), axis=0)).add_prefix("clr_")


def build_features(wells: pd.DataFrame, drop_tds: bool = False) -> pd.DataFrame:
    """Feature frame; missing depth is left NaN with an indicator (imputed inside the fold)."""
    x = clr(wells)
    if not drop_tds:
        x["log_tds"] = np.log10(wells["TDS"].astype(float))
    depth = wells["depth_mid_ft"].astype(float)
    x["log_depth"] = np.log10(depth.where(depth > 0))
    x["depth_missing"] = x["log_depth"].isna().astype(float)
    for p in PLAYTYPES:
        x[f"play_{p.lower()}"] = (wells["PLAYTYPE"] == p).astype(float)
    era = wells["ERA"].where(wells["ERA"].isin(ERAS), "missing")
    for e in [*ERAS, "missing"]:
        x[f"era_{e.lower()}"] = (era == e).astype(float)
    return x


def target(wells: pd.DataFrame, col: str = "Li") -> pd.Series:
    return np.log10(wells[col].astype(float)).rename(f"log10_{col}")
