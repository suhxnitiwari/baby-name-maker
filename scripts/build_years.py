# The time machine: the most-given names of every year, from official birth records only.
# Writes data/years.json: one entry per place, each with who published it, what it covers, its publication rules
# (so a name that isn't listed reads "not published", never "0 babies"), and the top girls' and boys' names of every year.
#
# Sources (all in raw/, not committed; see docs/name-sources.md for where each one comes from):
#   us   SSA national files. 1880-2017 from the babynames R package (hadley/babynames, built from the same SSA files),
#        2018-2025 read from ssa.gov/oact/babynames/names.zip (the site blocks scripts, so its top 20 per year were
#        extracted in a browser): raw/us-top20-1880-2017.tsv, raw/us-top20-2018-2025.tsv
#   fr   INSEE fichier des prénoms 2024, national: raw/fr-prenoms-2024-nat.csv
#   ca   Statistics Canada table 17-10-0147-01: raw/ca-17100147.zip
#   ew   ONS baby names 1996-2025: raw/ew-1996-2025.xlsx
#   sct  National Records of Scotland, all names 1974-2025: raw/sct-1974-2025.csv
#   ni   NISRA full list of first forenames 1997-2025: raw/ni-1997-2025.xlsx
#   ie   CSO VSA50 / VSA60: raw/ie-VSA50.csv, raw/ie-VSA60.csv
#   no   Statistics Norway table 10467: raw/no-10467.json
#   at   Statistik Austria OGD_VORNAMEN: raw/at.csv
#   nz   DIA baby names 1900-2025 (bot-protected; its top 12 per year were extracted in a browser): raw/nz-top12-1900-2025.txt
#   nsw  NSW Registry, popular baby names from 1952: raw/au-nsw-popular-baby-names-from-1952-*.csv
import csv, glob, io, json, os, re, sys, unicodedata, zipfile, collections

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, "raw")
sys.path.insert(0, os.path.join(HERE, "scripts"))
import xlsx

TOP = 12

def title(n):
    n = n.strip()
    if not (n.isupper() or n.islower()): return n
    return "-".join(p[:1].upper() + p[1:].lower() for p in n.split("-"))

def new(): return collections.defaultdict(lambda: {"girl": collections.Counter(), "boy": collections.Counter()})

def top_years(c):
    return {str(y): [[[n, v] for n, v in c[y][sx].most_common(TOP)] for sx in ("girl", "boy")] for y in sorted(c) if c[y]["girl"] or c[y]["boy"]}

def us():
    c = new()
    for r in csv.DictReader(open(f"{RAW}/us-top20-1880-2017.tsv"), delimiter="\t"):
        c[int(r["year"])]["girl" if r["sex"] == "F" else "boy"][r["name"]] = int(r["n"])
    for line in open(f"{RAW}/us-top20-2018-2025.tsv"):
        y, s, lst = line.rstrip("\n").split("\t")
        for item in lst.split(","):
            n, v = item.rsplit(" ", 1); c[int(y)]["girl" if s == "F" else "boy"][n] = int(v)
    return c

def france():
    c = new()
    for r in csv.DictReader(open(f"{RAW}/fr-prenoms-2024-nat.csv", encoding="utf-8"), delimiter=";"):
        if r["prenom"].startswith("_") or not r["periode"].isdigit(): continue
        c[int(r["periode"])]["boy" if r["sexe"] == "1" else "girl"][title(r["prenom"])] += int(r["valeur"])
    return c

def canada():
    c = new()
    with zipfile.ZipFile(f"{RAW}/ca-17100147.zip").open("17100147.csv") as fh:
        rd = csv.reader(io.TextIOWrapper(fh, encoding="utf-8-sig")); head = next(rd)
        i = {h: k for k, h in enumerate(head)}
        for r in rd:
            if r[i["GEO"]] != "Canada" or r[i["Indicator"]] != "Frequency" or not r[i["VALUE"]]: continue
            sx = r[i["Sex at birth"]]
            if sx not in ("Male", "Female"): continue
            c[int(r[i["REF_DATE"]])]["girl" if sx == "Female" else "boy"][title(r[i["First name at birth"]])] += int(float(r[i["VALUE"]]))
    return c

