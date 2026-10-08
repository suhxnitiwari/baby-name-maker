# More real first names, kept apart from data/names-db.tsv: data/names-extra.tsv holds ONLY names whose folded form
# (lowercase, accents stripped, spaces and hyphens removed, as fold() in app.js) is not already in names-db.tsv.
# Same format: name <TAB> gender f|m|u|? <TAB> countries <TAB> people recorded. Every name is one a source records;
# nothing is generated. Same cleaning as build_world.py / single_names.py: Latin script, a vowel, no placeholders,
# compound given names split into single names ("María del Carmen" → María, Carmen), dropping pieces that are never names alone.
#
# Sources, in order (raw downloads go in raw/, which is gitignored):
#   ar    RENAPER (Argentina), historical first names 1922-2015 (datos.gob.ar): raw/ar-renaper-historico-nombres-1922-2015.zip
#   lists data/name-lists.tsv (official approved/recognised/registered lists; rejected names skipped)
#   br    IBGE Censo 2010 names (brasil.io's mirror of the IBGE API): raw/br-nomes.csv.gz, and the IBGE Censo 2022 names API
#         (servicodados.ibge.gov.br/api/v3/nomes/2022, every name with 20+ people, by sex): raw/br-ibge-2022/
#   cl    Servicio de Registro Civil e Identificación (Chile), every name registered 1920-2021: raw/cl.csv
#   wd    Wikidata (CC0), items that are given names (Q202444 / Q11879590 / Q12308941 / Q3409032), every Latin-script label,
#         alias and native label: raw/wd-given-names-latin/
#   jp    JMnedict (EDRDG, CC BY-SA 4.0), given-name entries' romanised readings: raw/JMnedict.xml.gz
#   fr    INSEE (France), fichier des personnes décédées 1970-2025, every given name of everyone recorded: raw/fr-deces/
#   wikt  English Wiktionary (CC BY-SA 4.0), every entry in a "<language> given names" category: raw/wikt-given-names.tsv
#   it    ISTAT (Italy) "Conta nomi", names of babies registered at birth 1999-2024 (full lists from 2022; the service cuts the
#         1999-2021 lists off part-way): raw/it-istat-contanomi/ (fetch_istat_names.py). Names given to only one baby in all
#         those years are left out, because ISTAT says it doesn't correct spelling or transcription mistakes
#   tr    TÜİK (Türkiye) "İstatistiklerle Çocuk" 2014-2025, top 30 names of babies born in the year and of all children 0-17:
#         raw/tr/tr-tuik-cocuk-names-2014-2025.tsv
#   tw    Ministry of the Interior (Taiwan), 全國姓名統計分析 2023, tables 50, 51 and 56 (top single-character names, top 100
#         names, top 10 by period of birth): raw/tw/tw-moi-112-names.tsv. Names there are in characters; the Latin form is the
#         CC-CEDICT pinyin (cedict_pinyin.py), only where every character has one reading
#   be    Statbel (Belgium), first names of newborns 1995-2025 (5+ babies in a year), births summed: raw/be-statbel/names-1995-2025.tsv
#   es    INE (Spain), names of residents with 20+ people (Padrón, 1 Jan 2022; INE strips accents): raw/es/es-ine-nombres-ge20.tsv
#   se    Statistics Sweden TAB622, every tilltalsnamn (name a person goes by) with 10+ bearers 2005-2020, no counts:
#         raw/se/se-scb-TAB622-tilltalsnamn-min10-metadata.json
#
#   python3 scripts/build_names_extra.py            (downloads what is missing, then rewrites data/names-extra.tsv)
#   python3 scripts/build_names_extra.py --offline  (only what is already in raw/)
import collections, csv, glob, gzip, io, json, os, re, sys, time, unicodedata, urllib.parse, urllib.request, zipfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); RAW = os.path.join(ROOT, "raw"); DATA = os.path.join(ROOT, "data")
sys.path.insert(0, HERE)
from build_world import clean as world_clean, num
from single_names import SPLIT, PARTICLES

DB = os.path.join(DATA, "names-db.tsv"); OUT = os.path.join(DATA, "names-extra.tsv")
OFFLINE = "--offline" in sys.argv
UA = {"User-Agent": "Lullabyte name builder (https://github.com/suhxnitiwari)"}
csv.field_size_limit(1 << 30)

