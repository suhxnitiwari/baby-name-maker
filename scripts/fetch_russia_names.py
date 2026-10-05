# Downloads the given names that English Wiktionary and Wikidata record for the languages of the peoples of the Russian
# Federation, into raw/ru/. Read by build_russia_cultures.py and build_russia_forms.py.
#
#   Wiktionary (CC BY-SA 4.0): every page in "<Language> given names" and its subcategories ("male given names", "female
#     given names", "unisex given names", "given names from Arabic", "diminutives of male given names" ...), with its
#     wikitext and the categories it was found in: raw/ru/wikt/<Language>.json
#   Wikidata (CC0): items that are a given name (P31 Q202444), female given name (Q11879590), male given name (Q12308941)
#     or unisex given name (Q3409032) whose "language of work or name" (P407) is one of these languages, with their
#     English label and native label (P1705): raw/ru/wikidata-given-names.json
#
# Polite: one request at a time, 50 pages per request, a contact user agent, maxlag.
#
#   python3 scripts/fetch_russia_names.py              (skips what is already downloaded)
#   python3 scripts/fetch_russia_names.py --refresh    (downloads everything again)
import json, os, sys, time, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "raw", "ru")
sys.path.insert(0, HERE)
from fetch_wiktionary_names import api, pages, UA

# Wiktionary's name for each language (its category prefix). Wiktionary splits Mari, Komi, Altai and Nenets into their
# standard languages.
LANGUAGES = """Russian Tatar Bashkir Chuvash Eastern_Mari Western_Mari Udmurt Komi-Zyrian Komi-Permyak Erzya Moksha Chechen Ingush Avar
Dargwa Lezgi Lak Tabasaran Kumyk Nogai Adyghe Kabardian Karachay-Balkar Ossetian Kalmyk Buryat Yakut Tuvan Southern_Altai Northern_Altai
Khakas Shor Tundra_Nenets Forest_Nenets Khanty Mansi Evenki Even Chukchi""".replace("_", "~").split()
LANGUAGES = [l.replace("~", " ") for l in LANGUAGES]
# Wikidata language items → Wiktionary language name (Wikidata splits some languages and dialects differently)
WD_LANG = {"Q7737": "Russian", "Q25285": "Tatar", "Q13389": "Bashkir", "Q33348": "Chuvash", "Q973685": "Eastern Mari", "Q3906614": "Eastern Mari",
           "Q1776032": "Western Mari", "Q13238": "Udmurt", "Q36126": "Komi-Zyrian", "Q34114": "Komi-Zyrian", "Q56318": "Komi-Permyak", "Q29952": "Erzya",
           "Q13343": "Moksha", "Q33350": "Chechen", "Q33509": "Ingush", "Q29561": "Avar", "Q32332": "Dargwa", "Q31746": "Lezgi", "Q36206": "Lak",
           "Q34079": "Tabasaran", "Q36209": "Kumyk", "Q33871": "Nogai", "Q27776": "Adyghe", "Q33522": "Kabardian", "Q33714": "Karachay-Balkar",
           "Q33968": "Ossetian", "Q2585922": "Ossetian", "Q33634": "Kalmyk", "Q33120": "Buryat", "Q16116629": "Buryat", "Q34299": "Yakut", "Q34119": "Tuvan",
           "Q1991779": "Southern Altai", "Q2640863": "Northern Altai", "Q33575": "Khakas", "Q34139": "Shor", "Q36452": "Tundra Nenets", "Q33563": "Khanty",
           "Q33759": "Mansi", "Q30004": "Evenki", "Q29960": "Even", "Q33170": "Chukchi"}

def subcats(cat):
    out, cont = [], {}
    while True:
        d = api(action="query", list="categorymembers", cmtitle="Category:" + cat, cmlimit="500", cmtype="subcat|page", **cont)
        out += [(m["title"], m["ns"]) for m in d.get("query", {}).get("categorymembers", [])]
        if "continue" not in d: return out
        cont = d["continue"]

def tree(lang):
    # every page under "<lang> given names", with the categories it sits in; "renderings of" categories are other
    # languages' spellings of these names and are not walked
    seen, found, todo = set(), {}, [f"{lang} given names"]
    while todo:
        cat = todo.pop()
        if cat in seen: continue
        seen.add(cat)
        for title, ns in subcats(cat):
            if ns == 14:
                sub = title.split(":", 1)[1]
                if sub.startswith(lang + " ") and "given names" in sub and "renderings" not in sub: todo.append(sub)
            elif ns == 0: found.setdefault(title, []).append(cat)
    return found

def wiktionary(refresh):
    os.makedirs(os.path.join(RAW, "wikt"), exist_ok=True)
    for lang in LANGUAGES:
        path = os.path.join(RAW, "wikt", lang.replace(" ", "_") + ".json")
        if os.path.exists(path) and not refresh: continue
        found = tree(lang)
        text = pages(sorted(found)) if found else {}
        json.dump({t: {"cats": sorted(c), "text": text.get(t, "")} for t, c in sorted(found.items())}, open(path, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"  {lang}: {len(found):,} pages", flush=True)

SPARQL = """SELECT ?item ?type ?lang ?en ?native WHERE {
  VALUES ?lang { %s }
  VALUES ?type { wd:Q202444 wd:Q11879590 wd:Q12308941 wd:Q3409032 }
  ?item wdt:P407 ?lang ; wdt:P31 ?type .
  OPTIONAL { ?item rdfs:label ?en . FILTER(LANG(?en) = "en") }
  OPTIONAL { ?item wdt:P1705 ?native . }
}"""

def wikidata(refresh):
    path = os.path.join(RAW, "wikidata-given-names.json")
    if os.path.exists(path) and not refresh: return
    q = SPARQL % " ".join("wd:" + k for k in WD_LANG)
    for attempt in range(6):
        try:
            req = urllib.request.Request("https://query.wikidata.org/sparql", data=urllib.parse.urlencode({"query": q, "format": "json"}).encode(), headers=UA)
            res = json.load(urllib.request.urlopen(req, timeout=120))["results"]["bindings"]
            break
        except Exception as e:
            print("  wikidata retry:", e); time.sleep(10 * (attempt + 1))
    else: raise RuntimeError("Wikidata query kept failing")
    # one row per item and language: [qid, [type qids], Wiktionary language name, English label, [native labels]]
    by = {}
    for b in res:
        qid, typ = b["item"]["value"].rsplit("/", 1)[1], b["type"]["value"].rsplit("/", 1)[1]
        lang = WD_LANG[b["lang"]["value"].rsplit("/", 1)[1]]
        r = by.setdefault((qid, lang), [qid, [], lang, b.get("en", {}).get("value", ""), []])
        if typ not in r[1]: r[1].append(typ)
        n = b.get("native", {}).get("value")
        if n and n not in r[4]: r[4].append(n)
    rows = sorted(by.values(), key=lambda r: (r[2], r[3], r[0]))
    json.dump(rows, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"  Wikidata: {len(rows):,} (item, language) rows", flush=True)

if __name__ == "__main__":
    refresh = "--refresh" in sys.argv
    wiktionary(refresh)
    wikidata(refresh)
