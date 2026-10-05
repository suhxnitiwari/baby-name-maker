#!/usr/bin/env python3
"""Buddhist sacred names -> data/sacred/buddhist.tsv (format: docs/sacred-format.md).

Run:  python3 scripts/build_sacred_buddhist.py            (fetches anything missing into raw/sacred/buddhist/)
      python3 scripts/build_sacred_buddhist.py --offline  (only use what is already there)
      python3 scripts/build_sacred_buddhist.py --check    (also print match contexts for spot checks)

Sources
  1. Pali Canon (Theravada). SuttaCentral bilara-data, Mahasangiti Pali root texts of the Sutta Pitaka
     (DN, MN, SN, AN and the Khuddaka Nikaya; Jataka = verses only), CC0. Segment ids such as dn16:1.1.3.
     Names come from SuttaCentral's edition of Malalasekera's Dictionary of Pali Proper Names (sc-data
     dictionaries/complex/en/pli2en_dppn.json): every person / being / place sense with its alternative names.
     Each name is verified in the Pali text by matching inflected forms of its stem (conservative endings
     only, whole tokens). A name that is also a common Pali word (in SuttaCentral's NCPED) or that DPPN gives
     to several people is only kept where a DPPN reference to that person points at a sutta segment in which
     the form occurs; such rows get no occurrence count.
  2. Mahayana sutras, Sanskrit editions from GRETIL (CC BY-NC-SA 4.0): Saddharmapundarika (Vaidya 1960),
     Prajnaparamitahrdaya, Vajracchedika (Vaidya 1961), Sukhavativyuha (larger and smaller), Vimalakirtinirdesa
     (Taisho University 2006 edition of the Potala manuscript). A curated list of figures is matched with
     hand-checked patterns (sandhi such as tac chariputra, compounds such as bhadantanandah) and cited by
     chapter / section / page of the edition.
  3. Wikidata (CC0) for QIDs and sex (P21) of the well-known figures; the Pali and Sanskrit rows of one figure
     share the QID. Other figures get slug:buddhist:<name> ids; their sex comes from DPPN's own wording
     (bhikkhuni / thera, she / he) and is left blank when DPPN does not say.
"""
import collections, json, os, re, subprocess, sys, time, unicodedata, urllib.parse, urllib.request
from html import unescape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw", "sacred", "buddhist")
OUT = os.path.join(ROOT, "data", "sacred", "buddhist.tsv")
OFFLINE = "--offline" in sys.argv
CHECK = "--check" in sys.argv
UA = {"User-Agent": "Lullabyte-build/1.0 (https://github.com/suhxnitiwari/baby-name-maker)"}
COLS = ("name figure_id figure sex original translit language tradition subtradition corpus text passage url occurrences "
        "entity_type name_role status relation source confidence").split()

BILARA = os.path.join(RAW, "bilara-data")
SCDATA = os.path.join(RAW, "sc-data")
GRETIL = os.path.join(RAW, "gretil")
WD_CACHE = os.path.join(RAW, "wikidata_cache.json")
SRC_PALI = "SuttaCentral bilara-data Mahāsaṅgīti Pāli (CC0); names from DPPN, SuttaCentral sc-data edition"
SRC_WD = "; Wikidata (CC0)"
GRETIL_URL = "https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/plaintext/{}.txt"
GRETIL_HTML = "https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/html/{}.htm"


# ----------------------------------------------------------------------------------------------- fetching
def fetch():
    if OFFLINE:
        return
    os.makedirs(RAW, exist_ok=True)
    if not os.path.isdir(BILARA):
        subprocess.run(["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse",
                        "https://github.com/suttacentral/bilara-data.git", BILARA], check=True)
        subprocess.run(["git", "-C", BILARA, "sparse-checkout", "set", "root/pli/ms/sutta"], check=True)
    if not os.path.isdir(SCDATA):
        subprocess.run(["git", "clone", "--depth", "1", "--filter=blob:none", "--no-checkout",
                        "https://github.com/suttacentral/sc-data.git", SCDATA], check=True)
        subprocess.run(["git", "-C", SCDATA, "sparse-checkout", "init", "--no-cone"], check=True)
        subprocess.run(["git", "-C", SCDATA, "sparse-checkout", "set", "/dictionaries/complex/en/pli2en_dppn.json",
                        "/dictionaries/simple/en/pli2en_ncped.json",
                        "/dictionaries/simple/en/pli2en_dpd.json"], check=True)
        subprocess.run(["git", "-C", SCDATA, "checkout"], check=True)
    os.makedirs(GRETIL, exist_ok=True)
    for t in MAHAYANA_TEXTS:
        p = os.path.join(GRETIL, t["file"] + ".txt")
        if not os.path.exists(p):
            req = urllib.request.Request(GRETIL_URL.format(t["file"]), headers=UA)
            open(p, "wb").write(urllib.request.urlopen(req, timeout=120).read())


def wikidata(qids):
    cache = json.load(open(WD_CACHE)) if os.path.exists(WD_CACHE) else {}
    need = [q for q in sorted(set(qids)) if q not in cache]
    if need and not OFFLINE:
        for i in range(0, len(need), 45):
            u = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(dict(
                action="wbgetentities", ids="|".join(need[i:i + 45]), props="labels|claims", languages="en", format="json"))
            d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60))
            for q, e in d["entities"].items():
                p21 = [c["mainsnak"].get("datavalue", {}).get("value", {}).get("id") for c in e.get("claims", {}).get("P21", [])]
                cache[q] = {"label": e.get("labels", {}).get("en", {}).get("value"), "p21": p21}
            time.sleep(3)
        json.dump(cache, open(WD_CACHE, "w"), ensure_ascii=False, indent=0)
    return cache


def wd_sex(cache, q):
    p = (cache.get(q) or {}).get("p21") or []
    if p == ["Q6581097"]:
        return "boy"
    if p == ["Q6581072"]:
        return "girl"
    return ""


# ----------------------------------------------------------------------------------------------- text utils
def nfc(s):
    return unicodedata.normalize("NFC", s)


def pali_norm(s):
    return nfc(s).lower().replace("ṃ", "ṁ")


TOK = re.compile(r"[^\W\d_]+")
FOLD = str.maketrans({"ā": "a", "ī": "i", "ū": "u", "ṁ": "m", "ṃ": "m", "ṅ": "n", "ñ": "n", "ṭ": "t", "ḍ": "d", "ṇ": "n",
                      "ḷ": "l", "ḥ": "h", "Ā": "A", "Ī": "I", "Ū": "U", "Ṭ": "T", "Ḍ": "D", "Ṇ": "N", "Ḷ": "L", "Ñ": "N"})


def latin_pali(s):
    """Today's Latin spelling of a Pali name: Ānanda -> Ananda, Nigaṇṭha Nāṭaputta -> Nigantha Nataputta."""
    s = nfc(s).translate(FOLD)
    return " ".join(w[:1].upper() + w[1:] for w in s.split())


def latin_skt(s):
    """Today's Latin spelling of a Sanskrit name: Avalokiteśvara -> Avalokiteshvara, Mañjuśrī -> Manjushri."""
    s = nfc(s)
    s = re.sub(r"ṃ(?=[pbm])", "m", s)
    s = s.replace("ṃ", "n").replace("c", "ch").replace("C", "Ch").replace("ś", "sh").replace("ṣ", "sh").replace("Ś", "Sh").replace("Ṣ", "Sh")
    s = s.replace("ṛ", "ri").replace("Ṛ", "Ri").replace("chh", "chh")
    return latin_pali(s)


# IAST -> Devanagari (for the 'original' column of Sanskrit rows)
_V = [("ai", "ऐ", "ै"), ("au", "औ", "ौ"), ("ā", "आ", "ा"), ("ī", "ई", "ी"), ("ū", "ऊ", "ू"), ("ṝ", "ॠ", "ॄ"),
      ("ṛ", "ऋ", "ृ"), ("ḷ", "ऌ", "ॢ"), ("a", "अ", ""), ("i", "इ", "ि"), ("u", "उ", "ु"), ("e", "ए", "े"), ("o", "ओ", "ो")]
