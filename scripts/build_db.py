# Builds Lullabyte's canonical database, data/lullabyte.sqlite (schema: scripts/schema.sql), from every source the
# site uses, then checks the rules the schema promises. The site still loads its compact JSON files; this database
# is where the layers live together, so questions like "every pronunciation of Maya" or "how many babies were named
# Isla in Scotland, by year" are one query.
#
#   python3 scripts/build_db.py                 # ~1–2 minutes; the database is rebuilt from scratch
#
# Layers and where they come from:
#   names, associations, meanings, name_forms   names.js (hand-written), data/*-names.json, data/names-db.tsv
#   name_references                              data/scripture-names.json (sacred texts)
#   relationships                                spelling families (generator.js), data/relations.json (Wiktionary)
#   pronunciations, syllables, lullabytes        data/pron.json, run through phonetics.js + musicbox.js in Node
#   popularity_observations, sources            build_years.py's official sources (full counts, every year)
import csv, json, os, re, sqlite3, subprocess, sys, unicodedata, importlib.util, collections

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA, DB = os.path.join(HERE, "data"), os.path.join(HERE, "data", "lullabyte.sqlite")

def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower().replace(" ", "").replace("-", "")

if os.path.exists(DB): os.remove(DB)
db = sqlite3.connect(DB)
db.executescript(open(os.path.join(HERE, "scripts/schema.sql")).read())

# ── sources ──
SRC = [
    ("hand", "Lullabyte", "Hand-written names with meanings (names.js)", None, None, "curated", None, None, "full", None, None, None, None, "this project"),
    ("wiktionary", "Wiktionary", "Given-name categories and entries", "https://en.wiktionary.org", None, "open data", None, None, None, None, None, None, None, "CC BY-SA 4.0"),
    ("wikidata", "Wikidata", "Given-name items", "https://www.wikidata.org", None, "open data", None, None, None, None, None, None, None, "CC0"),
    ("stepbible", "Tyndale House", "STEPBible TIPNR", "https://github.com/STEPBible/STEPBible-Data", None, "scholarly", None, None, None, None, None, None, None, "CC BY 4.0"),
    ("jmnedict", "EDRDG", "JMnedict / KANJIDIC2", "https://www.edrdg.org", None, "dictionary", None, None, None, None, None, None, None, "CC BY-SA 4.0"),
    ("registries", "Government registries in 18+ countries", "data/names-db.tsv (see docs/name-sources.md)", None, None, "government", None, None, "full", 5, None, None, None, "various open licences"),
    ("cmudict", "Carnegie Mellon University", "CMU Pronouncing Dictionary", "https://github.com/cmusphinx/cmudict", None, "dictionary", None, None, None, None, None, None, None, "BSD-2-Clause"),
    ("hand-checked", "Lullabyte", "Hand-checked pronunciations (scripts/build_pron.py)", None, None, "curated", None, None, None, None, None, None, None, "this project"),
    ("rules", "Lullabyte", "Per-language sound rules (phonetics.js)", None, None, "derived", None, None, None, None, None, None, None, "this project"),
]
db.executemany("INSERT INTO sources VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL)", SRC)

# ── names: the identity layer ──
ids, rows_by = {}, {}
def name_id(display, **kw):
    if display in ids:
        return ids[display]
    cur = db.execute("INSERT INTO names (display_name, normalized_name, traditional_gender, primary_origin, origin_language, kind) VALUES (?,?,?,?,?,?)",
                     (display, norm(display), kw.get("g"), kw.get("o") or None, kw.get("l") or None, kw.get("kind")))
    ids[display] = cur.lastrowid
    return cur.lastrowid

G = {"g": "girl", "b": "boy", "e": "either", "f": "girl", "m": "boy", "u": "either"}
def add_row(n, g, o, l, r, m, src, texts, kind, also, source):
    nid = name_id(n, g=G.get(g), o=o, l=l, kind=kind)
    for c in [o, *(also or [])]:
        if c: db.execute("INSERT INTO associations VALUES (?,?,?,?)", (nid, "culture", c, source))
    for rel in (r.split(",") if isinstance(r, str) and r else r or []):
        db.execute("INSERT INTO associations VALUES (?,?,?,?)", (nid, "religion", rel, source))
    if l: db.execute("INSERT INTO associations VALUES (?,?,?,?)", (nid, "language", l, source))
    if m: db.execute("INSERT INTO meanings (name_id, meaning, etymology, source_id) VALUES (?,?,?,?)", (nid, m, src or None, source))
    for t in (texts.split(",") if texts else []):
        db.execute("INSERT INTO name_references VALUES (?,?,?,?,?,?)", (nid, "religious text", t, None, "named in the text", source))

