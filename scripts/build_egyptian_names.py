"""Ancient Egyptian personal names -> data/egyptian-names.json (+ deities and figures of the Book of the Dead ->
data/sacred/egyptian.tsv).

Row format is that of data/culture-names.json plus an 11th slot:
    [name, g, culture, language, religions, meaning, src, texts, kind, also, ease]
ease 1 = spelled and said easily in modern English (Tiye, Ahmose, Nefertari), 2 = fine with a second look
(Hatshepsut, Senenmut), 3 = hard (Djedefre, Khentkaus). Rows are sorted by ease, then name.

Strictly pre-Arabic: every name is attested before the Arab conquest (641 CE). Greek names borne in Ptolemaic Egypt
(Cleopatra, Berenice, Arsinoe, Ptolemy) are kept with culture "Greek" and the note "Greek name used in Ptolemaic
Egypt"; they are never given Egyptian origin. Deities are kept with kind "deity" and a source sentence that says they
are a god's or goddess's name, not a person's.

Sources (all open):
  PNM   Persons and Names of the Middle Kingdom and Early New Kingdom, version 6 (A. Ilin-Tomich, Mainz 2025),
        Zenodo doi:10.5281/zenodo.1411391, CC BY 4.0. Transliteration, sex of the bearers, period, English translation.
  TLA   Thesaurus Linguae Aegyptiae (BBAW), corpus v18/v19 "premium" sentence sets on Hugging Face, CC BY-SA 4.0:
        lemma transliterations of personal names (PERSN) with the dates of the text witnesses.
  WD    Wikidata (CC0): ancient Egyptian people (label, sex, dynasty), deities (label, sex), and the Egyptian lexemes the
        TLA bot uploaded (TLA lemma IDs, transliterations, glosses of royal and divine names).
  Wikt  English Wiktionary (CC BY-SA 4.0), via data/meanings.json or the entry: Greek origin and meaning of Ptolemaic
        names whose Wikidata given-name item does not give Greek (Berenice, Arsinoe).
  Budge E. A. Wallis Budge, The Book of the Dead: an English translation of the chapters ... (1898, PD),
        archive.org OCR (cached by build_sacred_world.py in raw/sacred/world/archive/) for the deity citations.
Not used: AGÉA (IFAO; no licence stated, search interface only), Trismegistos People and LGPN (no open download),
Ranke, Die ägyptischen Personennamen (1935; PD in Germany since 2024 but not in the US until 2031; only the PNM's
Ranke numbers are cited), sacred-texts.com (Cloudflare challenge), the TLA website (bot-verification wall).

The display form is the person's conventional English name as Wikidata labels it (Nefertiti, Senenmut). It is linked to
a transliteration when the Egyptological rendering of a PNM/TLA reading (render()) has the same consonants and is
clearly the closest (Senenmut = sn-n-mw.t); otherwise the row says no transliteration was found. A person's row needs
such a link (evidence the name is Egyptian), except the must-check names. Vowels in
Egyptian names are a modern convention: the script records only consonants, so every source sentence says so.
Meanings are only the PNM's English translation of the same transliteration. Sex is the person's (Wikidata P21) or
what the PNM records for the name's bearers; nothing is guessed.

    python3 scripts/build_egyptian_names.py            (downloads into raw/egyptian/ once; delete a file to refetch)
"""
import collections, gzip, json, os, re, sqlite3, sys, time, unicodedata, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "raw", "egyptian")
OUT = os.path.join(ROOT, "data", "egyptian-names.json")
SACRED = os.path.join(ROOT, "data", "sacred", "egyptian.tsv")
UA = {"User-Agent": "Lullabyte-build/1.0 (https://github.com/suhxnitiwari/baby-name-maker)"}
VOWELS = "Vowels are a modern Egyptological convention (hieroglyphs write consonants only)"


# ------------------------------------------------------------------------------------------------ fetching
def get(url, name, binary=True):
    p = os.path.join(RAW, name)
    if os.path.exists(p) and os.path.getsize(p) > 0:
        return p
    os.makedirs(os.path.dirname(p), exist_ok=True)
    for attempt in range(2 if "wiktionary" in url else 5):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=600).read()
            break
        except Exception as e:
            print("  retry", url[:80], e, file=sys.stderr); time.sleep(5 * (attempt + 1))
    else:
        raise RuntimeError("kept failing: " + url)
    open(p, "wb").write(data)
    return p


def sparql(q, name):
    return json.load(open(get("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"}), name)))["results"]["bindings"]


def entities(qids, prefix):
    out = {}
    qids = sorted(set(qids), key=lambda q: int(q[1:]))
    for i in range(0, len(qids), 50):
        chunk = qids[i:i + 50]
        p = get("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
            {"action": "wbgetentities", "ids": "|".join(chunk), "props": "labels|aliases|descriptions|claims|sitelinks",
             "languages": "en|de", "format": "json"}), f"wd/{prefix}-{chunk[0]}-{len(chunk)}.json")
        out.update(json.load(open(p))["entities"])
    return out


def claims(e, prop):
    out = []
    for c in e.get("claims", {}).get(prop, []):
        v = c.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(v, dict) and "id" in v: out.append(v["id"])
        elif isinstance(v, dict) and "time" in v: out.append(v["time"])
        elif v is not None: out.append(v)
    return out