def england_wales():
    c = new()
    for sex, sheet in (("girl", "Table_1"), ("boy", "Table_2")):
        head = None
        for r in xlsx.rows(f"{RAW}/ew-1996-2025.xlsx", sheet):
            if r and r[0] == "Name": head = r; continue
            if not head or not r or not r[0]: continue
            for k, h in enumerate(head):
                m = re.match(r"(\d{4}) Count", h or "")
                if m and k < len(r) and r[k] and str(r[k]).isdigit():
                    c[int(m.group(1))][sex][r[0]] = int(r[k])
    return c

def scotland():
    c = new()
    for r in csv.DictReader(open(f"{RAW}/sct-1974-2025.csv", encoding="utf-8-sig")):
        c[int(r["Year"])]["girl" if r["Sex"].startswith("G") else "boy"][title(r["Name"])] += int(r["Number"])
    return c

def northern_ireland():
    # NISRA full list 1997-2025: each year is a block of three columns (name, number of babies, rank)
    c = new()
    for sex, sheet in (("boy", "Table 1"), ("girl", "Table 2")):
        head = None
        for r in xlsx.rows(f"{RAW}/ni-1997-2025.xlsx", sheet):
            if r and r[0] and str(r[0]).endswith(" Name"): head = r; continue
            if not head: continue
            for k, h in enumerate(head):
                m = re.match(r"(\d{4}) Name", str(h or ""))
                if m and k + 1 < len(r) and r[k] and str(r[k + 1] or "").isdigit():
                    c[int(m.group(1))][sex][title(str(r[k]))] = int(r[k + 1])
    return c

def ireland():
    c = new()
    for sex, f in (("boy", "ie-VSA50.csv"), ("girl", "ie-VSA60.csv")):
        rd = csv.reader(open(f"{RAW}/{f}", encoding="utf-8-sig")); next(rd)
        for stat, _, _, year, _, name, _, val in rd:
            if stat.endswith("C01") and val: c[int(year)][sex][name] = int(float(val))
    return c

def norway():
    d = json.load(open(f"{RAW}/no-10467.json"))
    names = sorted(d["dimension"]["Fornavn"]["category"]["index"].items(), key=lambda kv: kv[1])
    years = sorted(d["dimension"]["Tid"]["category"]["index"].items(), key=lambda kv: kv[1])
    vals, ny = d["value"], len(years)
    c = new()
    for code, ni in names:
        sex, name = ("girl" if code[0] == "1" else "boy"), title(code[1:])
        for y, yi in years:
            v = vals[ni * ny + yi] if isinstance(vals, list) else vals.get(str(ni * ny + yi))
            if isinstance(v, (int, float)) and v > 0: c[int(y)][sex][name] = int(v)
    return c

def austria():
    c = new()
    for r in csv.DictReader(open(f"{RAW}/at.csv", encoding="utf-8-sig"), delimiter=";"):
        if not (r.get("F-ANZAHL_LGEB") or "").isdigit(): continue
        c[int(r["C-JAHR-0"])]["boy" if r["C-GESCHLECHT-0"] == "1" else "girl"][r["F-VORNAME_NORMALISIERT"]] += int(r["F-ANZAHL_LGEB"])
    return c

def new_zealand():
    c = new()
    for line in open(f"{RAW}/nz-top12-1900-2025.txt"):
        m = re.match(r"(\d{4})([FM])(.*)", line.strip())
        for item in m.group(3).split(","):
            n, v = item.rsplit(" ", 1); c[int(m.group(1))]["girl" if m.group(2) == "F" else "boy"][n] = int(v)
    return c

def nsw():
    c = new()
    for f in glob.glob(f"{RAW}/au-nsw-popular-baby-names-from-1952-*.csv"):
        for r in csv.DictReader(open(f, encoding="utf-8-sig")):
            c[int(r["Year"])]["girl" if r["Gender"].startswith("F") else "boy"][title(r["Name"])] += int(r["Number"])
    return c

