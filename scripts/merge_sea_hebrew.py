"""Ready data/sea-names.json and data/hebrew-extra.json for the page, and apply data/sea-fixes.json to data/culture-names.json.

- a name the site already knows from another list keeps its culture: its row loses the ease slot (which would claim the culture)
  and only adds its line, script and culture alongside (Em stays English; Khmer Em joins it)
- Filipino rows that restate a name culture-names.json already has are left out
- respelled and dropped names leave culture-names.json (the respelled ones have full rows in sea-names.json)
"""
import json, os, re, unicodedata
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda f: os.path.join(ROOT, "data", f)
fold = lambda s: "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")
load = lambda f: json.load(open(D(f), encoding="utf-8"))
save = lambda f, x: json.dump(x, open(D(f), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

culture = load("culture-names.json")
for fx in load("sea-fixes.json"):
    if fx["action"] in ("respell", "drop"):
        culture = [r for r in culture if r[0] != fx["name"]]
    elif fx["action"] == "untag":
        for r in culture:
            if r[0] == fx["name"]:
                r[9] = [c for c in r[9] if c != fx["tag"]]
                r[6] = r[6].replace(f" Also a {fx['tag']} name.", "")
                if r[2] == fx["tag"]: r[2] = ""
culture = [r for r in culture if r[0] != "Sagat" or "Bengali" not in (r[2], r[3])]   # the merged Wikidata item: Kazakh, Thai, Hindi and Bengali names in one row
save("culture-names.json", culture)

known = {fold(r[0]) for r in culture}
for f in os.listdir(os.path.join(ROOT, "data")):
    if f.endswith("-names.json") and f not in ("sea-names.json", "famous-names.json", "bollywood-names.json"):
        try: known |= {fold(r[0]) for r in load(f) if isinstance(r, list) and r and isinstance(r[0], str)}
        except Exception: pass
for line in open(os.path.join(ROOT, "names.js"), encoding="utf-8"):
    if re.match(r"^[A-Z][^|]*\|[bge]\|", line): known.add(fold(line.split("|")[0]))
filipino_have = {fold(r[0]) for r in culture if r[2] == "Filipino" or "Filipino" in r[9]}

def ready(rows, skip_filipino=False):
    out = []
    for r in rows:
        if skip_filipino and r[2] == "Filipino" and fold(r[0]) in filipino_have: continue
        if fold(r[0]) in known: r = r[:10]
        out.append(r)
    return out

sea = load("sea-names.json")
for r in sea:
    if r[0] == "Sanguanari": r[0] = "Sanguansri"
sea = [r for r in sea if not (r[0] == "Sbong" and r[2] == "Khmer")]
sea = ready(sea, True)
save("sea-names.json", sea)
heb = ready(load("hebrew-extra.json"))
save("hebrew-extra.json", heb)
print("culture", len(culture), "sea", len(sea), sum(len(r) == 11 for r in sea), "claim culture;", "hebrew", len(heb), sum(len(r) == 11 for r in heb), "claim")

# each new name shows its own script: "Written เฉลิม." → native-forms.json, unless the name already has a form in that language
# (run after any rebuild of native-forms.json, which drops these)
nf = load("native-forms.json"); added = 0
for r in sea + heb:
    m = re.search(r"Written ([^.(]+?)[.(]", r[6])
    if not m or r[3] not in ("Thai", "Khmer", "Lao", "Burmese", "Hebrew"): continue
    form, k = m.group(1).split(" or ")[0].split("/")[0].strip(), fold(r[0])
    if any(l == r[3] for _, l in nf.get(k, [])): continue
    nf[k] = nf.get(k, []) + [[form, r[3]]]; added += 1
save("native-forms.json", nf)
print("scripts added", added)
