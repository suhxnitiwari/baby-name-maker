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
#   ba-fbih  Federal Statistical Office of the Federation of BiH, top 100 newborn names 2012-2025 (one PDF per sex and year,
#        raw/ba-fbih-YYYY-top100-[fm].pdf), read into raw/ba-fbih-fzs-top100-2012-2025.tsv
#   ba-rs  Republika Srpska Institute of Statistics, top 10 newborn names (ranks only; 2024 press-conference slide, 2025 articles
#        7635/7636 on rzs.rs.ba): raw/ba-rs-rzs-*.pdf|html, read into raw/ba-rs-rzs-top10-2024-2025.tsv (Latin + Cyrillic)
#   bg   National Statistical Institute "Names in Bulgaria" releases 2012-2025 (raw/bg-nsi-Names*.pdf, news pages), read into
#        raw/bg-nsi-newborn-top-names-2012-2025.tsv (Latin as NSI spells it in English + Cyrillic)
#   br   IBGE Censo 2010 names API, top 20 per sex per decade of birth: raw/br-ibge-censo2010-ranking-by-decade.json
#   fi   DVV Nimipalvelu, most popular first names by decade of birth (population register): raw/fi-dvv-top-etunimet-*.html
#   es   INE "Nombres más frecuentes por fecha de nacimiento" (Censos de población anuales, 1 January 2025), the 50 most frequent
#        names of residents of Spain by decade of birth: raw/spanish/ine-nombres_por_fecha.xlsx (fetch_spanish_sources.py)
#   md   Public Services Agency, most frequent first names of newborns 2016-2023 (dataset.gov.md 16943 / 16944):
#        raw/md-asp-prenume-YYYY-[fm].(pdf|docx|xlsx)
#   lv   Central Statistical Bureau "100 most popular newborn names", ranks by five-year period (tools.stat.gov.lv/names/api):
#        raw/lv-csp-top100-ranks-1920-2025-(female|male)-latvia.json
#   lu   STATEC "La démographie luxembourgeoise en chiffres" 2023-2025 editions (data years 2022-2024), top 5 table:
#        raw/lu-statec-demographie-en-chiffres-*.pdf
#   nl   SVB kindernamen, every name given 10+ times, 2017-2025 (the JSON behind svb.nl's tables): raw/nl-svb-(meisjes|jongens)namen-YYYY.json
#   ru-moscow  Moscow Government open data (data.mos.ru datasets 2009 girls / 2011 boys, from the Moscow civil registry), the 100
#        most popular names of each month since 2015: raw/ru/moscow-names-(2009|2011).(json|csv|zip), downloaded by
#        fetch_moscow_names.py. Left out of years.json until those files are there (data.mos.ru only answers from Russia)
#   it   ISTAT "Conta nomi" (survey "Iscritti in anagrafe per nascita"), names of babies registered at birth 1999 onward, by sex,
#        from the web service behind istat.it/dati/calcolatori/contanomi: raw/it-istat-contanomi/YYYY-[fm].json (fetch_istat_names.py)
#   tr   TÜİK "İstatistiklerle Çocuk" bulletins 2014-2025 (veriportali.tuik.gov.tr), table of the most used child names: the top 30 of
#        babies born in the year (counts from 2021, ranks only before): raw/tr/tuik-cocuk-YYYY-*.xls, read into
#        raw/tr/tr-tuik-cocuk-names-2014-2025.tsv
#   tw   Ministry of the Interior (Taiwan) "全國姓名統計分析" (data date 2023-06-30), table 56: top 10 given names of people in the
#        household register by period of birth: raw/tw/tw-moi-112namestat.pdf, read into raw/tw/tw-moi-112-names.tsv;
#        pinyin from CC-CEDICT (raw/tw/cedict_1_0_ts_utf-8_mdbg.txt.gz) via cedict_pinyin.py, only where the reading is certain
#   be   Statbel "First names of newborns" 1995-2025, national top 12 per year (fetched in a browser): raw/be-statbel/top12-1995-2025.json
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

