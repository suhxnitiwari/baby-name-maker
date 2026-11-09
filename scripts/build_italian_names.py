# Italian names → data/italian-names.json, in the row format of data/culture-names.json:
#   [name, g ('g'|'b'|'e'), "Italian", "Italian", religions, meaning, story, texts, kind, also]
#
# Sources (all open):
#   English Wiktionary (CC BY-SA 4.0): every page in "Italian male / female / unisex given names", read for the Italian
#     section's etymology (Giulia ← Latin Iūlia, Gennaro ← Neapolitan ← Latin Iānuārius) and its English equivalent.
#   ISTAT, the Italian national statistics institute (CC BY 4.0, raw/it-istat-contanomi/, fetch_istat_names.py): babies
#     given each name since 1999. Names that are not on Wiktionary come in when 100+ babies got them and Italy gives at least
#     a quarter of everyone registered with the name in Italy and data/names-db.tsv together (Azzurra, Ilenia, Marika); a double
#     name (Maria Vittoria, Francesco Pio) needs 1,000+ babies, so one family's pairing never becomes a name.
# A meaning is only a gloss: the one in Wiktionary's etymology, else the one the site's own lists give the source word
# (data/latin-names.json for Latin, data/greek-names.json for Ancient Greek). Names already carded elsewhere keep their
# origin; this list adds the etymology, a meaning they lack, and the Italian count (app.js only fills what is empty).
#
#   python3 scripts/build_italian_names.py      (downloads raw/italian/wiktionary.json once)
import glob, json, os, re, sys, unicodedata, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "raw", "italian"); DATA = os.path.join(ROOT, "data"); OUT = os.path.join(DATA, "italian-names.json")
os.makedirs(RAW, exist_ok=True)

def plain(s): return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c))
def fold(s): return re.sub(r"[\s'-]", "", plain(s).lower())
def lfold(s): return fold(s).replace("j", "i").replace("v", "u")

WIKT = os.path.join(RAW, "wiktionary.json")
if not os.path.exists(WIKT):
    sys.path.insert(0, HERE); from fetch_wiktionary_names import members, pages
    mem = {c: members(c) for c in ("Italian male given names", "Italian female given names", "Italian unisex given names")}
    json.dump({"members": mem, "pages": pages(sorted({t for v in mem.values() for t in v}))}, open(WIKT, "w"), ensure_ascii=False)
W = json.load(open(WIKT, encoding="utf-8")); MEM, PAGES = W["members"], W["pages"]

LANG = {"la": "Latin", "la-lat": "Late Latin", "la-med": "Medieval Latin", "la-vul": "Vulgar Latin", "LL.": "Late Latin", "ML.": "Medieval Latin",
        "grc": "Ancient Greek", "gkm": "Byzantine Greek", "el": "Greek", "he": "Hebrew", "hbo": "Biblical Hebrew", "arc": "Aramaic", "ar": "Arabic",
        "gem": "Germanic", "gem-pro": "Proto-Germanic", "goh": "Old High German", "lng": "Lombardic", "got": "Gothic", "frk": "Frankish", "de": "German",
        "fr": "French", "fro": "Old French", "es": "Spanish", "pt": "Portuguese", "en": "English", "ru": "Russian", "pl": "Polish", "cel": "Celtic",
        "ett": "Etruscan", "nap": "Neapolitan", "scn": "Sicilian", "vec": "Venetian", "lmo": "Lombard", "fur": "Friulian", "sc": "Sardinian",
        "pms": "Piedmontese", "lij": "Ligurian", "co": "Corsican", "fa": "Persian", "sa": "Sanskrit", "non": "Old Norse", "ga": "Irish", "cy": "Welsh",
        "sla": "Slavic", "cu": "Old Church Slavonic", "hu": "Hungarian", "tr": "Turkish", "ja": "Japanese", "sq": "Albanian", "ro": "Romanian", "it": "Italian"}
SRC_T = re.compile(r"\{\{(inh\+?|der\+?|bor\+?|lbor|learned borrowing|m|l|uder|calque)\|([^{}]*)\}\}")

def section(txt):
    i = txt.find("==Italian==")
    if i < 0: return ""
    j = re.search(r"\n==[^=]", txt[i + 11:])
    return txt[i: i + 11 + j.start()] if j else txt[i:]

