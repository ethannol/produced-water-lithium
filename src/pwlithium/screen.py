"""Screening rule, cluster bootstrap and basin / formation tables (pre-registered)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from pwlithium.util import CEILING, FLOOR, N_BOOT, SEED


def passes_screen(li: pd.Series, mg: pd.Series, floor: float = FLOOR, ceiling: float = CEILING,
                  tds: pd.Series | None = None, tds_min: float | None = None) -> pd.Series:
    """Well passes if Li >= floor and Mg/Li <= ceiling (and TDS >= tds_min when given).

    Wells without Mg cannot pass the joint screen (the ratio is undefined)."""
    ratio = mg / li
    ok = (li >= floor) & (ratio <= ceiling)
    if tds_min is not None:
        ok &= tds >= tds_min
    return ok.fillna(False).astype(bool)


def _stats(li: np.ndarray, ok: np.ndarray) -> tuple[float, float]:
    return float(np.median(li)), float(ok.mean())


def cluster_bootstrap(li: np.ndarray, ok: np.ndarray, clusters: np.ndarray,
                      n_boot: int = N_BOOT, seed: int = SEED) -> dict[str, float]:
    """Percentile intervals for the median Li and the screened fraction.

    Resamples wells. With more than one cluster (dataset), clusters are resampled with
    replacement first and then wells within each drawn cluster (two-stage bootstrap).
    """
    rng = np.random.default_rng(seed)
    li = np.asarray(li, float)
    ok = np.asarray(ok, bool)
    clusters = np.asarray(clusters)
    uniq = np.unique(clusters)
    idx_by = {c: np.flatnonzero(clusters == c) for c in uniq}
    meds = np.empty(n_boot)
    fracs = np.empty(n_boot)
    n = len(li)
    for b in range(n_boot):
        if len(uniq) > 1:
            drawn = rng.choice(uniq, size=len(uniq), replace=True)
            parts = [rng.choice(idx_by[c], size=len(idx_by[c]), replace=True) for c in drawn]
            idx = np.concatenate(parts)
        else:
            idx = rng.integers(0, n, size=n)
        meds[b], fracs[b] = _stats(li[idx], ok[idx])
    med, frac = _stats(li, ok)
    return {
        "median_li": med, "median_lo": float(np.percentile(meds, 2.5)),
        "median_hi": float(np.percentile(meds, 97.5)),
        "frac_pass": frac, "frac_lo": float(np.percentile(fracs, 2.5)),
        "frac_hi": float(np.percentile(fracs, 97.5)),
    }


def naive_bootstrap(li: np.ndarray, ok: np.ndarray, n_boot: int = N_BOOT, seed: int = SEED):
    """Row/well bootstrap ignoring clusters (used only to show the difference)."""
    return cluster_bootstrap(li, ok, np.zeros(len(li)), n_boot=n_boot, seed=seed)


def group_table(wells: pd.DataFrame, by: str, min_wells: int, floor: float = FLOOR,
                ceiling: float = CEILING, tds_min: float | None = None, n_boot: int = N_BOOT,
                seed: int = SEED, bootstrap: bool = True) -> pd.DataFrame:
    """Per group: wells with Li, datasets, median/IQR Li, screened fraction, Mg/Li, intervals."""
    w = wells.loc[wells["Li"].notna()].copy()
    w["ok"] = passes_screen(w["Li"], w["Mg"], floor, ceiling, w["TDS"], tds_min)
    recs = []
    for name, g in w.groupby(by, sort=True):
        if name == "Unknown" and by == "FORMSIMPLE":
            continue
        rec = {
            by: name, "n_wells": len(g), "n_datasets": g["IDDB"].nunique(),
            "n_wells_mg": int(g["Mg"].notna().sum()),
            "n_rows": int(g["n_rows"].sum()),
            "li_q25": float(g["Li"].quantile(0.25)), "li_q75": float(g["Li"].quantile(0.75)),
            "frac_above_floor": float((g["Li"] >= floor).mean()),
            "mgli_median": float(g["mg_li"].median()), "mgli_q25": float(g["mg_li"].quantile(0.25)),
            "mgli_q75": float(g["mg_li"].quantile(0.75)),
            "n_pass": int(g["ok"].sum()),
            "share_sg_estimated": float(g["sg_estimated"].mean()),
            "share_coord_approx": float(g["coord_approx"].mean()),
            "share_balanced_by_construction": float(g["balanced_by_construction"].mean()),
            "ranked": len(g) >= min_wells,
        }
        if bootstrap and len(g) >= min_wells:
            rec.update(cluster_bootstrap(g["Li"].values, g["ok"].values, g["IDDB"].values,
                                         n_boot=n_boot, seed=seed))
        else:
            rec.update({"median_li": float(g["Li"].median()), "median_lo": np.nan,
                        "median_hi": np.nan, "frac_pass": float(g["ok"].mean()),
                        "frac_lo": np.nan, "frac_hi": np.nan})
        recs.append(rec)
    out = pd.DataFrame(recs)
    out = out.sort_values(["ranked", "median_li"], ascending=[False, False]).reset_index(drop=True)
    out["rank"] = np.where(out["ranked"], np.arange(1, len(out) + 1), np.nan)
    return out


def top_set(table: pd.DataFrame, by: str, k: int = 5) -> list[str]:
    t = table.loc[table["ranked"]].sort_values("median_li", ascending=False)
    return t[by].head(k).tolist()


def separable_pairs(table: pd.DataFrame, by: str) -> list[tuple[str, str]]:
    """Ordered pairs (a above b) whose 95% intervals for the median do not overlap."""
    t = table.loc[table["ranked"]].sort_values("median_li", ascending=False).reset_index(drop=True)
    pairs = []
    for i in range(len(t)):
        for j in range(i + 1, len(t)):
            if t.loc[i, "median_lo"] > t.loc[j, "median_hi"]:
                pairs.append((t.loc[i, by], t.loc[j, by]))
    return pairs


def robustness(primary: pd.DataFrame, other: pd.DataFrame, by: str) -> dict:
    """Pre-registered test: top-5 overlap >= 4 and no separable pair reverses order."""
    top_p, top_o = top_set(primary, by), top_set(other, by)
    overlap = len(set(top_p) & set(top_o))
    med_o = other.set_index(by)["median_li"]
    reversed_pairs = [
        (a, b) for a, b in separable_pairs(primary, by)
        if a in med_o.index and b in med_o.index and med_o[a] < med_o[b]
    ]
    return {
        "top5_primary": top_p, "top5_other": top_o, "top5_overlap": overlap,
        "n_separable_pairs": len(separable_pairs(primary, by)),
        "n_reversed_pairs": len(reversed_pairs), "reversed_pairs": reversed_pairs,
        "robust": bool(overlap >= 4 and not reversed_pairs),
        "moved": sorted(set(top_p) ^ set(top_o)),
    }
