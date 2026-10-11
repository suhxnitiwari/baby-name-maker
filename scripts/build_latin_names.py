# Latin names → data/latin-names.json, in the storied-row format of data/culture-names.json plus an 11th slot, ease:
#   [name, g ('g'|'b'|'e'), "Latin", "Latin", religions, meaning, source_sentence, texts "", "real", also [], ease]
#
# Sources (all open):
#   English Wiktionary (CC BY-SA 4.0): every page in "Latin praenomina", "Latin nomina gentilia", "Latin cognomina",
#     "Latin male given names", "Latin female given names", with each page's Latin etymology; and, for names the site
#     already has that come from Latin (Clara, Serena, Valentina…), the etymology on that name's own Wiktionary page.
#   Lewis & Short, A Latin Dictionary (Perseus Digital Library, CC BY-SA 3.0, PerseusDL/lexica on GitHub): the meaning
#     of a name's Latin root word when Wiktionary names the root without glossing it.
#   Epigraphic Database Heidelberg (CC BY-SA 4.0, raw/roman/edh_data_pers.csv): how many people of that sex bear the
#     name on Roman inscriptions (as praenomen, nomen or cognomen), leaving out emperors and their family (status 0).
#   Wikidata (CC0): given-name items whose language of name (P407) is Latin, for Latin names the categories miss.
#
# Rules: a meaning is only ever a gloss from Wiktionary or Lewis & Short, and only when the etymology is not hedged
# (possibly, perhaps…); sex comes from the source (a feminine -a form of a Roman name is kept only when Wiktionary
# lists it as a woman's name or women bear it on inscriptions in EDH); names that Latin borrowed from Greek, Hebrew,
# Germanic… are left out (they are not Latin names). The form people use today is the Latin form when it is used
# (Felix, Aurelia, Cornelius), else a modern form found in the birth registries in data/names-db.tsv (Iulia → Julia,
# Cassianus → Cassian); the Latin form is kept in the sentence.
# ease: 1 easy to spell in modern English (used in English-speaking registries), 2 plain spelling, 3 hard (ae, oe, ii…).
#
#   python3 scripts/build_latin_names.py          (downloads into raw/latin/ only what is not cached there)
import csv, html, json, os, re, sys, unicodedata, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "raw", "latin"); DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "latin-names.json")
sys.path.insert(0, HERE)
from fetch_wiktionary_names import members, pages, UA
os.makedirs(RAW, exist_ok=True)

def fold(s):
    s = unicodedata.normalize("NFD", s); s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    for a, b in (("æ", "ae"), ("œ", "oe"), ("ø", "o"), ("ß", "ss")): s = s.replace(a, b)
    return re.sub(r"[\s-]", "", s)
def plain(s):  # Fēlīx → Felix
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c))
def lfold(s):  # Latin spelling fold: Iulia = Julia, Valeria = Ualeria
    return fold(s).replace("j", "i").replace("v", "u")

# ── downloads (cached) ──
CATS = ["Latin praenomina", "Latin nomina gentilia", "Latin cognomina", "Latin male given names", "Latin female given names"]
WIKT = os.path.join(RAW, "wiktionary.json")
if not os.path.exists(WIKT):
    mem = {c: members(c) for c in CATS}
    titles = sorted({t for v in mem.values() for t in v})
    json.dump({"members": mem, "pages": pages(titles)}, open(WIKT, "w"), ensure_ascii=False)
W = json.load(open(WIKT)); MEM, PAGES = W["members"], W["pages"]

LS_XML = os.path.join(RAW, "ls.xml")
if not os.path.exists(LS_XML):
    urllib.request.urlretrieve("https://raw.githubusercontent.com/PerseusDL/lexica/master/CTS_XML_TEI/perseus/pdllex/lat/ls/lat.ls.perseus-eng1.xml", LS_XML)

WD = os.path.join(RAW, "wikidata.json")
if not os.path.exists(WD):
    q = """SELECT ?item ?label ?type WHERE { VALUES ?type { wd:Q12308941 wd:Q11879590 wd:Q3409032 }
      ?item wdt:P31 ?type ; wdt:P407 wd:Q397 . ?item rdfs:label ?label FILTER(lang(?label)="en") }"""
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q})
    req = urllib.request.Request(url, headers={**UA, "Accept": "application/sparql-results+json"})
    open(WD, "wb").write(urllib.request.urlopen(req, timeout=120).read())
WDROWS = json.load(open(WD))["results"]["bindings"]
WDSEX = {"Q12308941": "b", "Q11879590": "g", "Q3409032": "e"}

# ── what the site already has ──
def storied():
    for f in sorted(os.listdir(DATA)):
        if f.endswith(".json") and f != "latin-names.json":
            try: d = json.load(open(os.path.join(DATA, f)))
            except Exception: continue
            if isinstance(d, list):
                for r in d:
                    if isinstance(r, list) and len(r) >= 6 and isinstance(r[0], str): yield f, r
SITE = {}      # folded → {"m": meaning or "", "lang": set, "files": set}
def note(n, m="", lang="", f=""):
    e = SITE.setdefault(fold(n), {"m": "", "lang": set(), "files": set(), "n": n})
    if m and not e["m"]: e["m"] = m
    if lang: e["lang"].add(lang)
    if f: e["files"].add(f)
