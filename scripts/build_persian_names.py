#!/usr/bin/env python3
"""Persian and ancient Iranian names -> data/persian-names.json (+ data/sacred/persian.tsv).

Run:  python3 scripts/build_persian_names.py            (fetches anything missing into raw/persian/)
      python3 scripts/build_persian_names.py --offline  (only use what is already cached)

Origin is kept strict. A row's culture says where the name comes from, not where it is used:
  "Persian"  a Persian-language name whose own source traces it to Persian or an older Iranian stage
             (Middle Persian, Old Persian, Avestan, Parthian ...), or that is attested in an Iranian text
             (Avesta, Old Persian inscriptions, Middle Persian books, the Shahnameh) and no source gives it
             a foreign origin.
  "Iranian"  an ancient Iranian name that is not Persian specifically (Avestan, Median, Parthian, Sogdian,
             Bactrian), language = the stage it is attested in.
Names that come from Arabic (Mohammad, Ali, Reza, Zahra, Fatemeh, Maryam ...) are not written, even though
they are among the most common names in Iran; nor are names from Turkic, Greek, Hebrew, European languages
or Kurdish. Names made of Arabic and Persian parts are kept with "Arabic + Persian elements" at the head of
src, and are never described as Persian-origin. Nothing is guessed: every name, sex and meaning is printed by
a cited source, and a row's src says which.

Sources (all cached under raw/persian/; delete a file to fetch it again)
  Avesta          avesta.org (J. H. Peterson's digital edition): Avestan text after Geldner 1896 (PD) and
                  Darmesteter's / Mills's SBE translations (1880-1898, PD). The Fravardin Yasht catalogue
                  (Yt 13.95-142) is read verse by verse; sex is the grammar of the text (ashaono masculine,
                  ashaonya feminine) and its "son of" / "wife of" / "maid".
  Middle Persian  West's SBE translations of the Bundahishn (1880), Denkard (1892, 1897) and Haug & West's
                  Arda Viraf (1872) on avesta.org (PD).
  Old Persian     English Wiktionary "Old Persian given names" (CC BY-SA 4.0), each entry with its Old
                  Persian cuneiform, transliteration and inscription citation where the entry gives one.
  Wiktionary      English Wiktionary (CC BY-SA 4.0): Persian, Middle Persian, Parthian, Avestan, Sogdian,
                  Bactrian and Median given names and proper nouns, with their etymology sections.
  Wikidata        (CC0): Achaemenid, Arsacid and Sasanian dynasty members; Shahnameh characters (P1441).
  Shahnameh       ganjoor.net (Ferdowsi's text, PD; ganjoor asks for a link back): every character name
                  is looked up in the text and cited by its first bayt.
  Not used        Encyclopaedia Iranica (copyrighted; cited for etymologies at most, nothing copied);
                  Tavernier, Iranica in the Achaemenid Period (copyrighted); Persepolis Fortification
                  name indexes (no openly licensed list); baby-name websites.
"""
import collections, hashlib, html, json, os, re, sys, time, unicodedata, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw", "persian")
WORLD_RAW = os.path.join(ROOT, "raw", "sacred", "world")
OUT = os.path.join(ROOT, "data", "persian-names.json")
OUT_SACRED = os.path.join(ROOT, "data", "sacred", "persian.tsv")
OFFLINE = "--offline" in sys.argv
UA = {"User-Agent": "Lullabyte-build/1.0 (https://github.com/suhxnitiwari/baby-name-maker; names research)"}


# ----------------------------------------------------------------------------------------------- fetching
def get(url, path, pause=1.0, data=None):
    """Cached download: url -> raw/persian/<path>. Returns the local path or None."""
    p = os.path.join(RAW, path)
    if os.path.exists(p) and os.path.getsize(p) > 0:
        return p
    if OFFLINE:
        return None
    os.makedirs(os.path.dirname(p), exist_ok=True)
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers=UA, data=data)
            body = urllib.request.urlopen(req, timeout=180).read()
            break
        except Exception as e:  # noqa
            code = getattr(e, "code", None)
            if code == 404 or attempt == 5:
                print(f"  fetch failed {url[:120]}: {e}", file=sys.stderr)
                return None
            time.sleep(65 if code == 429 else 3 + 3 * attempt)
    open(p, "wb").write(body)
    time.sleep(pause)
    return p


def read(p, enc="utf-8"):
    return open(p, encoding=enc, errors="replace").read() if p else ""


def nfc(s):
    return unicodedata.normalize("NFC", s)


def fold(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    return re.sub(r"[\s\-'’ʿʾ.]", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s))


# ----------------------------------------------------------------------------------------------- Wiktionary
WAPI = "https://en.wiktionary.org/w/api.php?"


def wapi(params, path):
    p = get(WAPI + urllib.parse.urlencode({**params, "format": "json", "formatversion": "2"}), path)
    return json.load(open(p, encoding="utf-8")) if p else {}


def category(cat, depth=3, prefix=None, seen=None):
    """Titles in a Wiktionary category and its subcategories (only subcategories of the same language)."""
    seen = seen if seen is not None else set()
    if cat in seen:
        return {}
    seen.add(cat)
    prefix = prefix or cat.split(" given names")[0].split(" proper nouns")[0].split(" male")[0].split(" female")[0]
    out, cont, i = {}, None, 0
    while True:
        params = {"action": "query", "list": "categorymembers", "cmtitle": "Category:" + cat, "cmlimit": "500",
                  "cmtype": "page|subcat"}
        if cont:
            params["cmcontinue"] = cont
        d = wapi(params, f"wikt/cat/{slug(cat)}-{i}.json")
        for m in d.get("query", {}).get("categorymembers", []):
            t = m["title"]
            if m["ns"] == 14:
                sub = t.split(":", 1)[1]
                if depth > 0 and sub.startswith(prefix + " "):
                    for k, v in category(sub, depth - 1, prefix, seen).items():
                        out.setdefault(k, set()).update(v)
            elif m["ns"] == 0:
                out.setdefault(t, set()).add(cat)
        cont = d.get("continue", {}).get("cmcontinue")
        i += 1
        if not cont:
            break
    return out


def slug(s):
    s2 = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")
    return s2[:80] + "-" + hashlib.md5(s.encode()).hexdigest()[:6]


_PAGES = None


def pages(titles):
    """{title: wikitext} for many titles, 50 per request; every answer is cached under raw/persian/wikt/pages/."""
    global _PAGES
    d0 = os.path.join(RAW, "wikt", "pages")
    if _PAGES is None:
        _PAGES = {}
        for f in sorted(os.listdir(d0)) if os.path.isdir(d0) else []:
            for pg in json.load(open(os.path.join(d0, f), encoding="utf-8")).get("query", {}).get("pages", []):
                rv = pg.get("revisions")
                _PAGES[pg["title"]] = rv[0]["slots"]["main"]["content"] if rv else ""
    need = sorted({t for t in titles if t and t not in _PAGES})
    for i in range(0, len(need), 50):
        batch = need[i:i + 50]
        key = hashlib.md5("|".join(batch).encode()).hexdigest()[:16]
        d = wapi({"action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main",
                  "titles": "|".join(batch)}, f"wikt/pages/{key}.json")
        norm = {n["from"]: n["to"] for n in d.get("query", {}).get("normalized", [])}
        for pg in d.get("query", {}).get("pages", []):
            rv = pg.get("revisions")
            _PAGES[pg["title"]] = rv[0]["slots"]["main"]["content"] if rv else ""
        for a, b in norm.items():
            _PAGES[a] = _PAGES.get(b, "")
    return {t: _PAGES[t] for t in titles if _PAGES.get(t)}


