# English names across 1,400 years → data/english-names.json, in the row format of data/culture-names.json:
#   [name, g, culture, language, religions, meaning, src, texts, kind, also]
#
# Where a name was used (England) and where it comes from are kept apart. Culture is "English" for every row; the
# language is "Old English" only for a name a source gives as Old English (Wiktionary's Old English given names, an Old
# English label on Wikidata, or an English entry that derives it from Old English), "Middle English" for one recorded
# in medieval England, and "English" otherwise. src says when and where the name is recorded.
#
#   Wikidata (CC0): the 1,200-odd people who carry a PASE ID (P2625), i.e. people recorded in the Prosopography of
#     Anglo-Saxon England, with their sex and Old English label. PASE itself is not harvested: its terms allow
#     "individual, non-commercial use only … all other use is prohibited without the express written consent".
#   Wiktionary (CC BY-SA 4.0): Old English and Middle English given names (cached by build_medieval.py in
#     raw/medieval/), and every English given name, kept here when its entry derives it from Old or Middle English,
#     from an English word or an English surname, calls it a Puritan or virtue name, or says an author coined it.
#   data/medieval-names.json: its Old English and medieval English rows (Domesday Book, Wikidata), reused as they are.
#   DMNES (Dictionary of Medieval Names from European Sources, © The Editors, no open licence): not harvested. Only the
#     entries of the medieval names this project was asked to check are read and cited by year, as the site's own
#     "Cite as" line invites.
#   C. W. Bardsley, Curiosities of Puritan Nomenclature (1880, public domain, Project Gutenberg #39284): the parish
#     register entries it quotes ("1604, Feb. 23. Patience, daughter of …"), with the year and the sex the entry gives.
#   Literature (public domain texts from Project Gutenberg): the Dramatis Personae of every Shakespeare play
#     (Gutenberg #100), the character lists in each work's English Wikipedia article (CC BY-SA 4.0), and the characters
#     Wikidata links to the work (P674 / P1441). A name is kept only when it also appears in the work's text. The year
#     is the work's publication date on Wikidata (or "c." its composition date).
#   FreeBMD / FreeREG: not used. Their terms allow manual searches for personal research only and forbid reproducing
#     extracted data.
#
# Meanings come only from Wiktionary. A sex comes only from a source: the Wikidata person or character, the register
# entry, the character list ("daughter of", "Mrs", "his"/"her"), DMNES's m./f., or Wiktionary's male/female category.
# Downloads are cached in raw/english/ (delete a file to fetch it again). Polite: one request at a time, a contact
# user agent, pauses between requests.
#
#   python3 scripts/build_english_names.py
import collections, csv, html, json, os, re, sys, time, unicodedata, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "raw", "english"); MED = os.path.join(ROOT, "raw", "medieval")
OUT = os.path.join(ROOT, "data", "english-names.json")
sys.path.insert(0, HERE)
from fetch_wiktionary_names import members, pages, UA
from build_cultures import clean, section
from build_medieval import etymology, modern_form, given_name_section

# ───────────────────────── helpers ─────────────────────────
def fold(s):   # as app.js
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not 0x300 <= ord(c) <= 0x36F).lower()
    for a, b in (("æ", "ae"), ("ǣ", "ae"), ("ǽ", "ae"), ("ø", "o"), ("œ", "oe"), ("ð", "d"), ("þ", "th"), ("ß", "ss")): s = s.replace(a, b)
    return re.sub(r"[\s-]", "", s)

def loose(s): return fold(plain_oe(s)).replace("ae", "e")   # Ælfræd and Ælfred, Eadgyþ and Ēadgȳð are one name

def plain_oe(s):
    """The usual modern scholarly spelling of an Old English form (PASE's house style): þ ð → th, ƿ → w, no length marks."""
    s = s.replace("þ", "th").replace("ð", "th").replace("Þ", "Th").replace("Ð", "Th").replace("ƿ", "w").replace("Ƿ", "W")
    s = s.replace("ǣ", "æ").replace("Ǣ", "Æ").replace("ǽ", "æ").replace("Ǽ", "Æ")
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not 0x300 <= ord(c) <= 0x36F)
    return unicodedata.normalize("NFC", s)

def get(url, data=None, tries=6, **headers):
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={**UA, **headers})
            return urllib.request.urlopen(req, timeout=300).read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 404: return ""
            time.sleep(5 * (attempt + 1))
        except Exception:
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("could not fetch " + url)

def cached(name, fetch):
    path = os.path.join(RAW, name)
    if not os.path.exists(path):
        data = fetch()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f: (f.write(data) if isinstance(data, str) else json.dump(data, f, ensure_ascii=False))
    with open(path, encoding="utf-8") as f: return json.load(f) if name.endswith(".json") else f.read()

def sparql(q):
    t = get("https://query.wikidata.org/sparql", data=urllib.parse.urlencode({"query": q}).encode(), Accept="application/sparql-results+json")
    time.sleep(1)
    return [{k: v["value"] for k, v in b.items()} for b in json.loads(t)["results"]["bindings"]]

def year(v):
    m = re.match(r"^(-?\d{1,4})-", v or "")
    return int(m.group(1)) if m else None

NAME = re.compile(r"^[A-ZÆÞÐ][a-zà-ÿæþðǣāēīōūȳ]+(?:-[A-Za-zà-ÿ][a-zà-ÿ]+)*$")
SEX = {"Q6581072": "g", "Q6581097": "b", "Q1052281": "g", "Q2449503": "b"}

# ───────────────────────── 1. PASE people on Wikidata ─────────────────────────
PASE_Q = """SELECT ?x ?pase ?en ?ang ?native ?sex ?desc ?born ?died ?fl ?links WHERE {
 ?x wdt:P2625 ?pase. ?x wikibase:sitelinks ?links.
 OPTIONAL{?x rdfs:label ?en FILTER(lang(?en)="en")}
 OPTIONAL{?x rdfs:label ?ang FILTER(lang(?ang)="ang")}
 OPTIONAL{?x wdt:P1559 ?native FILTER(lang(?native)="ang")}
 OPTIONAL{?x wdt:P21 ?sex}
 OPTIONAL{?x schema:description ?desc FILTER(lang(?desc)="en")}
 OPTIONAL{?x wdt:P569 ?born} OPTIONAL{?x wdt:P570 ?died} OPTIONAL{?x wdt:P1317 ?fl} }"""
STOP_OE = {"unnamed", "anonymous", "saint", "st", "king", "queen", "abbot", "abbess", "bishop", "the"}

def pase_people():
    people = {}
    for b in cached("wikidata-pase.json", lambda: sparql(PASE_Q)):
        p = people.setdefault(b["x"], {"pase": b["pase"], "en": b.get("en", ""), "ang": set(), "sex": set(), "desc": b.get("desc", ""),
                                       "died": None, "fl": None, "links": int(b.get("links", 0))})
        for k in ("ang", "native"):
            if b.get(k): p["ang"].add(b[k])
        if b.get("sex") and b["sex"].rsplit("/", 1)[-1] in SEX: p["sex"].add(SEX[b["sex"].rsplit("/", 1)[-1]])
        for k in ("died", "fl"):
            y = year(b.get(k))
            if y and 400 < y < 1150: p[k] = min(p[k] or 9999, y)
    out = []
    for p in people.values():
        if len(p["sex"]) != 1: continue
        en = re.split(r",| of | the | se | II\b| I\b| III\b| \(", p["en"])[0].strip()
        if not NAME.match(en) or en.lower() in STOP_OE: continue
        native = ""
        for a in sorted(p["ang"], key=lambda a: (fold(plain_oe(a.split()[0]))[:3] != fold(en)[:3], a)):
            w = a.split()[0]
            if NAME.match(plain_oe(w)) and w.lower() not in STOP_OE: native = w; break
        if native: en = plain_oe(native)      # the Old English form Wikidata records (Alfred the Great → Ælfrēd → Ælfred)
        out.append(dict(p, name=en, native=native, sex=p["sex"].pop()))
    return out

