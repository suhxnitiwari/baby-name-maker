#!/usr/bin/env python3
"""Sacred names from Asian scriptures beyond the first layer -> data/sacred/asia.tsv (+ asia-review.tsv).
Format: docs/sacred-format.md. Companion of build_sacred_buddhist.py and build_sacred_indic.py (figure_ids are shared).

Run:  python3 scripts/build_sacred_asia.py            (fetches anything missing into raw/sacred/asia/)
      python3 scripts/build_sacred_asia.py --offline  (only use what is already there)
      python3 scripts/build_sacred_asia.py --check    (print the first match context of every row, for spot checks)

Method. Every corpus is loaded as a list of citable segments (a verse, a line of a page, a chapter). Every figure is a
hand-written entry: the display name, the figure it belongs to and the exact forms it takes in that edition (regexes over
the edition's own spelling, OCR-folded for the scanned English translations). A row is written only where a form is
found in the text; the passage is the first segment it occurs in and `occurrences` counts every match. Figures already
in indic.tsv / buddhist.tsv keep their figure_id (and sex); new figures get a Wikidata QID by a search whose description
must fit (cached), else slug:<tradition>:<name>. Sex comes from Wikidata P21 or the earlier tables, never guessed.
Rows whose forms are also ordinary words, or whose match could be someone else, go to asia-review.tsv.

Corpora (all public domain or openly licensed; see SOURCE strings):
  Buddhist  Jataka (tr. Cowell et al. 1895-1907, archive.org OCR); GRETIL Sanskrit (CC BY-NC-SA 4.0): Astasahasrika
            Prajnaparamita, Gandavyuha, Dasabhumika, Lankavatara, Bodhicaryavatara, Tara stotras; CBETA T2008 Platform
            Sutra (CBETA, non-commercial); Bardo Thodol and Milarepa's biography (ed. Evans-Wentz 1927, 1928; US public
            domain, archive.org OCR).
  Jain      Acaranga (Jacobi, SBE 22, 1884), Uttaradhyayana and Sutrakrtanga (Jacobi, SBE 45, 1895), Uvasagadasao
            (Hoernle 1888), Candana from the Kalpa Sutra (SBE 22).
  Sikh      Vaaran Bhai Gurdas, Vaaran Bhai Gurdas Singh, Dasam Granth (BaniDB API, Khalis Foundation); Mata Khivi from
            the Guru Granth Sahib (BaniDB, already fetched by build_sacred_indic.py).
  Chinese   zh.wikisource (public-domain classical texts): Analects, Mencius, Daodejing (Wang Bi), Zhuangzi, Liezi,
            Great Learning, Doctrine of the Mean, Classic of Filial Piety, Shangshu, Shijing, Yijing, Liji, Chunqiu,
            Shanhaijing, Taishang Ganying Pian.
  Shinto    Kojiki and Nihon Shoki, original kanbun text from zh.wikisource.
"""
import collections, glob, html, json, os, re, sys, time, unicodedata, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from build_sacred_buddhist import latin_skt, latin_pali, deva  # noqa: E402  (pure helpers, no side effects)

RAW = os.path.join(ROOT, "raw", "sacred", "asia"); RAW_SACRED = os.path.join(ROOT, "raw", "sacred")
OUT = os.path.join(ROOT, "data", "sacred", "asia.tsv"); REVIEW = os.path.join(ROOT, "data", "sacred", "asia-review.tsv")
OFFLINE = "--offline" in sys.argv; CHECK = "--check" in sys.argv
UA = {"User-Agent": "Lullabyte-build/1.0 (https://github.com/suhxnitiwari/baby-name-maker)"}
COLS = ("name figure_id figure sex original translit language tradition subtradition corpus text passage url occurrences "
        "entity_type name_role status relation source confidence").split()
SRC_WD = "Wikidata (CC0)"


# ───────────────────────────────────────────────────────────── fetching
def get(url, path, sleep=1.0, binary=False):
    if os.path.exists(path) and os.path.getsize(path) > 200:
        return path
    if OFFLINE:
        return None
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for a in range(6):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300).read()
            open(path, "wb").write(data); time.sleep(sleep); return path
        except Exception as e:
            if "404" in str(e): return None          # past the last page
            print(f"  retry {url[-70:]}: {e}", file=sys.stderr); time.sleep(min(120, 10 * 2 ** a))
    return None


def ia_text(identifier, filename, path):
    return get(f"https://archive.org/download/{identifier}/{urllib.parse.quote(filename)}", path)


# ───────────────────────────────────────────────────────────── shared tables
def load_tsv(p):
    if not os.path.exists(p): return []
    lines = open(p, encoding="utf-8").read().split("\n")
    head = lines[0].split("\t")
    return [dict(zip(head, l.split("\t"))) for l in lines[1:] if l]

EARLIER = [r for f in ("indic.tsv", "buddhist.tsv", "abrahamic.tsv") for r in load_tsv(os.path.join(ROOT, "data", "sacred", f))]
SEX_BY_FID = {}
for r in EARLIER:
    if r.get("sex") and r["figure_id"].startswith("Q"): SEX_BY_FID.setdefault(r["figure_id"], r["sex"])

