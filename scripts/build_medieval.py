# Medieval names used in England, France and Scandinavia, c. 1050–1500 → data/medieval-names.json
#
#   Wiktionary (CC BY-SA 4.0): every entry in "Middle English / Old French / Middle French / Old English / Old Norse /
#     Old Swedish male/female given names", with its etymology ("from Old French Alison") and meaning when the entry
#     gives one, and for Norse names the usual modern form (Sigríðr → Sigrid).
#     (Wiktionary has no Anglo-Norman given-name categories.)
#   Domesday Book (1086), Hull Domesday Project data by Prof. J.J.N. Palmer, as listed on opendomesday.org
#     (CC BY-NC-SA): every landholder named in 1066 (before the Conquest) or 1086 (after it).
#   Wikidata (CC0): the given names of people born 1050–1500 who were subjects of the Kingdom of England,
#     the Kingdom of France or the Duchy of Normandy, with the birth year of the earliest one.
#
# Downloads are cached in raw/medieval/ (delete that folder to fetch again).
#
#   python3 scripts/build_medieval.py
import collections, html, json, os, re, sys, time, unicodedata, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "raw", "medieval"); OUT = os.path.join(ROOT, "data", "medieval-names.json")
sys.path.insert(0, HERE)
from fetch_wiktionary_names import api, members, pages, UA
from build_cultures import clean, section

# Wiktionary language → (culture, also)
WIKT = {"Middle English": ("Medieval English", []), "Old French": ("Old French", ["Medieval French"]),
        "Middle French": ("Old French", ["Middle French", "Medieval French"]), "Old English": ("Old English", ["Anglo-Saxon"]),
        "Old Norse": ("Old Norse", ["Nordic"]), "Old Swedish": ("Old Norse", ["Nordic", "Old Swedish"])}
LANGS = {"fro": "Old French", "xno": "Anglo-Norman", "nrf": "Norman", "enm": "Middle English", "ang": "Old English", "frm": "Middle French",
         "la": "Latin", "LL.": "Late Latin", "ML.": "Medieval Latin", "la-lat": "Late Latin", "la-med": "Medieval Latin", "frk": "Frankish",
         "gem-pro": "Proto-Germanic", "gmw-pro": "Proto-West Germanic", "gem": "Germanic", "grc": "Ancient Greek", "hbo": "Biblical Hebrew",
         "he": "Hebrew", "non": "Old Norse", "goh": "Old High German", "odt": "Old Dutch", "osx": "Old Saxon", "sga": "Old Irish",
         "cel": "Celtic", "cel-bry-pro": "Proto-Brythonic", "ar": "Arabic", "arc": "Aramaic", "en": "English", "fr": "French", "it": "Italian",
         "oc": "Occitan", "pro": "Old Occitan", "br": "Breton", "xbm": "Middle Breton", "wlm": "Middle Welsh", "owl": "Old Welsh"}
TITLES = set("""King Queen Count Countess Earl Bishop Archbishop Abbot Abbess Abbey Canon Canons Saint St Church Lady Lord Prior Priest
Sheriff Monks Nuns Brother Sister Wife Mother Father Son Daughter Widow Chaplain Deacon Archdeacon The Dean Master Reeve Burgesses""".split())
ENGLISH = re.compile(r"^(Ael|Aeth|Æ|Ead|Eal|Wulf|Leof|God[^f]|Brict|Brih|Sae|Sig|Thor|Thur|Ulf|Ket|Gunn|Stan|Wig|Ord|Eld|Cyn|Ecg|Tos|Thyr)")
NAME = re.compile(r"^[A-ZÀ-ÞĀ-ſǢǼ][^\W\d_]+(?:[-'’][^\W\d_]+)?$")

def fold(n):
    n = n.replace("Æ", "Ae").replace("æ", "ae").replace("Þ", "Th").replace("þ", "th").replace("Ð", "Th").replace("ð", "th")
    return "".join(c for c in unicodedata.normalize("NFKD", n) if not unicodedata.combining(c)).lower()

def cached(name, fetch):
    path = os.path.join(RAW, name)
    if not os.path.exists(path):
        data = fetch()
        with open(path, "w", encoding="utf-8") as f: (json.dump(data, f, ensure_ascii=False) if not isinstance(data, str) else f.write(data))
    with open(path, encoding="utf-8") as f: return json.load(f) if name.endswith(".json") else f.read()

