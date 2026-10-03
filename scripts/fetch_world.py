# Downloads every official first-name dataset we can reach into raw/ (not committed).
# Each source: country code, a file name, and either a URL or a CKAN portal query that expands to many files.
# Run: python3 scripts/fetch_world.py            (skips files already downloaded)
#      python3 scripts/fetch_world.py --list     (just print what would be fetched)
import json, os, re, sys, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(os.path.dirname(HERE), "raw")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126 Safari/537.36"}

def get(url, timeout=120):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()

# ── single files ──
FILES = [
    # Poland: PESEL register, everyone ever registered (living and deceased), first and second given names
    ("pl", "pl-m-1.xlsx", "https://api.dane.gov.pl/resources/1159637,lista-imion-meskich-w-rejestrze-pesel-stan-na-20012026-imie-pierwsze/file"),
    ("pl", "pl-f-1.xlsx", "https://api.dane.gov.pl/resources/1159639,lista-imion-zenskich-w-rejestrze-pesel-stan-na-20012026-imie-pierwsze/file"),
    ("pl", "pl-m-2.xlsx", "https://api.dane.gov.pl/resources/1159889,lista-imion-meskich-w-rejestrze-pesel-stan-na-20012026-imie-drugie/file"),
    ("pl", "pl-f-2.xlsx", "https://api.dane.gov.pl/resources/1159892,lista-imion-zenskich-w-rejestrze-pesel-stan-na-20012026-imie-drugie/file"),
    # Brazil: IBGE Census 2010 name frequencies (compiled from the IBGE names API by Brasil.io)
    ("br", "br-nomes.csv.gz", "https://data.brasil.io/dataset/genero-nomes/nomes.csv.gz"),
    # Israel: Central Bureau of Statistics, names given to 5+ babies a year, 1948–2024 (tidied by the babynamesIL package)
    ("il", "il.csv", "https://raw.githubusercontent.com/aviezerl/babynamesIL/main/data-raw/babynamesIL.csv"),
    ("il", "il-other.csv", "https://raw.githubusercontent.com/aviezerl/babynamesIL/main/data-raw/babynamesIL_other.csv"),
    # Chile: Servicio de Registro Civil e Identificación, first names registered 1920–2021 (via the guaguas package)
    ("cl", "cl.csv", "https://raw.githubusercontent.com/rivaquiroga/guaguas/main/data-raw/1920-2021.csv"),
    # Northern Ireland: NISRA, every first forename registered since 1997
    ("ni", "ni-m.csv", "https://admin.opendatani.gov.uk/dataset/9ebaf276-f4d5-41e9-bf22-b7ccab8cf85e/resource/38838243-d047-4af7-87a0-bd1109e10b45/download/boysnames.csv"),
    ("ni", "ni-f.csv", "https://admin.opendatani.gov.uk/dataset/9ebaf276-f4d5-41e9-bf22-b7ccab8cf85e/resource/c5fc1673-fa62-45dd-b2e8-90d68258dab9/download/girlsnames.csv"),
    # British Columbia: every name given 5+ times a year, past 100 years
    ("bc", "bc-m.csv", "https://www2.gov.bc.ca/assets/gov/birth-adoption-death-marriage-and-divorce/statistics-reports/bc-popular-boys-names.csv"),
    ("bc", "bc-f.csv", "https://www2.gov.bc.ca/assets/gov/birth-adoption-death-marriage-and-divorce/statistics-reports/bc-popular-girls-names.csv"),
    # Alberta: frequency of every baby name, 1980–2025
    ("ab", "ab-1980.xlsx", "https://open.alberta.ca/dataset/11245675-b047-49fc-8bd1-cc2ce8314a6d/resource/e8aac308-c754-484c-b446-0c57ed0e8d37/download/baby-names-frequency_1980_2020.xlsx"),
    ("ab", "ab-2021.xlsx", "https://open.alberta.ca/dataset/11245675-b047-49fc-8bd1-cc2ce8314a6d/resource/754e4f4b-7324-4a65-908b-20da73661331/download/baby-names-frequency_2025.xlsx"),
    # Ontario: first names from births registered 1913–2023
    ("on", "on-f.csv", "https://data.ontario.ca/dataset/4d339626-98f9-49fe-aede-d64f03fa914f/resource/acc72e92-3100-4a04-8f5f-4fad9cd77cc5/download/baby_names_-_female_.csv"),
    ("on", "on-m.csv", "https://data.ontario.ca/dataset/eb4c585c-6ada-4de7-8ff1-e876fb1a6b0b/resource/5d8b8ece-fa01-43c5-955b-4b642b28c559/download/baby_names_-_male.csv"),
    # Zürich: names of the whole resident population, newborns, and newborns' second names
    ("zh", "zh-pop.csv", "https://data.stadt-zuerich.ch/dataset/bev_bestand_vornamen_jahrgang_geschlecht_od3701/download/BEV370OD3701.csv"),
    ("zh", "zh-baby.csv", "https://data.stadt-zuerich.ch/dataset/bev_vornamen_baby_od3700/download/BEV370OD3700.csv"),
    ("zh", "zh-baby2.csv", "https://data.stadt-zuerich.ch/dataset/bev_zweitevornamen_baby_od3702/download/BEV370OD3702.csv"),
    # Austria: Statistik Austria, first names of every newborn since 1984 (all of Austria; rarer than 4 a year: national count only)
    ("at", "at.csv", "https://data.statistik.gv.at/data/OGDEXT_VORNAMEN_1.csv"),
    # Portugal: Ministry of Justice (IRN), names registered
    ("pt", "pt-f.csv", "https://dados.justica.gov.pt/dataset/ef89faf2-c327-4e4b-bb33-fbfca8e4c8c0/resource/e52dce08-035a-4eb5-bd2a-224f8f11e3a1/download/nomesfeminino.csv"),
    ("pt", "pt-m.csv", "https://dados.justica.gov.pt/dataset/825b6dc1-2bcd-4ccb-a6d6-98bb8c8a4781/resource/65175021-c8ca-4618-a04e-595c34ba15f6/download/nomesmasculino.csv"),
    # Luxembourg: national register, most-given first names
    ("lu", "lu.csv", "https://download.data.public.lu/resources/prenoms-les-plus-donnes-au-luxembourg/20201014-124908/rnrpp-prenoms-les-plus-utilises-2020.csv"),
    # Israel: Wikidata given names with Hebrew labels (CC0), to turn Hebrew-script names into Latin spellings (hebrew_names.py)
    *[("israel", f"wd-he-{k}.tsv", "https://query.wikidata.org/sparql?query=" + urllib.parse.quote(
        f'SELECT ?t ?he ?en WHERE {{ VALUES ?t {{ wd:Q202444 wd:Q11879590 wd:Q3409032 }} ?i wdt:P31 ?t . ?i {p} ?he . FILTER(lang(?he)="he") ?i rdfs:label ?en . FILTER(lang(?en)="en") }}')
        + "&format=tsv") for k, p in (("native", "wdt:P1705"), ("label", "rdfs:label"), ("alias", "skos:altLabel"))],
    # ── Japanese, Korean, Chinese (read by build_east_asian.py) ──
    ("east-asia", "JMnedict.xml.gz", "http://ftp.edrdg.org/pub/Nihongo/JMnedict.xml.gz"),          # EDRDG, CC BY-SA 4.0
    ("east-asia", "kanjidic2.xml.gz", "http://www.edrdg.org/kanjidic/kanjidic2.xml.gz"),           # EDRDG, CC BY-SA 4.0
    ("east-asia", "cedict_1_0_ts_utf-8_mdbg.txt.gz", "https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz"),  # MDBG, CC BY-SA 4.0
    # ── sacred texts (read by build_scriptures.py) ──
    # Bible: every person named (STEPBible TIPNR, Tyndale House, CC BY 4.0) and name meanings (Hitchcock, 1869, public domain)
    ("bible", "tipnr.txt", "https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/Proper%20Nouns/TIPNR%20-%20Translators%20Individualised%20Proper%20Names%20with%20all%20References%20-%20STEPBible.org%20CC%20BY.txt"),
    ("bible", "hitchcock.txt", "https://ccel.org/ccel/h/hitchcock/bible_names/cache/bible_names.txt"),
    # Hindu texts: Cologne Digital Sanskrit Dictionaries (CC BY-NC-SA 3.0)
    *[("hindu", f"skt-{d}.txt", f"https://raw.githubusercontent.com/sanskrit-lexicon/csl-orig/master/v02/{d}/{d}.txt") for d in ("inm", "pe", "pui", "vei", "mci")],
    ("hindu", "gita-verse.json", "https://raw.githubusercontent.com/gita/gita/main/data/verse.json"),
    # Quran: Quranic Arabic Corpus morphology (Kais Dukes, GPL; text by Tanzil)
    ("quran", "quran-morph.txt", "https://raw.githubusercontent.com/cltk/arabic_morphology_quranic-corpus/master/quranic-corpus-morphology-0.4.txt"),
]

