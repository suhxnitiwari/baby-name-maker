# Given names of characters in public-domain Iberian literature (Castilian, Catalan, Galician), each attested by work and
# passage, for later merging into the Spanish name data.
#
# Reads / caches (downloads only what is missing, one request at a time, >= 1 s apart, maxlag=5 on Wikimedia):
#   raw/spanish/lit/pg/<id>.txt           Project Gutenberg plain-text UTF-8 editions (public domain in the US; PG licence)
#   raw/spanish/lit/ws/<lang>/<title>.html Wikisource pages via the MediaWiki parse API (public-domain texts; CC BY-SA site)
#   raw/spanish/lit/ws/ca-tirant-pages.json  list of Tirant lo Blanch (1905) chapter pages on ca.wikisource
#   raw/spanish/lit/wikidata-characters.json  Wikidata (CC0): characters of each work (P1441 / P674), given name, sex
# Writes:
#   raw/spanish/lit-attestations.tsv
#     name sex sex_evidence language work author year passage snippet occurrences source_url method
#
# Methods: dramatis (personae list of a play, Celestina's interlocutor lines), honorific (capitalised word after
# don/doña/fray/rey/...), wikidata (character of the work, given name confirmed in the text), title (name in the title),
# mustcheck (fixed list of names searched in every text, kept only with person evidence). Sex only from honorifics,
# dramatis descriptions or Wikidata P21; blank otherwise. Names are kept exactly as printed.
#
#   python3 scripts/fetch_spanish_literature.py
import html, json, os, re, sys, time, unicodedata, urllib.parse, urllib.request
from html.parser import HTMLParser
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
CACHE = os.path.join(ROOT, "raw", "spanish", "lit"); OUT = os.path.join(ROOT, "raw", "spanish", "lit-attestations.tsv")
UA = {"User-Agent": "Lullabyte/1.0 (https://github.com/suhxnitiwari/baby-name-maker; suhxnitiwari@gmail.com)"}
LAST = [0.0]

def get(url, data=None):
    for attempt in range(5):
        wait = 1.2 - (time.time() - LAST[0])
        if wait > 0: time.sleep(wait)
        try:
            req = urllib.request.Request(url, data=data, headers=UA)
            with urllib.request.urlopen(req, timeout=120) as r: body = r.read().decode("utf-8")
            LAST[0] = time.time()
            if '"code":"maxlag"' in body or '"code": "maxlag"' in body: raise IOError("maxlag")
            return body
        except Exception as e:
            LAST[0] = time.time(); print(f"  {url[:90]}: {e}; retrying", file=sys.stderr); time.sleep(5 * (attempt + 1))
    raise SystemExit("giving up on " + url)

def cached(path, url, data=None):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True); print("  fetch", url[:100], file=sys.stderr)
        body = get(url, data)
        with open(path, "w", encoding="utf-8") as f: f.write(body)
    with open(path, encoding="utf-8") as f: return f.read()

# ---------------------------------------------------------------- sources
def pg(n):
    t = cached(os.path.join(CACHE, "pg", f"{n}.txt"), f"https://www.gutenberg.org/cache/epub/{n}/pg{n}.txt").replace("\r\n", "\n")
    a = re.search(r"^\*\*\* ?START OF.*$", t, re.M); b = re.search(r"^\*\*\* ?END OF", t, re.M)
    return t[a.end() if a else 0:b.start() if b else len(t)]

def wsapi(lang): return f"https://{lang}.wikisource.org/w/api.php"
def safe(t): return re.sub(r'[/\\:*?"<>|]', "_", t)

class Text(HTMLParser):
    SKIP = ("pagenum", "reference", "mw-editsection", "noprint", "ws-noexport", "mw-cite-backlink", "ws-pagenum", "mw-references-wrap")
    BLOCK = {"p", "br", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "dd", "dt", "table", "poem"}
    VOID = {"br", "img", "hr", "meta", "link", "input", "wbr", "source", "col"}
    def __init__(s): super().__init__(); s.out = []; s.stack = []
    def handle_starttag(s, tag, attrs):
        if tag in s.VOID:
            if tag == "br" and not any(s.stack): s.out.append("\n")
            return
        cls = dict(attrs).get("class") or ""
        s.stack.append(tag in ("style", "script", "sup") and "reference" in cls or tag in ("style", "script") or any(k in cls for k in s.SKIP))
        if tag in s.BLOCK and not any(s.stack): s.out.append("\n")
    def handle_endtag(s, tag):
        if tag in s.VOID: return
        if s.stack: s.stack.pop()
        if tag in s.BLOCK and not any(s.stack): s.out.append("\n")
    def handle_data(s, d):
        if not any(s.stack): s.out.append(d)

