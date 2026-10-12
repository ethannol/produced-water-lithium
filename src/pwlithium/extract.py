"""Deterministic extract of the needed columns from the NPWGD v3.0 workbook.

Reads the 80 MB xlsx once (openpyxl, read-only, values only) and writes
`data/raw/npwgd_v3_extract.csv` with a fixed column order. Values are written as
the workbook holds them: empty cell -> empty field, numbers -> shortest round-trip
repr, text unchanged. No cleaning, no renaming, no unit change happens here.
"""

from __future__ import annotations

import csv
from pathlib import Path

import openpyxl

COLUMNS = [
    # identity, provenance
    "IDUSGS", "IDORIG", "IDDB", "SOURCE", "REFERENCE", "REMARKS",
    # classification
    "PLAYTYPE", "WELLTYPE", "BASIN", "PROVINCE", "REGION", "FORMATION", "FORMSIMPLE",
    "GROUP", "MEMBER", "ERA", "PERIOD", "EPOCH", "LITHOLOGY",
    # location
    "STATE", "COUNTY", "FIELD", "LATITUDE", "LONGITUDE", "COORDAPX", "COORDNEW",
    # well
    "WELLNAME", "API", "NWIS", "DATECOMP", "DEPTHUPPER", "DEPTHLOWER", "ELEVATION",
    # time, method
    "TIMESERIES", "DAY", "DATESAMPLE", "DATEANALYS", "METHOD", "LAB",
    # physical
    "TEMP", "SG", "SPGRAV", "PH", "COND", "UNITSORIG",
    # TDS
    "TDS", "TDSLAB", "TDSCALC", "TDSDESC",
    # chemistry (mg/L)
    "Li", "Na", "K", "Ca", "Mg", "Sr", "Ba", "B", "Cl", "Br", "I", "SO4", "HCO3", "CO3",
    "ALKALINITY", "FeTot", "Si", "KNa",
    # quality
    "CHARGEBAL",
]


def _cell(v: object) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return repr(v)
    return str(v)


def extract(xlsx: Path, csv_path: Path, columns: list[str] = COLUMNS) -> int:
    """Write the extract; return the number of data rows written."""
    wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    rows = ws.iter_rows(values_only=True)
    header = [str(h) for h in next(rows)]
    idx = [header.index(c) for c in columns]  # KeyError-like failure if a column is absent
    n = 0
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(columns)
        for r in rows:
            if all(v is None for v in r):
                continue
            w.writerow([_cell(r[i]) for i in idx])
            n += 1
    wb.close()
    return n


def dictionary_to_csv(xlsx: Path, csv_path: Path) -> int:
    wb = openpyxl.load_workbook(xlsx, read_only=True, data_only=True)
    ws = wb.worksheets[0]
    n = 0
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        for r in ws.iter_rows(values_only=True):
            if all(v is None for v in r):
                continue
            w.writerow([_cell(v) for v in r])
            n += 1
    wb.close()
    return n