# ── whole CKAN datasets (every CSV / XLSX / ZIP in them) ──
CKAN = [
    ("au", "https://data.sa.gov.au/data", ["popular-baby-names"]),
    ("au", "https://data.gov.au/data", ["nsw-popular-baby-names-from-1952", "popular-baby-names1", "top-100-baby-names", "top-baby-names-in-tasmania", "top-baby-names-in-tasmania-in-2016"]),
]
# ── CKAN searches (every matching dataset) ──
SEARCH = [
    ("de", "https://www.govdata.de/ckan", "vornamen", lambda p: "vornam" in (p["name"] + p["title"]).lower()),
]

def expand():
    out = list(FILES)
    def take(cc, base, p):
        for r in p.get("resources", []):
            u = r.get("url") or ""
            fmt = (r.get("format") or u.rsplit(".", 1)[-1]).lower()
            if not any(x in fmt for x in ("csv", "xls", "zip", "json")) or "api" in fmt: continue
            ext = ".zip" if "zip" in fmt else ".xlsx" if "xls" in fmt else ".json" if "json" in fmt else ".csv"
            out.append((cc, f"{cc}-{p['name'][:50]}-{r['id'][:8]}{ext}", u))
    for cc, base, ids in CKAN:
        for i in ids:
            try: take(cc, base, json.loads(get(f"{base}/api/3/action/package_show?id={i}"))["result"])
            except Exception as e: print("  ! ckan", i, e)
    for cc, base, q, keep in SEARCH:
        start = 0
        while True:
            res = json.loads(get(f"{base}/api/3/action/package_search?q={urllib.parse.quote(q)}&rows=200&start={start}"))["result"]
            for p in res["results"]:
                if keep(p): take(cc, base, p)
            start += 200
            if start >= res["count"]: break
    return out

