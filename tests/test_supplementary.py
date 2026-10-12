import pandas as pd

from pwlithium.domain_calibration import domain_reliability
from pwlithium.screen_coverage import screening_coverage


def test_missing_mg_is_unknown_only_when_li_floor_passes():
    wells = pd.DataFrame(dict(BASIN=["x"]*4, Li=[120., 120., 120., 20.], Mg=[100., None, 2000., None]))
    result = screening_coverage(wells).iloc[0]
    assert (result.n_pass, result.n_unknown, result.n_fail) == (1, 1, 2)
    assert (result.fraction_lower, result.fraction_upper) == (.25, .5)


def test_domain_bins_keep_support_and_uncertainty():
    oof = pd.DataFrame(dict(BASIN=["x", "x", "y"], pred=[2., 2., 1.], sigma=[.2]*3, y=[3., 1., 1.]))
    result = domain_reliability(oof, "BASIN")
    assert result.n.sum() == 3
    assert ((result.observed_lo <= result.observed) & (result.observed_hi >= result.observed)).all()


def test_all_unknown_abstains_from_evaluable_fraction():
    wells = pd.DataFrame(dict(BASIN=["x"], Li=[120.], Mg=[float("nan")]))
    result = screening_coverage(wells).iloc[0]
    assert result.fraction_lower == 0
    assert result.fraction_upper == 1
    assert pd.isna(result.evaluable_fraction)
