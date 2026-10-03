# Appends hand-written name lines (Name|g|Culture|Language|Religion|meaning|story) to the curated list in names.js,
# skipping names it already has.   python3 scripts/add_curated.py file1.txt file2.txt …
import os, re, sys, unicodedata
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); JS = os.path.join(ROOT, "names.js")
fold = lambda n: unicodedata.normalize("NFD", n).encode("ascii", "ignore").decode().lower()
src = open(JS, encoding="utf-8").read()
end = src.index("\n`;\n", src.index("REAL_RAW"))
have = {fold(l.split("|")[0]) for l in src[:end].split("\n") if l.count("|") == 6}
add, bad = [], 0
for path in sys.argv[1:]:
    for l in open(path, encoding="utf-8"):
        l = l.strip()
        f = l.split("|")
        if len(f) != 7 or f[1] not in "gbe" or not f[1] or not f[0] or " " in f[0] or not f[5]: bad += bool(l); continue
        f[4] = ",".join(r.strip() for r in f[4].split(",") if r.strip())
        if fold(f[0]) in have: continue
        have.add(fold(f[0])); add.append("|".join(x.strip() for x in f))
open(JS, "w", encoding="utf-8").write(src[:end] + "\n" + "\n".join(add) + src[end:])
print(f"added {len(add)} names, skipped {bad} malformed lines")
