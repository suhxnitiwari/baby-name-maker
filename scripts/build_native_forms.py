"""Every original-script spelling our sources know for a name → data/native-forms.json.

The card shows a name in its own script (Suhani सुहानी, Hana هناء · 花 · 하나). Those spellings are scattered across sources:
the culture lists ("Written सुहानी."), Wiktionary etymologies ("From Arabic هَنَاء"), the Japanese list (kanji), the sacred texts
(the original form), Wiktionary relations (the native pair), and official lists that print the native form (Cyprus, Hungary's
minority names). This gathers them per name, one form per language, with the language named. Nothing is transliterated here:
only forms a source actually prints.
Output: { folded latin name: [[native, language], ...] } with the name's own language first when known.
"""
import csv, json, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda f: os.path.join(ROOT, "data", f)
def fold(s):
    s = unicodedata.normalize("NFD", s.lower())
    return re.sub(r"[\s-]", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))
LATIN = re.compile(r"^[\sA-Za-zÀ-ɏḀ-ỿ'’.\-]+$")
native_ok = lambda t: t and not LATIN.match(t) and len(t) <= 24 and not re.search(r"[\d()=+?]", t)

out = {}
def add(name, form, lang, first=False):
    form = (form or "").strip().strip(".,;:“”\"'")
    if not name or not native_ok(form) or not lang:
        return
    lst = out.setdefault(fold(name), [])
    if not any(l == lang or f == form for f, l in lst):
        lst.insert(0, [form, lang]) if first else lst.append([form, lang])

# each name's own Wiktionary etymology comes first: it says where the name is from (Omar ← Arabic عُمَر)
if os.path.exists(D("native-ety.json")):
    for k, fs in json.load(open(D("native-ety.json"), encoding="utf-8")).items():
        for f, l in reversed(fs):
            if l not in ("Chinese", "Japanese", "Korean"): add(k, f, l, first=True)   # Wiktionary's characters for "Wei" are the surname 魏; the name list has 伟

# culture lists: "A Hindi name from Sanskrit. Written सुहानी."
for f in ["culture-names.json", "caucasus-balkan-names.json", "also-cultures.json", "medieval-names.json", "az-names.json", "russia-cultures.json", "bible-extra.json", "scripture-names.json"]:
    if not os.path.exists(D(f)):
        continue
    for r in json.load(open(D(f), encoding="utf-8")):
        name, lang, src = r[0], r[3] or r[2], r[6] or ""
        m = re.search(r"Written ([^\s.,(]+(?: [^\s.,(]+)?)", src)
        if m: add(name, m.group(1), lang)
        m = re.search(r"\(Hebrew ([^;)]+)", src)
        if m: add(name, m.group(1), "Hebrew")

# the hand-written names (names.js): "Written सुहानी, the feminine of …"
src = open(os.path.join(ROOT, "names.js"), encoding="utf-8").read()
for line in src[src.index("REAL_RAW = `") + 12: src.index("`;", src.index("REAL_RAW = `"))].strip().split("\n"):
    f = line.split("|")
    if len(f) >= 7:
        m = re.search(r"Written ([^\s.,(]+)", f[6])
        if m: add(f[0], m.group(1), f[3] or f[2])

# Japanese: the usual kanji
ea = json.load(open(D("east-asian-names.json"), encoding="utf-8"))
for n, g, kanji, *_ in ea.get("ja", []):
    if kanji: add(n, kanji.split("・")[0], "Japanese")
for key, lang in (("ko", "Korean"), ("zh", "Chinese")):
    for row in ea.get(key, []):
        if len(row) > 2 and isinstance(row[2], str): add(row[0], row[2], lang)

# Wiktionary etymologies: "From Arabic هَنَاء (hanāʔ)" — the first native word after a language name
mean = json.load(open(D("meanings.json"), encoding="utf-8"))
for k, v in mean.items():
    ety = v.get("ety") or ""
    m = re.search(r"\b(?:from|of|form of)\s+(?:the\s+)?(?:Classical |Modern |Biblical |Ancient |Old |Middle )?([A-Z][a-z]+(?: [A-Z][a-z]+)?)\s+([^\sA-Za-z(]{2,}[^\s,;.(]*)", ety)
    if m: add(k, m.group(2), m.group(1))

# Wiktionary relations: [name, relation, related, language, [native, native_related]]
for row in json.load(open(D("relations.json"), encoding="utf-8")):
    if len(row) > 4 and row[4]:
        add(row[0], row[4][0], row[3]); add(row[2], row[4][1], row[3])

# sacred texts: the form in the text's own script
if os.path.exists(D("sacred.json")):
    sac = json.load(open(D("sacred.json"), encoding="utf-8"))
    LANG = {"Tanakh": "Hebrew", "Old Testament": "Hebrew", "Mishnah": "Hebrew", "Talmud": "Hebrew", "New Testament": "Greek", "Qur'an": "Arabic",
            "Guru Granth Sahib": "Punjabi"}
    for name, _, refs in sac["n"]:
        for ref in refs:
            corpus = sac["c"][ref[1]]
            add(name, ref[8], LANG.get(corpus, "Sanskrit" if sac["t"][ref[0]] in ("Hindu", "Jain") else "Pali" if corpus == "Pali Canon" else "Sanskrit"))

# official lists that print the native form (Cyprus Greek, Hungary's minority names)
NL = {"cy": "Greek", "hu-minority-armenian": "Armenian", "hu-minority-bulgarian": "Bulgarian", "hu-minority-greek": "Greek", "hu-minority-serbian": "Serbian",
      "hu-minority-ukrainian": "Ukrainian", "hu-minority-rusyn": "Rusyn"}
if os.path.exists(D("name-lists.tsv")):
    for r in csv.DictReader(open(D("name-lists.tsv"), encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
        lang = next((v for k, v in NL.items() if r["list"].startswith(k)), None)
        if lang and r.get("native") and r["status"] != "rejected": add(r["name"], r["native"].title() if lang == "Greek" else r["native"], lang)

json.dump(out, open(D("native-forms.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"wrote native-forms.json: {len(out):,} names, {sum(map(len, out.values())):,} forms")
for k in ["suhani", "hana", "muhammad", "aishwarya", "maryam", "sofia", "haruto", "giorgos"]:
    print(" ", k, out.get(k))
