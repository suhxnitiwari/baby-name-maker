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
#        ONS top 100 baby names historical data, every ten years 1904-2024 (ranks only): raw/ew-historical-1904-2024.xlsx
#   sct  National Records of Scotland, all names 1974-2025: raw/sct-1974-2025.csv
#   ni   NISRA full list of first forenames 1997-2025: raw/ni-1997-2025.xlsx
#   ie   CSO VSA50 / VSA60: raw/ie-VSA50.csv, raw/ie-VSA60.csv
#   no   Statistics Norway table 10467: raw/no-10467.json
#   at   Statistik Austria OGD_VORNAMEN: raw/at.csv
#   nz   DIA baby names 1900-2025 (bot-protected; its top 12 per year were extracted in a browser): raw/nz-top12-1900-2025.txt
#   nsw  NSW Registry, popular baby names from 1952: raw/au-nsw-popular-baby-names-from-1952-*.csv
#   qld  Queensland Government open data "Top 100 Baby Names" (data.qld.gov.au; the download links sit behind a bot
#        challenge, so each resource was read through the portal's own CKAN datastore API): raw/qld-top100-*.json
#   se   Statistics Sweden table TAB619 (PxWeb v2 API), newborns' top 100 1998-2022: raw/se-TAB619-newborns-top100-1998-2022.json
#        Skatteverket "Namn på nyfödda" (dataportal.se, CSV), 2021 onward: raw/se-skatteverket-namn-pa-nyfodda.csv
#   pl   dane.gov.pl dataset 219 "Imiona nadawane dzieciom w Polsce": raw/pl-newborns-2000-2019.csv, raw/pl-newborns-20YY-[fm].xlsx
#   dk   Statistics Denmark "Navne til nyfødte" top 50 (dst.dk's own top-list endpoint, one HTML table per year): raw/dk-top50-*.html
#   ch   Federal Statistical Office, DF_BEVNAT_PRENOMS_1 / _2 (stats.swiss SDMX API, Switzerland total):
#        raw/ch-newborns-prenoms-[12].csv, raw/ch-newborns-prenoms-[12]-structure.json
#   cat  Idescat "Noms dels nadons" (onomastica API, top 100 a year; display spellings from each name's Idescat page):
#        raw/cat-idescat-nadons-top100-1997-2025.json, raw/cat-idescat-name-forms.json
#   de-berlin  Berlin open data "Liste der häufigen Vornamen" 2012-2023, one file per district plus one of rare names:
#        raw/de-liste-der-haufigen-vornamen-in-berlin-*.csv
#   cl   Servicio de Registro Civil e Identificación, every first name registered 1920-2021 (via the guaguas package): raw/cl.csv
#   za   Stats SA "Recorded live births" (P0305) 2014-2024; the top-ten tables were read out of the PDFs
#        (raw/za-P0305-*.pdf) into raw/za-top10-2014-2024.tsv
#   br   IBGE Censo 2010 names API, top 20 per sex per decade of birth: raw/br-ibge-censo2010-ranking-by-decade.json
#   fi   DVV Nimipalvelu, most popular first names by decade of birth (population register): raw/fi-dvv-top-etunimet-*.html
import csv, glob, html, io, json, os, re, sys, unicodedata, zipfile, collections

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

def ranked(): return collections.defaultdict(lambda: {"girl": [], "boy": []})

def top_years(c, r=None):
    # r: years published as ranks only (no counts); they keep their rank order and get null counts
    out = {y: [[[n, v] for n, v in c[y][sx].most_common(TOP)] for sx in ("girl", "boy")] for y in c if c[y]["girl"] or c[y]["boy"]}
    for y in (r or {}):
        if y not in out: out[y] = [[[n, None] for n in r[y][sx][:TOP]] for sx in ("girl", "boy")]
    return {str(y): out[y] for y in sorted(out)}

def text(path):
    # visible text of an HTML page, cells separated by "|"
    h = open(path, encoding="utf-8").read()
    h = re.sub(r"<(script|style).*?</\1>", "", h, flags=re.S)
    return re.sub(r"\|[\s|]*", "|", html.unescape(re.sub(r"<[^>]+>", "|", h)))

def first_sheet(path):
    return re.search(r'<sheet [^>]*name="([^"]+)"', zipfile.ZipFile(path).read("xl/workbook.xml").decode()).group(1)

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