# ───────────────────────── 2. Wiktionary ─────────────────────────
def fetch_english():
    sex = {}
    for g, label in (("b", "male"), ("g", "female"), ("e", "unisex")):
        for t in members(f"English {label} given names"): sex[t] = "e" if t in sex and sex[t] != g else g
    text = pages(sorted(sex))
    return {"names": {t: {"g": g, "text": text.get(t, "")} for t, g in sex.items()}}

def ety_text(sec):
    m = re.search(r"(?ms)^===+\s*Etymology[^=]*===+\s*$(.*?)(?=^===|\Z)", sec)
    return m.group(1) if m else ""

def plain(t):
    t = re.sub(r"<ref.*?</ref>|<ref[^>]*/>", "", t, flags=re.S)
    t = re.sub(r"\{\{(?:m|l|w|lw|ll)\|[^|{}]*\|([^|{}]*)[^{}]*\}\}", r"\1", t)
    t = re.sub(r"\{\{(?:inh|der|bor|uder|bor\+|der\+|inh\+)\|[^|{}]*\|([^|{}]*)\|([^|{}]*)[^{}]*\}\}", lambda m: f"{LANG_NAME.get(m.group(1), m.group(1))} {m.group(2)}", t)
    return clean(t)

LANG_NAME = {"ang": "Old English", "enm": "Middle English", "en": "English", "fro": "Old French", "xno": "Anglo-Norman", "la": "Latin", "non": "Old Norse",
             "grc": "Ancient Greek", "he": "Hebrew", "fr": "French", "it": "Italian", "gmw-pro": "Proto-West Germanic", "gem-pro": "Proto-Germanic"}
COIN = re.compile(r"(?:[Cc]oined|[Ii]nvented|[Ff]irst used|[Cc]reated) by ([A-Z][\w.]*(?: [A-Z][\w.']*){0,3})")

def wikt_english():
    d = cached("wikt-English.json", fetch_english)["names"]
    out = {}
    for t, v in d.items():
        sec = section(v["text"], "English")
        if not sec or not re.search(r"\{\{given name\|en", sec): continue
        gn = " ".join(re.findall(r"\{\{given name\|en[^{}]*\}\}", sec))
        frm = set(re.findall(r"\|from\d*=([^|}]+)", gn))
        e = ety_text(sec)
        first = re.search(r"\{\{(?:inh|der|bor|uder)\|en\|([\w-]+)\|", e)
        chain, meaning = etymology(sec)
        info = {"g": v["g"], "chain": chain, "meaning": meaning, "ety": plain(e)[:400], "first": first.group(1) if first else ""}
        oe = re.search(r"\{\{(?:inh|der|uder)\|en\|ang\|([^|{}]+)", e)
        if oe: info["oe"] = oe.group(1)
        if "Old English" in frm or info["first"] == "ang" or (info["first"] == "enm" and oe): info["kind"] = "oe"
        elif info["first"] == "enm": info["kind"] = "me"
        elif "English" in frm: info["kind"] = "word"
        elif "surnames" in frm and info["first"] in ("ang", "enm"): info["kind"] = "surname"
        if re.search(r"Puritan|virtue name", e): info["puritan"] = True
        c = COIN.search(info["ety"])
        if c and not re.search(r"\b(?:Popularized|popularised)\b", info["ety"][:c.start()][-30:]):
            sent = [s for s in re.split(r"(?<=[.;])\s+", info["ety"]) if COIN.search(s)]
            info["coined"] = sent[0].rstrip(".;") if sent else ""
        out[t] = info
    return out

# ───────────────────────── 3. DMNES (cited entries only) ─────────────────────────
# must-check name → (DMNES headword, the forms that count as this name)
DMNES = {"Avice": ("Avice", r"^A[uv][iy]s|^A[uv]ic"), "Amice": ("Amice", r"^Ami[cs]"), "Anabel": ("Amabel", r"^Anab|^Annab"),
         "Cecily": ("Cecilia", r"^C[ei]c[ei]l[iy]e?$|^Cecely|^Sisl"), "Clarice": ("Clarice", r"^Clari[cs]"), "Emmeline": ("Emmeline", r"^Em[m]?e?l[iy]n"),
         "Isolde": ("Isolde", r"^[IY]s[eo]u?l[dt]|^Isot"), "Juliana": ("Juliana", r"^[IJ]ulian"), "Margery": ("Margaret", r"^Marg[eo]r[iy]|^Marjor"),
         "Matilda": ("Mathilda", r"^Mat[h]?ild"), "Maud": ("Mathilda", r"^Ma[uw]d|^Mald|^Mahald|^Mahault"), "Millicent": ("Milicent", r"^Mil"),
         "Petronilla": ("Petronilla", r"^Pe[t]?ron|^Parnel|^Pernel"), "Rosamund": ("Rosamund", r"^Rosam"), "Sybil": ("Sibyl", r"^S[iy]b[iy]l"),
         "Anselm": ("Anselm", r"^Ans[ea]l"), "Osbert": ("Osbert", r"^Osb[ea]r"), "Ranulf": ("Ralph", r"^Ran[u]?l"), "Theobald": ("Theobald", r"^Th?eob|^Tebald|^Tibald")}

def dmnes():
    out = {}
    for name, (head, forms) in DMNES.items():
        page = cached(f"dmnes/{head}.html", lambda h=head: (time.sleep(3), get(f"https://dmnes.org/name/{h}"))[1])
        if not page: continue
        text = html.unescape(re.sub(r"<[^>]+>", "\n", page))
        sx = re.search(r"\n\s*(m|f)\.\s*\n", text)
        eng = re.search(r"\nEngland\n(.*?)(?=\n(?:Scotland|Ireland|Wales|France|Italy|Iberia|Spain|Portugal|Germany|Low Countries|Scandinavia|Hungary|Sweden|Norway|Denmark|Iceland|Switzerland|Bohemia|Estonia|Latvia|Malta)\n|\nCite as)", text, re.S)
        if not eng or not sx: continue
        best = None
        for m in re.finditer(r"(\d{4})(?:[x–-]\S*)?\s+([^\s(;,]+)", eng.group(1)):
            y, form = int(m.group(1)), m.group(2)
            if re.search(forms, form) and (best is None or y < best[0]): best = (y, form)
        if best: out[name] = {"g": "b" if sx.group(1) == "m" else "g", "year": best[0], "form": best[1], "head": head}
    return out