def ws(lang, title):
    p = os.path.join(CACHE, "ws", lang, safe(title) + ".html")
    q = urllib.parse.urlencode({"action": "parse", "page": title, "prop": "text", "format": "json", "formatversion": 2,
                                "redirects": 1, "disablelimitreport": 1, "maxlag": 5})
    body = cached(p, wsapi(lang) + "?" + q)
    d = json.loads(body)
    if "error" in d: raise SystemExit(f"{lang}.wikisource {title}: {d['error']}")
    x = Text(); x.feed(d["parse"]["text"])
    t = re.sub(r"[ \t\xa0]+", " ", "".join(x.out)); return re.sub(r"\n\s*\n+", "\n\n", t)

def ws_url(lang, title): return f"https://{lang}.wikisource.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))

def tirant_pages():
    p = os.path.join(CACHE, "ws", "ca-tirant-pages.json")
    if not os.path.exists(p):
        titles, cont = [], {}
        while True:
            q = {"action": "query", "list": "allpages", "apprefix": "Tirant lo Blanch (1905)/", "aplimit": 500, "format": "json", "maxlag": 5, **cont}
            d = json.loads(get(wsapi("ca") + "?" + urllib.parse.urlencode(q)))
            titles += [x["title"] for x in d["query"]["allpages"]]
            if "continue" not in d: break
            cont = d["continue"]
        os.makedirs(os.path.dirname(p), exist_ok=True); json.dump(titles, open(p, "w"), ensure_ascii=False)
    ch = [t for t in json.load(open(p)) if re.search(r"/\d/Capítol \d+$", t)]
    return sorted(ch, key=lambda t: int(t.rsplit(" ", 1)[1]))

# ---------------------------------------------------------------- works
# src: ("pg", id, start_re, end_re) or ("ws", lang, [(label, title), ...]); heads: [(key, regex, label)] applied per line
# (label may use {0} for group 1; a key resets the keys after it); dram: (start_re, end_re) inside the work text, or
# ("ws", title) for a Wikisource cast page, or "caps" for Celestina-style interlocutor lines.
CEL = ["Aucto primero", "El segundo aucto", "El tercer aucto", "El aucto quarto", "El aucto quinto", "El aucto sesto",
       "El sétimo aucto", "El octavo aucto", "El aucto noveno", "El décimo aucto", "El aucto onzeno", "El aucto dozeno",
       "Aucto trezeno", "Aucto quatorzeno", "Aucto dézimoquinto", "Aucto décimo sesto", "Aucto décimo séptimo",
       "Aucto décimo octavo", "Aucto décimonono", "El veyteno aucto", "Veynte e un aucto"]
NOV = [("La gitanilla", r"^LA JITANILLA\.$", "Q555967"), ("El amante liberal", r"^EL AMANTE LIBERAL\.$", "Q558212"),
       ("Rinconete y Cortadillo", r"^RINCONETE Y CORTADILLO\.$", "Q556786"), ("La española inglesa", r"^LA ESPAÑOLA INGLESA\.$", "Q559540"),
       ("El licenciado Vidriera", r"^EL LICENCIADO VIDRIERA\.$", "Q576188"), ("La fuerza de la sangre", r"^LA FUERZA DE LA SANGRE\.$", "Q554508"),
       ("El celoso extremeño", r"^EL CELOSO ESTREMEÑO\.$", "Q554472"), ("La ilustre fregona", r"^LA ILUSTRE FREGONA\.$", "Q596079"),
       ("Las dos doncellas", r"^LAS DOS DONCELLAS\.$", "Q580406"), ("La señora Cornelia", r"^LA SEÑORA CORNELIA\.$", "Q609506"),
       ("El casamiento engañoso", r"^EL CASAMIENTO ENGAÑOSO\.$", "Q10271189"), ("El coloquio de los perros", r"^COLOQUIO QUE PASO ENTRE CIPION", "Q554504")]
