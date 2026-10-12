"""The two pre-registered models and their small fixed grids."""

from __future__ import annotations

from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RIDGE_GRID = [{"alpha": a} for a in (0.01, 0.1, 1.0, 10.0, 100.0)]
HGB_GRID = [
    {"learning_rate": lr, "max_leaf_nodes": leaves}
    for lr in (0.05, 0.1) for leaves in (7, 15, 31)
]
GRIDS = {"ridge": RIDGE_GRID, "hgb": HGB_GRID}


def make_model(name: str, params: dict, seed: int = 0):
    if name == "ridge":
        return Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("ridge", Ridge(alpha=params["alpha"])),
        ])
    if name == "hgb":
        return Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("hgb", HistGradientBoostingRegressor(
                learning_rate=params["learning_rate"], max_leaf_nodes=params["max_leaf_nodes"],
                max_iter=300, min_samples_leaf=20, early_stopping=False, random_state=seed)),
        ])
    raise ValueError(name)
