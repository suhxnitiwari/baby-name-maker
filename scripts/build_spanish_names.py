# Names of Spain's languages (and the indigenous languages of Latin America) → data/spanish-names.json, one row per name
# per culture, in the row format of data/culture-names.json: [name, g, culture, language, religions, meaning, story, texts, kind, also].
#
# A name gets a row in a culture when a source says it is a name in that language:
#   Wiktionary (CC BY-SA 4.0): the given-name categories of the English, Spanish, Catalan, Galician, Basque and Asturian
#     editions (raw/spanish/wikt-*.json, fetch_spanish_sources.py; raw/wikt/{Catalan,Galician,Basque,Quechua,Nahuatl,
#     Guarani,Aymara}.json, fetch_wiktionary_names.py). Only the English edition's etymology is used for meanings.
#   Wikidata (CC0): given-name items tagged with the language (P407), raw/spanish/wd-given-names.json.
#   Official lists (raw/spanish/<eu|gl|ca|ast|an>-*.tsv, fetch_spanish_regional.py): Euskaltzaindia's Izendegia, the Real
#     Academia Galega's Galician names, and the other normative lists found; their own explanation is quoted, untranslated.
#   Literature (raw/spanish/lit-attestations.tsv, fetch_spanish_literature.py): characters named in public-domain Spanish,
#     Catalan and Galician works, attested with work and passage. A name printed in a Spanish text is recorded as used
#     there, not as Spanish by origin.
#   History (raw/spanish/wd-iberian-royals.json): people of the medieval Iberian kingdoms with a title, office or house,
#     born or died before 1600, by the first word of their Spanish (or, for the Catalan-speaking lands, Catalan) label.
# INE's count of residents (raw/spanish/ine-*.xlsx, 1 January 2025) is added to the story of names that have a row; a name
# only on INE's list (used in Spain) gets no row, since being used in Spain doesn't make a name Spanish.
#
#   python3 scripts/build_spanish_names.py
import collections, csv, glob, json, os, re, sys, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "raw", "spanish"); WIKT = os.path.join(ROOT, "raw", "wikt"); OUT = os.path.join(ROOT, "data", "spanish-names.json")
sys.path.insert(0, HERE)
import xlsx
from build_cultures import section, details, clean

NAME = re.compile(r"^[A-ZÀ-ÖØ-ÞĀ-ſ][A-Za-zÀ-ÖØ-öø-ɏḀ-ỿ'’·\-]*$")      # one capitalised word (Núria, Pau·la is not a name, Pere-Joan is)
def fold(s): return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn").replace("·", "")
def ok(n): return bool(n) and NAME.match(n) and 2 <= len(n) <= 24 and "·" not in n.strip("·")

# culture → (language, also-baskets)
IA = ["Indigenous American"]
CULT = {"Spanish": ("Spanish", []), "Catalan": ("Catalan", []), "Galician": ("Galician", []), "Basque": ("Basque", []),
        "Asturian": ("Asturian", []), "Aragonese": ("Aragonese", []), "Ladino": ("Ladino", ["Jewish"]),
        "Quechua": ("Quechua", IA), "Nahua": ("Nahuatl", IA), "Guarani": ("Guarani", IA), "Mapuche": ("Mapudungun", IA), "Aymara": ("Aymara", IA)}

E = {}            # (culture, fold) → entry
def entry(culture, name):
    k = (culture, fold(name))
    if k not in E: E[k] = {"forms": collections.Counter(), "sex": {}, "meaning": "", "ety": "", "notes": [], "src": set(), "lit": [], "hist": [], "official": [], "texts": [], "lang": ""}
    E[k]["forms"][name] += 1
    return E[k]
PRI = {"official": 0, "wikt-en": 1, "wikt": 2, "ine": 3, "wikidata": 4, "royal": 5, "lit": 6}
def sex(e, src, g):
    if g in ("b", "g", "e"): e["sex"].setdefault(src, set()).add(g)

