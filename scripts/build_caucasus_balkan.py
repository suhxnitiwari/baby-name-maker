# Georgian and Albanian names → data/caucasus-balkan-names.json, in the row format of data/culture-names.json:
#   [name, g ('g'|'b'|'e'), culture, language, religions, meaning, story, texts, kind, also]
#
# Sources (open licences only; nothing is guessed: culture, sex and meaning are only what a source states):
#   English Wiktionary (CC BY-SA 4.0): "Georgian/Albanian male/female/unisex given names" and their subcategories
#     (diminutives, "from <language>"), each page's wikitext. Sex from the category; meaning from the entry.
#   Georgian Wiktionary (CC BY-SA 4.0): "მამაკაცის სახელი (ქართული)" (male) and "ქალის სახელი (ქართული)" (female).
#     Used for the name and its sex only: its definitions are Georgian-language noun senses, not name meanings.
#   Albanian Wiktionary (CC BY-SA 4.0): has no given-name category ("Emra shqip" is "Albanian nouns"); probed and recorded.
#   Wikidata (CC0): given-name items (P31 Q202444 / Q11879590 female / Q12308941 male / Q3409032 unisex) whose
#     "language of work or name" (P407) is Georgian (Q8108) or Albanian (Q8748), or whose native label (P1705) is tagged
#     ka / sq, or (Georgian) is written in Mkhedruli with no other language given. Sex from the class; items that are only
#     "given name" (Q202444) with no sex anywhere else are left out.
#
# Georgian names are spelled in Latin by the national romanization (2002) without its apostrophes (ქ and კ both k,
# თ and ტ t, ფ and პ p, ც and წ ts, ჩ and ჭ ch, ყ q, ღ gh, ხ kh, ჟ zh, ჯ j), as Georgians write their names: Giorgi,
# Ketevan, Tsotne. The Mkhedruli spelling is kept as "Written <native>." so the script index (build_native_forms.py)
# picks it up. Albanian names keep ë and ç.
#
# Only names not already in data/culture-names.json with the same culture are written.
#
#   python3 scripts/build_caucasus_balkan.py            (downloads into raw/caucasus-balkan/ once; delete a file to refetch)
import collections, json, os, re, sys, time, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "raw", "caucasus-balkan"); OUT = os.path.join(ROOT, "data", "caucasus-balkan-names.json")
sys.path.insert(0, HERE)
from build_cultures import section, clean, details, georgian, latinize_tr  # same entry parsing and Georgian table as culture-names.json
UA = {"User-Agent": "Lullabyte/1.0 (https://github.com/suhxnitiwari/baby-name-maker; suhxnitiwari@gmail.com)"}
GEO = re.compile(r"^[ა-ჰ]+$")
LAT = re.compile(r"^[A-Za-zÀ-ɏ]+(?:-[A-Za-zÀ-ɏ]+)?$")

def get(url, data=None):
    for attempt in range(30):
        try:
            req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode() if data else None, headers=UA)
            d = json.load(urllib.request.urlopen(req, timeout=120))
            if isinstance(d, dict) and d.get("error", {}).get("code") == "maxlag": time.sleep(10); continue
            return d
        except Exception as e:
            print("  retry", url[:60], e, file=sys.stderr); time.sleep(3 * (attempt + 1))
    raise RuntimeError("kept failing: " + url)

def wiki(host, **q):
    q.update(format="json", maxlag="20", formatversion="2")
    return get(f"https://{host}/w/api.php", q)

def members(host, cat, cmtype="page"):
    out, cont = [], {}
    while True:
        d = wiki(host, action="query", list="categorymembers", cmtitle=cat, cmlimit="500", cmtype=cmtype, **cont)
        out += [m["title"] for m in d.get("query", {}).get("categorymembers", [])]
        if "continue" not in d: return out
        cont = d["continue"]; time.sleep(.3)

def texts(host, titles):
    out = {}
    for i in range(0, len(titles), 50):
        d = wiki(host, action="query", prop="revisions", rvprop="content", rvslots="main", titles="|".join(titles[i:i + 50]))
        for p in d.get("query", {}).get("pages", []):
            out[p["title"]] = ((p.get("revisions") or [{}])[0].get("slots", {}).get("main", {}).get("content", ""))
        time.sleep(.5)
    return out

