# Builds data/hebrew-extra.json: Hebrew given names the site doesn't have yet, each with its Hebrew spelling and a Latin
# spelling taken from a source (never a guessed reading of the letters), and data/bible-place-names.json: places in the Bible
# that people use as given names.
#
# Sources (all open):
#   · English Wiktionary, "Hebrew given names" and its male / female / unisex / diminutive subcategories (CC BY-SA 4.0):
#     the pointed headword, the sex, the Latin spelling the entry gives ({{given name|he|…|xlit=…}}; eq= is an English
#     equivalent, not a spelling), else its own transliteration with the stress marks taken off, and a meaning only where the
#     entry states one (or the same word, pointed the same way, defined on the page). European names written in Hebrew
#     letters (חוויאר = Javier) are left out: the site has the name itself.
#   · Hebrew Wiktionary (he.wiktionary.org), category "שמות" and every entry defined as "שם פרטי" (CC BY-SA 4.0): the pointed
#     headword and the sex ("שם פרטי לזכר / לנקבה"); its pronunciation line is the last-resort Latin spelling.
#   · Wikidata given-name items in Hebrew (language P407 = Hebrew, writing system Hebrew, or a Hebrew native label; CC0):
#     the Hebrew label, the English label as the Latin spelling, the sex from the item's class.
#   · STEPBible TIPNR (raw/tipnr.txt, CC BY 4.0): Bible people's Hebrew forms and their ESV / KJV / NIV spellings, and Bible places.
#   · Israel's Central Bureau of Statistics name tables (raw/il.csv, Hebrew letters) and their vetted Latin pairings
#     (raw/il-latin.csv, "known pairing" and "usual spelling" only, never a "verified reading"): how many babies were given
#     a name, the sex when no name source gives one, and a Latin spelling only when no name source gives one.
#   · Hitchcock's Bible Names Dictionary (1869, public domain; raw/hitchcock.txt): meanings of Bible names and places only.
#
# A name is new when no storied list, sacred-text index or registry the site loads has it (case- and accent-folded).
# Rows: [name, sex g|b|e, culture, language, faiths, meaning, story, texts, kind, also, ease]; ease 1 = plain English letters,
# 2 = not plain but the sources give a plain-letter spelling (stated in the story), 3 = neither. Sorted by ease, then name.
# bible-place-names.json rows carry a 12th slot: {"place": true, "first": "Matthew 21:17", "ref": "Mat.21.17"}.
# Downloads are cached in raw/hebrew-extra/; delete that folder to fetch everything again.
#
#   python3 scripts/build_hebrew_extra.py
import collections, csv, difflib, glob, gzip, json, os, re, sys, time, unicodedata, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "raw"); CACHE = os.path.join(RAW, "hebrew-extra"); DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "hebrew-extra.json"); OUT_PLACES = os.path.join(DATA, "bible-place-names.json")
UA = {"User-Agent": "Lullabyte-build/1.0 (https://github.com/suhxnitiwari/baby-name-maker)"}
EN_WT = "https://en.wiktionary.org/w/api.php?"; HE_WT = "https://he.wiktionary.org/w/api.php?"
SPARQL = "https://query.wikidata.org/sparql?"

# ─────────────────────────────────────────────────────────────
# fetching (polite, cached)
# ─────────────────────────────────────────────────────────────
def api(base, **q):
    q.update(format="json", formatversion=2, maxlag=10)
    for attempt in range(10):
        try:
            req = urllib.request.Request(base, data=urllib.parse.urlencode(q).encode(), headers=UA)
            d = json.load(urllib.request.urlopen(req, timeout=60))
            if d.get("error", {}).get("code") == "maxlag": time.sleep(5); continue
            time.sleep(0.4)
            return d
        except Exception:
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"{base} kept failing")

def cached(name, fetch):
    path = os.path.join(CACHE, name)
    if os.path.exists(path):
        with (gzip.open(path, "rt", encoding="utf-8") if path.endswith(".gz") else open(path, encoding="utf-8")) as fh: return json.load(fh)
    data = fetch()
    os.makedirs(CACHE, exist_ok=True)
    with (gzip.open(path, "wt", encoding="utf-8") if path.endswith(".gz") else open(path, "w", encoding="utf-8")) as fh:
        json.dump(data, fh, ensure_ascii=False)
    return data

def category_tree(base, root, skip=lambda t: False):
    """every page in a category and its subcategories (titles), with the subcategory each came from"""
    seen, pages, todo = set(), {}, [root]
    while todo:
        cat = todo.pop()
        if cat in seen or skip(cat): continue
        seen.add(cat); cont = {}
        while True:
            d = api(base, action="query", list="categorymembers", cmtitle=cat, cmlimit=500, cmtype="page|subcat", **cont)
            for m in d["query"]["categorymembers"]:
                if m["ns"] == 14: todo.append(m["title"])
                elif m["ns"] == 0: pages.setdefault(m["title"], []).append(cat)
            if "continue" not in d: break
            cont = d["continue"]
    return pages

def search_titles(base, phrase):
    out, off = [], 0
    while True:
        d = api(base, action="query", list="search", srsearch=f'"{phrase}"', srnamespace=0, srlimit=500, sroffset=off, srprop="")
        if "query" not in d: print("search failed:", phrase, str(d)[:200]); return out
        out += [s["title"] for s in d["query"]["search"]]
        if "continue" not in d: return out
        off = d["continue"]["sroffset"]

def wikitexts(base, titles):
    out, titles = {}, sorted(set(titles))
    for i in range(0, len(titles), 50):
        d = api(base, action="query", prop="revisions", rvprop="content", rvslots="main", titles="|".join(titles[i:i + 50]))
        for p in d["query"]["pages"]:
            if "revisions" in p: out[p["title"]] = p["revisions"][0]["slots"]["main"]["content"]
    return out

def sparql(q):
    url = SPARQL + urllib.parse.urlencode({"query": q, "format": "json"})
    for attempt in range(6):
        try: return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120))["results"]["bindings"]
        except Exception: time.sleep(10 * (attempt + 1))
    raise RuntimeError("Wikidata query kept failing")

# ─────────────────────────────────────────────────────────────
# text helpers
# ─────────────────────────────────────────────────────────────
HEB_LETTERS = re.compile(r"[א-ת]")
def unpoint(h):
    """Hebrew without vowel points or cantillation; maqaf and geresh made plain"""
    h = re.sub(r"[֑-ׇֽ]", lambda m: "-" if m.group() == "־" else "", h)
    return h.replace("״", '"').replace("׳", "'").replace("’", "'").replace("-", " ").strip()