for line in open(os.path.join(ROOT, "names.js"), encoding="utf-8"):
    p = line.rstrip("\n").split("|")
    if len(p) >= 6 and re.match(r"^[^\s/`]", p[0]) and p[1] in ("g", "b", "e"): note(p[0], p[5], p[3], "names.js")
for f, r in storied(): note(r[0], r[5] if isinstance(r[5], str) else "", r[3] if isinstance(r[3], str) else "", f)
MEANINGS = json.load(open(os.path.join(DATA, "meanings.json")))
DB = {}        # folded → (count, set of registries) from the birth registries
for f in ("names-db.tsv", "names-extra.tsv"):
    for line in open(os.path.join(DATA, f), encoding="utf-8"):
        p = line.rstrip("\n").split("\t")
        if len(p) < 4: continue
        k = fold(p[0]); c = int(p[3]) if p[3].isdigit() else 0
        old = DB.get(k, (0, set(), p[0]))
        DB[k] = (old[0] + c, old[1] | set(p[2].split(",")), old[2] if old[0] >= c else p[0])
ROMAN = {fold(r[0]): r for r in json.load(open(os.path.join(DATA, "roman-names.json")))}
def on_site(k): return k in SITE or k in DB
def site_meaning(k):
    m = (SITE.get(k) or {}).get("m") or (MEANINGS.get(k) or {}).get("m") or ""
    return m

# ── Lewis & Short ──
LS = {}        # plain lowercase headword → gloss (first sense's italic English words)
STOP = re.compile(r"^(lit|trop|absol|sup|comp|gen|dat|acc|abl|adj|adv|subst|fin|act|pass|neutr|plur|sing|poet|meton|transf|fig|i\. ?e|in gen|ib|al|sc|v|cf|esp|prop|class|freq|rare|init|dep|post-class|ante-class|m|f|n|id|in a good sense|in a bad sense)\.?$", re.I)
def _strip(s): return html.unescape(re.sub(r"<[^>]+>", "", s))
def ls_gloss(body):
    body = re.sub(r"<(cit|bibl|etym|foreign|quote)\b.*?</\1>", "", body, flags=re.S)
    senses = re.findall(r"<sense[^>]*>(.*?)</sense>", body, re.S) or [body]
    for s in senses:
        s = re.sub(r"\([^()]*\)", "", s)
        head = s.split(":")[0]
        its = [_strip(i).strip(" ,;.") for i in re.findall(r'<hi rend="ital">(.*?)</hi>', head, re.S)]
        its = [i for i in its if i and not STOP.match(i) and len(i) < 40 and "." not in i]
        if its: return ", ".join(dict.fromkeys(i[0].lower() + i[1:] if not i[:2].isupper() else i for i in its[:3]))
    return ""
for key, body in re.findall(r'<entryFree [^>]*key="([^"]+)"[^>]*>(.*?)</entryFree>', open(LS_XML, encoding="utf-8").read(), re.S):
    orth = re.search(r"<orth[^>]*>(.*?)</orth>", body)
    if not orth or not orth.group(1)[:1].islower(): continue          # proper names (Cassius…) are not root words
    k = lfold(re.sub(r"\d", "", key))
    if k in LS: continue                                                 # homographs: the first entry only
    g = ls_gloss(body)
    if g: LS[k] = g


# ── wikitext → text ──
LANGS = {"grc": "Ancient Greek", "grc-koi": "Koine Greek", "ett": "Etruscan", "osc": "Oscan", "xum": "Umbrian", "hbo": "Biblical Hebrew", "he": "Hebrew",
         "ine-pro": "Proto-Indo-European", "itc-pro": "Proto-Italic", "itc-ola": "Old Latin", "itc-ala": "Old Latin", "la": "Latin", "la-lat": "Late Latin",
         "la-vul": "Vulgar Latin", "la-med": "Medieval Latin", "la-eccl": "Ecclesiastical Latin", "la-new": "New Latin", "LL.": "Late Latin", "ML.": "Medieval Latin",
         "sbv": "Sabine", "itc-sbl": "Sabellic", "xvn": "Vandalic", "gem-pro": "Proto-Germanic", "frk": "Frankish", "goh": "Old High German", "cel-pro": "Proto-Celtic",
         "xtg": "Gaulish", "arc": "Aramaic", "en": "English", "enm": "Middle English", "it": "Italian", "es": "Spanish", "fr": "French", "fro": "Old French",
         "frm": "Middle French", "pt": "Portuguese", "de": "German", "ro": "Romanian", "ca": "Catalan", "pl": "Polish", "nl": "Dutch", "ru": "Russian"}
