#!/usr/bin/env python3
# Builds data/sacred/abrahamic.tsv: names in the Hebrew Bible, the New Testament, the Mishnah, the Babylonian Talmud and
# the Qur'an, one row per (name form, figure, corpus) in the format of docs/sacred-format.md.
#
# Sources (all downloads are cached in raw/sacred/abrahamic/; delete a file or folder there to fetch it again):
#   1. STEPBible data, Tyndale House Cambridge (github.com/STEPBible/STEPBible-Data, CC BY 4.0)
#        TIPNR  every person, place and people in the Old and New Testaments, each Hebrew/Greek form with every verse
#        TBESH / TBESG  brief Hebrew and Greek lexicons: transliteration, gender of each proper name
#        TAHOT  tagged Hebrew Old Testament: used only for its English→Hebrew verse numbering (Sefaria links)
#      → Tanakh (Jewish, books as Sefaria names them, sefaria.org links in Hebrew verse numbering),
#        Old Testament and New Testament (Christian, biblegateway.com ESV links). Occurrences = TIPNR references.
#   2. Sefaria (sefaria.org API). Topic pages (people under Biblical Figures, Mishnaic People, Talmudic People) give
#      Hebrew names, sex, a Wikipedia link and curated source refs. A Mishnah / Talmud row is written only when the
#      name is found in the cited passage itself: Mishnah text "Torat Emet 357" (Public Domain), Talmud text
#      "Wikisource Talmud Bavli" (CC BY-SA). Topic metadata is CC BY-SA (Sefaria's default for its own data).
#   3. Quranic Arabic Corpus (corpus.quran.com, Kais Dukes / University of Leeds, GNU GPL): the lemma frequency list
#      gives every proper-noun (PN) lemma with its count; the search page gives its first location and the English
#      gloss; the ontology page says what the name is (prophet, angel, jinn, place …).
#   4. Wikidata (CC0) for figure ids (QIDs) and sex (P21); English Wiktionary (CC BY-SA) for spelling variants.
#
# Figure ids: a curated table for figures shared with the Qur'an (checked against Wikidata labels at build time),
# then Sefaria's Wikipedia link (matched to the TIPNR person by shared verses), then a Wikidata "human biblical figure"
# whose English label is unique and matches a TIPNR name borne by only one person; otherwise slug:<tradition>:<id>.
#
#   python3 scripts/build_sacred_abrahamic.py            # build (downloads whatever is not cached yet)
#   python3 scripts/build_sacred_abrahamic.py --fetch    # only download
import collections, difflib, hashlib, html, json, os, re, sys, time, unicodedata, urllib.error, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "raw", "sacred", "abrahamic")
OUT = os.path.join(ROOT, "data", "sacred", "abrahamic.tsv")
UA = {"User-Agent": "Lullabyte-build/1.0 (https://github.com/suhxnitiwari/baby-name-maker)"}
COLS = ("name figure_id figure sex original translit language tradition subtradition corpus text passage url occurrences "
        "entity_type name_role status relation source confidence").split()

STEP = "https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/"
STEP_FILES = {
    "tipnr.txt": "Proper Nouns/TIPNR - Translators Individualised Proper Names with all References - STEPBible.org CC BY.txt",
    "tbesh.txt": "Lexicons/TBESH - Translators Brief lexicon of Extended Strongs for Hebrew - STEPBible.org CC BY.txt",
    "tbesg.txt": "Lexicons/TBESG - Translators Brief lexicon of Extended Strongs for Greek - STEPBible.org CC BY.txt",
}
for _p in ("Gen-Deu", "Jos-Est", "Job-Sng", "Isa-Mal"):
    STEP_FILES[f"tahot-{_p}.txt"] = f"Translators Amalgamated OT+NT/TAHOT {_p} - Translators Amalgamated Hebrew OT - STEPBible.org CC BY.txt"

SRC_TIPNR = "STEPBible TIPNR (Tyndale House), CC BY 4.0"
SRC_SEFARIA = "Sefaria topics (CC BY-SA) + text: {} ({})"
SRC_QAC = "Quranic Arabic Corpus (Univ. of Leeds), GNU GPL"

_last = {}
def get(url, path, delay=0.0, tries=6):
    """Download url to RAW/path once; return its text."""
    full = os.path.join(RAW, path)
    if os.path.exists(full):
        return open(full, encoding="utf-8").read()
    host = urllib.parse.urlparse(url).netloc
    for attempt in range(tries):
        wait = _last.get(host, 0) + delay - time.time()
        if wait > 0: time.sleep(wait)
        _last[host] = time.time()
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read().decode("utf-8")
            break
        except urllib.error.HTTPError as e:
            if e.code == 404: data = ""; break
            time.sleep(3 * (attempt + 1))
        except Exception:
            time.sleep(3 * (attempt + 1))
    else:
        raise RuntimeError(f"{url} kept failing")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    tmp = full + ".part"
    open(tmp, "w", encoding="utf-8").write(data); os.replace(tmp, full)
    return data

def get_json(url, path, delay=0.0):
    t = get(url, path, delay)
    return json.loads(t) if t.strip() else None

def strip_marks(s):
    """Hebrew/Arabic/Greek without vowel points, cantillation and punctuation marks."""
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.category(c).startswith("M"))

# ─────────────────────────────────────────────────────────────
# Bible books
# ─────────────────────────────────────────────────────────────
BOOKS = ("Gen Exo Lev Num Deu Jos Jdg Rut 1Sa 2Sa 1Ki 2Ki 1Ch 2Ch Ezr Neh Est Job Psa Pro Ecc Sng Isa Jer Lam Ezk Dan Hos Jol Amo "
         "Oba Jon Mic Nam Hab Zep Hag Zec Mal Mat Mrk Luk Jhn Act Rom 1Co 2Co Gal Eph Php Col 1Th 2Th 1Ti 2Ti Tit Phm Heb Jas 1Pe "
         "2Pe 1Jn 2Jn 3Jn Jud Rev").split()
OT = BOOKS[:BOOKS.index("Mat")]; NT = BOOKS[BOOKS.index("Mat"):]
ENGLISH = dict(zip(BOOKS, ("Genesis,Exodus,Leviticus,Numbers,Deuteronomy,Joshua,Judges,Ruth,1 Samuel,2 Samuel,1 Kings,2 Kings,"
    "1 Chronicles,2 Chronicles,Ezra,Nehemiah,Esther,Job,Psalms,Proverbs,Ecclesiastes,Song of Songs,Isaiah,Jeremiah,Lamentations,"
    "Ezekiel,Daniel,Hosea,Joel,Amos,Obadiah,Jonah,Micah,Nahum,Habakkuk,Zephaniah,Haggai,Zechariah,Malachi,Matthew,Mark,Luke,John,"
    "Acts,Romans,1 Corinthians,2 Corinthians,Galatians,Ephesians,Philippians,Colossians,1 Thessalonians,2 Thessalonians,"
    "1 Timothy,2 Timothy,Titus,Philemon,Hebrews,James,1 Peter,2 Peter,1 John,2 John,3 John,Jude,Revelation").split(",")))
# Jewish order (Torah, Nevi'im, Ketuvim) and Sefaria's book titles
TANAKH = ("Gen Exo Lev Num Deu Jos Jdg 1Sa 2Sa 1Ki 2Ki Isa Jer Ezk Hos Jol Amo Oba Jon Mic Nam Hab Zep Hag Zec Mal "
          "Psa Pro Job Sng Rut Lam Ecc Est Dan Ezr Neh 1Ch 2Ch").split()
SEFARIA_BOOK = {b: ENGLISH[b].replace("1 ", "I ").replace("2 ", "II ") for b in OT}
SEFARIA_TO_STEP = {v: k for k, v in SEFARIA_BOOK.items()}
ORDER_TANAKH = {b: i for i, b in enumerate(TANAKH)}
ORDER_BIBLE = {b: i for i, b in enumerate(BOOKS)}