def is_hebrew(h): return bool(h) and bool(re.fullmatch(r"[א-ת֑-ׇ'\"׳״־ -]+", h)) and bool(HEB_LETTERS.search(h))

def fold(s):
    """the site's own fold (app.js): accents off, lower case, no spaces or hyphens"""
    s = unicodedata.normalize("NFD", s); s = re.sub(r"[̀-ͯ]", "", s).lower()
    for a, b in (("æ", "ae"), ("ǣ", "ae"), ("ǽ", "ae"), ("ø", "o"), ("ǿ", "o"), ("œ", "oe"), ("ð", "d"), ("đ", "d"), ("þ", "th"), ("ß", "ss"), ("ł", "l"), ("ı", "i"), ("ŋ", "ng")):
        s = s.replace(a, b)
    return re.sub(r"[\s-]", "", s)

LATIN_OK = re.compile(r"[A-Z][a-z'’]*(?:[ -][A-Z]?[a-z'’]+)*")
PLAIN = re.compile(r"[A-Za-z]+(?:[ -][A-Za-z]+)*")
def tidy_latin(s):
    """a Latin spelling as a name: stress accents off (Wiktionary's avív = Aviv), first letter capital; None if not a name"""
    s = re.sub(r"\s*\(.*?\)\s*", "", (s or "")).strip().replace("’", "'")
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    s = unicodedata.normalize("NFC", s)
    if not s or not re.fullmatch(r"[A-Za-z'\- ]+", s) or s.startswith("'") or len(s) < 2: return None
    s = " ".join(w[:1].upper() + w[1:] for w in s.split(" "))
    return s if LATIN_OK.fullmatch(s) else None

