# Official given-name lists for Spain's regional languages, normalised to TSV for later merging.
#
#   python3 scripts/fetch_spanish_regional.py [eu] [gl] [ca] [ast] [an]     (no args = all)
#
# Every download is cached under raw/spanish/ (eu-, gl-, ca-, ast-, an- prefixes); a rerun only fetches what is missing.
# Requests are made one at a time with a pause between them and an honest User-Agent.
# Output: raw/spanish/<prefix>-<short>.tsv with columns
#   name  sex(b/g/e/empty)  meaning  equivalents  count  source_url  note
# and a "# " comment line on top naming the source, publisher, URL, access date and the terms found.
#
# Sources (see each TSV's header line for the terms quoted):
#   eu  Euskaltzaindia (Royal Academy of the Basque Language), EODA "Pertsona-izenak" database,
#       https://www.euskaltzaindia.eus/index.php?option=com_ecoeoda&task=izenaPortada&Itemid=469&lang=eu
#       Search listing pages (10 names per page) crawled per sex x "arautzea" (normative status); these pages print the
#       name, sex, Spanish/French/... equivalents and the Basque explanation. No open licence stated.
#   (further sources are added below as they are found)
import html, os, re, sys, time, urllib.parse, urllib.request
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "raw", "spanish")
UA = "Lullabyte/1.0 (https://github.com/suhxnitiwari/baby-name-maker; suhxnitiwari@gmail.com)"
PAUSE = 1.5
COLS = ["name", "sex", "meaning", "equivalents", "count", "source_url", "note"]


def fetch(url, cache, binary=False, data=None):
    """GET (or POST data) url once, caching the body at raw/spanish/<cache>."""
    p = os.path.join(OUT, cache)
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": UA}, data=data)
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=120) as r: body = r.read()
                break
            except urllib.error.HTTPError as e:
                if e.code in (401, 403, 429): raise SystemExit(f"blocked ({e.code}) at {url}; not retrying")
                print(f"  {e} on {url}; retrying", flush=True); time.sleep(10 * (attempt + 1))
            except Exception as e:
                print(f"  {e} on {url}; retrying", flush=True); time.sleep(10 * (attempt + 1))
        else: raise SystemExit(f"failed: {url}")
        open(p, "wb").write(body)
        time.sleep(PAUSE)
    b = open(p, "rb").read()
    return b if binary else b.decode("utf-8", errors="replace")


def clean(s):
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def write_tsv(short, header, rows):
    p = os.path.join(OUT, short + ".tsv")
    with open(p, "w", encoding="utf-8") as f:
        f.write("# " + header.replace("\n", " ") + "\n")
        f.write("\t".join(COLS) + "\n")
        for r in rows:
            f.write("\t".join(str(r.get(c, "") or "").replace("\t", " ").replace("\n", " ") for c in COLS) + "\n")
    print(f"  wrote {p}: {len(rows)} rows", flush=True)


# ---------------------------------------------------------------- Basque: Euskaltzaindia EODA
EU_BASE = ("https://www.euskaltzaindia.eus/index.php?option=com_ecoeoda&Itemid=469&task=bilaketa&view=bilaketa"
           "&lang=eu&query=%2A%3A%2A&mota=izenak&ordena=score")
EU_SEX = {"1": "g", "2": "b", "3": "e"}           # emakumezkoa / gizonezkoa / epizenoa
EU_STATUS = {"10": "Euskaltzaindiaren araua", "3": "ikerlari baten arautze proposamena",
             "4": "oinarri sendoko arautze proposamena", "5": "batzordeak ontzat emandako arautze proposamena",
             "6": "batzordearen beraren arautze proposamena", "7": "batzordearen argitalpena"}


def eu_pages(facets, tag):
    """Yield every listing page for the given facet query string."""
    first = fetch(EU_BASE + facets + "&nondik=0", f"eu-eoda/{tag}-0.html")
    m = re.search(r"([\d.]+)\s*</?[^>]*>?\s*emaitza", first) or re.search(r">\s*([\d.]+)\s*<[^>]*>\s*emaitza", first)
    total = int(re.sub(r"\D", "", m.group(1))) if m else 0
    yield first
    for k in range(10, total, 10):
        yield fetch(EU_BASE + facets + f"&nondik={k}", f"eu-eoda/{tag}-{k}.html")


