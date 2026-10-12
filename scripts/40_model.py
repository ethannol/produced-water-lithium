"""Step 4: the predictive question. log10 Li from major-ion chemistry, TDS, depth, play type
and era; ridge and gradient boosting; random-by-well, leave-one-dataset-out and
leave-one-basin-out; screening metrics at the floor; positive control on log10 TDS."""

import os

os.environ["OMP_NUM_THREADS"] = "1"  # see docs/decisions.md: thread oversubscription

import numpy as np
import pandas as pd
from cairn import record, split_overlap

from pwlithium import cv, features
from pwlithium.util import DERIVED, FLOOR, MIN_WELLS_BASIN, TABLES, commas

TABLES.mkdir(parents=True, exist_ok=True)
wells = pd.read_csv(DERIVED / "wells_primary.csv", low_memory=False)
FLOOR_LOG = float(np.log10(FLOOR))
MIN_GROUP = MIN_WELLS_BASIN  # pre-registered: groups with >= 20 modelling wells are held out


def protocols(groups_ds: np.ndarray, groups_basin: np.ndarray, groups_well: np.ndarray):
    rnd = []
    for rep in (0, 1, 2):
        rnd += [(f"rep{rep}_fold{i}", tr, te) for i, (tr, te) in
                enumerate(cv.random_group_folds(groups_well, 5, rep))]
    return {
        "random": (rnd, groups_well),
        "lodo": (cv.leave_one_group_out(groups_ds, MIN_GROUP), groups_ds),
        "lobo": (cv.leave_one_group_out(groups_basin, MIN_GROUP), groups_basin),
    }


def run(target_col: str, prefix: str, drop_tds: bool):
    m = features.modelling_mask(wells, target_col)
    w = wells.loc[m].reset_index(drop=True)
    X = features.build_features(w, drop_tds=drop_tds)
    y = features.target(w, target_col).values
    g_well, g_ds, g_basin = w["well_id"].values, w["IDDB"].values, w["BASIN"].values
    record(f"{prefix}.n_wells", len(w))
    record(f"{prefix}.n_features", X.shape[1])
    record(f"{prefix}.target_sd", float(np.std(y)), note=f"SD of log10 {target_col}; RMSE of a mean predictor")
    record(f"{prefix}.n_datasets_heldout", len(cv.leave_one_group_out(g_ds, MIN_GROUP)))
    record(f"{prefix}.n_basins_heldout", len(cv.leave_one_group_out(g_basin, MIN_GROUP)))
    all_folds, oofs = [], []
    for proto, (folds, groups) in protocols(g_ds, g_basin, g_well).items():
        # leakage sensor on the first fold of each protocol (the splitter asserts on every fold)
        _, tr0, te0 = folds[0]
        split_overlap(w.iloc[tr0], w.iloc[te0], key="well_id", quiet=True)
        if proto != "random":
            split_overlap(w.iloc[tr0], w.iloc[te0], key="IDDB" if proto == "lodo" else "BASIN", quiet=True)
        for model in ("ridge", "hgb"):
            fold_df, oof = cv.evaluate(model, X, y, groups, folds, FLOOR_LOG, seed=0)
            s = cv.summarise(fold_df, oof, FLOOR_LOG)
            for k, v in s.items():
                record(f"{prefix}.{proto}.{model}.{k}", v)
            fold_df.insert(0, "model", model)
            fold_df.insert(0, "protocol", proto)
            all_folds.append(fold_df)
            oof = oof.assign(protocol=proto, model=model, well_id=w["well_id"].values[oof["idx"]],
                             IDDB=g_ds[oof["idx"]], BASIN=g_basin[oof["idx"]])
            oofs.append(oof)
            if proto == "random":
                # spread across the three repetitions (pooled RMSE per repetition)
                reps = [cv.rmse(oof.loc[oof["fold"].str.startswith(f"rep{r}"), "y"],
                                oof.loc[oof["fold"].str.startswith(f"rep{r}"), "pred"]) for r in (0, 1, 2)]
                record(f"{prefix}.{proto}.{model}.rmse_rep_min", float(min(reps)))
                record(f"{prefix}.{proto}.{model}.rmse_rep_max", float(max(reps)))
            if model == "hgb" and prefix == "model":
                rel = cv.reliability(oof["y"], oof["pred"], oof["sigma"].values, FLOOR_LOG)
                rel.to_csv(TABLES / f"calibration_hgb_{proto}.csv", index=False)
                nz = rel.loc[rel["n"] > 0]
                record(f"{prefix}.{proto}.hgb.calib_max_gap",
                       float((nz["observed"] - nz["mean_prob"]).abs().max()))
                record(f"{prefix}.{proto}.hgb.calib_n_bins_used", int(len(nz)))
    folds_df = pd.concat(all_folds, ignore_index=True)
    folds_df.to_csv(TABLES / f"cv_folds_{prefix}.csv", index=False)
    oof_df = pd.concat(oofs, ignore_index=True)
    oof_df.to_csv(DERIVED / f"oof_{prefix}.csv", index=False)
    return w, folds_df, oof_df