def fetch_step():
    for name, path in STEP_FILES.items():
        get(STEP + urllib.parse.quote(path), name)

def heb_verse_map():
    """(book, ch, v) in English numbering → (ch, v) in Hebrew numbering, from TAHOT refs like Jol.2.28(3.1).
    Also returns, per psalm, the Strong numbers in its title (English verse 0 = Hebrew verse 1): TIPNR files a name
    in a psalm title under verse 1."""
    m, titles = {}, collections.defaultdict(set)
    for p in ("Gen-Deu", "Jos-Est", "Job-Sng", "Isa-Mal"):
        for line in open(os.path.join(RAW, f"tahot-{p}.txt"), encoding="utf-8"):
            r = re.match(r"(\w+)\.(\d+)\.(\d+)\((\d+)\.(\d+)\)#", line)
            if not r: continue
            m[(r[1], int(r[2]), int(r[3]))] = (int(r[4]), int(r[5]))
            if r[1] == "Psa" and r[3] == "0":
                titles[int(r[2])] |= set(re.findall(r"H\d{4}", line.split("\t")[4] if line.count("\t") > 4 else ""))
    return m, titles

def to_hebrew(b, c, v, strong, vmap, titles):
    if b == "Psa" and v == 1 and strong[:5] in titles.get(c, ()): return (c, 1)
    return vmap.get((b, c, v), (c, v))

def lexicon(fname):
    """dStrong → (lemma, translit, morph, gloss, is_aramaic)"""
    out = {}
    for line in open(os.path.join(RAW, fname), encoding="utf-8"):
        c = line.rstrip("\n").split("\t")
        if len(c) > 6 and re.fullmatch(r"[HG]\d{4}[A-Za-z]?", c[0].strip()):
            d = c[1].split("=")[0].strip()
            e = (c[3].strip(), c[4].strip(), c[5].strip(), c[6].strip(), "Aramaic" in c[1])
            out.setdefault(d, e); out.setdefault(c[0].strip(), e)
    return out

REF = re.compile(r"\b([123]?[A-Z][a-z]{1,2})\.(\d+)\.(\d+)([a-z]?)")

ROLE_TYPE = [  # first words of TIPNR's summary → entity_type
    (r"^(prophet|prophetess)\b", "prophet"),
    (r"^(king|queen|emperor|pharaoh|prince|tetrarch|ethnarch|ruler|governor|herod)", "royal"),
    (r"^apostle", "disciple"),
]
OVERRIDE_TYPE = {"Michael@Dan.10.13-Rev": "angel", "Satan@Deu.13.13-Rev": "demon", "Abaddon@Job.26.6-Rev": "demon",
                 "Jesus@Isa.7.14-Rev": "human"}

def tipnr():
    """→ list of figures: {uid, kind, sex, label, type, forms: [{dstrong, original, names[(spelling, tags)], refs[]}]}"""
    txt = open(os.path.join(RAW, "tipnr.txt"), encoding="utf-8").read()
    figs = []
    for b in txt.split("$========== ")[1:]:
        lines = b.split("\n"); kind = lines[0].strip()
        if kind.startswith("EXCLUDED"): continue
        head = lines[1].split("\t")
        if len(head) < 9: continue
        typ = head[8].strip(); uid = head[0].split("=")[0].strip()
        summary = re.sub(r"<[^>]+>", "", head[7]).lstrip("#").strip()
        if kind.startswith("PERSON"):
            if typ in ("Male", "Female"):
                role = (re.match(r"(?:An?|The)?\s*(.*)", summary)[1] or "").lower()
                et = next((t for pat, t in ROLE_TYPE if re.search(pat, role)), "human")
            elif typ == "Group": et = "tribe"
            else: continue
        elif kind.startswith("PLACE"): et = "place"
        elif kind == "OTHER":
            if typ == "Supernatural": et = "angel" if re.search(r"\bangel\b", summary, re.I) else "deity"
            elif typ == "Group": et = "tribe"
            elif typ == "Title": et = "title"
            else: continue
        else: continue
        et = OVERRIDE_TYPE.get(uid, et)
        brief = (re.search(r"@Brief= *(.*)", b) or [None, ""])[1].strip()
        f = {"uid": uid, "kind": kind, "sex": {"Male": "boy", "Female": "girl"}.get(typ, ""), "type": et,
             "desc": head[1].strip(), "brief": brief, "forms": []}
        for l in lines[2:]:
            if not l.startswith("– "): continue
            c = l.split("\t")
            sig = c[0][2:].strip()
            if sig not in ("Named", "Spelled", "Greek", "Aramaic", "Group", "(same ref[s] with Variant)") or len(c) < 5: continue
            if sig == "Group" and et != "tribe": continue  # gentilics under a person (Abiezrite) are peoples
            if "=" not in c[2] or not REF.search(c[4]): continue
            dstrong = c[2].split("«")[0].strip(); original = c[2].split("=", 1)[1].strip()
            names = []
            for part in c[3].split(";"):
                s, _, tags = part.partition("=")
                s = s.strip()
                if re.fullmatch(r"[A-Z][A-Za-z'\-]+(?: [A-Z][A-Za-z'\-]+)*", s) and s not in [n for n, _ in names]:
                    names.append((s, tags.strip()))
            refs = [(r[1], int(r[2]), int(r[3]), r[4]) for r in REF.finditer(c[4]) if r[1] in ORDER_BIBLE]
            if names and refs:
                f["forms"].append({"sig": sig, "dstrong": dstrong, "original": original, "names": names, "refs": refs})
        if f["forms"]:
            f["label"] = f["forms"][0]["names"][0][0]
            figs.append(f)
    return figs

# ─────────────────────────────────────────────────────────────
# Sefaria
# ─────────────────────────────────────────────────────────────
SEF = "https://www.sefaria.org/api/"
SEF_DELAY = 0.7
SEF_CATS = ("biblical-figures", "mishnaic-people", "talmudic-people")

def sefaria_topic(slug, refs=True):
    q = "?with_refs=1&with_links=1" if refs else "?with_links=1"
    return get_json(SEF + "topics/" + urllib.parse.quote(slug) + q, f"sefaria/topics/{slug}.json", SEF_DELAY)

def sefaria_people():
    """slug → (category, topic json) for every person under the three categories (walks sub-categories)."""
    out, seen = {}, set()
    def walk(slug, cat, depth=0):
        if slug in seen or depth > 4: return
        seen.add(slug)
        t = sefaria_topic(slug)
        if not t: return
        kids = [l["topic"] for l in t.get("links", {}).get("is-category-of", {}).get("links", [])]
        if depth > 0 and t.get("subclass") == "person":
            out[slug] = (cat, t)
        for k in kids: walk(k, cat, depth + 1)
    for cat in SEF_CATS: walk(cat, cat)
    return out

MISHNAH_TRACTATES = ("Berakhot Peah Demai Kilayim Sheviit Terumot Maasrot Maaser_Sheni Challah Orlah Bikkurim Shabbat Eruvin "
    "Pesachim Shekalim Yoma Sukkah Beitzah Rosh_Hashanah Taanit Megillah Moed_Katan Chagigah Yevamot Ketubot Nedarim Nazir Sotah "
    "Gittin Kiddushin Bava_Kamma Bava_Metzia Bava_Batra Sanhedrin Makkot Shevuot Eduyot Avodah_Zarah Avot Horayot Zevachim "
    "Menachot Chullin Bekhorot Arakhin Temurah Keritot Meilah Tamid Middot Kinnim Kelim Oholot Negaim Parah Tahorot Mikvaot "
    "Niddah Makhshirin Zavim Tevul_Yom Yadayim Oktzin").split()
