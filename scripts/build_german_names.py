# German and continental Germanic names of every era → data/german-names.json (the row format of culture-names.json:
# [name, g, culture, language, religions, meaning, src, texts, kind, also]).
#
# Where a name is used and where it comes from are kept apart. The culture says who used the name (German, Frankish,
# Gothic, Lombard, Alemannic, Bavarian) and the language says in which stage it is attested (Old High German, Middle High
# German, German, Low German…); where the name comes from is said in words ("from Hebrew", "from Old High German") and,
# only when a source gives a Germanic etymology, by the extra basket "Germanic" in `also`. Johann is a German name of
# Hebrew origin; Adalbert is a German name of Germanic origin.
#
#   Wiktionary (CC BY-SA 4.0): every entry in "<language> given names" and its subcategories (male, female, unisex,
#     diminutives, "from <language>") for German, Old High German, Middle High German, Old Saxon, Low German,
#     East Central German, Luxembourgish, Cimbrian, Alemannic German, Bavarian and Gothic; the etymology and the meaning
#     the entry glosses. Gothic entries keep their Gothic spelling ("Written 𐌸𐌹𐌿𐌳𐌰𐍂𐌴𐌹𐌺𐍃.") and are spelled in Latin
#     letters with Wiktionary's own Gothic transliteration.
#   Wikidata (CC0): given-name items whose language (P407) is German, Old High German, Middle High German, Low German,
#     Old Saxon, Swiss German, Luxembourgish, Gothic, Frankish, Lombardic, Alemannic or Bavarian; the members (P53) of the
#     Merovingian, Carolingian, Ottonian, Salian, Hohenstaufen and later German houses, the Amal and Balt Gothic houses,
#     the Lombard Lethings and the Bavarian Agilolfings (and their branches); and the people of the Holy Roman Empire,
#     East Francia, the Frankish, Lombard and Gothic kingdoms and the German states before 1871 with a given name (P735).
#     A person's name is the first word of their German label (Chlodwig I. → Chlodwig) or their given-name item.
#   Literature (public domain): the characters Wikidata places in a work (P1441 / P674) and, for plays, the cast list
#     printed in the text, each kept only when the name is found in the text itself: Project Gutenberg's German texts,
#     German Wikisource, and Internet Archive scans of 19th-century editions of the Middle High German epics.
#
# Nothing is guessed: a name, its sex and its meaning are kept only when a source gives them. Not used: DMNES (no reuse
# licence, all rights reserved), Archion, Ancestry/FamilySearch indexes, beliebte-vornamen.de and GfdS lists.
# Downloads are cached in raw/german/ (delete a file there to fetch it again).
#
# Each row has an 11th slot, ease (1–3): how easily the name is spelled in modern English and used today. 1 = plain English letters,
# at most 8 of them, and given to 100+ people in the modern registries (data/names-db.tsv); 3 = letters English doesn't use
# (þ, ƕ, â), old spellings (Chl-, Hr-, -uu-), more than 11 letters, or no one in the modern registries; 2 = the rest.
# Rows are sorted by ease, then name.
#
#   python3 scripts/build_german_names.py             (downloads what raw/german/ lacks)
#   python3 scripts/build_german_names.py --offline   (only what is cached; a stage whose download is missing is skipped)
import collections, csv, glob, json, os, re, sys, time, unicodedata, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "raw", "german"); OUT = os.path.join(ROOT, "data", "german-names.json")
sys.path.insert(0, HERE)
from fetch_wiktionary_names import api, UA
from build_cultures import clean, section
from build_medieval import etymology, tpl_args, LANGS as MED_LANGS

LANGS = dict(MED_LANGS)
LANGS.update({"gmh": "Middle High German", "gml": "Middle Low German", "de": "German", "got": "Gothic", "lng": "Lombardic", "gsw": "Alemannic German",
              "bar": "Bavarian", "lb": "Luxembourgish", "nds": "Low German", "nds-de": "Low German", "gmw-ecg": "East Central German", "cim": "Cimbrian",
              "gme-pro": "Proto-East Germanic", "osx": "Old Saxon", "dum": "Middle Dutch", "nl": "Dutch", "da": "Danish", "sv": "Swedish", "no": "Norwegian",
              "pl": "Polish", "cs": "Czech", "hu": "Hungarian", "sl": "Slovene", "ru": "Russian", "es": "Spanish", "pt": "Portuguese", "ga": "Irish",
              "grc-koi": "Koine Greek", "la-new": "New Latin", "sla-pro": "Proto-Slavic", "cel-pro": "Proto-Celtic", "fy": "West Frisian",
              "ofs": "Old Frisian", "ine-pro": "Proto-Indo-European", "xvn": "Vandalic"})
MED_LANGS.update(LANGS)   # etymology() reads build_medieval's table
GERMANIC_ROOT = re.compile(r"Germanic|Old High German|Middle High German|Old Saxon|Frankish|Gothic|Lombardic|Old Norse|Old English|Old Frisian|Old Dutch|"
                           r"Middle Low German|Vandalic|Burgundian")
NAME = re.compile(r"^[A-ZÀ-ÞĀ-ſƕǶÞ][^\W\d_]+(?:[-'’][^\W\d_]+)?$")
STOP = set("""Der Die Das Des Dem Den Ein Eine Und Von Zu Zum Zur Am Im Sankt St Heilige Heiliger Hl Kaiser Kaiserin König Königin Graf Gräfin Herzog Herzogin
Prinz Prinzessin Fürst Fürstin Markgraf Markgräfin Landgraf Landgräfin Pfalzgraf Pfalzgräfin Erzherzog Erzherzogin Kurfürst Kurfürstin Bischof Erzbischof
Abt Äbtissin Papst Frau Herr Fräulein Lady Lord Sir Don Donna Doktor Dr Meister Pater Bruder Schwester Mutter Vater Ritter Junker Baron Baronin Freiherr
Freifrau Gräfin Marquis Marquise Herzogs Königs Kaisers Graf Burggraf Burggräfin Vogt Kanzler Major Hauptmann Oberst Leutnant General Rat Präsident
Saint Queen King Emperor Empress Duke Duchess Count Countess Prince Princess Saint Bishop Abbot Abbess Pope The""".split())

