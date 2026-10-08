# Downloads the sources for data/spanish-names.json into raw/spanish/ (skips anything already there).
#
#   INE "Apellidos y nombres más frecuentes" (Estadística del Padrón Continuo / Censos de población anuales, 1 Jan 2025),
#     ine.es/daco/daco42/nombyapel/: every name borne by 20+ residents of Spain by sex (nombres_por_edad_media.xlsx), the 100
#     most frequent by province of residence (nombres_mas_frecuentes.xlsx), the 50 most frequent by decade of birth
#     (nombres_por_fecha.xlsx), and the methodology note (nota_nombres.pdf). INE terms: free reuse citing the source.
#   Wiktionary (CC BY-SA 4.0), one JSON per edition and list: {title: {"g": b|g|e, "cats": [...], "text": wikitext}}
#     en  "<Language> male/female/unisex given names" for Spanish, Old Spanish, Asturian, Leonese, Aragonese, Ladino
#         (Catalan, Galician, Basque, Quechua, Nahuatl, Guarani and Aymara are already in raw/wikt/, fetch_wiktionary_names.py)
#     es  ES:Antropónimos femeninos / masculinos / ambiguos
#     ca  Prenoms femenins / masculins en català, castellà, gallec, basc, aragonès
#     gl  Nomes propios en galego / castelán / vasco / catalán / asturiano / aragonés (proper nouns of every kind: the
#         builder keeps only entries defined as "nome propio masculino/feminino")
#     eu  Emakume / Gizon izenak euskaraz, gaztelaniaz, katalanez, galizieraz
#     ast Nomes propios femeninos / masculinos asturianos, aragoneses, españoles, gallegos, catalanes (proper nouns of every
#         kind: the builder keeps only entries defined as given names)
#   Wikidata (CC0)
#     wd-iberian-royals.json  people of the medieval and early-modern Iberian kingdoms (citizenship Castile, León, Navarre,
#                             Aragon, Barcelona, Portugal, Asturias, Galicia, Majorca, Valencia) with a noble title, an office
#                             or a royal/noble house, with their Spanish, Catalan and Galician labels, sex and dates
#     wd-given-names.json     given-name items tagged with an Iberian or Latin American indigenous language (P407)
#
#   python3 scripts/fetch_spanish_sources.py
import json, os, sys, time, urllib.parse, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); RAW = os.path.join(ROOT, "raw", "spanish")
UA = {"User-Agent": "Lullabyte/1.0 (https://github.com/suhxnitiwari/baby-name-maker; suhxnitiwari@gmail.com)"}

def get(url, data=None, headers=None, tries=8):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
            return urllib.request.urlopen(req, timeout=180).read()
        except Exception as e:
            print("   retry", url[:90], e, flush=True); time.sleep(5 * (attempt + 1))
    raise RuntimeError("failed: " + url)

def ine():
    for f in ("nombres_por_edad_media.xlsx", "nombres_mas_frecuentes.xlsx", "nombres_por_fecha.xlsx", "nota_nombres.pdf"):
        path = os.path.join(RAW, "ine-" + f)
        if os.path.exists(path): continue
        open(path, "wb").write(get("https://www.ine.es/daco/daco42/nombyapel/" + f)); print("  INE", f); time.sleep(2)

# ── Wiktionary ──
def api(wiki, **q):
    q.update(format="json", maxlag="5")
    for attempt in range(30):
        d = json.loads(get(f"https://{wiki}.wiktionary.org/w/api.php", data=urllib.parse.urlencode(q).encode()))
        if d.get("error", {}).get("code") == "maxlag": time.sleep(10); continue
        return d
    raise RuntimeError("maxlag")

def members(wiki, cat):
    out, cont = [], {}
    while True:
        d = api(wiki, action="query", list="categorymembers", cmtitle=cat, cmlimit="500", cmtype="page", cmnamespace="0", **cont)
        out += [m["title"] for m in d.get("query", {}).get("categorymembers", [])]
        if "continue" not in d: return out
        cont = d["continue"]; time.sleep(.5)

def texts(wiki, titles):
    out = {}
    for i in range(0, len(titles), 50):
        d = api(wiki, action="query", prop="revisions", rvprop="content", rvslots="main", titles="|".join(titles[i:i + 50]))
        for p in d.get("query", {}).get("pages", {}).values():
            out[p["title"]] = (p.get("revisions") or [{}])[0].get("slots", {}).get("main", {}).get("*", "")
        time.sleep(.5)
    return out

# (file, wiki, [(category, sex)])  sex "" = decided from the entry itself
def wikt_lists():
    L = []
    for lang in ("Spanish", "Old Spanish", "Asturian", "Leonese", "Aragonese", "Ladino", "Extremaduran", "Classical Nahuatl"):
        L.append((f"wikt-en-{lang.replace(' ', '_')}", "en", [(f"Category:{lang} {s} given names", g) for s, g in (("male", "b"), ("female", "g"), ("unisex", "e"))]))
    L.append(("wikt-es", "es", [("Categoría:ES:Antropónimos femeninos", "g"), ("Categoría:ES:Antropónimos masculinos", "b"), ("Categoría:ES:Antropónimos ambiguos", "e")]))
    for lang, key in (("català", "ca"), ("castellà", "es"), ("gallec", "gl"), ("basc", "eu"), ("aragonès", "an")):
        L.append((f"wikt-ca-{key}", "ca", [(f"Categoria:Prenoms femenins en {lang}", "g"), (f"Categoria:Prenoms masculins en {lang}", "b")]))
    for lang, key in (("galego", "gl"), ("castelán", "es"), ("vasco", "eu"), ("catalán", "ca"), ("asturiano", "ast"), ("aragonés", "an")):
        L.append((f"wikt-gl-{key}", "gl", [(f"Categoría:Nomes propios en {lang}", "")]))
    for lang, key in (("euskaraz", "eu"), ("gaztelaniaz", "es"), ("katalanez", "ca"), ("galizieraz", "gl")):
        L.append((f"wikt-eu-{key}", "eu", [(f"Kategoria:Emakume izenak {lang}", "g"), (f"Kategoria:Gizon izenak {lang}", "b")]))
    for lang, key in (("asturianos", "ast"), ("aragoneses", "an"), ("españoles", "es"), ("gallegos", "gl"), ("catalanes", "ca")):
        L.append((f"wikt-ast-{key}", "ast", [(f"Categoría:Nomes propios femeninos {lang}", "g"), (f"Categoría:Nomes propios masculinos {lang}", "b")]))
    return L