def england_wales_snapshots():
    # ONS top 100 every ten years since 1904, names only; kept for the years before the annual series starts (1996)
    r = ranked()
    for sex, sheet in (("girl", "Table_1"), ("boy", "Table_2")):
        head = None
        for row in xlsx.rows(f"{RAW}/ew-historical-1904-2024.xlsx", sheet):
            if row and row[0] == "Rank": head = row; continue
            if not head or not row or not str(row[0] or "").isdigit(): continue
            for k, h in enumerate(head):
                if str(h or "").isdigit() and int(h) < 1996 and k < len(row) and row[k]:
                    r[int(h)][sex].append(row[k].strip())
    return r

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

def queensland():
    # 1960-2005 is one long table (Name, Sex, Year, Count); each later year is a top-100 table with girls and boys side by side
    c = new()
    for f in glob.glob(f"{RAW}/qld-top100-*.json"):
        for r in json.load(open(f))["result"]["records"]:
            if "Year" in r:
                if str(r["Count"] or "").isdigit(): c[int(r["Year"])]["girl" if r["Sex"].startswith("F") else "boy"][title(r["Name"])] += int(r["Count"])
                continue
            y = int(re.search(r"(\d{4})\.json$", f).group(1))
            for sex, k in (("girl", "Girl"), ("boy", "Boy")):
                n, v = r.get(f"{k} Names"), str(r.get(f"Count of {k} Names") or "")
                if n and v.isdigit(): c[y][sex][title(n)] += int(v)
    return c

def sweden():
    # Statistics Sweden until 2022 (spellings grouped, top 100); Skatteverket from 2023 (each spelling apart, top ~1,000).
    # Codes are sex + list: "1"/"2" = boys/girls in the top 100, "10"/"20" the same names in the top 10
    d = json.load(open(f"{RAW}/se-TAB619-newborns-top100-1998-2022.json"))
    dims = [sorted(d["dimension"][k]["category"]["index"].items(), key=lambda kv: kv[1]) for k in d["id"]]
    lab = d["dimension"]["Tilltalsnamn"]["category"]["label"]
    (names, contents, years), (_, nc, ny) = dims, d["size"]
    count = next(i for code, i in contents if code == "BE0001AJ")
    c = new()
    for code, ni in names:
        sex = "boy" if code[0] == "1" else "girl"
        for y, yi in years:
            v = d["value"][(ni * nc + count) * ny + yi]
            if v: c[int(y)][sex][lab[code]] = max(c[int(y)][sex][lab[code]], int(v))
    for r in csv.DictReader(open(f"{RAW}/se-skatteverket-namn-pa-nyfodda.csv", encoding="cp1252")):
        y = int(r["FODELSEAR"])
        # skip 2021-2022 (Statistics Sweden's) and a birth year whose names are still being registered
        if r["GRUPPERING"] != "Total" or y <= 2022 or int(r["UPPDATERINGSDATUM"][:4]) <= y: continue
        c[y]["girl" if r["KÖN"] == "Kvinna" else "boy"][r["NAMN"]] = int(r["ANTAL"])
    return c

def poland():
    c = new()
    for r in csv.DictReader(open(f"{RAW}/pl-newborns-2000-2019.csv", encoding="utf-8-sig")):
        c[int(r["Rok"])]["girl" if r["Płeć"] == "K" else "boy"][title(r["Imię"])] += int(r["Liczba"])
    for f in glob.glob(f"{RAW}/pl-newborns-20??-[fm].xlsx"):
        y, s = re.search(r"(\d{4})-([fm])\.xlsx$", f).groups()
        for r in xlsx.rows(f, first_sheet(f)):
            if len(r) > 2 and str(r[2] or "").isdigit(): c[int(y)]["girl" if s == "f" else "boy"][title(r[0])] = int(r[2])
    return c

def denmark():
    # each page: "Pigenavne" (girls) then "Drengenavne" (boys), rows of rank | name | number | per 1,000
    c = new()
    for f in glob.glob(f"{RAW}/dk-top50-*.html"):
        y = int(re.search(r"(\d{4})\.html$", f).group(1))
        for sex, part in zip(("girl", "boy"), text(f).split("Drengenavne")):
            for n, v in re.findall(r"\|\d+\|([^|\d]+)\|(\d+)\|", part): c[y][sex][n.strip()] = int(v)
    return c