def section(text, lang):
    m = re.search(r"(?m)^==\s*" + re.escape(lang) + r"\s*==\s*$", text)
    if not m:
        return ""
    nxt = re.search(r"(?m)^==[^=].*==\s*$", text[m.end():])
    return text[m.end(): m.end() + nxt.start()] if nxt else text[m.end():]


# ----------------------------------------------------------------------------------------------- Wikidata
def sparql(query, path):
    """Wikidata query service (CC0), cached; the service allows about one query a minute when busy."""
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": query, "format": "json"})
    p = get(url, path, pause=61)
    if not p:
        return []
    try:
        d = json.load(open(p, encoding="utf-8"))
    except ValueError:
        os.remove(p)
        return []
    return [{k: v["value"] for k, v in b.items()} for b in d["results"]["bindings"]]


SEX = {"Q6581097": "b", "Q6581072": "g", "Q2449503": "b", "Q1052281": "g"}
DYNASTIES = {"Q13527812": "Achaemenid", "Q12818551": "Arsacid (Parthian)", "Q15955102": "Sasanian",
             "Q2655716": "Mihranid", "Q769552": "House of Karen", "Q13415387": "House of Suren",
             "Q17004913": "House of Ispahbudhan"}
Q_DYN = """SELECT ?p ?en ?fa ?desc ?sex ?fam ?gn ?gnen ?native WHERE {
  VALUES ?fam { %s }
  ?p wdt:P31 wd:Q5; wdt:P53 ?fam .
  OPTIONAL { ?p rdfs:label ?en FILTER(LANG(?en)="en") }
  OPTIONAL { ?p rdfs:label ?fa FILTER(LANG(?fa)="fa") }
  OPTIONAL { ?p schema:description ?desc FILTER(LANG(?desc)="en") }
  OPTIONAL { ?p wdt:P21 ?sex }
  OPTIONAL { ?p wdt:P735 ?gn . ?gn rdfs:label ?gnen FILTER(LANG(?gnen)="en") }
  OPTIONAL { ?p wdt:P1559 ?native }
}""" % " ".join("wd:" + q for q in DYNASTIES)
Q_SHAH = """SELECT ?p ?en ?fa ?desc ?sex ?inst WHERE {
  ?p wdt:P1441 wd:Q8279 .
  OPTIONAL { ?p rdfs:label ?en FILTER(LANG(?en)="en") }
  OPTIONAL { ?p rdfs:label ?fa FILTER(LANG(?fa)="fa") }
  OPTIONAL { ?p schema:description ?desc FILTER(LANG(?desc)="en") }
  OPTIONAL { ?p wdt:P21 ?sex }
  OPTIONAL { ?p wdt:P31 ?inst }
}"""


def wikidata_people():
    dyn = sparql(Q_DYN, "wikidata/dynasties.json")
    shah = sparql(Q_SHAH, "wikidata/shahnameh.json")
    return dyn, shah


# ----------------------------------------------------------------------------------------------- etymology
IRANIAN = {"pal", "peo", "ae", "xpr", "xmn", "sog", "xbc", "xme", "kho", "oos", "ira-pro", "ira-old", "ira-mid", "iir-pro",
           "fa-cls", "ira-sgc-pro", "ira-wes-pro", "ira-sym-pro", "ira-mny-pro", "ira-pat-pro", "ira-csh-pro"}
ARABIC = {"ar", "acm", "apc", "arz", "ajp", "afb", "xaa", "sem-arb"}
NEUTRAL = {"fa", "ine-pro", "und", "mul"}
NEW_IRANIAN = {"ckb", "kmr", "ku", "mzn", "glk", "lrc", "bal", "ps", "tg", "os", "zza", "sdh", "bqi", "tly"}   # other living Iranian languages
LANGNAME = {"Middle Persian": "pal", "Old Persian": "peo", "Avestan": "ae", "Parthian": "xpr", "Sogdian": "sog", "Bactrian": "xbc",
            "Arabic": "ar", "Classical Persian": "fa-cls", "Median": "xme", "Proto-Iranian": "ira-pro", "Old Iranian": "ira-old",
            "Ancient Greek": "grc", "Greek": "el", "Turkish": "tr", "Ottoman Turkish": "ota", "English": "en", "French": "fr",
            "German": "de", "Latin": "la", "Hebrew": "he", "Central Kurdish": "ckb", "Northern Kurdish": "kmr", "Mazanderani": "mzn",
            "Armenian": "hy", "Russian": "ru", "Mongolian": "mn", "Old Anatolian Turkish": "trk-oat", "Chagatai": "chg",
            "Aramaic": "arc", "Sanskrit": "sa", "Akkadian": "akk", "Elamite": "elx", "Urartian": "xur", "Georgian": "ka",
            "Italian": "it", "Spanish": "es", "Japanese": "ja", "Turkic": "trk", "Mongolic": "xgn"}
STAGE = {"xme-old": "Median", "pal": "Middle Persian", "peo": "Old Persian", "ae": "Avestan", "xpr": "Parthian", "xmn": "Middle Persian",
         "sog": "Sogdian", "xbc": "Bactrian", "xme": "Median", "fa-cls": "Classical Persian", "kho": "Khotanese"}
CHAIN_T = {"inh", "inh+", "bor", "bor+", "der", "der+", "lbor", "slbor", "uder", "ubor", "obor", "learned borrowing",
           "inherited", "borrowed", "derived", "calque", "psm", "translit", "tl"}
PART_T = {"af", "affix", "compound", "com", "suffix", "prefix", "confix", "blend"}


def lang_class(code):
    if not code or code in NEUTRAL:
        return None
    if code in IRANIAN or code.split("-")[0] in IRANIAN or code.startswith("ira-"):
        return "iranian"
    if code in ARABIC:
        return "arabic"
    if code in NEW_IRANIAN:
        return "other-iranian"
    return "foreign"


def templates(text):
    """Etymology templates in reading order: [(name, [args])]; inner templates that are not ours are dropped."""
    found, n = {}, 0
    def sub(m):
        nonlocal n
        name, _, args = m.group(1).partition("|")
        name = name.strip()
        if name in CHAIN_T or name in PART_T or name in ("etymon", "ety", "given name", "m", "l", "desc", "head",
                                                          "fa-proper noun", "pal-proper noun", "xpr-proper noun"):
            n += 1
            found[n] = (name, args.split("|") if args else [])
            return f"\x00{n}\x00"
        return ""
    t = text
    for _ in range(8):
        t2 = re.sub(r"\{\{([^{}]*)\}\}", sub, t)
        if t2 == t:
            break
        t = t2
    return [found[int(k)] for k in re.findall(r"\x00(\d+)\x00", t)]