# ───────────────────────── 4. Bardsley's parish registers ─────────────────────────
GUT = "https://www.gutenberg.org/cache/epub/{0}/pg{0}.txt"
def gutenberg(n):
    def fetch():
        time.sleep(2)
        return get(GUT.format(n))
    return cached(f"gutenberg/pg{n}.txt", fetch)

REG = re.compile(r'"\s*(1[4-7]\d\d)[,.][^"]{0,40}?\.\s+(?:(?:Baptized|Bapt\.|Christened|Christening of|Buried|Bur\.|Died)\s+)?'
                 r'((?:[A-Z][a-z]+)(?:-[a-z]+)*(?:-[A-Z][a-z]+)*)(?:\s+[A-Z][a-z]+)?,\s+(d\.|s\.|dau\.|daughter|son|the daughter|the son|wife)\b')
MARR = re.compile(r'"\s*(1[4-7]\d\d)[,.][^"]{0,40}?\.\s+Married\s+([A-Z][a-z]+(?:-[a-z]+)*)\s+[A-Z][\w\'-]+\s+and\s+([A-Z][a-z]+(?:-[a-z]+)*)\s+[A-Z]')
def bardsley():
    text = gutenberg(39284).replace("\r", "")
    text = re.sub(r"\s*\n\s*", " ", text)
    out = collections.defaultdict(lambda: {"b": 0, "g": 0, "year": 9999})
    for y, n, rel in REG.findall(text):
        g = "g" if rel.startswith(("d", "the d", "wife")) else "b"
        o = out[n]; o[g] += 1; o["year"] = min(o["year"], int(y))
    for y, a, b in MARR.findall(text):
        for n, g in ((a, "b"), (b, "g")):
            o = out[n]; o[g] += 1; o["year"] = min(o["year"], int(y))
    return {n: o for n, o in out.items() if n not in ("Baptized", "Buried", "Married", "Christened", "Mr", "Mrs", "John's")}