# ── Wiktionary etymology, rendered as text ──
LN = {"es": "Spanish", "osp": "Old Spanish", "la": "Latin", "LL.": "Late Latin", "la-lat": "Late Latin", "la-med": "Medieval Latin", "ML.": "Medieval Latin", "la-vul": "Vulgar Latin",
      "VL.": "Vulgar Latin", "grc": "Ancient Greek", "el": "Greek", "gkm": "Byzantine Greek", "he": "Hebrew", "hbo": "Biblical Hebrew", "arc": "Aramaic", "ar": "Arabic", "xaa": "Andalusian Arabic",
      "eu": "Basque", "xaq": "Aquitanian", "ca": "Catalan", "gl": "Galician", "pt": "Portuguese", "roa-opt": "Old Galician-Portuguese", "fr": "French", "fro": "Old French",
      "pro": "Old Occitan", "oc": "Occitan", "it": "Italian", "de": "German", "en": "English", "ast": "Asturian", "an": "Aragonese", "lad": "Ladino", "gem": "Germanic",
      "gem-pro": "Proto-Germanic", "got": "Gothic", "frk": "Frankish", "goh": "Old High German", "gmw-pro": "Proto-West Germanic", "cel": "Celtic", "cel-pro": "Proto-Celtic",
      "xce": "Celtiberian", "sa": "Sanskrit", "fa": "Persian", "qu": "Quechua", "nah": "Nahuatl", "nci": "Classical Nahuatl", "gn": "Guarani", "ay": "Aymara", "arn": "Mapudungun",
      "ine-pro": "Proto-Indo-European", "itc-pro": "Proto-Italic", "ett": "Etruscan", "ga": "Irish", "cy": "Welsh", "ru": "Russian", "pl": "Polish", "hu": "Hungarian",
      "tr": "Turkish", "ja": "Japanese", "yi": "Yiddish", "sem": "Semitic", "roa-oca": "Old Catalan", "roa-ole": "Old Leonese", "roa-oan": "Navarro-Aragonese", "egy": "Egyptian",
      "phn": "Phoenician", "xib": "Iberian", "qsb-xib-euq": "pre-Roman (Basque-Iberian)", "qfa-sub-ibe": "pre-Roman Iberian substrate", "akk": "Akkadian", "syc": "Classical Syriac", "nl": "Dutch", "sv": "Swedish", "no": "Norwegian", "da": "Danish", "non": "Old Norse", "ang": "Old English"}
def word(args):
    # positional args after the language codes: word, alt, gloss; named t=/gloss=
    pos = [a for a in args if "=" not in a]; kw = dict(a.split("=", 1) for a in args if "=" in a)
    w = (pos[1] if len(pos) > 1 and pos[1] else pos[0] if pos else "")
    alt = pos[2] if len(pos) > 2 and pos[2] else ""
    gl = kw.get("t") or kw.get("gloss") or (pos[3] if len(pos) > 3 else "")
    out = alt or w
    if gl: out += f" (“{clean(gl)}”)"
    return out.strip()