def cached(name, fetch):
    os.makedirs(RAW, exist_ok=True)
    path = os.path.join(RAW, name)
    if not os.path.exists(path):
        print("  fetching", name, flush=True)
        json.dump(fetch(), open(path, "w", encoding="utf-8"), ensure_ascii=False)
    return json.load(open(path, encoding="utf-8"))

# ── English Wiktionary: every page under the male/female/unisex categories, subcategories included ──
def fetch_en(lang):
    sex = {}
    for g, label in (("b", "male"), ("g", "female"), ("e", "unisex")):
        todo, seen = [f"Category:{lang} {label} given names"], set()
        while todo:
            cat = todo.pop()
            if cat in seen: continue
            seen.add(cat)
            for t in members("en.wiktionary.org", cat): sex[t] = "e" if t in sex and sex[t] != g else g
            todo += members("en.wiktionary.org", cat, "subcat")
    tx = texts("en.wiktionary.org", sorted(sex))
    return {t: {"g": g, "text": tx.get(t, "")} for t, g in sex.items()}

# ── Georgian Wiktionary ──
KA_CATS = {"კატეგორია:მამაკაცის სახელი (ქართული)": "b", "კატეგორია:ქალის სახელი (ქართული)": "g"}
def fetch_ka():
    sex = {}
    for cat, g in KA_CATS.items():
        for t in members("ka.wiktionary.org", cat): sex[t] = "e" if t in sex and sex[t] != g else g
    return {t: {"g": g} for t, g in sex.items()}

# ── Albanian Wiktionary: look for a given-name category ──
def fetch_sq():
    found = {}
    for prefix in ("Emra", "Emër", "Emrat", "Antroponim"):
        d = wiki("sq.wiktionary.org", action="query", list="allcategories", acprefix=prefix, aclimit="500", acprop="size")
        for c in d.get("query", {}).get("allcategories", []):
            found[c["category"]] = c.get("pages", 0)
    return found

# ── Wikidata ──
WD_Q = """SELECT ?i ?cls ?lang ?nl ?en ?ka ?sq WHERE {
  VALUES ?cls { wd:Q202444 wd:Q11879590 wd:Q12308941 wd:Q3409032 }
  ?i wdt:P31 ?cls .
  { ?i wdt:P407 ?L . VALUES ?L { wd:Q8108 wd:Q8748 } } UNION
  { ?i wdt:P1705 ?x . FILTER(LANG(?x) IN ("ka", "sq") || REGEX(STR(?x), "^[ა-ჰ]+$")) }
  OPTIONAL { ?i wdt:P407 ?lang }
  OPTIONAL { ?i wdt:P1705 ?nl }
  OPTIONAL { ?i rdfs:label ?en FILTER(LANG(?en) IN ("en", "mul")) }
  OPTIONAL { ?i rdfs:label ?ka FILTER(LANG(?ka) = "ka") }
  OPTIONAL { ?i rdfs:label ?sq FILTER(LANG(?sq) = "sq") }
}"""
def fetch_wd():
    d = get("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": WD_Q, "format": "json"}))
    items = {}
    for b in d["results"]["bindings"]:
        q = b["i"]["value"].rsplit("/", 1)[1]
        it = items.setdefault(q, {"cls": [], "lang": [], "native": [], "en": "", "ka": "", "sq": ""})
        c = b["cls"]["value"].rsplit("/", 1)[1]
        if c not in it["cls"]: it["cls"].append(c)
        if "lang" in b:
            l = b["lang"]["value"].rsplit("/", 1)[1]
            if l not in it["lang"]: it["lang"].append(l)
        if "nl" in b:
            v = [b["nl"]["value"], b["nl"].get("xml:lang", "")]
            if v not in it["native"]: it["native"].append(v)
        for k in ("en", "ka", "sq"):
            if k in b: it[k] = b[k]["value"]
    return items
CLS_SEX = {"Q11879590": "g", "Q12308941": "b", "Q3409032": "e"}
KA, SQ = "Q8108", "Q8748"

def sex_of(gs):
    gs = set(gs) - {""}
    if not gs: return ""
    return "e" if "e" in gs or len(gs) > 1 else gs.pop()