# ───────────────────────── 5. Literature ─────────────────────────
# (work, author as said in the source line, Gutenberg texts, English Wikipedia pages that list its characters)
WORKS = [
    ("Beowulf", "", [16328, 981], ["Beowulf"]),
    ("The Canterbury Tales", "Chaucer's", [2383], ["The Canterbury Tales", "The Knight's Tale", "The Miller's Tale", "The Clerk's Tale", "The Man of Law's Tale", "The Franklin's Tale", "The Physician's Tale", "The Nun's Priest's Tale"]),
    ("Troilus and Criseyde", "Chaucer's", [257], ["Troilus and Criseyde"]),
    ("Le Morte d'Arthur", "Malory's", [1251, 1252], ["Le Morte d'Arthur"]),
    ("The Faerie Queene", "Spenser's", [70717, 72698, 15272], ["The Faerie Queene", "List of characters in The Faerie Queene"]),
    ("The Countess of Pembroke's Arcadia", "Sidney's", [70854], ["The Countess of Pembroke's Arcadia"]),
    ("Paradise Lost", "Milton's", [26], ["Paradise Lost"]),
    ("The Pilgrim's Progress", "Bunyan's", [131], ["The Pilgrim's Progress"]),
    ("Pamela", "Richardson's", [6124, 12958], ["Pamela; or, Virtue Rewarded"]),
    ("Clarissa", "Richardson's", [9296, 9798, 9881, 10462, 10799, 11364, 11889, 12180, 12398], ["Clarissa"]),
    ("Joseph Andrews", "Fielding's", [9611, 9609], ["Joseph Andrews"]),
    ("Tom Jones", "Fielding's", [6593], ["The History of Tom Jones, a Foundling"]),
    ("Amelia", "Fielding's", [6098], ["Amelia (novel)"]),
    ("Gulliver's Travels", "Swift's", [829], ["Gulliver's Travels"]),
    ("Cadenus and Vanessa", "Swift's", [13621, 14353], ["Cadenus and Vanessa"]),
    ("Sense and Sensibility", "Jane Austen's", [161], ["Sense and Sensibility"]),
    ("Pride and Prejudice", "Jane Austen's", [1342], ["Pride and Prejudice", "List of Pride and Prejudice characters"]),
    ("Mansfield Park", "Jane Austen's", [141], ["Mansfield Park"]),
    ("Emma", "Jane Austen's", [158], ["Emma (novel)"]),
    ("Northanger Abbey", "Jane Austen's", [121], ["Northanger Abbey"]),
    ("Persuasion", "Jane Austen's", [105], ["Persuasion (novel)"]),
    ("Lady Susan", "Jane Austen's", [946], ["Lady Susan"]),
    ("Jane Eyre", "Charlotte Brontë's", [1260], ["Jane Eyre", "List of Jane Eyre characters"]),
    ("Shirley", "Charlotte Brontë's", [30486], ["Shirley (novel)"]),
    ("Villette", "Charlotte Brontë's", [9182], ["Villette (novel)"]),
    ("The Professor", "Charlotte Brontë's", [1028], ["The Professor (novel)"]),
    ("Wuthering Heights", "Emily Brontë's", [768], ["Wuthering Heights"]),
    ("Agnes Grey", "Anne Brontë's", [767], ["Agnes Grey"]),
    ("The Tenant of Wildfell Hall", "Anne Brontë's", [969], ["The Tenant of Wildfell Hall"]),
    ("The Pickwick Papers", "Dickens's", [580], ["The Pickwick Papers"]),
    ("Oliver Twist", "Dickens's", [730], ["Oliver Twist", "List of Oliver Twist characters"]),
    ("Nicholas Nickleby", "Dickens's", [967], ["Nicholas Nickleby", "List of Nicholas Nickleby characters"]),
    ("The Old Curiosity Shop", "Dickens's", [700], ["The Old Curiosity Shop"]),
    ("Barnaby Rudge", "Dickens's", [917], ["Barnaby Rudge"]),
    ("A Christmas Carol", "Dickens's", [46], ["A Christmas Carol"]),
    ("Martin Chuzzlewit", "Dickens's", [968], ["Martin Chuzzlewit"]),
    ("Dombey and Son", "Dickens's", [821], ["Dombey and Son"]),
    ("David Copperfield", "Dickens's", [766], ["David Copperfield", "List of David Copperfield characters"]),
    ("Bleak House", "Dickens's", [1023], ["Bleak House"]),
    ("Hard Times", "Dickens's", [786], ["Hard Times (novel)"]),
    ("Little Dorrit", "Dickens's", [963], ["Little Dorrit"]),
    ("A Tale of Two Cities", "Dickens's", [98], ["A Tale of Two Cities"]),
    ("Great Expectations", "Dickens's", [1400], ["Great Expectations", "List of Great Expectations characters"]),
    ("Our Mutual Friend", "Dickens's", [883], ["Our Mutual Friend"]),
    ("The Mystery of Edwin Drood", "Dickens's", [564], ["The Mystery of Edwin Drood"]),
    ("Adam Bede", "George Eliot's", [507], ["Adam Bede"]),
    ("The Mill on the Floss", "George Eliot's", [6688], ["The Mill on the Floss"]),
    ("Silas Marner", "George Eliot's", [550], ["Silas Marner"]),
    ("Romola", "George Eliot's", [24020], ["Romola"]),
    ("Felix Holt, the Radical", "George Eliot's", [40882], ["Felix Holt, the Radical"]),
    ("Middlemarch", "George Eliot's", [145], ["Middlemarch"]),
    ("Daniel Deronda", "George Eliot's", [7469], ["Daniel Deronda"]),
    ("Under the Greenwood Tree", "Hardy's", [2662], ["Under the Greenwood Tree"]),
    ("A Pair of Blue Eyes", "Hardy's", [224], ["A Pair of Blue Eyes"]),
    ("Far from the Madding Crowd", "Hardy's", [27], ["Far from the Madding Crowd"]),
    ("The Hand of Ethelberta", "Hardy's", [3469], ["The Hand of Ethelberta"]),
    ("The Return of the Native", "Hardy's", [122], ["The Return of the Native"]),
    ("The Trumpet-Major", "Hardy's", [2864], ["The Trumpet-Major"]),
    ("Two on a Tower", "Hardy's", [3146], ["Two on a Tower"]),
    ("The Mayor of Casterbridge", "Hardy's", [143], ["The Mayor of Casterbridge"]),
    ("The Woodlanders", "Hardy's", [482], ["The Woodlanders"]),
    ("Tess of the d'Urbervilles", "Hardy's", [110], ["Tess of the d'Urbervilles"]),
    ("Jude the Obscure", "Hardy's", [153], ["Jude the Obscure"]),
    ("The Warden", "Trollope's", [619], ["The Warden"]),
    ("Barchester Towers", "Trollope's", [3409], ["Barchester Towers"]),
    ("Doctor Thorne", "Trollope's", [3166], ["Doctor Thorne"]),
    ("Framley Parsonage", "Trollope's", [2860], ["Framley Parsonage"]),
    ("The Small House at Allington", "Trollope's", [4599], ["The Small House at Allington"]),
    ("The Last Chronicle of Barset", "Trollope's", [3045], ["The Last Chronicle of Barset"]),
    ("Can You Forgive Her?", "Trollope's", [19500], ["Can You Forgive Her?"]),
    ("Phineas Finn", "Trollope's", [18000], ["Phineas Finn"]),
    ("The Way We Live Now", "Trollope's", [5231], ["The Way We Live Now"]),
    ("Mary Barton", "Elizabeth Gaskell's", [2153], ["Mary Barton"]),
    ("Cranford", "Elizabeth Gaskell's", [394], ["Cranford (novel)"]),
    ("Ruth", "Elizabeth Gaskell's", [4275], ["Ruth (novel)"]),
    ("North and South", "Elizabeth Gaskell's", [4276], ["North and South (Gaskell novel)"]),
    ("Sylvia's Lovers", "Elizabeth Gaskell's", [4537], ["Sylvia's Lovers"]),
    ("Wives and Daughters", "Elizabeth Gaskell's", [4274], ["Wives and Daughters"]),
    ("Little Lord Fauntleroy", "Frances Hodgson Burnett's", [479], ["Little Lord Fauntleroy"]),
    ("A Little Princess", "Frances Hodgson Burnett's", [146], ["A Little Princess"]),
    ("The Secret Garden", "Frances Hodgson Burnett's", [113], ["The Secret Garden"]),
    ("Alice's Adventures in Wonderland", "Lewis Carroll's", [11], ["Alice's Adventures in Wonderland"]),
    ("Through the Looking-Glass", "Lewis Carroll's", [12], ["Through the Looking-Glass"]),
    ("Sylvie and Bruno", "Lewis Carroll's", [620], ["Sylvie and Bruno"]),
    ("The Jungle Book", "Kipling's", [236], ["The Jungle Book"]),
    ("The Second Jungle Book", "Kipling's", [1937], ["The Second Jungle Book"]),
    ("Captains Courageous", "Kipling's", [2186], ["Captains Courageous"]),
    ("Stalky & Co.", "Kipling's", [3006], ["Stalky & Co."]),
    ("Kim", "Kipling's", [2226], ["Kim (novel)"]),
    ("Just So Stories", "Kipling's", [2781], ["Just So Stories"]),
    ("Puck of Pook's Hill", "Kipling's", [557], ["Puck of Pook's Hill"]),
    ("Lorna Doone", "R. D. Blackmore's", [840], ["Lorna Doone"]),
    ("Peter Pan", "J. M. Barrie's", [16], ["Peter and Wendy", "Peter Pan"]),
    ("The Voyage Out", "Virginia Woolf's", [144], ["The Voyage Out"]),
    ("Night and Day", "Virginia Woolf's", [1245], ["Night and Day (Woolf novel)"]),
    ("Jacob's Room", "Virginia Woolf's", [5670], ["Jacob's Room"]),
    ("Mrs Dalloway", "Virginia Woolf's", [71865], ["Mrs Dalloway"]),
]
# Shakespeare: the plays in Gutenberg #100, each with its Dramatis Personae, and the Wikipedia page for its date
SHAKESPEARE = {
    "ALL’S WELL THAT ENDS WELL": "All's Well That Ends Well", "THE TRAGEDY OF ANTONY AND CLEOPATRA": "Antony and Cleopatra", "AS YOU LIKE IT": "As You Like It",
    "THE COMEDY OF ERRORS": "The Comedy of Errors", "THE TRAGEDY OF CORIOLANUS": "Coriolanus", "CYMBELINE": "Cymbeline",
    "THE TRAGEDY OF HAMLET, PRINCE OF DENMARK": "Hamlet", "THE FIRST PART OF KING HENRY THE FOURTH": "Henry IV, Part 1",
    "THE SECOND PART OF KING HENRY THE FOURTH": "Henry IV, Part 2", "THE LIFE OF KING HENRY THE FIFTH": "Henry V (play)",
    "THE FIRST PART OF HENRY THE SIXTH": "Henry VI, Part 1", "THE SECOND PART OF KING HENRY THE SIXTH": "Henry VI, Part 2",
    "THE THIRD PART OF KING HENRY THE SIXTH": "Henry VI, Part 3", "KING HENRY THE EIGHTH": "Henry VIII (play)", "THE LIFE AND DEATH OF KING JOHN": "King John (play)",
    "THE TRAGEDY OF JULIUS CAESAR": "Julius Caesar (play)", "THE TRAGEDY OF KING LEAR": "King Lear", "LOVE’S LABOUR’S LOST": "Love's Labour's Lost",
    "THE TRAGEDY OF MACBETH": "Macbeth", "MEASURE FOR MEASURE": "Measure for Measure", "THE MERCHANT OF VENICE": "The Merchant of Venice",
    "THE MERRY WIVES OF WINDSOR": "The Merry Wives of Windsor", "A MIDSUMMER NIGHT’S DREAM": "A Midsummer Night's Dream", "MUCH ADO ABOUT NOTHING": "Much Ado About Nothing",
    "THE TRAGEDY OF OTHELLO, THE MOOR OF VENICE": "Othello", "PERICLES, PRINCE OF TYRE": "Pericles, Prince of Tyre", "KING RICHARD THE SECOND": "Richard II (play)",
    "KING RICHARD THE THIRD": "Richard III (play)", "THE TRAGEDY OF ROMEO AND JULIET": "Romeo and Juliet", "THE TAMING OF THE SHREW": "The Taming of the Shrew",
    "THE TEMPEST": "The Tempest", "THE LIFE OF TIMON OF ATHENS": "Timon of Athens", "THE TRAGEDY OF TITUS ANDRONICUS": "Titus Andronicus",
    "TROILUS AND CRESSIDA": "Troilus and Cressida", "TWELFTH NIGHT; OR, WHAT YOU WILL": "Twelfth Night", "THE TWO GENTLEMEN OF VERONA": "The Two Gentlemen of Verona",
    "THE TWO NOBLE KINSMEN": "The Two Noble Kinsmen", "THE WINTER’S TALE": "The Winter's Tale"}