def eu_entries(page):
    for blk in re.split(r"<h3>", page)[1:]:
        m = re.search(r'href="([^"]*task=izenaIkusi[^"]*kodea=(\d+)[^"]*)"\s*>\s*(.*?)<span>\((\w+)\)</span>', blk, re.S)
        if not m: continue
        url, code, name, sexw = html.unescape(m.group(1)), m.group(2), clean(m.group(3)), m.group(4)
        body = blk[m.end():].split("</h3>")[-1]
        body = body.split("<h3")[0]
        eq, mean = [], []
        for li in re.findall(r"<li>(.*?)</li>", body, re.S):
            if "<small>" in li: mean.append(clean(li))
            else:
                for f, lang in re.findall(r"([^<>,]+?)\s*<span[^>]*>\((\w+)\)</span>", li):
                    eq.append(f"{lang}: {clean(f)}")
        yield code, dict(name=name, sexw=sexw, meaning=" ".join(mean), equivalents="; ".join(eq), source_url=url)


def basque():
    print("Basque: Euskaltzaindia EODA", flush=True)
    names = {}
    for sx, s in EU_SEX.items():
        for st, label in EU_STATUS.items():
            for page in eu_pages(f"&sexua_facet[]={sx}&arautzea_facet[]={st}", f"s{sx}-a{st}"):
                for code, e in eu_entries(page):
                    e["sex"] = s; e["status"] = label
                    names[code] = e
        hyp = set()
        for page in eu_pages(f"&sexua_facet[]={sx}&hipokoristikoa_facet[]=1", f"s{sx}-hipo"):
            for code, e in eu_entries(page):
                hyp.add(code)
                names.setdefault(code, dict(e, sex=s, status=""))
        for c in hyp: names[c]["hypo"] = True
        first = fetch(EU_BASE + f"&sexua_facet[]={sx}&nondik=0", f"eu-eoda/s{sx}-0.html")
        tot = int(re.search(r"([\d.]+)\s*</span>\s*emaitza", first).group(1).replace(".", ""))
        got = sum(1 for e in names.values() if e["sex"] == s)
        print(f"  sex {s}: {got} parsed of {tot} listed", flush=True)
        if got < tot:   # names without a status facet: take them from the plain per-sex listing
            for page in eu_pages(f"&sexua_facet[]={sx}", f"s{sx}"):
                for code, e in eu_entries(page): names.setdefault(code, dict(e, sex=s, status=""))
    rows = []
    for code, e in sorted(names.items(), key=lambda kv: kv[1]["name"].lower()):
        note = "arautzea: " + e["status"] if e.get("status") else ""
        if e.get("hypo"): note += ("; " if note else "") + "hipokoristikoa"
        rows.append(dict(name=e["name"], sex=e["sex"], meaning=e["meaning"], equivalents=e["equivalents"],
                         source_url=e["source_url"], note=note))
    write_tsv("eu-euskaltzaindia", "Euskaltzaindia (Real Academia de la Lengua Vasca), EODA Pertsona-izenak (Basque given names); "
              "https://www.euskaltzaindia.eus/index.php?option=com_ecoeoda&task=izenaPortada&Itemid=469&lang=eu ; "
              f"accessed {date.today()}; listing pages crawled by sex and 'arautzea' (normative status). Terms: " + EU_TERMS, rows)


# ---------------------------------------------------------------- Galician: Real Academia Galega, Guía de nomes galegos
RAG = "https://academia.gal/nomes/-/nome/"
RAG_PDFS = {"g": ("https://www.academia.gal/documents/35271/636756/GNG_Femininos.pdf", "gl-rag-GNG_Femininos.pdf"),
            "b": ("https://www.academia.gal/documents/35271/636756/GNG_Masculinos.pdf", "gl-rag-GNG_Masculinos.pdf")}
