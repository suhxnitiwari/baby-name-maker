# Builds data/names-db.tsv: every real name from official government registries.
# Columns: name <TAB> gender (f / m / u = used for both / ? = registry has no sex) <TAB> countries <TAB> total recorded
import sys, os, csv, json, re, unicodedata, collections
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.dirname(HERE)
sys.path.insert(0, HERE); import xlsx
DB_OUT = sys.argv[1] if len(sys.argv) > 1 else "names-db.tsv"

sys.argv = ["x", "/dev/null"]
exec(open(os.path.join(HERE, "build.py")).read().split("SOURCES = [")[0])  # us, canada, nsw, england_wales, france loaders
OUT = DB_OUT

VALID = re.compile(r"^[^\W\d_]+(?:[ '\-][^\W\d_]+)*$", re.UNICODE)
def clean(n):
    n = re.sub(r"\s+", " ", (n or "").strip())
    if not VALID.match(n) or len(n.replace(" ", "")) < 2: return None
    return title_words(n)
PARTICLES = {"de", "del", "la", "las", "los", "y", "da", "das", "do", "dos", "di", "du", "van", "von", "der", "e"}
def title_words(n):
    # "MARIA DEL CARMEN" → "Maria del Carmen", "JEAN-PIERRE" → "Jean-Pierre", "mc kenzie" → "Mc Kenzie"
    words = n.split(" ")
    out = []
    for i, w in enumerate(words):
        lw = w.lower()
        if i > 0 and lw in PARTICLES: out.append(lw); continue
        out.append("-".join(p[:1].upper() + p[1:].lower() for p in w.split("-")) if (w.isupper() or w.islower()) else w)
    return " ".join(out)
def key(n): return unicodedata.normalize("NFC", n).lower().replace(" ", "").replace("-", "")

# per-name tallies
fem = collections.Counter(); mal = collections.Counter(); unk = collections.Counter()
where = collections.defaultdict(set); display = {}
# placeholders registries use when a baby has no name yet
PLACEHOLDERS = {"nombreunico", "sinnombre", "otros", "noinformado", "desconocido", "baby", "babyboy", "babygirl", "unknown",
                "infant", "unnamed", "notnamed", "noname", "male", "female", "boy", "girl", "child", "newborn", "bebe", "nn"}
def add(name, sex, count, cc):
    n = clean(name)
    if not n or count <= 0 or key(n) in PLACEHOLDERS: return
    k = key(n)
    display.setdefault(k, n)
    {"f": fem, "m": mal, "?": unk}[sex][k] += count
    where[k].add(cc)

def from_year_counts(c, cc):
    for sex, s in (("girl", "f"), ("boy", "m")):
        for n, years in c[sex].items(): add(n, s, sum(years.values()), cc)

for cc, fn in (("us", us), ("ca", canada), ("au", nsw), ("uk", england_wales), ("fr", france)):
    from_year_counts(fn(), cc); print(cc, len(display), flush=True)

# Spain (population counts, names held by 20+ people)
for sheet, s in (("Hombres", "m"), ("Mujeres", "f")):
    on = False
    for r in xlsx.rows(f"{D}/es.xlsx", sheet):
        if r and r[0] == "Orden": on = True; continue
        if on and r and len(r) > 2 and r[1] and r[2]: add(r[1], s, int(float(r[2])), "es")
print("es", len(display), flush=True)

# Ireland (CSO JSON-stat: statistic × year × name)
for t, s in (("VSA50", "m"), ("VSA60", "f")):
    d = json.load(open(f"{D}/ie-{t}.json"))
    ids = d["id"]; size = d["size"]; namedim = d["dimension"][ids[-1]]["category"]
    # JSON-stat "index" is either a list of codes in order, or {code: position}
    order = lambda cat: cat["index"] if isinstance(cat["index"], list) else [c for c, _ in sorted(cat["index"].items(), key=lambda kv: kv[1])]
    names = [namedim["label"][c] for c in order(namedim)]
    statcat = d["dimension"][ids[0]]["category"]
    count_stat = next(i for i, c in enumerate(order(statcat)) if "Rank" not in statcat["label"][c])
    vals = d["value"]; ny, nn = size[1], size[2]
    for k, n in enumerate(names):
        tot = 0
        for y in range(ny):
            v = vals[count_stat * ny * nn + y * nn + k] if isinstance(vals, list) else vals.get(str(count_stat * ny * nn + y * nn + k))
            if isinstance(v, (int, float)): tot += v
        add(n, s, int(tot), "ie")
print("ie", len(display), flush=True)

# Québec (every name since 1980; "<5" counted as 2)
for f, s in (("qc-f.csv", "f"), ("qc-m.csv", "m")):
    rd = csv.reader(open(f"{D}/{f}", encoding="utf-8-sig"))
    next(rd)
    for r in rd:
        if not r: continue
        tot = sum(2 if v.strip() == "<5" else int(v) if v.strip().isdigit() else 0 for v in r[1:])
        add(r[0], s, tot, "qc")
print("qc", len(display), flush=True)

# Switzerland (whole population, by birth year)
for f, s in (("ch-f.csv", "f"), ("ch-m.csv", "m")):
    for r in csv.DictReader(open(f"{D}/{f}", encoding="utf-8-sig")):
        v = r.get("VALUE", "")
        if v and v.isdigit(): add(r["firstname"], s, int(v), "ch")
print("ch", len(display), flush=True)

# Argentina (RENAPER, newborns 2012–2024; this file has no sex column)
for r in csv.DictReader(open(f"{D}/ar.csv", encoding="utf-8")):
    add(r["nombre"], "?", int(r["cantidad"] or 0), "ar")
print("ar", len(display), flush=True)

rows = []
for k, n in display.items():
    f, m, u = fem[k], mal[k], unk[k]
    if f + m == 0: g = "?"
    elif f >= .8 * (f + m): g = "f"
    elif m >= .8 * (f + m): g = "m"
    else: g = "u"
    rows.append((n, g, ",".join(sorted(where[k])), f + m + u))
from single_names import single_names
rows = single_names(rows)  # one name per entry: split "María del Carmen" into María and Carmen
with open(OUT, "w", encoding="utf-8") as fh:
    for r in rows: fh.write(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\n")
g = collections.Counter(r[1] for r in rows)
print("TOTAL", len(rows), dict(g), "→", OUT, os.path.getsize(OUT) // 1024, "KB")
