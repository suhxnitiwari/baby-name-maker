"""Portuguese names of every kind, with where each one is attested → data/portuguese-names.json

Rows are in the format of data/culture-names.json: [name, g, culture, language, religions, meaning, src, texts, kind, also],
plus an 11th slot, ease: 1 = plain letters, easy to spell in modern English and registered today (IRN list or
names-db.tsv); 2 = usable with care (accents, or not registered today); 3 = hard to spell or only historical. Rows are
sorted by ease, then name.
Culture is always "Portuguese"; the language is "Portuguese", or "Galician-Portuguese" for a medieval form that only the
medieval sources know (troubadours, Old Galician-Portuguese entries, the Livros de Linhagens).

Every name is printed by a source; nothing is generated. Spellings are kept exactly as the source prints them (Inês,
Gonçalo, Simão; and old spellings like Ignez or Luiz when a name list records that spelling).

  Wiktionary (CC BY-SA 4.0), en and pt: the Portuguese and Old Galician-Portuguese given-name categories, with sex and,
    when the entry states it, the meaning. Surname categories are read too, to keep surnames out.
  Wikidata (CC0): kings, queens, infantes and infantas and the royal houses of Portugal; every subject of the Kingdom
    or County of Portugal with a given name (P735); poets of the Galician-Portuguese lyric. A person's name counts only
    when their Portuguese label begins with it and it is their recorded given name.
  Public-domain texts: Project Gutenberg (Os Lusíadas, Camões's Rimas and Autos, Menina e Moça, Gil Vicente, Fernão
    Lopes, Rui de Pina, Garrett, Herculano, Camilo, Eça, Júlio Dinis) and Wikisource pt (Gil Vicente's autos, the
    Peregrinação), and the Livros de Linhagens in Portugaliae Monumenta Historica, Scriptores I (1856, archive.org,
    Public Domain Mark).
  Portugal's IRN list of admitted names (already in data/name-lists.tsv, list pt-admitted) is used only as a check.

A name in a text counts only if it is a known Portuguese given name (Wiktionary, the IRN list or a Wikidata bearer)
or a character the script lists with a quoted phrase from the text that shows the character's sex (CAST); a capital
letter alone never makes a name. Common words that are also names (rosa, graça, luz) need a title before them
(Dona Graça) to count, and surnames need to stand first in a name (Garcia de Resende) more often than after one.

Downloads are cached in raw/portuguese/ (one request at a time, a contact user agent, pauses between requests).

  python3 scripts/build_portuguese_names.py            (add --offline to use only the cache)
"""
import collections, csv, gzip, hashlib, html, json, os, re, sys, time, unicodedata, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "raw", "portuguese"); DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "portuguese-names.json")
UA = {"User-Agent": "Lullabyte/1.0 (https://github.com/suhxnitiwari/baby-name-maker; suhanitiwari@utexas.edu)"}
OFFLINE = "--offline" in sys.argv
sys.path.insert(0, HERE)
from build_cultures import section, details, clean  # noqa: E402

def fold(s):
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"[\s-]", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))
nfc = lambda s: unicodedata.normalize("NFC", s)

# ── polite cached fetching ──
_last = {}
def fetch(url, data=None, headers=None, pause=1.0, binary=False):
    key = hashlib.sha1((url + "\n" + json.dumps(data, sort_keys=True, ensure_ascii=False)).encode()).hexdigest()[:20]
    path = os.path.join(RAW, "cache", key)
    if os.path.exists(path):
        return open(path, "rb").read() if binary else open(path, encoding="utf-8").read()
    if OFFLINE: raise RuntimeError("not cached: " + url)
    host = urllib.parse.urlparse(url).netloc
    wait = _last.get(host, 0) + pause - time.time()
    if wait > 0: time.sleep(wait)
    body = urllib.parse.urlencode(data).encode() if data else None
    for attempt in range(8):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, data=body, headers={**UA, **(headers or {})}), timeout=300).read()
            break
        except Exception as e:
            if getattr(e, "code", 0) in (404,): r = b""; break
            time.sleep(5 * (attempt + 1))
    else: raise RuntimeError("kept failing: " + url)
    _last[host] = time.time()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "wb").write(r)
    return r if binary else r.decode("utf-8", "replace")

def mwapi(host, **q):
    q.update(format="json", formatversion="2", maxlag="10")
    for _ in range(5):
        d = json.loads(fetch(f"https://{host}/w/api.php", data=q, pause=1.0))
        if d.get("error", {}).get("code") != "maxlag": return d
        time.sleep(10)
    return d

def members(host, cat, ns=0):
    out, cont = [], {}
    while True:
        d = mwapi(host, action="query", list="categorymembers", cmtitle=cat, cmlimit="500", cmnamespace=str(ns), **cont)
        out += [m["title"] for m in d.get("query", {}).get("categorymembers", [])]
        if "continue" not in d: return out
        cont = {k: v for k, v in d["continue"].items() if k != "continue"}

def wikitexts(host, titles):
    out = {}
    titles = sorted(set(titles))
    for i in range(0, len(titles), 50):
        d = mwapi(host, action="query", prop="revisions", rvprop="content", rvslots="main", titles="|".join(titles[i:i + 50]))
        norm = {n["to"]: n["from"] for n in d.get("query", {}).get("normalized", [])}
        for p in d.get("query", {}).get("pages", []):
            t = norm.get(p["title"], p["title"])
            out[t] = ((p.get("revisions") or [{}])[0].get("slots", {}).get("main", {}).get("content", "")) if not p.get("missing") else ""
    return out

def sparql(q):
    d = json.loads(fetch("https://query.wikidata.org/sparql", data={"query": q}, headers={"Accept": "application/sparql-results+json"}, pause=2.0))
    return [{k: v["value"] for k, v in b.items()} for b in d["results"]["bindings"]]

