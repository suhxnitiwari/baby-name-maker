# Adds every official first-name list in raw/ (see fetch_world.py) to data/names-db.tsv.
# Each file is read the same way: find the name column, the count column (or year columns to sum),
# and the sex (from a column, the header, or the file name). One name per entry, Latin script only
# (the music box and search need letters it can sound out), registry placeholders removed.
#
#   python3 scripts/fetch_world.py && python3 scripts/build_world.py
import csv, gzip, io, json, os, re, sys, tempfile, unicodedata, zipfile, collections
import xml.etree.ElementTree as ET
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); RAW = os.path.join(ROOT, "raw")
sys.path.insert(0, HERE)
import xlsx
from single_names import single_names

DB = os.path.join(ROOT, "data", "names-db.tsv")
# file prefix → country code stored in the database
CC = {"pl": "pl", "br": "br", "il": "il", "cl": "cl", "ni": "nir", "bc": "ca", "ab": "ca", "on": "ca", "au": "au", "zh": "ch",
      "de": "de", "pt": "pt", "lu": "lu", "no": "no", "sct": "sct", "nz": "nz", "be": "be", "at": "at", "fi": "fi"}

NAME_RE = re.compile(r"(^m[aä]dchen$|^maedchen$|^jungen$|^knaben$|^girls?$|^boys?$|^weiblich$|^m[aä]nnlich$|vorname|^name|names?$|nome|nombre|first.?name|forename|given|pr[eé]nom|imi[eę]|navn|baby|voornaam|nimi|^navn)", re.I)
COUNT_RE = re.compile(r"(anzahl|^anz|count|number|frequen|cantidad|^total|liczba|occurr|h[aä]ufig|^n$|amount|births|babies|aantal|antall|lukum|fr[eé]quence|^freq|personen|^value$|^wert$)", re.I)
SEX_RE = re.compile(r"(geschlecht|^sex|gender|^sexo|p[lł]e[cć]|^kj[oø]nn|^k[oö]n$|^sukupuoli)", re.I)
SKIP_RE = re.compile(r"(rank|platz|position|^year|^jahr|anio|^ano$|ranking|prop|percent|prozent|%|stichtag)", re.I)
FEM = re.compile(r"(^f$|^w$|^k$|^2$|female|girl|fem|weib|m[aä]d|maed|kobieta|żeńsk|zensk|mujer|femme|^fille|^jente|^tytt|^nainen|^vrouw|^meisje|^frau)", re.I)
MAL = re.compile(r"(^m$|^1$|^h$|male|boy|masc|m[aä]nn|maenn|junge|jung|knab|mężczyzna|mezczyzna|męsk|mesk|hombre|varón|homme|gar[cç]on|^gutt|^poika|^mies|^man$|^jongen|^herr)", re.I)
PLACEHOLDERS = {"nombreunico", "sinnombre", "otros", "noinformado", "desconocido", "baby", "babyboy", "babygirl", "unknown", "infant", "unnamed",
                "notnamed", "noname", "male", "female", "boy", "girl", "child", "newborn", "bebe", "nn", "ohnevorname", "unbekannt", "keinvorname",
                "sonstige", "andere", "other", "others", "total", "gesamt", "summe", "insgesamt", "name", "vorname", "girls", "boys", "names",
                "kein", "ohne", "recien", "reciennacido", "nacido", "nacida", "hijo", "hija", "test", "sin", "jr", "sr", "md", "wm", "ii", "iii", "na"}
# every name needs a vowel (drops initials and abbreviations like "Md", "Jr", "Wm", "Tj")
VOWEL = re.compile(r"[aeiouyAEIOUYÀ-ÆÈ-ÏÒ-ÖØ-Ýà-æè-ïò-öø-ýĀ-ąĒ-ěĨ-ıŌ-őŨ-ųǍ-ǜẠ-ỹ]")
def ok(n): return bool(VOWEL.search(n)) and key(n).replace(" ", "").replace("-", "") not in PLACEHOLDERS
LATIN = re.compile(r"^[A-Za-zÀ-ɏḀ-ỿ' \-]+$")

def clean(n):
    n = re.sub(r"\s+", " ", str(n or "").replace("\xa0", " ")).strip().strip("'").strip()
    if not n or not LATIN.match(n) or len(n.replace(" ", "").replace("-", "")) < 2: return None
    if n.isupper() or n.islower():
        n = " ".join("-".join(p[:1].upper() + p[1:].lower() for p in w.split("-")) for w in n.split(" "))
    k = key(n)
    if re.search(r"(ovna|evna|ivna|ichna|ovich|evich|ovych|ivich|yevich|ovič|evič|oglu|oğlu|qizi|kyzy)$", k): return None   # patronymics, not first names
    return n if ok(n) else None