BAVLI_TRACTATES = ("Berakhot Shabbat Eruvin Pesachim Yoma Sukkah Beitzah Rosh_Hashanah Taanit Megillah Moed_Katan Chagigah "
    "Yevamot Ketubot Nedarim Nazir Sotah Gittin Kiddushin Bava_Kamma Bava_Metzia Bava_Batra Sanhedrin Makkot Shevuot Avodah_Zarah "
    "Horayot Zevachim Menachot Chullin Bekhorot Arakhin Temurah Keritot Meilah Tamid Niddah").split()
MISHNAH_VERSION, BAVLI_VERSION = ("Torat Emet 357", "Public Domain"), ("Wikisource Talmud Bavli", "CC BY-SA")

def sefaria_text(book, version, path):
    url = SEF + "v3/texts/" + urllib.parse.quote(book) + "?version=" + urllib.parse.quote("hebrew|" + version)
    d = get_json(url, path, SEF_DELAY)
    vs = [v for v in (d or {}).get("versions", []) if v.get("versionTitle") == version]
    return vs[0]["text"] if vs else []

def mishnah_text():
    """tractate (Sefaria name without 'Mishnah ') → [[mishnah text]] per chapter"""
    out = {}
    for t in MISHNAH_TRACTATES:
        book = "Pirkei_Avot" if t == "Avot" else "Mishnah_" + t
        out[t.replace("_", " ")] = sefaria_text(book, MISHNAH_VERSION[0], f"sefaria/mishnah/{t}.json")
    return out

def bavli_text():
    """tractate → list over amudim (index 0 = 1a) of [segment text]"""
    return {t.replace("_", " "): sefaria_text(t, BAVLI_VERSION[0], f"sefaria/bavli/{t}.json") for t in BAVLI_TRACTATES}

# ─────────────────────────────────────────────────────────────
# Quranic Arabic Corpus
# ─────────────────────────────────────────────────────────────
QAC = "https://corpus.quran.com/"
QAC_DELAY = 1.0

def qac_lemmas():
    """Every proper-noun lemma: [(arabic, buckwalter, count, search href)]"""
    out = []
    for page in range(1, 200):
        h = get(QAC + f"lemmas.jsp?page={page}", f"qac/lemmas-{page}.html", QAC_DELAY)
        rows = re.findall(r'<td class="at">(.*?)</td>\s*<td><a href="(/search\.jsp\?[^"]+)">(.*?)</a></td>\s*<td>(\d+)</td>\s*<td>(.*?)</td>', h, re.S)
        out += [(html.unescape(a).strip(), html.unescape(bw), int(n), html.unescape(href)) for a, href, bw, n, pos in rows if pos.strip() == "Proper noun"]
        last = max([int(x) for x in re.findall(r"lemmas\.jsp\?page=(\d+)", h)] or [0])
        if page >= last: break
    return out

def qac_search(bw, href):
    h = get(QAC + href.lstrip("/"), "qac/search-" + urllib.parse.quote(bw, safe="") + ".html", QAC_DELAY)
    rows = re.findall(r'<span class="l">\((\d+):(\d+):(\d+)\)</span> <i class="ab">(.*?)</i></td><td class="c2"><a [^>]*>(.*?)</a>', h, re.S)
    total = re.search(r"of <b>(\d+)</b>", h)
    concept = re.search(r'href="/concept\.jsp\?id=([^"]+)"', h)
    return {"locs": [(int(s), int(v), int(w)) for s, v, w, *_ in rows],
            "gloss": [re.sub(r"\([^)]*\)", "", html.unescape(g)).strip() for *_, g in rows],
            "total": int(total[1]) if total else len(rows), "concept": html.unescape(concept[1]) if concept else ""}

def qac_concept(cid):
    h = get(QAC + "concept.jsp?id=" + urllib.parse.quote(cid), "qac/concept-" + urllib.parse.quote(cid, safe="") + ".html", QAC_DELAY)
    t = re.sub(r"<[^>]+>", " ", h); t = html.unescape(re.sub(r"\s+", " ", t))
    path = re.search(r"classification in the ontology : Concept \(root\)(.*?) Quranic Concept", t)
    path = path[1].strip() if path else ""
    tr = re.search(r"Quranic Concept .*? Translation (.*?) (?:Transliteration|Categories|Verse List|[A-Z][a-z]+ is referred to)", t)
    wiki = re.search(r'href="(https?://en\.wikipedia\.org/wiki/[^"]+)"', h)
    return {"path": path, "translation": tr[1].strip() if tr else "", "wiki": wiki[1] if wiki else ""}


# ─────────────────────────────────────────────────────────────
# Build helpers
# ─────────────────────────────────────────────────────────────
def row(**kw):
    r = dict.fromkeys(COLS, ""); r.update(kw)
    return r

def step_translit(t):
    """STEPBible syllabified transliteration ('av.ra.ham) → Avraham"""
    t = t.replace(".", "").strip().lstrip("'")
    return t[:1].upper() + t[1:]

def lex_sex(morph):
    return {"M": "boy", "F": "girl"}.get((re.match(r"[NHA]:N-([MF])", morph or "") or [None, ""])[1], "")

def short_label(f, wd_desc=""):
    if f.get("fixed_label"): return f["fixed_label"]
    t = re.split(r"[,.;(]", f.get("brief") or "")[0].strip()
    if not t or t.lower() == f["label"].lower():
        t = (f.get("desc") or "").strip(); t = t[:1].lower() + t[1:]
    return f"{f['label']}, {t}" if t else f["label"]

def bg_url(book, ch, v):
    return "https://www.biblegateway.com/passage/?search=" + urllib.parse.quote(f"{ENGLISH[book]} {ch}:{v}") + "&version=ESV"

def sefaria_url(text, ch, v):
    return "https://www.sefaria.org/" + urllib.parse.quote(text.replace(" ", "_")) + f".{ch}.{v}"

# Sefaria refs → verses in Hebrew numbering
SEF_REF = re.compile(r"^(" + "|".join(sorted(map(re.escape, SEFARIA_TO_STEP), key=len, reverse=True)) + r") (\d+)(?::(\d+))?(?:-(\d+)(?::(\d+))?)?$")
def sefaria_verses(ref):
    m = SEF_REF.match(ref)
    if not m: return set()
    b = SEFARIA_TO_STEP[m[1]]; c1 = int(m[2]); v1 = int(m[3] or 1)
    if m[5]: c2, v2 = int(m[4]), int(m[5])
    elif m[4]: c2, v2 = (c1, int(m[4])) if m[3] else (int(m[4]), 200)
    else: c2, v2 = c1, (v1 if m[3] else 200)
    out = set()
    for c in range(c1, c2 + 1):
        for v in range(v1 if c == c1 else 1, (v2 if c == c2 else 200) + 1):
            out.add((b, c, v))
        if len(out) > 400: break
    return out

def edit1(a, b):
    """edit distance ≤ 1"""
    if a == b: return True
    if abs(len(a) - len(b)) > 1: return False
    if len(a) > len(b): a, b = b, a
    for i in range(len(b)):
        if a[:i] == b[:i] and (a[i:] == b[i + 1:] or (len(a) == len(b) and a[i + 1:] == b[i + 1:])): return True
    return False

def ascii_fold(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if c.isalpha() and ord(c) < 128).lower()

HEB_LETTER = "א-ת"
def heb_norm(s):
    s = strip_marks(html.unescape(re.sub(r"<[^>]+>", " ", s)))
    s = s.replace("־", " ").replace("״", '"').replace("׳", "'")
    s = re.sub(r"(?<![" + HEB_LETTER + r"])ר['׳]\s*", "רבי ", s)
    return re.sub(r"[^א-ת\"' ]+", " ", s)