# ── the name lists ──
SEX = {"male": "b", "female": "g", "unisex": "e"}
class Lex:
    def __init__(self):
        self.g = collections.defaultdict(set)       # form → sexes (b/g) from Portuguese name lists
        self.src = collections.defaultdict(set)     # form → sources
        self.meaning, self.frm, self.lang = {}, {}, {}
        self.surname = set()
        self.alt = {}                                # old or alternative spelling → the spelling it is listed under
    def add(self, form, g, src, meaning="", frm="", lang="Portuguese"):
        form = nfc(form)
        if g == "e": self.g[form] |= {"b", "g"}
        elif g: self.g[form].add(g)
        self.src[form].add(src)
        if meaning and form not in self.meaning: self.meaning[form] = meaning
        if frm and form not in self.frm: self.frm[form] = frm
        if lang == "Portuguese" or form not in self.lang: self.lang[form] = lang
    def __contains__(self, form): return form in self.src

LEX = Lex()

def en_wiktionary():
    host = "en.wiktionary.org"
    cats = {}
    for lang, code in (("Portuguese", "pt"), ("Old Galician-Portuguese", "roa-opt")):
        for sub in ("given names", "male given names", "female given names", "unisex given names", "diminutives of male given names", "diminutives of female given names"):
            for t in members(host, f"Category:{lang} {sub}"): cats.setdefault(t, set()).add((lang, sub))
    for t in members(host, "Category:Portuguese surnames"): LEX.surname.add(nfc(t))
    texts = wikitexts(host, list(cats))
    json.dump({"cats": {t: sorted(map(list, c)) for t, c in cats.items()}}, open(os.path.join(RAW, "en-wiktionary-titles.json"), "w", encoding="utf-8"), ensure_ascii=False)
    for t, cs in cats.items():
        if not re.match(r"^[^\W\d_][^\W\d_'’-]*$", t): continue
        for lang in sorted({c[0] for c in cs}):
            sec = section(texts.get(t, ""), lang)
            code = "pt" if lang == "Portuguese" else "roa-opt"
            gs = set(re.findall(r"\{\{given name\|" + code + r"\|(male|female|unisex)", sec))
            subs = {c[1] for c in cs if c[0] == lang}
            g = "e" if "unisex" in gs or "unisex given names" in subs or len(gs) > 1 else SEX[gs.pop()] if gs else \
                "b" if any("male" in s and "female" not in s for s in subs) and not any("female" in s for s in subs) else "g" if any("female" in s for s in subs) and not any("male given" in s and "female" not in s for s in subs) else ""
            d = details(sec) if sec else {}
            alt = re.search(r"\{\{(?:obsolete spelling of|alternative spelling of|alternative form of|archaic spelling of|pt-obsolete[^|]*)\|(?:pt\|)?([^|}]+)", sec)
            if alt and alt.group(1) != t: LEX.alt[nfc(t)] = nfc(clean(alt.group(1)))
            LEX.add(t, g, "Wiktionary", d.get("meaning", ""), d.get("from", ""), "Portuguese" if lang == "Portuguese" else "Galician-Portuguese")

def pt_section(text):
    m = re.search(r"\{\{-(pt|roa-opt|gl-pt|gpm)-\}\}", text)
    if not m: return ""
    nxt = re.search(r"(?m)^=\s*\{\{-[a-z-]+-\}\}\s*=", text[m.end():])
    return text[m.end(): m.end() + nxt.start()] if nxt else text[m.end():]

def pt_wiktionary(extra=()):
    host = "pt.wiktionary.org"
    titles = set(extra)
    for c in ("Categoria:Antropônimo (Português)", "Categoria:Prenome (Português)", "Categoria:Antropônimo (Galego-Português Medieval)"):
        titles |= set(members(host, c))
    sur = set(members(host, "Categoria:Sobrenome (Português)"))
    LEX.surname |= {nfc(t) for t in sur}
    texts = wikitexts(host, titles)
    for t, text in texts.items():
        sec = pt_section(text)
        if not sec or not re.match(r"^[^\W\d_][^\W\d_'’-]*$", t): continue
        defs = " ".join(re.findall(r"(?m)^#[^:*].*$", sec)).lower()
        defs = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", defs)
        g = set()
        if re.search(r"(prenome|nome próprio|antropônimo)\W+(\w+\W+)?feminino", defs): g.add("g")
        if re.search(r"(prenome|nome próprio|antropônimo)\W+(\w+\W+)?masculino", defs): g.add("b")
        if "sobrenome" in defs and not g: LEX.surname.add(nfc(t)); continue
        if not g: continue
        m = re.search(r"[Ss]ignifica\s+''([^'\n]{2,60})''", sec)
        lang = "Galician-Portuguese" if re.search(r"\{\{-(roa-opt|gpm)-\}\}", text) and "{{-pt-}}" not in text else "Portuguese"
        LEX.add(t, "e" if len(g) > 1 else g.pop(), "Wiktionary (pt)", clean(m.group(1)) if m else "", lang=lang)

