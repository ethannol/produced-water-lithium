"""Supplementary screening coverage without redefining the frozen denominator."""
import pandas as pd


def screening_coverage(wells, floor=100., ceiling=10.):
    rows = []
    data = wells.loc[wells.Li.notna()]
    for basin, group in data.groupby("BASIN"):
        eligible = group.Li >= floor
        unknown = eligible & group.Mg.isna()
        passed = eligible & group.Mg.notna() & (group.Mg / group.Li <= ceiling)
        n = len(group)
        rows.append(dict(BASIN=basin, n_li_wells=n, n_mg_known=int(group.Mg.notna().sum()),
                         n_pass=int(passed.sum()), n_unknown=int(unknown.sum()),
                         n_fail=int((~passed & ~unknown).sum()),
                         fraction_lower=float(passed.sum()/n),
                         fraction_upper=float((passed.sum()+unknown.sum())/n),
                         evaluable_fraction=(float(passed.sum()/(n-unknown.sum()))
                                             if n > unknown.sum() else None)))
    return pd.DataFrame(rows)
