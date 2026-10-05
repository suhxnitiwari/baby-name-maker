# Names of the peoples of the Russian Federation, by culture → data/russia-cultures.json (rows in the format of
# data/culture-names.json: [name, g, culture, language, religions, meaning, story, texts, kind, also]).
#
# Sources (downloaded by fetch_russia_names.py into raw/ru/):
#   Wiktionary (CC BY-SA 4.0): pages in "<Language> given names" and its subcategories, for Russian, Tatar, Bashkir,
#     Chuvash, Mari, Udmurt, Komi, Erzya, Moksha, Chechen, Ingush, Avar, Dargwa, Lezgi, Lak, Tabasaran, Kumyk, Nogai, Adyghe,
#     Kabardian, Karachay-Balkar, Ossetian, Kalmyk, Buryat, Yakut, Tuvan, Altai, Khakas, Shor, Nenets, Khanty, Mansi, Evenki,
#     Even and Chukchi. A Russian entry whose {{given name}} says from=<one of these languages> (Шойгу, from Tuvan) is also
#     a name of that people.
#   Wikidata (CC0): given-name items whose "language of work or name" (P407) is one of these languages.
#
# Where a name is used is never where it comes from. A culture is tagged only when a source says the name belongs to that
# language, and these are left out:
#   - entries whose source says the name came from Russian (a Russian name used by Bashkirs is not a Bashkir name);
#   - Wikidata language tags on an item that Wiktionary lists as a Russian given name (Сергей tagged Yakut, Chechen and
#     Bashkir), unless Wiktionary says the Russian name comes from that language;
#   - names whose sex the source doesn't give.
# A name shared by several peoples gets one row per culture. Religion is filled only where the entry states it
# ({{given name|usage=Muslim}}). The native spelling is kept in the story as "Written <native>.", the Latin form is the name.
#
#   python3 scripts/build_russia_cultures.py
import collections, json, os, re, sys, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "raw", "ru"); OUT = os.path.join(ROOT, "data", "russia-cultures.json")
sys.path.insert(0, HERE)
from build_cultures import section, details, clean
from russian_latin import romanize, strip_stress
from fetch_russia_names import WD_LANG

# Wiktionary language → (culture: one per people, language as shown)
PEOPLE = {
    "Russian": ("Russian", "Russian"), "Tatar": ("Tatar", "Tatar"), "Bashkir": ("Bashkir", "Bashkir"), "Chuvash": ("Chuvash", "Chuvash"),
    "Eastern Mari": ("Mari", "Meadow Mari"), "Western Mari": ("Mari", "Hill Mari"), "Udmurt": ("Udmurt", "Udmurt"),
    "Komi-Zyrian": ("Komi", "Komi-Zyrian"), "Komi-Permyak": ("Komi-Permyak", "Komi-Permyak"), "Erzya": ("Erzya", "Erzya"), "Moksha": ("Moksha", "Moksha"),
    "Chechen": ("Chechen", "Chechen"), "Ingush": ("Ingush", "Ingush"), "Avar": ("Avar", "Avar"), "Dargwa": ("Dargin", "Dargwa"), "Lezgi": ("Lezgin", "Lezgian"),
    "Lak": ("Lak", "Lak"), "Tabasaran": ("Tabasaran", "Tabasaran"), "Kumyk": ("Kumyk", "Kumyk"), "Nogai": ("Nogai", "Nogai"), "Adyghe": ("Adyghe", "Adyghe"),
    "Kabardian": ("Kabardian", "Kabardian"),
    # one language, two peoples (Karachays and Balkars); the sources don't say which, so the name stays with the language's community
    "Karachay-Balkar": ("Karachay-Balkar", "Karachay-Balkar"),
    "Ossetian": ("Ossetian", "Ossetian"), "Kalmyk": ("Kalmyk", "Kalmyk"), "Buryat": ("Buryat", "Buryat"), "Yakut": ("Sakha", "Sakha (Yakut)"),
    "Tuvan": ("Tuvan", "Tuvan"), "Southern Altai": ("Altai", "Southern Altai"), "Northern Altai": ("Altai", "Northern Altai"), "Khakas": ("Khakas", "Khakas"),
    "Shor": ("Shor", "Shor"), "Tundra Nenets": ("Nenets", "Nenets"), "Forest Nenets": ("Nenets", "Forest Nenets"), "Khanty": ("Khanty", "Khanty"),
    "Mansi": ("Mansi", "Mansi"), "Evenki": ("Evenki", "Evenki"), "Even": ("Even", "Even"), "Chukchi": ("Chukchi", "Chukchi"),
}
GENDER_QID = {"Q12308941": "b", "Q11879590": "g", "Q3409032": "e"}
RELIGION = {"Muslim": "Islamic", "Islamic": "Islamic", "Christian": "Christian", "Orthodox": "Christian", "Buddhist": "Buddhist", "Jewish": "Jewish"}

