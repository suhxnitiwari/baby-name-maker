# Names of Azerbaijan, from the Ministry of Justice's official open dataset ("Azərbaycan adları", opendata.az,
# https://exidmet.justice.gov.az:7076/Name/json/getNames): every given name with its gender, origin and meaning.
# Writes data/az-names.json in the culture-row format.
#
# Used in a country is not the same as from that culture: a name's culture is its ORIGIN as the ministry records it
# (Arabic, Persian, Azerbaijani…); being on Azerbaijan's list is said in the story. Meanings stay in Azerbaijani,
# quoted exactly, rather than machine-translated.
#
#   curl -k -o raw/az-names.json https://exidmet.justice.gov.az:7076/Name/json/getNames
#   python3 scripts/build_azerbaijan.py
import json, os, re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = json.load(open(os.path.join(HERE, "raw/az-names.json"), encoding="utf-8"))

ORIGIN = [("azərbaycan", "Azerbaijani"), ("türk", "Turkish"), ("ərəb", "Arab"), ("fars", "Persian"), ("yunan", "Greek"), ("latın", "Latin"),
          ("rus", "Russian"), ("yəhudi", "Hebrew"), ("qədim yəhudi", "Hebrew"), ("monqol", "Mongolian"), ("gürcü", "Georgian"), ("hind", "Indian"),
          ("alman", "German"), ("fransız", "French"), ("ingilis", "English"), ("italyan", "Italian"), ("ispan", "Spanish"), ("slavyan", "Slavic")]
out, seen = [], set()
for r in rows:
    text = (r.get("meaningOfName") or "").strip()
    if text.lower().startswith("familiya") or "(a)" in r["personName"]:          # surnames aren't given names
        continue
    g = {1: "b", 2: "g"}.get(r.get("genderId"), "e")
    # the origin the description names first is the name's own ("ərəb mənşəli… passed into Azerbaijani" is Arabic)
    hits = sorted((m.start(), en) for az, en in ORIGIN for m in re.finditer(rf"\b{az}\s+mənşəli", text.lower()))
    origins = list(dict.fromkeys(en for _, en in hits))
    origin = origins[0] if origins else "Azerbaijani"
    forms = [f.strip() for f in r["personName"].split("//") if f.strip()]
    for n in forms:
        if not re.fullmatch(r"[A-Za-zÀ-žƏəÇçĞğİıÖöŞşÜüẞ' -]+", n) or n.lower() in seen:
            continue
        seen.add(n.lower())
        story = (f"On Azerbaijan's official list of names (Ministry of Justice), of {origin} origin. "
                 + (f"Another spelling: {', '.join(f for f in forms if f != n)}. " if len(forms) > 1 else "")
                 + f"The ministry's description, in Azerbaijani: “{text[:280]}{'…' if len(text) > 280 else ''}”")
        out.append([n, g, origin, "Azerbaijani", "", "", story, "", "real", [c for c in dict.fromkeys(["Azerbaijani", *origins[1:]]) if c != origin]])

path = os.path.join(HERE, "data/az-names.json")
json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
by = {}
for row in out: by[row[2]] = by.get(row[2], 0) + 1
print(len(out), "given names", dict(sorted(by.items(), key=lambda kv: -kv[1])), os.path.getsize(path) // 1024, "KB")