def top_lists(f):
    # lines of YEAR, F|M, "Name count,Name count,..." read out of an agency's PDFs or press releases
    c = new()
    for line in open(f"{RAW}/{f}", encoding="utf-8"):
        y, s, lst = line.rstrip("\n").split("\t")
        for item in lst.split(","):
            n, v = item.strip().rsplit(" ", 1); c[int(y)]["girl" if s == "F" else "boy"][n] = int(v)
    return c

def south_africa(): return top_lists("za-top10-2014-2024.tsv")

def federation_bih(): return top_lists("ba-fbih-fzs-top100-2012-2025.tsv")

def spain_decades():
    # sheets ESPAÑA_hombres / ESPAÑA_mujeres: blocks of rank | NOMBRE | FRECUENCIA | Por 1.000 under "NACIDOS EN AÑOS 1930 A 1939";
    # "ANTES DE 1930" is kept under 1920. INE prints names in capitals without accents; they are only title-cased (Jose, Maria Carmen)
    c = new()
    path = f"{RAW}/spanish/ine-nombres_por_fecha.xlsx"
    for sheet, sx in (("ESPAÑA_hombres", "boy"), ("ESPAÑA_mujeres", "girl")):
        rows = list(xlsx.rows(path, sheet)); heads = rows[2]
        for r in rows[4:]:
            if not r or not (r[0] or "").isdigit(): continue
            for k in range(1, len(r) - 1, 3):
                h = heads[k] if k < len(heads) else ""
                m = re.search(r"(\d{4}) A|ANTES DE (\d{4})", h or "")
                if not m or not r[k] or not r[k + 1]: continue
                d = int(m.group(1)) if m.group(1) else int(m.group(2)) - 10
                c[d][sx][" ".join(title(w) for w in r[k].split())] = int(r[k + 1])
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

def latvia_ranks():
    # each name has one rank per period (0 = not in that period's top 100). The tool labels a period by its midpoint;
    # it is stored under its first year (1920 -> 1918, births 1918-1922). The last one runs 2023 to July 2026
    r = ranked()
    for sex, f in (("girl", "female"), ("boy", "male")):
        d = json.load(open(f"{RAW}/lv-csp-top100-ranks-1920-2025-{f}-latvia.json", encoding="utf-8-sig"))
        mids = [y["year"] for y in d["years"]]
        ranks = collections.defaultdict(list)
        for n in d["data"]:
            for mid, k in zip(mids, n["data"].split(",")):
                if k != "0": ranks[mid - 2].append((int(k), title(n["name"])))
        for start, lst in ranks.items(): r[start][sex] = [n for _, n in sorted(lst)]
    return r

LV_PERIODS = {str(m - 2): [m - 2, m + 2] for m in range(1920, 2025, 5)} | {"2023": [2023, 2026]}

def luxembourg():
    # rows of three cells (Luxembourgish, foreign, all births), each "name(s) | count"; tied names share a cell and may wrap.
    # Only the all-births column is kept
    import fitz
    c = new()
    for f, y, page in (("2023", 2022, 11), ("2024", 2023, 23), ("2025", 2024, 23)):
        t = fitz.open(f"{RAW}/lu-statec-demographie-en-chiffres-{f}.pdf")[page].get_text()
        i = t.index("Femmes"); t = re.sub(r",\s*\n", ", ", t[i:t.index("Source", i)])
        girls, boys = t.split("Hommes")
        for sex, part in (("girl", girls), ("boy", boys)):
            cells = [x.strip() for x in part.split("\n")[1:] if x.strip()]
            for k in range(0, len(cells) - 5, 6):
                for n in cells[k + 4].split(", "): c[y][sex][n] = int(cells[k + 5])
    return c

def netherlands():
    # rows: name, count, rank, length, (unused)
    c = new()
    for f in glob.glob(f"{RAW}/nl-svb-*namen-*.json"):
        s, y = re.search(r"(meisjes|jongens)namen-(\d{4})", f).groups()
        for r in json.load(open(f, encoding="utf-8-sig"))["data"]: c[int(y)]["girl" if s == "meisjes" else "boy"][r[0]] = int(r[1])
    return c