def norway():
    # Statistics Norway: everyone's first names (10501) and newborns' names since 1880 (10467), all names, all years
    for t in ("10501", "10467"):
        path = os.path.join(RAW, f"no-{t}.json")
        if os.path.exists(path): continue
        meta = json.loads(get(f"https://data.ssb.no/api/v0/no/table/{t}"))
        q = {"query": [{"code": v["code"], "selection": {"filter": "all", "values": ["*"]}} for v in meta["variables"] if v["code"] != "ContentsCode"]
             + [{"code": "ContentsCode", "selection": {"filter": "item", "values": ["Personer"]}}], "response": {"format": "json-stat2"}}
        req = urllib.request.Request(f"https://data.ssb.no/api/v0/no/table/{t}", data=json.dumps(q).encode(), headers={**UA, "Content-Type": "application/json"})
        open(path, "wb").write(urllib.request.urlopen(req, timeout=300).read()); print("  ", path)

if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    try: norway()
    except Exception as e: print("  ! norway", e)
    todo = expand()
    print(len(todo), "files")
    if "--list" in sys.argv:
        for cc, fn, u in todo: print(cc, fn, u)
        sys.exit()
    ok = bad = 0
    for cc, fn, u in todo:
        path = os.path.join(RAW, fn)
        if os.path.exists(path) and os.path.getsize(path) > 0: ok += 1; continue
        try:
            data = get(u)
            if data[:200].lstrip().lower().startswith((b"<!doctype html", b"<html")): raise ValueError("got a web page, not data")
            open(path, "wb").write(data); ok += 1
            print(f"  {fn}  {len(data) // 1024} KB", flush=True)
        except Exception as e:
            bad += 1; print(f"  ! {fn}  {u}  {e}", flush=True)
    print(f"done: {ok} files, {bad} failed")