GL_LANG = {"Alemán": "de", "Catalán": "ca", "Español": "es", "Éuscaro": "eu", "Francés": "fr", "Húngaro": "hu",
           "Inglés": "en", "Italiano": "it", "Portugués": "pt", "Romanés": "ro", "Ruso": "ru", "Polaco": "pl",
           "Neerlandés": "nl", "Checo": "cs", "Sueco": "sv", "Irlandés": "ga", "Bretón": "br", "Asturiano": "ast",
           "Aragonés": "an", "Occitano": "oc", "Latín": "la", "Grego": "el", "Hebreo": "he", "Árabe": "ar"}


def rag_pdf_names(path):
    import pypdf   # the only non-stdlib dependency, used for the RAG's two PDF lists
    out = []
    for i, pg in enumerate(pypdf.PdfReader(path).pages):
        if i < 8: continue     # cover, credits and introduction
        lines = [l.strip() for l in (pg.extract_text() or "").split("\n") if l.strip()]
        if lines and lines[0].startswith("Nomes "): lines = lines[1:]
        if lines and lines[0].isdigit(): lines = lines[1:]
        out += [l for l in lines if not re.fullmatch(r"[A-ZÁÉÍÓÚ]", l)]
    return out


def rag_entry(page):
    s = re.sub(r"<script.*?</script>|<style.*?</style>|<svg.*?</svg>", "", page, flags=re.S)
    m = re.search(r'names-content__title__content">(.*?)</span>', s, re.S)
    if not m: return None
    e = {"title": clean(m.group(1)), "labels": [clean(x) for x in re.findall(r'names-content__label">(.*?)</p>', s, re.S)]}
    end = s.find('id="proximityNames"')
    body = s[m.end():end if end > 0 else len(s)]
    parts = re.split(r'<h3 class="names-content__subtitle">(.*?)</h3>', body)
    sec = {clean(parts[i]): parts[i + 1] for i in range(1, len(parts) - 1, 2)}
    e["etym"] = clean(re.sub(r"</p>", " ", sec.get("Etimoloxía e historia", "")))
    e["variants"] = "; ".join(clean(x) for x in re.findall(r'<p class="names-content__references">(.*?)</p>', sec.get("Variantes", ""), re.S))
    e["hypo"] = "; ".join(clean(x) for x in re.findall(r'<p class="names-content__references">(.*?)</p>', sec.get("Hipocorísticos", ""), re.S))
    eq, lang = [], ""
    for tr in re.findall(r"<tr>(.*?)</tr>", sec.get("Equivalencias noutras linguas", ""), re.S):
        tds = [clean(x) for x in re.findall(r"<td>(.*?)</td>", tr, re.S)]
        if len(tds) != 3: continue
        lang = tds[0] or lang
        eq.append((GL_LANG.get(lang, lang), tds[1], tds[2]))
    e["eq"] = eq
    return e