TITLE_WORDS = ("רבי", "רב", "רבן", "מר", "ר")
def name_patterns(titles):
    """Hebrew titles of a person → regexes that find the name in an unpointed text."""
    pats = set()
    for t in titles:
        t = re.sub(r"\s+", " ", heb_norm(t)).strip()
        if not t or "#" in t: continue
        words = t.split(" ")
        cores = [t]
        if words[0] in TITLE_WORDS and len(words) > 1: cores.append(" ".join(words[1:]))
        for c in cores:
            if len(c.replace(" ", "")) < 3 or c in TITLE_WORDS: continue
            pats.add(c)
    return [re.compile(r"(?<![" + HEB_LETTER + r"])(?<!בית )[ודלבכשמ]{0,3}" + re.escape(p).replace(r"\ ", r"\s+") + r"(?![" + HEB_LETTER + r"])") for p in sorted(pats)]

MISH_REF = re.compile(r"^(?:Mishnah (.+?)|Pirkei (Avot)) (\d+):(\d+)(?:-(\d+)(?::(\d+))?)?$")
BAVLI_REF = re.compile(r"^(.+?) (\d+)([ab])(?::(\d+))?(?:-(?:(\d+)([ab]):)?(\d+))?$")

def mishnah_passages(ref, M):
    """→ [(order key, citation, url, text)] for a Mishnah ref"""
    m = MISH_REF.match(ref)
    if not m: return []
    t = m[1] or m[2]
    if t not in M: return []
    ch, a = int(m[3]), int(m[4])
    b = int(m[5]) if m[5] and not m[6] else a
    out, chap = [], M[t][ch - 1] if ch - 1 < len(M[t]) else []
    for n in range(a, min(b, a + 20) + 1):
        if n - 1 < len(chap):
            name = "Pirkei Avot" if t == "Avot" else "Mishnah " + t
            out.append(((MISHNAH_TRACTATES.index(t.replace(" ", "_")), ch, n), f"{name} {ch}:{n}", sefaria_url(name, ch, n), chap[n - 1]))
    return out

def bavli_passages(ref, B):
    m = BAVLI_REF.match(ref)
    if not m or m[1] not in B: return []
    t = m[1]; daf = int(m[2]); amud = m[3]
    idx = (daf - 1) * 2 + (amud == "b")
    pages = B[t]
    if idx >= len(pages) or not pages[idx]: return []
    s1 = int(m[4] or 1)
    if m[6]: idx2 = (int(m[5]) - 1) * 2 + (m[6] == "b"); s2 = int(m[7])
    elif m[7]: idx2, s2 = idx, int(m[7])
    else: idx2, s2 = idx, (s1 if m[4] else 999)
    out = []
    for i in range(idx, min(idx2, idx + 3) + 1):
        if i >= len(pages): break
        lo = s1 if i == idx else 1; hi = s2 if i == idx2 else 999
        for n in range(lo, min(hi, len(pages[i])) + 1):
            dafname = f"{i // 2 + 1}{'ab'[i % 2]}"
            out.append(((BAVLI_TRACTATES.index(t.replace(" ", "_")), i, n), f"{t} {dafname}:{n}",
                        "https://www.sefaria.org/" + urllib.parse.quote(t.replace(" ", "_")) + f".{dafname}.{n}", pages[i][n - 1]))
    return out

GEN = {"Z": "pair (zugot)", "T": "tanna", "A": "amora", "PT": "pre-tannaitic", "GN": "geon"}
def sage_name(en):
    """Latin personal name from a Sefaria title: Rabbi Yochanan b. Napacha → Yochanan"""
    n = re.split(r" (?:b\.|ben|bar|son of|daughter of|the|of|HaNasi|haNasi|from|ha-)(?=\s|$)| \(|,", en)[0].strip()
    w = n.split(" ")
    if len(w) > 1 and w[0] in ("Rabbi", "Rav", "Rabban", "R.", "Rebbi", "Mar", "Rabbeinu", "King", "Queen"): n = " ".join(w[1:])
    return n

# ─────────────────────────────────────────────────────────────
# Qur'an helpers
# ─────────────────────────────────────────────────────────────
BW = {"'": "ʾ", ">": "ʾ", "<": "ʾ", "&": "ʾ", "}": "ʾ", "|": "ʾā", "b": "b", "p": "h", "t": "t", "v": "th", "j": "j",
      "H": "ḥ", "x": "kh", "d": "d", "*": "dh", "r": "r", "z": "z", "s": "s", "$": "sh", "S": "ṣ", "D": "ḍ", "T": "ṭ",
      "Z": "ẓ", "E": "ʿ", "g": "gh", "f": "f", "q": "q", "k": "k", "l": "l", "m": "m", "n": "n", "h": "h", "w": "w", "y": "y"}
def bw_translit(bw):
    """Buckwalter lemma (QAC) → romanization in the usual scholarly style: <iboraAhiym → Ibrāhīm"""
    if bw == "{ll~ah": return "Allāh"
    w = re.sub(r"\d+$", "", bw).replace("^", "")
    w = re.sub(r"(?<=[^aiu])[aiu]$", "", w)                                     # final case vowel
    w = re.sub(r"iy~$", "iy", w.replace("aw`", "aA").replace("iY", "iy"))
    if w[1:2] == "~": w = w[0] + w[2:]                                           # assimilated article (s~aAmiriY~)
    if w.startswith("A") and len(w) > 1 and w[1] not in "aiu": w = "|" + w[1:]   # A^dam → ʾādam
    out, i, al = [], 0, ""
    if w.startswith("{l"):
        al, w = "al-", w[2:].lstrip("o")
        if w[1:2] == "~": w = w[0] + w[2:]                                       # sun letter
    elif w.startswith("{"): w = w[1:]
    VOW = "aiuAY`oFNK~_#"
    while i < len(w):
        c, nx = w[i], w[i + 1:i + 2]
        if c == "a":
            if nx in ("A", "Y", "`"): out.append("ā"); i += 2; i += w[i:i + 1] == "`"; continue
            out.append("a")
        elif c == "i":
            if nx == "y" and w[i + 2:i + 3] not in ("a", "i", "u", "~", "A"): out.append("ī"); i += 2; continue
            out.append("i")
        elif c == "u":
            if nx == "w" and w[i + 2:i + 3] not in ("a", "i", "u", "~", "A"): out.append("ū"); i += 2; continue
            out.append("u")
        elif c in ("A", "`"): out.append("ā")
        elif c == "Y": out.append("ā" if not out or out[-1] != "ā" else "")
        elif c == "~":
            if out and out[-1] not in "aiuāīū": out.append(out[-1])
        elif c in BW: out.append(BW[c])
        i += 1
    t = "".join(out)
    if t.startswith("ʾ") and len(t) > 1: t = t[1:]                              # initial hamza is not written
    t = t.replace("ʾā", "ʾā")
    if w.endswith("p"): t = t[:-1] + ("t" if t[-2:-1] == "ā" else "")            # tāʾ marbūṭa: Janna, Manāt
    k = 1 if t[:1] in "ʿʾ" else 0
    t = t[:k] + t[k:k + 1].upper() + t[k + 1:]
    return al + t if not al else "al-" + t