GALDOS_CH = [("ch", r"^\s*-+([IVXLC]+)-+\s*$", "ch. {0}")]
ACTS = [("act", r"^\s*ACTO (PRIMERO|SEGUNDO|TERCERO)", "Acto {0}")]
W = [
    # Sánchez 1779 edition; es.wikisource has only vv. 1-294 and 3715-3744 transcribed (the other scan pages are empty)
    dict(t="Cantar de mio Cid", a="Anónimo", y="c. 1200", l="Spanish", kind="verse", qid="Q320713",
         src=("ws", "es", [("", "Colección de poesías castellanas anteriores al siglo XV/Tomo I/Poema del Cid")], r"^1 De los sos oios", r"^NOTA\.$"),
         heads=[("v", r"^\s*(\d{1,4}) ", "v. {0}")]),
    dict(t="Romancero selecto del Cid", a="Anónimo (ed. Manuel Milá y Fontanals)", y="15th-16th c.", l="Spanish", kind="verse",
         src=("pg", 57648, r"^PARTE PRIMERA$", r"^ÍNDICE"),
         heads=[("part", r"^PARTE (PRIMERA|SEGUNDA|TERCERA|CUARTA|QUINTA|SEXTA)$", "Parte {0}"), ("rom", r"^([IVXLC]+)$", "romance {0}")]),
    dict(t="Libro de buen amor", a="Juan Ruiz, Arcipreste de Hita", y="1330", l="Spanish", kind="verse", qid="Q2283127",
         src=("pg", 16625, r"^\s*\[1\] Señor Dios, que", r"^FIN DEL TOMO SEGUNDO|^ÍNDICE DE VOCES|^Indice de voces"),
         heads=[("st", r"^\s*\[(\d+)\]", "stanza {0}")]),
    # Gutenberg #1619 is a copyrighted 1998 edition, so the Cejador 1913 edition on es.wikisource is used instead
    dict(t="La Celestina", a="Fernando de Rojas", y="1499", l="Spanish", kind="prose", qid="Q583705", dram="caps", title=["Celestina"],
         src=("ws", "es", [(f"auto {i + 1}", "La Celestina (1913)/" + a) for i, a in enumerate(CEL)])),
    dict(t="Tirant lo Blanc", a="Joanot Martorell", y="1490", l="Catalan", kind="prose", qid="Q559667", src=("tirant",), title=["Tirant"]),
    dict(t="Lazarillo de Tormes", a="Anónimo", y="1554", l="Spanish", kind="prose", qid="Q770895",
         src=("pg", 320, r"^Prólogo$", None), heads=[("tr", r"^(Prólogo|Tratado \w+)$", "{0}")], title=["Lazarillo"]),
    dict(t="Don Quijote, Part I", a="Miguel de Cervantes", y="1605", l="Spanish", kind="prose", qid="Q480",
         src=("pg", 2000, r"^Capítulo primero\. Que trata de la condición", r"^Segunda parte del ingenioso caballero"),
         heads=[("ch", r"^Capítulo (\w+)\.", "Part I, ch. {0}")]),
    dict(t="Don Quijote, Part II", a="Miguel de Cervantes", y="1615", l="Spanish", kind="prose", qid="Q480",
         src=("pg", 2000, r"^Capítulo Primero\. De lo que el cura y el barbero", None),
         heads=[("ch", r"^Capítulo (\w+)\.", "Part II, ch. {0}")]),
] + [dict(t=t, a="Miguel de Cervantes", y="1613", l="Spanish", kind="prose", qid=q, novela=True,
          src=("pg", 61202, s, NOV[i + 1][1] if i + 1 < len(NOV) else r"^LA TIA FINGIDA\.$"))
     for i, (t, s, q) in enumerate(NOV)] + [
    dict(t="Fuenteovejuna", a="Lope de Vega", y="1619", l="Spanish", kind="play", qid="Q2608537",
         src=("pg", 60198, r"^Hablan en ella las personas", None), heads=ACTS, dram=(r"^Hablan en ella", r"^\s*ACTO PRIMERO")),
    dict(t="El perro del hortelano", a="Lope de Vega", y="1618", l="Spanish", kind="play", qid="Q17195711",
         src=("ws", "es", [(f"Acto {a}", f"El perro del hortelano/Acto {a}") for a in ("I", "II", "III")]), dram=("ws", "El perro del hortelano/Personas")),
    dict(t="El caballero de Olmedo", a="Lope de Vega", y="c. 1620", l="Spanish", kind="play", qid="Q5824114",
         src=("ws", "es", [(f"Acto {a}", f"El caballero de Olmedo/Acto {a}") for a in ("I", "II", "III")]), dram=("ws", "El caballero de Olmedo")),
    dict(t="Peribáñez y el comendador de Ocaña", a="Lope de Vega", y="1614", l="Spanish", kind="play", qid="Q3847742",
         src=("ws", "es", [(f"Acto {a}", f"Peribáñez y el comendador de Ocaña/Acto {a}") for a in ("I", "II", "III")]),
         dram=("ws", "Peribáñez y el comendador de Ocaña/Personas")),
    dict(t="La vida es sueño", a="Pedro Calderón de la Barca", y="1635", l="Spanish", kind="play", qid="Q138174",
         src=("pg", 54436, r"^LA VIDA ES SUEÑO\.$", r"^LA DEVOCION DE LA CRUZ\.$"),
         heads=[("j", r"^JORNADA (\w+)\.$", "Jornada {0}")], dram=(r"^PERSONAS\.$", r"^La escena es")),
    dict(t="El burlador de Sevilla", a="Tirso de Molina", y="1630", l="Spanish", kind="play", qid="Q2714218",
         src=("ws", "es", [(f"Acto {a}", f"El burlador de Sevilla/Acto {a}") for a in ("I", "II", "III")]), dram=("ws", "El burlador de Sevilla/Elenco")),
    dict(t="Leyendas", a="Gustavo Adolfo Bécquer", y="1858-1864", l="Spanish", kind="prose",
         src=("pg", 53552, r"^MAESE PÉREZ EL ORGANISTA$", r"^DESDE MI CELDA$"),
         heads=[("ley", r"^(MAESE PÉREZ EL ORGANISTA|LOS OJOS VERDES|EL RAYO DE LUNA|TRES FECHAS|LA CORZA BLANCA|LA ROSA DE PASIÓN|LA PROMESA"
                 r"|EL MONTE DE LAS ÁNIMAS|EL GNOMO|EL MISERERE|LAS HOJAS SECAS|LA VENTA DE LOS GATOS)$", "{0}")]),
    dict(t="Doña Perfecta", a="Benito Pérez Galdós", y="1876", l="Spanish", kind="prose", qid="Q476558", title=["Perfecta"],
         src=("pg", 15725, r"^\s*=Villahorrenda", r"^\s*NOTES\s*$"), heads=[("ch", r"^\s{10,}([IVXLC]+)\s*$", "ch. {0}")]),
    dict(t="Fortunata y Jacinta", a="Benito Pérez Galdós", y="1887", l="Spanish", kind="prose", qid="Q3815979", title=["Fortunata", "Jacinta"],
         src=("pg", 17013, r"^Parte primera$", None),
         heads=[("part", r"^Parte (primera|segunda|tercera|cuarta)$", "Parte {0}"), ("ch", r"^\s*-+([IVXLC]+)-+\s*$", "ch. {0}")]),
    dict(t="Marianela", a="Benito Pérez Galdós", y="1878", l="Spanish", kind="prose", qid="Q6762098", title=["Marianela"],
         src=("pg", 17340, r"^\s*-+I-+\s*$", None), heads=GALDOS_CH),
    dict(t="Misericordia", a="Benito Pérez Galdós", y="1897", l="Spanish", kind="prose", qid="Q5836705",
         src=("pg", 21831, r"^I$", None), heads=[("ch", r"^([IVXLC]+)$", "ch. {0}")]),
    dict(t="Trafalgar", a="Benito Pérez Galdós", y="1873", l="Spanish", kind="prose", qid="Q3997228",
         src=("pg", 16961, r"^\s*-+I-+\s*$", None), heads=GALDOS_CH),
    dict(t="La Regenta", a="Leopoldo Alas (Clarín)", y="1884", l="Spanish", kind="prose", qid="Q1784466",
         src=("pg", 17073, r"^\s*-+I-+\s*$", None), heads=[("ch", r"^\s*-+([IVXLC]+)-+\s*$", "ch. {0}")]),
    dict(t="Cantares gallegos", a="Rosalía de Castro", y="1863", l="Galician", kind="verse", qid="Q3311871",
         src=("pg", 59037, r"^PRÓLOGO$", r"^ÍNDICE$")),
    dict(t="Follas novas", a="Rosalía de Castro", y="1880", l="Galician", kind="verse", qid="Q3310994",
         src=("pg", 65703, r"^DUAS PALABRAS D’A AUTORA$", r"^\s*ÍNDICE\.?\s*$")),
]
NOT_FOUND = ["Romancero viejo (es.wikisource 'El romancero viejo' is flagged as a copyrighted modern edition; used Romancero selecto del Cid instead)",
             "Amadís de Gaula (es.wikisource has only the prologue; not on Gutenberg)", "Palmerín de Oliva", "Tirante el Blanco (Castilian translation)"]