# ── Latin letters for each language's Cyrillic: a Russian base plus each alphabet's own letters ──
BASE = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюя", "a b v g d e yo zh z i y k l m n o p r s t u f kh ts ch sh shch - y - e yu ya".split()))
BASE["ъ"] = BASE["ь"] = ""
EXTRA = {
    "Tatar": {"ә": "ä", "ө": "ö", "ү": "ü", "җ": "j", "ң": "ng", "һ": "h"},
    "Bashkir": {"ә": "ä", "ө": "ö", "ү": "ü", "ғ": "gh", "ҡ": "q", "ң": "ng", "ҙ": "dh", "ҫ": "th", "һ": "h"},
    "Chuvash": {"ӑ": "ă", "ӗ": "ĕ", "ҫ": "ś", "ӳ": "ü"},
    "Eastern Mari": {"ӓ": "ä", "ӧ": "ö", "ӱ": "ü", "ҥ": "ng"}, "Western Mari": {"ӓ": "ä", "ӧ": "ö", "ӱ": "ü", "ҥ": "ng", "ӹ": "ÿ"},
    "Udmurt": {"ӝ": "dzh", "ӟ": "dz", "ӥ": "i", "ӧ": "ö", "ӵ": "ch"}, "Komi-Zyrian": {"і": "i", "ӧ": "ö"}, "Komi-Permyak": {"і": "i", "ӧ": "ö"},
    "Yakut": {"ҕ": "gh", "ҥ": "ng", "ө": "ö", "ү": "ü", "һ": "h"}, "Buryat": {"ө": "ö", "ү": "ü", "һ": "h"},
    "Kalmyk": {"ә": "ä", "җ": "j", "ң": "ng", "ө": "ö", "ү": "ü", "һ": "h"}, "Tuvan": {"ң": "ng", "ө": "ö", "ү": "ü"},
    "Southern Altai": {"ј": "j", "ҥ": "ng", "ӧ": "ö", "ӱ": "ü"}, "Northern Altai": {"ј": "j", "ҥ": "ng", "ӧ": "ö", "ӱ": "ü"},
    "Khakas": {"ғ": "gh", "і": "i", "ң": "ng", "ӧ": "ö", "ӱ": "ü", "ҷ": "ch"}, "Shor": {"ғ": "gh", "ң": "ng", "ӧ": "ö", "ӱ": "ü"},
    "Ossetian": {"ӕ": "æ"}, "Kumyk": {"гъ": "gh", "къ": "q", "нг": "ng", "оь": "ö", "уь": "ü"}, "Nogai": {"нъ": "ng", "оь": "ö", "уь": "ü"},
    "Karachay-Balkar": {"гъ": "gh", "къ": "q", "нг": "ng"}, "Tundra Nenets": {"ӈ": "ng", "ʼ": "", "ˮ": ""}, "Khanty": {"ӈ": "ng", "ӑ": "ă", "ӛ": "ë", "ӧ": "ö", "ӯ": "ū", "ҳ": "h"},
    "Mansi": {"ӈ": "ng", "ā": "ā"}, "Evenki": {"ӈ": "ng"}, "Even": {"ӈ": "ng", "ӫ": "ö", "ӡ": "dz"}, "Chukchi": {"ӄ": "q", "ӈ": "ng", "ԓ": "lh"},
}
PALOCHKA = "ӀӏI1l"   # the Caucasian palochka (marks ejectives); often typed as I, l or 1 inside Cyrillic
LATIN_NAME = re.compile(r"^[A-Za-zÀ-ɏḀ-ỿ'’ -]+$")

