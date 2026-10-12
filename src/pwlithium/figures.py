"""Matplotlib figures. One palette (blue, orange, aqua categorical slots; a blue
sequential ramp; gray for context), thin marks, direct labels, no dual axes."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
GRAY, INK, MUTED = "#c3c2b7", "#0b0b0b", "#52514e"
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white", "axes.edgecolor": GRAY,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": "#ecebe7", "grid.linewidth": 0.6, "axes.titleweight": "semibold",
    "axes.titlesize": 11, "axes.labelsize": 9.5, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
    "legend.fontsize": 8.5, "legend.frameon": False, "font.size": 9.5, "text.color": INK,
    "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED, "savefig.dpi": 160,
})


def _save(fig, path):
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def coverage(by_basin_decade: pd.DataFrame, basins: list[str], path) -> None:
    """Where lithium was measured versus not, by basin (rows) and decade (columns)."""
    d = by_basin_decade.copy()
    d["decade"] = d["decade"].fillna(-1).astype(int)
    d = d.loc[d["BASIN"].isin(basins)]
    decades = sorted(d["decade"].unique())
    labels = ["no date" if x < 0 else f"{x}s" for x in decades]
    rows = len(basins)
    fig, axes = plt.subplots(1, 2, figsize=(10, 0.32 * rows + 1.6), sharey=True,
                             gridspec_kw={"width_ratios": [1.3, 1]})
    share = d.pivot_table(index="BASIN", columns="decade", values="sum", aggfunc="sum").reindex(basins)
    total = d.pivot_table(index="BASIN", columns="decade", values="size", aggfunc="sum").reindex(basins)
    frac = (share / total).reindex(columns=decades)
    ax = axes[0]
    cmap = matplotlib.colors.ListedColormap(SEQ)
    im = ax.imshow(frac.values, aspect="auto", cmap=cmap, vmin=0, vmax=1)
    ax.set_xticks(range(len(decades)), labels, rotation=45, ha="right")
    ax.set_yticks(range(rows), basins)
    ax.grid(False)
    ax.set_title("Share of rows with Li measured, by basin and decade")
    for i in range(rows):
        for j in range(len(decades)):
            n = total.iloc[i, j] if j < total.shape[1] else np.nan
            if pd.notna(n) and n > 0:
                v = frac.iloc[i, j]
                ax.text(j, i, f"{v:.0%}" if n >= 20 else "·", ha="center", va="center", fontsize=6.5,
                        color="white" if v > 0.55 else INK)
    fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02, label="share with Li")
    ax = axes[1]
    tot = total.sum(axis=1)
    li = share.sum(axis=1)
    y = np.arange(rows)
    ax.barh(y, tot, color=GRAY, height=0.62, label="rows")
    ax.barh(y, li, color=BLUE, height=0.62, label="rows with Li")
    ax.set_xscale("log")
    ax.set_title("Rows and rows with Li (log scale)")
    ax.invert_yaxis()
    ax.legend(loc="lower right")
    for i in range(rows):
        ax.text(tot.iloc[i] * 1.15, i, f"{int(li.iloc[i])}/{int(tot.iloc[i])}", va="center",
                fontsize=7, color=MUTED)
    _save(fig, path)


def basin_ranking(primary: pd.DataFrame, adjusted: pd.DataFrame, floor: float, path) -> None:
    """Median Li with 95% cluster bootstrap intervals, primary vs without Li-focused datasets."""
    p = primary.loc[primary["ranked"]].sort_values("median_li", ascending=True).reset_index(drop=True)
    a = adjusted.set_index("BASIN")
    n = len(p)
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 0.34 * n + 1.8), sharey=True,
                             gridspec_kw={"width_ratios": [1.5, 1]})
    y = np.arange(n)
    ax = axes[0]
    ax.axvline(floor, color=ORANGE, lw=1, ls="--")
    ax.text(floor, n - 0.4, f" floor {floor:g} mg/L", color=ORANGE, fontsize=8, va="top")
    for i, r in p.iterrows():
        ax.plot([r["median_lo"], r["median_hi"]], [i + 0.15, i + 0.15], color=BLUE, lw=2, solid_capstyle="round")
        ax.plot(r["median_li"], i + 0.15, "o", color=BLUE, ms=5)
        if r["BASIN"] in a.index and pd.notna(a.loc[r["BASIN"], "median_lo"]):
            q = a.loc[r["BASIN"]]
            ax.plot([q["median_lo"], q["median_hi"]], [i - 0.15, i - 0.15], color=ORANGE, lw=2, solid_capstyle="round")
            ax.plot(q["median_li"], i - 0.15, "o", color=ORANGE, ms=5, mfc="white")
    ax.set_xscale("log")
    labels = [f"{b}  (n={int(k)}, {int(d)} ds)"
              for b, k, d in zip(p["BASIN"], p["n_wells"], p["n_datasets"], strict=True)]
    ax.set_yticks(y, labels)
    ax.set_xlabel("median well Li, mg/L (95% cluster bootstrap)")
    ax.set_title("Median lithium by basin")
    ax.plot([], [], "o-", color=BLUE, label="primary")
    ax.plot([], [], "o-", color=ORANGE, mfc="white", label="without Li-focused datasets")
    ax.legend(loc="lower right")
    ax = axes[1]
    for i, r in p.iterrows():
        ax.plot([r["frac_lo"], r["frac_hi"]], [i, i], color=BLUE, lw=2, solid_capstyle="round")
        ax.plot(r["frac_pass"], i, "o", color=BLUE, ms=5)
    ax.set_xlim(-0.02, 1.02)
    ax.set_xlabel("fraction of wells passing Li >= floor and Mg/Li <= 10")
    ax.set_title("Screened fraction")
    _save(fig, path)


def mgli_vs_li(lw: pd.DataFrame, floor: float, ceiling: float, path, top_basins: list[str]) -> None:
    fig, ax = plt.subplots(figsize=(8, 6))
    d = lw.loc[lw["mg_li"].notna()]
    other = d.loc[~d["BASIN"].isin(top_basins)]
    ax.scatter(other["Li"], other["mg_li"], s=9, color=GRAY, alpha=0.6, lw=0, label="other basins")
    for b, c in zip(top_basins, [BLUE, ORANGE, AQUA], strict=False):
        g = d.loc[d["BASIN"] == b]
        ax.scatter(g["Li"], g["mg_li"], s=14, color=c, alpha=0.8, lw=0, label=f"{b} (n={len(g)})")
    ax.set_xscale("log")
    ax.set_yscale("log")
    xmax = d["Li"].max() * 2
    ax.fill_betweenx([d["mg_li"].min() / 2, ceiling], floor, xmax, color=AQUA, alpha=0.08, lw=0)
    ax.axvline(floor, color=INK, lw=0.8, ls="--")
    ax.axhline(ceiling, color=INK, lw=0.8, ls="--")
    ax.text(floor * 1.1, d["mg_li"].min(), f"passes: Li >= {floor:g} mg/L, Mg/Li <= {ceiling:g}",
            fontsize=8, color=MUTED)
    ax.set_xlabel("well Li, mg/L")
    ax.set_ylabel("Mg/Li mass ratio")
    ax.set_title("Mg/Li against lithium, one point per well")
    ax.legend(loc="upper right")
    _save(fig, path)


def missingness(rows: pd.DataFrame, path) -> None:
    m, u = rows.loc[rows["li_measured"]], rows.loc[~rows["li_measured"]]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
    panels = [(axes[0], "TDS", "TDS, mg/L", 2, 6), (axes[1], "depth_mid_ft", "depth midpoint, ft", 2, 4.5)]
    for ax, col, lab, lo, hi in panels:
        bins = np.linspace(lo, hi, 36)
        for g, c, name in [(u, GRAY, "Li not measured"), (m, BLUE, "Li measured")]:
            v = np.log10(g[col].where(g[col] > 0)).dropna()
            ax.hist(v, bins=bins, density=True, histtype="step", lw=1.8, color=c, label=f"{name} (n={len(v)})")
        ax.set_xlabel(f"log10 {lab}")
        ax.set_ylabel("density")
        ax.legend(loc="upper left")
    ax = axes[2]
    dec = rows.groupby("decade", dropna=True)["li_measured"].agg(["mean", "size"])
    ax.bar(dec.index.astype(int), dec["mean"], width=8, color=BLUE)
    for x, (s, n) in zip(dec.index.astype(int), dec[["mean", "size"]].values, strict=True):
        ax.text(x, s + 0.01, f"{int(n)}", ha="center", fontsize=6.5, color=MUTED)
    ax.set_xlabel("sampling decade (row counts above bars)")
    ax.set_ylabel("share of rows with Li")
    axes[0].set_title("Rows with and without lithium")
    _save(fig, path)


def headline_errors(folds: pd.DataFrame, target_sd: float, path, title: str, control: pd.DataFrame | None = None,
                    control_sd: float | None = None) -> None:
    """RMSE per fold under the three protocols, both models, with the mean-predictor line."""
    protos = [("random", "random 5-fold\nby well (x3)"), ("lodo", "leave-one-\ndataset-out"),
              ("lobo", "leave-one-\nbasin-out")]
    panels = [("Li", folds, target_sd)]
    if control is not None:
        panels.append(("TDS (positive control)", control, control_sd))
    fig, axes = plt.subplots(1, len(panels), figsize=(5.2 * len(panels), 4.2), sharey=False)
    axes = np.atleast_1d(axes)
    rng = np.random.default_rng(0)
    for ax, (name, f, sd) in zip(axes, panels, strict=True):
        for j, (p, _lab) in enumerate(protos):
            for k, (model, c) in enumerate([("ridge", ORANGE), ("hgb", BLUE)]):
                g = f.loc[(f.protocol == p) & (f.model == model), "rmse"]
                x = j + (k - 0.5) * 0.3
                ax.scatter(x + rng.uniform(-0.06, 0.06, len(g)), g, s=16, color=c, alpha=0.65, lw=0)
                ax.plot([x - 0.1, x + 0.1], [g.median()] * 2, color=c, lw=2.2)
        ax.axhline(sd, color=MUTED, lw=1, ls=":")
        ax.text(2.45, sd, " mean\n predictor", fontsize=7.5, color=MUTED, va="center")
        ax.set_xticks(range(3), [lab for _, lab in protos], fontsize=8.5)
        ax.set_ylabel(f"held-out RMSE, log10 {name.split(' ')[0]}")
        ax.set_title(name)
        ax.set_xlim(-0.6, 2.9)
    axes[0].plot([], [], "s", color=ORANGE, label="ridge")
    axes[0].plot([], [], "s", color=BLUE, label="gradient boosting")
    axes[0].legend(loc="upper left")
    fig.suptitle(title, fontsize=11, fontweight="semibold")
    _save(fig, path)


def calibration(tables: dict[str, pd.DataFrame], path) -> None:
    fig, ax = plt.subplots(figsize=(5.2, 4.6))
    ax.plot([0, 1], [0, 1], color=GRAY, lw=1)
    for (name, t), c in zip(tables.items(), [BLUE, ORANGE, AQUA], strict=False):
        t = t.loc[t["n"] > 0]
        ax.plot(t["mean_prob"], t["observed"], "o-", color=c, lw=1.8, ms=5, label=name)
        for _, r in t.iterrows():
            ax.text(r["mean_prob"], r["observed"] + 0.03, str(int(r["n"])), fontsize=6, color=MUTED, ha="center")
    ax.set_xlabel("predicted probability Li >= 100 mg/L")
    ax.set_ylabel("observed share >= 100 mg/L")
    ax.set_title("Calibration of the screening probability (boosted model)")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.08)
    ax.legend(loc="upper left")
    _save(fig, path)


def well_map(lw: pd.DataFrame, floor: float, path) -> None:
    """Lithium wells on a plain lon/lat frame: exact coordinates as points, approximate ones
    as hollow markers, no basemap (none is bundled; the coordinates do not support finer)."""
    fig, ax = plt.subplots(figsize=(10, 6))
    d = lw.loc[(lw["LONGITUDE"] < -60) & (lw["LONGITUDE"] > -170) & (lw["LATITUDE"] > 20)]
    ex, ap = d.loc[~d["coord_approx"]], d.loc[d["coord_approx"]]
    ax.scatter(ex["LONGITUDE"], ex["LATITUDE"], s=6, color=GRAY, lw=0, alpha=0.7,
               label=f"Li < {floor:g} mg/L, exact location")
    ax.scatter(ap["LONGITUDE"], ap["LATITUDE"], s=14, facecolors="none", edgecolors=GRAY, lw=0.6,
               label="approximate location (centroid)")
    hi = ex.loc[ex["Li"] >= floor]
    ax.scatter(hi["LONGITUDE"], hi["LATITUDE"], s=12, color=BLUE, lw=0, label=f"Li >= {floor:g} mg/L, exact location")
    hia = ap.loc[ap["Li"] >= floor]
    ax.scatter(hia["LONGITUDE"], hia["LATITUDE"], s=22, facecolors="none", edgecolors=BLUE, lw=0.9,
               label=f"Li >= {floor:g} mg/L, approximate")
    ax.set_aspect(1.25)
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    ax.set_title("Wells with lithium measured (no basemap; approximate locations are county, field or basin centroids)")
    ax.legend(loc="lower left", markerscale=1.5)
    _save(fig, path)
