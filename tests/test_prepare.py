import numpy as np
import pandas as pd

from pwlithium import prepare


def _rows():
    base = {c: np.nan for c in prepare.NUMERIC}
    recs = []
    spec = [
        # IDUSGS, IDDB, API, WELLNAME, lat, lon, depth, Li, Mg, CHARGEBAL, COORDAPX, PLAYTYPE, WELLTYPE, STATE, FORMATION, SG
        (1, "A", "100", "W1", 30.0, -90.0, 5000, 10.0, 100.0, 1.0, None, "Sedimentary", "Conventional Hydrocarbon", "Texas", "Smackover", 1.1),
        (2, "A", "100", "W1", 30.0, -90.0, 5000, 30.0, 300.0, -2.0, None, "Sedimentary", "Conventional Hydrocarbon", "Texas", "Smackover", 1.1),
        (3, "A", "100", "W1", 30.0, -90.0, 5000, 20.0, np.nan, 0.0, None, "Sedimentary", "Conventional Hydrocarbon", "Texas", "Smackover", 1.1),
        (4, "A", "101", "W2", 30.1, -90.1, 6000, 150.0, 300.0, 12.0, None, "Sedimentary", "Conventional Hydrocarbon", "Texas", "Smackover", 1.2),
        (5, "B", None, "W1", 31.0, -91.0, 7000, 5.0, 50.0, 3.0, None, "Shale", "Shale Gas", "Louisiana", "Haynesville", 1.05),
        (6, "B", None, None, 31.5, -91.5, 7000, np.nan, 50.0, 25.0, "Approximate location", "Shale", "Shale Gas", "Louisiana", "Haynesville", 1.05),
        (7, "B", None, None, 31.5, -91.5, 7000, 2.0, 50.0, np.nan, "Approximate location", "Shale", "Shale Gas", "Louisiana", "Haynesville", 1.05),
        (8, "C", "200", None, 40.0, -80.0, 2000, 1.0, 10.0, 0.0, None, "Geothermal", "Geothermal", "Nevada", "Granite", 1.0),
        (9, "C", "201", None, 40.0, -80.0, 2000, 1.0, 10.0, 0.0, None, "Sedimentary", "Conventional Hydrocarbon", "Ontario", "Salina", 1.0),
        (10, "C", "202", None, 40.0, -80.0, 2000, 1.0, 10.0, 0.0, None, "Sedimentary", "Injection", "Texas", "Injection Water", 1.0),
        (11, "C", "203", None, 40.0, -80.0, 2000, 1.0, 10.0, 0.0, None, "Sedimentary", "Conventional Hydrocarbon", "Texas", "Frio", 1.5),
    ]
    for s in spec:
        r = dict(base)
        r.update(dict(zip(["IDUSGS", "IDDB", "API", "WELLNAME", "LATITUDE", "LONGITUDE", "DEPTHUPPER", "Li", "Mg",
                           "CHARGEBAL", "COORDAPX", "PLAYTYPE", "WELLTYPE", "STATE", "FORMATION", "SG"], s, strict=True)))
        r.update({"BASIN": "Gulf Coast", "FORMSIMPLE": r["FORMATION"], "ERA": "Mesozoic", "PERIOD": "Jurassic",
                  "UNITSORIG": "mg/L", "TDSDESC": "reported measured", "DATESAMPLE": "1990-01-01", "TDS": 100000.0,
                  "SPGRAV": np.nan})
        recs.append(r)
    df = pd.DataFrame(recs)
    df["IDUSGS"] = df["IDUSGS"].astype("int64")
    return prepare.derive(df)


def test_missing_is_missing_and_present_is_detected():
    df = _rows()
    assert df["li_measured"].tolist() == [True, True, True, True, True, False, True, True, True, True, True]
    assert np.isnan(df.loc[df["IDUSGS"] == 6, "Li"].iloc[0])
    assert df.loc[df["IDUSGS"] == 3, "mg_li"].isna().all()  # no Mg: ratio undefined, never zero
    assert df["sg_estimated"].all()  # SPGRAV missing everywhere in the fixture
    assert df.loc[df["CHARGEBAL"] == 0.0, "balanced_by_construction"].all()


def test_inclusion_rules_log_each_exclusion():
    kept, log = prepare.apply_inclusion(_rows())
    assert set(kept["IDUSGS"]) == {1, 2, 3, 4, 5, 6, 7}
    removed = dict(zip(log["step"], log["rows_removed"], strict=True))
    assert removed["playtype_not_produced_water"] == 1
    assert removed["welltype_injection_water_co2"] == 1
    assert removed["formation_injected_fluid"] == 0  # row 10 already left under the welltype rule
    assert removed["non_us_state"] == 1
    assert removed["sg_out_of_range"] == 1
    assert log["rows_after"].iloc[-1] == 7


def test_charge_balance_filter_removes_exactly_intended_rows():
    kept, _ = prepare.apply_inclusion(_rows())
    f10 = prepare.charge_balance_filter(kept, 10)
    assert set(f10["IDUSGS"]) == {1, 2, 3, 5}  # 4 (12%), 6 (25%) and 7 (missing) go
    f15 = prepare.charge_balance_filter(kept, 15)
    assert set(f15["IDUSGS"]) == {1, 2, 3, 4, 5}
    assert len(prepare.charge_balance_filter(kept, None)) == 7


def test_dedup_collapses_planted_repeat_without_touching_distinct_wells():
    kept, _ = prepare.apply_inclusion(_rows())
    keyed = prepare.well_key(kept)
    wells = prepare.collapse_wells(keyed)
    # rows 1,2,3 share dataset A + API 100 -> one well with the median Li of 10, 30, 20
    w1 = wells.loc[wells["well_id"] == "A|api:100"].iloc[0]
    assert w1["n_rows"] == 3 and w1["Li"] == 20.0 and w1["Mg"] == 200.0
    assert w1["key_class"] == "api"
    # W1 in dataset B is a different well than W1 in dataset A
    assert "B|name:W1" in set(wells["well_id"])
    # rows 6 and 7: approximate coordinates, no identifier -> each its own well
    assert {"B|row:6", "B|row:7"} <= set(wells["well_id"])
    assert len(wells) == 5
    assert wells["n_rows"].sum() == len(keyed)