IRN = {}
def irn():
    for r in csv.DictReader(open(os.path.join(DATA, "name-lists.tsv"), encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
        if r["list"] == "pt-admitted" and r["status"] != "rejected":
            IRN.setdefault(nfc(r["name"]), set()).add({"f": "g", "m": "b"}.get(r["gender"], ""))

# ── Wikidata: real people ──
HOUSES = "wd:Q704122 wd:Q1642657 wd:Q747516 wd:Q853342 wd:Q2354826"      # Burgundy (2 items), Aviz, Braganza, Braganza-Saxe-Coburg and Gotha
TITLES = "wd:Q6029007 wd:Q109655717 wd:Q3330607 wd:Q1934769"              # Infante, Infanta, Prince of Portugal, Duke of Braganza
POSITIONS = "wd:Q58800860 wd:Q58799308"                                   # monarch of Portugal, queen consort of Portugal
PERSON = """?x wdt:P31 wd:Q5; wdt:P735 ?gn.
 OPTIONAL { ?gn rdfs:label ?gnl FILTER(lang(?gnl)="pt") } OPTIONAL { ?gn wdt:P31 ?cls }
 OPTIONAL { ?x wdt:P21 ?sex } OPTIONAL { ?x wdt:P569 ?born } OPTIONAL { ?x wikibase:sitelinks ?links }
 OPTIONAL { ?x rdfs:label ?xl FILTER(lang(?xl)="pt") } OPTIONAL { ?x schema:description ?desc FILTER(lang(?desc)="en") }"""
def wikidata():
    groups = {
        "royal": f"""SELECT ?x ?xl ?desc ?sex ?born ?links ?gn ?gnl ?cls ?role WHERE {{
          {{ VALUES ?h {{ {HOUSES} }} ?x wdt:P53 ?h BIND("house" AS ?role) }} UNION {{ VALUES ?t {{ {TITLES} }} ?x wdt:P97 ?t BIND("title" AS ?role) }}
          UNION {{ VALUES ?p {{ {POSITIONS} }} ?x wdt:P39 ?p BIND("crown" AS ?role) }} UNION {{ ?k wdt:P39 wd:Q58800860. ?x wdt:P26 ?k BIND("spouse" AS ?role) }}
          {PERSON} }}""",
        "subject": f"""SELECT ?x ?xl ?desc ?sex ?born ?links ?gn ?gnl ?cls WHERE {{ VALUES ?c {{ wd:Q45670 wd:Q1139807 }} ?x wdt:P27 ?c. {PERSON} }}""",
        "troubadour": f"""SELECT ?x ?xl ?desc ?sex ?born ?links ?gn ?gnl ?cls WHERE {{
          {{ ?x wdt:P1412 wd:Q1072111 }} UNION {{ ?x wdt:P135 wd:Q2457695 }} UNION {{ ?x wdt:P6886 wd:Q1072111 }} {PERSON} }}""",
    }
    people = {}
    for grp, q in groups.items():
        try: res = sparql(q)
        except RuntimeError as e: print("  Wikidata skipped (not cached):", grp); continue
        for r in res:
            x = r["x"].rsplit("/", 1)[1]
            p = people.setdefault(x, {"q": x, "label": r.get("xl", ""), "desc": r.get("desc", ""), "sex": set(), "born": "", "links": 0, "gn": {}, "groups": set()})
            p["groups"].add(grp if grp != "royal" else "royal-" + r.get("role", ""))
            if r.get("sex"): p["sex"].add({"Q6581097": "b", "Q6581072": "g"}.get(r["sex"].rsplit("/", 1)[1], ""))
            if r.get("born") and re.match(r"-?\d{4}", r["born"]) and not p["born"]: p["born"] = r["born"][:4]
            p["links"] = max(p["links"], int(r.get("links", 0) or 0))
            gq = r["gn"].rsplit("/", 1)[1]
            e = p["gn"].setdefault(gq, {"label": r.get("gnl", ""), "cls": set()})
            if r.get("cls"): e["cls"].add({"Q12308941": "b", "Q11879590": "g", "Q3409032": "e"}.get(r["cls"].rsplit("/", 1)[1], ""))
    return people

PARTICLES = {"de", "da", "do", "dos", "das", "e", "d'", "del", "von", "van", "la", "le", "y", "o", "a"}
HONORIFIC = {"D.", "Dom", "Dona", "Infante", "Infanta", "Santa", "Santo", "São", "Beata", "Beato", "Frei", "Sóror", "Soror", "Rainha", "Rei", "Princesa", "Príncipe", "Madre", "Padre", "Fr."}
def person_names(people):
    """{name: [person, …]} for every person whose Portuguese label starts with their recorded given name(s)."""
    out = collections.defaultdict(list)
    for p in people.values():
        words = [w for w in re.split(r"\s+", re.sub(r"\(.*?\)", "", p["label"]).strip()) if w]
        while words and words[0] in HONORIFIC: words = words[1:]
        labels = {e["label"]: e for e in p["gn"].values() if e["label"]}
        for w in words:
            if w.lower() in PARTICLES or not re.match(r"^[^\W\d_][^\W\d_'’]*$", w): break
            w = nfc(w)
            if w in labels: out[w].append((p, labels[w]["cls"]))
            elif labels and (w in LEX or w in IRN) and len(p["gn"]) == 1 and words.index(w) == 0:
                out[w].append((p, set()))         # labelled with the Portuguese form of their one given name (Mary I → Maria)
            else: break
    return out

def role(p):
    g = p["groups"]
    d = p["desc"]
    if d and re.search(r"(?i)portug|queen|king|infant|prince|princess|duke|duchess|troubadour|trovador|poet|countess|count", d):
        return d
    if "troubadour" in g: return "a poet of the Galician-Portuguese lyric"
    if any(x.startswith("royal") for x in g): return "of the Portuguese royal family"
    return d or "a subject of the Kingdom of Portugal"

# ── texts ──
PG = lambda i: ("pg", i)
WORKS = [
    # key, title shown, year, author, source, verse?, start (regex where the work itself begins)
    ("Os Lusíadas", "Os Lusíadas", "1572", "Luís de Camões", PG(3333), True, r"^Canto Primeiro"),
    ("Camões, Rimas", "Camões's Rimas", "1595", "Luís de Camões", PG(37192), True, r"^RIMAS\.$"),
    ("Camões, Obras II", "Camões's sonnets and autos (Obras, 1843, vol. II)", "1843", "Luís de Camões", PG(31509), True, r"^SONETOS|^SONETO"),
    ("Menina e Moça", "Menina e Moça", "1554", "Bernardim Ribeiro", PG(27725), False, r"^CAPITULO I\b|^\s*MENINA E MOÇA"),
    ("Pranto de Maria Parda", "Pranto de Maria Parda", "1522", "Gil Vicente", PG(21287), True, None),
    ("Monólogo do Vaqueiro", "Monólogo do Vaqueiro", "1502", "Gil Vicente", PG(24129), True, None),
    ("Auto da Barca do Inferno", "Auto da Barca do Inferno", "1517", "Gil Vicente", ("ws", "Auto da Barca do Inferno", True), True, None),
    ("Auto da Alma", "Auto da Alma", "1518", "Gil Vicente", ("ws", "Auto da Alma", False), True, None),
    ("Auto da Lusitânia", "Auto da Lusitânia", "1532", "Gil Vicente", ("ws", "Auto da Lusitânia", False), True, None),
    ("Auto da Índia", "Auto da Índia", "1509", "Gil Vicente", ("ws", "Auto da Índia", False), True, None),
    ("Auto de Mofina Mendes", "Auto de Mofina Mendes", "1534", "Gil Vicente", ("ws", "Auto de Mofina Mendes", False), True, None),
    ("Farsa de Inês Pereira", "Farsa de Inês Pereira", "1523", "Gil Vicente", ("ws", "Farsa de Inês Pereira", False), True, None),
    ("O Velho da Horta", "O Velho da Horta", "1512", "Gil Vicente", ("ws", "O Velho da Horta", False), True, None),
    ("Peregrinação", "the Peregrinação", "1614", "Fernão Mendes Pinto", ("ws", "Peregrinaçam", True), False, None),
    ("Crónica de D. Pedro I", "Fernão Lopes's Crónica de D. Pedro I", "c. 1434", "Fernão Lopes", PG(16633), False, r"^\s*CAPITULO I\b|^\s*Prologo|^\s*PROLOGO"),
    ("Crónica de D. Afonso II", "Rui de Pina's Crónica de D. Afonso II", "c. 1510", "Rui de Pina", PG(22826), False, None),
    ("Crónica de D. Sancho II", "Rui de Pina's Crónica de D. Sancho II", "c. 1510", "Rui de Pina", PG(27311), False, None),
    ("Crónica de D. Afonso III", "Rui de Pina's Crónica de D. Afonso III", "c. 1510", "Rui de Pina", PG(15674), False, None),
    ("Crónica de D. Dinis", "Rui de Pina's Crónica de D. Dinis", "c. 1510", "Rui de Pina", (("pg", 16571), ("pg", 18167)), False, None),
    ("Crónica de D. Afonso V", "Rui de Pina's Crónica de D. Afonso V", "c. 1510", "Rui de Pina", (("pg", 25987), ("pg", 21911), ("pg", 24508)), False, None),
    ("Frei Luís de Sousa", "Frei Luís de Sousa", "1843", "Almeida Garrett", PG(17591), False, None),
    ("Viagens na Minha Terra", "Viagens na Minha Terra", "1846", "Almeida Garrett", PG(24401), False, None),
    ("Romanceiro", "Garrett's Romanceiro", "1843", "Almeida Garrett", (("pg", 63438), ("pg", 63439)), True, None),
    ("Miragaia", "Miragaia", "1844", "Almeida Garrett", PG(24411), True, None),
    ("Eurico, o Presbítero", "Eurico, o Presbítero", "1844", "Alexandre Herculano", PG(45966), False, None),
    ("Lendas e Narrativas", "Lendas e Narrativas", "1851", "Alexandre Herculano", (("pg", 9654), ("pg", 17005)), False, None),
    ("Amor de Perdição", "Amor de Perdição", "1862", "Camilo Castelo Branco", PG(16425), False, None),
    ("A Queda dum Anjo", "A Queda dum Anjo", "1866", "Camilo Castelo Branco", PG(17927), False, None),
    ("Amor de Salvação", "Amor de Salvação", "1864", "Camilo Castelo Branco", PG(26988), False, None),
    ("A Filha do Arcediago", "A Filha do Arcediago", "1854", "Camilo Castelo Branco", PG(27364), False, None),
    ("A Neta do Arcediago", "A Neta do Arcediago", "1856", "Camilo Castelo Branco", PG(29740), False, None),
    ("O Bem e o Mal", "O Bem e o Mal", "1863", "Camilo Castelo Branco", PG(62624), False, None),
    ("Novelas do Minho", "Novelas do Minho", "1875", "Camilo Castelo Branco", PG(21406), False, None),
    ("A Brasileira de Prazins", "A Brasileira de Prazins", "1882", "Camilo Castelo Branco", PG(68905), False, None),
    ("O Crime do Padre Amaro", "O Crime do Padre Amaro", "1875", "Eça de Queirós", PG(31971), False, None),
    ("O Primo Basílio", "O Primo Basílio", "1878", "Eça de Queirós", PG(42942), False, None),
    ("O Mandarim", "O Mandarim", "1880", "Eça de Queirós", PG(16384), False, None),
    ("A Relíquia", "A Relíquia", "1887", "Eça de Queirós", PG(17515), False, None),
    ("Os Maias", "Os Maias", "1888", "Eça de Queirós", PG(40409), False, None),
    ("A Ilustre Casa de Ramires", "A Ilustre Casa de Ramires", "1900", "Eça de Queirós", PG(23145), False, None),
    ("A Cidade e as Serras", "A Cidade e as Serras", "1901", "Eça de Queirós", PG(18220), False, None),
    ("Contos (Eça)", "Eça de Queirós's Contos", "1902", "Eça de Queirós", PG(31347), False, None),
    ("Uma Família Inglesa", "Uma Família Inglesa", "1868", "Júlio Dinis", PG(16443), False, None),
    ("A Morgadinha dos Canaviais", "A Morgadinha dos Canaviais", "1868", "Júlio Dinis", PG(29120), False, None),
    ("Os Fidalgos da Casa Mourisca", "Os Fidalgos da Casa Mourisca", "1871", "Júlio Dinis", PG(16428), False, None),
]
LINHAGENS = [  # (key, title, line range in the PMH OCR text)
    ("Livro Velho and Livro do Deão", "the Livro Velho and the Livro do Deão (Livros de Linhagens)", 22900, 30806),
    ("Livro de Linhagens do Conde D. Pedro", "the Livro de Linhagens do Conde D. Pedro", 30807, 42875),
]
MEDIEVAL = {"Livro Velho and Livro do Deão", "Livro de Linhagens do Conde D. Pedro"}

# Invented characters, kept only with a phrase from the text that shows their sex. Checked against the cached text.
CAST = {
    "Menina e Moça": [("Aonia", "g", r"senhora Aonia"), ("Belisa", "g", r"Belisa \(que assim se chamava aquela senhora"),
                      ("Bimnarder", "b", r"Bimnarder \(chamando-o assim por seu nome\)"), ("Enis", "g", r"uma mulher de casa, que Enis se chamava"),
                      ("Cruelcia", "g", r"Era Cruelcia uma de duas filhas"), ("Fileno", "b", r"Fileno, o marido de Aonia")],
}

def gutenberg(i):
    path = os.path.join(RAW, "pg", f"pg{i}.txt")
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, "w", encoding="utf-8").write(fetch(f"https://www.gutenberg.org/cache/epub/{i}/pg{i}.txt", pause=2.0))
    t = open(path, encoding="utf-8").read()
    a = re.search(r"\*\*\* ?START OF[^\n]*\n", t); b = re.search(r"\*\*\* ?END OF", t)
    return t[a.end() if a else 0: b.start() if b else len(t)]

def html_text(h):
    h = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?is)<span[^>]*class=\"[^\"]*pagenum[^\"]*\"[^>]*>.*?</span>", " ", h)
    h = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</h\d>|</dd>|</li>|</tr>", "\n", h)
    return html.unescape(re.sub(r"<[^>]+>", "", h))

