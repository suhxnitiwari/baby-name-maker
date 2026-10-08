# Finnish, Finland-Swedish, Finnish Orthodox, Karelian and Sámi names → data/finnish-names.json, in the row format of
# data/culture-names.json:
#   [name, g ('g'|'b'|'e'), culture, language, religions, meaning, src, texts, kind, also]
#
# Nothing is guessed: every name, sex, culture and meaning is what a cited source states, and src says which source and era.
# One row per (name, culture). Usage and origin are kept apart: Pekka is a Finnish name (usage) and a vernacular form of
# Petrus (origin, as Wiktionary states it); a name is called a "Finnish word name" only when Wiktionary derives it from an
# ordinary Finnish word, and the word's own meaning is quoted.
#
# Sources (downloads cached in raw/finnish/; delete a file to fetch it again):
#   English Wiktionary (CC BY-SA 4.0): "<lang> male/female/unisex given names" and their subcategories (not the
#     "renderings of" ones) for Finnish, Northern Sami, Inari Sami, Skolt Sami, Karelian and Swedish, with each page's
#     wikitext; and the Finnish common-noun pages that word names come from, for their meaning when the name page
#     gives none.
#
# ease (11th slot): 1 = plain English letters as written; 2 = has letters like ä ö á š but the plain-letter spelling is
#   itself registered (names-db.tsv, names-extra.tsv or name-lists.tsv), stated in src as "Also written …"; 3 = otherwise.
# Rows are sorted by ease, then name.
#   Finnish Wiktionary (CC BY-SA 4.0): "Suomen kielen miesten/naisten etunimet", "Pohjoissaamen kielen miesten/naisten
#     etunimet", "Inarinsaamen kielen naisten etunimet", "Ruotsin kielen miesten/naisten etunimet" (name and sex only).
#   Wikidata (CC0): given-name items (P31 Q202444 / Q11879590 / Q12308941 / Q3409032) whose P407 is Finnish (Q1412),
#     Northern Sami (Q33947), Inari Sami (Q33462), Skolt Sami (Q13271), Karelian (Q33557) or Finland Swedish (Q1461092).
#   Finnish Wikipedia (CC BY-SA 4.0): the "Nimipäivät" section of the 366 day articles ("2. tammikuuta" …). Only the
#     Orthodox calendar (kept by the Orthodox Church of Finland) and the Sámi calendars (compiled by Pekka Sammallahti)
#     are used, as membership only (no dates). The Finnish and Finland-Swedish calendars are counted but NOT used: the
#     University of Helsinki holds catalogue copyright to them (Copyright Act s. 49, upheld by the Supreme Court in
#     2000) and allows free publication of at most two weeks or 15 names at a time
#     (https://almanakka.helsinki.fi/en/name-days/copyright-to-name-days/). Set USE_UH_CALENDARS only with a licence.
#     A calendar name is kept only when another source here gives its sex (Wiktionary, Wikidata, DVV).
#   University of Helsinki Almanac Office, name-day reform archive: the transcribed consistory minutes of the 1908 and 1929
#     almanac reforms (public documents, 1907 and 1927-29), listing old > new names for the Finnish- and the
#     Swedish-language almanac. The 1865, 1879 and 1881-83 proposals are only scans without a text layer (not used).
#     History page: https://almanakka.helsinki.fi/en/name-days (Aino in 1890; separate Swedish calendar in 1929).
#   DVV population names (data/name-lists.tsv, list fi-population): sex only, for names another source attests.
#   Kalevala (data/sacred/world.tsv, corpus Kalevala, built by build_sacred_world.py): marks names "In the Kalevala."
#
#   python3 scripts/build_finnish_names.py
import collections, csv, glob, json, os, re, sys, time, unicodedata, urllib.parse, urllib.request, calendar
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "raw", "finnish"); OUT = os.path.join(ROOT, "data", "finnish-names.json")
sys.path.insert(0, HERE)
from build_cultures import section, clean   # same Wiktionary section parsing as culture-names.json
UA = {"User-Agent": "Lullabyte/1.0 (https://github.com/suhxnitiwari/baby-name-maker; suhxnitiwari@gmail.com)"}
USE_UH_CALENDARS = False
NAME = re.compile(r"^[A-Za-zÀ-ɏʹ]+(?:-[A-Za-zÀ-ɏʹ]+)?$")

# ── polite fetching ──
def get(url, data=None):
    for attempt in range(12):
        try:
            req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode() if data else None, headers=UA)
            d = json.load(urllib.request.urlopen(req, timeout=180))
            if isinstance(d, dict) and d.get("error", {}).get("code") == "maxlag": time.sleep(10); continue
            return d
        except Exception as e:
            print("  retry", url[:70], e, file=sys.stderr); time.sleep(5 * (attempt + 1))
    raise RuntimeError("kept failing: " + url)