# fold(), exactly as app.js does it: the key that decides whether two spellings are the same name
SUBS = [("æ", "ae"), ("ǣ", "ae"), ("ǽ", "ae"), ("ø", "o"), ("ǿ", "o"), ("œ", "oe"), ("ð", "d"), ("đ", "d"), ("þ", "th"), ("ß", "ss"), ("ł", "l"), ("ı", "i"), ("ŋ", "ng")]
COMB = re.compile("[̀-ͯ]")
def fold(s):
    s = COMB.sub("", unicodedata.normalize("NFD", s)).lower()
    for a, b in SUBS: s = s.replace(a, b)
    return re.sub(r"[\s-]", "", s)
key = lambda n: unicodedata.normalize("NFC", n).lower()

EXTRA_PLACEHOLDERS = {"sinnombre", "nn", "nomeignorado", "ignorado", "naoinformado", "semnome", "nonombre", "sinregistro", "fallecido", "rn", "nonato", "mortinato", "sansprenom", "inconnu", "inconnue", "veuve", "epouse", "dit", "dite"}
def clean(n):
    n = world_clean(n)
    if not n: return None
    k = fold(n)
    if k in EXTRA_PLACEHOLDERS or len(k) < 2 or any(len(w) > 20 for w in SPLIT.split(n)) or re.search(r"(.)\1\1", k): return None
    return n

def get(url, path, data=None, headers=None):
    if os.path.exists(path): return path
    if OFFLINE: return None
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=300) as r: body = r.read()
    open(path, "wb").write(body); return path

# ── sources: each yields (raw name, sex f|m|?, people) ──
def argentina():
    p = os.path.join(RAW, "ar-renaper-historico-nombres-1922-2015.zip")
    get("https://infra.datos.gob.ar/catalog/otros/dataset/2/distribution/2.1/download/historico-nombres.zip", p)
    with zipfile.ZipFile(p) as z, z.open("historico-nombres.csv") as fh:
        tot = collections.Counter()
        for r in csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8", errors="replace")):
            tot[r["nombre"]] += num(r["cantidad"])
    for n, c in tot.items(): yield n, "?", c

