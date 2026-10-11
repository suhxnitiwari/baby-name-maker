"""Bible names the site shows without a meaning → data/strongs-meanings.json, the meaning Strong's dictionaries give.

Only for names cited to the Tanakh, Old Testament or New Testament (data/sacred.json) that no other list gives a meaning:
it never replaces a meaning already sourced. Gentilics (Abiezrite, "a descendant of Arod") are not given names and are skipped.
"""
import sys, os, json, re, glob, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from strongs import meaning
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fold = lambda s: "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")
s = json.load(open(os.path.join(ROOT, "data", "sacred.json"), encoding="utf-8"))
bible = {i for i, c in enumerate(s["c"]) if c in ("Tanakh", "Old Testament", "New Testament")}
people = {}
for n, sex, rows in s["n"]:
    if sex and any(r[1] in bible for r in rows): people.setdefault(n, sex)
have = set()
for l in open(os.path.join(ROOT, "names.js"), encoding="utf-8"):
    x = l.split("|")
    if len(x) > 5 and x[5].strip(): have.add(fold(x[0]))
for f in glob.glob(os.path.join(ROOT, "data", "*.json")):
    if f.endswith("strongs-meanings.json"): continue
    try:
        for r in json.load(open(f, encoding="utf-8")):
            if isinstance(r, list) and len(r) > 5 and isinstance(r[5], str) and r[5]: have.add(fold(r[0]))
    except Exception: pass
out = []
for n, sex in sorted(people.items()):
    if fold(n) in have or not re.match(r"^[A-Z][a-z]+$", n) or re.search(r"(ite|ites)$", n): continue
    k, m, _ = meaning(n)
    if not m or re.search(r"\b(descendant|inhabitant|patronymic|patrial)\b|^an? [A-Z]", m): continue
    lang = "Greek" if k.startswith("G") else "Hebrew"
    out.append([n, sex, lang, lang, "Christian" if k.startswith("G") else "Jewish,Christian", m, f"Meaning '{m}' (Strong's {k}).", "", "real", []])
json.dump(out, open(os.path.join(ROOT, "data", "strongs-meanings.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(len(out), "meanings")