WD_CACHE = os.path.join(RAW, "wikidata.json")
def wd_resolve(specs):
    """{key: (search, description regex)} -> {key: (qid, sex)}; cached, accepted only when the description fits."""
    cache = json.load(open(WD_CACHE, encoding="utf-8")) if os.path.exists(WD_CACHE) else {}
    changed = False
    def call(params):
        for a in range(5):
            try:
                u = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(params)
                return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read())
            except Exception as e:
                time.sleep(60 if "429" in str(e) else 3 + 5 * a)
        return {}
    for key, (q, rx) in specs.items():
        ck = f"search:{q}|{rx}"
        if ck in cache or OFFLINE: continue
        time.sleep(0.7)
        j = call({"action": "wbsearchentities", "search": q, "language": "en", "format": "json", "limit": 8})
        if "search" not in j: continue
        cache[ck] = next((x["id"] for x in j["search"] if re.search(rx, x.get("description", ""), re.I)), ""); changed = True
        if sum(1 for k in cache if k.startswith("search:")) % 25 == 0:
            os.makedirs(RAW, exist_ok=True); json.dump(cache, open(WD_CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    qids = sorted({cache.get(f"search:{q}|{rx}", "") for q, rx in specs.values()} - {""})
    need = [q for q in qids if f"sex:{q}" not in cache and not OFFLINE]
    for i in range(0, len(need), 40):
        time.sleep(0.7)
        j = call({"action": "wbgetentities", "ids": "|".join(need[i:i + 40]), "props": "claims", "format": "json"})
        for q, e in j.get("entities", {}).items():
            sx = [c["mainsnak"].get("datavalue", {}).get("value", {}).get("id") for c in e.get("claims", {}).get("P21", [])]
            cache[f"sex:{q}"] = "boy" if sx == ["Q6581097"] else ("girl" if sx == ["Q6581072"] else ""); changed = True
    if changed:
        os.makedirs(RAW, exist_ok=True); json.dump(cache, open(WD_CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    out = {}
    for key, (q, rx) in specs.items():
        qid = cache.get(f"search:{q}|{rx}", "")
        out[key] = (qid, cache.get(f"sex:{qid}", "") if qid else "")
    return out


# ───────────────────────────────────────────────────────────── generic engine
Seg = collections.namedtuple("Seg", "text passage url body")

def fold(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c))

class Fig:
    """One name form of one figure in one corpus family.
    pats: regexes over the segment body; scope: predicate on Seg (where the figure may be counted);
    fid: a known figure_id (QID or slug) or None -> Wikidata search wd=(search, desc rx) -> slug."""
    def __init__(self, name, figure, et, role, translit="", original="", pats=(), fid=None, wd=None, rel="",
                 status="attested", conf=0.85, scope=None, review=False, sex="", key=None, ctx=None, lang=None):
        self.__dict__.update(locals()); del self.__dict__["self"]
        self.key = key or re.sub(r"[^a-z0-9]+", "", fold(name).lower())

def scan(segs, fig, flags=0):
    rx = re.compile("|".join(f"(?:{p})" for p in fig.pats), flags)
    crx = re.compile(fig.ctx, flags) if fig.ctx else None
    n, first, ctx_txt, hit = 0, None, "", ""
    for i, s in enumerate(segs):
        if fig.scope and not fig.scope(s): continue
        ms = list(rx.finditer(s.body))
        if not ms: continue
        if crx:
            win = " ".join(x.body for x in segs[max(0, i - 1):i + 2])
            if not crx.search(rx.sub(" ", win)): continue
        n += len(ms)
        if first is None:
            first = s; a = ms[0].start(); ctx_txt = s.body[max(0, a - 60):a + 70].replace("\n", " "); hit = ms[0].group(0)
    return n, first, ctx_txt, hit

def build(figs, segs, base, tradition, flags=0, wd_tag="", stats=None):
    """figs -> (rows, review rows). base: dict of corpus-level columns (language, subtradition, corpus, source)."""
    specs = {f"{wd_tag}:{f.key}": f.wd for f in figs if not f.fid and f.wd}
    wd = wd_resolve(specs) if specs else {}
    rows, review = [], []
    for f in figs:
        n, first, ctx, hit = scan(segs, f, flags)
        if not n:
            if stats is not None: stats["not found"].append(f"{base['corpus']}: {f.name}")
            continue
        qid, wsex = wd.get(f"{wd_tag}:{f.key}", ("", "")) if not f.fid else ("", "")
        fid = f.fid or qid or f"slug:{tradition.lower()}:{f.key}"
        sex = f.sex or wsex or SEX_BY_FID.get(fid, "")
        if f.role == "divine" or f.et in ("place", "tribe", "concept", "virtue", "title"): sex = ""
        src = base["source"] + (f"; {SRC_WD}" if fid.startswith("Q") else "")
        r = dict(name=f.name, figure_id=fid, figure=f.figure, sex=sex, original=hit if f.original == "*" else f.original, translit=f.translit,
                 language=f.lang or base["language"], tradition=tradition, subtradition=base.get("subtradition", ""),
                 corpus=base["corpus"], text=first.text, passage=first.passage, url=first.url, occurrences=str(n),
                 entity_type=f.et, name_role=f.role, status=f.status, relation=f.rel, source=src, confidence=f"{f.conf:.2f}")
        (review if f.review else rows).append(r)
        if CHECK: print(f"  [{base['corpus']}] {f.name} ({n}) {first.passage}: …{ctx}…")
    return rows, review


# ───────────────────────────────────────────────────────────── Sikh (BaniDB)
GUR_DIG = str.maketrans("੦੧੨੩੪੫੬੭੮੯", "0123456789")
GB = "(?<![਀-੿])"; GE = "(?![਀-੿])"

def g(*forms):
    return GB + "(?:" + "|".join(forms) + ")" + GE

def banidb_segs(src, corpus):
    d = os.path.join(RAW, "banidb")
    if not OFFLINE:
        p = 1
        while p < 1500:
            path = os.path.join(d, f"{src}{p:04d}.json")
            if not os.path.exists(path):
                get(f"https://api.banidb.com/v2/angs/{p}/{src}", path, sleep=0.4)
            if not os.path.exists(path) or '"error":true' in open(path, encoding="utf-8").read(300):
                if os.path.exists(path): os.remove(path)
                break
            p += 1
    segs = []
    for path in sorted(glob.glob(os.path.join(d, f"{src}[0-9]*.json"))):
        j = json.load(open(path, encoding="utf-8")); page = j["source"]["pageNo"]; pauri = 0
        for v in j.get("page", []):
            t = v["verse"]["unicode"]
            m = re.match(r"\s*(?:ਪਉੜੀ\s*)?([੦-੯]+)\s*:", t)
            if m: pauri = int(m.group(1).translate(GUR_DIG))
            url = f"https://www.sikhitothemax.org/shabad?id={v['shabadId']}"
            if src == "D":
                segs.append(Seg("", f"Dasam Granth p. {page}", url, t))
            else:
                segs.append(Seg(f"Vaar {page}", f"Vaar {page}" + (f", Pauri {pauri}" if pauri else ""), url, t))
    return segs

def ggs_segs():
    segs = []
    for path in sorted(glob.glob(os.path.join(RAW_SACRED, "ggs", "ang*.json"))):
        j = json.load(open(path, encoding="utf-8"))
        for v in j.get("page", []):
            ang = int(os.path.basename(path)[3:7])
            segs.append(Seg("", f"Ang {ang}", f"https://www.sikhitothemax.org/ang?ang={ang}&source=G", v["verse"]["unicode"]))
    return segs

GURU_CTX = g("ਨਾਨਕ", "ਨਾਨਕੁ", "ਅੰਗਦ", "ਅੰਗਦੁ", "ਅਮਰਦਾਸ", "ਅਮਰਦਾਸੁ", "ਰਾਮਦਾਸ", "ਰਾਮਦਾਸੁ", "ਅਰਜਨ", "ਅਰਜਨੁ", "ਹਰਿਗੋਬਿੰਦ",
             "ਹਰਿਰਾਇ", "ਹਰਿਕ੍ਰਿਸ਼ਨ", "ਤੇਗ ਬਹਾਦਰ", "ਗੁਰ", "ਗੁਰੂ", "ਸ੍ਰੀ", "ਬਾਬਾ", "ਬਾਬੇ")
LINEAGE = g("ਨਾਨਕ", "ਅੰਗਦ", "ਅਮਰਦਾਸ", "ਰਾਮਦਾਸ", "ਅਰਜਨ", "ਹਰਿਗੋਬਿੰਦ", "ਹਰਿਰਾਇ", "ਹਰਿਕ੍ਰਿਸ਼ਨ", "ਤੇਗ ਬਹਾਦਰ")
GURUS = dict(nanak="Q83322", angad="Q370204", amardas="Q454703", ramdas="Q335353", arjan="Q369920", tegh="Q2019145")

def vaar(n):
    return lambda s: s.text == f"Vaar {n}"

def sikh(stats):
    SRC = "{} text via BaniDB API (Khalis Foundation)"
    rows, review = [], []
    # ---- Gurus and their circle (all three corpora)
    gurus = [
        Fig("Nanak", "Guru Nanak, first Sikh Guru", "saint", "personal", "Nānak", "ਨਾਨਕ", [g("ਨਾਨਕ", "ਨਾਨਕੁ", "ਨਾਨਕਾ", "ਨਾਨਕੈ", "ਨਾਨਕਿ", "ਨਾਨਕੋ")], fid=GURUS["nanak"], conf=0.9),
        Fig("Angad", "Guru Angad, second Sikh Guru", "saint", "personal", "Aṅgad", "ਅੰਗਦ", [g("ਅੰਗਦ", "ਅੰਗਦੁ", "ਅੰਗਦਿ")], fid=GURUS["angad"], conf=0.9, key="angad"),
        Fig("Lehna", "Guru Angad, second Sikh Guru", "saint", "personal", "Lahiṇā", "ਲਹਿਣਾ", [g("ਲਹਿਣਾ", "ਲਹਣਾ", "ਲਹਣੇ", "ਲਹਿਣੇ")], fid=GURUS["angad"],
            rel="birth name of Guru Angad", ctx=g("ਨਾਨਕ\\S*", "ਬਾਬ\\S*", "ਅੰਗਦ\\S*", "ਗੁਰਿਆਈ", "ਅਮਰਦਾਸ\\S*")),
        Fig("Amar Das", "Guru Amar Das, third Sikh Guru", "saint", "personal", "Amar Dās", "ਅਮਰਦਾਸ", [g("ਅਮਰਦਾਸ", "ਅਮਰਦਾਸੁ", "ਅਮਰਦਾਸਿ", "ਅਮਰਦਾਸੈ", "ਅਮਰ ਦਾਸ")], fid=GURUS["amardas"], conf=0.9),
        Fig("Ram Das", "Guru Ram Das, fourth Sikh Guru", "saint", "personal", "Rām Dās", "ਰਾਮਦਾਸ", [g("ਰਾਮਦਾਸ", "ਰਾਮਦਾਸੁ", "ਰਾਮਦਾਸਿ", "ਰਾਮਦਾਸੈ")], fid=GURUS["ramdas"],
            scope=lambda s: s.text != "Vaar 11", conf=0.85),   # Vaar 11 Pauri 19: Ramdas the storekeeper, another Sikh
        Fig("Arjan", "Guru Arjan, fifth Sikh Guru", "saint", "personal", "Arjan", "ਅਰਜਨ", [g("ਅਰਜਨ", "ਅਰਜਨੁ", "ਅਰਜਨਿ")], fid=GURUS["arjan"], conf=0.85),
        Fig("Hargobind", "Guru Hargobind, sixth Sikh Guru", "saint", "personal", "Hargobind", "ਹਰਿਗੋਬਿੰਦ", [g("ਹਰਿਗੋਬਿੰਦ", "ਹਰਿਗੋਬਿੰਦੁ", "ਹਰਗੋਬਿੰਦ")],
            wd=("Guru Hargobind", r"Sikh|guru"), conf=0.85),
        Fig("Har Rai", "Guru Har Rai, seventh Sikh Guru", "saint", "personal", "Har Rāi", "ਹਰਿਰਾਇ", [g("ਹਰਿਰਾਇ", "ਹਰਿ ਰਾਇ")], wd=("Guru Har Rai", r"Sikh|guru"),
            ctx=g("ਅਰਜਨ", "ਹਰਿਗੋਬਿੰਦ", "ਹਰਿਕ੍ਰਿਸ਼ਨ", "ਤੇਗ ਬਹਾਦਰ", "ਗੁਰ\\S*")),
        Fig("Har Krishan", "Guru Har Krishan, eighth Sikh Guru", "saint", "personal", "Har Krishan", "ਹਰਿਕ੍ਰਿਸ਼ਨ", [g("ਹਰਿਕ੍ਰਿਸ਼ਨ", "ਹਰਿਕ੍ਰਿਸਨ")], wd=("Guru Har Krishan", r"Sikh|guru")),
        Fig("Tegh Bahadur", "Guru Tegh Bahadur, ninth Sikh Guru", "saint", "personal", "Tegh Bahādur", "ਤੇਗ ਬਹਾਦਰ", [g("ਤੇਗ ਬਹਾਦਰ", "ਤੇਗਬਹਾਦਰ", "ਤੇਗ ਬਹਾਦੁਰ")], fid=GURUS["tegh"], conf=0.9),
        Fig("Gobind Singh", "Guru Gobind Singh, tenth Sikh Guru", "saint", "personal", "Gobind Siṅgh", "ਗੋਬਿੰਦ ਸਿੰਘ", [g("ਗੋਬਿੰਦ ਸਿੰਘ", "ਗੋਬਿੰਦਸਿੰਘ", "ਗੋਬਿੰਦ ਸਿੰਘੁ")],
            wd=("Guru Gobind Singh", r"Sikh|guru"), conf=0.9),
        Fig("Mardana", "Bhai Mardana, companion of Guru Nanak", "disciple", "personal", "Mardānā", "ਮਰਦਾਨਾ", [g("ਮਰਦਾਨਾ", "ਮਰਦਾਨੇ", "ਮਰਦਾਨਿਆ")], fid="Q3696391", conf=0.9),
    ]
    in_d = {"Angad", "Amar Das", "Ram Das", "Arjan", "Hargobind"}   # in the Dasam Granth these also name epic figures (Angad the vanara, Arjuna)
    # ---- Sikhs named in Vaar 11 (Pauris 13-31) of Bhai Gurdas: (name, forms, pauri note)
    V11 = [("Taru Popat", ["ਤਾਰੂ ਪੋਪਟੁ"]), ("Mula Kir", ["ਮੂਲਾ ਕੀੜੁ"]), ("Pirtha", ["ਪਿਰਥਾ"]), ("Kheda", ["ਖੇਡਾ"]),
           ("Prithi Mal", ["ਪਿਰਥੀ ਮਲੁ"]), ("Rama Didi", ["ਰਾਮਾ ਡਿਡੀ"]), ("Daulat Khan Lodi", ["ਦਉਲਤ ਖਾਂ ਲੋਦੀ"]), ("Malo", ["ਮਾਲੋ"]),
           ("Manga", ["ਮਾਂਗਾ"]), ("Bhagta", ["ਭਗਤਾ"]), ("Buddha", ["ਬੁਢਾ"]), ("Jita", ["ਜਿਤਾ"]), ("Phirna", ["ਫਿਰਣਾ"]),
           ("Jodh", ["ਜੋਧੁ"]), ("Paro Julka", ["ਪਾਰੋ ਜੁਲਕਾ"]), ("Mallu Shahi", ["ਮਲੂਸਾਹੀ"]), ("Kedari", ["ਕੇਦਾਰੀ"]),
           ("Narain Das", ["ਨਰਾਇਣ ਦਾਸੁ"]), ("Lalu", ["ਲਾਲੂ"]), ("Jaga", ["ਜਗਾ"]), ("Tulsa", ["ਤੁਲਸਾ"]), ("Ugrasain", ["ਉਗ੍ਰਸੈਣੁ"]),
           ("Mohan", ["ਮੋਹਣੁ"]), ("Amru", ["ਅਮਰੂ"]), ("Gopi", ["ਗੋਪੀ"]), ("Gangu", ["ਗੰਗੂ"]), ("Tiratha", ["ਤੀਰਥਾ"]),
           ("Manak Chand", ["ਮਾਣਕਚੰਦੁ"]), ("Bisan Das", ["ਬਿਸਨਦਾਸੁ"]), ("Mahanand", ["ਮਹਾਂਨੰਦੁ"]), ("Bidhi Chand", ["ਬਿਧੀ ਚੰਦ"]),
           ("Dungar Das", ["ਡੂੰਗਰੁਦਾਸੁ"]), ("Jetha", ["ਜੇਠਾ"]), ("Kisna", ["ਕਿਸਨਾ"]), ("Tiloka", ["ਤਿਲੋਕਾ"]), ("Samunda", ["ਸਮੁੰਦਾ"]),
           ("Bhagirath", ["ਭਾਗੀਰਥੁ"]), ("Haridas", ["ਹਰਿਦਾਸ"]), ("Nihalu", ["ਨਿਹਾਲੂ"]), ("Mukand", ["ਮੁਕੰਦੁ"]), ("Dharma", ["ਧਰਮਾ"]),
           ("Sundar", ["ਸੁੰਦਰਿ"]), ("Chatur Das", ["ਚਤੁਰਦਾਸੁ"]), ("Kapur", ["ਕਪੂਰੁ"]), ("Chhaju", ["ਛਜੂ"]), ("Bhana", ["ਭਾਨਾ"]),
           ("Gurdita", ["ਗੁਰਦਿਤਾ"]), ("Saindas", ["ਸਾਈਂਦਾਸੁ"]), ("Ramdas Bhandari", ["ਰਾਮਦਾਸੁ ਭੰਡਾਰੀਆ"]), ("Lalo", ["ਲਾਲੋ"]),
           ("Bhai Gurdas", ["ਗੁਰਦਾਸੁ"])]
    v11 = [Fig(n, f"{n}, Sikh named by Bhai Gurdas (Vaar 11)", "disciple", "personal", "", fs[0], [g(*fs)], scope=vaar(11),
               conf=0.8, key=re.sub(r"\W", "", n.lower()), rel="one of the Sikhs listed in Vaar 11", review=False) for n, fs in V11]
    for f in v11:
        if f.name == "Buddha":
            f.wd = ("Baba Buddha", r"Sikh"); f.figure = "Baba Buddha, Sikh of the first six Gurus"
        if f.name == "Bidhi Chand":
            f.wd = ("Bhai Bidhi Chand", r"Sikh|warrior")
        if f.name == "Daulat Khan Lodi":
            f.wd = ("Daulat Khan Lodi", r"governor|Lahore|Punjab"); f.et = "human"; f.figure = "Daulat Khan Lodi, governor (Sultanpur)"
        if f.name in ("Durga", "Gopi", "Mohan", "Dharma", "Sundar", "Mukand", "Haridas", "Jetha", "Bhagirath", "Kapur", "Jaga", "Lalu",
                      "Lalo", "Tulsa", "Gangu"):
            f.review = True                      # also ordinary words / names of God or of others; kept for review
        if f.name == "Bhai Gurdas":
            f.scope = None; f.figure = "Bhai Gurdas, author of the Vaaran"; f.wd = ("Bhai Gurdas", r"Sikh|writer|poet")
    # ---- Devotees of the Puranic past in Vaar 10
    V10 = [("Dhru", "Q1059587", ["ਧ੍ਰੂ", "ਧ੍ਰੂਅ"], "Dhruva"), ("Prahlad", None, ["ਪ੍ਰਹਿਲਾਦੁ", "ਪ੍ਰਹਿਲਾਦ", "ਪ੍ਰਹਲਾਦੁ"], "Prahlada"),
           ("Bidar", "Q2002511", ["ਬਿਦਰੁ", "ਬਿਦਰ"], "Vidura"), ("Draupadi", "Q1057886", ["ਦਰੋਪਤੀ", "ਦ੍ਰੋਪਤੀ", "ਦ੍ਰਉਪਦੀ"], "Draupadi"),
           ("Sudama", None, ["ਸੁਦਾਮਾ", "ਸੁਦਾਮੇ"], "Sudama"), ("Janak", "Q1500207", ["ਜਨਕੁ", "ਜਨਕ"], "Janaka"),
           ("Ambrik", None, ["ਅੰਬਰੀਕ", "ਅੰਬਰੀਕੁ"], "Ambarisha"), ("Bal", None, ["ਬਲਿ ਰਾਜਾ", "ਰਾਜਾ ਬਲਿ"], "Mahabali"),
           ("Valmik", None, ["ਬਾਲਮੀਕੁ", "ਬਾਲਮੀਕ"], "Valmiki"), ("Ahalya", "Q796591", ["ਅਹਿਲਿਆ"], "Ahalya")]
    v10 = [Fig(n, f"{n} ({en}), devotee of the Puranic past", "human", "personal", "", fs[0], [g(*fs)], fid=q,
               wd=None if q else (en, r"Hindu|mythology|devotee|king|sage|poet|asura|daitya|Ramayana"), scope=vaar(10), conf=0.8,
               key=re.sub(r"\W", "", en.lower()), rel=f"Punjabi form of {en}") for n, q, fs, en in V10]
    b = banidb_segs("B", "Vaaran Bhai Gurdas"); s = banidb_segs("S", "Vaaran Bhai Gurdas Singh"); d = banidb_segs("D", "Dasam Granth")
    print(f"  BaniDB: Vaaran {len(b)} lines, Vaaran (Gurdas Singh) {len(s)}, Dasam Granth {len(d)} lines ({len({x.passage for x in d})} pages)", file=sys.stderr)
    for segs, corpus in ((b, "Vaaran Bhai Gurdas"), (s, "Vaaran Bhai Gurdas Singh")):
        base = dict(language="Gurmukhi/Punjabi", corpus=corpus, source=SRC.format(corpus))
        figs = gurus + (v11 + v10 if corpus == "Vaaran Bhai Gurdas" else [])
        r, rv = build(figs, segs, base, "Sikh", wd_tag="sikh", stats=stats); rows += r; review += rv
    # Dasam Granth: Gurus (lineage verses only for names shared with epic figures), deities and epic figures
    dg = []
    for f in gurus:
        f2 = Fig(**{k: v for k, v in f.__dict__.items()})
        if f.name in in_d: f2.ctx = LINEAGE
        dg.append(f2)
    H = dict(language="Braj/Gurmukhi")
    DEV = [  # name, figure, et, role, fid or wd, forms, relation
        ("Chandi", "Chandi (Durga), the Goddess", "deity", "divine", None, ("Chandi", r"goddess|Hindu"), ["ਚੰਡੀ", "ਚੰਡਿਕਾ", "ਚੰਡਕਾ"], ""),
        ("Durga", "Durga, the Goddess", "deity", "divine", None, ("Durga", r"goddess"), ["ਦੁਰਗਾ"], ""),
        ("Kalika", "Kali (Kalika), the Goddess", "deity", "divine", None, ("Kali", r"goddess"), ["ਕਾਲਿਕਾ", "ਕਾਲਕਾ"], ""),
        ("Bhagauti", "Bhagauti, God as the sword / the Goddess", "deity", "divine", "slug:sikh:bhagauti", None, ["ਭਗਉਤੀ", "ਭਗੌਤੀ"], "name of God (the sword) and of the Goddess"),
        ("Sita", "Sita, Hindu goddess", "deity", "personal", "Q191114", None, ["ਸੀਤਾ"], ""),
        ("Janaki", "Sita, Hindu goddess", "deity", "epithet", "Q191114", None, ["ਜਾਨਕੀ"], "epithet of Sita"),
        ("Krishna", "Krishna, Hindu deity", "deity", "personal", "Q42891", None, ["ਕ੍ਰਿਸਨ", "ਕ੍ਰਿਸਨੰ", "ਕ੍ਰਿਸਨਿ"], ""),
        ("Radha", "Radha, beloved of Krishna", "deity", "personal", None, ("Radha", r"goddess|Krishna"), ["ਰਾਧਾ", "ਰਾਧਿਕਾ", "ਰਾਧਕਾ"], ""),
        ("Lachhman", "Lakshmana, brother of Rama", "human", "personal", "Q917687", None, ["ਲਛਮਨ", "ਲਛਮਣ", "ਲਛਮਨਾ", "ਲਛਮਣੰ"], "Punjabi form of Lakshmana"),
        ("Hanuman", "Hanuman", "deity", "personal", "Q188618", None, ["ਹਨੂਮਾਨ", "ਹਨੂਮਾਨਿ", "ਹਨੂਮੰਤ"], ""),
        ("Ravan", "Ravana, king of Lanka", "demon", "personal", "Q235102", None, ["ਰਾਵਨ", "ਰਾਵਣ", "ਰਾਵਣਹਿ", "ਰਾਵਣੰ"], "Punjabi form of Ravana"),
        ("Dasrath", "Dasharatha, father of Rama", "royal", "personal", "Q1996692", None, ["ਦਸਰਥ"], "Punjabi form of Dasharatha"),
        ("Kausalya", "Kausalya, mother of Rama", "royal", "personal", None, ("Kausalya", r"Rama|mother|queen"), ["ਕਉਸਲਿਆ", "ਕੌਸੱਲਿਆ"], ""),
        ("Kaikeyi", "Kaikeyi, queen of Dasharatha", "royal", "personal", None, ("Kaikeyi", r"Rama|queen|Dasharatha"), ["ਕੈਕਈ"], ""),
        ("Shatrughan", "Shatrughna, Rama's brother", "human", "personal", "Q3518451", None, ["ਸਤ੍ਰੁਘਨ", "ਸਤ੍ਰੁਘਣ"], "Punjabi form of Shatrughna"),
        ("Jasudha", "Yashoda, foster-mother of Krishna", "human", "personal", None, ("Yashoda", r"Krishna|mother"), ["ਜਸੁਧਾ", "ਜਸੋਧਾ"], "Punjabi form of Yashoda"),
        ("Balbhadra", "Balarama, brother of Krishna", "deity", "personal", None, ("Balarama", r"Krishna|deity|brother"), ["ਬਲਿਭਦ੍ਰ", "ਬਲਿਭਦ੍ਰਹਿ"], "Punjabi form of Balabhadra"),
        ("Baldev", "Balarama, brother of Krishna", "deity", "epithet", None, ("Balarama", r"Krishna|deity|brother"), ["ਬਲਦੇਵ", "ਬਲਦੇਵਹਿ"], "another name of Balarama"),
        ("Rukmini", "Rukmini, wife of Krishna", "royal", "personal", None, ("Rukmini", r"Krishna|wife|consort|goddess"), ["ਰੁਕਮਿਨੀ", "ਰੁਕਮਿਨਿ", "ਰੁਕਮਨਿ"], ""),
        ("Kans", "Kamsa, king of Mathura", "demon", "personal", None, ("Kamsa", r"Mathura|king|Krishna"), ["ਕੰਸ", "ਕੰਸਹਿ"], "Punjabi form of Kamsa"),
        ("Kalki", "Kalki, the tenth avatar", "deity", "personal", None, ("Kalki", r"avatar|Vishnu"), ["ਕਲਕੀ"], ""),
        ("Mahishasur", "Mahishasura, buffalo demon", "demon", "personal", None, ("Mahishasura", r"demon|asura"), ["ਮਹਿਖਾਸੁਰ", "ਮਹਿਖਾਸੁਰੈ"], ""),
        ("Sumbh", "Shumbha, asura", "demon", "personal", None, ("Shumbha", r"asura|demon"), ["ਸੁੰਭ", "ਸੁੰਭਾਸੁਰ"], ""),
        ("Nisumbh", "Nishumbha, asura", "demon", "personal", None, ("Nishumbha", r"asura|demon"), ["ਨਿਸੁੰਭ", "ਨਿਸੁੰਭਹਿ"], ""),
        ("Parbati", "Parvati, goddess", "deity", "personal", None, ("Parvati", r"goddess"), ["ਪਾਰਬਤੀ"], "Punjabi form of Parvati"),
        ("Udhav", "Uddhava, friend of Krishna", "human", "personal", "slug:hindu:uddhava", None, ["ਊਧਵ", "ਊਧੋ"], "Punjabi form of Uddhava"),
        ("Sudama", "Sudama, friend of Krishna", "human", "personal", None, ("Sudama", r"Krishna|friend"), ["ਸੁਦਾਮਾ"], ""),
        ("Draupadi", "Draupadi", "human", "personal", "Q1057886", None, ["ਦ੍ਰੁਪਤੀ", "ਦ੍ਰੋਪਤੀ", "ਦ੍ਰੁਪਦੀ"], ""),
        ("Parshuram", "Parashurama, avatar", "deity", "personal", None, ("Parashurama", r"avatar|Vishnu"), ["ਪਰਸਰਾਮ", "ਪਰਸੁਰਾਮ"], "Punjabi form of Parashurama"),
        ("Prahlad", "Prahlada, devotee of Vishnu", "human", "personal", None, ("Prahlada", r"devotee|asura|Vishnu|Hiranyakashipu"), ["ਪ੍ਰਹਲਾਦ", "ਪ੍ਰਹਿਲਾਦਿ"], "Punjabi form of Prahlada"),
        ("Dhru", "Dhruva, devotee of Vishnu", "human", "personal", None, ("Dhruva", r"devotee|Vishnu|prince"), ["ਧ੍ਰੂਅ", "ਧ੍ਰੂ"], "Punjabi form of Dhruva"),
        ("Brahma", "Brahma, creator god", "deity", "divine", None, ("Brahma", r"Hindu god|creator|deity"), ["ਬ੍ਰਹਮਾ"], ""),
        ("Bisan", "Vishnu", "deity", "divine", None, ("Vishnu", r"Hindu|deity|god"), ["ਬਿਸਨੁ", "ਬਿਸਨ"], "Punjabi form of Vishnu"),
        ("Parth", "Arjuna, Pandava hero", "human", "epithet", "Q185790", None, ["ਪਾਰਥ", "ਪਾਰਥਿ"], "epithet of Arjuna (son of Pritha)"),
    ]
    for n, fig, et, role, fid, wdq, forms, rel in DEV:
        dg.append(Fig(n, fig, et, role, "", forms[0], [g(*forms)], fid=fid, wd=wdq, rel=rel, conf=0.8, key="dg" + n.lower(), lang=H["language"],
                      review=n in ("Bhagauti", "Kans", "Sumbh", "Bisan", "Dhru")))   # also words: sword, bronze, …
    for f in dg:
        if f.name == "Sumbh": f.review = True
    base = dict(language="Braj/Gurmukhi", corpus="Dasam Granth", source=SRC.format("Dasam Granth"))
    r, rv = build(dg, d, base, "Sikh", wd_tag="sikh", stats=stats); rows += r; review += rv
    # Mata Khivi in the Guru Granth Sahib (Ramkali ki Vaar of Satta and Balwand); the earlier GGS pass did not list her
    gg = ggs_segs()
    if gg:
        base = dict(language="Gurmukhi/Punjabi", corpus="Guru Granth Sahib", source="Guru Granth Sahib text via BaniDB API (Khalis Foundation)")
        r, rv = build([Fig("Khivi", "Mata Khivi, wife of Guru Angad", "human", "personal", "Khīvī", "ਖੀਵੀ", [g("ਖੀਵੀ")],
                           wd=("Mata Khivi", r"Sikh|Angad|wife"), conf=0.9)], gg, base, "Sikh", wd_tag="sikh", stats=stats)
        rows += r; review += rv
    return rows, review


# ───────────────────────────────────────────────────────────── scanned English translations (OCR)
ORD = {w: i for i, w in enumerate("first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth thirteenth "
       "fourteenth fifteenth sixteenth seventeenth eighteenth nineteenth twentieth".split(), 1)}
ORD.update({"thirtieth": 30})
def ordinal(w):
    w = w.lower().replace("-", " ").split()
    if len(w) == 2 and w[0] in ("twenty", "thirty"): return (20 if w[0] == "twenty" else 30) + ORD.get(w[1], 0)
    return ORD.get(w[0]) if len(w) == 1 else None

ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}
def roman(s):
    s = s.upper().replace("l", "I").replace("1", "I")
    if not s or any(c not in ROMAN for c in s): return None
    v = 0
    for i, c in enumerate(s):
        v += -ROMAN[c] if i + 1 < len(s) and ROMAN[s[i + 1]] > ROMAN[c] else ROMAN[c]
    return v

def ocr_lines(path):
    t = open(path, encoding="utf-8", errors="replace").read()
    t = re.sub(r"(\w)[-¬][ \t]*\n[ \t]*(\w+)", r"\1\2\n", t)          # re-join hyphenated words
    return [fold(l) for l in t.split("\n")]

def ocr_segs(lines, a, b, label, url, head):
    """Lines a..b -> one Seg per line; head(line, state) updates the citation state; label(state) -> (text, passage)."""
    st, segs = {}, []
    for l in lines[a:b]:
        head(l, st)
        if l.strip():
            t, p = label(st)
            segs.append(Seg(t, p, url, l))
    return segs

def W(*alts):   # whole-word OCR pattern (case-insensitive)
    return r"(?<![A-Za-z])(?:" + "|".join(alts) + r")(?![a-z])"


# ───────────────────────────────────────────────────────────── Jain
JAIN_FID = dict(mahavira="Q9422", siddhartha="Q7508053", trishala="Q7844032", sudharman="Q7633775", indrabhuti="Q15304493",
                arishtanemi="Q1746328", parshva="Q1400271", rishabha="Q9429", nandivardhana="slug:jain:nandivardhana",
                sudarshana="slug:jain:sudarshana", krishna="Q42891", brahmadatta=None)

def jain(stats):
    rows, review = [], []
    # ---- Acaranga, SBE 22 (Book I-II), from the better of the two scans
    p22 = get("https://archive.org/download/sbe22jainasutraspart1_202002/SBE%2022%20Jaina%20Sutras%20Part%201_djvu.txt",
              os.path.join(RAW_SACRED, "kalpa", "sbe22.txt")) or os.path.join(RAW_SACRED, "kalpa", "sbe22.txt")
    L = ocr_lines(p22)
    a = next(i for i, l in enumerate(L) if i > 1000 and re.match(r"\s*FIRST BOOK", l))
    k = next(i for i, l in enumerate(L) if i > a and re.match(r"\s*THE KALPA S\S*TRA\s*$", l))
    def h_ac(l, st):
        m = re.match(r"\s*BOOK (I+|[12])[,.]\s*LECTURE ((?:[\dIl]\s?){1,2})[,.]?\s*(?:LESSON ([\dIl]+))?", l)
        if m:
            st["b"] = "I" * len(m.group(1)) if m.group(1)[0] == "I" else "I" * int(m.group(1))
            st["l"] = m.group(2).replace(" ", "").replace("I", "1").replace("l", "1"); st["s"] = (m.group(3) or "").replace("I", "1").replace("l", "1")
            pg = re.search(r"(\d{2,3})\s*$", l)
            if pg: st["p"] = pg.group(1)
    def lab_ac(st):
        ref = ".".join(x for x in (st.get("b", "I"), st.get("l", "1"), st.get("s", "")) if x)
        return f"Book {st.get('b', 'I')}, Lecture {st.get('l', '1')}", f"Ācārāṅga {ref}"
    ac = ocr_segs(L, a, k, lab_ac, "https://archive.org/details/sbe22jainasutraspart1_202002", h_ac)
    base = dict(language="Prakrit", subtradition="Shvetambara", corpus="Acaranga Sutra",
                source="Ācārāṅga Sūtra, tr. H. Jacobi, Sacred Books of the East 22 (1884, public domain), archive.org OCR")
    figs = [
        Fig("Mahavira", "Mahavira (Vardhamana), 24th Tirthankara", "saint", "personal", "Mahāvīra", "", [W(r"Mah\S?v\S{1,2}ra")], fid=JAIN_FID["mahavira"]),
        Fig("Siddhartha", "Siddhartha, father of Mahavira", "royal", "personal", "Siddhārtha", "", [W(r"Sid-?\s?dh\S?rtha")], fid=JAIN_FID["siddhartha"]),
        Fig("Trishala", "Trishala, mother of Mahavira", "human", "personal", "Triśalā", "", [W(r"Tri-?\S?sal\S?")], fid=JAIN_FID["trishala"]),
        Fig("Videhadatta", "Trishala, mother of Mahavira", "human", "epithet", "Videhadattā", "", [W(r"Videhadatt\S?")], fid=JAIN_FID["trishala"], rel="another name of Trishala"),
        Fig("Priyakarini", "Trishala, mother of Mahavira", "human", "epithet", "Priyakāriṇī", "", [W(r"Priyak\S?ri\S?\S?")], fid=JAIN_FID["trishala"], rel="another name of Trishala"),
        Fig("Suparshva", "Suparshva, paternal uncle of Mahavira", "human", "personal", "Supārśva", "", [W(r"Sup\S?r\S?va")], key="suparshva-uncle"),
        Fig("Nandivardhana", "Nandivardhana, elder brother of Mahavira", "royal", "personal", "Nandivardhana", "", [W(r"Nandivardhana")], fid=JAIN_FID["nandivardhana"]),
        Fig("Sudarshana", "Sudarshana, sister of Mahavira", "human", "personal", "Sudarśanā", "", [W(r"Suda\S?\S?an\S?")], fid=JAIN_FID["sudarshana"]),
        Fig("Yashoda", "Yashoda, wife of Mahavira", "human", "personal", "Yaśodā", "", [W(r"Yas\S?od\S?", r"Yarod\S?")], wd=("Yashoda Jain", r"Mahavira|wife"), key="yashoda-jain"),
        Fig("Anojja", "Anojja (Priyadarshana), daughter of Mahavira", "human", "personal", "Aṇojjā", "", [W(r"A\s?nogg\S?")], key="anojja"),
        Fig("Priyadarshana", "Anojja (Priyadarshana), daughter of Mahavira", "human", "epithet", "Priyadarśanā", "", [W(r"Priyadar\S?\S?an\S?")], key="anojja", rel="other name of Anojja"),
        Fig("Seshavati", "Seshavati (Yashasvati), granddaughter of Mahavira", "human", "personal", "Śeṣavatī", "", [W(r"\S?Seshavat\S?")], key="seshavati"),
    ]
    for f in figs:
        if f.key in ("anojja", "seshavati", "suparshva-uncle"): f.fid = f"slug:jain:{f.key}"
    r, rv = build(figs, ac, base, "Jain", flags=re.I, wd_tag="jain", stats=stats); rows += r; review += rv
    # ---- Candana in the Kalpa Sutra (§135: "thirty-six thousand nuns with Candana at their head")
    LK = ocr_lines(os.path.join(RAW_SACRED, "kalpa", "mbp.txt"))
    kk = max(i for i, l in enumerate(LK) if re.match(r"\s*THE KALPA S\S?TRA\s*$", l))
    ks = []
    for i in range(kk, len(LK)):
        if re.match(r"\s*INDEX\.?\s*$", LK[i]): break
        m = re.search(r"\((\d{1,3})\)", " ".join(LK[i:i + 2]))
        ks.append(Seg("Lives of the Jinas", f"Kalpa Sutra, Lives of the Jinas §{m.group(1) if m else ''}".rstrip(" §"),
                      "https://archive.org/details/jainasutrasparti029233mbp", LK[i]))
    base = dict(language="Prakrit", subtradition="Shvetambara", corpus="Kalpa Sutra",
                source="Kalpa Sutra, tr. H. Jacobi, Sacred Books of the East 22 (1884, public domain), archive.org OCR")
    r, rv = build([Fig("Chandana", "Chandana (Chandanbala), head of Mahavira's nuns", "disciple", "personal", "Candanā", "",
                       [r"\S{0,2}andan(?:a|cL|d|A|&)(?=\s+at their head)"], wd=("Chandanbala", r"Jain|nun|Mahavira"), key="chandana", conf=0.8)],
                  ks, base, "Jain", wd_tag="jain", stats=stats); rows += r; review += rv
    # ---- Uttaradhyayana and Sutrakrtanga, SBE 45
    p45 = ia_text("mlbd.gainasutraspart20000vol-45.unse", "mlbd.gainasutraspart20000vol-45.unse_djvu.txt", os.path.join(RAW, "jain", "sbe45.txt")) \
          or os.path.join(RAW, "jain", "sbe45.txt")
    L = ocr_lines(p45)
    u0 = next(i for i, l in enumerate(L) if i > 1500 and l.strip() == "UTTARADHYAYANA.")
    s0 = next(i for i, l in enumerate(L) if i > u0 + 5000 and re.match(r"\s*FIRST BOOK\.?\s*$", l))
    s1 = next(i for i, l in enumerate(L) if i > s0 and re.match(r"\s*INDEX OF NAMES", l))
    def h_ut(l, st):
        m = re.match(r"\s*([A-Z]+(?:-[A-Z]+)?) LECTURE", l)
        if m and ordinal(m.group(1)): st["l"] = ordinal(m.group(1))
        m = re.match(r"\s*LECTURE ([IVXLl1x]+)[.,]\s*(\d+)?", l)
        if m and roman(m.group(1).upper()):
            v = roman(m.group(1).upper())
            if v in (st.get("l", 0), st.get("l", 0) + 1): st["l"] = v     # running heads are OCR-noisy: only confirm or step
    def lab_ut(st):
        return f"Lecture {st.get('l', 1)}", f"Uttarādhyayana, Lecture {st.get('l', 1)}"
    def h_su(l, st):
        m = re.match(r"\s*(FIRST|SECOND) BOOK", l)
        if m: st["b"] = 1 if m.group(1) == "FIRST" else 2; st["l"] = 1
        m = re.match(r"\s*([A-Z]+(?:-[A-Z]+)?) LECTURE", l)
        if m and ordinal(m.group(1)): st["l"] = ordinal(m.group(1))
    def lab_su(st):
        return f"Book {st.get('b', 1)}", f"Sūtrakṛtāṅga {'I' * st.get('b', 1)}.{st.get('l', 1)}"
    url45 = "https://archive.org/details/mlbd.gainasutraspart20000vol-45.unse"
    ut = ocr_segs(L, u0, s0, lab_ut, url45, h_ut); su = ocr_segs(L, s0, s1, lab_su, url45, h_su)
    SRC45 = "{}, tr. H. Jacobi, Sacred Books of the East 45 (1895, public domain), archive.org OCR"
    UT = [
        Fig("Mahavira", "Mahavira (Vardhamana), 24th Tirthankara", "saint", "personal", "Mahāvīra", "", [W(r"Mah\S?v\S{1,2}ra")], fid=JAIN_FID["mahavira"]),
        Fig("Gautama", "Indrabhuti Gautama, first ganadhara of Mahavira", "disciple", "personal", "Gautama", "", [W(r"Gautama")], fid=JAIN_FID["indrabhuti"],
            rel="clan name of Indrabhuti"),
        Fig("Keshi", "Keshi, follower of Parshva", "saint", "personal", "Keśi", "", [W(r"Kesi")], wd=("Keshi Kumar", r"Jain|Parshva|monk")),
        Fig("Parshva", "Parshvanatha, 23rd Tirthankara", "saint", "personal", "Pārśva", "", [W(r"P\S?rsva")], fid=JAIN_FID["parshva"]),
        Fig("Arishtanemi", "Arishtanemi (Neminatha), 22nd Tirthankara", "saint", "personal", "Ariṣṭanemi", "", [W(r"Arisht\S?nemi")], fid=JAIN_FID["arishtanemi"]),
        Fig("Rathanemi", "Rathanemi, brother of Arishtanemi", "saint", "personal", "Rathanemi", "", [W(r"Rathanemi")], wd=("Rathanemi", r"Jain|Neminatha")),
        Fig("Rajimati", "Rajimati, betrothed of Arishtanemi", "saint", "personal", "Rājīmatī", "", [W(r"R\S?g\S?mat\S?")], wd=("Rajimati", r"Jain|Neminatha|princess|nun")),
        Fig("Keshava", "Krishna, Hindu deity", "deity", "epithet", "Keśava", "", [W(r"Kesava")], fid=JAIN_FID["krishna"], rel="epithet of Krishna (Vasudeva)"),
        Fig("Vasudeva", "Krishna, Hindu deity", "deity", "epithet", "Vāsudeva", "", [W(r"V\S?sudeva")], fid=JAIN_FID["krishna"], rel="epithet of Krishna", review=True),
        Fig("Samudravijaya", "Samudravijaya, father of Arishtanemi", "royal", "personal", "Samudravijaya", "", [W(r"Samudravigaya", r"Samudravijaya")], key="samudravijaya"),
        Fig("Ugrasena", "Ugrasena, king, father of Rajimati", "royal", "personal", "Ugrasena", "", [W(r"Ugrasena")], key="ugrasena"),
        Fig("Nami", "Nami, king of Videha (Uttaradhyayana 9)", "royal", "personal", "Nami", "", [W(r"Nami")], key="nami-videha",
            rel="the pratyekabuddha king, not the 21st Tirthankara"),
        Fig("Harikesha", "Harikesha Bala, Chandala monk", "saint", "personal", "Harikeśa", "", [W(r"Harikesa")], key="harikesha"),
        Fig("Chitra", "Chitra, brother of Sambhuta", "saint", "personal", "Citra", "", [W(r"[KX]itra")], key="chitra-jain"),
        Fig("Sambhuta", "Sambhuta (Brahmadatta in his former birth)", "human", "personal", "Sambhūta", "", [W(r"Sambh\S?ta")], key="sambhuta"),
        Fig("Brahmadatta", "Brahmadatta, universal monarch", "royal", "personal", "Brahmadatta", "", [W(r"Brahmadatta")], key="brahmadatta-cakravartin"),
        Fig("Mrigaputra", "Mrigaputra, prince turned monk", "saint", "personal", "Mṛgāputra", "", [W(r"Mrig\S?putra")], key="mrigaputra"),
        Fig("Samudrapala", "Samudrapala, merchant's son turned monk", "saint", "personal", "Samudrapāla", "", [W(r"Samudrap\S?la")], key="samudrapala"),
        Fig("Jayaghosha", "Jayaghosha, Brahmin turned monk", "saint", "personal", "Jayaghoṣa", "", [W(r"Gayagh\S?sha")], key="jayaghosha"),
        Fig("Vijayaghosha", "Vijayaghosha, Brahmin sacrificer", "human", "personal", "Vijayaghoṣa", "", [W(r"Vigayagh\S?sha")], key="vijayaghosha"),
        Fig("Kapila", "Kapila, Brahmin monk (Uttaradhyayana 8)", "saint", "personal", "Kapila", "", [W(r"Kapila")], key="kapila-jain"),
        Fig("Bhrigu", "Bhrigu, family priest (Uttaradhyayana 14)", "human", "personal", "Bhṛgu", "", [W(r"Bhrigu")], key="bhrigu-jain", review=True),
        Fig("Ishukara", "Ishukara, king (Uttaradhyayana 14)", "royal", "personal", "Iṣukāra", "", [W(r"Ishuk\S?ra")], key="ishukara"),
        Fig("Kunthu", "Kunthu, 17th Tirthankara", "saint", "personal", "Kunthu", "", [W(r"Kunthu")], fid="Q2790221"),
        Fig("Shreyamsa", "Shreyamsa, 11th Tirthankara", "saint", "personal", "Śreyāṃsa", "", [W(r"Srey\S?msa")], fid="slug:jain:shreyamsa", review=True),
    ]
    base = dict(language="Prakrit", subtradition="Shvetambara", corpus="Uttaradhyayana Sutra", source=SRC45.format("Uttarādhyayana Sūtra"))
    r, rv = build(UT, ut, base, "Jain", flags=re.I, wd_tag="jain", stats=stats); rows += r; review += rv
    SU = [
        Fig("Mahavira", "Mahavira (Vardhamana), 24th Tirthankara", "saint", "personal", "Mahāvīra", "", [W(r"Mah\S?v\S{1,2}ra")], fid=JAIN_FID["mahavira"]),
        Fig("Sudharman", "Arya Sudharman, ganadhara", "disciple", "personal", "Sudharman", "", [W(r"Sudharman")], fid=JAIN_FID["sudharman"]),
        Fig("Jambu", "Jambu (Jambusvamin), disciple of Sudharman", "disciple", "personal", "Jambū", "", [W(r"[GJ]amb\S{1,2}(?:sv\S?min)?")], wd=("Jambuswami", r"Jain|disciple|kevali")),
        Fig("Gautama", "Indrabhuti Gautama, first ganadhara of Mahavira", "disciple", "personal", "Gautama", "", [W(r"Gautama")], fid=JAIN_FID["indrabhuti"], rel="clan name of Indrabhuti"),
        Fig("Indrabhuti", "Indrabhuti Gautama, first ganadhara of Mahavira", "disciple", "personal", "Indrabhūti", "", [W(r"Indrabh\S?ti")], fid=JAIN_FID["indrabhuti"]),
        Fig("Ardraka", "Ardraka, prince who debated Goshala", "saint", "personal", "Ārdraka", "", [W(r"\S?rdraka")], wd=("Ardraka", r"Jain|prince|monk"), key="ardraka"),
        Fig("Goshala", "Goshala Mankhaliputta, Ajivika teacher", "human", "personal", "Gośāla", "", [W(r"Gos\S?la")], wd=("Makkhali Gosala", r"Ajivika|ascetic|teacher")),
        Fig("Udaka", "Udaka Pedhalaputra, follower of Parshva", "human", "personal", "Udaka", "", [W(r"Udaka")], key="udaka", review=True),
        Fig("Parshva", "Parshvanatha, 23rd Tirthankara", "saint", "personal", "Pārśva", "", [W(r"P\S?rsva")], fid=JAIN_FID["parshva"]),
        Fig("Kashyapa", "Mahavira (Vardhamana), 24th Tirthankara", "saint", "epithet", "Kāśyapa", "", [W(r"K\S?syapa")], fid=JAIN_FID["mahavira"], rel="gotra name of Mahavira", review=True),
        Fig("Jnatriputra", "Mahavira (Vardhamana), 24th Tirthankara", "saint", "epithet", "Jñātṛputra", "", [W(r"[GJ]\S?\S?\S?triputra")], fid=JAIN_FID["mahavira"], rel="epithet of Mahavira (son of the Jnatri clan)"),
    ]
    base = dict(language="Prakrit", subtradition="Shvetambara", corpus="Sutrakrtanga", source=SRC45.format("Sūtrakṛtāṅga"))
    r, rv = build(SU, su, base, "Jain", flags=re.I, wd_tag="jain", stats=stats); rows += r; review += rv
    # ---- Uvasagadasao, tr. A.F.R. Hoernle, vol. 2 (1888)
    pu = ia_text("hoernle-the-uvasagadasao-v.-2-1888", "Hoernle The Uvāsagadasāo V. 2 ( 1888)_djvu.txt", os.path.join(RAW, "jain", "uvasaga2.txt")) \
         or os.path.join(RAW, "jain", "uvasaga2.txt")
    L = ocr_lines(pu)
    u0 = next(i for i, l in enumerate(L) if re.match(r"\s*FIRST LECTURE", l))
    u1 = next((i for i, l in enumerate(L) if i > u0 + 5000 and re.match(r"\s*(APPENDIX|INDEX)[ .IVX]*$", l)), len(L))
    def h_uv(l, st):
        m = re.match(r"\s*([A-Z]+) LECTURE\.?\s*$", l.replace("KIGHTH", "EIGHTH"))
        if m and ordinal(m.group(1)): st["l"] = ordinal(m.group(1)); st["p"] = 0
        m = re.match(r"\s*(\d{1,3})\. [A-Z“\"]", l)
        if m and 0 < int(m.group(1)) - st.get("p", 0) <= 12: st["p"] = int(m.group(1))
    def lab_uv(st):
        return f"Lecture {st.get('l', 1)}", f"Uvāsagadasāo {st.get('l', 1)}" + (f" §{st['p']}" if st.get("p") else "")
    uv = ocr_segs(L, u0, u1, lab_uv, "https://archive.org/details/hoernle-the-uvasagadasao-v.-2-1888", h_uv)
    UV = [
        Fig("Ananda", "Ananda, householder of Vaniyagama, lay disciple of Mahavira", "human", "personal", "Āṇanda", "", [W(r"\S?nanda")],
            key="ananda-jain-householder", rel="the householder Ananda, not the Buddha's attendant"),
        Fig("Sivananda", "Sivananda, wife of the householder Ananda", "human", "personal", "Sivanandā", "", [W(r"Sivanand\S?")], key="sivananda"),
        Fig("Kamadeva", "Kamadeva, householder of Champa, lay disciple", "human", "personal", "Kāmadeva", "", [W(r"K\S?madeva")], key="kamadeva-jain"),
        Fig("Chulanipiya", "Chulanipiya, householder of Benares, lay disciple", "human", "personal", "Culaṇīpiyā", "", [W(r"Chulan\S?piy\S?")], key="chulanipiya"),
        Fig("Suradeva", "Suradeva, householder of Benares, lay disciple", "human", "personal", "Surādeva", "", [W(r"Sur\S?deva")], key="suradeva"),
        Fig("Chullasayaga", "Chullasayaga, householder of Alabhiya, lay disciple", "human", "personal", "Cullasayaga", "", [W(r"Chullas\S?yaga")], key="chullasayaga"),
        Fig("Kundakoliya", "Kundakoliya, householder of Kampillapura, lay disciple", "human", "personal", "Kuṇḍakoliya", "", [W(r"Kundakoliya")], key="kundakoliya"),
        Fig("Saddalaputta", "Saddalaputta, potter of Polasapura, lay disciple", "human", "personal", "Saddālaputta", "", [W(r"Sadd\S?\S?laputta")], key="saddalaputta"),
        Fig("Aggimitta", "Aggimitta, wife of Saddalaputta", "human", "personal", "Aggimittā", "", [W(r"Aggimitt\S?")], key="aggimitta"),
        Fig("Mahasayaga", "Mahasayaga, householder of Rayagiha, lay disciple", "human", "personal", "Mahāsayaga", "", [W(r"Mah\S?sayaga")], key="mahasayaga"),
        Fig("Revai", "Revai (Revati), wife of Mahasayaga", "human", "personal", "Revaī", "", [W(r"Reva\S")], key="revai"),
        Fig("Nandinipiya", "Nandinipiya, householder of Savatthi, lay disciple", "human", "personal", "Naṃdiṇīpiyā", "", [W(r"Nandin\S?piy\S?")], key="nandinipiya"),
        Fig("Salihipiya", "Salihipiya, householder of Savatthi, lay disciple", "human", "personal", "Sālihīpiyā", "", [W(r"S\S?lih\S?piy\S?")], key="salihipiya"),
        Fig("Bhadda", "Bhadda, wife of Kamadeva", "human", "personal", "Bhaddā", "", [W(r"Bhadd\S")], key="bhadda-jain", review=True),
        Fig("Goshala", "Goshala Mankhaliputta, Ajivika teacher", "human", "personal", "Gosāla", "", [W(r"Gos\S{1,2}la")], wd=("Makkhali Gosala", r"Ajivika|ascetic|teacher")),
        Fig("Goyama", "Indrabhuti Gautama, first ganadhara of Mahavira", "disciple", "personal", "Goyama", "", [W(r"Goyama")], fid=JAIN_FID["indrabhuti"], rel="Prakrit form of Gautama"),
        Fig("Suhamma", "Arya Sudharman, ganadhara", "disciple", "personal", "Suhamma", "", [W(r"Suhamma", r"Sohamma")], fid=JAIN_FID["sudharman"], rel="Prakrit form of Sudharman"),
        Fig("Jambu", "Jambu (Jambusvamin), disciple of Sudharman", "disciple", "personal", "Jambū", "", [W(r"J[au]mb\S")], wd=("Jambuswami", r"Jain|disciple|kevali"), rel="Prakrit form"),
        Fig("Mahavira", "Mahavira (Vardhamana), 24th Tirthankara", "saint", "personal", "Mahāvīra", "", [W(r"Mah\S{1,2}v\S{1,2}ra")], fid=JAIN_FID["mahavira"]),
    ]
    base = dict(language="Prakrit", subtradition="Shvetambara", corpus="Upasakadasha",
                source="Uvāsagadasāo, tr. A.F.R. Hoernle (1888, public domain), archive.org OCR")
    r, rv = build(UV, uv, base, "Jain", flags=re.I, wd_tag="jain", stats=stats); rows += r; review += rv
    return rows, review



# ───────────────────────────────────────────────────────────── Buddhist
GRETIL_TXT = "https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/plaintext/{}.txt"
GRETIL_HTML = "https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/html/{}.htm"
SL = "a-zāīūṛṝḷṃṁḥñṅṇṭḍśṣ"
def sk(*stems):   # Sanskrit stem(s), any inflection / compound continuation, not inside another word
    return rf"(?:(?<![{SL}])|(?<=ārya)|(?<=āryam))(?:" + "|".join(stems) + rf")[{SL}]*"

BUD = dict(buddha="Q9441", ananda="Q28988", sariputta="Q320142", moggallana="Q379814", rahula="Q218969", devadatta="Q451043",
           suddhodana="Q226488", maya="Q877831", yasodhara="Q466572", sakka="Q1444745", ajatasattu="Q379242", bimbisara="Q317765",
           pasenadi="Q3055324", visakha="Q2467542", angulimala="Q263512", kassapa_past="Q1808464", mahakassapa="Q335304",
           subhuti="Q1144771", maitreya="Q193461", manjushri="Q471696", avalokiteshvara="Q193849", samantabhadra="Q868306",
           amitabha="Q236242", akshobhya="Q756612", dipankara="Q1227131", brahmadatta="slug:buddhist:brahmadatta-1",
           purna="slug:buddhist:punna-4", sita="Q191114", lakshmana="Q917687", dasharatha="Q1996692", ravana="Q235102", krishna="Q42891")

def gretil_segs(fid, corpus, chapters):
    path = get(GRETIL_TXT.format(fid), os.path.join(RAW, "gretil", fid + ".txt"))
    raw = unicodedata.normalize("NFC", open(path, encoding="utf-8").read())
    body = raw.split("\n# Text", 1)[1]
    st, segs, pending = {}, [], []
    for l in body.split("\n"):
        lab = chapters(l, st)
        if lab == "flush":            # a verse number closes the lines before it
            for x in pending: segs.append(Seg(st.get("t", ""), st["p"], GRETIL_HTML.format(fid), x))
            pending = []; continue
        if l.strip():
            if st.get("verse_mode"): pending.append(l.lower())
            else: segs.append(Seg(st.get("t", ""), st.get("p", corpus), GRETIL_HTML.format(fid), l.lower()))
    return segs

def ch_asp(l, st):
    m = re.match(r"asp_(\d+):", l)
    if m: st["c"] = int(m.group(1)); st["t"] = f"Chapter {st['c']}"
    m = re.search(r"\(vaidya (\d+)\)", l)
    if m: st["v"] = m.group(1)
    st["p"] = f"Aṣṭasāhasrikā ch. {st.get('c', 1)}" + (f" (Vaidya p. {st['v']})" if st.get("v") else "")

GV_HEADS = {}
def ch_gv(l, st):
    m = re.match(r"(\d{1,2})(?: //)? ([a-zāīūṛṃṇṭḍśṣñ]+[ḥ]?) /\s*$", l.strip()) or re.match(r"(\d{1,2}) // (nidānaparivartaḥ) /", l.strip())
    if m and int(m.group(1)) == st.get("c", 0) + 1 or (m and int(m.group(1)) > st.get("c", 0) and int(m.group(1)) - st.get("c", 0) <= 2):
        st["c"] = int(m.group(1)); GV_HEADS[st["c"]] = m.group(2); st["t"] = f"Chapter {st['c']}"
    st["p"] = f"Gaṇḍavyūha ch. {st.get('c', 1)}"

def ch_dbh(l, st):
    m = re.match(r"(\d{1,2}) ([a-zāīūṛṃṇṭḍśṣ]+) nāma", l.strip())
    if m and "c2" not in st: st["c"] = int(m.group(1))
    if re.match(r"11 parīndanā", l.strip()): st["c2"] = 1      # the verse summary that follows repeats the bhūmi heads
    st["t"] = ""; st["p"] = f"Daśabhūmika, bhūmi {st.get('c', 1)}" if st.get("c", 1) <= 10 else "Daśabhūmika, parīndanā"

def ch_lank(l, st):
    m = re.match(r"start parivarta (\d+)", l.strip())
    if m: st["c"] = int(m.group(1))
    st["t"] = f"Chapter {st.get('c', 1)}"; st["p"] = f"Laṅkāvatāra ch. {st.get('c', 1)}"

def ch_verses(tag, label):
    def f(l, st):
        st["verse_mode"] = True
        m = re.search(rf"{tag}_?(\d+(?:\.\d+)?)", l)
        if m:
            st["p"] = f"{label} {m.group(1)}"; return "flush"
    return f

def jataka_segs():
    vols = {1: ("jatakaorstorieso01cowe", "jatakaorstorieso01cowe_djvu.txt"), 2: ("jatakaorstorieso02cowe", "jatakaorstorieso02cowe_djvu.txt"),
            3: ("jatakaorstorieso03cowe", "jatakaorstorieso03cowe_djvu.txt"),
            4: ("dli.ernet.18111", "18111-The Jataka Or Stories Of The Buddhas Former Briths Vol - Iv (1901)_djvu.txt"),
            5: ("cup-jataka-vol-5-francis-cowell-1905", "CUP-Jataka-vol-5-Francis-Cowell-1905_djvu.txt"),
            6: ("jatakaorstorieso06cowe", "jatakaorstorieso06cowe_djvu.txt")}
    first = {1: 1, 2: 151, 3: 301, 4: 439, 5: 511, 6: 538}
    segs = []
    for v, (ident, fn) in vols.items():
        p = ia_text(ident, fn, os.path.join(RAW, "jataka", f"v{v:02d}.txt")) or os.path.join(RAW, "jataka", f"v{v:02d}.txt")
        L = ocr_lines(p); cur = None
        end = next((i for i, l in enumerate(L) if i > len(L) // 2 and re.match(r"\s*(GENERAL )?INDEX\.?\s*$", l)), len(L))
        for l in L[:end]:
            m = re.match(r"\s*No\.\s+(\d{1,3})[.\s]", l)
            if m:
                n = int(m.group(1))
                if (cur is None and abs(n - first[v]) <= 2) or (cur is not None and 0 <= n - cur <= 4): cur = n
            if cur is None or not l.strip() or re.match(r"\s*[A-Z][\w\-' ]{2,40}\s+\d{1,3}\s*$", l): continue   # contents lines
            segs.append(Seg(f"Jataka No. {cur}", f"Jātaka No. {cur} (Cowell ed., vol. {v})", f"https://archive.org/details/{ident}", l))
    return segs

# names shared by several Jataka characters: counted only in the story the row is about
JATAKA_SCOPE = {"Sīvalī": {"Jataka No. 539"}, "Sāma": {"Jataka No. 540"}, "Kusa": {"Jataka No. 531"}, "Kuṇāla": {"Jataka No. 536"},
                "Sivi": {"Jataka No. 499"}, "Dasaratha": {"Jataka No. 461"}, "Amarā": {"Jataka No. 546", "Jataka No. 112"},
                "Temiya": {"Jataka No. 538"}, "Nimi": {"Jataka No. 541", "Jataka No. 9"}}

def buddhist(stats):
    rows, review = [], []
    # ---- Jataka prose, Cowell's translation
    js = jataka_segs()
    print(f"  Jataka: {len(js)} lines, {len({s.text for s in js})} stories", file=sys.stderr)
    J = [  # name (Pali, Cowell's spelling folded), figure, et, fid / wd, extra pattern, relation, review
        ("Bodhisatta", "Gotama, the Buddha", "title", "title", BUD["buddha"], None, None, "the Buddha in a former birth", False),
        ("Brahmadatta", "Brahmadatta, king of Benares (Kasi)", "royal", "personal", BUD["brahmadatta"], None, None, "the king of Benares in most Jataka frames", False),
        ("Devadatta", "Devadatta, the Buddha's cousin", "disciple", "personal", BUD["devadatta"], None, None, "", False),
        ("Ānanda", "Ānanda, the Buddha's attendant", "disciple", "personal", BUD["ananda"], None, None, "", False),
        ("Sāriputta", "Sāriputta, chief disciple", "disciple", "personal", BUD["sariputta"], None, None, "", False),
        ("Moggallāna", "Mahāmoggallāna, chief disciple", "disciple", "personal", BUD["moggallana"], None, None, "", False),
        ("Rāhula", "Rāhula, the Buddha's son", "disciple", "personal", BUD["rahula"], None, None, "", False),
        ("Suddhodana", "Suddhodana, the Buddha's father", "royal", "personal", BUD["suddhodana"], None, None, "", False),
        ("Anāthapiṇḍika", "Anāthapiṇḍika, lay disciple", "human", "personal", "Q550218", None, None, "", False),
        ("Visākhā", "Visākhā Migāramātā, chief laywoman disciple", "human", "personal", BUD["visakha"], None, None, "", True),
        ("Ajātasattu", "Ajātasattu, king of Magadha", "royal", "personal", BUD["ajatasattu"], None, None, "", False),
        ("Bimbisāra", "Bimbisāra, king of Magadha", "royal", "personal", BUD["bimbisara"], None, None, "", False),
        ("Uppalavaṇṇā", "Uppalavaṇṇā, chief nun", "disciple", "personal", None, ("Uppalavanna", r"nun|disciple|bhikkhuni"), None, "", False),
        ("Khemā", "Khemā (several queens and a chief nun of this name)", "human", "personal", "slug:buddhist:khemaa-jataka", None, None, "", True),
        ("Aṅgulimāla", "Aṅgulimāla, robber turned monk", "disciple", "personal", BUD["angulimala"], None, None, "", False),
        ("Mallikā", "Mallikā, queen of Kosala", "royal", "personal", None, ("Mallika queen", r"queen|Kosala|Pasenadi"), None, "", True),
        ("Sakka", "Sakka, king of the devas", "deity", "divine", BUD["sakka"], None, None, "", False),
        ("Mātali", "Mātali, Sakka's charioteer", "deity", "personal", None, ("Matali", r"charioteer|Indra|Sakka"), None, "", False),
        ("Vessantara", "Vessantara, the Bodhisatta's last human birth before Gotama", "royal", "personal", None, ("Vessantara", r"Jataka|prince|Buddha"), None, "", False),
        ("Maddī", "Maddī, wife of Vessantara", "royal", "personal", None, ("Maddi", r"Vessantara|princess|Jataka"), None, "", False),
        ("Jāli", "Jāli, son of Vessantara", "royal", "personal", None, None, None, "", False),
        ("Kaṇhājinā", "Kaṇhājinā, daughter of Vessantara", "royal", "personal", None, None, None, "", False),
        ("Jūjaka", "Jūjaka, the brahmin who begged Vessantara's children", "human", "personal", None, ("Jujaka", r"brahmin|Vessantara|Jataka"), None, "", False),
        ("Phusatī", "Phusatī, mother of Vessantara", "royal", "personal", None, None, None, "", False),
        ("Mahājanaka", "Mahājanaka, king of Mithilā (Jātaka 539)", "royal", "personal", None, ("Mahajanaka", r"Jataka|king"), None, "", False),
        ("Sīvalī", "Sīvalī, queen of Mahājanaka", "royal", "personal", None, None, None, "", True),
        ("Temiya", "Temiya, the 'dumb cripple' prince (Jātaka 538)", "royal", "personal", None, ("Temiya", r"Jataka|prince"), None, "", False),
        ("Nimi", "Nimi, king of Mithilā (Jātaka 541)", "royal", "personal", None, ("Nimi Jataka", r"Jataka|king"), None, "", True),
        ("Mahosadha", "Mahosadha, the wise minister (Jātaka 546)", "human", "personal", None, ("Mahosadha", r"Jataka|minister|sage"), None, "", False),
        ("Amarā", "Amarā, wife of Mahosadha", "human", "personal", None, None, None, "", True),
        ("Vidhura", "Vidhura, the wise minister (Jātaka 545)", "human", "personal", None, ("Vidhurapandita", r"Jataka|minister|sage"), None, "", False),
        ("Puṇṇaka", "Puṇṇaka, yakkha general (Jātaka 545)", "mythological_being", "personal", None, None, None, "", True),
        ("Bhūridatta", "Bhūridatta, nāga prince (Jātaka 543)", "mythological_being", "personal", None, ("Bhuridatta", r"Jataka|naga"), None, "", False),
        ("Sāma", "Sāma (Suvaṇṇasāma), devoted son (Jātaka 540)", "human", "personal", None, ("Suvannasama", r"Jataka"), None, "", True),
        ("Dukūlaka", "Dukūlaka, father of Sāma", "human", "personal", None, None, None, "", False),
        ("Pārikā", "Pārikā, mother of Sāma", "human", "personal", None, None, None, "", False),
        ("Candakumāra", "Candakumāra, prince (Jātaka 542)", "royal", "personal", None, None, None, "", False),
        ("Nārada", "Nārada, sage", "sage", "personal", None, None, None, "", True),
        ("Kusa", "Kusa, the ugly prince (Jātaka 531)", "royal", "personal", None, ("Kusa Jataka", r"Jataka"), None, "", True),
        ("Pabhāvatī", "Pabhāvatī, wife of Kusa", "royal", "personal", None, None, None, "", False),
        ("Sutasoma", "Sutasoma, prince (Jātaka 537)", "royal", "personal", None, None, None, "", False),
        ("Ummadantī", "Ummadantī, the maddening beauty (Jātaka 527)", "human", "personal", None, None, None, "", False),
        ("Sivi", "Sivi, king who gave his eyes (Jātaka 499)", "royal", "personal", None, ("Sivi Jataka", r"Jataka|king"), None, "", True),
        ("Kuṇāla", "Kuṇāla, the cuckoo (Jātaka 536)", "mythological_being", "personal", None, None, None, "", True),
        ("Isisiṅga", "Isisiṅga (Ṛṣyaśṛṅga), horned ascetic", "sage", "personal", None, None, None, "", False),
        ("Nalinikā", "Nalinikā, princess who seduced Isisiṅga", "royal", "personal", None, None, None, "", False),
        ("Alambusā", "Alambusā, celestial nymph", "mythological_being", "personal", None, None, None, "", False),
        ("Hatthipāla", "Hatthipāla, brahmin's son turned ascetic (Jātaka 509)", "sage", "personal", None, None, None, "", True),
        ("Losaka", "Losaka Tissa, the unlucky monk (Jātaka 41)", "disciple", "personal", None, None, None, "", False),
        ("Mittavindaka", "Mittavindaka, the greedy sailor", "human", "personal", None, None, None, "", False),
        ("Sambulā", "Sambulā, faithful wife (Jātaka 519)", "royal", "personal", None, None, None, "", False),
        ("Sotthisena", "Sotthisena, husband of Sambulā", "royal", "personal", None, None, None, "", False),
        ("Chaddanta", "Chaddanta, the six-tusked elephant king (Jātaka 514)", "mythological_being", "personal", None, None, None, "", False),
        ("Rāma", "Rāma-paṇḍita (Dasaratha Jātaka 461)", "royal", "personal", "Q160213", None, None, "Rāmapaṇḍita of the Dasaratha Jātaka", True),
        ("Sītā", "Sita, Hindu goddess", "royal", "personal", BUD["sita"], None, None, "Pali form; sister-wife of Rāma in the Dasaratha Jātaka", False),
        ("Lakkhaṇa", "Lakshmana, brother of Rama", "royal", "personal", BUD["lakshmana"], None, None, "Pali form of Lakṣmaṇa", False),
        ("Dasaratha", "Dasharatha, father of Rama", "royal", "personal", BUD["dasharatha"], None, None, "Pali form of Daśaratha", False),
        ("Vāsudeva", "Krishna, Hindu deity", "royal", "epithet", BUD["krishna"], None, None, "Vāsudeva-Kaṇha of the Ghata Jātaka (454)", True),
        ("Baladeva", "Balarama, brother of Krishna", "royal", "personal", None, ("Balarama", r"Krishna|deity|brother"), None, "Pali form", False),
        ("Vissakamma", "Vissakamma (Viśvakarman), divine craftsman", "deity", "personal", None, ("Vishvakarma", r"craftsman|architect|deity|god"), None, "Pali form", False),
        ("Pañcasikha", "Pañcasikha, gandhabba musician", "mythological_being", "personal", None, None, None, "", False),
        ("Sujampati", "Sakka, king of the devas", "deity", "epithet", BUD["sakka"], None, None, "epithet of Sakka (husband of Sujā)", False),
        ("Setaketu", "Setaketu, proud young brahmin (Jātaka 377)", "human", "personal", None, None, None, "", False),
        ("Uddālaka", "Uddālaka, brahmin (Jātaka 487)", "human", "personal", None, None, None, "", False),
    ]
    figs = []
    for nm, label, et, role, fid, wdq, xpat, rel, rv in J:
        f_ = fold(nm)
        sc = JATAKA_SCOPE.get(nm)
        figs.append(Fig(latin_pali(nm), label, et, role, nm, nm, [rf"\b{f_}\b(?![-\w]*[Jj][aā]taka)(?!\s+Birth)(?!-sprite)"] + ([xpat] if xpat else []), fid=fid, wd=wdq, rel=rel,
                        review=rv and not sc, conf=0.8, key="jataka-" + f_.lower(), lang="Pali",
                        scope=(lambda s_, sc=sc: s_.text in sc) if sc else None))
    base = dict(language="Pali", subtradition="Theravada", corpus="Jataka",
                source="Jātaka, tr. E.B. Cowell, R. Chalmers, W.H.D. Rouse, H.T. Francis, R.A. Neil (1895-1907, public domain), archive.org OCR")
    r, rv = build(figs, js, base, "Buddhist", wd_tag="bud", stats=stats); rows += r; review += rv
    # ---- Mahayana Sanskrit (GRETIL)
    texts = [
        ("sa_aSTasAhasrikA-prajJApAramitA", "Astasahasrika Prajnaparamita", "Aṣṭasāhasrikā Prajñāpāramitā, ed. P.L. Vaidya 1960", ch_asp, [
            ("Subhūti", "subhūti", [sk("subhūt")], BUD["subhuti"], None, "disciple", "personal", ""),
            ("Śāriputra", "śāriputra", [sk("śāriputr", "śāradvatīputr")], BUD["sariputta"], None, "disciple", "personal", "Sanskrit form of Pali Sāriputta"),
            ("Śakra", "śakra", [sk("śakro devānām", "śakreṇa devānām", "śakrasya devānām", "śakraṃ devānām")], BUD["sakka"], None, "deity", "divine", "Sanskrit form of Pali Sakka"),
            ("Kauśika", "kauśika", [sk("kauśik")], BUD["sakka"], None, "deity", "epithet", "epithet of Śakra"),
            ("Maitreya", "maitreya", [sk("maitrey")], BUD["maitreya"], None, "bodhisattva", "personal", ""),
            ("Pūrṇa Maitrāyaṇīputra", "pūrṇa maitrāyaṇīputra", [sk("maitrāyaṇīputr")], BUD["purna"], None, "disciple", "personal", ""),
            ("Ānanda", "ānanda", [rf"(?<![{SL}])ānand(?:a|aḥ|o|ena|asya|am|aṃ){'(?![' + SL + '])'}"], BUD["ananda"], None, "disciple", "personal", ""),
            ("Sadāprarudita", "sadāprarudita", [sk("sadāprarudit")], None, ("Sadaprarudita", r"bodhisattva"), "bodhisattva", "personal", ""),
            ("Dharmodgata", "dharmodgata", [sk("dharmodgat")], None, ("Dharmodgata", r"bodhisattva"), "bodhisattva", "personal", ""),
            ("Akṣobhya", "akṣobhya", [sk("akṣobhy")], BUD["akshobhya"], None, "sage", "personal", ""),
            ("Dīpaṃkara", "dīpaṃkara", [sk("dīpaṃkar", "dīpaṅkar")], BUD["dipankara"], None, "sage", "personal", ""),
            ("Gaṅgadevā", "gaṅgadevā", [sk("gaṅgadev")], None, None, "human", "personal", "the laywoman Gaṅgadevā, foretold to become a Buddha"),
        ]),
        ("sa_gaNDavyUhasUtra", "Gandavyuha", "Gaṇḍavyūhasūtra, ed. P.L. Vaidya 1960", ch_gv, [
            ("Sudhana", "sudhana", [sk("sudhan")], None, ("Sudhana", r"bodhisattva|pilgrim|Gandavyuha|youth"), "bodhisattva", "personal", "the pilgrim youth of the Gaṇḍavyūha"),
            ("Mañjuśrī", "mañjuśrī", [sk("mañjuśr", "mañjuśir")], BUD["manjushri"], None, "bodhisattva", "personal", ""),
            ("Samantabhadra", "samantabhadra", [sk("samantabhadr")], BUD["samantabhadra"], None, "bodhisattva", "personal", ""),
            ("Maitreya", "maitreya", [sk("maitrey")], BUD["maitreya"], None, "bodhisattva", "personal", ""),
            ("Avalokiteśvara", "avalokiteśvara", [sk("avalokiteśvar")], BUD["avalokiteshvara"], None, "bodhisattva", "personal", ""),
            ("Śāriputra", "śāriputra", [sk("śāriputr")], BUD["sariputta"], None, "disciple", "personal", "Sanskrit form of Pali Sāriputta"),
            ("Vairocana", "vairocana", [sk("vairocan(?!ottara)")], None, ("Vairocana", r"Buddha"), "sage", "personal", ""),
        ]),
        ("sa_dazabhUmikasUtra", "Dasabhumika Sutra", "Daśabhūmikasūtra, ed. P.L. Vaidya 1967", ch_dbh, [
            ("Vajragarbha", "vajragarbha", [sk("vajragarbh")], None, ("Vajragarbha", r"bodhisattva"), "bodhisattva", "personal", ""),
            ("Vimukticandra", "vimukticandra", [sk("vimukticandr")], None, ("Vimukticandra", r"bodhisattva"), "bodhisattva", "personal", ""),
        ]),
        ("sa_saddharmalaGkAvatArasUtra", "Lankavatara Sutra", "Saddharmalaṅkāvatārasūtra, ed. P.L. Vaidya 1963", ch_lank, [
            ("Mahāmati", "mahāmati", [sk("mahāmat")], None, ("Mahamati", r"bodhisattva"), "bodhisattva", "personal", ""),
            ("Rāvaṇa", "rāvaṇa", [sk("rāvaṇ")], BUD["ravana"], None, "royal", "personal", "Rāvaṇa, lord of Laṅkā, who requests the teaching"),
        ]),
        ("sa_zAntideva-bodhicaryAvatAra", "Bodhicaryavatara", "Śāntideva, Bodhicaryāvatāra", ch_verses("Bca", "Bodhicaryāvatāra"), [
            ("Mañjuśrī", "mañjuśrī", [sk("mañjuśr", "mañjughoṣ", "mañjunāth")], BUD["manjushri"], None, "bodhisattva", "personal", ""),
            ("Samantabhadra", "samantabhadra", [sk("samantabhadr")], BUD["samantabhadra"], None, "bodhisattva", "personal", ""),
            ("Avalokita", "avalokita", [sk("avalokit"), r"(?<=ary)āvalokit"], BUD["avalokiteshvara"], None, "bodhisattva", "epithet", "short form of Avalokiteśvara"),
            ("Ākāśagarbha", "ākāśagarbha", [sk("ākāśagarbh")], None, ("Akasagarbha", r"bodhisattva"), "bodhisattva", "personal", ""),
            ("Kṣitigarbha", "kṣitigarbha", [sk("kṣitigarbh")], None, ("Ksitigarbha", r"bodhisattva"), "bodhisattva", "personal", ""),
            ("Śrīsaṃbhava", "śrīsaṃbhava", [sk("śrīsaṃbhav")], None, None, "human", "personal", "the merchant's son of the Gaṇḍavyūha, cited by Śāntideva"),
            ("Maitreya", "maitreya", [sk("maitrey")], BUD["maitreya"], None, "bodhisattva", "personal", ""),
        ]),
        ("sa_tArAbhaTTArikAnAmASTottarazatakastotra", "Tara Namashtottarashataka", "Āryatārābhaṭṭārikānāmāṣṭottaraśatakastotra, ed. G. de Blonay 1895",
         ch_verses("tbh", "Tārānāmāṣṭottaraśataka v."), [
            ("Tārā", "tārā", [sk("tār(?:ā|e|āṃ|āyai|āyāḥ|ayā)(?![{SL}])".replace("{SL}", SL))], None, ("Tara", r"bodhisattva|Buddhis|deity|goddess"), "bodhisattva", "personal", ""),
            ("Avalokiteśvara", "avalokiteśvara", [sk("avalokiteśvar", "lokeśvar")], BUD["avalokiteshvara"], None, "bodhisattva", "personal", ""),
        ]),
    ]
    for fidfile, corpus, edition, chf, flist in texts:
        segs = gretil_segs(fidfile, corpus, chf)
        figs = []
        for nm, iast, pats, fid, wdq, et, role, rel in flist:
            figs.append(Fig(latin_skt(nm), nm.split(",")[0] if fid is None else "", et, role, nm, deva(iast), pats, fid=fid, wd=wdq, rel=rel,
                            conf=0.9, key=re.sub(r"[^a-z]", "", fold(nm).lower()), lang="Sanskrit"))
        for f in figs:
            if not f.figure: f.figure = FIG_LABEL.get(f.fid, f.translit)
            elif f.figure == f.translit and f.et == "bodhisattva": f.figure = f"{f.translit}, bodhisattva"
        if fidfile == "sa_gaNDavyUhasUtra":
            figs += gandavyuha_figs(segs)
        base = dict(language="Sanskrit", subtradition="Mahayana", corpus=corpus, source=f"GRETIL, {edition} (CC BY-NC-SA 4.0)")
        r, rv = build(figs, segs, base, "Buddhist", wd_tag="bud", stats=stats); rows += r; review += rv
    # ---- Chinese canon (CBETA): Platform Sutra, Srimaladevi, Surangama, Mahayana Mahaparinirvana
    r, rv = platform_sutra(stats); rows += r; review += rv
    r, rv = cbeta_extra(stats); rows += r; review += rv
    # ---- Tibetan: Bardo Thodol, Milarepa (Evans-Wentz, OCR)
    r, rv = tibetan(stats); rows += r; review += rv
    return rows, review

FIG_LABEL = {BUD["subhuti"]: "Subhūti, disciple", BUD["sariputta"]: "Sāriputta, chief disciple", BUD["sakka"]: "Sakka, king of the devas",
             BUD["maitreya"]: "Maitreya, the future Buddha", BUD["purna"]: "Puṇṇa Mantāniputta, disciple", BUD["ananda"]: "Ānanda, the Buddha's attendant",
             BUD["akshobhya"]: "Akṣobhya Buddha", BUD["dipankara"]: "Dīpaṅkara, Buddha of the past", BUD["manjushri"]: "Mañjuśrī, bodhisattva",
             BUD["samantabhadra"]: "Samantabhadra, bodhisattva", BUD["avalokiteshvara"]: "Avalokiteśvara, bodhisattva", BUD["ravana"]: "Rāvaṇa, King of Lankā",
             BUD["maya"]: "Māyā, the Buddha's mother", BUD["yasodhara"]: "Yasodharā (Rāhulamātā), the Buddha's wife"}

GV_DEITY = set(range(32, 43)) | {45}
GV_BODHI = {30, 31}
def gandavyuha_figs(segs):
    """The kalyanamitras Sudhana visits: one chapter each (heading = the teacher's name). Counted inside their own chapter."""
    out = []
    for c, head in sorted(GV_HEADS.items()):
        if c in (1, 2, 3, 30, 54, 55, 56) or head.endswith("parivartaḥ") or "caryā" in head: continue
        nom = head.rstrip("ḥ")
        stem = re.sub(r"(a|ā|ī|i|vān)$", "", nom) if len(nom) > 5 else nom
        disp = nom
        et = "deity" if c in GV_DEITY else ("bodhisattva" if c in GV_BODHI else "human")
        fid = {43: BUD["yasodhara"], 44: BUD["maya"]}.get(c)
        rel = {43: "Gopā, name of the Buddha's wife (Pali Yasodharā) in Mahāyāna texts", 44: "the Buddha's mother"}.get(c, f"kalyāṇamitra of Sudhana (ch. {c})")
        word_like = nom in ("āśā", "megha", "vidvān", "prabhūtā", "anala", "vaira", "māyā", "acalā", "mahādeva", "sthāvarā", "vāsantī", "sucandra")
        out.append(Fig(latin_skt(disp), f"{disp[:1].upper() + disp[1:]}, teacher of Sudhana (Gaṇḍavyūha ch. {c})" if not fid else FIG_LABEL[fid],
                       et, "personal", disp, deva(disp), [rf"(?<![{SL}]){re.escape(stem)}[{SL}]*"], fid=fid, rel=rel, conf=0.8,
                       scope=(lambda s, c=c: s.passage == f"Gaṇḍavyūha ch. {c}"), review=word_like or len(disp) > 20,
                       key=f"gv{c}-" + re.sub(r"[^a-z]", "", fold(disp)), lang="Sanskrit"))
    return out

def cbeta_segs(vol, no, label):
    fn = f"T{vol}n{no}"
    p = get(f"https://raw.githubusercontent.com/cbeta-org/xml-p5/master/T/T{vol}/{fn}.xml", os.path.join(RAW, "cbeta", fn + ".xml"))
    x = open(p, encoding="utf-8").read()
    x = x[x.find("<body"):]
    x = re.sub(r"<note[^>]*>.*?</note>", "", x, flags=re.S)
    segs, cur, chapter, juan = [], None, "", 1
    for part in re.split(r'(<lb n="[0-9a-z]+"[^>]*/>)', x):
        m = re.match(r'<lb n="([0-9a-z]+)"', part)
        if m: cur = m.group(1); continue
        mm = re.search(r'<cb:mulu level="1"[^>]*>([^<]+)</cb:mulu>', part)
        if mm: chapter = mm.group(1)
        mj = re.search(r'<milestone n="(\d+)" unit="juan"', part)
        if mj: juan = int(mj.group(1))
        t = re.sub(r"<[^>]+>", "", part).strip()
        if t and cur:
            segs.append(Seg(chapter, f"T{vol} no. {int(no)}, p. {int(cur[:4])}{cur[4]}{int(cur[5:])}" + (f" (fasc. {juan})" if label == "juan" else ""),
                            f"https://cbetaonline.dila.edu.tw/zh/{fn}_p{cur}", t))
    return segs

SRC_CBETA = "{}, CBETA XML P5 (Taishō text; non-commercial use with header)"
# Chinese renderings of Indian figures in the Chinese canon: (pinyin name, tones, hanzi forms, figure id or Wikidata spec, label, entity_type, Sanskrit name)
CB_IND = {
    "ananda": ("Anan", "Ānán", ["阿難"], BUD["ananda"], "Ānanda, the Buddha's attendant", "disciple", "Ānanda"),
    "shariputra": ("Shelifu", "Shèlìfú", ["舍利弗"], BUD["sariputta"], "Sāriputta, chief disciple", "disciple", "Śāriputra"),
    "maudgalyayana": ("Mujianlian", "Mùjiànlián", ["目犍連", "目連"], BUD["moggallana"], "Mahāmoggallāna, chief disciple", "disciple", "Maudgalyāyana"),
    "manjushri": ("Wenshushili", "Wénshūshīlì", ["文殊師利", "文殊"], BUD["manjushri"], "Mañjuśrī, bodhisattva", "bodhisattva", "Mañjuśrī"),
    "guanyin": ("Guanshiyin", "Guānshìyīn", ["觀世音"], BUD["avalokiteshvara"], "Avalokiteśvara, bodhisattva", "bodhisattva", "Avalokiteśvara"),
    "puxian": ("Puxian", "Pǔxián", ["普賢"], BUD["samantabhadra"], "Samantabhadra, bodhisattva", "bodhisattva", "Samantabhadra"),
    "mile": ("Mile", "Mílè", ["彌勒"], BUD["maitreya"], "Maitreya, the future Buddha", "bodhisattva", "Maitreya"),
    "dashizhi": ("Dashizhi", "Dàshìzhì", ["大勢至"], ("Mahasthamaprapta", r"bodhisattva"), "Mahāsthāmaprāpta, bodhisattva", "bodhisattva", "Mahāsthāmaprāpta"),
    "fulouna": ("Fulouna", "Fùlóunà", ["富樓那"], BUD["purna"], "Puṇṇa Mantāniputta, disciple", "disciple", "Pūrṇa"),
    "kauṇḍinya": ("Jiaochenna", "Jiāochénnà", ["憍陳那", "憍陳如"], "Q2708070", "Aññāsi Koṇḍañña, first disciple", "disciple", "Kauṇḍinya"),
    "subhuti": ("Xuputi", "Xūpútí", ["須菩提"], BUD["subhuti"], "Subhūti, disciple", "disciple", "Subhūti"),
    "upali": ("Youboli", "Yōubōlí", ["優波離"], "Q984630", "Upāli, disciple", "disciple", "Upāli"),
    "aniruddha": ("Analütuo", "Ānàlǜtuó", ["阿那律陀", "阿那律"], "Q3306373", "Anuruddha, disciple", "disciple", "Aniruddha"),
    "mahakashyapa": ("Mohe Jiashe", "Móhē Jiāshè", ["摩訶迦葉"], BUD["mahakassapa"], "Mahākassapa, disciple", "disciple", "Mahākāśyapa"),
    "rahula": ("Luohouluo", "Luóhóuluó", ["羅睺羅"], BUD["rahula"], "Rāhula, the Buddha's son", "disciple", "Rāhula"),
    "yashodhara": ("Yeshutuoluo", "Yēshūtuóluó", ["耶輸陀羅"], BUD["yasodhara"], "Yasodharā (Rāhulamātā), the Buddha's wife", "human", "Yaśodharā"),
    "matangi": ("Modengqie", "Módēngqié", ["摩登伽"], ("Matangi Surangama", r"Buddhis|woman|Ananda"), "Mātaṅgī (Prakṛti), the woman who enchanted Ānanda", "human", "Mātaṅgī"),
    "prakriti": ("Xing Biqiuni", "Xìng Bǐqiūní", ["性比丘尼"], None, "Prakṛti, the nun (formerly Mātaṅgī's daughter)", "disciple", "Prakṛti"),
    "prasenajit": ("Bosini", "Bōsīnì", ["波斯匿"], BUD["pasenadi"], "Pasenadi, king of Kosala", "royal", "Prasenajit"),
    "mallika": ("Moli", "Mòlì", ["末利夫人", "末利"], None, "Mallikā, queen of Kosala", "royal", "Mallikā"),
    "srimala": ("Shengman", "Shèngmán", ["勝鬘"], ("Srimala", r"queen|Buddhis|sutra"), "Śrīmālā, queen of Ayodhyā", "royal", "Śrīmālā"),
    "yashomitra": ("Youcheng", "Yǒuchēng", ["友稱"], None, "Yaśomitra, king of Ayodhyā, husband of Śrīmālā", "royal", "Yaśomitra"),
    "sakra": ("Dishi", "Dìshì", ["帝釋"], BUD["sakka"], "Sakka, king of the devas", "deity", "Śakra"),
    "cunda": ("Chuntuo", "Chúntuó", ["純陀"], ("Cunda", r"smith|Buddha|meal"), "Cunda, the smith who gave the last meal", "human", "Cunda"),
    "kashyapa_bodhi": ("Jiashe Pusa", "Jiāshè Púsà", ["迦葉菩薩"], None, "Kāśyapa, bodhisattva of the Mahāparinirvāṇa sūtra", "bodhisattva", "Kāśyapa"),
    "subhadra": ("Xubatuo", "Xūbátuó", ["須跋陀"], ("Subhadda", r"disciple|Buddha|monk"), "Subhadra, the last disciple", "disciple", "Subhadra"),
    "ajatashatru": ("Asheshi", "Āshéshì", ["阿闍世"], BUD["ajatasattu"], "Ajātasattu, king of Magadha", "royal", "Ajātaśatru"),
    "jivaka": ("Qipo", "Qípó", ["耆婆"], ("Jivaka", r"physician|doctor"), "Jīvaka, the physician", "human", "Jīvaka"),
    "devadatta": ("Tipodaduo", "Típódáduō", ["提婆達多"], BUD["devadatta"], "Devadatta, the Buddha's cousin", "disciple", "Devadatta"),
    "sunakshatra": ("Shanxing", "Shànxīng", ["善星"], None, "Sunakṣatra, the monk who lost faith", "disciple", "Sunakṣatra"),
    "shizihou": ("Shizihou", "Shīzǐhǒu", ["師子吼菩薩"], None, "Siṃhanāda, bodhisattva of the Mahāparinirvāṇa sūtra", "bodhisattva", "Siṃhanāda"),
    "maya": ("Moye", "Móyē", ["摩耶"], BUD["maya"], "Māyā, the Buddha's mother", "human", "Māyā"),
    "yuexi": ("Yueguang", "Yuèguāng", ["月光童子"], None, "Candraprabha, the youth Moonlight", "bodhisattva", "Candraprabha"),
}

def cbeta_extra(stats):
    rows, review = [], []
    texts = [("12", "0353", "Srimaladevi Sutra", "Śrīmālādevī Siṃhanāda sūtra (T353, tr. Guṇabhadra)",
              ["srimala", "yashomitra", "prasenajit", "mallika", "sakra", "ananda"]),
             ("19", "0945", "Surangama Sutra", "Śūraṅgama sūtra (T945)",
              ["ananda", "matangi", "prakriti", "prasenajit", "manjushri", "guanyin", "puxian", "mile", "dashizhi", "fulouna", "kauṇḍinya",
               "shariputra", "maudgalyayana", "subhuti", "upali", "aniruddha", "mahakashyapa", "rahula", "yashodhara", "yuexi"]),
             ("12", "0374", "Mahayana Mahaparinirvana Sutra", "Mahāyāna Mahāparinirvāṇa sūtra (T374, tr. Dharmakṣema)",
              ["cunda", "kashyapa_bodhi", "manjushri", "ananda", "subhadra", "ajatashatru", "jivaka", "kauṇḍinya", "devadatta", "sunakshatra",
               "shizihou", "maya", "shariputra", "maudgalyayana", "rahula", "mahakashyapa"])]
    for vol, no, corpus, title, keys in texts:
        segs = cbeta_segs(vol, no, "juan" if no == "0374" else "")
        figs = []
        for k in keys:
            nm, tr, forms, link, lab, et, skt = CB_IND[k]
            fid, wdq = (link, None) if isinstance(link, str) else (None, link)
            figs.append(Fig(nm, lab, et, "personal", tr, forms[0], [re.escape(f) for f in forms], fid=fid, wd=wdq, conf=0.85,
                            key="cb-" + re.sub(r"[^a-z]", "", fold(k)), rel=f"Chinese rendering of Sanskrit {skt}", lang="Chinese",
                            review=k in ("mile", "maya", "shizihou", "mallika", "yashomitra")))
        base = dict(language="Chinese", subtradition="Mahayana", corpus=corpus, source=SRC_CBETA.format(title))
        r, rv = build(figs, segs, base, "Buddhist", wd_tag="bud", stats=stats); rows += r; review += rv
    return rows, review

def platform_sutra(stats):
    segs = cbeta_segs("48", "2008", "")
    P = [("Huineng", "Huìnéng", ["惠能", "慧能"], ("Huineng", r"Chan|Zen|patriarch|monk"), "Huineng, Sixth Patriarch of Chan"),
         ("Hongren", "Hóngrěn", ["弘忍"], ("Daman Hongren", r"Chan|Zen|patriarch|monk"), "Hongren, Fifth Patriarch of Chan"),
         ("Shenxiu", "Shénxiù", ["神秀"], ("Yuquan Shenxiu", r"Chan|Zen|monk"), "Shenxiu, Chan master"),
         ("Bodhidharma", "Dámó", ["達磨", "達摩"], ("Bodhidharma", r"monk|Chan|Zen|patriarch"), "Bodhidharma, first Chan patriarch"),
         ("Fahai", "Fǎhǎi", ["法海"], None, "Fahai, disciple of Huineng and compiler of the sutra"),
         ("Huiming", "Huìmíng", ["惠明"], None, "Huiming, monk who pursued Huineng"),
         ("Fada", "Fǎdá", ["法達"], None, "Fada, disciple of Huineng"),
         ("Zhitong", "Zhìtōng", ["智通"], None, "Zhitong, disciple of Huineng"),
         ("Zhidao", "Zhìdào", ["志道"], None, "Zhidao, disciple of Huineng"),
         ("Xingsi", "Xíngsī", ["行思"], ("Qingyuan Xingsi", r"Chan|Zen|monk"), "Qingyuan Xingsi, disciple of Huineng"),
         ("Huairang", "Huáiràng", ["懷讓"], ("Nanyue Huairang", r"Chan|Zen|monk"), "Nanyue Huairang, disciple of Huineng"),
         ("Xuanjue", "Xuánjué", ["玄覺"], ("Yongjia Xuanjue", r"Chan|Zen|monk"), "Yongjia Xuanjue, disciple of Huineng"),
         ("Zhihuang", "Zhìhuáng", ["智隍"], None, "Zhihuang, meditator converted by Huineng"),
         ("Zhicheng", "Zhìchéng", ["志誠"], None, "Zhicheng, disciple sent by Shenxiu"),
         ("Shenhui", "Shénhuì", ["神會"], ("Heze Shenhui", r"Chan|Zen|monk"), "Heze Shenhui, disciple of Huineng"),
         ("Yinzong", "Yìnzōng", ["印宗"], None, "Yinzong, dharma master who ordained Huineng"),
         ("Wei Qu", "Wéi Qú", ["韋璩", "韋刺史"], None, "Wei Qu, prefect of Shaozhou"),
         ("Xue Jian", "Xuē Jiǎn", ["薛簡"], None, "Xue Jian, imperial envoy")]
    figs = [Fig(n, lab, "sage" if n not in ("Wei Qu", "Xue Jian") else "human", "personal", tr, forms[0], forms, wd=wdq, conf=0.9,
                key="chan-" + n.lower().replace(" ", ""), lang="Chinese") for n, tr, forms, wdq, lab in P]
    for f in figs:   # the prefaces (序, 贊) use 神會 as a word ("spiritual comprehension")
        if f.name == "Shenhui": f.scope = lambda s: "序" not in s.text and "贊" not in s.text
    base = dict(language="Chinese", subtradition="Chan", corpus="Platform Sutra",
                source="Liuzu Dashi Fabao Tanjing (T2008, Zongbao ed.), CBETA XML P5 (non-commercial use with header)")
    return build(figs, segs, base, "Buddhist", wd_tag="bud", stats=stats)

def tibetan(stats):
    rows, review = [], []
    pb = ia_text("the-tibetan-book-of-the-dead_202401", "the tibetan book of the dead_djvu.txt", os.path.join(RAW, "tibetan", "bardo.txt")) \
         or os.path.join(RAW, "tibetan", "bardo.txt")
    L = ocr_lines(pb)
    a = next(i for i, l in enumerate(L) if i > 4000 and re.match(r"\s*BOOK [I1l]\]", l)) - 150
    b = next((i for i, l in enumerate(L) if i > a and re.match(r"\s*(ADDENDA|INDEX)\.?\s*$", l)), len(L))
    def h_b(l, st):
        m = re.match(r"\s*(?:BOOK|PART) [I1l]+\s?[\]}].*?(\d{2,3})\s*$", l)
        if m: st["p"] = m.group(1)
    bs = ocr_segs(L, a, b, lambda st: ("Bardo Thödol", "Bardo Thödol, Evans-Wentz ed." + (f" p. {st['p']}" if st.get("p") else "")),
                  "https://archive.org/details/the-tibetan-book-of-the-dead_202401", h_b)
    BT = [("Padmasambhava", "Padma Sambhava", [W(r"Padma[- ]?Sambhava")], ("Padmasambhava", r"Buddhist|guru|Tibet|master"), "sage", "personal", "Padmasambhava, Guru Rinpoche"),
          ("Chenrezig", "Chenrazee", [W(r"Chenrazee")], BUD["avalokiteshvara"], "bodhisattva", "personal", "Avalokiteśvara, bodhisattva"),
          ("Avalokiteshvara", "Avalokiteshvara", [W(r"Avalokiteshvara")], BUD["avalokiteshvara"], "bodhisattva", "personal", "Avalokiteśvara, bodhisattva"),
          ("Vairochana", "Vairochana", [W(r"Vairochana")], ("Vairocana", r"Buddha"), "sage", "personal", "Vairocana Buddha"),
          ("Vajrasattva", "Vajra-Sattva", [W(r"Vajra-?Sattva")], ("Vajrasattva", r"bodhisattva|Buddha|deity"), "bodhisattva", "personal", "Vajrasattva"),
          ("Ratnasambhava", "Ratna-Sambhava", [W(r"Ratna-?Sambhava")], ("Ratnasambhava", r"Buddha"), "sage", "personal", "Ratnasambhava Buddha"),
          ("Amoghasiddhi", "Amogha-Siddhi", [W(r"Amogha-?Siddhi")], ("Amoghasiddhi", r"Buddha"), "sage", "personal", "Amoghasiddhi Buddha"),
          ("Amitabha", "Amitabha", [W(r"Amitabha")], BUD["amitabha"], "sage", "personal", "Amitābha Buddha"),
          ("Akshobhya", "Akshobhya", [W(r"Akshobhya")], BUD["akshobhya"], "sage", "personal", "Akṣobhya Buddha"),
          ("Samantabhadra", "Samanta-Bhadra", [W(r"Samanta-?Bhadra")], BUD["samantabhadra"], "bodhisattva", "personal", "Samantabhadra"),
          ("Mamaki", "Mamaki", [W(r"Mamaki")], None, "deity", "personal", "Māmakī, consort of Vajrasattva"),
          ("Tara", "Tara", [W(r"Tara")], ("Tara", r"bodhisattva|Buddhis|goddess"), "bodhisattva", "personal", "Tārā"),
          ("Hayagriva", "Hayagriva", [W(r"Hayagriva")], ("Hayagriva", r"deity|Buddhis|wrathful"), "deity", "personal", "Hayagrīva"),
          ("Yama", "Yama", [W(r"Yama(?:-Raja)?")], None, "deity", "personal", "Yama, Lord of Death"),
          ("Vajrapani", "Vajra-Pani", [W(r"Vajra-?Pani")], ("Vajrapani", r"bodhisattva"), "bodhisattva", "personal", "Vajrapāṇi")]
    figs = []
    for n, tr, pats, link, et, role, lab in BT:
        fid, wdq = (link, None) if isinstance(link, str) else (None, link)
        figs.append(Fig(n, lab, et, role, tr, "", pats, fid=fid, wd=wdq, conf=0.8, key="bardo-" + n.lower(), lang="Tibetan",
                        rel="Tibetan name of Avalokiteśvara" if n == "Chenrezig" else "", review=n in ("Tara", "Yama")))
    for f in figs:
        if f.name == "Chenrezig": f.translit = "Chenrazee (Spyan-ras-gzigs)"
    base = dict(language="Tibetan", subtradition="Vajrayana", corpus="Bardo Thodol",
                source="Bardo Thödol, tr. Kazi Dawa-Samdup, ed. W.Y. Evans-Wentz (1927, US public domain), archive.org OCR")
    r, rv = build(figs, bs, base, "Buddhist", flags=re.I, wd_tag="bud", stats=stats); rows += r; review += rv
    pm = ia_text("tibetsgreatyogim0000wyev", "tibetsgreatyogim0000wyev_djvu.txt", os.path.join(RAW, "tibetan", "milarepa.txt")) \
         or os.path.join(RAW, "tibetan", "milarepa.txt")
    L = ocr_lines(pm)
    a = next(i for i, l in enumerate(L) if re.match(r"\s*PART I: THE PATH OF DARKNESS", l))
    b = next((i for i, l in enumerate(L) if i > a and re.match(r"\s*INDEX\.?\s*$", l)), len(L))
    def h_m(l, st):
        m = re.match(r"\s*CHAPTER ([IVXL]+)\s*$", l)
        if m and roman(m.group(1)): st["c"] = roman(m.group(1))
    ms = ocr_segs(L, a, b, lambda st: (f"Chapter {st.get('c', 1)}", f"Jetsün Kahbum, Evans-Wentz ed., ch. {st.get('c', 1)}"),
                  "https://archive.org/details/tibetsgreatyogim0000wyev", h_m)
    MI = [("Milarepa", "Milarepa", [W(r"Milarepa", r"Mila[- ]Repa")], ("Milarepa", r"yogi|Tibet|poet|Buddhis"), "saint", "personal", "Milarepa, Tibetan yogi"),
          ("Marpa", "Marpa", [W(r"Marpa")], ("Marpa Lotsawa", r"translator|Tibet|Buddhis|teacher"), "saint", "personal", "Marpa the Translator, Milarepa's guru"),
          ("Damema", "Damema", [W(r"Damema")], ("Dagmema", r"Marpa|wife|yogini"), "human", "personal", "Damema, wife of Marpa"),
          ("Rechungpa", "Rechung", [W(r"Rechung(?:pa)?")], ("Rechungpa", r"disciple|Milarepa|yogi"), "disciple", "personal", "Rechungpa, disciple of Milarepa"),
          ("Gampopa", "Gampopa", [W(r"Gampopa")], ("Gampopa", r"Tibet|teacher|Kagyu|Buddhis"), "disciple", "personal", "Gampopa, disciple of Milarepa"),
          ("Naropa", "Naropa", [W(r"Naropa")], ("Naropa", r"Buddhis|mahasiddha|scholar|yogi"), "saint", "personal", "Naropa, Indian master"),
          ("Tilopa", "Tilopa", [W(r"Tilopa")], ("Tilopa", r"Buddhis|mahasiddha|yogi"), "saint", "personal", "Tilopa, Indian master"),
          ("Peta", "Peta", [W(r"Peta")], None, "human", "personal", "Peta, Milarepa's sister"),
          ("Zesay", "Zesay", [W(r"Zesay")], None, "human", "personal", "Zesay, Milarepa's betrothed"),
          ("Ngogpa", "Ngogpa", [W(r"Ngogpa", r"Ngogdun(?:-Chudor)?")], None, "saint", "personal", "Ngogdun Chudor, disciple of Marpa"),
          ("Mila Sherab Gyaltsen", "Mila-Sherab-Gyaltsen", [W(r"Mila-Sherab-Gyaltsen")], None, "human", "personal", "Mila-Sherab-Gyaltsen, Milarepa's father"),
          ("Atisha", "Atisha", [W(r"Atisha")], ("Atisa", r"Buddhis|teacher|Bengal|monk"), "saint", "personal", "Atiśa Dīpaṃkara"),
          ("Padmasambhava", "Padma Sambhava", [W(r"Padma[- ]?Sambhava")], ("Padmasambhava", r"Buddhist|guru|Tibet|master"), "sage", "personal", "Padmasambhava, Guru Rinpoche"),
          ("Tseringma", "Tseringma", [W(r"Tseringma")], None, "deity", "personal", "Tseringma, mountain goddess")]
    figs = []
    for n, tr, pats, link, et, role, lab in MI:
        fid, wdq = (link, None) if isinstance(link, str) else (None, link)
        figs.append(Fig(n, lab, et, role, tr, "", pats, fid=fid, wd=wdq, conf=0.8, key="mila-" + n.lower().replace(" ", ""), lang="Tibetan",
                        review=n in ("Peta",)))
    for f in figs:
        if f.name == "Padmasambhava": f.key = "bardo-padmasambhava"
    base = dict(language="Tibetan", subtradition="Vajrayana", corpus="Life of Milarepa",
                source="Jetsün Kahbum (Life of Milarepa), tr. Kazi Dawa-Samdup, ed. W.Y. Evans-Wentz (1928, US public domain; scan of the 2nd ed.), archive.org OCR")
    r, rv = build(figs, ms, base, "Buddhist", flags=re.I, wd_tag="bud", stats=stats); rows += r; review += rv
    return rows, review



# ───────────────────────────────────────────────────────────── Wikisource (Chinese classics, Kojiki, Nihon Shoki)
WS = os.path.join(RAW, "wikisource")
WS_SETS = [("zh", p) for p in ["論語/", "孟子/", "莊子/", "列子/", "尚書/", "詩經/", "周易/", "禮記/", "山海經/", "日本書紀/卷第", "古事記/"]]
WS_PAGES = [("zh", t) for t in ["道德經 (王弼本)", "今文孝經", "太上感應篇", "禮記/大學", "禮記/中庸",
                                 # the index pages give the canonical order of the chapters
                                 "論語", "孟子", "莊子", "列子", "尚書", "詩經", "周易", "禮記", "山海經", "日本書紀", "古事記"]]

def ws_get(url):
    for a in range(8):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode("utf-8")
        except Exception as e:
            print(f"  retry {e}", file=sys.stderr); time.sleep(min(120, 10 * 2 ** a))
    return ""

def ws_fetch():
    os.makedirs(WS, exist_ok=True)
    titles = []
    for host, pre in WS_SETS:
        cp = os.path.join(WS, f"{host}_list_{pre.replace('/', '_')}.json")
        if not os.path.exists(cp) and not OFFLINE:
            out, cont = [], {}
            while True:
                q = dict(action="query", list="allpages", apprefix=pre, aplimit="500", format="json", **cont)
                j = json.loads(ws_get(f"https://{host}.wikisource.org/w/api.php?" + urllib.parse.urlencode(q)) or "{}"); time.sleep(3)
                out += [x["title"] for x in j.get("query", {}).get("allpages", [])]
                if "continue" not in j: break
                cont = {"apcontinue": j["continue"]["apcontinue"]}
            json.dump(out, open(cp, "w"), ensure_ascii=False)
        if os.path.exists(cp):
            titles += [(host, t) for t in json.load(open(cp)) if t.count("/") == 1 and " (" not in t and "全覽" not in t and "（" not in t]
    titles += WS_PAGES
    for host, t in titles:
        p = os.path.join(WS, host, t.replace("/", "__") + ".wiki")
        if (not os.path.exists(p) or not os.path.getsize(p)) and not OFFLINE:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w", encoding="utf-8").write(ws_get(f"https://{host}.wikisource.org/w/index.php?" + urllib.parse.urlencode(dict(title=t, action="raw"))))
            time.sleep(2.5)
    return titles

WS_DROP = {"header", "header2", "textquality", "*", "注", "註", "小註", "small", "smaller", "sup", "!"}   # {{*|…}} = inline commentary
def wikitext_clean(t):
    if "<onlyinclude>" in t:
        t = "\n".join(re.findall(r"<onlyinclude>(.*?)(?:</onlyinclude>|$)", t, re.S))
    t = re.sub(r"<ref[^>/]*/>|<ref[^>]*>.*?</ref>", "", t, flags=re.S)
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
    t = re.sub(r"-\{(?:[^{}|]*\|)?([^{}]*)\}-", r"\1", t)
    for _ in range(8):
        n = re.sub(r"\{\{([^{}|]*)\|([^{}|]*)(?:\|[^{}]*)?\}\}",
                   lambda m: m.group(2) if len(m.group(1).strip()) <= 12 and m.group(1).strip().lower() not in WS_DROP else "", t)
        n = re.sub(r"\{\{[^{}]*\}\}", "", n)
        if n == t: break
        t = n
    t = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"<[^>]+>|'{2,3}", "", t)
    return t

CN_NUM = {c: i for i, c in enumerate("〇一二三四五六七八九", 0)}
def cn_int(s):
    if not s: return None
    if s.isdigit(): return int(s)
    v, cur = 0, 0
    for c in s:
        if c == "十": v += (cur or 1) * 10; cur = 0
        elif c == "百": v += (cur or 1) * 100; cur = 0
        elif c in CN_NUM: cur = CN_NUM[c]
        else: return None
    return v + cur

def ws_segs(host, prefix_or_title, book, single=False):
    segs = []
    files = [os.path.join(WS, host, prefix_or_title.replace("/", "__") + ".wiki")] if single else \
            sorted(glob.glob(os.path.join(WS, host, glob.escape(prefix_or_title.replace("/", "__")) + "*.wiki")))
    parent = os.path.join(WS, host, prefix_or_title.split("/")[0] + ".wiki")
    ptxt = open(parent, encoding="utf-8").read() if os.path.exists(parent) and not single else ""
    def order(p):
        sect = os.path.basename(p)[:-5].split("__", 1)[-1]
        m = re.search(r"第([一二三四五六七八九十百]+)$", sect)
        if m: return (0, cn_int(m.group(1)), "")
        i = ptxt.find("/" + sect + "|"); i = ptxt.find("/" + sect) if i < 0 else i; i = ptxt.find(sect) if i < 0 else i
        return (1, i if i >= 0 else 10 ** 9, sect)
    files.sort(key=order)
    for p in files:
        if not os.path.exists(p): continue
        title = os.path.basename(p)[:-5].replace("__", "/")
        if "/" in title and not single and ("序" in title.split("/")[1] or "目錄" in title): continue
        sect = title.split("/", 1)[1] if "/" in title else ""
        url = f"https://{host}.wikisource.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))
        num = None
        raw = open(p, encoding="utf-8").read()
        for line in wikitext_clean(raw).split("\n"):
            m = re.match(r"\s*=+\s*([0-9]+|[〇一二三四五六七八九十百]+)\s*=+\s*$", line) or \
                re.match(r"\s*([一二三四五六七八九十百]+)之([一二三四五六七八九十百]+)\s*$", line)
            if m:
                num = cn_int(m.group(m.lastindex)); continue
            line = line.strip(" 　:*#=")
            if len(line) < 2 or "‧" in line or "毛詩序" in line or re.match(r"《[^》]{1,8}》，", line): continue   # Mao prefaces to the Odes
            m = re.search(r"第([一二三四五六七八九十百]+)$", sect)
            if m and sect.startswith("卷第"):   # Nihon Shoki, vol. 3
                psg = f"{book}, vol. {cn_int(m.group(1))}"
            elif m:   # Analects 11.5 (先進)
                psg = f"{book} {cn_int(m.group(1))}" + (f".{num}" if num else "") + f" ({re.sub(r'第.*$', '', sect)})"
            else:
                psg = f"{book}" + (f", {sect}" if sect else "") + (f" {num}" if num else "")
            segs.append(Seg(sect, psg, url, line))
    return segs

# key: (pinyin name, pinyin with tones, label, entity_type, Wikidata search, description regex)
CN = {
    "confucius": ("Kongzi", "Kǒngzǐ", "Confucius", "sage", "Confucius", r"philosopher"),
    "zhongni": ("Zhongni", "Zhòngní", "Confucius", "sage", None, None),
    "yanhui": ("Yan Hui", "Yán Huí", "Yan Hui, disciple of Confucius", "disciple", "Yan Hui", r"disciple|Confuci"),
    "yanyuan": ("Yan Yuan", "Yán Yuān", "Yan Hui, disciple of Confucius", "disciple", None, None),
    "zilu": ("Zilu", "Zǐlù", "Zilu (Zhong You), disciple of Confucius", "disciple", "Zilu", r"disciple|Confuci"),
    "zhongyou": ("Zhong You", "Zhòng Yóu", "Zilu (Zhong You), disciple of Confucius", "disciple", None, None),
    "zigong": ("Zigong", "Zǐgòng", "Zigong (Duanmu Ci), disciple of Confucius", "disciple", "Zigong", r"disciple|Confuci|merchant|diplomat"),
    "zengzi": ("Zengzi", "Zēngzǐ", "Zengzi (Zeng Shen), disciple of Confucius", "disciple", "Zengzi", r"philosopher|disciple|Confuci"),
    "zixia": ("Zixia", "Zǐxià", "Zixia (Bu Shang), disciple of Confucius", "disciple", "Zixia", r"disciple|Confuci|philosopher"),
    "ziyou": ("Ziyou", "Zǐyóu", "Ziyou (Yan Yan), disciple of Confucius", "disciple", "Yan Yan", r"disciple|Confuci"),
    "zizhang": ("Zizhang", "Zǐzhāng", "Zizhang (Zhuansun Shi), disciple of Confucius", "disciple", "Zizhang", r"disciple|Confuci"),
    "ranyou": ("Ran You", "Rǎn Yǒu", "Ran You (Ran Qiu), disciple of Confucius", "disciple", "Ran Qiu", r"disciple|Confuci"),
    "ranqiu": ("Ran Qiu", "Rǎn Qiú", "Ran You (Ran Qiu), disciple of Confucius", "disciple", None, None),
    "zhonggong": ("Zhonggong", "Zhònggōng", "Zhonggong (Ran Yong), disciple of Confucius", "disciple", "Ran Yong", r"disciple|Confuci"),
    "zaiwo": ("Zai Wo", "Zǎi Wǒ", "Zai Wo, disciple of Confucius", "disciple", "Zai Yu", r"disciple|Confuci"),
    "youzi": ("Youzi", "Yǒuzǐ", "Youzi (You Ruo), disciple of Confucius", "disciple", "You Ruo", r"disciple|Confuci"),
    "minziqian": ("Min Ziqian", "Mǐn Zǐqiān", "Min Ziqian (Min Sun), disciple of Confucius", "disciple", "Min Sun", r"disciple|Confuci"),
    "fanchi": ("Fan Chi", "Fán Chí", "Fan Chi, disciple of Confucius", "disciple", "Fan Chi", r"disciple|Confuci"),
    "gongxihua": ("Gongxi Hua", "Gōngxī Huá", "Gongxi Chi (Zihua), disciple of Confucius", "disciple", "Gongxi Chi", r"disciple|Confuci"),
    "simaniu": ("Sima Niu", "Sīmǎ Niú", "Sima Niu, disciple of Confucius", "disciple", "Sima Geng", r"disciple|Confuci"),
    "zengxi": ("Zeng Xi", "Zēng Xī", "Zeng Dian (Zeng Xi), father of Zengzi", "disciple", "Zeng Dian", r"disciple|Confuci"),
    "ranboniu": ("Ran Boniu", "Rǎn Bóniú", "Ran Geng (Boniu), disciple of Confucius", "disciple", "Ran Geng", r"disciple|Confuci"),
    "gongyechang": ("Gongye Chang", "Gōngyě Cháng", "Gongye Chang, disciple and son-in-law of Confucius", "disciple", "Gongye Chang", r"disciple|Confuci"),
    "nanrong": ("Nan Rong", "Nán Róng", "Nangong Kuo (Nan Rong), disciple of Confucius", "disciple", "Nangong Kuo", r"disciple|Confuci"),
    "yao": ("Yao", "Yáo", "Emperor Yao, legendary sage-king", "royal", "Emperor Yao", r"emperor|legendary|ruler|sage"),
    "shun": ("Shun", "Shùn", "Emperor Shun, legendary sage-king", "royal", "Emperor Shun", r"emperor|legendary|ruler|sage"),
    "yu": ("Yu", "Yǔ", "Yu the Great, tamer of the flood", "royal", "Yu the Great", r"king|legendary|ruler|Xia|flood"),
    "tang": ("Tang", "Tāng", "Tang of Shang, founder of the Shang", "royal", "Tang of Shang", r"king|Shang|ruler"),
    "kingwen": ("Wen", "Wén Wáng", "King Wen of Zhou", "royal", "King Wen of Zhou", r"king|Zhou"),
    "kingwu": ("Wu", "Wǔ Wáng", "King Wu of Zhou", "royal", "King Wu of Zhou", r"king|Zhou"),
    "zhougong": ("Zhougong", "Zhōugōng", "Duke of Zhou", "royal", "Duke of Zhou", r"Zhou|regent|duke"),
    "boyi": ("Boyi", "Bóyí", "Boyi, recluse brother of Shuqi", "sage", "Boyi", r"brother|Shang|Zhou|hermit|recluse|Guzhu"),
    "shuqi": ("Shuqi", "Shūqí", "Shuqi, recluse brother of Boyi", "sage", "Shuqi", r"brother|Shang|Zhou|hermit|recluse|Guzhu"),
    "guanzhong": ("Guan Zhong", "Guǎn Zhòng", "Guan Zhong, chancellor of Qi", "human", "Guan Zhong", r"chancellor|politician|statesman|philosopher"),
    "weizi": ("Weizi", "Wēizǐ", "Weizi, half-brother of King Zhou of Shang", "royal", "Weizi", r"Shang|Song|duke|prince"),
    "jizi": ("Jizi", "Jīzǐ", "Jizi, Shang noble", "royal", "Jizi", r"Shang|sage|Joseon|noble"),
    "bigan": ("Bigan", "Bǐgān", "Bigan, Shang prince", "royal", "Bigan", r"Shang|prince|god of wealth"),
    "liuxiahui": ("Liuxia Hui", "Liǔxià Huì", "Liuxia Hui, worthy of Lu", "sage", "Liuxia Hui", r"Lu|official|philosopher|virtuous"),
    "houji": ("Houji", "Hòujì", "Houji, ancestor of the Zhou, god of millet", "deity", "Hou Ji", r"Zhou|agricultur|millet|deity|culture hero"),
    "gaoyao": ("Gaoyao", "Gāoyáo", "Gaoyao, minister of justice under Shun", "human", "Gao Yao", r"minister|Shun|judge|legendary"),
    "yiyin": ("Yi Yin", "Yī Yǐn", "Yi Yin, minister of Tang", "human", "Yi Yin", r"Shang|minister|chancellor"),
    "taibo": ("Taibo", "Tàibó", "Taibo, founder of Wu", "royal", "Taibo", r"Wu|Zhou|founder|king"),
    "nanzi": ("Nanzi", "Nánzǐ", "Nanzi, wife of Duke Ling of Wey", "royal", "Nanzi", r"Wey|duchess|consort|Wei"),
    "jieyu": ("Jieyu", "Jiēyú", "Jieyu, the madman of Chu", "sage", "Jieyu", r"Chu|recluse|hermit|madman"),
    "zichan": ("Zichan", "Zǐchǎn", "Zichan, chancellor of Zheng", "human", "Zichan", r"Zheng|statesman|chancellor|politician"),
    "mengzi": ("Mengzi", "Mèngzǐ", "Mencius", "sage", "Mencius", r"philosopher"),
    "gaozi": ("Gaozi", "Gàozǐ", "Gaozi, philosopher who debated Mencius", "sage", "Gaozi", r"philosopher"),
    "gongsunchou": ("Gongsun Chou", "Gōngsūn Chǒu", "Gongsun Chou, disciple of Mencius", "disciple", "Gongsun Chou", r"disciple|Mencius"),
    "wanzhang": ("Wan Zhang", "Wàn Zhāng", "Wan Zhang, disciple of Mencius", "disciple", "Wan Zhang", r"disciple|Mencius"),
    "yangzhu": ("Yang Zhu", "Yáng Zhū", "Yang Zhu, philosopher", "sage", "Yang Zhu", r"philosopher"),
    "mozi": ("Mozi", "Mòzǐ", "Mozi (Mo Di), philosopher", "sage", "Mozi", r"philosopher"),
    "modi": ("Mo Di", "Mò Dí", "Mozi (Mo Di), philosopher", "sage", None, None),
    "xuxing": ("Xu Xing", "Xǔ Xíng", "Xu Xing, agriculturalist", "sage", "Xu Xing", r"philosopher|agricultur"),
    "gusou": ("Gusou", "Gǔsǒu", "Gusou, father of Shun", "human", "Gusou", r"Shun|father"),
    "fuyue": ("Fu Yue", "Fù Yuè", "Fu Yue, minister of Wuding", "human", "Fu Yue", r"Shang|minister|chancellor"),
    "bailixi": ("Baili Xi", "Bǎilǐ Xī", "Baili Xi, minister of Qin", "human", "Baili Xi", r"Qin|minister|politician"),
    "laozi": ("Laozi", "Lǎozǐ", "Laozi", "sage", "Laozi", r"philosopher|Taoism|Daoism"),
    "laodan": ("Lao Dan", "Lǎo Dān", "Laozi", "sage", None, None),
    "zhuangzi": ("Zhuangzi", "Zhuāngzǐ", "Zhuangzi (Zhuang Zhou)", "sage", "Zhuangzi", r"philosopher"),
    "zhuangzhou": ("Zhuang Zhou", "Zhuāng Zhōu", "Zhuangzi (Zhuang Zhou)", "sage", None, None),
    "huizi": ("Huizi", "Huìzǐ", "Hui Shi (Huizi), logician", "sage", "Hui Shi", r"philosopher|logician"),
    "huishi": ("Hui Shi", "Huì Shī", "Hui Shi (Huizi), logician", "sage", None, None),
    "liezi": ("Liezi", "Lièzǐ", "Liezi (Lie Yukou)", "sage", "Liezi", r"philosopher|Tao"),
    "lieyukou": ("Lie Yukou", "Liè Yùkòu", "Liezi (Lie Yukou)", "sage", None, None),
    "xuyou": ("Xu You", "Xǔ Yóu", "Xu You, recluse who refused Yao's throne", "sage", "Xu You", r"hermit|recluse|legendary"),
    "huangdi": ("Huangdi", "Huángdì", "Yellow Emperor", "deity", "Yellow Emperor", r"emperor|deity|legendary|mythical"),
    "fuxi": ("Fuxi", "Fúxī", "Fuxi, culture hero", "deity", "Fuxi", r"culture hero|deity|legendary|mythical"),
    "shennong": ("Shennong", "Shénnóng", "Shennong, divine farmer", "deity", "Shennong", r"deity|legendary|ruler|culture hero|mythical"),
    "daozhi": ("Dao Zhi", "Dào Zhí", "Robber Zhi", "human", "Robber Zhi", r"robber|bandit|outlaw"),
    "paoding": ("Pao Ding", "Páo Dīng", "Cook Ding", "human", None, None),
    "nanguoziqi": ("Nanguo Ziqi", "Nánguō Zǐqí", "Ziqi of South Wall", "sage", None, None),
    "nieque": ("Nieque", "Nièquē", "Nieque, sage", "sage", None, None),
    "wangni": ("Wang Ni", "Wáng Ní", "Wang Ni, sage", "sage", None, None),
    "huzi": ("Huzi", "Húzǐ", "Huzi (Huqiu Zilin), Liezi's teacher", "sage", None, None),
    "hundun": ("Hundun", "Hùndùn", "Hundun, emperor of the centre", "mythological_being", "Hundun", r"mythical|legendary|chaos|creature"),
    "peng": ("Peng", "Péng", "Peng, the giant bird", "mythological_being", "Peng", r"bird|mythical|legendary"),
    "kun": ("Kun", "Kūn", "Kun, the giant fish", "mythological_being", None, None),
    "guangchengzi": ("Guangchengzi", "Guǎngchéngzǐ", "Guangchengzi, immortal", "deity", "Guangchengzi", r"Tao|immortal|deity"),
    "hebo": ("Hebo", "Hébó", "Hebo, god of the Yellow River", "deity", "Hebo", r"river|god|deity"),
    "beihairuo": ("Ruo", "Ruò", "Ruo, god of the North Sea", "deity", None, None),
    "lunbian": ("Lun Bian", "Lún Biǎn", "Wheelwright Bian", "human", None, None),
    "gengsangchu": ("Gengsang Chu", "Gēngsāng Chǔ", "Gengsang Chu, disciple of Laozi", "sage", "Gengsang Chu", r"Tao|disciple|philosopher"),
    "guanyin_yin": ("Guan Yin", "Guān Yǐn", "Yin Xi, Keeper of the Pass", "sage", "Yin Xi", r"Tao|Laozi|philosopher"),
    "huaxu": ("Huaxu", "Huáxū", "Huaxu, mother of Fuxi", "deity", "Huaxu", r"mother|mythical|legendary|goddess"),
    "kingmu": ("Mu", "Mù Wáng", "King Mu of Zhou", "royal", "King Mu of Zhou", r"king|Zhou"),
    "xiwangmu": ("Xiwangmu", "Xīwángmǔ", "Queen Mother of the West", "deity", "Queen Mother of the West", r"goddess|deity"),
    "yugong": ("Yugong", "Yúgōng", "the Foolish Old Man", "human", None, None),
    "kuafu": ("Kuafu", "Kuāfù", "Kuafu, the giant who chased the sun", "mythological_being", "Kuafu", r"giant|mythical|myth"),
    "nuwa": ("Nüwa", "Nǚwā", "Nüwa, mother goddess", "deity", "Nüwa", r"goddess|deity|mythical"),
    "gonggong": ("Gonggong", "Gònggōng", "Gonggong, water god", "deity", "Gonggong", r"god|deity|mythical|water"),
    "boya": ("Boya", "Bóyá", "Boya, zither player", "human", "Yu Boya", r"musician|qin|guqin"),
    "zhongziqi": ("Zhong Ziqi", "Zhōng Zǐqī", "Zhong Ziqi, woodcutter who understood Boya", "human", "Zhong Ziqi", r"woodcutter|friend|music"),
    "yanshi": ("Yanshi", "Yǎnshī", "Yanshi, artificer", "human", None, None),
    "hane": ("Han E", "Hán É", "Han E, singer", "human", None, None),
    "bianque": ("Bian Que", "Biǎn Què", "Bian Que, physician", "human", "Bian Que", r"physician|doctor|medical"),
    "zaofu": ("Zaofu", "Zàofù", "Zaofu, charioteer", "human", "Zaofu", r"charioteer|driver|Zhao"),
    "jiangyuan": ("Jiang Yuan", "Jiāng Yuán", "Jiang Yuan, mother of Houji", "deity", "Jiang Yuan", r"mother|Zhou|consort|Hou Ji"),
    "tairen": ("Tairen", "Tàirèn", "Tairen, mother of King Wen", "royal", "Tairen", r"mother|Zhou|King Wen"),
    "taisi": ("Taisi", "Tàisì", "Taisi, wife of King Wen", "royal", "Taisi", r"wife|Zhou|King Wen|queen"),
    "taijiang": ("Taijiang", "Tàijiāng", "Taijiang, wife of Gugong Danfu", "royal", "Taijiang", r"Zhou|wife|consort"),
    "danfu": ("Danfu", "Dǎnfù", "Gugong Danfu, ancestor of the Zhou", "royal", "Gugong Danfu", r"Zhou|ancestor|duke|leader"),
    "wangji": ("Wangji", "Wáng Jì", "Ji Li (Wang Ji), father of King Wen", "royal", "Ji Li", r"Zhou|father|King Wen"),
    "zhongshanfu": ("Zhong Shanfu", "Zhòng Shānfǔ", "Zhong Shanfu, minister of King Xuan", "human", "Zhong Shanfu", r"Zhou|minister|official"),
    "yinjifu": ("Yin Jifu", "Yǐn Jífǔ", "Yin Jifu, general of King Xuan", "human", "Yin Jifu", r"Zhou|general|minister|official"),
    "shaogong": ("Shaogong", "Shàogōng", "Duke of Shao", "royal", "Duke of Shao", r"Zhou|duke|regent"),
    "mengjiang": ("Mengjiang", "Mèngjiāng", "Meng Jiang, the eldest Jiang lady of the Odes", "human", None, None),
    "zhuangjiang": ("Zhuangjiang", "Zhuāngjiāng", "Zhuang Jiang, duchess of Wey", "royal", "Zhuang Jiang", r"Wey|Wei|duchess|consort|poet"),
    "gun": ("Gun", "Gǔn", "Gun, father of Yu", "human", "Gun", r"father|Yu|flood|myth"),
    "danzhu": ("Danzhu", "Dānzhū", "Danzhu, son of Yao", "royal", "Danzhu", r"Yao|son"),
    "xihe": ("Xihe", "Xīhé", "Xihe, sun goddess / astronomers", "deity", "Xihe", r"goddess|sun|deity"),
    "kui": ("Kui", "Kuí", "Kui, music master of Shun", "human", None, None),
    "taijia": ("Taijia", "Tàijiǎ", "Tai Jia, king of Shang", "royal", "Tai Jia", r"Shang|king"),
    "pangeng": ("Pangeng", "Pángēng", "Pan Geng, king of Shang", "royal", "Pan Geng", r"Shang|king"),
    "wuding": ("Wuding", "Wǔdīng", "Wu Ding, king of Shang", "royal", "Wu Ding", r"Shang|king"),
    "chengwang": ("Cheng", "Chéng Wáng", "King Cheng of Zhou", "royal", "King Cheng of Zhou", r"king|Zhou"),
    "kangshu": ("Kangshu", "Kāngshū", "Kangshu, brother of King Wu", "royal", "Kangshu", r"Wey|Wei|Zhou|duke|marquis"),
    "chiyou": ("Chiyou", "Chīyóu", "Chiyou, war god", "deity", "Chiyou", r"tribal|mythical|leader|god|war"),
    "jingwei": ("Jingwei", "Jīngwèi", "Jingwei, the bird that fills the sea", "mythological_being", "Jingwei", r"bird|mythical|myth"),
    "nuwa_jingwei": ("Nüwa", "Nǚwá", "Jingwei, the bird that fills the sea", "mythological_being", "Jingwei", r"bird|mythical|myth"),
    "xingtian": ("Xingtian", "Xíngtiān", "Xingtian, the headless giant", "mythological_being", "Xingtian", r"giant|mythical|deity|myth"),
    "zhulong": ("Zhulong", "Zhúlóng", "Zhulong, the torch dragon", "mythological_being", "Zhulong", r"dragon|mythical|deity|god"),
    "dijun": ("Dijun", "Dìjùn", "Dijun, supreme god", "deity", "Dijun", r"god|deity|emperor|mythical"),
    "changxi": ("Changxi", "Chángxī", "Changxi, moon goddess", "deity", "Changxi", r"goddess|moon|deity"),
    "yi_archer": ("Yi", "Yì", "Houyi, the archer", "mythological_being", "Houyi", r"archer|mythical|hero"),
    "yinglong": ("Yinglong", "Yìnglóng", "Yinglong, winged dragon", "mythological_being", "Yinglong", r"dragon"),
    "ba": ("Ba", "Bá", "Ba, drought goddess", "deity", "Nüba", r"drought|goddess|deity"),
    "zhurong": ("Zhurong", "Zhùróng", "Zhurong, god of fire", "deity", "Zhurong", r"fire|god|deity"),
    "yandi": ("Yandi", "Yándì", "Yan Emperor", "deity", "Yan Emperor", r"emperor|ruler|legendary|deity|mythical"),
    "goumang": ("Goumang", "Gōumáng", "Goumang, god of spring and wood", "deity", "Goumang", r"god|deity|spring|wood"),
    "rushou": ("Rushou", "Rùshōu", "Rushou, god of autumn and metal", "deity", "Rushou", r"god|deity|autumn|metal"),
    "luwu": ("Luwu", "Lùwú", "Luwu, guardian of Kunlun", "mythological_being", "Luwu", r"god|deity|mythical|Kunlun|guardian"),
    "taishang": ("Taishang", "Tàishàng", "Laozi", "deity", None, None),
}
CN_ALIAS = {"zhongni": "confucius", "yanyuan": "yanhui", "zhongyou": "zilu", "ranqiu": "ranyou", "laodan": "laozi", "zhuangzhou": "zhuangzi",
            "huishi": "huizi", "lieyukou": "liezi", "modi": "mozi", "nuwa_jingwei": "jingwei", "taishang": "laozi"}
CN_REL = {"zhongni": "courtesy name of Confucius", "yanyuan": "courtesy name of Yan Hui", "zhongyou": "personal name of Zilu",
          "ranqiu": "personal name of Ran You", "laodan": "another name of Laozi", "zhuangzhou": "personal name of Zhuangzi",
          "huishi": "personal name of Huizi", "lieyukou": "personal name of Liezi", "modi": "personal name of Mozi",
          "nuwa_jingwei": "Nüwa (女娃), daughter of the Yan Emperor, who became the Jingwei bird",
          "taishang": "the Most High (Taishang Laojun), the deified Laozi"}

def cnf(key, forms, review=False, scope=None, rel="", role=None):
    nm, tr, lab, et, q, rx = CN[key]
    bk = CN_ALIAS.get(key, key)
    spec = (CN[bk][4], CN[bk][5]) if CN[bk][4] else None
    return Fig(nm, CN[bk][2], et, role or ("epithet" if bk != key else "personal"), tr, forms[0], [re.escape(f) for f in forms],
               wd=spec, review=review, scope=scope, conf=0.8 if review else 0.9, key="cn-" + bk + ("" if bk == key else "-" + key),
               rel=rel or CN_REL.get(key, ""), lang="Chinese")

ANALECTS_DISCIPLES = [("yanhui", ["顏回"]), ("yanyuan", ["顏淵"]), ("zilu", ["子路"]), ("zhongyou", ["仲由"]), ("zigong", ["子貢"]), ("zengzi", ["曾子"]),
    ("zixia", ["子夏"]), ("ziyou", ["子游"]), ("zizhang", ["子張"]), ("ranyou", ["冉有", "冉子"]), ("ranqiu", ["冉求"]), ("zhonggong", ["仲弓"]),
    ("zaiwo", ["宰我", "宰予"]), ("youzi", ["有子"]), ("minziqian", ["閔子騫", "閔子"]), ("fanchi", ["樊遲"]), ("gongxihua", ["公西華", "公西赤"]),
    ("simaniu", ["司馬牛"]), ("zengxi", ["曾皙"]), ("ranboniu", ["伯牛"]), ("gongyechang", ["公冶長"]), ("nanrong", ["南容"])]
SAGE_KINGS = [("yao", ["堯"]), ("shun", ["舜"]), ("yu", ["禹"]), ("kingwen", ["文王"]), ("kingwu", ["武王"]), ("zhougong", ["周公"])]

def chinese(stats):
    ws_fetch()
    rows, review = [], []
    def run(segs, corpus, tradition, figs, sub=""):
        nonlocal rows, review
        if not segs:
            stats["no text"].append(corpus); return
        base = dict(language="Chinese", subtradition=sub, corpus=corpus, source=f"{corpus}, classical text (public domain), zh.wikisource")
        r, rv = build(figs, segs, base, tradition, wd_tag="cn", stats=stats); rows += r; review += rv
    K = lambda: [cnf(k, f) for k, f in SAGE_KINGS]
    run(ws_segs("zh", "論語/", "Analects"), "Analects", "Confucian",
        [cnf("confucius", ["孔子"]), cnf("zhongni", ["仲尼"])] + [cnf(k, f) for k, f in ANALECTS_DISCIPLES] + K() + [
         cnf("tang", ["湯"], review=True), cnf("boyi", ["伯夷"]), cnf("shuqi", ["叔齊"]), cnf("guanzhong", ["管仲"]), cnf("weizi", ["微子"]), cnf("jizi", ["箕子"]),
         cnf("bigan", ["比干"]), cnf("liuxiahui", ["柳下惠"]), cnf("houji", ["稷"], review=True), cnf("gaoyao", ["皋陶"]), cnf("yiyin", ["伊尹"]),
         cnf("taibo", ["泰伯"]), cnf("nanzi", ["南子"]), cnf("jieyu", ["接輿"]), cnf("zichan", ["子產"])])
    run(ws_segs("zh", "孟子/", "Mencius"), "Mencius", "Confucian",
        [cnf("mengzi", ["孟子"]), cnf("confucius", ["孔子"]), cnf("zhongni", ["仲尼"]), cnf("gaozi", ["告子"]), cnf("gongsunchou", ["公孫丑"]),
         cnf("wanzhang", ["萬章"]), cnf("yangzhu", ["楊朱", "楊氏"]), cnf("mozi", ["墨子"]), cnf("modi", ["墨翟"]), cnf("xuxing", ["許行"]),
         cnf("gusou", ["瞽瞍"]), cnf("fuyue", ["傅說"]), cnf("bailixi", ["百里奚"]), cnf("boyi", ["伯夷"]), cnf("yiyin", ["伊尹"]), cnf("liuxiahui", ["柳下惠"]),
         cnf("houji", ["后稷"]), cnf("gaoyao", ["皋陶"]), cnf("zengzi", ["曾子"]), cnf("zigong", ["子貢"]), cnf("zilu", ["子路"]), cnf("yanyuan", ["顏淵"]),
         cnf("tang", ["湯"], review=True)] + K())
    run(ws_segs("zh", "禮記/大學", "Great Learning", single=True), "Great Learning", "Confucian",
        [cnf("zengzi", ["曾子"]), cnf("kingwen", ["文王"]), cnf("yao", ["堯"]), cnf("shun", ["舜"]), cnf("tang", ["湯"], review=True)])
    run(ws_segs("zh", "禮記/中庸", "Doctrine of the Mean", single=True), "Doctrine of the Mean", "Confucian",
        [cnf("zhongni", ["仲尼"]), cnf("zilu", ["子路"]), cnf("wangji", ["王季"])] + K())
    run(ws_segs("zh", "今文孝經", "Classic of Filial Piety", single=True), "Classic of Filial Piety", "Confucian",
        [cnf("zhongni", ["仲尼"]), cnf("zengzi", ["曾子"]), cnf("zhougong", ["周公"]), cnf("houji", ["后稷"]), cnf("kingwen", ["文王"])])
    # Daodejing: the text names no one (Laozi is not named in it), so it gives no rows
    run(ws_segs("zh", "莊子/", "Zhuangzi"), "Zhuangzi", "Daoist",
        [cnf("zhuangzi", ["莊子"]), cnf("zhuangzhou", ["莊周"]), cnf("laozi", ["老子"]), cnf("laodan", ["老聃"]), cnf("huizi", ["惠子"]), cnf("huishi", ["惠施"]),
         cnf("liezi", ["列子"]), cnf("lieyukou", ["列禦寇"]), cnf("xuyou", ["許由"]), cnf("huangdi", ["黃帝"]), cnf("fuxi", ["伏羲", "伏戲"]),
         cnf("shennong", ["神農"]), cnf("confucius", ["孔子"]), cnf("zhongni", ["仲尼"]), cnf("yanhui", ["顏回"]), cnf("zigong", ["子貢"]), cnf("zilu", ["子路"]),
         cnf("daozhi", ["盜跖"]), cnf("paoding", ["庖丁"]), cnf("nanguoziqi", ["南郭子綦"]), cnf("nieque", ["齧缺"]), cnf("wangni", ["王倪"]),
         cnf("huzi", ["壺子"]), cnf("hundun", ["渾沌"]), cnf("peng", ["鵬"]), cnf("kun", ["鯤"]), cnf("guangchengzi", ["廣成子"]), cnf("hebo", ["河伯"]),
         cnf("beihairuo", ["北海若"]), cnf("lunbian", ["輪扁"]), cnf("gengsangchu", ["庚桑楚"]), cnf("jieyu", ["接輿"]), cnf("yangzhu", ["楊朱"]),
         cnf("mozi", ["墨子"]), cnf("xiwangmu", ["西王母"]), cnf("boyi", ["伯夷"]), cnf("shuqi", ["叔齊"]), cnf("yao", ["堯"]), cnf("shun", ["舜"]), cnf("yu", ["禹"])])
    run(ws_segs("zh", "列子/", "Liezi"), "Liezi", "Daoist",
        [cnf("liezi", ["列子"]), cnf("huzi", ["壺丘子林", "壺子"]), cnf("guanyin_yin", ["關尹"]), cnf("huangdi", ["黃帝"]), cnf("huaxu", ["華胥"]),
         cnf("kingmu", ["穆王"]), cnf("xiwangmu", ["西王母"]), cnf("yangzhu", ["楊朱"]), cnf("yugong", ["愚公"]), cnf("kuafu", ["夸父"]),
         cnf("nuwa", ["女媧"]), cnf("gonggong", ["共工"]), cnf("boya", ["伯牙"]), cnf("zhongziqi", ["鍾子期"]), cnf("yanshi", ["偃師"]), cnf("hane", ["韓娥"]),
         cnf("bianque", ["扁鵲"]), cnf("zaofu", ["造父"]), cnf("confucius", ["孔子"]), cnf("zhongni", ["仲尼"]), cnf("laodan", ["老聃"]),
         cnf("yanhui", ["顏回"]), cnf("zigong", ["子貢"]), cnf("yao", ["堯"]), cnf("shun", ["舜"]), cnf("yu", ["禹"])])
    idx = os.path.join(WS, "zh", "尚書.wiki")   # the 58 chapters of the received text (index table), not the bamboo-slip finds also hosted
    canon = set(re.findall(r"\|\d+\|\|([^|\n]+)", open(idx, encoding="utf-8").read())) if os.path.exists(idx) else set()
    run([x for x in ws_segs("zh", "尚書/", "Shangshu") if not canon or x.text in canon], "Shangshu", "Confucian",
        K() + [cnf("gaoyao", ["皋陶"]), cnf("houji", ["后稷"]), cnf("gun", ["鯀"]), cnf("danzhu", ["丹朱"]), cnf("xihe", ["羲和"]),
         cnf("kui", ["夔"], review=True), cnf("tang", ["成湯"]), cnf("yiyin", ["伊尹"]), cnf("taijia", ["太甲"]), cnf("pangeng", ["盤庚"]), cnf("fuyue", ["傅說"]),
         cnf("wuding", ["武丁", "高宗"]), cnf("weizi", ["微子"]), cnf("jizi", ["箕子"]), cnf("bigan", ["比干"]), cnf("shaogong", ["召公"]),
         cnf("chengwang", ["成王"]), cnf("kangshu", ["康叔"]), cnf("gonggong", ["共工"]), cnf("chiyou", ["蚩尤"])])
    run(ws_segs("zh", "詩經/", "Shijing"), "Shijing", "Confucian",
        [cnf("jiangyuan", ["姜嫄"]), cnf("houji", ["后稷"]), cnf("tairen", ["大任", "太任"]), cnf("taisi", ["大姒", "太姒"]), cnf("taijiang", ["大姜", "太姜"]),
         cnf("danfu", ["亶父"]), cnf("wangji", ["王季"]), cnf("kingwen", ["文王"]), cnf("kingwu", ["武王"]), cnf("zhougong", ["周公"]), cnf("shaogong", ["召公", "召伯"]),
         cnf("zhongshanfu", ["仲山甫"]), cnf("yinjifu", ["吉甫"]), cnf("tang", ["成湯"]), cnf("yu", ["禹"]), cnf("mengjiang", ["孟姜"]), cnf("zhuangjiang", ["莊姜"])])
    run(ws_segs("zh", "周易/", "Yijing"), "Yijing", "Confucian",
        [cnf("fuxi", ["包犧", "庖犧", "伏羲"]), cnf("shennong", ["神農"]), cnf("huangdi", ["黃帝"]), cnf("jizi", ["箕子"]), cnf("wuding", ["高宗"]),
         cnf("kingwen", ["文王"]), cnf("yao", ["堯"]), cnf("shun", ["舜"])])
    run([x for x in ws_segs("zh", "禮記/", "Liji") if x.text not in ("大學", "中庸")], "Liji", "Confucian",
        [cnf("confucius", ["孔子"]), cnf("zhongni", ["仲尼"]), cnf("zengzi", ["曾子"]), cnf("zixia", ["子夏"]), cnf("ziyou", ["子游"]), cnf("zizhang", ["子張"]),
         cnf("zilu", ["子路"]), cnf("zigong", ["子貢"]), cnf("yanyuan", ["顏淵"]), cnf("houji", ["后稷"]), cnf("shennong", ["神農"]), cnf("huangdi", ["黃帝"])] + K())
    run(ws_segs("zh", "山海經/", "Shanhaijing"), "Shanhaijing", "Chinese folk",
        [cnf("xiwangmu", ["西王母"]), cnf("nuwa", ["女媧"]), cnf("kuafu", ["夸父"]), cnf("jingwei", ["精衛"]), cnf("nuwa_jingwei", ["女娃"]), cnf("xingtian", ["刑天"]),
         cnf("zhulong", ["燭龍", "燭陰"]), cnf("dijun", ["帝俊"]), cnf("xihe", ["羲和"]), cnf("changxi", ["常羲"]), cnf("yi_archer", ["羿"]), cnf("huangdi", ["黃帝"]),
         cnf("chiyou", ["蚩尤"]), cnf("yinglong", ["應龍"]), cnf("ba", ["魃"]), cnf("gonggong", ["共工"]), cnf("zhurong", ["祝融"]), cnf("gun", ["鯀"]),
         cnf("yu", ["禹"]), cnf("yandi", ["炎帝"]), cnf("goumang", ["句芒"]), cnf("rushou", ["蓐收"]), cnf("luwu", ["陸吾"]), cnf("houji", ["后稷"]),
         cnf("shun", ["舜"]), cnf("yao", ["堯"], review=True)])
    run(ws_segs("zh", "太上感應篇", "Taishang Ganying Pian", single=True), "Taishang Ganying Pian", "Daoist", [cnf("taishang", ["太上"])])
    return rows, review


# ───────────────────────────────────────────────────────────── Shinto: Kojiki, Nihon Shoki (original text)
# name, translit, label, entity_type, Wikidata search + description, Kojiki forms, Nihon Shoki forms
KAMI = [
    ("Amaterasu", "Amaterasu-ōmikami", "Amaterasu, sun goddess", "deity", ("Amaterasu", r"goddess|deity|kami|sun"), ["天照大御神", "天照大神"], ["天照大神", "天照大日孁尊", "大日孁貴"]),
    ("Susanoo", "Susa-no-o-no-mikoto", "Susanoo, storm god", "deity", ("Susanoo", r"god|deity|kami|storm"), ["須佐之男", "須佐能男"], ["素戔嗚", "素戔烏"]),
    ("Izanagi", "Izanagi-no-mikoto", "Izanagi, creator god", "deity", ("Izanagi", r"god|deity|kami|creator"), ["伊邪那岐"], ["伊奘諾"]),
    ("Izanami", "Izanami-no-mikoto", "Izanami, creator goddess", "deity", ("Izanami", r"goddess|deity|kami|creator"), ["伊邪那美"], ["伊奘冉"]),
    ("Tsukuyomi", "Tsukuyomi-no-mikoto", "Tsukuyomi, moon god", "deity", ("Tsukuyomi", r"god|deity|kami|moon"), ["月讀"], ["月讀", "月夜見", "月弓"]),
    ("Okuninushi", "Ōkuninushi-no-kami", "Ōkuninushi, god of the land", "deity", ("Ōkuninushi", r"god|deity|kami"), ["大國主"], ["大國主", "大己貴"]),
    ("Onamuji", "Ōnamuji-no-kami", "Ōkuninushi, god of the land", "deity", ("Ōkuninushi", r"god|deity|kami"), ["大穴牟遲"], []),
    ("Konohanasakuya", "Konohana-no-sakuya-bime", "Konohanasakuya-hime, goddess of Mount Fuji and blossoms", "deity", ("Konohanasakuya-hime", r"goddess|deity|kami"),
     ["木花之佐久夜毘賣", "木花佐久夜毘賣", "木花之佐久夜毗賣"], ["木花開耶姬", "木花之開耶姬", "木花開耶姫", "木花之開耶姫"]),
    ("Iwanaga", "Iwa-naga-hime", "Iwanaga-hime, rock goddess, sister of Konohanasakuya", "deity", ("Iwanaga-hime", r"goddess|deity|kami"), ["石長比賣"], ["磐長姬", "磐長姫"]),
    ("Ninigi", "Ninigi-no-mikoto", "Ninigi, grandson of Amaterasu", "deity", ("Ninigi-no-Mikoto", r"god|deity|kami"), ["邇邇藝"], ["瓊瓊杵"]),
    ("Ame-no-Uzume", "Ame-no-Uzume-no-mikoto", "Ame-no-Uzume, goddess of dawn and dance", "deity", ("Ame-no-Uzume", r"goddess|deity|kami"), ["天宇受賣"], ["天鈿女"]),
    ("Tajikarao", "Ame-no-Tajikarao-no-kami", "Ame-no-Tajikarao, god of strength", "deity", ("Ame-no-Tajikarao", r"god|deity|kami"), ["天手力男"], ["手力雄"]),
    ("Omoikane", "Omoikane-no-kami", "Omoikane, god of wisdom", "deity", ("Omoikane", r"god|deity|kami|wisdom"), ["思金神"], ["思兼神"]),
    ("Kushinada", "Kushinada-hime", "Kushinada-hime, wife of Susanoo", "deity", ("Kushinadahime", r"goddess|deity|kami|wife"), ["櫛名田比賣"], ["奇稻田姬", "奇稻田姫"]),
    ("Orochi", "Yamata-no-Orochi", "Yamata no Orochi, eight-headed serpent", "mythological_being", ("Yamata no Orochi", r"serpent|dragon|monster"), ["八俣遠呂智", "八俣遠吕"], ["八岐大蛇"]),
    ("Sukunabikona", "Sukuna-biko-na-no-kami", "Sukunabikona, dwarf god of medicine", "deity", ("Sukunabikona", r"god|deity|kami"), ["少名毘古那"], ["少彥名", "少彦名"]),
    ("Kotoshironushi", "Kotoshiro-nushi-no-kami", "Kotoshironushi, oracle god", "deity", ("Kotoshironushi", r"god|deity|kami"), ["事代主"], ["事代主"]),
    ("Takemikazuchi", "Takemikazuchi-no-kami", "Takemikazuchi, thunder god", "deity", ("Takemikazuchi", r"god|deity|kami|thunder"), ["建御雷"], ["武甕槌"]),
    ("Takeminakata", "Takeminakata-no-kami", "Takeminakata, god of Suwa", "deity", ("Takeminakata", r"god|deity|kami"), ["建御名方"], []),
    ("Hoori", "Hoori-no-mikoto", "Hoori (Yamasachi-hiko)", "deity", ("Hoori", r"god|deity|kami|Yamasachi"), ["火遠理"], ["彥火火出見", "彦火火出見"]),
    ("Hoderi", "Hoderi-no-mikoto", "Hoderi (Umisachi-hiko)", "deity", ("Hoderi", r"god|deity|kami|Umisachi"), ["火照命"], ["火闌降"]),
    ("Toyotama", "Toyotama-hime", "Toyotama-hime, sea princess", "deity", ("Toyotama-hime", r"goddess|deity|kami|princess"), ["豐玉毘賣", "豊玉毘賣"], ["豐玉姬", "豐玉姫", "豊玉姫"]),
    ("Tamayori", "Tamayori-hime", "Tamayori-hime, mother of Emperor Jimmu", "deity", ("Tamayori-hime", r"goddess|deity|kami|mother"), ["玉依毘賣"], ["玉依姬", "玉依姫"]),
    ("Jimmu", "Kamu-yamato-iware-biko", "Emperor Jimmu", "royal", ("Emperor Jimmu", r"emperor"), ["神倭伊波禮毘古"], ["神日本磐余彥", "神日本磐余彦"]),
    ("Yamato Takeru", "Yamato-takeru-no-mikoto", "Yamato Takeru, prince-hero", "royal", ("Yamato Takeru", r"prince|hero|legendary"), ["倭建"], ["日本武"]),
    ("Ousu", "Ousu-no-mikoto", "Yamato Takeru, prince-hero", "royal", ("Yamato Takeru", r"prince|hero|legendary"), ["小碓"], ["小碓"]),
    ("Ototachibana", "Oto-tachibana-hime", "Ototachibana-hime, wife of Yamato Takeru", "royal", ("Ototachibana-hime", r"wife|princess|consort|Yamato"), ["弟橘比賣"], ["弟橘媛"]),
    ("Miyazu", "Miyazu-hime", "Miyazu-hime, wife of Yamato Takeru", "royal", ("Miyazu-hime", r"wife|princess|consort|Yamato"), ["美夜受比賣"], ["宮簀媛"]),
    ("Suseri", "Suseri-bime", "Suseri-bime, daughter of Susanoo", "deity", ("Suseri-hime", r"goddess|deity|kami|daughter"), ["須勢理毘賣"], []),
    ("Yagami", "Yagami-hime", "Yagami-hime, wife of Ōkuninushi", "deity", ("Yagami-hime", r"goddess|princess|deity|kami"), ["八上比賣"], []),
    ("Ame-no-Minakanushi", "Ame-no-Minakanushi-no-kami", "Ame-no-Minakanushi, first kami", "deity", ("Ame-no-Minakanushi", r"god|deity|kami"), ["天之御中主"], ["天御中主"]),
    ("Kuninotokotachi", "Kuni-no-toko-tachi-no-mikoto", "Kuninotokotachi, eternal land god", "deity", ("Kuninotokotachi", r"god|deity|kami"), ["國之常立"], ["國常立"]),
    ("Takamimusubi", "Takamimusubi-no-kami", "Takamimusubi, creator kami", "deity", ("Takamimusubi", r"god|deity|kami"), ["高御產巢日", "高御産巣日"], ["高皇產靈", "高皇産靈"]),
    ("Kamimusubi", "Kamimusubi-no-kami", "Kamimusubi, creator kami", "deity", ("Kamimusubi", r"god|deity|kami|goddess"), ["神產巢日", "神産巣日"], ["神皇產靈", "神皇産靈"]),
    ("Kagutsuchi", "Kagutsuchi-no-kami", "Kagutsuchi, fire god", "deity", ("Kagutsuchi", r"god|deity|kami|fire"), ["迦具土"], ["軻遇突智"]),
    ("Oyamatsumi", "Ōyamatsumi-no-kami", "Ōyamatsumi, mountain god", "deity", ("Ōyamatsumi", r"god|deity|kami|mountain"), ["大山津見"], ["大山祇"]),
    ("Ukanomitama", "Uka-no-mitama-no-kami", "Ukanomitama, rice deity (Inari)", "deity", ("Ukanomitama", r"god|deity|kami|goddess|Inari"), ["宇迦之御魂"], ["倉稻魂"]),
    ("Ogetsu", "Ōgetsu-hime", "Ōgetsu-hime, food goddess", "deity", ("Ōgetsu-hime", r"goddess|deity|kami|food"), ["大宜都比賣", "大氣都比賣"], []),
    ("Sarutahiko", "Sarutahiko-no-kami", "Sarutahiko, earthly guide", "deity", ("Sarutahiko Ōkami", r"god|deity|kami"), ["猿田毘古"], ["猿田彥", "猿田大神", "猿田神"]),
    ("Okinaga-tarashi", "Okinaga-tarashi-hime", "Empress Jingū", "royal", ("Empress Jingū", r"empress|regent|legendary"), ["息長帶比賣"], ["氣長足姬", "氣長足姫"]),
    ("Ame-no-Wakahiko", "Ame-no-Wakahiko", "Ame-no-Wakahiko, envoy kami", "deity", ("Ame-no-Wakahiko", r"god|deity|kami"), ["天若日子"], ["天稚彥", "天稚"]),
    ("Shitateru", "Shitateru-hime", "Shitateru-hime, daughter of Ōkuninushi", "deity", ("Shitateru-hime", r"goddess|deity|kami"), ["下照比賣"], ["下照姬", "下照姫"]),
    ("Ichikishima", "Ichikishima-hime", "Ichikishima-hime, Munakata goddess", "deity", ("Ichikishimahime", r"goddess|deity|kami"), ["市寸嶋比賣", "市寸島比賣"], ["市杵嶋姬"]),
    ("Tagitsu", "Tagitsu-hime", "Tagitsu-hime, Munakata goddess", "deity", ("Tagitsuhime", r"goddess|deity|kami"), ["多岐都比賣"], ["湍津姬", "湍津姫"]),
    ("Tagiri", "Tagiri-bime", "Tagiri-bime (Takiri-bime), Munakata goddess", "deity", ("Tagorihime", r"goddess|deity|kami"), ["多紀理毘賣"], ["田心姬", "田心姫"]),
    ("Ugayafukiaezu", "Ugaya-fuki-aezu-no-mikoto", "Ugayafukiaezu, father of Emperor Jimmu", "deity", ("Ugayafukiaezu", r"god|deity|kami|father"), ["鵜葺草葺不合", "鵜草葺不合", "鵜（葺）草葺不合"], ["鸕鷀草葺不合"]),
    ("Shiotsuchi", "Shiotsuchi-no-kami", "Shiotsuchi, tide god", "deity", ("Shiotsuchi", r"god|deity|kami|sea"), ["鹽椎", "塩椎"], ["鹽土老翁", "塩土老翁"]),
]
KANJI_VAR = ["毘毗", "邇迩", "邪耶", "產産", "巢巣", "豐豊", "彥彦", "姬姫", "嗚鳴", "冉𠕋冊", "奘弉", "猿猨", "嶋島", "稻稲", "靈霊", "國国", "賣売", "遲遅"]
def kanji_rx(form):
    """a form as a regex that accepts the common variant characters of the edition (毘/毗, 邇/迩, 產/産 …)"""
    out = []
    for c in form:
        g = next((v for v in KANJI_VAR if c in v), None)
        out.append(f"[{g}]" if g else re.escape(c))
    return "".join(out)

KAMI_ALT = {"Onamuji": "earlier name of Ōkuninushi", "Ousu": "birth name of Yamato Takeru"}

def shinto(stats):
    ws_fetch()
    rows, review = [], []
    ko = ws_segs("zh", "古事記/", "Kojiki")
    ns = ws_segs("zh", "日本書紀/卷第", "Nihon Shoki")
    for segs, corpus, idx in ((ko, "Kojiki", 5), (ns, "Nihon Shoki", 6)):
        if not segs:
            stats["no text"].append(corpus); continue
        figs = []
        for k in KAMI:
            forms = k[idx]
            if not forms: continue
            alt = k[0] in KAMI_ALT
            figs.append(Fig(k[0], k[2], k[3], "epithet" if alt else "personal", k[1], "*", [kanji_rx(f) for f in forms], wd=k[4], conf=0.9,
                            key="kami-" + re.sub(r"\W", "", k[4][0].lower()) + ("-" + k[0].lower() if alt else ""), rel=KAMI_ALT.get(k[0], ""), lang="Japanese"))
        base = dict(language="Japanese", subtradition="", corpus=corpus, source=f"{corpus}, original text (public domain), zh.wikisource")
        r, rv = build(figs, segs, base, "Shinto", wd_tag="kami", stats=stats); rows += r; review += rv
    return rows, review


# ───────────────────────────────────────────────────────────── Tenrikyo: Mikagura-uta (Nakayama Miki, 1866-82; ja.wikisource)
def tenrikyo(stats):
    p = os.path.join(WS, "ja", "みかぐらうた.wiki")
    if not OFFLINE and not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(ws_get("https://ja.wikisource.org/w/index.php?title=" + urllib.parse.quote("みかぐらうた") + "&action=raw"))
    if not os.path.exists(p):
        stats["no text"].append("Mikagura-uta"); return [], []
    segs, sect = [], ""
    for line in open(p, encoding="utf-8").read().split("\n"):
        m = re.match(r"==\s*(.+?)\s*==", line)
        if m: sect = m.group(1); continue
        if line.strip(": "):
            segs.append(Seg(sect, f"Mikagura-uta, {sect}", "https://ja.wikisource.org/wiki/" + urllib.parse.quote("みかぐらうた"), line.strip(": ")))
    base = dict(language="Japanese", subtradition="", corpus="Mikagura-uta", source="Mikagura-uta (Nakayama Miki, public domain), ja.wikisource")
    return build([Fig("Tenri-O-no-Mikoto", "Tenri-O-no-Mikoto, God the Parent of Tenrikyo", "deity", "divine", "Tenri-ō-no-mikoto", "*",
                      [r"てんりわうの(?:みこと|つとめ)"], fid="slug:tenrikyo:tenri-o-no-mikoto", conf=0.9, key="tenri", lang="Japanese")],
                 segs, base, "Tenrikyo", wd_tag="tenri", stats=stats)


# ───────────────────────────────────────────────────────────── main
def write(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\t".join(COLS) + "\n")
        for r in rows:
            f.write("\t".join(str(r.get(c, "")).replace("\t", " ").replace("\n", " ") for c in COLS) + "\n")

SECTIONS = {"buddhist": "buddhist", "jain": "jain", "sikh": "sikh", "chinese": "chinese", "shinto": "shinto", "tenrikyo": "tenrikyo"}

def main():
    stats = collections.defaultdict(list)
    only = [a[2:] for a in sys.argv[1:] if a.startswith("--") and a[2:] in SECTIONS]
    rows, review = [], []
    for name, fn in SECTIONS.items():
        if only and name not in only: continue
        print(f"{name}…", file=sys.stderr)
        r, rv = globals()[fn](stats); rows += r; review += rv
    seen, out = set(), []
    for r in rows:
        k = (r["corpus"], r["name"], r["figure_id"])
        if k not in seen: seen.add(k); out.append(r)
    review = [r for r in review if (r["corpus"], r["name"], r["figure_id"]) not in seen]
    if only:
        print(f"(--{'/'.join(only)}: not writing) {len(out)} rows, {len(review)} review", file=sys.stderr)
    else:
        write(OUT, out); write(REVIEW, review)
        print(f"wrote {len(out)} rows -> {OUT}; {len(review)} -> {REVIEW}", file=sys.stderr)
    for k, v in collections.Counter((r["tradition"], r["corpus"]) for r in out).most_common():
        print(f"  {k[0]:9} {k[1]:30} {v}", file=sys.stderr)
    for k, v in stats.items():
        print(f"  {k}: {len(v)}: {'; '.join(v)}", file=sys.stderr)

if __name__ == "__main__":
    main()