def drop_notes(t):
    t = re.sub(r"(?ms)^\[(Nota|Footnote|Ilustración|Illustration)\b.*?(?=\n\s*\n)", "", t)   # bracketed notes, illustrations
    return re.sub(r"(?m)^\s*\d{1,3}\s*$", "", t)                                            # printed page numbers

def load(w):
    """-> (text, [(label, start_offset)], source_url)"""
    s = w["src"]
    if s[0] == "pg":
        t = pg(s[1])
        if s[2]:
            m = re.search(s[2], t, re.M); t = t[m.start():]
        if s[3]:
            m = re.search(s[3], t[200:], re.M)
            if m: t = t[:200 + m.start()]
        return drop_notes(t), None, f"https://www.gutenberg.org/ebooks/{s[1]}"
    if s[0] == "ws":
        parts, secs, off = [], [], 0
        for label, title in s[2]:
            x = ws(s[1], title); secs.append((label, off)); parts.append(x); off += len(x) + 2
        t = re.sub(r"Página:[^\n]*?1779\.djvu/\d+", "", "\n\n".join(parts))
        if len(s) > 3:   # slice start / end like the Gutenberg texts
            m = re.search(s[3], t, re.M); t = t[m.start():]
            m = re.search(s[4], t, re.M); t = t[:m.start()] if m else t
        return t, secs if s[2][0][0] else None, ws_url(s[1], s[2][0][1].split("/Acto")[0])
    if s[0] == "tirant":
        parts, secs, off = [], [], 0
        for title in tirant_pages():
            x = ws("ca", title); secs.append(("cap. " + title.rsplit(" ", 1)[1], off)); parts.append(x); off += len(x) + 2
        return "\n\n".join(parts), secs, ws_url("ca", "Tirant lo Blanch (1905)")