def galician_rag():
    print("Galician: RAG Guía de nomes galegos", flush=True)
    sex = {}
    for sx, (url, cache) in RAG_PDFS.items():
        fetch(url, cache, binary=True)
        for n in rag_pdf_names(os.path.join(OUT, cache)):
            sex[n] = "e" if sex.get(n, sx) != sx else sx
    print(f"  {len(sex)} names in the two PDF lists", flush=True)
    covered, entries, missing = {}, [], []
    for n in sorted(sex, key=str.lower):
        if n in covered: continue
        page = fetch(RAG + urllib.parse.quote(n), f"gl-rag/{n}.html")
        e = rag_entry(page)
        if not e: missing.append(n); continue
        forms = [f.strip() for f in e["title"].split(",")]
        e["url"] = RAG + n
        entries.append(e)
        for f in forms + [n]: covered.setdefault(f, e)
    rows = []
    for n in sorted(sex, key=str.lower):
        e, s = covered.get(n), sex[n]
        if not e:
            rows.append(dict(name=n, sex=s, source_url=RAG_PDFS[s if s != "e" else "g"][0], note="in the PDF list; no entry page found"))
            continue
        col = {"b": 1, "g": 2}.get(s)
        eqs = []
        for t in e["eq"]:
            if col: v = t[col]
            else: v = " / ".join(x for x in t[1:] if x)
            if v: eqs.append(f"{t[0]}: {v}")
        note = [f"entry: {e['title']}"] + (["label: " + ", ".join(e["labels"])] if e["labels"] else [])
        if e["variants"]: note.append("variantes: " + e["variants"])
        if e["hypo"]: note.append("hipocorísticos: " + e["hypo"])
        rows.append(dict(name=n, sex=s, meaning=e["etym"], equivalents="; ".join(eqs),
                         source_url=RAG + urllib.parse.quote(n), note="; ".join(note)))
    if missing: print(f"  no entry page for {len(missing)}: {missing[:20]}", flush=True)
    write_tsv("gl-rag-nomes", "Real Academia Galega, Guía de nomes galegos (coord. A. I. Boullón Agrelo), https://academia.gal/nomes ; "
              "sex from the RAG's two lists GNG_Femininos.pdf / GNG_Masculinos.pdf (version Xuño 2025); meaning = the entry's "
              "'Etimoloxía e historia' text, equivalents = its 'Equivalencias noutras linguas' table (column for that sex); "
              f"accessed {date.today()}. Terms: " + GL_TERMS, rows)


# ---------------------------------------------------------------- Galician: IGE resident population by name (1 Jan 2023)
IGE = "https://www.ige.gal/igebdt/onomast/"


def ige_key(n):
    import unicodedata
    out = ""
    for ch in n.upper():
        if ch == "Ñ": out += ch; continue
        out += "".join(c for c in unicodedata.normalize("NFD", ch) if not unicodedata.combining(c))
    return out


def ige_cells(page):
    return [[clean(c) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r, re.S)] for r in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S)]


def galician_ige():
    print("Galician: IGE names of residents", flush=True)
    sex = {}
    for sx, (url, cache) in RAG_PDFS.items():
        fetch(url, cache, binary=True)
        for n in rag_pdf_names(os.path.join(OUT, cache)):
            sex.setdefault(n, set()).add(sx)
    rows = []
    top = fetch(IGE + "nomconc.jsp?idioma=gl&codigo=12", "gl-ige-nomconc-12.html")
    for c in ige_cells(top):
        if len(c) == 8 and c[1].replace(".", "").isdigit():
            for nm, cnt, sx in ((c[0], c[1], "g"), (c[4], c[5], "b")):
                rows.append(dict(name=nm, sex=sx, count=cnt.replace(".", ""), source_url=IGE + "nomconc.jsp?idioma=gl&codigo=12",
                                 note="top 25 of Galicia by sex; residents 1 Jan 2023"))
    done = set()
    for n in sorted(sex, key=str.lower):
        for sx in sorted(sex[n]):
            k = (ige_key(n), sx)
            if k in done: continue
            done.add(k)
            url = IGE + f"nomes.jsp?idioma=gl&coincidencia=Exacta&sexo={'Muller' if sx == 'g' else 'Home'}&cb=" + urllib.parse.quote(k[0])
            page = fetch(url, f"gl-ige/{k[0]}-{sx}.html")
            gal = [c for c in ige_cells(page) if c and c[0] == "GALICIA" and len(c) >= 2]
            if not gal: continue
            forms = [m for m in sex if ige_key(m) == k[0] and sx in sex[m]]
            rows.append(dict(name=k[0], sex=sx, count=gal[0][1].replace(".", ""), source_url=url,
                             note="residents of Galicia 1 Jan 2023, exact match, accents removed by IGE; queried for RAG form(s) " + ", ".join(forms)
                             + (f"; mean age {gal[0][3]}" if len(gal[0]) > 3 and gal[0][3] else "")))
    write_tsv("gl-ige-residentes", "Instituto Galego de Estatística (IGE), 'Distribución municipal dun nome' / 'Nomes por concello', "
              "https://www.ige.gal/igebdt/onomast/nomes.jsp , data at 1 Jan 2023 (INE census file); every name of the RAG guide "
              "queried by its listed sex, plus Galicia's top 25 per sex; IGE removes accents; names with <=5 bearers in a municipality "
              f"are only in totals. Accessed {date.today()}. Terms: " + GL_IGE_TERMS, rows)