# an origin outside Latin and the Italic languages: Latin borrowed the name (Agatha, Rachel, Adalheidis)
FOREIGN = re.compile(r"^(grc|grc-koi|hbo|he|arc|gem|gem-pro|gmw-pro|frk|goh|got|ang|non|xvn|cel|cel-pro|xtg|sga|peo|fa|ar|syc|pl|cu|sla-pro|ka|hy|egy|cop|phn|akk|ira-pro|xlc|xpu|ine-pro-x)$")
HEDGE = re.compile(r"\b(possibl|perhaps|probabl|maybe|uncertain|unknown|obscure|disputed|likely|unclear|doubtful|conjectur|may be|might|traditionally|said to|folk|popular etymolog|however|or from|either|would|but some)\w*", re.I)
CHRIST = re.compile(r"\b(saint|saints|martyr|martyrs|pope|bishop|Christian|apostle|church|hermit|abbot|monk|nun)\b", re.I)
def tparams(inner):
    parts, depth, cur = [], 0, ""
    for ch in inner:
        if ch in "{[": depth += 1
        if ch in "}]": depth -= 1
        if ch == "|" and depth == 0: parts.append(cur); cur = ""
        else: cur += ch
    parts.append(cur)
    pos = [p for p in parts if not re.match(r"^\w+=", p)]
    kw = dict(p.split("=", 1) for p in parts if re.match(r"^\w+=", p))
    return pos, kw
def links(s): return re.sub(r"<[^>]*>", "", re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s))
def inline(word):  # fēlīx<t:happy> → (fēlīx, happy, uncertain?)
    t = re.search(r"<t:([^>]*)>", word); w = re.sub(r"<[^>]*>", "", word)
    return w.strip(), links(t.group(1)) if t else "", "<unc" in word
class Ety:
    def __init__(self): self.ment, self.foreign, self.hedged, self.srcs, self.text = [], False, False, [], ""
    def mention(self, lang, w, alt="", g="", unc=False):
        w, tg, u = inline(w); g = re.sub(r"”,\s*“", ", ", links(g or tg)).strip(" “”"); shown = re.sub(r"[<>]", "", links(alt or w)).strip()
        if u or unc: self.hedged = True
        if lang == "la" and not self.hedged: self.ment.append((shown, g))
        return shown + (f" “{g}”" if g else "")
    def tpl(self, inner):
        pos, kw = tparams(inner); name = pos[0].strip(); args = pos[1:]
        if name in ("m", "l", "mention", "link", "l-self", "ll", "m+", "from"):
            if len(args) >= 2 and (args[1] or (len(args) > 2 and args[2])): return self.mention(args[0], args[1], args[2] if len(args) > 2 else "", kw.get("t") or kw.get("gloss") or (args[3] if len(args) > 3 else ""))
            return ""
        if name in ("der", "bor", "inh", "uder", "lbor", "der+", "bor+", "inh+", "slbor", "obor", "learned borrowing", "cog", "ncog", "noncog", "calque", "psm", "translit"):
            if name in ("cog", "ncog", "noncog"): lang, rest = (args[0] if args else ""), args[1:]
            else:
                lang, rest = (args[1] if len(args) > 1 else ""), args[2:]
                if FOREIGN.match(lang): self.foreign = True
                if name not in ("calque", "psm", "translit"): self.srcs.append(lang)
            lab = LANGS.get(lang, "")
            if not rest or rest[0] in ("", "-"): return lab
            word = self.mention(lang, rest[0], rest[1] if len(rest) > 1 else "", kw.get("t") or kw.get("gloss") or (rest[2] if len(rest) > 2 else ""))
            return (lab + " " + word).strip()
        if name in ("suffix", "suf", "af", "affix", "prefix", "pre", "compound", "com", "surf", "confix"):
            lang = args[0] if args else ""; words = []
            for i, a in enumerate(args[1:], 1):
                if a: words.append(self.mention(lang, a, kw.get(f"alt{i}", ""), kw.get(f"t{i}") or kw.get(f"gloss{i}", "")))
            return " + ".join(words)
        if name in ("ety", "etymon"):
            return self.ety_tpl(args, kw)
        if name in ("coin", "coinage"): return "coined by " + links(args[1] if len(args) > 1 else "")
        if name in ("w", "W", "wp"): return links(args[1] if len(args) > 1 else (args[0] if args else ""))
        if name in ("lit", "literally"): return "literally “" + links(args[0] if args else "") + "”"
        if name in ("gloss", "gl"): return "(“" + (args[0] if args else "") + "”)"
        if name in ("taxlink", "vern", "q", "qualifier", "i", "ng", "non-gloss", "smallcaps"): return links(args[-1] if args else "")
        if name in ("unc", "uncertain", "rfe"): self.hedged = True
        return ""
    def ety_tpl(self, args, kw):
        """{{ety|la|:af|aureus<t:golden>|-ius|text=+}} → "From aureus “golden” + -ius" """
        lang, groups = (args[0] if args else "la"), []
        for a in args[1:]:
            if a.startswith(":"):
                op = re.sub(r"<[^>]*>", "", a[1:]); groups.append([op, []])
                if "<unc" in a: self.hedged = True
            elif groups and a: groups[-1][1].append(a)
        out = []
        for op, items in groups:
            words = []
            for it in items:
                if re.sub(r"<[^>]*>", "", it).split(":")[-1] in ("", "-"): continue
                ln, w = (it.split(":", 1) if re.match(r"^[a-z-]{2,10}:", it) else (lang, it))
                if op in ("der", "bor", "inh", "lbor", "uder"):
                    self.srcs.append(ln)
                    if FOREIGN.match(ln): self.foreign = True
                shown = self.mention(ln, w)
                words.append((LANGS.get(ln, "") + " " + shown).strip() if ln != "la" else shown)
            if words: out.append(" + ".join(words))
        return ("From " + ", from ".join(out)) if out else ""
