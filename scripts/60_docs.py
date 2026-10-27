"""Step 6: run the test suite, record its counts, and render the README, walkthrough and
resume bullet from their templates with the ledger (cairn render covers only the report).
Fails on any unresolved placeholder, so every number in those documents is a ledger value."""

import re
import subprocess
import sys
from pathlib import Path

from cairn import load_ledger, record
from cairn.numbers import render

ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    (ROOT / "README.tmpl.md", ROOT / "README.md"),
    (ROOT / "docs" / "walkthrough.tmpl.md", ROOT / "docs" / "walkthrough.md"),
    (ROOT / "docs" / "resume_bullet.tmpl.md", ROOT / "docs" / "resume_bullet.md"),
]

tests = sorted((ROOT / "tests").glob("test_*.py"))
record("tests.n_tests", sum(len(re.findall(r"^def test_", p.read_text(), re.M)) for p in tests),
       note="count of `def test_` functions in tests/")
record("tests.n_files", len(tests))
proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(ROOT / "tests")],
                      cwd=ROOT, capture_output=True, text=True)
summary = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
record("tests.n_passed", int(m.group(1)) if (m := re.search(r"(\d+) passed", summary)) else 0)
record("tests.n_failed", int(m.group(1)) if (m := re.search(r"(\d+) failed", summary)) else 0)
print(f"pytest: {summary}")
if proc.returncode != 0:
    print(proc.stdout[-3000:])
    raise SystemExit("test suite failed")

cairn_head = subprocess.run(["git", "-C", str(ROOT.parent / "cairn-lithium-baseline"), "rev-parse", "HEAD"],
                            capture_output=True, text=True)
record("env.cairn_commit", cairn_head.stdout.strip() if cairn_head.returncode == 0 else "unknown")
ledger = load_ledger()
for src, dst in DOCS:
    text, missing = render(src.read_text(), ledger)
    if missing:
        raise SystemExit(f"{src.name}: unresolved placeholders {sorted(set(missing))}")
    dst.write_text(text)
    print(f"rendered {dst.relative_to(ROOT)}")