def strip_wiki(s):
    s = re.sub(r"\{\{(?:gloss|gl|q|qualifier|i|lb|label|sense)\|[^{}]*\}\}", "", s)
    s = re.sub(r"\{\{(?:tcl|l|m|w|wp)\|(?:[a-z-]+\|)?([^|{}]+)[^{}]*\}\}", r"\1", s)
    s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]+)\]\]", r"\1", s)
    s = re.sub(r"'''?|<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip(" ,;:.")

# ─────────────────────────────────────────────────────────────
# what the site already has
# ─────────────────────────────────────────────────────────────
STORIED = ["scripture-names", "bible-extra", "culture-names", "also-cultures", "east-asian-names", "medieval-names", "az-names",
           "hebrew-names", "russia-cultures", "caucasus-balkan-names", "arabia-names", "mexico-names", "roman-names", "greek-names",
           "armenia-names", "bollywood-names", "english-names", "spanish-names", "portuguese-names", "german-names", "finnish-names",
           "persian-names", "egyptian-names"]
def story_culture():
    out = collections.defaultdict(set)
    for f in STORIED:
        p = os.path.join(DATA, f + ".json")
        if not os.path.exists(p): continue
        d = json.load(open(p, encoding="utf-8"))
        if isinstance(d, dict): rows = [[r[0], "", {"ja": "Japanese", "ko": "Korean", "zh": "Chinese"}[k]] for k in ("ja", "ko", "zh") for r in d.get(k, [])]
        else: rows = d
        for r in rows:
            # a Bollywood star's line or an ancient Greek bearer says nothing about the name's culture
            if r and isinstance(r[0], str) and not (len(r) > 6 and re.match(r"In Bollywood:|Used in ancient Greece", r[6] or "")): out[fold(r[0])].add(r[2])
    return out

def site_names():
    story = set()
    for f in STORIED:
        p = os.path.join(DATA, f + ".json")
        if not os.path.exists(p): continue
        d = json.load(open(p, encoding="utf-8"))
        rows = [r for k in ("ja", "ko", "zh") for r in d.get(k, [])] if isinstance(d, dict) else d
        story |= {fold(r[0]) for r in rows if r and isinstance(r[0], str)}
    sac = json.load(open(os.path.join(DATA, "sacred.json"), encoding="utf-8"))
    story |= {fold(r[0]) for r in sac["n"]}
    for p in glob.glob(os.path.join(DATA, "sacred", "*.tsv")):
        if "review" in os.path.basename(p): continue
        for l in open(p, encoding="utf-8").read().split("\n")[1:]:
            if l: story.add(fold(l.split("\t")[0]))
    registry = {}            # folded → (sex, official countries, people)
    for f in ("names-db.tsv", "names-extra.tsv"):
        for l in open(os.path.join(DATA, f), encoding="utf-8"):
            c = l.rstrip("\n").split("\t")
            if len(c) < 4: continue
            k = fold(c[0])
            if k not in registry: registry[k] = (c[1], c[2].split(","), int(c[3] or 0), c[0])
    return story, registry

# ─────────────────────────────────────────────────────────────
# an entry per Hebrew spelling (unpointed), filled by every source
# ─────────────────────────────────────────────────────────────
E = collections.defaultdict(lambda: {"pointed": collections.Counter(), "latin": [], "sex": collections.Counter(), "meaning": [],
                                     "src": [], "bible": False, "first": "", "brief": "", "qid": ""})
SRC_ORDER = {"wikt": 0, "wikidata": 1, "cbs": 2, "tipnr": 3, "wikt-tr": 4, "hewikt": 5}
LATIN_FROM = {"wikt": "Wiktionary", "wikidata": "Wikidata", "cbs": "Israel's CBS name tables as paired in raw/il-latin.csv",
              "tipnr": "STEPBible", "wikt-tr": "Wiktionary's transliteration", "hewikt": "Hebrew Wiktionary's pronunciation"}
STRONG = {"wikt", "wikidata", "cbs", "tipnr"}

def add_latin(h, s, how, also_only=False):
    s = tidy_latin(s)
    if s: E[h]["latin"].append((s, how, also_only))

# ── English Wiktionary ──
GN_SEX = {"male": "b", "female": "g", "unisex": "e"}
def en_wiktionary():
    pages = cached("enwikt-pages.json.gz", lambda: wikitexts(EN_WT, category_tree(
        EN_WT, "Category:Hebrew given names", skip=lambda c: "renderings of" in c)))
    n = 0
    for title, text in pages.items():
        i = text.find("==Hebrew==")
        if i < 0: continue
        sec = text[i + 10:]; m = re.search(r"\n==[^=]", sec); sec = sec[:m.start()] if m else sec
        # split by etymology so a proper noun's meaning comes only from its own etymology or its own word
        parts = re.split(r"\n===Etymology[^=]*===\n", "\n" + sec)
        for part in parts:
            heads = list(re.finditer(r"\{\{he-(proper noun|noun|adj|verb)\|([^\n]*?)\}\}\n((?:#.*\n?|\s*\n)*)", part))
            words = {}
            for hm in heads:
                kind, params, defs = hm.group(1), hm.group(2), hm.group(3)
                wv = (re.search(r"\bwv=([^|}]+)", params) or [None, ""])[1].strip()
                tr = (re.search(r"\btr=([^|}]+)", params) or [None, ""])[1].strip()
                if kind != "proper noun":
                    # the word's first sense, unless it is slang (a name is not named for a slang sense)
                    first = next((strip_wiki(l[1:]) for l in defs.split("\n") if re.match(r"#[^*:#]", l)
                                  and not re.search(r"\{\{lb\|he\|[^}]*(slang|colloquial|derogatory|vulgar|pejorative|offensive)", l)), "")
                    if first and wv: words.setdefault(unpoint(wv) + "|" + wv, first)
                    continue
                # a European name written in Hebrew letters (קלאודיו from Italian Claudio): the site has the name itself
                if re.search(r"\{\{(?:bor|lbor|der|bor\+|uder)\|he\|(?:en|es|it|fr|de|ru|pl|pt|ro|hu|nl|el|ka|uk)\|", part.split("===", 1)[0] if part.strip() else ""):
                    continue
                for gn in re.finditer(r"\{\{given name\|he\|([^{}]*)\}\}([^\n]*)", defs):
                    # …or one Wiktionary defines by a European name: חוויאר = Spanish Javier, קלאודיו; [[Claudio]]
                    if re.search(r"eq=(?:en|es|it|fr|de|ru|pl|pt|ro|hu|nl|el):", gn.group(1)) or re.match(r"\s*;\s*\[\[[A-Z]", gn.group(2)): continue
                    p = gn.group(1).split("|")
                    named = dict(x.split("=", 1) for x in p if "=" in x)
                    sexes = [x for x in p if "=" not in x] + [named.get("gender", "")]
                    sx = next((GN_SEX[x.split(" ")[0]] for x in sexes if x.split(" ")[0] in GN_SEX), None)
                    if not sx: continue
                    h = unpoint(wv or title)
                    if not is_hebrew(h): continue
                    e = E[h]; n += 1
                    e["pointed"][wv or title] += 3; e["sex"][sx] += 2; e["src"].append(("wikt", title))
                    named = {k.strip(): v for k, v in named.items()}
                    # xlit: how the name is written in Latin letters (eq= is an English equivalent, Joey for Yossi: not a spelling)
                    for s in re.split(r",\s*", named.get("xlit", "")):
                        add_latin(h, re.sub(r"^\w+:|<.*", "", s), "wikt")
                    dim = named.get("dim") or named.get("dimof") or ""
                    if dim: e["dim"] = re.sub(r"<.*", "", dim).split(",")[0].strip()
                    if tr: add_latin(h, tr.split(",")[0], "wikt-tr")
                    for key in ("meaning", "meaning1"):
                        if named.get(key): e["meaning"].append((strip_wiki(named[key]), "Wiktionary"))
                    if re.search(r"\{\{lb\|he\|[^}]*biblical", defs, re.I) or re.search(r"\bBible\b|biblical", defs): e["bible"] = True
                    ety = part.split("===", 1)[0] if part.strip() else ""
                    for mm in re.finditer(r"(?:thus|literally)\s+meaning\s+[\"“]([^\"”]{2,60})[\"”]", ety):
                        e["meaning"].append((strip_wiki(mm.group(1)), "Wiktionary"))
                    # the same word as a noun or adjective on this page, pointed the same way (שִׁירָה: singing)
                    w = words.get(h + "|" + wv) if wv and not dim else None
                    if w: e["meaning"].append((w, "Wiktionary, the word " + wv))
            # nouns after the proper noun in the same etymology
            for hm in heads:
                if hm.group(1) != "proper noun": continue
                wv = (re.search(r"\bwv=([^|}]+)", hm.group(2)) or [None, ""])[1].strip()
                h = unpoint(wv or title)
                if h in E and wv and not E[h].get("dim") and not any(s.startswith("Wiktionary, the word") for _, s in E[h]["meaning"]) and words.get(h + "|" + wv):
                    E[h]["meaning"].append((words[h + "|" + wv], "Wiktionary, the word " + wv))
    return n

# ── Hebrew Wiktionary ──
HE_SEX = [(r"שם פרטי (?:ל|של )?(?:שני|שתי) המינים|יוניסקס|לזכר ולנקבה|לנקבה ולזכר", "e"), (r"שם פרטי (?:ל|של )?(?:זכר|גבר|בן|בנים)", "b"),
          (r"שם פרטי (?:ל|של )?(?:נקבה|אישה|בת|בנות)", "g")]
def he_wiktionary():
    def titles():
        t = set(category_tree(HE_WT, "קטגוריה:שמות"))
        for phrase in ("שם פרטי לזכר", "שם פרטי לנקבה", "שם פרטי", "שם פרטי ממין זכר", "שם פרטי ממין נקבה"):
            t |= set(search_titles(HE_WT, phrase))
        return sorted(t)
    pages = cached("hewikt-pages.json.gz", lambda: wikitexts(HE_WT, cached("hewikt-titles.json", titles)))
    n = 0
    for title, text in pages.items():
        for sm in re.finditer(r"^==\s*([^=\n]+?)\s*==\s*$(.*?)(?=^==[^=]|\Z)", text, re.M | re.S):
            head, body = sm.group(1).strip(), sm.group(2)
            head = re.sub(r"\s*\(.*?\)\s*", "", head).strip()
            if not is_hebrew(head) or unpoint(head) != unpoint(title).split(" (")[0] and unpoint(head).replace(" ", "") != unpoint(title).replace(" ", ""):
                continue
            sx = None
            for line in body.split("\n"):
                if not line.startswith("#") or line.startswith(("#:", "#*")): continue
                for pat, g in HE_SEX:
                    if re.search(pat, line): sx = sx or g
                if sx: break
            if not sx: continue
            h = unpoint(head); e = E[h]; n += 1
            e["pointed"][head] += 2; e["sex"][sx] += 2; e["src"].append(("hewikt", title))
            if "קטגוריה:דמויות מקראיות" in text: e["bible"] = True
            pr = re.search(r"\|\s*הגייה\s*=\s*([^\n|]+)", body)
            if pr: add_latin(h, re.sub(r"'''|\[\[|\]\]|\{\{[^}]*\}\}", "", pr.group(1)).split(",")[0].split("/")[0].strip(), "hewikt")
    return n

# ── Wikidata ──
SEX_Q = {"Q12308941": "b", "Q11879590": "g", "Q3409032": "e"}
def wikidata():
    q = """SELECT ?i ?t ?he ?en ?nat ?scr (GROUP_CONCAT(DISTINCT ?alt;separator="|") AS ?alts) (GROUP_CONCAT(DISTINCT ?lang;separator="|") AS ?langs) WHERE {
      VALUES ?t {wd:Q12308941 wd:Q11879590 wd:Q3409032 wd:Q202444} ?i wdt:P31 ?t .
      {?i wdt:P282 wd:Q33513} UNION {?i wdt:P407 ?l . VALUES ?l {wd:Q9288 wd:Q1982224}} UNION {?i wdt:P1705 ?n0 . FILTER(LANG(?n0)="he")}
      OPTIONAL{?i rdfs:label ?he FILTER(LANG(?he)="he")} OPTIONAL{?i rdfs:label ?en FILTER(LANG(?en)="en")}
      OPTIONAL{?i wdt:P1705 ?nat} OPTIONAL{?i wdt:P282 ?scr} OPTIONAL{?i skos:altLabel ?alt FILTER(LANG(?alt)="en")} OPTIONAL{?i wdt:P407 ?lang}
    } GROUP BY ?i ?t ?he ?en ?nat ?scr"""
    rows = cached("wikidata-hebrew-given-names-2.json", lambda: sparql(q))
    v = lambda r, k: r.get(k, {}).get("value", "")
    by = collections.defaultdict(lambda: {"t": set(), "he": "", "en": "", "nat": set(), "scr": set(), "alts": set(), "langs": set()})
    for r in rows:
        b = by[v(r, "i").rsplit("/", 1)[-1]]
        b["t"].add(v(r, "t").rsplit("/", 1)[-1]); b["he"] = b["he"] or v(r, "he"); b["en"] = b["en"] or v(r, "en")
        if v(r, "nat"): b["nat"].add(v(r, "nat"))
        if v(r, "scr"): b["scr"].add(v(r, "scr").rsplit("/", 1)[-1])
        b["alts"] |= {a for a in v(r, "alts").split("|") if a}
        b["langs"] |= {x.rsplit("/", 1)[-1] for x in v(r, "langs").split("|") if x}
    n = 0
    for qid, b in sorted(by.items()):
        if b["scr"] - {"Q33513", "Q8229"}: continue                   # written in another script (Georgian, Cyrillic…)
        nat_he = [x for x in sorted(b["nat"]) if is_hebrew(x)]
        nat_lat = [x for x in sorted(b["nat"]) if not is_hebrew(x)]
        hebrew_item = bool(nat_he) or "Q9288" in b["langs"] or "Q1982224" in b["langs"]
        # a Latin-script name of another language (Polish Gerszon, French Guerschon) that only carries a Hebrew label: not a Hebrew name
        if nat_lat and not hebrew_item: continue
        if b["scr"] == {"Q8229"} and not b["langs"] & {"Q9288", "Q1982224"}: continue
        he = b["he"] if is_hebrew(b["he"]) else ""
        # the Hebrew label and the Hebrew native label disagree (Yoed labelled סורק): trust neither
        if he and nat_he and all(unpoint(x) != unpoint(he) for x in nat_he): continue
        heb = [he] if he else nat_he
        if not heb: continue
        h = unpoint(heb[0])
        if not he and h not in WITNESS: continue      # a native label alone, seen by no other source
        sexes = {SEX_Q[t] for t in b["t"] if t in SEX_Q}
        sx = "e" if "e" in sexes or {"b", "g"} <= sexes else next(iter(sexes), None)
        e = E[h]; n += 1
        for x in heb:
            if unpoint(x) == h: e["pointed"][x] += 1
        if sx: e["sex"][sx] += 1
        e["src"].append(("wikidata", qid)); e["qid"] = e["qid"] or qid
        if b["en"] and not is_hebrew(b["en"]): add_latin(h, b["en"], "wikidata")
        for a in sorted(b["alts"]):
            if not is_hebrew(a) and "(" not in a: add_latin(h, a, "wikidata", also_only=True)
    return n

# ── STEPBible TIPNR ──
BOOKS = ("Gen Exo Lev Num Deu Jos Jdg Rut 1Sa 2Sa 1Ki 2Ki 1Ch 2Ch Ezr Neh Est Job Psa Pro Ecc Sng Isa Jer Lam Ezk Dan Hos Jol Amo Oba Jon "
         "Mic Nam Hab Zep Hag Zec Mal Mat Mrk Luk Jhn Act Rom 1Co 2Co Gal Eph Php Col 1Th 2Th 1Ti 2Ti Tit Phm Heb Jas 1Pe 2Pe 1Jn 2Jn 3Jn Jud Rev").split()
BOOK_NAME = dict(zip(BOOKS, ("Genesis,Exodus,Leviticus,Numbers,Deuteronomy,Joshua,Judges,Ruth,1 Samuel,2 Samuel,1 Kings,2 Kings,1 Chronicles,"
    "2 Chronicles,Ezra,Nehemiah,Esther,Job,Psalms,Proverbs,Ecclesiastes,Song of Songs,Isaiah,Jeremiah,Lamentations,Ezekiel,Daniel,Hosea,Joel,"
    "Amos,Obadiah,Jonah,Micah,Nahum,Habakkuk,Zephaniah,Haggai,Zechariah,Malachi,Matthew,Mark,Luke,John,Acts,Romans,1 Corinthians,"
    "2 Corinthians,Galatians,Ephesians,Philippians,Colossians,1 Thessalonians,2 Thessalonians,1 Timothy,2 Timothy,Titus,Philemon,Hebrews,"
    "James,1 Peter,2 Peter,1 John,2 John,3 John,Jude,Revelation").split(",")))
NT = set(BOOKS[BOOKS.index("Mat"):])
REF = re.compile(r"\b([123]?[A-Z][a-z]{1,2})\.(\d+)\.(\d+)")
def ref_key(r): return (BOOKS.index(r[0]), int(r[1]), int(r[2]))
def verse(r): return f"{BOOK_NAME[r[0]]} {r[1]}:{r[2]}"
TITLES = {"caesar", "christ", "messiah", "pharaoh", "rabbi", "rabboni", "lord", "tirshatha", "rabshakeh", "rabsaris", "tartan", "jeshurun", "hashem", "jasher", "jew"}

def tipnr():
    """people: Hebrew form → spellings, sex, first verse; places: spelling → Hebrew/Greek forms, first verse, mentions"""
    txt = open(os.path.join(RAW, "tipnr.txt"), encoding="utf-8").read()
    people, places, person_mentions = {}, {}, collections.Counter()
    for b in txt.split("$========== ")[1:]:
        kind = b.split("\n")[0].strip()
        is_place = kind == "PLACE"
        is_person = kind.startswith("PERSON")
        lines = b.split("\n"); sex, brief = "", ""
        for i, l in enumerate(lines):
            c = l.split("\t")
            # a block can hold several individuals: each starts with its own head line (name@ref … Male/Female)
            if not l.startswith(("– ", "@")) and len(c) > 8 and "@" in c[0]:
                sex = c[8].strip()
                nxt = next((x for x in lines[i + 1:] if x.startswith("@Brief=") or (not x.startswith(("– ", "@")) and "@" in x.split("\t")[0])), "")
                brief = nxt[7:].split("\t")[0].strip() if nxt.startswith("@Brief=") else ""
                continue
            if not l.startswith("– ") or l.startswith(("– Total", "– Group", "– Name combined")): continue
            if len(c) < 5: continue
            refs = sorted({(m[0], m[1], m[2]) for m in REF.findall(c[4]) if m[0] in BOOK_NAME}, key=ref_key)
            if not refs: continue
            script = c[2].split("=", 1)[-1] if "=" in c[2] else ""
            forms = [x.strip() for x in script.split(",") if x.strip()]
            for part in c[3].split(";"):
                s = re.sub(r"\(.*?\)", "", part.split("=")[0]).strip()
                if not re.fullmatch(r"[A-Z][a-z'\-]+(?: [A-Z][a-z'\-]+)?", s): continue
                tags = set(re.findall(r"\b(KJV|ESV|NIV)\b", part.split("=", 1)[1])) if "=" in part else {"ESV", "KJV", "NIV"}
                if is_place:
                    p = places.setdefault(s, {"forms": collections.Counter(), "refs": set(), "at": []})
                    for f in forms: p["forms"][f] += len(refs)
                    p["refs"] |= set(refs)
                    # what the place is, from the block holding this line ("Zion|Jerusalem@…" is another name for Jerusalem)
                    main = c[1].split("@")[0].split("|")[-1].replace("_", " ")
                    p["at"].append((refs[0], brief, main if main != s else "", [f for f in forms if is_hebrew(f)]))
                elif is_person and sex in ("Male", "Female"):
                    person_mentions[s] += len(refs)
                    for f in forms:
                        if not is_hebrew(f): continue
                        h = unpoint(f)
                        pe = people.setdefault(h, {"spell": collections.Counter(), "sex": collections.Counter(), "refs": [], "pointed": collections.Counter(), "brief": "", "tags": collections.defaultdict(set)})
                        if len(refs) > max([0] + list(pe["spell"].values())): pe["brief"] = brief
                        pe["spell"][s] += len(refs); pe["sex"][sex] += 1; pe["refs"] += refs; pe["pointed"][f] += len(refs); pe["tags"][s] |= tags
                elif kind == "PLACE+PERSON":
                    person_mentions[s] += len(refs)
    return people, places, person_mentions

def hitchcock():
    out, lines = {}, open(os.path.join(RAW, "hitchcock.txt"), encoding="utf-8").read().split("\n")
    for i, l in enumerate(lines[:-1]):
        m = re.fullmatch(r"   ([A-Z][A-Za-z'\-]+)", l.rstrip())
        nxt = lines[i + 1].strip()
        if m and lines[i + 1].startswith("          ") and nxt:
            out.setdefault(m.group(1).lower(), nxt.rstrip(".;"))
    return out
HITCH = "Hitchcock's Bible Names Dictionary, 1869, public domain"

def cbs():
    """Hebrew spelling → {sex: babies} for Jewish families (CBS 1949–2024), and Latin pairings from raw/il-latin.csv"""
    babies = collections.defaultdict(collections.Counter)
    for f in ("il.csv", "il-other.csv"):
        p = os.path.join(RAW, f)
        if not os.path.exists(p): continue
        for r in csv.DictReader(open(p, encoding="utf-8")):
            if r["sector"] in ("Jewish", "Other"): babies[unpoint(r["name"])]["b" if r["sex"] == "M" else "g"] += int(r["n"])
    pairs = collections.defaultdict(list)
    for r in csv.DictReader(open(os.path.join(RAW, "il-latin.csv"), encoding="utf-8")):
        # only the vetted pairings: a "verified reading" is a reading of the letters checked against other countries' registers
        # (Abby for אבי, Minor for מנור), so it never names a Hebrew name here
        if r["community"] in ("Jewish", "Other") and r["how"] in ("known pairing", "usual spelling"): pairs[unpoint(r["hebrew"])].append((r["name"], r["how"]))
    return babies, pairs

# ─────────────────────────────────────────────────────────────
WITNESS = set()       # Hebrew spellings some other source has (Wiktionary, Israel's records)
def clean_hitchcock(m):
    """Hitchcock's cross-references are not meanings: "or Urijah, the Lord is my light" → "the Lord is my light"; "same as Naashon" → none"""
    m = re.sub(r"^(?:or |the same as |same with )?[A-Z][a-z\-]+(?:, or [A-Z][a-z\-]+)?,\s*", "", m)
    return "" if re.match(r"(?:the )?same (?:as|with)\b|see [A-Z]", m) else m

def build_names(story, registry):
    babies, pairs = cbs()
    counts = {"wikt": en_wiktionary(), "hewikt": he_wiktionary()}
    WITNESS.update(babies, E)
    counts["wikidata"] = wikidata()
    people, places, person_mentions = tipnr()
    hitch = hitchcock()
    print("entries from", counts)
    # TIPNR: Hebrew Bible people, by their Hebrew form; and the Bible's spellings of names other sources gave
    for h, pe in people.items():
        if h not in E and all(r[0] in NT for r in pe["refs"]): continue   # Hebrew Bible people, or names another source gave
        e = E[h]
        if not e["src"]: e["src"].append(("tipnr", ""))
        elif not any(s == "tipnr" for s, _ in e["src"]): e["src"].append(("tipnr", ""))
        e["bible"] = True
        for f, c in pe["pointed"].items(): e["pointed"][f] += c
        for s, _ in pe["spell"].most_common():
            if s.lower() not in TITLES and not re.search(r"(ites?|eans?)$", s): add_latin(h, s, "tipnr")
        if not e["sex"]:   # the Bible's sex only where no name source gave one
            for sx, c in pe["sex"].items(): e["sex"]["b" if sx == "Male" else "g"] += c
        first = min(pe["refs"], key=ref_key); e["first"] = e["first"] or verse(first); e["brief"] = e["brief"] or pe["brief"]
        for s, _ in pe["spell"].most_common():
            m = clean_hitchcock(hitch.get(s.lower(), ""))
            # a Bible name's meaning comes from the Bible dictionary first (Merav is Merab, not the modern word for 'maximum')
            if m: e["meaning"].insert(0, (m, HITCH)); break
    # Israel's records: Latin pairings for names the sources gave without one, and the babies
    for h, e in E.items():
        for n, how in pairs.get(h, []): add_latin(h, n, "cbs")

    rows, skipped, stats = [], collections.Counter(), collections.Counter()
    taken = set()
    for h, e in sorted(E.items()):
        if not e["latin"]: skipped["no Latin spelling in any source"] += 1; continue
        if not e["sex"] and sum(babies.get(h, {}).values()) >= 20:
            # no name source says: Israel's records do (the sex of the babies given the name; both if each has a fifth)
            c = babies[h]; tot = c["b"] + c["g"]
            e["sex"]["e" if min(c["b"], c["g"]) >= .2 * tot else "b" if c["b"] > c["g"] else "g"] += 1; e["sex_from_cbs"] = True
        if not e["sex"]: skipped["no sex in any source"] += 1; continue
        b, g, both = e["sex"]["b"], e["sex"]["g"], e["sex"]["e"]
        sx = "e" if both >= max(b, g) or (b and g and min(b, g) * 2 >= max(b, g)) else "b" if b > g else "g"
        pointed = e["pointed"].most_common(1)[0][0] if e["pointed"] else h
        if not any(re.search(r"[ְ-ֻ]", p) for p in [pointed]):
            pointed = next((p for p, _ in e["pointed"].most_common() if re.search(r"[ְ-ֻ]", p)), pointed)
        lat = sorted(e["latin"], key=lambda x: SRC_ORDER[x[1]])
        # the name sources' spellings; Israel's pairing only when they give none; a transliteration only when nothing else does
        strong = [x for x in lat if x[1] in STRONG - {"cbs"} and not x[2]] or [x for x in lat if x[1] == "cbs"]
        usable = strong or [x for x in lat if not x[2]][:1]
        if not usable: skipped["only alias spellings"] += 1; continue
        spellings = list(dict.fromkeys(s for s, _, _ in usable))
        # the plain-letter spelling to state: a name source's or Israel's before the English Bible's (Zeev, not KJV Zeeb)
        plain_any = next((s for s, how, _ in sorted(lat, key=lambda x: x[1] == "tipnr") if PLAIN.fullmatch(s)), None)
        srcs = [s for s, _ in e["src"]]
        kinds = {s for s in srcs}
        meaning, msrc = next(((m, s) for m, s in e["meaning"] if m and len(m) < 90), ("", ""))
        for s in spellings:
            k = fold(s)
            if k in story or k in taken: continue
            how = next(x[1] for x in usable if x[0] == s)
            taken.add(k)
            ease = 1 if PLAIN.fullmatch(s) else 2 if plain_any and plain_any != s else 3
            label = []
            if "wikt" in kinds: label.append("Wiktionary")
            if "hewikt" in kinds: label.append("Hebrew Wiktionary")
            if "wikidata" in kinds: label.append(f"Wikidata {e['qid']}")
            if "tipnr" in kinds and not label: label.append("STEPBible")
            head = (f"A Hebrew name from the Bible, first in {e['first']} (STEPBible)" if e["bible"] and e["first"] and "tipnr" in kinds and len(label) == 1 and label[0] == "STEPBible"
                    else f"A Hebrew name ({'; '.join(label)})")
            parts = [head + ".", f"Written {pointed}."]
            if e["bible"] and e["first"] and not head.startswith("A Hebrew name from the Bible"): parts.append(f"In the Bible, first in {e['first']} (STEPBible).")
            parts.append(f"Latin spelling from {LATIN_FROM[how]}.")
            if meaning: parts.append(f"Meaning '{meaning}' ({msrc}).")
            c = babies.get(h)
            if c and sum(c.values()): parts.append(f"Given to {sum(c.values()):,} babies in Israel since 1949 (CBS).")
            if e.get("dim"): parts.append(f"A diminutive of {e['dim']} (Wiktionary).")
            if e.get("sex_from_cbs"): parts.append("Boy or girl as recorded by the CBS.")
            if ease == 2: parts.append(f"Also written {plain_any}.")
            faith = "Jewish" if e["bible"] else ""
            rows.append([s, sx, "Hebrew", "Hebrew", faith, meaning, " ".join(parts), "", "real", [], ease])
            stats[how] += 1; stats["in a registry already" if k in registry else "new to every list"] += 1
    rows.sort(key=lambda r: (r[10], r[0]))
    return rows, skipped, stats, places, person_mentions, hitch

# ─────────────────────────────────────────────────────────────
# places in the Bible that are given names
# ─────────────────────────────────────────────────────────────
OFFICIAL_SKIP = {"wd", "wikt", "wikt2"}          # Wikidata and Wiktionary listings are not records of people
ENGLISH_OR_ISRAEL = {"us", "uk", "ca", "qc", "au", "ie", "nir", "sct", "nz", "il"}
MIN_PEOPLE = 100
# the places the owner named: these need only the rule itself (in the official records at all, or a given name on Wiktionary)
OWNER_NAMED = {"Bethany", "Sharon", "Jordan", "Eden", "Shiloh", "Salem", "Carmel", "Hebron", "Bethel", "Galilee", "Zion", "Canaan", "Goshen", "Jericho"}
# names that pass the records test but are a different name with the same letters, or a modern country or city whose use as a name
# owes nothing to the Bible: left out (reason given)
NOT_THE_PLACE = {
    "Asia": "the continent", "India": "the country", "Italy": "the country", "Egypt": "the country", "Syria": "the country",
    "Malta": "the country", "Cyprus": "the country", "Spain": "the country", "Persia": "the country", "Armenia": "the country",
    "Arabia": "the region", "Rome": "the city", "Athens": "the city", "Memphis": "the US city (Tennessee) and Egyptian city",
    "Alexandria": "the feminine of Alexander", "Philadelphia": "the US city", "Damascus": "the city", "Phoenix": "the bird and the US city",
    "Roman": "the name Roman (Latin Romanus); TIPNR's 'Roman' is an adjective", "Nile": "the river; Nile as a name is mostly Irish Niall's spelling",
    "Ava": "the English name Ava", "Myra": "the English name Myra", "Adria": "the Catalan form of Adrian", "Luz": "the Spanish name Luz (light)",
    "Salim": "the Arabic name Salim", "Koa": "the Hawaiian name Koa", "Pau": "the Catalan form of Paul", "Sina": "a German and Samoan name",
    "Hali": "an Estonian and Indian name", "Hara": "a name of Shiva", "Hena": "an Albanian and Bengali name", "Lasha": "the Georgian name Lasha",
    "Jaan": "the Estonian form of John", "Aija": "the Latvian and Finnish name Aija", "Ain": "the Estonian name Ain", "Ezel": "the Turkish name Ezel",
    "Azem": "the Albanian name Azem", "Chun": "the Chinese name Chun", "Kun": "the Chinese name Kun", "Shen": "the Chinese name Shen", "Pai": "the Chinese and Thai name Pai",
    "Dung": "the Vietnamese name Dung", "Eshan": "the Indian name Eshan", "Mashal": "the Urdu name Mashal", "Mishal": "the Arabic name Mishal",
    "Sahar": "the Arabic and Hebrew word for dawn / moon as a modern name", "Zahar": "the Arabic name Zahar", "Zair": "the Arabic name Zair",
    "Cesarea": "the Spanish and Italian name Cesarea (from Caesar)", "Melita": "the Greek and Italian name Melita", "Grecia": "the Spanish name Grecia",
    "Sinai": "a Spanish given name", "Sela": "a name from the word (rock / selah)", "Tarah": "a spelling of Tara", "Seba": "a Spanish name",
    "Neah": "a spelling of Neha / Nia", "Hilen": "a spelling of Helen", "Kain": "the Finnish form of Cain", "Amana": "a Japanese and Arabic name",
    "Ivah": "a spelling of Iva", "Aven": "an English name (Avon)", "Harmon": "the English surname Harmon", "Rhodes": "the surname Rhodes",
    "Tyrus": "a spelling of Tyrese / Tyree", "Tyre": "the English name Tyre (Tyree)", "Corban": "a spelling of Corbin", "Dor": "the Hebrew word dor (generation) as a modern name",
    "Javan": "a spelling of Javon", "Kamon": "a spelling of Camon / Kameron", "Saphir": "the French word for sapphire", "Shion": "the Japanese name Shion",
    "Sirah": "a spelling of Sira", "Zela": "a spelling of Zella", "Lycia": "a spelling of Licia / Lucia",
    "Magdalene": "the name Magdalene comes from Mary Magdalene, a person", "Corinthian": "an adjective", "Nazarene": "an adjective",
    "Median": "an adjective", "Media": "the English word media", "Arab": "the people", "Ether": "the English word ether", "Giah": "a spelling of Gia",
    "Halah": "the Arabic name Hala", "Shalisha": "a spelling of Shalisa", "Ar": "two letters", "On": "an English word", "No": "an English word",
    "Ai": "the Japanese and Chinese name Ai", "Ur": "the Basque name Ur", "Mamre": "too few records", "Lehi": "the Book of Mormon prophet Lehi",
    "Angle": "a word in the English Bible's 'Angle' (corner), not a place name", "Dilean": "a spelling of Dillon",
    "Anab": "the Hebrew word anav (grape) as a modern name", "Amad": "the Arabic name Amad", "Allon": "the Hebrew name Alon (oak) and the person Allon",
    "Almon": "the English surname Almon", "Azal": "the Arabic name Azal", "Ashan": "a South Asian name", "Neiel": "a spelling of Neil",
    "Calah": "a spelling of Kayla", "Rachal": "a spelling of Rachel", "Dannah": "a spelling of Dana", "Dura": "a Spanish name", "Nimrah": "the Urdu name Nimra",
    "Senir": "the Hebrew name Snir", "Kishon": "a spelling of Keshawn", "Janoah": "a spelling of Janae / Noah", "Wadi": "the Arabic word for a valley",
    "Etham": "a spelling of Ethan", "Enam": "the Bengali name Enam", "Seir": "the person Seir", "Edrei": "too few records",
    "Ariel": "the name Ariel (also a man in Ezra 8:16); Isaiah's Ariel is a poetic name for Jerusalem", "Ahava": "the Hebrew word for love as a modern name",
    "Leshem": "the Hebrew word for a gemstone as a modern name", "Shamir": "the Hebrew name Shamir (also a Levite in 1 Chronicles 24:24)",
    "Lasharon": "La- + Sharon, a modern American coinage", "Zared": "a spelling of Jared", "Rameses": "the pharaohs' name",
    "Aswan": "the modern Egyptian city (NIV's name for Syene)", "Madian": "a Spanish and Romanian name",
}
# TIPNR files some places under the English words a translation uses for them (the Brook of Egypt, the Valley Gate)
ENGLISH_WORDS = {"River", "Red", "Great", "No", "On", "Valley", "Fountain", "Beautiful", "Brook", "Iron", "Water", "East", "South", "New",
                 "Horse", "Married", "Desolate", "Forsaken", "Token", "Mortar", "Muster", "Olives", "Dung", "Angle", "Wadi", "Ether", "Media"}
BIBLE_LINK = re.compile(r"bibl|Bible|Testament|Holy Land|transferred|place|river|mountain|city|town|village|valley|plain|region", re.I)

def wikt_given():
    out = collections.defaultdict(set)
    for l in open(os.path.join(RAW, "wikt-given-names.tsv"), encoding="utf-8"):
        c = l.rstrip("\n").split("\t")
        # English given names only: a place name used as a name in English (Ai in Japanese is another name)
        if len(c) == 2 and re.fullmatch(r"English (?:(?:male|female|unisex) )?given names", c[1]): out[c[0]].add(c[1])
    return out

def english_section(t):
    i = t.find("==English==")
    if i < 0: return ""
    t = t[i + 11:]; m = re.search(r"\n==[^=]", t)
    return t[:m.start()] if m else t

def build_places(registry, places, person_mentions, hitch, story_culture):
    wg = wikt_given()
    pre = {}
    for s, p in places.items():
        r = registry.get(fold(s))
        official = [c for c in r[1] if c not in OFFICIAL_SKIP] if r else []
        if official or wg.get(s): pre[s] = (p, r, official)
    pages = cached("enwikt-place-pages-all.json", lambda: wikitexts(EN_WT, sorted(pre)))
    rows, dropped, seen = [], [], {}
    # one row per name: Bethel, not also KJV's Beth-el (the spelling with more verses wins)
    for s in sorted(pre, key=lambda s: (-len(pre[s][0]["refs"]), "-" in s, s)):
        p, r, official = pre[s]; k = fold(s)
        if k in seen: continue
        en = english_section(pages.get(s, ""))
        gn = [l for l in en.split("\n") if re.search(r"\{\{given name\|en\b", l)]
        wikt_link = bool(wg.get(s)) and any(BIBLE_LINK.search(l) for l in gn)
        mentions = len(p["refs"])
        if person_mentions.get(s, 0) > mentions:
            dropped.append((s, f"a person's name more often than a place ({person_mentions[s]} vs {mentions} verses)")); continue
        if s in OWNER_NAMED: why = "owner"
        elif s in NOT_THE_PLACE: dropped.append((s, NOT_THE_PLACE[s])); continue
        elif wikt_link: why = "wiktionary"
        elif not (r and r[2] >= MIN_PEOPLE and set(official) & ENGLISH_OR_ISRAEL):
            dropped.append((s, "fewer than 100 people in English-speaking or Israeli records, and not a Wiktionary given name from the place")); continue
        elif s in ENGLISH_WORDS: dropped.append((s, "an English word: the English Bible's translation, not a place name")); continue
        elif story_culture.get(k, set()) - {"Hebrew", "Israeli", "English", ""}:
            dropped.append((s, "the site knows it as a " + "/".join(sorted(story_culture[k] - {"Hebrew", "Israeli", "English", ""})) + " name")); continue
        else: why = "records"
        seen[k] = s
        first = min(p["refs"], key=ref_key)
        at = min(p["at"], key=lambda a: ref_key(a[0]))
        heb = at[3] or [f for f, _ in p["forms"].most_common() if is_hebrew(f)]
        if heb: written = heb[0]
        else:
            m = re.search(r"\{\{(?:der|bor|inh)\|en\|(he|hbo|arc)\|([^|}]+)", en)
            gr = next((f for f, _ in p["forms"].most_common() if re.search(r"[Ͱ-Ͽἀ-῿]", f)), "")
            frm = re.sub(r"\[\[|\]\]", "", m.group(2)) if m else ""
            if frm and is_hebrew(frm):
                written = (f"{gr} in the Greek New Testament, from " if gr else "") + f"{'Aramaic' if m.group(1) == 'arc' else 'Hebrew'} {frm} (Wiktionary)"
            elif gr: written = f"{gr} in the Greek New Testament; no Hebrew form in the sources"
            else: dropped.append((s, "no Hebrew or Greek form")); seen.pop(k); continue
        nt_only = all(x[0] in NT for x in p["refs"])
        if official and r: sx = {"f": "g", "m": "b", "u": "e"}.get(r[0])
        else: sx = None
        if not sx and wg.get(s):
            ss = {("g" if "female" in c else "b" if " male" in c else "e" if "unisex" in c else None) for c in wg[s]} - {None}
            sx = "e" if "e" in ss or {"b", "g"} <= ss else next(iter(ss), None)
        if not sx: dropped.append((s, "no sex in the records")); seen.pop(k); continue
        evidence = []
        if official and r: evidence.append(f"Given to {r[2]:,} people in the official name records on this site")
        if wikt_link: evidence.append("Wiktionary lists it as an English given name taken from the place")
        elif wg.get(s): evidence.append("Wiktionary lists it as an English given name")
        same = at[2] and difflib.SequenceMatcher(None, s.lower(), at[2].lower()).ratio() >= .6     # Kerith ~ Cherith: a spelling
        what = (f"{'The same place as' if same else 'Another name for'} {at[2]}" + (f": {at[1].rstrip('.')}" if at[1] else "")) if at[2] else at[1].rstrip(".")
        if person_mentions.get(s): what += f". Also the name of a person in the Bible ({person_mentions[s]} verse{'s' if person_mentions[s] > 1 else ''})"
        m = hitch.get(s.lower(), "")
        story = (f"A place in the Bible used as a given name: {s}, first in {verse(first)}. Written {written}. "
                 + (f"{what} (STEPBible). " if what else "") + "; ".join(evidence) + "."
                 + (f" Meaning '{m}' ({HITCH})." if m else ""))
        ease = 1 if PLAIN.fullmatch(s) else 3
        rows.append([s, sx, "Hebrew", "Hebrew", "Christian" if nt_only else "Christian,Jewish", m, story, "", "real", [], ease,
                     {"place": True, "first": verse(first), "ref": f"{first[0]}.{first[1]}.{first[2]}", "evidence": why}])
    rows.sort(key=lambda r: (r[10], r[0]))
    return rows, dropped

if __name__ == "__main__":
    story, registry = site_names()
    rows, skipped, stats, places, person_mentions, hitch = build_names(story, registry)
    json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(rows):,} new Hebrew names → data/hebrew-extra.json", dict(stats), "skipped:", dict(skipped))
    print("sex", collections.Counter(r[1] for r in rows), "ease", collections.Counter(r[10] for r in rows))
    prow, dropped = build_places(registry, places, person_mentions, hitch, story_culture())
    json.dump(prow, open(OUT_PLACES, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(prow)} Bible places used as given names → data/bible-place-names.json; left out: {len(dropped)}")
    for s, why in dropped: print("  -", s, ":", why)