def get(url, **headers):
    for attempt in range(6):
        try: return urllib.request.urlopen(urllib.request.Request(url, headers={**UA, **headers}), timeout=300).read().decode("utf-8")
        except Exception: time.sleep(5 * (attempt + 1))
    raise RuntimeError("could not fetch " + url)

# ---------- Wiktionary ----------
def fetch_wikt(lang):
    sex = {}
    for g, label in (("b", "male"), ("g", "female")):
        for t in members(f"{lang} {label} given names"): sex[t] = "e" if t in sex and sex[t] != g else g
    text = pages(sorted(sex))
    return {t: {"g": g, "text": text.get(t, "")} for t, g in sex.items()}

def tpl_args(t):
    pos, kw = [], {}
    for a in t.split("|")[1:]:
        if "=" in a: k, v = a.split("=", 1); kw[k.strip()] = v.strip()
        else: pos.append(a.strip())
    return pos, kw

def etymology(sec):
    """("from Old French Alison, from Latin X", "meaning") from an entry's Etymology section."""
    ety = re.search(r"(?ms)^===+\s*Etymology[^=]*===+\s*$(.*?)(?=^===|\Z)", sec)
    e = re.sub(r"\{\{etymon\|[^{}]*\}\}|<ref.*?</ref>|<ref[^>]*/>", "", ety.group(1) if ety else "", flags=re.S)
    chain, glosses = [], []
    for m in re.finditer(r"\{\{([^{}]*)\}\}", e):
        name = m.group(1).split("|")[0].strip()
        pos, kw = tpl_args(m.group(1))
        if name in ("der", "inh", "bor", "lbor", "der+", "inh+", "bor+", "lbor+", "learned borrowing") and len(pos) >= 3:
            lang, term = LANGS.get(pos[1]), pos[2].lstrip("*")
            if lang and term and term != "-" and len(chain) < 2: chain.append(f"{lang} {clean(term)}")
            g = kw.get("t") or kw.get("gloss") or (pos[4] if len(pos) > 4 else "")
            if g: glosses.append(g)
        elif name in ("m", "l", "cog", "noncog") and (kw.get("t") or kw.get("gloss") or len(pos) > 3):
            g = kw.get("t") or kw.get("gloss") or (pos[3] if len(pos) > 3 else "")
            if g and name != "cog": glosses.append(g)
        elif name in ("af", "affix", "compound", "com", "suffix", "prefix"):
            glosses += [kw[k] for k in sorted(kw) if re.fullmatch(r"t\d", k)]
    glosses = [clean(g) for g in glosses if clean(g) and not re.fullmatch(r"[A-Z]\w+(, [A-Z]\w+)*", clean(g)) and not re.search(r"\bname\b|saint", g, re.I)]
    if not glosses:     # the entry's own meaning=/lit= (not a noun sense: "Guy" the effigy is not what Guy means)
        m = re.search(r"\{\{given name\|[^{}]*\|meaning=([^|}]+)", sec) or re.search(r"\|lit=([^|}]+)", e)
        if m: glosses = [clean(m.group(1))]
    meaning = " + ".join(dict.fromkeys(glosses[:3]))
    return ", from ".join(chain), (meaning if len(meaning) < 70 else "")

def modern_form(sec, name):
    """The name's usual modern form, from the entry's Descendants: English first, then Norwegian, Danish, Swedish, Icelandic."""
    for code in ("en", "no", "nb", "da", "sv", "is"):
        m = re.search(r"\{\{desc\|" + code + r"\|([^|}]+)", sec)
        if m and clean(m.group(1)) not in (name, "-", ""): return clean(m.group(1))
    return ""

def given_name_section(text, langs):
    """The first section of `langs` on a page that defines a given name (not just an inflected or abbreviated form)."""
    for l in langs:
        sec = section(text, l)
        if sec and re.search(r"(?m)^#\s*\{\{given name\|", sec): return l, sec
    return None, ""

# ---------- Domesday ----------
def domesday_names(page):
    rows = re.findall(r'<tr>\s*<td><a href="/name/[^"]+"[^>]*/>(.*?)</a></td>\s*<td>(.*?)</td>\s*<td>(\d+)</td>\s*<td>(\d+)</td>', page, re.S)
    out = collections.defaultdict(lambda: {"b": 0, "g": 0, "pre": 0, "post": 0, "holders": 0})
    skipped = 0
    for label, kind, pre, post in rows:
        if kind in ("Male", "Female", "English canon", "Other English clergy or institution", "English bishop/archbishop", "Foreign bishop"):
            label = re.sub(r"<[^>]*>|\{[^}]*\}", " ", html.unescape(label)).replace("(", "").replace(")", "")
            words = [w for w in label.split() if w.strip(",") not in TITLES]
            first = words[0].strip(",") if words else ""
            if not NAME.match(first) or len(first) < 3 or "," in label.split()[0]: skipped += 1; continue
            d = out[first]
            d["g" if kind == "Female" else "b"] += 1
            d["pre"] += int(pre); d["post"] += int(post); d["holders"] += 1
        else: skipped += 1
    return dict(out), skipped

