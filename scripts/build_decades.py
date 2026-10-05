# The time machine: the most-given names of every decade, for the charts.
#   US: Social Security Administration, 1880-2017 via the babynames R package (hadley/babynames),
#       aggregated by decade with R into us-decades.tsv; the 2020s come from data/popularity.json (SSA, 2020-2024).
#   NSW: Registry of Births, Deaths & Marriages, 1952-2025 (raw/au-nsw-popular-baby-names-from-1952-*.csv).
import csv, glob, json, os, sys, collections

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
US_TSV = sys.argv[1] if len(sys.argv) > 1 else "/private/tmp/claude-501/bnm-data/us-decades.tsv"
TOP = 12

def title(n):
    return "-".join(p[:1].upper() + p[1:].lower() for p in n.strip().split("-"))

def top(counter):
    return [[n, c] for n, c in counter.most_common(TOP)]

out = {"countries": []}

# United States
us = collections.defaultdict(lambda: {"girl": collections.Counter(), "boy": collections.Counter()})
for r in csv.DictReader(open(US_TSV), delimiter="\t"):
    us[int(r["dec"])]["girl" if r["sex"] == "F" else "boy"][r["name"]] += int(r["n"])
pop = json.load(open(os.path.join(HERE, "data/popularity.json")))
usp = next(c for c in pop["countries"] if c["key"] == "us")
w = usp["top"]["5"]
decades = {str(d): {"girl": top(v["girl"]), "boy": top(v["boy"])} for d, v in sorted(us.items())}
decades["2010"]["note"] = "2010-2017"
decades["2020"] = {"girl": w["girl"][:TOP], "boy": w["boy"][:TOP], "note": f"{w['from']}-{usp['last']}"}
out["countries"].append({"key": "us", "label": "the United States", "source": "US Social Security Administration", "decades": decades})

# New South Wales
nsw = collections.defaultdict(lambda: {"girl": collections.Counter(), "boy": collections.Counter()})
years = set()
for f in glob.glob(os.path.join(HERE, "raw/au-nsw-popular-baby-names-from-1952-*.csv")):
    for r in csv.DictReader(open(f, encoding="utf-8-sig")):
        y = int(r["Year"]); years.add(y)
        nsw[y // 10 * 10]["girl" if r["Gender"].startswith("F") else "boy"][title(r["Name"])] += int(r["Number"])
decades = {str(d): {"girl": top(v["girl"]), "boy": top(v["boy"])} for d, v in sorted(nsw.items())}
decades["1950"]["note"] = "1952-1959"
decades[str(max(years) // 10 * 10)]["note"] = f"{max(years) // 10 * 10}-{max(years)}"
out["countries"].append({"key": "au", "label": "New South Wales", "source": "NSW Registry of Births, Deaths & Marriages", "decades": decades})

path = os.path.join(HERE, "data/decades.json")
json.dump(out, open(path, "w"), ensure_ascii=False, separators=(",", ":"))
for c in out["countries"]:
    ds = sorted(c["decades"])
    print(c["key"], ds[0], "-", ds[-1], {d: c["decades"][d]["girl"][0][0] for d in ds})
print("wrote", path, os.path.getsize(path) // 1024, "KB")