# meaning glosses in an English Wiktionary etymology: t=/gloss=/lit=, or the gloss slot of {{m}}, {{l}}, {{der}}, {{bor}}, {{inh}}
GLOSS_POS = {"m": 4, "l": 4, "der": 5, "bor": 5, "inh": 5, "uder": 5, "cog": 4}
def ety_glosses(sec):
    ety = re.search(r"(?ms)^===+\s*Etymology[^=]*===+\s*$(.*?)(?=^===)", sec)
    if not ety: return ""
    # only the first sentence, and only when it says where the name is from ("From {{m|sq|shpresë||hope}}.")
    e = re.split(r"(?<=[.;])\s", ety.group(1).strip(), maxsplit=1)[0]
    if not re.match(r"^From\b", e) or re.search(r"\b(uncertain|unknown|possibly|perhaps|probably|folk etymology|disputed|compare|cognate|akin)\b", e, re.I): return ""
    gl = []
    for tpl in re.findall(r"\{\{([^{}]*)\}\}", e):
        parts = tpl.split("|"); name = parts[0].strip()
        kw = {p.split("=", 1)[0].strip(): p.split("=", 1)[1] for p in parts[1:] if "=" in p}
        pos = [p for p in parts[1:] if "=" not in p]
        g = kw.get("t") or kw.get("gloss") or kw.get("lit")
        if not g and name in GLOSS_POS and len(pos) >= GLOSS_POS[name]: g = pos[GLOSS_POS[name] - 1]   # {{m|sq|shpresë||hope}}
        if not g and name in ("af", "affix", "compound", "com"):
            ts = [kw[k] for k in sorted(kw) if re.match(r"^t\d$", k)]
            if ts and len(ts) == len(pos) - 1: g = " + ".join(ts)
        g = clean(g or "")
        if g and re.match(r"^[A-Za-z][A-Za-z ,;:'()/-]*$", g): gl.append(g)
    gl = list(dict.fromkeys(gl))
    return gl[0] if len(gl) == 1 else ""

HEDGE = re.compile(r"\b(perhaps|possibly|probably|uncertain|unknown|disputed|folk etymology)\b", re.I)
def meaning_from(text, lang):
    sec = section(text, lang)
    if not sec: return {}, ""
    # a page with several etymologies (მაშა: "pliers" and the name Masha): only the one with the given-name sense
    parts = re.split(r"(?m)^(?====+\s*Etymology \d)", sec)
    if len(parts) > 1:
        sec = next((p for p in parts if "{{given name|" in p), "")
        if not sec: return {}, ""
    d = details(sec)
    m = d.get("meaning") or ety_glosses(sec)
    ety = re.search(r"(?ms)^===+\s*Etymology[^=]*===+\s*$(.*?)(?=^===)", sec)
    stated = re.search(r"\{\{given name\|[^{}]*\|meaning=", sec)
    if m and not stated and ety and HEDGE.search(re.split(r"(?<=\.)\s", ety.group(1).strip(), maxsplit=1)[0]): m = ""   # "Perhaps from …"
    # a chain of borrowings (Ottoman "lady" ← Sogdian "queen") is one meaning, not a compound
    if " + " in m and ety and not re.search(r"\{\{(?:af|affix|compound|com\+?|suffix|prefix|blend)\|", ety.group(1)): m = m.split(" + ")[0]
    m = re.sub(r"\s*[”\"]\s*or\s*[“\"]\s*", " or ", m or "").strip(" “”\"")
    return d, m

# ── Pashto: only names whose own entry makes them Pashto words (no "borrowed from Arabic/Persian") ──
PS_Q = """SELECT ?i ?cls ?lang ?nl ?en WHERE {
  VALUES ?cls { wd:Q202444 wd:Q11879590 wd:Q12308941 wd:Q3409032 }
  ?i wdt:P31 ?cls ; wdt:P407 wd:Q58680 .
  OPTIONAL { ?i wdt:P407 ?lang } OPTIONAL { ?i wdt:P1705 ?nl } OPTIONAL { ?i rdfs:label ?en FILTER(LANG(?en) = "en") } }"""
def fetch_ps_wd():
    d = get("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": PS_Q, "format": "json"}))
    items = {}
    for b in d["results"]["bindings"]:
        it = items.setdefault(b["i"]["value"].rsplit("/", 1)[1], {"cls": set(), "lang": set(), "native": set(), "en": ""})
        it["cls"].add(b["cls"]["value"].rsplit("/", 1)[1])
        if "lang" in b: it["lang"].add(b["lang"]["value"].rsplit("/", 1)[1])
        if "nl" in b: it["native"].add((b["nl"]["value"], b["nl"].get("xml:lang", "")))
        if "en" in b: it["en"] = b["en"]["value"]
    return {q: {k: sorted(v) if isinstance(v, set) else v for k, v in it.items()} for q, it in items.items()}
