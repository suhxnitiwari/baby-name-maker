#!/usr/bin/env python3
# Builds data/sacred/abrahamic2.tsv (+ abrahamic2-review.tsv for doubtful rows): names in the later texts of the
# Abrahamic traditions, one row per (name form, figure, corpus) in the format of docs/sacred-format.md. Figure ids are
# the ones scripts/build_sacred_abrahamic.py gives (Wikidata QIDs, else slug:…), so a person links across texts.
#
#   1. Rabbinic (Sefaria API; only versions whose licence is Public Domain, CC0, CC BY or CC BY-SA — never CC BY-NC or
#      'unknown'): Tosefta, Jerusalem Talmud, Midrash Rabbah, Mekhilta, Sifra, Sifrei, Mishneh Torah, Zohar, Sefer
#      Yetzirah, Sefer HaBahir. People are Sefaria's topic pages (Biblical Figures, Mishnaic People, Talmudic People,
#      CC BY-SA). A row is written only when the name is found in the passage it cites: either a passage the topic page
#      itself lists, or a full-text match of a name form that belongs to one person only and carries a title or a
#      patronymic (רבי עקיבא, שמעון בן שטח). Pirkei Avot is already in abrahamic.tsv (as Mishnah).
#   2. Christian: deuterocanon and Orthodox additions (Brenton's Septuagint, English 1851 + Greek, eBible.org, PD);
#      1 Enoch, Jubilees (R.H. Charles), Kebra Nagast (Budge); Apostolic Fathers, Gospel of Peter, Protoevangelium of
#      James (Roberts-Donaldson / Lightfoot), Gospel of Thomas — see SOURCES below.
#   3. Islamic hadith (separate corpora from the Qur'an): the six Sunni collections + Muwatta Malik (fawazahmed0
#      hadith-api, Unlicense, Arabic + English, sunnah.com numbering) and Musnad Ahmad (Open-Hadith-Data, ODbL 1.0 /
#      DbCL 1.0). Narrators are read from the chain (isnad); a few figures are found in the narration itself.
#   4. Latter-day Saint scriptures, Mandaean, Bahá'í and other texts where an open edition exists.
#
# Every download is cached in raw/sacred/abrahamic2/ (and the Sefaria topic / Wikidata caches of the first script in
# raw/sacred/abrahamic/ are reused).
#
#   python3 scripts/build_sacred_abrahamic2.py            # build
#   python3 scripts/build_sacred_abrahamic2.py rabbinic   # build only some families (rabbinic christian islamic other)
import collections, csv, difflib, hashlib, html, json, os, re, sys, time, unicodedata, urllib.error, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build_sacred_abrahamic as A   # noqa: E402  (reuses its downloads, Sefaria topics and figure-id logic)

RAW = os.path.join(ROOT, "raw", "sacred", "abrahamic2")
OUT = os.path.join(ROOT, "data", "sacred", "abrahamic2.tsv")
OUT_REVIEW = os.path.join(ROOT, "data", "sacred", "abrahamic2-review.tsv")
COLS = A.COLS
UA = A.UA

_last = {}
def get(url, path, delay=0.0, tries=6, binary=False):
    """Download url to RAW/path once; return its text (or bytes)."""
    full = os.path.join(RAW, path)
    if os.path.exists(full):
        b = open(full, "rb").read()
        if binary: return b
        try: return b.decode("utf-8")
        except UnicodeDecodeError: return b.decode("latin-1")
    host = urllib.parse.urlparse(url).netloc
    data = None
    for attempt in range(tries):
        wait = _last.get(host, 0) + delay - time.time()
        if wait > 0: time.sleep(wait)
        _last[host] = time.time()
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180).read()
            break
        except urllib.error.HTTPError as e:
            if e.code in (404, 400): data = b""; break
            time.sleep(3 * (attempt + 1))
        except Exception:
            time.sleep(3 * (attempt + 1))
    if data is None:
        raise RuntimeError(f"{url} kept failing")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    tmp = full + ".part"
    open(tmp, "wb").write(data); os.replace(tmp, full)
    if binary: return data
    try: return data.decode("utf-8")
    except UnicodeDecodeError: return data.decode("latin-1")

def get_json(url, path, delay=0.0):
    t = get(url, path, delay)
    return json.loads(t) if t.strip() else None

def row(**kw):
    r = dict.fromkeys(COLS, ""); r.update(kw)
    return r

def fold(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.category(c).startswith("M") and c not in "ʿʾ'’‘`")