def kw(args):
    return {a.split("=", 1)[0].strip(): a.split("=", 1)[1].strip() for a in args if "=" in a}


def pos(args):
    return [a.strip() for a in args if "=" not in a]


def etymology(sec, code):
    """(chain languages, parts [(lang, word)], meaning-bearing glosses) from a language section's etymology."""
    blocks = re.split(r"(?m)^===\s*Etymology[^=]*===\s*$", sec)
    ety_blocks = blocks[1:] if len(blocks) > 1 else [sec]
    gn = [b for b in ety_blocks if "{{given name|" + code in b]
    b = (gn or ety_blocks)[0]
    head = re.split(r"(?m)^====?\s*(?:Pronunciation|Proper noun|Noun|Adjective|Alternative forms)", b)[0]
    chain, parts = [], []
    for name, args in templates(head):
        p, k = pos(args), kw(args)
        if name in CHAIN_T and len(p) >= 2 and p[0] == code:
            chain.append(p[1])
        elif name in PART_T and p and p[0] == code and k.get("nocat") != "1":
            for i, w in enumerate(p[1:], 1):
                lang = k.get(f"lang{i}", code)
                if w and w != "-":
                    parts.append((lang, w))
        elif name in ("etymon", "ety") and p and p[0] == code:
            mode = None
            for a in p[1:]:
                if a.startswith(":"):
                    mode = a[1:]
                    continue
                m = re.match(r"^([a-z]{2,3}(?:-[a-z]{2,4})*):", a)
                if mode in ("inh", "bor", "der", "lbor", "uder", "ubor", "slbor"):
                    if m:
                        chain.append(m.group(1))
                    chain += re.findall(r"<ety:(?:inh|bor|der|lbor|uder|ubor)<([a-z]{2,3}(?:-[a-z]{2,4})*):", a)
                elif mode in ("af", "compound", "suffix", "prefix", "from"):
                    w = re.sub(r"<.*", "", a[m.end():] if m else a)
                    if w:
                        parts.append((m.group(1) if m else code, w))
    # "from {{m|grc|Ἀλέξανδρος}}": a source named in running text counts as a step of the chain
    for m in re.finditer(r"[Ff]rom (?:an? )?\x01?\{\{(?:m|l|m\+)\|([a-z]{2,3}(?:-[a-z]{2,4})*)\|", head):
        if m.group(1) != code:
            chain.append(m.group(1))
        elif not chain and not parts:
            w = re.match(r"([^|}]+)", head[m.end():])
            if w:
                parts.append((code, w.group(1)))
    return chain, parts, b


def given(sec, code):
    m = re.search(r"\{\{given name\|" + re.escape(code) + r"\|([^{}]*)\}\}", sec)
    if not m:
        return None
    args = m.group(1).split("|")
    p, k = pos(args), kw(args)
    g = {"male": "b", "female": "g", "unisex": "e"}.get(p[0] if p else "", "")
    return {"g": g, **k}


def classify(chain, parts, cats=(), gn_from="", part_class=None):
    """iranian / arabic / mixed / foreign / other-iranian / unknown, plus the Iranian stage named (if any)."""
    langs = list(chain)
    for c in (cats if not chain else ()):
        m = re.search(r" from (.+)$", c)
        if m and m.group(1) in LANGNAME:
            langs.append(LANGNAME[m.group(1)])
    for f in re.split(r"[,+]| and ", gn_from if not chain else ""):
        if f.strip() in LANGNAME:
            langs.append(LANGNAME[f.strip()])
    gfrom = [LANGNAME.get(f.strip()) for f in re.split(r"[,+<]| and ", gn_from or "") if f.strip()]
    if gfrom and all(gfrom) and not any(lang_class(l) == "iranian" for l in gfrom):
        langs += gfrom                    # "from=Arabic < Ancient Greek" (Eskandar): the entry's own summary wins
    cls = [c for c in (lang_class(l) for l in langs) if c]
    stage = next((STAGE[l] for l in langs if l in STAGE), "")
    via_arabic = bool(cls) and cls[0] == "arabic" and "iranian" in cls
    # the deepest step decides: Shahrzad (Arabic <- Middle Persian) is Iranian, Arghavan (Middle Persian <- Aramaic) is not
    if cls and cls[-1] == "iranian":
        return ("iranian", stage, via_arabic)
    if cls and any(cls):
        if "arabic" in cls:
            return ("arabic", "", False)
        if "other-iranian" in cls:
            return ("other-iranian", "", False)
        return ("foreign", "", False)
    if parts and part_class:
        pc = [part_class(l, w) for l, w in parts]
        kinds = {c[0] for c in pc}
        stage = next((c[1] for c in pc if c[1]), "")
        if "arabic" in kinds and "iranian" in kinds:
            return ("mixed", stage, False)
        if "arabic" in kinds:
            return ("arabic", "", False)
        if kinds & {"foreign", "other-iranian"}:
            return ("foreign", "", False)
        if "iranian" in kinds:
            return ("iranian", stage, False)
    return ("unknown", "", False)


# ----------------------------------------------------------------------------------------------- New Persian (Wiktionary)
TR = [("â", "a"), ("ā", "a"), ("á", "a"), ("ê", "e"), ("ē", "e"), ("ô", "o"), ("ō", "o"), ("û", "u"), ("ū", "u"), ("î", "i"),
      ("ī", "i"), ("š", "sh"), ("ž", "zh"), ("č", "ch"), ("ḵ", "kh"), ("x", "kh"), ("ğ", "gh"), ("ġ", "gh"), ("q", "gh"),
      ("ʿ", ""), ("ʾ", ""), ("'", ""), ("’", ""), ("ḥ", "h"), ("ṣ", "s"), ("ẓ", "z"), ("ṭ", "t"), ("ż", "z"), ("ṯ", "s"), ("ḏ", "z")]


def latin_from_tr(tr):
    s = tr.strip().split(",")[0].split("/")[0].strip().lower()
    for a, b in TR:
        s = s.replace(a, b)
    s = re.sub(r"[^a-z -]", "", s).strip()
    return s[:1].upper() + s[1:] if s else ""


WORD_NOT = {"جین"}   # the Persian noun جین is "gene"; the given name is English Jane


