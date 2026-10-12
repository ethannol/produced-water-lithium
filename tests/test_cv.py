import numpy as np
import pandas as pd
import pytest

from pwlithium import cv, features


def test_leave_one_group_out_never_leaks():
    groups = np.array(["a"] * 25 + ["b"] * 30 + ["c"] * 5 + ["d"] * 20)
    folds = cv.leave_one_group_out(groups, min_size=20)
    assert [f[0] for f in folds] == ["a", "b", "d"]  # c is too small to be a test fold
    for name, tr, te in folds:
        assert set(groups[te]) == {name}
        assert name not in set(groups[tr])
        assert len(tr) + len(te) == len(groups)
        cv.assert_no_leak(groups, tr, te)
    with pytest.raises(AssertionError):
        cv.assert_no_leak(groups, np.arange(10), np.arange(5, 15))


def test_random_group_folds_keep_groups_whole():
    groups = np.repeat(np.arange(37), 3)
    folds = cv.random_group_folds(groups, 5, seed=0)
    seen = np.zeros(len(groups), int)
    for tr, te in folds:
        assert not set(groups[tr]) & set(groups[te])
        seen[te] += 1
    assert (seen == 1).all()


def _synthetic(n=600, seed=0):
    rng = np.random.default_rng(seed)
    na, k, ca, mg, cl = (10 ** rng.uniform(2, 5, n) for _ in range(5))
    depth = 10 ** rng.uniform(3, 4, n)
    # salinity rises with depth and with the Ca share of the cations (a brine-like pattern)
    tds = 10 ** (2.0 + 0.9 * np.log10(depth) + 0.5 * np.log10(ca / (na + k + ca + mg)) + rng.normal(0, 0.1, n))
    w = pd.DataFrame({"Na": na, "K": k, "Ca": ca, "Mg": mg, "Cl": cl, "TDS": tds, "depth_mid_ft": depth,
                      "PLAYTYPE": rng.choice(["Sedimentary", "Shale"], n), "ERA": rng.choice(["Paleozoic", None], n)})
    w["Li"] = 10 ** (np.log10(w["TDS"]) - 3 + rng.normal(0, 0.1, n))
    return w


def test_positive_control_beats_mean_predictor():
    w = _synthetic()
    x = features.build_features(w, drop_tds=True)
    y = features.target(w, "TDS").values
    groups = np.arange(len(w))
    folds = [(str(i), tr, te) for i, (tr, te) in enumerate(cv.random_group_folds(groups, 3, 0))]
    fold_df, oof = cv.evaluate("hgb", x, y, groups, folds, floor_log=np.log10(1e5))
    s = cv.summarise(fold_df, oof, np.log10(1e5))
    mean_rmse = cv.rmse(oof["y"], np.full(len(oof), oof["y"].mean()))
    assert s["rmse_pooled"] < 0.5 * mean_rmse
    assert s["r2_pooled"] > 0.8
    assert len(oof) == len(w)


def test_metrics_hand_computed():
    y = np.array([1.0, 2.0, 3.0, 4.0])
    p = np.array([1.0, 2.0, 3.0, 2.0])
    assert cv.rmse(y, p) == pytest.approx(1.0)
    assert cv.mae(y, p) == pytest.approx(0.5)
    assert cv.r2(y, p) == pytest.approx(1 - 4 / 5)
    m = cv.screening_metrics(y, p, sigma=0.5, floor_log=2.5)
    assert m["n_pos"] == 2 and m["n_pred_pos"] == 1 and m["precision"] == 1.0 and m["recall"] == 0.5