_C = [("kh", "ख"), ("gh", "घ"), ("ch", "छ"), ("jh", "झ"), ("ṭh", "ठ"), ("ḍh", "ढ"), ("th", "थ"), ("dh", "ध"),
      ("ph", "फ"), ("bh", "भ"), ("k", "क"), ("g", "ग"), ("ṅ", "ङ"), ("c", "च"), ("j", "ज"), ("ñ", "ञ"), ("ṭ", "ट"),
      ("ḍ", "ड"), ("ṇ", "ण"), ("t", "त"), ("d", "द"), ("n", "न"), ("p", "प"), ("b", "ब"), ("m", "म"), ("y", "य"),
      ("r", "र"), ("l", "ल"), ("v", "व"), ("ś", "श"), ("ṣ", "ष"), ("s", "स"), ("h", "ह")]


def deva(iast):
    s, out, i, prev_c = nfc(iast).lower(), [], 0, False
    while i < len(s):
        if s[i] == " ":
            if prev_c:
                out.append("्")
            out.append(" "); prev_c = False; i += 1; continue
        if s[i] in "ṃṁ":
            out.append("ं"); prev_c = False; i += 1; continue
        if s[i] == "ḥ":
            out.append("ः"); prev_c = False; i += 1; continue
        for lat, ind, mat in _V:
            if s.startswith(lat, i):
                out.append(mat if prev_c else ind); prev_c = False; i += len(lat); break
        else:
            for lat, dv in _C:
                if s.startswith(lat, i):
                    if prev_c:
                        out.append("्")
                    out.append(dv); prev_c = True; i += len(lat); break
            else:
                out.append(s[i]); prev_c = False; i += 1
    if prev_c:
        out.append("्")
    return "".join(out)


# ----------------------------------------------------------------------------------------------- Pali corpus
COLLECTIONS = [  # folder, acronym, text name
    ("dn", "DN", "Digha Nikaya"), ("mn", "MN", "Majjhima Nikaya"), ("sn", "SN", "Samyutta Nikaya"),
    ("an", "AN", "Anguttara Nikaya"), ("kp", "Kp", "Khuddakapatha"), ("dhp", "Dhp", "Dhammapada"),
    ("ud", "Ud", "Udana"), ("iti", "Iti", "Itivuttaka"), ("snp", "Snp", "Sutta Nipata"), ("vv", "Vv", "Vimanavatthu"),
    ("pv", "Pv", "Petavatthu"), ("thag", "Thag", "Theragatha"), ("thig", "Thig", "Therigatha"),
    ("tha-ap", "Tha Ap", "Apadana"), ("thi-ap", "Thi Ap", "Apadana"), ("bv", "Bv", "Buddhavamsa"),
    ("cp", "Cp", "Cariyapitaka"), ("ja", "Ja", "Jataka"), ("mnd", "Mnd", "Mahaniddesa"), ("cnd", "Cnd", "Culaniddesa"),
    ("ps", "Ps", "Patisambhidamagga"), ("ne", "Ne", "Nettippakarana"), ("pe", "Pe", "Petakopadesa"),
    ("mil", "Mil", "Milindapanha"),
]
COLL = {c[0]: (i, c[1], c[2]) for i, c in enumerate(COLLECTIONS)}
VINAYA = {"pli-tv-kd": "Kd", "pli-tv-pvr": "Pvr"}  # + pli-tv-bu-vb-pj -> Bu Pj, pli-tv-bi-vb-pc -> Bi Pc


def collection(uid):
    """uid -> (sort index, acronym prefix, text name, uid prefix) or None (Patimokkha: no numbering)."""
    m = re.match(r"[a-z-]+?(?=\d)", uid)
    if not m:
        return None
    c = m.group(0)
    if c in COLL:
        i, acr, text = COLL[c]
        return i, acr, text, c
    if c.startswith("pli-tv-"):
        acr = VINAYA.get(c) or " ".join(x.capitalize() for x in c[len("pli-tv-"):].split("-") if x != "vb")
        return 100, acr, "Vinaya Pitaka", c
    return None