# ------------------------------------------------------------------------------------------------ PNM
PNM_SQL = "pnm-v6.sql"
PNM_URL = "https://zenodo.org/api/records/15806808/files/Persons%20and%20Names%20of%20the%20Middle%20Kingdom%20Ver%206%202025-07-04.sql/content"


def parse_values(body):
    rows, i, n = [], 0, len(body)
    while i < n:
        if body[i] != "(":
            i += 1; continue
        i += 1; row = []
        while True:
            while body[i] in " \t\r\n": i += 1
            if body[i] == "'":
                i += 1; buf = []
                while True:
                    ch = body[i]
                    if ch == "\\":
                        buf.append({"n": "\n", "r": "\r", "t": "\t", "0": "\0"}.get(body[i + 1], body[i + 1])); i += 2
                    elif ch == "'":
                        if body[i + 1] == "'": buf.append("'"); i += 2
                        else: i += 1; break
                    else: buf.append(ch); i += 1
                row.append("".join(buf))
            else:
                j = i
                while body[j] not in ",)": j += 1
                tok = body[i:j].strip(); i = j
                row.append(None if tok == "NULL" else (int(tok) if re.fullmatch(r"-?\d+", tok) else tok))
            while body[i] in " \t\r\n": i += 1
            if body[i] == ",": i += 1; continue
            if body[i] == ")": i += 1; break
        rows.append(row)
    return rows


def pnm():
    db = os.path.join(RAW, "pnm-v6.sqlite")
    if not os.path.exists(db):
        sql = open(get(PNM_URL, PNM_SQL), encoding="utf-8").read()
        con = sqlite3.connect(db + ".tmp")
        for t in ("personal_names", "name_types", "names_types_xref", "spellings", "spellings_attestations_xref", "attestations", "inscriptions"):
            cols = None
            for m in re.finditer(r"INSERT INTO `%s` \((.*?)\) VALUES\n(.*?)\);\n" % t, sql, re.S):
                cs = [c.strip("` ") for c in m.group(1).split(",")]
                if cols is None:
                    cols = cs; con.execute("CREATE TABLE %s (%s)" % (t, ",".join('"%s"' % c for c in cols)))
                con.executemany("INSERT INTO %s VALUES (%s)" % (t, ",".join("?" * len(cols))), parse_values(m.group(2) + ")"))
        con.commit(); con.close(); os.rename(db + ".tmp", db)
    con = sqlite3.connect(db)
    foreign = {r[0]: r[1] for r in con.execute(
        "select x.personal_names_id, t.title from names_types_xref x join name_types t on t.name_types_id=x.name_types_id "
        "where t.title in ('foreign name','Western Asian name')")}
    dyn = collections.defaultdict(set)
    for pid, a, b in con.execute(
            "select s.personal_names_id, i.dating_sort_start, i.dating_sort_end from spellings s "
            "join spellings_attestations_xref x on x.spellings_id=s.spellings_id join attestations a on a.attestations_id=x.attestations_id "
            "join inscriptions i on i.inscriptions_id=a.inscriptions_id where i.dating_sort_start is not null"):
        if a: dyn[pid].add(int(str(a)[:2]))
        if b: dyn[pid].add(int(str(b)[:2]))
    out = []
    for pid, tr, en, g, ranke, tla, period in con.execute(
            "select personal_names_id, personal_name, translation_en, gender, ranke, tla, usage_period from personal_names"):
        if not tr or g not in ("m", "f", "both"): continue
        out.append({"id": pid, "tr": tr, "en": en or "", "g": {"m": "b", "f": "g", "both": "e"}[g], "ranke": ranke or "",
                    "tla": [t.strip() for t in (tla or "").split(";") if t.strip()], "period": period or "",
                    "dyn": sorted(d for d in dyn[pid] if 11 <= d <= 18), "foreign": foreign.get(pid, "")})
    return out


# ------------------------------------------------------------------------------------------------ TLA
TLA = {"tla-Earlier_Egyptian_original-v18-premium": "Earlier Egyptian", "tla-late_egyptian-v19-premium": "Late Egyptian"}


def tla():
    lem = {}
    for ds in TLA:
        p = get(f"https://huggingface.co/datasets/thesaurus-linguae-aegyptiae/{ds}/resolve/main/train.jsonl", ds + ".jsonl")
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            for a, b in zip(r["lemmatization"].split(" "), r["glossing"].split(" ")):
                if b != "PERSN" or "|" not in a: continue
                i, t = a.split("|", 1)
                e = lem.setdefault(i, {"tr": t, "years": []})
                for k in ("dateNotBefore", "dateNotAfter"):
                    if re.fullmatch(r"-?\d+", r.get(k) or ""): e["years"].append(int(r[k]))
    return lem


# ------------------------------------------------------------------------------------------------ conventional rendering
# Used only to LINK a person's conventional English name to a transliteration in PNM/TLA (the name shown is always the
# source's label). Egyptological convention: weak consonants as vowels (ꜣ ꜥ -> a, j -> i, w -> u), e between consonants,
# and the usual fixed forms of common elements and theophoric names.
ELEM = {"ptḥ": "ptah", "sbk": "sobek", "jmn": "amen", "jmn.w": "amen", "ḥtp": "hotep", "ḥtp.w": "hotep", "ꜥnḫ": "ankh", "nḫt": "nakht",
        "rꜥ": "ra", "rꜥw": "ra", "rꜥ.w": "ra", "ḥr": "hor", "ḥr.w": "hor", "mnṯw": "mentu", "mnṯ.w": "mentu", "jꜥḥ": "ah", "ms": "mose", "ms.w": "mose",
        "wsr": "user", "mꜣꜥ.t": "maat", "mꜣꜥ": "maa", "ḥꜣ.t": "hat", "kꜣ": "ka", "bꜣ": "ba", "nṯr": "netjer", "ḫnsw": "khonsu", "ḫns.w": "khonsu",
        "jtm": "atum", "jtm.w": "atum", "nfr": "nefer", "nfr.w": "neferu", "ḏḥw.tj": "djehuti", "ḏḥwtj": "djehuti", "stẖ": "set", "ꜣs.t": "iset", "js.t": "iset"}
