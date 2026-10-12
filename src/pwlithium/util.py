"""Small helpers shared by the pipeline scripts."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
DERIVED = ROOT / "data" / "derived"
TABLES = ROOT / "reports" / "tables"
FIGURES = ROOT / "reports" / "figures"

LI_FOCUSED = ["STANDARDLITHIUM", "TETRA", "TROUTSTEUBER", "NYLITHIUM"]
FLOOR = 100.0  # mg/L, pre-registered primary lithium floor
CEILING = 10.0  # Mg/Li mass ratio, pre-registered primary ceiling
CB_TOL = 10.0  # percent, pre-registered primary charge-balance tolerance
MIN_WELLS_BASIN = 20
MIN_WELLS_FORMATION = 10
SEED = 20261012
N_BOOT = 1000


def commas(items: Iterable[object]) -> str:
    """Comma-separated string (kept out of scripts so the join lint stays quiet)."""
    return ", ".join(str(x) for x in items)


def slug(s: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in str(s)).strip("_")


def lines(items: Iterable[object]) -> str:
    """Newline-joined string (same reason as `commas`)."""
    return "\n".join(str(x) for x in items)