def wikisource(title, subpages):
    host = "pt.wikisource.org"
    titles = [title]
    if subpages:
        d = mwapi(host, action="query", list="allpages", apnamespace="0", apprefix=title + "/", aplimit="500")
        titles += [p["title"] for p in d["query"]["allpages"]]
    parts = []
    for t in titles:
        d = mwapi(host, action="parse", page=t, prop="text", disablelimitreport="1", disableeditsection="1")
        parts.append(html_text(d.get("parse", {}).get("text", "")))
    return "\n\n".join(parts)

def work_text(src, start):
    if src and isinstance(src[0], tuple): return "\n\n".join(work_text(s, start) for s in src)
    t = gutenberg(src[1]) if src[0] == "pg" else wikisource(src[1], src[2])
    t = nfc(t.replace("\r", ""))
    if start:
        m = re.search(start, t, re.M)
        if m: t = t[m.start():]
    return t

def pmh():
    path = os.path.join(RAW, "pmh-scriptores-v1.txt")
    if not os.path.exists(path):
        open(path, "w", encoding="utf-8").write(fetch("https://archive.org/download/portugaliaemonumentahistoricascrv1/Portugaliae_monumenta_historica_Scr_V1_djvu.txt", pause=2.0))
    return open(path, encoding="utf-8").read().split("\n")