def natkey(uid):
    return [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", uid)]


class Corpus:
    def __init__(self):
        files = []
        for part in ("sutta", "vinaya"):  # Vinaya is cited only after every Sutta Pitaka occurrence
            for dp, _, fs in os.walk(os.path.join(BILARA, "root", "pli", "ms", part)):
                for f in fs:
                    if f.endswith("_root-pli-ms.json"):
                        uid = f[: -len("_root-pli-ms.json")]
                        c = collection(uid)
                        if c:
                            files.append((c[0], natkey(uid), uid, os.path.join(dp, f)))
        files.sort()
        self.segs = []          # [(seg_id, uid, lowered text)]
        self.seg_index = {}     # seg_id -> position
        self.tok = {}           # token -> [count, first position]
        for _, _, uid, path in files:
            for sid, txt in json.load(open(path, encoding="utf-8")).items():
                pos = len(self.segs)
                low = pali_norm(txt)
                self.segs.append((sid, uid, low))
                self.seg_index[sid] = pos
                for t in TOK.findall(low):
                    e = self.tok.get(t)
                    if e is None:
                        self.tok[t] = [1, pos]
                    else:
                        e[0] += 1
        self.uids = {uid for _, _, uid, _ in files}
        self.uid_range = {}  # file uid and sutta uid (an1.228 inside an1.228-237) -> segment range
        for pos, (sid, uid, _) in enumerate(self.segs):
            for u in {uid, sid.split(":")[0]}:
                a = self.uid_range.get(u)
                self.uid_range[u] = (pos, pos + 1) if a is None else (a[0], pos + 1)

    def cite(self, pos):
        sid, uid, _ = self.segs[pos]
        _, acr, text, coll = collection(uid)
        num = sid[len(coll):]
        return dict(text=text, passage=f"{acr} {num}", url=f"https://suttacentral.net/{uid}")

    def count_tokens(self, forms):
        n, first = 0, None
        for f in forms:
            e = self.tok.get(f)
            if e:
                n += e[0]
                first = e[1] if first is None else min(first, e[1])
        return n, first

    def count_phrase(self, wordforms):
        """wordforms: list (per word) of sets of forms; count consecutive token sequences."""
        cand = None
        for f in wordforms[0]:
            if f in self.tok:
                cand = True
        if not cand or not all(any(f in self.tok for f in fs) for fs in wordforms):
            return 0, None
        alt = [("|".join(sorted(map(re.escape, fs), key=len, reverse=True))) for fs in wordforms]
        rx = re.compile(r"(?<![^\W\d_])" + r"[^\w]+".join(f"(?:{a})" for a in alt) + r"(?![^\W\d_])")
        first_word = wordforms[0]
        n, first = 0, None
        for pos, (_, _, low) in enumerate(self.segs):
            if not any(f in low for f in first_word):
                continue
            k = len(rx.findall(low))
            if k:
                n += k
                first = pos if first is None else first
        return n, first

    def seg_has(self, pos, forms, phrase=None):
        low = self.segs[pos][2]
        if phrase:
            return bool(phrase.search(low))
        return any(t in forms for t in TOK.findall(low))


def inflect(word):
    """Conservative inflected forms of one Pali name word (citation form, lower case)."""
    w = pali_norm(word)
    if w.endswith("a"):
        s = w[:-1]
        e = ["a", "o", "aṁ", "ena", "assa", "āya", "ā", "asmā", "amhā", "e", "asmiṁ", "amhi", "ehi", "ebhi", "ānaṁ", "esu", "āse"]
    elif w.endswith("ā"):
        s = w[:-1]
        e = ["ā", "aṁ", "āya", "āyaṁ", "e", "āyo", "āhi", "ānaṁ", "āsu", "ehi", "esu", "uno", "unā"]
    elif w.endswith("ī"):
        s = w[:-1]
        e = ["ī", "iṁ", "iyā", "iyaṁ", "i", "iyo", "īhi", "īnaṁ", "ino", "inā", "issa", "inaṁ"]
    elif w.endswith("i"):
        s = w[:-1]
        e = ["i", "iṁ", "inā", "ino", "issa", "imhā", "imhi", "ismiṁ", "ayo", "ī", "īhi", "īnaṁ", "iyā"]
    elif w.endswith("u") or w.endswith("ū"):
        s = w[:-1]
        e = ["u", "ū", "uṁ", "unā", "uno", "ussa", "avo", "ūhi", "ūnaṁ", "uyā"]
    else:
        return {w}
    return {s + x for x in e}


# ----------------------------------------------------------------------------------------------- DPPN
def dppn_senses():
    """-> list of senses: {key, n, nsenses, cls, head, alias[], text(html), place_type}"""
    d = json.load(open(os.path.join(SCDATA, "dictionaries", "complex", "en", "pli2en_dppn.json"), encoding="utf-8"))
    out = []
    for e in d:
        t = e["text"]
        cls = re.search(r"<dl class='([^']+)'", t).group(1)
        senses, cur = [], None
        for m in re.finditer(r"<dt([^>]*)>(.*?)</dt>|<dd([^>]*)>(.*?)</dd>", t, re.S):
            if m.group(2) is not None:
                inner = m.group(2)
                if "<dfn" in inner or cur is None:
                    head = unescape(re.sub(r"<[^>]+>", "", re.sub(r"<sup>.*?</sup>", "", inner))).strip()
                    if cur is not None and not cur["text"].strip() and head == cur["head"]:
                        continue  # repeated heading for the same sense
                    cur = {"key": e["word"], "cls": cls, "head": nfc(head), "alias": [], "text": "", "info": ""}
                    senses.append(cur)
                else:
                    a = nfc(unescape(re.sub(r"<[^>]+>", "", inner)).strip())
                    if a and a != cur["head"] and a not in cur["alias"]:
                        cur["alias"].append(a)
            else:
                if "info" in (m.group(3) or ""):
                    cur["info"] += m.group(4)
                else:
                    cur["text"] += m.group(4)
        for i, s in enumerate(senses):
            s["n"] = i + 1  # DPPN's own numbering (Visākhā 2 stays 2 even when Visākhā 1 is empty)
        senses = [s for s in senses if re.sub(r"<[^>]+>|\s|\.", "", s["text"]) or s["info"]]
        for s in senses:
            s["nsenses"] = len(senses)
            pt = re.search(r"<span class='type'>([^<]*)</span>", s["info"])
            s["place_type"] = pt.group(1) if pt else ""
            out.append(s)
    return out


def plain(html):
    return unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<a class='ref'[^>]*>.*?</a>", " ", html, flags=re.S))).replace("  ", " ")


def first_sentence(html):
    p = re.search(r"<p>(.*?)</p>", html, re.S)
    s = re.sub(r"\s+([.,;:])", r"\1", re.sub(r"\s+", " ", plain(p.group(1) if p else html))).strip()
    return re.split(r"(?<=[a-zāīū\)])\.(?:\s|$)", s, maxsplit=1)[0]


def dppn_refs(html):
    """SuttaCentral links in a DPPN sense -> [(uid, anchor or '')]"""
    return [(m.group(1), m.group(2) or "") for m in
            re.finditer(r"https://suttacentral\.net/([a-z0-9.\-]+)/en/[a-z]+(?:#([0-9.a-z\-]+))?", html)]


FEM = (r"bhikkhunī|bhikkhunis?|nuns?|therī|therīgāthā|upāsikā|lay ?-?woman|laywomen|queens?|princess(?:es)?|daughters?|"
       r"wi(?:fe|ves)|mothers?|wom[ae]n|lady|ladies|courtesan|sisters?|goddess|devadhītā|consort|niece|widow|maid|girl|"
       r"brahminee|she|her")
MALE = (r"monks?|bhikkhu|thera|elder|theragāthā|upāsaka|lay ?-?man|kings?|princes?|sons?|father|husband|brothers?|nephew|"
        r"man|householder|minister|devaputta|youth|boy|chieftain|chief|general|he|his|him|rājā")
RX_SEX = re.compile(rf"\b(?:(?P<f>{FEM})|(?P<m>{MALE}))\b", re.I)


def dpd_lexicon():
    """Digital Pali Dictionary (via sc-data): headwords with an ordinary meaning, and the grammatical gender of
    headwords glossed 'name of a monk / nun / king ...' (only when every such sense agrees)."""
    p = os.path.join(SCDATA, "dictionaries", "simple", "en", "pli2en_dpd.json")
    common, gender = set(), collections.defaultdict(set)
    if not os.path.exists(p):
        return common, {}
    for e in json.load(open(p, encoding="utf-8")):
        defs = e.get("definition")
        for d in (defs if isinstance(defs, list) else [defs]):
            m = re.match(r"^(\S+)(?: [\d.]+)?: ([\w .,]+?)\. <b>(.*?)</b>", d or "")
            if not m:
                continue
            hw, pos, mean = pali_norm(m.group(1)), m.group(2), m.group(3)
            if re.match(r"(?:name of|family name|clan name|epithet|surname|patronymic)", mean):
                if re.match(r"name of an? (?:\w+ )?(?:monk|nun|arahant|bhikkhunī|brahmin|king|queen|prince|princess|"
                            r"layman|laywoman|lay follower|man|woman|wanderer|ascetic|householder|minister|merchant|"
                            r"courtesan|teacher|student|disciple|elder|novice|servant|youth)\b", mean):
                    gender[hw].add({"masc": "boy", "fem": "girl"}.get(pos.split()[0], "?"))
            else:
                common.add(hw)
    return common, {k: next(iter(v)) for k, v in gender.items() if len(v) == 1 and "?" not in v}


def dppn_sex(sense):
    s = first_sentence(sense["text"])
    m = RX_SEX.search(s)
    sex = ""
    if m:
        sex = "girl" if m.group("f") else "boy"
    else:
        body = plain(sense["text"])
        he = len(re.findall(r"\b(?:he|his|him)\b", body, re.I))
        she = len(re.findall(r"\b(?:she|her|hers)\b", body, re.I))
        if he >= 2 and she == 0:
            sex = "boy"
        elif she >= 2 and he == 0:
            sex = "girl"
    if sex == "girl" and pali_norm(sense["head"]).endswith("a"):
        return ""  # DPPN wording and the Pali grammatical gender disagree: leave blank
    return sex


CAT = [
    ("sage", r"pacceka ?-?buddhas?|\b(?:a|seven|past|former|future|second|third|fourth|fifth|sixth|twenty[- ]\w+)\s+buddhas?\b|buddhas? of (?:a|the) past|\bbuddha of a past"),
    ("mythological_being", r"\b(?:yakkhas?|yakkhinī|nāgas?|asuras?|gandhabbas?|supaṇṇas?|garuḷas?|kinnaras?|petas?|petī|spirits?|kumbhaṇḍas?|rakkhasas?|snakes?)\b"),
    ("deity", r"\b(?:devas?|devaputta|devatā|deit(?:y|ies)|gods?|goddess|brahmā|mahābrahmā|brahmās|great kings|cātummahārājikā|devadhītā)\b"),
    ("disciple", r"\b(?:monks?|bhikkhu|bhikkhunī|nuns?|thera|therī|elder|arahants?|disciples?|novice|sāmaṇera|theragāthā|therīgāthā)\b"),
    ("royal", r"\b(?:king|queen|prince|princess|rājā|rājakumāra|consort|monarch|cakkavatti)\b"),
    ("tribe", r"\b(?:clan|tribe|people|race|gotta|family)\b"),
]


MYTH_CLASS = CAT[1][1] + "|" + CAT[2][1] + r"|\b(?:demons|non[- ]human|beings|brahmas|deities)\b"
CAT += [
    ("place", r"\b(?:township|town|village|city|country|district|region|river|mountain|hill|park|grove|monastery|lake|forest|"
              r"vimāna|palace|mansion|hell|heaven)\b"),
    ("human", r"\b(?:physician|brahmin|householder|wanderer|paribbājaka|ascetic|merchant|banker|seṭṭhi|headman|minister|"
              r"youth|courtesan|lay devotee|laywoman|layman|man|woman|lady|robber|hunter|servant|slave|teacher|sage|seer)\b"),
]


def classify(sense):
    if sense["cls"] == "place":
        return "place"
    s = first_sentence(sense["text"]).lower()
    if s.startswith(("the name given to", "name given to")):
        return "tribe" if re.search(r"inhabitants|people|clan|tribe|family", s[:60]) else "title"
    if re.match(r"(?:the|a) (?:\w+ )?inhabitants of\b|(?:the )?people of\b", s):
        return "tribe"
    if re.match(r"(?:the name of |name of )?(?:a|an|one) (?:[\w-]+ )?(?:class|group|race|family|clan|tribe)\b", s) \
            or re.search(r"\b(?:a|an) (?:class|group) of\b", s[:40]):
        return "mythological_being" if re.search(MYTH_CLASS, s) else "tribe"
    best = None
    for et, rx in CAT:
        if et == "tribe":
            continue
        m = re.search(rx, s)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), et)
    return best[1] if best else "human"


