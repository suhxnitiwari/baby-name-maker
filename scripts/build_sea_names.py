# Southeast Asian given names → data/sea-names.json, plus data/sea-fixes.json (corrections for data/culture-names.json)
#
# The rule: a name is shown the way families write it in English, never as a letter-by-letter transliteration.
# Every spelling comes from a source:
#   - English Wiktionary given-name entries (CC BY-SA): the entry's own Latin rendering (xlit=, "; Thaworn",
#     "romanised variously as ..."), or, for Thai entries with none, the Royal Institute (RTGS) romanization
#     the entry prints.
#   - Wikidata (CC0): the English labels of notable Thai, Cambodian, Lao and Burmese people, paired with their
#     native-script labels. A person's English label is the spelling they (or the press) use, so
#     "Somsak Thepsutin" / "สมศักดิ์ เทพสุทิน" attests that สมศักดิ์ is written Somsak.
#   - Wikidata given-name items with a native label (P1705) and an English label.
# Meanings only from a Wiktionary gloss in the same etymology as the given-name sense; blank otherwise.
# Sex only from the source: the Wiktionary template, the Wikidata item type, or the recorded sex of the bearers.
#
#   python3 scripts/build_sea_names.py           (downloads are cached under raw/sea/)
import collections, hashlib, html, json, os, re, time, unicodedata, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
CACHE = os.path.join(ROOT, "raw", "sea")
OUT = os.path.join(ROOT, "data", "sea-names.json")
FIXES = os.path.join(ROOT, "data", "sea-fixes.json")
EVIDENCE = os.path.join(CACHE, "evidence.json")
UA = "Lullabyte-namebuilder/1.0 (suhanitiwari@utexas.edu)"

# ─────────────────────────────── fetching (cached) ───────────────────────────────
def _cached(kind, key, fetch):
    d = os.path.join(CACHE, kind); os.makedirs(d, exist_ok=True)
    f = os.path.join(d, hashlib.md5(key.encode()).hexdigest() + ".json")
    if os.path.exists(f): return json.load(open(f, encoding="utf-8"))
    for attempt in range(4):
        try:
            data = fetch(); break
        except Exception as e:
            if attempt == 3: raise
            time.sleep(5 * (attempt + 1))
    json.dump(data, open(f, "w", encoding="utf-8"), ensure_ascii=False)
    time.sleep(0.4)
    return data

def wikt(params):
    q = urllib.parse.urlencode({**params, "format": "json", "formatversion": "2"})
    def go():
        req = urllib.request.Request("https://en.wiktionary.org/w/api.php?" + q, headers={"User-Agent": UA})
        return json.load(urllib.request.urlopen(req, timeout=90))
    return _cached("wikt", q, go)

def sparql(q):
    def go():
        req = urllib.request.Request("https://query.wikidata.org/sparql", data=urllib.parse.urlencode({"query": q}).encode(),
                                     headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
        rows = json.load(urllib.request.urlopen(req, timeout=300))["results"]["bindings"]
        return [{k: v["value"] for k, v in r.items()} for r in rows]
    return _cached("wd", q, go)

def members(cat, seen=None):
    seen = seen if seen is not None else set(); out = []; cont = {}
    while True:
        d = wikt({"action": "query", "list": "categorymembers", "cmtitle": cat, "cmlimit": "500", **cont})
        for m in d["query"]["categorymembers"]:
            if m["ns"] == 14:
                if m["title"] not in seen: seen.add(m["title"]); out += members(m["title"], seen)
            elif m["ns"] == 0: out.append(m["title"])
        if "continue" in d: cont = {"cmcontinue": d["continue"]["cmcontinue"]}
        else: return sorted(set(out))

def wikitext(titles):
    out = {}
    for i in range(0, len(titles), 50):
        d = wikt({"action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main", "titles": "|".join(titles[i:i + 50])})
        for p in d["query"]["pages"]:
            if "revisions" in p: out[p["title"]] = p["revisions"][0]["slots"]["main"]["content"]
    return out

def rendered(title):
    t = wikt({"action": "parse", "page": title, "prop": "text"})["parse"]["text"]
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t))).replace(" ", "")

def section(s, lang):
    m = re.search(rf"^=={re.escape(lang)}==\s*$(.*?)(?=^==[^=]|\Z)", s, re.M | re.S)
    return m.group(1) if m else ""

# ─────────────────────────────── template parsing ───────────────────────────────
def templates(s):
    """Top-level {{...}} templates in s as (name, positional, named)."""
    out, i = [], 0
    while True:
        i = s.find("{{", i)
        if i < 0: return out
        depth, j = 0, i
        while j < len(s):
            if s.startswith("{{", j): depth += 1; j += 2
            elif s.startswith("}}", j):
                depth -= 1; j += 2
                if depth == 0: break
            else: j += 1
        body = s[i + 2:j - 2]; i = j
        parts, buf, d2 = [], "", 0
        for k, ch in enumerate(body):
            if body.startswith("{{", k) or body.startswith("[[", k): d2 += 1
            if body.startswith("}}", k) or body.startswith("]]", k): d2 -= 1
            if ch == "|" and d2 <= 0: parts.append(buf); buf = ""
            else: buf += ch
        parts.append(buf)
        pos, named = [], {}
        for p in parts[1:]:
            m = re.match(r"\s*([a-z0-9_-]+)\s*=(.*)$", p, re.S)
            if m and not m.group(1).isdigit(): named[m.group(1)] = m.group(2).strip()
            else: pos.append(p.strip())
        out.append((parts[0].strip(), pos, named))

