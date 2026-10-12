# Five-minute walkthrough

_Rendered from the ledger by `scripts/60_docs.py`; do not edit `walkthrough.md`._

**The question (30 s).** Produced water from oil and gas wells sometimes carries lithium.
The USGS compiled 113135 analyses from 63 sources into
one database. Where is the lithium, and how much of that map is really a map of who
sampled what, when, and which papers got compiled?

**The first trap (30 s).** Before any analysis I checked how "below detection" is stored.
It is not. 6416 lithium values, 0 zeros,
0 negatives, no flags, 0
detection fields in the dictionary. A non-detect is an empty cell, the same as "never
analyzed". So every median in this study is a median of reported values. That is a
limitation I can state, not one I can fix.

**The method (45 s).** I pre-registered and froze the plan before computing anything:
produced-water rows only, U.S. only, charge balance within 10 percent,
one unit per well within its source dataset, a screen of Li at or above
100 mg/L with Mg/Li at or below 10 from published
screening papers, and bootstrap intervals that resample wells and cluster by dataset.
5500 lithium rows become 4141 wells.

**The ranking (60 s).** 100 of 4141 wells pass.
By median lithium the top basin is Amarillo Arch at 181 mg/L,
but that is 27 wells from one dataset, every location a centroid,
with an interval from 34 to 299.
Arkla (255 wells, 5 datasets)
sits at 67 mg/L and Appalachian
(564 wells, 9 datasets) at
55. Only 3 basins
have a screened fraction whose interval excludes zero. The USGS named four datasets it
added because they were lithium-rich; they hold 11 wells and
removing them changes nothing. The real dataset effect is elsewhere: where a basin has
several sources, their medians differ by a median factor of 4.1
and up to 59. And lithium was measured on 5.5%
of rows, 46% of them from the 1960s; a model guesses
which rows have it with AUC 0.75. So the ranking is of the wells someone chose to
analyze.

**The model (60 s).** Can chemistry stand in for a lithium analysis? Gradient boosting on
major-ion log-ratios, TDS, depth, play type and era. Random folds by well: RMSE
0.37 in log10 units, R-squared 0.76.
Leave a whole dataset out: 0.51. Leave a whole basin out:
0.51, with folds from 0.27 to
1.19. The pooled out-of-basin R-squared is still
0.55, which passes the rule I froze, but precision at the floor
drops from 0.78 to 0.28 and
only 6 of 22 held-out basins are
predicted usefully on their own. The model knows which basins are brine-rich; it does not
know which wells in a new basin will clear the floor. The positive control, TDS from the
same features, scores 0.83, so the pipeline is fine.

**The sentence to leave with (15 s).** The public database says lithium-rich produced
water exists in a handful of basins, but the number it gives any basin is mostly a number
about which datasets were compiled and which wells were analyzed; a new field needs its
own lithium analyses, and chemistry alone will not substitute for them across basins.
Every number here is pre-registered, recorded in a ledger, and re-executed by the harness.