def persian_layer():
    cat = category("Persian given names")
    P = pages(cat)
    info = {}
    need_parts = set()
    for t, text in P.items():
        sec = section(text, "Persian")
        if not sec:
            continue
        chain, parts, blk = etymology(sec, "fa")
        if not chain and not parts:
            # "From the name of Imam علی and his title رضا": the words the etymology links to
            parts = [("fa", w) for n, a in templates(blk.split("===")[0] if blk else "")
                     if n == "l" and pos(a)[:1] == ["fa"] for w in pos(a)[1:2]]
        info[t] = (sec, chain, parts)
        need_parts |= {re.sub(r"[\u064b-\u0652\u0670]", "", w) for l, w in parts if l == "fa"}
    PP = pages([w.replace("ـ", "-") if w.startswith("ـ") or w.endswith("ـ") else w for w in need_parts]) if need_parts else {}

    def part_class(lang, w):
        if lang != "fa":
            c = lang_class(lang)
            return (c or "unknown", STAGE.get(lang, ""), False)
        w = re.sub(r"[\u064b-\u0652\u0670]", "", w)
        sec = section(PP.get(w) or PP.get(w.replace("ـ", "-")) or P.get(w) or "", "Persian")
        if not sec:
            return ("unknown", "", False)
        ch, _pa, _b = etymology(sec, "fa")
        return classify(ch, [])

    out, stats = [], collections.Counter()
    for t, (sec, chain, parts) in info.items():
        g = given(sec, "fa") or {}
        cats = cat.get(t, ())
        sex = g.get("g") or ("b" if any(" male " in c for c in cats) else "g" if any(" female " in c for c in cats)
                             else "e" if any("unisex" in c for c in cats) else "")
        kind, stage, via_ar = classify(chain, parts, cats, g.get("from", ""), part_class)
        blk = etymology(sec, "fa")[2]
        if kind == "unknown" and t not in WORD_NOT and not g.get("eq") and "{{given name|fa" in blk and re.search(r"(?m)^====?=?\s*(Noun|Adjective)\s*=", blk):
            # an ordinary Persian word (لاله "tulip") whose entry names no source language at all, anywhere
            langs = [pos(a)[1] for n, a in templates(sec) if n in CHAIN_T and len(pos(a)) > 1 and pos(a)[0] == "fa"]
            langs += re.findall(r"<ety:\w+<([a-z-]+):|:(?:inh|bor|der)\|([a-z-]+):", sec)
            if not langs:
                kind = "word"
        stats[kind] += 1
        head = re.search(r"\{\{fa-proper noun\|[^{}]*?tr=([^|}]+)", sec)
        xlit = re.sub(r"^w:", "", (g.get("xlit") or "").split(",")[0]).strip()
        latin = xlit or (latin_from_tr(head.group(1)) if head else "")
        out.append(dict(native=t, sex=sex, kind=kind, stage=stage, via_arabic=via_ar, latin=latin, sec=sec,
                        eq=g.get("eq", ""), meaning=g.get("meaning", ""), parts=parts, chain=chain, cats=sorted(cats)))
    return out, stats


def iranian_form(blk):
    """the first older Iranian form an etymology names: ('Middle Persian', 'Šīrēn')"""
    for m in re.finditer(r"\{\{(?:inh|der|bor|lbor|uder|ubor|slbor)\+?\|[a-z-]+\|(pal|peo|ae|xpr|xme|sog|xbc)\|([^{}]*)\}\}", blk):
        k = kw(m.group(2).split("|"))
        f = k.get("ts") or k.get("tr") or ""
        if f and not f.startswith("*"):
            return STAGE[m.group(1)], f.split(",")[0].strip()
    m = re.search(r"\b(pal|peo|ae|xpr):(?:<[^>]*>)*?<ts:([^>]+)>", blk)
    if m:
        return STAGE[m.group(1)], m.group(2).split("~")[0].strip()
    return "", ""