def short_desc(sense, et):
    if et == "place":
        return sense["place_type"] or "place"
    s = first_sentence(sense["text"])
    s = re.sub(r"\s+", " ", s).strip(" .")
    if len(s) > 70:
        s = s[:70].rsplit(" ", 1)[0] + "…"
    return s


# ----------------------------------------------------------------------------------------------- curated
# DPPN key, sense number -> Wikidata QID, Sanskrit form, label, entity_type override
CURATED = {
    ("gotama", 1): ("Q9441", "Gautama", "Gotama, the Buddha", "sage"),
    ("ānanda", 1): ("Q28988", "Ānanda", "Ānanda, the Buddha's attendant", None),
    ("rāhula", 1): ("Q218969", "Rāhula", "Rāhula, the Buddha's son", "disciple"),
    ("sāriputta", 1): ("Q320142", "Śāriputra", "Sāriputta, chief disciple", None),
    ("mahāmoggallāna", 1): ("Q379814", "Mahāmaudgalyāyana", "Mahāmoggallāna, chief disciple", None),
    ("mahāpajāpatī", 1): ("Q613944", "Mahāprajāpatī", "Mahāpajāpatī Gotamī, the Buddha's foster mother", None),
    ("rāhulamātā", 1): ("Q466572", "Yaśodharā", "Yasodharā (Rāhulamātā), the Buddha's wife", "human"),
    ("khemā", 1): ("Q2627201", "Kṣemā", "Khemā, chief bhikkhunī disciple", None),
    ("uppalavaṇṇā", 1): ("Q3175198", "Utpalavarṇā", "Uppalavaṇṇā, chief bhikkhunī disciple", None),
    ("visākhā", 2): ("Q2467542", "Viśākhā", "Visākhā Migāramātā, chief laywoman disciple", "disciple"),
    ("anāthapiṇḍika", 1): ("Q2264464", "Anāthapiṇḍada", "Anāthapiṇḍika, lay patron", None),
    ("mahākassapa", 1): ("Q335304", "Mahākāśyapa", "Mahākassapa, disciple", None),
    ("subhūti", 1): ("Q1144771", "Subhūti", "Subhūti, disciple", "disciple"),
    ("mahākaccāyana", 1): ("Q44277", "Mahākātyāyana", "Mahākaccāna, disciple", None),
    ("anuruddha", 1): ("Q3306373", "Aniruddha", "Anuruddha, disciple and the Buddha's cousin", None),
    ("upāli", 1): ("Q984630", "Upāli", "Upāli, disciple, master of the Vinaya", None),
    ("aññātakoṇḍañña", 1): ("Q2708070", "Ājñātakauṇḍinya", "Aññāsi Koṇḍañña, first disciple", None),
    ("devadatta", 1): ("Q451043", "Devadatta", "Devadatta, the Buddha's cousin", None),
    ("suddhodana", 1): ("Q226488", "Śuddhodana", "Suddhodana, the Buddha's father", "royal"),
    ("māyā", 1): ("Q877831", "Māyā", "Māyā, the Buddha's mother", "royal"),
    ("nanda", 2): ("Q3610453", "Nanda", "Nanda, the Buddha's half-brother", "disciple"),
    ("bimbisāra", 1): ("Q317765", "Bimbisāra", "Bimbisāra, king of Magadha", None),
    ("ajātasattu", 1): ("Q379242", "Ajātaśatru", "Ajātasattu, king of Magadha", "royal"),
    ("pasenadi", 1): ("Q3055324", "Prasenajit", "Pasenadi, king of Kosala", None),
    ("jīvaka", 1): ("Q1689712", "Jīvaka", "Jīvaka, the Buddha's physician", "human"),
    ("aṅgulimāla", 1): ("Q263512", "Aṅgulimāla", "Aṅgulimāla, robber turned monk", "disciple"),
    ("paṭācārā", 1): ("Q7144138", "Paṭācārā", "Paṭācārā, bhikkhunī", None),
    ("kisāgotamī", 1): ("Q133576452", "Kṛśā Gautamī", "Kisāgotamī, bhikkhunī", None),
    ("dhammadinnā", 1): ("Q11774717", "Dharmadinnā", "Dhammadinnā, bhikkhunī", None),
    ("ambapālī", 1): ("Q688689", "Āmrapālī", "Ambapālī, courtesan of Vesālī", "human"),
    ("sakka", 1): ("Q1444745", "Śakra", "Sakka, king of the devas", "deity"),
    ("sahampati", 1): ("Q9178677", "Sahāṃpati", "Brahmā Sahampati", "deity"),
    ("māra", 1): ("Q1352021", "Māra", "Māra, the Evil One", "demon"),
    ("assaji", 1): ("Q2363264", "Aśvajit", "Assaji, one of the first five disciples", None),
    ("āḷārakālāma", 1): ("Q2500007", "Ārāḍa Kālāma", "Āḷāra Kālāma, the Bodhisatta's teacher", "human"),
    ("uddaka", 1): ("Q7876891", "Udraka Rāmaputra", "Uddaka Rāmaputta, the Bodhisatta's teacher", "human"),
    ("nigaṇṭha nāṭaputta", 1): ("Q9422", "Nirgrantha Jñātiputra", "Nigaṇṭha Nāṭaputta (Mahāvīra)", "human"),
    ("kuvera", 1): ("Q866315", "Vaiśravaṇa", "Vessavaṇa (Kuvera), Great King of the north", "deity"),
    ("piṇḍola", 2): ("Q4919193", "Piṇḍola Bhāradvāja", "Piṇḍola Bhāradvāja, arahant", "disciple"),
    ("kassapa", 1): ("Q1808464", "Kāśyapa", "Kassapa, Buddha of the past", "sage"),
    ("vipassī", 1): ("Q1451813", "Vipaśyin", "Vipassī, Buddha of the past", "sage"),
    ("sikhī", 1): ("Q17060571", "Śikhin", "Sikhī, Buddha of the past", "sage"),
    ("kakusandha", 1): ("Q586206", "Krakucchanda", "Kakusandha, Buddha of the past", "sage"),
    ("koṇāgamana", 1): ("Q527056", "Kanakamuni", "Koṇāgamana, Buddha of the past", "sage"),
    ("bhaddā", 3): ("Q3889040", "Bhadrā Kuṇḍalakeśā", "Bhaddā Kuṇḍalakesā, bhikkhunī", "disciple"),
    ("sāmāvatī", 1): ("Q7408914", "Śyāmāvatī", "Sāmāvatī, queen of Udena", "royal"),
    ("khujjuttarā", 1): ("Q3510814", "Kubjottarā", "Khujjuttarā, laywoman disciple", "disciple"),
    ("soṇa", 2): ("Q11315531", "Śroṇa Koṭiviṃśa", "Soṇa Koḷivisa, monk", "disciple"),
    ("yasa", 1): ("Q1000808", "Yaśas", "Yasa, early disciple", "disciple"),
    ("cunda", 1): ("Q5194211", None, "Cunda the smith", "human"),
    ("sañjaya", 3): ("Q1229185", "Sañjayin Vairaṭṭīputra", "Sañjaya Belaṭṭhiputta, teacher", "human"),
    ("makkhali", 1): ("Q2701335", "Maskarin Gośālīputra", "Makkhali Gosāla, teacher", "human"),
    ("pūraṇa kassapa", 1): ("Q6142462", "Pūraṇa Kāśyapa", "Pūraṇa Kassapa, teacher", "human"),
    ("ajitakesakambala", 1): ("Q153187", "Ajita Keśakambala", "Ajita Kesakambala, teacher", "human"),
    ("pakudha", 1): ("Q6135087", "Kakuda Kātyāyana", "Pakudha Kaccāyana, teacher", "human"),
    ("vepacitti", 1): ("Q3538740", "Vemacitrin", "Vepacitti, asura chief", "mythological_being"),
    ("virūḷha", 1): ("Q1188515", "Virūḍhaka", "Virūḷhaka, Great King of the south", "deity"),
    ("virūpakkha", 1): ("Q1188714", "Virūpākṣa", "Virūpakkha, Great King of the west", "deity"),
    ("dhataraṭṭha", 1): ("Q1188767", "Dhṛtarāṣṭra", "Dhataraṭṭha, Great King of the east", "deity"),
    ("uruvelākassapa", 1): ("Q11387712", "Uruvilvā-Kāśyapa", "Uruvelā Kassapa, disciple", "disciple"),
    ("mahāpanthaka", 1): ("Q140352614", "Mahāpanthaka", "Mahāpanthaka, arahant", "disciple"),
    ("cūḷapanthaka", 1): (None, "Cūḍapanthaka", "Cūḷapanthaka, arahant", "disciple"),
    ("sīvali", 1): ("Q225037", "Śīvali", "Sīvali, monk", "disciple"),
    ("puṇṇa", 4): (None, "Pūrṇa Maitrāyaṇīputra", "Puṇṇa Mantāniputta, disciple", "disciple"),
    ("isidāsī", 1): (None, "Ṛṣidāsī", "Isidāsī, bhikkhunī", "disciple"),
}
SKIP_KEYS = {"buddha"}  # duplicate of Gotama with only titles
TITLE_ALIASES = {"buddha", "tathāgata", "bhagavā", "sugata", "satthā"}
PERSONAL_ALIASES = {"moggallāna", "kolita", "yasodharā", "bimbā", "siddhattha", "gotamī", "pajāpatī", "mahāmāyā",
                    "kaccāna", "kaccāyana", "upatissa", "koṇḍañña", "āḷāra", "kālāma", "rāmaputta", "pippali",
                    "kubera", "vessavaṇa", "seniya", "bhāradvāja", "ahiṁsaka", "kesakambala", "gosāla"}