SHORT = {"Hamlet": "Hamlet", "Henry V (play)": "Henry V", "Henry VIII (play)": "Henry VIII", "King John (play)": "King John", "Julius Caesar (play)": "Julius Caesar",
         "Richard II (play)": "Richard II", "Richard III (play)": "Richard III"}
SH_POEMS = [("Venus and Adonis", [1045], ["Venus and Adonis (Shakespeare poem)"]), ("The Rape of Lucrece", [100], ["The Rape of Lucrece"])]

MALE_T = {"Mr", "Mr.", "Master", "Sir", "Lord", "King", "Prince", "Duke", "Earl", "Count", "Baron", "Marquis", "Marquess", "Father", "Friar", "Brother", "Uncle",
          "Emperor", "Abbot", "Bishop", "Archbishop", "Cardinal", "Monsieur", "Signor", "Signior", "Don", "Squire", "Parson", "Reverend", "Rev.", "Rev"}
FEMALE_T = {"Mrs", "Mrs.", "Miss", "Ms", "Mistress", "Lady", "Dame", "Queen", "Princess", "Duchess", "Countess", "Baroness", "Marchioness", "Mother", "Sister",
            "Aunt", "Empress", "Abbess", "Madame", "Mademoiselle", "Madam", "Signora", "Donna", "Nurse"}
OTHER_T = {"Dr", "Dr.", "Doctor", "Captain", "Capt.", "Colonel", "Col.", "Major", "General", "Admiral", "Lieutenant", "Lt.", "Sergeant", "Professor", "Judge",
           "Old", "Young", "Little", "Saint", "St", "St.", "The", "A", "An", "Giant", "Cousin", "Corporal", "Ensign", "Pastor", "Deacon", "Mynheer", "Herr", "Frau",
           "Big", "Tiny", "Poor", "Good", "Goodman", "Goody", "Widow", "Gaffer", "Grandfather", "Grandmother", "Granny", "Monseigneur", "Senior", "Junior", "Mme", "Mlle"}
# a title before a single word: these name the person by their given name (Sir Toby, Queen Margaret); the rest by surname (Mrs Bennet, Lady Russell)
GIVEN_AFTER = {"Sir", "King", "Queen", "Prince", "Princess", "Emperor", "Empress", "Friar", "Brother", "Sister", "Saint", "St", "St.", "Duke", "Duchess", "Count",
               "Countess", "Don", "Donna", "Signor", "Signior", "Signora", "Little", "Young", "Old", "Cousin", "Nurse"}
NOT_GIVEN = {"Senior", "Junior", "Elder", "Younger", "Ghost", "Chorus", "Prologue", "Epilogue", "Fool", "Clown", "Porter", "Nurse", "Page", "Boy", "Girl",
             "Servant", "Messenger", "Lord", "Lady", "Sir", "King", "Queen", "Gentleman", "Gentlewoman", "Captain", "Doctor", "Duke", "Earl", "Officer", "Soldier",
             "Mayor", "Sheriff", "Mother", "Father", "Old", "Young", "Mr", "Mrs", "Miss", "Master", "Mistress", "First", "Second", "Third", "Another", "Other", "All",
             "Both", "Several", "Two", "Three", "Citizen", "Citizens", "Lords", "Ladies", "Attendants", "Spirit", "Spirits", "Witch", "Witches", "Narrator", "Characters",
             "Main", "Minor", "Major", "Other", "The", "His", "Her", "Their", "Its", "Who", "Mister", "Madam", "Uncle", "Aunt", "Grandmother", "Grandfather", "God",
             "Christ", "Jesus", "Satan", "Death", "Sin", "Night", "Chaos", "Time", "Rumour", "Hymen", "Book", "Volume", "Part", "Chapter", "Canto", "Act", "Scene",
             "Bishop", "Archbishop", "Cardinal", "Prince", "Princess", "Emperor", "Pope", "Friar", "Abbot", "Abbess", "Governor", "General", "Colonel", "Squire",
             "Parson", "Vicar", "Rector", "Curate", "Dean", "Lieutenant", "Sergeant", "Corporal", "Constable", "Judge", "Count", "Countess", "Baron", "Marquis",
             "Mrs.", "Mr.", "Dr", "Dr.", "St", "Saint", "Widow", "Wife", "Husband", "Son", "Daughter", "Brother", "Sister", "Cousin", "Nephew", "Niece", "Child",
             "Children", "Family", "House", "Hall", "Street", "London", "England", "English", "French", "Ancient", "Modern"}
ROLE_F = {"female", "daughter", "wife", "sister", "mother", "widow", "niece", "aunt", "girl", "woman", "lady", "gentlewoman", "maid", "maiden", "queen", "princess",
          "duchess", "countess", "heroine", "mistress", "wench", "shepherdess", "hostess", "governess", "actress", "stepmother", "stepdaughter", "granddaughter",
          "grandmother", "nun", "abbess", "fiancée", "baroness", "housekeeper", "spinster", "sister-in-law", "daughter-in-law", "mother-in-law", "goddess"}
ROLE_M = {"male", "son", "husband", "brother", "father", "widower", "nephew", "uncle", "boy", "man", "gentleman", "king", "prince", "duke", "earl", "lord", "hero",
          "fellow", "shepherd", "host", "stepfather", "stepson", "grandson", "grandfather", "monk", "friar", "abbot", "fiancé", "baron", "count", "knight",
          "brother-in-law", "son-in-law", "father-in-law", "squire", "clergyman", "priest", "vicar", "rector", "curate", "bishop", "archbishop", "god", "emperor",
          "nobleman", "tradesman", "schoolmaster", "butler", "footman", "groom", "bridegroom", "parson", "chaplain", "cardinal", "marquis", "sir"}

def wiki_pages(titles):
    """wikitext and Wikidata item of English Wikipedia pages (redirects followed)."""
    out = {}
    for i in range(0, len(titles), 20):
        chunk = titles[i:i + 20]
        q = dict(action="query", prop="revisions|pageprops", rvprop="content", rvslots="main", titles="|".join(chunk), redirects=1, format="json",
                 formatversion=2, maxlag=5)
        d = json.loads(get("https://en.wikipedia.org/w/api.php", data=urllib.parse.urlencode(q).encode()))
        alias = {r["from"]: r["to"] for r in d["query"].get("redirects", []) + d["query"].get("normalized", [])}
        got = {p["title"]: (p.get("revisions", [{}])[0].get("slots", {}).get("main", {}).get("content", ""), p.get("pageprops", {}).get("wikibase_item", ""))
               for p in d["query"]["pages"] if not p.get("missing")}
        for t in chunk:
            u = alias.get(alias.get(t, t), alias.get(t, t))
            if u in got: out[t] = {"title": u, "text": got[u][0], "qid": got[u][1]}
        time.sleep(1)
    return out