def clean_text(t):
    t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"\{\{w\|(?:[^|}]*\|)?([^|}]*)\}\}", r"\1", t)
    t = re.sub(r"\{\{[^{}]*\}\}", "", t)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>|'''?", "", t)).strip(" :;,.")


def meaning_of(sec, code="fa"):
    """A meaning only where the entry states one for the name: the given-name line's meaning=, the etymology's lit=,
    or the definition of the word the name is (same etymology, and the proper noun has no other sense)."""
    g = given(sec, code) or {}
    if g.get("meaning"):
        return clean_text(g["meaning"])[:80]
    blk = etymology(sec, code)[2]
    head = re.split(r"(?m)^====?\s*(?:Pronunciation|Proper noun|Noun|Adjective)", blk)[0]
    for n, a in templates(head):
        if (n in CHAIN_T or n in PART_T or n in ("etymon", "ety")) and kw(a).get("lit"):
            return clean_text(kw(a)["lit"])[:80]
    pn = re.search(r"(?ms)^====?\s*Proper noun\s*=+\s*$(.*?)(?=^===|\Z)", blk)
    senses = re.findall(r"(?m)^#(?![:*])\s*(.*)$", pn.group(1)) if pn else []
    if len(senses) != 1:
        return ""
    m = re.search(r"(?ms)^====?\s*(?:Noun|Adjective)\s*=+\s*$.*?^#(?![:*])\s*([^\n]*)", blk)
    if not m:
        return ""
    d = clean_text(re.sub(r"\{\{(?:lb|q|qualifier|gloss)\|[^{}]*\}\}", "", m.group(1)))
    d = re.sub(r"\(\s*\)", "", d).strip(" ,;")
    return d[:80] if 2 < len(d) < 60 and not re.search(r"given name|surname|name of", d, re.I) else ""


# ----------------------------------------------------------------------------------------------- ancient languages (Wiktionary)
ANCIENT = [("Old Persian", "peo", "Persian"), ("Middle Persian", "pal", "Persian"), ("Parthian", "xpr", "Iranian"),
           ("Avestan", "ae", "Iranian"), ("Bactrian", "xbc", "Iranian")]
SCRIPT_TITLE = {"peo": "Old Persian cuneiform", "pal": "Book Pahlavi", "xpr": "Inscriptional Parthian", "ae": "Avestan script",
                "xbc": "Greek script"}


def ancient_layer():
    cats = {}
    for L, code, _c in ANCIENT:
        for c in (f"{L} given names", f"{L} proper nouns"):
            for t, v in category(c).items():
                cats.setdefault(t, set()).update(v)
    P = pages(cats)
    out, stats = [], collections.Counter()
    for L, code, culture in ANCIENT:
        for t, text in sorted(P.items()):
            sec = section(text, L)
            g = given(sec, code) if sec else None
            if not g:
                continue
            chain, parts, blk = etymology(sec, code)
            kind, _stage, _ = classify(chain, [], [c for c in cats.get(t, ()) if c.startswith(L)])
            disputed = bool(re.search(r"\{\{(?:unk|unknown)\|", blk.split("===Proper noun")[0]))
            if kind in ("foreign", "arabic") and not disputed:
                stats[f"{L}: {kind}"] += 1
                continue
            lang, cult = L, culture
            if "xme" in " ".join(chain) or "xme-old" in chain:
                lang, cult = "Median", "Iranian"
            hd = re.search(r"\{\{(?:head\|" + code + r"\|proper noun|" + code + r"-proper noun)([^{}]*)\}\}", sec)
            hk = kw(hd.group(1).split("|")) if hd else {}
            ts = (hk.get("ts") or (hk.get("tr") if code in ("xpr", "pal") and not re.search(r"[ʾʿẖ']", hk.get("tr", "")) else "")
                  or "").split(",")[0].strip()
            ts = re.split(r"\s*[~/]\s*", re.sub(r"[ʰ\u2060]", "", ts))[0].strip()
            if ts.startswith("*"):
                stats[f"{L}: reconstructed form only"] += 1
                continue
            xl = re.sub(r"^w:", "", (g.get("xlit") or "").split(",")[0]).strip()
            latin = g.get("eq") or xl or ts or (t if code == "xbc" else "")
            if not latin or not re.match(r"^[A-Za-zÀ-ɏḀ-ỿ' -]+$", latin):
                stats[f"{L}: no Latin form"] += 1
                continue
            latin = latin[:1].upper() + latin[1:]
            line = re.search(r"\{\{given name\|" + code + r"\|[^{}]*\}\}(.*)", sec)
            desc = clean_text(line.group(1)) if line else ""
            addl = clean_text(g.get("addl", ""))
            fa = re.search(r"(?m)^\*\s*\{\{desc(?:tree)?\|(?:bor=1\|)?fa\|([^|}]+)", sec)
            stats[f"{L}: kept"] += 1
            out.append(dict(name=latin, g=g.get("g", ""), culture=cult, language=lang, form=ts or t, script=t,
                            code=code, desc=desc or addl, fa=fa.group(1) if fa else "", meaning=meaning_of(sec, code),
                            disputed=disputed and kind in ("foreign", "unknown"), chain=chain))
    return out, stats


# ----------------------------------------------------------------------------------------------- Avesta: Fravardin Yasht catalogue
def yt13():
    eng = read(get("https://www.avesta.org/ka/yt13sbe.htm", "avesta/yt13sbe.htm"), "latin-1")
    ave = read(get("https://www.avesta.org/ka/yt13.htm", "avesta/yt13.htm") or
               (os.path.join(WORLD_RAW, "avesta", "ka_yt13.htm") if os.path.exists(os.path.join(WORLD_RAW, "avesta", "ka_yt13.htm")) else None),
               "latin-1")
    def verses(t):
        s = strip_tags(re.sub(r"(?is)<(script|style|head).*?</\1>", "", t))
        out, cur = {}, None
        for line in s.splitlines():
            m = re.match(r"^\s*(\d{1,3})\.\s*$", line) or re.match(r"^\s*(\d{1,3})\.\s+(.*)$", line)
            if m:
                cur = int(m.group(1))
                line = m.group(2) if m.lastindex == 2 else ""
            if cur:
                out[cur] = out.get(cur, "") + " " + line
        return out
    E, A = verses(eng), verses(ave)
    norm = lambda s: re.sub(r"[^a-z]", "", unicodedata.normalize("NFD", s.lower().replace("ý", "y").replace("x", "kh")
                                                                   .replace("ñ", "n").replace("ã", "a").replace("å", "a")))
    NAME = r"([A-Z][A-Za-z]+(?:[- ][A-Za-z]+)*?)"
    rows = []
    for v in range(95, 143):
        txt = re.sub(r"\[[^\]]*\]", "", " ".join(E.get(v, "").split()))
        fem = v >= 139
        for m in re.finditer(r"Fravashis? [Oo]f the holy (?:and \w+ )?(?:and pure )?(?:king |maid |one whose name is )?"
                             r"([A-Z][\w-]+(?: (?:and )?[A-Z][\w-]+)?)(?:, the (son|sons|wife|daughter) of (?:the son of )?(?:the great )?([A-Z][\w-]+))?", txt):
            names = [n for n in re.split(r" and | ", m.group(1)) if n and n[0].isupper() and n.upper() != n]
            if m.group(1).isupper():
                names = [m.group(1).title()]
            for n in names:
                rows.append((n, "g" if fem else "b", v, m.group(2) or "", m.group(3) or ""))
            if m.group(3) and m.group(2) in ("son", "sons"):
                rows.append((m.group(3), "b", v, "father", ""))
            elif m.group(3) and m.group(2) == "wife":
                rows.append((m.group(3), "b", v, "husband", ""))
    out, seen = [], set()
    for n, g, v, rel, other in rows:
        if n in ("We", "Fravashi", "Turanian", "Aethrapati", "Hamidhpati", "Miza", "Raozhdya", "Tanya", "Saena", "Uspaeshta", "Fryana",
                 "Kahrkana", "Pidha", "Apakhshira", "Athwya") or (n, v) in seen:
            continue
        seen.add((n, v))
        best, score = "", 0.0
        import difflib
        for w in re.findall(r"[^\s,.!;:()]+", A.get(v, "")):
            r = difflib.SequenceMatcher(None, norm(n), norm(w)[:len(norm(n)) + 3]).ratio()
            if r > score:
                best, score = w, r
        who = {"son": f", son of {other}", "sons": f", son of {other}", "wife": f", wife of {other}", "father": ", named as a father",
               "husband": ", named as a husband"}.get(rel, "")
        out.append(dict(name=n, g=g, verse=v, form=best if score >= 0.6 else "", who=who))
    return out


# ----------------------------------------------------------------------------------------------- Shahnameh
def shahnameh_text():
    """[(passage, url, text)] from ganjoor's Shahnameh, reusing the world build's cache when present."""
    def gj(path, url):
        w = os.path.join(WORLD_RAW, "ganjoor", path)
        return w if os.path.exists(w) else get(url, "ganjoor/" + path, pause=0.15)
    segs = []
    root = gj("cat33.json", "https://api.ganjoor.net/api/ganjoor/cat/33?poems=true")
    if not root:
        return segs
    def cat(cid, label):
        p = gj(f"cat{cid}.json", f"https://api.ganjoor.net/api/ganjoor/cat/{cid}?poems=true")
        if not p:
            return
        c = json.load(open(p, encoding="utf-8"))["cat"]
        for po in c.get("poems") or []:
            pj = gj(f"poem{po['id']}.json", f"https://api.ganjoor.net/api/ganjoor/poem/{po['id']}?verses=true&catInfo=false"
                    "&rhymes=false&recitations=false&images=false&songs=false&comments=false&navigation=false")
            if not pj:
                continue
            pd = json.load(open(pj, encoding="utf-8"))
            couplet = {}
            for v in pd["verses"]:
                couplet.setdefault(v["coupletIndex"], []).append(v["text"])
            for ci, texts in sorted(couplet.items()):
                segs.append((f"Shahnameh, {label}, {po['title']}, bayt {ci + 1}", "https://ganjoor.net" + pd["fullUrl"], " ".join(texts)))
        for ch in c.get("children") or []:
            cat(ch["id"], ch["title"])
    for ch in json.load(open(root, encoding="utf-8"))["cat"]["children"]:
        cat(ch["id"], ch["title"])
    return segs


FA_NORM = lambda s: re.sub(r"[ً-ٰٕ]", "", s).replace("ي", "ی").replace("ك", "ک")


def find_in_text(segs, form):
    rx = re.compile(r"(?<![؀-ۿ])" + re.escape(FA_NORM(form)) + r"(?![؀-ۿ])")
    first, n = None, 0
    for ps, url, txt in segs:
        k = len(rx.findall(FA_NORM(txt)))
        if k:
            n += k
            first = first or (ps, url)
    return first, n


def read_tsv(path):
    if not os.path.exists(path):
        return []
    lines = open(path, encoding="utf-8").read().splitlines()
    cols = lines[0].split("\t")
    return [dict(zip(cols, l.split("\t"))) for l in lines[1:] if l.strip()]


def world_rows():
    """The world build's Zoroastrian and Shahnameh rows (raw/sacred/world-persian-partial.tsv, else data/sacred/world*.tsv)."""
    part = os.path.join(ROOT, "raw", "sacred", "world-persian-partial.tsv")
    if os.path.exists(part):
        return read_tsv(part)
    rows = []
    for f in ("world.tsv", "world-review.tsv"):
        rows += [r for r in read_tsv(os.path.join(ROOT, "data", "sacred", f)) if r["tradition"] in ("Zoroastrian", "Persian mythology")]
    return rows


# ----------------------------------------------------------------------------------------------- people of ancient Iran (Wikidata)
def ancient_people():
    """{key: [person sentence]} keyed by Persian script ('fa:شاپور') and by folded English given name ('en:shapur')."""
    dyn, _ = wikidata_people()
    by, seen = collections.defaultdict(list), set()
    for r in sorted(dyn, key=lambda r: r.get("en", "")):
        q = r["p"].rsplit("/", 1)[1]
        if q in seen or not r.get("en"):
            continue
        seen.add(q)
        desc = r.get("desc", "")
        fam = DYNASTIES.get(r.get("fam", "").rsplit("/", 1)[-1], "")
        sentence = f"{r['en']}, {desc} (Wikidata {q})" if desc else f"{r['en']}, of the {fam}{'' if fam.startswith('House') else ' house'} (Wikidata {q})"
        sex = SEX.get(r.get("sex", "").rsplit("/", 1)[-1], "")
        first_en = re.sub(r"\s+(?:[IVX]+|the\b.*)$", "", r["en"]).split(" of ")[0]
        keys = {"en:" + fold(first_en)} | ({"en:" + fold(r["gnen"])} if r.get("gnen") else set())
        # the Persian spelling counts only for a one-name label (Shapur I, Meherdates of Parthia), not Adhar Valash
        if r.get("fa") and re.fullmatch(r"[^\s,]+(?: [IVX]+)?(?: (?:of|the) .*)?", r["en"]):
            keys.add("fa:" + FA_NORM(r["fa"].split()[0]))
        fa1 = r["fa"].split()[0] if r.get("fa") else ""
        for k in keys:
            by[k].append((sentence, sex, q, fa1, r["en"]))
    for k in by:
        # the best-known bearer first: "the Great", then a regnal "I", then the shortest label
        by[k].sort(key=lambda p: ("Great" not in p[4] + p[0], not re.search(r" I$| I,", p[4]), len(p[4])))
    return by


# ----------------------------------------------------------------------------------------------- English spellings of Iranian names
EN_FORMS = ["Roxana", "Roxane", "Atossa", "Cyrus", "Darius", "Xerxes", "Artaxerxes", "Cambyses", "Hystaspes", "Mithridates",
            "Arsaces", "Parysatis", "Amestris", "Statira", "Smerdis", "Artemisia", "Mardonius", "Orontes", "Tiridates", "Phraates",
            "Vologases", "Artabanus", "Pharnaces", "Ariobarzanes", "Bagoas", "Masistes", "Otanes", "Datis", "Tigranes",
            "Zoroaster", "Zarathustra", "Mithra", "Anahita", "Jamshid", "Shapur", "Khosrow", "Bahram", "Ardashir", "Peroz",
            "Hormizd", "Kavad", "Narseh", "Yazdegerd", "Shirin", "Azar", "Laleh", "Roshan", "Dara", "Rustam", "Sohrab"]


def english_layer(people):
    titles = set(EN_FORMS) | {k[3:].title() for k in people if k.startswith("en:")}
    P = pages(titles)
    out = []
    for t, text in sorted(P.items()):
        for L, code in (("English", "en"), ("Translingual", "mul"), ("Latin", "la")):
            sec = section(text, L)
            g = given(sec, code) if sec else None
            if not g:
                continue
            chain, _parts, blk = etymology(sec, code)
            langs = [l for l in chain if lang_class(l)]
            if not langs or lang_class(langs[-1]) != "iranian":
                continue
            stage = next((STAGE[l] for l in reversed(langs) if l in STAGE), "")
            form = iranian_form(blk)[1]
            out.append(dict(name=t, g=g.get("g", ""), stage=stage or "Old Iranian", form=form, meaning=meaning_of(sec, code), lang=L))
            break
    return out


# ----------------------------------------------------------------------------------------------- ease
EN_CODES = {"us", "uk", "au", "ca", "ie", "nir"}


def name_sets():
    en, anywhere = {}, set()
    for f in ("names-db.tsv", "names-extra.tsv"):
        p = os.path.join(ROOT, "data", f)
        for line in open(p, encoding="utf-8") if os.path.exists(p) else []:
            q = line.rstrip("\n").split("\t")
            if len(q) < 4:
                continue
            anywhere.add(fold(q[0]))
            if f == "names-db.tsv" and EN_CODES & set(q[2].split(",")):
                en[q[0].lower()] = en.get(q[0].lower(), 0) + int(q[3] or 0)
    storied = set()
    for f in os.listdir(os.path.join(ROOT, "data")):
        if f.endswith(".json") and f != os.path.basename(OUT):
            try:
                d = json.load(open(os.path.join(ROOT, "data", f), encoding="utf-8"))
            except ValueError:
                continue
            if isinstance(d, list) and d and isinstance(d[0], list) and isinstance(d[0][0], str):
                storied |= {fold(r[0]) for r in d}
    return en, anywhere, storied


DICT = [w.strip() for w in open("/usr/share/dict/words")] if os.path.exists("/usr/share/dict/words") else []
WORDS = {w for w in DICT if w.islower()}


def plain(n, longest=9):
    """spelled as English speakers would read it: letters only, short, no odd clusters (kh, sh, zh, gh count as one letter)"""
    l = n.lower()
    if not re.fullmatch(r"[a-z]+", l) or not 3 <= len(l) <= longest:
        return False
    k = re.sub(r"Kt$", "K", re.sub(r"kh|sh|zh|gh|ch|th", "K", l))
    if len(re.findall(r"[aeiouy]+", k)) > 4 or re.search(r"aa|ii|uu|ae|oe|aou|uo|[^aeiouyK]{3,}|K[^aeiouy]|[^aeiouy]K|^[^aeiouyK]{2}(?<!^(?:br|dr|fr|gr|kr|pr|tr|sp|st|sk|sh|bl|fl|gl|kl|pl|sl))", k):
        return False
    return not re.search(r"[^aeiouyK]{2}$", k) or re.search(r"(nd|nt|st|rd|rt|rz|rs|rn|sht|zd|ft|kht|ns)$", l)


def ease_of(n, modern, en):
    """1 easy and already used today, 2 easy to spell, 3 hard (diacritics, hyphens, long Avestan compounds)"""
    l = n.lower()
    if l in WORDS and l not in en:
        return 3 if not modern else 2
    if l in en or plain(n) and modern:
        return 1
    if plain(n, 11):
        return 2
    return 3


# ----------------------------------------------------------------------------------------------- main
def sentence(s):
    s = s.strip()
    return s if s.endswith(".") else s + "."


def main():
    en_names, anywhere, storied = name_sets()
    people = ancient_people()
    fa_rows, fa_stats = persian_layer()
    fa_by = {FA_NORM(r["native"]): r for r in fa_rows}
    anc, anc_stats = ancient_layer()
    eng = english_layer(people)
    yt = yt13()
    world = world_rows()
    segs = shahnameh_text()
    _dyn, shah = wikidata_people()
    entries = collections.OrderedDict()
    excluded = collections.Counter()

    def person(name, fa=""):
        hits = people.get("fa:" + FA_NORM(fa)) if fa else None
        hits = hits or people.get("en:" + fold(name))
        return hits[0] if hits else None

    def add(name, layer, g, culture, language, src, meaning="", fa="", texts=(), religions="", modern=False, ancient=None):
        name = name.strip()
        if not name or not g:
            excluded["no sex in any source" if not g else "no name"] += 1
            return
        k = fold(name)
        e = entries.setdefault(k, dict(name=name, gs=set(), layers=[], culture=culture, language=language, srcs=[], meaning="",
                                       fa="", texts=[], religions=set(), modern=False, ancient=None))
        e["gs"].add(g)
        e["layers"].append(layer)
        e["srcs"].append(sentence(src))
        if meaning and fold(meaning) != fold(name) and not re.fullmatch(r"[A-Z][a-z]+", meaning):
            e["meaning"] = e["meaning"] or meaning
        e["fa"] = e["fa"] or fa
        e["texts"] += [t for t in texts if t not in e["texts"]]
        if religions:
            e["religions"].add(religions)
        e["modern"] = e["modern"] or modern
        e["ancient"] = e["ancient"] or ancient

    # 1. New Persian given names (Wiktionary)
    for r in fa_rows:
        if r["kind"] in ("arabic",) or (r["kind"] != "iranian" and "ar" in r["chain"]):
            excluded["Arabic origin (Persian given name from Arabic)"] += 1
            continue
        if r["kind"] not in ("iranian", "word", "mixed"):
            excluded[{"foreign": "other foreign origin (Turkic, Greek, European, Indic, Aramaic …)",
                      "other-iranian": "Kurdish, Mazanderani or another living Iranian language, not Persian",
                      "unknown": "Persian given name whose entry states no origin"}[r["kind"]]] += 1
            continue
        latin = r["latin"]
        if not latin or not re.fullmatch(r"[A-Za-z' -]+", latin):
            excluded["no Latin spelling in the entry"] += 1
            continue
        sec = r["sec"]
        stage, form = iranian_form(etymology(sec, "fa")[2])
        if r["kind"] == "mixed":
            src = "Arabic + Persian elements: a compound of an Arabic and a Persian word (Wiktionary); not a Persian-origin name"
        elif r["kind"] == "word":
            src = "A Persian word used as a name; Wiktionary gives no older source and no foreign one"
        elif stage and form:
            src = f"A Persian name from {stage} {form}" + (", which reached Persian through Arabic" if r["via_arabic"] else "") + " (Wiktionary)"
        else:
            src = f"A Persian name from {r['stage'] or 'an older Iranian language'} (Wiktionary)"
        who = person(latin, r["native"])
        if who:
            src = f"Used in ancient Iran: {who[0]}. " + src
        add(latin, "persian", r["sex"], "Persian", "Persian", src + f". Written {r['native']}", meaning_of(sec), r["native"],
            modern=True, ancient=bool(who))

    # 2. Old Persian, Middle Persian, Parthian, Avestan and Bactrian given names (Wiktionary)
    for r in anc:
        who = person(r["name"], r["fa"])
        desc = r["desc"] or "a given name"
        lead = f"Used in ancient Iran: {who[0]}" if who else f"Used in ancient Iran: {desc}"
        src = f"{lead}. {r['language']} {r['form']} (Wiktionary)"
        if r["disputed"]:
            src += "; origin disputed (Wiktionary names an Elamite theory)"
        fa = r["fa"] or (who[3] if who else "")
        if fa:
            src += f". Written {fa}"
        add(r["name"], r["code"], r["g"] or (who[1] if who else ""), r["culture"], r["language"], src, r["meaning"], r["fa"],
            religions="Zoroastrian" if r["code"] == "ae" else "", ancient=True)

    # 3. English spellings that Wiktionary traces to an Iranian language (Cyrus, Roxana, Xerxes)
    for r in eng:
        who = person(r["name"])
        lead = f"Used in ancient Iran: {who[0]}. " if who else ""
        src = lead + (f"The English form of {r['stage']} {r['form']}" if r["form"] else f"The English form of a {r['stage']} name") + " (Wiktionary)"
        if who and who[3]:
            src += f". Written {who[3]}"
        add(r["name"], "english", r["g"], "Persian" if r["stage"] in ("Old Persian", "Middle Persian") else "Iranian",
            r["stage"], src, r["meaning"], ancient=bool(who))

    # 4. Avesta: the Fravardin Yasht catalogue
    for r in yt:
        form = f" (Avestan text: {r['form']})" if r["form"] else ""
        src = (f"Used in ancient Iran: a faithful {'woman' if r['g'] == 'g' else 'man'}{r['who']}, honoured in the Avesta's "
               f"Fravardin Yasht, Yasht 13.{r['verse']}{form}; Darmesteter's translation")
        add(r["name"], "avesta", r["g"], "Iranian", "Avestan", src, texts=["Avesta"], religions="Zoroastrian", ancient=True)

    # 5. Shahnameh: the world build's rows, then Wikidata's characters found in the text
    done = set()
    for w in world:
        if w.get("corpus") != "Shahnameh" or w.get("entity_type") not in ("human", "royal"):
            continue
        review = "review" in w.get("relation", "")
        fa = w["original"]
        fr = fa_by.get(FA_NORM(fa))
        if fr and fr["kind"] in ("arabic", "foreign", "other-iranian"):
            excluded[f"Shahnameh name of {fr['kind']} origin"] += 1
            continue
        sex = {"boy": "b", "girl": "g"}.get(w["sex"], "") or (fr["sex"] if fr else "")
        fig = w["figure"].split(", ", 1)[1] if ", " in w["figure"] else ""
        if not sex:
            continue
        # a name the world build flagged (also a common word) is cited without its first passage, which may be the word
        cite = "" if review else f"; first in {w['passage']}"
        src = f"In Ferdowsi's Shahnameh ({w['name']}{', ' + fig if fig else ''}{cite}). Written {fa}"
        done.add(fold(w["name"]))
        add(w["name"], "shahnameh", sex, "Persian", "Persian", src, fa=fa, texts=["Shahnameh"], modern=bool(fr))
    for r in shah:
        en, fa, desc = r.get("en", ""), r.get("fa", ""), r.get("desc", "")
        sex = SEX.get(r.get("sex", "").rsplit("/", 1)[-1], "")
        if not (en and fa and sex) or re.search(r"\bArab|Roman|Rumi|Byzantine|Greek|Chinese|Indian\b", desc):
            if desc and re.search(r"\bArab", desc):
                excluded["Shahnameh name of Arabic origin"] += 1
            continue
        en = re.sub(r"\s*\(.*\)", "", en).strip()
        if fold(en) in done or len(en.split()) > 2:
            continue
        form = fa.split()[0] if len(fa.split()) > 2 else fa
        first, n = find_in_text(segs, form)
        if not first and form != fa.split()[0]:
            form = fa.split()[0]
            first, n = find_in_text(segs, form)
        if not first:
            excluded["Shahnameh character not found in ganjoor's text"] += 1
            continue
        fr = fa_by.get(FA_NORM(form))
        if fr and fr["kind"] in ("arabic", "foreign", "other-iranian"):
            excluded[f"Shahnameh name of {fr['kind']} origin"] += 1
            continue
        done.add(fold(en))
        src = f"In Ferdowsi's Shahnameh ({en}{', ' + desc if desc else ''}; first in {first[0]}). Written {form}"
        add(en, "shahnameh", sex, "Persian", "Persian", src, fa=form, texts=["Shahnameh"], modern=bool(fr))

    # rows
    rows = []
    for k, e in entries.items():
        g = "e" if len(e["gs"]) > 1 or "e" in e["gs"] else next(iter(e["gs"]))
        srcs = list(dict.fromkeys(e["srcs"]))
        anc_s = [s for s in srcs if s.startswith("Used in ancient Iran")]
        other = [s for s in srcs if not s.startswith("Used in ancient Iran")]
        src = " ".join(anc_s[:1] + other)
        written = re.findall(r" ?Written ([^\s.]+)\.", src)
        src = re.sub(r" ?Written [^\s.]+\.", "", src).strip()
        fa = (e["fa"] or (written[0] if written else "")).rstrip("\u0654")
        if fa:
            src += f" Written {fa}."
        if len(src) > 600:
            src = src[:597].rsplit(" ", 1)[0] + "…"
        modern = e["modern"] or fold(e["name"]) in anywhere
        ease = ease_of(e["name"], modern, en_names)
        rows.append(dict(row=[e["name"], g, e["culture"], e["language"], ",".join(sorted(e["religions"])), e["meaning"], src,
                              ",".join(e["texts"]), "real", [], ease], layers=sorted(set(e["layers"])),
                         new=k not in anywhere and k not in storied))
    rows.sort(key=lambda x: (x["row"][10], fold(x["row"][0])))
    js = [x["row"] for x in rows if x["row"][10] <= 2]
    json.dump(js, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    with open(OUT.replace(".json", ".tsv"), "w", encoding="utf-8") as f:
        f.write("name\tsex\tease\tculture\tlanguage\treligions\tmeaning\tlayers\tnew_to_site\ttexts\tsource\n")
        for x in rows:
            r = x["row"]
            f.write("\t".join(str(v) for v in (r[0], r[1], r[10], r[2], r[3], r[4], r[5], ",".join(x["layers"]), int(x["new"]), r[7], r[6])) + "\n")
    sacred_rows = sacred(yt, world)
    report = {"rows": len(rows), "json_rows": len(js), "ease": collections.Counter(x["row"][10] for x in rows),
              "json_ease": collections.Counter(r[10] for r in js),
              "layers": collections.Counter(l for x in rows for l in x["layers"]),
              "new_to_site": sum(x["new"] for x in rows), "new_in_json": sum(x["new"] for x in rows if x["row"][10] <= 2),
              "excluded": excluded, "persian_wiktionary": fa_stats, "ancient_wiktionary": anc_stats, "sacred_rows": sacred_rows}
    print(json.dumps(report, ensure_ascii=False, indent=1, default=dict))


# ----------------------------------------------------------------------------------------------- data/sacred/persian.tsv
COLS = ("name figure_id figure sex original translit language tradition subtradition corpus text passage url occurrences "
        "entity_type name_role status relation source confidence").split()
AVESTA_SRC = ("avesta.org (J. H. Peterson's digital edition): Avestan text after Geldner 1896 and Darmesteter's translation "
              "(SBE 23, 1883); both public domain")


def denkard():
    """Denkard Book 7 (West, SBE 47, 1897; PD), matched with the world build's Middle Persian name list."""
    p = get("https://www.avesta.org/denkard/dk7.html", "avesta/denkard_dk7.html")
    if not p:
        return []
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import build_sacred_world as W
    t = re.sub(r"(?is)<(script|style|head).*?</\1>", "", read(p, "latin-1"))
    url = "https://www.avesta.org/denkard/dk7.html"
    segs, ch = [], None
    for blk in re.split(r"(?i)(<h3[^>]*>.*?</h3>)", t):
        m = re.match(r"(?i)<h3[^>]*>\s*CHAPTER\s+(\d+)", blk)
        if m:
            ch = m.group(1)
            continue
        if not ch:
            continue
        verse = "0"
        for piece in re.split(r"(?m)^\s*(\d{1,3})\.\s*$|(?<=[.!?'\"])\s+(\d{1,3})\.\s", strip_tags(blk)):
            if piece is None:
                continue
            if re.fullmatch(r"\d{1,3}", piece.strip()):
                verse = piece.strip()
                continue
            s = " ".join(piece.split())
            if s:
                segs.append(W.Seg("Denkard, Book 7", f"Denkard 7.{ch}.{verse}", url, s, is_original=False))
    cfg = W.C("Denkard", "Zoroastrian", "eng", "Middle Persian", None, W.PAHLAVI,
              "avesta.org, E. W. West's translation of Denkard Book 7 (SBE 47, 1897; PD), spellings as edited by J. H. Peterson",
              original=False)
    wd = W.wikidata(sorted({f["title"] for f in W.parse(W.PAHLAVI)}))
    rows, review, _missing = W.match_corpus(cfg, segs, wd, [])
    return rows + review


def sacred(yt, world):
    rows = [w for w in world if w.get("tradition") == "Zoroastrian"]
    have = {(r["corpus"], fold(r["name"])) for r in rows}
    ids = {fold(r["name"]): r["figure_id"] for r in rows}
    seen = set()
    for r in yt:
        k = ("Avesta", fold(r["name"]))
        if k in have or k in seen:
            continue
        seen.add(k)
        who = "faithful woman" if r["g"] == "g" else "faithful man"
        rows.append(dict(name=r["name"], figure_id=ids.get(fold(r["name"]), f"slug:zoroastrian:{re.sub(r'[^a-z0-9]+', '-', r['name'].lower())}"),
                         figure=f"{r['name']}, {who}{r['who']} in the Fravardin Yasht", sex="girl" if r["g"] == "g" else "boy",
                         original=r["form"], translit=r["name"], language="Avestan", tradition="Zoroastrian", subtradition="",
                         corpus="Avesta", text="Yashts", passage=f"Yasht 13.{r['verse']}", url="https://www.avesta.org/ka/yt13sbe.htm",
                         occurrences="", entity_type="human", name_role="personal", status="attested", relation="",
                         source=AVESTA_SRC, confidence=0.9 if r["form"] else 0.8))
    try:
        dk = denkard()
    except Exception as e:  # noqa  (the world build's module is optional)
        print(f"  Denkard skipped: {e}", file=sys.stderr)
        dk = []
    rows += [r for r in dk if ("Denkard", fold(r["name"])) not in have]
    os.makedirs(os.path.dirname(OUT_SACRED), exist_ok=True)
    with open(OUT_SACRED, "w", encoding="utf-8") as f:
        f.write("\t".join(COLS) + "\n")
        for r in rows:
            f.write("\t".join(str(r.get(c, "")).replace("\t", " ").replace("\n", " ") for c in COLS) + "\n")
    return collections.Counter(r["corpus"] for r in rows)


if __name__ == "__main__":
    main()