EXTRA_ALIASES = {("kuvera", 1): ["Vessavaṇa"]}
# commentarial names that the sutta texts use for someone else: never counted for this figure
NOT_IN_TEXT = {("gotama", 1, "siddhattha"), ("gotama", 1, "aṅgīrasa")}  # DN 3 Aṅgīrasa is an ancient seer
# ambiguous forms whose first sutta occurrence was checked by hand to be this figure
FIRST_OK = {("gotama", "gotama"), ("gotama", "sakyamunī"), ("mahāmoggallāna", "moggallāna"),
            ("mahāmoggallāna", "kolita"), ("rāhulamātā", "yasodharā")}
# figures DPPN (SuttaCentral edition) lacks; cited where the curated sutta places them
EXTRA_FIGURES = [
    dict(head="Metteyya", qid="Q193461", skt="Maitreya", label="Metteyya, the future Buddha", et="bodhisattva",
         within="dn26", count=False),
    dict(head="Vessabhū", qid="Q7923332", skt="Viśvabhū", label="Vessabhū, Buddha of the past", et="sage",
         within="dn14", count=False),
    dict(head="Dīpaṅkara", qid="Q1227131", skt="Dīpaṃkara", label="Dīpaṅkara, Buddha of the past", et="sage",
         within=None, count=True),
    dict(head="Siddhattha", qid=None, skt="Siddhārtha", label="Siddhattha, Buddha of the past (Bv 17)", et="sage",
         within="bv", count=True, sex_from="DPPN-less; Bv"),
]
# extra exclusions of forms that are mostly ordinary words
EXCLUDE_FORMS = {"sakka": {"sakkā", "sakka", "sakkaṁ", "sakke", "sakkāya", "sakkehi", "sakkesu", "sakkānaṁ"}}
PIN_FIRST = {"ānanda": "dn1:3.74.1"}  # dn1:1.6.3 has ānando 'joy'; checked by hand
KEEP_COUNT = {"ānanda", "gotama", "māra", "sakka"}  # common-word homographs where the name use dominates

