# Ancient Roman names → data/roman-names.json, in the row format of data/culture-names.json:
#   [name, g ('g'|'b'|'e'), culture, language, religions, meaning, story, texts, kind, also]
#
# 1. data/roman-names.tsv, hand-curated. Every row is a person who bore the name in antiquity:
#   INSCRIPTION      an epitaph or dedication in the Epigraphic Database Heidelberg (EDH, CC BY-SA 4.0,
#                    https://edh.ub.uni-heidelberg.de/data/download, edh_data_pers.csv + edh_data_text.csv);
#                    attest_count = people of that sex in EDH bearing the name as praenomen (abbreviations
#                    counted: L. = Lucius), nomen or cognomen, leaving out emperors and their family (EDH status 0)
#   TABLET           Vindolanda tablets (Roman Inscriptions of Britain / Vindolanda Tablets Online)
#   LITERARY-PERSON  a real person in an ancient author (Perseus, CC BY-SA; LacusCurtius)
#   Sex is the sex EDH (or the text) gives the bearer. ease: 1 usable as written, 2 usable through a real descendant
#   (Aemilia → Emilia), 3 hard. Only ease 1–2 and confidence high/medium go to the site.
# 2. Every other praenomen, nomen and cognomen that 5+ people of one sex bear on inscriptions in EDH (raw/roman/, same
#   files; counted as in build_latin_names.py), with one of those people as the example: the earliest dated inscription
#   with a findspot.
#   Names the Romans took from Greek are left out (they are in data/greek-names.json), as are uncertain readings
#   (EDH's + and [ ]). The meaning is the one data/latin-names.json gives the same Latin name (Wiktionary, Lewis & Short),
#   else none. The name shows in its modern form when birth registries use it (Iulia → Julia), else as written in Latin.
#
#   python3 scripts/build_roman_names.py
import csv, json, os, re, unicodedata, collections
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "roman-names.tsv"); OUT = os.path.join(ROOT, "data", "roman-names.json")
EDH_DIR = os.path.join(ROOT, "raw", "roman")
csv.field_size_limit(10 ** 9)

def short(source):  # "CIL VI 31846 (EDH HD000144) https://…" → "CIL VI 31846"
    return re.split(r" \(EDH| https?://|;", source)[0].strip()
def plain(s): return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c))
def fold(s): return re.sub(r"[\s'-]", "", plain(s).lower())
def lfold(s): return fold(s).replace("j", "i").replace("v", "u")

rows, done = [], set()
for r in csv.DictReader(open(SRC, encoding="utf-8"), delimiter="\t"):
    done.add(lfold(r["latin"]))
    if r["ease"] not in ("1", "2") or r["confidence"] not in ("high", "medium"): continue
    who, ref = r["who"], short(r["source"])
    if r["ease"] == "2":
        story = f"The modern form of the ancient Roman {r['latin']}: {who}. ({ref})"
    elif r["latin"] != r["name"]:
        story = f"An ancient Roman name, written {r['latin']} in Latin: {who}. ({ref})"
    else:
        story = f"An ancient Roman name: {who}. ({ref})"
    # the meanings in the TSV are Lewis & Short glosses written from memory, not looked up one by one, so they stay off the site until checked
    rows.append([r["name"], r["sex"], "Ancient Roman", "Latin", "", "", story, "", "real", []])
hand = len(rows)

# ── 2. the inscriptions ──
PRAE = {"a": "Aulus", "ap": "Appius", "c": "Gaius", "cn": "Gnaeus", "d": "Decimus", "l": "Lucius", "m": "Marcus", "m'": "Manius", "mam": "Mamercus",
        "n": "Numerius", "p": "Publius", "q": "Quintus", "ser": "Servius", "sex": "Sextus", "s": "Spurius", "sp": "Spurius", "t": "Titus", "ti": "Tiberius", "v": "Vibius"}
ROLE = {"praenomen": "first name (praenomen)", "nomen": "family name (nomen)", "cognomen": "personal name (cognomen)"}
def where(p):   # "Samothracia, insula" → Samothracia, "Colonia Iulia Augusta Philippensium (= Philippi)" → Philippi
    p = p.strip(); m = re.search(r"\(=\s*([^)]+)\)", p)
    if m: p = m.group(1)
    p = re.sub(r",?\s*\b(bei|insula|Insel|Umgebung|nahe|sive .*|vel .*)\b.*$", "", p).strip(" ,")
    return "" if re.search(r"[?\[]|unbekannt|incertus", p) else p
texts = {}
for t in csv.DictReader(open(os.path.join(EDH_DIR, "edh_data_text.csv"), encoding="utf-8")):
    texts[t["hd_nr"]] = (where(t["fo_antik"]), where(t["fo_modern"]), t["dat_jahr_a"].strip(), t["dat_jahr_e"].strip())