def wiki(host, **q):
    q.update(format="json", maxlag="5", formatversion="2")
    return get(f"https://{host}/w/api.php", q)
def members(host, cat, cmtype="page"):
    out, cont = [], {}
    while True:
        d = wiki(host, action="query", list="categorymembers", cmtitle=cat, cmlimit="500", cmtype=cmtype, **cont)
        out += [m["title"] for m in d.get("query", {}).get("categorymembers", [])]
        if "continue" not in d: return out
        cont = d["continue"]; time.sleep(.5)
def texts(host, titles):
    out = {}
    for i in range(0, len(titles), 50):
        d = wiki(host, action="query", prop="revisions", rvprop="content", rvslots="main", redirects="1", titles="|".join(titles[i:i + 50]))
        redir = {r["to"]: r["from"] for r in d.get("query", {}).get("redirects", [])}
        for p in d.get("query", {}).get("pages", []):
            t = ((p.get("revisions") or [{}])[0].get("slots", {}).get("main", {}).get("content", ""))
            out[p["title"]] = t
            if p["title"] in redir: out[redir[p["title"]]] = t
        time.sleep(1)
    return out
def cached(name, fetch):
    os.makedirs(RAW, exist_ok=True)
    path = os.path.join(RAW, name)
    if not os.path.exists(path):
        print("  fetching", name, flush=True)
        json.dump(fetch(), open(path, "w", encoding="utf-8"), ensure_ascii=False)
    return json.load(open(path, encoding="utf-8"))

# ── English Wiktionary categories ──
def fetch_en(lang):
    sex, cats = {}, collections.defaultdict(list)
    for g, label in (("b", "male"), ("g", "female"), ("e", "unisex")):
        todo, seen = [f"Category:{lang} {label} given names"], set()
        while todo:
            cat = todo.pop()
            if cat in seen: continue
            seen.add(cat)
            for t in members("en.wiktionary.org", cat):
                sex[t] = "e" if t in sex and sex[t] != g else g
                cats[t].append(cat.split(":", 1)[1])
            todo += [c for c in members("en.wiktionary.org", cat, "subcat") if "renderings of" not in c]
    tx = texts("en.wiktionary.org", sorted(sex))
    return {t: {"g": g, "cats": cats[t], "text": tx.get(t, "")} for t, g in sex.items()}

FI_WIKT = {"Suomen kielen miesten etunimet": ("Finnish", "b"), "Suomen kielen naisten etunimet": ("Finnish", "g"),
           "Pohjoissaamen kielen miesten etunimet": ("Northern Sami", "b"), "Pohjoissaamen kielen naisten etunimet": ("Northern Sami", "g"),
           "Inarinsaamen kielen naisten etunimet": ("Inari Sami", "g"),
           "Ruotsin kielen miesten etunimet": ("Swedish", "b"), "Ruotsin kielen naisten etunimet": ("Swedish", "g")}
def fetch_fi_wikt():
    return {cat: members("fi.wiktionary.org", "Luokka:" + cat) for cat in FI_WIKT}

WD_LANGS = {"Q1412": "Finnish", "Q33947": "Northern Sami", "Q33462": "Inari Sami", "Q13271": "Skolt Sami", "Q33557": "Karelian", "Q1461092": "Finland Swedish"}
WD_Q = """SELECT ?i ?cls ?L ?lab ?ll ?nl WHERE {
  VALUES ?L { %s } VALUES ?cls { wd:Q202444 wd:Q11879590 wd:Q12308941 wd:Q3409032 }
  ?i wdt:P407 ?L ; wdt:P31 ?cls .
  OPTIONAL { ?i rdfs:label ?lab FILTER(LANG(?lab) IN ("mul", "en", "fi", "se", "smn", "sms", "sv", "krl")) BIND(LANG(?lab) AS ?ll) }
  OPTIONAL { ?i wdt:P1705 ?nl } }""" % " ".join("wd:" + q for q in WD_LANGS)
def fetch_wd():
    d = get("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": WD_Q, "format": "json"}))
    items = {}
    for b in d["results"]["bindings"]:
        it = items.setdefault(b["i"]["value"].rsplit("/", 1)[1], {"cls": [], "langs": [], "labels": {}, "native": []})
        for k, key in (("cls", "cls"), ("L", "langs")):
            v = b[k]["value"].rsplit("/", 1)[1]
            if v not in it[key]: it[key].append(v)
        if "lab" in b: it["labels"][b["ll"]["value"]] = b["lab"]["value"]
        if "nl" in b:
            v = [b["nl"]["value"], b["nl"].get("xml:lang", "")]
            if v not in it["native"]: it["native"].append(v)
    return items