# ═════════════════════════════════════════════════════════════
# Figure ids shared with abrahamic.tsv
# ═════════════════════════════════════════════════════════════
class Ids:
    """The figure ids, labels and sexes of build_sacred_abrahamic.py, computed the same way from the same caches."""
    def __init__(self):
        A.fetch_step()
        figs = A.tipnr(); self.byuid = byuid = {f["uid"]: f for f in figs}
        vmap, ptitles = A.heb_verse_map()
        self.people = people = A.sefaria_people()
        ids = {}
        self.sef_wiki = sef_wiki = {slug: urllib.parse.unquote(t["properties"]["enWikiLink"]["value"].rsplit("/wiki/", 1)[1]).replace("_", " ")
                    for slug, (_, t) in people.items() if "/wiki/" in t.get("properties", {}).get("enWikiLink", {}).get("value", "")}
        quran_wiki = {v[1] for v in A.QURAN.values() if v[1]}
        self.wq = wq = A.wiki_qids([w for w, _ in A.BIBLE_WIKI.values()] + list(sef_wiki.values()) + list(quran_wiki))
        for uid, (title, lab) in A.BIBLE_WIKI.items():
            if uid in byuid: byuid[uid]["fixed_label"] = lab
            if uid in byuid and wq.get(title): ids[uid] = wq[title]
        by_heb, by_en = collections.defaultdict(set), collections.defaultdict(set)
        fverses = {}
        for f in figs:
            if not f["kind"].startswith("PERSON") or f["type"] == "tribe": continue
            vs = set()
            for x in f["forms"]:
                by_heb[re.sub(r"[\s־]", "", A.strip_marks(x["original"]))].add(f["uid"])
                for n, _ in x["names"]: by_en[n.lower()].add(f["uid"])
                for b, c, v, _ in x["refs"]:
                    if b in A.SEFARIA_BOOK: vs.add((b,) + A.to_hebrew(b, c, v, x["dstrong"], vmap, ptitles))
            fverses[f["uid"]] = vs
        self.topic_fig = topic_fig = {}
        for slug, (cat, t) in people.items():
            he = {re.sub(r"[\s־]", "", A.strip_marks(x["text"])) for x in t.get("titles", []) if x["lang"] == "he"}
            en = {x["text"].lower() for x in t.get("titles", []) if x["lang"] == "en"}
            cands = set().union(*[by_heb.get(h, set()) for h in he], *[by_en.get(e, set()) for e in en]) if (he or en) else set()
            if not cands: continue
            verses = set().union(*[A.sefaria_verses(r["ref"]) for r in t.get("refs", []) if not r.get("is_sheet")] or [set()])
            if not verses: continue
            score = sorted(((len(fverses[u] & verses), u) for u in cands), reverse=True)
            if score[0][0] >= 1 and (len(score) == 1 or score[1][0] < score[0][0]):
                topic_fig[slug] = score[0][1]
        for slug, uid in topic_fig.items():
            q = wq.get(sef_wiki.get(slug, ""))
            if q and uid not in ids and q not in ids.values(): ids[uid] = q
        wd = A.wd_biblical(); wd_by_label = collections.defaultdict(list)
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
            ids[f["uid"]] = w["qid"]; used.add(w["qid"])
        for f in figs:
            if f["uid"] not in ids: ids[f["uid"]] = "slug:biblical:" + f["uid"].lower().replace(" ", "_")
        self.ids = ids
        self.went = A.wd_entities([q for q in list(ids.values()) + list(wq.values()) if q and q.startswith("Q")])
        for t, q in list(wq.items()):
            if q and re.search(r"given name|family name|surname|disambiguation|list article|Wikimedia", self.went.get(q, {}).get("desc", ""), re.I): wq[t] = None
        # the published table: figure_id → (figure label, sex) as written in abrahamic.tsv (labels must stay identical)
        self.published = {}
        self.published_names = collections.defaultdict(set)
        p = os.path.join(ROOT, "data", "sacred", "abrahamic.tsv")
        if os.path.exists(p):
            for r in csv.DictReader(open(p, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
                self.published.setdefault(r["figure_id"], (r["figure"], r["sex"]))
                self.published_names[r["name"].lower()].add(r["figure_id"])

    def topic(self, slug):
        """Sefaria person topic → (figure_id, label, sex, entity_type, latin name), exactly as abrahamic.tsv has it."""
        cat, t = self.people[slug]
        uid = self.topic_fig.get(slug)
        if uid:
            f = self.byuid[uid]; fid = self.ids[uid]
            label = A.short_label(f, self.went.get(fid, {}).get("desc", "")); sex = f["sex"]; et = f["type"]; name = t["primaryTitle"]["en"]
        else:
            q = self.wq.get(self.sef_wiki.get(slug, ""))
            fid = q if q else "slug:jewish:" + slug
            gen = t.get("properties", {}).get("generation", {}).get("value", "")
            kind = A.GEN.get(re.sub(r"\d+$", "", gen), "")
            d = self.went.get(q, {}).get("desc", "") if q else ""
            label = t["primaryTitle"]["en"] + (f", {d}" if d else f", {kind}" if kind else "")
            sex = {"M": "boy", "F": "girl"}.get(t.get("properties", {}).get("sex", {}).get("value", ""), "") or (self.went.get(q, {}).get("sex", "") if q else "")
            et = "sage" if cat in ("mishnaic-people", "talmudic-people") else "human"
            name = A.sage_name(t["primaryTitle"]["en"])
        if fid in self.published:
            label, psex = self.published[fid]; sex = sex or psex
        return fid, label, sex, et, name

    def qid_of(self, wiki_title):
        """English Wikipedia title → QID (cached lookups)."""
        return wiki_qid(wiki_title)

_wq_cache = {}
def wiki_qid(title):
    if title not in _wq_cache:
        _wq_cache.update(A.wiki_qids([title]))
    return _wq_cache.get(title)

def wiki_qids(titles):
    todo = [t for t in titles if t not in _wq_cache]
    if todo: _wq_cache.update(A.wiki_qids(todo))
    return {t: _wq_cache.get(t) for t in titles}


# ═════════════════════════════════════════════════════════════
# 1. Rabbinic literature (Sefaria)
# ═════════════════════════════════════════════════════════════
SEF = "https://www.sefaria.org/api/"
SEF_DELAY = 0.7
OPEN_LICENSES = ("Public Domain", "CC0", "CC-BY", "CC-BY-SA")   # never CC-BY-NC, never 'unknown'
LIC_LABEL = {"Public Domain": "Public Domain", "CC0": "CC0", "CC-BY": "CC BY", "CC-BY-SA": "CC BY-SA"}

YERUSHALMI = ("Berakhot Peah Demai Kilayim Sheviit Terumot Maasrot Maaser_Sheni Challah Orlah Bikkurim Shabbat Eruvin Pesachim "
    "Yoma Shekalim Sukkah Rosh_Hashanah Beitzah Taanit Megillah Chagigah Moed_Katan Yevamot Sotah Ketubot Nedarim Nazir Gittin "
    "Kiddushin Bava_Kamma Bava_Metzia Bava_Batra Sanhedrin Shevuot Avodah_Zarah Makkot Horayot Niddah").split()
TOSEFTA = ("Berakhot Peah Demai Terumot Sheviit Kilayim Maasrot Maaser_Sheni Orlah Challah Bikkurim Shabbat Eruvin Pesachim "
    "Shekalim Yoma Sukkah Beitzah Rosh_Hashanah Ta'anit Megillah Moed_Katan Chagigah Yevamot Ketubot Nedarim Nazir Sotah Gittin "
    "Kiddushin Bava_Kamma Bava_Metzia Bava_Batra Sanhedrin Makkot Shevuot Eduyot Avodah_Zarah Horayot Zevachim Chullin Menachot "
    "Bekhorot Arakhin Temurah Meilah Keritot Kelim_Kamma Kelim_Metzia Kelim_Batra Oholot Negaim Parah Niddah Mikvaot Tahorot "
    "Makhshirin Zavim Yadayim Tevul_Yom Oktsin").split()
RABBAH = "Bereshit Shemot Vayikra Bamidbar Devarim Shir_HaShirim Ruth Esther Kohelet Eikhah".split()
# (corpus, [Sefaria titles])
RABBINIC = [
    ("Tosefta", ["Tosefta " + t.replace("_", " ") for t in TOSEFTA]),
    ("Jerusalem Talmud", ["Jerusalem Talmud " + t.replace("_", " ") for t in YERUSHALMI]),
    ("Midrash Rabbah", [t.replace("_", " ") + " Rabbah" for t in RABBAH]),
    ("Mekhilta", ["Mekhilta DeRabbi Yishmael", "Mekhilta DeRabbi Shimon Ben Yochai"]),
    ("Sifra", ["Sifra"]),
    ("Sifrei", ["Sifrei Bamidbar", "Sifrei Devarim"]),
    ("Mishneh Torah", None),          # filled from Sefaria's table of contents
    ("Zohar", ["Zohar"]),
    ("Sefer Yetzirah", ["Sefer Yetzirah"]),
    ("Sefer HaBahir", ["Sefer HaBahir"]),
]

def mishneh_torah_titles():
    toc = get_json(SEF + "index", "sefaria/toc.json", SEF_DELAY)
    out = []
    def walk(n, path):
        if "contents" in n:
            for c in n["contents"]: walk(c, path + [n.get("category", "")])
        elif "title" in n and "Mishneh Torah" in path and not any("Commentar" in p for p in path):
            out.append(n["title"])
    for c in toc: walk(c, [])
    return out

def sef_versions(title):
    d = get_json(SEF + "texts/versions/" + urllib.parse.quote(title.replace(" ", "_")), "sefaria/versions/" + title.replace(" ", "_") + ".json", SEF_DELAY)
    return d or []

def pick_version(title):
    """Best open version: Hebrew/Aramaic first (PD > CC0 > CC BY > CC BY-SA), else an open English translation."""
    vs = [v for v in sef_versions(title) if v.get("license") in OPEN_LICENSES and not re.search(r"\[[a-z]{2}\]", v.get("versionTitle", ""))]
    rank = lambda v: (v["language"] != "he", "Community Translation" in v["versionTitle"], OPEN_LICENSES.index(v["license"]))
    vs.sort(key=rank)
    return (vs[0]["language"], vs[0]["versionTitle"], vs[0]["license"]) if vs else None

def sef_index(title):
    return get_json(SEF + "v2/raw/index/" + urllib.parse.quote(title.replace(" ", "_")), "sefaria/index/" + title.replace(" ", "_") + ".json", SEF_DELAY)

def leaf_refs(title):
    """Sefaria refs of the text-bearing nodes of a (possibly complex) book: [(ref, url_ref)]"""
    idx = sef_index(title)
    if not idx: return []
    if "schema" not in idx or "nodes" not in idx["schema"]:
        return [title]
    out = []
    def walk(n, path):
        if "nodes" in n:
            for c in n["nodes"]: walk(c, path + [c_title(c)])
        else:
            out.append(", ".join([title] + [p for p in path if p]))
    def c_title(n):
        if n.get("default"): return ""
        return next((x["text"] for x in n.get("titles", []) if x.get("lang") == "en" and x.get("primary")), n.get("key", ""))
    for c in idx["schema"]["nodes"]: walk(c, [c_title(c)])
    return out

def sef_text(ref, lang, vtitle):
    url = SEF + "v3/texts/" + urllib.parse.quote(ref.replace(" ", "_")) + "?version=" + urllib.parse.quote(("hebrew" if lang == "he" else "english") + "|" + vtitle)
    key = hashlib.md5((ref + "|" + vtitle).encode()).hexdigest()[:10]
    d = get_json(url, "sefaria/texts/" + re.sub(r"[^\w]+", "_", ref)[:80] + "-" + key + ".json", SEF_DELAY)
    vs = [v for v in (d or {}).get("versions", []) if v.get("versionTitle") == vtitle]
    return (vs[0]["text"] if vs else []), (d or {})

def flatten(text, prefix=()):
    """nested Sefaria text → [(index tuple 1-based, string)]"""
    if isinstance(text, str):
        return [(prefix, text)] if text.strip() else []
    out = []
    for i, t in enumerate(text or []):
        out += flatten(t, prefix + (i + 1,))
    return out

def sef_url(base, ix):
    return "https://www.sefaria.org/" + urllib.parse.quote(base.replace(" ", "_"), safe=",_'") + "".join(f".{i}" for i in ix)

def book_segments(title, lang, vtitle):
    """→ [(base ref, section tuple, text)] for every segment of a Sefaria book in one version."""
    segs = []
    for ref in leaf_refs(title):
        text, d = sef_text(ref, lang, vtitle)
        for ix, s in flatten(text):
            segs.append((ref, ix, s))
    return segs

REF_ALIAS = {"Bereishit Rabbah": "Bereshit Rabbah"}
def split_ref(ref):
    """'Sifra, Tzav, Chapter 18 1-4' → ('Sifra, Tzav, Chapter 18', [(1,), (2,), (3,), (4,)]); unparsable → None"""
    m = re.match(r"^(.*?) (\d+(?::\d+)*)(?:-(\d+(?::\d+)*))?$", ref)
    if not m: return None
    base = REF_ALIAS.get(m[1], m[1])
    for a, b in REF_ALIAS.items(): base = base.replace(a + ",", b + ",")
    lo = tuple(int(x) for x in m[2].split(":"))
    if not m[3]: return base, [lo]
    hi = tuple(int(x) for x in m[3].split(":"))
    if len(hi) == 1 and hi[0] >= lo[-1] and hi[0] - lo[-1] < 60:
        return base, [lo[:-1] + (k,) for k in range(lo[-1], hi[0] + 1)]
    return base, [lo]

HEB_PREFIX = "ודלבכשמה"
def heb_words(s):
    return A.heb_norm(s).split()

def heb_variants(w):
    """a Hebrew word with up to three one-letter prefixes (ו ד ל ב כ ש מ ה) removed"""
    out = [w]
    for k in range(1, 4):
        if len(w) - k < 2 or any(c not in HEB_PREFIX for c in w[:k]): break
        out.append(w[k:])
    return out

TITLE_HE = {"רבי", "רב", "רבן", "מר", "רבנו", "רבינו"}
def topic_he_forms(t):
    """Hebrew name forms of a topic (word tuples) as name_patterns() would build them."""
    forms = set()
    for x in t.get("titles", []):
        if x["lang"] != "he": continue
        s = re.sub(r"\s+", " ", A.heb_norm(x["text"])).strip()
        if not s or "#" in s: continue
        w = tuple(s.split(" "))
        forms.add(w)
        if w[0] in TITLE_HE and len(w) > 1: forms.add(w[1:])
    return {f for f in forms if len("".join(f)) >= 3 and not (len(f) == 1 and f[0] in TITLE_HE)}

# English Bible-style spellings of rabbis' names in older translations (Soncino Zohar: R. Simeon, R. Judah, R. Jose)
EN_ALIAS = {"simeon": "shimon", "judah": "yehuda", "jose": "yose", "hiya": "chiya", "hiyya": "chiya", "isaac": "yitzchak", "eleazar": "elazar",
            "hezekiah": "chizkiya", "phinehas": "pinchas", "jochanan": "yochanan", "johanan": "yochanan", "joshua": "yehoshua", "nehemiah": "nechemya",
            "ishmael": "yishmael", "meir": "meir", "akiba": "akiva", "gamaliel": "gamliel", "jeremiah": "yirmiya", "chiyya": "chiya"}
EN_TITLE = re.compile(r"^(?:Rabbi|Rav|Rabban|R\.|Rebbi|Mar)\s+")
def en_key(s):
    """loose English key of a rabbinic name: 'R. Yehudah b. Betheira' ≈ 'Rabbi Yehuda ben Beteira'"""
    s = fold(s).lower()
    s = " ".join(EN_ALIAS.get(w, w) for w in s.split())
    s = re.sub(r"\b(?:rabbi|rav|rabban|r\.|rebbi)\s+", "r ", s)
    s = re.sub(r"\b(?:ben|bar|b\.|son of|ibn)\s+", "b ", s)
    s = s.replace("ch", "k").replace("kh", "k").replace("tz", "z").replace("ts", "z").replace("ph", "f").replace("h", "").replace("'", "")
    s = re.sub(r"[^a-z ]", "", s)
    s = re.sub(r"(.)\1+", r"\1", s)
    s = re.sub(r"[aeiouy]+$", "a", s); s = re.sub(r"(?<=\w)[aeiouy]+(?= )", "a", s)
    return re.sub(r"\s+", " ", s).strip()

def rabbinic(ids):
    people = ids.people
    # every person's name forms → which topics bear them
    he_forms = {slug: topic_he_forms(t) for slug, (cat, t) in people.items()}
    form_owner = collections.defaultdict(set)
    for slug, fs in he_forms.items():
        for f in fs: form_owner[f].add(slug)
    def safe(f, slug):
        """a form found anywhere in a text can be credited to this person only if no one else bears it and it is
        a titled name (רבי עקיבא) or has a patronymic (שמעון בן שטח) — never a bare biblical word like נח or דן"""
        if form_owner[f] != {slug}: return False
        if people[slug][0] == "biblical-figures": return len(f) >= 2 and (f[0] in TITLE_HE or "בן" in f or "בר" in f or "בת" in f)
        return len(f) >= 2
    full_forms = collections.defaultdict(list)   # first word → [(form, slug)]
    for slug, fs in he_forms.items():
        for f in fs:
            if safe(f, slug): full_forms[f[0]].append((f, slug))
    maxlen = max([len(f) for fs in full_forms.values() for f, _ in fs] or [1])
    # English name keys (for books with no open Hebrew text)
    en_forms = collections.defaultdict(set)
    for slug, (cat, t) in people.items():
        if cat == "biblical-figures": continue
        for x in t.get("titles", []):
            if x["lang"] == "en" and EN_TITLE.match(x["text"]) and len(x["text"].split()) >= 2:
                en_forms[en_key(x["text"])].add(slug)
    # passages each topic lists: (base ref, sections) → slugs; a ref to a whole section covers its segments
    topic_refs = collections.defaultdict(set)
    for slug, (cat, t) in people.items():
        for r in t.get("refs", []):
            if r.get("is_sheet"): continue
            sp = split_ref(r["ref"])
            if sp:
                for ix in sp[1]: topic_refs[(sp[0], ix)].add(slug)
    def listed_for(base, ix):
        out = set()
        for k in range(1, len(ix) + 1): out |= topic_refs.get((base, ix[:k]), set())
        return out
    EN_NAME = re.compile(r"\b(?:Rabbi|Rav|Rabban|R\.)\s+[A-Z][\w'’-]+(?:\s+(?:b\.|ben|bar|son of)\s+[A-Z][\w'’-]+)?")

    rows, review, stats = [], [], []
    for corpus, titles in RABBINIC:
        titles = titles or mishneh_torah_titles()
        first, count, how, src_of = {}, collections.Counter(), {}, {}
        for bi, title in enumerate(titles):
            v = pick_version(title)
            if not v:
                print(f"  {title}: no open version", file=sys.stderr); stats.append((corpus, title, "", "no open edition found", 0)); continue
            lang, vtitle, lic = v
            segs = book_segments(title, lang, vtitle)
            src = f"Sefaria topics (CC BY-SA) + text: {vtitle} ({LIC_LABEL[lic]})"
            found = set()
            for order, (base, ix, text) in enumerate(segs):
                listed = listed_for(base, ix)
                hit = {}
                if lang == "he":
                    words = heb_words(text)
                    for i, w in enumerate(words):
                        for wv in heb_variants(w):
                            for f, slug in full_forms.get(wv, ()):
                                if tuple([wv] + words[i + 1:i + len(f)]) == f: hit.setdefault(slug, "text")
                    if listed:   # passages the topic page lists: any of the person's forms will do (incl. a bare name)
                        flat = " " + " ".join(words) + " "
                        for slug in listed:
                            if any(re.search(r"(?<= )[" + HEB_PREFIX + r"]{0,3}" + re.escape(" ".join(f)) + r"(?= )", flat) for f in he_forms.get(slug, ())):
                                hit[slug] = "ref"
                else:
                    plain = html.unescape(re.sub(r"<[^>]+>", " ", text))
                    for m in EN_NAME.finditer(plain):
                        own = en_forms.get(en_key(m.group(0)), set())
                        if len(own) == 1: hit.setdefault(next(iter(own)), "en:" + m.group(0))
                    for slug in listed:
                        for x in people[slug][1].get("titles", []):
                            if x["lang"] == "en" and len(x["text"]) > 2 and re.search(r"\b" + re.escape(x["text"]) + r"\b", plain):
                                hit[slug] = "ref-en:" + x["text"]; break
                for slug, why in hit.items():
                    count[slug] += 1; found.add(slug)
                    if slug not in first: first[slug] = ((bi, order), base, ix, lang); src_of[slug] = src
                    RANK = lambda w: 0 if w == "ref" or w.startswith("ref-en") else 1 if w == "text" else 2
                    if slug not in how or RANK(why) < RANK(how[slug]): how[slug] = why
            stats.append((corpus, title, lang, f"{vtitle} ({LIC_LABEL[lic]})", len(found)))
            print(f"  {title} [{lang} {vtitle} / {lic}]: {len(segs)} segments, {len(found)} people", file=sys.stderr)
        for slug, (key, base, ix, lang) in first.items():
            t = people[slug][1]
            if re.search(r" and |'s ", t["primaryTitle"]["en"]): continue
            fid, label, sex, et, name = ids.topic(slug)
            why = how[slug]
            conf = 0.9 if why in ("ref",) or why.startswith("ref-en") else 0.85 if why == "text" else 0.75
            en_form = why.split(":", 1)[1] if ":" in why else ""
            cite = base + " " + ":".join(map(str, ix))
            text_title = next(tt for tt in titles if base == tt or base.startswith(tt + ","))
            r = row(name=name, figure_id=fid, figure=label, sex=sex, original=t["primaryTitle"].get("he", ""),
                    translit=t["primaryTitle"]["en"],
                    language="Aramaic" if corpus in ("Jerusalem Talmud", "Zohar") else "Hebrew",
                    tradition="Jewish", subtradition="Kabbalah" if corpus in ("Zohar", "Sefer Yetzirah", "Sefer HaBahir") else "Rabbinic",
                    corpus=corpus, text=text_title, passage=cite, url=sef_url(base, ix), occurrences=count[slug], entity_type=et,
                    name_role="title" if name in ("Rav", "Rabbi", "Mar", "Caesar") else "personal", status="attested",
                    relation=(f"no open Hebrew text; the open English translation reads '{en_form}'" if en_form else "no open Hebrew text; found in the open English translation" if lang != "he" else ""),
                    source=src_of[slug] + ("" if lang == "he" else "; Hebrew form from the topic page"), confidence=conf)
            (rows if conf >= 0.8 else review).append(r)
    return rows, review, stats


# ═════════════════════════════════════════════════════════════
# English-text person finder (shared by the Christian, Latter-day Saint and other English corpora)
# ═════════════════════════════════════════════════════════════
# A capitalised word is a candidate name when it is never written in lower case in the corpus or in the KJV, and is
# not only ever sentence-initial. It is taken as a PERSON when the text itself shows it acting or related as one
# ("Tobias said", "the son of Raguel", "his wife Edna", "king Antiochus") more than as a place ("in Ecbatane", "the
# land of Media"); TIPNR's person/place split for names it knows is added as a prior. Sex is written only when the
# text says it next to the name ("X the son of", "his daughter X", "queen X", "X his wife").
VERB = r"(?:said|saith|says|spake|spoke|answered|replied|asked|cried|called|went|came|took|gave|begat|bare|died|lived|dwelt|was|were|did|had|commanded|sent|saw|heard|wrote|prayed|wept|arose|rose|fled|reigned|slew|knew|made|brought|returned|smote|blessed|told|sat|stood|looked|lifted|fell|kissed|married|loved|feared|hearkened|believed|departed|entered|turned|wrought|prophesied|baptized|preached|taught|testified|did)"
PERSON_CUES = [
    (r"\b{N},? (?:the |a |his |her |thy |my )?(?:son|sons|daughter|daughters|wife|husband|brother|sister|father|mother|servant|maid|handmaid|king|queen|prince|priest|prophet|prophetess|captain|governor|scribe|elder|disciple|apostle|bishop|deacon|angel|archangel)\b", 2),
    (r"\b(?:son|daughter|wife|husband|brother|sister|father|mother|servant|maid|handmaid|seed|house|children|sons|daughters|descendants|household|kindred|people) of {N}\b", 2),
    (r"\b(?:king|queen|prince|princess|priest|prophet|prophetess|captain|governor|lord|lady|brother|sister|father|mother|uncle|son|daughter|wife|husband|elder|apostle|angel|archangel|chief|judge|named|called|whose name was|name was|man|woman|young man|maiden|damsel|servant) {N}\b", 2),
    (r"\b{N},? " + VERB + r"\b", 1),
    (r"\b(?:unto|to|with|by|said|saith|told|asked|blessed|called|answered|sent|commanded|begat|bare|married|loved|kissed|slew|saw|heard) {N}\b", 0.5),
    (r"\b{N}'s\b", 0.5),
]
PLACE_CUES = [
    (r"\b(?:in|at|from|into|toward|towards|unto the land of|the land of|city of|cities of|land of|country of|wilderness of|mount|mountain of|river|sea of|plain of|valley of|borders of|coasts of|out of|over against|near|nigh unto|through|throughout|round about|gate of|walls of|kingdom of|king of|kings of|men of|inhabitants of|people of the|the) {N}\b", 1),
    (r"\b{N},? (?:a|the) (?:city|town|village|country|land|river|mountain|region|province|nation)\b", 3),
]
GIRL_CUES = [r"\b(?:his|her|their|thy|my|the) (?:wife|daughter|sister|mother|handmaid|maid|maiden|damsel|aunt|grandmother) {N}\b", r"\b{N},? (?:his|her|their|the) (?:wife|daughter|sister|mother|handmaid|maid|virgin|widow)\b", r"\bqueen {N}\b", r"\b{N},? (?:a|the) (?:woman|virgin|widow|prophetess|queen)\b", r"\b{N} (?:the|a) daughter of\b"]
ANGEL_CUES = [r"\b(?:angel|archangel|angels|archangels|watcher|watchers) {N}\b", r"\b{N},? (?:one of )?(?:the |an )?(?:holy |chief |great )?(?:angels?|archangels?|watchers?)\b"]
BOY_CUES = [r"\b(?:his|her|their|thy|my|the) (?:son|brother|father|husband|uncle|grandfather) {N}\b", r"\b{N},? (?:his|her|their|the) (?:son|brother|father|husband)\b", r"\bking {N}\b", r"\b{N},? (?:a|the) (?:man|king|prince|priest|prophet|high priest|captain|son of)\b", r"\b{N} the son of\b"]

_KJV_LOWER = None
def kjv_lower_words():
    """every word written in lower case somewhere in the KJV with Apocrypha (eBible.org, PD)"""
    global _KJV_LOWER
    if _KJV_LOWER is None:
        import io, zipfile
        z = zipfile.ZipFile(io.BytesIO(get("https://ebible.org/Scriptures/eng-kjv_usfm.zip", "christian/eng-kjv.zip", binary=True)))
        txt = " ".join(z.read(n).decode("utf-8", "replace") for n in z.namelist() if n.endswith(".usfm"))
        _KJV_LOWER = set(re.findall(r"(?<![\\\w])([a-z][a-z']+)", re.sub(r"\\[a-z0-9]+\*?", " ", txt)))
    return _KJV_LOWER

TIPNR_KIND = None
def tipnr_kinds():
    """English name → set of TIPNR kinds (person, place, tribe) and the person figures bearing it"""
    global TIPNR_KIND
    if TIPNR_KIND is None:
        kinds, persons = collections.defaultdict(set), collections.defaultdict(list)
        for f in A.tipnr():
            k = "person" if f["kind"].startswith("PERSON") and f["type"] != "tribe" else "tribe" if f["type"] == "tribe" else "place" if f["type"] == "place" else "other"
            for x in f["forms"]:
                for n, _ in x["names"]:
                    kinds[n].add(k)
                    if k == "person" and f not in persons[n]: persons[n].append(f)
        TIPNR_KIND = (kinds, persons)
    return TIPNR_KIND

NAME_RE = re.compile(r"(?<![\w'’\-])([A-Z][a-z]+(?:[\-’'][A-Za-z][a-z]+)*)(?![\w\-])")
STOP_CAPS = set("""I O Oh And But For Then Now Behold Yea Nay The A An In On Of To Unto By With From As At If When While Which Who
Whom Whose What Where Wherefore Therefore Thus So Also Moreover Furthermore Neither Nor Yet Lest Let Thou Thee Thy Thine Ye You Your
He She It We They His Her Its Our Their Him Them Me My Mine Us This That These Those There Here Lo Amen Hallelujah Alleluia Selah
Lord God Christ Spirit Holy Ghost Father Son Saviour Savior Redeemer Almighty Highest Heaven Heavens Hell Sabbath Jews Gentiles
Chapter Verse Book Section Psalm Psalms Saying Vision Mandate Similitude Parable Prologue Epilogue Preface Introduction Note Notes
Praetorium Ethiopia Zion Sinai Jewish Jew Jewry Wacon Egypt Palestine Babylon Jerusalem Rome Persia Media Assyria Edom Moab""".split())

def find_people(segments, min_cues=2, extra_lower=()):
    """segments: [(order, cite, url, text)] → {name: {first:(order,cite,url,text), n, person, place, girl, boy, tipnr}}"""
    lower = kjv_lower_words() | set(extra_lower)
    kinds, _ = tipnr_kinds()
    text_all = "\n".join(t for _, _, _, t in segments)
    lower |= set(re.findall(r"(?<![\w'])([a-z][a-z']+)", text_all))
    cand = collections.Counter(); mid = collections.Counter(); first = {}
    for seg in segments:
        t = seg[3]
        for m in NAME_RE.finditer(t):
            w = m.group(1)
            if w in STOP_CAPS or w.lower() in lower or len(w) < 3 or w.endswith("ish") or re.search(r"-[a-z]", w): continue
            cand[w] += 1; first.setdefault(w, seg)
            before = t[max(0, m.start() - 3):m.start()]
            if not re.search(r"(?:^|[.!?:;\"“”‘(\[]\s*|\n\s*)$", t[:m.start()][-4:] if m.start() else ""): mid[w] += 1
    out = {}
    for w, n in cand.items():
        if not mid[w]: continue
        if re.search(r"(?:ites|ians|eans|ims|ines)$", w): continue           # peoples: Amalekites, Assyrians
        ev = {"person": 0.0, "weak": 0.0, "place": 0.0, "girl": 0, "boy": 0}
        N = re.escape(w)
        for pat, wt in PERSON_CUES:
            ev["person" if wt >= 1 else "weak"] += wt * min(len(re.findall(pat.replace("{N}", N), text_all)), 5)
        for pat, wt in PLACE_CUES:
            ev["place"] += wt * min(len(re.findall(pat.replace("{N}", N), text_all)), 5)
        for pat in GIRL_CUES: ev["girl"] += len(re.findall(pat.replace("{N}", N), text_all))
        for pat in BOY_CUES: ev["boy"] += len(re.findall(pat.replace("{N}", N), text_all))
        ev["angel"] = sum(len(re.findall(pat.replace("{N}", N), text_all)) for pat in ANGEL_CUES)
        k = kinds.get(w, set())
        if k == {"person"}: ev["person"] += 2
        elif k and "person" not in k: ev["place"] += 3; ev["placename"] = True
        elif len(k) > 1: ev["mixed"] = True                     # TIPNR: a person and also a place or a people (Israel, Ammon)
        ev.update(first=first[w], n=n, tipnr=k)
        out[w] = ev
    return out

def classify(ev, min_person=2.0):
    """→ 'person', 'doubt' or None"""
    p = ev["person"]
    if ev.get("placename"): return "doubt" if (ev["girl"] or ev["boy"]) and p >= 3 else None    # TIPNR knows it only as a place
    if ev.get("mixed") and p < 2 * min_person + 2: return "doubt" if p >= 1 else None
    if p >= min_person and p > (ev["place"] + 0.5 * ev["weak"] * 0) * 1.5 and p > ev["place"] * 1.5: return "person"
    if p >= 1 and p >= ev["place"]: return "doubt"
    return None

def sex_of(ev):
    if ev["girl"] and not ev["boy"]: return "girl"
    if ev["boy"] and not ev["girl"]: return "boy"
    if ev["girl"] >= 3 * ev["boy"] and ev["girl"] >= 3: return "girl"
    if ev["boy"] >= 3 * ev["girl"] and ev["boy"] >= 3: return "boy"
    return ""

def wd_characters(work_qids):
    """Wikidata items 'present in work' (P1441) of these works → {english label: (qid, sex, desc)} (CC0)"""
    vals = " ".join("wd:" + q for q in work_qids)
    sp = ('SELECT ?p ?l ?d ?sex WHERE { VALUES ?w { ' + vals + ' } ?p wdt:P1441 ?w . ?p rdfs:label ?l FILTER(lang(?l)="en") '
          'OPTIONAL{?p schema:description ?d FILTER(lang(?d)="en")} OPTIONAL{?p wdt:P21 ?sex} }')
    key = hashlib.md5(vals.encode()).hexdigest()[:10]
    d = get_json("https://query.wikidata.org/sparql?format=json&query=" + urllib.parse.quote(sp), f"wikidata/p1441-{key}.json", 1.0)
    out = {}
    for r in (d or {}).get("results", {}).get("bindings", []):
        q = r["p"]["value"].rsplit("/", 1)[1]; lab = r["l"]["value"]
        out.setdefault(lab, (q, A.WD_SEX.get(r.get("sex", {}).get("value", "").rsplit("/", 1)[-1], ""), r.get("d", {}).get("value", "")))
        out.setdefault(lab.split(" (")[0].split(",")[0], out[lab])
    return out

def famous_figure(ids, name, min_occ=15):
    """the abrahamic.tsv figure for a name borne by exactly one well-attested TIPNR person (Moses, Abraham)"""
    _, persons = tipnr_kinds()
    fs = persons.get(name, [])
    big = [f for f in fs if sum(len(x["refs"]) for x in f["forms"]) >= min_occ]
    if len(big) != 1 or any(sum(len(x["refs"]) for x in f["forms"]) >= 5 for f in fs if f is not big[0]): return None
    f = big[0]; fid = ids.ids[f["uid"]]
    lab, sx = ids.published.get(fid, (A.short_label(f), f["sex"]))
    return fid, lab, f["sex"] or sx

# angels named in many of these texts: TIPNR figure (Bible) or English Wikipedia article
ANGELS = {"Michael": "Michael@Dan.10.13-Rev", "Gabriel": "Gabriel@Dan.8.16-Luk", "Raphael": "Raphael (archangel)", "Uriel": "Uriel",
          "Phanuel": "Phanuel (angel)", "Raguel": "Raguel (angel)", "Sariel": "Sariel", "Remiel": "Remiel", "Azazel": "Azazel",
          "Semjaza": "Shemihaza"}
ANGELS_ALWAYS = {"Michael", "Gabriel", "Raphael", "Uriel", "Phanuel"}     # the rest only where the text calls them angels

def english_rows(ids, segments, corpus, tradition, subtradition, source, wd=None, slug_prefix="", language="English",
                 greek=None, min_person=2.0, link_famous=True, extra_lower=(), text_of=None, base_conf=0.85, famous_ok=(), uid_map=None):
    """people found in an English text → (rows, review)"""
    rows, review = [], []
    found = find_people(segments, extra_lower=extra_lower)
    for w, ev in sorted(found.items()):
        c = classify(ev, min_person)
        if wd and w in wd and not ev.get("placename") and (ev["person"] + ev["weak"] + ev["angel"] >= 0.5 or c): c = "person"   # a character Wikidata lists for this work
        is_angel = w in ANGELS_ALWAYS or (w in ANGELS and ev["angel"])
        if is_angel: c = "person"
        if not c: continue
        order, cite, url, text = ev["first"]
        sex = sex_of(ev); fid = label = None; conf = base_conf; how = []
        et = "angel" if ev["angel"] or is_angel else "human"
        if et == "angel": sex = ""
        if w in (uid_map or {}) or is_angel:
            ref = (uid_map or {}).get(w) or ANGELS[w]
            if "@" in ref and ref in ids.ids:
                fid = ids.ids[ref]; f = ids.byuid[ref]
                label, psex = ids.published.get(fid, (A.short_label(f), f["sex"])); sex = "" if et == "angel" else (f["sex"] or psex or sex)
            elif "@" not in ref and wiki_qid(ref):
                fid = wiki_qid(ref); label = ids.published.get(fid, (f"{w}, angel",))[0]
            if fid: how.append("identified by this text's own context")
        if not fid and wd and w in wd:
            q, wsex, desc = wd[w]
            if re.search(r"\bangel|watcher|demon\b", desc, re.I): et = "angel"; sex = ""
            fid, label = q, ids.published.get(q, (f"{w}" + (f", {desc}" if desc else ""),))[0]
            if wsex and sex and wsex != sex: fid = None
            else: sex = wsex or sex; how.append("Wikidata")
        if not fid and link_famous and w in famous_ok:
            ff = famous_figure(ids, w)
            if ff and c == "person":
                fid, label, fsex = ff
                if fsex and sex and fsex != sex: fid = None
                else: sex = fsex or sex; conf = min(conf, 0.85); how.append("same figure as the Bible's " + w)
        if not fid:
            fid = f"slug:{slug_prefix}:{re.sub(r'[^a-z0-9]+', '-', fold(w).lower())}"
            label = f"{w}, named in {text_of(cite) if text_of else corpus}"
        orig, tr_ = (greek(w, ev["first"]) if greek else ("", ""))
        r = row(name=w, figure_id=fid, figure=label, sex=sex, original=orig or w, translit=tr_ or "", language=("Greek" if orig else language),
                tradition=tradition, subtradition=subtradition, corpus=corpus, text=text_of(cite) if text_of else corpus, passage=cite, url=url,
                occurrences=ev["n"], entity_type=et, name_role="personal", status="attested",
                relation=("; ".join(how) if how else ""), source=source + (" + Wikidata (CC0)" if "Wikidata" in how else ""),
                confidence=conf if c == "person" else 0.6)
        (rows if c == "person" else review).append(r)
    return rows, review

# ═════════════════════════════════════════════════════════════
# 2. Christian texts outside the 66-book canon
# ═════════════════════════════════════════════════════════════
EBIBLE = "https://ebible.org/Scriptures/"
DEUTERO = {"TOB": "Tobit", "JDT": "Judith", "ESG": "Esther (Greek)", "WIS": "Wisdom of Solomon", "SIR": "Sirach", "BAR": "Baruch",
           "LJE": "Letter of Jeremiah", "SUS": "Susanna", "BEL": "Bel and the Dragon", "1MA": "1 Maccabees", "2MA": "2 Maccabees"}
ORTHODOX = {"1ES": "1 Esdras", "3MA": "3 Maccabees", "MAN": "Prayer of Manasseh", "PSA": "Psalm 151"}
SRC_BRENTON = "Brenton's Septuagint, English 1851 + Greek (eBible.org eng-Brenton / grcbrent), Public Domain"
# figures of the Hebrew Bible that the deuterocanon names again (linked to the abrahamic.tsv figure when TIPNR has one
# well-attested bearer of the name)
BIBLE_AGAIN = set("""Abraham Isaac Jacob Israel Moses Aaron Joshua Samuel David Solomon Elijah Elias Elisha Daniel Noah Noe Adam Eve Enoch
Enos Seth Joseph Judah Juda Levi Reuben Simeon Benjamin Ephraim Manasses Manasseh Hezekiah Ezekias Josiah Josias Isaiah Esaias
Jeremiah Jeremias Ezekiel Ezechiel Nebuchadnezzar Nabuchodonosor Cyrus Darius Artaxerxes Zerubbabel Zorobabel Ezra Esdras
Nehemiah Esther Mordecai Mardochaeus Haman Aman Ahasuerus Pharaoh Sarah Sara Rebecca Rebekah Rachel Leah Lot Job Jonah Jonas Nathan
Phinehas Phinees Caleb Gideon Samson Saul Jeroboam Rehoboam Ahab Jezebel Achab Hiram Balaam Korah Core Dathan Abiram Enoch Cain Abel""".split())

def usfm_books(zipname, path):
    import io, zipfile
    z = zipfile.ZipFile(io.BytesIO(get(EBIBLE + zipname + "_usfm.zip", path, binary=True)))
    out = {}
    for n in z.namelist():
        if not n.endswith(".usfm"): continue
        t = z.read(n).decode("utf-8", "replace")
        m = re.search(r"\\id (\w+)", t)
        if not m: continue
        b = m.group(1); ch = 0; verses = {}
        t = re.sub(r"\\f .*?\\f\*", "", t, flags=re.S); t = re.sub(r"\\x .*?\\x\*", "", t, flags=re.S)
        t = re.sub(r"\\w ([^|\\]*)\|[^\\]*\\w\*", r"\1", t)
        for line in t.split("\n"):
            mc = re.match(r"\\c (\d+)", line)
            if mc: ch = int(mc.group(1)); continue
            for mv in re.finditer(r"\\v (\d+)\w*\s+(.*?)(?=\\v \d|$)", line):
                txt = re.sub(r"\\[a-z0-9]+\*?", " ", mv.group(2))
                verses[(ch, int(mv.group(1)))] = re.sub(r"\s+", " ", txt).strip()
            if not re.match(r"\\(?:c|v|id|h|toc|mt|ms|s|r|d|cl|rem|ide)", line) and ch and verses and not re.search(r"\\v \d", line):
                txt = re.sub(r"\\[a-z0-9]+\*?", " ", line).strip()
                if txt and line.startswith(("\\p", "\\q", "\\m", "\\li", "\\pi", "\\nb")):
                    k = max(verses); verses[k] = (verses[k] + " " + txt).strip()
        out[b] = verses
    return out

GREEK = {"α": "a", "β": "b", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "e", "θ": "th", "ι": "i", "κ": "k", "λ": "l", "μ": "m", "ν": "n",
         "ξ": "x", "ο": "o", "π": "p", "ρ": "r", "σ": "s", "ς": "s", "τ": "t", "υ": "u", "φ": "ph", "χ": "ch", "ψ": "ps", "ω": "o"}
GREEK_SCH = dict(GREEK, η="ē", ω="ō", υ="y", χ="ch")
def greek_translit(w, scholarly=False):
    d = unicodedata.normalize("NFD", w)
    rough = "\u0314" in d[:4]
    base = "".join(c for c in d if not unicodedata.category(c).startswith("M")).lower()
    m = GREEK_SCH if scholarly else GREEK
    t = "".join(m.get(c, c) for c in base)
    t = t.replace("ou", "ou").replace("gg", "ng").replace("gk", "nk")
    if scholarly: t = re.sub(r"(?<=[aeēo])y", "u", t)
    if rough: t = "h" + t
    return t[:1].upper() + t[1:]

def deuterocanon(ids):
    eng = usfm_books("eng-Brenton", "christian/eng-Brenton.zip")
    grc = usfm_books("grcbrent", "christian/grcbrent.zip")
    wd = wd_characters(["Q131737", "Q202129", "Q202135", "Q155980", "Q211746", "Q161985", "Q209748", "Q1200049", "Q223169",
                        "Q1052253", "Q1337449", "Q912549", "Q756861", "Q218087", "Q131068"])
    rows, review, stats = [], [], []
    for corpus, books, sub in (("Deuterocanon", DEUTERO, "Catholic and Orthodox"), ("Orthodox Old Testament", ORTHODOX, "Eastern Orthodox")):
        segs, where = [], {}
        for b, title in books.items():
            for (ch, v), t in sorted(eng.get(b, {}).items()):
                if b == "PSA" and ch != 151: continue
                cite = f"{title} {v}" if b == "PSA" else f"{title} {ch}:{v}"
                if b == "PSA": cite = f"Psalm 151:{v}"
                url = f"https://ebible.org/eng-Brenton/{b}{ch:03d}.htm" if b == "PSA" else f"https://ebible.org/eng-Brenton/{b}{ch:02d}.htm"
                segs.append((len(segs), cite, url, t)); where[cite] = (b, ch, v, title)
        def greek(name, first):
            b, ch, v, _ = where[first[1]]
            gt = grc.get(b, {}).get((ch, v), "")
            best, score = "", 0
            for w in re.findall(r"(?<!\w)(\w[^\s,.;:·()\[\]«»]+)", unicodedata.normalize("NFC", gt)):
                if not unicodedata.category(w[0]) == "Lu": continue
                r = difflib.SequenceMatcher(None, greek_translit(w).lower(), fold(name).lower()).ratio()
                if r > score: best, score = w.strip("’'"), r
            return (best, greek_translit(best, True)) if score >= 0.7 else ("", "")
        r, rv = english_rows(ids, segs, corpus, "Christian", sub, SRC_BRENTON, wd=wd, slug_prefix="deuterocanon", greek=greek,
                             link_famous=True, famous_ok=BIBLE_AGAIN, text_of=lambda c: where[c][3])
        rows += r; review += rv; stats.append(("Christian", corpus, "en+grc", SRC_BRENTON, len(r)))
        print(f"  {corpus}: {len(segs)} verses, {len(r)} people, {len(rv)} doubtful", file=sys.stderr)
    return rows, review, stats

def roman(s):
    v = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}; n = 0
    for i, c in enumerate(s):
        x = v[c]; n += -x if i + 1 < len(s) and v[s[i + 1]] > x else x
    return n

def split_verses(chapter_text, ch, book, url, start_order, cite_fmt):
    """inline '1.' '2.' verse numbers → segments; numbers must rise by small steps (OCR noise is skipped)"""
    out, cur, last = [], 1, 0
    parts = re.split(r"(?<![\w,])(\d{1,3})\.\s", chapter_text)
    buf = parts[0]
    for i in range(1, len(parts), 2):
        n = int(parts[i])
        if last < n <= last + 3 or (last == 0 and n == 1):
            if buf.strip(): out.append((start_order + len(out), cite_fmt.format(book=book, ch=ch, v=cur), url, buf))
            cur, last, buf = n, n, parts[i + 1]
        else:
            buf += f" {parts[i]}. " + parts[i + 1]
    if buf.strip(): out.append((start_order + len(out), cite_fmt.format(book=book, ch=ch, v=cur), url, buf))
    return out

def roman_chapters(text, start_pat, max_ch, head=r"^\s*([IVXLC]+)\.\s+(.*)", conv=None, ok=lambda rest: True):
    """split an OCR text into chapters whose headings are numbered I. II. … (or 1. 2. …); a heading is accepted only if
    it continues the sequence (OCR may lose one or two: the chunk before such a gap is labelled with the range, e.g. '6–7')"""
    conv = conv or roman
    chunks, cur, buf = [], 0, []
    for line in text.split("\n"):
        m = re.match(head, line)
        n = conv(m.group(1)) if m else 0
        if m and (cur + 1 <= n <= cur + 4) and n <= max_ch and ok(m.group(2)) and (cur > 0 or re.match(start_pat, line)):
            if cur: chunks.append((cur, n - 1, "\n".join(buf)))
            cur, buf = n, [m.group(2)]
        elif cur:
            buf.append(line)
    if cur: chunks.append((cur, cur, "\n".join(buf)))
    return chunks

def clean_ocr(t):
    t = re.sub(r"[〚〛⌜⌝†‡]", "", t)
    t = re.sub(r"-\n\s*", "", t)
    return re.sub(r"\s+", " ", t)

def ethiopian(ids):
    rows, review, stats = [], [], []
    wd = wd_characters(["Q220890", "Q843946", "Q1123371"])
    # 1 Enoch, R.H. Charles 1917 (Project Gutenberg #77935)
    t = get("https://www.gutenberg.org/cache/epub/77935/pg77935.txt", "christian/enoch.txt")
    t = t[t.index("I. 1. The words of the blessing"):t.index("*** END OF THE PROJECT GUTENBERG")]
    segs = []
    for ch, ch2, body in roman_chapters(t, r"^I\. 1\.", 108):
        url = f"https://en.wikisource.org/wiki/The_Book_of_Enoch_(Charles)/Chapter_{ch}"
        if ch2 == ch: segs += split_verses(clean_ocr(body), ch, "1 Enoch", url, len(segs), "{book} {ch}:{v}")
        else: segs.append((len(segs), f"1 Enoch {ch}–{ch2}", url, clean_ocr(body)))
    for corpus, segs_, src, url in (("1 Enoch", segs, "1 Enoch, tr. R.H. Charles 1917 (Project Gutenberg #77935), Public Domain", None),):
        r, rv = english_rows(ids, segs_, corpus, "Christian", "Ethiopian Orthodox Tewahedo", src, wd=wd, slug_prefix="enoch",
                             famous_ok=BIBLE_AGAIN, text_of=lambda c: "1 Enoch")
        rows += r; review += rv; stats.append(("Christian", corpus, "en", src, len(r)))
        print(f"  {corpus}: {len(segs_)} verses, {len(r)} people, {len(rv)} doubtful", file=sys.stderr)
    # Jubilees, R.H. Charles 1917 (archive.org OCR)
    t = get("https://archive.org/download/bookofjubileesor01char/bookofjubileesor01char_djvu.txt", "christian/jubilees.txt")
    segs = []
    for ch, ch2, body in roman_chapters(t, r"^\s*I\.\s+And\s+it\s+came\s+to\s+pass\s+in\s+the\s+first\s+year", 50,
                                        ok=lambda rest: bool(re.match(r"\s*[A-Z][a-z]", rest))):
        url = "https://archive.org/details/bookofjubileesor01char"
        if ch2 == ch: segs += split_verses(clean_ocr(body), ch, "Jubilees", url, len(segs), "{book} {ch}:{v}")
        else: segs.append((len(segs), f"Jubilees {ch}–{ch2}", url, clean_ocr(body)))
    src = "Jubilees, tr. R.H. Charles 1917 (archive.org bookofjubileesor01char, OCR), Public Domain"
    r, rv = english_rows(ids, segs, "Jubilees", "Christian", "Ethiopian Orthodox Tewahedo", src, wd=wd, slug_prefix="jubilees",
                         famous_ok=BIBLE_AGAIN, text_of=lambda c: "Jubilees")
    rows += r; review += rv; stats.append(("Christian", "Jubilees", "en", src, len(r)))
    print(f"  Jubilees: {len(segs)} verses, {len(r)} people, {len(rv)} doubtful", file=sys.stderr)
    # Kebra Nagast, E.A.W. Budge 1922 (archive.org OCR): 117 chapters, no verses
    t = get("https://archive.org/download/budge-1922-kebra-nagast/Budge_1922_Kebra_Nagast_djvu.txt", "christian/kebra.txt")
    segs = []
    i = t.find("I. CONCERNING THE G", t.find("THE GLORY OF KINGS"))     # chapter 1's heading is OCR'd as a Roman 'I.'
    t = "1." + t[i + 2:]
    for ch, ch2, body in roman_chapters(t, r"^1\.", 117, head=r"^\s*([\dIl]{1,3})\.\s+(.*)", conv=lambda x: int(x.replace("I", "1").replace("l", "1")) if re.search(r"\d", x) or x == "1" else 0,
                                        ok=lambda rest: bool(re.match(r"(?i)(?:concern|how|of |the |more|a |what|and |regard|here)", rest.strip()))):
        cite = f"Kebra Nagast {ch}" if ch == ch2 else f"Kebra Nagast {ch}–{ch2}"
        segs.append((len(segs), cite, "https://archive.org/details/budge-1922-kebra-nagast", clean_ocr(body)))
    src = "Kebra Nagast, tr. E.A.W. Budge 1922 (archive.org, OCR), Public Domain"
    r, rv = english_rows(ids, segs, "Kebra Nagast", "Christian", "Ethiopian Orthodox Tewahedo", src, wd=wd, slug_prefix="kebra-nagast",
                         famous_ok=BIBLE_AGAIN, text_of=lambda c: "Kebra Nagast")
    rows += r; review += rv; stats.append(("Christian", "Kebra Nagast", "en", src, len(r)))
    print(f"  Kebra Nagast: {len(segs)} chapters, {len(r)} people, {len(rv)} doubtful", file=sys.stderr)
    return rows, review, stats

ECW = "https://www.earlychristianwritings.com/text/"
def ecw_text(page):
    h = get(ECW + page + ".html", f"christian/ecw-{page}.html")
    h = h.split('<hr width="50%">')[0].split("Chronological List")[0]          # the site's menus and footer
    t = re.sub(r"(?is)<(script|style|ins)[^>]*>.*?</\1>", " ", h)
    t = re.sub(r"(?i)<br\s*/?>|</?p[^>]*>", "\n", t)
    return html.unescape(re.sub(r"<[^>]+>", " ", t))

def early_christian(ids):
    rows, review, stats = [], [], []
    wd = wd_characters(["Q210752", "Q898808", "Q10993949", "Q262557", "Q131546", "Q762054", "Q328435"])
    af, apoc = [], []
    # Apostolic Fathers, J.B. Lightfoot 1891 (earlychristianwritings.com)
    for page, title, pat in (("didache-lightfoot", "Didache", r"^\s*(\d+):(\d+)\s"), ("1clement-lightfoot", "1 Clement", r"^\s*1Clem (\d+|prologue):(\d+)"),
                             ("barnabas-lightfoot", "Epistle of Barnabas", r"^\s*Barnabas (\d+):(\d+)"), ("shepherd-lightfoot", "Shepherd of Hermas", r"^\s*(\d+)\[(\d+)\]:(\d+)")):
        t = ecw_text(page); cur = None; buf = []
        def flush():
            if cur and buf: af.append((len(af), f"{title} {cur}", ECW + page + ".html", re.sub(r"\s+", " ", " ".join(buf))))
        for line in t.split("\n"):
            m = re.match(pat, line)
            if m:
                flush(); buf = [line[m.end():]]
                g = m.groups(); cur = f"{g[1]}:{g[2]}" if len(g) == 3 else (f"0:{g[1]}" if g[0] == "prologue" else f"{g[0]}:{g[1]}")
            elif cur: buf.append(line)
        flush()
    src = "Apostolic Fathers, tr. J.B. Lightfoot & J.R. Harmer 1891 (earlychristianwritings.com), Public Domain"
    r, rv = english_rows(ids, af, "Apostolic Fathers", "Christian", "", src, wd=wd, slug_prefix="apostolic-fathers", famous_ok=BIBLE_AGAIN | NT_AGAIN,
                         text_of=lambda c: re.sub(r" \d+:\d+$", "", c))
    rows += r; review += rv; stats.append(("Christian", "Apostolic Fathers", "en", src, len(r)))
    print(f"  Apostolic Fathers: {len(af)} verses, {len(r)} people, {len(rv)} doubtful", file=sys.stderr)
    # Protoevangelium of James (ANF vol. 8, Walker 1870/1886) — chapters "2. And his wife Anna…"
    t = ecw_text("infancyjames-roberts")
    t = t[t.index("IN THE RECORDS OF THE TWELVE TRIBES"):]
    parts = re.split(r"\n\s*(\d{1,2})\.\s", "\n" + t)
    segs = [(0, "Protoevangelium of James 1", ECW + "infancyjames-roberts.html", parts[0])]
    for i in range(1, len(parts), 2):
        if int(parts[i]) == len(segs) + 1: segs.append((len(segs), f"Protoevangelium of James {parts[i]}", ECW + "infancyjames-roberts.html", parts[i + 1]))
        else: segs[-1] = segs[-1][:3] + (segs[-1][3] + f" {parts[i]}. " + parts[i + 1],)
    apoc += [x for x in segs if int(x[1].rsplit(" ", 1)[1]) <= 25]
    # Gospel of Peter (ANF vol. 9, J. Armitage Robinson) — sections 1–14
    t = ecw_text("gospelpeter")
    t = t[t.index("THE GOSPEL ACCORDING TO PETER") + 29:]
    t = re.split(r"\n\s*(?:MATTHEW|MARK|LUKE|JOHN)\.?\s*\n|Online Text for Gospel of Peter|Text Sources", t)[0]
    for m in re.finditer(r"(?:^|\n)\s*(\d{1,2}) (.*?)(?=\n\s*\d{1,2} [A-Z]|\Z)", t, re.S):
        apoc.append((len(apoc), f"Gospel of Peter {m.group(1)}", ECW + "gospelpeter.html", m.group(2)))
    # Gospel of Thomas, Mark M. Mattison's public-domain translation (gospels.net)
    h = get("https://www.gospels.net/thomas", "christian/thomas.html")
    t = html.unescape(re.sub(r"<[^>]+>", "\n", re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)))
    t = t[t.index("Prologue"):]
    for m in re.finditer(r"(Prologue|Saying (\d+):[^\n]*)\n(.*?)(?=\nSaying \d+:|\Z)", t, re.S):
        if m.group(2) and int(m.group(2)) > 114: break
        apoc.append((len(apoc), "Gospel of Thomas " + (m.group(2) or "prologue"), "https://www.gospels.net/thomas", m.group(3)[:3000]))
    src = ("Protoevangelium of James (tr. A. Walker, ANF 8) and Gospel of Peter (tr. J.A. Robinson, ANF 9), earlychristianwritings.com, "
           "Public Domain; Gospel of Thomas, tr. M.M. Mattison (gospels.net), dedicated to the Public Domain")
    r, rv = english_rows(ids, apoc, "New Testament apocrypha", "Christian", "", src, wd=wd, slug_prefix="nt-apocrypha", famous_ok=BIBLE_AGAIN | NT_AGAIN,
                         uid_map={"Mary": "Mary@Mat.1.16-Act", "Joseph": "Joseph@Mat.1.16-Jhn", "Elizabeth": "Elizabeth@Luk.1.5-",
                                  "Zacharias": "Zechariah@Luk.1.5-", "Pilate": "Pilate@Mat.27.2-1Ti", "Peter": "Peter@Mat.4.18-2Pe",
                                  "Andrew": "Andrew@Mat.4.18-Act", "Alphaeus": "Alphaeus@Mat.10.3-Act", "Jesus": "Jesus@Isa.7.14-Rev", "Thomas": "Thomas@Mat.10.3-Act"},
                         min_person=1.0, text_of=lambda c: re.sub(r" (?:\d+|prologue)$", "", c))
    # Mary's parents: the Protoevangelium is the source of Joachim and Anna (Anne)
    q = wiki_qids(["Saint Joachim", "Saint Anne"])
    went = A.wd_entities([v for v in q.values() if v])
    for x in r + rv:
        if x["text"] == "Protoevangelium of James" and x["name"] in ("Joachim", "Anna"):
            qid = q["Saint Joachim" if x["name"] == "Joachim" else "Saint Anne"]
            w = went.get(qid, {})
            x.update(figure_id=qid, figure=f"{w.get('label') or x['name']}, {w.get('desc', '')}".strip(", "), sex=w.get("sex", "") or x["sex"],
                     entity_type="saint", relation=("father" if x["name"] == "Joachim" else "mother") + " of Mary in this text", confidence=0.95,
                     source=src.split(";")[0] + " + Wikidata (CC0)")
            if x in rv: rv.remove(x); r.append(x)
            if x["name"] == "Anna":
                r.append(dict(x, name="Anne", original="", translit="", status="related", occurrences="",
                              relation="later form of Anna (Greek Ἄννα, Hebrew Hannah), the name under which the Church venerates Mary's mother",
                              source="Wikidata (CC0) label of " + qid, confidence=0.9))
    rows += r; review += rv; stats.append(("Christian", "New Testament apocrypha", "en", src, len(r)))
    print(f"  NT apocrypha: {len(apoc)} sections, {len(r)} people, {len(rv)} doubtful", file=sys.stderr)
    return rows, review, stats