key = lambda n: unicodedata.normalize("NFC", n).lower()

def num(v):
    s = str(v or "").strip()
    if s in ("..", "<5", "<3", "x", "*", "<10"): return 1          # suppressed small counts: the name was given, just a few times
    if re.fullmatch(r"\d+\.0+", s): s = s.split(".")[0]
    d = re.sub(r"[^\d]", "", s)
    return int(d) if d and len(d) < 10 else 0

def sex_of(*hints):
    for h in hints:
        h = str(h or "").strip()
        if not h: continue
        for part in re.split(r"[\s_\-/.()]+", h) + [h]:
            if FEM.search(part): return "f"
            if MAL.search(part): return "m"
    return "?"

# ── reading any file into tables (rows of cells) ──
def decode(b):
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try: return b.decode(enc)
        except UnicodeDecodeError: pass
def csv_rows(text):
    sample = text[:5000]
    delim = max([",", ";", "\t", "|"], key=sample.count)
    return list(csv.reader(io.StringIO(text), delimiter=delim))
def xlsx_tables(path):
    z = zipfile.ZipFile(path)
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    for s in wb.iter("{%s}sheet" % xlsx.NS["m"]):
        yield s.get("name"), [r for r in xlsx.rows(path, s.get("name"))]
def tables(path, data=None, label=""):
    data = data if data is not None else open(path, "rb").read()
    label = label or os.path.basename(path)
    if data[:2] == b"\x1f\x8b": data = gzip.decompress(data)
    if data[:2] == b"PK":
        z = zipfile.ZipFile(io.BytesIO(data))
        if "xl/workbook.xml" in z.namelist():
            with tempfile.NamedTemporaryFile(suffix=".xlsx") as t:
                t.write(data); t.flush()
                for sh, rows in xlsx_tables(t.name): yield f"{label} {sh}", rows
        else:
            for m in z.namelist():
                if m.endswith("/") or not re.search(r"\.(csv|txt|xlsx|tsv)$", m, re.I): continue
                yield from tables(None, z.read(m), f"{label} {m}")
        return
    if data.lstrip()[:1] in (b"[", b"{"):
        d = json.loads(decode(data))
        recs = d if isinstance(d, list) else next((v for v in d.values() if isinstance(v, list)), [])
        recs = [r for r in recs if isinstance(r, dict)]
        if recs:
            cols = list(recs[0].keys())
            yield label, [cols] + [[r.get(c) for c in cols] for r in recs]
        return
    if b"urn:schemas-microsoft-com:office:spreadsheet" in data[:2000]:
        ns = "{urn:schemas-microsoft-com:office:spreadsheet}"
        root = ET.fromstring(data)
        for ws in root.iter(ns + "Worksheet"):
            rows = []
            for row in ws.iter(ns + "Row"):
                out = []
                for c in row.findall(ns + "Cell"):
                    i = c.get(ns + "Index")
                    if i: out += [""] * (int(i) - 1 - len(out))
                    d = c.find(ns + "Data"); out.append("".join(d.itertext()) if d is not None else "")
                rows.append(out)
            yield f"{label} {ws.get(ns + 'Name')}", rows
        return
    text = decode(data)
    if text and not text.lstrip().lower().startswith(("<!doctype", "<html", "<?xml")): yield label, csv_rows(text)

# ── reading a table into (name, sex, count) ──
def read_table(label, rows):
    rows = [[("" if c is None else str(c)).strip() for c in r] for r in rows if r]
    for h in range(min(25, len(rows))):
        hdr = [c.lower() for c in rows[h]]
        names = [i for i, c in enumerate(hdr) if NAME_RE.search(c) and not COUNT_RE.search(c) and not SEX_RE.search(c) and not SKIP_RE.search(c)]
        if names: break
    else:
        return
    counts = [i for i, c in enumerate(hdr) if COUNT_RE.search(c) and not SKIP_RE.search(c)]
    sexes = [i for i, c in enumerate(hdr) if SEX_RE.search(c) and not SKIP_RE.search(c)]
    years = [i for i, c in enumerate(hdr) if re.fullmatch(r"(18|19|20)\d\d", c)]
    for r in rows[h + 1:]:
        for j, ni in enumerate(names):
            if ni >= len(r): continue
            if len(names) > 1:   # paired columns: "Girl names | Count | Boy names | Count"
                nxt = names[j + 1] if j + 1 < len(names) else len(hdr)
                cc = [i for i in counts if ni < i < nxt] or [i for i in range(ni + 1, min(nxt, len(r))) if re.fullmatch(r"[\d.,\s]+", r[i] or "")][:1]
                cnt = num(r[cc[0]]) if cc and cc[0] < len(r) else 1
                sx = sex_of(hdr[ni], hdr[cc[0]] if cc else "", label)
            else:
                if counts: cnt = sum(num(r[i]) for i in counts[:1] if i < len(r))
                elif years: cnt = sum(num(r[i]) for i in years if i < len(r))
                else: cnt = 1
                sx = sex_of(r[sexes[0]] if sexes and sexes[0] < len(r) else "", hdr[ni], label)
            n = clean(r[ni])
            if n: yield n, sx, max(cnt, 1)