def sections(w, t, secs):
    if secs is not None: return secs
    heads, out, state = w.get("heads") or [], [("", 0)], {}
    keys = [k for k, _, _ in heads]
    pos = 0
    for line in t.split("\n"):
        for i, (k, rx, fmt) in enumerate(heads):
            m = re.match(rx, line)
            if m:
                state[k] = fmt.format(*m.groups()) if m.groups() else fmt
                for k2 in keys[i + 1:]: state.pop(k2, None)
                out.append((", ".join(state[x] for x in keys if x in state), pos)); break
        pos += len(line) + 1
    return out

def where(secs, i, t=None):
    if len(secs) == 1 and t is not None: return "para. %d" % (len(re.findall(r"\n\s*\n", t[:i])) + 1)
    lab = ""
    for l, o in secs:
        if o > i: break
        lab = l
    return lab

def snippet(t, i, j):
    a = " ".join(t[max(0, i - 120):i].split()[-7:]); b = " ".join(t[j:j + 120].split()[:7])
    return re.sub(r"\s+", " ", f"{a} {t[i:j]} {b}").strip().replace("\t", " ")

def fold(s): return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c)).lower()

# ---------------------------------------------------------------- extraction
M_HON = "don señor fray maese micer mosén mosen infante rey conde tío tio siñor duque marqués príncipe mossèn senyor rei comte duc".split()
F_HON = "doña dona señora sor infanta reina condesa doncella tía tia siñora duquesa marquesa princesa na senyora comtessa donzella duquessa".split()
HON = {h: "b" for h in M_HON} | {h: "g" for h in F_HON}
CAT_ONLY = {"mossèn", "senyor", "senyora", "rei", "comte", "comtessa", "donzella", "duquessa", "na", "duc"}
ABBR = {"D.": "b", "D.ª": "g", "Dª": "g", "Dña.": "g", "D.a": "g"}
UP, LO = "A-ZÁÉÍÓÚÑÜÀÈÒÏÇ", "a-záéíóúñüàèòïç"
RX_HON = re.compile(r"(?<![\w.])(" + "|".join(sorted(map(re.escape, list(HON) + [h.capitalize() for h in HON]), key=len, reverse=True))
                    + r"|D\.ª|Dª|Dña\.|D\.a|D\.)\s+((?:[" + UP + r"][" + LO + r"]+))(?![\w])")
# Capitalised words that follow an honorific but are not given names: titles, roles, holy names, epithets, adjectives.
STOP = set("""Dios Santa Santo San Sant Nuestra Nuestro Señor Señora Jesucristo Cristo Jesús Virgen Don Doña Dona Fray Rey Reina
Conde Condesa Duque Duquesa Marqués Marquesa Príncipe Princesa Infante Infanta Licenciado Bachiller Maestro Maese Capitán Cura
Barbero Caballero Alcalde Comendador Gobernador Obispo Arzobispo Doctor Padre Madre Tío Tía Abad Canónigo Cardenal Emperador
Emperatriz Almirante Gran Grande Católico Católica Moro Mora Cristiano Cristiana Santísimo Santísima Papa Juez Corregidor Oidor
Magistral Provisor Deán Arcipreste Mayor Mio Mío Mi Vuestra Vuestro Merced Excelencia Ilustrísima Usted Ud Señoría Alteza Majestad
Senyor Senyora Rei Comte Déu Sant Mossèn Na Nostre Nostra Verge Emperadriu Emperador Duc Gloriós Beneyt El La Los Las Lo Le Les Un Una
De Del En Y E A O Quijote Quijada Quesada Quijana Panza Carrasco Lozano Mendoza Toboso Mancha Cid Campeador Pérez
Abbat Fulano Carnal Quaresma Cuaresma Almuerço Ceçina Ximio Xymio Rraby Jhesuxristo Melón Polo Aly Venus Júpiter Neptuno Apolo Marte
Cupido Dauid David Acab Ezechías Buenaventura Sobrino Tolosa Molinera Tobosa Quijotes Quijotísimo Bacía Archipiela Paralipomenón
Dolorida Lobuna Zorruna Magallanes Trifaldi Juanes Sanchos Sta Rincon Rincón Vidriera Garnacha Redoma Pipota Contreras Loaysa
Campuzano Peralta Colindres Simueque Pimpinela Clavijo Camacho Gigote Alfeñiquén Quirieleisón Pandahilado Tomillas Fulana Zutano
Mengano Ilustrísimo Excelentísimo Reverendísimo Santiago Cristóbal""".split())
STOP_SURNAME = re.compile(r"^[" + UP + r"][" + LO + r"]+(ez|az|iz|oz)$")   # patronymic surnames: Pérez, Díaz, Muñoz ...
GIVEN_EZ = set()

def honorifics(w, t):
    """-> {name: [count, {b/g: n}, first_match]} from capitalised words after a (Catalan-only where marked) honorific."""
    found = {}
    for m in RX_HON.finditer(t):
        h, nm = m.group(1), m.group(2)
        hl = h.lower()
        sex = ABBR.get(h) or HON.get(hl)
        if hl in CAT_ONLY and w["l"] != "Catalan": continue
        if w["l"] == "Catalan" and hl not in CAT_ONLY and hl not in ("don", "doña", "infanta", "infante", "reina", "rey"): continue
        if nm in STOP or (STOP_SURNAME.match(nm) and nm not in GIVEN_EZ) or len(nm) < 3: continue
        if sex is None: continue
        r = found.setdefault(nm, [0, {}, m, {}]); r[0] += 1; r[1][sex] = r[1].get(sex, 0) + 1; r[3][hl] = r[3].get(hl, 0) + 1
    return found