NT_AGAIN = set("Jesus Mary Joseph Peter Simon Andrew James John Matthew Thomas Philip Bartholomew Paul Herod Pilate Elizabeth Zacharias Zechariah Salome Magdalene Judas Levi Caiaphas Annas Apollos Cephas".split())

def christian(ids):
    rows, review, stats = [], [], []
    for f in (deuterocanon, ethiopian, early_christian):
        r, rv, st = f(ids); rows += r; review += rv; stats += st
    return rows, review, stats

# ═════════════════════════════════════════════════════════════
# 3. Hadith
# ═════════════════════════════════════════════════════════════
# Arabic (fully vocalized) → scholarly romanization in pausal form: عُمَرَ بْنَ الْخَطَّابِ → ʿUmar ibn al-Khaṭṭāb
FATHA, DAMMA, KASRA, SUKUN, SHADDA = "َ", "ُ", "ِ", "ْ", "ّ"
TANWIN = "ًٌٍ"; DAGGER = "ٰ"
CONS = {"ء":"ʾ","أ":"ʾ","إ":"ʾ","ؤ":"ʾ","ئ":"ʾ","آ":"ʾā","ب":"b","ت":"t","ث":"th","ج":"j","ح":"ḥ","خ":"kh","د":"d","ذ":"dh","ر":"r",
        "ز":"z","س":"s","ش":"sh","ص":"ṣ","ض":"ḍ","ط":"ṭ","ظ":"ẓ","ع":"ʿ","غ":"gh","ف":"f","ق":"q","ك":"k","ل":"l","م":"m","ن":"n",
        "ه":"h","و":"w","ي":"y","ة":"t","ى":"ā","ا":"ā","ٱ":""}
