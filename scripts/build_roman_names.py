# Ancient Roman names: data/roman-names.tsv → data/roman-names.json, in the row format of data/culture-names.json:
#   [name, g ('g'|'b'|'e'), culture, language, religions, meaning, story, texts, kind, also]
#
# data/roman-names.tsv is hand-curated. Every row is a person who bore the name in antiquity:
#   INSCRIPTION      an epitaph or dedication in the Epigraphic Database Heidelberg (EDH, CC BY-SA 4.0,
#                    https://edh.ub.uni-heidelberg.de/data/download, edh_data_pers.csv + edh_data_text.csv);
#                    attest_count = people of that sex in EDH bearing the name as praenomen (abbreviations
#                    counted: L. = Lucius), nomen or cognomen, leaving out emperors and their family (EDH status 0)
#   TABLET           Vindolanda tablets (Roman Inscriptions of Britain / Vindolanda Tablets Online)
#   LITERARY-PERSON  a real person in an ancient author (Perseus, CC BY-SA; LacusCurtius)
# Sex is the sex EDH (or the text) gives the bearer. Meaning is the Lewis & Short gloss of the Latin word behind a
# cognomen; family names (nomina) are left without one.
# ease: 1 usable as written, 2 usable through a real descendant (Aemilia → Emilia), 3 hard. Only ease 1–2 and
# confidence high/medium go to the site.
#
#   python3 scripts/build_roman_names.py
import csv, json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "roman-names.tsv"); OUT = os.path.join(ROOT, "data", "roman-names.json")

def short(source):  # "CIL VI 31846 (EDH HD000144) https://…" → "CIL VI 31846"
    return re.split(r" \(EDH| https?://|;", source)[0].strip()

rows = []
for r in csv.DictReader(open(SRC, encoding="utf-8"), delimiter="\t"):
    if r["ease"] not in ("1", "2") or r["confidence"] not in ("high", "medium"): continue
    who, ref = r["who"], short(r["source"])
    if r["ease"] == "2":
        story = f"The modern form of the ancient Roman {r['latin']}: {who}. ({ref})"
    elif r["latin"] != r["name"]:
        story = f"An ancient Roman name, written {r['latin']} in Latin: {who}. ({ref})"
    else:
        story = f"An ancient Roman name: {who}. ({ref})"
    # the meanings in the TSV are Lewis & Short glosses written from memory, not looked up one by one, so they stay off the site until checked
    rows.append([r["name"], r["sex"], "Ancient Roman", "Latin", "", "", story, "", "real", []])
json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"{len(rows)} names → {os.path.relpath(OUT, ROOT)}")