GL_IGE_TERMS = ("IGE aviso legal: reuse governed by Lei 37/2007 on reuse of public-sector information and Xunta general reuse "
                "conditions (cite the source, do not distort the data, state date of update); 'Queda prohibida toda comercialización deste dereito de acceso'.")


# ---------------------------------------------------------------- Catalan: Generalitat (Justícia) name finder + Idescat
JUST = "https://justicia.gencat.cat/ca/serveis/cercador_de_noms/index.html?accion=buscar&mode=normal&lang=cat"
IDESCAT_NOMS = "https://www.idescat.cat/noms/?lang=ca&f=ssv"
IDESCAT_NADONS = "https://www.idescat.cat/nadons/?lang=ca&f=ssv"


def justicia_entries(page):
    i = page.find('id="cercador_text"')
    seg = page[i:page.find("</dl>", i)] if i >= 0 else ""
    for dt, dd in re.findall(r"<dt>(.*?)</dt>\s*<dd>(.*?)</dd>", seg, re.S):
        m = re.search(r"<strong>(.*?)</strong>(.*)", dt, re.S)
        name, gloss = clean(m.group(1)), clean(m.group(2))
        e = {"name": name, "gloss": gloss, "onom": "", "es": "", "notes": []}
        for p in re.findall(r"<p>(.*?)</p>", dd, re.S):
            if "<a" in p: continue
            t = clean(p)
            if t.startswith("Onomàstica"): e["onom"] = t.split(":", 1)[1].strip()
            elif t.startswith("Equivalència castellana"): e["es"] = t.split(":", 1)[1].strip()
            elif t: e["notes"].append(t)
        yield e


def catalan_justicia():
    print("Catalan: Departament de Justícia, Cercador de noms", flush=True)
    entries = {}
    for L in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        pag = 1
        while True:
            page = fetch(JUST + f"&nomc={L}&pag={pag}", f"ca-justicia/{L}-{pag}.html")
            for e in justicia_entries(page): entries[(e["name"], e["gloss"], e["es"], e["onom"], tuple(e["notes"]))] = e
            if f"pag={pag + 1}&amp;nomc={L}" not in page and f"pag={pag + 1}&nomc={L}" not in page: break
            pag += 1
    rows = []
    for e in sorted(entries.values(), key=lambda e: e["name"].lower()):
        text = " ".join([e["gloss"]] + e["notes"])
        fem = bool(re.search(r"\bfemen[íi]", text)); masc = bool(re.search(r"\bmascul[íi]", text))
        sx = "g" if fem and not masc else "b" if masc and not fem else ""
        note = []
        if e["gloss"]: note.append(e["gloss"])
        if e["onom"]: note.append("onomàstica: " + e["onom"])
        rows.append(dict(name=e["name"], sex=sx, meaning=" ".join(e["notes"]), equivalents=("es: " + e["es"]) if e["es"] else "",
                         source_url=JUST + "&nomc=" + urllib.parse.quote(e["name"][:3]), note="; ".join(note)))
    write_tsv("ca-justicia-noms", "Generalitat de Catalunya, Departament de Justícia, 'Cercador de noms' (Catalan given names with "
              "Spanish equivalents, saint's day and short notes; >1,500 names), https://justicia.gencat.cat/ca/serveis/cercador_de_noms/ ; "
              "the page's open-data XML link (/.content/tramits/noms/LlistatNoms.xml) returned 404, so the A-Z result pages were read. "
              "Sex is only filled where the entry itself says 'femení'/'masculí' (one of the two). "
              f"Accessed {date.today()}. Terms: " + CA_GENCAT_TERMS, rows)


