# Turns official baby-name data from several countries into one compact JSON for the app.
import csv, io, json, os, re, zipfile, collections, sys
sys.path.insert(0, os.path.dirname(__file__))
import xlsx

D = "/private/tmp/claude-501/bnm-data"
OUT = sys.argv[1] if len(sys.argv) > 1 else "popularity.json"
TOP = 100        # names per top list
LOOKUP = 1000    # names per sex per country kept for card badges / spelling ranking

def title(n):
    n = n.strip()
    return "-".join(p[:1].upper() + p[1:].lower() for p in n.split("-")) if n.isupper() or n.islower() else n

# counts[sex][name][year] = births
def new(): return {"girl": collections.defaultdict(dict), "boy": collections.defaultdict(dict)}

def us():
    c = new()
    for f in os.listdir(f"{D}/ssa"):
        m = re.match(r"yob(\d{4})\.txt", f)
        if not m: continue
        y = int(m.group(1))
        for name, sex, n in csv.reader(open(f"{D}/ssa/{f}")):
            c["girl" if sex == "F" else "boy"][name][y] = int(n)
    return c

def nsw():
    c = new()
    for r in csv.DictReader(open(f"{D}/nsw.csv", encoding="utf-8-sig")):
        c["girl" if r["Gender"].startswith("F") else "boy"][title(r["Name"])][int(r["Year"])] = int(r["Number"])
    return c

def bc():
    c = new()
    for sex, f in (("boy", "bc-boys.csv"), ("girl", "bc-girls.csv")):
        rows = list(csv.reader(open(f"{D}/{f}", encoding="utf-8-sig")))
        years = rows[0][1:]
        for r in rows[1:]:
            if not r or not r[0] or r[0].upper() == "TOTAL": continue
            for y, v in zip(years, r[1:]):
                if y.isdigit() and v and v.strip().isdigit() and int(v) > 0:
                    c[sex][title(r[0])][int(y)] = int(v)
    return c

def canada():
    c = new()
    z = zipfile.ZipFile(f"{D}/statcan.zip")
    with z.open("17100147.csv") as fh:
        rd = csv.reader(io.TextIOWrapper(fh, encoding="utf-8-sig"))
        next(rd)
        for r in rd:
            if r[1] != "Canada" or r[5] != "Frequency" or not r[12]: continue
            sex = "girl" if r[3].startswith("F") else "boy" if r[3].startswith("M") else None
            if sex: c[sex][title(r[4])][int(r[0])] = int(float(r[12]))
    return c

def france():
    c = new()
    for r in csv.DictReader(open(glob1(f"{D}/fr", ".csv"), encoding="utf-8"), delimiter=";"):
        if not r["periode"].isdigit() or r["prenom"].startswith("_"): continue
        c["boy" if r["sexe"] == "1" else "girl"][title(r["prenom"])][int(r["periode"])] = int(r["valeur"])
    return c

def england_wales():
    c = new()
    for sex, sheet in (("girl", "Table_1"), ("boy", "Table_2")):
        head = None
        for r in xlsx.rows(f"{D}/ew.xlsx", sheet):
            if r and r[0] == "Name": head = r; continue
            if not head or not r or not r[0]: continue
            for i, h in enumerate(head):
                m = re.match(r"(\d{4}) Count", h or "")
                if m and i < len(r) and r[i] and str(r[i]).isdigit():
                    c[sex][title(r[0])][int(m.group(1))] = int(r[i])
    return c

def glob1(d, ext): return next(os.path.join(d, f) for f in os.listdir(d) if f.endswith(ext))

SOURCES = [
    ("us", "United States", "US Social Security Administration", us),
    ("ca", "Canada", "Statistics Canada", canada),
    ("au", "Australia · New South Wales", "NSW Registry of Births, Deaths & Marriages", nsw),
    ("ew", "England & Wales (incl. London)", "Office for National Statistics", england_wales),
    ("fr", "France", "INSEE", france),
]

out = {"countries": [], "lookup": {}}
for key, label, source, fn in SOURCES:
    c = fn()
    years = sorted({y for s in c.values() for d in s.values() for y in d})
    first, last = years[0], years[-1]
    entry = {"key": key, "label": label, "source": source, "first": first, "last": last, "top": {}}
    for win in ("1", "5", "50", "100"):
        start = max(first, last - int(win) + 1)
        entry["top"][win] = {"from": start}
        for sex in ("girl", "boy"):
            tot = {n: sum(v for y, v in d.items() if y >= start) for n, d in c[sex].items()}
            entry["top"][win][sex] = [[n, t] for n, t in sorted(tot.items(), key=lambda kv: -kv[1])[:TOP] if t > 0]
    # lookup: latest-year rank + count, and 5-year total, for each sex
    look = {}
    for sex in ("girl", "boy"):
        latest = sorted(((n, d.get(last, 0)) for n, d in c[sex].items()), key=lambda kv: -kv[1])
        for rank, (n, v) in enumerate(latest[:LOOKUP], 1):
            if v <= 0: break
            look[f"{sex[0]}:{n.lower()}"] = [rank, v]
    out["lookup"][key] = look
    out["countries"].append(entry)
    print(f"{key:3} {label:32} {first}-{last}  girls#1 now: {entry['top']['1']['girl'][0]}  boys#1 now: {entry['top']['1']['boy'][0]}  lookup {len(look)}", flush=True)

json.dump(out, open(OUT, "w"), ensure_ascii=False, separators=(",", ":"))
print("wrote", OUT, os.path.getsize(OUT) // 1024, "KB")