def name_lists():
    for r in csv.DictReader(open(os.path.join(DATA, "name-lists.tsv"), encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
        if r["status"] == "rejected": continue
        yield r["name"], {"f": "f", "m": "m", "u": "u"}.get(r["gender"], "?"), num(r["count"]), r["country"].lower()

IBGE22 = "https://servicodados.ibge.gov.br/api/v3/nomes/2022/localidade/0/ranking/nome?sexo={}&page={}"
def ibge_2022():
    # IBGE Censo 2022 names API: every name given to 20+ people, by sex, 30 per page (about 4,500 pages). Each page is kept
    # as one line of raw/br-ibge-2022/<F|M>.jsonl, so an interrupted run picks up where it stopped. Half a second between pages.
    d = os.path.join(RAW, "br-ibge-2022"); os.makedirs(d, exist_ok=True)
    for sx in "FM":
        p = os.path.join(d, f"{sx}.jsonl")
        done = {json.loads(l)["page"]: json.loads(l) for l in open(p, encoding="utf-8")} if os.path.exists(p) else {}
        if not OFFLINE:
            total = max([v["totalPages"] for v in done.values()] or [None]) if done else None
            page = 1
            with open(p, "a", encoding="utf-8") as fh:
                while total is None or page <= total:
                    if page not in done:
                        for attempt in range(6):
                            try:
                                with urllib.request.urlopen(urllib.request.Request(IBGE22.format(sx, page), headers=UA), timeout=60) as r: body = r.read()
                                res = json.loads(gzip.decompress(body) if body[:2] == b"\x1f\x8b" else body)
                                break
                            except Exception as e:
                                print(f"    ibge {sx} p{page}: {e}; retrying", flush=True); time.sleep(10 * (attempt + 1))
                        else: raise SystemExit("IBGE names API kept failing")
                        fh.write(json.dumps(res, ensure_ascii=False) + "\n"); fh.flush(); done[page] = res
                        if page % 200 == 0: print(f"    ibge 2022 {sx}: page {page:,} of {res['totalPages']:,}", flush=True)
                        time.sleep(0.5)
                    total = done[page]["totalPages"]; page += 1
        for res in done.values():
            for it in res["items"]: yield it["nome"], sx.lower(), it["frequencia"]

def brazil():
    # Censo 2010: the IBGE names API (servicodados.ibge.gov.br/api/v2/censos/nomes) only ranks the top 20 per query; brasil.io's
    # genero-nomes dataset is every name that API returns, with its female and male counts (frequency_female/male).
    # Censo 2022 is added the same way; both count the people alive then, so per name and sex the larger count is kept, not the sum
    p = get("https://data.brasil.io/dataset/genero-nomes/nomes.csv.gz", os.path.join(RAW, "br-nomes.csv.gz"))
    best = collections.Counter()
    for r in csv.DictReader(io.StringIO(gzip.decompress(open(p, "rb").read()).decode("utf-8"))):
        for sx, col in (("f", "frequency_female"), ("m", "frequency_male")):
            c = num(r[col]); k = (r["first_name"].title(), sx)
            if c: best[k] = max(best[k], c)
    for n, sx, c in ibge_2022():
        k = (n.title(), sx); best[k] = max(best[k], c)
    for (n, sx), c in best.items(): yield n, sx, c

def chile():
    p = get("https://raw.githubusercontent.com/rivaquiroga/guaguas/main/data-raw/1920-2021.csv", os.path.join(RAW, "cl.csv"))
    for r in csv.DictReader(open(p, encoding="utf-8")):
        yield r["nombre"], "f" if r["sexo"] == "F" else "m" if r["sexo"] == "M" else "?", num(r["n"])

WD_CLASSES = {"Q202444": "?", "Q11879590": "f", "Q12308941": "m", "Q3409032": "u"}
WD_RANGES = [0, 1_000_000, 3_000_000, 6_000_000, 10_000_000] + list(range(20_000_000, 140_000_001, 10_000_000)) + [200_000_000]
def wikidata():
    # every item that is a given name (or a female / male / unisex given name), with every Latin-script spelling Wikidata
    # records for it: its label in any language, its aliases, and its native label (P1705). One query per class and
    # item-number range, so each stays small.
    d = os.path.join(RAW, "wd-given-names-latin"); os.makedirs(d, exist_ok=True)
    def fetch(cls, lo, hi):
        p = os.path.join(d, f"{cls}-{lo}-{hi}.tsv")
        if os.path.exists(p) or OFFLINE: return
        if any(re.fullmatch(rf"{cls}-(\d+)-(\d+)\.tsv", f) and lo <= int(f.split("-")[1]) < hi for f in os.listdir(d)):
            mid = (lo + hi) // 2; fetch(cls, lo, mid); fetch(cls, mid, hi); return   # split on an earlier run
        q = f"""SELECT DISTINCT ?item ?l WHERE {{
  ?item wdt:P31 wd:{cls} .
  FILTER(STRSTARTS(STR(?item), "http://www.wikidata.org/entity/Q"))
  BIND(xsd:integer(STRAFTER(STR(?item), "entity/Q")) AS ?id)
  FILTER(?id >= {lo} && ?id < {hi})
  {{ ?item rdfs:label ?lab }} UNION {{ ?item skos:altLabel ?lab }} UNION {{ ?item wdt:P1705 ?lab }}
  BIND(STR(?lab) AS ?l)
  FILTER(REGEX(?l, "^[A-Za-zÀ-ɏḀ-ỿ' -]+$"))
}}"""
        for attempt in range(3):
            try:
                req = urllib.request.Request("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"}), headers=UA)
                with urllib.request.urlopen(req, timeout=120) as r: res = json.loads(r.read().decode("utf-8"), strict=False)["results"]["bindings"]
                break
            except Exception as e:
                print(f"    wd {cls} Q{lo:,}-Q{hi:,}: {e}; retrying", flush=True); time.sleep(10 * (attempt + 1))
        else:
            # the answer is cut off when a range is too big: split it in two
            if hi - lo < 1000: raise SystemExit("Wikidata query service kept failing")
            mid = (lo + hi) // 2; fetch(cls, lo, mid); fetch(cls, mid, hi); return
        with open(p, "w", encoding="utf-8") as fh:
            for b in res: fh.write(f"{b['item']['value'].rsplit('/', 1)[1]}\t{cls}\t{' '.join(b['l']['value'].split())}\n")
        print(f"    wd {cls} Q{lo:,}-Q{hi:,}: {len(res):,} labels", flush=True)
        time.sleep(2)
    for cls in WD_CLASSES:
        for lo, hi in zip(WD_RANGES, WD_RANGES[1:]): fetch(cls, lo, hi)
    items = collections.defaultdict(lambda: [set(), set()])
    for f in sorted(os.listdir(d)):
        for line in open(os.path.join(d, f), encoding="utf-8"):
            q, cls, lab = line.rstrip("\n").split("\t")
            items[q][0].add(WD_CLASSES[cls]); items[q][1].add(lab)
    for q, (sexes, labs) in items.items():
        s = sexes - {"?"}
        sx = "u" if "u" in s or s == {"f", "m"} else s.pop() if s else "?"
        for lab in labs: yield lab, sx, 0