def wiktionary():
    for fn, wiki, cats in wikt_lists():
        path = os.path.join(RAW, fn + ".json")
        if os.path.exists(path): continue
        sex, where = {}, {}
        for cat, g in cats:
            for t in members(wiki, cat):
                sex[t] = "e" if t in sex and sex[t] and g and sex[t] != g else (g or sex.get(t, ""))
                where.setdefault(t, []).append(cat)
        tx = texts(wiki, sorted(sex))
        json.dump({t: {"g": g, "cats": where[t], "text": tx.get(t, "")} for t, g in sex.items()}, open(path, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"  {fn}: {len(sex):,} entries", flush=True)

# ── Wikidata ──
def sparql(q):
    return json.loads(get("https://query.wikidata.org/sparql", data=urllib.parse.urlencode({"query": q}).encode(),
                          headers={"Accept": "application/sparql-results+json"}), strict=False)["results"]["bindings"]

KINGDOMS = {"Q217196": "Crown of Castile", "Q179293": "Kingdom of Castile", "Q175276": "Kingdom of León", "Q200262": "Kingdom of Navarre",
            "Q3446210": "Kingdom of Pamplona", "Q204920": "Crown of Aragon", "Q199442": "Kingdom of Aragon", "Q1233672": "County of Barcelona",
            "Q45670": "Kingdom of Portugal", "Q231392": "Kingdom of Asturias", "Q303421": "Kingdom of Galicia", "Q836676": "Kingdom of Majorca",
            "Q142417": "Kingdom of Valencia"}
ROYALS_Q = """SELECT DISTINCT ?p ?c ?sex ?born ?died ?esl ?cal ?gll ?desc WHERE {
  VALUES ?c { %s }
  ?p wdt:P27 ?c; wdt:P31 wd:Q5.
  { ?p wdt:P97 [] } UNION { ?p wdt:P39 [] } UNION { ?p wdt:P53 [] }
  OPTIONAL { ?p wdt:P21 ?sex } OPTIONAL { ?p wdt:P569 ?born } OPTIONAL { ?p wdt:P570 ?died }
  OPTIONAL { ?p rdfs:label ?esl. FILTER(lang(?esl)="es") } OPTIONAL { ?p rdfs:label ?cal. FILTER(lang(?cal)="ca") }
  OPTIONAL { ?p rdfs:label ?gll. FILTER(lang(?gll)="gl") } OPTIONAL { ?p schema:description ?desc. FILTER(lang(?desc)="en") }
}""" % " ".join("wd:" + q for q in KINGDOMS)

LANGS = {"Q1321": "Spanish", "Q7026": "Catalan", "Q9307": "Galician", "Q8752": "Basque", "Q29507": "Asturian", "Q8765": "Aragonese",
         "Q36196": "Ladino", "Q5218": "Quechua", "Q13300": "Nahuatl", "Q35876": "Guarani", "Q33730": "Mapudungun", "Q4627": "Aymara"}
GIVEN_Q = """SELECT DISTINCT ?n ?type ?lang ?label ?native ?nl WHERE {
  VALUES ?lang { %s }
  VALUES ?type { wd:Q12308941 wd:Q11879590 wd:Q3409032 }
  ?n wdt:P31 ?type; wdt:P407 ?lang.
  OPTIONAL { ?n wdt:P1705 ?native. BIND(lang(?native) AS ?nl) }
  ?n rdfs:label ?label. FILTER(lang(?label) IN ("es","ca","gl","eu","ast","an","lad","qu","nah","gn","arn","ay"))
}""" % " ".join("wd:" + q for q in LANGS)

def wikidata():
    path = os.path.join(RAW, "wd-iberian-royals.json")
    if not os.path.exists(path):
        rows = sparql(ROYALS_Q)
        json.dump([{k: v["value"].rsplit("/", 1)[-1] if v["value"].startswith("http://www.wikidata.org/entity/") else v["value"] for k, v in r.items()} for r in rows],
                  open(path, "w", encoding="utf-8"), ensure_ascii=False); print("  royals", len(rows)); time.sleep(5)
    path = os.path.join(RAW, "wd-given-names.json")
    if not os.path.exists(path):
        rows = sparql(GIVEN_Q)
        json.dump([{k: v["value"].rsplit("/", 1)[-1] if v["value"].startswith("http://www.wikidata.org/entity/") else v["value"] for k, v in r.items()} | {"label_lang": r["label"].get("xml:lang", "")} for r in rows],
                  open(path, "w", encoding="utf-8"), ensure_ascii=False); print("  given names", len(rows))

if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    what = sys.argv[1:] or ["ine", "wiktionary", "wikidata"]
    if "ine" in what: ine()
    if "wikidata" in what: wikidata()
    if "wiktionary" in what: wiktionary()
