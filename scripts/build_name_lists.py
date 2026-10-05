#!/usr/bin/env python3
"""Official government first-name lists -> data/name-lists.tsv (+ data/name-list-relations.tsv).

These lists say a name is APPROVED, RECOGNISED, REGISTERED or USED in a country.
They say nothing about where a name comes from (origin) and are kept apart from
newborn popularity. Approved-in-a-country != used-in-a-country != originating-there.

Run:  python3 scripts/build_name_lists.py          (downloads anything missing into raw/official-lists/)
      python3 scripts/build_name_lists.py --offline (only use what is already in raw/official-lists/)

Lists (list id -> source):
  dk-approved          Familieretshuset (Denmark), approved first names (navneapi behind the official lists)
  cz-recognised        Ministerstvo vnitra (Czechia), Seznam jmen (CSV)
  be-population        Statbel (Belgium), first names of the total population by municipality, 1 Jan 2025
  cy-births            Ministry of Interior (Cyprus), list of births and names (data.gov.cy)
  fi-population        DVV (Finland), etunimitilasto: first names of living Finnish citizens (5+ bearers)
  hu-legal             HUN-REN/ELTE NYTK (Hungary), legal first-name register (10/2025 KIM)
  hu-minority-<lang>   Hungary, nationality name registers (11-23/2025 KIM, Magyar Kozlony 2025/101)
  is-approved / is-rejected / is-pending   Registers Iceland (island.is), Personal Names Register

Columns: name gender list country count region native status name_type
  gender  f | m | u
  count   empty when the list has no counts (never 0)
  status  approved | rejected | pending | empty   (rejected rows must never be suggested)
  name_type first | middle
"""
import collections, csv, json, os, re, sys, time, unicodedata, urllib.request, zipfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "scripts"))
import xlsx  # noqa: E402  (project's minimal xlsx reader)

RAW = os.path.join(HERE, "raw", "official-lists")
OUT = os.path.join(HERE, "data", "name-lists.tsv")
OUT_REL = os.path.join(HERE, "data", "name-list-relations.tsv")
DB = os.path.join(HERE, "data", "names-db.tsv")
OFFLINE = "--offline" in sys.argv
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"

# ---------------------------------------------------------------- downloads
SOURCES = {
    "dk-familieretshuset-godkendte-fornavne.json":
        "https://navneapi.familieretshuset.dk/api/Names?Pagination.PageNumber=1&Pagination.PageSize=120000"
        "&StartsWith=&MinLength=1&MaxLength=25&Contains=&EndsWith=&IsMale=true&IsFemale=true&IsUnisex=true",
    "cz-mvcr-seznam-jmen.csv": "https://archiv.mv.gov.cz/soubor/opendata-seznam-jmen-csv.aspx",
    "cz-mvcr-seznam-muzskych-jmen.xlsx": "https://archiv.mv.gov.cz/soubor/seznam-muzskych-jmen.aspx",
    "cz-mvcr-seznam-zenskych-jmen.xlsx": "https://archiv.mv.gov.cz/soubor/seznam-zenskych-jmen.aspx",
    "cz-mvcr-seznam-rodove-neutralnich-jmen.xlsx": "https://archiv.mv.gov.cz/soubor/seznam-rodove-neutralnich-jmen.aspx",
    # statbel.fgov.be sits behind an F5 bot challenge; these are the Internet Archive's
    # byte-for-byte captures of the official files (id_ = raw original bytes).
    "be-statbel-ta-pop-male-2025.xlsx":
        "https://web.archive.org/web/20250703082134id_/https://statbel.fgov.be/sites/default/files/files/opendata/"
        "Voornamen%20bevolking%20per%20gemeente/TA_POP_MALE_2025.xlsx",
    "be-statbel-ta-pop-female-2025.xlsx":
        "https://web.archive.org/web/20250703082013id_/https://statbel.fgov.be/sites/default/files/files/opendata/"
        "Voornamen%20bevolking%20per%20gemeente/TA_POP_FEMALE_2025.xlsx",
    "cy-moi-births-first-names-2016-10-25.dsv": "https://data.gov.cy/sites/default/files/openData25102016.dsv",
    "cy-moi-greek-names-romanisation.csv":
        "https://data.gov.cy/sites/default/files/%CE%A4%CF%85%CF%80%CE%BF%CF%80%CE%BF%CE%AF%CE%B7%CF%83%CE%B7"
        "%20%CE%95%CE%BB%CE%BB%CE%B7%CE%BD%CE%B9%CE%BA%CF%8E%CE%BD%20%CE%9F%CE%BD%CE%BF%CE%BC%CE%AC%CF%84%CF%89%CE%BD.csv",
    # avoindata.suomi.fi answers 403 to browser user agents but redirects plain clients to the file.
    "fi-dvv-etunimitilasto-2026-08-04.xlsx":
        "https://avoindata.suomi.fi/data/dataset/57282ad6-3ab1-48fb-983a-8aba5ff8d29a/resource/"
        "08c89936-a230-42e9-a9fc-288632e234f5/download/etunimitilasto-2026-08-04-dvv.xlsx",
    "pt-irn-lista-nomes-proprios.pdf":
        "https://irn.justica.gov.pt/Portals/33/Regras%20Nome%20Proprio/Lista%20Nomes%20Pr%C3%B3prios.pdf",
    "hu-nytud-utonevjegyzek-ferfi.txt": "https://file.nytud.hu/osszesffi.txt",
    "hu-nytud-utonevjegyzek-noi.txt": "https://file.nytud.hu/osszesnoi.txt",
    "hu-magyar-kozlony-2025-101-utonevjegyzekek.pdf":
        "https://magyarkozlony.hu/hivatalos-lapok/OTynYjVcFRtaP8gZ1DQD68ac9dc20c4ae/dokumentumok/"
        "740f528317d36e822d6ef927e986b20b4cd80fa2/letoltes",
}
PLAIN_UA = {"fi-dvv-etunimitilasto-2026-08-04.xlsx"}