def jmnedict():
    p = get("http://ftp.edrdg.org/pub/Nihongo/JMnedict.xml.gz", os.path.join(RAW, "JMnedict.xml.gz"))
    import xml.etree.ElementTree as ET
    # entities (&fem; etc.) are declared in the DTD; read them as plain text
    text = gzip.open(p, "rt", encoding="utf-8").read()
    text = re.sub(r"<!DOCTYPE.*?\]>", "", text, flags=re.S)
    text = re.sub(r"&(\w[\w-]*);", r"\1", text)
    for _, el in ET.iterparse(io.StringIO(text)):
        if el.tag != "entry": continue
        for tr in el.findall("trans"):
            types = {t.text for t in tr.findall("name_type")}
            sx = "f" if types == {"fem"} else "m" if types == {"masc"} else "u" if types >= {"fem", "masc"} else "?" if "given" in types else None
            if sx is None: continue
            for d in tr.findall("trans_det"):
                for part in re.split(r"\s*[,;/]\s*", re.sub(r"\(.*?\)", "", d.text or "")):
                    if part and " " not in part.strip(): yield part.strip(), sx, 0
        el.clear()

def france():
    # INSEE, fichier des personnes décédées (Licence Ouverte): everyone who died in France since 1970, with all their given
    # names ("MARTIN*JOSEPHINE FRANCOISE/") and sex (1 man, 2 woman). Every given name counts, first or not. The yearly
    # files are ~6 GB in all, so each is streamed once and only its name counts are kept: raw/fr-deces/deces-YYYY.tsv
    d = os.path.join(RAW, "fr-deces"); os.makedirs(d, exist_ok=True)
    if not OFFLINE:
        with urllib.request.urlopen(urllib.request.Request("https://www.data.gouv.fr/api/1/datasets/fichier-des-personnes-decedees/", headers=UA), timeout=60) as r:
            res = json.load(r)["resources"]
        for r in res:
            m = re.fullmatch(r"deces-(\d{4})\.txt", r["title"])
            out = m and os.path.join(d, f"deces-{m.group(1)}.tsv")
            if not out or os.path.exists(out): continue
            c = collections.Counter()
            for attempt in range(4):
                try:
                    c.clear()
                    with urllib.request.urlopen(urllib.request.Request(r["url"], headers=UA), timeout=300) as fh:
                        for line in io.TextIOWrapper(fh, encoding="latin-1"):
                            nm, sx = line[:80], line[80:81]
                            if "*" not in nm: continue
                            for tok in nm.split("*", 1)[1].split("/", 1)[0].split():
                                c[(tok, "m" if sx == "1" else "f" if sx == "2" else "?")] += 1
                    break
                except Exception as e:
                    print(f"    {r['title']}: {e}; retrying", flush=True); time.sleep(20)
            else: raise SystemExit(f"could not read {r['url']}")
            with open(out, "w", encoding="utf-8") as fh:
                for (tok, sx), n in c.items(): fh.write(f"{tok}\t{sx}\t{n}\n")
            print(f"    {r['title']}: {sum(c.values()):,} given names", flush=True)
    for f in sorted(os.listdir(d)):
        for line in open(os.path.join(d, f), encoding="utf-8"):
            tok, sx, n = line.rstrip("\n").split("\t"); yield tok, sx, int(n)