def ety_text(s):
    """an Etymology section → (first sentence as text, Ety)"""
    e = Ety()
    s = re.sub(r"<ref[^>]*/>|<ref.*?</ref>|<!--.*?-->", "", s, flags=re.S)
    lines = [l for l in s.strip().split("\n") if l.strip() and not l.lstrip().startswith(("{{root|", "{{wp", "{{wikipedia", "{{rfv", "[[Category", "{{was fwotd", "{{also", "*", "[[File:", "[[Image:", "{{commonscat", "{{multiple images"))]
    # a structured {{ety}} / {{etymon}} line without text=+ only feeds the prose that follows it
    prose = [l for l in lines if not (re.match(r"^\{\{(ety|etymon)\|", l.strip()) and "text=" not in l)]
    if not prose: prose = lines
    if not prose: return "", e
    txt = prose[0]
    for _ in range(5):
        txt2 = re.sub(r"\{\{([^{}]*)\}\}", lambda mo: e.tpl(mo.group(1)), txt)
        if txt2 == txt: break
        txt = txt2
    txt = links(txt).replace("'''", "").replace("''", "")
    txt = re.sub(r"\s+", " ", re.sub(r"\(\s*[,;]?\s*\)", "", txt)).strip(" ,;")
    txt = re.sub(r"\.(\s*\.)+", ".", re.sub(r"\s+([,.;:])", r"\1", txt)).strip(" ,;.")
    # the sentences up to the first that names a Latin word (at most two): "From Old French; the name of a martyr, from Latin Quīntīnus…"
    sents = re.split(r"(?<!\bSt)(?<!\bcf)(?<=[a-z”)\]\-\d'\"])\. (?=[A-Z])", txt)
    keep = sents[:1]
    if e.ment and not any(w in sents[0] for w, g in e.ment) and len(sents) > 1 and any(w in sents[1] for w, g in e.ment):
        # "From Old French. The name of a martyr, from Latin Quīntīnus…" keeps both; "In use since 1500. French Claude, from…" only the second
        # …but "Transferred from a surname. Also partially from Latin dexter" is not a Latin name: the first sentence is the origin
        keep = sents[:2] if re.match(r"(?i)from\b", sents[0]) else [] if re.search(r"surname|\bfrom (the |a |an )?[A-Z]|derived|borrowed|form of|variant of", sents[0], re.I) else sents[1:2]
    if not keep: e.ment = []; return "", e
    low1 = lambda k: k[0].lower() + k[1:] if re.match(r"(The|A|An|Name|From|Feminine|Masculine|Diminutive|Variant)\b", k) else k
    txt = "; ".join([keep[0].rstrip(".")] + [low1(k).rstrip(".") for k in keep[1:]])
    e.ment = [(w, g) for w, g in e.ment if w and w in txt]
    # a template this script cannot render leaves a hole ("the given names are s of ie"), a list of theories ends in a colon: no text then
    if re.search(r"#|\s-\s|\bthe of\b|\bs of\b|from [(;,]|^from$|: \(|:$|\(\s*\)|\+\s*[+,;]", txt, re.I): txt, e.ment = "", []
    if HEDGE.search(txt): e.hedged = True
    e.text = txt
    return txt, e
def section(text, lang):
    m = re.search(r"(?:^|\n)==%s==\n(.*?)(?=\n==[^=]|\Z)" % re.escape(lang), text, re.S); return m.group(1) if m else ""
def etymologies(sec):
    return re.findall(r"===+Etymology[^=]*===+\n(.*?)(?=\n===|\Z)", sec, re.S)
def gloss_of(e):
    """the meaning: the first Latin word the etymology glosses, else the Lewis & Short gloss of the first Latin common word"""
    if e.hedged: return "", ""
    for i, (w, g) in enumerate(e.ment):
        if g and not w.startswith("-"):
            nxt = e.ment[i + 1] if i + 1 < len(e.ment) else None      # a compound: Aenobarbus, from aēnus “copper” and barba “beard”
            if nxt and nxt[1] and not nxt[0].startswith("-") and not re.search(r"suffix|^-", nxt[1]) and e.text and re.search(re.escape(f"{w} “{g}”") + r" (and|\+) " + re.escape(nxt[0]), e.text):
                return f"{g} + {nxt[1]}", "Wiktionary"
            return g, "Wiktionary"
    for w, g in e.ment:
        if w[:1].islower() and not w.startswith("-"):
            lg = LS.get(lfold(plain(w)))
            return (lg, "Lewis & Short") if lg else ("", "")
    return "", ""

# ── Latin entries ──
KIND = {"Latin praenomina": "praenomen", "Latin nomina gentilia": "nomen", "Latin cognomina": "cognomen",
        "Latin male given names": "given-b", "Latin female given names": "given-g"}
