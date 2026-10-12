"""Network step, deliberately not numbered: download the NPWGD v3.0 archive, write the
deterministic extract and the manifest. Run once; re-freeze afterwards. The numbered
pipeline (`cairn run`) never touches the network or the archive."""

import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

from pwlithium import acquire
from pwlithium.extract import COLUMNS, dictionary_to_csv, extract

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
A = acquire.ARCHIVE

if "--no-download" not in sys.argv:
    acquire.download()
downloaded = None
hp = A / "USGS_NPWGDv3_excel.xlsx.headers"
if hp.is_file():
    downloaded = acquire.parse_headers(hp.read_text()).get("date")
for name, spec in acquire.FILES.items():
    size = (A / name).stat().st_size
    if size != spec["expected_bytes"]:
        raise SystemExit(f"{name}: {size} bytes, expected {spec['expected_bytes']}")

RAW.mkdir(parents=True, exist_ok=True)
n = extract(A / "USGS_NPWGDv3_excel.xlsx", RAW / "npwgd_v3_extract.csv")
nd = dictionary_to_csv(A / "USGS_NPWGDv3_data_dictionary.xlsx", RAW / "data_dictionary.csv")
shutil.copyfile(A / "USGS_NPWGDv3_metadata.xml", RAW / "USGS_NPWGDv3_metadata.xml")
shutil.copyfile(A / "version_history.txt", RAW / "version_history.txt")
raw_files = ["npwgd_v3_extract.csv", "data_dictionary.csv", "USGS_NPWGDv3_metadata.xml", "version_history.txt"]
manifest = acquire.write_manifest(
    {
        "written_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "source_sheet": "Sheet1",
        "rows": n,
        "columns": COLUMNS,
        "n_columns": len(COLUMNS),
        "dictionary_rows": nd,
        "raw_sha256": {f"data/raw/{f}": acquire.sha256(RAW / f) for f in raw_files},
    },
    downloaded_at_utc=downloaded,
)
print(f"extract: {n} rows x {len(COLUMNS)} columns; manifest written")