def chain(sec):
    """[(language, term, gloss)] from the etymology, oldest last: Gennaro ← Neapolitan Gennaro ← Latin Iānuārius"""
    ety = re.search(r"===Etymology[^=]*===\n(.*?)(?=\n===|\Z)", sec, re.S)
    if not ety: return []
    text = re.sub(r"\{\{ety\|[^{}]*\}\}", "", ety.group(1))
    if re.search(r"\b(possibly|perhaps|probably|uncertain|unknown|disputed|may be|might)\b", text, re.I): return []
    out = []
    for kind, args in SRC_T.findall(text):
        p = [a for a in args.split("|") if "=" not in a]; kw = dict(a.split("=", 1) for a in args.split("|") if "=" in a)
        if kind in ("m", "l", "uder"): lang, term, gloss = (p + ["", "", "", ""])[0], (p + ["", ""])[1], (p + ["", "", "", ""])[3] or kw.get("t", "")
        else: lang, term, gloss = (p + ["", "", "", "", ""])[1], (p + ["", "", "", ""])[2], (p + ["", "", "", "", ""])[4] or kw.get("t", "")
        if lang == "it" or not term or lang not in LANG: continue
        out.append((LANG[lang], term.split("<")[0].strip(), gloss.strip()))
    return out

# meanings the site already has for the source words
LATIN_M = {}
for r in json.load(open(os.path.join(DATA, "latin-names.json"), encoding="utf-8")):
    if not r[5]: continue
    LATIN_M.setdefault(lfold(r[0]), r[5])
    m = re.search(r"from Latin ([^\s,;(“]+)", r[6])
    if m: LATIN_M.setdefault(lfold(m.group(1)), r[5])
GREEK_M = {}
for r in json.load(open(os.path.join(DATA, "greek-names.json"), encoding="utf-8")):
    m = re.search(r"Written (\S+?)\.", r[6])
    if r[5] and m: GREEK_M.setdefault(plain(m.group(1)).lower(), r[5])
def meaning(src):
    for lang, term, gloss in src:
        if gloss: return gloss
        if "Latin" in lang and LATIN_M.get(lfold(term)): return LATIN_M[lfold(term)]
        if lang == "Ancient Greek" and GREEK_M.get(plain(term).lower()): return GREEK_M[plain(term).lower()]
    return ""

# ISTAT: babies per name and sex since 1999
ISTAT, SINCE = collections.defaultdict(collections.Counter), 9999
for f in glob.glob(os.path.join(ROOT, "raw", "it-istat-contanomi", "*.json")):
    d = json.load(open(f, encoding="utf-8")); SINCE = min(SINCE, d["year"])
    for n, k in d["rows"]: ISTAT[fold(n)][d["sex"]] += k
DISPLAY = {}
for f in glob.glob(os.path.join(ROOT, "raw", "it-istat-contanomi", "*.json")):
    for n, k in json.load(open(f, encoding="utf-8"))["rows"]: DISPLAY.setdefault(fold(n), " ".join(w.capitalize() for w in n.split()))
DB = {}
for line in open(os.path.join(DATA, "names-db.tsv"), encoding="utf-8"):
    n, g, cc, c = line.rstrip("\n").split("\t"); DB.setdefault(fold(n), int(c))
OTHER = {}          # folded name → the culture another of the site's lists gives it
for f in ("culture-names.json", "also-cultures.json", "arabia-names.json", "hindu-names.json", "caucasus-balkan-names.json", "persian-names.json"):
    p = os.path.join(DATA, f)
    if os.path.exists(p):
        for r in json.load(open(p, encoding="utf-8")):
            if isinstance(r, list) and len(r) > 2 and isinstance(r[0], str): OTHER.setdefault(fold(r[0]), r[2])
