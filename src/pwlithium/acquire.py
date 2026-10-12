"""Provenance of the USGS National Produced Waters Geochemical Database v3.0 archive.

The 80 MB workbook is downloaded once into `data/archive/npwgd/` (gitignored, outside
`data/raw/` so the cairn freeze hashes only the committed extract). This module records
the download (URL, HTTP response headers, size, SHA-256) in `data/raw/manifest.json`
and can verify the committed extract offline. `download()` is the only networked
function and is never called by a numbered pipeline step.
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "data" / "archive" / "npwgd"
RAW = ROOT / "data" / "raw"
MANIFEST = RAW / "manifest.json"

ITEM = "https://www.sciencebase.gov/catalog/item/64fa1e71d34ed30c2054ea11"
DOI = "https://doi.org/10.5066/P9DSRCZJ"
CITATION = (
    "Blondes, M.S., Knierim, K.J., Croke, M.R., Freeman, P.A., Doolan, C., Herzberg, A.S., "
    "and Shelton, J.L., 2019, U.S. Geological Survey National Produced Waters Geochemical "
    "Database (ver. 3.0, December 2023): U.S. Geological Survey data release, "
    "https://doi.org/10.5066/P9DSRCZJ."
)
_GET = "https://www.sciencebase.gov/catalog/file/get/64fa1e71d34ed30c2054ea11?f="
FILES: dict[str, dict[str, object]] = {
    "USGS_NPWGDv3_excel.xlsx": {
        "url": _GET + "__disk__e7%2Fef%2F17%2Fe7ef17fcb71c49e2241da4139ed775f8e328bdab",
        "expected_bytes": 80625044,
        "role": "database workbook (one sheet, one row per sample)",
    },
    "USGS_NPWGDv3_data_dictionary.xlsx": {
        "url": _GET + "__disk__00%2F9c%2Fc6%2F009cc66e8a1f7c565c58857f4669d7eba31fe018",
        "expected_bytes": 29653,
        "role": "data dictionary (209 fields)",
    },
    "USGS_NPWGDv3_metadata.xml": {
        "url": _GET + "__disk__3b%2F1b%2Fbe%2F3b1bbe47842a7e62d1e5328f40333f8a853c1eb6",
        "expected_bytes": 310373,
        "role": "FGDC metadata with process steps",
    },
    "version_history.txt": {
        "url": _GET + "__disk__00%2Fb8%2Fe3%2F00b8e3999bf79514c6fded7f0443b33792dd73e2",
        "expected_bytes": 6483,
        "role": "version history (which datasets v3.0 added and why)",
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_headers(text: str) -> dict[str, str]:
    """Last response block of a curl `-D` dump (redirects leave several blocks)."""
    blocks = [b for b in text.replace("\r", "").strip().split("\n\n") if b.strip()]
    out: dict[str, str] = {}
    for line in blocks[-1].splitlines():
        if line.upper().startswith("HTTP/"):
            out["status"] = line.strip()
        elif ":" in line:
            k, v = line.split(":", 1)
            if k.strip().lower() not in ("content-security-policy", "set-cookie"):
                out[k.strip().lower()] = v.strip()
    return out


def download(dest: Path = ARCHIVE) -> None:
    """Fetch every file into `dest` (network). Writes `<name>.headers` beside each file."""
    dest.mkdir(parents=True, exist_ok=True)
    for name, spec in FILES.items():
        req = urllib.request.Request(str(spec["url"]), headers={"User-Agent": "curl/8"})
        with urllib.request.urlopen(req, timeout=900) as resp:  # noqa: S310 (fixed https URLs)
            data = resp.read()
            hdrs = "\n".join(f"{k}: {v}" for k, v in resp.headers.items())
            status = f"HTTP/{resp.version // 10}.{resp.version % 10} {resp.status}"
        (dest / name).write_bytes(data)
        (dest / f"{name}.headers").write_text(status + "\n" + hdrs + "\n")


def write_manifest(extract: dict[str, object], downloaded_at_utc: str | None = None) -> dict:
    files = {}
    for name, spec in FILES.items():
        p = ARCHIVE / name
        hp = ARCHIVE / f"{name}.headers"
        files[name] = {
            "url": spec["url"],
            "role": spec["role"],
            "archive_path": f"data/archive/npwgd/{name}",
            "bytes": p.stat().st_size,
            "expected_bytes": spec["expected_bytes"],
            "sha256": sha256(p),
            "http_headers": parse_headers(hp.read_text()) if hp.is_file() else {},
        }
    manifest = {
        "dataset": "USGS National Produced Waters Geochemical Database v3.0 (December 2023)",
        "citation": CITATION,
        "doi": DOI,
        "sciencebase_item": ITEM,
        "licence": "public domain (U.S. Geological Survey)",
        "downloaded_at_utc": downloaded_at_utc or datetime.now(UTC).isoformat(timespec="seconds"),
        "note": (
            "The workbook stays in data/archive/ (gitignored). data/raw/ holds only the "
            "deterministic extract, the small metadata files and this manifest; the extract "
            "is written once and never modified. All cleaning happens downstream with an "
            "exclusion log."
        ),
        "archive_files": files,
        "extract": extract,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def verify_raw() -> dict[str, bool]:
    """Offline: do the committed data/raw files match the manifest?"""
    m = json.loads(MANIFEST.read_text())
    out = {}
    for rel, digest in m["extract"]["raw_sha256"].items():
        p = ROOT / rel
        out[rel] = p.is_file() and sha256(p) == digest
    return out