def switzerland():
    c = new()
    for f, sex in (("1", "boy"), ("2", "girl")):
        cl = next(x for x in json.load(open(f"{RAW}/ch-newborns-prenoms-{f}-structure.json"))["data"]["codelists"] if "FIRSTNAMES" in x["id"])
        names = {x["id"]: x["name"] for x in cl["codes"]}
        for r in csv.DictReader(open(f"{RAW}/ch-newborns-prenoms-{f}.csv", encoding="utf-8-sig")):
            if r["GEO"] == "8100" and r["OBS_VALUE"] and float(r["OBS_VALUE"]) > 0:
                c[int(r["TIME_PERIOD"])][sex][names[r["NAME"]]] = int(float(r["OBS_VALUE"]))
    return c

def catalonia():
    # the API gives names without accents (MARTI); each name's own Idescat page gives the spelling it shows (MARTÍ)
    forms = json.load(open(f"{RAW}/cat-idescat-name-forms.json"))
    c = new()
    for y, ents in json.load(open(f"{RAW}/cat-idescat-nadons-top100-1997-2025.json")).items():
        for e in ents:
            n = e["ono:f"]["ono:c"]
            c[int(y)]["girl" if n["sex"] == "f" else "boy"][title(forms.get(n["id"]) or n["content"])] = int(e["ono:f"]["ono:pos1"]["ono:v"])
    return c

def berlin():
    # per year: one file per district (names given 2+ times there) and one of names rare in every district, so the sum is
    # all of Berlin. From 2017 the files list every given name with its position; only first names (position 1) count here
    c = new()
    for f in glob.glob(f"{RAW}/de-liste-der-haufigen-vornamen-in-berlin-*.csv"):
        y = int(re.search(r"berlin-(\d{4})-", f).group(1))
        for r in csv.DictReader(open(f, encoding="utf-8-sig")):
            if r.get("position", "1") == "1" and r["anzahl"].isdigit():
                c[y]["girl" if r["geschlecht"] == "w" else "boy"][r["vorname"]] += int(r["anzahl"])
    return c

def chile():
    c = new()
    for r in csv.DictReader(open(f"{RAW}/cl.csv", encoding="utf-8")):
        c[int(r["anio"])]["girl" if r["sexo"] == "F" else "boy"][r["nombre"]] += int(r["n"])
    return c

def south_africa():
    c = new()
    for line in open(f"{RAW}/za-top10-2014-2024.tsv"):
        y, s, lst = line.rstrip("\n").split("\t")
        for item in lst.split(","):
            n, v = item.rsplit(" ", 1); c[int(y)]["girl" if s == "F" else "boy"][n] = int(v)
    return c

def brazil():
    # ranking?decada=D covers people born in [D-10, D); decada=1930 is everyone born before 1930 (kept under 1920)
    c = new()
    for k, res in json.load(open(f"{RAW}/br-ibge-censo2010-ranking-by-decade.json")).items():
        d, s = int(k[:4]) - 10, k[4]
        for r in res: c[d]["girl" if s == "F" else "boy"][title(r["nome"])] = r["frequencia"]
    return c

def moldova():
    # one report per sex and year, as PDF, DOCX or XLSX. The registry printouts (2016, 2017, 2023) list
    # count | rank | NAME; the typed tables (2018-2022) list rank | name | count
    import fitz
    c = new()
    for f in glob.glob(f"{RAW}/md-asp-prenume-*"):
        y, s, ext = re.search(r"(\d{4})-([fm])\.(\w+)$", f).groups()
        if ext == "xlsx": cells = [str(v or "") for r in xlsx.rows(f, first_sheet(f)) for v in r]
        elif ext == "docx": cells = re.findall(r"<w:t[^>]*>([^<]*)</w:t>", zipfile.ZipFile(f).read("word/document.xml").decode())
        else: cells = "\n".join(p.get_text() for p in fitz.open(f)).split("\n")
        t = "|" + "|".join(x.strip() for x in cells if x.strip()) + "|"
        if "TOATE" in t: rows = [(n, v) for v, _, n in re.findall(r"\|([\d.]+)\|(\d+)\|([^|\d]+)(?=\|)", t)]
        else: rows = [(n, v) for _, n, v in re.findall(r"\|(\d+)\.?\|([^|\d]+)\|(\d+)(?=\|)", t)]
        for n, v in rows: c[int(y)]["girl" if s == "f" else "boy"][title(n)] = int(v.replace(".", ""))
    return c