# ---------- Wikidata ----------
SPARQL = """SELECT ?name ?nameLabel ?c ?sex (COUNT(DISTINCT ?p) AS ?n) (MIN(YEAR(?b)) AS ?first) WHERE {
  VALUES ?c { wd:Q179876 wd:Q70972 wd:Q205855 }
  ?p wdt:P31 wd:Q5 ; wdt:P27 ?c ; wdt:P569 ?b ; wdt:P735 ?name .
  FILTER(YEAR(?b) >= 1050 && YEAR(?b) <= 1500)
  OPTIONAL { ?p wdt:P21 ?sex }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,fr". }
} GROUP BY ?name ?nameLabel ?c ?sex"""
COUNTRY = {"Q179876": "England", "Q70972": "France", "Q205855": "Normandy"}

def wikidata_names(res):
    out = collections.defaultdict(lambda: {"b": 0, "g": 0, "n": 0, "first": 9999, "where": collections.Counter()})
    for b in res["results"]["bindings"]:
        n = b["nameLabel"]["value"]
        if not NAME.match(n): continue
        d = out[n]; k = int(b["n"]["value"]); y = int(b["first"]["value"])
        sex = b.get("sex", {}).get("value", "").rsplit("/", 1)[-1]
        if sex == "Q6581072": d["g"] += k
        elif sex == "Q6581097": d["b"] += k
        d["n"] += k; d["first"] = min(d["first"], y); d["where"][COUNTRY[b["c"]["value"].rsplit("/", 1)[-1]]] += k
    return dict(out)

def century(y):
    c = (y - 1) // 100 + 1
    return f"{c}{'th' if 10 <= c % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(c % 10, 'th')} century"

def sex_of(b, g):
    if b and g and min(b, g) / (b + g) >= .2: return "e"
    return "g" if g > b else "b"

def an(word): return "An" if word[0] in "AEIOU" else "A"

