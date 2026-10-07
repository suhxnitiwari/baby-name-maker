# Early Armenian names → data/armenia-names.json, in the row format of data/culture-names.json:
#   [name, g ('g'|'b'|'e'), culture, language, religions, meaning, story, texts, kind, also]
#
# The source of truth is the hand-checked data/armenia-names.tsv: one row per name borne in Armenia before the Arab
# conquest (c. 640 CE), pagan or early Christian, with the Armenian spelling (classical orthography), the scholarly
# transliteration, who bore it and where that is written, and:
#   kind        NATIVE (Armenian or legendary-Armenian), IRANIAN-ORIGIN (Iranian/Parthian names borne by Armenians),
#               DEITY (a pre-Christian god's name), CHRISTIAN-IMPORT (biblical/Greek/Syriac/Latin names of the early
#               Church), OTHER-IMPORT (other foreign names: Greek Erato, Syriac Shamiram, Hittite Mushegh),
#               UNCERTAIN (origin unknown or disputed in the sources)
#   tier        1 coins, 2 Greek/Roman authors, 3 early Armenian historians (Movses Khorenatsi's legendary figures are
#               marked provisional), 4 later tradition
#   ease        1 usable as written in English, 2 easy in the stated modern spelling, 3 hard; only 1 and 2 reach the site
#   meaning     only when a cited source gives it (Wiktionary, Hübschmann); blank otherwise
#
# Sources are open: Robert Bedrosian's translations of Agathangelos, Pʿawstos Buzand, Movses Khorenatsi, Ghazar
# Parpetsi and Sebeos (archive.org), LacusCurtius for Strabo, Plutarch, Tacitus and Ammianus, Hübschmann's
# Armenische Grammatik I (1897, archive.org) and Wiktionary.
#
#   python3 scripts/build_armenia_names.py
import csv, json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "armenia-names.tsv"); OUT = os.path.join(ROOT, "data", "armenia-names.json")

# deities whose names are given names today (Wiktionary lists them as Armenian given names)
GIVEN_TODAY = {"Anahit", "Astghik", "Nane", "Vahagn", "Aramazd"}
GODDESS = {"Anahit", "Astghik", "Nane"}


def work(source):
    """Where the bearer is written, without URLs, translators, or the etymology and meaning references."""
    parts = []
    for p in source.split(";"):
        p = p.strip()
        if not p or re.match(r"(origin|Meaning|meaning|biblical|Greek form|the cave name|origin and later use)\b", p): continue
        if p.startswith(("Wiktionary", "Hübschmann")): continue
        p = re.sub(r"\s*\((?:Bedrosian[^)]*|https?://[^)]*|[^)]*https?://[^)]*)\)", "", p)
        p = re.sub(r"\s*https?://\S+", "", p).strip()
        if p: parts.append(p)
    return "; ".join(parts)


def language(r):
    o, k = r["origin"], r["kind"]
    if k in ("NATIVE", "UNCERTAIN") or "+" in o or o.startswith(("unknown", "uncertain", "Armenian")): return "Armenian"
    return re.split(r" \(|,| per ", o)[0].strip()


def origin_phrase(r):
    k, lang = r["kind"], language(r)
    if k == "NATIVE": return "an Armenian name"
    if k == "UNCERTAIN": return "of uncertain origin"
    if "+" in r["origin"]: return "formed from " + re.sub(r"\s*\([^)]*\)", "", r["origin"])
    if k == "CHRISTIAN-IMPORT": return f"from {lang}"
    article = "an" if lang[:1] in "AEIOU" else "a"
    return f"{article} {lang} name"


def sentence(r):
    n, arm, src = r["name"], r["armenian"], work(r["evidence_source"])
    if r["kind"] == "DEITY":
        who = "goddess" if n in GODDESS else "god"
        tail = ", used as a given name today" if n in GIVEN_TODAY else (", also an early Armenian man's name" if n == "Mihr" else "")
        return f"The name of the Armenian {who} {n}{tail}. Written {arm}. ({src})"
    return f"Used in early Armenia: {r['who']}; {origin_phrase(r)}. Written {arm}. ({src})"


rows = []
with open(SRC, newline="") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        if r["ease"] not in ("1", "2"): continue
        rows.append([r["name"], r["sex"], "Armenian", language(r), "", r["meaning"], sentence(r), "", "real", []])
with open(OUT, "w") as f:
    json.dump(rows, f, ensure_ascii=False, separators=(",", ":"))
print(len(rows), "names →", os.path.relpath(OUT, ROOT))