def render(t):
    def tpl(m):
        parts = m.group(1).split("|"); name, args = parts[0].strip(), [p.strip() for p in parts[1:]]
        if name in ("inh", "der", "bor", "lbor", "uder", "obor", "slbor", "cal", "inh+", "der+", "bor+", "uder+", "cog", "noncog", "ncog"):
            a = args[1:] if name not in ("cog", "noncog", "ncog") else args
            lang = LN.get(a[0], "") if a else ""
            w = word([x for x in a[1:]] and [a[0]] + a[1:])
            w = word(a) if a else ""
            pre = {"inh+": "Inherited from ", "der+": "Derived from ", "bor+": "Borrowed from ", "uder+": "Derived from "}.get(name, "")
            return (pre + lang + (" " + w if w and w != "-" else "")).strip()
        if name in ("m", "l", "mention", "link", "l-self", "m-self"): return word(args)
        if name in ("af", "affix", "compound", "com", "suffix", "prefix", "confix", "blend"):
            ws = [word(["x", a]) for a in args[1:] if "=" not in a and a]
            return " + ".join(ws)
        if name in ("gloss", "gl"): return f"(“{clean(args[0])}”)" if args else ""
        if name in ("lit", "literally"): return f"literally “{clean(args[0])}”" if args else ""
        if name in ("q", "qual", "qualifier", "i"): return f"({args[0]})" if args else ""
        if name in ("pronunciation spelling",): return f"pronunciation spelling of {args[1]}" if len(args) > 1 else ""
        if name in ("short for", "clipping", "clip", "abbreviation of", "ellipsis of", "diminutive of", "dim", "hypocorism of"):
            return {"dim": "diminutive of", "clip": "clipping of"}.get(name, name) + " " + (args[1] if len(args) > 1 else "")
        if name in ("unknown", "unk"): return "Of unknown origin" if not any(a.startswith("title=") for a in args) else "Of uncertain origin"
        if name in ("uncertain", "unc"): return "Of uncertain origin"
        if name in ("etyl",): return LN.get(args[0], "") if args else ""
        if name in ("w", "wikipedia", "lw"): return args[-1] if args else ""
        return ""
    for _ in range(3): t = re.sub(r"\{\{([^{}]*)\}\}", tpl, t)
    t = re.sub(r"<ref.*?(</ref>|/>)", "", t, flags=re.S)
    t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", t); t = re.sub(r"'''?|<[^>]+>|\{\{.*|\}\}", "", t)
    t = re.sub(r"\s+", " ", t).strip(" ,;:")
    t = re.sub(r"^[,.;: ]+", "", t)
    return t
def ety(sec):
    m = re.search(r"(?ms)^===+\s*Etymology[^=]*===+\s*$(.*?)(?=^==)", sec + "\n==")
    if not m: return ""
    t = render(m.group(1).strip().split("\n\n")[0])
    if not t or len(t) < 6 or not re.search(r"[A-Za-z]{3}", t): return ""
    s = re.split(r"(?<=[.!?])\s+(?=[A-Z])", t)
    out = s[0]
    if len(out) < 60 and len(s) > 1: out += " " + s[1]
    return out[:260].rstrip() + ("" if out.endswith(".") else ".")

# ── Wiktionary ──
def load(path):
    return json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}

def wiktionary():
    # English Wiktionary: a section per language, given-name categories carry the sex
    EN = [("Spanish", "Spanish", f"{RAW}/wikt-en-Spanish.json"), ("Old Spanish", "Spanish", f"{RAW}/wikt-en-Old_Spanish.json"),
          ("Asturian", "Asturian", f"{RAW}/wikt-en-Asturian.json"), ("Leonese", "Asturian", f"{RAW}/wikt-en-Leonese.json"),
          ("Aragonese", "Aragonese", f"{RAW}/wikt-en-Aragonese.json"), ("Ladino", "Ladino", f"{RAW}/wikt-en-Ladino.json"),
          ("Catalan", "Catalan", f"{WIKT}/Catalan.json"), ("Galician", "Galician", f"{WIKT}/Galician.json"), ("Basque", "Basque", f"{WIKT}/Basque.json"),
          ("Quechua", "Quechua", f"{WIKT}/Quechua.json"), ("Nahuatl", "Nahua", f"{WIKT}/Nahuatl.json"), ("Classical Nahuatl", "Nahua", f"{RAW}/wikt-en-Classical_Nahuatl.json"),
          ("Guarani", "Guarani", f"{WIKT}/Guarani.json"), ("Aymara", "Aymara", f"{WIKT}/Aymara.json")]
    seen = set()
    for lang, cult, path in EN:
        for title, v in load(path).items():
            sec = section(v["text"], lang)
            if not sec or (title, cult) in seen and lang == "Classical Nahuatl": continue
            # Ladino entries are written in Latin script; a Hebrew-script form is kept only when the entry gives one
            if not ok(title) and not (cult == "Ladino" and re.search(r"[֐-׿]", title)): continue
            seen.add((title, cult))
            # a Quechua or Nahuatl form of a Spanish name (Juan, Guadalupe) isn't an indigenous name
            if CULT[cult][1] == IA and re.search(r"\{\{(?:bor|bor\+|der|lbor)\|[a-z-]+\|(?:es|osp|la|grc|he)\|", sec): continue
            e = entry(cult, title); e["src"].add("wikt-en"); sex(e, "wikt-en", v["g"])
            d = details(sec)
            if d.get("meaning") and not e["meaning"]:
                e["meaning"] = " + ".join(dict.fromkeys(x.strip() for x in d["meaning"].split("+")))[:80]
            if not e["ety"]:
                e["ety"] = ety(sec)
            if lang in ("Old Spanish", "Leonese"): e["notes"].append(f"Listed by Wiktionary as an {lang} name.")
            heb = re.search(r"\{\{(?:lad-proper noun|head\|lad\|proper noun)[^}]*\|(?:head2?|tr|alt|sc=Hebr)[^}]*?([֐-׿][֐-׿֑-ׇ ]*)", sec)
            if cult == "Ladino" and heb: e["notes"].append(f"Written {heb.group(1).strip()}.")
    # other editions: category membership (and, for Galician and Asturian, a given-name definition) is the evidence
    OTHER = [("wikt-es", "es", "Spanish"), ("wikt-ca-ca", "ca", "Catalan"), ("wikt-ca-es", "ca", "Spanish"), ("wikt-ca-gl", "ca", "Galician"),
             ("wikt-ca-eu", "ca", "Basque"), ("wikt-ca-an", "ca", "Aragonese"), ("wikt-gl-gl", "gl", "Galician"), ("wikt-gl-es", "gl", "Spanish"),
             ("wikt-gl-eu", "gl", "Basque"), ("wikt-gl-ca", "gl", "Catalan"), ("wikt-gl-ast", "gl", "Asturian"), ("wikt-gl-an", "gl", "Aragonese"),
             ("wikt-eu-eu", "eu", "Basque"), ("wikt-eu-es", "eu", "Spanish"), ("wikt-eu-ca", "eu", "Catalan"), ("wikt-eu-gl", "eu", "Galician"),
             ("wikt-ast-ast", "ast", "Asturian"), ("wikt-ast-an", "ast", "Aragonese"), ("wikt-ast-es", "ast", "Spanish"), ("wikt-ast-gl", "ast", "Galician"),
             ("wikt-ast-ca", "ast", "Catalan")]
    for fn, wiki, cult in OTHER:
        for title, v in load(f"{RAW}/{fn}.json").items():
            if not ok(title): continue
            t, g = v["text"], v["g"]
            if wiki == "gl":
                # "Nomes propios" are proper nouns of every kind; a given name is defined as "nome propio masculino/feminino"
                gs = set(re.findall(r"nome propio\W*(?:\}\}\s*\{\{gl\|)?\s*(masculino|feminino)", t))
                if not gs: continue
                g = "e" if len(gs) > 1 else ("b" if "masculino" in gs else "g")
            if wiki == "ast":
                # likewise: a given name is defined as "Nome de pila masculín/femenín"
                m = re.search(r"(?i)nome de pila\]*\s*(masculín|femenín)?", t)
                if not m: continue
                g = {"masculín": "b", "femenín": "g"}.get((m.group(1) or "").lower(), g)
            if wiki == "ca" and not re.search(r"\{\{prenom\|", t): continue
            e = entry(cult, title); e["src"].add(f"wikt-{wiki}"); sex(e, "wikt", g)

# ── Wikidata given-name items ──
WD_LANG = {"Q1321": ("Spanish", "es"), "Q7026": ("Catalan", "ca"), "Q9307": ("Galician", "gl"), "Q8752": ("Basque", "eu"), "Q29507": ("Asturian", "ast"),
           "Q8765": ("Aragonese", "an"), "Q36196": ("Ladino", "lad"), "Q5218": ("Quechua", "qu"), "Q13300": ("Nahua", "nah"), "Q35876": ("Guarani", "gn"),
           "Q33730": ("Mapuche", "arn"), "Q4627": ("Aymara", "ay")}
WD_SEX = {"Q12308941": "b", "Q11879590": "g", "Q3409032": "e"}
def wikidata():
    items = collections.defaultdict(lambda: {"labels": {}, "native": set(), "types": set()})
    for r in load(f"{RAW}/wd-given-names.json"):
        it = items[(r["n"], r["lang"])]
        it["labels"][r.get("label_lang", "")] = r["label"]; it["types"].add(r["type"])
        if r.get("native"): it["native"].add((r["native"], r.get("nl", "")))
    for (q, lang), it in items.items():
        cult, code = WD_LANG[lang]
        # the name as written in that language: its native-language name (P1705) in that language, else its label there
        names = [n for n, nl in it["native"] if ok(n) and nl == code] or [it["labels"][c] for c in (code,) if ok(it["labels"].get(c, ""))]
        if not names: continue
        gs = {WD_SEX[t] for t in it["types"] if t in WD_SEX}
        for n in names[:1]:
            e = entry(cult, n); e["src"].add("wikidata"); e.setdefault("qids", []).append(q)
            sex(e, "wikidata", "e" if len(gs) > 1 else next(iter(gs)) if gs else "")

# ── official lists (fetch_spanish_regional.py) ──
PREFIX = {"eu": "Basque", "gl": "Galician", "ca": "Catalan", "ast": "Asturian", "an": "Aragonese"}
def official():
    lists = []
    for path in sorted(glob.glob(f"{RAW}/*-*.tsv")):
        base = os.path.basename(path); pre = base.split("-")[0]
        if pre not in PREFIX: continue
        lines = open(path, encoding="utf-8").read().split("\n")
        head = " ".join(l[2:] for l in lines if l.startswith("# "))
        rows = list(csv.DictReader([l for l in lines if l and not l.startswith("#")], delimiter="\t", quoting=csv.QUOTE_NONE))
        if not rows or "name" not in rows[0]: continue
        # a list of names with counts only is a usage table (who is called what), not a list of the language's names
        normative = any((r.get("meaning") or "").strip() or (r.get("sex") or "").strip() for r in rows) and not all((r.get("count") or "").strip() for r in rows)
        lists.append((base, PREFIX[pre], head, rows, normative))
    return lists

# ── INE ──
def ine():
    out = {"b": {}, "g": {}}
    p = f"{RAW}/ine-nombres_por_edad_media.xlsx"
    if not os.path.exists(p): return out, {}
    for sheet, g in (("Hombres", "b"), ("Mujeres", "g")):
        for r in xlsx.rows(p, sheet):
            if len(r) >= 4 and r[0] and r[0].isdigit() and r[1]: out[g][fold(r[1].strip())] = (int(r[2]), float(r[3]))
    prov = collections.defaultdict(list)          # fold → [(sex, province, rank)]
    p = f"{RAW}/ine-nombres_mas_frecuentes.xlsx"
    for sheet, g in (("Hombres_PROVINCIAdeRESIDENCIA", "b"), ("Mujeres_PROVINCIAdeRESIDENCIA", "g")):
        rs = list(xlsx.rows(p, sheet)); heads = rs[2]
        for r in rs[4:]:
            if not r or not (r[0] or "").isdigit(): continue
            for k in range(1, len(r), 3):
                h = heads[k] if k < len(heads) else None
                if h and r[k]: prov[fold(r[k])].append((g, re.sub(r"^\d+ - ", "", h).split("/")[0].title(), int(r[0])))
    return out, prov

# ── literature ──
def literature():
    p = f"{RAW}/lit-attestations.tsv"
    if not os.path.exists(p): return
    for r in csv.DictReader(open(p, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
        n = (r.get("name") or "").strip()
        cult = {"Spanish": "Spanish", "Catalan": "Catalan", "Galician": "Galician"}.get((r.get("language") or "").strip())
        if not cult or not ok(n): continue
        e = entry(cult, n); e["src"].add("lit"); sex(e, "lit", (r.get("sex") or "").strip())
        e["lit"].append(r)

# ── history ──
STOP = {"san", "santa", "santo", "beato", "beata", "don", "doña", "fray", "sor", "infante", "infanta", "rey", "reina", "conde", "condesa", "el", "la", "los",
        "las", "de", "del", "sant", "beat", "en", "na", "o", "a", "papa", "abad", "abadesa", "obispo", "maestre", "sancta", "sir", "lord"}
CASTILIAN = {"Q217196", "Q179293", "Q175276", "Q200262", "Q3446210", "Q199442", "Q231392", "Q303421"}
CATALAN = {"Q1233672", "Q204920", "Q836676", "Q142417"}
def year(v):
    m = re.match(r"^(-?)0*(\d{1,4})-", v or "")
    return int(m.group(2)) * (-1 if m.group(1) else 1) if m else None
def royals(spanish_known, foreign):
    people = {}
    for r in load(f"{RAW}/wd-iberian-royals.json"):
        p = people.setdefault(r["p"], {**r, "cs": set()}); p["cs"].add(r["c"])
    for q, p in people.items():
        b, d = year(p.get("born")), year(p.get("died"))
        if (b or d or 9999) >= 1600: continue
        g = {"Q6581097": "b", "Q6581072": "g"}.get(p.get("sex", ""), "")
        when = f"{b}–{d}" if b and d and b != d else f"{b}" if b and d else f"born {b}" if b else f"died {d}" if d else ""
        for cult, label, area in (("Spanish", p.get("esl", ""), CASTILIAN), ("Catalan", p.get("cal", ""), CATALAN)):
            if not label or not p["cs"] & area: continue
            tok = label.split()[0].strip(",")
            if tok.lower() in STOP or not ok(tok) or re.search(r"\d", tok): continue
            known = fold(tok) in spanish_known[cult]
            # a name no Spanish (or Catalan) source lists is kept only for the early kingdoms, and only if it isn't a name of
            # another European language (a French count with a Castilian title keeps his French name)
            if not known and (cult == "Catalan" or (b or d or 9999) >= 1350 or fold(tok) in foreign): continue
            e = entry(cult, tok); e["src"].add("royal"); sex(e, "royal", g)
            e["hist"].append((label, when, (p.get("desc") or "").strip(), q, b or d or 9999))

def main():
    wiktionary(); wikidata()
    lists = official()
    for base, cult, head, rows, normative in lists:
        if not normative: continue
        for r in rows:
            n = r["name"].strip()
            if not ok(n): continue
            e = entry(cult, n); e["src"].add("official"); sex(e, "official", (r.get("sex") or "").strip())
            e["official"].append((base, head, r))
    literature()
    # names a Spanish/Catalan source already lists (for the history filter), and names of other European languages
    spanish_known = collections.defaultdict(set)
    for (c, k), e in E.items(): spanish_known[c].add(k)
    usage, prov = ine()
    spanish_known["Spanish"] |= set(usage["b"]) | set(usage["g"])
    foreign = set()
    for r in json.load(open(os.path.join(ROOT, "data", "culture-names.json"), encoding="utf-8")):
        if r[2] in ("French", "English", "German", "Dutch", "Italian", "Portuguese", "Polish", "Hungarian", "Czech"): foreign.add(fold(r[0]))
    for f in ("medieval-names.json",):
        for r in json.load(open(os.path.join(ROOT, "data", f), encoding="utf-8")): foreign.add(fold(r[0]))
    royals(spanish_known, foreign)
    # regional usage tables (counts) for the story
    counts = collections.defaultdict(list)
    for base, cult, head, rows, normative in lists:
        if normative: continue
        for r in rows:
            if (r.get("count") or "").strip(): counts[(cult, fold(r["name"]))].append((base, head, r))

    rows = []
    for (cult, k), e in sorted(E.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        # the spelling most sources print, preferring accented over plain (Núria over Nuria) when tied
        name = sorted(e["forms"].items(), key=lambda kv: (-kv[1], kv[0] == fold(kv[0])))[0][0]
        # sex from the most reliable source that gives one
        g = ""
        for src in sorted(e["sex"], key=lambda s: PRI[s]):
            gs = e["sex"][src]
            g = "e" if len(gs) > 1 or "e" in gs else next(iter(gs)); break
        u = (usage["b"].get(k), usage["g"].get(k)) if cult == "Spanish" or True else (None, None)
        if not g and (u[0] or u[1]):
            nb, ng = (u[0] or (0,))[0], (u[1] or (0,))[0]
            g = "b" if nb >= 9 * ng else "g" if ng >= 9 * nb else "e"
            e["sex"]["ine"] = {g}
        if not g:
            # a name with no stated sex in any source is left out rather than guessed
            continue
        # Wikidata's language tags (P407) are loose (Montserrat is tagged Aragonese, Mark Spanish): a name only Wikidata gives is
        # kept when people in Spain bear it (INE) and it isn't a name of another European language
        if e["src"] == {"wikidata"} and (not (usage["b"].get(k) or usage["g"].get(k)) or k in foreign): continue
        lang, also_b = CULT[cult]
        story = [f"{'An' if cult[0] in 'AEIOU' else 'A'} {cult} name."]
        if e["ety"]: story.append("Etymology (Wiktionary): " + e["ety"])
        story += list(dict.fromkeys(e["notes"]))
        for base, head, r in e["official"][:2]:
            pub = "Euskaltzaindia" if base.startswith("eu-") and "uskaltzaindia" in head else "Real Academia Galega" if base.startswith("gl-rag") else \
                  re.search(r"(?:Source|Publisher|source|publisher)[:=]\s*([^;,.]+)", head).group(1).strip() if re.search(r"(?:Source|Publisher|source|publisher)[:=]\s*([^;,.]+)", head) else base
            s = f"On the official list of {cult} names ({pub})."
            m = (r.get("meaning") or "").strip()
            if m: s += f" Its explanation, in {cult if base[:2] != 'es' else 'Spanish'}: “{m[:220]}{'…' if len(m) > 220 else ''}”"
            eq = (r.get("equivalents") or "").strip()
            if eq: s += f" Equivalents given: {eq}."
            story.append(s)
        texts = []
        lit = sorted(e["lit"], key=lambda r: (r.get("year") or "9999")[:4].strip("c. ") or "9999")
        works_seen = set()
        for r in lit:
            w = r["work"].strip()
            if w in works_seen: continue
            works_seen.add(w); texts.append(w)
        for r in lit[:3]:
            yr = (r.get("year") or "").strip(); ps = (r.get("passage") or "").strip()
            pr = r["name"].strip()
            story.append(f"Named in {r['work'].strip()}" + (f" ({yr})" if yr else "") + (f", {ps}" if ps else "") + (f", as {pr}" if fold(pr) == k and pr != name else "") + ".")
        if len(works_seen) > 3: story.append(f"Also named in {len(works_seen) - 3} more works.")
        hist = sorted(e["hist"], key=lambda h: h[4])
        if hist:
            label, when, desc, q, _ = hist[0]
            story.append(f"Borne by {label}" + (f" ({when})" if when else "") + (f", {desc}" if desc and len(desc) < 90 else "") + "." + (f" {len(hist) - 1} more bearer{'s' if len(hist) > 2 else ''} in the medieval kingdoms." if len(hist) > 1 else ""))
        if cult == "Spanish" or True:
            parts = []
            for gg, word in (("b", "men"), ("g", "women")):
                if usage[gg].get(k): parts.append(f"{usage[gg][k][0]:,} {word} (average age {usage[gg][k][1]:.0f})")
            if parts: story.append(f"INE, 1 January 2025: {' and '.join(parts)} living in Spain have {name} as their full first name.")
            tops = sorted((r for r in prov.get(k, [])), key=lambda x: x[2])
            if tops and cult != "Spanish":
                story.append("Among the 50 most frequent names in " + ", ".join(dict.fromkeys(p for _, p, _ in tops[:4])) + " (INE).")
        for base, head, r in counts.get((cult, k), [])[:1]:
            story.append(f"{int(float(r['count'])):,} people ({base.split('.')[0].split('-', 1)[1]})." if False else "")
        story = [s for s in story if s]
        others = sorted({c for (c, kk) in E if kk == k and c != cult})
        rows.append([name, g, cult, lang, "", e["meaning"], " ".join(story), ",".join(texts), "real", others + also_b])
    rows.sort(key=lambda r: (fold(r[0]), r[2]))
    json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    per = collections.Counter(r[2] for r in rows)
    print(f"{len(rows):,} rows → {OUT} ({os.path.getsize(OUT) // 1024} KB); {sum(1 for r in rows if r[5]):,} with meanings, {sum(1 for r in rows if r[7]):,} in literature")
    print(per.most_common())

if __name__ == "__main__":
    main()