def ssv_rows(text):
    lines = text.lstrip("﻿").splitlines()
    hdr = next(i for i, l in enumerate(lines) if l.startswith("Pos.;"))
    for l in lines[hdr + 1:]:
        c = l.split(";")
        if len(c) >= 5 and c[0].isdigit(): yield c


def catalan_idescat():
    print("Catalan: Idescat", flush=True)
    txt = fetch(IDESCAT_NOMS, "ca-idescat-noms-poblacio.ssv")
    year = re.search(r"Catalunya\. (\d{4})", txt).group(1)
    rows = [dict(name=c[2], sex={"H": "b", "D": "g"}.get(c[1], ""), count=c[3].replace(".", ""), source_url=IDESCAT_NOMS,
                 note=f"population of Catalonia {year}; rank {c[0]}; {c[4]} per mille; mean age {c[5] if len(c) > 5 else ''}")
            for c in ssv_rows(txt)]
    write_tsv("ca-idescat-noms-poblacio", f"Idescat (Institut d'Estadística de Catalunya), 'Noms de la població' {year}, every given name "
              "borne by >=4 residents of Catalonia, by sex (Idescat from INE's annual population census); "
              f"{IDESCAT_NOMS} ; names are printed by Idescat in capitals, with merged spellings as 'NÚRIA/NURIA'. "
              f"Accessed {date.today()}. Terms: " + CA_IDESCAT_TERMS, rows)
    rows = []
    for y in range(1997, date.today().year + 1):
        try: txt = fetch(IDESCAT_NADONS + f"&t={y}", f"ca-idescat/nadons-{y}.ssv")
        except SystemExit: break
        if f"Catalunya. {y}" not in txt: continue      # the year is not published yet (Idescat falls back to the latest)
        rows += [dict(name=c[2], sex={"H": "b", "D": "g"}.get(c[1], ""), count=c[3].replace(".", ""), source_url=IDESCAT_NADONS + f"&t={y}",
                      note=f"newborns {y}; rank {c[0]}; {c[4]} per mille") for c in ssv_rows(txt)]
    write_tsv("ca-idescat-nadons", "Idescat, 'Noms dels nadons', every name given to >=4 babies of mothers resident in Catalonia, by "
              f"year and sex (one row per name and year); {IDESCAT_NADONS}&t=YYYY . Accessed {date.today()}. Terms: " + CA_IDESCAT_TERMS, rows)


def catalan():
    catalan_idescat()
    catalan_justicia()


# ---------------------------------------------------------------- Asturian: Ayuntamiento de Mieres list (no open ALLA list exists)
AST_PDF = "https://www.mieres.es/wp-content/uploads/2017/06/nomes_de__persona_n.pdf"


def asturian():
    print("Asturian: Mieres council list", flush=True)
    fetch(AST_PDF, "ast-mieres-nomes_de_persona.pdf", binary=True)
    import pypdf
    text = "\n".join(pg.extract_text() or "" for pg in pypdf.PdfReader(os.path.join(OUT, "ast-mieres-nomes_de_persona.pdf")).pages)
    sx, rows, seen = "", [], set()
    for line in text.split("\n"):
        l = line.strip()
        if "nomes d’home" in l or "nomes d'home" in l: sx = "b"; continue
        if "nomes de muyer" in l: sx = "g"; continue
        if not sx or not l or l.isdigit() or re.fullmatch(r"[A-ZÁÉÍÓÚÑ]", l) or l.startswith("NOMES DE"): continue
        for part in [x.strip() for x in l.split(",") if x.strip()]:
            forms = [part]
            m = re.fullmatch(r"(\S+?)(\w)/(\w)", part)            # "Abiliu/o" = Abiliu or Abilio
            if m: forms = [m.group(1) + m.group(2), m.group(1) + m.group(3)]
            m = re.fullmatch(r"(\S+) \((\S+)\)", part)             # "Xesusa (Susa)"
            if m: forms = [m.group(1), m.group(2)]
            for f in forms:
                if (f, sx) in seen: continue
                seen.add((f, sx))
                rows.append(dict(name=f, sex=sx, source_url=AST_PDF, note=f"printed line: {l}" if l.rstrip(",").strip() != f else ""))
    write_tsv("ast-mieres-nomes", "Ayuntamiento de Mieres (Asturias), Serviciu de Normalización Llingüística, 'Nomes de persona "
              f"n'asturiano' (list of men's and women's names, PDF linked from https://www.mieres.es/documentos/nomes-persona-nasturianu/), {AST_PDF} ; "
              "sex = the list the name is in; 'X/y' forms were expanded to both spellings and 'A (B)' to both names (printed line kept in note). "
              "The Academia de la Llingua Asturiana's own list ('Delles propuestes pa Nomes de Persona', Cartafueyos normativos 2, 2006) "
              f"is a printed booklet for sale, not online. Accessed {date.today()}. Terms: no licence stated on the page or PDF.", rows)