SUN = set("تثدذرزسشصضطظلن")
def tr_word(w):
    w = w.replace("ـ", "").replace("‏", "").strip("،,.:؛\"'()«»{}")
    if not w: return ""
    if re.fullmatch(r"[اٱ]?لل[" + FATHA + SHADDA + DAGGER + KASRA + DAMMA + "]*ه[" + KASRA + DAMMA + FATHA + "]?", w) or w in ("الله",): return "Allāh"
    if re.sub("[ً-ْٰ]", "", w) in ("بن", "ابن"): return "ibn"
    if re.sub("[ً-ْٰ]", "", w) in ("بنت", "ابنة"): return "bint"
    pre = ""
    base = re.sub("[ً-ْٰ]", "", w)
    if base.startswith(("ال", "ٱل")) and len(base) > 3:
        pre = "al-"
        i = 0
        # drop the article letters (and their marks)
        k = 0; out = []
        chars = list(w); j = 0; seen = 0
        while j < len(chars) and seen < 2:
            if chars[j] not in "ًٌٍَُِّْٰ": seen += 1
            j += 1
        while j < len(chars) and chars[j] in "ًٌٍَُِّْٰ": j += 1
        w = "".join(chars[j:])
        # sun letter: its shadda is the assimilated article, not a doubled consonant
        if w[:1] in SUN and SHADDA in w[1:3]: w = w[0] + w[1:3].replace(SHADDA, "", 1) + w[3:]
    out = []; i = 0; n = len(w)
    while i < n:
        c = w[i]; nx = w[i + 1] if i + 1 < n else ""
        if c in (FATHA, DAMMA, KASRA):
            v = {FATHA: "a", DAMMA: "u", KASRA: "i"}[c]
            # long vowels
            if c == FATHA and out and out[-1] == "ā": i += 1; continue          # لاَ: the fatha written after the alif
            if c == FATHA and nx in ("ا", "ى") : out.append("ā"); i += 2; continue
            if c == FATHA and nx == DAGGER: out.append("ā"); i += 2; continue
            if c == KASRA and nx == "ي" and i + 2 < n and w[i + 2] == SHADDA: out.append("i"); i += 1; continue
            if c == KASRA and nx == "ي" and (i + 2 >= n or w[i + 2] not in (FATHA, DAMMA, KASRA, SHADDA)): out.append("ī"); i += 2; continue
            if c == DAMMA and nx == "و" and (i + 2 >= n or w[i + 2] not in (FATHA, DAMMA, KASRA, SHADDA)): out.append("ū"); i += 2; continue
            out.append(v)
        elif c == SHADDA:
            if out and out[-1] not in "aiuāīū": out.append(out[-1])
            elif len(out) > 1 and out[-1] in "aiu" and out[-2] not in "aiuāīū": out.insert(len(out) - 1, out[-2])
        elif c in (SUKUN,) or c in TANWIN: pass
        elif c == DAGGER: out.append("ā")
        elif c in ("ا",) and i == 0: pass
        elif c in ("ا", "ى"):
            if out and out[-1] == "a": out[-1] = "ā"
            elif not out or out[-1] != "ā": out.append("ā")
        elif c in CONS: out.append(CONS[c])
        i += 1
    t = "".join(out)
    # pausal form: final short vowel, final t of tāʾ marbūṭa, -iyy → -ī
    t = re.sub(r"[aiu]$", "", t)
    t = re.sub(r"(?<=[aā])t$", "", t) if w.rstrip("ً-ْ").endswith("ة") or re.sub("[ً-ْٰ]", "", w).endswith("ة") else t
    t = re.sub(r"iyy$", "ī", t); t = re.sub(r"ā+", "ā", t)
    if t.startswith("ʾ"): t = t[1:]
    if not t: return ""
    k = 1 if t[0] in "ʿʾ" else 0
    t = t[:k] + t[k].upper() + t[k + 1:]
    return pre + t if pre else t