# Qur'an lemma → (TIPNR figure it names, English Wikipedia article for figures without one, entity_type, name_role, relation)
# Only identifications that the Quranic Arabic Corpus ontology itself makes and that are standard in the reference
# literature are linked; contested ones (Hūd = Eber, Shuʿayb = Jethro, Idrīs = Enoch, ʿImrān, Āzar = Terah) stay separate.
QURAN = {
    "{ll~ah": (None, "Allah", "deity", "divine", ""),
    "muwsaY`": ("Moses@Exo.2.10-Rev", None, "prophet", "personal", ""),
    "$ayoTa`n": ("Satan@Deu.13.13-Rev", None, "demon", "personal", ""),
    "firoEawon": ("Pharaoh@Exo.3.10-Rom", None, "royal", "title", ""),
    "<iboraAhiym": ("Abraham@Gen.11.26-1Pe", None, "prophet", "personal", ""),
    "<isoraA}iyl": ("Israel@Gen.25.26-Rev", None, "prophet", "personal", "name of Yaʿqūb (Jacob)"),
    "nuwH": ("Noah@Gen.5.29-2Pe", None, "prophet", "personal", ""),
    "maroyam": ("Mary@Mat.1.16-Act", None, "human", "personal", ""),
    "luwT": ("Lot@Gen.11.27-2Pe", None, "prophet", "personal", ""),
    "yuwsuf": ("Joseph@Gen.30.24-Rev", None, "prophet", "personal", ""),
    "A^dam": ("Adam@Gen.2.19-Jud", None, "prophet", "personal", ""),
    "EiysaY": ("Jesus@Isa.7.14-Rev", None, "prophet", "personal", ""),
    "ha`ruwn": ("Aaron@Exo.4.14-Heb", None, "prophet", "personal", ""),
    "<isoHaAq": ("Isaac@Gen.17.19-Jas", None, "prophet", "personal", ""),
    "sulayoma`n": ("Solomon@2Sa.5.14-Act", None, "prophet", "personal", ""),
    "daAwud": ("David@Rut.4.17-Rev", None, "prophet", "personal", ""),
    "yaEoquwb": ("Israel@Gen.25.26-Rev", None, "prophet", "personal", ""),
    "<isomaAEiyl": ("Ishmael@Gen.16.11-Psa", None, "prophet", "personal", ""),
    "<iboliys": (None, "Iblis", "demon", "personal", ""),
    "$uEayob": (None, "Shuaib", "prophet", "personal", ""),
    "masiyH": ("Jesus@Isa.7.14-Rev", None, "prophet", "epithet", "epithet of ʿĪsā (Jesus): al-Masīḥ, the Messiah"),
    "Sa`liH2": (None, "Salih", "prophet", "personal", ""),
    "zakariy~aA": ("Zechariah@Luk.1.5-", None, "prophet", "personal", ""),
    "huwd": (None, "Hud (prophet)", "prophet", "personal", ""),
    "ha`ma`n": (None, "Haman (Islam)", "human", "personal", ""),
    "yaHoyaY`": ("John@Mat.3.1-Act", None, "prophet", "personal", ""),
    ">ay~uwb": ("Job@Job.1.1-Jas", None, "prophet", "personal", ""),
    "qa`ruwn": ("Korah@Exo.6.21-Jud", None, "human", "personal", ""),
    "muHam~ad": (None, "Muhammad", "prophet", "personal", ""),
    ">aHomad": (None, "Muhammad", "prophet", "epithet", "name of Muhammad (Qur'an 61:6)"),
    "yuwnus": ("Jonah@2Ki.14.25-Luk", None, "prophet", "personal", ""),
    "<iloyaAs": ("Elijah@1Ki.17.1-Jas", None, "prophet", "personal", ""),
    "jaAluwt": ("Goliath@1Sa.17.4-1Ch", None, "human", "personal", ""),
    "TaAluwt": ("Saul@1Sa.9.2-Act", None, "royal", "personal", ""),
    "jiboriyl": ("Gabriel@Dan.8.16-Luk", None, "angel", "personal", ""),
    "miykaY`l": ("Michael@Dan.10.13-Rev", None, "angel", "personal", ""),
    "s~aAmiriY~": (None, "Samiri (Islamic figure)", "human", "epithet", ""),
    "Eimora`n": (None, None, "human", "personal", ""),
    "<idoriys": (None, "Idris (prophet)", "prophet", "personal", ""),
    "{loyasaEa": ("Elisha@1Ki.19.16-Luk", None, "prophet", "personal", ""),
    "luqoma`n": (None, "Luqman", "sage", "personal", ""),
    "A^zar": (None, None, "human", "personal", ""),
    "zayod": (None, "Zayd ibn Haritha", "human", "personal", ""),
    "Euzayor": (None, "Uzair", "human", "personal", ""),
    "ma`lik2": (None, "Maalik", "angel", "personal", ""),
    "ha`ruwt": (None, None, "angel", "personal", ""),
    "ma`ruwt": (None, None, "angel", "personal", ""),
    "tub~aE": (None, None, "royal", "title", ""),
    "baEol2": ("Baal@Num.25.3-Rom", None, "deity", "divine", ""),
    "{ll~a`t": (None, "Al-Lat", "deity", "divine", ""),
    "{loEuz~aY`": (None, "Al-Uzza", "deity", "divine", ""),
    "manaw`p": (None, "Manat (goddess)", "deity", "divine", ""),
    "wad~": (None, "Wadd", "deity", "divine", ""),
    "suwaAE": (None, "Suwa'", "deity", "divine", ""),
    "yaguwv": (None, "Yaghuth", "deity", "divine", ""),
    "yaEuwq": (None, "Ya'uq", "deity", "divine", ""),
    "nasor": (None, None, "deity", "divine", ""),
}
# kinds of QAC ontology concepts that are not names of beings, places or peoples (books, religions, times, stars …)
QURAN_SKIP_PATH = ("Holy Book", "Religion", "Time", "Month", "Day", "Star", "Event", "Physical Substance", "Tree", "Food")
QURAN_SKIP = {"{ll~ahum~a", "ja`hiliy~ap2", "s~ilom", "zaq~uwm", "jumuEap", "ramaDaAn", "$~iEoraY`"}

def fold(s):
    """romanization without diacritics and ʿ ʾ: al-Yasaʿ → al-Yasa"""
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.category(c).startswith("M") and c not in "ʿʾ'")

def quran_name(glosses, translit):
    """QAC's English gloss when it is a spelling of the Arabic name (Ibrahim, Maryam), else the plain romanization."""
    core = fold(translit); core_cmp = re.sub(r"^al-", "", core).lower()
    best = collections.Counter()
    for g in glosses:
        g = g.strip()
        while True:
            g2 = re.sub(r"^(?:the|and|O|so|then|by|with|to|for|of|in|at|surely|a|an|from|on)\s+|^Al-", "", g, flags=re.I)
            if g2 == g: break
            g = g2
        if g: best[g] += 1
    for g, _ in best.most_common(3):
        if re.fullmatch(r"[A-Z][a-z']+", g) and difflib.SequenceMatcher(None, g.lower(), core_cmp).ratio() >= 0.75: return g
    return core[:1].upper() + core[1:]

def surah_names():
    d = get_json("https://api.quran.com/api/v4/chapters?language=en", "qurancom/chapters.json", 0.5)
    return {c["id"]: c["name_simple"] for c in d["chapters"]}

def wiktionary_alt_forms(word):
    """'Alternative forms' listed in the English section of en.wiktionary's entry for word (CC BY-SA)."""
    d = get_json("https://en.wiktionary.org/w/api.php?action=parse&format=json&prop=wikitext&page=" + urllib.parse.quote(word),
                 f"wiktionary/{word}.json", 0.5)
    t = (d or {}).get("parse", {}).get("wikitext", {}).get("*", "")
    eng = re.search(r"==English==(.*?)(?:\n==[^=]|$)", t, re.S)
    if not eng: return []
    alt = re.search(r"===+\s*Alternative forms\s*===+\n(.*?)(?:\n=|$)", eng[1], re.S)
    if not alt: return []
    forms = []
    for tmpl in re.findall(r"\{\{(?:l|alt|alter)\|en\|([^}]*)\}\}", alt[1]):
        for x in tmpl.split("|"):
            x = x.strip()
            if re.fullmatch(r"[A-Z][a-z'\-]+", x) and x not in forms and x != word: forms.append(x)
    return forms

