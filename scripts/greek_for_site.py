"""Tidy data/greek-names.json (from build_greek_names.py) into the lines the name card shows. Run after build_greek_names.py.

The card shows one line per ancient layer: "An ancient Greek name: Maia, a daughter of Atlas and Pleione; in Theogony 938; borne by 6 people in
the Lexicon of Greek Personal Names. Written Μαῖα. (Smith's Dictionary; LGPN; Perseus)". From each row it keeps:
  - the first clean phrase of Smith's article (a garbled or cut-off excerpt is dropped, never shown),
  - the first passage it is named in, and the number of real people who bore it (LGPN),
  - the Greek form in the nominative (Ξάνθος, not the genitive Ξάνθους), so the card can write the name in Greek.
Meanings are left out: the matched Wiktionary glosses were often for another word (Maia → "Maia's month"), so names keep the meanings they have.
"""
import json, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "data", "greek-names.json")
rows = json.load(open(P, encoding="utf-8"))

END = {"os": "ος", "ē": "η", "a": "α", "ōn": "ων", "ōr": "ωρ", "ēs": "ης", "is": "ις", "eus": "ευς", "ō": "ω", "ōs": "ως", "as": "ας", "on": "ον"}
def nominative(forms, strict):
    if strict:
        for lat, gr in sorted(END.items(), key=lambda kv: -len(kv[0])):
            if strict.endswith(lat):
                hit = [f for f in forms if f.endswith(gr)]
                if hit:
                    return hit[0]
                break
    return forms[0]

def role(src):
    m = re.search(r"(?:^|\. )((?:A|An|The) [^()]*?) \(Smith's Dictionary\)", src)
    if not m:
        return ""
    r = m.group(1).strip()
    # a description of the person ("A lyric poet", "The famous youth of Abydos"), not a sentence about the sources
    if r.startswith("The ") and not re.match(r"The (son|daughter|wife|mother|father|brother|sister|famous|celebrated|king|queen|nymph|goddess|god|hero|last|first|eldest|youngest)\b", r):
        return ""
    if ";" in r or re.search(r"\b(accounts?|tells us|according to|says that|mentioned)\b", r):
        return ""
    if re.search(r"\d|\b[A-Z]\.\s", r):                  # citations and abbreviations: keep only the clause before them, if it is clean
        r = r.split(",")[0]
        if re.search(r"\d|\b[A-Z]\.\s", r):
            return ""
        r += "."
    if not r.endswith((".", ";")):                        # cut off mid-phrase: keep the first whole clause
        r = r.split(",")[0] if "," in r else ""
    r = r.rstrip(".;, ")
    if not (8 <= len(r) <= 120) or re.search(r"\b(of|the|and|a|an|by|to|in|who|was)$", r):
        return ""
    return r[0].lower() + r[1:]

out = []
for r in rows:
    name, src = r[0], r[6]
    m = re.match(r"Written ([^.]+)\.(?: Strictly ([^.]+)\.)?", src)
    forms = [f.strip() for f in m.group(1).split("/")] if m else []
    greek = nominative(forms, m.group(2)) if forms else ""
    bits = []
    who = role(src)
    if who:
        bits.append(f"{name}, {who}")
    first = re.search(r"\bIn ((?:Theogony|Iliad|Odyssey|Homeric Hymn|Argonautica|Apollodorus|Shield|Works and Days) [\d.]+\d)", src)
    if first:
        bits.append(f"in {first.group(1).strip()}")
    lg = re.search(r"Borne by (\d+) (?:people|person)", src)
    if lg:
        n = int(lg.group(1))
        bits.append(f"borne by {n} {'person' if n == 1 else 'people'} in the Lexicon of Greek Personal Names")
    if not bits:
        continue
    cite = "; ".join(s for s, k in (("Smith's Dictionary", who), ("Perseus", first), ("LGPN", lg)) if k)
    # "Used in ancient Greece", true whatever the name's origin: Esther, Elias and Tomyris were borne in the Greek world without being Greek names
    sentence = "Used in ancient Greece: " + "; ".join(bits) + "." + (f" Written {greek}." if greek else "") + f" ({cite})"
    # Smith's longest article picks the culture, so a famous Greek name can come out "Roman" (Alexander, Perseus, Diogenes): a Greek -os/-es form is Greek
    bare = "".join(c for c in unicodedata.normalize("NFD", greek or "") if unicodedata.category(c) != "Mn")
    latin = re.search(r"(ius|inus|anus|llus|ina|ia)$", name)                 # Aurelius, Marcellinus: Latin names written in Greek letters stay Roman
    culture = "Greek" if r[2] == "Roman" and not latin and re.search(r"(ος|ης|ων|ευς)$", bare) else r[2]
    out.append([name, r[1], culture, r[3], r[4], "", sentence, r[7], "real", r[9] if len(r) > 9 and isinstance(r[9], list) else []])

json.dump(out, open(P, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"{len(out)} names → {P}")
for r in out[:6] + [x for x in out if x[0] in ("Xanthus", "Danae", "Leander", "Hypatia")]:
    print(" ", r[0], "|", r[6])