def latin(native, lang):
    s = strip_stress(native)
    if LATIN_NAME.match(s): return s
    if lang == "Russian":
        return romanize(s, "bgn_plain")
    m = {**BASE, **EXTRA.get(lang, {})}
    low, out, i = s.lower(), [], 0
    while i < len(low):
        two = low[i:i + 2]
        if two in m and len(two) == 2: out.append(m[two]); i += 2; continue
        c = low[i]
        if c in PALOCHKA and i and re.match(r"[а-яё]", low[i - 1]): i += 1; continue
        if c in m: out.append(m[c])
        elif c in "- ": out.append(c)
        else: return ""
        i += 1
    r = "".join(out)
    r = "-".join(p[:1].upper() + p[1:] for p in r.split("-"))
    return r if LATIN_NAME.match(r) else ""

def gender_of(cats, sec, code):
    gs = set()
    for c in cats:
        if " male given names" in c or "diminutives of male" in c: gs.add("b")
        if "female given names" in c or "diminutives of female" in c: gs.add("g")
        if "unisex given names" in c: gs.add("e")
    if not gs:
        for g in re.findall(r"\{\{given name\|" + re.escape(code) + r"\|(male|female|unisex)", sec): gs.add({"male": "b", "female": "g", "unisex": "e"}[g])
    if not gs: return None
    return "e" if "e" in gs or len(gs) > 1 else gs.pop()

def lang_code(sec):
    m = re.search(r"\{\{given name\|([a-z-]+)\|", sec)
    return m.group(1) if m else ""

def article(w): return "An" if w[:1] in "AEIOU" else "A"

def story(culture, frm, eq, native, extra, source):
    s = f"{article(culture)} {culture} name"
    if frm: s += f" from {frm}"
    if eq: s += f", the {culture} form of {eq}"
    s += "."
    if extra: s += " " + extra
    if native: s += f" Written {native}."
    return s + f" Source: {source}."

