# Latin spellings of Russian given names → data/russia-forms.json, and "romanization_variant" links between them in
# data/relations.json.
#
# For every Russian given name on English Wiktionary (raw/ru/wikt/Russian.json, from fetch_russia_names.py):
#   generated from the Cyrillic, letter by letter (scripts/russian_latin.py): BGN/PCGN (and the same without its marks),
#   ISO 9, scientific, ICAO passport 2013;
#   from Wiktionary (CC BY-SA 4.0): the transliterations the entry lists (xlit=, "common"), the English entries that are
#   renderings of the name ("English renderings of Russian male/female given names": Sergei, Yevgeny, "common"), and the
#   English equivalent the entry names (eq=Alexander, "conventional English"). An eq= that is a different name rather than
#   a spelling of this one (Сергей eq=Sergius) is kept as "English equivalent" and not linked.
# Rows: [cyrillic, [{"latin": ..., "system": ...}, ...]].
#
# relations.json keeps every existing row; this script only adds (and on a rerun replaces) its own rows,
# [latin, "romanization_variant", other latin, "Russian", [cyrillic, cyrillic]], one per pair of plain-letter spellings of
# the same Cyrillic name (Sergey, Sergei, Sergej), skipping pairs already there.
#
#   python3 scripts/build_russia_forms.py
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "raw", "ru"); OUT = os.path.join(ROOT, "data", "russia-forms.json"); REL = os.path.join(ROOT, "data", "relations.json")
sys.path.insert(0, HERE)
from build_cultures import section
from russian_latin import romanize, strip_stress, is_russian_cyrillic, SYSTEMS
from fetch_russia_names import subcats
from fetch_wiktionary_names import pages

PLAIN = re.compile(r"^[A-Za-z]+(?:-[A-Za-z]+)*$")

def renderings():
    # English Wiktionary entries that render a Russian given name in English: {Cyrillic: [English spellings]}
    path = os.path.join(RAW, "wikt", "English_renderings.json")
    if not os.path.exists(path):
        titles = sorted({t for c in ("English renderings of Russian male given names", "English renderings of Russian female given names")
                         for t, ns in subcats(c) if ns == 0})
        json.dump(pages(titles), open(path, "w", encoding="utf-8"), ensure_ascii=False)
    out = {}
    for title, text in json.load(open(path, encoding="utf-8")).items():
        sec = section(text, "English")
        for m in re.finditer(r"\{\{(?:name translit|bor\+?|der\+?|uder)\|en\|ru\|([^{}]*)\}\}", sec):
            cyr = next((strip_stress(a) for a in m.group(1).split("|") if "=" not in a and a.strip()), "")
            if is_russian_cyrillic(cyr): out.setdefault(cyr, []).append(title)
    return out

def skeleton(s):
    # a rough spelling key, only to tell a spelling of the same name (Alexander, Aleksandr) from another name (Sergius)
    s = s.lower().replace("x", "ks").replace("ch", "kh").replace("ph", "f").replace("th", "t").replace("j", "y").replace("w", "v")
    s = re.sub(r"(.)\1", r"\1", s)
    return s

def close(a, b):
    a, b = skeleton(a), skeleton(b)
    # edit distance at most 2
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1): cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1] <= 2

def main():
    names = json.load(open(os.path.join(RAW, "wikt", "Russian.json"), encoding="utf-8"))
    eng = renderings()
    rows = []
    for title in sorted(names, key=strip_stress):
        cyr = strip_stress(title)
        if not is_russian_cyrillic(cyr): continue
        sec = section(names[title]["text"], "Russian")
        forms = []
        def add(latin, system):
            latin = latin.strip()
            if latin and not any(f["latin"] == latin and f["system"] == system for f in forms): forms.append({"latin": latin, "system": system})
        for key in ("bgn", "bgn_plain", "iso9", "scientific", "icao"):
            add(romanize(cyr, key), SYSTEMS.get(key, "BGN/PCGN without marks"))
        bgn = romanize(cyr, "bgn_plain")
        for gn in re.findall(r"\{\{given name\|ru\|[^{}]*\}\}", sec):
            for k, system in (("xlit", "common"), ("eq", None)):
                m = re.search(r"\|" + k + r"=([^|}]+)", gn)
                for v in (m.group(1).split(",") if m else []):
                    v = re.sub(r"\[\[|\]\]|<[^>]*>", "", v).strip()
                    if not re.match(r"^[A-Za-z][A-Za-z' -]*$", v): continue
                    add(v, system or ("conventional English" if close(v, bgn) else "English equivalent"))
        for v in eng.get(cyr, []): add(v, "common")
        rows.append([cyr, forms])
    json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(rows):,} Russian names → {OUT}")

    # relations: plain-letter spellings of one Cyrillic name, every pair once
    rels = json.load(open(REL, encoding="utf-8"))
    kept = [r for r in rels if r[1] != "romanization_variant"]
    have = {(r[0].lower(), r[2].lower(), r[1]) for r in kept}
    added = []
    for cyr, forms in rows:
        spell = list(dict.fromkeys(f["latin"] for f in forms if f["system"] != "English equivalent" and PLAIN.match(f["latin"])))
        for i, a in enumerate(spell):
            for b in spell[i + 1:]:
                if a.lower() == b.lower(): continue
                if (a.lower(), b.lower(), "romanization_variant") in have or (b.lower(), a.lower(), "romanization_variant") in have: continue
                have.add((a.lower(), b.lower(), "romanization_variant"))
                added.append([a, "romanization_variant", b, "Russian", [cyr, cyr]])
    json.dump(kept + added, open(REL, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"relations.json: {len(kept):,} existing rows kept, {len(added):,} romanization_variant rows added")
    return rows, added

if __name__ == "__main__":
    main()