def count(t, nm):
    return len(re.findall(r"(?<![\w])(" + re.escape(nm) + "|" + re.escape(nm.upper()) + r")(?![\w])", t))

def lower_share(t, nm):
    lo = len(re.findall(r"(?<![\w])" + re.escape(nm.lower()) + r"(?![\w])", t))
    return lo / max(1, count(t, nm))

ROLE = set(fold(x) for x in """rey reina duque duquesa marques marquesa conde condesa principe princesa infante infanta condestable
comendador maestre regidor alcalde alcaldes juez musica muchacho muchachos labrador labradores labradora villano villana villanos
criado criados criada criadas soldado soldados sombra cantores guardas enlutados musicos pastores pescadores acompanamiento gente
gracioso viejo dama damas caballero caballeros escudero paje pajes secretario mayordomo capitan sargento page""".split())
FEM_DESC = re.compile(r"\b(dama|criada|labradora|villana|pescadora|duquesa|infanta|reina|hija|madre|viuda|mujer|moza|esposa|"
                      r"condesa|marquesa|princesa|doncella|dueña|tía|hermana|sobrina|señora|esclava|mora|gitana|vieja)\b", re.I)
MASC_DESC = re.compile(r"\b(criado|galán|viejo|labrador|lacayo|rey|príncipe|duque|pescador|gracioso|padre|hijo|alcalde|alcaldes|"
                       r"comendador|soldado|pastor|escudero|caballero|marqués|conde|hermano|tío|sobrino|señor|paje|esclavo|moro|"
                       r"capitán|secretario|mayordomo|villano|maestre|regidor|infante|duque)\b", re.I)

def dramatis(w, t):
    """-> [(name, sex, evidence, line)]"""
    d = w.get("dram")
    if not d: return []
    if d == "caps":   # Celestina: lines listing the speakers of each auto, e.g. "CALISTO.  MELIBEA.  SEMPRONIO."
        out, seen = [], set()
        for line in t.split("\n"):
            if re.fullmatch(r"\s*[A-ZÁÉÍÓÚÑ]{3,}(?:[.,]\s*[A-ZÁÉÍÓÚÑ]{3,})+\.?\s*", line):
                for nm in re.findall(r"[A-ZÁÉÍÓÚÑ]{3,}", line):
                    n = nm.capitalize()
                    if n not in seen: seen.add(n); out.append((n, "", "", line.strip()))
        return out
    if d[0] == "ws": block = ws("es", d[1])
    else:
        a = re.search(d[0], t, re.M); b = re.search(d[1], t[a.end():], re.M); block = t[a.end():a.end() + b.start()]
    out = []
    for line in block.split("\n"):
        line = re.sub(r"^[\s*•·]+", "", line).strip().rstrip(".")
        if not line or len(line) > 80: continue
        caps = re.findall(r"\b[A-ZÁÉÍÓÚÑ]{2,}\b", re.sub(r"_[^_]*_|\[|\]", " ", line))
        if len([c for c in caps if len(c) > 2]) and re.search(r"[A-ZÁÉÍÓÚÑ]{3,}", line) and not re.search(r"[a-z]{3,}", re.sub(r"_[^_]*_", "", line).replace("[", "").replace("]", "")):
            # PG style: names in capitals, descriptions in _italics_; "ESTEBAN, ALONSO, _alcaldes._"
            desc = " ".join(re.findall(r"_([^_]*)_", line))
            groups = [g.split() for g in re.sub(r"_[^_]*_|\[|\]", " ", line).split(",")]
            groups = [[x.capitalize() for x in g] for g in groups if g]
        else:   # Wikisource style: "Don Diego Tenorio, viejo"
            nm, _, desc = line.partition(",")
            groups = [nm.split()]
        for g in groups:
            sex, ev = "", ""
            while g and fold(g[0]) in {"el", "la", "un", "una", "algunos", "dos", "don", "dona", "rey", "reina", "duque", "infanta"} | ROLE:
                f = fold(g[0])
                if f in ("don", "rey", "duque"): sex, ev = "b", g[0].lower()
                if f in ("dona", "reina", "infanta"): sex, ev = "g", g[0].lower()
                g = g[1:]
                if f in ROLE and f not in ("rey", "reina", "duque", "infanta"): g = []
            if not g or not g[0][:1].isupper() or fold(g[0]) in ROLE or fold(g[0]) in {"de", "del", "y"}: continue
            n = g[0]
            if not sex and desc:
                if FEM_DESC.search(desc) and not MASC_DESC.search(desc): sex, ev = "g", "dramatis personae: " + desc.strip(" _.")
                elif MASC_DESC.search(desc) and not FEM_DESC.search(desc): sex, ev = "b", "dramatis personae: " + desc.strip(" _.")
            elif sex: ev = "dramatis personae: " + ev
            out.append((n, sex, ev, line))
    return out