def char_entries(text):
    """(name, description) for each character a Wikipedia article lists in its Characters sections."""
    out, keep, level = [], False, 0
    for line in text.split("\n"):
        h = re.match(r"^(=+)\s*(.*?)\s*=+\s*$", line)
        if h:
            lv = len(h.group(1))
            if re.search(r"character|dramatis|personae|cast|pilgrims|the knights|family", h.group(2), re.I) and not re.search(r"adaptation|film|televis|radio|stage", h.group(2), re.I):
                keep, level = True, lv
            elif keep and lv <= level: keep = False
            continue
        if not keep: continue
        line = re.sub(r"<ref.*?</ref>|<ref[^>]*/>|\{\{(?:efn|sfn|refn|cite)[^{}]*\}\}", "", line)
        line = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", line)
        line = re.sub(r"\{\{(?:nowrap|lang|em|small)\|(?:[a-z-]+\|)?([^{}|]*)\}\}", r"\1", line)
        heads = []
        m = re.match(r"^[*#;:]+\s*(.*)$", line)
        if m:
            body = m.group(1)
            b = re.match(r"^'''(.+?)'''\s*(.*)$", body)
            if b: heads.append((b.group(1), b.group(2)))
            else:
                parts = re.split(r"\s+[–—-]\s+|:\s|,\s|\s\(", body, 1)
                words = parts[0].split()
                if len(parts) == 2 and len(words) <= 4 and all(w[:1].isupper() or w in ("de", "van", "von", "le", "la", "of", "the", "d'") for w in words):
                    heads.append((parts[0], parts[1]))
        for b in re.finditer(r"'''(.+?)'''", line):
            if not heads or b.group(1) != heads[0][0]: heads.append((b.group(1), line[b.end():]))
        for name, desc in heads:
            name = re.sub(r"''|\{\{[^{}]*\}\}|\"[^\"]*\"|“[^”]*”|\([^)]*\)", "", name).strip(" ,.:;'")
            for alt in re.split(r"\s+(?:and|or)\s+|/|;", name):
                if alt.strip(): out.append((alt.strip(), clean(desc)[:400]))
    return out

def given_of(full):
    """(given name, sex from a title) for a character's name, or ("", sex) when the name is a title and a surname."""
    full = re.sub(r"\([^)]*\)|\"[^\"]*\"|“[^”]*”|[,.](?=\s|$)", " ", full).replace("’", "'")
    toks = [t for t in full.split() if t]
    if toks and toks[0] in ("A", "An", "Two", "Three", "Four", "Several", "Another", "First", "Second", "Third", "Some", "Other", "All", "Both"): return "", ""
    sex, titles = "", []
    while toks and (toks[0] in MALE_T or toks[0] in FEMALE_T or toks[0] in OTHER_T or toks[0].rstrip(".") in MALE_T | FEMALE_T | OTHER_T):
        t = toks.pop(0); titles.append(t.rstrip("."))
        if t in MALE_T or t.rstrip(".") in MALE_T: sex = sex or "b"
        if t in FEMALE_T or t.rstrip(".") in FEMALE_T: sex = sex or "g"
    while toks and toks[0].lower() in ("de", "le", "la", "von", "van", "du", "of", "the"): return "", sex
    if not toks: return "", sex
    if titles and len(toks) == 1 and not set(titles) & GIVEN_AFTER: return "", sex
    g = toks[0]
    if not NAME.match(g) or g in NOT_GIVEN or len(g) < 2 or g.isupper() and len(g) > 1 and not g.istitle(): return "", sex
    return g, sex

PREP = {"to", "of", "with", "on", "in", "by", "for", "at", "from", "under", "and", "who", "whom", "whose", "that", "attending", "loved", "beloved"}
def sex_from_desc(desc):
    """The sex a description gives its subject: its own role noun before any preposition ("daughter to Cymbeline", "a Gentleman
    attending on the Duke", not "in love with the Duke"), else its pronouns when nearly all are one sex."""
    for w in re.findall(r"[a-zé-]+", desc.lower())[:14]:
        if w in PREP: break
        if w in ROLE_F: return "g"
        if w in ROLE_M: return "b"
    allw = re.findall(r"[a-z]+", desc.lower())
    m = sum(w in ("he", "him", "his", "himself") for w in allw); f = sum(w in ("she", "her", "hers", "herself") for w in allw)
    if m >= 2 and f * 4 <= m: return "b"
    if f >= 2 and m * 4 <= f: return "g"
    return ""

def dramatis_personae(text):
    """{play title in Gutenberg #100: [(name, description)]}."""
    text = text.replace("\r", "")
    out = {}
    starts = []
    contents_end = text.find("THE WINTER’S TALE") + 30
    for t in SHAKESPEARE:
        m = re.search(r"(?m)^" + re.escape(t) + r"\s*$", text[contents_end:])
        if m: starts.append((contents_end + m.start(), t))
    starts.sort()
    for i, (pos, t) in enumerate(starts):
        block = text[pos: starts[i + 1][0] if i + 1 < len(starts) else len(text)]
        dp = re.search(r"Dramatis Person\w+\s*\n(.*?)\n\s*(?:ACT|SCENE|Scene|THE SCENE|The Scene|PROLOGUE|Prologue|Induction|INDUCTION)\b", block, re.S)
        if not dp: continue
        entries = []
        for line in dp.group(1).split("\n"):
            line = line.strip()
            m = re.match(r"^([A-Z][A-Z’'\-. ]+[A-Z.])(?:\s*\(([^)]*)\))?\s*(?:,\s*(.*))?$", line)
            if m: entries.append((m.group(1).title().replace("’S", "’s"), m.group(3) or "", m.group(2) or ""))
        out[t] = entries
    return out

WD_CHARS = """SELECT ?w ?c ?label ?sex ?gn WHERE {
 VALUES ?w { %s }
 { ?c wdt:P1441 ?w } UNION { ?w wdt:P674 ?c } UNION { ?part wdt:P361 ?w. ?c wdt:P1441 ?part }
 OPTIONAL { ?c rdfs:label ?label FILTER(lang(?label)="en") }
 OPTIONAL { ?c wdt:P21 ?sex }
 OPTIONAL { ?c wdt:P735 ?g. ?g rdfs:label ?gn FILTER(lang(?gn)="en") } }"""
WD_DATES = """SELECT ?w ?pub ?inc WHERE { VALUES ?w { %s } OPTIONAL { ?w wdt:P577 ?pub } OPTIONAL { ?w wdt:P571 ?inc } }"""