count, roles, example = collections.Counter(), collections.defaultdict(collections.Counter), {}
EDH = collections.Counter()   # (lfold name, sex) → people, counted exactly as build_latin_names.py does, so both cards agree
for r in csv.DictReader(open(os.path.join(EDH_DIR, "edh_data_pers.csv"), encoding="utf-8")):
    if r["status"].startswith("0"): continue                 # emperors and their family
    sx = r["geschlecht"][:1]
    if sx not in ("M", "W"): continue
    every = set()
    for f in ("nomen", "cognomen", "supernomen"):
        for w in re.sub(r"\(.*?\)", " ", r[f]).split():
            w = re.sub(r"[^A-Za-z]", "", w)
            if len(w) > 1: every.add(lfold(w))
    found = []
    pr = re.sub(r"[+*?\s]", "", r["praenomen"]).rstrip(".").lower()
    if pr in PRAE: every.add(lfold(PRAE[pr]))
    for w in every: EDH[(w, sx)] += 1
    if pr in PRAE: found.append((PRAE[pr], "praenomen"))
    for f in ("nomen", "cognomen"):
        for w in r[f].split():
            if "+" in w or re.search(r"[^A-Za-z]", w) or len(w) < 3 or not w[0].isupper() or w[1:] != w[1:].lower(): continue
            found.append((w, f))
    # the person as the database files them, in the nominative (the stone itself often has them as "to Ulpius Zosimus")
    whole = re.sub(r"[*!]", "", " ".join(x for x in (r["praenomen"], r["nomen"], r["cognomen"]) if x and x != "00"))
    place, mp, a, e = texts.get(r["hd_nr"], ("", "", "", ""))
    ok = place and re.fullmatch(r"-?\d+", a) and (not e or re.fullmatch(r"-?\d+", e)) and not re.search(r"[\[\]()/!?<>{}]", whole)
    for w, f in found:
        k = (w, sx); count[k] += 1; roles[k][f] += 1
        if ok:
            cand = (int(a), r["hd_nr"], whole, place, mp, a, e)
            if k not in example or cand < example[k]: example[k] = cand

greek = {fold(r[0]) for r in json.load(open(os.path.join(ROOT, "data", "greek-names.json"), encoding="utf-8"))}
GREEKISH = re.compile(r"(y|ph|th|ch|rh|kh|(?<!a)e$|os$|on$|es$|eus$)")
latin_m = {}                                                   # the meaning data/latin-names.json gives a Latin name
for r in json.load(open(os.path.join(ROOT, "data", "latin-names.json"), encoding="utf-8")):
    if not r[5]: continue
    latin_m.setdefault(lfold(r[0]), r[5])
    m = re.search(r"from Latin ([^\s,;(“]+)", r[6])
    if m: latin_m.setdefault(lfold(m.group(1)), r[5])
DB = {}
for line in open(os.path.join(ROOT, "data", "names-db.tsv"), encoding="utf-8"):
    n, g, cc, c = line.rstrip("\n").split("\t"); DB.setdefault(fold(n), int(c))
def modern(latin):    # Iulia → Julia, Cassianus → Cassian, when birth registries use that form
    j = re.sub(r"^I(?=[aeiou])", "J", latin)
    cands = [latin, j] + [x[:-2] for x in (latin, j) if re.search(r"anus$", x) and len(x) > 6]   # Cassianus → Cassian (not Victorinus → Victorin)
    best = max(cands, key=lambda c: (DB.get(fold(c), 0), c == latin))
    return best if DB.get(fold(best), 0) >= 50 else latin
def era(a, e):
    a, e = int(a), int(e or a)
    f = lambda y: f"{-y} BCE" if y < 0 else f"{y} CE"
    if a == e: return f(a)
    return f"{-a}–{-e} BCE" if e < 0 else f"{f(a)}–{f(e)}" if a < 0 else f"{a}–{e} CE"

names = {}
for (w, sx), c in count.items():
    if c < 5 or lfold(w) in done or fold(w) in greek or GREEKISH.search(w.lower()): continue
    names.setdefault(w, {})[sx] = c
for w, by in sorted(names.items(), key=lambda kv: -sum(kv[1].values())):
    by = {s: EDH[(lfold(w), s)] for s in by}
    sx = max(by, key=by.get); other = "M" if sx == "W" else "W"
    g = "e" if len(by) == 2 and by[other] >= .25 * by[sx] else "g" if sx == "W" else "b"
    role = ROLE[roles[(w, sx)].most_common(1)[0][0]]
    who = lambda s: "women" if s == "W" else "men"
    people = f"{by[sx]:,} {who(sx)}" + (f" and {by[other]:,} {who(other)}" if other in by else "")
    n = modern(w)
    story = f"An ancient Roman {role}" + (f", written {w} in Latin" if n != w else "") + f": borne by {people} on Roman inscriptions"
    ex = example.get((w, sx))
    if ex:
        _, hd, whole, place, mp, a, e = ex
        story += f", among them {whole} ({place}{f', today {mp}' if mp and mp != place else ''}, {era(a, e)}; EDH {hd})"
    rows.append([n, g, "Ancient Roman", "Latin", "", latin_m.get(lfold(w), ""), story + ". (Epigraphic Database Heidelberg)", "", "real", []])
# one row per modern name and sex: the hand-curated row first, else the form with the most bearers
seen, out = set(), []
for r in rows:
    k = (fold(r[0]), r[1])
    if k in seen: continue
    seen.add(k); out.append(r)
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"{len(out)} names → {os.path.relpath(OUT, ROOT)} ({hand} hand-curated, {len(out) - hand} from inscriptions; {sum(1 for r in out if r[5])} with a meaning)")
