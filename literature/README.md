# Literature database

| File | Content |
|---|---|
| `literature.csv` | one row per paper: key, authors, title, venue, year, volume/pages, DOI, URL, category, method, relevance to this study, how it was verified, whether the manuscript cites it |
| `references.bib` | BibTeX for every row (same keys) |
| `review.md` | narrative review, grouped by the questions of the study |
| `records.tsv` | the hand-collected records (input of `build_lit.py`) |
| `build_lit.py` | merges `records.tsv` with `manuscript/refs.bib` into the two files above |

Categories: deterministic MPC, stochastic / chance-constrained / robust MPC, back-off tightening, forecasting and
calibration, value of forecasts, variability of renewables, ratio-based design rules, battery cost and sizing,
industrial energy flexibility, tuning and statistics, software.

**Verification.** Every new record was found with a web search during the study. The column `verified` says what
was confirmed on the page at `url`: `full` = authors, venue, volume/pages and DOI; `title`, `title+vol`,
`title+doi`, `title+vol+doi`, `title+authors`, `doi` = only those fields (the rest from general knowledge);
`memory` / `repository` = not opened. The 31 entries cited in the manuscript are tracked in
`manuscript/REFERENCES_CHECK.md`. A DOI is kept only where it was visible at the URL. Re-check every field against
the publisher page before citing.