# hand-written names (names.js REAL_RAW: Name|g/b/e|Culture|Language|Religions|meaning|story)
raw = open(os.path.join(HERE, "names.js"), encoding="utf-8").read()
block = raw[raw.index("REAL_RAW = `") + 12: raw.index("`", raw.index("REAL_RAW = `") + 12)]
for line in block.strip().split("\n"):
    p = line.split("|")
    if len(p) >= 6: add_row(p[0], p[1], p[2], p[3], p[4], p[5], p[6] if len(p) > 6 else "", "", "real", [], "hand")

for f, source in [("scripture-names.json", "stepbible"), ("culture-names.json", "wiktionary"), ("also-cultures.json", "wiktionary"),
                  ("hebrew-names.json", "wikidata"), ("medieval-names.json", "wiktionary"), ("bible-extra.json", "wiktionary")]:
    path = os.path.join(DATA, f)
    if not os.path.exists(path): continue
    for row in json.load(open(path, encoding="utf-8")):
        if isinstance(row, list) and len(row) >= 9:
            add_row(*row[:9], row[9] if len(row) > 9 else [], source)

# East Asian names: their native script is a name form, not a separate name
ea = json.load(open(os.path.join(DATA, "east-asian-names.json"), encoding="utf-8"))
for n, g, kanji, kana, ways, m in ea.get("ja", []):
    nid = name_id(n, g=G.get(g), o="Japanese", l="Japanese", kind="real")
    db.execute("INSERT INTO associations VALUES (?,?,?,?)", (nid, "culture", "Japanese", "jmnedict"))
    if m: db.execute("INSERT INTO meanings (name_id, meaning, source_id) VALUES (?,?,?)", (nid, m, "jmnedict"))
    if kanji: db.execute("INSERT INTO name_forms VALUES (?,?,?,?,?,?)", (nid, "Kanji", kanji, None, 1, "jmnedict"))
    db.execute("INSERT INTO name_forms VALUES (?,?,?,?,?,?)", (nid, "Kana", kana, None, 0, "jmnedict"))
    db.execute("INSERT INTO name_forms VALUES (?,?,?,?,?,?)", (nid, "Latin", n, "Hepburn", 0, "jmnedict"))
for lang, script, system, rows in (("Korean", "Hangul", "Revised Romanization", ea.get("ko", [])), ("Chinese", "Hanzi", "pinyin", ea.get("zh", []))):
    for n, g, native, other, m, real in rows:
        nid = name_id(n, g=G.get(g), o=lang, l=lang, kind="real" if real else "root")
        db.execute("INSERT INTO associations VALUES (?,?,?,?)", (nid, "culture", lang, "jmnedict"))
        if m: db.execute("INSERT INTO meanings (name_id, meaning, source_id) VALUES (?,?,?)", (nid, m, "jmnedict"))
        db.execute("INSERT INTO name_forms VALUES (?,?,?,?,?,?)", (nid, script, native, None, 1, "jmnedict"))
        db.execute("INSERT INTO name_forms VALUES (?,?,?,?,?,?)", (nid, "Latin", n, system, 0, "jmnedict"))

# every registered name, with what registries hold (an aggregate across countries, kept as an association)
for line in open(os.path.join(DATA, "names-db.tsv"), encoding="utf-8"):
    n, g, cc, cnt = line.rstrip("\n").split("\t")
    nid = name_id(n, g=G.get(g), kind="attested")
    for c in cc.split(","):
        db.execute("INSERT INTO associations VALUES (?,?,?,?)", (nid, "registered in", c, "registries"))

# meanings from Wiktionary, if fetched (scripts/fetch_meanings.py)
mp = os.path.join(DATA, "meanings.json")
if os.path.exists(mp):
    by_norm = collections.defaultdict(list)
    for d, i in ids.items(): by_norm[norm(d)].append(i)
    for k, v in json.load(open(mp, encoding="utf-8")).items():
        for nid in by_norm.get(norm(k), []):
            if v.get("m") or v.get("ety"):
                db.execute("INSERT INTO meanings VALUES (?,?,?,?,?,?)", (nid, v.get("m") or "", v.get("ety"), v.get("root"), "wiktionary", None))