PS_LETTERS = re.compile(r"^[\u0600-\u06FF\u0750-\u077F]+$")
def pashto_origin(sec):
    """(is a Pashto-origin given name, sex, Latin spelling) from the entry's Pashto section."""
    gn = re.search(r"\{\{given name\|ps\|([^{}]*)\}\}", sec)
    if not gn: return False, "", ""
    parts = gn.group(1).split("|")
    kw = {p.split("=", 1)[0]: p.split("=", 1)[1] for p in parts if "=" in p}
    pos = [p for p in parts if "=" not in p]
    sex = {"male": "b", "female": "g", "unisex": "e"}.get(pos[0] if pos else "", "")
    xlit = kw.get("xlit", "").split(",")[0].strip()
    if len(pos) > 1 or kw.get("from"): return False, sex, xlit                 # "{{given name|ps|male|Arabic}}", from=Persian
    ety = re.search(r"(?ms)^===+\s*Etymology[^=]*===+\s*$(.*?)(?=^===)", sec)
    if ety and re.search(r"\{\{(?:bor\+?|der\+?|inh\+?|lbor|slbor|ety)\|ps\|(?!ps\b)", ety.group(1)): return False, sex, xlit
    if ety and re.search(r"\{\{(?:com\+?|af|affix|compound)\|ps\|", ety.group(1)): return True, sex, xlit   # a Pashto compound (ابا + سین)
    # no etymology: a Pashto word whose page also gives it as a name (هېلۍ "duck")
    return (not ety and bool(re.search(r"(?m)^===+\s*(Noun|Adjective)\s*===+", sec))), sex, xlit

# ── San Marino: the given names (P735) of every Captain Regent (P39 = Q258045) ──
SM_Q = """SELECT ?p ?pLabel ?gn ?start ?sex WHERE {
  ?p p:P39 ?st . ?st ps:P39 wd:Q258045 . OPTIONAL { ?st pq:P580 ?start }
  OPTIONAL { ?p wdt:P735 ?gn } OPTIONAL { ?p wdt:P21 ?sex }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". } }"""
SM_GN = """SELECT * WHERE { VALUES ?gn { %s }
  OPTIONAL { ?gn wdt:P31 ?cls } OPTIONAL { ?gn rdfs:label ?it FILTER(LANG(?it) = "it") }
  OPTIONAL { ?gn rdfs:label ?en FILTER(LANG(?en) = "en") } OPTIONAL { ?gn rdfs:label ?mul FILTER(LANG(?mul) = "mul") }
  OPTIONAL { ?gn wdt:P1705 ?nl }
  OPTIONAL { ?gn wdt:P407 ?lang } }"""
def fetch_sm():
    d = get("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": SM_Q, "format": "json"}))
    people = {}
    for b in d["results"]["bindings"]:
        pp = people.setdefault(b["p"]["value"].rsplit("/", 1)[1], {"label": b["pLabel"]["value"], "gn": [], "start": [], "sex": ""})
        if "gn" in b and b["gn"]["value"].rsplit("/", 1)[1] not in pp["gn"]: pp["gn"].append(b["gn"]["value"].rsplit("/", 1)[1])
        if "start" in b and b["start"]["value"][:4] not in pp["start"]: pp["start"].append(b["start"]["value"][:4])
        if "sex" in b: pp["sex"] = b["sex"]["value"].rsplit("/", 1)[1]
    for pp in people.values(): pp["gn"] = [q for q in pp["gn"] if re.match(r"^Q\d+$", q)]       # not "unknown value"
    qs = sorted({q for pp in people.values() for q in pp["gn"]})
    names = {}
    for i in range(0, len(qs), 200):
        d = get("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": SM_GN % " ".join("wd:" + q for q in qs[i:i + 200]), "format": "json"}))
        for b in d["results"]["bindings"]:
            n = names.setdefault(b["gn"]["value"].rsplit("/", 1)[1], {"cls": [], "it": "", "en": "", "mul": "", "nl": "", "lang": []})
            if "cls" in b and b["cls"]["value"].rsplit("/", 1)[1] not in n["cls"]: n["cls"].append(b["cls"]["value"].rsplit("/", 1)[1])
            if "lang" in b and b["lang"]["value"].rsplit("/", 1)[1] not in n["lang"]: n["lang"].append(b["lang"]["value"].rsplit("/", 1)[1])
            for k in ("it", "en", "mul", "nl"):
                if k in b: n[k] = b[k]["value"]
        time.sleep(1)
    return {"people": people, "names": names}