# ----------------------------------------------------------------------------------------------- Mahayana
MAHAYANA_TEXTS = [
    dict(id="lotus", file="sa_saddharmapuNDarIkasUtra", corpus="Lotus Sutra",
         edition="Saddharmapuṇḍarīkasūtra, ed. P.L. Vaidya 1960"),
    dict(id="heart", file="sa_prajJApAramitAhRdayasUtra", corpus="Heart Sutra", edition="Prajñāpāramitāhṛdayasūtra"),
    dict(id="diamond", file="sa_vajracchedikA-prajJApAramitA", corpus="Diamond Sutra",
         edition="Vajracchedikā Prajñāpāramitā, ed. P.L. Vaidya 1961"),
    dict(id="larger", file="sa_sukhAvatIvyUha", corpus="Larger Sukhavativyuha", edition="Sukhāvatīvyūha (larger)"),
    dict(id="smaller", file="sa_smaller-sukhAvatIvyUha", corpus="Smaller Sukhavativyuha",
         edition="Sukhāvatīvyūha (smaller)"),
    dict(id="vkn", file="sa_vimalakIrtinirdeza", corpus="Vimalakirti Nirdesha",
         edition="Vimalakīrtinirdeśa, Taisho University 2006 (Potala manuscript)"),
]
L = "a-zāīūṛṝḷṃṁḥñṅṇṭḍśṣ"
NB = rf"(?![{L}])"  # no letter follows
# key, IAST citation form, pattern, Pali DPPN link (key, sense) or QID, entity_type, name_role, label, relation
MAHAYANA_FIGURES = [
    ("shakyamuni", "Śākyamuni", r"śākyamun", ("gotama", 1), "sage", "epithet", None, "epithet of the Buddha Gautama (Pali Sakyamunī)"),
    ("avalokiteshvara", "Avalokiteśvara", r"[āa]valokiteśvar", "Q193849", "bodhisattva", "personal", "Avalokiteśvara, bodhisattva", None),
    ("manjushri", "Mañjuśrī", r"mañjuśr|mañjuśir", "Q471696", "bodhisattva", "personal", "Mañjuśrī, bodhisattva", None),
    ("amitabha", "Amitābha", r"(?<![sś])amitābh|'mitābh", "Q236242", "sage", "personal", "Amitābha Buddha", None),
    ("amitayus", "Amitāyus", r"amitāyu", "Q236242", "sage", "epithet", "Amitābha Buddha", "another name of Amitābha"),
    ("maitreya", "Maitreya", r"maitrey", "Q193461", "bodhisattva", "personal", "Maitreya, the future Buddha", "Sanskrit form of Pali Metteyya"),
    ("ajita", "Ajita", rf"(?<!pravr)(?<!aśv)(?<![{L}]r)ajit(?:a|aḥ|o|ena|asya){NB}", "Q193461", "bodhisattva", "epithet", "Maitreya, the future Buddha", "epithet of Maitreya"),
    ("samantabhadra", "Samantabhadra", r"samantabhadr", "Q868306", "bodhisattva", "personal", "Samantabhadra, bodhisattva", None),
    ("vimalakirti", "Vimalakīrti", r"vimalakīrt(?!inirdeś)", "Q2502143", "human", "personal", "Vimalakīrti, Licchavi layman", None),
    ("subhuti", "Subhūti", r"subh[uū]t(?:i|e|ir|iḥ|iṃ|im|is|iś|in|inā|eḥ|er){NB}".replace("{NB}", NB), ("subhūti", 1), "disciple", "personal", None, "Sanskrit form of Pali Subhūti"),
    ("shariputra", "Śāriputra", r"(?:ś|ch)āriputr|śāradvatīputr", ("sāriputta", 1), "disciple", "personal", None, "Sanskrit form of Pali Sāriputta"),
    ("maudgalyayana", "Mahāmaudgalyāyana", r"maudgalyāyan", ("mahāmoggallāna", 1), "disciple", "personal", None, "Sanskrit form of Pali Mahāmoggallāna"),
    ("mahakashyapa", "Mahākāśyapa", r"mahākāśyap", ("mahākassapa", 1), "disciple", "personal", None, "Sanskrit form of Pali Mahākassapa"),
    ("mahakatyayana", "Mahākātyāyana", r"(?:mahā|bhadanta)kātyāyan", ("mahākaccāyana", 1), "disciple", "personal", None, "Sanskrit form of Pali Mahākaccāna"),
    ("purna", "Pūrṇa Maitrāyaṇīputra", r"maitrāyaṇīputr", ("puṇṇa", 4), "disciple", "personal", None, "Sanskrit form of Pali Puṇṇa Mantāniputta"),
    ("ananda", "Ānanda", rf"(?<!mah)ānand(?:a|aḥ|o|ena|asya|am|aṃ|as|aś|abhadr\w*|arāhul\w*){NB}", ("ānanda", 1), "disciple", "personal", None, "Sanskrit form of Pali Ānanda"),
    ("rahula", "Rāhula", r"rāhul(?!amāt)", ("rāhula", 1), "disciple", "personal", None, "Sanskrit form of Pali Rāhula"),
    ("yashodhara", "Yaśodharā", r"yaśodhar", ("rāhulamātā", 1), "human", "personal", None, "Sanskrit form of Pali Yasodharā"),
    ("mahaprajapati", "Mahāprajāpatī", r"mahāprajāpat", ("mahāpajāpatī", 1), "disciple", "personal", None, "Sanskrit form of Pali Mahāpajāpatī"),
    ("devadatta", "Devadatta", r"devadatt", ("devadatta", 1), "disciple", "personal", None, "Sanskrit form of Pali Devadatta"),
    ("aniruddha", "Aniruddha", rf"(?<![{L}])aniruddh(?:o|ena|am|aṃ|a|aḥ){NB}", ("anuruddha", 1), "disciple", "personal", None, "Sanskrit form of Pali Anuruddha"),
    ("upali", "Upāli", rf"upāl(?:i|ir|iḥ|im|iṃ|e|inā|eḥ){NB}", ("upāli", 1), "disciple", "personal", None, "Sanskrit form of Pali Upāli"),
    ("kaundinya", "Ājñātakauṇḍinya", r"kauṇḍiny", ("aññātakoṇḍañña", 1), "disciple", "personal", None, "Sanskrit form of Pali Aññāsi Koṇḍañña"),
    ("ajatashatru", "Ajātaśatru", r"ajātaśatr", ("ajātasattu", 1), "royal", "personal", None, "Sanskrit form of Pali Ajātasattu"),
    ("anathapindada", "Anāthapiṇḍada", r"(?:a|')nāthapiṇḍad", ("anāthapiṇḍika", 1), "human", "personal", None, "Sanskrit form of Pali Anāthapiṇḍika"),
    ("shakra", "Śakra", rf"śakr(?:o|aḥ|as|aś|eṇa|asya|a|aṃ|am|abrahm\w*){NB}", ("sakka", 1), "deity", "divine", None, "Sanskrit form of Pali Sakka"),
    ("sahampati", "Sahāṃpati", r"sahāṃpat|sahāpat", ("sahampati", 1), "deity", "divine", None, "Sanskrit form of Pali Sahampati"),
    ("vaishravana", "Vaiśravaṇa", r"vaiśravaṇ", ("kuvera", 1), "deity", "divine", None, "Sanskrit form of Pali Vessavaṇa"),
    ("dhritarashtra", "Dhṛtarāṣṭra", r"dhṛtarāṣṭr", ("dhataraṭṭha", 1), "deity", "divine", None, "Sanskrit form of Pali Dhataraṭṭha"),
    ("virudhaka", "Virūḍhaka", r"virūḍhak", ("virūḷha", 1), "deity", "divine", None, "Sanskrit form of Pali Virūḷhaka"),
    ("virupaksha", "Virūpākṣa", r"virūpākṣ", ("virūpakkha", 1), "deity", "divine", None, "Sanskrit form of Pali Virūpakkha"),
    ("dipamkara", "Dīpaṃkara", r"dīpaṃkar|dīpaṅkar", "Q1227131", "sage", "personal", "Dīpaṅkara, Buddha of the past", "Sanskrit form of Pali Dīpaṅkara"),
    ("bhaishajyaraja", "Bhaiṣajyarāja", r"bhaiṣajyarāj(?!asamudgat)", "Q4900820", "bodhisattva", "personal", "Bhaiṣajyarāja, bodhisattva", None),
    ("prabhutaratna", "Prabhūtaratna", r"prabhūtaratn(?!astada kalpu)(?!o nāma kalpo)(?!e kalpe)", "Q1815876", "sage", "personal", "Prabhūtaratna, Buddha of the past", None),
    ("mahasthamaprapta", "Mahāsthāmaprāpta", r"mahāsthām", "Q1465683", "bodhisattva", "personal", "Mahāsthāmaprāpta, bodhisattva", None),
    ("akshobhya", "Akṣobhya", r"akṣobhy", "Q756612", "sage", "personal", "Akṣobhya Buddha", None),
    ("dharmakara", "Dharmākara", rf"dharmākar(?:o|aḥ|eṇa|asya|a|aṃ|am|as|aś){NB}", "Q18649372", "bodhisattva", "personal", "Dharmākara, the monk who became Amitābha", None),
    ("lokeshvararaja", "Lokeśvararāja", r"lokeśvararāj", "Q6668652", "sage", "personal", "Lokeśvararāja, Buddha of the past", None),
    ("sadaparibhuta", "Sadāparibhūta", r"sadāparibhūt", "Q1544983", "bodhisattva", "personal", "Sadāparibhūta, bodhisattva", None),
    ("gadgadasvara", "Gadgadasvara", r"gadgadasvar", "Q17023782", "bodhisattva", "personal", "Gadgadasvara, bodhisattva", None),
    ("akshayamati", "Akṣayamati", r"akṣayamat", "Q17039583", "bodhisattva", "personal", "Akṣayamati, bodhisattva", None),
    ("vishishtacharitra", "Viśiṣṭacāritra", r"viśiṣṭacāritr", None, "bodhisattva", "personal", "Viśiṣṭacāritra, bodhisattva", None),
    ("candrasuryapradipa", "Candrasūryapradīpa", r"candrasūryapradīp", None, "sage", "personal", "Candrasūryapradīpa, Buddha of the past", None),
    ("mahabhijnajnanabhibhu", "Mahābhijñājñānābhibhū", r"mahābhijñājñānābhibh", None, "sage", "personal", "Mahābhijñājñānābhibhū, Buddha of the past", None),
    ("shubhavyuha", "Śubhavyūha", r"śubhavyūh", None, "royal", "personal", "Śubhavyūha, king (Lotus Sutra ch. 25)", None),
    ("sagara", "Sāgara", r"sāgar(?:a|asya|o|aḥ|eṇa)?\s?nāgarāj", None, "mythological_being", "personal", "Sāgara, nāga king", None),
    ("ratnakara", "Ratnākara", rf"ratnākar(?:o|aḥ|a|eṇa|āya|asya){NB}", None, "human", "personal", "Ratnākara, Licchavi youth (Vimalakīrtinirdeśa)", None),
    ("gandhahastin", "Gandhahastin", r"gandhahast", None, "bodhisattva", "personal", "Gandhahastin, bodhisattva", None),
    ("nityodyukta", "Nityodyukta", r"nityodyukt", None, "bodhisattva", "personal", "Nityodyukta, bodhisattva", None),
]
# texts where a pattern is known to hit something else
MAHAYANA_SKIP = {("ratnakara", "larger"), ("ratnakara", "lotus"), ("dharmakara", "lotus"),
                 ("ajita", "vkn"),          # Ajita Keśakambala there
                 ("akshobhya", "larger"),   # akṣobhya as a numeral
                 ("shubhavyuha", "vkn")}    # a Brahmā of that name