def srpska_ranks():
    # 2025's articles give ranks 1-4 and then list the rest without saying their order, so only those 4 are kept
    r, native = ranked(), {}
    for line in open(f"{RAW}/ba-rs-rzs-top10-2024-2025.tsv", encoding="utf-8"):
        if line.startswith("#"): continue
        y, s, lat, cyr = line.rstrip("\n").split("\t")
        lat, cyr = lat.split(","), cyr.split(",")
        native.update(zip(lat, cyr))
        r[int(y)]["girl" if s == "F" else "boy"] = lat[:4] if y == "2025" else lat
    SRPSKA_NATIVE.update(native)
    return r

SRPSKA_NATIVE = {}

BULGARIA_NATIVE = {}

def bulgaria():
    c = new()
    for line in open(f"{RAW}/bg-nsi-newborn-top-names-2012-2025.tsv", encoding="utf-8"):
        if line.startswith("#"): continue
        y, s, lat, cyr = line.rstrip("\n").split("\t")
        for a, b in zip(lat.split(","), cyr.split(",")):
            n, v = a.rsplit(" ", 1); c[int(y)]["girl" if s == "F" else "boy"][n] = int(v)
            BULGARIA_NATIVE[n] = b.rsplit(" ", 1)[0]
    return c

def finland():
    # each page: "Miehet" (men) table then "Naiset" (women), rows of rank | name | number; pages 1-2 = ranks 1-20
    c = new()
    for f in glob.glob(f"{RAW}/fi-dvv-top-etunimet-*.html"):
        d = int(re.search(r"etunimet-(\d{4})-", f).group(1))
        for sex, part in zip(("boy", "girl"), text(f).split("|Sija|")[1:]):
            for n, v in re.findall(r"\|\d+\.\|([^|]+)\|(\d[\d\s]*)(?=\|)", part): c[d][sex][n] = int(re.sub(r"\s", "", v))
    return c

MOSCOW_MONTHS = "январь февраль март апрель май июнь июль август сентябрь октябрь ноябрь декабрь".split()
MOSCOW_LATIN = {}

def moscow_files():
    return {ds: next(iter(sorted(glob.glob(f"{RAW}/ru/moscow-names-{ds}.*"))), None) for ds in ("2009", "2011")}

def moscow_rows(path):
    # the portal's JSON or CSV export (zipped or not), or rows read through apidata.mos.ru ({"Cells": {...}}); field names
    # in English (Name, NumberOfPersons, Year, Month) or as the CSV captions print them (Имя, Количество человек, Год, Месяц)
    raw = open(path, "rb").read()
    if raw[:2] == b"PK":
        z = zipfile.ZipFile(io.BytesIO(raw)); member = next(n for n in z.namelist() if n.lower().endswith((".json", ".csv")))
        raw, path = z.read(member), member
    for enc in ("utf-8-sig", "cp1251"):
        try: t = raw.decode(enc); break
        except UnicodeDecodeError: continue
    if path.lower().endswith(".csv"):
        recs = list(csv.DictReader(io.StringIO(t), delimiter=";" if t.count(";") > t.count(",") else ","))
    else:
        recs = [r.get("Cells", r) for r in json.loads(t)]
    pick = lambda r, *ks: next((r[k] for k in ks if k in r and r[k] not in (None, "")), None)
    for r in recs:
        n, v, y, m = pick(r, "Name", "Имя"), pick(r, "NumberOfPersons", "Количество человек"), pick(r, "Year", "Год"), pick(r, "Month", "Месяц")
        if n and str(v).strip().isdigit() and str(y).strip().isdigit(): yield n.strip(), int(v), int(y), str(m).strip().lower()

def moscow():
    # each month's top 100 per sex, summed into years. A year with fewer than 12 months published (the current one) is left out
    from russian_latin import romanize
    c, months = new(), collections.defaultdict(set)
    for (ds, path), sex in zip(moscow_files().items(), ("girl", "boy")):
        for n, v, y, m in moscow_rows(path):
            c[y][sex][n] += v; months[(y, sex)].add(m)
    for y in list(c):
        if any(len(months[(y, s)] & set(MOSCOW_MONTHS)) < 12 for s in ("girl", "boy")): del c[y]
    # the names as the registry prints them (Cyrillic), with a BGN/PCGN spelling for search
    for y in c:
        for s in ("girl", "boy"):
            for n, _ in c[y][s].most_common(TOP): MOSCOW_LATIN[n] = romanize(n, "bgn_plain") or ""
    return c