WHOLE = {"ḏḥw.tj-ms": "thutmose", "ḏḥwtj-ms": "thutmose", "ḏḥw.tj-ms.w": "thutmose", "jn-jtj⸗f": "intef", "jnj-jtj⸗f": "intef", "s-n-wsr.t": "senusret",
         "rꜥ-ms-sw": "ramesses", "rꜥw-ms-sw": "ramesses", "mnṯw-ḥtp": "mentuhotep", "mnṯ.w-ḥtp": "mentuhotep", "mnṯw-ḥtp.w": "mentuhotep",
         "stẖ.jj": "seti", "stẖ.j": "seti", "ḥw.t-ḥr": "hathor", "ḥw.t-ḥr.w": "hathor"}
CONS = {"b": "b", "p": "p", "f": "f", "m": "m", "n": "n", "r": "r", "h": "h", "ḥ": "h", "ḫ": "kh", "ẖ": "kh", "s": "s", "š": "sh", "q": "q",
        "k": "k", "g": "g", "t": "t", "ṯ": "tj", "d": "d", "ḏ": "dj", "l": "l"}


def tr_norm(t):
    t = unicodedata.normalize("NFC", t.lower()).replace("ẖ", "ẖ")
    t = t.replace("i̯", "j").replace("ꞽ", "j").replace("ï", "j").replace("y", "jj").replace("z", "s").replace("=", "⸗").replace("+", "-")
    return re.sub(r"\s*\(\?\)|ʾ", "", t)


def render(t):
    t = tr_norm(t)
    t = re.sub(r"\([^)]*\)", "", t)
    if t in WHOLE: return WHOLE[t]
    out, els = [], t.split("-")
    for k, el in enumerate(els):
        if el in ELEM: out.append(ELEM[el]); continue
        parts = re.split(r"[.⸗]", el)
        s = ELEM.get(parts[0]) or generic(parts[0], first=not out, prev=out[-1][-1:] if out else "")
        for sfx in parts[1:]:
            if not sfx: continue
            if sfx == "t":
                nxt = els[k + 1][:1] if k + 1 < len(els) else ""
                s += "t" if s[-1:] in "aeiou" or nxt in ("j", "ꜣ", "ꜥ") else "et"
                continue
            g = generic(sfx, first=False, prev=s[-1:])
            s += "e" + g if g[:1] not in "aeiou" and s[-1:] not in "aeiou" else g
        out.append(s)
    return re.sub(r"([aiu])\1+", r"\1", "".join(out))


def generic(c, first=True, prev=""):
    if c in ("m", "n") and not first: return c if prev in ("i",) else "e" + c
    ph = []
    for i, ch in enumerate(c):
        if ch in "ꜣꜥ": ph.append(("a", 1))
        elif ch == "j": ph.append(("i", 1))
        elif ch == "w":
            nxt = c[i + 1] if i + 1 < len(c) else ""
            ph.append(("w", 0) if nxt and nxt in "ꜣꜥj" else ("u", 1))
        elif ch in CONS: ph.append((CONS[ch], 0))
    s = ""
    for i, (p, v) in enumerate(ph):
        if i and not v and not ph[i - 1][1]: s += "e"
        s += p
    if len(ph) == 1 and not ph[0][1]: s = "e" + s if not first else s
    return s


# ------------------------------------------------------------------------------------------------ helpers
def display(label):
    """The personal name in a Wikidata label: 'Meresankh III' -> Meresankh, 'Nakht (scribe)' -> Nakht."""
    n = re.sub(r"\s*\(.*?\)", "", label).split(",")[0].strip()
    n = re.sub(r"\s+(?:[IVX]+|[A-H]|the (?:Elder|Younger)|Senior|Junior)$", "", n).strip()
    n = re.sub(r"\s+(?:[IVX]+|[A-H])$", "", n).strip()
    return n if re.fullmatch(r"[A-Z][a-z]+(?:-[A-Z]?[a-z]+)*", n) else ""


NOT_A_NAME = {"Scorpion"}   # Wikidata labels that translate the name into English


def link(name, sex, by_first):
    """Best transliteration for a conventional name: rendering similarity >= 0.85, clearly ahead of any different reading;
    PNM names must be recorded for the same sex (or both)."""
    import difflib
    key = name.lower().replace("-", "")
    scored = []
    for rd, src, d in by_first.get(key[0], []):
        if abs(len(rd) - len(key)) > 3 or (src == "PNM" and d["g"] not in (sex, "e")): continue
        if re.sub(r"[aeiouyw]", "", rd) != re.sub(r"[aeiouyw]", "", key): continue
        sc = difflib.SequenceMatcher(None, key, rd).ratio()
        if sc >= 0.8: scored.append((sc, src == "PNM", bool(d.get("en")), rd, src, d))
    if not scored: return None
    scored.sort(key=lambda x: x[:3], reverse=True)
    best = scored[0]
    if best[0] < 0.85: return None
    rivals = [x for x in scored[1:] if x[3] != best[3] and x[0] > best[0] - 0.04]
    same = [x for x in scored[1:] if x[3] == best[3] and x[4] == "PNM" and best[4] == "PNM" and x[5]["en"] and x[5]["en"] != best[5]["en"]]
    if rivals or same: return None
    return best[4], best[5]