def literature(wikt_sex):
    """{given name: [{"work", "by", "year", "yt", "sex"}]} for named characters confirmed in the text."""
    works = [(w, by, g, wp) for w, by, g, wp in WORKS] + [(t, "Shakespeare's", [1045] if t == "Venus and Adonis" else [100], wp) for t, _, wp in SH_POEMS]
    sh = dramatis_personae(gutenberg(100))
    titles = sorted({t for *_, wp in works for t in wp} | set(SHAKESPEARE.values()))
    wp = cached("wikipedia-works.json", lambda: wiki_pages(titles))
    qids = sorted({p["qid"] for p in wp.values() if p.get("qid")})
    dates = cached("wikidata-work-dates.json", lambda: [r for i in range(0, len(qids), 80) for r in sparql(WD_DATES % " ".join("wd:" + q for q in qids[i:i + 80]))])
    chars = cached("wikidata-characters.json", lambda: [r for i in range(0, len(qids), 40) for r in sparql(WD_CHARS % " ".join("wd:" + q for q in qids[i:i + 40]))])
    when = {}
    for r in dates:
        q = r["w"].rsplit("/", 1)[-1]
        p, c = year(r.get("pub")), year(r.get("inc"))
        cur = when.get(q, (9999, ""))
        if p and p < cur[0]: cur = (p, "")
        if c and not p and c < cur[0]: cur = (c, "c. ")
        when[q] = cur
    wdc = collections.defaultdict(list)
    for r in chars: wdc[r["w"].rsplit("/", 1)[-1]].append(r)

    found, stats = collections.defaultdict(list), collections.Counter()
    def note(given, sex, work, by, y, src_text, how, single=False, surname_check=False, wd_given=()):
        if not given: return
        if not re.search(r"\b" + re.escape(given) + r"\b", src_text):
            stats["not in the text"] += 1; return
        if single:      # a one-word entry that the text mostly uses as an ordinary word is a role (Priest, Clown), not a name
            low = len(re.findall(r"\b" + re.escape(given.lower()) + r"\b", src_text))
            mid = len(re.findall(r"[a-z,;] " + re.escape(given) + r"\b", src_text))
            if low > mid: stats["a role, not a name"] += 1; return
            if surname_check and given not in wd_given and re.search(r"\b(?:Mr|Mrs|Miss|Master|Dr|Sir|Lady|Captain|Colonel)\.? " + re.escape(given) + r"\b", src_text):
                stats["a surname (Mr/Mrs …)"] += 1; return
        sex = sex or wikt_sex.get(given, "")
        if sex not in ("b", "g", "e"): stats["no sex"] += 1; return
        found[given].append({"work": work, "by": by, "year": y, "sex": sex, "how": how})
        stats[how] += 1

    def date_of(pages):
        best = (9999, "")
        for t in pages:
            q = wp.get(t, {}).get("qid")
            if q in when and when[q][0] < best[0]: best = when[q]
        return best

    pg100 = gutenberg(100)
    for t, entries in sh.items():
        page = SHAKESPEARE[t]; y = date_of([page])
        name = SHORT.get(page, re.sub(r" \((?:play|Shakespeare)\)$", "", page))
        for full, desc, alt in entries:
            g, sx = given_of(full)
            sx = sx or sex_from_desc(desc)
            note(g, sx, name, "Shakespeare's", y, pg100, "Shakespeare: Dramatis Personae", single=len(full.split()) == 1)
        q = wp.get(page, {}).get("qid")
        for r in wdc.get(q, []):
            g = r.get("gn") or given_of(r.get("label", ""))[0]
            note(g if g and NAME.match(g) else "", SEX.get(r.get("sex", "").rsplit("/", 1)[-1], ""), name, "Shakespeare's", y, pg100, "Wikidata characters")
    for work, by, gids, pages_ in works:
        text = "\n".join(gutenberg(n) for n in gids)
        y = date_of(pages_)
        for t in pages_:
            p = wp.get(t)
            if not p: stats["Wikipedia page missing"] += 1; continue
            wd_given = {w for r in wdc.get(p.get("qid"), []) for w in (r.get("gn", ""), given_of(r.get("label", ""))[0]) if w}
            for full, desc in char_entries(p["text"]):
                g, sx = given_of(full)
                one = len(full.split()) == 1
                note(g, sx or sex_from_desc(desc), work, by, y, text, "Wikipedia character list", single=one, surname_check=one, wd_given=wd_given)
            for r in wdc.get(p.get("qid"), []):
                g = r.get("gn") or given_of(r.get("label", ""))[0]
                note(g if g and NAME.match(g) else "", SEX.get(r.get("sex", "").rsplit("/", 1)[-1], ""), work, by, y, text, "Wikidata characters")
    return found, stats

# ───────────────────────── build ─────────────────────────
def an(w): return "An" if w[:1] in "AEIOUÆ" else "A"