# ── relationships ──
by_norm = collections.defaultdict(list)
for d, i in ids.items(): by_norm[norm(d)].append(i)
first = lambda n: (by_norm.get(norm(n)) or [None])[0]
gen = open(os.path.join(HERE, "generator.js"), encoding="utf-8").read()
fam = gen[gen.index("SPELLING_FAMILIES = `") + 21: gen.index("`", gen.index("SPELLING_FAMILIES = `") + 21)]
for line in fam.strip().split("\n"):
    parts = re.findall(r"Abdul \w+|\w+", line) if "Abdul" in line else line.split()
    for a in parts:
        for b in parts:
            if a < b and first(a) and first(b):
                db.execute("INSERT INTO relationships VALUES (?,?,?,?,?)", (first(a), first(b), "spelling_variant", None, "hand"))
rp = os.path.join(DATA, "relations.json")
if os.path.exists(rp):
    for a, rel, b, lang in json.load(open(rp, encoding="utf-8")):
        if first(a) and first(b):
            db.execute("INSERT INTO relationships VALUES (?,?,?,?,?)", (first(a), first(b), rel, lang, "wiktionary"))

# ── pronunciations, syllables and lullabytes: the same code the site runs, in Node ──
NODE = r"""
globalThis.localStorage = { getItem() { return null }, setItem() {} };
globalThis.dispatchEvent = () => {}; globalThis.Event = class {}; globalThis.CustomEvent = class {};
const fs = require("fs"), vm = require("vm");
const src = ["names.js", "generator.js", "phonetics.js", "musicbox.js"].map(f => fs.readFileSync(f, "utf8")).join("\n;\n") + "\n;globalThis.PH = PH; globalThis.MB = MB;";
vm.runInThisContext(src);
PH.load(JSON.parse(fs.readFileSync("data/pron.json", "utf8")));
const names = JSON.parse(fs.readFileSync(0, "utf8")), out = [];
for (const n of names) {
  const opts = PH.options(n);
  opts.forEach((o, k) => {
    const m = MB.melody(n), main = m.ev.filter(e => e.kind === "main");
    out.push({ n, k, say: o.say, source: o.source, syl: o.syl, shape: PH.shape(o.syl),
      notes: k === 0 ? main.map(e => MB.NOTE_NAMES[e.i]).join(" ") : null, vel: k === 0 ? main.map(e => +e.v.toFixed(2)).join(" ") : null,
      art: k === 0 ? main.map(e => e.art).join(" ") : null, steps: k === 0 ? main.map((e, i) => +((main[i + 1] ? main[i + 1].t : m.steps - 3) - e.t).toFixed(2)).join(" ") : null });
  });
}
process.stdout.write(JSON.stringify({ algorithm: MB.ALGORITHM, out }));
"""
# pronounce the names people actually hold or that carry a story (the rest are sounded out live in the browser)
PRON = json.load(open(os.path.join(DATA, "pron.json")))
storied = [r[0] for r in db.execute("SELECT DISTINCT display_name FROM names JOIN meanings USING(name_id) WHERE display_name NOT LIKE '% %'")]
targets = sorted({d for d in ids if " " not in d and "-" not in d and norm(d) in PRON} | set(storied))
res = json.loads(subprocess.run(["node", "-e", NODE], input=json.dumps(targets), capture_output=True, text=True, cwd=HERE, check=True).stdout)
SRC_ID = lambda s: "cmudict" if "English" in s or "common way" in s else "hand-checked" if "hand" in s else "rules"
for p in res["out"]:
    nid = ids[p["n"]]
    syl = p["syl"]
    phon = " ".join(" ".join([*s["on"], s["v"] + str(s["stress"]), *s["co"]]) for s in syl)
    stressed = next((i for i, s in enumerate(syl) if s["stress"] == 1), None)
    cur = db.execute("INSERT INTO pronunciations (name_id, language, phonemes, respelling, syllable_count, primary_stress, has_diphthong, is_primary, source_id, confidence) VALUES (?,?,?,?,?,?,?,?,?,?)",
                     (nid, p["source"], phon, p["say"], len(syl), stressed, int(any(s["v"] in ("AY", "EY", "OY", "AW", "OW") for s in syl)), int(p["k"] == 0), SRC_ID(p["source"]),
                      .95 if "hand" in p["source"] else .85 if SRC_ID(p["source"]) == "cmudict" else .6))
    pid = cur.lastrowid
    for i, s in enumerate(syl):
        on = next((x for x in s["on"] if x != "HH"), s["on"][0] if s["on"] else "")
        place = "lips" if on in "P B M F V W".split() else "lr" if on in ("L", "R") else "tip" if on in "T D N S Z TH DH SH ZH CH JH".split() else "back" if on in "K G NG Y".split() else "h" if on == "HH" else "none"
        manner = "soft" if not on or on in "M N NG L R W Y".split() else "warm" if on in "B D G JH".split() else "crisp" if on in "P T K CH".split() else "airy"
        db.execute("INSERT INTO syllables VALUES (?,?,?,?,?,?,?,?)", (pid, i, " ".join(s["on"]), s["v"], " ".join(s["co"]), s["stress"], place, manner))
    if p["notes"]:
        db.execute("INSERT INTO lullabytes VALUES (?,?,?,?,?,?,?,?,?,?)", (pid, res["algorithm"], "C major pentatonic, C5–C7", p["notes"], p["steps"], p["vel"], p["art"], round(p["shape"], 3), "C5", 0))

