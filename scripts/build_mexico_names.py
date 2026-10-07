# Pre-colonial Mexican Indigenous names → data/mexico-names.json, in the storied-list row format read by app.js addStoried:
#   [name, g ('g'|'b'|'e'), culture, language, religions, meaning, story, texts, kind, also]
#
# Source of truth: data/mexico-names.tsv, hand-checked row by row against open scholarly sources (Online Nahuatl
# Dictionary, Visual Lexicon of Aztec Hieroglyphs, Codex Mendoza, Mesoweb, Relación de Michoacán, Mixtec codices).
# Each row keeps its people separate (Nahua, Classic Maya, Mixtec, Zapotec, Purépecha), its attested spelling, its
# evidence and its confidence. Only rows of ease 1 and 2 are written; ease-3 names (long compounds, glottal-marked Maya
# names, Mixtec calendar names) stay in the TSV for reference. Rows whose only evidence is a later tradition are left out.
# The TSV column `kind` says what the row is:
#   PERSON      a name borne by real (or, where marked, legendary) people before 1521 or in early-colonial records of them
#   DEITY-NAME  a god's name used as a given name today; never described as borne by a person
#   WORD-NAME   a word used as a given name today, with no person found who bore it before 1521
#
#   python3 scripts/build_mexico_names.py
import csv, json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "mexico-names.tsv"); OUT = os.path.join(ROOT, "data", "mexico-names.json")

def culture(people):
    # "Classic Maya (Palenque)" → "Classic Maya"; Nahua keeps its altepetl: "Nahua (Mexica)"
    return people.split(" (")[0] if people.startswith("Classic Maya") else people

def short_source(src):
    parts = []
    for p in re.split(r";\s*", src):
        p = re.sub(r"https?://\S+", "", p).replace("pointer to ", "").replace("pointer", "").strip(" ()")
        p = re.sub(r"\s*\(citing S\. L\. Cline, (The Book of Tributes)[^)]*\)?", r" / \1", p)
        p = re.sub(r",? '[^']*'", "", p)          # dictionary headword
        p = re.sub(r"\s*\(El Escorial[^)]*\)?", "", p)
        p = re.sub(r"\s+\(\s*", " / ", p).strip(" /,")
        if p and p not in parts: parts.append(p)
    return " / ".join(parts)

rows = []
for r in csv.DictReader(open(SRC, encoding="utf-8"), delimiter="\t"):
    if r["ease"] not in ("1", "2") or r["evidence"] == "LATER-TRADITION": continue
    src = short_source(r["source"]); att = r["attested_form"]; note = r["modern_spelling_note"]
    if r["kind"] == "DEITY-NAME":
        s = f"The name of the {r['people']} goddess {att}, used as a given name today; not recorded as a woman's name before 1521."
    elif r["kind"] == "WORD-NAME":
        s = f"A {r['language']} word ({att}" + (f", {r['meaning']}" if r["meaning"] else "") + "), used as a given name today; no person of this name is recorded before 1521."
        if note: s += f" {note}."
    else:
        who = r["who"].rstrip(".")
        s = f"Used before 1521: {who}" + ("" if att == r["name"] or att in who else f"; written {att}") + "."
        if note: s += f" {note}."
        if r["confidence"] == "provisional": s += " Some details are uncertain."
    s += f" ({src})"
    rows.append([r["name"], r["sex"], culture(r["people"]), r["language"], "", r["meaning"], s, "", "real", []])
json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"{len(rows)} names → {os.path.relpath(OUT, ROOT)}")