def finland():
    # each page: "Miehet" (men) table then "Naiset" (women), rows of rank | name | number; pages 1-2 = ranks 1-20
    c = new()
    for f in glob.glob(f"{RAW}/fi-dvv-top-etunimet-*.html"):
        d = int(re.search(r"etunimet-(\d{4})-", f).group(1))
        for sex, part in zip(("boy", "girl"), text(f).split("|Sija|")[1:]):
            for n, v in re.findall(r"\|\d+\.\|([^|]+)\|(\d[\d\s]*)(?=\|)", part): c[d][sex][n] = int(re.sub(r"\s", "", v))
    return c

# coverage: "all" = every name above a publication threshold; "top" = a ranked list only
# badge: "full" (all names above a threshold, ongoing), "ranked" (top-N only), "ended" (series no longer updated),
#        "population" (people counted in a register or census by when they were born, not newborn registrations)
# region: world region, for grouping the place picker
# optional: breaks (years where the method changes), ended (no new years coming), decades (keys are the first year of a
#        decade of birth), ranked (years published as ranks only, stored with null counts and listed in "snapshots")
PLACES = [
    dict(key="us", label="the United States", group="", region="North America", agency="Social Security Administration", dataset="Beyond the Top 1000 Names (national data)", license="Public domain",
         coverage="all", badge="full", threshold=5, rule="Names given to fewer than 5 babies in a year aren't published.", fn=us),
    dict(key="fr", label="France", group="", region="Europe", agency="INSEE", dataset="Fichier des prénoms, édition 2024", license="Licence Ouverte",
         coverage="all", badge="full", threshold=None, rounded=5, rule="Counts are rounded to the nearest 5. Rare names are grouped and not published. Before 2012, France excluding Mayotte.", fn=france),
    dict(key="no", label="Norway", group="", region="Europe", agency="Statistics Norway", dataset="Table 10467: births by first name", license="NLOD",
         coverage="all", badge="full", threshold=4, rule="Only names used by at least 200 people are listed; fewer than 4 babies in a year aren't published. From 2021, counted by naming year.", fn=norway),
    dict(key="ca", label="Canada", group="", region="North America", agency="Statistics Canada", dataset="Table 17-10-0147-01: first names at birth", license="Open Government Licence – Canada",
         coverage="all", badge="full", threshold=None, rule="Small counts are suppressed for confidentiality.", fn=canada),
    dict(key="ew", label="England & Wales", group="United Kingdom", region="Europe", agency="Office for National Statistics", dataset="Baby names in England and Wales: 1996 to 2025; Top 100 baby names historical data", license="Open Government Licence v3.0",
         coverage="all", badge="full", threshold=3, rule="Names given to 2 or fewer babies are redacted. Spellings are counted separately. 1904–1994: official top 100 every ten years, ranks only.", fn=england_wales, ranked=england_wales_snapshots),
    dict(key="sct", label="Scotland", group="United Kingdom", region="Europe", agency="National Records of Scotland", dataset="All names given to babies, 1974 to 2025", license="Open Government Licence v3.0",
         coverage="all", badge="full", threshold=1, rule="Every first forename registered.", fn=scotland),
    dict(key="ni", label="Northern Ireland", group="United Kingdom", region="Europe", agency="NISRA", dataset="Baby names full lists", license="Open Government Licence",
         coverage="all", badge="full", threshold=3, rule="Names given to fewer than 3 babies aren't published.", fn=northern_ireland),
    dict(key="ie", label="Ireland", group="", region="Europe", agency="Central Statistics Office", dataset="VSA50 / VSA60: names with 3 or more occurrences", license="CC BY 4.0",
         coverage="all", badge="full", threshold=3, rule="Names given to fewer than 3 babies aren't published.", fn=ireland),
    dict(key="at", label="Austria", group="", region="Europe", agency="Statistik Austria", dataset="First names of newborns (OGD)", license="CC BY 4.0",
         coverage="all", badge="full", threshold=1, rule="Before 2010 only babies of Austrian nationality were counted; from 2010, all babies.", breaks=[2010], fn=austria),
    dict(key="nz", label="New Zealand", group="", region="Oceania", agency="Department of Internal Affairs", dataset="Baby name popularity over time", license="CC BY 4.0",
         coverage="all", badge="full", threshold=10, rule="Names registered fewer than 10 times in a year aren't published. Years are registration years.", fn=new_zealand),
    dict(key="nsw", label="New South Wales", group="Australia", region="Oceania", agency="NSW Registry of Births, Deaths & Marriages", dataset="Popular baby names from 1952", license="CC BY 4.0",
         coverage="top", badge="ranked", threshold=None, rule="A ranked list of the most popular names only.", fn=nsw),
    dict(key="qld", label="Queensland", group="Australia", region="Oceania", agency="Queensland Department of Justice (Registry of Births, Deaths and Marriages)", dataset="Top 100 Baby Names (data.qld.gov.au)", license="CC BY 3.0",
         coverage="top", badge="ranked", threshold=None, rule="Top 100 names only.", fn=queensland),
    dict(key="se", label="Sweden", group="", region="Europe", agency="Statistics Sweden (to 2022) · Skatteverket (from 2023)", dataset="TAB619: newborns' 100 most common first names · Namn på nyfödda", license="CC0 (Statistics Sweden) · public open data (Skatteverket)",
         coverage="top", badge="ranked", threshold=None, rule="The name a child is called by (tilltalsnamn). 1998–2022: Statistics Sweden's top 100, with different spellings of a name counted together. From 2023: the Swedish Tax Agency's top list, each spelling counted on its own.", breaks=[2023], fn=sweden),
    dict(key="pl", label="Poland", group="", region="Europe", agency="Ministry of Digital Affairs (PESEL register)", dataset="Imiona nadawane dzieciom w Polsce (dane.gov.pl)", license="CC0 1.0",
         coverage="all", badge="full", threshold=2, rule="First names of children registered 2000–2025. 2000–2012: names given fewer than 5 times aren't published; from 2013, fewer than 2.", breaks=[2013], fn=poland),
    dict(key="dk", label="Denmark", group="", region="Europe", agency="Statistics Denmark", dataset="Navne til nyfødte: top 50", license="Open (cite Statistics Denmark)",
         coverage="top", badge="ranked", threshold=None, rule="Top 25 names for 1985–1992, top 50 from 1993; spellings of the same name are counted together. Before 1996 only babies with Danish citizenship were counted.", breaks=[1996], fn=denmark),
    dict(key="ch", label="Switzerland", group="", region="Europe", agency="Federal Statistical Office", dataset="DF_BEVNAT_PRENOMS_1 / _2: first names of newborns", license="Open use, source required (opendata.swiss terms_by)",
         coverage="all", badge="full", threshold=None, rule="Every first name given in the latest year, with its count in each year back to 2000; a name nobody was given recently may be missing from earlier years.", fn=switzerland),
    dict(key="cat", label="Catalonia", group="Spain", region="Europe", agency="Idescat", dataset="Noms dels nadons", license="CC BY 4.0",
         coverage="top", badge="ranked", threshold=None, rule="Top 100 names of babies born in Catalonia each year. Idescat counts accented and unaccented spellings together (Martí and Marti) and shows one of them.", fn=catalonia),
    dict(key="de-berlin", label="Berlin", group="Germany", region="Europe", agency="Berlin standesämter (via Berlin Open Data)", dataset="Liste der häufigen Vornamen", license="CC BY",
         coverage="all", badge="full", threshold=1, rule="One city, not all of Germany (Germany publishes no national list). Babies registered in Berlin. Until 2016 every given name counts; from 2017 only the first name.", breaks=[2017], fn=berlin),
    dict(key="cl", label="Chile", group="", region="Latin America", agency="Servicio de Registro Civil e Identificación", dataset="Names registered 1920–2021 (via the guaguas dataset)", license="CC0",
         coverage="all", badge="ended", ended=True, threshold=1, rule="Every first name registered, even once, 1920–2021.", fn=chile),
    dict(key="za", label="South Africa", group="", region="Africa", agency="Statistics South Africa", dataset="Recorded live births (P0305), top ten baby forenames", license="Free to use with attribution",
         coverage="top", badge="ranked", threshold=None, rule="Top 10 names only, for births that happened and were registered in the year. 2015–2016 count a forename in any position; from 2017 only the first forename.", breaks=[2017], fn=south_africa),
    dict(key="md", label="Moldova", group="", region="Europe", agency="Public Services Agency (Agenția Servicii Publice)", dataset="Raport statistic privind cel mai frecvent prenume al copiilor nou-născuți (dataset.gov.md)", license="Reuse with a link to date.gov.md",
         coverage="top", badge="ranked", threshold=None, rule="The most frequent first names of newborns registered by civil-status offices in the year (top 20 in 2018–2022, longer lists in 2016, 2017 and 2023).", fn=moldova),
    dict(key="br", label="Brazil", group="", region="Latin America", agency="IBGE", dataset="Censo 2010: Nomes no Brasil", license="Open (IBGE terms)",
         coverage="top", badge="population", decades=True, threshold=None, rule="Names of people counted in the 2010 census, by the decade they were born; 1920 stands for everyone born before 1930.", fn=brazil),
    dict(key="fi", label="Finland", group="", region="Europe", agency="Digital and Population Data Services Agency", dataset="Nimipalvelu: suosituimmat etunimet", license="CC BY 4.0",
         coverage="top", badge="population", decades=True, threshold=5, rule="People in the Finnish population register, by the decade they were born, counting every first name a person has (not only the one they go by). Names with fewer than 5 bearers aren't published.", fn=finland),
]