def make_entry(t, text, kinds):
    sec = section(text, "Latin")
    if not sec or not re.search(r"\{\{(la-proper noun|head\|la\|proper noun)|===Proper noun===", sec): return None
    head = re.search(r"\{\{la-(?:proper )?noun\|([^}]*)\}\}", sec)
    pos, kw = tparams(head.group(1)) if head else ([t], {})
    lemma = re.split(r"[<\/]", pos[0])[0].strip() if pos and pos[0] else t
    if not plain(lemma).isalpha(): lemma = t
    fem = re.split(r"[<\/]", kw.get("f", ""))[0].strip()
    defs = " ".join(re.findall(r"^#[^:*].*", sec, re.M))
    ety, e = ety_text((etymologies(sec) or [""])[0])
    froms = [f.strip() for f in re.findall(r"from=([^|}]+)", defs)]
    if any(f and f not in ("Latin", "Late Latin", "Etruscan", "Oscan", "Sabine", "Umbrian", "Old Latin") for f in froms): e.foreign = True
    if not ety and re.search(r"character in|Plautus|Terence|mythology", defs): e.foreign = True    # a play's Greek character
    # a Latin page's etymology that runs through any language outside Latin and its Italic neighbours: a borrowed name (Isabella ← Spanish)
    if any(not re.match(r"^(la|la-\w+|itc|itc-\w+|ett|osc|xum|sbv|ine-pro|ine|LL\.|ML\.)$", l) for l in e.srcs if l): e.foreign = True
    m, cite = gloss_of(e)
    return dict(title=t, lemma=lemma, kinds=kinds, gender=kw.get("g", ""), fem=fem, defs=defs, ety=ety, e=e, m=m, cite=cite,
                roman=any(k in ("praenomen", "nomen", "cognomen") for k in kinds))
cats_of = {}
for c, ts in MEM.items():
    for t in ts: cats_of.setdefault(t, []).append(KIND[c])
WDX = os.path.join(RAW, "wikidata-pages.json")
wd_extra = {}
for b in WDROWS:
    lab = b["label"]["value"]
    if lab not in cats_of and re.fullmatch(r"[A-Za-zÀ-ÿĀ-ž]+", lab): wd_extra[lab] = WDSEX.get(b["type"]["value"].rsplit("/", 1)[-1], "")
if not os.path.exists(WDX): json.dump(pages(sorted(wd_extra)), open(WDX, "w"), ensure_ascii=False)
WDP = json.load(open(WDX))
for t, sx in wd_extra.items():
    sec = section(WDP.get(t, ""), "Latin")
    # only a Latin page that calls it a person's name (not Terra the goddess or Libra the constellation)
    if sx in ("b", "g") and "{{la-proper noun" in sec and re.search(r"given name|cognomen|praenomen|nomen|gens", " ".join(re.findall(r"^#.*", sec, re.M))):
        PAGES[t] = WDP[t]; cats_of[t] = ["given-" + sx, "wikidata"]
WIKIDATA_ONLY = {t for t, k in cats_of.items() if "wikidata" in k}
ENTRIES, BORROWED = [], set()     # BORROWED: Latin names that Latin itself took from Greek, Hebrew… (Lūcās, Agatha)
for t, kinds in cats_of.items():
    ent = make_entry(t, PAGES.get(t, ""), kinds)
    if not ent: continue
    if ent["e"].foreign: BORROWED.add(lfold(plain(ent["lemma"])))
    # names Latin borrowed from Greek, Hebrew, Germanic… are not Latin names; Roman family names stay whatever their roots
    if ent["e"].foreign: continue
    ENTRIES.append(ent)
BYLATIN = {}
for ent in ENTRIES:
    BYLATIN.setdefault(lfold(plain(ent["lemma"])), ent)

# ── EDH bearer counts ──
EDH = {}       # (lfold name, sex M|W) → people
PRAE = {"a": "aulus", "ap": "appius", "c": "gaius", "cn": "gnaeus", "d": "decimus", "l": "lucius", "m": "marcus", "m'": "manius", "mam": "mamercus",
        "n": "numerius", "p": "publius", "q": "quintus", "ser": "servius", "sex": "sextus", "s": "spurius", "sp": "spurius", "t": "titus", "ti": "tiberius", "v": "vibius"}
for r in csv.DictReader(open(os.path.join(ROOT, "raw", "roman", "edh_data_pers.csv"), encoding="utf-8")):
    if r["status"].startswith("0"): continue
    sx = r["geschlecht"][:1]
    if sx not in ("M", "W"): continue
    seen = set()
    pr = re.sub(r"[+*?\s]", "", r["praenomen"]).rstrip(".").lower()
    if pr in PRAE: seen.add(lfold(PRAE[pr]))
    for f in ("nomen", "cognomen", "supernomen"):
        for w in re.sub(r"\(.*?\)", " ", r[f]).split():
            w = re.sub(r"[^A-Za-z]", "", w)
            if len(w) > 1: seen.add(lfold(w))
    for w in seen: EDH[(w, sx)] = EDH.get((w, sx), 0) + 1
def edh(word, sx): return EDH.get((lfold(plain(word)), "W" if sx == "g" else "M"), 0)

