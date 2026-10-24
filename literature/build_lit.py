"""Literature database: records.tsv (searched and verified in this project) + the manuscript bibliography.
Writes references.bib and literature.csv.
Usage (from literature/): python build_lit.py . core_refs.bib .   (core_refs.bib = the first manuscript bibliography)"""
import re, sys
import pandas as pd
S = sys.argv[1]; MS_BIB = sys.argv[2]; OUT = sys.argv[3]
t = pd.read_csv(f"{S}/records.tsv", sep="\t", dtype=str).fillna("")
t["doi"] = t["doi"].str.strip()
# keep a DOI only if it can be seen in the URL of the source page (otherwise it came from memory)
t.loc[~t.apply(lambda r: r.doi != "" and r.doi.lower().replace("/", "") in r.url.lower().replace("%2f", "").replace("/", "")
                                  or "doi" in r.verified, axis=1), "doi"] = ""
bib_ms = open(MS_BIB).read()
ms = {}
for m in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}", bib_ms, re.S):
    typ, key, body = m.groups()
    f = dict(re.findall(r"(\w+)\s*=\s*\{(.*?)\},?\n", body + "\n", re.S))
    ms[key] = dict(type=typ, **f)
CAT = {"A": "Deterministic and economic MPC, energy management", "B": "Stochastic, chance-constrained and robust MPC/optimisation",
       "C": "Renewable and price forecasting, probabilistic forecasts", "D": "Back-off and constraint tightening",
       "E": "Battery cost and sizing", "F": "Variability of renewables", "G": "Dimensionless ratios and normalised sizing",
       "H": "Industrial energy management and demand response", "I": "Tuning and evaluation statistics",
       "J": "Value of forecasts in storage operation", "K": "Software and models"}
ms_cat = {"mayne2000constrained": "A", "parisio2014mpc": "A", "oldewurtel2012use": "B", "mesbah2016stochastic": "B",
          "farina2016stochastic": "B", "charnes1959chance": "B", "hewing2020cautious": "B", "lei2021optimal": "B",
          "rasmussen2006gaussian": "C", "najibi2021enhanced": "C", "antonanzas2016review": "C", "gneiting2007probabilistic": "C",
          "smola2004tutorial": "C", "lago2021forecasting": "C", "hirth2018entsoe": "C", "zippenfenig2023openmeteo": "K",
          "xu2018factoring": "E", "kraft1988software": "K", "virtanen2020scipy": "K", "jones1998efficient": "I",
          "knowles2006parego": "I", "mckay1979comparison": "I", "sorourifar2021data": "I", "politis1992circular": "I",
          "rockafellar2000optimization": "I", "manwell2009wind": "K", "kunsch1989jackknife": "I", "kumar2019benchmarking": "D",
          "demiguel2026mapping": "G", "rawlings2017model": "A", "pedregosa2011scikit": "K"}
rows, bib = [], []
for k, f in ms.items():
    rows.append(dict(key=k, authors=f.get("author", ""), title=f.get("title", "").replace("{", "").replace("}", ""),
                     venue=f.get("journal", f.get("booktitle", f.get("publisher", f.get("howpublished", f.get("institution", ""))))),
                     year=f.get("year", ""), volume_pages=", ".join(x for x in (f.get("volume", ""), f.get("pages", "")) if x),
                     doi=f.get("doi", ""), url="", category=CAT[ms_cat[k]], method="", relevance="", in_manuscript="yes",
                     verified="see manuscript/REFERENCES_CHECK.md"))
for _, r in t.iterrows():
    if r.key in ms:
        continue
    rows.append(dict(key=r.key, authors=r.authors, title=r.title, venue=r.venue, year=r.year, volume_pages=r.volume_pages,
                     doi=r.doi, url=r.url, category=CAT[r.category[0]], method=r.method, relevance=r.relevance,
                     in_manuscript="", verified=r.verified))
    authors = " and ".join(a.strip() for a in r.authors.replace(" et al.", " and others").split(";"))
    vol, pages = "", ""
    if r.volume_pages:
        mm = re.match(r"([^,]+)(?:,\s*(.*))?", r.volume_pages)
        vol, pages = mm.group(1), (mm.group(2) or "")
    journalish = not any(s in r.venue for s in ("Conference", "ICML", "ICRA", "CASE", "IFAC World", "PSCC", "ICISSGT", "report", "Report", "arXiv", "Springer", "NTNU", "World Renewable"))
    fields = {"author": authors, "title": "{" + r.title + "}", "year": r.year}
    if journalish:
        typ = "article"; fields["journal"] = r.venue
        if vol:
            v = re.match(r"(\d+)\((\w+)\)", vol)
            if v: fields["volume"], fields["number"] = v.group(1), v.group(2)
            else: fields["volume"] = vol
        if pages: fields["pages"] = pages.replace("–", "--")
    elif r.venue in ("Springer",):
        typ = "book"; fields["publisher"] = r.venue
    elif "arXiv" in r.venue or "report" in r.venue.lower() or "NTNU" in r.venue:
        typ = "misc"; fields["howpublished"] = r.venue
    else:
        typ = "inproceedings"; fields["booktitle"] = r.venue
        if pages or vol: fields["pages"] = (pages or vol).replace("–", "--")
    if r.doi: fields["doi"] = r.doi
    if r.url: fields["url"] = r.url
    bib.append(f"@{typ}{{{r.key},\n" + ",\n".join(f"  {k} = {{{v}}}" for k, v in fields.items() if v) + "\n}\n")
pd.DataFrame(rows).to_csv(f"{OUT}/literature.csv", index=False)
_all = "% Manuscript bibliography\n" + bib_ms + "\n% Additional literature (records.tsv)\n" + "\n".join(bib)
_all = re.sub(r"(?<!\\)&", r"\\&", _all)   # BibTeX/LaTeX: escape bare ampersands
open(f"{OUT}/references.bib", "w").write(_all)
print(len(rows), "records;", sum(1 for r in rows if r["in_manuscript"]), "in the manuscript")
print(pd.DataFrame(rows).category.value_counts().to_string())