# ── finding names in a text ──
WORD = r"[^\W\d_]+(?:['’][^\W\d_]+)?"
CAP = re.compile(r"(?<![\w'’-])([A-ZÀ-ÖØ-Þ][^\W\d_A-ZÀ-ÖØ-Þ]+)(?![\w'’-])")
TITLE_M = set("dom frei fr padre sr snr senhor mestre tio irmão rei el-rei infante conde duque marquez marquês são santo menino primo compadre pai dr doutor abade conego cónego prior visconde barão morgado mano tiozinho fidalgo cavalleiro cavaleiro".split())
TITLE_F = set("dona d.ª sóror soror senhora sra snra tia irmã rainha infanta condessa duqueza duquesa santa menina prima comadre mãe viscondessa baroneza baronesa morgadinha madre mana tiazinha sr.ª".split())
ART_M = set("o do no pelo ao dum num".split()); ART_F = set("da na pela à duma numa".split())
SUR_LINK = set("de da do dos das d'".split())
STOP = set("""Deus Christo Cristo Jesus Senhor Senhora Nossa Virgem Rei Rainha Dom Dona Santa Santo São Sancto Sancta Infante Infanta Conde Condessa
Duque Duquesa Marquez Marquês Frei Padre Mestre El Elrei Portugal Lisboa Porto Coimbra Castella Castela Hespanha Espanha França Roma Christão Christã
Cristã Cristão Capitulo Capítulo Canto Livro Parte Acto Scena Cena Fim Prologo Prólogo Primeiro Segundo Terceiro Quarto Quinto Sexto Setimo Sétimo
Oitavo Nono Decimo Décimo Mãe Pai Filho Filha Igreja Céu Ceo Inferno Paraíso Anjo Diabo Amor Morte Fortuna Fé Esperança Caridade Graça Gloria Glória
Natureza Verdade Razão Saudade Saudades Sol Lua Terra Mar Gentil Gutenberg Project Senhorio Vossa Vosso Sua Seu Alteza Magestade Majestade Mercê""".split())
MONTHS = set("Janeiro Fevereiro Março Abril Maio Junho Julho Agosto Setembro Outubro Novembro Dezembro Setembro Outubro".split())