MONTHS = "tammikuuta helmikuuta maaliskuuta huhtikuuta toukokuuta kesäkuuta heinäkuuta elokuuta syyskuuta lokakuuta marraskuuta joulukuuta".split()
def fetch_days():
    titles = [f"{d}. {MONTHS[m - 1]}" for m in range(1, 13) for d in range(1, calendar.monthrange(2024, m)[1] + 1)]
    out = {}
    for i in range(0, len(titles), 50):
        d = wiki("fi.wikipedia.org", action="query", prop="revisions", rvprop="content|ids", rvslots="main", titles="|".join(titles[i:i + 50]))
        for p in d["query"]["pages"]:
            r = p["revisions"][0]; out[p["title"]] = {"revid": r["revid"], "text": r["slots"]["main"]["content"]}
        time.sleep(1)
    return out

# ── reading Wiktionary etymologies ──
LANGS = {"fi": "Finnish", "sv": "Swedish", "ru": "Russian", "la": "Latin", "LL.": "Late Latin", "ML.": "Medieval Latin", "grc": "Ancient Greek",
         "el": "Greek", "hbo": "Biblical Hebrew", "he": "Hebrew", "de": "German", "gmq-osw": "Old Swedish", "non": "Old Norse", "krl": "Karelian",
         "et": "Estonian", "en": "English", "fr": "French", "it": "Italian", "es": "Spanish", "ar": "Arabic", "no": "Norwegian", "da": "Danish",
         "se": "Northern Sami", "smn": "Inari Sami", "sms": "Skolt Sami", "arc": "Aramaic", "oc": "Occitan", "gml": "Middle Low German",
         "nds": "Low German", "gem": "Germanic", "orv": "Old East Slavic", "cu": "Old Church Slavonic", "is": "Icelandic", "hu": "Hungarian",
         "lt": "Lithuanian", "lv": "Latvian", "pl": "Polish", "cs": "Czech", "pt": "Portuguese", "nl": "Dutch", "ga": "Irish", "cy": "Welsh",
         "goh": "Old High German", "ang": "Old English", "fro": "Old French", "syc": "Classical Syriac", "fa": "Persian", "tr": "Turkish"}
HEDGE = re.compile(r"\b(uncertain|unknown|possibly|perhaps|probably|maybe|disputed|folk etymology)\b", re.I)
def render(t):
    """wikitext → plain text, keeping what the templates say"""
    t = re.sub(r"(?s)<ref[^>]*/>|<ref[^>]*>.*?</ref>|<!--.*?-->", "", t)
    def tpl(m):
        parts = [p.strip() for p in m.group(1).split("|")]
        name = parts[0]; kw = {p.split("=", 1)[0]: p.split("=", 1)[1] for p in parts[1:] if "=" in p}
        pos = [p for p in parts[1:] if "=" not in p]
        def word(term, alt="", gloss=""):
            w = alt or term
            w = "" if w == "-" else w
            g = gloss or kw.get("t") or kw.get("gloss") or ""
            lit = kw.get("lit")
            return (w + (f" '{g}'" if g else "") + (f" (literally '{lit}')" if lit else "")).strip()
        if name in ("m", "l", "ll", "m+", "l-self", "from", "mention"):
            return word(*(pos[1:4] + ["", "", ""])[:3])
        if name in ("der", "bor", "inh", "der+", "bor+", "inh+", "lbor", "slbor", "uder", "ubor", "cal", "calque", "sl"):
            lang = LANGS.get(pos[1], "") if len(pos) > 1 else ""
            return (lang + " " + word(*(pos[2:5] + ["", "", ""])[:3])).strip()
        if name in ("cog", "ncog", "noncog"):
            lang = LANGS.get(pos[0], "") if pos else ""
            return (lang + " " + word(*(pos[1:4] + ["", "", ""])[:3])).strip()
        if name in ("coin", "coinage"):
            who = (pos[1] if len(pos) > 1 else "").strip()
            return ("coined by " + who) if who else "coined"
        if name in ("suffix", "prefix", "af", "affix", "com", "compound", "com+", "blend"):
            ts = [kw.get(f"t{i + 1}") for i in range(len(pos) - 1)]
            return " + ".join(x + (f" '{t}'" if t else "") for x, t in zip(pos[1:], ts) if x and x != "-")
        if name in ("clipping", "clip", "short for", "abbreviation of", "back-form"):
            return ("clipping of " + pos[1]) if len(pos) > 1 else ""
        if name in ("m-g", "gloss", "gl"): return f"'{pos[0]}'" if pos else ""
        if name in ("w", "W", "lang", "q", "i", "qualifier"): return pos[-1] if pos else ""
        if name in ("taxlink", "taxfmt", "vern"): return pos[0] if pos else ""
        if name in ("unc", "uncertain"): return "Uncertain"
        if name in ("unk", "unknown"): return "Unknown"
        return ""
    for _ in range(3): t = re.sub(r"\{\{([^{}]*)\}\}", tpl, t)
    t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"<[^>]+>|'{3}|(?<!\w)'{2}(?!\w)", "", t)
    t = re.sub(r"\s*\(\s*\)", "", t)
    return re.sub(r"\s+", " ", t).strip()