def main():
    os.makedirs(RAW, exist_ok=True)
    rows = {}                                   # fold → record
    def rec(name):
        k = fold(name)
        if k not in rows: rows[k] = {"name": name, "sex": set(), "lang": "", "meaning": "", "oe": [], "med": [], "early": [], "lit": [], "word": "",
                                     "written": "", "modern": "", "coined": "", "puritan": False, "src_order": [], "medrow": None}
        return rows[k]
    counts = collections.Counter()

    wen = wikt_english()
    wikt_sex = {t: v["g"] for t, v in wen.items()}
    oe_wikt = json.load(open(os.path.join(MED, "wikt-Old_English.json"), encoding="utf-8"))
    me_wikt = json.load(open(os.path.join(MED, "wikt-Middle_English.json"), encoding="utf-8"))
    oe_keys = {loose(t) for t in oe_wikt}
    med_oe = {loose(r[0]) for r in json.load(open(os.path.join(ROOT, "data", "medieval-names.json"), encoding="utf-8")) if r[3] == "Old English"}
    # modern descendants that a source states: the Old English entry's Descendants, or an English entry "from Old English X"
    modern = {}
    for t, e in oe_wikt.items():
        _, sec = given_name_section(e["text"], ["Old English"])
        m = modern_form(sec, t) if sec else ""
        if m and NAME.match(m) and fold(m) != fold(plain_oe(t)): modern[loose(plain_oe(t))] = m
    for t, v in wen.items():
        if v.get("oe") and NAME.match(t):
            k = loose(plain_oe(clean(v["oe"])))
            if k != loose(t): modern.setdefault(k, t)

    # 1. Old English: Wiktionary
    for t, e in sorted(oe_wikt.items()):
        _, sec = given_name_section(e["text"], ["Old English"])
        if not sec: continue
        name = plain_oe(t)
        if not NAME.match(name): continue
        r = rec(name); r["sex"].add(e["g"]); r["lang"] = "Old English"
        if name != t: r["written"] = r["written"] or t
        chain, meaning = etymology(sec)
        r["meaning"] = r["meaning"] or meaning
        if "wikt-oe" not in r["src_order"]: r["src_order"].append("wikt-oe")
        counts["Wiktionary Old English"] += 1
    # 2. Old English: people recorded in PASE (Wikidata)
    pase = pase_people()
    for p in sorted(pase, key=lambda p: -p["links"]):
        name = p["name"]
        native = p["native"]
        r = rec(name); r["sex"].add(p["sex"])
        confirmed = loose(name) in oe_keys or loose(name) in modern or loose(name) in med_oe
        if confirmed: r["lang"] = "Old English"
        if native and native != name and plain_oe(native) == name: r["written"] = r["written"] or native
        r["oe"].append(p)
        counts["PASE people (Wikidata)"] += 1

    # 3. Medieval: data/medieval-names.json (Old English and medieval English rows), Wiktionary Middle English, DMNES citations
    for row in json.load(open(os.path.join(ROOT, "data", "medieval-names.json"), encoding="utf-8")):
        if row[2] not in ("Old English", "Medieval English"): continue
        name = plain_oe(row[0]) if row[2] == "Old English" else row[0]
        if not NAME.match(name): continue
        r = rec(name); r["sex"].add(row[1]); r["medrow"] = row
        if row[2] == "Old English": r["lang"] = "Old English"
        if name != row[0]: r["written"] = r["written"] or row[0]
        r["meaning"] = r["meaning"] or row[5]
        counts["medieval-names.json (" + row[2] + ")"] += 1
    for t, e in sorted(me_wikt.items()):
        _, sec = given_name_section(e["text"], ["Middle English"])
        if not sec or not NAME.match(t): continue
        r = rec(t); r["sex"].add(e["g"]); r["lang"] = r["lang"] or "Middle English"
        chain, meaning = etymology(sec); r["meaning"] = r["meaning"] or meaning
        r["med"].append(("Middle English given name (Wiktionary)", 1500)); counts["Wiktionary Middle English"] += 1
    dm = dmnes()
    for name, d in dm.items():
        r = rec(name); r["sex"].add(d["g"])
        if d["year"] < 1500: r["lang"] = r["lang"] or "Middle English"
        era = "Medieval English" if d["year"] < 1500 else "Early modern English"
        r["med"].append((f"{era} (DMNES, {d['year']}: {d['form']})", d["year"])); counts["DMNES citations"] += 1

    # 4. Early modern: Bardsley's register entries
    for n, o in bardsley().items():
        if not NAME.match(n): continue
        r = rec(n)
        if o["b"]: r["sex"].add("b")
        if o["g"]: r["sex"].add("g")
        r["early"].append(o["year"]); counts["Bardsley register entries"] += 1

    # 5. Wiktionary English: Old/Middle English origin, word names, English surnames, Puritan, coined
    for t, v in wen.items():
        if not NAME.match(t): continue
        k = fold(t)
        if not (v.get("kind") or v.get("puritan") or v.get("coined") or k in rows): continue
        r = rec(t); r["sex"].add(v["g"])
        r["meaning"] = r["meaning"] or v["meaning"]
        if v.get("puritan"): r["puritan"] = True
        if v.get("coined"): r["coined"] = v["coined"]
        if v.get("kind") and not r["word"]: r["word"] = (v["kind"], v["chain"])
        if v.get("kind") or v.get("puritan") or v.get("coined"): counts["Wiktionary English (" + (v.get("kind") or ("puritan" if v.get("puritan") else "coined")) + ")"] += 1

    # 6. Literature
    lit, lstats = literature(wikt_sex)
    for g, hits in lit.items():
        r = rec(g)
        for h in hits: r["sex"].add(h["sex"])
        r["lit"] = hits
        if g in wen:
            r["meaning"] = r["meaning"] or wen[g]["meaning"]
            if wen[g].get("coined"): r["coined"] = wen[g]["coined"]
    counts["literary names"] = len(lit)

    # rows
    out = []
    for k, r in sorted(rows.items(), key=lambda kv: kv[0]):
        sx = r["sex"] - {""}
        if not sx: continue
        g = "e" if "e" in sx or {"b", "g"} <= sx else sx.pop()
        parts, also = [], []
        lang = r["lang"]
        if r["oe"]:
            best = r["oe"][0]
            who = best["en"] + (f", {best['desc']}" if best["desc"] and len(best["desc"]) < 70 else "")
            d = best["died"] and f", d. {best['died']}" or (best["fl"] and f", fl. {best['fl']}" or "")
            n = len(r["oe"])
            parts.append(("Old English" if lang == "Old English" else "Anglo-Saxon England") + f"; recorded in PASE (e.g. {who}{d})" +
                         (f", {n} people" if n > 1 else "") + ".")
            also.append("Anglo-Saxon")
        elif lang == "Old English":
            mr = r["medrow"]
            if mr and "Domesday" in mr[6]: parts.append("Old English; " + mr[6].split(". ", 1)[-1].replace("Recorded", "recorded"))
            else: parts.append("Old English given name, used in England before the Norman Conquest (Wiktionary).")
            also.append("Anglo-Saxon")
        if r["written"] and lang == "Old English": parts.append(f"Written {r['written']}.")
        if lang == "Old English" and loose(r["name"]) in modern and fold(modern[loose(r["name"])]) != k: parts.append(f"Modern form: {modern[loose(r['name'])]}.")
        if r["med"]:
            first = sorted(r["med"], key=lambda x: x[1])[0]
            parts.append(first[0] + ".")
            if first[1] < 1500: lang = lang or "Middle English"; also.append("Medieval English")
        elif r["medrow"] and r["medrow"][2] == "Medieval English":
            parts.append(r["medrow"][6].replace("A medieval English name. ", "Medieval English. ").replace("A Middle English name", "Middle English"))
            lang = lang or "Middle English"; also.append("Medieval English")
        if r["word"] and not lang:
            kind, chain = r["word"]
            if kind == "oe": parts.append(f"An English name from {chain} (Wiktionary)." if chain else "An English name from Old English (Wiktionary).")
            elif kind == "me": parts.append(f"An English name from {chain} (Wiktionary)." if chain else "An English name from Middle English (Wiktionary).")
            elif kind == "word": parts.append(f"An English word name{', from ' + chain if chain else ''} (Wiktionary).")
            elif kind == "surname": parts.append(f"From an English surname{', from ' + chain if chain else ''} (Wiktionary).")
        if r["early"]:
            y = min(r["early"])
            parts.append(("Puritan virtue name, recorded" if r["puritan"] else "Recorded") +
                         f" in an English parish register in {y} (Bardsley, Curiosities of Puritan Nomenclature, 1880).")
            also.append("Puritan") if r["puritan"] else None
        elif r["puritan"]:
            parts.append("A Puritan virtue name (Wiktionary)."); also.append("Puritan")
        if r["lit"]:
            hits = sorted(r["lit"], key=lambda h: (h["year"][0], h["work"]))
            seen = list(dict.fromkeys((h["by"], h["work"], h["year"]) for h in hits))
            by, work, (y, c) = seen[0]
            when = f" ({c}{y})" if y < 9999 else ""
            s = f"In {by + ' ' if by else ''}{work}{when}"
            if len(seen) > 1:
                by2, work2, (y2, c2) = seen[1]
                s += f"; also in {by2 + ' ' if by2 else ''}{work2}" + (f" ({c2}{y2})" if y2 < 9999 else "")
                if len(seen) > 2: s += f" and {len(seen) - 2} more"
            parts.append(s + ".")
            also.append("Literary")
        if r["coined"]: parts.append(r["coined"].rstrip(".") + " (Wiktionary).")
        if not parts: continue
        lang = lang or "English"
        src = " ".join(parts)
        out.append([r["name"], g, "English", lang, "", (r["meaning"] or "")[:80], src, "", "real", list(dict.fromkeys(also))])

    with open(OUT, "w", encoding="utf-8") as f: json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(out):,} names → {os.path.relpath(OUT, ROOT)} ({os.path.getsize(OUT) // 1024} KB), {sum(1 for r in out if r[5]):,} with meanings")
    for k, v in counts.items(): print(f"  {k}: {v:,}")
    print("  by language:", dict(collections.Counter(r[3] for r in out)))
    print("  by basket:", dict(collections.Counter(a for r in out for a in r[9])))
    print("  literature:", dict(lstats))
    return out

if __name__ == "__main__":
    main()