def wiktionary():
    # English Wiktionary (CC BY-SA 4.0): every entry in a "<language> given names" category or one of its subcategories
    # ("<language> male given names", diminutives, "English renderings of ..."), for every language. The "... from <language>"
    # origin subcategories are skipped: their entries are almost always in the plain category too. Only page titles are used.
    # One request at a time, a second apart, maxlag. Each finished category is appended to raw/wikt-given-names.part
    # (so a stopped run resumes); the finished list is raw/wikt-given-names.tsv (title, category).
    p = os.path.join(RAW, "wikt-given-names.tsv"); part = os.path.join(RAW, "wikt-given-names.part")
    if not os.path.exists(p) and not OFFLINE:
        def api(**q):
            q.update(format="json", maxlag="5")
            for attempt in range(30):
                try:
                    time.sleep(1)
                    with urllib.request.urlopen(urllib.request.Request("https://en.wiktionary.org/w/api.php?" + urllib.parse.urlencode(q), headers=UA), timeout=90) as r: d = json.load(r)
                    if d.get("error", {}).get("code") == "maxlag": time.sleep(15); continue
                    return d
                except Exception as e:
                    print(f"    wikt: {e}; waiting", flush=True); time.sleep(60 if "429" in str(e) else 10)
            raise SystemExit("Wiktionary API kept failing")
        done = {}   # category → (its pages, its subcategories)
        if os.path.exists(part):
            for line in open(part, encoding="utf-8"):
                c = json.loads(line); done[c["cat"]] = (c["pages"], c["subcats"])
        seen, queue = {"Category:Given names by language"}, ["Category:Given names by language"]
        with open(part, "a", encoding="utf-8") as fh:
            while queue:
                cat = queue.pop()
                if cat not in done:
                    pages, subs, cont = [], [], {}
                    while True:
                        d = api(action="query", list="categorymembers", cmtitle=cat, cmlimit=500, cmtype="page|subcat", **cont)
                        for m in d["query"]["categorymembers"]:
                            if m["ns"] == 14: subs.append(m["title"])
                            elif m["ns"] == 0: pages.append(m["title"])
                        if "continue" not in d: break
                        cont = d["continue"]
                    done[cat] = (pages, subs)
                    fh.write(json.dumps({"cat": cat, "pages": pages, "subcats": subs}, ensure_ascii=False) + "\n"); fh.flush()
                    if len(done) % 100 == 0: print(f"    wikt: {len(done):,} categories read, {len(queue):,} queued", flush=True)
                for t in done[cat][1]:
                    if "given names" in t and "surname" not in t and " from " not in t and t not in seen: seen.add(t); queue.append(t)
        with open(p, "w", encoding="utf-8") as fh:
            for cat in seen - {"Category:Given names by language"}:
                for t in done[cat][0]: fh.write(f"{t}\t{cat[9:]}\n")
    if not os.path.exists(p): return
    for line in open(p, encoding="utf-8"):
        t, c = line.rstrip("\n").split("\t")
        sx = "u" if "unisex" in c else "f" if "female" in c else "m" if "male" in c else "?"
        yield t, sx, 0

def italy():
    tot = collections.Counter()
    for f in glob.glob(os.path.join(RAW, "it-istat-contanomi", "*-[fm].json")):
        d = json.load(open(f, encoding="utf-8"))
        for n, c in d["rows"]:
            # "FRANCESCO D'ASSISI": d' is a particle, not a name; NICOLO' (= Nicolò) loses its apostrophe in clean()
            n = " ".join(w for w in n.split() if not re.match(r"(?i)de?'", w))
            if n: tot[(n, d["sex"])] += int(c)
    for (n, sx), c in tot.items():
        if sum(tot[(n, s)] for s in "fm") >= 2: yield n, sx, c

