import numpy as np
import pandas as pd

from pwlithium import screen


def test_screening_rule_hand_computed():
    li = pd.Series([150.0, 150.0, 90.0, 400.0, 100.0, 120.0])
    mg = pd.Series([1000.0, 2000.0, 100.0, np.nan, 1000.0, 1300.0])
    # Mg/Li: 6.67 pass, 13.3 fail, Li below floor fail, no Mg fail, 10.0 exactly passes, 10.83 fails
    assert screen.passes_screen(li, mg, 100, 10).tolist() == [True, False, False, False, True, False]
    assert screen.passes_screen(li, mg, 100, 20).tolist() == [True, True, False, False, True, True]
    tds = pd.Series([2e5, 2e5, 2e5, 2e5, 5e4, 2e5])
    assert screen.passes_screen(li, mg, 100, 10, tds, 1e5).tolist() == [True, False, False, False, False, False]


def test_group_table_counts():
    w = pd.DataFrame({
        "BASIN": ["X"] * 4 + ["Y"] * 2,
        "IDDB": ["d1", "d1", "d2", "d2", "d3", "d3"],
        "Li": [200.0, 50.0, 300.0, 10.0, 1.0, np.nan],
        "Mg": [400.0, 400.0, 6000.0, 10.0, 10.0, 1.0],
        "TDS": [2e5] * 6, "n_rows": [1] * 6,
        "sg_estimated": [False] * 6, "coord_approx": [False] * 6, "balanced_by_construction": [False] * 6,
    })
    w["mg_li"] = w["Mg"] / w["Li"]
    t = screen.group_table(w, "BASIN", min_wells=3, n_boot=50).set_index("BASIN")
    assert t.loc["X", "n_wells"] == 4 and t.loc["X", "n_datasets"] == 2
    assert t.loc["X", "n_pass"] == 1  # 200 passes (ratio 2); 300 fails (ratio 20)
    assert t.loc["X", "frac_above_floor"] == 0.5
    assert t.loc["Y", "n_wells"] == 1 and not t.loc["Y", "ranked"]


def test_clustered_bootstrap_wider_than_naive_with_within_dataset_correlation():
    rng = np.random.default_rng(1)
    # five datasets, each with a strong dataset-level offset: wells within a dataset are alike
    offsets = np.array([0.5, 1.0, 1.5, 2.0, 2.5])
    li = np.concatenate([10 ** (o + rng.normal(0, 0.05, 40)) for o in offsets])
    clusters = np.repeat(np.arange(5), 40)
    ok = li >= 100
    clustered = screen.cluster_bootstrap(li, ok, clusters, n_boot=400, seed=3)
    naive = screen.naive_bootstrap(li, ok, n_boot=400, seed=3)
    assert clustered["median_hi"] - clustered["median_lo"] > 2 * (naive["median_hi"] - naive["median_lo"])
    assert clustered["frac_hi"] - clustered["frac_lo"] > naive["frac_hi"] - naive["frac_lo"]
    assert naive["median_lo"] <= naive["median_li"] <= naive["median_hi"]


def test_robustness_detects_moved_basin():
    def tab(names, meds):
        return pd.DataFrame({"BASIN": names, "median_li": meds, "median_lo": [m * 0.9 for m in meds],
                             "median_hi": [m * 1.1 for m in meds], "ranked": True})
    a = tab(list("ABCDEF"), [100, 80, 60, 40, 20, 10])
    b = tab(list("ABCDEF"), [100, 80, 60, 40, 10, 20])  # E and F swap: not in top 5 order of separable pairs?
    r = screen.robustness(a, b, "BASIN")
    assert r["top5_overlap"] == 4 and r["moved"] == ["E", "F"]
    assert r["n_reversed_pairs"] == 1 and not r["robust"]
    assert screen.robustness(a, a, "BASIN")["robust"]