PLACEHOLDER = {"datomancante", "nonindicato", "ignoto", "sconosciuto"}
NOT_ITALIAN = {"suami", "suamy", "nohaila"}   # Swami and Nuhaila in Italian letters
TOTAL = {k: sum(c.values()) for k, c in ISTAT.items()}
def edits(w):   # every spelling one slip away: a letter dropped, doubled, swapped with its neighbour or changed
    a = "abcdefghilmnopqrstuvyz"
    out = {w[:i] + w[i + 1:] for i in range(len(w))} | {w[:i] + w[i + 1] + w[i] + w[i + 2:] for i in range(len(w) - 1)}
    out |= {w[:i] + c + w[i + 1:] for i in range(len(w)) for c in a} | {w[:i] + c + w[i:] for i in range(len(w) + 1) for c in a}
    return out - {w}
def typo(k, total):   # a registration slip of a far commoner name (Frnacesco, Alessnadro, Betarice)
    return any(TOTAL.get(e, 0) >= 50 * total for e in edits(k))
def babies(k):
    c = ISTAT.get(k)
    return f"given to {sum(c.values()):,} babies in Italy since {SINCE} (ISTAT)" if c and sum(c.values()) else ""

rows, seen = [], set()
sexes = collections.defaultdict(set)
for cat, g in (("Italian male given names", "b"), ("Italian female given names", "g"), ("Italian unisex given names", "e")):
    for t in MEM.get(cat, []): sexes[t].add(g)
for t in sorted(PAGES):
    sec = section(PAGES[t])
    if not sec or not sexes.get(t) or " " in t and not ISTAT.get(fold(t)): continue
    g = "e" if len(sexes[t]) > 1 or "e" in sexes[t] else next(iter(sexes[t]))
    src = chain(sec)
    eq = re.search(r"\{\{given name\|it\|[^{}]*\beq=([^|}]+)", sec)
    parts = []
    if src:
        lang, term, gloss = src[0]
        steps, had = [], set()
        for l, w, _ in src[:3]:
            if lfold(w) not in had: had.add(lfold(w)); steps.append(f"from {l} {w}")
        parts.append("An Italian name, " + ", ".join(steps))
    else:
        parts.append("An Italian name")
    if eq: parts[-1] += f"; the Italian form of {eq.group(1).split(',')[0].strip()}"
    parts[-1] += " (Wiktionary)"
    rows.append([t, g, "Italian", "Italian", "", meaning(src), parts[0] + ".", "", "real", []]); seen.add(fold(t))
    # the Italian count as its own line, so it reaches a name that already has a card (app.js adds "Given to …" lines)
    b = babies(fold(t))
    if b: rows.append([t, g, "Italian", "Italian", "", "", b[0].upper() + b[1:] + ".", "", "real", []])
wikt = len(rows)

# names given mostly in Italy, from ISTAT alone
for k, c in sorted(ISTAT.items(), key=lambda kv: -sum(kv[1].values())):
    n = DISPLAY[k]; total = sum(c.values())
    if k in seen or k in PLACEHOLDER or total < 100 or total < DB.get(k, 0) / 3: continue       # Italy gives at least a quarter of them
    if typo(k, total) or k in NOT_ITALIAN: continue
    if not re.fullmatch(r"[A-Za-zÀ-ÿ' ]+", n) or len(n) < 3: continue
    if " " in n and total < 1000: continue                   # established double names only (Maria Vittoria, Francesco Pio)
    # a name families from elsewhere give in Italy is theirs, not Italian: spellings Italian doesn't use (Klevis, Swami, Doaa,
    # Yassmine), or a name the site already files under another culture (Endri is Albanian)
    if re.search(r"[kwxj]|aa|yass", n.lower()) or OTHER.get(k, "Italian") not in ("Italian", "Latin", "Ancient Roman"): continue
    g = "e" if min(c["f"], c["m"]) >= .2 * total else "g" if c["f"] > c["m"] else "b"
    rows.append([n, g, "Italian", "Italian", "", "", f"An Italian name, given to {total:,} babies in Italy since {SINCE} (ISTAT).", "", "real", []])
    seen.add(k)
json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
names = len({r[0] for r in rows})
print(f"{names:,} names → {os.path.relpath(OUT, ROOT)} ({len({r[0] for r in rows[:wikt]}):,} from Wiktionary, {len(rows) - wikt:,} from ISTAT alone; "
      f"{sum(1 for r in rows if r[5]):,} with a meaning, {sum(1 for r in rows if ', from ' in r[6] or 'name, from' in r[6]):,} with an etymology)")