def turkey():
    best = collections.Counter()
    for line in open(os.path.join(RAW, "tr", "tr-tuik-cocuk-names-2014-2025.tsv"), encoding="utf-8"):
        if line.startswith("#"): continue
        y, g, sx, rk, n, v = line.rstrip("\n").split("\t")
        k = (n, g, sx); best[k] = max(best[k], int(v or 0))   # the same children recur year after year: keep the largest count
    for (n, g, sx), c in best.items(): yield n, sx, c

def taiwan():
    from cedict_pinyin import pinyin
    best = collections.Counter()
    for line in open(os.path.join(RAW, "tw", "tw-moi-112-names.tsv"), encoding="utf-8"):
        if line.startswith("#"): continue
        tab, sx, per, rk, n, v = line.rstrip("\n").split("\t")
        if tab != "t56": best[(n, sx)] = max(best[(n, sx)], int(v))   # t50/t51 already count everyone; t56 is a slice of them
        else: best[(n, sx)] = max(best[(n, sx)], 0)
    for (n, sx), c in best.items():
        p = pinyin(n)
        if p: yield p, sx, c

def belgium():
    for r in csv.DictReader(open(os.path.join(RAW, "be-statbel", "names-1995-2025.tsv"), encoding="utf-8"), delimiter="\t"):
        yield r["name"], r["sex"], num(r["births"])

def spain():
    for line in open(os.path.join(RAW, "es", "es-ine-nombres-ge20.tsv"), encoding="utf-8"):
        if line.startswith("#"): continue
        sx, n, c = line.rstrip("\n").split("\t"); yield n, sx, int(c)

def sweden():
    d = json.load(open(os.path.join(RAW, "se", "se-scb-TAB622-tilltalsnamn-min10-metadata.json"), encoding="utf-8"))
    for code, n in d["dimension"]["Tilltalsnamn"]["category"]["label"].items():
        yield n.replace("’", "'"), "f" if code.endswith("K") else "m", 0

SOURCES = [("ar", "RENAPER Argentina 1922-2015", argentina), ("lists", "official name lists (data/name-lists.tsv)", name_lists),
           ("br", "IBGE Censo 2010 + 2022 (Brazil)", brazil), ("cl", "Registro Civil Chile 1920-2021", chile),
           ("wd", "Wikidata given names", wikidata), ("jp", "JMnedict given names", jmnedict),
           ("fr", "INSEE deaths file 1970-2025 (France)", france),
           ("wikt", "Wiktionary given names, all languages", wiktionary),
           ("it", "ISTAT Conta nomi 1999-2024 (Italy)", italy), ("tr", "TÜİK İstatistiklerle Çocuk 2014-2025 (Türkiye)", turkey),
           ("tw", "Ministry of the Interior name statistics 2023 (Taiwan), CC-CEDICT pinyin", taiwan),
           ("be", "Statbel first names of newborns 1995-2025 (Belgium)", belgium), ("es", "INE names with 20+ residents (Spain)", spain),
           ("se", "Statistics Sweden TAB622 tilltalsnamn with 10+ bearers", sweden)]

# pieces of a compound given name that are never names on their own: particles, and the connecting words of devotional
# names ("María de los Ángeles", "Ana del Sagrado Corazón", "José de San Martín")
NOT_NAMES = {fold(w) for w in PARTICLES} | {"a", "al", "o", "u", "i", "lo", "los", "las", "den", "ten", "ter", "het", "st", "ste", "sta",
    "san", "santa", "santo", "santos", "sao", "sagrado", "sagrada", "corazon", "dios", "nuestra", "senora", "senor", "nino", "jesus",
    "nombre", "hijo", "hija", "ii", "iii", "jr", "sr"}