def aragonese():
    print("Aragonese: no official open list found (see report); nothing written", flush=True)


# ---------------------------------------------------------------- Basque: Eustat newborn top 100
EUSTAT = {"g": "https://es.eustat.eus/elementos/xls0005715_c.csv", "b": "https://es.eustat.eus/elementos/xls0005716_c.csv"}


def eustat():
    import csv, io
    print("Basque: Eustat newborn top 100", flush=True)
    rows = []
    for sx, url in EUSTAT.items():
        txt = fetch(url, "eu-eustat-" + url.rsplit("/", 1)[1]).lstrip("﻿")
        lines = list(csv.reader(io.StringIO(txt), delimiter=";"))
        years = next(l for l in lines if len(l) > 2 and re.fullmatch(r"\d{4}", l[1].strip()))
        years = [y for y in years if y.strip()]
        for l in lines:
            if not l or not l[0].strip().isdigit(): continue
            for k, y in enumerate(years):
                nm, cnt = l[1 + 2 * k].strip(), l[2 + 2 * k].strip()
                if nm: rows.append(dict(name=nm, sex=sx, count=cnt.replace(".", ""), source_url=url,
                                        note=f"newborns C.A. de Euskadi {y}; rank {l[0]}"))
    write_tsv("eu-eustat-nacimientos", "Eustat (Instituto Vasco de Estadística), 'Lista de los 100 nombres de niña / niño más frecuentes en "
              "la C.A. de Euskadi' (tables tbl0005715 / tbl0005716, CSV), one row per name and year; Eustat prints merged spellings "
              f"as 'Martin/Martín'. {EUSTAT['g']} , {EUSTAT['b']} ; accessed {date.today()}. Terms: the table pages declare "
              "Licencia: Creative Commons (https://creativecommons.org/licenses/by/3.0/deed.es).", rows)


GL_TERMS = ("RAG aviso legal (https://academia.gal/aviso-legal): all rights reserved; 'queda expresamente prohibida a reprodución, transformación, distribución ... extracción ou reutilización do sitio web, os seus contidos' without prior RAG authorisation. Use only as reference / ask the RAG.")
CA_GENCAT_TERMS = ("Generalitat avís legal (https://tramits.gencat.cat/ca/ajuda/avis_legal/): reuse permitted worldwide under the 'Llicència oberta d\u2019ús d\u2019informació – Catalunya' or the equivalent CC0.")
CA_IDESCAT_TERMS = ("Idescat avís legal (https://www.idescat.cat/institut/web/): 'l\u2019Idescat permet reutilitzar la informació ... sempre que se\u2019n citi la font', without altering it and stating the date of last update.")
EU_TERMS = "no open licence stated; the database page says it includes third-party content used with permission (copyright Euskaltzaindia)."

def galician():
    galician_rag()
    galician_ige()


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    want = sys.argv[1:] or ["eu", "gl", "ca", "ast", "an"]
    for k in want:
        f = {"eu": lambda: (eustat(), basque()), "gl": galician, "ca": catalan, "ast": asturian, "an": aragonese}.get(k) or globals().get({"gl": "galician", "ca": "catalan", "ast": "asturian", "an": "aragonese"}.get(k, ""), None)
        if f: f()