def fold(s):
    s = unicodedata.normalize("NFD", s.replace("ß", "ss").replace("Þ", "Th").replace("þ", "th").replace("Æ", "Ae").replace("æ", "ae").lower())
    return re.sub(r"[\s'’-]", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))

def an(w): return "An" if w[:1] in "AEIOUÄÖÜ" else "A"

# ---------- polite downloads, cached ----------
OFFLINE = "--offline" in sys.argv
def cached(name, fetch):
    path = os.path.join(RAW, name)
    if not os.path.exists(path) and OFFLINE: return None
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = fetch()
        with open(path, "w", encoding="utf-8") as f: (json.dump(data, f, ensure_ascii=False) if not isinstance(data, str) else f.write(data))
    with open(path, encoding="utf-8") as f: return json.load(f) if name.endswith(".json") else f.read()

def get(url, **headers):
    for attempt in range(6):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers={**UA, **headers}), timeout=300).read()
            time.sleep(1)
            return data.decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            if e.code == 404: return ""
            time.sleep(10 * (attempt + 1))
        except Exception: time.sleep(10 * (attempt + 1))
    raise RuntimeError("could not fetch " + url)

def sparql(q):
    return json.loads(get("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q}), Accept="application/sparql-results+json"))["results"]["bindings"]

V = lambda b, k: b.get(k, {}).get("value", "")
Q = lambda b, k: V(b, k).rsplit("/", 1)[-1]

# ---------- 1. Wiktionary ----------
WIKT = {  # Wiktionary language → (culture, language shown)
    "German": ("German", "German"), "Old High German": ("German", "Old High German"), "Middle High German": ("German", "Middle High German"),
    "Old Saxon": ("German", "Old Saxon"), "Low German": ("German", "Low German"), "East Central German": ("German", "East Central German"),
    "Luxembourgish": ("German", "Luxembourgish"), "Cimbrian": ("German", "Cimbrian"), "Alemannic German": ("Alemannic", "Alemannic German"),
    "Bavarian": ("Bavarian", "Bavarian"), "Gothic": ("Gothic", "Gothic")}

def fetch_wikt(lang):
    cats, seen, todo = collections.defaultdict(set), set(), [(f"{lang} given names", 0)]
    while todo:
        cat, depth = todo.pop()
        if cat in seen: continue
        seen.add(cat); cont = {}
        while True:
            d = api(action="query", list="categorymembers", cmtitle="Category:" + cat, cmlimit="500", cmtype="page|subcat", **cont)
            for m in d.get("query", {}).get("categorymembers", []):
                t = m["title"]
                if t.startswith("Category:"):
                    sub = t[9:]
                    if depth < 2 and sub.startswith(lang + " ") and "renderings" not in sub: todo.append((sub, depth + 1))
                else: cats[t].add(cat)
            time.sleep(.3)
            if "continue" not in d: break
            cont = d["continue"]
    titles, text = sorted(cats), {}
    for i in range(0, len(titles), 50):
        d = api(action="query", prop="revisions", rvprop="content", rvslots="main", titles="|".join(titles[i:i + 50]))
        for p in d.get("query", {}).get("pages", {}).values():
            text[p["title"]] = ((p.get("revisions") or [{}])[0]).get("slots", {}).get("main", {}).get("*", "")
        time.sleep(.5)
    return {t: {"cats": sorted(cats[t]), "text": text.get(t, "")} for t in titles}

GOTHIC = dict(zip("𐌰𐌱𐌲𐌳𐌴𐌵𐌶𐌷𐌸𐌹𐌺𐌻𐌼𐌽𐌾𐌿𐍀𐍂𐍃𐍄𐍅𐍆𐍇𐍈𐍉", ["a", "b", "g", "d", "e", "q", "z", "h", "þ", "i", "k", "l", "m", "n", "j", "u", "p", "r", "s", "t", "w", "f", "x", "ƕ", "o"]))
def gothic_latin(s):   # Wiktionary's Gothic transliteration (Module:got-translit), letter by letter
    out = "".join(GOTHIC.get(c, "?") for c in s)
    return "" if "?" in out else out[:1].upper() + out[1:]

def sex_of_entry(cats, sec):
    s = {g for c in cats for w, g in (("male", "b"), ("female", "g"), ("unisex", "e")) if re.search(r"\b" + w + r"\b", c)}
    if not s:
        m = re.search(r"\{\{given name\|(?:[a-z-]+\|)?(male|female|unisex)", sec)
        if m: s = {{"male": "b", "female": "g", "unisex": "e"}[m.group(1)]}
    return "" if not s else ("e" if len(s) > 1 or "e" in s else s.pop())

def diminutive_of(sec):
    m = re.search(r"\{\{given name\|[^{}]*\bdim(?:of)?=([^|}]+)", sec) or re.search(r"\{\{(?:diminutive of|dim of)\|[a-z-]+\|([^|}]+)", sec)
    return clean(m.group(1)) if m else ""

# ---------- 2. Wikidata ----------
LANG_Q = {"Q188": ("German", "German"), "Q35218": ("German", "Old High German"), "Q837985": ("German", "Middle High German"), "Q25433": ("German", "Low German"),
          "Q505674": ("German", "Middle Low German"), "Q35219": ("German", "Old Saxon"), "Q387066": ("German", "Swiss German"), "Q9051": ("German", "Luxembourgish"),
          "Q35722": ("Gothic", "Gothic"), "Q10860505": ("Frankish", "Old Frankish"), "Q35972": ("Lombard", "Lombardic"), "Q131339": ("Alemannic", "Alemannic German"),
          "Q29540": ("Bavarian", "Bavarian")}
GN_CLASS = {"Q202444": "e", "Q11879590": "g", "Q12308941": "b", "Q3409032": "e"}
WD_NAMES = """SELECT ?i ?c ?lang ?de ?en ?native WHERE {
  VALUES ?lang { %s } VALUES ?c { wd:Q202444 wd:Q11879590 wd:Q12308941 wd:Q3409032 }
  ?i wdt:P407 ?lang ; wdt:P31 ?c .
  OPTIONAL { ?i rdfs:label ?de FILTER(lang(?de) = "de") } OPTIONAL { ?i rdfs:label ?en FILTER(lang(?en) = "en") }
  OPTIONAL { ?i wdt:P1705 ?native } }""" % " ".join("wd:" + q for q in LANG_Q)

# house → (culture, adjective); the branches of each house come from Wikidata (part of / subclass of / parent organization)
HOUSES = {"Q59488": ("Frankish", "Merovingian"), "Q133602": ("Frankish", "Carolingian"), "Q931785": ("Frankish", "Pippinid"), "Q697806": ("Frankish", "Arnulfing"),
          "Q157106": ("German", "Ottonian"), "Q161204": ("German", "Salian"), "Q130875": ("German", "Hohenstaufen"), "Q156433": ("German", "Welf"),
          "Q65968": ("German", "Habsburg"), "Q131621": ("German", "Wittelsbach"), "Q83969": ("German", "Hohenzollern"), "Q152909": ("German", "Wettin"),
          "Q122293": ("German", "Luxembourg"), "Q522698": ("German", "Babenberg"), "Q247331": ("German", "Zähringen"), "Q168352": ("German", "Ascanian"),
          "Q699788": ("German", "Württemberg"), "Q689115": ("German", "Hessian"), "Q646085": ("German", "Nassau"), "Q619029": ("German", "Conradine"),
          "Q689402": ("German", "Billung"), "Q700158": ("German", "Mecklenburg"), "Q155594": ("German", "Oldenburg"), "Q1753846": ("German", "Saxe-Coburg"),
          "Q263364": ("Bavarian", "Agilolfing"), "Q452762": ("Gothic", "Amal"), "Q789757": ("Gothic", "Balt"), "Q2709068": ("Lombard", "Lething")}
BRANCHES = """SELECT ?root ?fam WHERE { VALUES ?root { %s } ?fam (wdt:P361|wdt:P279|wdt:P749)+ ?root . }""" % " ".join("wd:" + q for q in HOUSES)
PEOPLE = """SELECT ?p ?fam ?state ?de ?en ?desc ?sex ?b ?d ?links ?saint
  (GROUP_CONCAT(DISTINCT ?gnl; separator="|") AS ?gn) (GROUP_CONCAT(DISTINCT ?cl; separator="|") AS ?cit) WHERE {
  %s
  OPTIONAL { ?p wdt:P735 ?g . ?g rdfs:label ?gnl FILTER(lang(?gnl) = "de") }
  OPTIONAL { ?p rdfs:label ?de FILTER(lang(?de) = "de") } OPTIONAL { ?p rdfs:label ?en FILTER(lang(?en) = "en") }
  OPTIONAL { ?p schema:description ?desc FILTER(lang(?desc) = "en") } OPTIONAL { ?p wdt:P21 ?sex }
  OPTIONAL { ?p wdt:P569 ?b } OPTIONAL { ?p wdt:P570 ?d } OPTIONAL { ?p wikibase:sitelinks ?links } OPTIONAL { ?p wdt:P411 ?saint }
  OPTIONAL { ?p wdt:P27 ?c . ?c rdfs:label ?cl FILTER(lang(?cl) = "en") }
} GROUP BY ?p ?fam ?state ?de ?en ?desc ?sex ?b ?d ?links ?saint"""
# realms → (culture, how the src names it); a German state's people count only with a name German records also know
STATES = {"Q146246": ("Frankish", "the Frankish kingdom"), "Q31929": ("Frankish", "the Carolingian Empire"), "Q105098": ("Frankish", "Austrasia"),
          "Q854415": ("Lombard", "the Lombard kingdom"), "Q583038": ("Gothic", "the Ostrogothic kingdom"), "Q126936": ("Gothic", "the Visigothic kingdom"),
          "Q2940142": ("Gothic", "the Visigothic kingdom"), "Q3307686": ("Gothic", "the Visigothic kingdom"),
          "Q153080": ("German", "East Francia"), "Q175211": ("German", "the Kingdom of Germany"), "Q12548": ("German", "the Holy Roman Empire"),
          "Q47261": ("German", "the Duchy of Bavaria"), "Q256961": ("German", "the Electorate of Bavaria"), "Q156199": ("German", "the Electorate of Saxony"),
          "Q148499": ("German", "the Margraviate of Brandenburg"), "Q168651": ("German", "Hesse-Kassel"), "Q699964": ("German", "the Archduchy of Austria"),
          "Q435583": ("German", "the Old Swiss Confederacy"), "Q27306": ("German", "the Kingdom of Prussia"), "Q154195": ("German", "the Kingdom of Bavaria"),
          "Q153015": ("German", "the Kingdom of Saxony"), "Q159631": ("German", "the Kingdom of Württemberg"), "Q164079": ("German", "the Kingdom of Hanover"),
          "Q186320": ("German", "the Grand Duchy of Baden"), "Q151624": ("German", "the German Confederation")}
GERMAN_LANDS = re.compile(r"German|Prussia|Bavaria|Saxony|Saxe|Austria|Holy Roman|Hesse|Württemberg|Baden|Hanover|Brunswick|Mecklenburg|Franc|Frank|Thuringia|"
                          r"Swabia|Palatinate|Brandenburg|Silesia|Luxembourg|Swiss|Switzerland|Liechtenstein|Oldenburg|Anhalt|Nassau|Lippe|Reuss|Schwarzburg|"
                          r"Waldeck|Holstein|Schleswig|Pomerania|Cologne|Trier|Mainz|Tyrol|Styria|Carinthia|Lorraine|Lombard|Goth|Austrasia|Neustria|Burgund|Alsace", re.I)

ROLES = ["saint", "empress", "emperor", "queen", "king", "electress", "elector", "archduchess", "archduke", "grand duchess", "grand duke", "duchess", "duke",
         "margravine", "margrave", "landgravine", "landgrave", "countess palatine", "count palatine", "burgravine", "burgrave", "countess", "count",
         "princess", "prince", "abbess", "abbot", "archbishop", "bishop", "nun", "monk", "mystic", "poet", "minnesinger", "theologian", "noblewoman", "nobleman"]
def role_of(desc, saint):
    if saint: return "saint"
    d = (desc or "").lower()
    for r in ROLES:
        if re.search(r"\b" + r + r"\b", d): return r
    return ""

def era_language(year, culture):
    if culture == "Gothic": return "Gothic"
    if culture == "Lombard": return "Lombardic"
    if culture == "Frankish": return "Old Frankish" if year and year < 700 else "Old High German"
    if not year or year < 1050: return "Old High German"
    if year < 1350: return "Middle High German"
    if year < 1650: return "Early New High German"
    return "German"

def first_word(label):
    w = [x for x in re.split(r"[\s,]+", re.sub(r"\(.*?\)", "", label or "")) if x]
    while w and w[0].rstrip(".") in STOP: w = w[1:]
    return w[0] if w and NAME.match(w[0]) and len(w[0]) > 2 and w[0] not in STOP else ""

def year(v):
    m = re.match(r"^(-?\d{1,4})-", v or "")
    return int(m.group(1)) if m else None

# ---------- 3. literature ----------
# key: (title shown, year, language, Wikidata works, texts, mode). texts: gutenberg ids, "ia:<Internet Archive id>", "ws:<German Wikisource page>".
# mode "cast": also read the play's printed cast list; "mhg": a Middle/Old High German edition where only names are capitalised
WORKS = {
    "hildebrandslied": ("the Hildebrandslied (c. 830)", "Old High German", ["Q263158"], ["ws:Hildebrandslied"], "mhg"),
    "nibelungenlied": ("the Nibelungenlied (c. 1200)", "Middle High German", ["Q131554"], [48888, 14915], "mhg"),
    "kudrun": ("Kudrun (c. 1240)", "Middle High German", ["Q491164"], ["ia:11668863bsb"], ""),
    "parzival": ("Wolfram von Eschenbach's Parzival (c. 1210)", "Middle High German", ["Q1247232", "Q1514654", "Q2576669"],
                 ["ia:parzivalundtitu01eschgoog", "ia:parzivalundtiturelsimrick2aufl"], "mhg"),
    "tristan": ("Gottfried von Strassburg's Tristan (c. 1210)", "Middle High German", ["Q2454177"], ["ia:gottfriedsvonst00bechgoog", "ia:tristanundisoldevongottfriedsimr1"], "mhg"),
    "erec": ("Hartmann von Aue's Erec (c. 1185)", "Middle High German", ["Q1349655"], ["ia:ereceineerzhlun01haupgoog"], "mhg"),
    "iwein": ("Hartmann von Aue's Iwein (c. 1200)", "Middle High German", ["Q2048507", "Q1198287"], ["ia:11941725bsb"], "mhg"),
    "heldenbuch": ("the Dietrich epics (Deutsches Heldenbuch)", "Middle High German", ["Q1281547", "Q878781", "Q329662", "Q2650997", "Q1544259"],
                   ["ia:deutscheshelden00jngoog", "ia:bub_gb_sqIFAQAAIAAJ"], "mhg"),
    "khm": ("Grimm's Kinder- und Hausmärchen (folklore name)", "German", ["Q163027"], [20050, 20051, 77905], "folk"),
    "faust": ("Goethe's Faust (1808)", "German", ["Q29478", "Q13221881", "Q2500544"], [2229, 21000, 2230], "cast"),
    "werther": ("Goethe's Die Leiden des jungen Werthers (1774)", "German", ["Q151883"], [19794], ""),
    "meister": ("Goethe's Wilhelm Meisters Lehrjahre (1795–96)", "German", ["Q1194031", "Q478344"], list(range(2335, 2343)), ""),
    "wahlverwandtschaften": ("Goethe's Die Wahlverwandtschaften (1809)", "German", [], [2403], ""),
    "goetz": ("Goethe's Götz von Berlichingen (1773)", "German", [], [2321], "cast"),
    "egmont": ("Goethe's Egmont (1788)", "German", ["Q1298242"], [2146], "cast"),
    "hermann": ("Goethe's Hermann und Dorothea (1797)", "German", [], [2312], ""),
    "raeuber": ("Schiller's Die Räuber (1781)", "German", ["Q466333"], [47804], "cast"),
    "kabale": ("Schiller's Kabale und Liebe (1784)", "German", ["Q263150"], [6498], "cast"),
    "wallenstein": ("Schiller's Wallenstein (1799)", "German", [], [6518, 6525, 6549], "cast"),
    "tell": ("Schiller's Wilhelm Tell (1804)", "German", ["Q937281"], [77182], "cast"),
    "jungfrau": ("Schiller's Die Jungfrau von Orleans (1801)", "German", [], [6383], "cast"),
    "fiesco": ("Schiller's Fiesco (1783)", "German", [], [6499], "cast"),
    "emilia": ("Lessing's Emilia Galotti (1772)", "German", [], [9108], "cast"),
    "minna": ("Lessing's Minna von Barnhelm (1767)", "German", ["Q1209859"], [9187], "cast"),
    "nathan": ("Lessing's Nathan der Weise (1779)", "German", ["Q286611"], [9186], "cast"),
    "kaethchen": ("Kleist's Das Käthchen von Heilbronn (1810)", "German", [], [6646], "cast"),
    "krug": ("Kleist's Der zerbrochne Krug (1808)", "German", [], [6647], "cast"),
    "homburg": ("Kleist's Prinz Friedrich von Homburg (1821)", "German", [], [6723], "cast"),
    "topf": ("E. T. A. Hoffmann's Der goldne Topf (1814)", "German", ["Q785009"], [17362], ""),
    "nachtstuecke": ("E. T. A. Hoffmann's Nachtstücke (1816–17)", "German", ["Q798227"], [6341], ""),
    "murr": ("E. T. A. Hoffmann's Kater Murr (1819–21)", "German", ["Q1314475"], [38780], ""),
    "zaches": ("E. T. A. Hoffmann's Klein Zaches (1819)", "German", [], [9200], ""),
    "effi": ("Fontane's Effi Briest (1895)", "German", ["Q1296168"], [5323], ""),
    "treibel": ("Fontane's Frau Jenny Treibel (1892)", "German", [], [46184], ""),
    "stechlin": ("Fontane's Der Stechlin (1898)", "German", [], [53628], ""),
    "adultera": ("Fontane's L'Adultera (1882)", "German", ["Q1744488"], [52912], ""),
    "schimmelreiter": ("Storm's Der Schimmelreiter (1888)", "German", ["Q895730"], [19790], ""),
    "immensee": ("Storm's Immensee (1849)", "German", [], [6651], ""),
    "seldwyla": ("Keller's Die Leute von Seldwyla (1856)", "German", [], [6696, 28042], ""),
    "heidi": ("Johanna Spyri's Heidi (1880)", "German", ["Q271697"], [7500, 7512], ""),
    "buddenbrooks": ("Thomas Mann's Buddenbrooks (1901)", "German", ["Q326909"], [34811], ""),
    "zauberberg": ("Thomas Mann's Der Zauberberg (1924)", "German", ["Q212898"], [65661, 65662], ""),
    "venedig": ("Thomas Mann's Der Tod in Venedig (1912)", "German", ["Q828296"], [12108], ""),
    "kroeger": ("Thomas Mann's Tonio Kröger (1903)", "German", [], [23313], ""),
    "hoheit": ("Thomas Mann's Königliche Hoheit (1909)", "German", ["Q1109439"], [35328], ""),
    "heine": ("Heine's Buch der Lieder (1827)", "German", [], [3498], ""),
}
CHARS = """SELECT ?w ?c ?de ?sex (GROUP_CONCAT(DISTINCT ?al; separator="|") AS ?alias) WHERE {
  VALUES ?top { %s }
  { ?w wdt:P361* ?top } { ?c wdt:P1441 ?w } UNION { ?w wdt:P674 ?c }
  OPTIONAL { ?c rdfs:label ?de FILTER(lang(?de) = "de") } OPTIONAL { ?c skos:altLabel ?al FILTER(lang(?al) = "de") } OPTIONAL { ?c wdt:P21 ?sex }
} GROUP BY ?w ?c ?de ?sex"""
SEX_Q = {"Q6581097": "b", "Q6581072": "g", "Q2449503": "b", "Q1052281": "g", "Q15145778": "b", "Q15145779": "g"}

def text_of(src):
    if isinstance(src, int):
        return cached(f"texts/pg{src}.txt", lambda: get(f"https://www.gutenberg.org/cache/epub/{src}/pg{src}.txt"))
    kind, ident = src.split(":", 1)
    safe = re.sub(r"[^\w-]", "_", ident)
    if kind == "ia": return cached(f"texts/ia-{safe}.txt", lambda: get(f"https://archive.org/download/{ident}/{ident}_djvu.txt"))
    if kind == "ws":
        return cached(f"texts/ws-{safe}.txt", lambda: json.loads(get("https://de.wikisource.org/w/api.php?" + urllib.parse.urlencode(
            {"action": "parse", "page": ident, "prop": "wikitext", "format": "json", "redirects": 1}))).get("parse", {}).get("wikitext", {}).get("*", ""))

FEM = re.compile(r"^(?:\w+in|Tochter|Mutter|Schwester|Frau|Witwe|Magd|Amme|Dame|Fräulein|Mädchen|Braut|Gattin|Gemahlin|Nichte|Base|Tante|Jungfer|Kammerjungfer|Zofe|Hexe|Nonne|Äbtissin)$")
MASC = re.compile(r"^(?:Sohn|Bruder|Vater|Mann|Knecht|Diener|Soldat|Ritter|Graf|König|Herzog|Prinz|Fürst|Student|Famulus|Kammerdiener|Jäger|Wirt|Pfarrer|Doktor|"
                  r"Oberst|Major|Hauptmann|Leutnant|Wachtmeister|Neffe|Oheim|Onkel|Vetter|Bräutigam|Gatte|Gemahl|Junge|Knabe|Bauer|Schreiber|Sekretär|Kaplan|"
                  r"Pater|Mönch|Abt|Bischof|Kanzler|Rat|Richter|Schulze|Page|Bedienter|Kammerherr|Edelmann|Hofmarschall|Präsident|Kaiser|Landvogt|Ritter|Freiherr|"
                  r"Hirte|Fischer|Jude|Templer|Derwisch|Sultan|Narr|Burgvogt|Bürger|Meister|Geselle|Schütze|Rittmeister|Kurfürst|Feldmarschall)$")
def cast_list(text):
    """[(name, sex)] from a play's printed cast list ("Personen" … up to the first act)."""
    m = re.search(r"(?m)^\s*_?(?:Personen|PERSONEN|Personen des Vorspiels|Die Personen)[._:]*_?\s*$", text)
    if not m: return []
    block = re.split(r"(?m)^\s*_?(?:Erste[rs]? (?:Aufzug|Akt|Handlung|Aufzugs)|ERSTE[RS]? (?:AUFZUG|AKT)|Erster Auftritt|Vorspiel|Der Schauplatz|Ort der Handlung|Die Szene)", text[m.end():m.end() + 8000])[0]
    out = []
    for line in block.split("\n"):
        line = line.strip(" _\t")
        if not line or len(line) > 160: continue
        head, _, desc = line.partition(",")
        words = head.replace(".", "").split()
        if not words or words[0] in STOP or not NAME.match(words[0]): continue
        dw = re.findall(r"[A-ZÄÖÜ][a-zäöüß]+", desc)
        sex = next(("g" if FEM.match(w) else "b" for w in dw if FEM.match(w) or MASC.match(w)), "")
        out.append((words[0], len(words), sex))
    return out

# ---------- lexicons ----------
def load_tsv_names(path, codes=None):
    out = {}
    if not os.path.exists(path): return out
    for line in open(path, encoding="utf-8"):
        f = line.rstrip("\n").split("\t")
        if len(f) < 4: continue
        if codes and not set(f[2].split(",")) & codes: continue
        out[fold(f[0])] = (f[0], f[1], int(f[3]) if f[3].isdigit() else 0)
    return out

def site_names():
    keys = set(load_tsv_names(os.path.join(ROOT, "data", "names-db.tsv"))) | set(load_tsv_names(os.path.join(ROOT, "data", "names-extra.tsv")))
    for f in ["scripture-names.json", "bible-extra.json", "culture-names.json", "also-cultures.json", "medieval-names.json", "az-names.json",
              "hebrew-names.json", "russia-cultures.json", "caucasus-balkan-names.json"]:
        p = os.path.join(ROOT, "data", f)
        if os.path.exists(p):
            for r in json.load(open(p, encoding="utf-8")):
                if isinstance(r, list) and r and isinstance(r[0], str): keys.add(fold(r[0]))
    ea = json.load(open(os.path.join(ROOT, "data", "east-asian-names.json"), encoding="utf-8"))
    for rows in ea.values():
        for r in rows:
            if isinstance(r, list) and r and isinstance(r[0], str): keys.add(fold(r[0]))
    return keys

# ---------- build ----------
if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    stats = collections.Counter()
    rows = {}                                      # (fold(name), culture) → row
    def add(name, g, culture, language, source, meaning="", origin="", note="", text="", germanic=False, native="", era=None, order=9):
        k = (fold(name), culture)
        r = rows.get(k)
        if not r:
            r = rows[k] = {"name": name, "g": set(), "culture": culture, "language": language, "meaning": "", "origin": "", "notes": [], "texts": [],
                           "germanic": False, "native": "", "sources": set(), "era": era, "order": order, "lit": []}
        if g: r["g"].add(g)
        if order < r["order"]: r["language"], r["order"] = language, order    # the language of the strongest source (Wiktionary entry first)
        r["meaning"] = r["meaning"] or meaning; r["origin"] = r["origin"] or origin; r["native"] = r["native"] or native
        r["germanic"] |= germanic; r["sources"].add(source)
        if era is not None and (r["era"] is None or era < r["era"]): r["era"] = era
        if note and note not in r["notes"]: r["notes"].append(note)
        if text and text not in r["texts"]: r["texts"].append(text)
        return r

    # 1. Wiktionary
    wikt = {l: cached(f"wikt-{l.replace(' ', '_')}.json", lambda l=l: fetch_wikt(l)) for l in WIKT}
    lexicon = {}                                   # fold → (spelling, sex): names German sources record
    for lang, (culture, language) in WIKT.items():
        for title, e in sorted(wikt[lang].items()):
            sec = section(e["text"], lang)
            if not sec or not re.search(r"\{\{given name\|", sec): stats[f"wikt {lang}: no given-name sense"] += 1; continue
            native = ""
            name = title
            if lang == "Gothic":
                native, name = title, gothic_latin(title)
            if not name or not NAME.match(name): stats[f"wikt {lang}: not a single-word name"] += 1; continue
            g = sex_of_entry(e["cats"], sec)
            if not g: stats[f"wikt {lang}: sex not given"] += 1; continue
            origin, meaning = etymology(sec)
            if fold(meaning) == fold(name): meaning = ""
            from_cats = [c.split(" from ", 1)[1] for c in e["cats"] if " from " in c]
            germanic = bool(GERMANIC_ROOT.search(origin.split(", from ")[-1].rsplit(" ", 1)[0] if origin else "")) or any(GERMANIC_ROOT.search(c) for c in from_cats) \
                or lang in ("Old High German", "Middle High German", "Old Saxon", "Gothic") and not origin
            dim = diminutive_of(sec)
            note = f"A diminutive of {dim}." if dim and fold(dim) != fold(name) else ""
            add(name, g, culture, language, "wikt", meaning, origin, note, germanic=germanic, native=native, order=0 if lang == "German" else 1)
            if culture in ("German", "Alemannic", "Bavarian"): lexicon.setdefault(fold(name), (name, g))
            stats[f"wikt {lang}"] += 1

    # 2a. Wikidata given-name items
    for b in cached("wd-given-names.json", lambda: sparql(WD_NAMES)) or []:
        culture, language = LANG_Q[Q(b, "lang")]
        label = V(b, "de") or V(b, "en")
        native = V(b, "native")
        if culture == "Gothic" and native and not re.search(r"[A-Za-z]", native): label = label or gothic_latin(native)
        if not label or not NAME.match(label): stats["wikidata item: not a single-word label"] += 1; continue
        # Wikidata's language tag on Fiametta or Ildefonse says Gothic or Frankish; outside German only a form in the old script is trusted
        if culture in ("Gothic", "Frankish", "Lombard") and not (native and not re.search(r"[A-Za-z]", native)):
            stats[f"wikidata item: {culture} tag without an old-script form"] += 1; continue
        add(label, GN_CLASS[Q(b, "c")], culture, language, "wd", native=native if native and not re.search(r"[A-Za-z]", native) else "", order=2,
            germanic=culture != "German" or language in ("Old High German", "Middle High German", "Old Saxon"))
        if culture == "German": lexicon.setdefault(fold(label), (label, GN_CLASS[Q(b, "c")]))
        stats[f"wikidata given-name items {language}"] += 1
    db_de = load_tsv_names(os.path.join(ROOT, "data", "names-db.tsv"), {"de", "at", "ch", "lu", "li"})
    for k, (n, g, c) in db_de.items(): lexicon.setdefault(k, (n, {"f": "g", "m": "b"}.get(g, "")))

    # 2b. Wikidata houses and realms
    branches = cached("wd-house-branches.json", lambda: sparql(BRANCHES)) or []
    house_of = {q: q for q in HOUSES}
    for b in branches: house_of.setdefault(Q(b, "fam"), Q(b, "root"))
    fams = sorted(house_of)
    def fetch_people():
        out = []
        for i in range(0, len(fams), 15):
            out += sparql(PEOPLE % ("VALUES ?fam { %s } ?p wdt:P53 ?fam ; wdt:P31 wd:Q5 ." % " ".join("wd:" + f for f in fams[i:i + 15])))
        for s in STATES:
            out += sparql(PEOPLE % ("VALUES ?state { wd:%s } ?p wdt:P27 ?state ; wdt:P31 wd:Q5 ." % s))
        return out
    people = collections.defaultdict(lambda: {"fams": set(), "states": set()})
    plist = cached("wd-people.json", fetch_people)
    if plist is None: stats["people: not downloaded (offline)"] = 1
    for b in plist or []:
        p = people[Q(b, "p")]
        if V(b, "fam"): p["fams"].add(Q(b, "fam"))
        if V(b, "state"): p["states"].add(Q(b, "state"))
        for k in ("de", "en", "desc", "b", "d", "gn", "cit"): p[k] = p.get(k) or V(b, k)
        p["sex"] = p.get("sex") or SEX_Q.get(Q(b, "sex"), ""); p["links"] = max(p.get("links", 0), int(V(b, "links") or 0)); p["saint"] = p.get("saint") or bool(V(b, "saint"))
    bearers = collections.defaultdict(list)       # (fold, culture) → [(person, name, how)]
    for qid, p in people.items():
        if not p["sex"]: stats["people: sex not given"] += 1; continue
        by, dy = year(p["b"]), year(p["d"])
        when = by if by is not None else (dy - 30 if dy is not None else None)
        houses = [house_of[f] for f in p["fams"] if f in house_of]
        if houses:
            h = sorted(houses, key=lambda h: list(HOUSES).index(h))[0]
            culture, adj = HOUSES[h]
            cit = [c for c in p["cit"].split("|") if c]
            if culture == "German" and cit and not any(GERMAN_LANDS.search(c) for c in cit): stats["people: house member of a non-German realm"] += 1; continue
            how = ("house", adj)
        else:
            st = sorted(p["states"], key=lambda s: list(STATES).index(s))[0]
            culture, realm = STATES[st]
            how = ("realm", realm)
        if culture == "German" and when is not None and when >= 1871: continue
        names = []
        w = first_word(p["de"])
        if w: names.append(w)
        for gn in p["gn"].split("|"):
            if gn and NAME.match(gn) and fold(gn) not in map(fold, names): names.append(gn)
        if culture in ("Frankish", "Gothic", "Lombard") and when is not None and when < 800:
            e = first_word(p["en"])        # the usual English form of an early name (Fredegund, Radegund), when it is a spelling of the same name
            if e and fold(e)[:2] == fold(names[0] if names else e)[:2] and fold(e) not in map(fold, names): names.append(e)
        if not names: stats["people: no single-word given name"] += 1; continue
        for n in names:
            # a realm's subject counts only with a name German sources also record (an Italian in the Empire stays Italian)
            if how[0] == "realm" and culture == "German" and fold(n) not in lexicon: stats["people: name not otherwise German"] += 1; continue
            bearers[(fold(n), culture)].append((p, n, how, when))
    for (k, culture), bs in bearers.items():
        bs.sort(key=lambda x: (-x[0]["links"], x[3] if x[3] is not None else 9999))
        p, n, how, when = bs[0]
        first = min((x[3] for x in bs if x[3] is not None), default=None)
        sexes = {x[0]["sex"] for x in bs}
        lang = era_language(first, culture)
        role = role_of(p["desc"], p["saint"])
        dy = year(p["d"])
        who = (p["en"] or p["de"]) + (f", d. {dy}" if dy is not None and dy > 0 else "")
        if how[0] == "house": desc = f"{an(how[1]).lower()} {how[1]} {role}" if role else f"a member of the {how[1]} house"
        else: desc = f"{an(role).lower()} {role} of {how[1]}" if role else f"recorded in {how[1]}"
        note = f"{lang}; {desc} ({who})."
        if len(bs) > 1: note = note[:-1] + f"; {len(bs):,} bearers on Wikidata" + (f", the earliest born {first}" if first is not None and first > 0 else "") + "."
        name = n if n[:1].isupper() else n.title()
        add(name, "e" if len(sexes) > 1 and min(sum(x[0]["sex"] == s for x in bs) for s in sexes) / len(bs) >= .2 else
            collections.Counter(x[0]["sex"] for x in bs).most_common(1)[0][0], culture, lang, "people", note=note, era=first, order=3,
            germanic=culture in ("Frankish", "Gothic", "Lombard", "Bavarian"))
        stats[f"people → {culture}"] += 1

    # 3. literature
    tops = sorted({q for w in WORKS.values() for q in w[2]})
    chars = cached("wd-characters.json", lambda: sparql(CHARS % " ".join("wd:" + q for q in tops))) or []
    top_of = {}
    for key, w in WORKS.items():
        for q in w[2]: top_of[q] = key
    # which work each character item belongs to: the listed work, or a tale/part of it
    parts = cached("wd-work-parts.json", lambda: sparql("SELECT ?w ?top WHERE { VALUES ?top { %s } ?w wdt:P361* ?top }" % " ".join("wd:" + q for q in tops))) or []
    part_top = {Q(b, "w"): top_of[Q(b, "top")] for b in parts}
    cand = collections.defaultdict(list)          # work key → [(name, sex, how)]
    for b in chars:
        key = part_top.get(Q(b, "w"))
        if not key: continue
        sex = SEX_Q.get(Q(b, "sex"), "")
        forms = [V(b, "de")] + [a for a in V(b, "alias").split("|") if a]
        for i, f in enumerate(forms):
            w = first_word(f)
            if w: cand[key].append((w, sex, "wd" if i == 0 else "alias"))
    lit_stats = collections.Counter()
    for key, (title, language, _, texts, mode) in WORKS.items():
        body = "\n".join(text_of(t) or "" for t in texts)
        if not body.strip(): stats[f"literature: no text for {key}"] += 1; continue
        flat = fold(body)
        words = collections.Counter(fold(w) for w in re.findall(r"[^\W\d_]+", body))
        found = {}
        if mode == "cast":
            for t in texts:
                for n, nwords, sex in cast_list(text_of(t)):
                    if nwords > 1 and fold(n) not in lexicon: continue          # "Lady Milford", "Odoardo Galotti": only a known first name
                    cand[key].append((n, sex, "cast"))
        if mode == "mhg":
            # Middle and Old High German editions capitalise only names: a capitalised word inside a verse that German sources know as a name
            mid = collections.Counter(m.group(1) for m in re.finditer(r"(?<=[a-zäöüâêîôûæœ,;] )([A-ZÄÖÜ][a-zäöüâêîôûæœ]{2,})\b", body))
            for w, c in mid.items():
                if c >= 3 and fold(w) in lexicon and w not in STOP: cand[key].append((lexicon[fold(w)][0], "", "text"))
        for n, sex, how in cand[key]:
            if words.get(fold(n), 0) < (1 if how in ("wd", "alias") else 2): continue      # the name must be in the text itself
            known = fold(n) in lexicon
            if mode in ("", "cast") and not known: lit_stats[(key, "not otherwise German")] += 1; continue
            g = sex or (lexicon[fold(n)][1] if known else "")
            if not g: lit_stats[(key, "sex not given")] += 1; continue
            f = found.setdefault(fold(n), [n, set()]); f[1].add(g)
        for k, (n, gs) in found.items():
            lang = language if mode in ("mhg",) else "German"
            r = add(n, "e" if len(gs) > 1 else next(iter(gs)), "German", lang, "lit", note=f"In {title}.", text=re.sub(r"^(the |\w+'s )|( \(.*)$", "", title).strip(),
                    order=4, germanic=False)
            r["lit"].append(key)
            lit_stats[key] += 1

    # 4. meanings for names without one: data/meanings.json (Wiktionary), then the name's own Wiktionary page
    mean = json.load(open(os.path.join(ROOT, "data", "meanings.json"), encoding="utf-8"))
    need = sorted({r["name"] for r in rows.values() if not r["meaning"] and not (mean.get(fold(r["name"])) or {}).get("m") and not r["native"]})
    def fetch_extra():
        out = {}
        for i in range(0, len(need), 50):
            d = api(action="query", prop="revisions", rvprop="content", rvslots="main", titles="|".join(need[i:i + 50]), redirects="1")
            for p in d.get("query", {}).get("pages", {}).values():
                out[p["title"]] = ((p.get("revisions") or [{}])[0]).get("slots", {}).get("main", {}).get("*", "")
            time.sleep(.5)
        return out
    extra = cached("wikt-extra.json", fetch_extra) or {}
    for r in rows.values():
        if r["meaning"]: continue
        m = mean.get(fold(r["name"])) or {}
        if m.get("m") and re.search(r"German|Gothic|Old Saxon|Hebrew|Greek|Latin|Aramaic", m.get("ety", "")) and not re.search(r"identical with|also a|cognate", m.get("ety", ""), re.I):
            # the gloss of this spelling's own origin, not a look-alike word (Estonian mari "berry")
            r["meaning"] = m["m"]
            if m.get("root") and GERMANIC_ROOT.search(m["root"]) and not re.search(r"^Borrowed from German", m.get("ety", "")): r["germanic"] = True
            continue
        text = extra.get(r["name"], "")
        for lang in ("German", "Old High German", "Middle High German", "Gothic", "Old Saxon", "Low German", "Alemannic German", "Bavarian", "Luxembourgish"):
            sec = section(text, lang)
            if sec and re.search(r"\{\{given name\|", sec):
                origin, meaning = etymology(sec)
                if meaning and fold(meaning) != fold(r["name"]):
                    r["meaning"] = meaning; r["origin"] = r["origin"] or origin
                    if origin and GERMANIC_ROOT.search(origin.split(", from ")[-1].rsplit(" ", 1)[0]): r["germanic"] = True
                break

    # 5. rows
    modern = {}
    for f in ("names-db.tsv",):
        for line in open(os.path.join(ROOT, "data", f), encoding="utf-8"):
            x = line.rstrip("\n").split("\t")
            if len(x) >= 4 and x[3].isdigit(): modern[fold(x[0])] = max(modern.get(fold(x[0]), 0), int(x[3]))
    OLD = re.compile(r"^(?:Chl|Chr|Chn|Hl|Hr|Hw|Hn|Hu[^m]|Uu|Wr)|uu|dh|hh|[bdgkpt]h[bdgkpt]|[^aeiouy]{4}", re.I)
    def ease(n):
        plain = re.fullmatch(r"[A-Za-z]+", n)
        count = modern.get(fold(n), 0)
        if not re.fullmatch(r"[A-Za-zÄÖÜäöüß]+", n) or OLD.search(n) or len(n) > 11 or count == 0: return 3
        if plain and len(n) <= 8 and count >= 100: return 1
        return 2

    PHRASE = {"German": "German", "Frankish": "Frankish", "Gothic": "Gothic", "Lombard": "Lombard", "Alemannic": "Alemannic", "Bavarian": "Bavarian"}
    out = []
    for r in sorted(rows.values(), key=lambda r: (fold(r["name"]), r["culture"])):
        gs = r["g"]
        g = "e" if "e" in gs or len(gs) > 1 else next(iter(gs))
        lang = r["language"]
        head = f"{an(lang)} {lang} name" if lang != r["culture"] else f"{an(r['culture'])} {r['culture']} name"
        if r["culture"] not in lang and lang not in ("Old High German", "Middle High German", "Early New High German", "Old Frankish", "Lombardic"):
            head += f" ({r['culture']})"
        src = head + (f", from {r['origin']}" if r["origin"] and fold(r["origin"].split(",")[0].split(" ")[-1]) != fold(r["name"]) else "") + "."
        if r["native"]: src += f" Written {r['native']}."
        src += "".join(" " + n for n in r["notes"][:4])
        also = ["Germanic"] if r["germanic"] else []
        if re.match(r"^[A-Z][a-z]+, ", r["meaning"]): r["meaning"] = ""        # a gloss that only names a figure ("Gabriel, an archangel…")
        out.append([r["name"], g, r["culture"], lang, "", r["meaning"][:80], src, ",".join(r["texts"]), "real", also, ease(r["name"])])
    # a name in several cultures: the other cultures go in "also" too
    by_name = collections.defaultdict(list)
    for row in out: by_name[fold(row[0])].append(row)
    for rs in by_name.values():
        for row in rs:
            row[9] = list(dict.fromkeys(row[9] + [x[2] for x in rs if x[2] != row[2]]))
    out.sort(key=lambda r: (r[10], fold(r[0]), r[2]))
    with open(OUT, "w", encoding="utf-8") as f: json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

    # report
    site = site_names()
    names = {fold(r[0]) for r in out}
    print(f"{len(out):,} rows, {len(names):,} distinct names → {os.path.relpath(OUT, ROOT)} ({os.path.getsize(OUT) // 1024} KB); "
          f"{sum(1 for r in out if r[5]):,} with a meaning; {len(names - site):,} names new to the site")
    for c, n in collections.Counter(r[2] for r in out).most_common(): print(f"  {c}: {n:,}")
    print("  by language:", dict(collections.Counter(r[3] for r in out).most_common()))
    print("  new by culture:", dict(collections.Counter(r[2] for r in out if fold(r[0]) not in site)))
    print("  literature:", {k: lit_stats[k] for k in WORKS})
    print("  ", dict(stats))
    print("  literature skipped:", {f"{k[0]}:{k[1]}": v for k, v in lit_stats.items() if isinstance(k, tuple)})