# ─────────────────────────────────────────────────────────────
# Build
# ─────────────────────────────────────────────────────────────
# English Wikipedia article of TIPNR figures that are named in the Qur'an (→ one QID for every tradition)
BIBLE_WIKI = {  # uid: (article, neutral label used in every tradition)
    "Moses@Exo.2.10-Rev": ("Moses", "Moses, prophet who led the Israelites out of Egypt"),
    "Satan@Deu.13.13-Rev": ("Satan", "Satan, the adversary"),
    "Pharaoh@Exo.3.10-Rom": ("Pharaoh of the Exodus", "Pharaoh, king of Egypt in the Exodus story"),
    "Abraham@Gen.11.26-1Pe": ("Abraham", "Abraham, patriarch"),
    "Israel@Gen.25.26-Rev": ("Jacob", "Jacob (Israel), patriarch, son of Isaac"),
    "Noah@Gen.5.29-2Pe": ("Noah", "Noah, survivor of the Flood"),
    "Mary@Mat.1.16-Act": ("Mary, mother of Jesus", "Mary, mother of Jesus"),
    "Lot@Gen.11.27-2Pe": ("Lot (biblical person)", "Lot, nephew of Abraham"),
    "Joseph@Gen.30.24-Rev": ("Joseph (Genesis)", "Joseph, son of Jacob"),
    "Adam@Gen.2.19-Jud": ("Adam", "Adam, the first man"),
    "Jesus@Isa.7.14-Rev": ("Jesus", "Jesus of Nazareth"),
    "Aaron@Exo.4.14-Heb": ("Aaron", "Aaron, brother of Moses"),
    "Isaac@Gen.17.19-Jas": ("Isaac", "Isaac, son of Abraham"),
    "Solomon@2Sa.5.14-Act": ("Solomon", "Solomon, king of Israel, son of David"),
    "David@Rut.4.17-Rev": ("David", "David, king of Israel"),
    "Ishmael@Gen.16.11-Psa": ("Ishmael", "Ishmael, son of Abraham and Hagar"),
    "Zechariah@Luk.1.5-": ("Zechariah, father of John the Baptist", "Zechariah, priest, father of John the Baptist"),
    "John@Mat.3.1-Act": ("John the Baptist", "John the Baptist"),
    "Job@Job.1.1-Jas": ("Job (biblical figure)", "Job, the righteous sufferer"),
    "Korah@Exo.6.21-Jud": ("Korah", "Korah, who rebelled against Moses"),
    "Jonah@2Ki.14.25-Luk": ("Jonah", "Jonah, prophet"),
    "Elijah@1Ki.17.1-Jas": ("Elijah", "Elijah, prophet"),
    "Goliath@1Sa.17.4-1Ch": ("Goliath", "Goliath, Philistine warrior"),
    "Saul@1Sa.9.2-Act": ("Saul", "Saul, first king of Israel"),
    "Gabriel@Dan.8.16-Luk": ("Gabriel", "Gabriel, archangel"),
    "Michael@Dan.10.13-Rev": ("Michael (archangel)", "Michael, archangel"),
    "Elisha@1Ki.19.16-Luk": ("Elisha", "Elisha, prophet, successor of Elijah"),
    "Baal@Num.25.3-Rom": ("Baal", "Baal, Canaanite god"),
    "Miriam@Exo.15.20-Mic": ("Miriam", "Miriam, prophetess, sister of Moses and Aaron"),
}
EPITHETS = {"Zelotes", "Zealot", "Iscariot", "Boanerges", "Didymus", "Twin", "Magdalene", "Bar-Jonah", "Barjona"}
CONF = {"Named": 1.0, "Greek": 1.0, "Aramaic": 1.0, "Spelled": 0.95, "Group": 0.95, "(same ref[s] with Variant)": 0.9}