def tr(s):
    ws = [tr_word(w) for w in s.split()]
    ws = [w for w in ws if w]
    if ws and ws[0] in ("Abī", "Abā"): ws[0] = "Abū"
    if ws and ws[0] in ("ibn", "bint"): ws[0] = ws[0].capitalize()
    return " ".join(ws)


HARAKAT = "\u064b\u064c\u064d\u064e\u064f\u0650\u0651\u0652\u0670\u0640"
def ar_plain(s):
    s = "".join(c for c in s if c not in HARAKAT and c not in "\u200f\u200e")
    return s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ٱ", "ا").replace("ى", "ي")

def ar_pausal(w):
    """drop the case ending of a vocalized word: عَائِشَةَ → عَائِشَة"""
    return re.sub("[\u064b-\u0650\u0652]+$", "", w)

HADITH_FZ = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/"
OHD = "https://raw.githubusercontent.com/mhashim6/Open-Hadith-Data/master/"
# fawazahmed0 edition, corpus name, sunnah.com slug, link by number (else by book/hadith)
HADITH = [("bukhari", "Sahih al-Bukhari", "bukhari", True), ("muslim", "Sahih Muslim", "muslim", False),
          ("abudawud", "Sunan Abi Dawud", "abudawud", True), ("tirmidhi", "Jami at-Tirmidhi", "tirmidhi", True),
          ("nasai", "Sunan an-Nasa'i", "nasai", True), ("ibnmajah", "Sunan Ibn Majah", "ibnmajah", True),
          ("malik", "Muwatta Malik", "malik", False)]