def ety_of(sec):
    m = re.search(r"(?ms)^===+\s*Etymology[^=]*===+\s*$(.*?)(?=^===)", sec)
    return m.group(1).strip() if m else ""
def sentences(raw):
    raw = re.sub(r"(?s)<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", raw)
    raw = re.sub(r"(?m)^\{\{(?:etymid|etymon|rfe|etystub|wp|wikipedia)[^{}]*\}\}\s*", "", raw)
    text = render(raw.split("\n*")[0])
    return [x.strip() for x in re.split(r"(?<=[a-z0-9)'\]])\.\s+(?=[A-Z])", text) if x.strip(" .")]
def short(s, n=150):
    s = s.strip().rstrip(".")
    if len(s) <= n: return s
    for sep in (", ", " (", "; "):
        i = s.find(sep)
        if 15 <= i <= n: s = s[:i]; break
    else: s = s[:n].rsplit(" ", 1)[0] + "…"
    while s.count("(") > s.count(")"): s = s[:s.rfind("(")].rstrip(" ,;")
    return s
def readable(s):
    """an etymology sentence that rendered cleanly (no template left empty: "Probably .", "from , and")"""
    return bool(s) and len(s) > 12 and s[0].isalnum() and not re.search(r"\s[.,;)]|\(\s*\)|\(\s|''|\s'\s", s) and not s.startswith("Uncertain")

def word_name(sec):
    """(Finnish word, its gloss) when the etymology derives the name from an ordinary Finnish word"""
    e = re.sub(r"(?m)^\{\{(?:etymid|etymon)[^{}]*\}\}\s*", "", ety_of(sec))
    m = re.match(r"^(?:Modern usage from|From|Directly from)\s+\{\{(from|m|der|inh|l)\|([^{}]*)\}\}", e)
    if not m: return None
    parts = [p.strip() for p in m.group(2).split("|")]; pos = [p for p in parts if "=" not in p]
    kw = {p.split("=", 1)[0]: p.split("=", 1)[1] for p in parts if "=" in p}
    if m.group(1) in ("der", "inh"): pos = pos[1:]
    if len(pos) < 2 or pos[0] != "fi": return None
    term = pos[1]
    if not re.match(r"^[a-zäöå]+$", term): return None
    if HEDGE.search(re.split(r"(?<=\.)\s", e, maxsplit=1)[0]): return None
    gloss = (pos[3] if len(pos) > 3 else "") or kw.get("t") or kw.get("gloss") or ""
    return term, clean(gloss)

def first_def(text):
    sec = section(text, "Finnish")
    for m in re.finditer(r"(?ms)^===+\s*(Noun|Adjective|Verb|Interjection|Adverb)\s*===+\s*$(.*?)(?=^===|\Z)", sec):
        for line in m.group(2).splitlines():
            if line.startswith("# "):
                d = render(re.sub(r"\{\{(?:lb|lbl|label|sense|q|qualifier|i|gloss|gl|n-g|ng|defdate)\|[^{}]*\}\}", "", line[2:]))
                d = re.sub(r"\s*\([^()]*\)", "", d).replace("'", "")
                d = re.split(r"[;:]", d)[0].strip(" .")
                if d and not re.search(r"given name|surname|form of|plural of|genitive|inflection", d, re.I): return d
    return ""

# ── 1908 and 1929 almanac reforms (consistory minutes, transcribed by the Almanac Office) ──
def reform(path):
    """{"fi": (old names, new names), "sv": (…)}: Finnish-almanac lines are dated "4.1.", Swedish-almanac ones "4.1" """
    out = {"fi": (set(), set()), "sv": (set(), set())}
    if not os.path.exists(path): return out
    def names(s):
        if "(" in s: return set()                                  # "(ei nimeä)", "(inget namn)"
        return {p.strip() for p in s.split(",") if NAME.match(p.strip()) and p.strip()[0].isupper()}   # not "Erkki Transl.", double names
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^\s*(\d{1,2}\.\d{1,2})(\.?)\s+(.*?)\s*>\s*(.*)$", line.strip())
        if not m: continue
        side = "fi" if m.group(2) else "sv"
        out[side][0].update(names(m.group(3))); out[side][1].update(names(m.group(4)))
    return out