def main():
    w, folds, oof = run("Li", "model", drop_tds=False)
    if len(w) < 500:
        record("model.verdict", "abstain: fewer than 500 modelling wells")
    else:
        # pre-registered conclusions (boosted model)
        lobo_r2 = folds.loc[(folds.protocol == "lobo") & (folds.model == "hgb")]  # noqa: F841 (per-fold table kept)
        hgb = {p: cv.summarise(folds.loc[(folds.protocol == p) & (folds.model == "hgb")],
                               oof.loc[(oof.protocol == p) & (oof.model == "hgb")], FLOOR_LOG)
               for p in ("random", "lodo", "lobo")}
        useful_out = hgb["lobo"]["r2_pooled"] >= 0.30 and hgb["lobo"]["cls_auc"] >= 0.75
        useful_in = hgb["random"]["r2_pooled"] >= 0.30
        verdict = ("useful out of basin" if useful_out else
                   "useful within basin only" if useful_in else "not usefully predictable")
        record("model.verdict", verdict)
        record("model.rmse_ratio_lobo_random_hgb", hgb["lobo"]["rmse_pooled"] / hgb["random"]["rmse_pooled"])
        record("model.rmse_ratio_lodo_random_hgb", hgb["lodo"]["rmse_pooled"] / hgb["random"]["rmse_pooled"])
        # per-basin held-out table for the report
        lb = folds.loc[(folds.protocol == "lobo") & (folds.model == "hgb")].sort_values("rmse")
        record("model.lobo.hgb.best_basin", str(lb.iloc[0]["fold"]))
        record("model.lobo.hgb.best_basin_rmse", float(lb.iloc[0]["rmse"]))
        record("model.lobo.hgb.best_basin_r2", float(lb.iloc[0]["r2"]))
        record("model.lobo.hgb.worst_basin", str(lb.iloc[-1]["fold"]))
        record("model.lobo.hgb.worst_basin_rmse", float(lb.iloc[-1]["rmse"]))
        record("model.lobo.hgb.worst_basin_r2", float(lb.iloc[-1]["r2"]))
        record("model.lobo.hgb.n_basins_r2_positive", int((lb["r2"] > 0).sum()))
        record("model.lobo.hgb.n_basins_r2_ge_0_3", int((lb["r2"] >= 0.3).sum()))
        ld = folds.loc[(folds.protocol == "lodo") & (folds.model == "hgb")].sort_values("rmse")
        record("model.lodo.hgb.best_dataset", str(ld.iloc[0]["fold"]))
        record("model.lodo.hgb.best_dataset_rmse", float(ld.iloc[0]["rmse"]))
        record("model.lodo.hgb.worst_dataset", str(ld.iloc[-1]["fold"]))
        record("model.lodo.hgb.worst_dataset_rmse", float(ld.iloc[-1]["rmse"]))
        record("model.lodo.hgb.n_datasets_r2_positive", int((ld["r2"] > 0).sum()))
        record("model.lodo.hgb.datasets_r2_negative", commas(ld.loc[ld["r2"] <= 0, "fold"]) or "none")
        # mean bias per held-out basin (systematic over/under prediction)
        bias = (oof.loc[(oof.protocol == "lobo") & (oof.model == "hgb")]
                .groupby("fold").apply(lambda g: float((g["pred"] - g["y"]).mean()), include_groups=False))
        record("model.lobo.hgb.bias_abs_median", float(bias.abs().median()))
        record("model.lobo.hgb.bias_abs_max", float(bias.abs().max()))
        record("model.lobo.hgb.bias_max_basin", str(bias.abs().idxmax()))
    print('done')


if __name__ == '__main__':
    main()