def mahayana_sections(tid, text):
    """-> list of (start_offset, section label for text column, passage, anchor) in document order."""
    out = []
    if tid == "lotus":
        for m in re.finditer(r"saddhp_(\d+):\s*([^|\n]+)", text):
            out.append((m.start(), f"Chapter {m.group(1)} ({m.group(2).strip()})", f"Lotus Sutra ch. {m.group(1)}"))
    elif tid == "vkn":
        for m in re.finditer(r"vkn (\d+)\.(\d+)", text):
            out.append((m.start(), f"Chapter {m.group(1)}", f"Vimalakīrtinirdeśa {m.group(1)}.{m.group(2)}"))
    elif tid == "diamond":
        out.append((0, "Vajracchedikā", "Vajracchedikā, Vaidya p. 75"))
        for m in re.finditer(r"\(vajr, vaidya (\d+)\)", text):
            out.append((m.start(), "Vajracchedikā", f"Vajracchedikā, Vaidya p. {m.group(1)}"))
    elif tid == "larger":
        for m in re.finditer(r"(?<![\w'])p(\d+)(?!\w)", text):
            out.append((m.start(), "Sukhāvatīvyūha", f"Sukhāvatīvyūha p. {m.group(1)}"))
    elif tid == "smaller":
        prev = 0
        for m in re.finditer(r"//(\d+)//", text):  # section number closes the section
            out.append((prev, "Sukhāvatīvyūha (smaller)", f"Smaller Sukhāvatīvyūha §{m.group(1)}"))
            prev = m.end()
    elif tid == "heart":
        out.append((0, "Prajñāpāramitāhṛdaya", "Heart Sutra"))
    return out


def section_at(secs, off):
    best = secs[0] if secs else (0, "", "")
    for s in secs:
        if s[0] <= off:
            best = s
        else:
            break
    return best


# ----------------------------------------------------------------------------------------------- build
def row(**kw):
    r = dict.fromkeys(COLS, "")
    r.update(kw)
    return r


