"""The numbers under the headline, counted from the data itself → data/stats.json.

countries  every country whose official agency published the names (birth registers, name lists, statistics offices)
records    every time a name was counted in those records (the per-name totals in names-db.tsv, summed)
texts      sacred texts and epics the names are cited from (data/sacred.json corpora), and their traditions
passages   cited passages
languages  languages a name is shown in its own script (data/native-forms.json)
years      the span of the yearly records (data/years.json)
names      distinct names, as the page counts them (it builds the invented names itself, so pass its count: the console
           prints "names: N" once everything has loaded): python3 scripts/build_stats.py --names N
           The page climbs to this number on arrival, then corrects it with its own live count.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda f: os.path.join(ROOT, "data", f)

# source code / place → country (Québec is Canada, Northern Ireland and Scotland are the UK, Berlin is Germany …)
COUNTRY = {"us": "US", "ca": "CA", "qc": "CA", "au": "AU", "uk": "GB", "nir": "GB", "sct": "GB", "ie": "IE", "fr": "FR", "es": "ES", "ch": "CH",
           "ar": "AR", "br": "BR", "cl": "CL", "pl": "PL", "de": "DE", "at": "AT", "no": "NO", "lu": "LU", "pt": "PT", "il": "IL", "fi": "FI",
           "be": "BE", "nz": "NZ", "dk": "DK", "cz": "CZ", "cy": "CY", "hu": "HU", "is": "IS", "ro": "RO", "jp": "JP", "it": "IT", "tr": "TR", "tw": "TW", "se": "SE", "es": "ES"}
PLACE = {"the United States": "US", "Canada": "CA", "England & Wales": "GB", "Scotland": "GB", "Northern Ireland": "GB", "Ireland": "IE",
         "France": "FR", "Catalonia": "ES", "Switzerland": "CH", "Brazil": "BR", "Chile": "CL", "Poland": "PL", "Berlin": "DE", "Austria": "AT",
         "Norway": "NO", "Luxembourg": "LU", "Finland": "FI", "Denmark": "DK", "New Zealand": "NZ", "New South Wales": "AU", "Queensland": "AU",
         "Sweden": "SE", "the Netherlands": "NL", "Bulgaria": "BG", "Latvia": "LV", "Moldova": "MD", "South Africa": "ZA",
         "Federation of BiH": "BA", "Republika Srpska": "BA", "Spain": "ES", "Italy": "IT", "Türkiye": "TR", "Taiwan": "TW", "Belgium": "BE"}

countries, records = set(), 0
for f in ["names-db.tsv", "names-extra.tsv"]:
    for line in open(D(f), encoding="utf-8"):
        x = line.rstrip("\n").split("\t")
        if len(x) < 3:
            continue
        countries |= {COUNTRY[c] for c in x[2].split(",") if c in COUNTRY}
        if f == "names-db.tsv" and len(x) > 3 and x[3].isdigit():
            records += int(x[3])
places = json.load(open(D("years.json"), encoding="utf-8"))["places"]
missing = [p["label"] for p in places if p["label"] not in PLACE]
assert not missing, f"map these places to a country: {missing}"
countries |= {PLACE[p["label"]] for p in places}

sac = json.load(open(D("sacred.json"), encoding="utf-8"))
nf = json.load(open(D("native-forms.json"), encoding="utf-8"))
old = json.load(open(D("stats.json"), encoding="utf-8")) if os.path.exists(D("stats.json")) else {}
out = {
    "names": int(sys.argv[sys.argv.index("--names") + 1]) if "--names" in sys.argv else old.get("names", 0),
    "countries": len(countries),
    "records": records,
    "texts": len(sac["c"]),
    "traditions": len(sac["t"]),
    "passages": sum(len(refs) for _, _, refs in sac["n"]),
    "languages": len({l for forms in nf.values() for _, l in forms}),
    "from": min(int(p["first"]) for p in places if p.get("first")),
    "to": max(int(p["last"]) for p in places if p.get("last")),
}
json.dump(out, open(D("stats.json"), "w", encoding="utf-8"), separators=(",", ":"))
print(out)
