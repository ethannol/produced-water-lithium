import csv

import openpyxl

from pwlithium.extract import COLUMNS, extract


def test_extract_row_count_and_columns(tmp_path):
    header = ["JUNK1", *COLUMNS, "JUNK2"]  # extra columns must be dropped, order fixed by COLUMNS
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(header)
    for i in range(7):
        row = {c: None for c in header}
        row["IDUSGS"] = i + 1
        row["IDDB"] = "SYN"
        row["Li"] = 1.5 * (i + 1) if i % 2 == 0 else None  # blanks stay blank
        row["REMARKS"] = "text, with comma" if i == 0 else None
        ws.append([row[c] for c in header])
    ws.append([None] * len(header))  # fully empty trailing row is skipped
    p = tmp_path / "syn.xlsx"
    wb.save(p)
    out = tmp_path / "out.csv"
    n = extract(p, out)
    assert n == 7
    with out.open(newline="") as fh:
        rows = list(csv.reader(fh))
    assert rows[0] == COLUMNS
    assert len(rows) == 8
    li = rows[0].index("Li")
    assert rows[1][li] == "1.5" and rows[2][li] == ""
    assert rows[1][rows[0].index("REMARKS")] == "text, with comma"