def ease(n):
    s = n.lower().replace("-", "")
    hard = len(re.findall(r"kh|dj|tj|q|[^aeiouy]{3}|aa|ii|uu", s))
    if len(s) <= 7 and not hard and not re.search(r"[^aeiouy]{2}$", s): return 1
    if len(s) <= 10 and hard <= 1: return 2
    return 3


def period_of_dyn(d):
    return ("Early Dynastic Period" if d <= 2 else "Old Kingdom" if d <= 6 else "First Intermediate Period" if d <= 10 else
            "Middle Kingdom" if d <= 12 else "Second Intermediate Period" if d <= 17 else "New Kingdom" if d <= 20 else
            "Third Intermediate Period" if d <= 25 else "Late Period" if d <= 31 else "Ptolemaic Period")


def period_of_year(y):
    return ("Early Dynastic Period" if y < -2686 else "Old Kingdom" if y < -2181 else "First Intermediate Period" if y < -2055 else
            "Middle Kingdom" if y < -1650 else "Second Intermediate Period" if y < -1550 else "New Kingdom" if y < -1069 else
            "Third Intermediate Period" if y < -664 else "Late Period" if y < -332 else "Ptolemaic Period" if y < -30 else "Roman Period")


ORD = {w: i for i, w in enumerate("Zeroth First Second Third Fourth Fifth Sixth Seventh Eighth Ninth Tenth Eleventh Twelfth Thirteenth "
                                  "Fourteenth Fifteenth Sixteenth Seventeenth Eighteenth Nineteenth Twentieth".split())}
ORD.update({"Twenty-first": 21, "Twenty-second": 22, "Twenty-third": 23, "Twenty-fourth": 24, "Twenty-fifth": 25, "Twenty-sixth": 26,
            "Twenty-seventh": 27, "Twenty-eighth": 28, "Twenty-ninth": 29, "Thirtieth": 30, "Thirty-first": 31})
FOREIGN_DYN = {15: "Hyksos (Western Asian)", 22: "Libyan", 23: "Libyan", 24: "Libyan", 25: "Kushite (Nubian)", 27: "Persian", 31: "Persian"}
STATES = "Q11768 Q187979 Q177819 Q232211 Q191324 Q206715 Q180568 Q212728 Q621917 Q2320005 Q202311 Q17302295 Q1484140 Q714601 Q926624".split()


# ------------------------------------------------------------------------------------------------ people
def people():
    q = ("SELECT DISTINCT ?x WHERE { VALUES ?cls { wd:Q5 wd:Q3658341 } ?x wdt:P31 ?cls . VALUES ?st { %s } "
         "{ ?x wdt:P27 ?st } UNION { ?x wdt:P2348 ?st } UNION { ?x wdt:P53 ?d . ?d wdt:P31 wd:Q11876947 } "
         "UNION { ?x wdt:P2348 ?d2 . ?d2 wdt:P31 wd:Q11876947 } UNION { ?x wdt:P39 ?pos . VALUES ?pos { wd:Q37110 wd:Q1073256 wd:Q14942945 } } }"
         % " ".join("wd:" + s for s in STATES))
    ids = [b["x"]["value"].rsplit("/", 1)[1] for b in sparql(q, "wd-candidates.json")]
    ents = entities(ids, "person")
    refs = set()
    for e in ents.values():
        for p in ("P53", "P2348", "P27", "P735", "P39"): refs.update(claims(e, p))
    labels = entities([r for r in refs if re.fullmatch(r"Q\d+", r)], "ref")
    return ents, labels


def lexemes():
    """Wikidata lexemes uploaded from the TLA: royal personal names ('personal name of several kings') and deity names."""
    q = ("SELECT ?l ?lemma ?cls ?tla ?item ?gloss WHERE { ?l dct:language wd:Q50868 ; wikibase:lemma ?lemma ; wdt:P31 ?cls . "
         "VALUES ?cls { wd:Q115642102 wd:Q115642037 } OPTIONAL { ?l wdt:P12188 ?tla } OPTIONAL { ?l ontolex:sense ?s . "
         "OPTIONAL { ?s wdt:P5137 ?item } OPTIONAL { ?s skos:definition ?gloss } } }")
    out = collections.defaultdict(lambda: {"lemma": "", "cls": "", "tla": "", "items": set(), "gloss": set()})
    for b in sparql(q, "wd-lexemes.json"):
        e = out[b["l"]["value"].rsplit("/", 1)[1]]
        if not re.search(r"[\U00013000-\U0001342F]", b["lemma"]["value"]): e["lemma"] = b["lemma"]["value"]
        e["cls"] = "royal" if b["cls"]["value"].endswith("Q115642102") else "deity"
        if "tla" in b: e["tla"] = b["tla"]["value"]
        if "item" in b: e["items"].add(b["item"]["value"].rsplit("/", 1)[1])
        if "gloss" in b: e["gloss"].add(b["gloss"]["value"])
    return out