# special cases
def brazil(path):
    for r in csv.DictReader(io.StringIO(gzip.decompress(open(path, "rb").read()).decode("utf-8"))):
        f, m = num(r["frequency_female"]), num(r["frequency_male"])
        n = clean(r["first_name"])
        if not n: continue
        if f: yield n, "f", f
        if m: yield n, "m", m

def norway():
    # Statistics Norway: everyone's first names (table 10501) and newborns since 1880 (table 10467); 1 = girl, 2 = boy
    import urllib.request
    p = os.path.join(RAW, "no-10501.json")
    if not os.path.exists(p): return
    for t in ("no-10501.json", "no-10467.json"):
        d = json.load(open(os.path.join(RAW, t)))
        names = d["dimension"]["Fornavn"]["category"]
        idx, lab = names["index"], names["label"]
        vals = d["value"]; per = len(vals) // len(idx)
        for code, pos in idx.items():
            n = clean(lab[code].split(" ")[0].title())
            tot = sum(v or 0 for v in vals[pos * per:(pos + 1) * per])
            if n: yield n, "f" if code.startswith("1") else "m", max(1, tot)

def load_sources():
    out = collections.defaultdict(list)   # cc → [(name, sex, count)]
    per_file = []
    for fn in sorted(os.listdir(RAW)):
        path = os.path.join(RAW, fn)
        pre = re.split(r"[-.]", fn)[0]
        cc = CC.get(pre)
        if not cc or fn.startswith("no-"): continue
        got = []
        try:
            if pre == "br": got = list(brazil(path))
            else:
                for label, rows in tables(path): got += list(read_table(label, rows))
        except Exception as e:
            print("  !", fn, e); continue
        per_file.append((fn, len(got)))
        out[cc] += got
    out["no"] += list(norway())
    return out, per_file

if __name__ == "__main__":
    # start from the 10 registries already in the database
    fem = collections.Counter(); mal = collections.Counter(); unk = collections.Counter()
    where = collections.defaultdict(set); disp = {}
    # the 10 original registries, frozen the first time this runs (so running it again never double-counts)
    BASE = os.path.join(RAW, "base-10-registries.tsv")
    if not os.path.exists(BASE): open(BASE, "w", encoding="utf-8").write(open(DB, encoding="utf-8").read())
    for line in open(BASE, encoding="utf-8"):
        n, g, ccs, c = line.rstrip("\n").split("\t"); c = int(c); k = key(n)
        disp[k] = n; where[k].update(ccs.split(","))
        if g == "f": fem[k] += c
        elif g == "m": mal[k] += c
        elif g == "u": fem[k] += c // 2; mal[k] += c - c // 2
        else: unk[k] += c
    before = len(disp)
    src, per_file = load_sources()
    added = {}
    for cc, items in src.items():
        new = set()
        for n, sx, c in items:
            k = key(n)
            if k not in disp: disp[k] = n; new.add(k)
            {"f": fem, "m": mal}.get(sx, unk)[k] += c
            where[k].add(cc)
        added[cc] = (len({key(n) for n, _, _ in items}), len(new))
    rows = []
    for k, n in disp.items():
        f, m, u = fem[k], mal[k], unk[k]
        g = "?" if f + m == 0 else "f" if f >= .8 * (f + m) else "m" if m >= .8 * (f + m) else "u"
        rows.append((n, g, ",".join(sorted(where[k])), f + m + u))
    rows = [r for r in single_names(rows) if ok(r[0])]
    with open(DB, "w", encoding="utf-8") as fh:
        for r in rows: fh.write(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\n")
    print(f"{before:,} names before → {len(rows):,} single first names now")
    for cc, (tot, new) in sorted(added.items(), key=lambda kv: -kv[1][1]): print(f"  {cc:4} {tot:>8,} names in its lists · {new:>7,} new")
    json.dump({"files": per_file, "countries": {cc: {"names": t, "new": n} for cc, (t, n) in added.items()}},
              open(os.path.join(RAW, "build-report.json"), "w"), indent=1)
