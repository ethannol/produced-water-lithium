"""Step 4b: positive control. The same pipeline predicts log10 TDS from the same features
with TDS removed, under the same three protocols (pre-registered pass: random-fold
pooled R-squared >= 0.80 for the boosted model)."""

import os

os.environ["OMP_NUM_THREADS"] = "1"  # see docs/decisions.md: thread oversubscription

import runpy
import sys

import numpy as np
from cairn import record

sys.argv = [sys.argv[0]]
ns = runpy.run_path("scripts/40_model.py", run_name="model_lib")
run, cv = ns["run"], ns["cv"]
wc, fc, oc = run("TDS", "control", drop_tds=True)
ctrl = cv.summarise(fc.loc[(fc.protocol == "random") & (fc.model == "hgb")],
                    oc.loc[(oc.protocol == "random") & (oc.model == "hgb")], float(np.log10(1e5)))
record("control.passes", "passes" if ctrl["r2_pooled"] >= 0.80 else "FAILS")
print("control done")