# ── popularity observations: every year, full counts, from the official sources ──
spec = importlib.util.spec_from_file_location("build_years_src", os.path.join(HERE, "scripts/build_years.py"))
src = open(os.path.join(HERE, "scripts/build_years.py"), encoding="utf-8").read()
src = src[: src.index("out = {")]                       # the parsers and PLACES, without writing years.json
mod = {"__file__": os.path.join(HERE, "scripts/build_years.py"), "__name__": "build_years_src"}
exec(compile(src, "build_years.py", "exec"), mod)
for p in mod["PLACES"]:
    fn = p.get("fn")
    if not fn: continue
    sid = "obs-" + p["key"]
    db.execute("INSERT OR REPLACE INTO sources VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL)",
               (sid, p["agency"], p["dataset"], None, p["label"], "statistical agency", None, None, p.get("badge") or ("ranked" if p.get("coverage") == "top" else "full"),
                p.get("threshold"), p.get("rule"), "nearest " + str(p["rounded"]) if p.get("rounded") else None, None, p["license"]))
    counts = fn()
    n_obs, years = 0, []
    for y, sexes in counts.items():
        years.append(int(y))
        for sex, ctr in sexes.items():
            for rank, (spelling, c) in enumerate(ctr.most_common(), 1):
                nid = (by_norm.get(norm(spelling)) or [None])[0]
                span = (p.get("periods") or {}).get(str(y)) or ([int(y), int(y) + p["period"] - 1] if p.get("period") and int(y) not in p.get("single_years", []) else None)
                db.execute("INSERT INTO popularity_observations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                           (nid, spelling, sex, int(y), "decade" if p.get("decades") else "period" if span else "year", c, rank, p["label"], int(bool(p.get("rounded"))),
                            "phonetic" if p.get("grouped") else None, 1 if p.get("first_name_only") else None, span[0] if span else None, span[1] if span else None, sid))
                n_obs += 1
    if years: db.execute("UPDATE sources SET data_start_year=?, data_end_year=? WHERE source_id=?", (min(years), max(years), sid))
    print(f"  observations {p['key']:4} {n_obs:>9,}", flush=True)

db.commit()

# ── checks: the rules the schema promises ──
q = lambda s: db.execute(s).fetchone()[0]
checks = [
    ("every name keeps its display spelling", q("SELECT COUNT(*) FROM names WHERE display_name IS NULL OR display_name = ''") == 0),
    ("no observation claims a zero count", q("SELECT COUNT(*) FROM popularity_observations WHERE count = 0") == 0),
    ("every observation names its source", q("SELECT COUNT(*) FROM popularity_observations WHERE source_id IS NULL") == 0),
    ("every lullaby records its algorithm", q("SELECT COUNT(*) FROM lullabytes WHERE algorithm_version IS NULL") == 0),
    ("the signature C is never part of the name", q("SELECT COUNT(*) FROM lullabytes WHERE signature_in_name = 1") == 0),
]
print()
for label, ok in checks: print(("✓ " if ok else "✗ ") + label)
for t in ["names", "name_forms", "meanings", "associations", "name_references", "relationships", "pronunciations", "syllables", "lullabytes", "popularity_observations", "sources"]:
    print(f"{t:24} {q(f'SELECT COUNT(*) FROM {t}'):>10,}")
db.execute("VACUUM")
db.close()
print("wrote", DB, os.path.getsize(DB) // 1024 // 1024, "MB")
if not all(ok for _, ok in checks): sys.exit(1)