# coverage: "all" = every name above a publication threshold; "top" = a ranked list only
PLACES = [
    dict(key="us", label="the United States", group="", agency="Social Security Administration", dataset="Beyond the Top 1000 Names (national data)", license="Public domain",
         coverage="all", threshold=5, rule="Names given to fewer than 5 babies in a year aren't published.", fn=us),
    dict(key="fr", label="France", group="", agency="INSEE", dataset="Fichier des prénoms, édition 2024", license="Licence Ouverte",
         coverage="all", threshold=None, rounded=5, rule="Counts are rounded to the nearest 5. Rare names are grouped and not published. Before 2012, France excluding Mayotte.", fn=france),
    dict(key="no", label="Norway", group="", agency="Statistics Norway", dataset="Table 10467: births by first name", license="NLOD",
         coverage="all", threshold=4, rule="Only names used by at least 200 people are listed; fewer than 4 babies in a year aren't published. From 2021, counted by naming year.", fn=norway),
    dict(key="ca", label="Canada", group="", agency="Statistics Canada", dataset="Table 17-10-0147-01: first names at birth", license="Open Government Licence – Canada",
         coverage="all", threshold=None, rule="Small counts are suppressed for confidentiality.", fn=canada),
    dict(key="ew", label="England & Wales", group="United Kingdom", agency="Office for National Statistics", dataset="Baby names in England and Wales: 1996 to 2025", license="Open Government Licence v3.0",
         coverage="all", threshold=3, rule="Names given to 2 or fewer babies are redacted. Spellings are counted separately.", fn=england_wales),
    dict(key="sct", label="Scotland", group="United Kingdom", agency="National Records of Scotland", dataset="All names given to babies, 1974 to 2025", license="Open Government Licence v3.0",
         coverage="all", threshold=1, rule="Every first forename registered.", fn=scotland),
    dict(key="ni", label="Northern Ireland", group="United Kingdom", agency="NISRA", dataset="Baby names full lists", license="Open Government Licence",
         coverage="all", threshold=3, rule="Names given to fewer than 3 babies aren't published.", fn=northern_ireland),
    dict(key="ie", label="Ireland", group="", agency="Central Statistics Office", dataset="VSA50 / VSA60: names with 3 or more occurrences", license="CC BY 4.0",
         coverage="all", threshold=3, rule="Names given to fewer than 3 babies aren't published.", fn=ireland),
    dict(key="at", label="Austria", group="", agency="Statistik Austria", dataset="First names of newborns (OGD)", license="CC BY 4.0",
         coverage="all", threshold=1, rule="Before 2010 only babies of Austrian nationality were counted; from 2010, all babies.", breaks=[2010], fn=austria),
    dict(key="nz", label="New Zealand", group="", agency="Department of Internal Affairs", dataset="Baby name popularity over time", license="CC BY 4.0",
         coverage="all", threshold=10, rule="Names registered fewer than 10 times in a year aren't published. Years are registration years.", fn=new_zealand),
    dict(key="nsw", label="New South Wales", group="Australia", agency="NSW Registry of Births, Deaths & Marriages", dataset="Popular baby names from 1952", license="CC BY 4.0",
         coverage="top", threshold=None, rule="A ranked list of the most popular names only.", fn=nsw),
]

out = {"built": "official birth records only; each place keeps its own publication rules", "places": []}
for p in PLACES:
    fn = p.pop("fn")
    years = top_years(fn())
    ys = sorted(map(int, years))
    p.update(first=ys[0], last=ys[-1], years=years)
    out["places"].append(p)
    print(f"{p['key']:4} {p['label']:20} {ys[0]}-{ys[-1]}  {len(ys)} years   #1 girl {ys[-1]}: {years[str(ys[-1])][0][0][0]}   #1 boy: {years[str(ys[-1])][1][0][0]}", flush=True)

path = os.path.join(HERE, "data/years.json")
json.dump(out, open(path, "w"), ensure_ascii=False, separators=(",", ":"))
print("wrote", path, os.path.getsize(path) // 1024, "KB")