SRC_FZ = "fawazahmed0/hadith-api (Unlicense; Arabic text and sunnah.com numbering)"
SRC_OHD = "Open-Hadith-Data, Musnad Ahmad (ODbL 1.0 / DbCL 1.0; Hadith Encyclopedia numbering)"

# words that start or join links of the chain (unvocalized, normalized)
ISNAD_CONN = re.compile(r"^(?:و?(?:حدثنا|حدثني|حدثناه|حدثنيه|حدثته|حدثتني|حدثتنا|اخبرنا|اخبرني|اخبرناه|اخبرته|اخبرتني|انبانا|انباني|انبانيه|سمعت|سمع|سمعا)|عن|عنه|عنها|يقول|تقول|قال|قالا|قالت|قالوا|يعني|ح|كلاهما|جميعا|ثلاثتهم|وهو|هو|اي|حديثا|نحوه|بهذا|ذكر|يحدث|تحدث|ثنا|انا|نا)$")
ISNAD_END = {"ان", "انه", "انها", "انهم", "انهما", "كان", "كانت", "فقال", "فقالت", "قلت", "يرفعه", "مرفوعا", "رضي", "رضى", "صلي", "صلى", "عليه", "عليها", "في", "الي", "علي", "انا", "لما", "اذا", "اذ", "ما", "من", "لا", "يا", "قد", "لقد", "رايت", "جاء", "جاءت", "اتي", "اتت", "خرج", "دخل", "سال", "سالت", "كنا", "كنت", "بلغه", "بلغني", "يبلغ", "به", "بمثله", "بنحوه", "بمعناه", "بهذا", "مثله", "مثل", "نحو", "قصة", "ياثر", "يبلغ", "رفعه", "يرويه", "يروي"}
NOT_NAME = set("ابيه ابي ابيها ابوه ابوها جده جدي جدته جدتي امه امي امها عمه عمي عمته خاله خالته اخيه اخته اخي اخوه رجل امراة رجلا رجال بعض اصحابه اصحابنا اصحاب اهل غير واحد النبي رسول الله فلان فلانة شيخ شيخا مولي مولاه مولاة له لها لهم لنا وغيره غيره كلاهما ابنه ابنته ابن بنت ام ابو ابا امراته زوجه زوجها يأثر ياثر رفعه يرويه".split())
NAME_WORD = re.compile(r"^[\u0621-\u064a]+$")

def isnad_links(text):
    """the narrators named in the chain: [[(vocalized word, plain word), …], …] in chain order"""
    words = text.replace("\u200f", " ").replace("\u200e", " ").replace("ـ", " ").split()
    out, seg = [], []
    for w in words:
        p = ar_plain(w).strip("،,.:؛\"'()«»{}[]")
        if not p: continue
        brk = w.rstrip().endswith(("،", ",", ":", "؛", "."))
        if ISNAD_CONN.match(p):
            if seg: out.append(seg); seg = []
            continue
        if p in ISNAD_END or not NAME_WORD.match(p) or p.startswith("وحدث") or p.startswith("واخبر"):
            if seg: out.append(seg); seg = []
            if p in ("رضي", "رضى", "صلي", "صلى", "ان", "انه", "انها", "انهم", "انهما", "كان", "كانت", "فقال", "فقالت", "قلت") or not NAME_WORD.match(p): break
            continue
        seg.append((w.strip("،,.:؛\"'()«»{}[]"), p))
        if brk: out.append(seg); seg = []
        if len(out) > 14: break
    if seg: out.append(seg)
    links = []
    for sg in out:
        ps = [p for _, p in sg]
        if not (1 <= len(ps) <= 7): continue
        if len(ps) == 1 and ps[0] in NOT_NAME: continue
        if ps[0] in ("ابن", "بن", "بنت") and len(ps) == 1: continue
        if any(p in NOT_NAME and p not in ("ابن", "بن", "بنت", "ام", "ابو", "ابي", "ابا", "عبد", "بني", "الله", "ابيه") for p in ps[:1]) and ps[0] not in ("ابي", "ابو", "ابا", "ام", "ابن"): continue
        if ps[0] in ("ابي", "ابو", "ابا", "ام") and len(ps) == 1: continue
        if ps[-1] in ("بن", "ابن", "بنت", "ابو", "ابي", "ام", "عبد"): continue
        if ar_key(ps) == "ابو القاسم": break        # the Prophet's kunya: the narration has begun
        links.append(sg)
    return links

