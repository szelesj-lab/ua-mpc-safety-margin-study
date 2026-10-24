# Reference check (before submission)

This table covers the 31 entries of the first draft. The other 93 entries (added with the literature database)
are tracked in the `verified` column of `literature/literature.csv` of the study repository: `full` = all fields read
on the source page, other values = only the listed fields confirmed. Every one of them must be checked against the
publisher page before submission; several `url` fields point to repository or preprint copies and should be
replaced by the DOI.

Status of each entry in `refs.bib`. "Opened" = the bibliographic data was read on an opened source page in this
project; "memory" = filled in from general knowledge and must be checked against the publisher page.

| Key | Status | To check |
|---|---|---|
| mayne2000constrained | memory | pages 789–814, DOI |
| parisio2014mpc | opened (doi), pages from memory | pages 1813–1827 |
| oldewurtel2012use | opened | author list |
| mesbah2016stochastic | opened (vol, pages) | DOI |
| farina2016stochastic | opened (DOI) | volume 44, pages 53–67 |
| charnes1959chance | opened (DOI) | pages |
| hewing2020cautious | opened (vol 28, issue 6, DOI) | pages (ETH record and memory disagree, left out) |
| lei2021optimal | opened (arXiv) | is there a journal/conference version? |
| rasmussen2006gaussian | standard reference | – |
| najibi2021enhanced | opened (IJEPES 130, 106916, DOI) | – |
| antonanzas2016review | memory | volume 136, pages 78–111, DOI |
| gneiting2007probabilistic | opened (vol, issue, pages) | DOI |
| smola2004tutorial | memory | issue 3, pages 199–222, DOI |
| lago2021forecasting | opened | – |
| hirth2018entsoe | opened | – |
| zippenfenig2023openmeteo | opened (Zenodo DOI) | cite the version used |
| xu2018factoring | memory | volume 33(2), pages 2248–2259, DOI |
| kraft1988software | memory | report number DFVLR-FB 88-28 |
| virtanen2020scipy | memory | volume 17, pages 261–272, DOI |
| jones1998efficient | memory | volume 13(4), pages 455–492, DOI |
| knowles2006parego | memory | volume 10(1), pages 50–66, DOI |
| mckay1979comparison | memory | volume 21(2), pages 239–245, DOI |
| sorourifar2021data | opened (authors, ADCHEM 2021) | IFAC-PapersOnLine volume, pages, DOI |
| politis1992circular | memory | editors, pages 263–270 |
| rockafellar2000optimization | memory | volume 2(3), pages 21–41, DOI |
| manwell2009wind | memory | edition and year actually used |
| kunsch1989jackknife | memory | volume 17(3), pages 1217–1241, DOI |
| kumar2019benchmarking | opened (DOI, journal, year) | volume, issue, article number |
| demiguel2026mapping | opened (arXiv) | – |
| rawlings2017model | standard reference | – |
| pedregosa2011scikit | standard reference | – |

Before submission: a targeted search for 2022–2026 papers in Applied Energy, Energy, IEEE Trans. Smart Grid and
Journal of Energy Storage on uncertainty-aware / chance-constrained battery MPC and on back-off baselines, so that
the related-work section and the novelty claims are up to date. The bibliography style is `unsrtnat` (numbered in
order of citation); replace it with Elsevier's `elsarticle-num` if it is available in your TeX installation.