# ------------------------------------------------------------------------------------------------ build
def build():
    names = pnm()
    lem = tla()
    lex = lexemes()
    ents, refs = people()
    lab = lambda q: refs.get(q, {}).get("labels", {}).get("en", {}).get("value", "")

    # transliterations to link to: PNM names (not foreign-typed), TLA personal-name lemmas, royal personal-name lexemes
    by_first = collections.defaultdict(list)
    def add(src, d):
        rd = render(d["tr"])
        if rd: by_first[rd[0]].append((rd, src, d))
    for n in names:
        if not n["foreign"]: add("PNM", n)
    pnm_tla = {t for n in names for t in n["tla"]}
    for i, e in lem.items():
        if i not in pnm_tla: add("TLA", dict(e, id=i))
    for lid, e in lex.items():
        gl = " ".join(e["gloss"])
        if e["cls"] == "royal" and e["lemma"] and re.search(r"personal name|Eigenname", gl) and not re.search(r"Horus|throne|Thron|Nebty|Nebti|Gold", gl):
            add("TLA-royal", dict(e, lid=lid, tr=e["lemma"]))

    # royal title names (Horus, Nebty, Gold Horus, throne names) as rendered from the TLA lexemes on Wikidata
    title_names = {}
    for lid, e in lex.items():
        gl = " ".join(e["gloss"])
        if e["cls"] == "royal" and e["lemma"] and not re.search(r"personal name|Eigenname", gl):
            kind = ("a king's Horus name, i.e. a royal title name, not a birth name" if re.search(r"Horus", gl) else
                    "a king's throne name, i.e. a royal title name, not a birth name" if re.search(r"hron", gl) else
                    "a king's Nebty or Gold name, i.e. a royal title name" if re.search(r"Neb|Gold", gl) else
                    "a royal name in the TLA, which does not say whether it is a birth name or a title name")
            title_names.setdefault(render(e["lemma"]), (kind, e["lemma"], e["tla"], lid))
    rows, seen, skipped = {}, set(), collections.Counter()
    # Greek given names: the person's given name (P735) is a Wikidata given-name item whose language (P407) is Greek,
    # Ancient Greek or Koine Greek, and that item's name is the person's name (Kleopatra/Cleopatra, Ptolemaios/Ptolemy)
    sys.path.insert(0, HERE)
    from build_cultures import greek as greek_latin
    def gn_forms(g):
        r = refs.get(g, {})
        fs = [v["value"] for v in r.get("labels", {}).values()] + [a["value"] for v in r.get("aliases", {}).values() for a in v]
        fs += [greek_latin(v["text"]) for v in claims(r, "P1705") if isinstance(v, dict)]
        return fs
    stem = lambda x: unicodedata.normalize("NFD", x.lower()).replace("k", "c")[:4]
    MEAN = json.load(open(os.path.join(ROOT, "data", "meanings.json"), encoding="utf-8"))
    def wikt_greek(name):
        """Wiktionary (CC BY-SA 4.0) says the name comes from Ancient Greek: data/meanings.json, else the entry itself."""
        m = MEAN.get(name.lower()) or {}
        if m.get("root") == "Ancient Greek": return m.get("m", ""), True
        try:
            p = get("https://en.wiktionary.org/w/index.php?" + urllib.parse.urlencode({"title": name, "action": "raw"}), f"wikt/{name}.txt")
        except RuntimeError:
            open(os.path.join(RAW, f"wikt/{name}.txt"), "w").write("(no entry)"); return "", False
        t = open(p, encoding="utf-8").read()
        ety = re.search(r"(?s)===\s*Etymology[^=]*===(.*?)(?:\n==|$)", t)
        ok = bool(ety and re.search(r"\{\{(?:bor|der|inh)\+?\|en\|grc\||from Ancient Greek|\{\{bor\|la\|grc", ety.group(1)))
        return "", ok
    def is_greek(e, name):
        if any(re.search(r"Ptolem", lab(d)) for d in claims(e, "P53")) and wikt_greek(name)[1]: return True
        return any({"Q35497", "Q9129", "Q107358"} & set(claims(refs.get(g, {}), "P407")) and any(stem(f) == stem(name) for f in gn_forms(g))
                   for g in claims(e, "P735"))
    for q, e in ents.items():
        if "labels" not in e: continue
        label = e["labels"].get("en", {}).get("value", "")
        name = display(label)
        if not name: skipped["label not a single name"] += 1; continue
        sex = {"Q6581097": "b", "Q6581072": "g"}.get((claims(e, "P21") or [""])[0], "")
        if not sex: skipped["no sex on Wikidata"] += 1; continue
        dyns = sorted({ORD[m.group(1)] for d in claims(e, "P53") + claims(e, "P2348")
                       for m in [re.match(r"(\S+) Dynasty of Egypt", lab(d))] if m and m.group(1) in ORD})
        sts = [lab(s) for s in claims(e, "P27") + claims(e, "P2348") if s in STATES]
        ptol = any(re.search(r"Ptolem", lab(d)) for d in claims(e, "P53")) or "Ptolemaic Kingdom" in sts
        years = [int(t[:5].replace("+", "")) for p in ("P569", "P570", "P1317") for t in claims(e, p) if isinstance(t, str) and re.match(r"[+-]\d{4}", t)]
        roman = any(s in ("Roman Egypt", "Byzantine Egypt") for s in sts) or any(y >= -30 for y in years)
        if "Q389688" in claims(e, "P27"): skipped["Achaemenid (Persian) ruler"] += 1; continue
        # Greek names: Ptolemaic dynasty, or a given name (P735) Wikidata ties to (Ancient/Koine) Greek
        greek_gn = is_greek(e, name)
        if roman and not ptol:
            skipped["Roman or Byzantine period"] += 1; continue
        if ptol:
            if not greek_gn:
                skipped["Ptolemaic/Roman, language of the name not recorded"] += 1; continue
            key = (name, "Greek")
            r = rows.setdefault(key, {"name": name, "culture": "Greek", "language": "Greek", "g": set(), "bearers": [], "tr": None,
                                      "period": "Ptolemaic Period" if ptol else "Roman Period", "dyn": [], "meaning": "", "kind": "real"})
            r["g"].add(sex); r["bearers"].append((len(e.get("sitelinks", {})), label, e.get("descriptions", {}).get("en", {}).get("value", ""), q, [], r["period"]))
            if not r["meaning"]:
                try: r["meaning"] = wikt_greek(name)[0]
                except Exception: pass
            continue
        if any(d in FOREIGN_DYN for d in dyns) and not any(d not in FOREIGN_DYN for d in dyns):
            skipped["ruler or family of a foreign dynasty (%s)" % FOREIGN_DYN[dyns[0]]] += 1; continue
        # transliteration: the candidate whose conventional rendering is closest to the name (see render())
        tr, meaning, trsrc = None, "", ""
        if name in NOT_A_NAME: skipped["label is an English translation"] += 1; continue
        c = link(name, sex, by_first)
        import difflib
        key = name.lower().replace("-", "")
        tn = title_names.get(key) or next((v for k, v in title_names.items() if k[:1] == key[:1] and re.sub(r"[aeiouyw]", "", k) == re.sub(r"[aeiouyw]", "", key)
                                           and difflib.SequenceMatcher(None, k, key).ratio() >= 0.85), None)
        if tn and not c and set(claims(e, "P39")) & {"Q37110"}:
            c = None
            tr, trsrc = tn[1], "TLA lemma %s (via Wikidata lexeme %s); %s" % (tn[2], tn[3], tn[0])
        linkd = c
        if c:
            src, d = c
            tr = d["tr"]
            if src == "PNM":
                trsrc = "PNM name %s%s" % (d["id"], ", Ranke PN " + d["ranke"].split(";")[0].strip() if d["ranke"] else "")
                meaning = "" if re.search(r"throne name|birth name|Horus name", d["en"]) else d["en"]
                if re.search(r"throne name", d["en"]): trsrc += "; PNM notes it is a king's throne name used as a personal name"
            elif src == "TLA": trsrc = "TLA lemma %s" % d["id"]
            else: trsrc = "TLA lemma %s (via Wikidata lexeme %s)" % (d["tla"], d["lid"])
        if not dyns and not set(STATES[:9] + STATES[12:]) & set(claims(e, "P27") + claims(e, "P2348")) and not set(claims(e, "P39")) & {"Q37110", "Q1073256", "Q14942945"}:
            skipped["no dynasty or pharaonic-period state on Wikidata"] += 1; continue
        per = period_of_dyn(dyns[0]) if dyns else (sts[0] if sts and sts[0] != "Ancient Egypt" else "")
        key = (name, "Ancient Egyptian")
        r = rows.setdefault(key, {"name": name, "culture": "Ancient Egyptian", "language": "Egyptian", "g": set(), "bearers": [], "tr": None,
                                  "period": per, "dyn": [], "meaning": "", "kind": "real", "trsrc": ""})
        r["g"].add(sex); r["dyn"] = sorted(set(r["dyn"]) | set(dyns))
        if not r["period"]: r["period"] = per
        r["bearers"].append((len(e.get("sitelinks", {})), label, e.get("descriptions", {}).get("en", {}).get("value", ""), q, dyns, per))
        if tr and not r["tr"]:
            if trsrc.startswith("TLA lemma") and "Wikidata lexeme" not in trsrc and dyns and dyns[0] > 20:
                tr = None   # Late Period and later: TLA alone does not say whether a name is Egyptian or Libyan/Nubian
            else:
                r["tr"], r["meaning"], r["trsrc"], r["link"] = tr, meaning, trsrc, linkd

    # deities: Wikidata items of Egyptian deities (sex from P21), transliteration from the TLA deity lexemes
    q = ("SELECT DISTINCT ?x WHERE { VALUES ?c { wd:Q146083 } ?x wdt:P31 ?c . ?x wikibase:sitelinks ?n . FILTER(?n >= 15) }")
    dq = {b["x"]["value"].rsplit("/", 1)[1] for b in sparql(q, "wd-deities.json")}
    dq |= {it for e in lex.values() if e["cls"] == "deity" for it in e["items"]}      # the deities the TLA's divine-name lexemes point to (Horus, Seth...)
    deities = {k: v for k, v in entities(sorted(dq), "deity").items() if len(v.get("sitelinks", {})) >= 15}
    dlex = {}
    for lid, e in lex.items():
        if e["cls"] == "deity" and e["lemma"]:
            for it in e["items"]: dlex.setdefault(it, (e["lemma"], e["tla"], lid))
    for qd, e in deities.items():
        label = e.get("labels", {}).get("en", {}).get("value", "")
        name = display(label)
        sex = {"Q6581097": "b", "Q6581072": "g"}.get((claims(e, "P21") or [""])[0], "")
        if not name or not sex or (name, "deity") in rows or "Q5" in claims(e, "P31"): continue   # deified humans (Imhotep) stay people
        r = rows.setdefault((name, "deity"), {"name": name, "culture": "Ancient Egyptian", "language": "Egyptian", "g": {sex},
                                                          "bearers": [(len(e.get("sitelinks", {})), label, e.get("descriptions", {}).get("en", {}).get("value", ""), qd, [], "")],
                                                          "tr": None, "period": "", "dyn": [], "meaning": "", "kind": "deity", "trsrc": ""})
        if qd in dlex: r["tr"], r["trsrc"] = dlex[qd][0], "TLA lemma %s (via Wikidata lexeme %s)" % (dlex[qd][1], dlex[qd][2])
    return rows, skipped, deities