def ar_key(ps):
    """normalized key of a narrator name: kunya case unified (ابي/ابا → ابو), ة → ه"""
    ps = list(ps)
    ps = ["ابو" if (p in ("ابي", "ابا") and (i == 0 or ps[i - 1] not in ("بن", "ابن", "بنت"))) else p for i, p in enumerate(ps)]
    k = " ".join(ps).replace("ة", "ه")
    return re.sub(r" ام المومنين$", "", k)

def name_parts(ps):
    """→ (ism words, kind) where kind is personal (an ism), kunya (Abū/Umm …) or nasab (Ibn …)"""
    if ps[0] in ("ابو", "ابي", "ابا"): return 2 if len(ps) > 1 else 1, "kunya"
    if ps[0] == "ام": return 2, "kunya"
    if ps[0] in ("ابن", "بن"): return 2, "nasab"
    i = 0
    while i < len(ps) and ps[i].startswith("ال") and i < len(ps) - 1 and ps[i + 1] not in ("بن", "ابن", "بنت"): i += 1   # leading nisba: الحميدي عبد الله
    if (ps[i] == "عبد" or (i + 1 < len(ps) and ps[i + 1] == "الله")) and i + 1 < len(ps): return (i, i + 2), "personal"
    return (i, i + 1), "personal"

def en_narrator(txt):
    """the companion an English hadith opens with: 'Narrated 'Umar bin Al-Khattab:' → 'Umar bin Al-Khattab"""
    t = (txt or "").strip()
    for pat in (r"^Narrated ([^:]{2,60}?)\s*(?:\(|:)", r"^It was narrated (?:from|that) ([A-Z][^:,]{2,50}?) (?:that|who said|said|:)",
                r"^([A-Z'][\w'\- ]{2,50}?)(?:,? \[may Allah[^\]]*\])? (?:narrated|reported|said)\b"):
        m = re.match(pat, t)
        if m:
            n = m.group(1).strip(" ,'\"")
            if re.search(r"\b(?:Messenger|Prophet|Allah|that|from|He|I|We|They|A man|My father)\b", n): return ""
            return n
    return ""

def en_fold(n):
    n = fold(n).lower().replace("-", " ")
    n = re.sub(r"\b(?:bin|b\.|ibn)\b", "ibn", n)
    n = re.sub(r"\b(?:al|as|ad|an|ar|az|ash|at|adh)\s+", "al ", n)
    return re.sub(r"[^a-z ]", "", re.sub(r"\s+", " ", n)).strip()

# English forms of the hadith edition → English Wikipedia article of the companion (curated; checked against Wikidata
# sex at build time). Only forms that name one person are listed.
COMPANIONS = {
    "aisha": "Aisha", "aishah": "Aisha", "aisha the mother of the faithful believers": "Aisha", "aishah the mother of the believers": "Aisha",
    "abu hurairah": "Abu Hurayrah", "abu huraira": "Abu Hurayrah", "anas ibn malik": "Anas ibn Malik", "anas": "Anas ibn Malik",
    "ibn umar": "Abdullah ibn Umar", "abdullah ibn umar": "Abdullah ibn Umar", "ibn abbas": "Abdullah ibn Abbas", "abdullah ibn abbas": "Abdullah ibn Abbas",
    "jabir ibn abdullah": "Jabir ibn Abd Allah", "jabir": "Jabir ibn Abd Allah", "abu said al khudri": "Abu Sa'id al-Khudri", "abu saeed al khudri": "Abu Sa'id al-Khudri",
    "umar ibn al khattab": "Umar", "umar ibn alkhattab": "Umar", "abu bakr al siddiq": "Abu Bakr", "abu bakr as siddiq": "Abu Bakr",
    "ali ibn abi talib": "Ali", "ali ibn abu talib": "Ali", "uthman ibn affan": "Uthman", "umm salamah": "Umm Salama", "umm salama": "Umm Salama",
    "hafsah": "Hafsa bint Umar", "hafsa": "Hafsa bint Umar", "maimuna": "Maymuna bint al-Harith", "maimunah": "Maymuna bint al-Harith", "maymunah": "Maymuna bint al-Harith",
    "asma bint abi bakr": "Asma bint Abi Bakr", "asma bint abu bakr": "Asma bint Abi Bakr", "abu musa al ashari": "Abu Musa al-Ash'ari", "abu musa": "Abu Musa al-Ash'ari",
    "abdullah ibn masud": "Abdullah ibn Masud", "ibn masud": "Abdullah ibn Masud", "abu dharr": "Abu Dharr al-Ghifari", "abu dhar": "Abu Dharr al-Ghifari",
    "muadh ibn jabal": "Mu'adh ibn Jabal", "abu ayyub al ansari": "Abu Ayyub al-Ansari", "abu ayyub": "Abu Ayyub al-Ansari", "ubayy ibn kab": "Ubayy ibn Ka'b",
    "zaid ibn arqam": "Zayd ibn Arqam", "zayd ibn arqam": "Zayd ibn Arqam", "zaid ibn thabit": "Zayd ibn Thabit", "zayd ibn thabit": "Zayd ibn Thabit",
    "usamah ibn zaid": "Usama ibn Zayd", "usama ibn zaid": "Usama ibn Zayd", "salman al farsi": "Salman the Persian", "salman al farisi": "Salman the Persian",
    "abu talhah": "Abu Talha al-Ansari", "abu talha": "Abu Talha al-Ansari", "sad ibn abi waqqas": "Sa'd ibn Abi Waqqas", "abdur rahman ibn auf": "Abd al-Rahman ibn Awf",
    "al bara ibn azib": "Al-Bara' ibn 'Azib", "al bara": "Al-Bara' ibn 'Azib", "abu qatadah": "Abu Qatada al-Ansari", "abu qatada": "Abu Qatada al-Ansari",
    "hudhaifah": "Hudhayfah ibn al-Yaman", "hudhaifa": "Hudhayfah ibn al-Yaman", "ammar ibn yasir": "Ammar ibn Yasir", "abu ad darda": "Abu Darda", "abu al darda": "Abu Darda",
    "amr ibn al as": "Amr ibn al-As", "abdullah ibn amr": "Abd Allah ibn Amr ibn al-As", "abdullah ibn amr ibn al as": "Abd Allah ibn Amr ibn al-As",
    "muawiyah": "Muawiya I", "muawiya": "Muawiya I", "sahl ibn sad": "Sahl ibn Sa'd", "al numan ibn bashir": "Nu'man ibn Bashir", "numan ibn bashir": "Nu'man ibn Bashir",
    "umm atiyyah": "Umm Atiyya", "umm atiya": "Umm Atiyya", "umm habibah": "Umm Habiba", "umm habiba": "Umm Habiba", "safiyyah": "Safiyya bint Huyayy",
    "juwairiyah": "Juwayriyya bint al-Harith", "juwairiya": "Juwayriyya bint al-Harith", "sawdah": "Sawda bint Zamʿa", "zainab bint jahsh": "Zaynab bint Jahsh",
    "fatimah bint qais": "Fatima bint Qays", "fatima bint qais": "Fatima bint Qays", "abu umamah": "Abu Umama al-Bahili", "uqbah ibn amir": "Uqba ibn Amir",
    "abu bakrah": "Abu Bakrah", "imran ibn husain": "Imran ibn Husain", "kab ibn malik": "Ka'b ibn Malik", "umm sulaim": "Umm Sulaym", "umm haram": "Umm Haram",
    "asma bint umais": "Asma bint Umays", "al hasan ibn ali": "Hasan ibn Ali", "al husain ibn ali": "Husayn ibn Ali", "al rubai bint muawwidh": "Al-Rubayyi' bint Mu'awwidh",
    "abu sufyan": "Abu Sufyan", "abu sufyan ibn harb": "Abu Sufyan", "al abbas": "Al-Abbas ibn Abd al-Muttalib", "abu juhaifah": "Abu Juhayfa", "abu barzah": "Abu Barza al-Aslami",
    "abu said": "Abu Sa'id al-Khudri", "abu saeed": "Abu Sa'id al-Khudri", "thawban": "Thawban ibn Bujdud", "abu malik al ashari": "Abu Malik al-Ash'ari",
    "khabbab": "Khabbab ibn al-Aratt", "ibn al zubair": "Abdullah ibn al-Zubayr", "abdullah ibn al zubair": "Abdullah ibn al-Zubayr",
    "samurah ibn jundab": "Samura ibn Jundab", "wail ibn hujr": "Wa'il ibn Hujr", "abu hurayrah": "Abu Hurayrah", "anas ibn malik al ansari": "Anas ibn Malik",
}
# Arabic forms of figures that must be found even outside the chain (searched in the whole narration, unvocalized text):
# regex → (English Wikipedia article, Latin name, confidence)
HADITH_FIGURES = [
    (r"فاطمه (?:بنت|ابنه) (?:رسول الله|النبي|محمد)|فاطمه عليها السلام", "Fatimah", "Fatimah", 0.95),
    (r"\bخديجه\b", "Khadija bint Khuwaylid", "Khadija", 0.9),
    (r"زينب (?:بنت|ابنه) جحش", "Zaynab bint Jahsh", "Zaynab", 1.0),
    (r"زينب (?:بنت|ابنه) (?:رسول الله|النبي)", "Zainab bint Muhammad", "Zaynab", 1.0),
    (r"زينب (?:بنت|ابنه) ابي سلمه", "Zaynab bint Abi Salama", "Zaynab", 1.0),
    (r"\bالحسن بن علي\b", "Hasan ibn Ali", "Hasan", 0.95),
    (r"\bالحسين بن علي\b", "Husayn ibn Ali", "Husayn", 0.95),
    (r"\bعائشه\b", "Aisha", "Aisha", 0.9),
    (r"\bابو بكر الصديق\b|\bابي بكر الصديق\b|\bابا بكر الصديق\b", "Abu Bakr", "Abu Bakr", 1.0),
    (r"\bعمر بن الخطاب\b", "Umar", "Umar", 1.0),
    (r"\bعلي بن ابي طالب\b", "Ali", "Ali", 1.0),
    (r"\bعثمان بن عفان\b", "Uthman", "Uthman", 1.0),
    (r"\bبلال بن رباح\b", "Bilal ibn Rabah", "Bilal", 1.0),
    (r"\bسلمان الفارسي\b", "Salman the Persian", "Salman", 1.0),
    (r"\bحمزه بن عبد المطلب\b", "Hamza ibn Abd al-Muttalib", "Hamza", 1.0),
    (r"\bام ايمن\b", "Umm Ayman", "Umm Ayman", 0.9),
    (r"\bبريره\b", None, "Barira", 0.85),
    (r"\bام سلمه\b", "Umm Salama", "Umm Salama", 0.9),
    (r"\bحفصه\b", "Hafsa bint Umar", "Hafsa", 0.85),
    (r"\bسوده بنت زمعه\b", "Sawda bint Zamʿa", "Sawda", 1.0),
    (r"\bام كلثوم بنت (?:رسول الله|النبي)", "Umm Kulthum bint Muhammad", "Umm Kulthum", 1.0),
    (r"\bرقيه بنت (?:رسول الله|النبي)", "Ruqayyah bint Muhammad", "Ruqayya", 1.0),
    (r"\bاسماء بنت ابي بكر\b", "Asma bint Abi Bakr", "Asma", 1.0),
    (r"\bاسماء بنت عميس\b", "Asma bint Umays", "Asma", 1.0),
    (r"\bصفيه بنت حيي\b", "Safiyya bint Huyayy", "Safiyya", 1.0),
    (r"\bجويريه بنت الحارث\b", "Juwayriyya bint al-Harith", "Juwayriya", 1.0),
    (r"\bميمونه بنت الحارث\b", "Maymuna bint al-Harith", "Maymuna", 1.0),
    (r"\bام حبيبه\b", "Umm Habiba", "Umm Habiba", 0.9),
    (r"\bسميه\b", "Sumayyah bint Khabbat", "Sumayya", 0.8),
]
# a bare name in a narration (not the chain) is taken as this figure only with lower confidence
HADITH_BARE = [(r"\bبلال\b", "Bilal ibn Rabah", "Bilal", 0.8), (r"\bسلمان\b", "Salman the Persian", "Salman", 0.7),
               (r"\bفاطمه\b", "Fatimah", "Fatimah", 0.7), (r"\bزينب\b", None, "Zaynab", 0.6)]