MUST = """Jimena Mencía Leonor Elvira Sol Inés Blanca Constanza Violante Berenguela Sancha Urraca Toda Catalina Beatriz Isabel Leonisa
Teodosia Preciosa Melibea Rosaura Estrella Laurencia Dulcinea Areúsa Álvar Alonso Rodrigo Gonzalo Sancho Diego Martín García Amadís
Teodoro Segismundo Tirant Carmesina Estefania Plaerdemavida Diafebus Hipòlit""".split()
VARIANTS = {"Jimena": ["Ximena", "Xiména"], "Inés": ["Ynés", "Ines"], "Isabel": ["Ysabel"], "Álvar": ["Alvar", "Albar"],
            "Beatriz": ["Beatris"], "Areúsa": ["Areusa"], "Mencía": ["Mencia"], "García": ["Garcia"], "Martín": ["Martin"],
            "Hipòlit": ["Ypòlit", "Hipolit", "Ipolit", "Ypolit"], "Estefania": ["Estephania"], "Diafebus": ["Diaphebus"],
            "Carmesina": ["Carmessina"], "Tirant": ["Tyrant"]}
AMBIG = {"Sol", "Estrella", "Blanca", "Toda", "Preciosa", "Urraca"}   # also ordinary words: need an honorific or the cast list

def mid_sentence(t, nm):
    """occurrences of nm not at a line start, not after sentence punctuation, not after San/Santa/Santo"""
    n, first = 0, None
    for m in re.finditer(r"(?<![\w])" + re.escape(nm) + r"(?![\w])", t):
        pre = t[max(0, m.start() - 12):m.start()]
        if re.search(r"(^|\n)[\s\-—«\"'¡¿(]*$", pre) or re.search(r"[.!?¡¿:;—«\"']\s*$", pre) or re.search(r"\b(San|Santa|Santo|Sant)\s+$", pre): continue
        n += 1; first = first or m
    return n, first

def wikidata():
    p = os.path.join(CACHE, "wikidata-characters.json")
    qids = sorted({w["qid"] for w in W if w.get("qid")})
    q = """SELECT ?w ?c ?cl ?gl ?sex WHERE { VALUES ?w { %s } { ?c wdt:P1441 ?w } UNION { ?w wdt:P674 ?c }
      OPTIONAL { ?c rdfs:label ?cl FILTER(LANG(?cl) IN ("es","ca","gl")) }
      OPTIONAL { ?c wdt:P735 ?g . ?g rdfs:label ?gl FILTER(LANG(?gl) IN ("es","ca","gl","mul")) }
      OPTIONAL { ?c wdt:P21 ?sex } }""" % " ".join("wd:" + x for x in qids)
    body = cached(p, "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"}))
    out = {}
    for b in json.loads(body)["results"]["bindings"]:
        w, c = b["w"]["value"].rsplit("/", 1)[1], b["c"]["value"].rsplit("/", 1)[1]
        r = out.setdefault(w, {}).setdefault(c, {"labels": set(), "given": set(), "sex": set()})
        if "cl" in b: r["labels"].add(b["cl"]["value"])
        if "gl" in b: r["given"].add(b["gl"]["value"])
        if "sex" in b: r["sex"].add(b["sex"]["value"].rsplit("/", 1)[1])
    return out

SEXQ = {"Q6581097": "b", "Q6581072": "g"}
COLS = "name sex sex_evidence language work author year passage snippet occurrences source_url method".split()
PRIO = ["dramatis", "title", "honorific", "wikidata", "mustcheck"]