def plain(s):
    s = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", s)
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    s = s.replace("''", "")
    return re.sub(r"\s+", " ", s).strip(" ;,.")

GLOSS_TPL = {"bor", "bor+", "der", "der+", "inh", "inh+", "m", "l", "com", "af", "affix", "suf", "cog"}
def ety_glosses(text):
    """Glosses given in etymology templates: t=/gloss=/4th positional, com t1/t2."""
    out = []
    for name, pos, named in templates(text):
        if name not in GLOSS_TPL or name == "cog": continue
        if name in ("com", "af", "affix"):
            ts = [plain(named.get(f"t{k}", "")) for k in range(1, 4)]
            ts = [t for t in ts if t]
            if len(ts) >= 2: out.append(" + ".join(ts))
            continue
        g = named.get("t") or named.get("gloss") or (pos[3] if name in ("m", "l") and len(pos) > 3 else pos[4] if len(pos) > 4 else "")
        if name in ("m", "l") and not g and len(pos) > 3: g = pos[3]
        g = plain(g)
        if g and g.lower() not in ("idem", "-"): out.append(g)
    return out

SEX = {"female": "g", "male": "b", "unisex": "e"}

def wikt_entries(lang, code, header=None):
    """Every given-name sense in Category:<lang> given names, with its etymology block."""
    header = header or lang
    titles = members(f"Category:{lang} given names")
    wt = wikitext(titles)
    out = []
    for t in titles:
        sec = section(wt.get(t, ""), header)
        if not sec: continue
        blocks = re.split(r"^===\s*Etymology[^=]*===\s*$", sec, flags=re.M)
        if len(blocks) > 1 and not blocks[0].strip().startswith("===Etymology"):
            pre, blocks = blocks[0], blocks[1:]
        else: pre = ""
        for b in blocks:
            text = pre + b if len(blocks) == 1 else b
            for line in text.split("\n"):
                if not line.startswith("#") or line.startswith("#:") or line.startswith("#*"): continue
                gn = [x for x in templates(line) if x[0] in ("given name", "name translit")]
                if not gn: continue
                name, pos, named = gn[0]
                if name == "name translit":
                    typ = named.get("type", "")
                    sex = "g" if "female" in typ else "b" if "male" in typ else "e"
                    out.append({"title": t, "lang": lang, "sex": sex, "native": pos[2] if len(pos) > 2 else "", "renders": True, "block": text})
                    continue
                sexw = pos[1] if len(pos) > 1 else ""
                rest = line.split("}}", 1)[1] if "}}" in line else ""
                xlit = named.get("xlit", "")
                tail = plain(re.sub(r"\{\{n-g\|([^}]*)\}\}", r"\1", rest))
                variously = re.search(r"romanised variously as ([A-Z][\w, ]+?)(?:, etc|$)", rest)
                unlinked = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", rest)
                trail = re.match(r"\s*[;,]\s*([A-Z][a-z]+(?: [A-Z][a-z]+)?)\s*\.?\s*$", unlinked)
                out.append({"title": t, "lang": lang, "sex": SEX.get(sexw, "e"), "sex_given": sexw in SEX,
                            "xlit": xlit or (trail.group(1) if trail else ""),
                            "variously": [v.strip() for v in variously.group(1).split(",")] if variously else [],
                            "from": named.get("from", ""), "dimof": [d.strip() for d in named.get("dimof", named.get("dim", "")).split(",") if d.strip()],
                            "eq": named.get("eq", ""), "block": text, "line": line})
    return out

def sense_glosses(block):
    """Definitions of the non-name parts of speech in this etymology block."""
    out, pos = [], None
    for line in block.split("\n"):
        h = re.match(r"^=+\s*([^=]+?)\s*=+\s*$", line)
        if h: pos = h.group(1); continue
        if pos in ("Noun", "Adjective", "Verb") and re.match(r"^# (?![:*])", line) and "given name" not in line:
            g = re.sub(r"\{\{(lb|gloss|q|qualifier|i)\|[^{}]*\}\}", "", line[2:])
            g = re.sub(r"\{\{alt form\|[^{}]*\}\}:?", "", g)
            g = plain(g)
            if g: out.append(g)
    return out