def hadith_texts():
    """→ [(corpus, edition, [(number, book, in-book number, arabic, english)])]"""
    out = []
    for ed, corpus, slug, bynum in HADITH:
        a = json.loads(get(HADITH_FZ + f"ara-{ed}.json", f"hadith/fz-ara-{ed}.json"))
        e = json.loads(get(HADITH_FZ + f"eng-{ed}.json", f"hadith/fz-eng-{ed}.json"))
        eng = {h["hadithnumber"]: h["text"] for h in e["hadiths"]}
        books = a["metadata"].get("sections", {})
        out.append((corpus, ed, slug, bynum, books,
                    [(h["hadithnumber"], h["reference"]["book"], h["reference"]["hadith"], h["text"], eng.get(h["hadithnumber"], "")) for h in a["hadiths"]]))
    t = get(OHD + "Musnad_Ahmad_Ibn-Hanbal/musnad_ahmad_ibn-hanbal_ahadith_mushakkala.utf8.csv", "hadith/ahmad.csv")
    csv.field_size_limit(10 ** 9)
    rows = [(int(r[0]), None, None, r[1], "") for r in csv.reader(t.splitlines()) if r and r[0].isdigit()]
    out.append(("Musnad Ahmad", "ahmad", None, False, {}, rows))
    return out

def hadith_cite(corpus, slug, bynum, num, book, inbook):
    n = str(num).rstrip("0").rstrip(".") if isinstance(num, float) else str(num)
    if slug is None: return f"{corpus} {n}", ""
    if bynum: return f"{corpus} {n}", f"https://sunnah.com/{slug}:{n}"
    if book == 0: return f"{corpus}, Introduction {inbook}", f"https://sunnah.com/{slug}/introduction"
    return f"{corpus}, Book {book}, Hadith {inbook}", f"https://sunnah.com/{slug}/{book}/{inbook}"

FEM = re.compile(r"^(?:قالت|عنها|حدثتني|حدثتنا|اخبرتني|اخبرتنا|انها|تقول|سمعتها|زوج|امراه)$")
MASC = re.compile(r"^(?:قال|عنه|حدثني|حدثنا|اخبرني|اخبرنا|انه|يقول|سمعته|يحدث|يرفعه)$")

def pl_text(ar):
    return " ".join(ar_plain(w).strip("،,.:؛\"'()«»") for w in ar.replace("\u200f", " ").replace("ـ", " ").split())

def islamic(ids):
    texts = hadith_texts()
    titles = sorted(set(COMPANIONS.values()) | {f[1] for f in HADITH_FIGURES if f[1]} | {f[1] for f in HADITH_BARE if f[1]})
    q = wiki_qids(titles)
    went = A.wd_entities([v for v in q.values() if v])
    def fig(title):
        qid = q.get(title)
        if not qid: return None
        w = went.get(qid, {})
        if re.search(r"disambiguation|given name|family name|Wikimedia", w.get("desc", ""), re.I) or not w.get("sex"): return None
        label = ids.published.get(qid, (None,))[0] or (w.get("label") or title) + (", " + w["desc"] if w.get("desc") else "")
        return qid, label, w.get("sex", "")
    rows, review, stats = [], [], []
    # pass 1: every narrator of every chain, with its English form when the chain's last link is the companion the
    # English edition names
    for corpus, ed, slug, bynum, books, hadiths in texts:
        seen = {}                     # key → dict
        en_pair = collections.defaultdict(collections.Counter); en_raw = collections.defaultdict(collections.Counter)
        figs = {}
        for num, book, inbook, ar, en in hadiths:
            links = isnad_links(ar)
            words_after = ar.replace("\u200f", " ").split()
            for li, sg in enumerate(links):
                ps = [p for _, p in sg]
                key = ar_key(ps)
                d = seen.get(key)
                if not d:
                    d = seen[key] = {"first": (num, book, inbook), "n": 0, "voc": collections.Counter(), "fem": 0, "masc": 0, "last": 0}
                d["n"] += 1
                d["voc"][" ".join(ar_pausal(w) for w, _ in sg)] += 1
                if li == len(links) - 1: d["last"] += 1
                # the companion's sex from the grammar right after the name: رضي الله عنها / قالت (her) vs عنه / قال (him)
                if li == len(links) - 1:
                    m = re.search(re.escape(" ".join(ps)) + r" (?:(?:رضي|رضى) الله (عنها|عنه)|(قالت|قال|انها|انه)\b)", pl_text(ar))
                    if m:
                        g = m.group(1) or m.group(2)
                        d["fem" if g in ("عنها", "قالت", "انها") else "masc"] += 1
            if links and en:
                e = en_narrator(en)
                if e:
                    ek = re.sub(r"h$", "", en_fold(e)); en_pair[ar_key([p for _, p in links[-1]])][ek] += 1; en_raw[ek][e] += 1
            # figures searched in the whole narration
            toks = ar.replace("\u200f", " ").replace("ـ", " ").split()
            ptoks = [ar_plain(w).strip("،,.:؛\"'()«»").replace("ة", "ه") for w in toks]
            pl = " " + " ".join(ptoks) + " "
            def voc(m):
                i = pl[:m.start()].count(" ") - (0 if pl[m.start()] == " " else 1)
                i = max(i, 0); k = m.group(0).strip().count(" ") + 1
                ws = [ar_pausal(w.strip("،,.:؛\"'()«»")) for w in toks[i:i + k]]
                while len(ws) > 1 and ar_plain(ws[-1]) in ("عليها", "السلام"): ws.pop()
                return " ".join(ws)
            for pat, title, nm, conf in HADITH_FIGURES:
                if (title, nm) not in figs:
                    m = re.search(r"(?<= )(?:" + pat + ")", pl)
                    if m: figs[(title, nm)] = (num, book, inbook, conf, voc(m))
            for pat, title, nm, conf in HADITH_BARE:
                k = (title, nm, "bare")
                if k not in figs and (title, nm) not in figs:
                    m = re.search(r"(?<= )(?:" + pat + ")", pl)
                    if m: figs[k] = (num, book, inbook, conf, voc(m))
        src = SRC_FZ if slug else SRC_OHD
        n_rows = 0
        isms_with_more = collections.Counter()
        for key in seen:
            ps = key.split(" ")
            span, kind = name_parts(ps)
            if kind == "personal" and span[1] < len(ps): isms_with_more[" ".join(ps[span[0]:span[1]])] += 1
        for key, d in seen.items():
            if d["n"] < 2: continue
            voc = d["voc"].most_common(1)[0][0]
            ps = key.split(" ")
            span, kind = name_parts(ps)
            full_tr = tr(voc)
            vw = voc.split(" ")
            if kind == "personal":
                a, b = span; ism_voc = " ".join(vw[a:b]); ism_tr = tr(ism_voc)
            else:
                ism_voc = " ".join(vw[:span]); ism_tr = tr(ism_voc)
            if not ism_tr: continue
            name = fold(ism_tr)
            if name == "Abd Allah": name = "Abdullah"
            bare = kind == "personal" and span == (0, len(ps))
            if len(ps) == 1 and seen.get("ابو " + key, {}).get("n", 0) > d["n"]: continue   # هريرة cut from أبي هريرة
            ens = en_pair.get(key)
            en_form = ""
            if ens:
                e, c = ens.most_common(1)[0]
                tot = sum(ens.values())
                core = lambda x: re.sub(r"\b(?:abu|umm|ibn|al|bint)\b", "", x).replace(" ", "")
                if c >= 2 and c >= 0.6 * tot and difflib.SequenceMatcher(None, core(e), core(en_fold(fold(full_tr)))).ratio() >= 0.75:
                    en_form = en_raw[e].most_common(1)[0][0].replace("`", "ʿ")
            title = COMPANIONS.get(en_fold(en_form)) if en_form else None
            f = fig(title) if title else None
            sex = "girl" if (d["fem"] >= 2 and d["fem"] > d["masc"] * 4) or ps[0] in ("ام", "بنت") or "بنت" in ps else "boy" if d["masc"] >= 2 and d["masc"] > d["fem"] * 4 else ""
            if f:
                fid, label, wsex = f
                if wsex and sex and wsex != sex: f = None
            if f:
                fid, label, wsex = f; sex = wsex or sex
            elif bare and isms_with_more.get(key): continue          # bare first name; a fuller form is listed
            else:
                fid = "slug:islamic:" + re.sub(r"[^a-z]+", "-", fold(full_tr).lower()).strip("-")
                label = fold(full_tr) if not full_tr.startswith(("ʿ", "ʾ")) else full_tr
                label = full_tr + (", hadith narrator named by first name only" if bare else ", hadith narrator")
            if en_form and f:
                nm = en_form.split(" bin ")[0].split(" ibn ")[0].strip("'’ ")
                nm = fold(nm).replace("'", "")
                if kind == "personal" and nm and nm[0].upper() == name[0].upper() and len(nm.split()) == 1: name = nm
            role = {"personal": "personal", "kunya": "epithet", "nasab": "epithet"}[kind]
            rel = {"kunya": "kunya (teknonym)", "nasab": "patronymic (nasab) by which the narrator is known"}.get(kind, "")
            num, book, inbook = d["first"]
            cite, url = hadith_cite(corpus, slug, bynum, num, book, inbook)
            conf = 0.9 if f else 0.8 if d["n"] >= 3 else 0.7
            r = row(name=name, figure_id=fid, figure=label, sex=sex, original=voc, translit=full_tr, language="Arabic",
                    tradition="Islamic", subtradition="Sunni", corpus=corpus, text=(books.get(str(book), "") if books else "").strip() or corpus,
                    passage=cite, url=url, occurrences=d["n"], entity_type="human", name_role=role, status="attested",
                    relation=rel + ("; " if rel and en_form else "") + (f"English edition: {en_form}" if en_form else ""),
                    source=src + (" + Wikidata (CC0) id" if f else ""), confidence=conf)
            if conf >= 0.8 and kind != "nasab": rows.append(r); n_rows += 1
            else: review.append(r)
        for k, (num, book, inbook, conf, matched) in figs.items():
            title, nm = k[0], k[1]
            f = fig(title) if title else None
            cite, url = hadith_cite(corpus, slug, bynum, num, book, inbook)
            fid, label, sex = f if f else ("slug:islamic:" + fold(nm).lower().replace(" ", "-"), nm + ", named in a hadith", "")
            if any(x["figure_id"] == fid and x["corpus"] == corpus for x in rows[-n_rows:] if n_rows): continue
            r = row(name=nm, figure_id=fid, figure=label, sex=sex, original=matched.strip(), translit=tr(matched), language="Arabic",
                    tradition="Islamic", subtradition="Sunni", corpus=corpus, text=(books.get(str(book), "") if books else "").strip() or corpus,
                    passage=cite, url=url, occurrences="", entity_type="human", name_role="epithet" if nm.startswith("Umm ") else "personal",
                    status="attested", relation="named in the narration" + (" (bare name; identity by the usual reading)" if len(k) > 2 else ""),
                    source=src + " + Wikidata (CC0) id", confidence=conf)
            (rows if conf >= 0.8 and len(k) == 2 else review).append(r); n_rows += 1
        stats.append(("Hadith", corpus, "ar", src, n_rows))
        print(f"  {corpus}: {len(hadiths)} hadith, {len(seen)} narrator forms, {n_rows} rows", file=sys.stderr)
    return rows, review, stats

def other(ids): return [], [], []


# ═════════════════════════════════════════════════════════════
# Build
# ═════════════════════════════════════════════════════════════
def write(path, rows):
    seen, out = set(), []
    for r in rows:
        k = (r["name"], r["figure_id"], r["tradition"], r["corpus"], r["original"], r["status"])
        if k in seen: continue
        seen.add(k); out.append(r)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(COLS) + "\n")
        for r in out:
            fh.write("\t".join(str(r[c]).replace("\t", " ").replace("\n", " ").strip() for c in COLS) + "\n")
    return out

FAMILIES = ("rabbinic", "christian", "islamic", "other")

def main():
    want = [a for a in sys.argv[1:] if a in FAMILIES] or list(FAMILIES)
    ids = Ids()
    rows, review, stats = [], [], []
    for fam in want:
        print(f"── {fam}", file=sys.stderr)
        r, rv, st = globals()[fam](ids)
        rows += r; review += rv; stats += st
    out = write(OUT if len(want) == len(FAMILIES) else OUT.replace(".tsv", "-" + "-".join(want) + ".tsv"), rows)
    rev = write(OUT_REVIEW if len(want) == len(FAMILIES) else OUT_REVIEW.replace(".tsv", "-" + "-".join(want) + ".tsv"), review)
    cnt = collections.Counter((r["tradition"], r["corpus"]) for r in out)
    for k, v in sorted(cnt.items()): print(*k, v, sep="\t", file=sys.stderr)
    print(f"{len(out)} rows, {len(rev)} review rows", file=sys.stderr)
    json.dump(stats, open(os.path.join(RAW, "stats.json"), "w"), ensure_ascii=False, indent=0)

if __name__ == "__main__":
    main()