def main():
    fetch_step()
    figs = tipnr(); byuid = {f["uid"]: f for f in figs}
    vmap, ptitles = heb_verse_map(); H = lexicon("tbesh.txt"); G = lexicon("tbesg.txt")
    people = sefaria_people()
    print(f"TIPNR figures {len(figs)}, Sefaria people {len(people)}", file=sys.stderr)

    # ── figure ids ────────────────────────────────────────────
    ids, idsrc = {}, collections.Counter()
    sef_wiki = {slug: urllib.parse.unquote(t["properties"]["enWikiLink"]["value"].rsplit("/wiki/", 1)[1]).replace("_", " ")
                for slug, (_, t) in people.items() if "/wiki/" in t.get("properties", {}).get("enWikiLink", {}).get("value", "")}
    quran_wiki = {v[1] for v in QURAN.values() if v[1]}
    wq = wiki_qids([w for w, _ in BIBLE_WIKI.values()] + list(sef_wiki.values()) + list(quran_wiki))
    for uid, (title, lab) in BIBLE_WIKI.items():
        if uid in byuid: byuid[uid]["fixed_label"] = lab
        if uid in byuid and wq.get(title): ids[uid] = wq[title]; idsrc["curated"] += 1

    # Sefaria biblical figure ↔ TIPNR person: same Hebrew (or English) name and at least one shared verse
    by_heb, by_en = collections.defaultdict(set), collections.defaultdict(set)
    fverses = {}
    for f in figs:
        if not f["kind"].startswith("PERSON") or f["type"] == "tribe": continue
        vs = set()
        for x in f["forms"]:
            by_heb[re.sub(r"[\s־]", "", strip_marks(x["original"]))].add(f["uid"])
            for n, _ in x["names"]: by_en[n.lower()].add(f["uid"])
            for b, c, v, _ in x["refs"]:
                if b in SEFARIA_BOOK: vs.add((b,) + to_hebrew(b, c, v, x["dstrong"], vmap, ptitles))
        fverses[f["uid"]] = vs
    topic_fig = {}
    for slug, (cat, t) in people.items():
        he = {re.sub(r"[\s־]", "", strip_marks(x["text"])) for x in t.get("titles", []) if x["lang"] == "he"}
        en = {x["text"].lower() for x in t.get("titles", []) if x["lang"] == "en"}
        cands = set().union(*[by_heb.get(h, set()) for h in he], *[by_en.get(e, set()) for e in en]) if (he or en) else set()
        if not cands: continue
        verses = set().union(*[sefaria_verses(r["ref"]) for r in t.get("refs", []) if not r.get("is_sheet")] or [set()])
        if not verses: continue
        score = sorted(((len(fverses[u] & verses), u) for u in cands), reverse=True)
        if score[0][0] >= 1 and (len(score) == 1 or score[1][0] < score[0][0]):
            topic_fig[slug] = score[0][1]
    sex_of = {}
    for slug, uid in topic_fig.items():
        q = wq.get(sef_wiki.get(slug, ""))
        if q and uid not in ids and q not in ids.values(): ids[uid] = q; idsrc["sefaria"] += 1
    # Wikidata 'human biblical figure' with a unique English label that only one TIPNR person bears
    wd = wd_biblical(); wd_by_label = collections.defaultdict(list)
    for x in wd: wd_by_label[x["label"].lower()].append(x)
    tip_by_label = collections.defaultdict(list)
    for f in figs:
        if f["kind"].startswith("PERSON") and f["type"] != "tribe": tip_by_label[f["label"].lower()].append(f)
    used = set(ids.values())
    for lab, fs in tip_by_label.items():
        if len(fs) != 1 or len(wd_by_label.get(lab, [])) != 1: continue
        f, w = fs[0], wd_by_label[lab][0]
        if f["uid"] in ids or w["qid"] in used: continue
        if f["sex"] and w["sex"] and f["sex"] != w["sex"]: continue
        ids[f["uid"]] = w["qid"]; used.add(w["qid"]); idsrc["wikidata-label"] += 1
    for f in figs:
        if f["uid"] not in ids: ids[f["uid"]] = "slug:biblical:" + f["uid"].lower().replace(" ", "_")
    print("figure ids:", dict(idsrc), file=sys.stderr)
    went = wd_entities([q for q in list(ids.values()) + list(wq.values()) if q and q.startswith("Q")])
    for t, q in list(wq.items()):   # an article that is a name list or disambiguation page is not a figure
        if q and re.search(r"given name|family name|surname|disambiguation|list article|Wikimedia", went.get(q, {}).get("desc", ""), re.I): wq[t] = None
    desc = lambda q: went.get(q, {}).get("desc", "")

    rows = []
    # ── Bible ────────────────────────────────────────────────
    for f in figs:
        fid = ids[f["uid"]]; label = short_label(f, desc(fid))
        person = f["type"] not in ("place", "tribe")
        role = {"deity": "divine", "title": "title"}.get(f["type"], "personal" if person else "")
        for x in f["forms"]:
            L = H if x["dstrong"].startswith("H") else G
            lex = L.get(x["dstrong"]) or L.get(x["dstrong"][:5]) or ("", "", "", "", False)
            greek = x["dstrong"].startswith("G")
            lang = "Greek" if greek else ("Aramaic" if x["sig"] == "Aramaic" or lex[4] else "Hebrew")
            tr = step_translit(lex[1]) if lex[1] else ""
            sex = (f["sex"] or (lex_sex(lex[2]) if f["type"] not in ("deity", "angel", "demon", "title") else "") or went.get(fid, {}).get("sex", "")) if person else ""
            conf = CONF.get(x["sig"], 0.9)
            ot = [r for r in x["refs"] if r[0] in SEFARIA_BOOK]; nt = [r for r in x["refs"] if r[0] in NT]
            common = dict(figure_id=fid, figure=label, sex=sex, original=x["original"], translit=tr, language=lang,
                          entity_type=f["type"], name_role="epithet" if x["names"][0][0] in EPITHETS else role, status="attested", source=SRC_TIPNR)
            if ot and not greek:
                heb = [(b,) + to_hebrew(b, c, v, x["dstrong"], vmap, ptitles) for b, c, v, _ in ot]
                b, c, v = min(heb, key=lambda r: (ORDER_TANAKH[r[0]], r[1], r[2]))
                n = x["names"][0][0]
                rows.append(row(name=n, tradition="Jewish", corpus="Tanakh", text=SEFARIA_BOOK[b], passage=f"{SEFARIA_BOOK[b]} {c}:{v}",
                                url=sefaria_url(SEFARIA_BOOK[b], c, v), occurrences=len(ot), confidence=conf, **common))
                b, c, v, _ = min(ot, key=lambda r: (ORDER_BIBLE[r[0]], r[1], r[2]))
                for n, tags in x["names"]:
                    rows.append(row(name=n, tradition="Christian", corpus="Old Testament", text=ENGLISH[b], passage=f"{ENGLISH[b]} {c}:{v}",
                                    url=bg_url(b, c, v), occurrences=len(ot), confidence=conf if "ESV" in tags or not tags else round(conf - 0.05, 2), **common))
            if nt:
                b, c, v, _ = min(nt, key=lambda r: (ORDER_BIBLE[r[0]], r[1], r[2]))
                for n, tags in x["names"]:
                    rows.append(row(name=n, tradition="Christian", corpus="New Testament", text=ENGLISH[b], passage=f"{ENGLISH[b]} {c}:{v}",
                                    url=bg_url(b, c, v), occurrences=len(nt), confidence=conf if "ESV" in tags or not tags else round(conf - 0.05, 2), **common))

    # ── Sefaria: Hebrew-style spellings of Tanakh names (Avraham, Moshe) ──
    tanakh_rows = collections.defaultdict(list)
    for r in rows:
        if r["corpus"] == "Tanakh": tanakh_rows[r["figure_id"]].append(r)
    for slug, uid in topic_fig.items():
        t = people[slug][1]
        for r in list(tanakh_rows.get(ids[uid], [])):
            target = ascii_fold(r["translit"])
            for x in t.get("titles", []):
                n = x["text"].strip()
                if x["lang"] != "en" or not re.fullmatch(r"[A-Z][a-z']+", n) or n == r["name"]: continue
                if len(target) > 2 and edit1(ascii_fold(n), target) and not any(q["name"] == n and q["figure_id"] == r["figure_id"] for q in rows):
                    rows.append(dict(r, name=n, confidence=0.95, source=SRC_TIPNR + "; spelling: Sefaria topic title"))
                    break

    # ── Sefaria: Mishnah and Talmud ─────────────────────────
    M, B = mishnah_text(), bavli_text()
    for slug, (cat, t) in sorted(people.items()):
        titles = [x["text"] for x in t.get("titles", []) if x["lang"] == "he"]
        pats = name_patterns(titles)
        if not pats: continue
        found = {"Mishnah": [], "Talmud": []}
        for r in t.get("refs", []):
            if r.get("is_sheet"): continue
            for corpus, passages in (("Mishnah", mishnah_passages(r["ref"], M)), ("Talmud", bavli_passages(r["ref"], B))):
                for key, cite, url, text in passages:
                    if any(p.search(heb_norm(text)) for p in pats): found[corpus].append((key, cite, url))
        if not any(found.values()) or re.search(r" and |'s ", t["primaryTitle"]["en"]): continue
        uid = topic_fig.get(slug)
        if uid:
            f = byuid[uid]; fid = ids[uid]; label = short_label(f, desc(fid)); sex = f["sex"]; et = f["type"]; name = t["primaryTitle"]["en"]
        else:
            q = wq.get(sef_wiki.get(slug, ""))
            fid = q if q else "slug:jewish:" + slug
            gen = t.get("properties", {}).get("generation", {}).get("value", "")
            kind = GEN.get(re.sub(r"\d+$", "", gen), "")
            label = t["primaryTitle"]["en"] + (f", {desc(q)}" if q and desc(q) else f", {kind}" if kind else "")
            sex = {"M": "boy", "F": "girl"}.get(t.get("properties", {}).get("sex", {}).get("value", ""), "") or (went.get(q, {}).get("sex", "") if q else "")
            et = "sage" if cat in ("mishnaic-people", "talmudic-people") else "human"
            name = sage_name(t["primaryTitle"]["en"])
        for corpus, hits in found.items():
            if not hits: continue
            key, cite, url = min(hits)
            text = re.sub(r" \d+[ab]?:\d+$", "", cite)
            version = MISHNAH_VERSION if corpus == "Mishnah" else BAVLI_VERSION
            rows.append(row(name=name, figure_id=fid, figure=label, sex=sex, original=t["primaryTitle"].get("he", ""),
                            translit=t["primaryTitle"]["en"], language="Hebrew" if corpus == "Mishnah" else "Aramaic",
                            tradition="Jewish", subtradition="Rabbinic", corpus=corpus, text=text, passage=cite, url=url,
                            occurrences="", entity_type=et, name_role="title" if name in ("Rav", "Rabbi", "Mar", "Caesar") else "personal",
                            status="attested", source=SRC_SEFARIA.format(*version), confidence=0.9))

    # ── Qur'an ───────────────────────────────────────────────
    surah = surah_names()
    qent = went
    quran_names = []
    for arabic, bw, count, href in qac_lemmas():
        if bw in QURAN_SKIP: continue
        sr = qac_search(bw, href)
        c = qac_concept(sr["concept"]) if sr["concept"] else {"path": "", "translation": "", "wiki": ""}
        if any(k in c["path"] for k in QURAN_SKIP_PATH): continue
        uid, wiki, et, role, rel = QURAN.get(bw, (None, None, "", "personal", ""))
        if not et:
            p = c["path"]
            if "Historic People" in p or re.search(r"\b(Tribe|Nation|People)\b", p): et, role = "tribe", ""
            elif "Location" in p or "Living Creation" not in p: et, role = "place", ""
            elif "Angel" in p: et = "angel"
            elif "Prophet" in p or "Messenger" in p: et = "prophet"
            else: et = "human"
        if et in ("place", "tribe"): role = ""
        if uid: fid = ids[uid]
        elif wiki and wq.get(wiki): fid = wq[wiki]
        else: fid = "slug:islamic:" + ascii_fold(bw_translit(bw))
        name = quran_name(sr["gloss"], bw_translit(bw))
        s, v, _ = sr["locs"][0]
        sex = "" if et in ("place", "tribe") else ((byuid[uid]["sex"] if uid else "") or qent.get(fid, {}).get("sex", ""))
        if uid: label = short_label(byuid[uid], qent.get(fid, {}).get("desc", ""))
        elif et == "place" and c["translation"] and fold(c["translation"]).lower() != name.lower(): label = f"{name} ({c['translation']})"
        else: label = name + (f", {qent[fid]['desc']}" if qent.get(fid, {}).get("desc") else "")
        r = row(name=name, figure_id=fid, figure=label, sex=sex, original=arabic, translit=bw_translit(bw), language="Arabic",
                tradition="Islamic", corpus="Qur'an", text=f"Surah {surah.get(s, s)}", passage=f"Qur'an {s}:{v}",
                url=f"https://quran.com/{s}/{v}", occurrences=sr["total"], entity_type=et, name_role=role,
                status="attested", relation=rel, source=SRC_QAC, confidence=1.0 if sr["concept"] else 0.9)
        rows.append(r)
        bible_names = {n for x in byuid[uid]["forms"] for n, _ in x["names"]} if uid else set()
        if et not in ("place", "tribe", "deity") and role == "personal" and name not in bible_names: quran_names.append(r)

    # ── related forms ───────────────────────────────────────
    # Mary ← Miriam: TBESG (Abbott-Smith) gives Μαρία / Μαριάμ as the Greek of Aramaic and Hebrew מִרְיָם
    abbott = next((l for l in open(os.path.join(RAW, "tbesg.txt"), encoding="utf-8") if l.startswith("G3137\tG3137G")), "")
    mir = [r for r in rows if r["figure_id"] == ids.get("Miriam@Exo.15.20-Mic") and r["corpus"] == "Old Testament"]
    if "מרים" in strip_marks(abbott) and "Μαριαμ" in strip_marks(abbott) and mir:
        rows.append(dict(mir[0], name="Mary", original="Μαριάμ", translit="Mariam", language="Greek", occurrences="", status="related",
                         relation="later form of Miriam, via Greek Mariam (Μαριάμ) / Maria", confidence=0.9,
                         source="STEPBible TBESG (Abbott-Smith lexicon, G3137), CC BY 4.0"))
    for r in quran_names:
        for alt in wiktionary_alt_forms(r["name"]):
            if alt[0] != r["name"][0] or alt == r["name"] + "s" or difflib.SequenceMatcher(None, alt.lower(), r["name"].lower()).ratio() < 0.6: continue
            if any(q["name"] == alt and q["figure_id"] == r["figure_id"] and q["corpus"] == "Qur'an" for q in rows): continue
            rows.append(dict(r, name=alt, occurrences="", status="related", relation=f"spelling variant of {r['name']}",
                             source="English Wiktionary, 'Alternative forms' of " + r["name"] + " (CC BY-SA 4.0)", confidence=0.8))

    # ── write ───────────────────────────────────────────────
    seen, out = set(), []
    for r in rows:
        k = (r["name"], r["figure_id"], r["tradition"], r["corpus"], r["original"], r["status"])
        if k in seen: continue
        seen.add(k); out.append(r)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\t".join(COLS) + "\n")
        for r in out:
            fh.write("\t".join(str(r[c]).replace("\t", " ").replace("\n", " ") for c in COLS) + "\n")
    cnt = collections.Counter((r["tradition"], r["corpus"], r["status"]) for r in out)
    for k, v in sorted(cnt.items()): print(*k, v, sep="\t", file=sys.stderr)
    print(f"{len(out)} rows → {os.path.relpath(OUT, ROOT)}", file=sys.stderr)