# ─────────────────────────────── spelling and ease ───────────────────────────────
def strip_marks(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def vowel_groups(n):
    return len(re.findall(r"[aeiouy]+", n.lower()))

SEVERE = re.compile(r"^ng|x|q|chh|nh|aeu|oeu|eu[^r]|ue|ao|ia[iou]|uai|ieng|ouy|^ph|^bh|hm|hn|dh")
MILD = re.compile(r"kh|ph|th|ng[^aeiouy]|ng$|ch|tt|pp|kk")
def ease_of(name):
    n = name.lower()
    if len(n) > 10 or vowel_groups(n) > 3 or SEVERE.search(n): return 3
    if MILD.search(n) or len(n) > 8: return 2
    return 1

def rate(name, alts):
    e = ease_of(name)
    if e == 1: return 1
    if any(ease_of(a) == 1 for a in alts): return 2
    return e

# ─────────────────────────────── Wikidata people ───────────────────────────────
F, M = "http://www.wikidata.org/entity/Q6581072", "http://www.wikidata.org/entity/Q6581097"
SCRIPT = {"th": "฀-๿", "km": "ក-៿", "lo": "຀-໿", "my": "က-႟"}
COUNTRY = {"th": "Q869", "km": "Q424", "lo": "Q819", "my": "Q836"}

def people(lang):
    cc = COUNTRY[lang]; rows = {}
    for cond in (f"?p wdt:P27 wd:{cc}", f"?p wdt:P19/wdt:P17 wd:{cc}"):
        q = f'''SELECT ?p ?gn ?gnen ?sex ?en ?nat WHERE {{ {cond} . ?p wdt:P31 wd:Q5 ; rdfs:label ?nat FILTER(LANG(?nat)="{lang}")
 OPTIONAL {{ ?p wdt:P735 ?gn . OPTIONAL {{ ?gn rdfs:label ?gnen FILTER(LANG(?gnen)="en") }} }}
 OPTIONAL {{ ?p wdt:P21 ?sex }}
 OPTIONAL {{ ?p rdfs:label ?en FILTER(LANG(?en)="en") }} }}'''
        for r in sparql(q):
            if "en" not in r: continue
            p = rows.setdefault(r["p"], {"en": r["en"], "nat": r["nat"], "sex": set(), "gn": set()})
            if "sex" in r: p["sex"].add(r["sex"])
            if "gnen" in r: p["gn"].add(r["gnen"])
    return rows

def given_items(lang):
    q = f'''SELECT ?item ?type ?native ?en WHERE {{ VALUES ?type {{wd:Q202444 wd:Q12308941 wd:Q11879590 wd:Q3409032}}
 ?item wdt:P31 ?type ; wdt:P1705 ?native . FILTER(REGEX(STR(?native), "[{SCRIPT[lang]}]"))
 OPTIONAL {{ ?item rdfs:label ?en FILTER(LANG(?en)="en") }} }}'''
    out = {}
    for r in sparql(q):
        if not re.fullmatch(f"[{SCRIPT[lang]}]+", r["native"]) or "en" not in r: continue
        t = r["type"].rsplit("/", 1)[1]
        d = out.setdefault(r["item"], {"native": r["native"], "en": r["en"], "sex": set()})
        d["sex"].add({"Q12308941": "b", "Q11879590": "g", "Q3409032": "e"}.get(t, ""))
    return list(out.values())

LATIN = re.compile(r"[A-Z][a-z]+")
def name_pairs(lang, rows):
    """(native given name, Latin given name, sex) from people whose English and native labels line up word for word."""
    nat_ok = re.compile(f"[{SCRIPT[lang]}]+")
    clean = lambda s: re.sub(r"\s*\(.*?\)\s*", " ", s).replace(",", " ").split()
    two = []
    for p in rows.values():
        en, nat = clean(p["en"]), clean(p["nat"])
        nat = [next((w[len(t):] for t in TITLES if w.startswith(t) and len(w) > len(t)), w) for w in nat]
        if any(w.startswith(BAD_PREFIX) for w in nat): continue
        if len(en) != 2 or len(nat) != 2: continue
        if not all(LATIN.fullmatch(w) for w in en) or not all(nat_ok.fullmatch(w) for w in nat): continue
        sex = "g" if p["sex"] == {F} else "b" if p["sex"] == {M} else ""
        two.append((en, nat, sex, p["gn"]))
    if lang != "km":                                                     # Thai and Lao: given name first
        return [(n[0], e[0], s) for e, n, s, _ in two if initial_ok(lang, n[0], e[0]) and initial_ok(lang, n[1], e[1])]
    first = collections.Counter(e[0] for e, *_ in two)                   # Khmer: family name first, unless the person flips it
    out = []
    for e, n, s, gn in two:
        flip = (e[0] in gn and e[1] not in gn) or (first[e[1]] >= 3 and first[e[0]] <= 1 and e[1] not in gn)
        if not (initial_ok(lang, n[0], e[0]) and initial_ok(lang, n[1], e[1])): continue
        out.append((n[0], e[0], s) if flip else (n[1], e[1], s))
    # a word that is mostly a family name (Norodom, Hun) is not offered as a given name
    fam = collections.Counter(e[0] for e, n, s, gn in two); giv = collections.Counter(e[1] for e, n, s, gn in two)
    return [x for x in out if not (fam[x[1]] >= 3 and giv[x[1]] <= 1)]


# ─────────────────────────────── does a Latin spelling fit the native word? ───────────────────────────────
# Labels are paired word by word, so a person whose two labels are ordered differently would pair the wrong words
# (Galabru with ឈីវកេក). A spelling is kept only if its first sound fits the native word's first consonant.
def _m(spec):
    out = {}
    for part in spec.split():
        chars, lat = part.split("=")
        for ch in chars: out[ch] = tuple(lat.split(","))
    return out
VOWEL = ("a", "e", "i", "o", "u", "y", "h", "w", "v")
INITIAL = {
    "th": _m("ก=k,g ขฃคฅฆ=k,kh,c ง=ng,n จ=j,ch,c,j ฉชฌ=ch,c,j ซ=s,z ญ=y,n ฎด=d ฏต=t,d ฐฑฒถทธ=th,t,d ณน=n ↯บ=b,p,v ป=p,b ผพภ=ph,p,bh,b ฝฟ=f,ph "
             "ม=m ย=y,j ร=r,l ล=l,r ฬ=l ฤ=r ว=w,v ศษส=s,c,sh ห=h ฮ=h อ=a,e,i,o,u,y,au".replace("↯", "")),
    "km": _m("ក=k,g,c ខ=kh,k គ=k,g,c ឃ=kh,k ង=ng,n ច=ch,c,j ឆ=chh,ch,c ជ=ch,c,j ឈ=chh,ch,c,j ញ=nh,ny,gn,n ដ=d ឋ=th,t ឌ=d ឍ=th,t ណ=n "
             "ត=t,d ថ=th,t ទ=t,d,th ធ=th,t ន=n ប=b,p ផ=ph,p ព=p,b,ph ភ=ph,p ម=m យ=y,j ឡ=l រ=r,l ល=l វ=v,w ស=s,c ហ=h អ=a,e,i,o,u,y,h,k "
             "ឥឦ=e,i,y ឧឩឪ=o,u ឫឬ=r ឭឮ=l ឯឰ=a,e ឱឲឳ=a,o,au"),
    "lo": _m("ກ=k,g,c ຂຄ=kh,k ງ=ng,n ຈ=ch,j,c ສຊ=s,x,c ຍ=ny,y,gn,n ດ=d ຕ=t,d ຖທ=th,t ນໜ=n ບ=b,p ປ=p,b ຜພ=ph,p ຝຟ=f,ph ມໝ=m ຢ=y "
             "ຣລ=l,r ວ=v,w ຫ=h ອ=a,e,i,o,u,y ຮ=h"),
}
LEAD = {"th": "เแโใไ", "lo": "ເແໂໃໄ", "km": ""}
SILENT_H = {"th": ("ห", "งญนมยรลว"), "lo": ("ຫ", "ງຍນມຍຣລວ"), "km": ("", "")}
TITLES = ("หม่อมราชวงศ์", "หม่อมหลวง", "หม่อมเจ้า", "ม.ร.ว.", "ม.ล.", "ເຈົ້າ")
BAD_PREFIX = ("พระ", "สมเด็จ", "ພນະ", "ພະນະ", "ທ່ານ", "ព្រះ", "សម្តេច", "ឯកឧត្តម", "លោក")

def initial_ok(lang, nat, lat):
    nat = nat.lstrip(LEAD[lang])
    if not nat: return False
    h, sonor = SILENT_H[lang]
    if h and nat[0] == h and len(nat) > 1 and nat[1] in sonor: nat = nat[1:]
    opts = INITIAL[lang].get(nat[0])
    if opts is None: return False
    l = lat.lower()
    return any(l.startswith(o) for o in opts) or (opts[0] in "aeiouy" and l[0] in "aeiouy")

def _norm(s):
    s = s.lower()
    for a, b in (("ph", "p"), ("th", "t"), ("kh", "k"), ("bh", "b"), ("dh", "d"), ("ch", "c"), ("j", "c"), ("w", "v"), ("ee", "i"),
                 ("oo", "u"), ("ou", "u"), ("r", ""), ("h", ""), ("y", "i"), ("g", "k"), ("d", "t"), ("b", "p")):
        s = s.replace(a, b)
    return re.sub(r"(.)\1", r"\1", s)

def similar(a, b):
    """Two spellings of the same name (Thanapat/Tanapat, Worapol/Worrapon), not two different names."""
    a, b = _norm(a), _norm(b)
    if a[:1] != b[:1]: return False
    import difflib
    return difflib.SequenceMatcher(None, a, b).ratio() >= 0.7

# ─────────────────────────────── one culture ───────────────────────────────
CULTURE = {"th": ("Thai", "Thai"), "km": ("Khmer", "Khmer"), "lo": ("Lao", "Lao")}
ENGLISH, FOREIGN = set(), set()
SEA = {"Thai", "Khmer", "Lao", "Burmese", "Filipino", "Vietnamese", "Malay", "Indonesian", "Javanese"}
# names shared through Sanskrit, Pali, Persian and Arabic (Dara, Tara, Mali) are not foreign to Southeast Asia
SHARED = SEA | {"Hindi", "Bengali", "Gujarati", "Marathi", "Tamil", "Telugu", "Malayali", "Odia", "Punjabi", "Urdu", "Persian", "Arabic",
                "Sanskrit", "Pali", "South Asian", "Indic"}
def load_english():
    """Names from European, Central Asian and East Asian lists on the site: a Cambodian person named Andres or Ogawa
    does not make Andres a Khmer name."""
    D = lambda f: json.load(open(os.path.join(ROOT, "data", f), encoding="utf-8"))
    for r in D("english-names.json"): ENGLISH.add(r[0].lower())
    FOREIGN.update(ENGLISH)
    for f in ("spanish-names.json", "portuguese-names.json", "german-names.json", "greek-names.json", "finnish-names.json", "culture-names.json"):
        for r in D(f):
            if r[2] not in SHARED: FOREIGN.add(r[0].lower())
    for a, _, b, c, *_ in D("relations.json"):
        if c not in SHARED: FOREIGN.update((a.lower(), b.lower()))
    ea = D("east-asian-names.json")
    for r in ea.get("ja", []): FOREIGN.add(str(r[0]).lower())

# reviewed by hand: a person's name that is not a name of the culture (a Japanese surname, a French word, an English name)
NOT_NATIVE = {"Thai": {"Ann", "Anna"}, "Khmer": {"Ogawa", "Soubert", "Deux", "Sunnix"}, "Lao": set()}

# meanings checked by hand against the entry: the gloss printed is not what the name means
MEANING_BLANK = {
    "សុភា": "the only glosses are legal senses of the word (court, conferee), not the name",
    "ສັກດາ": "entry's etymology describes Siddhartha, a different word",
    "ឈួន": "etymology gloss is 'fever'; not a name meaning",
    "ភារៈ": "word sense is 'load, burden'; entry does not say the name means this",
    "រី": "word is a preposition",
    "ឡាយ": "word senses are 'marbled pattern; signature'",
    "សួន": "",
    "ខាន់": "word senses disagree (cloth; rug / bracelet, collar, ring)",
}

def meaning_for(e):
    """The gloss of the word this given-name sense is, from its own etymology block:
    the word's own definition when it has one or two, else a gloss the etymology gives for its Pali/Sanskrit/Old Khmer source."""
    if not e or e["title"] in MEANING_BLANK or e.get("eq"): return ""
    senses = [re.sub(r"^\((to be)\)\s*|^to be ", "", g) for g in sense_glosses(e["block"])]
    if 1 <= len(senses) <= 2: m = senses[0]
    else:
        ety = e["block"].split("Pronunciation")[0]
        m = ""
        for name, pos, named in templates(ety):
            if name in ("bor", "bor+", "der", "der+", "inh", "inh+") and len(pos) > 1 and pos[1] in ("pi", "sa", "okz", "xhm", "km", "th"):
                g = plain(named.get("t") or named.get("gloss") or (pos[4] if len(pos) > 4 else ""))
                if g and g.lower() != "idem": m = g; break
            if name in ("com", "af", "affix"):
                ts = [re.sub(r";\s*etc\.?$", "", plain(named.get(f"t{k}", ""))) for k in range(1, 4)]
                ts = [t for t in ts if t and t.lower() != "idem"]
                if ts: m = " + ".join(ts); break
    m = re.sub(r"\s*\([^)]*\)", "", m)
    m = re.sub(r"\s*;?\s*etc\.?$", "", m).strip(" ;,.")
    parts = [x.strip() for x in re.split(r"[;,]", m) if x.strip()]
    if len(parts) > 3: m = ", ".join(parts[:3])
    return m if len(m) <= 50 else ""

RTGS = re.compile(r"Royal Institute ([a-z\-]+)")
def rtgs(title):
    """The first Royal Institute romanization the entry prints (kan-la-ya-ni → Kanlayani)."""
    m = RTGS.search(rendered(title))
    return m.group(1).replace("-", "").capitalize() if m else ""

def build_culture(lang, evidence):
    culture, language = CULTURE[lang]
    header = {"th": "Thai", "km": "Khmer", "lo": "Lao"}[lang]
    native = collections.defaultdict(lambda: {"latin": collections.Counter(), "sex": collections.Counter(), "src": set(), "wikt": None})
    # 1) Wiktionary
    for e in wikt_entries(header, lang):
        if e.get("renders"): continue
        if e.get("eq") or e.get("from", "").split(" <")[0] in ("English", "Russian", "Arabic", "French"): continue   # แมรี is Mary, not a Thai name
        d = native[e["title"]]
        d["wikt"] = d["wikt"] or e
        if e.get("sex_given"): d["sex"][e["sex"]] += 5
        for sp in ([e["xlit"]] if e["xlit"] else []) + e["variously"]:
            d["latin"][sp] += 2; d["src"].add("Wiktionary")
    for t in members(f"Category:English renderings of {header} given names") if lang == "th" else []:
        pass                                                             # covered by people/items below when they carry Thai script
    # 2) Wikidata given-name items
    for it in given_items(lang):
        d = native[it["native"]]
        sp = strip_marks(it["en"])
        if LATIN.fullmatch(sp) and initial_ok(lang, it["native"], sp): d["latin"][sp] += 1; d["src"].add("Wikidata")
        for s in it["sex"]:
            if s: d["sex"][s] += 1
    # 3) Wikidata people
    for nat, lat, sex in name_pairs(lang, people(lang)):
        d = native[nat]; d["latin"][lat] += 1; d["src"].add("people")
        d.setdefault("bearers", collections.Counter())[lat] += 1
        if sex: d["sex"][sex] += 1
    # 4) Thai entries with no Latin spelling anywhere: the Royal Institute romanization the entry prints
    for nat, d in native.items():
        if not d["latin"] and d["wikt"] and lang == "th":
            r = rtgs(nat)
            if r: d["latin"][r] += 1; d["src"].add("RTGS")
    rows = {}
    for nat, d in native.items():
        if not d["latin"]: continue
        bearers = sum(d.get("bearers", {}).values())
        # a Western name carried by a Thai/Khmer/Lao person (Peter, Alexandra) is not this culture's name
        # the most used spelling; on a tie, the one other spellings agree with (Kamonwan over a mislabelled Gamolchanok)
        main = max(d["latin"], key=lambda sp: (d["latin"][sp] + 0.5 * sum(c for o, c in d["latin"].items() if o != sp and similar(sp, o)),
                                                 sp in (d["wikt"] or {}).get("xlit", "")))
        if main.lower() in FOREIGN and not d["wikt"] and bearers < 3: continue
        if len(main) < 2: continue
        f, m, e = d["sex"]["g"], d["sex"]["b"], d["sex"]["e"]
        if f + m + e == 0:
            if not d["wikt"]: continue
            e = 1                                                        # Wiktionary lists it as a given name without saying for whom
        sex = "g" if f >= 4 * max(m, 0.25) and f > e else "b" if m >= 4 * max(f, 0.25) and m > e else "e"
        if e > f + m: sex = "e"
        key = main.lower()
        r = rows.setdefault(key, {"name": main, "natives": collections.Counter(), "alts": collections.Counter(), "sex": collections.Counter(),
                                  "wikt": None, "bearers": 0, "src": set()})
        r["natives"][nat] += sum(d["latin"].values())
        for sp, c in d["latin"].items():
            if sp.lower() != key: r["alts"][sp] += c
        r["sex"][sex] += sum(d["latin"].values()); r["bearers"] += bearers
        r["wikt"] = r["wikt"] or d["wikt"]; r["src"] |= d["src"]
    out = []
    for key, r in rows.items():
        if r["name"] in NOT_NATIVE[culture]: continue
        weight = sum(r["natives"].values())
        if lang == "th" and r["bearers"] < 2 and not r["wikt"] and "Wikidata" not in r["src"]: continue
        sex = r["sex"].most_common(1)[0][0]
        nats = [n for n, _ in r["natives"].most_common(2)]
        alts = [a for a, _ in r["alts"].most_common() if similar(r["name"], a) and a.lower() not in rows][:3]
        cands = [native[n]["wikt"] for n, _ in r["natives"].most_common() if native[n]["wikt"]]
        e = next((c for c in cands if meaning_for(c)), cands[0] if cands else None)
        meaning = meaning_for(e)
        origin = ""
        if e and e.get("from") in ("Pali", "Sanskrit", "Arabic"): origin = f" from {e['from']}"
        s = f"A {culture} name" + (f" meaning '{meaning}' (Wiktionary)" if meaning else "") + origin + "."
        s += " Written " + " or ".join(nats) + "."
        if alts: s += " Also written " + ", ".join(alts) + "."
        ease = rate(r["name"], alts)
        out.append([r["name"], sex, culture, language, "", meaning, s, "", "real", [], ease])
        evidence[f"{culture}:{r['name']}"] = {"native": dict(r["natives"]), "spellings": {r["name"]: weight - sum(r["alts"].values()), **dict(r["alts"])},
                                               "bearers": r["bearers"], "sources": sorted(r["src"]), "wiktionary": e["title"] if e else ""}
    # everything a dictionary or name item attests, then the names most notable people carry
    out.sort(key=lambda x: (not (evidence[f"{culture}:{x[0]}"]["wiktionary"] or "Wikidata" in evidence[f"{culture}:{x[0]}"]["sources"]),
                            -sum(evidence[f"{culture}:{x[0]}"]["spellings"].values())))
    cap = {"th": 450, "km": 400, "lo": 400}[lang]
    return out[:cap]

# ─────────────────────────────── Filipino ───────────────────────────────
PH = [("Tagalog", "tl"), ("Cebuano", "ceb"), ("Ilocano", "ilo"), ("Hiligaynon", "hil"), ("Kapampangan", "pam"), ("Central Bikol", "bcl")]
EXTRA_PH = ["Inday", "Dodong", "Nonoy", "Nene", "Neneng", "Bebot", "Toto", "Totoy", "Dodoy", "Day", "Dong", "Ading", "Bunso", "Jun-Jun",
            "Boy", "Ineng", "Ening", "Baby", "Girlie", "Bebe", "Ging", "Bing", "Pinky", "Dindo"]
NATIVE_PH = {"Tagalog", "Cebuano", "Ilocano", "Hiligaynon", "Kapampangan", "Central Bikol", "Bikol", "Waray-Waray", ""}

def filipino(evidence):
    by = {}
    for lang, code in PH:
        for e in wikt_entries(lang, code):
            if e.get("renders"): continue
            t = e["title"]
            if not re.fullmatch(r"[A-Z][a-zñ]+(?:[- ][A-Z]?[a-z]+)*", t): continue
            nick = bool(e["dimof"])
            ety = e["block"].split("{{" + code + "-pr")[0]
            native_word = [g for name, pos, named in templates(ety) if name in ("m", "l", "inh") and pos and pos[0] == code
                           for g in [plain(named.get("t") or named.get("gloss") or (pos[3] if len(pos) > 3 else ""))] if g]
            if not (nick or e["from"] in NATIVE_PH and (native_word or e["from"] in ("Tagalog", "Cebuano") or not e["from"])): continue
            if not nick and not e["from"] and not native_word and t.lower() in FOREIGN: continue
            d = by.setdefault(t, {"langs": [], "sex": collections.Counter(), "dimof": [], "meaning": "", "from": set()})
            if lang not in d["langs"]: d["langs"].append(lang)
            if e.get("sex_given"): d["sex"][e["sex"]] += 1
            for x in e["dimof"]:
                x = plain(x)
                if x and x not in d["dimof"]: d["dimof"].append(x)
            if native_word and not d["meaning"]: d["meaning"] = native_word[0]
            d["from"].add(e["from"])
    # nicknames Wiktionary defines in prose rather than with the given-name template ("a male nickname")
    extra = wikitext(EXTRA_PH)
    for t, text in extra.items():
        for lang, code in PH:
            for line in section(text, lang).split("\n"):
                if not line.startswith("# "): continue
                pl = plain(re.sub(r"\{\{n-g\|([^}]*)\}\}", r"\1", line[2:])).lower()
                m = re.match(r"(?:an? )?(?:common )?(male|female)? ?(nickname|given name)(?: given to an? (?:young )?(filipina|filipino))?", pl)
                if not m or not (m.group(1) or m.group(3)): continue
                sx = "g" if (m.group(1) == "female" or m.group(3) == "filipina") else "b"
                d = by.setdefault(t, {"langs": [], "sex": collections.Counter(), "dimof": [], "meaning": "", "from": set(), "nickname": True})
                if lang not in d["langs"]: d["langs"].append(lang)
                d["sex"][sx] += 1
    out = []
    for t, d in by.items():
        if not d["sex"]: sex = "e"
        else:
            sex = "e" if d["sex"]["e"] or (d["sex"]["g"] and d["sex"]["b"]) else d["sex"].most_common(1)[0][0]
        language = d["langs"][0]
        others = [l for l in d["langs"][1:]]
        if d.get("nickname") and not d["dimof"]:
            s = f"A Filipino nickname (Wiktionary)."
        elif d["dimof"]:
            s = f"A Filipino nickname for {', '.join(d['dimof'][:-1]) + ' or ' + d['dimof'][-1] if len(d['dimof']) > 1 else d['dimof'][0]} (Wiktionary)."
        else:
            s = "A Filipino name" + (f" meaning '{d['meaning']}'" if d["meaning"] else "") + " (Wiktionary)."
        if others: s += f" Used in {language} and {', '.join(others)}." if len(others) == 1 else f" Used in {language}, {', '.join(others)}."
        out.append([t, sex, "Filipino", language, "", d["meaning"], s, "", "real", [], ease_of(t)])
        evidence[f"Filipino:{t}"] = {"languages": d["langs"], "dimof": d["dimof"], "sources": ["Wiktionary"]}
    return out

# ─────────────────────────────── Burmese (for fixes only) ───────────────────────────────
def has_word(text, w):
    """w occurs as whole syllables: မေ is not inside မောင်, မြ is not inside မြင့်."""
    for m in re.finditer(re.escape(w), text):
        nxt, after = text[m.end():m.end() + 1], text[m.end() + 1:m.end() + 3].replace("\u1037", "")[:1]
        if nxt and unicodedata.category(nxt) in ("Mn", "Mc"): continue
        if after in ("\u103a", "\u1039"): continue                       # the next letter is this syllable's final consonant
        return True
    return False

def burmese_spellings(syllables, min_count=3):
    """For each Burmese name syllable, the English word that notable Burmese people use for it (co-occurrence in labels)."""
    rows = people("my")
    tok = collections.Counter(); co = collections.defaultdict(collections.Counter)
    for p in rows.values():
        en = [w for w in re.sub(r"\(.*?\)", " ", p["en"]).split() if LATIN.fullmatch(w)]
        nat = p["nat"]
        if not en or re.search("[A-Za-z]", nat): continue
        for w in set(en): tok[w] += 1
        for s in syllables:
            if has_word(nat, s):
                for w in set(en): co[s][w] += 1
    out = {}
    for s in syllables:
        n = sum(1 for p in rows.values() if has_word(p["nat"], s))
        best = max(co[s].items(), key=lambda kv: (kv[1] / tok[kv[0]]) * kv[1], default=None)
        if best and best[1] >= min_count and best[1] / tok[best[0]] >= 0.6 and best[1] / max(n, 1) >= 0.5:
            out[s] = (best[0], best[1], n)
    return out

def burmese(evidence):
    """Burmese has no family names; each name word is written in English the way Burmese people write it (ဝင်း Win)."""
    entries = [e for e in wikt_entries("Burmese", "my") if not e.get("renders")]
    att = burmese_spellings(sorted({e["title"] for e in entries}), min_count=2)
    by = {}
    for e in entries:
        if e["title"] not in att: continue
        w, c, n = att[e["title"]]
        d = by.setdefault(w.lower(), {"name": w, "native": [], "sex": collections.Counter(), "meaning": "", "count": 0, "from": ""})
        if e["title"] not in d["native"]: d["native"].append(e["title"]); d["count"] += c
        if e.get("sex_given"): d["sex"][e["sex"]] += 1
        d["meaning"] = d["meaning"] or meaning_for(e)
        d["from"] = d["from"] or (e["from"] if e["from"] in ("Pali", "Sanskrit", "Arabic") else "")
    out = []
    for d in by.values():
        sex = "e" if not d["sex"] or d["sex"]["e"] or (d["sex"]["g"] and d["sex"]["b"]) else d["sex"].most_common(1)[0][0]
        s = "A Burmese name" + (f" meaning '{d['meaning']}' (Wiktionary)" if d["meaning"] else "") + (f" from {d['from']}" if d["from"] else "") + "."
        s += " Written " + " or ".join(d["native"][:2]) + "."
        out.append([d["name"], sex, "Burmese", "Burmese", "", d["meaning"], s, "", "real", [], ease_of(d["name"])])
        evidence[f"Burmese:{d['name']}"] = {"native": d["native"], "people_spelling_it_so": d["count"], "sources": ["Wiktionary", "people"]}
    return out

# reviewed by hand: rows whose problem is not a spelling the data above can correct
MANUAL_FIXES = [
    {"name": "Kongmā", "file": "data/culture-names.json", "action": "respell", "new_name": "Kongma",
     "reason": "Macron comes from a scholarly transliteration on the Wikidata item; the Royal Institute (RTGS) spelling of กงมา, used on Thai documents, has no diacritics."},
    {"name": "Sagat", "file": "data/culture-names.json", "action": "untag", "tag": "Thai",
     "reason": "Owner flagged the Thai tag. Its only source is Wikidata Q110677429, which merges four unrelated names (Kazakh Сағат, Thai สกัด, Hindi सगत, Bengali সগত); the one Thai bearer is the boxer Sagat Petchyindee and สกัด is the verb 'to block'. "
               "The same merge also makes this a Bengali row that shows Cyrillic ('Written Сағат'); the main session may want to drop or rebuild the row."},
]

# ─────────────────────────────── fixes ───────────────────────────────
def fixes(sea_rows):
    cn = json.load(open(os.path.join(ROOT, "data", "culture-names.json"), encoding="utf-8"))
    ours = {(r[2], strip_marks(r[0]).lower()) for r in sea_rows}
    by_native = {}
    for r in sea_rows:
        for w in re.findall(r"Written ([^.]+)\.", r[6])[:1]:
            for n in w.split(" or "): by_native[(r[2], n)] = r[0]
    out = []
    for r in cn:
        if r[2] in ("Khmer", "Thai", "Lao"):
            m = re.search(r"Written (\S+?)\.", r[6]); nat = m.group(1) if m else ""
            new = by_native.get((r[2], nat))
            if new and new != r[0]:
                out.append({"name": r[0], "file": "data/culture-names.json", "action": "respell", "new_name": new,
                            "reason": f"Letter-by-letter transliteration of {nat}; the attested spelling is {new} (see data/sea-names.json for the full row)."})
            elif not new and (r[2], strip_marks(r[0]).lower()) in ours and r[0] != strip_marks(r[0]):
                out.append({"name": r[0], "file": "data/culture-names.json", "action": "respell", "new_name": strip_marks(r[0]),
                            "reason": "Macron from a scholarly transliteration; the name is written without it."})
        if r[2] == "Burmese" and re.match(r"A Burmese name\. Written ", r[6]):
            out.append({"burmese": True, "row": r})
        for tag in ("Khmer",):
            if tag in r[9] and r[0] == "Smbat":
                out.append({"name": r[0], "file": "data/culture-names.json", "action": "untag", "tag": "Khmer",
                            "reason": "Smbat (Սմբատ) is Armenian; no Khmer source names it. Remove 'Khmer' from also and the 'Also a Khmer name.' clause."})
    burm = [x.pop("row") for x in out if x.get("burmese")]
    out = [x for x in out if not x.get("burmese")]
    syl = {re.search(r"Written (\S+?)\.", r[6]).group(1): r for r in burm}
    attested = burmese_spellings(list(syl))
    for s, r in syl.items():
        if s in attested:
            w, c, n = attested[s]
            out.append({"name": r[0], "file": "data/culture-names.json", "action": "respell", "new_name": w,
                        "reason": f"Letter-by-letter transliteration of {s}; {c} of the {n} Burmese people on Wikidata whose name contains {s} write it {w}"
                                  + (" (see data/sea-names.json for the full row)." if (("Burmese", w.lower()) in ours) else ".")})
        else:
            out.append({"name": r[0], "file": "data/culture-names.json", "action": "drop",
                        "reason": f"Letter-by-letter transliteration of {s}, not a spelling Burmese families use; no source-attested spelling found."})
    return out + MANUAL_FIXES

def main():
    load_english()
    evidence, rows = {}, []
    for lang in ("th", "km", "lo"):
        rows += build_culture(lang, evidence)
    # names shared by Thai and Lao rows
    have = collections.defaultdict(set)
    for r in rows: have[r[0].lower()].add(r[2])
    for r in rows:
        r[9] = sorted(have[r[0].lower()] - {r[2]})
        if r[9]: r[6] += " Also a " + " and ".join(r[9]) + " name."
    rows += filipino(evidence)
    rows += burmese(evidence)
    rows.sort(key=lambda r: (r[10], r[2], r[0]))
    json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    fx = fixes(rows)
    json.dump(fx, open(FIXES, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(evidence, open(EVIDENCE, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    c = collections.Counter((r[2], r[1], r[10]) for r in rows)
    for k in sorted(c): print(k, c[k])
    print(len(rows), "rows;", len(fx), "fixes")

if __name__ == "__main__":
    main()