LANG_QID = {"Q652": "Italian", "Q397": "Latin", "Q1860": "English", "Q150": "French", "Q188": "German", "Q1321": "Spanish", "Q5146": "Portuguese",
            "Q9027": "Swedish", "Q9035": "Danish", "Q9043": "Norwegian", "Q7411": "Dutch", "Q9056": "Czech", "Q809": "Polish", "Q9067": "Hungarian",
            "Q7737": "Russian", "Q35497": "Ancient Greek", "Q9129": "Greek", "Q9288": "Hebrew", "Q13955": "Arabic", "Q256": "Turkish", "Q1412": "Finnish",
            "Q8748": "Albanian", "Q7913": "Romanian", "Q9078": "Latvian", "Q9083": "Lithuanian", "Q9072": "Estonian", "Q9063": "Slovene", "Q9058": "Slovak",
            "Q8798": "Ukrainian", "Q7918": "Bulgarian", "Q9299": "Serbian", "Q6654": "Croatian", "Q9142": "Irish", "Q9309": "Welsh", "Q7026": "Catalan",
            "Q8752": "Basque", "Q9307": "Galician", "Q294": "Icelandic", "Q33965": "Venetian", "Q15085": "Romagnol", "Q33970": "Emilian"}
def fold(s):
    import unicodedata
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"[\s-]", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))
def attested():
    """every name already in our data, folded as in app.js"""
    out = set()
    for f in ("names-db.tsv", "names-extra.tsv"):
        p = os.path.join(ROOT, "data", f)
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"): out.add(fold(line.split("\t", 1)[0]))
    for f in ("culture-names.json", "also-cultures.json", "medieval-names.json", "az-names.json", "russia-cultures.json", "bible-extra.json",
              "scripture-names.json", "hebrew-names.json"):
        p = os.path.join(ROOT, "data", f)
        if os.path.exists(p):
            for r in json.load(open(p, encoding="utf-8")): out.add(fold(r[0]))
    return out