def main():
    wd = wikidata()
    rows, report = {}, []
    for w in W:
        t, secs, url = load(w)
        secs = sections(w, t, secs)
        recs = {}   # fold(name) -> dict
        def add(name, method, sex, ev, i, j, passage=None, snip=None):
            k = fold(name)
            r = recs.setdefault(k, {"forms": {}, "methods": [], "sexes": {}, "ev": [], "passage": None, "snippet": None})
            r["forms"][name] = count(t, name); r["methods"].append(method)
            if sex: r["sexes"][sex] = r["sexes"].get(sex, 0) + 1; r["ev"].append(ev)
            if r["passage"] is None or PRIO.index(method) < PRIO.index(r["methods"][0]):
                r["passage"] = passage if passage is not None else where(secs, i, t)
                r["snippet"] = snip if snip is not None else snippet(t, i, j)
        cast = dramatis(w, t)
        castnames = set()
        for n, sex, ev, line in cast:
            if count(t, n) == 0 and w.get("dram") != "caps": continue
            castnames.add(fold(n))
            if w.get("dram") == "caps":
                m = re.search(r"(?<![\w])" + re.escape(n.upper()) + r"(?![\w])", t)
                add(n, "dramatis", sex, ev, m.start(), m.end(), where(secs, m.start()) + " (interlocutores)" if where(secs, m.start()) else "interlocutores", line)
            else: add(n, "dramatis", sex, ev, 0, 0, "Dramatis personae", line[:120])
        for n in w.get("title", []):
            m = re.search(r"(?<![\w])" + re.escape(n) + r"(?![\w])", t)
            if m: add(n, "title", "", "", m.start(), m.end())
        if w["kind"] != "play":
            for n, (c, sx, m, hs) in honorifics(w, t).items():
                if lower_share(t, n) > 0.5: continue           # "rey Moro", "señora Duquesa": ordinary words
                sex = max(sx, key=sx.get) if max(sx.values()) >= 0.9 * sum(sx.values()) else ""
                ev = ", ".join(f"{h} x{k}" for h, k in sorted(hs.items(), key=lambda x: -x[1]))
                add(n, "honorific", sex, ev if sex else "", m.start(2), m.end(2))
        for c, r in wd.get(w.get("qid"), {}).items():
            cands = sorted(r["given"]) or sorted({re.sub(r"^(Don|Doña|Dona|Fray|Sor|Maese|Mossèn|Rey|Reina|El|La|Lo)\s+", "", l).split()[0] for l in r["labels"] if l.split()})
            sex = "".join(SEXQ.get(s, "") for s in r["sex"])
            for n in cands:
                n = n.strip(",")
                if n in STOP: continue
                m = re.search(r"(?<![\w])" + re.escape(n) + r"(?![\w])", t)
                if not m:   # same name printed with other accents
                    m2 = next((x for x in re.finditer(r"(?<![\w])[" + UP + r"][" + LO + r"]+", t) if fold(x.group()) == fold(n)), None) if len(n) > 2 else None
                    if not m2: continue
                    m, n = m2, m2.group()
                add(n, "wikidata", sex if len(sex) == 1 else "", f"Wikidata {c} P21 {'male' if sex == 'b' else 'female'}" if len(sex) == 1 else "", m.start(), m.end())
        hon = honorifics(w, t)
        for base in MUST:
            for form in [base] + VARIANTS.get(base, []):
                if count(t, form) == 0: continue
                k = fold(form)
                if form in hon:
                    c, sx, m, hs = hon[form]
                    sex = max(sx, key=sx.get) if max(sx.values()) >= 0.9 * sum(sx.values()) else ""
                    ev = ", ".join(f"{h} x{n}" for h, n in hs.items())
                    add(form, "mustcheck", sex, ev if sex else "", m.start(2), m.end(2))
                    if base in AMBIG: recs[k]["forms"][form] = c
                elif k in castnames: pass
                elif base not in AMBIG:
                    n, m = mid_sentence(t, form)
                    if n >= 2: add(form, "mustcheck", "", "", m.start(), m.end())
                if k in recs: recs[k].setdefault("must", base)
        for k, r in recs.items():
            name = max(r["forms"], key=r["forms"].get)
            if name.isupper(): name = name.capitalize()
            sexes = r["sexes"]; sex = next(iter(sexes)) if len(sexes) == 1 else ""
            ev = "; ".join(dict.fromkeys(e for e in r["ev"] if e)) if sex else ("conflicting: " + "; ".join(r["ev"]) if len(sexes) > 1 else "")
            occ = sum(r["forms"].values()) if not (w["kind"] == "play" or w.get("dram") == "caps") else count(t, name)
            if r.get("must") in AMBIG and "dramatis" not in r["methods"]: occ = r["forms"][name]
            rows[(name, w["t"])] = dict(name=name, sex=sex, sex_evidence=ev, language=w["l"], work=w["t"], author=w["a"], year=w["y"],
                                        passage=r["passage"], snippet=r["snippet"], occurrences=occ, source_url=url,
                                        method=sorted(r["methods"], key=PRIO.index)[0], must=r.get("must"))
        report.append((w["t"], url, sum(1 for k in rows if k[1] == w["t"])))
        print(f"{w['t']:40} {len(t):>9} chars {len(secs):>4} sections {report[-1][2]:>4} names", file=sys.stderr)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\t".join(COLS) + "\n")
        for r in sorted(rows.values(), key=lambda r: ([x["t"] for x in W].index(r["work"]), fold(r["name"]))):
            f.write("\t".join(str(r[c]).replace("\t", " ").replace("\n", " ") for c in COLS) + "\n")
    print(f"{len(rows)} rows, {len({fold(r['name']) for r in rows.values()})} distinct names -> {OUT}", file=sys.stderr)
    for base in MUST:
        hits = [(r["name"], r["work"], r["passage"]) for r in rows.values() if r.get("must") == base]
        print(f"  {base:14} " + ("; ".join(f"{n} in {w} ({p})" for n, w, p in hits) if hits else "NOT FOUND"), file=sys.stderr)
    print("Not available: " + "; ".join(NOT_FOUND), file=sys.stderr)

if __name__ == "__main__":
    main()