# ── the form people use today, and how easy it is to spell ──
ENGLISH = {"us", "uk", "ca", "au", "ie", "nir"}
def db_count(k): return DB.get(k, (0, set(), ""))[0]
def modern(latin):
    p = plain(latin); j = re.sub(r"^I(?=[aeiou])", "J", p)
    cands = [p, j] + [x[:-2] for x in (p, j) if re.search(r"(an|in)us$", x) and len(x) > 6]   # Cassianus → Cassian, Iulianus → Julian
    if db_count(fold(p)) >= 50: return p
    best = max(cands, key=lambda c: db_count(fold(c)))
    return best if db_count(fold(best)) >= 50 else p
def ease(n):
    cnt, regs, _ = DB.get(fold(n), (0, set(), ""))
    if not n.isascii(): return 3
    if re.search(r"ae|oe|ii|uu|ei|q(?!u)|^.{11,}|x[^aeiou]", n.lower()): return 3
    if len(regs & ENGLISH) >= 2 and cnt >= 50: return 1
    return 2

# ── sentences ──
def fmt(n): return f"{n:,}"
def edh_phrase(word, sx):
    if sx == "e":
        w, m = edh(word, "g"), edh(word, "b")
        if not (w or m): return ""
        both = " and ".join(x for x in (f"{fmt(w)} {'woman' if w == 1 else 'women'}" if w else "", f"{fmt(m)} {'man' if m == 1 else 'men'}" if m else "") if x)
        return f"borne by {both} on Roman inscriptions (Epigraphic Database Heidelberg)"
    c = edh(word, sx)
    if not c: return ""
    who = ("man" if c == 1 else "men") if sx != "g" else ("woman" if c == 1 else "women")
    return f"borne by {fmt(c)} {who} on Roman inscriptions (Epigraphic Database Heidelberg)"
KINDTXT = {"praenomen": "a Roman first name (praenomen)", "nomen": "a Roman family name (nomen gentile)", "cognomen": "a Roman surname (cognomen)"}
LANGSTART = re.compile(r"^(" + "|".join(sorted({v for v in LANGS.values()}, key=len, reverse=True)) + r") (?!form|name|variant|diminutive|feminine|masculine|equivalent|spelling|version|given|and)\S")
def show_gloss(text, ment, m, cite):
    """when the meaning is Lewis & Short's, put it after the word in the sentence"""
    if cite != "Lewis & Short" or not m: return text
    for w, g in ment:
        if w[:1].islower() and not w.startswith("-") and w in text and f"{w} “" not in text:
            return text.replace(w, f"{w} “{m}”", 1)
    return text
def lead_from(ety, lemma, cite, hedged, see_gloss=""):
    """"A Latin name, from fēlīx “lucky, happy” (Wiktionary)" — the etymology as Wiktionary gives it"""
    cite = cite or "Wiktionary"
    if not ety or len(ety) > 230: return f"A Latin name, from Latin {lemma}"
    m = re.match(r"(?i)see (\S+)$", ety)
    if m: return f"A Latin name, from the Latin word {m.group(1)}" + (f" “{see_gloss}”" if see_gloss else "") + f" ({cite})"
    low = ety[0].lower() + ety[1:]
    if LANGSTART.match(ety): ety = low = "from " + ety
    if re.match(r"(?i)from\b", ety) and not hedged: return f"A Latin name, {low} ({cite})"
    if re.match(r"(?i)from\b", ety): return f"A Latin name. Wiktionary on its origin: {ety}"
    return f"A Latin name, from Latin {lemma}. {ety} ({cite})"
def sentence(ent, form, sx, fem=None):
    lemma = fem or ent["lemma"]
    if fem:
        chain = ent["ety"] and not ent["e"].hedged and len(ent["ety"]) < 200
        lead = f"A Latin name, from {fem}, the women's form of the Roman name {ent['lemma']}"
        if chain: lead += (f"; {ent['lemma']} is " if re.match(r"(?i)from\b", ent["ety"]) else f"; {ent['lemma']}: ") + show_gloss(ent["ety"][0].lower() + ent["ety"][1:], ent["e"].ment, ent["m"], ent["cite"]) + f" ({ent['cite'] or 'Wiktionary'})"
        elif ent.get("fem_src") != "EDH": lead += " (Wiktionary)"
    else: lead = lead_from(show_gloss(ent["ety"], ent["e"].ment, ent["m"], ent["cite"]), lemma, ent["cite"], ent["e"].hedged, ent["m"])
    bits = []
    if plain(lemma) != form and not lead.startswith(f"A Latin name, from Latin {lemma}") and not fem: bits.append(f"written {lemma} in Latin")
    kinds = [KINDTXT[k] for k in ("praenomen", "nomen", "cognomen") if k in ent["kinds"]]
    if kinds and not fem: bits.append(" and ".join(kinds))
    if re.search(r"saint|martyr", ent["defs"], re.I): bits.append("a name of early saints")
    elif CHRIST.search(ent["defs"]): bits.append("a name of the early Church")
    ep = edh_phrase(lemma, sx)
    if ep: bits.append(ep)
    return (lead + ("; " + "; ".join(bits) if bits else "") + ".").replace("..", ".")

