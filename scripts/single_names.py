# One name per entry. Spain, Québec, Argentina and Switzerland register a person's full given name
# ("María del Carmen", "Jean-Pierre", "Sonia Viviana") as one name. We split those: each part's people
# are added to that single name (its countries too), and the compound entry is removed.
# Parts that never appear as a name on their own ("Dios", "Cabeza", initials) are dropped: they are
# pieces of devotional names, not first names. Gender always comes from the single name's own records.
#
#   python3 scripts/single_names.py data/names-db.tsv      (rewrites the file in place; safe to run twice)
import re, sys, unicodedata

SPLIT = re.compile(r"[ \-]+")
PARTICLES = {"de", "del", "la", "las", "los", "y", "da", "das", "do", "dos", "di", "du", "van", "von", "der", "e", "el", "dei", "della", "des", "le"}
key = lambda n: unicodedata.normalize("NFC", n).lower()

def single_names(rows):
    """rows: (name, gender, "cc,cc", count) → the same, one name per row, most people first."""
    singles = {key(n): [n, g, set(cc.split(",")), int(c)] for n, g, cc, c in rows if not SPLIT.search(n)}
    for n, g, cc, c in rows:
        if not SPLIT.search(n): continue
        for w in {key(w) for w in SPLIT.split(n)} - PARTICLES:
            s = singles.get(w)
            if s: s[2].update(cc.split(",")); s[3] += int(c)
    out = [(n, g, ",".join(sorted(cc)), c) for n, g, cc, c in singles.values()]
    out.sort(key=lambda r: -r[3])
    return out

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/names-db.tsv"
    rows = [l.rstrip("\n").split("\t") for l in open(path, encoding="utf-8") if l.strip()]
    out = single_names(rows)
    with open(path, "w", encoding="utf-8") as fh:
        for r in out: fh.write(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\n")
    print(f"{len(rows):,} entries → {len(out):,} single names → {path}")