def italy():
    # ISTAT prints names in capitals without accents, an accented final letter as an apostrophe (NICOLO' = Nicolò), and
    # compound names whole (GIOVANNI PIO); they are kept as printed, only title-cased
    c = new()
    for f in glob.glob(f"{RAW}/it-istat-contanomi/*-[fm].json"):
        d = json.load(open(f, encoding="utf-8"))
        for n, v in d["rows"]:
            c[int(d["year"])]["girl" if d["sex"] == "f" else "boy"][" ".join(title(w) for w in n.split())] += int(v)
    return c

def turkey_rows():
    for line in open(f"{RAW}/tr/tr-tuik-cocuk-names-2014-2025.tsv", encoding="utf-8"):
        if line.startswith("#"): continue
        y, g, s, rk, n, v = line.rstrip("\n").split("\t")
        if g == "born": yield int(y), "girl" if s == "f" else "boy", int(rk), n, int(v) if v else None

def turkey():
    c = new()
    for y, sex, rk, n, v in turkey_rows():
        if v is not None: c[y][sex][n] = v
    return c

def turkey_ranks():
    r = ranked()
    for y, sex, rk, n, v in sorted(turkey_rows()):
        if v is None: r[y][sex].append(n)
    return r

TAIWAN_LATIN, TW_PERIODS = {}, {}

def taiwan():
    # table 56: periods of birth in ROC years (民國1-9年 = 1912-1920, then 民國10-19年 = 1921-1930 ...; the last runs to June 2023).
    # Each period is stored under its first year; names stay in characters, with CEDICT pinyin for search where it is certain
    from cedict_pinyin import pinyin
    c = new()
    for line in open(f"{RAW}/tw/tw-moi-112-names.tsv", encoding="utf-8"):
        if line.startswith("#"): continue
        tab, s, per, rk, n, v = line.rstrip("\n").split("\t")
        if tab != "t56": continue
        a, b = int(per[:4]), int(per[5:9])
        c[a]["girl" if s == "f" else "boy"][n] = int(v); TW_PERIODS[str(a)] = [a, b]
        if pinyin(n): TAIWAN_LATIN[n] = pinyin(n)
    return c