def one_source(cc, gen):
    """this source's names, one name per entry: key → [display, f, m, ?, countries]"""
    raw = collections.defaultdict(lambda: [collections.Counter(), 0, 0, 0, set(), set()])
    for t in gen():
        n, sx, c = t[:3]; ccs = t[3] if len(t) > 3 else cc
        n = clean(n)
        if not n: continue
        e = raw[key(n)]; e[0][n] += max(c, 0)
        e[{"f": 1, "m": 2}.get(sx, 3)] += c
        if sx == "u": e[1] += c // 2; e[2] += c - c // 2; e[3] -= c
        e[4].add(ccs); e[5].add(sx)
    singles = {k: v for k, v in raw.items() if not SPLIT.search(k)}
    for k, v in raw.items():
        if not SPLIT.search(k): continue
        disp = v[0].most_common(1)[0][0]
        for w in {p for p in SPLIT.split(disp) if p}:
            if fold(w) in NOT_NAMES or not clean(w): continue
            s = singles.get(key(w))
            if s is None: s = singles[key(w)] = [collections.Counter(), 0, 0, 0, set(), set()]
            s[0][clean(w)] += sum(v[0].values()); s[1] += v[1]; s[2] += v[2]; s[3] += v[3]; s[4] |= v[4]; s[5] |= v[5]
    return singles

if __name__ == "__main__":
    db = {fold(l.split("\t", 1)[0]) for l in open(DB, encoding="utf-8") if l.strip()}
    storied = set()
    for f in ["scripture-names", "bible-extra", "culture-names", "also-cultures", "medieval-names", "az-names", "hebrew-names", "russia-cultures"]:
        storied |= {fold(r[0]) for r in json.load(open(os.path.join(DATA, f + ".json"), encoding="utf-8"))}
    ea = json.load(open(os.path.join(DATA, "east-asian-names.json"), encoding="utf-8"))
    storied |= {fold(r[0]) for lang in ("ja", "ko", "zh") for r in ea.get(lang, [])}
    print(f"names-db: {len(db):,} folded · storied lists add {len(storied - db):,} more")

    extra = {}   # folded → {"disp": Counter, "f","m","?" people, "cc": set, "sx": sexes seen}
    report = []
    goal = int(next((a.split("=")[1] for a in sys.argv if a.startswith("--goal=")), 1_000_000))
    for cc, label, gen in SOURCES:
        total = len(db | set(extra) | storied)
        if total >= goal * 1.02:
            print(f"total {total:,} passes {goal:,}: {label} not needed"); break
        singles = one_source(cc, gen)
        new = []
        for k, (disp, f, m, u, ccs, sxs) in singles.items():
            fk = fold(disp.most_common(1)[0][0])
            if fk in db or len(fk) < 2: continue
            e = extra.get(fk)
            if e is None:
                e = extra[fk] = {"disp": collections.Counter(), "f": 0, "m": 0, "?": 0, "cc": set(), "sx": set()}
                new.append(disp.most_common(1)[0][0])
            for n, c in disp.items(): e["disp"][n] += c + 1   # +1 so names with no counts still vote for their spelling
            e["f"] += f; e["m"] += m; e["?"] += max(u, 0); e["cc"] |= ccs; e["sx"] |= sxs
        report.append((cc, label, len(singles), len(new), new))
        print(f"  {cc:6} {label}: {len(singles):,} single names · {len(new):,} new · total now {len(db | set(extra) | storied):,}", flush=True)

    rows = []
    for fk, e in extra.items():
        disp = max(e["disp"].items(), key=lambda kv: (kv[1], kv[0] != kv[0].lower()))[0]
        f, m = e["f"], e["m"]
        if f + m: g = "f" if f >= .8 * (f + m) else "m" if m >= .8 * (f + m) else "u"
        else:
            s = e["sx"]   # sources without counts (approved lists, Wikidata, JMnedict) still give the class
            g = "u" if "u" in s or s >= {"f", "m"} else "f" if s == {"f"} else "m" if s == {"m"} else "?"
        rows.append((disp, g, ",".join(sorted(e["cc"])), f + m + e["?"]))
    rows.sort(key=lambda r: (-r[3], r[0]))
    with open(OUT, "w", encoding="utf-8") as fh:
        for r in rows: fh.write(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\n")
    allk = db | {fold(r[0]) for r in rows} | storied
    print(f"\n{len(rows):,} new names → {OUT} ({os.path.getsize(OUT) / 1e6:.1f} MB)")
    print(f"distinct real names: names-db {len(db):,} ∪ names-extra {len(rows):,} ∪ storied {len(storied):,} = {len(allk):,}")
    import random
    for cc, label, tot, n, new in report:
        random.seed(cc); print(f"  {cc}: {n:,} new · e.g. {', '.join(random.sample(new, min(15, len(new))))}")