rows, info = {}, {}
def put(name, sex, rel, meaning, sent, latin, how):
    k = fold(name)
    # Maria is also the women's form of the Roman Marius, but the name people use is the Hebrew one Latin borrowed: leave it
    if lfold(name) in BORROWED or lfold(plain(latin)) in BORROWED: return
    if meaning and not all(f"“{m}”" in sent for m in meaning.split(" + ")): meaning = ""          # a meaning always shows where it comes from
    if k in rows:
        r = rows[k]
        if r[1] != sex and {r[1], sex} == {"g", "b"} and info[k]["how"] != "feminine" and how != "feminine": r[1] = "e"
        if not r[5] and meaning: r[5], r[6] = meaning, sent
        return
    rows[k] = [name, sex, "Latin", "Latin", rel, meaning, sent, "", "real", [], ease(name)]
    info[k] = dict(latin=latin, how=how + (":wikidata" if plain(latin) in WIKIDATA_ONLY else ""))

# 1. names from the categories (and Wikidata)
for ent in sorted(ENTRIES, key=lambda e: (not e["roman"], e["title"])):
    kinds = ent["kinds"]
    if not ent["roman"] and not ent["ety"] and not edh(ent["lemma"], "g" if "given-g" in kinds else "b") and fold(modern(ent["lemma"])) not in SITE:
        continue   # a bare listing: no origin, no bearer, nothing to say
    sx = "g" if ("given-g" in kinds or ent["gender"] == "f") else "b"
    form = modern(ent["lemma"])
    rel = "Christian" if CHRIST.search(ent["defs"]) else ""
    put(form, sx, rel, ent["m"], sentence(ent, form, sx), ent["lemma"], "category")
    # the women's form of a Roman name: kept when women bore it (EDH) or Wiktionary lists it as a woman's name
    if not ent["fem"] and sx == "b" and ent["roman"] and plain(ent["lemma"]).endswith("us") and edh(ent["lemma"][:-2] + "a", "g") >= 3:
        ent["fem"], ent["fem_src"] = ent["lemma"][:-2] + "a", "EDH"          # Sevērus → Sevēra: women bore it on inscriptions
    if ent["fem"] and sx == "b" and (edh(ent["fem"], "g") or plain(ent["fem"]) in MEM["Latin female given names"]):
        fform = modern(ent["fem"])
        put(fform, "g", rel, ent["m"], sentence(ent, fform, "g", fem=ent["fem"]), ent["fem"], "feminine")

# a Roman name spelled like a name the site has for another reason (the cognomen Pera, "wallet", and Pera the Catalan Peter) says
# nothing about that name: unless the site already ties the name to Latin, the name's own Wiktionary page has to (step 2)
def latin_tied(k): return k in ROMAN or "Latin" in (SITE.get(k) or {}).get("lang", set()) or (MEANINGS.get(k) or {}).get("root") == "Latin"
# (a longer name that Roman men or women bore at least 5 times on inscriptions is taken to be the Roman one: Valens, Romana, Novia)
homographs = [rows[k][0] for k in list(rows) if (k in SITE or k in DB) and not latin_tied(k)
              and not (len(k) >= 5 and edh(info[k]["latin"], rows[k][1] if rows[k][1] != "e" else "b") >= 5)]
for n in homographs: del rows[fold(n)]

# 2. names the site already has that come from Latin: the etymology on each name's own Wiktionary page
cands = set(homographs)
for k, e in SITE.items():
    if "Latin" in e["lang"] or k in ROMAN: cands.add(e["n"])
for k, v in MEANINGS.items():
    if v.get("root") == "Latin" and k in SITE: cands.add(SITE[k]["n"])
cands = sorted(c for c in cands if fold(c) not in rows and re.fullmatch(r"[A-Za-zÀ-ÿĀ-ž]+", c))
SP = os.path.join(RAW, "site-pages.json")
sp = json.load(open(SP)) if os.path.exists(SP) else {}
todo = [c for c in cands if c not in sp]
if todo: sp.update(pages(todo)); json.dump(sp, open(SP, "w"), ensure_ascii=False)
SECTIONS = ("English", "Latin", "Italian", "Spanish", "Portuguese", "French", "German", "Romanian", "Catalan", "Polish", "Dutch")
def site_sex(sec):
    s = set()
    for m in re.finditer(r"\{\{given name\|[^}]*\}\}", sec):
        t = m.group(0)
        if re.search(r"\|(gender=)?(unisex|male or female|female or male)\b", t): s |= {"g", "b"}
        elif re.search(r"\|(gender=)?female\b", t): s.add("g")
        elif re.search(r"\|(gender=)?male\b", t): s.add("b")
    for m in re.finditer(r"\{\{la-proper noun[^}]*g=([mf])", sec): s.add("b" if m.group(1) == "m" else "g")
    return "e" if s == {"g", "b"} else (s.pop() if s else "")
def latin_mention(sec):
    """the first etymology in a section that comes from Latin: (text, Ety, first Latin word)"""
    for raw in etymologies(sec):
        ety, e = ety_text(raw)
        if e.ment and not e.foreign: return ety, e
    return None