# ------------------------------------------------------------------------------------------------ Book of the Dead
BOTD = "bookdeadanengli01budggoog"   # Budge, The Book of the Dead: an English translation of the chapters ... (1898; PD)
BOTD_SRC = "E. A. Wallis Budge, The Book of the Dead: an English translation of the chapters, hymns, etc. of the Theban recension (1898; PD), archive.org OCR; Wikidata (CC0); TLA lemmas via Wikidata lexemes (CC0)"
ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}


def roman(r):
    n = 0
    for a, b in zip(r, r[1:] + " "):
        n += -ROMAN[a] if ROMAN.get(b, 0) > ROMAN[a] else ROMAN[a]
    return n


def botd_chapters():
    """[(chapter number, printed page, url, text)] cut at Budge's chapter headings (after his introduction)."""
    base = os.path.join(ROOT, "raw", "sacred", "world", "archive")
    def cached(url, name):
        p = os.path.join(base, name)
        if not os.path.exists(p):
            open(p, "wb").write(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300).read())
        return p
    dl = f"https://archive.org/download/{BOTD}/{BOTD}"
    text = gzip.open(cached(dl + "_hocr_searchtext.txt.gz", BOTD + ".searchtext.gz"), "rt", encoding="utf-8").read()
    index = json.load(gzip.open(cached(dl + "_hocr_pageindex.json.gz", BOTD + ".pageindex.gz"), "rt"))
    nums = {p["leafNum"]: p.get("pageNumber") or "" for p in json.load(open(cached(dl + "_page_numbers.json", BOTD + ".page_numbers.json")))["pages"]}
    starts = [e[0] for e in index]
    heads = [(m.start(), roman(m.group(1))) for m in re.finditer(r"(?m)^\s*Chapter\s+([IVXLC]+)\b", text)]
    import bisect
    out = []
    for k, (pos, ch) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(text)
        leaf = bisect.bisect_right(starts, pos) - 1
        pg = nums.get(leaf, "")
        url = f"https://archive.org/details/{BOTD}/page/{pg or 'n%d' % leaf}/mode/1up"
        out.append((ch, pg, url, re.sub(r"-\n(\w)", r"\1", text[pos:end])))
    return out