def belgium():
    c = new()
    for y, d in json.load(open(f"{RAW}/be-statbel/top12-1995-2025.json", encoding="utf-8")).items():
        for s, sex in (("f", "girl"), ("m", "boy")):
            for n, v in d[s]: c[int(y)][sex][n] = int(v)
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
    dict(key="ba-fbih", label="Federation of BiH", group="Bosnia and Herzegovina", region="Europe", agency="Federal Statistical Office (Federalni zavod za statistiku)", dataset="Top 100 names of newborns", license="Source: FZS",
         coverage="top", badge="ranked", threshold=None, rule="Top 100 names of babies born in the Federation of Bosnia and Herzegovina, one of the country's two entities; Republika Srpska publishes its own list.", fn=federation_bih),
    dict(key="ba-rs", label="Republika Srpska", group="Bosnia and Herzegovina", region="Europe", agency="Republika Srpska Institute of Statistics", dataset="Most popular names of newborns", license="Source: RZS RS",
         coverage="top", badge="ranked", threshold=None, native=SRPSKA_NATIVE, rule="Most popular names of babies born in Republika Srpska, one of the country's two entities, ranks only (no counts): top 10 for 2024, top 4 for 2025. Published in Cyrillic and Latin.", fn=new, ranked=srpska_ranks),
    dict(key="bg", label="Bulgaria", group="", region="Europe", agency="National Statistical Institute", dataset="Names in Bulgaria (annual release)", license="Source: NSI",
         coverage="top", badge="ranked", threshold=None, native=BULGARIA_NATIVE, rule="Most common names of babies born in the year: top 20 for 2012–2015, top 10 from 2016 (NSI marks most years preliminary). Names in Latin as NSI writes them in English; the Cyrillic is kept.", fn=bulgaria),
    dict(key="md", label="Moldova", group="", region="Europe", agency="Public Services Agency (Agenția Servicii Publice)", dataset="Raport statistic privind cel mai frecvent prenume al copiilor nou-născuți (dataset.gov.md)", license="Reuse with a link to date.gov.md",
         coverage="top", badge="ranked", threshold=None, rule="The most frequent first names of newborns registered by civil-status offices in the year (top 20 in 2018–2022, longer lists in 2016, 2017 and 2023).", fn=moldova),
    dict(key="nl", label="the Netherlands", group="", region="Europe", agency="Sociale Verzekeringsbank (SVB)", dataset="Kindernamen (child benefit registrations)", license="Public (svb.nl)",
         coverage="all", badge="full", threshold=10, rule="Children registered for child benefit, by year of birth. Names given to fewer than 10 babies aren't published.", fn=netherlands),
    dict(key="lu", label="Luxembourg", group="", region="Europe", agency="STATEC", dataset="La démographie luxembourgeoise en chiffres (top 5 first names of newborns)", license="Source: STATEC",
         coverage="top", badge="ranked", threshold=None, rule="Top 5 names of all babies born in the year (STATEC also splits them by Luxembourgish and foreign nationality). Tied names share a rank. Spellings are counted separately (Leo and Léo).", fn=luxembourg),
    dict(key="lv", label="Latvia", group="", region="Europe", agency="Central Statistical Bureau of Latvia", dataset="100 most popular newborn names in Latvia", license="Open (cite CSB)",
         coverage="top", badge="ranked", period=5, periods=LV_PERIODS, threshold=None, rule="Top 100 first names in five-year periods of birth, ranks only (no counts). Each key is the first year of its period (1918 = births 1918–1922); the last period, 2023 to July 2026, is provisional. Before 1990 only people still in the register are counted. Spellings are kept apart (Kristiāns and Kristians).", fn=new, ranked=latvia_ranks),
    dict(key="br", label="Brazil", group="", region="Latin America", agency="IBGE", dataset="Censo 2010: Nomes no Brasil", license="Open (IBGE terms)",
         coverage="top", badge="population", decades=True, threshold=None, rule="Names of people counted in the 2010 census, by the decade they were born; 1920 stands for everyone born before 1930.", fn=brazil),
    dict(key="fi", label="Finland", group="", region="Europe", agency="Digital and Population Data Services Agency", dataset="Nimipalvelu: suosituimmat etunimet", license="CC BY 4.0",
         coverage="top", badge="population", decades=True, threshold=5, rule="People in the Finnish population register, by the decade they were born, counting every first name a person has (not only the one they go by). Names with fewer than 5 bearers aren't published.", fn=finland),
    dict(key="es", label="Spain", group="", region="Europe", agency="Instituto Nacional de Estadística (INE)", dataset="Nombres más frecuentes por fecha de nacimiento (Censos de población anuales, 1 January 2025)", license="Free reuse citing INE as the source",
         coverage="top", badge="population", decades=True, threshold=None, rule="People living in Spain on 1 January 2025, by the decade they were born, from INE's table of the 50 most frequent names of each decade (residents counted, not births; people who died or left before 2025 are missing). 1920 stands for everyone born before 1930; 2020 covers 2020–2024. Compound names count as their own name (Maria Carmen). INE prints names without accents; they are shown as printed.", fn=spain_decades),
    dict(key="it", label="Italy", group="", region="Europe", agency="ISTAT", dataset="Conta nomi: names of babies registered at birth (survey Iscritti in anagrafe per nascita)", license="CC BY 4.0 (Istat)",
         coverage="all", badge="full", threshold=1, rule="Babies of the resident population registered at birth, by year of birth, from 1999. Every first name is counted, down to one baby, written as ISTAT prints it: compound names whole (Giovanni Pio) and an accented last letter as an apostrophe (Nicolo' for Nicolò). ISTAT does not correct spelling mistakes or a name that doesn't match the baby's sex.", fn=italy),
    dict(key="tr", label="Türkiye", group="", region="Middle East & West Asia", agency="Turkish Statistical Institute (TÜİK)", dataset="İstatistiklerle Çocuk (Statistics on Child): most used names of babies born in the year", license="Free to use with attribution (TÜİK)",
         coverage="top", badge="ranked", threshold=None, rule="Top 30 names of babies born in the year, from the Address Based Population Registration System (ADNKS). 2014–2020 are ranks only; counts from 2021. 2014 is the age-0 group at the end of the year. Turkish spelling as published (Göktuğ, İnci).", fn=turkey, ranked=turkey_ranks),
    dict(key="tw", label="Taiwan", group="", region="East Asia", agency="Ministry of the Interior, Department of Household Registration", dataset="全國姓名統計分析 (National name statistics), table 56: top 10 given names by period of birth", license="Open Government Data License, version 1.0 (attribution)",
         coverage="top", badge="population", threshold=None, period=10, periods=TW_PERIODS, script="Han", latin=TAIWAN_LATIN,
         rule="People in Taiwan's household register on 30 June 2023, by when they were born (ten-year periods counted in Republic of China years: 1912–1920, 1921–1930, and so on; the last is 2021 to June 2023). Living people, not newborn registrations. Names are in Chinese characters as registered; the pinyin for search comes from the CC-CEDICT dictionary, not from the ministry, and is left out where a character has more than one reading.", fn=taiwan),
    dict(key="be", label="Belgium", group="", region="Europe", agency="Statbel", dataset="First names of newborns 1995–2025", license="Statbel open data (attribution)",
         coverage="all", badge="full", threshold=5, rule="Statbel publishes names given to at least 5 newborns in a year in Belgium.", fn=belgium),
]
if all(moscow_files().values()):
    PLACES.append(dict(key="ru-moscow", label="Moscow (city)", group="Russia", region="Europe", agency="Moscow Government open data / Moscow civil registry (ZAGS)",
         dataset="Сведения о наиболее популярных женских / мужских именах среди новорожденных (data.mos.ru datasets 2009 and 2011)",
         license="Open data (Russian Government decree No. 583 of 10 July 2013); reuse with a link to data.mos.ru", coverage="top", badge="ranked", threshold=None,
         script="Cyrillic", latin=MOSCOW_LATIN,
         rule="One city, not all of Russia (Russia publishes no national list). The registry publishes the 100 most popular names of each month for girls and boys; a year here adds up the twelve months, so a name only counts in the months it made that month's top 100. Names are shown in Cyrillic as registered, with a BGN/PCGN spelling for search.",
         fn=moscow))

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

