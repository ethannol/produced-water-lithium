"""Held-domain reliability with support and Wilson binomial intervals."""
import numpy as np
import pandas as pd
from scipy.stats import norm


def domain_reliability(oof, domain, floor_log=2., bins=5):
    rows = []
    for label, group in oof.groupby(domain):
        prob = norm.sf((floor_log-group.pred.to_numpy()) / np.maximum(group.sigma.to_numpy(), 1e-6))
        truth = group.y.to_numpy() >= floor_log
        assignment = np.minimum((prob*bins).astype(int), bins-1)
        for b in range(bins):
            mask = assignment == b
            n = int(mask.sum())
            if not n:
                continue
            k = int(truth[mask].sum())
            rate = k/n
            z = norm.ppf(.975)
            center = (rate+z*z/(2*n))/(1+z*z/n)
            half = z*np.sqrt(rate*(1-rate)/n+z*z/(4*n*n))/(1+z*z/n)
            rows.append(dict(domain=str(label), bin=b, n=n, n_positive=k,
                             mean_probability=float(prob[mask].mean()), observed=rate,
                             observed_lo=center-half, observed_hi=center+half))
    return pd.DataFrame(rows)