def sacred(rows, deities):
    sys.path.insert(0, HERE)
    import build_sacred_world as W
    budge = {f["name"]: f for f in W.parse(W.EGYPTIAN)}
    chapters = botd_chapters()
    cols = ("name figure_id figure sex original translit language tradition subtradition corpus text passage url occurrences "
            "entity_type name_role status relation source confidence").split()
    out = []
    for r in sorted((r for r in rows.values() if r["kind"] == "deity"), key=lambda r: r["name"]):
        top = sorted(r["bearers"], reverse=True)[0]
        e = deities.get(top[3], {})
        forms = {r["name"]}
        title = e.get("sitelinks", {}).get("enwiki", {}).get("title", "")
        f = budge.get(r["name"]) or next((b for b in budge.values() if b["title"] == title), None)
        if f: forms |= set(f["forms"].lstrip("=~").split(","))
        ambiguous = (f and f["review"]) or len(r["name"]) <= 3
        pats = [re.compile(r"(?<![A-Za-z-])" + re.escape(x) + r"(?![a-z-])") for x in sorted(forms, key=len, reverse=True) if x]
        n, first, used = 0, None, collections.Counter()
        for ch, pg, url, t in chapters:
            for p in pats:
                for m in p.finditer(t):
                    if ambiguous and not re.search(r"(?:the god|the goddess|of|and|to|unto|by|with|,)\s+$", t[max(0, m.start() - 12):m.start()]):
                        continue
                    n += 1; used[m.group(0)] += 1
                    if first is None: first = (ch, pg, url)
        if not first: continue
        sex = {"g": "girl", "b": "boy"}.get(next(iter(r["g"])), "")
        printed = used.most_common(1)[0][0]
        out.append({"name": r["name"], "figure_id": top[3], "figure": f"{r['name']}, {top[2]}" if top[2] else r["name"], "sex": sex,
                    "original": "", "translit": r["tr"] or "", "language": "Egyptian", "tradition": "Egyptian religion", "subtradition": "",
                    "corpus": "Book of the Dead", "text": "Theban recension (Budge 1898 translation)",
                    "passage": f"BD chapter {first[0]} (Budge 1898" + (f", p. {first[1]})" if first[1] else ")"), "url": first[2],
                    "occurrences": str(n), "entity_type": "deity", "name_role": "divine", "status": "attested",
                    "relation": "" if printed == r["name"] else f"printed {printed} in Budge's translation",
                    "source": BOTD_SRC, "confidence": "0.7" if ambiguous else "0.8"})
    os.makedirs(os.path.dirname(SACRED), exist_ok=True)
    with open(SACRED, "w", encoding="utf-8") as fh:
        fh.write("\t".join(cols) + "\n")
        for o in out: fh.write("\t".join(o[c].replace("\t", " ") for c in cols) + "\n")
    print(f"{len(out)} deity rows -> {SACRED}")