# ─────────────────────────────────────────────────────────────
# Wikidata
# ─────────────────────────────────────────────────────────────
WDQS = "https://query.wikidata.org/sparql?format=json&query="
WD_SEX = {"Q6581097": "boy", "Q6581072": "girl", "Q2449503": "boy", "Q1052281": "girl"}

def wd_biblical():
    """Wikidata items that are a 'human biblical figure' (Q20643955): [{qid, label, desc, sex}]"""
    q = ('SELECT ?p ?l ?d ?sex WHERE { ?p wdt:P31 wd:Q20643955 . ?p rdfs:label ?l FILTER(lang(?l)="en") '
         'OPTIONAL{?p schema:description ?d FILTER(lang(?d)="en")} OPTIONAL{?p wdt:P21 ?sex} }')
    d = get_json(WDQS + urllib.parse.quote(q), "wikidata/biblical-figures.json", 1.0)
    out = {}
    for r in d["results"]["bindings"]:
        qid = r["p"]["value"].rsplit("/", 1)[1]
        out.setdefault(qid, {"qid": qid, "label": r["l"]["value"], "desc": r.get("d", {}).get("value", ""),
                             "sex": WD_SEX.get(r.get("sex", {}).get("value", "").rsplit("/", 1)[-1], "")})
    return list(out.values())

def wd_entities(qids):
    """qid → {label, desc, sex}"""
    out, qids = {}, sorted(set(qids))
    for i in range(0, len(qids), 50):
        chunk = qids[i:i + 50]; key = hashlib.md5("|".join(chunk).encode()).hexdigest()[:10]
        d = get_json("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=labels|descriptions|claims&languages=en&ids="
                     + "|".join(chunk), f"wikidata/entities-{chunk[0]}-{key}.json", 0.5)
        for k, v in d.get("entities", {}).items():
            sex = [c["mainsnak"].get("datavalue", {}).get("value", {}).get("id") for c in v.get("claims", {}).get("P21", [])]
            out[k] = {"label": v.get("labels", {}).get("en", {}).get("value", ""),
                      "desc": v.get("descriptions", {}).get("en", {}).get("value", ""),
                      "sex": WD_SEX.get(sex[0], "") if len(sex) == 1 else ""}
    return out

def wiki_qids(titles):
    """English Wikipedia titles → QID (follows redirects)."""
    out, titles = {}, sorted(set(titles))
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        key = hashlib.md5("|".join(chunk).encode()).hexdigest()[:10]
        d = get_json("https://en.wikipedia.org/w/api.php?action=query&format=json&formatversion=2&prop=pageprops&ppprop=wikibase_item&redirects=1&titles="
                     + urllib.parse.quote("|".join(chunk)), f"wikidata/enwiki-{chunk[0][:20].replace('/', '_')}-{key}.json", 0.5)
        q = d.get("query", {})
        norm = {x["from"]: x["to"] for x in q.get("normalized", [])}; red = {x["from"]: x["to"] for x in q.get("redirects", [])}
        pp = {p["title"]: p.get("pageprops", {}).get("wikibase_item") for p in q.get("pages", [])}
        for t in chunk:
            a = norm.get(t, t); out[t] = pp.get(red.get(a, a))
    return out


if __name__ == "__main__":
    if "--fetch" in sys.argv:
        fetch_step()
        print("sefaria people:", len(sefaria_people()))
        mishnah_text(); bavli_text()
        for a, bw, n, href in qac_lemmas():
            s = qac_search(bw, href)
            if s["concept"]: qac_concept(s["concept"])
        print("fetched")
    else:
        main()
