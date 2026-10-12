"""Cross-validation protocols, inner grid selection and metrics (pre-registered)."""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.stats import norm
from sklearn.metrics import brier_score_loss, roc_auc_score

from pwlithium.models import GRIDS, make_model


# ---------------------------------------------------------------- splitters
def random_group_folds(groups: np.ndarray, k: int, seed: int) -> list[tuple[np.ndarray, np.ndarray]]:
    """k folds that never split a group; groups are assigned to folds at random."""
    rng = np.random.default_rng(seed)
    uniq = np.unique(groups)
    perm = rng.permutation(uniq)
    fold_of = {g: i % k for i, g in enumerate(perm)}
    f = np.array([fold_of[g] for g in groups])
    return [(np.flatnonzero(f != i), np.flatnonzero(f == i)) for i in range(k)]


def leave_one_group_out(groups: np.ndarray, min_size: int) -> list[tuple[str, np.ndarray, np.ndarray]]:
    """Hold out every group with at least `min_size` members; train on everything else."""
    out = []
    vals, counts = np.unique(groups, return_counts=True)
    for g, c in zip(vals, counts, strict=True):
        if c >= min_size:
            test = np.flatnonzero(groups == g)
            train = np.flatnonzero(groups != g)
            out.append((str(g), train, test))
    return out


def assert_no_leak(groups: np.ndarray, train: np.ndarray, test: np.ndarray) -> None:
    if set(groups[train]) & set(groups[test]):
        raise AssertionError("group appears in both train and test")


# ---------------------------------------------------------------- metrics
def rmse(y, p) -> float:
    return float(np.sqrt(np.mean((np.asarray(y) - np.asarray(p)) ** 2)))


def mae(y, p) -> float:
    return float(np.mean(np.abs(np.asarray(y) - np.asarray(p))))


def r2(y, p) -> float:
    y = np.asarray(y, float)
    sst = float(np.sum((y - y.mean()) ** 2))
    if sst == 0:
        return float("nan")
    return 1.0 - float(np.sum((y - np.asarray(p)) ** 2)) / sst


def screening_metrics(y_log, p_log, sigma, floor_log: float) -> dict[str, float]:
    y = np.asarray(y_log) >= floor_log
    pred_pos = np.asarray(p_log) >= floor_log
    prob = 1.0 - norm.cdf((floor_log - np.asarray(p_log)) / np.maximum(sigma, 1e-6))
    out = {
        "n": int(len(y)), "n_pos": int(y.sum()),
        "precision": float(y[pred_pos].mean()) if pred_pos.any() else float("nan"),
        "recall": float(pred_pos[y].mean()) if y.any() else float("nan"),
        "n_pred_pos": int(pred_pos.sum()),
        "brier": float(brier_score_loss(y, prob)),
    }
    out["auc"] = float(roc_auc_score(y, p_log)) if 0 < y.sum() < len(y) else float("nan")
    return out


def reliability(y_log, p_log, sigma, floor_log: float, n_bins: int = 10) -> pd.DataFrame:
    y = (np.asarray(y_log) >= floor_log).astype(float)
    prob = 1.0 - norm.cdf((floor_log - np.asarray(p_log)) / np.maximum(sigma, 1e-6))
    edges = np.linspace(0, 1, n_bins + 1)
    b = np.clip(np.digitize(prob, edges[1:-1]), 0, n_bins - 1)
    rows = []
    for i in range(n_bins):
        m = b == i
        rows.append({"bin": i, "p_lo": edges[i], "p_hi": edges[i + 1], "n": int(m.sum()),
                     "mean_prob": float(prob[m].mean()) if m.any() else np.nan,
                     "observed": float(y[m].mean()) if m.any() else np.nan})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- inner selection
def select_params(name: str, X: pd.DataFrame, y: np.ndarray, groups: np.ndarray, seed: int,
                  k: int = 3) -> tuple[dict, float]:
    """Grid point with the lowest mean RMSE over k grouped inner folds; also that RMSE."""
    folds = random_group_folds(groups, k, seed)
    best, best_score = None, np.inf
    for params in GRIDS[name]:
        scores = []
        for tr, te in folds:
            m = make_model(name, params, seed)
            m.fit(X.iloc[tr], y[tr])
            scores.append(rmse(y[te], m.predict(X.iloc[te])))
        s = float(np.mean(scores))
        if s < best_score:
            best, best_score = params, s
    return best, best_score


# ---------------------------------------------------------------- evaluation
def _one_fold(name, X, y, groups, inner_groups, label, tr, te, floor_log, seed):
    assert_no_leak(groups, tr, te)
    params, sigma = select_params(name, X.iloc[tr], y[tr], inner_groups[tr], seed)
    m = make_model(name, params, seed)
    m.fit(X.iloc[tr], y[tr])
    p = m.predict(X.iloc[te])
    row = {"fold": label, "n_train": len(tr), "n_test": len(te), "rmse": rmse(y[te], p),
           "mae": mae(y[te], p), "r2": r2(y[te], p), "sigma_inner": sigma, **params}
    row.update({f"cls_{k}": v for k, v in screening_metrics(y[te], p, sigma, floor_log).items()})
    oof = pd.DataFrame({"idx": te, "fold": label, "y": y[te], "pred": p, "sigma": sigma})
    return row, oof


def evaluate(name: str, X: pd.DataFrame, y: np.ndarray, groups: np.ndarray,
             folds: list[tuple[str, np.ndarray, np.ndarray]], floor_log: float, seed: int = 0,
             inner_groups: np.ndarray | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fit on every training fold (grid chosen inside it) and predict the held-out fold.

    Folds run in parallel processes, each single-threaded (OMP_NUM_THREADS=1: the boosted
    model is forty times slower under macOS thread oversubscription). Every fold is seeded,
    so the result does not depend on the scheduling. Returns (per-fold metrics,
    out-of-fold predictions with the fold's sigma)."""
    inner_groups = groups if inner_groups is None else inner_groups
    y = np.asarray(y, float)
    n_jobs = int(os.environ.get("PWLI_JOBS", "8"))
    results = Parallel(n_jobs=n_jobs, prefer="processes")(
        delayed(_one_fold)(name, X, y, groups, inner_groups, label, tr, te, floor_log, seed)
        for label, tr, te in folds
    )
    return pd.DataFrame([r for r, _ in results]), pd.concat([o for _, o in results], ignore_index=True)


def summarise(fold_df: pd.DataFrame, oof: pd.DataFrame, floor_log: float) -> dict[str, float]:
    s = {
        "n_folds": int(len(fold_df)),
        "rmse_pooled": rmse(oof["y"], oof["pred"]), "mae_pooled": mae(oof["y"], oof["pred"]),
        "r2_pooled": r2(oof["y"], oof["pred"]),
        "rmse_fold_min": float(fold_df["rmse"].min()), "rmse_fold_median": float(fold_df["rmse"].median()),
        "rmse_fold_max": float(fold_df["rmse"].max()),
        "rmse_fold_q25": float(fold_df["rmse"].quantile(0.25)),
        "rmse_fold_q75": float(fold_df["rmse"].quantile(0.75)),
        "r2_fold_median": float(fold_df["r2"].median()), "r2_fold_min": float(fold_df["r2"].min()),
        "r2_fold_max": float(fold_df["r2"].max()),
        "n_oof": int(len(oof)),
    }
    s.update({f"cls_{k}": v for k, v in
              screening_metrics(oof["y"], oof["pred"], oof["sigma"].values, floor_log).items()})
    return s
