"""Bible places used as given names (data/bible-place-names.json, from build_hebrew_extra.py) → the line the card shows.

"A place in the Bible: Eden, the perfect garden where God placed Adam and Eve; first in Genesis 2:8. The word means 'pleasure'. (STEPBible; Strong's H5731)"
A place is not a person: the line says so, and it never sets the name's origin, sex or meaning (Selah, Eden and Shiloh were never women).
Meanings come from Strong's dictionaries (raw/strongs, Open Scriptures, CC BY-SA), not Hitchcock (1869), whose guesses ran wild (Carmel "circumcised lamb").
"""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from strongs import meaning
COMMON = {"Village", "Town", "Region", "Another", "The", "A", "An", "River", "City", "Mountain", "Place", "Mount", "Valley", "Land", "Hill"}
out = []
for r in json.load(open(os.path.join(ROOT, "data", "bible-place-names.json"), encoding="utf-8")):
    s = r[6]
    ref = re.search(r"first in ([^.]+?\d+:\d+)", s).group(1)
    body = s.split(" (STEPBible)")[0]
    body = re.sub(r"^A place in the Bible used as a given name: [^.]+?\d+:\d+\.\s*", "", body)
    body = re.sub(r"^Written .*?(?:\(Wiktionary\)\.|\.)\s*(?:no Hebrew form in the sources\.\s*)?", "", body)
    person = "Also the name of a person" in body
    desc = re.sub(r"\.?\s*Also the name of a person in the Bible.*$", "", body).strip().rstrip(".")
    k, m, _ = meaning(r[0])
    line = f"A place in the Bible: {r[0]}" + (f", {desc[0].lower() + desc[1:] if desc.split()[0] in COMMON else desc}" if desc else "") + f"; first in {ref}."
    if m: line += f" The word means '{m}'."
    if person: line += " Also a person's name in the Bible."
    line += " (STEPBible" + (f"; Strong's {k}" if k else "") + ")"
    out.append([r[0], "", "", "", "", "", line, "", "real", []])
json.dump(out, open(os.path.join(ROOT, "data", "bible-places.json"), "w", encoding="utf-8"), ensure_ascii=False)
print(len(out))
for x in out:
    if x[0] in ("Eden", "Carmel", "Shiloh", "Zion", "Bethany", "Calvary", "Sharon", "Jordan", "Salem", "Beulah"): print(" ", x[6])
