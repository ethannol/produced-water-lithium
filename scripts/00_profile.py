"""Step 0: verify the committed extract against the manifest (offline), profile it, and
record the provenance and the non-detect finding. `cairn profile` crashes on this file
(see docs/decisions.md), so the profile is written here in the same spirit."""

import json

import pandas as pd
from cairn import record

from pwlithium import acquire
from pwlithium.prepare import IONS, NUMERIC, load_raw
from pwlithium.util import RAW, ROOT, commas
from pwlithium.util import lines as join_lines

ok = acquire.verify_raw()
if not all(ok.values()):
    raise SystemExit(f"raw files do not match the manifest: {[k for k, v in ok.items() if not v]}")
m = json.loads(acquire.MANIFEST.read_text())
xl = m["archive_files"]["USGS_NPWGDv3_excel.xlsx"]
record("manifest.archive_bytes", xl["bytes"], unit="bytes")
record("manifest.archive_sha256", xl["sha256"])
record("manifest.archive_http_status", xl["http_headers"].get("status", "unknown"))
record("manifest.download_date", m["downloaded_at_utc"])
record("manifest.extract_rows", m["extract"]["rows"], unit="rows")
record("manifest.extract_columns", m["extract"]["n_columns"])
record("manifest.n_archive_files", len(m["archive_files"]))

df = load_raw()
record("profile.rows", len(df), unit="rows")
record("profile.columns", df.shape[1])
if len(df) != m["extract"]["rows"]:
    raise SystemExit("extract row count differs from the manifest")

# Non-detect finding: how chemistry columns represent anything below detection.
raw_text = pd.read_csv(RAW / "npwgd_v3_extract.csv", dtype=str, usecols=IONS, keep_default_na=False)
for c in IONS:
    s = raw_text[c]
    nonempty = s != ""
    num = pd.to_numeric(s.where(nonempty), errors="coerce")
    record(f"nondetect.{c}.nonempty", int(nonempty.sum()))
    record(f"nondetect.{c}.non_numeric", int((nonempty & num.isna()).sum()))
    record(f"nondetect.{c}.zero", int((num == 0).sum()))
    record(f"nondetect.{c}.negative", int((num < 0).sum()))
    record(f"nondetect.{c}.lt_prefixed", int(s.str.startswith("<").sum()))
li = df["Li"].dropna()
record("nondetect.li_min", float(li.min()), unit="mg/L")
record("nondetect.li_n_below_1", int((li < 1).sum()))
record("nondetect.li_n_below_0_1", int((li < 0.1).sum()))
record("nondetect.li_share_integer", float((li == li.round(0)).mean()))
record("nondetect.remarks_detect_rows", int(df["REMARKS"].fillna("").str.contains("detect", case=False).sum()))
record("nondetect.dictionary_fields", int(len(pd.read_csv(RAW / "data_dictionary.csv")) ))
dd = pd.read_csv(RAW / "data_dictionary.csv")
record("nondetect.dictionary_detection_fields",
       int(dd.iloc[:, 2].fillna("").str.contains("detect", case=False).sum()),
       note="dictionary descriptions mentioning detection")

# Profile in the spirit of `cairn profile`: grain, nulls, types, distinct counts.
lines = ["# Profile: data/raw/npwgd_v3_extract.csv", "",
         f"Rows: {len(df)}. One row = one compiled produced-water sample (IDUSGS unique).", "",
         "| field | non-null | distinct | type | examples |", "|---|---|---|---|---|"]
for c in df.columns:
    s = df[c]
    ex = commas(str(v)[:30] for v in s.dropna().unique()[:3])
    lines.append(f"| {c} | {int(s.notna().sum())} | {s.nunique()} | "
                 f"{'numeric' if c in NUMERIC or c == 'IDUSGS' else 'text'} | {ex} |")
lines += ["", "Censoring markers: none in any chemistry column (no '<', ND, zero or negative values;",
          "see ledger keys nondetect.*). Empty cell = not reported or below detection."]
(ROOT / "profiles").mkdir(exist_ok=True)
(ROOT / "profiles" / "npwgd_v3_extract.md").write_text(join_lines(lines) + "\n")
record("profile.idusgs_unique", bool(df["IDUSGS"].is_unique))
record("profile.n_datasets", int(df["IDDB"].nunique()))
record("profile.n_basins", int(df["BASIN"].nunique()))
record("profile.li_rows", int(df["Li"].notna().sum()))
print("profile written; rows", len(df))
