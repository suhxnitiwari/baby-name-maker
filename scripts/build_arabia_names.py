# Pre-Islamic Arabian names → data/arabia-names.json, in the row format of data/culture-names.json:
#   [name, g ('g'|'b'|'e'), culture, language, religions, meaning, story, texts, kind, also]
#
# The source of truth is the hand-checked data/arabia-names.tsv: one row per name borne before 610 CE, with the
# Arabic spelling, the scholarly transliteration, who bore it, the evidence (PERSON in the classical sources, or
# INSCRIPTION), the kind of woman's name (HISTORICAL, BELOVED in a poem's nasib, LITERARY), a source tier
# (1 inscriptions, 2 the poetry itself, 3 later books on pre-Islamic Arabs, 4 later stories, always provisional),
# an ease score for English spelling (1 spelled as English speakers would, 2 easy with a known modern spelling,
# 3 needs explaining) and a confidence. Only ease 1 and 2 reach the site.
#
#   python3 scripts/build_arabia_names.py
import csv, json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "arabia-names.tsv"); OUT = os.path.join(ROOT, "data", "arabia-names.json")

def work(source):
    """The source without its URLs: 'Ibn Saʿd, al-Tabaqat al-Kubra, vol. 8; meaning: Lane'."""
    s = re.sub(r"\s*https?://\S+", "", source)
    return re.sub(r"\s*;\s*;", ";", s).strip(" ;")

def sentence(r):
    who = r["who"]
    if r["century"] and r["century"][0].isdigit():
        when = re.sub(r"(\d+(?:st|nd|rd|th)) c\.", r"\1 century", r["century"])
        if "BCE" not in when: when = when.replace(" CE", "")
    else:
        when = r["century"]
    return f"Used in Arabia before Islam: {who}, {when}. Written {r['arabic']}. ({work(r['source'])})"

rows = []
with open(SRC, newline="") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        if r["ease"] not in ("1", "2"): continue
        lang = "Old Arabic" if r["language"] == "Old Arabic" else r["language"]
        # the meanings in the TSV were noted from Lane's Lexicon without being checked against it, so they stay out of the site until they are
        rows.append([r["name"], r["sex"], "Pre-Islamic Arabian", lang, "", "", sentence(r), "", "real", []])
with open(OUT, "w") as f:
    json.dump(rows, f, ensure_ascii=False, separators=(",", ":"))
print(len(rows), "names →", os.path.relpath(OUT, ROOT))
