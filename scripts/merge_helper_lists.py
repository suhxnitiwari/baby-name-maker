"""Ready data/sea-names.json, data/hebrew-extra.json and data/latin-names.json for the page, and apply data/sea-fixes.json to data/culture-names.json.

- a name the site already knows from another list keeps its culture: its row loses the ease slot (which would claim the culture)
  and only adds its line, script and culture alongside (Em stays English; Khmer Em joins it)
- Filipino rows that restate a name culture-names.json already has are left out
- respelled and dropped names leave culture-names.json (the respelled ones have full rows in sea-names.json)
"""
import json, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indic_check import matches
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
    if f.endswith("-names.json") and f not in ("sea-names.json", "latin-names.json", "famous-names.json", "bollywood-names.json"):
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
# Latin: Greek names Latin only borrowed stay out (Cleopater)
lat = ready([r for r in load("latin-names.json") if r[0] not in ("Cleopater",)])
save("latin-names.json", lat)
print("latin", len(lat), sum(len(r) == 11 for r in lat), "claim")
print("culture", len(culture), "sea", len(sea), sum(len(r) == 11 for r in sea), "claim culture;", "hebrew", len(heb), sum(len(r) == 11 for r in heb), "claim")

# Hindu names (data/hindu-names.json, from build_hindu_names.py): a name other cultures also use (Mira, Adi, Amit) keeps its
# origin and only gains Sanskrit beside it; the rest are Sanskrit or the Indian language they come from
INDIAN = {"Indian", "Hindi", "Sanskrit", "Bengali", "Tamil", "Telugu", "Marathi", "Gujarati", "Punjabi", "Kannada", "Malayali", "Malayalam", "Odia",
          "Nepali", "South Asian", "Sindhi", "Assamese", "Konkani", "Pali", "Sikh", "Rajasthani", "Kashmiri", "Hindu"}
elsewhere = set()
for f in os.listdir(os.path.join(ROOT, "data")):
    if f.endswith("-names.json") and f not in ("hindu-names.json", "famous-names.json", "bollywood-names.json", "city-names.json", "strongs-meanings.json", "bible-places.json"):
        try: elsewhere |= {fold(r[0]) for r in load(f) if isinstance(r, list) and len(r) > 2 and isinstance(r[2], str) and r[2] and r[2] not in INDIAN}
        except Exception: pass
for line in open(os.path.join(ROOT, "names.js"), encoding="utf-8"):
    x = line.split("|")
    if len(x) > 3 and re.match(r"^[A-Z]", x[0]) and x[2] not in INDIAN: elsewhere.add(fold(x[0]))
# …and its Sanskrit meaning stays off that card too: Arabic Rana is not "a king"
hin = [r[:5] + [""] + r[6:10] if fold(r[0]) in elsewhere else r for r in load("hindu-names.json")]
# a row whose Devanagari spells only part of the name (नील for Sunil) took its meaning from that part too: neither is kept
def whole(r):
    m = re.search(r"Written ([^.(,;]+?)[.(,;]", r[6])
    return not m or matches(r[0], m.group(1).split(" or ")[0].split("/")[0].strip())
hin = [r if whole(r) else r[:5] + [""] + [re.sub(r"Written [^.]*\.\s*", "", r[6])] + r[7:] for r in hin]
# the helper's raw "meaning|fact|parts" lines become "meaning; fact"; a bare part-by-part chain is no meaning at all
def tidy(m):
    if "|" in m:
        parts = m.split("|"); fact = parts[1].strip() if len(parts) > 1 else ""
        return parts[0].strip() + (f"; {fact}" if fact and fact != "-" else "")
    return "" if re.search(r"‘[^’]+’ \+ ", m) else m
hin = [r[:5] + [tidy(r[5])] + r[6:] for r in hin]
UNSURE = {"Rana"}   # MW's "a king" is not backed by Wiktionary, which knows Rana only as a Rajput surname: no meaning rather than a guess
hin = [r[:5] + [""] + r[6:] if r[0] in UNSURE else r for r in hin]
save("hindu-names.json", hin)
print("hindu", len(hin), sum(len(r) == 11 for r in hin), "claim")

# each new name shows its own script: "Written เฉลิม." → native-forms.json, unless the name already has a form in that language
# (run after any rebuild of native-forms.json, which drops these)
rng = lambda a, b: (lambda c: a <= ord(c) <= b)
DEV = rng(0x0900, 0x097F)
SCRIPT = {"Sanskrit": DEV, "Hindi": DEV, "Marathi": DEV, "Nepali": DEV, "Bengali": rng(0x0980, 0x09FF), "Punjabi": rng(0x0A00, 0x0A7F),
          "Gujarati": rng(0x0A80, 0x0AFF), "Odia": rng(0x0B00, 0x0B7F), "Tamil": rng(0x0B80, 0x0BFF), "Telugu": rng(0x0C00, 0x0C7F),
          "Kannada": rng(0x0C80, 0x0CFF), "Malayalam": rng(0x0D00, 0x0D7F), "Hebrew": rng(0x0590, 0x05FF), "Thai": rng(0x0E00, 0x0E7F),
          "Lao": rng(0x0E80, 0x0EFF), "Burmese": rng(0x1000, 0x109F), "Khmer": rng(0x1780, 0x17FF)}
nf = load("native-forms.json"); added = 0
for r in sea + heb + hin:
    m = re.search(r"Written ([^.(,;]+?)[.(,;]", r[6])
    if not m or r[3] not in ("Thai", "Khmer", "Lao", "Burmese", "Hebrew", "Sanskrit", "Hindi", "Bengali", "Tamil", "Telugu", "Marathi", "Gujarati", "Punjabi", "Kannada", "Malayalam", "Odia", "Nepali"): continue
    form, k = m.group(1).split(" or ")[0].split("/")[0].strip(), fold(r[0])
    if not SCRIPT.get(r[3], lambda c: True)(form[0]): continue          # Lalita's Bengali ললিতা is not a Sanskrit spelling
    if not matches(r[0], form): continue                                # संधि is sandhi, not Sandhya
    if any(l == r[3] for _, l in nf.get(k, [])): continue
    nf[k] = nf.get(k, []) + [[form, r[3]]]; added += 1
for k, form, lang in (("sandhya", "संध्या", "Sanskrit"), ("rana", "राणा", "Hindi"), ("ganesh", "गणेश", "Sanskrit"), ("sunil", "सुनील", "Hindi")):   # checked by hand
    nf[k] = [[form, lang]] + [f for f in nf.get(k, []) if f[1] != lang and f[0] != "राणी"]
save("native-forms.json", nf)
print("scripts added", added)