def main():
    fetch()
    t0 = time.time()
    corpus = Corpus()
    print(f"Pali corpus: {len(corpus.segs)} segments, {len(corpus.tok)} distinct tokens ({time.time() - t0:.0f}s)")
    ncped = {pali_norm(e["entry"]) for e in json.load(open(os.path.join(SCDATA, "dictionaries", "simple", "en", "pli2en_ncped.json"), encoding="utf-8"))}
    dpd_common, dpd_gender = dpd_lexicon()
    ncped |= dpd_common
    senses = [s for s in dppn_senses() if s["cls"] in ("person", "place") and s["key"] not in SKIP_KEYS]
    qids = [v[0] for v in CURATED.values() if v[0]] + [f["qid"] for f in EXTRA_FIGURES if f["qid"]] + \
           [f[3] for f in MAHAYANA_FIGURES if isinstance(f[3], str)]
    wd = wikidata(qids)

    # how many DPPN senses carry each form (head or alias)
    holders = collections.Counter()
    for s in senses:
        for f in {pali_norm(s["head"])} | {pali_norm(a) for a in s["alias"]}:
            holders[f] += 1

    rows, fig_of = [], {}
    joined = {}  # head written together with an alias: piṇḍolabhāradvājo (Thag colophons)
    stats = collections.Counter()

    def forms_of(word):
        w = pali_norm(word)
        if " " in w:
            return None
        fs = inflect(w) | joined.get(w, set())
        return fs - EXCLUDE_FORMS.get(w, set())

    def locate(word):
        """-> (count, first_pos, phrase_rx or None, display form) of a name form in the corpus."""
        w = pali_norm(word)
        if " " in w:
            parts = w.split()
            wf = [inflect(p) for p in parts]
            n, first = corpus.count_phrase(wf)
            rx = re.compile(r"(?<![^\W\d_])" + r"[^\w]+".join("(?:" + "|".join(map(re.escape, f)) + ")" for f in wf) + r"(?![^\W\d_])")
            return n, first, rx, word
        fs = forms_of(w)
        n, first = corpus.count_tokens(fs)
        if n == 0 and len(w) >= 8:  # joined DPPN headword written as two words in the text (Āḷārakālāma)
            for i in range(3, len(w) - 3):
                a, b = w[:i], w[i:]
                if not (a.endswith(("a", "ā", "ī", "i", "u")) and any(f in corpus.tok for f in inflect(a)) and
                        any(f in corpus.tok for f in inflect(b))):
                    continue
                n2, first2 = corpus.count_phrase([inflect(a), inflect(b)])
                if n2:
                    disp = word[:i] + " " + word[i:i + 1].upper() + word[i + 1:]
                    rx = re.compile(r"(?<![^\W\d_])(?:" + "|".join(map(re.escape, inflect(a))) + r")[^\w]+(?:" +
                                    "|".join(map(re.escape, inflect(b))) + r")(?![^\W\d_])")
                    return n2, first2, rx, disp
        return n, first, None, word

    def verified_ref(sense, word, rx):
        """earliest DPPN reference of this sense whose Pali segment (or a near one) has the form."""
        fs = forms_of(word) or set()
        best = None
        for uid, anchor in dppn_refs(sense["text"]):
            if uid not in corpus.uid_range:
                continue
            m = re.fullmatch(r"an1\.(\d+)(?:-\d+)?", uid)
            if m and 188 <= int(m.group(1)) <= 267:  # AN 1 'foremost' lists: DPPN's anchors drift by a few suttas
                cands = range(corpus.uid_range["an1.188-197"][0], corpus.uid_range["an1.258-267"][1])
            elif anchor and f"{uid}:{anchor}" in corpus.seg_index:
                sutta = corpus.segs[corpus.seg_index[f"{uid}:{anchor}"]][0].split(":")[0]
                cands = range(*corpus.uid_range[sutta])  # anywhere in that sutta (incl. Thag/Thig colophons)
            else:
                cands = range(*corpus.uid_range[uid])
            for p in cands:
                if corpus.seg_has(p, fs, rx):
                    best = p if best is None else min(best, p)
                    break
        return best

    # ---- Pali Canon from DPPN
    for s in senses:
        key = (s["key"], s["n"])
        cur = CURATED.get(key)
        et = (cur[3] if cur and cur[3] else None) or classify(s)
        qid = cur[0] if cur else None
        is_class = bool(re.match(r"(?:the name of |name of )?(?:a|an|one) (?:class|group|race|family|clan|tribe)\b",
                                 first_sentence(s["text"]).lower()))
        sex = "" if et in ("place", "tribe", "title") or is_class else (
            (wd_sex(wd, qid) if qid else "") or dppn_sex(s) or dpd_gender.get(pali_norm(s["head"]), ""))
        slug = re.sub(r"[^a-z0-9]+", "-", latin_pali(nfc(s["head"]).replace("ā", "aa").replace("ī", "ii").replace("ū", "uu")).lower()).strip("-")
        fid = qid or f"slug:buddhist:{slug}" + (f"-{s['n']}" if s["nsenses"] > 1 else "")
        if cur:
            label = cur[2]
        else:
            d = short_desc(s, et)
            label = f"{s['head']}, {d[:1].lower() + d[1:] if d[:2] in ('A ', 'An', 'On', 'Th', 'Na') else d}"
            if s["nsenses"] > 1:
                label += f" (DPPN {s['head']} {s['n']})"
        fig_of[key] = dict(fid=fid, label=label, sex=sex, et=et, skt=cur[1] if cur else None, head=s["head"])
        forms = [(s["head"], True)] + [(a, False) for a in s["alias"] + EXTRA_ALIASES.get(key, [])]
        hw = pali_norm(s["head"])
        joined.clear()
        if " " not in hw:
            joined[hw] = {hw + f for a in s["alias"] if " " not in a for f in inflect(a)}
        for form, is_head in forms:
            lw = pali_norm(form)
            if (s["key"], s["n"], lw) in NOT_IN_TEXT:
                continue
            is_title = not is_head and lw in TITLE_ALIASES
            n, first, rx, disp = locate(form)
            if n == 0:
                stats["not_in_text"] += 1
                continue
            stem_alts = {lw, lw[:-1] + "a", lw[:-1] + "ā", lw[:-1] + "ī", lw[:-1] + "i"} if lw[-1:] in "aāīiu" else {lw}
            common = bool(stem_alts & ncped) and lw not in KEEP_COUNT and not is_title
            shared = holders[lw] > 1 and not is_title
            short = len(lw) <= 3
            ref = verified_ref(s, form, rx)
            if common or shared or short:
                if ref is not None:
                    pos, occ, conf = ref, "", 0.85
                elif (s["key"], lw) in FIRST_OK:  # first occurrence checked by hand
                    pos, occ, conf = first, "", 0.8
                else:
                    stats["ambiguous_unverified"] += 1
                    continue
            else:
                pos, occ, conf = first, n, (0.95 if ref is not None else 0.85)
                if lw in PIN_FIRST:
                    pos = corpus.seg_index[PIN_FIRST[lw]]
            if key == ("gotama", 1) and lw == "gotama":
                occ = ""  # also the clan name of many others
            c = corpus.cite(pos)
            if is_title:
                role, ret = "title", "title"
            elif is_head:
                role = "word" if et in ("place", "tribe", "title") or is_class else ("divine" if et == "deity" else "personal")
                ret = et
            else:
                role = "word" if et in ("place", "tribe", "title") or is_class else (
                    ("divine" if et == "deity" else "personal") if lw in PERSONAL_ALIASES else ("divine" if et == "deity" else "epithet"))
                ret = et
            rel = ""
            if not is_head:
                rel = f"another name of {s['head']}" if role in ("personal", "word") else f"epithet of {s['head']}"
            if cur and cur[1] and not is_title:
                skt_rel = f"Pali form of Sanskrit {cur[1]}"
                rel = f"{rel}; {skt_rel}" if rel else skt_rel
            rows.append(row(name=latin_pali(disp), figure_id=fid, figure=label, sex=fig_of[key]["sex"], original=disp,
                            translit=disp, language="Pali", tradition="Buddhist", subtradition="Theravada",
                            corpus="Pali Canon", text=c["text"], passage=c["passage"], url=c["url"], occurrences=occ,
                            entity_type=ret, name_role=role, status="attested", relation=rel,
                            source=SRC_PALI + (SRC_WD if qid else ""), confidence=conf))
            stats["pali_rows"] += 1

    # Gotama's personal name: DPPN gives Siddhattha, but in the suttas that name belongs to a Buddha of the past
    g = fig_of.get(("gotama", 1))
    if g:
        rows.append(row(name="Siddhattha", figure_id=g["fid"], figure=g["label"], sex=g["sex"], original="Siddhattha",
                        translit="Siddhattha", language="Pali", tradition="Buddhist", subtradition="Theravada",
                        corpus="Pali Canon", text="", passage="", url="https://suttacentral.net/define/gotama",
                        occurrences="", entity_type="sage", name_role="personal", status="related",
                        relation="personal name of Gotama given by DPPN (commentarial); Pali form of Sanskrit Siddhārtha; "
                                 "the Siddhattha of the canonical verses (Bv, Ap) is a Buddha of the past",
                        source=SRC_PALI + SRC_WD, confidence=0.7))

    # figures missing from SuttaCentral's DPPN
    for f in EXTRA_FIGURES:
        fs = inflect(f["head"])
        if f["within"]:
            pos = next((p for p, (_, u, low) in enumerate(corpus.segs)
                        if (u == f["within"] or re.match(re.escape(f["within"]) + r"\d", u)) and any(t in fs for t in TOK.findall(low))), None)
        else:
            pos = corpus.count_tokens(fs)[1]
        if pos is None:
            continue
        n = corpus.count_tokens(fs)[0]
        c = corpus.cite(pos)
        sex = wd_sex(wd, f["qid"]) if f["qid"] else ""
        fid = f["qid"] or f"slug:buddhist:{re.sub(r'[^a-z0-9]+', '-', latin_pali(f['head']).lower())}-past-buddha"
        key = ("extra", f["head"])
        fig_of[key] = dict(fid=fid, label=f["label"], sex=sex, et=f["et"], skt=f["skt"], head=f["head"])
        rows.append(row(name=latin_pali(f["head"]), figure_id=fid, figure=f["label"], sex=sex, original=f["head"],
                        translit=f["head"], language="Pali", tradition="Buddhist", subtradition="Theravada",
                        corpus="Pali Canon", text=c["text"], passage=c["passage"], url=c["url"],
                        occurrences=n if f["count"] else "", entity_type=f["et"], name_role="personal",
                        status="attested", relation=f"Pali form of Sanskrit {f['skt']}",
                        source="SuttaCentral bilara-data Mahāsaṅgīti Pāli (CC0); curated" + (SRC_WD if f["qid"] else ""),
                        confidence=0.9))
        stats["pali_rows"] += 1

    # ---- Mahayana sutras
    texts = {}
    for t in MAHAYANA_TEXTS:
        raw = nfc(open(os.path.join(GRETIL, t["file"] + ".txt"), encoding="utf-8").read())
        body = raw.split("\n# Text", 1)[1].lower()
        texts[t["id"]] = (t, body, mahayana_sections(t["id"], body))
    for key, iast, pat, link, et, role, label, rel in MAHAYANA_FIGURES:
        rx = re.compile(pat)
        if isinstance(link, tuple):
            f = fig_of.get(link)
            if f is None:
                print("  missing Pali link", link)
                continue
            fid, flabel, sex = f["fid"], f["label"], f["sex"]
        else:
            fid = link or f"slug:buddhist:{key}"
            flabel, sex = label, wd_sex(wd, link) if link else ""
            if link == "Q193461" and fig_of.get(("extra", "Metteyya")):
                sex = fig_of[("extra", "Metteyya")]["sex"]
        for t in MAHAYANA_TEXTS:
            if (key, t["id"]) in MAHAYANA_SKIP:
                continue
            _, body, secs = texts[t["id"]]
            hits = list(rx.finditer(body))
            if not hits:
                continue
            sec = section_at(secs, hits[0].start())
            if CHECK:
                a = hits[0].start()
                print(f"  [{t['id']}] {iast}: …{body[max(0, a - 50):a + 60]!r}…".replace("\\n", " "))
            conf = 0.95 if key not in ("ajita", "shakra", "ananda", "aniruddha", "upali", "sagara") else 0.85
            rows.append(row(name=latin_skt(iast), figure_id=fid, figure=flabel, sex=sex, original=deva(iast),
                            translit=iast, language="Sanskrit", tradition="Buddhist", subtradition="Mahayana",
                            corpus=t["corpus"], text=sec[1], passage=sec[2], url=GRETIL_HTML.format(t["file"]),
                            occurrences=len(hits), entity_type=et, name_role=role, status="attested",
                            relation=rel or "", source=f"GRETIL, {t['edition']} (CC BY-NC-SA 4.0)" + (SRC_WD if fid.startswith("Q") else ""),
                            confidence=conf))
            stats["mahayana_rows"] += 1

    # ---- dedupe and write
    seen, out = set(), []
    for r in rows:
        k = (r["original"], r["figure_id"], r["corpus"])
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\t".join(COLS) + "\n")
        for r in out:
            fh.write("\t".join(str(r[c]).replace("\t", " ").replace("\n", " ") for c in COLS) + "\n")
    by = collections.Counter(r["corpus"] for r in out)
    print(f"wrote {len(out)} rows -> {os.path.relpath(OUT, ROOT)}")
    for k, v in by.most_common():
        print(f"  {k}: {v}")
    print("  entity types:", dict(collections.Counter(r["entity_type"] for r in out).most_common()))
    print("  sex:", dict(collections.Counter(r["sex"] or "-" for r in out)))
    print("  skipped:", dict(stats))


if __name__ == "__main__":
    main()