def fetch(fname):
    path = os.path.join(RAW, fname)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    if OFFLINE:
        sys.exit("missing %s (run without --offline)" % path)
    os.makedirs(RAW, exist_ok=True)
    ua = "curl/8.4" if fname in PLAIN_UA else UA
    print("  downloading", fname, file=sys.stderr)
    req = urllib.request.Request(SOURCES[fname], headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=600) as r, open(path + ".part", "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
    os.replace(path + ".part", path)
    return path


def fetch_iceland():
    path = os.path.join(RAW, "is-island-mannanafnaskra.json")
    if os.path.exists(path):
        return path
    if OFFLINE:
        sys.exit("missing %s" % path)
    rows = {}
    for L in "AÁBCDÐEÉFGHIÍJKLMNOÓPQRSTUÚVWXYÝZÞÆÖ":
        q = {"query": "query($l:String!){ getIcelandicNameByInitialLetter(input:{initialLetter:$l})"
                      " { id icelandicName type status visible description verdict url } }",
             "variables": {"l": L}}
        req = urllib.request.Request("https://island.is/api/graphql", data=json.dumps(q).encode(),
                                     headers={"Content-Type": "application/json", "User-Agent": UA})
        for r in json.load(urllib.request.urlopen(req, timeout=60))["data"]["getIcelandicNameByInitialLetter"] or []:
            rows[r["id"]] = r
        time.sleep(0.3)
    json.dump(sorted(rows.values(), key=lambda r: r["id"]), open(path, "w"), ensure_ascii=False, indent=0)
    return path


# ---------------------------------------------------------------- helpers
def fold(s):
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c)).casefold().strip()


TURKISH = set("İıŞşĞğ")


def nice_case(s):
    """ANNA-MARIE / jiří / O'NEIL -> Anna-Marie / Jiří / O'Neil. Keeps every letter and diacritic."""
    s = re.sub(r"\s+", " ", s.strip())
    if any(c in TURKISH for c in s):
        low = s.replace("I", "ı").replace("İ", "i").lower()
    else:
        low = s.lower()
    out, up = [], True
    for i, c in enumerate(low):
        if up and c.isalpha():
            if c == "i" and any(ch in TURKISH for ch in s) and i < len(s) and s[i] == "İ":
                c = "İ"
            else:
                c = c.upper()
            up = False
        out.append(c)
        if c in " -":
            up = True
        elif c in "'’" and len(out) == 2:  # O'Neil, D'Arcy
            up = True
    return "".join(out)


# Latin look-alikes typed into Cyrillic / Greek words in the source PDFs and registers.
LAT2CYR = dict(zip("AaBCcEeHhKkMOoPpTXxyIiJjSs", "АаВСсЕеНнКкМОоРрТХхуІіЈјЅѕ"))
LAT2GRK = dict(zip("ABEZHIKMNOPTYX", "ΑΒΕΖΗΙΚΜΝΟΡΤΥΧ"))
homoglyph_fixes = collections.Counter()


def fix_script(s, tag):
    if re.search("[Ѐ-ӿ]", s) and re.search("[A-Za-z]", s):
        t = "".join(LAT2CYR.get(c, c) for c in s)
        if t != s:
            homoglyph_fixes[tag] += 1
        return t
    if re.search("[Ͱ-Ͽ]", s) and re.search("[A-Z]", s):
        t = "".join(LAT2GRK.get(c, c) for c in s)
        if t != s:
            homoglyph_fixes[tag] += 1
        return t
    return s


# ELOT 743 (= ISO 843 type 2) transliteration of upper-case Greek, used only when the
# Cyprus Ministry of Interior romanisation table has no entry for a name.
_V = set("ΑΕΗΙΟΥΩΆΈΉΊΌΎΏΪΫ")
_VOICED = set("ΒΓΔΖΛΜΝΡ") | _V
_SIMPLE = {"Α": "A", "Β": "V", "Γ": "G", "Δ": "D", "Ε": "E", "Ζ": "Z", "Η": "I", "Θ": "TH", "Ι": "I", "Κ": "K",
           "Λ": "L", "Μ": "M", "Ν": "N", "Ξ": "X", "Ο": "O", "Π": "P", "Ρ": "R", "Σ": "S", "Τ": "T", "Υ": "Y",
           "Φ": "F", "Χ": "CH", "Ψ": "PS", "Ω": "O", "Ϊ": "I", "Ϋ": "Y"}