def main():
    if not os.path.isdir(os.path.join(RAW, "wikt")):
        sys.exit("raw/ru/wikt is missing: run python3 scripts/fetch_russia_names.py first")
    wikt = {}
    for lang in PEOPLE:
        p = os.path.join(RAW, "wikt", lang.replace(" ", "_") + ".json")
        wikt[lang] = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    russian_names = {strip_stress(t) for t in wikt["Russian"]}
    # Russian names whose entry says they come from one of the peoples' languages: {Cyrillic: {language}}
    russian_from = collections.defaultdict(set)

    rows, seen, stats, dropped = [], {}, collections.Counter(), collections.defaultdict(list)
    def add(name, g, lang, rel, meaning, text, native, source, basket=()):
        basket = list(basket)
        culture, language = PEOPLE[lang]
        # one row per name and culture: the same name from a second source, or written a second way, adds to the first
        k = (name.lower(), culture)
        if k in seen:
            r = rows[seen[k]]
            if native and native not in r[6]:
                r[6] = r[6].replace(" Source:", f" Also written {native}. Source:", 1) if "Written" in r[6] else r[6].replace(" Source:", f" Written {native}. Source:", 1)
            stats[(culture, "duplicate")] += 1; return
        seen[k] = len(rows)
        rows.append([name, g, culture, language, rel, meaning[:80], text, "", "real", basket])
        stats[(culture, source)] += 1

    for lang, pages in wikt.items():
        for title, v in sorted(pages.items()):
            sec = section(v["text"], lang)
            if not sec: stats[(lang, "no section")] += 1; continue
            code = lang_code(sec)
            d = details(sec)
            g = gender_of(v["cats"], sec, code)
            if not g: dropped["sex not given"].append(f"{lang}:{title}"); continue
            frm = d.get("from", "")
            if lang != "Russian" and re.search(r"\bRussian\b", frm):
                dropped["from Russian"].append(f"{lang}:{title}"); continue
            native = strip_stress(title)
            n = latin(native, lang)
            if not n or " " in n: dropped["no Latin form"].append(f"{lang}:{title}"); continue
            usage = re.search(r"\{\{given name\|[^{}]*\|usage=([^|}]+)", sec)
            rel = RELIGION.get(usage.group(1).strip(), "") if usage else ""
            nat = "" if LATIN_NAME.match(native) else native
            eq = d.get("eq", "").split(",")[0].strip()
            add(n, g, lang, rel, d.get("meaning", ""), story(PEOPLE[lang][0], frm if frm.lower() not in (lang.lower(), "") else "", eq if eq.lower() != n.lower() else "", nat, "", "Wiktionary"), nat, "wiktionary",
                # the Slavic basket only for Russian entries that don't name a non-Slavic source (not Аббас, from Arabic)
                ["Slavic"] if lang == "Russian" and (not frm or "Slavic" in frm) else [])
            if lang == "Russian":
                for f in re.split(r"[,<]\s*", frm):
                    f = f.strip()
                    if f in PEOPLE and f != "Russian": russian_from[native].add(f)
    # the peoples a Russian entry names as the source of the name (Шойгу: Russian, from Tuvan)
    for native, langs in sorted(russian_from.items()):
        v = wikt["Russian"].get(native) or next(x for t, x in wikt["Russian"].items() if strip_stress(t) == native)
        sec = section(v["text"], "Russian")
        g = gender_of(v["cats"], sec, "ru")
        for lang in sorted(langs):
            n = latin(native, "Russian")
            add(n, g, lang, "", "", story(PEOPLE[lang][0], "", "", native, f"Wiktionary records it as a Russian given name from {lang}.", "Wiktionary"), native, "wiktionary (Russian entry)")

    wd = json.load(open(os.path.join(RAW, "wikidata-given-names.json"), encoding="utf-8"))
    peoples_items = {r[0] for r in wd if r[2] != "Russian" and r[2] in PEOPLE}
    for qid, types, lang, label, natives in wd:
        if lang not in PEOPLE: continue
        gs = {GENDER_QID[t] for t in types if t in GENDER_QID}
        if not gs: dropped["sex not given"].append(f"wikidata:{lang}:{qid} {label or natives}"); continue
        g = "e" if "e" in gs or len(gs) > 1 else gs.pop()
        cyr = [strip_stress(x) for x in natives if re.search(r"[Ѐ-ӿ]", x)]
        lat = [x for x in natives if LATIN_NAME.match(x)]
        native = cyr[0] if cyr else ""
        if lang != "Russian" and native in russian_names and lang not in russian_from.get(native, ()):
            dropped["Wikidata language tag on a Russian name"].append(f"{lang}:{native}"); continue
        # and the other way: the Russian spelling of a Tatar or Chechen name (Алсу) is not a Russian name, unless
        # Wiktionary lists it as one
        if lang == "Russian" and qid in peoples_items and native not in russian_names:
            dropped["Wikidata Russian tag on another people's name"].append(f"{native or label}"); continue
        # Russian names get the same romanization as the Wiktionary ones; for the others Wikidata's English label is kept
        name = latin(native, lang) if native and lang == "Russian" else label if label and LATIN_NAME.match(label) else (latin(native, lang) if native else "")
        if not name or " " in name: dropped["no Latin form"].append(f"wikidata:{lang}:{qid}"); continue
        written = native + (f" ({', '.join(x for x in lat if x != name)})" if [x for x in lat if x != name] else "") if native else ""
        add(name, g, lang, "", "", story(PEOPLE[lang][0], "", "", written, "", f"Wikidata {qid}"), native, "wikidata")

    rows.sort(key=lambda r: (r[0].lower(), r[2]))
    json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    per = collections.Counter(r[2] for r in rows)
    print(f"{len(rows):,} rows ({len({r[0].lower() for r in rows}):,} names) in {len(per)} cultures → {OUT}")
    for c, n in per.most_common():
        src = {s: v for (cc, s), v in stats.items() if cc == c and s != "duplicate"}
        print(f"  {c:16} {n:5}  {src}")
    for why, xs in dropped.items(): print(f"  left out, {why}: {len(xs)}  e.g. {xs[:8]}")

if __name__ == "__main__":
    main()