def reform_text(pdf):
    txt = pdf[:-4] + ".txt"
    if not os.path.exists(txt) and os.path.exists(pdf):
        try:
            import pypdf
            open(txt, "w", encoding="utf-8").write("\n".join((p.extract_text() or "") for p in pypdf.PdfReader(pdf).pages))
        except ImportError: print("  pypdf missing: cannot read", pdf, file=sys.stderr)
    return txt
def fetch_pdf(name):
    path = os.path.join(RAW, f"almanakka-{name}.pdf")
    if not os.path.exists(path):
        url = "https://almanakka.helsinki.fi/hubfs/Nimip%C3%A4iv%C3%A4uudistukset/" + name + ".pdf"
        print("  fetching", url, flush=True)
        open(path, "wb").write(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()); time.sleep(2)
    return path

# ── name-day calendars on fi.wikipedia ──
CAL = {"suomalainen kalenteri": "Finnish", "suomenruotsalainen kalenteri": "Finland-Swedish", "ortodoksinen kalenteri": "Orthodox",
       "pohjoissaamenkielinen kalenteri": "Northern Sámi", "inarinsaamenkielinen kalenteri": "Inari Sámi", "vanhemmissa kalentereissa": "older"}
def calendars(days):
    cal = collections.defaultdict(set); cal["_targets"] = {}
    for v in days.values():
        m = re.search(r"==\s*Nimipäivät\s*==(.*?)(?=\n==[^=]|\Z)", v["text"], re.S)
        if not m: continue
        for line in m.group(1).splitlines():
            if not line.startswith("*") or ":" not in line: continue
            label, rest = line.split(":", 1)
            label = re.sub(r"[\[\]*–]", "", label).strip().lower()
            if label not in CAL: continue
            for tgt, shown in re.findall(r"\[\[([^|\]]*)\|([^\]]*)\]\]", rest): cal["_targets"][shown.strip(" ,")] = tgt
            rest = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", rest).replace("''", "")
            for n in rest.split(","):
                n = n.strip(" .")
                if NAME.match(n): cal[CAL[label]].add(n)
    return cal

def fold(s):
    s = unicodedata.normalize("NFD", s.lower().replace("ʹ", ""))
    return re.sub(r"[\s'’-]", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))
def plain(s):
    for a, b in (("đ", "d"), ("Đ", "D"), ("ŧ", "t"), ("Ŧ", "T"), ("ŋ", "ng"), ("Ŋ", "Ng"), ("ʹ", ""), ("ǥ", "g"), ("Ǥ", "G")): s = s.replace(a, b)
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
ASCII = re.compile(r"^[A-Za-z]+(?:-[A-Za-z]+)?$")

def site_names():
    """every name already on the site (folded), and the exact spellings registered in the name files"""
    seen, spellings = set(), set()
    for f in ("names-db.tsv", "names-extra.tsv", "name-lists.tsv"):
        p = os.path.join(ROOT, "data", f)
        if not os.path.exists(p): continue
        for line in open(p, encoding="utf-8"):
            n = line.split("\t", 1)[0]
            seen.add(fold(n)); spellings.add(n.lower())
    for p in glob.glob(os.path.join(ROOT, "data", "*.json")):
        if os.path.abspath(p) == OUT: continue
        try: d = json.load(open(p, encoding="utf-8"))
        except Exception: continue
        if isinstance(d, list):
            for r in d:
                if isinstance(r, list) and r and isinstance(r[0], str): seen.add(fold(r[0]))
    return seen, spellings

def dvv_sex():
    out = collections.defaultdict(collections.Counter)
    for line in open(os.path.join(ROOT, "data", "name-lists.tsv"), encoding="utf-8"):
        c = line.rstrip("\n").split("\t")
        if len(c) > 4 and c[2] == "fi-population" and c[1] in ("f", "m") and c[4].isdigit(): out[c[0]][c[1]] += int(c[4])
    sex = {}
    for n, cnt in out.items():
        tot = sum(cnt.values())
        sex[n] = "g" if cnt["f"] >= .8 * tot else "b" if cnt["m"] >= .8 * tot else "e"
    return sex