def sentence(r):
    b = sorted(r["bearers"], reverse=True)
    top = b[0]
    who = top[1] + (", " + top[2].rstrip(".") if top[2] else "")
    tr = (f"Egyptian {r['tr']}, {r['trsrc']}. " if r.get("tr") else "Transliteration not found in the PNM or TLA data used. ")
    if r["kind"] == "deity":
        kind = "A goddess's name" if r["g"] == {"g"} else "A god's name"
        return f"{kind} in ancient Egyptian religion, not a person's name in the sources used: {who}. {tr}{VOWELS}. Wikidata {top[3]}."
    if r["culture"] == "Greek":
        return (f"Used in ancient Egypt: Greek name used in Ptolemaic Egypt, not of Egyptian origin; {who} ({r['period']}). "
                f"Greek origin per Wikidata's given-name item or Wiktionary" + ("; meaning from Wiktionary" if r["meaning"] else "") + f". Wikidata {top[3]}.")
    per = top[5] + (" (Dyn. %s)" % "–".join(str(d) for d in sorted({top[4][0], top[4][-1]})) if top[4] else "")
    if not per and r.get("link"):
        src, d = r["link"]
        if src == "PNM" and d["dyn"]:
            per = "the PNM dates the name's attestations to Dyn. %s (%s)" % ("–".join(str(x) for x in sorted({d['dyn'][0], d['dyn'][-1]})), period_of_dyn(d["dyn"][0]))
        elif src == "TLA" and d.get("years"):
            per = "TLA texts with the name date from c. %d to %d BCE (%s)" % (-min(d["years"]), -max(d["years"]), period_of_year(min(d["years"])))
    others = len(b) - 1
    s = f"Used in ancient Egypt: {who}" + (f", and {others} more on Wikidata" if others else "") + (f"; {per}" if per else "") + ". "
    s += tr + VOWELS + (f". Meaning as translated by the PNM." if r["meaning"] else ".") + f" Wikidata {top[3]}."
    return s


if __name__ == "__main__":
    rows, skipped, deities = build()
    # keep it bounded: famous bearers first (Wikidata sitelinks), all must-check names, all deities with sex
    MUST = set("Narmer Djer Merneith Hetepheres Meresankh Khentkaus Nimaathap Imhotep Ptahhotep Hemiunu Nefermaat Itet Sobekneferu Senet "
               "Neferu Sathathor Mentuhotep Amenemhat Senusret Sinuhe Ahmose Ahmose-Nefertari Hatshepsut Neferure Senenmut Tiye Nefertiti "
               "Mutnodjmet Mutnedjmet Nimaethap Sithathor Meritaten Ankhesenamun Tey Thutmose Amenhotep Ramesses Seti Khaemwaset Nefertari Isetnofret Bintanath Nakht "
               "Cleopatra Berenice Arsinoe Ptolemy".split())
    fame = lambda r: max(b[0] for b in r["bearers"])
    LIMIT_PEOPLE, LIMIT_GODS = int(os.environ.get("EGY_PEOPLE", 150)), int(os.environ.get("EGY_GODS", 40))
    gods = sorted([r for r in rows.values() if r["kind"] == "deity"], key=lambda r: -fame(r))
    greek = {r["name"] for r in rows.values() if r["culture"] == "Greek"}
    # Egyptian origin needs evidence: a non-foreign PNM name or a TLA lemma; must-check names without one are kept and say so
    godnames = {r["name"] for r in gods[:LIMIT_GODS]}
    people = [r for r in rows.values() if r["kind"] == "real" and not (r["culture"] != "Greek" and r["name"] in greek) and r["name"] not in godnames
              and (r["culture"] == "Greek" or r["tr"] or r["name"] in MUST)]
    people.sort(key=lambda r: (r["name"] not in MUST, ease(r["name"]), -fame(r)))
    keep = people[:LIMIT_PEOPLE] + gods[:LIMIT_GODS]
    out = []
    for r in keep:
        g = "e" if len(r["g"]) > 1 else next(iter(r["g"]))
        out.append([r["name"], g, r["culture"], r["language"], "Ancient Egyptian religion" if r["kind"] == "deity" else "",
                    r["meaning"], sentence(r), "", r["kind"], [], ease(r["name"])])
    out.sort(key=lambda x: (x[10], x[0]))
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    c = collections.Counter((x[2], x[8]) for x in out)
    ntr = sum(bool(re.search(r"Egyptian \S+, (PNM|TLA)", x[6])) for x in out)
    print(f"{len(out)} rows -> {OUT}: {dict(c)}; ease {dict(collections.Counter(x[10] for x in out))}; "
          f"with transliteration {ntr}; with meaning {sum(bool(x[5]) for x in out)}")
    print("candidates:", len(rows), "skipped:", dict(skipped))
    print("must-check missing:", sorted(MUST - {x[0] for x in out}))
    sacred(rows, deities)