out = {"built": "official birth records only; each place keeps its own publication rules", "places": []}
for p in PLACES:
    fn, rk = p.pop("fn"), p.pop("ranked", None)
    rk = rk() if rk else None
    years = top_years(fn(), rk)
    ys = sorted(map(int, years))
    if rk: p["snapshots"] = sorted(y for y in rk if str(y) in years and years[str(y)][0] and years[str(y)][0][0][1] is None)
    p.update(first=ys[0], last=ys[-1], years=years)
    out["places"].append(p)
    print(f"{p['key']:9} {p['label']:20} {ys[0]}-{ys[-1]}  {len(ys)} years   #1 girl {ys[-1]}: {years[str(ys[-1])][0][0][0]}   #1 boy: {years[str(ys[-1])][1][0][0]}", flush=True)

path = os.path.join(HERE, "data/years.json")
json.dump(out, open(path, "w"), ensure_ascii=False, separators=(",", ":"))
print("wrote", path, os.path.getsize(path) // 1024, "KB")

# Census snapshots by age group, kept out of years.json: an age group is not a birth year, so these never become years.
#   me   MONSTAT 2023 Census release 149/2024, most frequent names by age group and by municipality (names only, no counts):
#        raw/me-monstat-popis2023-imena.pdf
def montenegro_census():
    import fitz
    pages = [p.get_text() for p in fitz.open(f"{RAW}/me-monstat-popis2023-imena.pdf")]
    rows = []
    # page 2: girls by age, 3: boys by age, 4: girls by municipality, 5: boys by municipality; each block is a label + 10 names
    for page, sex, by in ((1, "girl", "age"), (2, "boy", "age"), (3, "girl", "municipality"), (4, "boy", "municipality")):
        lines = [x.strip() for x in pages[page].split("\n") if x.strip()]
        lines = lines[lines.index("Crna Gora"):]
        for k in range(0, len(lines) - 10, 11):
            label, names = lines[k], lines[k + 1:k + 11]
            if label == "Crna Gora":
                if by == "municipality": continue  # the national list is already in the age table
                age, mun = "all", None
            elif by == "age": age, mun = label.replace(" i više", "+"), None
            else: age, mun = "all", label
            rows += [dict(place="Montenegro", source="MONSTAT 2023 Census", reference_year=2023, sex=sex, age_group=age,
                          municipality=mun, rank=i + 1, name=n, count=None) for i, n in enumerate(names)]
    return rows

census = montenegro_census()
path = os.path.join(HERE, "data/census-names.json")
json.dump(census, open(path, "w"), ensure_ascii=False, separators=(",", ":"))
print("wrote", path, len(census), "rows")