def scan(text, verse):
    """Per capitalized word: how often it stands where a name can stand, and the clues around it."""
    st = collections.defaultdict(lambda: collections.Counter())
    lc = collections.Counter(w for w in re.findall(r"(?<![\w'’-])([a-zà-öø-ÿ][^\W\d_]*)(?![\w'’-])", text))
    for m in CAP.finditer(text):
        w = m.group(1)
        i = m.start()
        before = text[max(0, i - 60): i]
        after = text[m.end(): m.end() + 60]
        line_start = text.rfind("\n", 0, i) + 1
        first_on_line = not text[line_start:i].strip(" \t\"'«“—–-_*(")
        prev_chr = before.rstrip()[-1:] if before.rstrip() else "\n"
        s = st[w]
        s["all"] += 1
        sentence_start = prev_chr in ".!?…:;«»\"“”—–-(\n_*[" or (verse and first_on_line) or not before.strip()
        if sentence_start: continue
        s["free"] += 1
        pw = re.findall(r"([^\W\d_][^\s]*|[^\W\d_]\.(?:ª)?)\s*$", before)
        prev = pw[0] if pw else ""
        pl = prev.lower().rstrip(",")
        prev2 = re.findall(r"(\S+)\s+\S+\s*$", before)
        prev2 = prev2[0] if prev2 else ""
        nxt = re.match(r"\s*([^\s,.;:!?]+)(\s+([^\s,.;:!?]+))?", after)
        nw = nxt.group(1) if nxt else ""; nw2 = (nxt.group(3) or "") if nxt else ""
        cap_prev = bool(re.match(r"^[A-ZÀ-ÖØ-Þ][^\W\d_]+$", prev)) and prev not in STOP and pl not in TITLE_M | TITLE_F
        if cap_prev or (pl in SUR_LINK and re.match(r"^[A-ZÀ-ÖØ-Þ]", prev2 or "x") and prev2 not in STOP): s["sur"] += 1
        else:
            title = pl in TITLE_M or pl in TITLE_F or prev in ("D.", "D.ª", "Fr.", "Sr.", "Snr.", "S.", "Sta.", "Sto.")
            if title: s["title"] += 1
            if pl in TITLE_M: s["vb"] += 1
            if pl in TITLE_F or prev == "D.ª": s["vg"] += 1
            if pl in ART_M and not re.match(r"^[A-ZÀ-ÖØ-Þ]", prev2): s["ab"] += 1
            if pl in ART_F and not re.match(r"^[A-ZÀ-ÖØ-Þ]", prev2): s["ag"] += 1
            if title or re.match(r"^[A-ZÀ-ÖØ-Þ][^\W\d_]+$", nw) and nw not in STOP or (nw.lower() in SUR_LINK and re.match(r"^[A-ZÀ-ÖØ-Þ]", nw2)): s["given"] += 1
    # speaker labels in plays (INÊS PEREIRA. / PERO:) are the play's cast
    for m in re.finditer(r"(?m)^\s*([A-ZÀ-ÖØ-Þ]{3,}(?:\s+[A-ZÀ-ÖØ-Þ]{2,})*)\s*[.:—-]", text):
        for i, w in enumerate(m.group(1).split()):
            st[w.capitalize() if not w.startswith(("Á", "É")) else w[0] + w[1:].lower()]["cast" if i == 0 else "castsur"] += 1
    return st, lc

def old_key(s):
    """A key that old and new spellings share (Ignez/Inês, Luiz/Luís, Affonso/Afonso, Thereza/Teresa)."""
    s = fold(s)
    for a, b in (("ph", "f"), ("th", "t"), ("y", "i"), ("chr", "cr"), ("ign", "in"), ("ct", "t")):
        s = s.replace(a, b)
    s = re.sub(r"([bcdfglmnprt])\1", r"\1", s)
    s = re.sub(r"z$", "s", s); s = re.sub(r"(?<=[aeiou])z(?=[aeiou])", "s", s)
    s = re.sub(r"am$", "ao", s); s = re.sub(r"oel$", "uel", s)
    return s