# a Latin name mentioned on those pages (Victoria → Latin Victōria) gets its own Latin page, for its etymology
LX = os.path.join(RAW, "latin-pages.json")
lx = json.load(open(LX)) if os.path.exists(LX) else {}
want = set()
for n in cands:
    for lang in SECTIONS:
        sec = section(sp.get(n, ""), lang)
        hit = sec and latin_mention(sec)
        if hit:
            w = hit[1].ment[0][0]
            if w[:1].isupper() and lfold(plain(w)) not in BYLATIN and lfold(plain(w)) not in BORROWED: want.add(plain(w))
            break
todo = sorted(w for w in want if w not in lx and w not in PAGES)
if todo: lx.update(pages(todo)); json.dump(lx, open(LX, "w"), ensure_ascii=False)
for t, text in lx.items():
    ent = make_entry(t, text, ["given"])
    if ent and ent["e"].foreign: BORROWED.add(lfold(plain(ent["lemma"])))
    elif ent: BYLATIN.setdefault(lfold(plain(ent["lemma"])), ent)
HOMO = {fold(n) for n in homographs}
for n in cands:
    text = sp.get(n, "")
    for lang in SECTIONS:
        if lang == "Latin" and fold(n) in HOMO: continue     # the Roman Pera's page says nothing about the Catalan Pera
        sec = section(text, lang)
        if not sec or not re.search(r"given name|proper noun", sec, re.I): continue
        hit = latin_mention(sec)
        if not hit: continue
        ety, e = hit
        first_latin = ety.find(e.ment[0][0])
        if re.search(r"folk etymolog|pet form", ety, re.I) and e.hedged: break
        if re.search(r"\bGreek\b", ety) and not re.search(r"unetymological", ety): break      # Ulysses ← Ulyssēs ← Greek Ὀδυσσεύς
        if re.search(r"\b(Greek|Hebrew|Russian|Germanic|German|Frankish|Aramaic|Arabic|Celtic|Gaulish|Old English|Old Norse|Gothic|Persian|Slavic)\b", ety[:first_latin]): break
        sx = site_sex(sec)
        if not sx: break
        m, cite = gloss_of(e)
        w = e.ment[0][0]; via = BYLATIN.get(lfold(plain(w)))
        if lfold(plain(w)) in BORROWED: break          # Lukas ← Latin Lūcās ← Greek Λουκᾶς: not a Latin name
        chain = ""
        if not m and via and via["m"] and not e.hedged and not via["e"].hedged and w[:1].isupper() \
                and via["ety"] and re.match(r"(?i)from\b", via["ety"]) and len(via["ety"]) < 160:      # Lucia ← Lūcia ← Lūcius, from lūx “light”
            m, cite = via["m"], via["cite"]
            chain = f"; Latin {via['lemma']} is " + via["ety"][0].lower() + via["ety"][1:]
        if len(ety) > 230 or not ety: break
        ety = show_gloss(ety, e.ment, m, cite)
        low = ety[0].lower() + ety[1:]
        if LANGSTART.match(ety): ety = low = "from " + ety
        if e.hedged: sent = f"A Latin name. Wiktionary on its origin: {ety}"
        elif re.match(r"(?i)(ultimately |borrowed |a )?(from|borrowing|borrowed|learned borrowing)\b", ety): sent = f"A Latin name, {low}{chain} ({cite or 'Wiktionary'})"
        else: sent = f"A Latin name, from Latin {w}. {ety}{chain} ({cite or 'Wiktionary'})"
        ep = edh_phrase(w, sx) if lfold(plain(w)) in (lfold(n), lfold(n) + "us") else ""     # Cassian ← Cassiānus
        if ep: sent += "; " + ep
        rel = "Christian" if re.search(r"\b(saint|saints|martyr|martyrs|pope|Christian)\b", ety, re.I) else ""
        put(n, sx, rel, m, sent + ".", w, "site-page:" + lang)
        break

# ── keep what adds something; easy names first ──
out = []
for k, r in rows.items():
    exists = k in SITE or k in DB
    had = bool(site_meaning(k))
    if not r[5] and re.fullmatch(r"A Latin name(, from Latin \S+)?(; [^;]*(praenomen|nomen gentile|cognomen)\))*\.", r[6]): continue   # nothing to say
    info[k].update(exists=exists, had=had, edh=edh(info[k]["latin"], r[1]))
    out.append(r)
out.sort(key=lambda r: (r[10], -db_count(fold(r[0])), -info[fold(r[0])]["edh"], r[0]))
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
json.dump({fold(r[0]): info[fold(r[0])] for r in out}, open(os.path.join(RAW, "report.json"), "w"), ensure_ascii=False, indent=0)
new = [r for r in out if not info[fold(r[0])]["exists"]]
added = [r for r in out if info[fold(r[0])]["exists"] and r[5] and not info[fold(r[0])]["had"]]
print(f"{len(out)} rows → {os.path.relpath(OUT, ROOT)}: {len(new)} new names, {len(out) - len(new)} the site already has "
      f"({len(added)} of them get a meaning they lacked); {sum(1 for r in out if r[5])} rows with a meaning")