def elot743(word):
    w = unicodedata.normalize("NFC", word.upper())
    w = "".join({"Ά": "Α", "Έ": "Ε", "Ή": "Η", "Ί": "Ι", "Ό": "Ο", "Ύ": "Υ", "Ώ": "Ω"}.get(c, c) for c in w)
    out, i = [], 0
    while i < len(w):
        c, n = w[i], (w[i + 1] if i + 1 < len(w) else "")
        nn = w[i + 2] if i + 2 < len(w) else ""
        start = i == 0 or not w[i - 1].isalpha()
        if c == "Γ" and n in "ΓΚΞΧ" and n:
            out.append({"Γ": "NG", "Κ": "GK", "Ξ": "NX", "Χ": "NCH"}[n]); i += 2; continue
        if c == "Μ" and n == "Π":
            end = not nn.isalpha()
            out.append("B" if start or end else "MP"); i += 2; continue
        if c == "Ο" and n == "Υ":
            out.append("OU"); i += 2; continue
        if c in "ΑΕΗ" and n == "Υ":
            out.append(_SIMPLE[c] + ("V" if nn in _VOICED and nn else "F")); i += 2; continue
        out.append(_SIMPLE.get(c, c)); i += 1
    return "".join(out)


# ---------------------------------------------------------------- readers
def sheet_names(path):
    wb = ET.fromstring(zipfile.ZipFile(path).read("xl/workbook.xml"))
    return [s.get("name") for s in wb.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet")]


ROWS = []   # dicts
RELS = []   # (name, relation, related_name, language, source)


def add(name, gender, lst, country, count=None, region="", native="", status="", name_type="first"):
    ROWS.append(dict(name=name, gender=gender, list=lst, country=country,
                     count="" if not count else str(count), region=region, native=native,
                     status=status, name_type=name_type))


def build_dk():
    d = json.load(open(fetch("dk-familieretshuset-godkendte-fornavne.json"), encoding="utf-8"))
    g = {"Female": "f", "Male": "m", "Unisex": "u"}
    for it in d["items"]:
        add(it["name"].strip(), g[it["gender"]], "dk-approved", "DK", status="approved")


def build_cz():
    path = fetch("cz-mvcr-seznam-jmen.csv")
    for p in ("cz-mvcr-seznam-muzskych-jmen.xlsx", "cz-mvcr-seznam-zenskych-jmen.xlsx",
              "cz-mvcr-seznam-rodove-neutralnich-jmen.xlsx"):
        fetch(p)  # kept for provenance; the CSV is the same list in machine-readable form
    g = {"ZENA": "f", "MUZ": "m", "NEUTRALNI": "u", "NEUTRÁLNI": "u"}
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            name = (r["JMENO"] or "").strip().rstrip("*").strip()
            if name:
                add(nice_case(name), g[r["DRUH_JMENA"].strip()], "cz-recognised", "CZ")


def be_region(nis):
    nis = nis.strip()
    if nis.startswith("21"):
        return "Brussels"
    if nis[:1] in "1347" or nis[:2] in ("23", "24"):
        return "Flanders"
    if nis[:1] in "5689" or nis[:2] == "25":
        return "Wallonia"
    return None


def build_be():
    for fname, gender in (("be-statbel-ta-pop-female-2025.xlsx", "f"), ("be-statbel-ta-pop-male-2025.xlsx", "m")):
        path = fetch(fname)
        tot, reg = collections.Counter(), collections.defaultdict(collections.Counter)
        for i, r in enumerate(xlsx.rows(path, sheet_names(path)[0])):
            if i == 0 or len(r) < 5 or not r[3]:
                continue
            n, c = r[3].strip(), int(float(r[4]))
            tot[n] += c
            rg = be_region(r[0] or "")
            if rg:
                reg[n][rg] += c
        for n, c in tot.items():
            region = ";".join("%s:%d" % (k, reg[n][k]) for k in ("Flanders", "Wallonia", "Brussels") if reg[n][k])
            add(n, gender, "be-population", "BE", c, region)


CY_DISTRICTS = {"ΛΕΥΚΩΣΙΑ": "Nicosia", "ΛΕΜΕΣΟΣ": "Limassol", "ΛΑΡΝΑΚΑ": "Larnaca", "ΠΑΦΟΣ": "Paphos",
                "ΑΜΜΟΧΩΣΤΟΣ": "Famagusta", "ΚΕΡΥΝΕΙΑ": "Kyrenia"}
CY_NOT_NAMES = {"-", "--", ".", "ΝΕΚΡΟ", "ΝΕΚΡΟΣ", "ΝΕΚΡΗ", "ΑΓΝΩΣΤΟ", "ΑΓΝΩΣΤΟΣ", "ΑΓΝΩΣΤΗ", "ΑΝΩΝΥΜΟ",
                "ΑΝΩΝΥΜΟΣ", "ΑΝΩΝΥΜΗ", "ΑΒΑΠΤΙΣΤΟ", "ΑΒΑΠΤΙΣΤΟΣ", "ΑΒΑΠΤΙΣΤΗ", "ΑΚΑΤΟΝΟΜΑΣΤΟ",
                "ΑΚΑΤΟΝΟΜΑΣΤΟΣ", "ΑΚΑΤΟΝΟΜΑΣΤΗ", "ΧΩΡΙΣ ΟΝΟΜΑ", "ΒΡΕΦΟΣ", "UNKNOWN", "BABY", "NN"}
cy_stats = collections.Counter()


def build_cy():
    std = {}
    with open(fetch("cy-moi-greek-names-romanisation.csv"), encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            std[r["GREEK_NAME"].strip()] = r["ROMAIKI_GRAFI"].strip()
    tot = collections.Counter()
    reg = collections.defaultdict(collections.Counter)
    sexmap = {"ΑΡΡΕΝ": "m", "ΘΗΛΥ": "f"}
    with open(fetch("cy-moi-births-first-names-2016-10-25.dsv"), encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\r\n").split(";")
            if len(p) < 4 or p[3] not in sexmap:
                cy_stats["no sex"] += 1
                continue
            n = re.sub(r"\s+", " ", p[0]).strip().upper()
            if not n or n in CY_NOT_NAMES or not re.search(r"[^\W\d_]", n):
                cy_stats["not a name"] += 1
                continue
            n = fix_script(n, "cy")
            key = (n, sexmap[p[3]])
            tot[key] += 1
            reg[key][CY_DISTRICTS.get(p[2].strip(), p[2].strip() or "unknown")] += 1
    for (n, g), c in tot.items():
        region = ";".join("%s:%d" % kv for kv in sorted(reg[(n, g)].items(), key=lambda kv: -kv[1]))
        if re.search("[Ͱ-Ͽ]", n):
            parts = n.split(" ")
            lat = []
            for w in parts:
                if w in std:
                    lat.append(std[w]); cy_stats["latin: MOI table"] += 1
                else:
                    lat.append(elot743(w)); cy_stats["latin: ELOT 743"] += 1
            add(nice_case(" ".join(lat)), g, "cy-births", "CY", c, region, native=n)
        else:
            add(nice_case(n), g, "cy-births", "CY", c, region)


def build_fi():
    path = fetch("fi-dvv-etunimitilasto-2026-08-04.xlsx")
    for sheet, g in (("Naiset kaikki", "f"), ("Miehet kaikki", "m")):
        for i, r in enumerate(xlsx.rows(path, sheet)):
            if i == 0 or len(r) < 2 or not r[0]:
                continue
            add(r[0].strip(), g, "fi-population", "FI", int(float(r[1])))


def build_hu_legal():
    for fname, g in (("hu-nytud-utonevjegyzek-noi.txt", "f"), ("hu-nytud-utonevjegyzek-ferfi.txt", "m")):
        with open(fetch(fname), encoding="utf-8-sig") as f:
            lines = [l.strip() for l in f]
        for l in lines[1:]:  # first line is the title ("... jegyzéke: női nevek -- 2025. július 31.")
            if l:
                add(l, g, "hu-legal", "HU", status="approved")


HU_LANGS = {"Bolgár": "bulgarian", "Görög": "greek", "Horvát": "croatian", "Lengyel": "polish", "Német": "german",
            "Örmény": "armenian", "Roma": "roma", "Román": "romanian", "Ruszin": "rusyn", "Szerb": "serbian",
            "Szlovák": "slovak", "Szlovén": "slovene", "Ukrán": "ukrainian"}
HU_REG = {"bulgarian": "11", "greek": "12", "croatian": "13", "polish": "14", "german": "15", "armenian": "16",
          "roma": "17", "romanian": "18", "rusyn": "19", "serbian": "20", "slovak": "21", "slovene": "22",
          "ukrainian": "23"}
hu_check = {}


def hu_segment(tables, lang, sect, items):
    t = tables.setdefault((lang, sect), {"letters": None, "rows": collections.defaultdict(list), "inline": {}})
    byy = collections.defaultdict(list)
    for y, x, s in items:
        byy[y].append((x, s.strip()))
    head_y = None
    for y, xs in byy.items():
        labels = sorted(xs)
        txt = [s for _, s in labels]
        if txt[:4] == ["A", "B", "C", "D"] or txt == ["A", "B C D"]:
            head_y = y
            if t["letters"] is None:
                t["letters"] = [x for x, s in labels if s in ("A", "B", "C", "D")]
    nums = {}  # row numbers (may be split into fragments like '6' '.')
    for y, xs in byy.items():
        left = "".join(s for x, s in sorted(xs) if x < 112 and re.fullmatch(r"[\d.\s]+", s)).replace(" ", "")
        m = re.match(r"^(\d+)\.?$", left)
        if m:
            nums[y] = int(m.group(1))
        else:
            for x, s in xs:
                mm = re.match(r"^(\d+)\.\s+(\S.*)$", s.strip())
                if x < 100 and mm:  # Greek table: whole row in one string
                    nums[y] = int(mm.group(1))
                    t["inline"][int(mm.group(1))] = mm.group(2)
    if head_y is not None:
        nums = {y: n for y, n in nums.items() if y < head_y}
    if not nums:
        return
    first_y, ghost = {}, set()  # some pages hold a second, shifted copy of the table: keep the first
    for y, n in nums.items():
        if n in first_y:
            ghost.add(y)
        else:
            first_y[n] = y
    ys = sorted(nums)
    top = max(ys) + 9
    other = tables.get((lang, "férfi" if sect == "női" else "női"), {})
    letters = next((L for L in (t["letters"], other.get("letters")) if L and len(L) == 4),
                   [175.0, 282.0, 380.0, 472.0])
    hist = collections.Counter(round(x) for y, x, s in items
                               if y <= top and not (x < 112 and re.fullmatch(r"[\d.\s]+", s.strip() or "x")))
    starts = []  # cells are left-aligned: each column's start is the commonest x just left of its letter
    for L in letters:
        cand = [(c, x) for x, c in hist.items() if L - 62 <= x <= L - 22 and c >= 3]
        starts.append(max(cand)[1] if cand else L - 41)
    for y, x, s in items:
        if y > 760 or y > top or (head_y is not None and y >= head_y):
            continue
        if x < 112 and (re.match(r"^\s*\d+\.?\s*$", s) or re.match(r"^\s*\d+\.\s+\S", s) or s.strip() == "."):
            continue
        ny = min(ys, key=lambda yy: abs(yy - y))
        if abs(ny - y) > 9 or ny in ghost:
            continue
        col = 0
        for i in range(1, 4):
            if x >= starts[i] - 3:
                col = i
        t["rows"][nums[ny]].append((y, x, s, col))


hu_stats = collections.Counter()


def _script(tok):
    letters = [ch for ch in tok if ch.isalpha()]
    if not letters:
        return None
    return "other" if any(ch >= "\u0370" for ch in letters) else "lat"


def split_spanning(s):
    """'Álekszánder Александер Álekszánder' -> three pieces; 'Богослав, Богосав  Bogoszláv' -> two."""
    out = []
    for chunk in re.split(r"\s{2,}", s):
        if not chunk.strip():
            continue
        toks = re.split(r"(\s+)", chunk)
        cur, cur_sc = "", None
        for tk in toks:
            sc = _script(tk)
            if sc and cur_sc and sc != cur_sc and cur.strip():
                out.append(cur)
                cur = ""
            cur += tk
            if sc:
                cur_sc = sc
        if cur.strip():
            out.append(cur)
    lead = s[: len(s) - len(s.lstrip())]
    return [lead + out[0]] + out[1:] if out else [s]


def name_list(cell):
    """'Adrijána, Adrijana' / 'Agnes/ Agnesz' / 'Hrajr Hrair' -> one name per variant; '-' -> []."""
    out = []
    for p in re.split(r"\s*[,;/]\s*", cell or ""):
        p = p.strip(" .-–")
        if not p or p in ("-", "–"):
            continue
        for w in p.split():
            if w[:1].isalpha() and w[:1].islower():
                return out  # running prose after the last table ("felhívja a ...")
        out.extend(p.split())  # these registers hold one-word names; a space separates variants
    return out


LOOK_LATIN = {"\u0570": "h", "\u0578": "n", "\u039f": "O", "\u03bf": "o", "\u0391": "A", "\u03b1": "a",
              "\u03bd": "n", "\u03b9": "i", "\u03bc": "m", "\u03b5": "e", "\u0395": "E", "\u0399": "I",
              "\u039a": "K", "\u03ba": "k", "\u039c": "M", "\u039d": "N", "\u03a1": "P", "\u03a4": "T",
              "\u03c4": "t", "\u03a5": "Y", "\u03a7": "X", "\u0392": "B", "\u0397": "H", "\u0396": "Z"}


def latinize(cell):
    """Latin names with a stray Greek/Armenian look-alike letter from the PDF font ('Joαννα' -> 'Joanna')."""
    out = []
    for w in re.split(r"(\s+)", cell):
        letters = [ch for ch in w if ch.isalpha()]
        lat = sum(1 for ch in letters if ch < "\u0250")
        if letters and 0 < lat < len(letters) and all(ch < "\u0250" or ch in LOOK_LATIN for ch in letters):
            w2 = "".join(LOOK_LATIN.get(ch, ch) for ch in w)
            if w2 != w:
                homoglyph_fixes["latin names"] += 1
            w = w2
        out.append(w)
    return "".join(out)


def build_hu_minority():
    import pypdf
    reader = pypdf.PdfReader(fetch("hu-magyar-kozlony-2025-101-utonevjegyzekek.pdf"))
    tables = collections.OrderedDict()   # (lang, sect) -> {"letters": [...], "rows": {num: [frags]}, "inline": {}}
    lang = sect = None
    for page in reader.pages:
        items = []

        def v(text, cm, tm, font, size):
            if text and text.strip():
                x = tm[4] * cm[0] + tm[5] * cm[2] + cm[4]
                y = tm[4] * cm[1] + tm[5] * cm[3] + cm[5]
                items.append([round(y, 1), round(x, 1), text])
        page.extract_text(visitor_text=v)
        width = float(page.mediabox.width)
        items = [it for it in items if 40 <= it[1] <= width]  # even pages carry an off-page ghost copy
        seen_pos, dedup = set(), []
        for it in items:  # some cells are drawn twice at the same spot
            k = (round(it[0]), round(it[1]))
            if k not in seen_pos:
                seen_pos.add(k)
                dedup.append(it)
        items = dedup
        numline = collections.OrderedDict()  # y -> [first index, joined digits]; numbers can be split ('1' '7.')
        for i, (y, x, txt) in enumerate(items):
            if x < 112 and re.fullmatch(r"[\d.\s]+", txt.strip() or "x"):
                e = numline.setdefault(y, [i, ""])
                e[1] += txt.strip()
        seen_num = {}
        for y, (i, val) in numline.items():  # a repeated row number starts a shifted second copy
            if not re.fullmatch(r"\d+\.", val):
                continue
            if val in seen_num and abs(seen_num[val] - y) > 1:
                items = items[:i]
                break
            seen_num[val] = y
        # split the page at section titles (a table can end and the next begin on one page)
        titles = []
        for y, x, s in items:
            m = re.search(r"(\w+) nemzetiségi utónévjegyzék\s*[–-]\s*(női|férfi)", s)
            if m and m.group(1) in HU_LANGS:
                titles.append((y, HU_LANGS[m.group(1)], m.group(2)))
            elif re.search(r"\b(rendelete|határozata)\s*$", s.strip()):  # next regulation or decision starts here
                titles.append((y, None, None))
        top_title = {}
        for y, l, sc in titles:  # titles are printed twice; cut once, at the higher copy
            top_title[(l, sc)] = max(y, top_title.get((l, sc), -1))
        cuts = sorted(((y, l, sc) for (l, sc), y in top_title.items()), reverse=True)
        items = [it for it in items if "nemzetiségi utónévjegyzék" not in it[2]]
        segs, cur, prev_y = [], (lang, sect), 10 ** 6
        for ty, l, sc in cuts:
            segs.append((cur, [it for it in items if ty + 3 < it[0] < prev_y]))
            cur, prev_y = (l, sc), ty + 3
        segs.append((cur, [it for it in items if it[0] < prev_y]))
        lang, sect = cur
        for (sl, ss), seg in segs:
            if sl:
                hu_segment(tables, sl, ss, seg)
    for (lang, sect), t in tables.items():
        g = "f" if sect == "női" else "m"
        lid = "hu-minority-" + lang
        src = "HU %s/2025 (IX. 3.) KIM" % HU_REG[lang]
        other = tables.get((lang, "férfi" if sect == "női" else "női"), {})
        letters = t["letters"] or other.get("letters") or [175.0, 282.0, 380.0, 472.0]
        allnums = set(t["rows"]) | set(t["inline"])
        nums = sorted(n for n in allnums if n >= 2 and (n - 1 in allnums or n + 1 in allnums))
        for n in sorted(allnums - set(nums) - {1}):
            print("  hu %s/%s: dropped stray row number %d" % (lang, sect, n), file=sys.stderr)
        hu_check[(lang, sect)] = (len(nums), (max(nums) - 1) if nums else 0)
        if os.environ.get("HU_DEBUG"):
            print(lang, sect, "missing:", sorted(set(range(2, max(nums) + 1)) - set(nums))[:40], file=sys.stderr)
        for n in nums:
            cells = ["", "", "", ""]
            frs = t["rows"].get(n, [])
            if n in t["inline"]:
                chunks = [c.strip() for c in re.split(r"\s{2,}", t["inline"][n]) if c.strip()]
                toks = chunks[0].split()
                gi = next((i for i, tk in enumerate(toks) if i and all(
                    "Ͱ" <= ch <= "Ͽ" for ch in tk if ch.isalpha())), len(toks))
                cells[0], cells[1] = " ".join(toks[:gi]), " ".join(toks[gi:])
                rest = chunks[1:]
                if len(rest) == 1:
                    cells[3] = rest[0]
                elif len(rest) >= 2:
                    cells[2], cells[3] = rest[0], " ".join(rest[1:])
                for y, x, s, _ in sorted(frs, key=lambda f: (-f[0], f[1])):
                    cells[3] = (cells[3] + " " + s.strip()).strip()
            else:
                parts = [[], [], [], []]
                for y, x, s, col in frs:
                    for k, piece in enumerate(split_spanning(s)):  # one string can run across columns
                        parts[min(col + k, 3)].append((y, x + k * 0.01, piece))
                for i, p in enumerate(parts):
                    txt, last_y = "", None
                    for y, x, s in sorted(p, key=lambda f: (-f[0], f[1])):
                        if last_y is not None and abs(y - last_y) > 2 and not txt.endswith("-"):
                            txt += " "
                        txt += s
                        last_y = y
                    cells[i] = re.sub(r"\s+", " ", txt).strip()
            # a cell can swallow its right-hand neighbours (Latin name + native script + transcription)
            for i in range(3):
                pieces = split_spanning(cells[i])
                if len(pieces) > 1:
                    cells[i] = pieces[0].strip()
                    for k, pc in enumerate(pieces[1:], 1):
                        j = min(i + k, 3)
                        cells[j] = (pc.strip() + " " + cells[j]).strip() if j > i else cells[j] + " " + pc
            toks = cells[0].split()
            if len(toks) == 3 and not cells[1] and not cells[2] and "," not in cells[0]:
                cells[0], cells[1], cells[2] = toks  # A B C printed as one string
            cells[0] = latinize(cells[0])
            cells[2] = latinize(cells[2])
            a, b, c, d = cells
            if re.search(r"\d", a):  # text after the last table (e.g. a government decision)
                continue
            names = name_list(a)
            if not names:
                hu_check.setdefault("empty", []).append((lang, sect, n))
                continue
            natives = [fix_script(x, lang) for x in name_list(b)]
            trans = name_list(c)
            eqs = name_list(d)
            hu_stats["rows"] += 1
            if len(names) > 1:
                hu_stats["cells with several names"] += 1
            for i, nm in enumerate(names):
                name = nice_case(nm) if nm.isupper() and len(nm) > 1 else nm
                if len(natives) == len(names):
                    native = natives[i]
                elif len(natives) == 1:
                    native = natives[0]
                else:
                    native = ", ".join(natives)
                if native.isupper() and len(native) > 1 and not re.search("[\u0370-\u03FF]", native):
                    native = nice_case(native)
                add(name, g, lid, "HU", status="approved", native=native if native and native != name else "")
                tr = trans[i] if len(trans) == len(names) else (trans[0] if len(trans) == 1 else "")
                if tr:
                    RELS.append((name, "transcription", nice_case(tr) if tr.isupper() and len(tr) > 1 else tr, lang, src))
                for eq in eqs:
                    RELS.append((name, "equivalent", nice_case(eq) if eq.isupper() and len(eq) > 1 else eq, lang, src))


def build_pt():
    """IRN 'Lista Nomes Próprios' (88 pages, two GÉNERO | NOME column pairs per page). Spellings kept exactly:
    Ágata and Agata are separate entries. The PDF has no 'não admitidos' (refused) section."""
    import pypdf
    txt = "\n".join(p.extract_text() for p in pypdf.PdfReader(fetch("pt-irn-lista-nomes-proprios.pdf")).pages)
    for g, n in re.findall(r"(Femininos|Masculinos)[ \t]+([^\n]*?)(?=[ \t]{2,}|[ \t]+(?:Femininos|Masculinos)\b|[ \t]*\n|$)",
                           txt):
        n = n.strip()
        if n:
            add(n, "f" if g == "Femininos" else "m", "pt-admitted", "PT", status="approved")


# Romania: DGEP (Direcția Generală pentru Evidența Persoanelor) name-day press releases, which print the number of
# people CURRENTLY in the population register per name. Only releases with a real text layer are used: most 2020-2023
# releases are scanned images, and OCR cannot reproduce ş/ţ/ș/ț exactly. Reference year = year of the release.
RO_RELEASES = {  # file in comunicate/<year>/ -> reference year
    "2018/2018-comunicat-4.pdf": 2018, "2019/2019-comunicat_1.pdf": 2019, "2019/2019-comunicat_4.pdf": 2019,
    "2019/2019-comunicat_7.pdf": 2019, "2019/2019_comunicat_11.pdf": 2019, "2019/2019_comunicat_12.pdf": 2019,
    "2019/2019_comunicat_13.pdf": 2019, "2022/2022-comunicat-2.pdf": 2022, "2022/2022-comunicat-7.pdf": 2022,
    "2022/2022-comunicat-8.pdf": 2022, "2023/2023-comunicat-26.pdf": 2023,
}
CENSUS = os.path.join(HERE, "data", "census-names.json")
ro_stats = collections.Counter()


def ro_release_rows(path):
    import pypdf
    txt = "\n".join((pg.extract_text() or "") for pg in pypdf.PdfReader(path).pages)
    order, rows = [], []
    pair = re.compile(r"([^\d\s][^\d]*?)\s+(\d{1,3}(?:\.\d{3})+|\d+)(?=\s|$)")
    for line in txt.splitlines():
        heads = re.findall(r"(?i)prenume\s+(masculine|feminine)", line)
        if heads:
            order = ["m" if h.lower() == "masculine" else "f" for h in heads]
            continue
        if not order or re.search(r"(?i)total|tel\.|fax|e-mail|obcina", line):
            continue
        pairs = pair.findall(line.strip())
        if not pairs:
            continue
        col0 = 1 if (len(order) == 2 and len(pairs) == 1 and re.match(r"^\s{2,}", line)) else 0
        for k, (name, cnt) in enumerate(pairs):
            sex = order[min(col0 + k, len(order) - 1)]
            name = re.sub(r"\s+([ăâîșțşţ])(?=$|/)", r"\1", name.strip())  # 'Mitric ă' -> 'Mitrică'
            name = re.sub(r"\s*/\s*", "/", name)
            if re.fullmatch(r"[^\W\d_][\w/ -]*", name):
                rows.append((sex, name, int(cnt.replace(".", ""))))
    return rows


def build_ro():
    census, best = [], {}
    for rel, year in RO_RELEASES.items():
        fn = os.path.basename(rel)
        SOURCES.setdefault(fn, "https://depabd.mai.gov.ro/comunicate/" + rel)
        path = os.path.join(RAW, "ro-dgep", fn)
        if not os.path.exists(path):
            if OFFLINE:
                sys.exit("missing " + path)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            req = urllib.request.Request(SOURCES[fn], headers={"User-Agent": UA})
            open(path, "wb").write(urllib.request.urlopen(req, timeout=120).read())
            time.sleep(1)
        rows = ro_release_rows(path)
        ro_stats["releases"] += 1
        for sex, name, cnt in rows:
            if re.search("[şţŞŢ]", name):
                ro_stats["names printed with cedilla ş/ţ"] += 1
            census.append({"place": "Romania", "source": "DGEP population register", "reference_year": year,
                           "sex": "boy" if sex == "m" else "girl", "age_group": "all", "municipality": None,
                           "rank": None, "name": name, "count": cnt})
            for i, spelling in enumerate(name.split("/")):
                k = (spelling, sex)
                single = "/" not in name
                if k not in best or year > best[k][0] or (single and not best[k][2]):
                    best[k] = (year, cnt if single else None, single)
    # merge into data/census-names.json: replace only the Romania rows, keep every other place untouched
    old = json.load(open(CENSUS, encoding="utf-8")) if os.path.exists(CENSUS) else []
    keep = [r for r in old if r.get("place") != "Romania"]
    census.sort(key=lambda r: (r["reference_year"], r["sex"], -r["count"], r["name"]))
    json.dump(keep + census, open(CENSUS, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    ro_stats["census rows"] = len(census)
    ro_stats["reference years"] = ",".join(str(y) for y in sorted({r["reference_year"] for r in census}))
    for (spelling, sex), (year, cnt, single) in best.items():
        add(spelling, sex, "ro-registered", "RO", cnt, status="registered")


IS_GENDER = {"ST": "f", "DR": "m", "KH": "u", "MI": "u", "RST": "f", "RDR": "m"}
IS_STATUS = {"Sam": "approved", "Haf": "rejected", "Óaf": "pending"}
is_stats = collections.Counter()


def build_is():
    for r in json.load(open(fetch_iceland(), encoding="utf-8")):
        if not r.get("visible"):
            is_stats["hidden on island.is (skipped)"] += 1
            continue
        status = IS_STATUS.get(r.get("status") or "")
        if not status:
            is_stats["no status given (skipped)"] += 1
            continue
        add(nice_case(r["icelandicName"]), IS_GENDER.get(r["type"], "u"), "is-" + status, "IS", status=status,
            name_type="middle" if r["type"] == "MI" else "first")


# ---------------------------------------------------------------- main
COLS = ["name", "gender", "list", "country", "count", "region", "native", "status", "name_type"]


def main():
    for step in (build_dk, build_cz, build_be, build_cy, build_fi, build_hu_legal, build_hu_minority, build_is,
                 build_pt, build_ro):
        print("·", step.__name__, file=sys.stderr)
        step()
    # one row per (name, gender, list, name_type); merge duplicates (sum counts)
    merged = collections.OrderedDict()
    for r in ROWS:
        k = (r["name"], r["gender"], r["list"], r["name_type"])
        if k in merged:
            m = merged[k]
            if r["count"] and (not m["count"] or int(r["count"]) > int(m["count"])) and r["native"]:
                m["native"] = r["native"]  # keep the native form of the bigger row
            elif not m["native"] and r["native"]:
                m["native"] = r["native"]
            if r["count"]:
                m["count"] = str(int(m["count"] or 0) + int(r["count"]))
            if r["region"] or m["region"]:
                reg = collections.Counter()
                for part in (m["region"] + ";" + r["region"]).split(";"):
                    if ":" in part:
                        kk, vv = part.rsplit(":", 1)
                        reg[kk] += int(vv)
                m["region"] = ";".join("%s:%d" % kv for kv in reg.most_common())
        else:
            merged[k] = dict(r)
    rows = sorted(merged.values(), key=lambda r: (r["list"], -int(r["count"] or 0), fold(r["name"]), r["gender"]))
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(COLS) + "\n")
        for r in rows:
            f.write("\t".join(r[c].replace("\t", " ") for c in COLS) + "\n")
    rels = sorted(set(RELS), key=lambda r: (r[3], fold(r[0]), r[1], fold(r[2])))
    with open(OUT_REL, "w", encoding="utf-8", newline="") as f:
        f.write("name\trelation\trelated_name\tlanguage\tsource\n")
        for r in rels:
            f.write("\t".join(r) + "\n")

    known = set()
    with open(DB, encoding="utf-8") as f:
        for line in f:
            known.add(fold(line.split("\t", 1)[0]))
    per = collections.defaultdict(list)
    for r in rows:
        per[r["list"]].append(r)
    print("\n%-26s %8s %8s %10s" % ("list", "rows", "names", "new-to-site"))
    for lst, rs in per.items():
        names = {fold(r["name"]) for r in rs}
        new = {n for n in names if n not in known}
        print("%-26s %8d %8d %10d" % (lst, len(rs), len(names), len(new)))
    allnames = {fold(r["name"]) for r in rows if r["status"] != "rejected"}
    print("%-26s %8d %8d %10d" % ("ALL (excl. rejected)", len(rows), len(allnames),
                                  len({n for n in allnames if n not in known})))
    print("\nrelations:", len(rels), collections.Counter(r[1] for r in rels))
    print("hu minority tables (parsed rows, expected rows):",
          {"%s/%s" % k: v for k, v in hu_check.items() if k != "empty"})
    if hu_check.get("empty"):
        print("hu rows with empty name:", hu_check["empty"][:20])
    print("homoglyph fixes (Latin letters inside Cyrillic/Greek words):", dict(homoglyph_fixes))
    print("hu minority:", dict(hu_stats))
    print("cyprus:", dict(cy_stats))
    print("iceland:", dict(is_stats))
    print("romania:", dict(ro_stats))
    print("\nwrote", OUT, "and", OUT_REL)


if __name__ == "__main__":
    main()