def main():
    os.makedirs(RAW, exist_ok=True)
    stats = collections.Counter()
    irn()
    en_wiktionary()
    pt_wiktionary()
    people = wikidata()
    json.dump([{**p, "sex": sorted(p["sex"]), "groups": sorted(p["groups"]), "gn": {k: {"label": v["label"], "cls": sorted(v["cls"])} for k, v in p["gn"].items()}}
               for p in people.values()], open(os.path.join(RAW, "wikidata-people.json"), "w", encoding="utf-8"), ensure_ascii=False)
    bearers = person_names(people)

    # texts: candidates first, then look up the ones no list has yet on Wiktionary (en and pt)
    scans = {}
    for key, title, year, author, src, verse, start in WORKS:
        try: text = work_text(src, start)
        except RuntimeError as e: print("  skipped", key, e); continue
        scans[key] = (scan(text, verse), text)
        stats["texts"] += 1
    lines = pmh()
    for key, title, a, b in LINHAGENS:
        t = "\n".join(lines[a - 1: b])
        t = re.sub(r"[¬-]\s*\n\s*", "", t)                              # words broken across lines
        t = re.sub(r"\s\d\s(?=\w)", " ", t)                             # the edition's variant-reading markers
        scans[key] = (scan(t, False), t)

    known = set(LEX.src) | set(IRN) | set(bearers)
    unknown = set()
    for (st, lc), _ in scans.values():
        for w, s in st.items():
            if w not in known and w not in STOP and (s["free"] >= 2 or s["cast"]) and len(w) > 2 and not lc.get(w.lower()): unknown.add(w)
    print(f"  looking up {len(unknown):,} more words on Wiktionary")
    try: en = wikitexts("en.wiktionary.org", unknown)
    except RuntimeError: print("  en Wiktionary lookups skipped (not cached)"); en = {}
    for t, text in en.items():
        sec = section(text, "Portuguese")
        if not sec: continue
        gs = set(re.findall(r"\{\{given name\|pt\|(male|female|unisex)", sec))
        alt = re.search(r"\{\{(?:obsolete spelling of|alternative spelling of|alternative form of|archaic spelling of|pt-obsolete[^|]*)\|(?:pt\|)?([^|}]+)", sec)
        if gs:
            d = details(sec)
            LEX.add(t, "e" if len(gs) > 1 or "unisex" in gs else SEX[gs.pop()], "Wiktionary", d.get("meaning", ""), d.get("from", ""))
        elif alt and nfc(clean(alt.group(1))) in LEX: LEX.alt[nfc(t)] = nfc(clean(alt.group(1)))
        if re.search(r"\{\{surname\|pt", sec): LEX.surname.add(nfc(t))
    try: pt_wiktionary(extra=unknown)
    except RuntimeError: print("  pt Wiktionary lookups skipped (not cached)"); pt_wiktionary()

    by_key = collections.defaultdict(set)
    for f in set(LEX.src) | set(IRN):
        by_key[old_key(f)].add(f)
    def resolve(w):
        """The listed name(s) a word in a text is: itself, the name Wiktionary lists it under, or the one name with the same old-spelling key."""
        out = []
        if w in LEX or w in IRN or w in bearers: out.append(w)
        if w in LEX.alt: out.append(LEX.alt[w])
        if not out:
            c = [f for f in by_key.get(old_key(w), ()) if f in LEX]
            if len(c) == 1: out.append(c[0])
        return out

    WORK_YEAR = {w[0]: int(re.search(r"\d{4}", w[2]).group()) for w in WORKS}
    att = collections.defaultdict(dict)        # name → {work key: (count, spelled)}
    sex_votes = collections.defaultdict(collections.Counter)
    for key, ((st, lc), text) in scans.items():
        lusiadas = key == "Os Lusíadas"
        cantos = [(m.start(), m.group(1)) for m in re.finditer(r"(?m)^Canto (\w+)", text)] if lusiadas else []
        for w, s in st.items():
            if w in STOP or w in MONTHS or len(w) < 2: continue
            ev = s["free"] + s["cast"]
            if ev == 0: continue
            names = resolve(w)
            if not names: continue
            low = lc.get(w.lower(), 0)
            if low >= 2 and low >= 0.25 * max(1, s["free"]) and s["title"] + s["cast"] < 2 and s["given"] < max(3, low): stats["common word"] += 1; continue
            is_sur = w in LEX.surname or any(n in LEX.surname for n in names)
            if (is_sur or s["sur"] > s["given"]) and not (s["given"] + s["cast"] >= 2 and s["given"] + s["cast"] >= s["sur"]): stats["surname"] += 1; continue
            if key in MEDIEVAL and s["given"] + s["title"] < 2: continue    # OCR text: only names standing first in a name, twice
            early = key in MEDIEVAL or (key in WORK_YEAR and WORK_YEAR[key] < 1700)
            for n in names:
                # a name only the IRN list knows (it admits Charlie and Cairo too) counts only in a text from before 1700, standing first in a name twice
                if n not in LEX and n not in bearers and not (early and s["given"] + s["title"] + s["cast"] >= 2): continue
                spelled = w if fold(w) != fold(n) and key not in MEDIEVAL else ""   # the PMH text is OCR: a lost cedilla is not a spelling
                part = ""
                if lusiadas:
                    i = text.find(w); i = re.search(r"(?<![\w'’-])" + re.escape(w) + r"(?![\w'’-])", text)
                    part = next((c for pos, c in reversed(cantos) if i and pos <= i.start()), "")
                att[n][key] = (ev, spelled, part)
                sex_votes[n]["b"] += s["vb"] + s["ab"]; sex_votes[n]["g"] += s["vg"] + s["ag"]
    # invented characters with a phrase that shows their sex
    cast_sex = {}
    for key, cast in CAST.items():
        if key not in scans: continue
        text = scans[key][1]
        for n, g, phrase in cast:
            if re.search(phrase, text):
                att[n][key] = (len(re.findall(r"(?<![\w-])" + re.escape(n) + r"(?![\w-])", text)), "", "")
                cast_sex[n] = g
            else: print("  cast phrase not found:", key, n)

    # ── rows ──
    WORK = {w[0]: w for w in WORKS}
    ROMAN = {"Primeiro": "I", "Segundo": "II", "Terceiro": "III", "Quarto": "IV", "Quinto": "V", "Sexto": "VI", "Sétimo": "VII", "Oitavo": "VIII", "Nono": "IX", "Décimo": "X"}
    def cite(key, spelled, part):
        if key in MEDIEVAL:
            s = "In " + next(t for k, t, a, b in LINHAGENS if k == key) + " (PMH Scriptores I, 1856)"
        else:
            _, title, year, author, *_ = WORK[key]
            s = f"Named in {title} ({year})" + (f", canto {ROMAN.get(part, part)}," if part else "") + ("" if title.startswith(("Camões", "Fernão", "Rui", "Garrett", "Eça", "the Pereg")) else f" by {author}")
            if title.startswith("the Pereg"): s += f" by {author}"
        return s + (f", spelled {spelled}" if spelled else "")
    def ex_person(ps):
        def rank(pc):
            p = pc[0]; g = p["groups"]
            return (0 if "royal-crown" in g or "royal-spouse" in g else 1 if "royal-title" in g else 2 if any(x.startswith("royal") for x in g) else 3 if "troubadour" in g else 4, -p["links"])
        return sorted(ps, key=rank)
    names = set(att) | set(bearers) | {f for f in LEX.src if LEX.lang.get(f) and not f in LEX.surname}
    db = {}
    for line in open(os.path.join(DATA, "names-db.tsv"), encoding="utf-8"):
        db[fold(line.split("\t", 1)[0])] = 1
    def ease(n, lang):
        """1 easy to spell in modern English and in use today; 2 usable with care (accents, rarer); 3 hard or historical only."""
        low = n.lower()
        plain = all(ord(c) < 128 for c in n)
        hard = lang == "Galician-Portuguese" or len(n) > 10 or re.search(r"lh|nh|ç|ã|õ|x|y|w|k|ph|th|^h|aa|ee|ii|oo|uu", low)
        in_use = n in IRN or fold(n) in db
        if plain and not hard and in_use and len(n) <= 8: return 1
        if hard and not in_use or lang == "Galician-Portuguese": return 3
        return 2
    rows = []
    for n in sorted(names):
        if not re.match(r"^[^\W\d_][^\W\d_'’-]*$", n) or len(n) < 2: continue
        ps = ex_person(bearers.get(n, []))
        works = sorted(att.get(n, {}).items(), key=lambda kv: (WORK[kv[0]][2] if kv[0] in WORK else "1300"))
        listed = n in LEX
        if not (listed or ps or works): continue
        if n in LEX.surname and not (works or ps) and "Wiktionary" not in LEX.src.get(n, ()): continue
        # sex: the Portuguese name lists, then Wikidata's class for the name, then the bearers, then the text's own phrase
        g = set(LEX.g.get(n, set())) | {x for x in IRN.get(n, set()) if x}
        if not g:
            for p, cls in ps: g |= {c for c in cls if c}
            if "e" in g: g = {"b", "g"}
        if not g:
            for p, cls in ps: g |= {x for x in p["sex"] if x}
        if not g and n in cast_sex: g = {cast_sex[n]}
        if not g: stats["no sex"] += 1; continue
        sex = "e" if len(g - {"e"}) > 1 or g == {"e"} else (g - {"e"}).pop()
        literary = n in cast_sex and not listed and n not in IRN and not ps
        medieval_only = not literary and (LEX.lang.get(n) == "Galician-Portuguese" or (not listed and n not in IRN and (all(k in MEDIEVAL for k, _ in works) or all("troubadour" in p["groups"] for p, _ in ps))))
        lang = "Galician-Portuguese" if medieval_only and n not in IRN and LEX.lang.get(n) != "Portuguese" else "Portuguese"
        parts = []
        all_works = list(works)
        if literary:
            k = next(k for k, _ in works if k in CAST)
            parts.append(f"A literary name from {WORK[k][1]} ({WORK[k][2]}), by {WORK[k][3]}; its sex is stated in the text.")
            works = [(k2, v) for k2, v in works if k2 != k]
        if ps:
            p = ps[0][0]
            yr = f" (b. {p['born'].lstrip('-')})" if p["born"] and not p["born"].startswith("-") else ""
            parts.append(f"Borne by {p['label']}{yr}, {role(p)} (Wikidata)" + (f", and {len(ps) - 1} more {'person' if len(ps) == 2 else 'people'} of the Kingdom of Portugal" if len(ps) > 1 else "") + ".")
        if works:
            cs = [cite(k, sp, part) for k, (c, sp, part) in works[:3]]
            more = len(works) - 3
            cs = cs[:1] + [re.sub(r"^(Named in|In) ", "in ", c) for c in cs[1:]]
            parts.append("; ".join(cs) + (f"; and {more} more work{'s' if more > 1 else ''}" if more > 0 else "") + ".")
        if not ps and not works and not literary:
            parts.append("A Portuguese given name (Wiktionary)." if lang == "Portuguese" else "An Old Galician-Portuguese given name (Wiktionary).")
        if LEX.frm.get(n): parts.insert(0, f"From {LEX.frm[n]}." if not LEX.frm[n].lower().startswith("from") else LEX.frm[n] + ".")
        if n in IRN: parts.append("Admitted in Portugal (IRN list).")
        texts = ",".join(dict.fromkeys(WORK[k][0] if k in WORK else k for k, _ in all_works))
        rows.append([n, sex, "Portuguese", lang, "", LEX.meaning.get(n, "")[:80], " ".join(parts), texts, "real", [], ease(n, lang)])
        stats["rows"] += 1
    rows.sort(key=lambda r: (r[10], r[0]))
    json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

    # ── report ──
    seen = set()
    for f in ("names-db.tsv", "names-extra.tsv"):
        for line in open(os.path.join(DATA, f), encoding="utf-8"):
            seen.add(fold(line.split("\t", 1)[0]))
    for f in os.listdir(DATA):
        if f.endswith(".json") and f != os.path.basename(OUT):
            try: d = json.load(open(os.path.join(DATA, f), encoding="utf-8"))
            except Exception: continue
            if isinstance(d, list) and d and isinstance(d[0], list) and len(d[0]) >= 9: seen |= {fold(r[0]) for r in d}
            elif isinstance(d, dict) and f == "east-asian-names.json": seen |= {fold(r[0]) for v in d.values() for r in v if isinstance(r, list)}
    new = [r for r in rows if fold(r[0]) not in seen]
    per_work = collections.Counter(k for n, ws in att.items() for k in ws)
    print(f"{len(rows):,} names → {OUT} ({os.path.getsize(OUT) // 1024} KB); {sum(1 for r in rows if r[5]):,} with meanings; "
          f"{len(new):,} new to the site; {sum(1 for r in rows if r[3] == 'Galician-Portuguese'):,} Galician-Portuguese")
    print("  sexes", collections.Counter(r[1] for r in rows), dict(stats))
    print("  per work", per_work.most_common())
    with open(os.path.join(RAW, "report.json"), "w", encoding="utf-8") as fh:
        json.dump({"new": [r[0] for r in new], "per_work": per_work, "stats": stats}, fh, ensure_ascii=False)
    check = "Inês Leonor Mafalda Constança Filipa Catarina Joana Teresa Madalena Mariana Amélia Luísa Beatriz Isabel Sancha Urraca Aónia Aonia Arima Afonso Dinis Duarte Vasco Gonçalo Martim Lopo Mem Paio Pero Nuno Álvaro João Pedro Simão Manuel Jacinto Amaro".split()
    have = {r[0]: r for r in rows}
    for n in check: print("  ", n, "→", (have[n][1], have[n][3], have[n][6][:150]) if n in have else "MISSING")

if __name__ == "__main__":
    main()
