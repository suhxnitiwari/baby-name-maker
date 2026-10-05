# Pronunciations for the names people actually have: data/pron.json
#   { "maya": ["M AY1 AH0", ...], ... }   ARPAbet phonemes, stress on vowels (1 primary, 2 secondary, 0 none)
# Source: the CMU Pronouncing Dictionary (raw/cmudict.dict, https://github.com/cmusphinx/cmudict, BSD-2-Clause),
# kept only for names in data/names-db.tsv held by 5+ people, plus a short hand-checked list for names the
# dictionary says the English-spelling way (Niamh is NEEV, not NY-uhm). Every other name is sounded out in the
# browser by phonetics.js, with rules for its language.
import json, os, re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# hand-checked: Irish, and a few the dictionary stresses oddly
FIX = {
    "niamh": ["N IY1 V"], "siobhan": ["SH IH0 V AO1 N"], "saoirse": ["S IH1 R SH AH0"], "aoife": ["IY1 F AH0"],
    "caoimhe": ["K IY1 V AH0"], "oisin": ["AH0 SH IY1 N"], "sean": ["SH AO1 N"], "sinead": ["SH IH0 N EY1 D"],
    "roisin": ["R OW0 SH IY1 N"], "aisling": ["AE1 SH L IH0 NG"], "grainne": ["G R AO1 N Y AH0"], "padraig": ["P AO1 R IH0 G"],
    "aiden": ["EY1 D AH0 N"], "aidan": ["EY1 D AH0 N"], "rian": ["R IY1 AH0 N"], "tadhg": ["T AY1 G"],
}

names = {}
for line in open(os.path.join(HERE, "data/names-db.tsv"), encoding="utf-8"):
    n, g, cc, cnt = line.rstrip("\n").split("\t")
    if " " not in n and int(cnt) >= 5:
        names[n.lower()] = int(cnt)

out = {}
for line in open(os.path.join(HERE, "raw/cmudict.dict"), encoding="latin-1"):
    line = line.split("#")[0].strip()
    if not line: continue
    word, *ph = line.split()
    base = re.sub(r"\(\d+\)$", "", word)
    if base in names and base not in FIX:
        out.setdefault(base, []).append(" ".join(ph))
out.update({k: ["!" + p for p in v] for k, v in FIX.items()})               # "!" marks a hand-checked reading
path = os.path.join(HERE, "data/pron.json")
json.dump(out, open(path, "w"), separators=(",", ":"))
print(f"{len(out):,} names with dictionary pronunciations ({sum(len(v) > 1 for v in out.values()):,} with more than one), {os.path.getsize(path) // 1024} KB")
