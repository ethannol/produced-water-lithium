"""Missingness comparison: rows with lithium measured versus rows without (pre-registered)."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from pwlithium.cv import random_group_folds


def smd(a: pd.Series, b: pd.Series) -> float:
    """Standardized mean difference with the pooled standard deviation."""
    a, b = a.dropna().astype(float), b.dropna().astype(float)
    sp = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
    return float((a.mean() - b.mean()) / sp) if sp > 0 else float("nan")


def composition(rows: pd.DataFrame, col: str, top: int = 12) -> pd.DataFrame:
    """Share of rows in each category, for the measured and unmeasured groups."""
    cat = rows[col].astype(object).where(rows[col].notna(), "missing")
    t = pd.crosstab(cat, rows["li_measured"], normalize="columns")
    t.columns = ["share_not_measured" if not c else "share_measured" for c in t.columns]
    t["diff"] = t["share_measured"] - t["share_not_measured"]
    t = t.reindex(t["share_measured"].sort_values(ascending=False).index).head(top)
    return t.reset_index()


def design(rows: pd.DataFrame) -> pd.DataFrame:
    x = pd.DataFrame(index=rows.index)
    lt = np.log10(rows["TDS"].where(rows["TDS"] > 0))
    ld = np.log10(rows["depth_mid_ft"].where(rows["depth_mid_ft"] > 0))
    x["log_tds"] = lt.fillna(lt.median())
    x["tds_missing"] = lt.isna().astype(float)
    x["log_depth"] = ld.fillna(ld.median())
    x["depth_missing"] = ld.isna().astype(float)
    dec = rows["decade"].astype("float")
    x["decade"] = dec.fillna(dec.median())
    x["decade_missing"] = dec.isna().astype(float)
    for p in ["Sedimentary", "Shale", "Coal"]:
        x[f"play_{p}"] = (rows["PLAYTYPE"] == p).astype(float)
    basins = rows["BASIN"].value_counts()
    for b in basins.index[:30]:
        x[f"basin_{b}"] = (rows["BASIN"] == b).astype(float)
    return x


def measured_auc(rows: pd.DataFrame, seed: int = 0, k: int = 5) -> tuple[float, list[float]]:
    """5-fold (grouped by well) cross-validated AUC of 'lithium measured'."""
    x = design(rows)
    y = rows["li_measured"].astype(int).values
    groups = rows["well_id"].values
    aucs = []
    for tr, te in random_group_folds(groups, k, seed):
        m = Pipeline([("scale", StandardScaler()),
                      ("lr", LogisticRegression(max_iter=2000, C=1.0))])
        m.fit(x.iloc[tr], y[tr])
        aucs.append(float(roc_auc_score(y[te], m.predict_proba(x.iloc[te])[:, 1])))
    return float(np.mean(aucs)), aucs