if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    wikt = {l: cached(f"wikt-{l.replace(' ', '_')}.json", lambda l=l: fetch_wikt(l)) for l in WIKT}
    page = cached("domesday-names.html", lambda: get("https://opendomesday.org/name/"))
    dome, dome_skipped = domesday_names(page)
    wd = wikidata_names(cached("wikidata.json", lambda: json.loads(get(
        "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": SPARQL}), Accept="application/sparql-results+json"))))

    rows, skipped = {}, collections.Counter()      # fold(name) → row dict
    def add(name, gender, culture, also, meaning, origin, source):
        k = fold(name)
        if k in rows:
            r = rows[k]
            if culture != r["culture"] and culture not in r["also"]: r["also"].append(culture)
            for a in also:
                if a not in r["also"] and a != r["culture"]: r["also"].append(a)
            if r["gender"] != gender: r["gender"] = "e" if {r["gender"], gender} >= {"b", "g"} or "e" in (r["gender"], gender) else r["gender"]
            if fold(meaning) != fold(r["name"]): r["meaning"] = r["meaning"] or meaning; r["origin"] = r["origin"] or origin; r["sources"].add(source)
        else:
            rows[k] = {"name": name, "gender": gender, "culture": culture, "also": list(also), "meaning": meaning, "origin": origin, "sources": {source}}
        return rows[k]

    # 1. Wiktionary
    for lang, (culture, also) in WIKT.items():
        for title, e in sorted(wikt[lang].items()):
            if not NAME.match(title): skipped[f"Wiktionary {lang}: not a single-word name"] += 1; continue
            _, sec = given_name_section(e["text"], [lang])
            if not sec: skipped[f"Wiktionary {lang}: inflected/alternative-only or no given-name sense"] += 1; continue
            origin, meaning = etymology(sec)
            r = add(title, e["g"], culture, also, meaning, origin, "wikt")
            r.setdefault("langs", []).append(lang)
            if culture == "Old Norse": r["modern"] = r.get("modern") or modern_form(sec, title)

    # 2. Domesday Book
    # a name held mostly after the Conquest is a newcomer's (Drogo, Ivo, Hamo) unless it is plainly English or Norse
    oe_keys = {fold(t) for t in wikt["Old English"]}
    for name, d in sorted(dome.items()):
        before = d["pre"] * 3 >= d["post"] or fold(name) in oe_keys or ENGLISH.match(name)
        culture = "Old English" if before and fold(name) in oe_keys else ("Medieval English" if before else "Anglo-Norman")
        r = add(name, sex_of(d["b"], d["g"]), culture, ["Medieval English"] if culture == "Anglo-Norman" else [], "", "", "domesday")
        r["domesday"] = dict(d, before=bool(before))

    # 3. Wikidata: people born 1050–1500
    for name, d in sorted(wd.items()):
        where = d["where"].most_common(1)[0][0]
        culture = {"France": "Old French", "Normandy": "Anglo-Norman"}.get(where) or ("Anglo-Norman" if d["first"] <= 1300 else "Medieval English")
        also = [c for c in ("Medieval English" if "England" in d["where"] else "", "Old French" if "France" in d["where"] else "") if c and c != culture]
        r = add(name, sex_of(d["b"], d["g"]) if d["b"] + d["g"] else "e", culture, also, "", "", "wikidata")
        r["wikidata"] = d

    # 4. meanings for Domesday/Wikidata names from their own Wiktionary page (any medieval or modern section with a given-name sense)
    need = sorted(r["name"] for r in rows.values() if not r["meaning"] or not r["origin"])
    extra = cached("wikt-extra.json", lambda: pages(need))
    for r in rows.values():
        text = extra.get(r["name"], "")
        if not text: continue
        lang, sec = given_name_section(text, ["Middle English", "Old French", "Anglo-Norman", "Old English", "Middle French", "English", "French", "Latin"])
        if sec:
            origin, meaning = etymology(sec)
            if fold(meaning) != fold(r["name"]): r["meaning"] = r["meaning"] or meaning
            if not r["origin"] and origin and lang in ("Middle English", "Old French", "Anglo-Norman", "Old English", "Middle French"): r["origin"] = origin

    # 5. rows
    LANG_OF = {"Old Norse": "Old Norse", "Anglo-Norman": "Anglo-Norman", "Medieval English": "Middle English", "Old French": "Old French", "Old English": "Old English"}
    out = []
    for r in sorted(rows.values(), key=lambda r: fold(r["name"])):
        lang = (r.get("langs") or [LANG_OF[r["culture"]]])[0]
        phrase = {"Anglo-Norman": "An Anglo-Norman name", "Medieval English": "A Middle English name" if "wikt" in r["sources"] else "A medieval English name",
                  "Old English": "An Old English name", "Old French": f"{an(lang)} {lang} name", "Old Norse": f"{an(lang)} {lang} name"}[r["culture"]]
        story = phrase + (f", from {r['origin']}" if r["origin"] else "") + "."
        if r.get("modern"): story += f" Modern form: {r['modern']}."
        d, w = r.get("domesday"), r.get("wikidata")
        if d and d["before"]: story += f" Recorded in Domesday Book (1086) for {d['holders']:,} landholder{'s' if d['holders'] > 1 else ''} of 1066, before the Norman Conquest."
        elif d: story += f" Recorded in Domesday Book (1086) for {d['holders']:,} landholder{'s' if d['holders'] > 1 else ''} after the Norman Conquest."
        elif w:
            place = "England" if w["where"]["England"] >= max(w["where"]["France"], w["where"]["Normandy"]) else ("Normandy" if w["where"]["Normandy"] > w["where"]["France"] else "France")
            story += f" Recorded in {place} from the {century(w['first'])}."
        elif r["culture"] == "Old English": story = story[:-1] + ", used in England before the Norman Conquest."
        culture = r["culture"]
        also = [a for a in r["also"] if a != culture]
        out.append([r["name"], r["gender"], culture, LANG_OF[culture] if culture not in ("Old French", "Old Norse") else lang, "", r["meaning"], story, "", "real", also])

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(out):,} names → {os.path.relpath(OUT, ROOT)}")
    for c, n in collections.Counter(r[2] for r in out).most_common(): print(f"  {c}: {n:,}")
    print("  sources:", dict(collections.Counter(s for r in rows.values() for s in r["sources"])))
    print(f"  skipped: {dome_skipped:,} Domesday entries that are institutions, groups or unnamed; " + "; ".join(f"{n} {k}" for k, n in skipped.items()))
