"""Merge data/sacred/*.tsv (format: docs/sacred-format.md) into data/sacred.json for the page.

Every row is one name form tied to one figure in one text corpus, with a citable passage. The page gets, per name:
the tradition, corpus, book, passage, a link to read it, how close the tie is (a = in the text, r = a related form,
s = a sacred association), what kind of name it is (p personal, e epithet, t title, d divine, w a word), the figure,
the original script and transliteration. Rows for places, tribes and concepts are kept, flagged by the figure's type.
"""
import csv, glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "sacred")
OUT = os.path.join(ROOT, "data", "sacred.json")
STATUS = {"attested": "a", "related": "r", "association": "s"}
ROLE = {"personal": "p", "epithet": "e", "title": "t", "divine": "d", "word": "w"}

rows = []
for path in sorted(glob.glob(os.path.join(SRC, "*.tsv"))):
    if path.endswith("-review.tsv"):
        continue  # low-confidence rows wait for a person
    with open(path, encoding="utf-8") as f:
        rows += [r for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE) if (r.get("name") or "").strip()]

trads, corps, figs, names = [], [], {}, {}
def idx(lst, v):
    if v not in lst: lst.append(v)
    return lst.index(v)

seen = set()
for r in rows:
    name, fid = r["name"].strip(), r["figure_id"].strip()
    status = STATUS.get(r["status"].strip())
    if not status or not fid:
        continue
    key = (name, r["tradition"], r["corpus"], fid, r.get("name_role", ""))
    if key in seen:
        continue
    seen.add(key)
    figs.setdefault(fid, [r["figure"].strip(), r["entity_type"].strip()])
    occ = r.get("occurrences", "").strip()
    e = names.setdefault(name, {"sex": set(), "refs": []})
    if r.get("sex", "").strip() in ("girl", "boy"):
        e["sex"].add(r["sex"].strip())
    e["refs"].append([idx(trads, r["tradition"].strip()), idx(corps, r["corpus"].strip()), r["text"].strip(), r["passage"].strip(), r["url"].strip(),
                      status, ROLE.get(r.get("name_role", "").strip(), "p"), fid, r.get("original", "").strip(), r.get("translit", "").strip(),
                      r.get("relation", "").strip(), int(occ) if occ.isdigit() else None])

ORDER = {"a": 0, "r": 1, "s": 2}
out = {"t": trads, "c": corps, "f": figs, "n": []}
for name, e in sorted(names.items()):
    sex = "e" if len(e["sex"]) == 2 else "g" if "girl" in e["sex"] else "b" if "boy" in e["sex"] else ""
    out["n"].append([name, sex, sorted(e["refs"], key=lambda x: (ORDER[x[5]], -(x[11] or 0)))])

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
by = {}
for _, _, refs in out["n"]:
    for ref in refs:
        by[corps[ref[1]]] = by.get(corps[ref[1]], 0) + 1
print(f"wrote {OUT}: {len(out['n']):,} names, {len(figs):,} figures, {sum(by.values()):,} references")
for c, n in sorted(by.items(), key=lambda kv: -kv[1]):
    print(f"  {c:<24} {n:,}")