#   xk   Kosovo Agency of Statistics, Census 2024 "Names and Surnames in Kosova", Tab. 5: the most common name for each single
#        year of age, with counts (raw/xk-ask-census2024-names-and-surnames-en.pdf), read into raw/xk-ask-census2024-top-name-by-single-age.tsv
def kosovo_census():
    rows = []
    for line in open(f"{RAW}/xk-ask-census2024-top-name-by-single-age.tsv", encoding="utf-8"):
        if line.startswith("#"): continue
        age, sex, item = line.rstrip("\n").split("\t")
        n, v = item.rsplit(" ", 1)
        rows.append(dict(place="Kosovo", source="Kosovo Agency of Statistics, Census 2024", reference_year=2024, sex="girl" if sex == "F" else "boy",
                         age_group=age, municipality=None, rank=1, name=n, count=int(v)))
    return rows

census = montenegro_census() + kosovo_census()
path = os.path.join(HERE, "data/census-names.json")
# other builders add their own places to this file (Romania: build_name_lists.py); keep their rows
mine = {r["place"] for r in census}
if os.path.exists(path):
    census += [r for r in json.load(open(path, encoding="utf-8")) if r["place"] not in mine]
json.dump(census, open(path, "w"), ensure_ascii=False, separators=(",", ":"))
print("wrote", path, len(census), "rows")