def kalevala():
    p = os.path.join(ROOT, "data", "sacred", "world.tsv")
    out = set()
    if not os.path.exists(p): return out
    for r in csv.DictReader(open(p, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
        if r.get("corpus") == "Kalevala" and r.get("entity_type") not in ("place", "tribe", "concept") and r.get("status") == "attested":
            out |= {r["name"], r["original"]}
    return out

CLS_SEX = {"Q11879590": "g", "Q12308941": "b", "Q3409032": "e"}
def sex_of(gs):
    gs = set(gs) - {"", None}
    if not gs: return ""
    return "e" if "e" in gs or len(gs) > 1 else gs.pop()
SAMI = {"Northern Sami": "Northern Sámi", "Inari Sami": "Inari Sámi", "Skolt Sami": "Skolt Sámi"}
def gloss_meaning(s):
    """the gloss in an etymology sentence, when it is the meaning of the source word (not of a name it is a form of)"""
    if HEDGE.search(s): return ""
    lit = re.search(r"literally '([^']+)'", s)
    if lit: return lit.group(1)
    gl = re.search(r"'([^']{2,40})'", s)
    if gl and not re.search(r"\bform\b|variant|short|diminutive|cognate|equivalent|rendering|interpret|compare|related", s[:gl.start()], re.I) and gl.group(1)[0].islower(): return gl.group(1)
    return ""

if __name__ == "__main__":
    stats = collections.Counter()
    en = {l: cached("en-wikt-" + l.replace(" ", "_") + ".json", lambda l=l: fetch_en(l)) for l in ("Finnish", "Northern Sami", "Inari Sami", "Skolt Sami", "Karelian", "Swedish")}
    fiw = cached("fi-wikt-categories.json", fetch_fi_wikt)
    wd = cached("wikidata-given-names.json", fetch_wd)
    days = cached("fi-wikipedia-days.json", fetch_days)
    dvv = dvv_sex(); kale = kalevala(); seen, spellings = site_names()

    # sex evidence by exact spelling, from every source
    sexes = collections.defaultdict(set)
    for l, d in en.items():
        for t, v in d.items(): sexes[t].add(v["g"])
    for cat, ts in fiw.items():
        for t in ts: sexes[t].add(FI_WIKT[cat][1])
    for q, it in wd.items():
        g = sex_of(CLS_SEX.get(c) for c in it["cls"])
        for lab in set(it["labels"].values()) | {n for n, _ in it["native"]}:
            if g: sexes[lab].add(g)
    def sex(n): return sex_of(sexes.get(n, ())) or dvv.get(n, "")

    rec = {}
    def add(culture, language, name, g, src, meaning="", religion="", order=5):
        if not name or not NAME.match(name): stats[(culture, "not a single name")] += 1; return
        if not g: stats[(culture, "no sex in any source (left out)")] += 1; return
        r = rec.setdefault((name, culture), {"lang": language, "langs": set(), "gs": set(), "src": [], "m": "", "rel": religion})
        r["gs"].add(g); r["langs"].add(language)
        if meaning and not r["m"]: r["m"] = meaning
        if src and src not in [s for _, s in r["src"]]: r["src"].append((order, src))

    # word names: the meaning of the Finnish word, from the name page or else the word's own page
    words = {}
    for t, v in en["Finnish"].items():
        w = word_name(section(v["text"], "Finnish"))
        if w: words[t] = w
    need = sorted({w for w, g in words.values() if not g})
    word_pages = cached("en-wikt-finnish-words.json", lambda: texts("en.wiktionary.org", need))

    # Finnish (English Wiktionary)
    for t, v in en["Finnish"].items():
        sec = section(v["text"], "Finnish")
        gn = re.search(r"\{\{given name\|fi\|[^{}]*\}\}", sec)
        eq = re.search(r"\|eq=([^|}]+)", gn.group(0)) if gn else None
        ss = sentences(ety_of(sec))
        meaning, parts = "", []
        if t in words:
            w, g = words[t]
            g = g or first_def(word_pages.get(w, ""))
            meaning = g
            parts.append(f"A Finnish word name: {w}" + (f" '{g}'" if g else "") + " (Wiktionary).")
            stats[("Finnish", "word names")] += 1
            if g: stats[("Finnish", "word names with the word's meaning")] += 1
        elif ss and readable(short(ss[0])):
            parts.append(f"A Finnish name. {short(ss[0])} (Wiktionary).")
            meaning = gloss_meaning(ss[0])
        else: parts.append("A Finnish name (Wiktionary).")
        if eq: parts.append("English equivalent: " + re.sub(r"^\w+:", "", clean(eq.group(1)).split(",")[0]) + ".")
        era = next((x for x in ss[1:] if re.search(r"\b1[5-9]\d\d\b|\b20[0-2]\d\b|century|Kalevala", x)), "")
        if era and not HEDGE.search(era) and readable(short(era, 170)): parts.append(short(era, 170) + " (Wiktionary).")
        add("Finnish", "Finnish", t, v["g"], " ".join(parts), meaning, order=1)
    for cat, ts in fiw.items():
        lang, g = FI_WIKT[cat]
        if lang == "Finnish":
            for t in ts: add("Finnish", "Finnish", t, g, "A Finnish name (Finnish Wiktionary).", order=2)
        elif lang in SAMI:
            for t in ts: add("Sámi", SAMI[lang], t, g, ("An " if SAMI[lang].startswith("I") else "A ") + f"{SAMI[lang]} name (Finnish Wiktionary).", order=2)

    # Sámi and Karelian (English Wiktionary)
    for l in ("Northern Sami", "Inari Sami", "Skolt Sami", "Karelian"):
        for t, v in en[l].items():
            sec = section(v["text"], l)
            ss = sentences(ety_of(sec)); gn = re.search(r"\{\{given name\|[a-z]+\|[^{}]*\}\}", sec)
            eq = re.search(r"\|eq=([^|}]+)", gn.group(0)) if gn else None
            lang = SAMI.get(l, l); art = "An" if lang[0] in "AEIOU" else "A"
            src = f"{art} {lang} name. {short(ss[0])} (Wiktionary)." if ss and readable(short(ss[0])) else f"{art} {lang} name (Wiktionary)."
            if eq: src += " English equivalent: " + re.sub(r"^\w+:", "", clean(eq.group(1)).split(",")[0]) + "."
            add("Sámi" if l in SAMI else "Karelian", lang, t, v["g"], src, gloss_meaning(ss[0]) if ss else "", order=1)

    # Wikidata
    WD_CULT = {"Q1412": ("Finnish", "Finnish", "fi"), "Q33947": ("Sámi", "Northern Sámi", "se"), "Q33462": ("Sámi", "Inari Sámi", "smn"),
               "Q13271": ("Sámi", "Skolt Sámi", "sms"), "Q33557": ("Karelian", "Karelian", "krl"), "Q1461092": ("Finland-Swedish", "Swedish", "sv")}
    for q, it in wd.items():
        g = sex_of(CLS_SEX.get(c) for c in it["cls"])
        for L in it["langs"]:
            cult, lang, code = WD_CULT[L]
            n = next((n for n, nl in it["native"] if nl == code), "") or it["labels"].get(code) or it["labels"].get("mul") or it["labels"].get("en", "")
            add(cult, lang, n, g, f"Tagged as a {lang} given name on Wikidata ({q}).", order=3)

    # almanac reforms
    ref = {y: reform(reform_text(fetch_pdf(f"NimiuudistusNamnrevidering{y}"))) for y in ("1908", "1929")}
    swedish = set(en["Swedish"]) | set(fiw["Ruotsin kielen miesten etunimet"]) | set(fiw["Ruotsin kielen naisten etunimet"])
    fi_any = {n for y in ref for n in ref[y]["fi"][0] | ref[y]["fi"][1]}
    finnish_attested = {n for (n, c) in rec if c == "Finnish"}
    finnish_origin = {t for t, v in en["Finnish"].items() if re.search(r"\{\{given name\|fi\|[^{}]*from=Finnish", v["text"]) or any("from Finnish" in c or "from Uralic" in c for c in v["cats"])}
    for y in ("1908", "1929"):
        old, new = ref[y]["fi"]
        for n in sorted(new - old):
            if n not in finnish_attested: stats[("Finnish", "almanac name with no Finnish-name source (not counted)")] += 1; continue
            back = y == "1929" and n in ref["1908"]["fi"][0]
            add("Finnish", "Finnish", n, sex(n), ("Returned to" if back else "Added to") + f" the Finnish-language almanac in the {y} name reform (University of Helsinki consistory minutes).", order=4)
        old, new = ref[y]["sv"]
        for n in sorted(old | new):
            if n in finnish_origin or (n not in swedish and n in fi_any): stats[("Finland-Swedish", "Finnish name in the Swedish almanac (not counted)")] += 1; continue
            if n in new - old:
                src = f"Added to Finland's Swedish-language almanac in the {y} name reform (University of Helsinki consistory minutes)."
                if y == "1929": src += " That reform gave Swedish-speaking Finns a name-day calendar of their own (University of Helsinki Almanac Office)."
            else: src = f"In Finland's Swedish-language almanac before the {y} name reform (University of Helsinki consistory minutes)."
            add("Finland-Swedish", "Swedish", n, sex(n), src, order=4)

    # name-day calendars (membership only, no dates)
    cal = calendars(days)
    # sex for calendar names no other source gives: what the name's own Finnish Wikipedia article states
    nosex = sorted(n for k in ("Orthodox", "Northern Sámi", "Inari Sámi") for n in cal[k] if not sex(n))
    tried = sorted({t for n in nosex for t in (cal["_targets"].get(n, n), n, n + " (nimi)", n + " (etunimi)")})
    arts = cached("fi-wikipedia-name-articles.json", lambda: texts("fi.wikipedia.org", tried))
    def wiki_sex(n):
        for t in (cal["_targets"].get(n, n), n + " (etunimi)", n + " (nimi)", n):
            a = re.sub(r"\{\{[^{}]*\}\}|<ref.*?</ref>", "", arts.get(t, ""), flags=re.S)
            lead = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", a)[:500].lower()
            if not re.search(r"etunimi|etunimenä|\bnimi\b", lead): continue
            if re.search(r"(miehen|miesten) ja (naisen|naisten)|(naisen|naisten) ja (miehen|miesten)|sukupuolineutraali", lead): return "e"
            if re.search(r"(naisen|naisten) (etu)?nimi|naisennimi", lead): return "g"
            if re.search(r"(miehen|miesten) (etu)?nimi|miehennimi", lead): return "b"
        return ""
    for n in nosex:
        g = wiki_sex(n)
        if g: sexes[n].add(g); stats[("calendar names", "sex from the name's Finnish Wikipedia article")] += 1
    for n in sorted(cal["Orthodox"]):
        add("Finnish Orthodox", "Finnish", n, sex(n), "In the Orthodox name-day calendar of Finland, kept by the Orthodox Church of Finland (as listed on Finnish Wikipedia).", religion="Christian", order=4)
    for n in sorted(cal["Northern Sámi"]):
        add("Sámi", "Northern Sámi", n, sex(n), "In the Sámi name-day calendar compiled by Pekka Sammallahti (as listed on Finnish Wikipedia).", order=4)
    for n in sorted(cal["Inari Sámi"]):
        add("Sámi", "Inari Sámi", n, sex(n), "In the Inari Sámi name-day calendar (as listed on Finnish Wikipedia).", order=4)
    if USE_UH_CALENDARS:
        for n in sorted(cal["Finnish"]): add("Finnish", "Finnish", n, sex(n), "In the Finnish name-day calendar.", order=4)
        for n in sorted(cal["Finland-Swedish"]): add("Finland-Swedish", "Swedish", n, sex(n), "In the Finland-Swedish name-day calendar.", order=4)

    # Aino: the first Finnish name in the almanac, 1890 (Almanac Office history, https://almanakka.helsinki.fi/en/name-days)
    if ("Aino", "Finnish") in rec:
        r = rec[("Aino", "Finnish")]
        r["src"] = [x for x in r["src"] if "1908 name reform" not in x[1]] + [(0, "Entered the almanac in 1890, the first Finnish name there (University of Helsinki Almanac Office).")]

    # rows
    cultures_of = collections.defaultdict(list)
    for (n, c) in rec: cultures_of[n].append(c)
    GROUPS = {"Finnish": ["Nordic"], "Finland-Swedish": ["Nordic"], "Finnish Orthodox": ["Nordic"], "Sámi": ["Nordic"], "Karelian": []}
    rows = []
    for (n, c), r in rec.items():
        srcs = [s for _, s in sorted(r["src"], key=lambda x: x[0])]
        if len(srcs) > 1: srcs = [s for s in srcs if not re.match(r"^An? [\w ]+ name \((Finnish )?Wiktionary\)\.$", s)] or srcs
        texts_ = ""
        if c in ("Finnish", "Karelian", "Finnish Orthodox") and n in kale: srcs.append("In the Kalevala."); texts_ = "Kalevala"
        ease = 1 if ASCII.match(n) else 3
        if ease == 3:
            p = plain(n)
            if ASCII.match(p) and p.lower() in spellings: ease = 2; srcs.append(f"Also written {p}.")
        also = list(dict.fromkeys([x for x in cultures_of[n] if x != c] + GROUPS[c]))
        lang = next((l for l in ("Northern Sámi", "Inari Sámi", "Skolt Sámi") if l in r["langs"]), r["lang"]) if c == "Sámi" else r["lang"]
        rows.append([n, sex_of(r["gs"]), c, lang, r["rel"], r["m"][:80], " ".join(srcs), texts_, "real", also, ease])
    rows.sort(key=lambda r: (r[10], r[0].lower(), r[2]))
    json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

    per = collections.Counter(r[2] for r in rows)
    new = [r for r in rows if fold(r[0]) not in seen]
    print(f"{len(rows):,} rows ({len({r[0] for r in rows}):,} distinct names) → {OUT} ({os.path.getsize(OUT) // 1024} KB)")
    for c, k in per.most_common():
        cr = [r for r in rows if r[2] == c]
        print(f"  {c}: {k} names, {len({r[0] for r in new if r[2] == c})} new to the site, {sum(1 for r in cr if r[5])} with meanings, ease 1/2/3 = "
              + "/".join(str(sum(1 for r in cr if r[10] == e)) for e in (1, 2, 3)))
    print("  Sámi by language:", dict(collections.Counter(r[3] for r in rows if r[2] == "Sámi")))
    print(f"  new to the site (any culture): {len({fold(r[0]) for r in new}):,} names")
    print("  name-day calendars on fi.wikipedia (distinct names):", {k: len(v) for k, v in cal.items()})
    print("  reforms (old, new):", {y: {s: (len(ref[y][s][0]), len(ref[y][s][1])) for s in ref[y]} for y in ref})
    for k, v in sorted(stats.items()): print("  ", k, v)