if __name__ == "__main__":
    stats = collections.Counter()
    en = {"Georgian": cached("en-wikt-Georgian.json", lambda: fetch_en("Georgian")),
          "Albanian": cached("en-wikt-Albanian.json", lambda: fetch_en("Albanian"))}
    ka = cached("ka-wikt.json", fetch_ka)
    sq = cached("sq-wikt-categories.json", fetch_sq)
    wd = cached("wikidata-given-names.json", fetch_wd)
    # names that only Georgian Wiktionary or Wikidata list: their own English Wiktionary page, when it has one
    # (Mkhedruli title for Georgian, with the bare form of a nominative in -ი; the Latin title for Albanian)
    def extra_titles():
        ts = set()
        for t in ka:
            ts.add(t)
            if t.endswith("ი") and t[-2:-1] not in ("", "ა", "ე", "ი", "ო", "უ"): ts.add(t[:-1])
        for it in wd.values():
            ts |= {n for n, _ in it["native"] if GEO.match(n)} | ({it["ka"]} if GEO.match(it["ka"]) else set())
            ts |= {n for n, l in it["native"] if l == "sq"} | {it["sq"], it["en"]}
        return sorted(t for t in ts if t and t not in en["Georgian"] and t not in en["Albanian"])
    extra = cached("en-wikt-extra.json", lambda: texts("en.wiktionary.org", extra_titles()))
    for lang in ("Georgian", "Albanian"):
        for t, tx in extra.items():
            sec = section(tx, lang)
            m = re.search(r"\{\{given name\|(?:ka|sq)\|([a-z]+)", sec or "")
            if m and m.group(1) in ("male", "female", "unisex"):
                en[lang][t] = {"g": {"male": "b", "female": "g", "unisex": "e"}[m.group(1)], "text": tx}
                stats[(lang, "en.wiktionary page outside the categories")] += 1
    existing = json.load(open(os.path.join(ROOT, "data", "culture-names.json"), encoding="utf-8"))
    have = collections.defaultdict(set)                       # lowercased name → cultures in culture-names.json
    for r in existing: have[r[0].lower()].add(r[2])

    # key (culture, display lower) → record
    rec = {}
    def add(culture, name, native, g, meaning, src, d=None):
        if not name or not g: stats[(culture, "no sex" if name else "no latin form")] += 1; return
        name = name[:1].upper() + name[1:]
        r = rec.setdefault((culture, name.lower()), {"n": name, "native": native, "gs": [], "m": "", "src": [], "from": "", "eq": ""})
        r["gs"].append(g)
        if native and not r["native"]: r["native"] = native
        if meaning and not r["m"]: r["m"] = meaning
        if src not in r["src"]: r["src"].append(src)
        if d:
            if d.get("from") and not r["from"]: r["from"] = d["from"]
            if d.get("eq") and not r["eq"]: r["eq"] = d["eq"]

    # Georgian native forms from every source, so one spelling decides the Latin name
    def geo_name(native): return georgian(native).capitalize() if GEO.match(native) else ""
    for t, v in en["Georgian"].items():
        if not GEO.match(t): stats[("Georgian", "en not Mkhedruli")] += 1; continue
        d, m = meaning_from(v["text"], "Georgian")
        add("Georgian", geo_name(t), t, v["g"], m, "en.wiktionary", d)
    en_geo = set(en["Georgian"])
    wd_geo = {n for it in wd.values() for n, _ in it["native"]} | {it["ka"] for it in wd.values()}
    for t, v in ka.items():
        if not GEO.match(t): continue
        # Georgian Wiktionary writes the nominative (თინათინი); English Wiktionary and Wikidata the bare name (თინათინ).
        # Use the bare form only when one of those sources has it.
        if t.endswith("ი") and len(t) > 3 and t[-2] not in "აეიოუ" and (t[:-1] in en_geo or t[:-1] in wd_geo): t = t[:-1]
        add("Georgian", geo_name(t), t, v["g"], "", "ka.wiktionary")
    for t, v in en["Albanian"].items():
        if not LAT.match(t): stats[("Albanian", "en not a single Latin word")] += 1; continue
        d, m = meaning_from(v["text"], "Albanian")
        add("Albanian", t, "", v["g"], m, "en.wiktionary", d)

    for q, it in wd.items():
        g = sex_of(CLS_SEX.get(c, "") for c in it["cls"])
        langs = set(it["lang"])
        geo_native = next((n for n, l in it["native"] if GEO.match(n) and l in ("ka", "")), "") or \
                     next((n for n, l in it["native"] if GEO.match(n)), "") or (it["ka"] if GEO.match(it["ka"]) else "")
        is_ka = KA in langs or any(l == "ka" for _, l in it["native"]) or (not langs and any(GEO.match(n) for n, _ in it["native"]))
        if is_ka and not (langs - {KA}) or KA in langs:
            if geo_native:
                if not g: g = sex_of(r_g for (c, k), r in rec.items() if c == "Georgian" and r["native"] == geo_native for r_g in r["gs"])
                add("Georgian", geo_name(geo_native), geo_native, g, "", "wikidata")
            else: stats[("Georgian", "wikidata without Mkhedruli")] += 1
        elif is_ka: stats[("Georgian", "wikidata other language (Mingrelian, Svan…)")] += 1
        is_sq = SQ in langs or any(l == "sq" for _, l in it["native"])
        if is_sq:
            n = next((n for n, l in it["native"] if l == "sq"), "") or it["sq"] or it["en"]
            if not LAT.match(n or ""): stats[("Albanian", "wikidata no single Latin label")] += 1; continue
            if not g:
                r = rec.get(("Albanian", n.lower()))
                g = sex_of(r["gs"]) if r else ""
            add("Albanian", n, "", g, "", "wikidata")

    # Pashto
    en["Pashto"] = cached("en-wikt-Pashto.json", lambda: fetch_en("Pashto"))
    ps_wd = cached("wikidata-pashto-given-names.json", fetch_ps_wd)
    ps_sq = cached("ps-wikt-categories.json", lambda: {c["category"]: c.get("pages", 0) for c in wiki("ps.wiktionary.org", action="query", list="allcategories", aclimit="500", acprop="size").get("query", {}).get("allcategories", [])})
    pashtun_native = {re.search(r"Written ([^\s.]+)", r[6]).group(1) for r in existing if r[2] == "Pashtun" and "Written " in r[6]}
    for t, v in en["Pashto"].items():
        sec = section(v["text"], "Pashto")
        ok, g, xlit = pashto_origin(sec)
        if not ok: stats[("Pashtun", "en.wiktionary borrowed (Arabic/Persian…) or no etymology")] += 1; continue
        if t in pashtun_native: stats[("Pashtun", "already (same Pashto spelling)")] += 1; continue
        d, m = meaning_from(v["text"], "Pashto")
        if not m:
            nm = re.search(r"(?ms)^===+\s*(?:Noun|Adjective)\s*===+\s*$.*?^#\s*([^:*\n][^\n]*)", sec)
            if nm and "given name" not in nm.group(1): m = clean(nm.group(1))
        add("Pashtun", xlit or latinize_tr(d.get("tr", "")), t, g or v["g"], m, "en.wiktionary", d)
    for q, it in ps_wd.items():
        native = [n for n, l in it["native"] if l == "ps" and PS_LETTERS.match(n)]
        if set(it["lang"]) != {"Q58680"} or not native: stats[("Pashtun", "wikidata: also tagged another language, or no Pashto label")] += 1; continue
        if native[0] in pashtun_native: stats[("Pashtun", "already (same Pashto spelling)")] += 1; continue
        add("Pashtun", it["en"] if LAT.match(it["en"] or "") else "", native[0], sex_of(CLS_SEX.get(c, "") for c in it["cls"]), "", "wikidata")

    # San Marino
    sm = cached("wikidata-san-marino-captains-regent.json", fetch_sm)
    seen = attested()
    sm_names = collections.defaultdict(lambda: {"people": [], "years": [], "sex": set()})
    for pq, pp in sm["people"].items():
        for gq in pp["gn"]:
            x = sm_names[gq]; x["people"].append(pp["label"]); x["years"] += pp["start"]
            x["sex"].add({"Q6581097": "b", "Q6581072": "g"}.get(pp["sex"], ""))
    sm_new = []
    for gq, x in sm_names.items():
        n = sm["names"].get(gq, {})
        label = n.get("it") or n.get("en") or n.get("mul") or n.get("nl") or ""   # the name as written (P1705) when it has no label
        if not LAT.match(label): stats[("Sammarinese", "given-name item without a one-word Latin label")] += 1; continue
        if fold(label) in seen: stats[("Sammarinese", "already in our data")] += 1; continue
        g = sex_of(CLS_SEX.get(c, "") for c in n.get("cls", [])) or sex_of(x["sex"])
        if not g: stats[("Sammarinese", "no sex")] += 1; continue
        ys = sorted(x["years"]); langs = [LANG_QID[l] for l in n.get("lang", []) if l in LANG_QID]
        k = len(set(x["people"]))
        story = (f"Borne by {k} Captain{'s' if k > 1 else ''} Regent of San Marino" + (f" ({ys[0]}" + (f"–{ys[-1]}" if ys[-1] != ys[0] else "") + ")" if ys else "")
                 + ": " + ", ".join(sorted(set(x["people"]))[:3]) + ".")
        sm_new.append([label, g, "Sammarinese", langs[0] if len(langs) == 1 else "", "", "", story, "", "real", []])
        seen.add(fold(label))

    # the same Georgian name in the nominative (დავითი, თამარი) and bare (დავით, თამარ): one name, the bare form, as written in Latin
    # (Davit, Tamar). Only when a source has the bare form: Giorgi and Irakli end in -i too.
    geo_bare = {r["native"]: k for (c, k), r in rec.items() if c == "Georgian"}
    geo_bare.update({re.search(r"Written (\S+?)\.", r[6]).group(1): r[0].lower() for r in existing if r[2] == "Georgian" and "Written " in r[6]})
    for (c, k), r in list(rec.items()):
        if c != "Georgian" or not r["native"].endswith("ი") or r["native"][-2:-1] in ("ა", "ე", "ი", "ო", "უ"): continue
        bare = geo_bare.get(r["native"][:-1])
        if not bare: continue
        del rec[(c, k)]; stats[("Georgian", "nominative form merged into the bare name")] += 1
        if ("Georgian", bare) in rec:
            b = rec[("Georgian", bare)]
            b["gs"] += r["gs"]; b["m"] = b["m"] or r["m"]; b["from"] = b["from"] or r["from"]; b["eq"] = b["eq"] or r["eq"]
    rows, already, nominative_dupes = [], collections.Counter(), []
    # Georgian rows already in culture-names.json under their Mkhedruli spelling (რუსუდანი there as Rusudan, ეთერი as Eteri)
    # (only when that row's Latin is a plain romanization of it: a few rows took a source word's transliteration
    # instead, Cpwk for ჭაბუკი, Farsi for ფარსადან, and get their proper row here)
    old_geo, bad_geo = set(), []
    for r in existing:
        m = r[2] == "Georgian" and re.search(r"Written (\S+?)\.", r[6])
        if not m: continue
        w = m.group(1); lat = georgian(w).lower()
        if r[0].lower() in (lat, lat[:-1] if w.endswith("ი") else lat): old_geo.add(w)
        else: bad_geo.append(f"{r[0]} ({w})")
    for (culture, k), r in sorted(rec.items(), key=lambda kv: kv[1]["n"]):
        if culture in have.get(k, ()): already[culture] += 1; continue
        if culture == "Georgian" and r["native"] in old_geo: already[culture] += 1; continue
        if culture == "Georgian" and r["native"] + "ი" in old_geo: nominative_dupes.append(f"{r['n']} (culture-names has {georgian(r['native'] + 'ი').capitalize()})")
        others = sorted(c for c in have.get(k, ()) if c != culture)
        art = "An" if culture[0] in "AEIOU" else "A"
        lang = {"Pashtun": "Pashto"}.get(culture, culture)
        story = f"{art} {culture} name" + (f" from {r['from']}" if r["from"] and r["from"].lower() != culture.lower() else "")
        story += (f", the {culture} form of {r['eq']}" if r["eq"] and r["eq"].lower() != k else "") + "."
        if r["native"]: story += f" Written {r['native']}."
        if others: story += f" Also {'an' if others[0][0] in 'AEIOU' else 'a'} {', '.join(others[:3])} name."
        rows.append([r["n"], sex_of(r["gs"]), culture, lang, "", r["m"][:80], story, "", "real", others])
    rows += sorted(sm_new)
    json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

    print(f"{len(rows)} new names → {OUT}")
    for c in ("Georgian", "Albanian", "Pashtun", "Sammarinese"):
        new = [r for r in rows if r[2] == c]
        print(f"  {c}: {len(new)} new ({sum(1 for r in new if r[5])} with meanings), {already[c]} already in culture-names.json")
    print("  skipped:", dict(stats))
    print(f"  bare Georgian names whose nominative is already a culture-names.json row ({len(nominative_dupes)}):", ", ".join(nominative_dupes))
    print(f"  culture-names.json Georgian rows whose Latin isn't their Mkhedruli ({len(bad_geo)}):", ", ".join(bad_geo))
    # meanings Wiktionary states for names already in culture-names.json without one (not written here: that file is build_cultures.py's)
    # meanings Wiktionary states for names already in culture-names.json without one → data/extra-meanings.json
    # ({lowercase name: {m, ety, src}}; culture-names.json itself is build_cultures.py's output)
    fill = {}
    for c in ("Georgian", "Albanian"):
        for t, v in en[c].items():
            n = geo_name(t) if c == "Georgian" else t
            row = next((r for r in existing if r[0] == n and r[2] == c), None)
            if row and not row[5]:
                _, m = meaning_from(v["text"], c)
                if not m: continue
                ety = re.search(r"(?ms)^===+\s*Etymology[^=]*===+\s*$(.*?)(?=^===)", section(v["text"], c))
                e = ety and re.split(r"(?<=\.)\s", ety.group(1).strip(), maxsplit=1)[0]
                fill[n.lower()] = {"m": m[:80], "ety": clean(re.sub(r"\{\{(?:m|l|der|bor|inh)\+?\|[^|{}]*\|(?:[^|{}]*\|)?([^|{}]+)[^{}]*\}\}", r"\1", e or "")), "src": "Wiktionary"}
    json.dump(fill, open(os.path.join(ROOT, "data", "extra-meanings.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)
    print(f"  data/extra-meanings.json: meanings for {len(fill)} existing rows that had none")
    print("  sq.wiktionary given-name categories:", {k: v for k, v in sq.items() if re.search(r"vet|femr|meshk|djal|vajz|përve", k)} or "none")
    print("  ps.wiktionary given-name categories:", {k: v for k, v in ps_sq.items() if re.search(r"نوم", k)})
    # Captains Regent by century of their (first) term
    by = collections.defaultdict(lambda: [set(), set()])
    for pp in sm["people"].values():
        if not pp["start"]: continue
        c = int(min(pp["start"])) // 100 + 1
        by[c][0].add(pp["label"]); by[c][1].update(pp["gn"])
    print("  Captains Regent by century (first term): regents / distinct given names:",
          {f"{c}{'st' if c == 21 else 'th'}": (len(v[0]), len(v[1])) for c, v in sorted(by.items())}, f"; {len(sm['people'])} regents, {len(sm_names)} distinct given names")
