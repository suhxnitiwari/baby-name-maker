# Builds data/sacred/indic.tsv (and data/sacred/indic-review.tsv) in the shared format of docs/sacred-format.md:
# names attested in the Hindu epics (Bhagavad Gita, Valmiki Ramayana, Mahabharata), the Guru Granth Sahib and the
# Jain Kalpa Sutra, each with the first passage it occurs in and an occurrence count.
#
# Hindu pipeline (Sanskrit has no capital letters, so nothing here looks at case):
#   1. texts: GRETIL e-texts of the BORI critical Mahabharata (18 parvans; Bhagavad Gita = MBh 6.23-40) and of the
#      Baroda critical Valmiki Ramayana, split into cited verses.
#   2. candidates: every Monier-Williams (Cologne) headword with an "N. of", "patr. of" or "metron. of" sense; the
#      citations of that sense (MBh., R., Bhag.) tie the name to a work. Wikidata characters with "present in work"
#      (P1441) give QIDs and a second, independent work tie.
#   3. attestation: inflected forms of each candidate (by stem class, with external sandhi) are matched against the
#      verses; compound members only for unambiguous names or name-name compounds (bhīmārjuna-).
#   4. epithets: a sense "N./patr./metron. of <figure>" makes the form an epithet of that figure; if the lexicon lists
#      several figures, the one the epithet co-occurs with most in that corpus is chosen and the others are noted.
#   5. rows whose figure tie is weak, or common words (kṛṣṇa "dark", rāma "pleasing") whose occurrences are not
#      concentrated near other names, go to indic-review.tsv instead.
# Sikh: every Ang of the Guru Granth Sahib from the BaniDB API. Jain: Jacobi's Kalpa Sutra (SBE 22, 1884, public
# domain) from the archive.org scan.
#
# Raw files are downloaded to raw/sacred/ on first run (rerunnable; cached).
#   python3 scripts/build_sacred_indic.py
import collections, json, os, re, sys, time, unicodedata, urllib.parse, urllib.request, zipfile

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "raw", "sacred"); OUTDIR = os.path.join(ROOT, "data", "sacred")
OUT = os.path.join(OUTDIR, "indic.tsv"); REVIEW = os.path.join(OUTDIR, "indic-review.tsv")
COLS = ["name", "figure_id", "figure", "sex", "original", "translit", "language", "tradition", "subtradition", "corpus",
        "text", "passage", "url", "occurrences", "entity_type", "name_role", "status", "relation", "source", "confidence"]
UA = "lullabyte-sacred-names/1.0 (research; static site build)"
GRETIL = "https://gretil.sub.uni-goettingen.de/gretil/"
SRC_GRETIL_MBH = "GRETIL Mahabharata (BORI critical ed., Tokunaga/Smith e-text)"
SRC_GRETIL_R = "GRETIL Valmiki Ramayana (Baroda critical ed., Tokunaga/Smith e-text, CC BY-NC-SA 4.0)"
SRC_MW = "Monier-Williams Sanskrit-English Dictionary (Cologne CDSL, CC BY-SA 4.0)"
SRC_WD = "Wikidata (CC0)"


def fetch(url, path, data=None, headers=None):
    if os.path.exists(path) and os.path.getsize(path) > 0: return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r: body = r.read()
            open(path, "wb").write(body); return path
        except Exception as e:
            if attempt == 3: raise
            time.sleep(65 if "429" in str(e) else 2 + 3 * attempt)


# ─────────────────────────────────────────────────────────────
# Script helpers: SLP1 → IAST, IAST → Devanagari, IAST → everyday romanization, normalization for matching
# ─────────────────────────────────────────────────────────────
SLP = {"a": "a", "A": "ā", "i": "i", "I": "ī", "u": "u", "U": "ū", "f": "ṛ", "F": "ṝ", "x": "ḷ", "X": "ḹ", "e": "e", "E": "ai",
       "o": "o", "O": "au", "M": "ṃ", "H": "ḥ", "k": "k", "K": "kh", "g": "g", "G": "gh", "N": "ṅ", "c": "c", "C": "ch", "j": "j",
       "J": "jh", "Y": "ñ", "w": "ṭ", "W": "ṭh", "q": "ḍ", "Q": "ḍh", "R": "ṇ", "t": "t", "T": "th", "d": "d", "D": "dh", "n": "n",
       "p": "p", "P": "ph", "b": "b", "B": "bh", "m": "m", "y": "y", "r": "r", "l": "l", "v": "v", "S": "ś", "z": "ṣ", "s": "s", "h": "h"}

def slp2iast(s):
    return "".join(SLP.get(ch, "") for ch in s)

IAST_TOKENS = sorted(["kh", "gh", "ch", "jh", "ṭh", "ḍh", "th", "dh", "ph", "bh", "ai", "au"], key=len, reverse=True)

def iast_split(s):
    out, i = [], 0
    while i < len(s):
        for t in IAST_TOKENS:
            if s.startswith(t, i): out.append(t); i += len(t); break
        else: out.append(s[i]); i += 1
    return out

DV_V = {"a": "अ", "ā": "आ", "i": "इ", "ī": "ई", "u": "उ", "ū": "ऊ", "ṛ": "ऋ", "ṝ": "ॠ", "ḷ": "ऌ", "e": "ए", "ai": "ऐ", "o": "ओ", "au": "औ"}
DV_M = {"a": "", "ā": "ा", "i": "ि", "ī": "ी", "u": "ु", "ū": "ू", "ṛ": "ृ", "ṝ": "ॄ", "ḷ": "ॢ", "e": "े", "ai": "ै", "o": "ो", "au": "ौ"}
DV_C = {"k": "क", "kh": "ख", "g": "ग", "gh": "घ", "ṅ": "ङ", "c": "च", "ch": "छ", "j": "ज", "jh": "झ", "ñ": "ञ", "ṭ": "ट", "ṭh": "ठ",
        "ḍ": "ड", "ḍh": "ढ", "ṇ": "ण", "t": "त", "th": "थ", "d": "द", "dh": "ध", "n": "न", "p": "प", "ph": "फ", "b": "ब", "bh": "भ",
        "m": "म", "y": "य", "r": "र", "l": "ल", "v": "व", "ś": "श", "ṣ": "ष", "s": "स", "h": "ह"}

def deva(s):
    toks, out, prev_c = iast_split(s.lower()), [], False
    for t in toks:
        if t in DV_C:
            if prev_c: out.append("्")
            out.append(DV_C[t]); prev_c = True
        elif t in DV_V:
            out.append(DV_M[t] if prev_c else DV_V[t]); prev_c = False
        elif t == "ṃ": out.append("ं"); prev_c = False
        elif t == "ḥ": out.append("ः"); prev_c = False
        else: prev_c = False
    if prev_c: out.append("्")
    return "".join(out)

DV_REV = {**{v: k for k, v in DV_V.items()}}
DV_MREV = {v: k for k, v in DV_M.items() if v}
DV_CREV = {v: k for k, v in DV_C.items()}

def deva2iast(s):
    out, i = [], 0
    s = unicodedata.normalize("NFC", s)
    while i < len(s):
        ch = s[i]
        if ch in DV_CREV:
            out.append(DV_CREV[ch]); nxt = s[i + 1] if i + 1 < len(s) else ""
            if nxt == "्": i += 2; continue
            if nxt in DV_MREV: out.append(DV_MREV[nxt]); i += 2; continue
            if nxt == "़": i += 1
            out.append("a"); i += 1; continue
        if ch in DV_REV: out.append(DV_REV[ch])
        elif ch == "ं": out.append("ṃ")
        elif ch == "ः": out.append("ḥ")
        elif ch == "ँ": out.append("ṃ")
        elif ch in " -": out.append(" ")
        i += 1
    return "".join(out)

def roman(s):
    """IAST → the everyday spelling (Kṛṣṇa → Krishna, Lakṣmaṇa → Lakshmana, Sañjaya → Sanjaya)."""
    s = s.lower(); toks = iast_split(s); out = []
    for i, t in enumerate(toks):
        nxt = toks[i + 1] if i + 1 < len(toks) else ""
        if t == "ṃ": out.append("m" if nxt[:1] in ("p", "b", "m", "v") else "n")
        elif t == "ḥ": continue
        else:
            out.append({"ā": "a", "ī": "i", "ū": "u", "ṛ": "ri", "ṝ": "ri", "ḷ": "li", "ṅ": "n", "ñ": "n", "ṇ": "n", "ṭ": "t", "ṭh": "th",
                        "ḍ": "d", "ḍh": "dh", "ś": "sh", "ṣ": "sh", "c": "ch", "ch": "chh"}.get(t, t))
    r = "".join(out).replace("kshsh", "ksh")
    return r[:1].upper() + r[1:]

def fold(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if c.isalpha() and ord(c) < 128)

STOPS = "kgcjṭḍtdpbśṣsh" + "yrlv"
NASAL_RE = re.compile(r"[ṅñṇnmṃṁ](?=(?:[kgcjṭḍtdpbśṣsh]|[yrlv]))")

def norm(s):
    """Matching key: NFC, lower, every nasal before a consonant written as anusvāra (MW saṃjaya = GRETIL sañjaya)."""
    s = unicodedata.normalize("NFC", s.lower()).replace("ṁ", "ṃ")
    s = re.sub(r"[ṅñṇnmṃ](?=[kgcjṭḍtdpbśṣshyrlv])", "ṃ", s)
    # anusvāra-normalization above would also hit ordinary n before y/r/v inside words, which MW and GRETIL agree on,
    # so only class nasals and m are folded before semivowels:
    return s

def norm_word(s):
    s = unicodedata.normalize("NFC", s.lower()).replace("ṁ", "ṃ")
    s = re.sub(r"[ṅñṇnmṃ](?=[kgcjṭḍtdpbśṣsh])", "ṃ", s)
    s = re.sub(r"[mṃ](?=[yrlv])", "ṃ", s)
    return s


# ─────────────────────────────────────────────────────────────
# 1. Texts
# ─────────────────────────────────────────────────────────────
def get_texts():
    fetch(GRETIL + "1_sanskr/2_epic/mbh/mbh1-18u.zip", os.path.join(RAW, "mbh1-18u.zip"))
    mbhfile = os.path.join(RAW, "mbh", "MBH1-18U.HTM")
    if not os.path.exists(mbhfile):
        zipfile.ZipFile(os.path.join(RAW, "mbh1-18u.zip")).extractall(os.path.join(RAW, "mbh"))
    fetch(GRETIL + "1_sanskr/2_epic/mbh/ext/bhgce__u.htm", os.path.join(RAW, "bhgce.htm"))
    fetch(GRETIL + "corpustei/transformations/plaintext/sa_rAmAyaNa.txt", os.path.join(RAW, "rAmAyaNa.txt"))
    return mbhfile

PARVAN = ["Adi Parva", "Sabha Parva", "Vana Parva", "Virata Parva", "Udyoga Parva", "Bhishma Parva", "Drona Parva",
          "Karna Parva", "Shalya Parva", "Sauptika Parva", "Stri Parva", "Shanti Parva", "Anushasana Parva",
          "Ashvamedhika Parva", "Ashramavasika Parva", "Mausala Parva", "Mahaprasthanika Parva", "Svargarohana Parva"]
KANDA = ["Bala Kanda", "Ayodhya Kanda", "Aranya Kanda", "Kishkindha Kanda", "Sundara Kanda", "Yuddha Kanda", "Uttara Kanda"]

def load_corpora():
    """→ {corpus: [(citation, text_section, url, verse_text)]} in text order."""
    mbhfile = get_texts()
    C = {}
    # Bhagavad Gita (BORI text, Bhg_CC.VVV ids; speaker lines carry the verse number)
    verses, cur = collections.OrderedDict(), None
    for line in open(os.path.join(RAW, "bhgce.htm"), encoding="utf-8"):
        m = re.match(r"(.*?)\s+Bhg_(\d\d)\.(\d\d\d)([a-z]?)\s", line)
        if not m: continue
        key = (int(m.group(2)), int(m.group(3)))
        verses.setdefault(key, []).append(m.group(1))
    url = GRETIL + "1_sanskr/2_epic/mbh/ext/bhgce__u.htm"
    C["Bhagavad Gita"] = [(f"Gita {c}.{v}", f"Chapter {c}", url, " ".join(t)) for (c, v), t in verses.items()]
    # Mahabharata: constituted text only (lines carrying * or @ are apparatus passages and appendices)
    verses = collections.OrderedDict()
    for line in open(mbhfile, encoding="utf-8"):
        m = re.match(r"(\d\d),(\d\d\d)\.(\d\d\d)([a-zA-Z]*)\t(.*?)(?:<BR>)?\s*$", line)
        if not m: continue
        verses.setdefault((int(m.group(1)), int(m.group(2)), int(m.group(3))), []).append(m.group(5))
    C["Mahabharata"] = [(f"MBh {b}.{c}.{v}", PARVAN[b - 1], GRETIL + f"1_sanskr/2_epic/mbh/mbh_{b:02d}_u.htm", " ".join(t))
                        for (b, c, v), t in verses.items()]
    # Valmiki Ramayana: verse lines up to the one ending in R_k,sss.vvv
    lines, out = [], []
    text = open(os.path.join(RAW, "rAmAyaNa.txt"), encoding="utf-8").read().split("# Text", 1)[1]
    url = GRETIL + "corpustei/transformations/html/sa_rAmAyaNa.htm"
    for line in text.split("\n"):
        line = line.strip()
        if not line: continue
        m = re.search(r"\s*R_(\d),(\d\d\d)\.(\d\d\d)\s*$", line)
        if m:
            lines.append(line[:m.start()]); k, s, v = map(int, m.groups())
            out.append((f"Ramayana {k}.{s}.{v}", KANDA[k - 1], url, " ".join(lines))); lines = []
        else: lines.append(line)
    C["Valmiki Ramayana"] = out
    return C


# ─────────────────────────────────────────────────────────────
# 2. Candidates: Monier-Williams proper-name senses, Wikidata characters
# ─────────────────────────────────────────────────────────────
WORK_LS = {"MBh.": {"Mahabharata"}, "Nal.": {"Mahabharata"}, "R.": {"Valmiki Ramayana"},
           "Bhag.": {"Bhagavad Gita", "Mahabharata"}}
# Monier-Williams citation abbreviations → work keys of the later corpora (see JOBS); generic Br./Up./Pur. tie the whole genre
_BR = {"SB", "AB", "KB", "TB", "JB", "PB", "GB", "SadvB", "JUB"}
_UP = {"BAU", "ChU", "TU", "AU", "KathU", "MundU", "SvetU", "KausU", "KenaU", "IsaU", "PrasnaU", "MandU", "MaitrU"}
_PUR = {"BhP", "UG", "VP", "DM", "DBhP", "SivaP", "BrahmaP", "GarP", "AgniP", "KurmaP", "LingaP", "MatsyaP", "SkP", "SkRkh",
        "VarP", "NarasP", "KalP", "HV"}
WORK_LS.update({
    "RV.": {"RV"}, "AV.": {"AV"}, "AV.Paipp.": {"AVP"}, "Paipp.": {"AVP"}, "VS.": {"VS"}, "TS.": {"TS"}, "MaitrS.": {"MS"},
    "Kāṭh.": {"KS"}, "ŚBr.": {"SB"}, "AitBr.": {"AB"}, "KauṣBr.": {"KB"}, "ŚāṅkhBr.": {"KB"}, "TBr.": {"TB"}, "JaimBr.": {"JB"},
    "PañcavBr.": {"PB"}, "TāṇḍyaBr.": {"PB"}, "TāṇḍBr.": {"PB"}, "GopBr.": {"GB"}, "ṢaḍvBr.": {"SadvB"}, "JaimUp.": {"JUB"},
    "Br.": _BR, "AitĀr.": {"AA"}, "TĀr.": {"TA"}, "ŚāṅkhĀr.": {"SA"}, "KauṣĀr.": {"SA"},
    "BṛĀrUp.": {"BAU"}, "ChUp.": {"ChU"}, "TUp.": {"TU"}, "AitUp.": {"AU"}, "KaṭhUp.": {"KathU"}, "MuṇḍUp.": {"MundU"},
    "ŚvetUp.": {"SvetU"}, "KauṣUp.": {"KausU"}, "KenUp.": {"KenaU"}, "ĪśUp.": {"IsaU"}, "PraśnUp.": {"PrasnaU"},
    "MāṇḍUp.": {"MandU"}, "MaitrUp.": {"MaitrU"}, "Up.": _UP,
    "Hariv.": {"HV"}, "BhP.": {"BhP", "UG"}, "VP.": {"VP"}, "MārkP.": {"DM"}, "Devīm.": {"DM"}, "ŚivaP.": {"SivaP"},
    "BrahmaP.": {"BrahmaP"}, "AgniP.": {"AgniP"}, "KūrmaP.": {"KurmaP"}, "LiṅgaP.": {"LingaP"}, "MatsyaP.": {"MatsyaP"},
    "SkandaP.": {"SkP", "SkRkh"}, "VarP.": {"VarP"}, "NarasP.": {"NarasP"}, "KālP.": {"KalP"}, "KālikāP.": {"KalP"},
    "Pur.": _PUR, "Gīt.": {"GG"}, "Yogas.": {"YS"}, "Mn.": {"Manu"}, "Yājñ.": {"Yajn"}, "Nār.": {"Narada"},
    "AṣṭāvS.": {"Ashtav"}, "Aṣṭāv.": {"Ashtav"}, "Pañcar.": {"Satvata"},
})

def ls_works(t):
    out = set()
    for ab, ws in WORK_LS.items():
        if t == ab or t.startswith(ab + " ") or re.match(re.escape(ab) + r"\s*[ivxlc\d]", t): out |= ws
    return out
SKIP_SENSE = re.compile(r"\b(work|treatise|hymn|S[āa]man|metre|Upaniṣad|Tantra|Purāṇa|drama|poem|commentary|lexicon|grammar|"
                        r"plant|tree|shrub|grass|flower|fruit|medicinal|disease|fever|mantra|formula|verse|rite|ceremony|"
                        r"sacrifice|Ekāha|Ahīna|Sattra|chapter|section|Adhyāya|Parvan|book|school|Śākhā|text|prayer|"
                        r"musical|Rāga|measure|mode|perfume|gem|jewel|mineral|fish|insect)(?:s|es)?\b", re.I)
TYPE_RULES = [
    ("place", r"\b(river|stream|mountain|mount|hill|town|city|country|district|forest|wood|lake|pond|place|Tīrtha|tīrtha|"
              r"region|village|hermitage|island|Dvīpa|Varṣa|ocean|sea|cave|grove|capital|kingdom|land|sacred bathing|peak|summit)\b"),
    ("tribe", r"\b(people|peoples|race|tribe|tribes|family|dynasty|clan|caste)\b"),
    ("demon", r"\b(Dānava|Daitya|Asura|Rākṣasa|Rākṣasī|Rakṣas|demon|demoness|Piśāca|Rāksasa|evil spirit)\b"),
    ("mythological_being", r"\b(Nāga|serpent|snake|Gandharva|Apsaras|Yakṣa|Yakṣī|Kiṃnara|Kinnara|Vidyādhara|Garuḍa|"
                           r"attendant of|Mātṛ|Mother|monkey|monkey-chief|bear|vulture|elephant|horse|bull|cow|Kumāra|"
                           r"Piśācī|spirit|being)\b"),
    ("deity", r"\b(god|goddess|deity|Deva|Devī|Viśve Devās|Āditya|Ādityas|Rudra|Rudras|Marut|Maruts|Vasu|Vasus|Aśvin|"
              r"Prajāpati|divinity|personified|Avatār|incarnation)\b"),
    ("sage", r"\b(Ṛṣi|Ṛishi|Rishi|Muni|sage|seer|Brāhman|ascetic|teacher|preceptor|Purohita|priest|hermit|Yogin)\b"),
    ("royal", r"\b(king|prince|princess|queen|monarch|Rāja|Rājan)\b"),
    ("concept", r"\b(bow|conch|conch-shell|weapon|sword|chariot|banner|arrow|club|discus|missile|disk)\b"),
    ("human", r"\b(son|daughter|wife|mother|father|brother|sister|man|woman|warrior|minister|charioteer|hero|descendant|"
              r"grandson|chief|leader|servant|maid|nurse|physician|merchant|Kshatriya|Kṣatriya|Śūdra|Vaiśya)\b"),
]
TYPE_RES = [(t, re.compile(p)) for t, p in TYPE_RULES]

def strip_tags(s):
    s = re.sub(r"<ls[^>]*>.*?</ls>", "", s)
    s = re.sub(r"<s>.*?</s>", "", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&amp;", "&").replace("&c.", "").replace("<", "").replace(">", "")
    return re.sub(r"\s+", " ", s).strip(" ,;")

def sense_type(txt):
    txt = re.sub(r"\s*\((?:[^()]|\([^()]*\))*\)", "", txt)      # parentheticals describe relatives, not the bearer
    for t, rx in TYPE_RES:
        if rx.search(txt): return t
    return ""

def load_mw():
    """→ {lemma(IAST): {"senses": [...], "ambiguous": bool, "lex": set}} for headwords with a proper-name sense."""
    zp = fetch("https://www.sanskrit-lexicon.uni-koeln.de/scans/MWScan/2020/downloads/mwxml.zip", os.path.join(RAW, "mwxml.zip"))
    xml = os.path.join(RAW, "mw", "xml", "mw.xml")
    if not os.path.exists(xml): zipfile.ZipFile(zp).extractall(os.path.join(RAW, "mw"))
    groups = collections.defaultdict(list)                 # key1 → [(lex, body)]
    for line in open(xml, encoding="utf-8"):
        m = re.match(r"<(H\d[A-Z]?)><h><key1>([^<]+)</key1>.*?<body>(.*)</body>", line)
        if not m: continue
        body = m.group(3)
        lx = re.findall(r'<info lex="([^"]+)"/>', body)
        groups[m.group(2)].append((lx[0] if lx else "", body))
    out, common = {}, set()
    for key, recs in groups.items():
        lemma = slp2iast(key)
        if len(lemma) < 2: continue
        senses, nonname, in_name, cur_lex, prev_works = [], 0, False, "", set()
        for lx, body in recs:
            if lx and lx != "inh": cur_lex = lx
            head = re.sub(r"^\s*(<hom>[^<]*</hom>)?\s*(<s>[^<]*</s>)?\s*(\(<s>[^<]*</s>\),?)?\s*(<lex>[^<]*</lex>)?\s*", "", body)
            is_n = bool(re.search(r"<ab>(N|patr|metron)\.</ab>", body))
            cont = in_name and lx == "inh" and re.match(r"\s*(of|<ab>du\.</ab>|<ab>pl\.</ab>)\b", head)
            # "‘exciting men’, Viṣṇu or Kṛṣṇa" / "‘thick-haired’, the hero Arjuna": a gloss followed by the figure it names
            gm = None
            if not is_n and cur_lex in ("m", "f"):
                gm = re.search(r"’,?\s*(?:\([^)]*\),?\s*)?(?:the\s+(?:hero|god|goddess|sage|king|demon|monkey)\s+)?"
                               r"((?:<s1>[^<]+</s1>(?:\s*(?:or|and|,)\s*)?)+)\s*(?:,|<ls|<info|$)", body)
            works = set()
            for ls in re.findall(r'<ls(?: n="([^"]*)")?>([^<]*)</ls>', body):
                t = (ls[0] + " " + ls[1]).strip()
                if t == "ib." or t.startswith("ib. "): works |= prev_works        # ibidem: the previous citation
                works |= ls_works(t)
            if re.search(r"<ls", body): prev_works = set(works)
            # "(personified as the daughter of heaven …)": Uṣas, Rātri — a deity the lexicon does not mark "N. of"
            if not is_n and cur_lex in ("m", "f") and re.search(r"personified|<ab>personif\.</ab>", body) and lx != "inh":
                senses.append({"txt": strip_tags(body), "works": works, "kind": "name", "targets": [], "esp": None, "qual": "",
                               "mentions": [], "lex": cur_lex, "type": "deity", "plural": False, "personified": True})
                nonname += 1                       # the word itself is an ordinary noun
                continue
            if gm:
                tg = re.findall(r"<s1>([^<]+)</s1>", gm.group(1))
                senses.append({"txt": strip_tags(body), "works": works, "kind": "epithet", "targets": tg, "esp": None, "qual": "",
                               "mentions": [norm_word(x.replace("-", "").replace("—", "")) for x in tg],
                               "lex": cur_lex, "type": "", "plural": False})
                in_name = True
                continue
            if is_n or cont:
                in_name = True
                txt = strip_tags(body)
                kind = "epithet" if re.search(r"<ab>(patr|metron)\.</ab>", body) else "name"
                # targets: "N. of <s1>X</s1>" / "patr. of <s1>X</s1>" / "N. of X, Y and Z"
                targets, esp = [], None
                tm = re.search(r"<ab>(?:N|patr|metron)\.</ab>\s*(?:<ab>fr\.</ab>\s*<s1>[^<]*</s1>,?\s*<ab>N\.</ab>\s*)?of\s+((?:<s1>[^<]+</s1>(?:,?\s*(?:or|and|,)?\s*)?)+)", body)
                if tm:
                    after = body[tm.end():tm.end() + 3]
                    if not after.startswith("'s") and not after.startswith("’s"):
                        # adjacent names are one name ("Arjuna Kārtavīrya"), not two figures
                        targets = re.findall(r"<s1>([^<]+)</s1>", re.sub(r"</s1>\s+<s1>", " ", tm.group(1)))
                    e = re.search(r"<ab>esp\.</ab>\s*of the last", body)
                    if e and targets: esp = targets[-1]
                    rest = body[tm.end():]          # "patr. of Aja, of Daśa-ratha, and (esp.) of Rāma-candra"
                    while targets:
                        m2 = re.match(r"\s*,?\s*(?:and\s+|or\s+)?(\(<ab>esp\.</ab>\)\s*)?of\s+<s1>([^<]+)</s1>", rest)
                        if not m2 or rest[m2.end():m2.end() + 2] in ("'s", "’s"): break
                        targets.append(m2.group(2))
                        if m2.group(1): esp = m2.group(2)
                        rest = rest[m2.end():]
                if not targets and cont:
                    cm = re.match(r"\s*of\s+((?:<s1>[^<]+</s1>(?:,?\s*(?:or|and)?\s*)?)+)", head)
                    if cm and not body[body.find(cm.group(1)) + len(cm.group(1)):].lstrip().startswith(("'s", "’s")):
                        targets = re.findall(r"<s1>([^<]+)</s1>", cm.group(1))
                qual = ""
                if len(targets) == 1:      # "patr. of Arjuna (a prince of the Haihayas)": a namesake, not the famous one
                    pos = body.find("<s1>" + targets[0] + "</s1>")
                    rest = body[pos + len(targets[0]) + 9:] if pos >= 0 else ""
                    qm = re.match(r"\s*\(([^()]*)\)", rest)
                    if qm: qual = strip_tags(qm.group(1))
                if targets and kind == "name": kind = "epithet"
                if kind == "epithet" and not targets: kind = "name"
                if SKIP_SENSE.search(txt.split(",")[0] if kind == "name" else "") and not targets: continue
                plural = "<ab>pl.</ab>" in body[:200]
                senses.append({"txt": txt, "works": works, "kind": kind, "targets": targets, "esp": esp, "qual": qual,
                               "mentions": [norm_word(x.replace("-", "").replace("—", "")) for x in re.findall(r"<s1>([^<]+)</s1>", body)],
                               "lex": cur_lex, "type": sense_type(txt) or ("tribe" if plural else ""), "plural": plural})
            else:
                in_name = False
                cites = [x for x in re.findall(r"<ls(?: n=\"[^\"]*\")?>([^<]*)</ls>", body) if x.strip() not in ("L.", "W.", "MW.", "Cat.", "ib.")]
                if cites and "<bot>" not in body and not re.search(r"\b(metre|q\.\s*v\.|See)\b", body):
                    nonname += 1
        if nonname or any(lx == "m:f:n" for lx, _ in recs): common.add(norm_word(lemma))
        if senses:
            out[lemma] = {"key": key, "senses": senses, "ambiguous": nonname > 0}
    return out, common

def wd_type(insts, desc):
    """Entity type from Wikidata instance-of labels (description only to tell kings and sages from other people)."""
    i = insts.lower(); d = desc.lower()
    if re.search(r"(^|\|)(hindu deity|deity|god|goddess|devi|river god|[a-z ]+ deity)(\||$)", i): return "deity"
    if "avatar" in i and "character" not in i: return "deity"
    if re.search(r"rakshasa|asura|daitya|demon", i): return "demon"
    if re.search(r"serpent|nāga|naga|yakṣa|yaksha|apsara|bird|ape|hybrid|dragon|mythical entity", i): return "mythological_being"
    if re.search(r"city|forest|country|temple|river|mountain|kingdom", i): return "place"
    if re.search(r"bow|weapon", i): return "concept"
    if re.search(r"group of|twins|couple", i) or re.search(r"\b(creatures|race|tribe|clan|people|dynasty)\b", d): return "tribe"
    if re.search(r"\b(king|queen|prince|princess|ruler)\b", d) or "mythological king" in i: return "royal"
    if re.search(r"\b(sage|rishi|ṛṣi|seer)\b", d) or "rishi" in i: return "sage"
    return "human"

WD_WORK = {"Q8276": "Mahabharata", "Q37293": "Valmiki Ramayana", "Q46802": "Bhagavad Gita"}
def load_wikidata():
    path = os.path.join(RAW, "wikidata_epics.json")
    q = """SELECT ?item ?work ?enLabel ?mulLabel ?saLabel ?hiLabel ?sex ?desc (GROUP_CONCAT(DISTINCT ?alias; separator="|") AS ?aliases)
      (GROUP_CONCAT(DISTINCT ?enAlias; separator="|") AS ?enAliases)
      (GROUP_CONCAT(DISTINCT ?instLabel; separator="|") AS ?insts) WHERE {
      VALUES (?work ?cls) { (wd:Q8276 wd:Q19896979) (wd:Q37293 wd:Q55607025) (wd:Q46802 wd:Q46802) (wd:Q422848 wd:Q422848) }
      { ?item wdt:P1441 ?work . } UNION { ?item wdt:P31 ?cls . }      # "present in work", or "character in the …" classes
      OPTIONAL { ?item rdfs:label ?enLabel FILTER(lang(?enLabel)="en") }
      OPTIONAL { ?item rdfs:label ?mulLabel FILTER(lang(?mulLabel)="mul") }
      OPTIONAL { ?item rdfs:label ?saLabel FILTER(lang(?saLabel)="sa") }
      OPTIONAL { ?item rdfs:label ?hiLabel FILTER(lang(?hiLabel)="hi") }
      OPTIONAL { ?item wdt:P21 ?sex }
      OPTIONAL { ?item skos:altLabel ?alias FILTER(lang(?alias) IN ("sa","hi")) }
      OPTIONAL { ?item skos:altLabel ?enAlias FILTER(lang(?enAlias)="en") }
      OPTIONAL { ?item schema:description ?desc FILTER(lang(?desc)="en") }
      OPTIONAL { ?item wdt:P31 ?inst . ?inst rdfs:label ?instLabel FILTER(lang(?instLabel)="en") }
    } GROUP BY ?item ?work ?enLabel ?mulLabel ?saLabel ?hiLabel ?sex ?desc"""
    if not os.path.exists(path):
        fetch("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q}), path,
              headers={"Accept": "application/sparql-results+json"})
    figs = {}
    for b in json.load(open(path, encoding="utf-8"))["results"]["bindings"]:
        g = lambda k: b.get(k, {}).get("value", "")
        qid = g("item").rsplit("/", 1)[-1]; work = WD_WORK.get(g("work").rsplit("/", 1)[-1])
        f = figs.setdefault(qid, {"qid": qid, "en": g("enLabel") or g("mulLabel"), "works": set(), "sex": "", "keys": set(), "akeys": set(),
                                  "desc": g("desc"), "type": wd_type(g("insts"), g("desc"))})
        if work: f["works"].add(work)
        if work == "Mahabharata": f["works"].add("Bhagavad Gita")      # the Gita is MBh 6.23-40
        # English aliases (Partha, Keshava, Dhananjaya …) only confirm an epithet the lexicon already gives
        f.setdefault("confirm", set()).update(fold(a) for a in g("enAliases").split("|") if a and " " not in a.strip())
        sx = g("sex").rsplit("/", 1)[-1]
        if sx == "Q6581097": f["sex"] = "boy"
        elif sx == "Q6581072": f["sex"] = "girl"
        for which, vals in (("keys", [g("saLabel"), g("hiLabel")]), ("akeys", [a for a in g("aliases").split("|") if a])):
            for dv in vals:
                if not re.search(r"[\u0900-\u097f]", dv) or " " in dv.strip(): continue
                ia = re.sub(r"ḥ$", "", norm_word(deva2iast(dv.strip(" :")).strip()))
                if len(ia) > 2:
                    f[which].add(ia)
                    if ia.endswith("ān"): f[which].add(ia[:-2] + "at")        # हनुमान् → hanumat
                    elif ia.endswith("ā") and which == "keys": f[which].add(ia[:-1] + "an")   # अश्वत्थामा → aśvatthāman
                    elif ia.endswith("ī") and which == "keys": f[which].add(ia[:-1] + "in")   # शिखण्डी → śikhaṇḍin
                    if re.search(r"[^aāiīuūeoṃ]$", ia) and which == "keys": f[which].add(ia + "a")   # Hindi अर्जुन → arjun(a)
    labels = collections.Counter(k for f in figs.values() for k in f["keys"])
    aliases = collections.Counter(k for f in figs.values() for k in f["akeys"] - f["keys"])
    by_key = collections.defaultdict(list)       # key → [(figure, "label"|"alias")]
    for f in figs.values():
        for k in f["keys"]: by_key[k].append((f, "label"))
        for k in f["akeys"] - f["keys"]:
            if labels[k] == 0 and aliases[k] == 1: by_key[k].append((f, "alias"))   # an alias shared or clashing is dropped
    return figs, by_key


# ─────────────────────────────────────────────────────────────
# 3. Attestation: inflected forms + sandhi
# ─────────────────────────────────────────────────────────────
END = {
    "a_m": ["a", "aḥ", "am", "ena", "eṇa", "āya", "āt", "asya", "e", "au", "ābhyām", "āḥ", "ān", "aiḥ", "ebhyaḥ", "ānām", "āṇām", "eṣu", "āḥ"],
    "a_n": ["am", "ena", "eṇa", "āya", "āt", "asya", "e", "āni", "āṇi", "aiḥ", "ānām", "āṇām", "eṣu"],
    "ā_f": ["ā", "e", "ām", "ayā", "āyai", "āyāḥ", "āyām", "ābhyām", "āḥ", "ābhiḥ", "ānām", "āṇām", "āsu"],
    "ī_f": ["ī", "i", "īm", "yā", "yai", "yāḥ", "yām", "yau", "yaḥ", "īḥ", "ībhyām", "ībhiḥ", "īṇām", "īnām", "īṣu"],
    "i_m": ["iḥ", "i", "e", "im", "inā", "iṇā", "aye", "eḥ", "au", "ī", "ayaḥ", "īn", "ibhiḥ", "īnām", "īṇām", "iṣu"],
    "i_f": ["iḥ", "i", "e", "im", "yā", "aye", "yai", "eḥ", "yāḥ", "au", "yām", "ī", "ayaḥ", "īḥ", "ibhiḥ", "īnām", "iṣu"],
    "u_m": ["uḥ", "u", "o", "um", "unā", "uṇā", "ave", "oḥ", "au", "ū", "avaḥ", "ūn", "ubhiḥ", "ūnām", "ūṇām", "uṣu"],
    "u_f": ["uḥ", "u", "o", "um", "vā", "ave", "vai", "oḥ", "vāḥ", "au", "vām", "ū", "avaḥ", "ūḥ", "ubhiḥ", "ūnām", "uṣu"],
    "ū_f": ["ūḥ", "u", "ūm", "vā", "vai", "vāḥ", "vām", "vau", "vaḥ"],
    "an": ["ā", "ānam", "nā", "ṇā", "ne", "ṇe", "naḥ", "ṇaḥ", "ni", "ṇi", "an", "ānau", "ānaḥ", "abhiḥ", "nām", "ṇām", "asu"],
    "in": ["ī", "inam", "inā", "iṇā", "ine", "iṇe", "inaḥ", "iṇaḥ", "ini", "iṇi", "in", "inau", "iṇau", "ibhiḥ", "inām", "iṇām", "iṣu"],
    "as": ["āḥ", "asam", "asā", "ase", "asaḥ", "asi", "aḥ", "asau", "obhiḥ", "asām"],
    "at": ["ān", "antam", "atā", "ate", "ataḥ", "ati", "an", "antau", "antaḥ", "adbhiḥ", "atām"],
    "ṛ": ["ā", "āram", "aram", "rā", "re", "uḥ", "ari", "aḥ", "ārau", "āraḥ", "ṝn", "ṛbhiḥ", "ṝṇām"],
    "cons": ["", "ḥ", "am", "ā", "e", "aḥ", "i"],
}
PARTICLES = ["api", "apy", "iva", "eva", "iti", "ity", "atha", "adya", "iha", "uvāca", "abravīt", "āha", "asti", "abhavat", "uta"]

def stem_class(lemma, lex):
    g = (lex or "m").split(":")[0]
    if lemma.endswith("ā"): return lemma[:-1], "ā_f"
    if lemma.endswith("ī"): return lemma[:-1], "ī_f"
    if lemma.endswith("ū"): return lemma[:-1], "ū_f"
    if lemma.endswith("an"): return lemma[:-2], "an"
    if lemma.endswith("in"): return lemma[:-2], "in"
    if lemma.endswith("as"): return lemma[:-2], "as"
    if re.search(r"[mv]at$", lemma): return lemma[:-2], "at"
    if lemma.endswith("ṛ"): return lemma[:-1], "ṛ"
    if lemma.endswith("a"): return lemma[:-1], ("a_n" if g == "n" else "a_m")
    if lemma.endswith("i"): return lemma[:-1], ("i_f" if g == "f" else "i_m")
    if lemma.endswith("u"): return lemma[:-1], ("u_f" if g == "f" else "u_m")
    return lemma, "cons"

def sandhi_finals(f):
    """External-sandhi variants of an inflected form as GRETIL writes it before the next word."""
    out = {f}
    if f.endswith("aḥ"): out |= {f[:-1] + "s", f[:-1] + "ś", f[:-1] + "ṣ", f[:-2] + "o", f[:-1]}
    elif f.endswith("ḥ"): out |= {f[:-1] + "s", f[:-1] + "ś", f[:-1] + "ṣ", f[:-1] + "r", f[:-1]}
    elif f.endswith("t"): out |= {f[:-1] + x for x in "dnjcl"}
    elif f.endswith("n"): out |= {f[:-1] + "ṃs", f[:-1] + "ṃś", f[:-1] + "ṃ", f[:-1] + "l", f + "n"}
    elif f.endswith("m"): out |= {f[:-1] + "ṃ"}
    return out

MERGE = {("a", "a"): "ā", ("a", "ā"): "ā", ("ā", "a"): "ā", ("ā", "ā"): "ā", ("a", "i"): "e", ("ā", "i"): "e",
         ("a", "u"): "o", ("ā", "u"): "o", ("a", "e"): "ai", ("ā", "e"): "ai", ("i", "i"): "ī", ("ī", "i"): "ī",
         ("u", "u"): "ū", ("ū", "u"): "ū"}

def fused(f):
    """form + following vowel-initial particle written as one word (sītāpy, rāmeti, arjunaiva)."""
    out = set()
    v = f[-1:]
    if v not in "aāiīuū" or not v: return out
    for p in PARTICLES:
        m = MERGE.get((v, p[0]))
        if m: out.add(f[:-1] + m + p[1:])
        elif v in "iī": out.add(f[:-1] + "y" + p)
        elif v in "uū": out.add(f[:-1] + "v" + p)
    return out

def forms_of(lemma, lex):
    stem, cls = stem_class(lemma, lex)
    base = set()
    for e in END[cls]:
        f = norm_word(stem + e)
        if cls == "a_m" and e == "a" and False: continue
        base |= sandhi_finals(f)
    if cls == "a_m":            # aḥ before vowels other than a → a (identical to vocative), ā-final plural → ā
        base |= {norm_word(stem + "ā")}
    allf = set(base)
    for f in list(base): allf |= fused(f)
    return {f for f in allf if len(f) >= 2}

def compound_form(lemma):
    stem, cls = stem_class(lemma, "")
    return {"an": stem + "a", "in": stem + "i", "as": stem + "o", "at": stem + "ad", "ṛ": stem + "ṛ"}.get(cls, lemma)

STOP_TOKENS = set("mayā tvayā mama tava aham tvam vayam yūyam asmi asi asti santi bhavati bhavanti sa saḥ so sā tat tad te me "
                  "tena tasya tasmin tasmāt tām tam yaḥ yo yā yat yad yena yasya yasmin yam yām ayam iyam idam imam imām etat etad "
                  "eṣa eṣaḥ eṣo eṣā iti eva api apy ca vā na hi tu atha tadā yadā tathā yathā punar punaḥ kim kaḥ ko kā".split())
TOKEN_RE = re.compile(r"[^\s|/;,.'’‘\"()\[\]0-9=]+")
VOWELS = "aāiīuūṛeo"
VMERGE_START = {"a": ("ā",), "ā": ("ā",), "i": ("e", "ī"), "ī": ("e", "ī"), "u": ("o", "ū"), "ū": ("o", "ū")}


class Matcher:
    def __init__(self, lemmas):
        """lemmas: {lemma: {"lex": str, "safe_compound": bool}}"""
        self.full = collections.defaultdict(set)     # token → lemmas (whole-word inflected forms)
        self.cf = collections.defaultdict(set)       # compound member form → lemmas
        self.cf_noinit = collections.defaultdict(set)  # member form minus initial vowel → lemmas (vowel sandhi)
        self.ends = {}
        self.info = lemmas
        for L, d in lemmas.items():
            for f in forms_of(L, d["lex"]): self.full[f].add(L)
            c = norm_word(compound_form(L))
            if len(c) >= 3:
                self.cf[c].add(L)
                if c[0] in VMERGE_START: self.cf_noinit[c[1:]].add(L)
        for st in STOP_TOKENS:                            # pronoun forms fused with particles (mayaiva, tvayāpi)
            for f in {st} | fused(st): self.full.pop(f, None)
        self.maxlen = max(len(k) for k in self.cf) if self.cf else 0
        self.cache = {}

    def best(self, Ls):
        top = max(self.info[L].get("prio", 0) for L in Ls)
        return frozenset(L for L in Ls if self.info[L].get("prio", 0) == top)

    def analyse(self, tok):
        """→ list of (lemma, kind) where kind in free|compound|dvandva. Longest spans win.
        A span is (start, end, lemmas, lshare, rshare): l/rshare = 1 when the edge vowel is shared with the
        neighbouring word by vowel sandhi (bhīma+arjuna → bhīmārjuna)."""
        if tok in self.cache: return self.cache[tok]
        res = []
        if tok in self.full:
            res = [(L, "free") for L in self.best(self.full[tok])]
            self.cache[tok] = res; return res
        n = len(tok); spans = []
        MERGED_END = {"ā": "a", "e": "a", "o": "a"}
        for i in range(n):
            if i > 0:                                     # final member carrying a case ending
                tail = tok[i:]
                if tail in self.full and tok[i] not in VOWELS: spans.append((i, n, self.best(self.full[tail]), 0, 0))
                if tok[i] in ("ā", "e", "o", "ī", "ū"):
                    for v0 in ("a", "ā", "i", "ī", "u", "ū"):
                        if tok[i] in VMERGE_START[v0] and (v0 + tok[i + 1:]) in self.full:
                            spans.append((i, n, self.best(self.full[v0 + tok[i + 1:]]), 1, 0))
            for j in range(min(n, i + self.maxlen + 1), i + 2, -1):
                piece = tok[i:j]
                cands = []
                if (i == 0 or tok[i] not in VOWELS) and piece in self.cf: cands.append((self.cf[piece], 0, 0))
                if i > 0 and tok[i] in ("ā", "e", "ī", "o", "ū") and tok[i + 1:j] in self.cf_noinit:
                    Ls = {L for L in self.cf_noinit[tok[i + 1:j]] if tok[i] in VMERGE_START[norm_word(compound_form(L))[0]]}
                    if Ls: cands.append((Ls, 1, 0))
                if j < n and tok[j - 1] in MERGED_END and (tok[i:j - 1] + MERGED_END[tok[j - 1]]) in self.cf:
                    cands.append((self.cf[tok[i:j - 1] + MERGED_END[tok[j - 1]]], 0, 1))
                for Ls, ls, rs in cands:
                    if j < n and n - j < 2: continue
                    if 0 < i < 2: continue
                    spans.append((i, j, self.best(Ls), ls, rs))
        spans = sorted(set(spans), key=lambda s: (-(s[1] - s[0]), s[0]))
        taken, chosen = [False] * (n + 1), []
        for s in spans:
            core = range(s[0] + s[3], s[1] - s[4])
            if s[1] - s[0] < 4 or any(taken[k] for k in core): continue
            for k in core: taken[k] = True
            chosen.append(s)
        chosen.sort()
        for c in chosen:
            i, j, Ls = c[0], c[1], c[2]
            neighbours = [o for o in chosen if o is not c and (abs(o[1] - i) <= 1 or abs(o[0] - j) <= 1)
                          and max(self.info[L].get("prio", 0) for L in o[2]) >= 2]
            for L in Ls:
                d = self.info[L]
                if neighbours: res.append((L, "dvandva"))
                elif d["safe_compound"] and len(norm_word(compound_form(L))) >= 5: res.append((L, "compound"))
        self.cache[tok] = res
        return res


def scan(corpus_verses, matcher):
    """→ {lemma: {"n": count, "verses": [verse idx...]}}, per-verse lemma sets"""
    hits = collections.defaultdict(lambda: {"n": 0, "verses": [], "free": 0, "vc": collections.Counter()})
    per_verse = []
    for vi, (_, _, _, txt) in enumerate(corpus_verses):
        seen = set()
        for tok in TOKEN_RE.findall(txt.lower()):
            tok = norm_word(tok)
            if tok.endswith("ṃ"): tok = tok[:-1] + "m"
            if tok in STOP_TOKENS: continue
            for L, kind in matcher.analyse(tok):
                h = hits[L]; h["n"] += 1; h["vc"][vi] += 1
                if kind == "free": h["free"] += 1
                if L not in seen: h["verses"].append(vi); seen.add(L)
        per_verse.append(seen)
    return hits, per_verse


# ─────────────────────────────────────────────────────────────
# 4/5. Hindu rows
# ─────────────────────────────────────────────────────────────
def scripture_hints():
    p = os.path.join(ROOT, "data", "scripture-names.json")
    hints = collections.defaultdict(list)
    if os.path.exists(p):
        for row in json.load(open(p, encoding="utf-8")):
            if "Hindu" in (row[4] or ""): hints[fold(row[0])].append(row[0])
    return hints

def modern_name(lemma, hints):
    # people write the nominative of consonant stems: Hanumat → Hanuman, Aśvatthāman → Ashvatthama, Śikhaṇḍin → Shikhandi
    lemma = re.sub(r"([mv])at$", r"\1ān", lemma)
    lemma = re.sub(r"an$", "ā", lemma) if not re.search(r"[mv]ān$", lemma) else lemma
    lemma = re.sub(r"in$", "ī", lemma)
    r = roman(lemma)
    if fold(r) in hints: return hints[fold(r)][0]
    return r

def clean_label(lemma_disp, txt):
    t = re.sub(r"^.*?\b(N\.|patr\.|metron\.)\s*(fr\.\s*\S+,?\s*N\.\s*)?of\s+", "", txt)
    t = re.sub(r"\s*\((?:[^()]|\([^()]*\))*\)", "", t)      # drop parentheticals
    t = re.split(r"[;]|, (?=[A-Z][a-z]+\.)", t)[0].strip(" ,.")
    t = re.sub(r"\s+", " ", t)
    if len(t) > 90: t = t[:87].rsplit(" ", 1)[0] + "…"
    return f"{lemma_disp}, {t}" if t else lemma_disp

GENERIC = re.compile(r"^(Muni|Ṛṣi|Rākṣasa|Rākṣasī|Brahman|Brāhman|Daitya|Dānava|Asura|Nāga|Yakṣa|Gandharva|Apsaras|Deva|Devī|Vānara|"
                     r"Piśāca|Kṣatriya|Vaiśya|Śūdra|Rāja|Rājan|Ṛṣis|Munis|Tīrtha|Tirtha|Rakṣas|Rākṣasas|Daityas|Dānavas|Asuras)$")
VERBISH = re.compile(r"(ati|anti|asi|āmi|āmaḥ|ate|ante|āte|māna|mānā|amāna|tvā|itvā|iṣyati|tavya|anīya)$")

def ls_works_ok(wkey, sn):
    return wkey in sn["works"]

def scan_dcs(verses, name_ids, personified):
    """Lemma counts from DCS: a token counts if its LemmaId carries a 'name of' gloss, or the lemma is a personified deity."""
    hits = collections.defaultdict(lambda: {"n": 0, "verses": [], "free": 0, "vc": collections.Counter(), "pure": True})
    per_verse = []
    for vi, v in enumerate(verses):
        seen = set()
        for lem, lid, cpd in v[4]:
            kind = name_ids.get(lid)
            if not kind and lem not in personified: continue
            h = hits[lem]; h["n"] += 1; h["vc"][vi] += 1
            if not cpd: h["free"] += 1
            if kind != "pure": h["pure"] = False
            if lem not in seen: h["verses"].append(vi); seen.add(lem)
        per_verse.append(seen)
    return hits, per_verse

def hindu(hints, later=True):
    C = load_corpora()
    mw, common = load_mw()
    figs, wd_by_key = load_wikidata()
    print(f"MW proper-name headwords: {len(mw)}; Wikidata epic figures: {len(figs)}", file=sys.stderr)
    for c, vs in C.items(): print(f"  {c}: {len(vs)} verses", file=sys.stderr)
    JOBS = [{"corpus": c, "text": "", "wkey": c, "verses": C[c], "scan": "matcher", "era": "epic", "split": False, "new": False,
             "src": {"Mahabharata": SRC_GRETIL_MBH, "Bhagavad Gita": SRC_GRETIL_MBH, "Valmiki Ramayana": SRC_GRETIL_R}[c]}
            for c in ("Mahabharata", "Bhagavad Gita", "Valmiki Ramayana")]
    name_ids, personified = {}, set()
    if later:
        JOBS += later_jobs()
        dcsd = load_dcs_dictionary()
        name_ids = {i: v[3] for i, v in dcsd.items() if v[3]}
        # DCS names the lexicon lacks as "N. of" get an entry from the DCS gloss
        for i, (w, gr, gloss, kind) in dcsd.items():
            if not kind: continue
            L = w.strip()
            if not L or L in mw: continue
            mw[L] = {"key": "", "ambiguous": kind == "mixed", "senses": [{
                "txt": gloss, "works": set(), "kind": "name", "targets": [], "esp": None, "qual": "", "mentions": [],
                "lex": {"m": "m", "f": "f", "n": "n"}.get(gr.strip()[:1], ""), "type": sense_type(gloss), "plural": False}]}
        personified = {norm_word(L) for L, d in mw.items() if any(sn.get("personified") for sn in d["senses"])}

    cand = {}
    for L, d in mw.items():
        k = norm_word(L)
        lex = next((s["lex"] for s in d["senses"] if s["lex"]), "m")
        tiedw = any(s["works"] for s in d["senses"])
        prio = 3 if k in wd_by_key else (2 if tiedw and not d["ambiguous"] else (1 if tiedw else 0))
        if k in cand and cand[k]["prio"] >= prio: continue
        cand[k] = {"lex": lex, "safe_compound": not d["ambiguous"], "mw": L, "prio": prio}
    matcher = Matcher(cand)
    fold_index = collections.defaultdict(list)
    for k2 in list(cand) + list(wd_by_key): fold_index[fold(roman(k2))].append(k2)

    en_index = collections.defaultdict(list)        # folded English alias → figures (Bhimasena → Bhīma)
    for f in figs.values():
        for a in f.get("confirm", ()): en_index[a].append(f)

    def is_amb(k, d):
        if d["ambiguous"] or k in common: return True
        if k[-1:] in ("ā", "ī") and (k[:-1] + "a") in common: return True     # niścitā ← niścita, kāmā ← kāma
        if k[-1:] == "a" and ((k[:-1] + "ā") in common or (k[:-1] + "ī") in common or k[:-1] in common): return True   # suhṛda ← suhṛd
        return bool(VERBISH.search(k))

    def transparent(k):
        for i in range(2, len(k) - 1):
            left, right = k[:i], k[i:]
            if left in common and right in common and len(right) >= 3: return True
            if k[i - 1] == "ā" and (left[:-1] + "a") in common and ("a" + right) in common: return True
            if k[i - 1] == "ā" and (left[:-1] + "a") in common and ("ā" + right) in common: return True
        return False

    def label_of(f):
        dsc = re.split(r"[;.]", f["desc"])[0].strip()
        en = f["en"] or roman(next(iter(f["keys"]), ""))
        return f"{en}, {dsc}" if dsc and len(dsc) <= 80 else en

    def resolve_target(t, k):
        if " " in t.strip(): return norm_word(t.replace("-", "").replace("—", "").replace(" ", ""))
        tk = norm_word(t.replace("-", "").replace("—", ""))
        if tk == k: return None
        if tk not in wd_by_key and tk not in cand and "-" in t:      # "Viṣṇu-Kṛṣṇa": the last member if the whole is unknown
            last = norm_word(re.split(r"[-—]", t)[-1])
            if last in wd_by_key or last in cand: tk = last
        if tk not in wd_by_key:                              # Rāma-candra → Rāma through Wikidata's English aliases
            ef = {f["qid"]: f for f in en_index.get(fold(roman(tk)), [])}
            if len(ef) == 1:
                f = next(iter(ef.values()))
                lk = sorted(x for x in f["keys"] if x in wd_by_key)
                if lk: return lk[0]
        if tk not in wd_by_key:                              # MW misprints (Sitā for Sītā): match ignoring vowel length
            alt = [k2 for k2 in fold_index.get(fold(roman(tk)), []) if k2 != k and k2 in wd_by_key]
            alt = alt or [k2 for k2 in fold_index.get(fold(roman(tk)), []) if k2 != k and tk not in cand]
            if alt: tk = alt[0]
        return tk

    names_of = collections.defaultdict(set)          # target key → unambiguous lemmas the lexicon gives as its epithets
    for k2, c2 in cand.items():
        d2 = mw[c2["mw"]]
        if is_amb(k2, d2): continue
        for s2 in d2["senses"]:
            if s2["kind"] == "epithet" and s2["works"]:
                for t in s2["targets"]:
                    tk = resolve_target(t, k2)
                    if tk: names_of[tk].add(k2)

    rows, review = [], []
    stats = collections.Counter()
    mbh_epithets = {}                                 # (lemma, figure_id) accepted in the MBh → trusted in the Gita
    mbh_accepted = set()                              # lemmas accepted in the MBh (the Gita has too few names for its own context test)
    # phase 1: scan every job
    for job in JOBS:
        t0 = time.time()
        if job["scan"] == "dcs":
            hits, per_verse = scan_dcs(job["verses"], name_ids, personified)
            for k2 in list(hits):
                if k2 not in cand:                     # DCS lemma spelled differently from MW: give it a candidate entry
                    L2 = next((L for L in mw if norm_word(L) == k2), None)
                    if not L2: hits.pop(k2); continue
                    cand[k2] = {"lex": next((x["lex"] for x in mw[L2]["senses"] if x["lex"]), "m"), "safe_compound": False, "mw": L2, "prio": 0}
        else:
            hits, per_verse = scan(job["verses"], matcher)
        job["hits"], job["per_verse"] = hits, per_verse
        print(f"  scanned {job['corpus']} / {job['text'] or job['corpus']} in {time.time() - t0:.0f}s, {len(hits)} lemmas", file=sys.stderr)
    # phase 2: Wikidata items for names of the later corpora (label match + Hindu-context description)
    if later:
        keys = {k for job in JOBS if job["new"] for k, h in job["hits"].items()
                if h["free"] and (any(ls_works_ok(job["wkey"], sn) for sn in mw[cand[k]["mw"]]["senses"]) or h.get("pure"))}
        keys -= {k for k in keys if any(v == "label" for f, v in wd_by_key.get(k, []))}
        found = wd_label_figs(sorted(keys))
        for k2, f in found.items(): wd_by_key[k2].append((f, "label"))
        print(f"  Wikidata label matches for later corpora: {len(found)} of {len(keys)} names", file=sys.stderr)
    # phase 3: decide
    for job in JOBS:
        corpus, verses, src = job["wkey"], job["verses"], job["src"]
        hits, per_verse = job["hits"], job["per_verse"]
        def fig_ok(f):
            if corpus in f["works"]: return True
            if not job["new"]: return False
            if "*" in f["works"]: return True
            return job["era"] != "vedic" or f["type"] in ("deity", "sage", "mythological_being", "demon")
        # context = figures Wikidata places in this work, found in the same verse
        anchor = {k for k in hits if any(v == "label" and fig_ok(f) for f, v in wd_by_key.get(k, []))}
        if job["scan"] == "dcs": anchor |= {k for k, h in hits.items() if h.get("pure")}
        ctx = [vs & anchor for vs in per_verse]
        base = sum(1 for x in ctx if x) / max(1, len(ctx))
        occ_sets = {k: set(h["verses"]) for k, h in hits.items()}

        def near(vi, k, w=2):
            return any((vi + dd) in occ_sets.get(k, ()) for dd in range(-w, w + 1))

        def wd_in(k, via=None):
            return [f for f, v in wd_by_key.get(k, []) if fig_ok(f) and (via is None or v == via)]

        for k, h in hits.items():
            L = cand[k]["mw"]; d = mw[L]; senses = d["senses"]
            amb = is_amb(k, d) and not h.get("pure")
            if job["scan"] == "dcs" and h.get("pure") and not h["free"]: continue
            ts = [s for s in senses if corpus in s["works"]]
            ts_ext = ts or ([s for s in senses if "Mahabharata" in s["works"]] if corpus == "Bhagavad Gita" else [])
            dcs_only = False
            if not ts_ext and job["scan"] == "dcs" and h.get("pure"):     # the DCS annotator lemmatized it as this name
                ts_ext = [s for s in senses if s["kind"] in ("name", "epithet")][:1]; dcs_only = True
            lab, ali = wd_in(k, "label"), wd_in(k, "alias")
            cverses = [vi for vi in h["verses"] if ctx[vi] - {k}]
            ratio = len(cverses) / max(1, len(h["verses"]))
            lift = ratio / base if base else 0.0
            reasons = []
            if os.environ.get("DEBUG_LEMMAS") and k in os.environ["DEBUG_LEMMAS"].split(","):
                print("DEBUG", corpus, k, "amb", amb, "lift %.2f" % lift, "ratio %.2f" % ratio, "n", h["n"], "free", h["free"],
                      "ts", len(ts), "lab", [f["qid"] for f in lab], "ali", [f["qid"] for f in ali], file=sys.stderr)

            role, target_fig, figure_id, figure, sex, etype, relation, conf = "personal", None, "", "", "", "", "", 0.0
            ep = [s for s in ts_ext if s["kind"] == "epithet" and s["targets"]]
            if not ep:      # MW often leaves "N. of Kṛṣṇa" uncited; the figure's own presence in the work is the tie
                ep = [s for s in senses if s["kind"] == "epithet" and s["targets"] and not s["works"]
                      and any(wd_in(resolve_target(t, k) or "", "label") for t in s["targets"])]
            pnames = [s for s in ts_ext if s["kind"] == "name"]
            if len(pnames) > 1:
                def sense_fit(sn):
                    m = [x for x in sn["mentions"] if x != k and x in occ_sets]
                    return sum(1 for vi in h["verses"][:400] for x in m if near(vi, x))
                pnames.sort(key=sense_fit, reverse=True)
            personal_sense = pnames[0] if pnames else None
            lexsex = lambda s: {"m": "boy", "f": "girl"}.get(((s or {}).get("lex") or "").split(":")[0], "")

            if not lab and not ali and not amb and k not in wd_by_key:
                rk = fold(roman(k))
                ef = [f for f in en_index.get(rk, []) + en_index.get(rk[:-1], []) if corpus in f["works"]]
                if len({f["qid"] for f in ef}) == 1: ali = [ef[0]]
            alias_fig = None
            if not lab and ali:
                f = ali[0]
                rk, fe = fold(roman(k)), fold(f["en"])
                if rk == fe or (len(fe) >= 4 and rk.startswith(fe)) or (len(rk) >= 4 and fe.startswith(rk)):
                    lab = [f]                       # the figure's own (fuller or shorter) name: Bhīmasena, Maya(sura)
                else:
                    agrees = any(fold(roman(resolve_target(t, k) or "")) in {fold(f["en"])} | {fold(roman(x)) for x in f["keys"]}
                                 for s in ep for t in s["targets"])
                    # an alias that the lexicon gives as a principal god's own name (Viṣṇu on Rāma's item) is not an epithet
                    own_god = any(s["kind"] == "name" and re.search(r"principal|chief god|supreme", s["txt"], re.I) for s in senses)
                    if agrees or (not own_god and not ep): alias_fig = f

            # the lexicon's epithet reading: pick the figure it names that this corpus supports best
            epi = None
            if ep and not lab and not alias_fig:
                tc = []
                for si, sn in enumerate(ep):
                    for ti, t in enumerate(sn["targets"]):
                        if GENERIC.match(t): continue
                        tk = resolve_target(t, k)
                        if tk and tk not in [x[1] for x in tc]: tc.append((t, tk, sn, si * 10 + ti))
                def presence(tk):
                    forms_t = ({tk} | names_of.get(tk, set())) - {k}
                    return sum(1 for vi in h["verses"] if any(near(vi, x) for x in forms_t)) / max(1, len(h["verses"]))
                def score(x):
                    t, tk, sn, order = x
                    return (1 if sn["esp"] == t else 0, round(presence(tk), 1) + (0.15 if wd_in(tk, "label") else 0), -order)
                if tc:
                    ranked = sorted(tc, key=score, reverse=True)
                    t, tk, sense, _ = ranked[0]
                    epi = {"t": t, "tk": tk, "sense": sense, "co": presence(tk),
                           "others": [x[0].replace("-", "") for x in ranked[1:] if x[2] is sense]}
                    if os.environ.get("DEBUG_LEMMAS") and k in os.environ["DEBUG_LEMMAS"].split(","):
                        print("DEBUG-EP", corpus, k, "->", tk, "co %.2f" % epi["co"], file=sys.stderr)
                    # a person of this very name in the lexicon fits better unless the text keeps it near its figure
                    if personal_sense and epi["co"] < 0.3:
                        epi = None

            if lab:
                f = lab[0]; figure_id, figure, sex, etype = f["qid"], label_of(f), f["sex"], f["type"]
                if not sex and etype in ("human", "royal", "sage", "deity", "demon", "mythological_being"): sex = lexsex(personal_sense)
                conf = 0.95 if ts_ext and not dcs_only else 0.9
                if job["new"] and "*" in f["works"]: conf = min(conf, 0.85)
                if amb:
                    if lift >= 0.9: conf = 0.85
                    else: conf = 0.55; reasons.append(f"also a common word and its occurrences are not concentrated near other names (lift {lift:.2f})")
            elif alias_fig or epi:
                role = "epithet"; others = []
                if alias_fig:
                    tf = alias_fig; sense = ep[0] if ep else personal_sense
                    relation = f"epithet of {alias_fig['en']} (Wikidata alias)"
                    if amb: reasons.append("also a common word; the epithet rests on a Wikidata alias only")
                else:
                    t, tk, sense, others = epi["t"], epi["tk"], epi["sense"], epi["others"]
                    # another work's figure only where the text retells that work: the MBh's Rāmopākhyāna (3.257-276)
                    tfl = wd_in(tk, "label") or [f for f, v in wd_by_key.get(tk, []) if v == "label" and corpus == "Mahabharata"
                                                 and "Valmiki Ramayana" in f["works"]]
                    if not tfl:                                   # Bhīmasena → Bhīma through Wikidata's English aliases
                        rt = fold(roman(tk))
                        ef = {f["qid"]: f for f in en_index.get(rt, []) if corpus in f["works"]}
                        if len(ef) == 1: tfl = list(ef.values())
                    tf = tfl[0] if tfl else None
                    if sense.get("qual") and tf:
                        qd = fold(sense["qual"])
                        if not any(w in qd for w in re.findall(r"[a-z]{5,}", fold(tf["desc"] + " " + tf["en"]))): tf = None
                    relation = f"epithet of {tf['en'] if tf else roman(tk)}" + (f" (also used of {', '.join(others)})" if others else "")
                    if re.search(r"\bpatr\.", sense["txt"]): relation += "; patronymic"
                    elif re.search(r"\bmetron\.", sense["txt"]): relation += "; metronymic"
                ls = lexsex(sense)
                if tf and tf["sex"] and ls and tf["sex"] != ls: continue      # anantā (f.) is no epithet of Kṛṣṇa
                if tf:
                    figure_id, figure, sex, etype = tf["qid"], label_of(tf), tf["sex"] or lexsex(sense), tf["type"]
                    conf = 0.85 - (0.1 if others else 0)
                else:
                    tsen = mw.get(cand.get(tk, {}).get("mw", ""), {}).get("senses", [])
                    tt = next((s for s in tsen if corpus in s["works"] and s["kind"] == "name"), None)
                    if sense.get("qual"):
                        figure_id = f"slug:hindu:{fold(roman(tk))}-{fold(sense['qual'])[:24]}"
                        figure = f"{roman(tk)} ({sense['qual']})"
                    else:
                        figure_id = f"slug:hindu:{fold(roman(tk))}"
                        figure = clean_label(roman(tk), tt["txt"]) if tt else roman(tk)
                    etype = (tt or {}).get("type") or ("deity" if re.search(r"^(Viṣṇu|Kṛṣṇa|Śiva|Rudra|Indra|Agni|Sūrya|Brahmā|Varuṇa|Yama)$", t) else "human")
                    sex = lexsex(sense) if etype not in ("place", "tribe", "concept") else ""
                    conf = 0.7 - (0.1 if others else 0)
                    if amb: reasons.append("also a common word, and the figure it names has no Wikidata item in this work")
                if amb:
                    rk = fold(roman(k))
                    confirmed = tf and (rk in tf.get("confirm", ()) or rk[:-1] in tf.get("confirm", ())
                                        or (corpus != "Bhagavad Gita" and epi and epi["co"] >= 0.4)
                                        or (corpus == "Bhagavad Gita" and (k, tf["qid"]) in mbh_epithets))
                    if alias_fig and not confirmed or not tf: conf = 0.5
                    elif not confirmed:
                        conf = 0.55; reasons.append("also a common word; Wikidata does not list it among the figure's names")
                    elif epi and epi["co"] < (0.3 if corpus == "Bhagavad Gita" else 0.2):
                        conf = 0.55; reasons.append(f"also a common word and seldom near its figure's other names ({epi['co']:.0%} of verses)")
                    else: conf = min(conf, 0.8)
            elif ts_ext:
                sense = personal_sense or ts_ext[0]
                figure_id = f"slug:hindu:{fold(roman(L))}"
                if len(pnames) > 1 and sense["mentions"]:
                    figure_id += "-" + fold(roman(next((x for x in sense["mentions"] if x != k), sense["mentions"][0])))
                figure = clean_label(roman(L), sense["txt"])
                etype = sense["type"] or ("tribe" if sense["plural"] else "human")
                sex = "" if etype in ("place", "tribe", "concept") else lexsex(sense)
                if amb and not VERBISH.search(k) and lift >= 1.8 and 3 <= h["free"] <= 30 and \
                        (corpus != "Bhagavad Gita" or k in mbh_accepted): conf = 0.6
                elif amb: conf = 0.45; reasons.append(f"also a common word (or a verb form); no Wikidata figure in this work (lift {lift:.2f})")
                elif transparent(k) and lift < 1.5:
                    conf = 0.5; reasons.append(f"reads as an ordinary compound of two common words (lift {lift:.2f})")
                elif corpus == "Bhagavad Gita" and k not in mbh_accepted:
                    conf = 0.5; reasons.append("not accepted for the Mahabharata as a whole, of which the Gita is part")
                elif dcs_only: conf = 0.65
                elif lift >= 1.2 or (len(h["verses"]) <= 2 and ratio == 1): conf = 0.7
                else: conf = 0.5; reasons.append(f"occurrences not concentrated near other names (lift {lift:.2f}); may be a homograph")
            else:
                if amb or len(k) < 5 or h["free"] == 0: continue
                sense = senses[0]
                if SKIP_SENSE.search(sense["txt"]) or re.search(r"\b(year|Kalpa|Yoga|wk|sound|constellation|lunar|Nakṣatra)\b", sense["txt"]): continue
                figure_id = f"slug:hindu:{fold(roman(L))}"
                figure = clean_label(roman(L), sense["txt"])
                etype = sense["type"] or "human"
                sex = "" if etype in ("place", "tribe", "concept") else lexsex(sense)
                conf = 0.4; reasons.append("the lexicon names it but cites no tie to this work")

            if h["free"] == 0: conf -= 0.1; reasons.append("only found inside compounds")
            if etype in ("place", "tribe", "concept"): sex = ""
            conf = round(max(0.1, min(conf, 0.99)), 2)
            use = cverses if amb and cverses else h["verses"]
            occ = h["n"]                     # every matched form (for common words this may include the ordinary word)
            cite, section, url, _ = verses[use[0]]
            translit = L[:1].upper() + L[1:]
            for rx, rep in ((r"ṃ(?=[cj])", "ñ"), (r"ṃ(?=[kg])", "ṅ"), (r"ṃ(?=[td])", "n"), (r"ṃ(?=[ṭḍ])", "ṇ"), (r"ṃ(?=[pb])", "m")):
                translit = re.sub(rx, rep, translit)
            if any(sn.get("personified") for sn in senses) and role == "personal" and etype == "deity" and amb:
                relation = (relation + "; " if relation else "") + "also the ordinary word; the text does not separate deity and word"
            row = {"name": modern_name(translit, hints), "figure_id": figure_id, "figure": figure, "sex": sex,
                   "original": deva(translit), "translit": translit, "language": "Sanskrit", "tradition": "Hindu",
                   "subtradition": "", "corpus": job["corpus"], "text": job["text"] or section, "passage": cite, "url": url,
                   "occurrences": str(occ), "entity_type": etype, "name_role": role, "status": "attested",
                   "relation": relation, "source": f"{src}; {SRC_MW}" + (f"; {SRC_WD}" if figure_id.startswith("Q") else ""),
                   "confidence": f"{conf:.2f}"}
            row["_split"] = job["split"]
            label = job["corpus"] + (f" / {job['text']}" if job["split"] else "")
            if conf < 0.6:
                row["relation"] = (row["relation"] + "; " if row["relation"] else "") + "review: " + "; ".join(reasons)
                review.append(row); stats[(label, "review")] += 1
            else:
                rows.append(row)
                if role == "epithet" and corpus == "Mahabharata": mbh_epithets[(k, figure_id)] = True
                if corpus == "Mahabharata": mbh_accepted.add(k)
                stats[(label, "epithet" if role == "epithet" else ("place" if etype in ("place", "tribe") else "name"))] += 1
    return rows, review, stats


# ─────────────────────────────────────────────────────────────
# Later waves: Vedic Śruti, Purāṇas, smṛti/sūtra/tantra texts.
# Sources: the Digital Corpus of Sanskrit (O. Hellwig, CC BY 4.0) in CoNLL-U — lemmatized by its annotators, so a name is
# counted by lemma, not by guessed inflection; and, where DCS lacks a text or has only part of it, the volunteer e-texts
# of sanskritdocuments.org (ITRANS), read with the same inflection matcher as the epics.
# ─────────────────────────────────────────────────────────────
DCS_GIT = "https://github.com/OliverHellwig/sanskrit.git"
DCS_DIR = os.path.join(RAW, "dcs", "dcs", "data", "conllu")
DCS_BLOB = "https://github.com/OliverHellwig/sanskrit/blob/master/dcs/data/conllu/files/"
SRC_DCS = "Digital Corpus of Sanskrit (O. Hellwig, CC BY 4.0)"
SD_URL = "https://sanskritdocuments.org/"
SRC_SD = "sanskritdocuments.org volunteer e-text"

def get_dcs():
    if not os.path.isdir(os.path.join(DCS_DIR, "files")):
        import subprocess
        d = os.path.join(RAW, "dcs")
        subprocess.run(["git", "clone", "-q", "--filter=blob:none", "--no-checkout", "--depth", "1", DCS_GIT, d], check=True)
        subprocess.run(["git", "-C", d, "sparse-checkout", "init", "--cone"], check=True)
        subprocess.run(["git", "-C", d, "sparse-checkout", "set", "dcs/data/conllu/files", "dcs/data/conllu/lookup"], check=True)
        subprocess.run(["git", "-C", d, "checkout", "-q"], check=True)

NAME_GLOSS = re.compile(r"^\s*(name of|N\. of|patronymic|metronymic|epithet of|a name of)", re.I)

def load_dcs_dictionary():
    """→ {LemmaId: (lemma, grammar, gloss, name_kind)} with name_kind '' | 'pure' | 'mixed'."""
    out = {}
    with open(os.path.join(DCS_DIR, "lookup", "dictionary.csv"), encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < 5: continue
            items = [x.strip() for x in p[4].split(";") if x.strip()]
            named = [x for x in items if NAME_GLOSS.match(x)]
            kind = "" if not named else ("pure" if len(named) == len(items) else "mixed")
            out[p[0]] = (p[1], p[2], "; ".join(named) or p[4][:120], kind)
    return out

def load_dcs_text(folder, prefix, text, chapters=None):
    """DCS folder → verses [(cite, section, url, text, tokens)], tokens = [(lemma, LemmaId, is_compound_member)]."""
    d = os.path.join(DCS_DIR, "files", folder)
    files = sorted(f for f in os.listdir(d) if f.endswith(".conllu"))
    have = {f for f in files}
    files += sorted(f for f in os.listdir(d) if f.endswith(".conllu_parsed") and f[:-7] not in have)
    def order(f):
        m = re.match(r".*-(\d{4})-", f); return int(m.group(1)) if m else 0
    out = []
    for fn in sorted(files, key=order):
        m = re.match(r".*?-\d{4}-(.*)-\d+\.conllu(?:_parsed)?$", fn)
        chap = m.group(1) if m else fn
        parts = [x.strip() for x in chap.split(",")]
        nums = [x for x in parts[1:]]
        if chapters and not chapters(nums): continue
        url = DCS_BLOB + urllib.parse.quote(f"{folder}/{fn}")
        cur_key, cur_txt, cur_tok = None, [], []
        def flush():
            if cur_key is not None:
                out.append((f"{prefix} {'.'.join(nums)}.{cur_key}".replace(" .", " "), text, url, " ".join(cur_txt), list(cur_tok)))
        with open(os.path.join(d, fn), encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("# text = "): txt = line[9:].strip(); continue
                if line.startswith("# sent_counter = "):
                    sc = line.split("=", 1)[1].strip()
                    if sc != cur_key:
                        flush(); cur_key, cur_txt, cur_tok = sc, [], []
                    cur_txt.append(txt); continue
                if not line[:1].isdigit(): continue
                c = line.rstrip("\n").split("\t")
                if "-" in c[0] or len(c) < 10: continue
                lid = re.search(r"LemmaId=(\d+)", c[9])
                cur_tok.append((norm_word(c[2]), lid.group(1) if lid else "", "Case=Cpd" in c[5]))
        flush()
    return out

# ITRANS (sanskritdocuments.org) → IAST
_ITX = sorted([("RRi", "ṛ"), ("R^i", "ṛ"), ("RRI", "ṝ"), ("R^I", "ṝ"), ("LLi", "ḷ"), ("L^i", "ḷ"), ("kSh", "kṣ"), ("chh", "ch"),
               ("shh", "ṣ"), ("Ch", "ch"), ("ch", "c"), ("Sh", "ṣ"), ("sh", "ś"), ("GY", "jñ"), ("j~n", "jñ"), ("~N", "ṅ"),
               ("~n", "ñ"), ("JN", "ñ"), ("aa", "ā"), ("ii", "ī"), ("uu", "ū"), ("A", "ā"), ("I", "ī"), ("U", "ū"), (".n", "ṃ"),
               (".m", "ṃ"), ("M", "ṃ"), (".N", "ṃ"), ("H", "ḥ"), (".a", "'"), (".h", ""), ("T", "ṭ"), ("D", "ḍ"), ("N", "ṇ"),
               ("x", "kṣ"), ("w", "v"), ("L", "ḷ"), ("E", "e"), ("O", "o")], key=lambda x: -len(x[0]))

def itrans2iast(s):
    s = re.sub(r"\{\\m\+\}", "ṃ", s)
    s = re.sub(r"\\[a-zA-Z]+\{[^}]*\}|\\[-,.]|[{}#]|\\[a-zA-Z]+", " ", s)
    out, i = [], 0
    while i < len(s):
        for a, b in _ITX:
            if s.startswith(a, i): out.append(b); i += len(a); break
        else: out.append(s[i]); i += 1
    return "".join(out)

ORD = {"prathama": 1, "dvitīya": 2, "tṛtīya": 3, "caturtha": 4, "pañcama": 5, "ṣaṣṭha": 6, "saptama": 7, "aṣṭama": 8,
       "navama": 9, "daśama": 10}

def load_itx(files, prefix, text, book=None, keep=None, mark_url=None):
    """sanskritdocuments ITRANS files → verses [(cite, section, url, iast_text)]. Verse ends at '|| n||'; a chapter
    boundary is a \\section with adhyāya/khaṇḍa/praśna, or an 'iti … ḥ' colophon. Explicit refs (|| 3\\.2||) are kept."""
    out = []
    for fn, bk in files:
        path = os.path.join(RAW, "sd", fn)
        url = SD_URL + (mark_url or "") + fn
        ch, in_ch, buf, started = 0, 0, [], False
        src_text = open(path, encoding="utf-8", errors="replace").read()
        has_ch = bool(re.search(r"\\(?:section|chapter)\{[^}]*(adhyAy|khaNDa|prashna|vallI|prapAThaka)", src_text))
        for raw in src_text.split("\n"):
            if raw.startswith("%") or raw.startswith("\\documentstyle") or raw.startswith("#"): continue
            if "\\begin{document}" in raw: started = True; continue
            if not started: continue
            line = re.sub(r"^\\EN\{[^}]*\}", "", raw.strip())
            sutra = re.search(r"\|\s*\d+\s*\\-\s*(\d+)\\\.(\d+)\s*$", line)      # Nārada Bhakti Sūtra: "… | 3 \- 1\.03"
            if sutra:
                out.append((f"{prefix} {int(sutra.group(1))}.{int(sutra.group(2))}", text, url, itrans2iast(line[:sutra.start()])))
                continue
            sec = re.match(r"\\(?:section|chapter)\{(.*)\}", line)
            if sec or re.match(r"\|*\s*iti\b.*(khaNDaH|adhyAyaH|prashnaH|vallI|prapAThakaH)", line):
                head = sec.group(1) if sec else ""
                if sec and not re.search(r"adhyAy|khaNDa|prashna|vallI|prapAThaka", head):
                    if has_ch and ch and re.search(r"stotra|sUkta|kavach|nyAsa|dhyAna|Arati|kShamA|rahasya|upasaMhAra", head):
                        ch, in_ch = -1, 0                  # appended hymns after the last chapter
                    continue
                n = re.search(r"\\-\s*(\d+)", head) or re.search(r"^\|*\s*(\d+)\\\.", head)
                if ch == -1: continue
                if in_ch or ch == 0: ch = int(n.group(1)) if n else ch + 1; in_ch = 0
                elif n: ch = int(n.group(1))
                buf = []; continue
            if line.startswith("\\") or not line: continue
            m = re.search(r"\|\|\s*([\d\\.,\s]+?)\s*\|\|", line)
            buf.append(re.sub(r"\|\|.*$", "", line) if m else line)
            if m:
                ref = re.sub(r"[\\\s]", "", m.group(1)).replace(",", ".")
                if line.lower().startswith("iti") or "adhyAyaH" in line: buf = []; continue
                if ch == -1 or (has_ch and ch == 0): buf = []; continue        # front and back matter outside the chapters
                ch_use = ch or 1
                cite = ref if "." in ref else f"{ch_use}.{ref}"
                if bk is not None and cite.count(".") < 2: cite = f"{bk}.{cite}"
                if keep and not keep(cite): buf = []; continue
                out.append((f"{prefix} {cite}", text, url, itrans2iast(" ".join(buf)).replace("|", " ")))
                in_ch += 1; buf = []
        if buf and not out:            # texts without verse numbers (Maitrī): one passage per paragraph
            pass
    return out

def load_itx_paragraphs(fn, prefix, text):
    out, n = [], 0
    started = False
    for raw in open(os.path.join(RAW, "sd", fn), encoding="utf-8", errors="replace"):
        if "\\begin{document}" in raw: started = True; continue
        if not started or raw.startswith(("%", "\\")): continue
        for seg in re.split(r"\.\.", raw):
            seg = seg.strip()
            if len(seg) > 20:
                n += 1; out.append((f"{prefix} ¶{n}", text, SD_URL + "doc_upanishhat/" + fn, itrans2iast(seg)))
    return out

SD_FILES = {
    "iisha": "doc_upanishhat/iisha.itx", "kena": "doc_upanishhat/kena.itx", "prashna": "doc_upanishhat/prashna.itx",
    "maandu": "doc_upanishhat/maandu.itx", "maitri": "doc_upanishhat/maitri.itx", "durga700": "doc_devii/durga700.itx",
    "avadhutagiitaa": "doc_giitaa/avadhutagiitaa.itx", "nAradabhaktisUtra": "doc_z_misc_major_works/nAradabhaktisUtra.itx",
    "brahmapur": "doc_purana/brahmapur.itx", "garuDapurANa": "doc_purana/garuDapurANa.itx",
    **{f"bhagpur-{b}": f"doc_purana/bhagpur-{b}.itx" for b in ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10a", "10b", "11", "12"]},
    **{f"devIbhAgavatam{b:02d}": f"doc_purana/devIbhAgavatam{b:02d}.itx" for b in range(1, 13)},
    **{f: f"doc_purana/{f}.itx" for f in ["shivapurANam1vidyeshvarasaMhitA", "shivapurANam2rudrasaMhitA1sRRiShTikhaNDaH",
       "shivapurANam2rudrasaMhitA2satIkhaNDaH", "shivapurANam2rudrasaMhitA3pArvatIkhaNDaH", "shivapurANam2rudrasaMhitA4kumArakhaNDaH",
       "shivapurANam2rudrasaMhitA5yuddhakhaNDaH", "shivapurANam3shatarudrasaMhitA", "shivapurANam4koTirudrasaMhitA",
       "shivapurANam5umAsaMhitA", "shivapurANam6kailAsasaMhitA", "shivapurANam7vAyavIyasaMhitA"]},
}

def get_sd():
    for f, p in SD_FILES.items():
        path = os.path.join(RAW, "sd", f + ".itx")
        if not os.path.exists(path):
            fetch(SD_URL + p, path, headers={"User-Agent": "Mozilla/5.0 (Macintosh) AppleWebKit/537.36 Chrome/120 Safari/537.36",
                                             "Accept": "*/*"})
            time.sleep(0.5)

def sd_dir(f): return SD_FILES[f].rsplit("/", 1)[0] + "/"

def dcs_cov(folder):
    d = os.path.join(DCS_DIR, "files", folder)
    return len({re.sub(r"\.conllu(_parsed)?$", "", f) for f in os.listdir(d) if ".conllu" in f})

def later_jobs():
    """Every later corpus as a scan job. 'era' decides which epic figures may stand for a name (Vedic: only gods/sages)."""
    get_dcs(); get_sd()
    J = []
    def dcs(corpus, text, wkey, folder, prefix, era, note="", split=False, chapters=None):
        vs = load_dcs_text(folder, prefix, text, chapters)
        cov = f"{dcs_cov(folder)} chapters annotated" + (f"; {note}" if note else "")
        J.append({"corpus": corpus, "text": text, "wkey": wkey, "verses": vs, "scan": "dcs", "era": era, "split": split,
                  "src": f"{SRC_DCS}, {text} ({cov})", "new": True})
    def itx(corpus, text, wkey, verses, era, note, split=False):
        J.append({"corpus": corpus, "text": text, "wkey": wkey, "verses": verses, "scan": "matcher", "era": era, "split": split,
                  "src": f"{SRC_SD}, {text} ({note})", "new": True})
    # Śruti
    dcs("Rigveda", "Rigveda", "RV", "Ṛgveda", "RV", "vedic")
    dcs("Atharvaveda", "Shaunaka", "AV", "Atharvaveda (Śaunaka)", "AVŚ", "vedic", split=True)
    dcs("Atharvaveda", "Paippalada", "AVP", "Atharvaveda (Paippalāda)", "AVP", "vedic", split=True)
    dcs("Shukla Yajurveda", "Vajasaneyi Samhita", "VS", "Vājasaneyisaṃhitā (Mādhyandina)", "VS", "vedic", "Mādhyandina, partial")
    dcs("Krishna Yajurveda", "Taittiriya Samhita", "TS", "Taittirīyasaṃhitā", "TS", "vedic", split=True)
    dcs("Krishna Yajurveda", "Maitrayani Samhita", "MS", "Maitrāyaṇīsaṃhitā", "MS", "vedic", split=True)
    dcs("Krishna Yajurveda", "Kathaka Samhita", "KS", "Kāṭhakasaṃhitā", "KS", "vedic", split=True)
    for text, wkey, folder, pre in [("Shatapatha Brahmana", "SB", "Śatapathabrāhmaṇa", "ŚB"), ("Aitareya Brahmana", "AB", "Aitareyabrāhmaṇa", "AB"),
                                    ("Kaushitaki Brahmana", "KB", "Kauṣītakibrāhmaṇa", "KB"), ("Taittiriya Brahmana", "TB", "Taittirīyabrāhmaṇa", "TB"),
                                    ("Jaiminiya Brahmana", "JB", "Jaiminīyabrāhmaṇa", "JB"), ("Panchavimsha Brahmana", "PB", "Pañcaviṃśabrāhmaṇa", "PB"),
                                    ("Gopatha Brahmana", "GB", "Gopathabrāhmaṇa", "GB"), ("Shadvimsha Brahmana", "SadvB", "Ṣaḍviṃśabrāhmaṇa", "ṢB"),
                                    ("Jaiminiya Upanishad Brahmana", "JUB", "Jaiminīya-Upaniṣad-Brāhmaṇa", "JUB")]:
        dcs("Brahmanas", text, wkey, folder, pre, "vedic", split=True)
    for text, wkey, folder, pre in [("Aitareya Aranyaka", "AA", "Aitareya-Āraṇyaka", "AĀ"), ("Taittiriya Aranyaka", "TA", "Taittirīyāraṇyaka", "TĀ"),
                                    ("Shankhayana Aranyaka", "SA", "Śāṅkhāyanāraṇyaka", "ŚĀ")]:
        dcs("Aranyakas", text, wkey, folder, pre, "vedic", split=True)
    for text, wkey, folder, pre in [("Brihadaranyaka Upanishad", "BAU", "Bṛhadāraṇyakopaniṣad", "BĀU"), ("Chandogya Upanishad", "ChU", "Chāndogyopaniṣad", "ChU"),
                                    ("Taittiriya Upanishad", "TU", "Taittirīyopaniṣad", "TU"), ("Aitareya Upanishad", "AU", "Aitareyopaniṣad", "AU"),
                                    ("Katha Upanishad", "KathU", "Kaṭhopaniṣad", "KaṭhU"), ("Mundaka Upanishad", "MundU", "Muṇḍakopaniṣad", "MuṇḍU"),
                                    ("Shvetashvatara Upanishad", "SvetU", "Śvetāśvataropaniṣad", "ŚvetU"), ("Kaushitaki Upanishad", "KausU", "Kauṣītakyupaniṣad", "KauṣU")]:
        dcs("Upanishads", text, wkey, folder, pre, "vedic", split=True)
    for text, wkey, fn, pre in [("Isha Upanishad", "IsaU", "iisha", "ĪU"), ("Kena Upanishad", "KenaU", "kena", "KenaU"),
                                ("Prashna Upanishad", "PrasnaU", "prashna", "PrU"), ("Mandukya Upanishad", "MandU", "maandu", "MāṇḍU")]:
        itx("Upanishads", text, wkey, load_itx([(fn + ".itx", None)], pre, text, mark_url=sd_dir(fn)), "vedic", "complete", split=True)
    itx("Upanishads", "Maitri Upanishad", "MaitrU", load_itx_paragraphs("maitri.itx", "MaitrU", "Maitri Upanishad"), "vedic",
        "complete; e-text has no verse numbers, cited by paragraph of the e-text", split=True)
    # Itihāsa / Purāṇa
    dcs("Harivamsha", "Harivamsha", "HV", "Harivaṃśa", "HV", "puranic", "critical-edition numbering")
    bh = [(f"bhagpur-{b}.itx", int(b[:2])) for b in ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10a", "10b", "11", "12"]]
    itx("Bhagavata Purana", "Bhagavata Purana", "BhP", load_itx(bh, "BhP", "Bhagavata Purana", mark_url="doc_purana/"), "puranic", "complete, 12 skandhas")
    itx("Uddhava Gita", "Uddhava Gita", "UG",
        load_itx([("bhagpur-11.itx", 11)], "BhP", "Uddhava Gita", keep=lambda c: 6 <= int(c.split(".")[1]) <= 29, mark_url="doc_purana/"),
        "puranic", "Bhagavata Purana 11.6-29")
    dcs("Vishnu Purana", "Vishnu Purana", "VP", "Viṣṇupurāṇa", "ViP", "puranic")
    itx("Devi Mahatmya", "Devi Mahatmya", "DM",
        [(f"DM {c.split()[1]} (chapter.Saptashati verse; Markandeya Purana ch. {80 + int(c.split()[1].split('.')[0])})", s, u, t)
         for c, s, u, t in load_itx([("durga700.itx", None)], "DM", "Devi Mahatmya", mark_url="doc_devii/",
                                    keep=lambda c: c.split(".")[0].isdigit() and 1 <= int(c.split(".")[0]) <= 13)],
        "puranic", "chapters 1-13 = Markandeya Purana 81-93; the e-text's added hymns are left out")
    itx("Devi Bhagavata Purana", "Devi Bhagavata Purana", "DBhP",
        load_itx([(f"devIbhAgavatam{b:02d}.itx", None) for b in range(1, 13)], "DBhP", "Devi Bhagavata Purana", mark_url="doc_purana/"),
        "puranic", "complete, 12 skandhas")
    shiva = ["shivapurANam1vidyeshvarasaMhitA", "shivapurANam2rudrasaMhitA1sRRiShTikhaNDaH", "shivapurANam2rudrasaMhitA2satIkhaNDaH",
             "shivapurANam2rudrasaMhitA3pArvatIkhaNDaH", "shivapurANam2rudrasaMhitA4kumArakhaNDaH", "shivapurANam2rudrasaMhitA5yuddhakhaNDaH",
             "shivapurANam3shatarudrasaMhitA", "shivapurANam4koTirudrasaMhitA", "shivapurANam5umAsaMhitA", "shivapurANam6kailAsasaMhitA",
             "shivapurANam7vAyavIyasaMhitA"]
    itx("Shiva Purana", "Shiva Purana", "SivaP", load_itx([(f + ".itx", None) for f in shiva], "ŚivaP", "Shiva Purana", mark_url="doc_purana/"),
        "puranic", "all seven saṃhitās of the vulgate (GRETIL has only books 1 and 7)")
    itx("Brahma Purana", "Brahma Purana", "BrahmaP", load_itx([("brahmapur.itx", None)], "BrP", "Brahma Purana", mark_url="doc_purana/"),
        "puranic", "complete")
    itx("Garuda Purana", "Garuda Purana", "GarP", load_itx([("garuDapurANa.itx", None)], "GarP", "Garuda Purana", mark_url="doc_purana/"),
        "puranic", "e-text of the vulgate")
    for corpus, wkey, folder, pre, note in [("Agni Purana", "AgniP", "Agnipurāṇa", "AgniP", "25 of 383 chapters"),
                                            ("Kurma Purana", "KurmaP", "Kūrmapurāṇa", "KūP", ""), ("Linga Purana", "LingaP", "Liṅgapurāṇa", "LiP", ""),
                                            ("Matsya Purana", "MatsyaP", "Matsyapurāṇa", "MPur", "chapters 1-176 of 291"),
                                            ("Varaha Purana", "VarP", "Varāhapurāṇa", "VarP", "one chapter only"),
                                            ("Narasimha Purana", "NarasP", "Narasiṃhapurāṇa", "NarasP", "one chapter only"),
                                            ("Kalika Purana", "KalP", "Kālikāpurāṇa", "KālP", "chapters 52-56 only")]:
        dcs(corpus, corpus, wkey, folder, pre, "puranic", note)
    dcs("Skanda Purana", "Skandapurana (early recension)", "SkP", "Skandapurāṇa", "SkP", "puranic", "Bakker et al. early Skandapurāṇa", split=True)
    dcs("Skanda Purana", "Revakhanda", "SkRkh", "Skandapurāṇa (Revākhaṇḍa)", "SkP Rkh", "puranic", split=True)
    # Kāvya, darśana, smṛti, tantra
    dcs("Gita Govinda", "Gita Govinda", "GG", "Gītagovinda", "GītGov", "puranic", "complete")
    dcs("Yoga Sutras", "Yoga Sutras", "YS", "Yogasūtra", "YS", "other", "complete")
    for corpus, wkey, folder, pre, note in [("Manusmriti", "Manu", "Manusmṛti", "Manu", "complete"), ("Yajnavalkya Smriti", "Yajn", "Yājñavalkyasmṛti", "YāSmṛ", "complete"),
                                            ("Narada Smriti", "Narada", "Nāradasmṛti", "NāSmṛ", ""), ("Arthashastra", "Artha", "Arthaśāstra", "ArthaŚ", "partial"),
                                            ("Ashtavakra Gita", "Ashtav", "Aṣṭāvakragīta", "AṣṭGī", "complete"),
                                            ("Satvata Tantra", "Satvata", "Sātvatatantra", "SātT", "Pāñcarātra"),
                                            ("Mrigendra Tantra", "Mrgendra", "Mṛgendratantra", "MṛgT", "Śaiva Āgama, Vidyāpāda"),
                                            ("Devikalottara Agama", "DeviKal", "Devīkālottarāgama", "DevīĀg", "Śaiva Āgama"),
                                            ("Todala Tantra", "Todala", "Toḍalatantra", "ToḍalT", "Śākta"), ("Matrikabheda Tantra", "Matrka", "Mātṛkābhedatantra", "MBhT", "Śākta"),
                                            ("Mahachina Tantra", "Mahacina", "Mahācīnatantra", "MCT", "Śākta, one chapter"),
                                            ("Vaikhanasa Dharmasutra", "VaikhDh", "Vaikhānasadharmasūtra", "VaikhDhS", "Vaikhānasa")]:
        dcs(corpus, corpus, wkey, folder, pre, "other", note)
    itx("Avadhuta Gita", "Avadhuta Gita", "Avadh", load_itx([("avadhutagiitaa.itx", None)], "AvG", "Avadhuta Gita", mark_url="doc_giitaa/"), "other", "complete")
    itx("Narada Bhakti Sutras", "Narada Bhakti Sutras", "NBS", load_itx([("nAradabhaktisUtra.itx", None)], "NBS", "Narada Bhakti Sutras",
        mark_url="doc_z_misc_major_works/"), "other", "complete")
    for j in J: print(f"  {j['corpus']} / {j['text']}: {len(j['verses'])} passages", file=sys.stderr)
    return J

# Not found as an open machine-readable edition (reported, no rows): Samaveda; Jaiminīya/Kauthuma Saṃhitā; Brahmāṇḍa,
# Brahmavaivarta, Mārkaṇḍeya (beyond the Devī Māhātmya), Vāmana, Padma, Nārada, Bhaviṣya Purāṇas; Brahma Sūtras (mūla only);
# Yoga Vāsiṣṭha (complete); Jayākhya and Ahirbudhnya Saṃhitās; Kulārṇava and Mahānirvāṇa Tantras.

WDL_CACHE = os.path.join(RAW, "wd_labels.json")
WD_OK = re.compile(r"hindu|vedic|\bveda|rigved|ṛgved|upanishad|upaniṣad|brahmana|purana|purāṇa|mahabharata|ramayana|\bsage\b|rishi|"
                   r"ṛṣi|\bseer\b|deity|goddess|\bgod\b|mytholog|asura|demon|apsara|gandharva|rakshasa|avatar|sanskrit|\bepic\b|"
                   r"legendary|daitya|\bnaga\b|tirthankara|jain|indian king|ancient india", re.I)
WD_BAD = re.compile(r"\bfilm\b|album|\bsong\b|single|village|town in|city in|district|given name|family name|surname|asteroid|"
                    r"\bship\b|company|\bband\b|actor|actress|politician|cricket|football|television|\bnovel\b|journal|crater|genus|"
                    r"species|disambiguation|temple|river in|mountain in|newspaper|software|painting|magazine|school|college|"
                    r"university|book by|poem by|sculpture|railway|station|constituency|neighbourhood|locality|lake in|beetle|moth|"
                    r"plant|scholar|writer|poet\b|singer|musician|scientist|astronomer|mathematician|philosopher \(|journalist", re.I)
WD_TEXT = re.compile(r"literary work|religious text|\btext\b|upanishad|book|scripture|written work|hymn", re.I)

def wd_label_figs(keys):
    """Wikidata items whose English label or alias equals the name (IAST or everyday spelling) and whose description places
    them in Hindu tradition. A name matching two or more such items gets none (no guessing)."""
    try: cache = json.load(open(WDL_CACHE, encoding="utf-8"))
    except Exception: cache = {}
    labels_of = {}
    for k in keys:
        L = re.sub(r"ṃ(?=[cj])", "ñ", re.sub(r"ṃ(?=[kg])", "ṅ", re.sub(r"ṃ(?=[td])", "n", k)))
        cand = {roman(L), L[:1].upper() + L[1:], modern_name(L[:1].upper() + L[1:], {})}
        if roman(L).endswith("a") and len(L) > 4: cand.add(roman(L)[:-1])
        labels_of[k] = {c for c in cand if len(c) > 2}
    need = sorted({l for v in labels_of.values() for l in v} - set(cache))
    for i in range(0, len(need), 120):
        chunk = need[i:i + 120]
        vals = " ".join(json.dumps(l, ensure_ascii=False) + "@en" for l in chunk)
        q = f"""SELECT ?l ?item ?desc ?sex (GROUP_CONCAT(DISTINCT ?il; separator="|") AS ?insts) WHERE {{
          VALUES ?l {{ {vals} }} ?item rdfs:label|skos:altLabel ?l .
          OPTIONAL {{ ?item schema:description ?desc FILTER(lang(?desc)="en") }}
          OPTIONAL {{ ?item wdt:P21 ?sex }}
          OPTIONAL {{ ?item wdt:P31 ?i . ?i rdfs:label ?il FILTER(lang(?il)="en") }} }} GROUP BY ?l ?item ?desc ?sex"""
        res = None
        for attempt in range(5):
            try:
                req = urllib.request.Request("https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q}),
                                             headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
                with urllib.request.urlopen(req, timeout=120) as r: res = json.loads(r.read())
                break
            except Exception as e:
                time.sleep(65 if "429" in str(e) else 5 + 5 * attempt)
        if res is None: continue
        for l in chunk: cache[l] = []
        for b in res["results"]["bindings"]:
            g = lambda x: b.get(x, {}).get("value", "")
            sx = g("sex").rsplit("/", 1)[-1]
            cache[g("l")].append({"qid": g("item").rsplit("/", 1)[-1], "desc": g("desc"), "insts": g("insts"),
                                  "sex": "boy" if sx == "Q6581097" else ("girl" if sx == "Q6581072" else "")})
        if i % 1200 == 0: json.dump(cache, open(WDL_CACHE, "w", encoding="utf-8"), ensure_ascii=False)
        time.sleep(0.3)
    json.dump(cache, open(WDL_CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    out = {}
    for k, labs in labels_of.items():
        hits = {}
        for l in labs:
            for c in cache.get(l, []):
                blob = c["desc"] + " | " + c["insts"]
                if WD_OK.search(blob) and not WD_BAD.search(c["desc"]) and not WD_TEXT.search(c["insts"]):
                    hits.setdefault(c["qid"], (l, c))
        if len(hits) == 1:
            qid, (l, c) = next(iter(hits.items()))
            out[k] = {"qid": qid, "en": l, "works": {"*"}, "sex": c["sex"], "keys": {k}, "akeys": set(), "confirm": set(),
                      "desc": c["desc"], "type": wd_type(c["insts"], c["desc"])}
    return out


# ─────────────────────────────────────────────────────────────
# Rāmcaritmānas (Awadhi; GRETIL romanized e-text): the Vālmīki figures, in Awadhi spellings derived by sound rules
# ─────────────────────────────────────────────────────────────
RCM_URL = GRETIL + "3_nia/hindi/tulrcm{}u.htm"
SRC_RCM = "GRETIL Tulasidasa, Ramacaritamanasa (romanized e-text)"
RCM_KANDA = ["Bala Kanda", "Ayodhya Kanda", "Aranya Kanda", "Kishkindha Kanda", "Sundara Kanda", "Lanka Kanda", "Uttara Kanda"]

def awadhi_forms(iast):
    """Sanskrit name → the spellings Tulsidas uses (ś/ṣ → s, ṇ → n, v → b, y- → j-, kṣ → kh/ch, ṛ → ri)."""
    base = {iast.lower()}
    rules = [("ś", "s"), ("ṣ", "s"), ("ṇ", "n"), ("ṃ", "ṃ"), ("ṛ", "ri")]
    for a, b in rules: base = {x.replace(a, b) for x in base} | base
    base |= {x.replace("v", "b") for x in base} | {("j" + x[1:]) if x.startswith("y") else x for x in base}
    base |= {x.replace("kṣ", "kh") for x in base} | {x.replace("kṣm", "chim") for x in base} | {x.replace("kṣ", "ch") for x in base}
    return {x for x in base if not re.search(r"[śṣṇṛ]", x)}

def ramcharitmanas(valmiki_rows, hints):
    texts = []
    for i in range(1, 8):
        p = fetch(RCM_URL.format(i), os.path.join(RAW, "rcm", f"tulrcm{i}u.htm"))
        h = open(p, encoding="utf-8", errors="replace").read()
        body = h.split("<hr>", 1)[-1]
        body = re.sub(r"<[^>]+>", "\n", body)
        texts.append(body)
    # passages: kāṇḍa.dohā — lines up to and including each dohā/soraṭhā
    passages = []
    for ki, body in enumerate(texts, 1):
        buf = []
        for line in body.split("\n"):
            line = line.strip()
            if not line: continue
            buf.append(line)
            m = re.match(r"(do|so|chaṃ)\.\s", line)
            n = re.search(r"//\s*(\d+)\s*(?:\((?:[a-z]|ka|kha|ga)\))?\s*//", line)
            if m and n and m.group(1) == "do":
                passages.append((f"RCM {ki}.{n.group(1)}", RCM_KANDA[ki - 1], RCM_URL.format(ki), " ".join(buf))); buf = []
        if buf: passages.append((f"RCM {ki}.end", RCM_KANDA[ki - 1], RCM_URL.format(ki), " ".join(buf)))
    toks = [(c, s, u, re.findall(r"[a-zāīūṛṃṅñṭḍṇśṣḷẽãĩõũ̃_]+", t.lower())) for c, s, u, t in passages]
    ENDS = ["", "u", "ū", "hi", "hiṃ", "hī", "hu", "ā", "i", "e", "ī", "jī"]
    rows, review = [], []
    seen = set()
    for r in valmiki_rows:
        if r["entity_type"] in ("place", "tribe", "concept"): continue
        tr = r["translit"]
        lem = re.sub(r"([mv])at$", r"\1āna", tr.lower())
        forms = awadhi_forms(lem)
        if lem.endswith("a"): forms |= {f[:-1] for f in forms if len(f) > 4}
        forms = {f for f in forms if len(f) >= 4}
        if not forms: continue
        key = (r["figure_id"], tr)
        if key in seen: continue
        seen.add(key)
        n, first = 0, None
        for c, s, u, ws in toks:
            k = sum(1 for w in ws for f in forms if w == f or (w.startswith(f) and w[len(f):] in ENDS))
            if k and first is None: first = (c, s, u)
            n += k
        if not n: continue
        short = min(len(f) for f in forms) <= 4
        conf = 0.6 if short else 0.75
        out = dict(r)
        word = sorted(forms, key=len)[0]
        out.update({"name": r["name"], "original": deva(word), "translit": word.capitalize(), "language": "Awadhi",
                    "corpus": "Ramcharitmanas", "text": first[1], "passage": first[0], "url": first[2], "occurrences": str(n),
                    "source": SRC_RCM + "; figure from the Valmiki Ramayana rows" + ("; " + SRC_WD if r["figure_id"].startswith("Q") else ""),
                    "confidence": f"{min(conf, float(r['confidence'])):.2f}"})
        if short or float(r["confidence"]) < 0.7:
            out["relation"] = (r["relation"] + "; " if r["relation"] else "") + "review: short form, may be an ordinary Awadhi word"
            review.append(out)
        else: rows.append(out)
    return rows, review

# Tirukkuṟaḷ (Project Madurai): it names almost no one. Only Indra (Kural 25) is a name in the text.
TK_URL = "https://www.projectmadurai.org/pm_etexts/utf8/pmuni0001.html"
def tirukkural():
    p = fetch(TK_URL, os.path.join(RAW, "tamil", "pmuni0001.html"))
    t = re.sub(r"<[^>]+>", "\n", open(p, encoding="utf-8", errors="replace").read()).replace("&nbsp;", " ")
    rows = []
    kurals = re.findall(r"([^\n]+)\n([^\n]+?)\s+(\d{1,4})\s*\n", t)
    q = wd_resolve({"indra": ("Indra", r"deity|god|Hindu|Vedic")})["indra"]
    for name, forms, fid, fig, rel in [("Indra", ("இந்திரன்", "இந்திரனே"), q["qid"] or "slug:hindu:indra", "Indra, king of the gods", "")]:
        hits = [int(n) for a, b, n in kurals if any(f in a + " " + b for f in forms)]
        if not hits: continue
        rows.append({"name": name, "figure_id": fid, "figure": fig, "sex": "boy", "original": "இந்திரன்", "translit": "Intiraṉ",
                     "language": "Tamil", "tradition": "Hindu", "subtradition": "", "corpus": "Tirukkural", "text": "Arattuppal",
                     "passage": f"Kural {hits[0]}", "url": TK_URL, "occurrences": str(len(hits)), "entity_type": "deity",
                     "name_role": "personal", "status": "attested", "relation": "",
                     "source": "Project Madurai, Tirukkural e-text; Wikidata (CC0)", "confidence": "0.85"})
    return rows


# ─────────────────────────────────────────────────────────────
# Wikidata look-ups for the Sikh and Jain figures (search by label, accepted only if the description fits; cached)
# ─────────────────────────────────────────────────────────────
WD_CACHE = os.path.join(RAW, "wd_lookup.json")

def _wd_cache():
    try: return json.load(open(WD_CACHE, encoding="utf-8"))
    except Exception: return {}

def _wd_get(url):
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read())
        except Exception as e:
            time.sleep(65 if "429" in str(e) else 3 + 5 * attempt)
    return {}

def wd_resolve(specs):
    """specs: {key: (search text, description regex)} → {key: {"qid", "sex"}} (qid "" when nothing fits)."""
    cache = _wd_cache(); changed = False
    for key, (q, rx) in specs.items():
        ck = f"search:{q}|{rx}"
        if ck in cache: continue
        time.sleep(1.0)
        j = _wd_get("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
            {"action": "wbsearchentities", "search": q, "language": "en", "format": "json", "limit": 7}))
        if "search" not in j: continue                       # failed request: try again next run
        hit = next((x["id"] for x in j["search"] if re.search(rx, x.get("description", "") + " " + x.get("label", ""), re.I)), "")
        cache[ck] = hit; changed = True
    qids = sorted({cache[f"search:{q}|{rx}"] for q, rx in specs.values()} - {""})
    need = [q for q in qids if f"sex:{q}" not in cache]
    for i in range(0, len(need), 40):
        time.sleep(1.0)
        j = _wd_get("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
            {"action": "wbgetentities", "ids": "|".join(need[i:i + 40]), "props": "claims", "format": "json"}))
        for q, e in j.get("entities", {}).items():
            sx = [c["mainsnak"].get("datavalue", {}).get("value", {}).get("id") for c in e.get("claims", {}).get("P21", [])]
            cache[f"sex:{q}"] = "boy" if "Q6581097" in sx else ("girl" if "Q6581072" in sx else ""); changed = True
    if changed: json.dump(cache, open(WD_CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    out = {}
    for key, (q, rx) in specs.items():
        qid = cache.get(f"search:{q}|{rx}", "")
        out[key] = {"qid": qid, "sex": cache.get(f"sex:{qid}", "") if qid else ""}
    return out


# ─────────────────────────────────────────────────────────────
# Sikh: Guru Granth Sahib (BaniDB)
# ─────────────────────────────────────────────────────────────
def ggs_lines():
    d = os.path.join(RAW, "ggs")
    os.makedirs(d, exist_ok=True)
    out = []
    for ang in range(1, 1431):
        p = os.path.join(d, f"ang{ang:04d}.json")
        if not (os.path.exists(p) and os.path.getsize(p) > 100):
            if os.path.exists(p): os.remove(p)
            fetch(f"https://api.banidb.com/v2/angs/{ang}/G", p)
        j = json.load(open(p, encoding="utf-8"))
        for v in j.get("page", []):
            out.append((ang, v["verse"]["unicode"], ((v.get("writer") or {}).get("english") or "")))
    return out

# key, name, figure, entity_type, role, translit, Wikidata search + description test, forms, writer tag, ambiguous, relation
# Forms are whole words as written (with case vowels). Ambiguous forms (ਰਾਮਦਾਸੁ "servant of Ram", ਨਾਮਾ "Name", ਧੰਨਾ "blessed",
# ਪਰਮਾਨੰਦ "supreme bliss") count only in a name context: the person's own bani, a heading, a Bhatt's eulogy, after ਗੁਰ/ਭਗਤ/ਕਹੁ, or
# in a line listing other bhagats.
SIKH = [
    ("nanak", "Nanak", "Guru Nanak, first Sikh Guru", "saint", "personal", "Nānak", ("Guru Nanak", r"first Sikh Guru|founder of Sikhism"),
     ["ਨਾਨਕ", "ਨਾਨਕੁ", "ਨਾਨਕਾ", "ਨਾਨਕੈ", "ਨਾਨਕਿ"], "Guru Nanak", False, "also the signature of Gurus 2-5 and 9"),
    ("angad", "Angad", "Guru Angad, second Sikh Guru", "saint", "personal", "Aṅgad", ("Guru Angad Dev", r"second Guru|Guru of Sikhism"),
     ["ਅੰਗਦ", "ਅੰਗਦੁ", "ਅੰਗਦਿ"], "Guru Angad", False, ""),
    ("lahna", "Lehna", "Guru Angad, second Sikh Guru", "saint", "personal", "Lahṇā", ("Guru Angad Dev", r"second Guru|Guru of Sikhism"),
     ["ਲਹਣਾ", "ਲਹਣੇ", "ਲਹਣੈ"], "", False, "birth name of Guru Angad"),
    ("amardas", "Amar Das", "Guru Amar Das, third Sikh Guru", "saint", "personal", "Amar Dās", ("Guru Amar Das", r"Sikh"),
     ["ਅਮਰਦਾਸ", "ਅਮਰਦਾਸੁ", "ਅਮਰਦਾਸਿ", "ਅਮਰਦਾਸੈ"], "Guru Amar", False, ""),
    ("ramdas", "Ram Das", "Guru Ram Das, fourth Sikh Guru", "saint", "personal", "Rām Dās", ("Guru Ram Das", r"Sikh"),
     ["ਰਾਮਦਾਸ", "ਰਾਮਦਾਸੁ", "ਰਾਮਦਾਸਿ", "ਰਾਮਦਾਸੈ"], "Guru Raam", True, ""),
    ("arjan", "Arjan", "Guru Arjan, fifth Sikh Guru", "saint", "personal", "Arjan", ("Guru Arjan", r"Sikh"),
     ["ਅਰਜੁਨ", "ਅਰਜੁਨੁ", "ਅਰਜਨ", "ਅਰਜਨੁ"], "Guru Arjan", True, "written ਅਰਜੁਨ (Arjun) in the Bhatts' swayyas"),
    ("kabir", "Kabir", "Kabir, bhagat", "saint", "personal", "Kabīr", ("Kabir", r"poet|saint|mystic"),
     ["ਕਬੀਰ", "ਕਬੀਰਾ", "ਕਬੀਰੁ", "ਕਬੀਰੈ", "ਕਬੀਰਿ"], "Bhagat Kabeer", False, ""),
    ("namdev", "Namdev", "Namdev, bhagat", "saint", "personal", "Nāmdev", ("Namdev", r"poet|saint|sant"),
     ["ਨਾਮਦੇਵ", "ਨਾਮਦੇਉ", "ਨਾਮਦੇਇ", "ਨਾਮਦੇਅ", "ਨਾਮਾ"], "Bhagat Naam", True, "also written ਨਾਮਾ (Nama)"),
    ("ravidas", "Ravidas", "Ravidas, bhagat", "saint", "personal", "Ravidās", ("Ravidas", r"poet|saint|guru|mystic|bhakti|Buddhism"),
     ["ਰਵਿਦਾਸ", "ਰਵਿਦਾਸੁ", "ਰਵਿਦਾਸਾ", "ਰਵਿਦਾਸਿ"], "Bhagat Ravi", False, ""),
    ("farid", "Farid", "Baba Farid (Shaikh Farid), bhagat", "saint", "personal", "Farīd", ("Baba Farid", r"preacher|mystic|saint|Sufi"),
     ["ਫਰੀਦ", "ਫਰੀਦਾ", "ਫਰੀਦੁ"], "Bhagat Sheikh", False, ""),
    ("trilochan", "Trilochan", "Trilochan, bhagat", "saint", "personal", "Trilocan", ("Bhagat Trilochan", r"saint"),
     ["ਤ੍ਰਿਲੋਚਨ", "ਤ੍ਰਿਲੋਚਨੁ", "ਤਿਲੋਚਨ", "ਤਿਲੋਚਨੁ"], "Bhagat Trilochan", False, ""),
    ("beni", "Beni", "Beni, bhagat", "saint", "personal", "Beṇī", ("Bhagat Beni", r"saint|bhagat"), ["ਬੇਣੀ", "ਬੇਣੀਆ"], "Bhagat Beni", False, ""),
    ("dhanna", "Dhanna", "Dhanna, bhagat", "saint", "personal", "Dhannā", ("Dhanna Bhagat", r"saint|bhagat|mystic|poet"),
     ["ਧੰਨਾ", "ਧੰਨੈ"], "Bhagat Dhannaa", True, ""),
    ("jaidev", "Jaidev", "Jaidev (Jayadeva), bhagat", "saint", "personal", "Jaidev", ("Jayadeva", r"poet"),
     ["ਜੈਦੇਉ", "ਜੈਦੇਵ", "ਜੈਦੇਵੁ"], "Bhagat Jaidev", False, ""),
    ("pipa", "Pipa", "Pipa, bhagat", "saint", "personal", "Pīpā", ("Pipa Bhagat", r"saint|mystic|poet|bhakti"), ["ਪੀਪਾ"], "Bhagat Peepaa", False, ""),
    ("sain", "Sain", "Sain, bhagat", "saint", "personal", "Sain", ("Bhagat Sain", r"saint|bhagat|poet"), ["ਸੈਨੁ", "ਸੈਣੁ"], "Bhagat Sain", True, ""),
    ("sadhna", "Sadhna", "Sadhna, bhagat", "saint", "personal", "Sadhnā", ("Bhagat Sadhna", r"saint|bhagat|poet"), ["ਸਧਨਾ"], "Bhagat Saadhnaa", False, ""),
    ("ramanand", "Ramanand", "Ramanand, bhagat", "saint", "personal", "Rāmānand", ("Ramananda", r"saint|poet|guru|Vaishnav"),
     ["ਰਾਮਾਨੰਦ", "ਰਾਮਾਨੰਦੁ"], "Bhagat Raamaanand", False, ""),
    ("parmanand", "Parmanand", "Parmanand, bhagat", "saint", "personal", "Parmānand", ("Bhagat Parmanand", r"saint|bhagat|poet"),
     ["ਪਰਮਾਨੰਦ", "ਪਰਮਾਨੰਦੁ"], "Bhagat Parmaanand", True, ""),
    ("surdas", "Surdas", "Surdas, bhagat", "saint", "personal", "Sūrdās", ("Surdas", r"poet|saint"), ["ਸੂਰਦਾਸ", "ਸੂਰਦਾਸੁ"], "Bhagat Surdaas", False, ""),
    ("bhikhan", "Bhikhan", "Bhikhan, bhagat", "saint", "personal", "Bhīkhan", ("Bhagat Bhikhan", r"saint|bhagat|Sufi|poet"),
     ["ਭੀਖਨ", "ਭੀਖਨੁ"], "Bhagat Bheekhan", False, ""),
    ("mardana", "Mardana", "Bhai Mardana, companion of Guru Nanak", "disciple", "personal", "Mardānā", ("Bhai Mardana", r"Sikh|companion|rabab|Nanak"),
     ["ਮਰਦਾਨਾ", "ਮਰਦਾਨੇ"], "Bhai Mardana", False, ""),
    ("waheguru", "Waheguru", "Waheguru, God", "deity", "divine", "Vāhigurū", None, ["ਵਾਹਿਗੁਰੂ", "ਵਾਹਗੁਰੂ", "ਵਾਹੁਗੁਰੂ"], "", False, "name of God"),
    ("hari", "Hari", "Hari, God", "deity", "divine", "Hari", None, ["ਹਰਿ", "ਹਰੀ"], "", False, "name of God"),
    ("gobind", "Gobind", "Gobind, God", "deity", "divine", "Gobind", None,
     ["ਗੋਬਿੰਦ", "ਗੋਬਿੰਦੁ", "ਗੋਬਿੰਦਾ", "ਗੋਬਿਦ", "ਗੋਬਿਦੁ", "ਗੋਬਿਦਾ"], "", False, "name of God"),
    ("govind", "Govind", "Gobind, God", "deity", "divine", "Govind", None, ["ਗੋਵਿੰਦ", "ਗੋਵਿੰਦੁ", "ਗੋਵਿੰਦਾ", "ਗੋਵਿਦ", "ਗੋਵਿਦੁ"], "", False, "name of God; spelling variant of Gobind"),
    ("ram", "Ram", "Ram, God", "deity", "divine", "Rām", None, ["ਰਾਮ", "ਰਾਮੁ", "ਰਾਮਾ", "ਰਾਮੈ"], "", False, "name of God, the all-pervading (not the epic king)"),
    ("gopal", "Gopal", "Gopal, God", "deity", "divine", "Gopāl", None, ["ਗੋਪਾਲ", "ਗੋਪਾਲੁ", "ਗੋਪਾਲਾ"], "", False, "name of God"),
    ("narayan", "Narayan", "Narayan, God", "deity", "divine", "Nārāiṇ", None, ["ਨਾਰਾਇਣ", "ਨਾਰਾਇਣੁ", "ਨਾਰਾਇਣਾ", "ਨਰਾਇਣ", "ਨਰਾਇਣੁ"], "", False, "name of God"),
    ("murari", "Murari", "Murari, God", "deity", "divine", "Murāri", None, ["ਮੁਰਾਰਿ", "ਮੁਰਾਰੀ", "ਮੁਰਾਰੇ"], "", False, "name of God"),
    ("madho", "Madho", "Madho (Madhav), God", "deity", "divine", "Mādho", None, ["ਮਾਧੋ", "ਮਾਧਉ", "ਮਾਧਵ", "ਮਾਧਵੇ"], "", False, "name of God"),
    ("damodar", "Damodar", "Damodar, God", "deity", "divine", "Dāmodar", None, ["ਦਾਮੋਦਰ", "ਦਾਮੋਦਰੁ"], "", False, "name of God"),
    ("mukand", "Mukand", "Mukand (Mukunda), God", "deity", "divine", "Mukand", None, ["ਮੁਕੰਦ", "ਮੁਕੰਦੁ", "ਮੁਕੰਦਾ", "ਮੁਕੰਦੇ"], "", False, "name of God"),
    ("banwari", "Banwari", "Banwari, God", "deity", "divine", "Banvārī", None, ["ਬਨਵਾਰੀ", "ਬਨਵਾਰੀਆ"], "", False, "name of God"),
    ("kartar", "Kartar", "Kartar, God the Creator", "deity", "divine", "Kartār", None, ["ਕਰਤਾਰ", "ਕਰਤਾਰੁ", "ਕਰਤਾਰਾ", "ਕਰਤਾਰੈ"], "", False, "name of God (the Creator)"),
    ("nirankar", "Nirankar", "Nirankar, the Formless One", "deity", "divine", "Nirankār", None, ["ਨਿਰੰਕਾਰ", "ਨਿਰੰਕਾਰੁ", "ਨਿਰੰਕਾਰਾ"], "", False, "name of God (the Formless)"),
    ("bithal", "Bithal", "Bithal (Vitthal), God", "deity", "divine", "Bīṭhal", None, ["ਬੀਠਲ", "ਬੀਠਲੁ", "ਬੀਠੁਲੁ", "ਬੀਠੁਲ"], "", False, "name of God in Namdev's bani"),
    ("raghunath", "Raghunath", "Raghunath, God", "deity", "divine", "Raghunāth", None, ["ਰਘੁਨਾਥ", "ਰਘੁਨਾਥੁ", "ਰਘੁਨਾਥਾ"], "", False, "name of God"),
    ("allah", "Allah", "Allah, God", "deity", "divine", "Allah", None, ["ਅਲਹ", "ਅਲਾਹ", "ਅਲਹੁ", "ਅਲਾਹੁ"], "", False, "name of God"),
]
GGS_URL = "https://www.sikhitothemax.org/ang?ang={}&source=G"
SRC_BANIDB = "Guru Granth Sahib text via BaniDB API (Khalis Foundation)"
NAME_CUE = {"ਗੁਰ", "ਗੁਰੂ", "ਗੁਰਿ", "ਗੁਰੁ", "ਭਗਤ", "ਭਗਤੁ", "ਕਹੁ", "ਕਹਤ", "ਕਹੈ", "ਭਣੈ", "ਪ੍ਰਣਵੈ", "ਬਿਨਵੰਤਿ", "ਸੇਖ", "ਜੀਉ", "ਜੀ"}

def sikh():
    lines = ggs_lines()
    print(f"  Guru Granth Sahib: {len(lines)} lines, {len({a for a, _, _ in lines})} Angs", file=sys.stderr)
    split = lambda t: [w for w in re.split(r"[\s॥।ੴ0-9੦-੯.,;:!?\"'()\[\]]+", t) if w]
    toks = [(ang, split(txt), wr) for ang, txt, wr in lines]
    person_forms = {f for row in SIKH if row[4] == "personal" and row[0] != "nanak" for f in row[7]}   # Nanak signs every Guru's line
    wd = wd_resolve({row[0]: row[6] for row in SIKH if row[6]})
    rows = []
    for key, name, figure, et, role, tr, spec, forms, wtag, amb, rel in SIKH:
        fs = set(forms); n = 0; first = None
        for ang, ws, wr in toks:
            for i, w in enumerate(ws):
                if w not in fs: continue
                if amb:
                    others = sum(1 for x in ws if x in person_forms and x not in fs)
                    ok = (wtag and wr.startswith(wtag)) or not wr or wr.startswith("Bhatt") or others >= 1 \
                         or (i > 0 and ws[i - 1] in NAME_CUE) or (i + 1 < len(ws) and ws[i + 1] in NAME_CUE)
                    if not ok: continue
                n += 1
                if first is None: first = ang
        if not n: continue
        q = wd.get(key, {"qid": "", "sex": ""})
        fid = q["qid"] or f"slug:sikh:{key if role == 'divine' else fold(name)}"
        if key == "lahna": fid = wd.get("angad", q)["qid"] or "slug:sikh:angad"
        if key == "govind": fid = "slug:sikh:gobind"
        rows.append({"name": name, "figure_id": fid, "figure": figure, "sex": q["sex"] if role != "divine" else "",
                     "original": forms[0], "translit": tr, "language": "Gurmukhi/Punjabi", "tradition": "Sikh", "subtradition": "",
                     "corpus": "Guru Granth Sahib", "text": "", "passage": f"Ang {first}", "url": GGS_URL.format(first),
                     "occurrences": str(n), "entity_type": et, "name_role": role, "status": "attested", "relation": rel,
                     "source": SRC_BANIDB + ("; " + SRC_WD if q["qid"] else ""),
                     "confidence": "0.90" if not amb else "0.80"})
    # Guru Tegh Bahadur: his bani is included (Mahala 9) but his name is not written in the text
    first9 = next((ang for ang, _, wr in toks if wr.startswith("Guru Tegh")), None)
    if first9:
        q = wd_resolve({"tegh": ("Guru Tegh Bahadur", r"Sikh")})["tegh"]
        rows.append({"name": "Tegh Bahadur", "figure_id": q["qid"] or "slug:sikh:teghbahadur", "figure": "Guru Tegh Bahadur, ninth Sikh Guru",
                     "sex": q["sex"], "original": "ਤੇਗ ਬਹਾਦਰ", "translit": "Tegh Bahādur", "language": "Gurmukhi/Punjabi",
                     "tradition": "Sikh", "subtradition": "", "corpus": "Guru Granth Sahib", "text": "", "passage": f"Ang {first9}",
                     "url": GGS_URL.format(first9), "occurrences": "", "entity_type": "saint", "name_role": "personal",
                     "status": "association", "relation": "author of the Mahala 9 bani; signs as Nanak, his own name is not in the text",
                     "source": SRC_BANIDB + ("; " + SRC_WD if q["qid"] else ""), "confidence": "0.90"})
    return rows


# ─────────────────────────────────────────────────────────────
# Jain: Kalpa Sutra, tr. Hermann Jacobi, SBE 22 (1884)
# ─────────────────────────────────────────────────────────────
KALPA_SCAN = "https://archive.org/download/jainasutrasparti029233mbp/jainasutrasparti029233mbp_djvu.txt"
KALPA_URL = "https://archive.org/details/jainasutrasparti029233mbp"
SRC_KALPA = "Kalpa Sutra, tr. H. Jacobi, Sacred Books of the East 22 (1884, public domain), archive.org OCR"
# key, name, figure, entity_type, translit, Jacobi's spellings folded to ASCII (his g = j, k = c), Wikidata search, relation
JAIN = [
    ("mahavira", "Mahavira", "Mahavira (Vardhamana), 24th Tirthankara", "saint", "Mahāvīra", ["mahavira"], ("Mahavira", r"religious leader|t[iī]rtha|jain"), ""),
    ("vardhamana", "Vardhamana", "Mahavira (Vardhamana), 24th Tirthankara", "saint", "Vardhamāna", ["vardhamana"], None, "birth name of Mahavira"),
    ("trishala", "Trishala", "Trishala, mother of Mahavira", "human", "Triśalā", ["trisala"], ("Trishala", r"mahavira|mother"), ""),
    ("siddhartha", "Siddhartha", "Siddhartha, father of Mahavira", "royal", "Siddhārtha", ["siddhartha"], ("Siddhartha of Kundagrama", r"mahavira|father"), ""),
    ("devananda", "Devananda", "Devananda, Brahmin mother of Mahavira's first conception", "human", "Devānandā", ["devananda"], ("Devananda", r"mahavira|jain"), ""),
    ("rishabhadatta", "Rishabhadatta", "Rishabhadatta, Brahmin husband of Devananda", "human", "Ṛṣabhadatta", ["rishabhadatta"], None, ""),
    ("nandivardhana", "Nandivardhana", "Nandivardhana, elder brother of Mahavira", "royal", "Nandivardhana", ["nandivardhana"], None, ""),
    ("yashoda", "Yashoda", "Yashoda, wife of Mahavira", "human", "Yaśodā", ["yasoda"], None, ""),
    # Supārśva is both Mahavira's uncle and the 7th Tirthankara; the scan only yields the Tirthankara list (§§185-203)
    ("suparshva", "Suparshva", "Suparshva, 7th Tirthankara", "saint", "Supārśva", ["suparsva"], ("Suparshvanatha", r"t[iī]rtha"), ""),
    ("sudarshana", "Sudarshana", "Sudarshana, sister of Mahavira", "human", "Sudarśanā", ["sudarsana"], None, ""),
    ("anojja", "Anojja", "Anojja (Priyadarshana), daughter of Mahavira", "human", "Aṇojjā", ["anogga"], None, ""),
    ("indrabhuti", "Indrabhuti", "Indrabhuti Gautama, first ganadhara of Mahavira", "disciple", "Indrabhūti", ["indrabhuti"], ("Indrabhuti Gautama", r"gan[a]?dhara|disciple|mahavira"), ""),
    ("agnibhuti", "Agnibhuti", "Agnibhuti, ganadhara", "disciple", "Agnibhūti", ["agnibhuti"], None, ""),
    ("vayubhuti", "Vayubhuti", "Vayubhuti, ganadhara", "disciple", "Vāyubhūti", ["vayubhuti"], None, ""),
    ("vyakta", "Vyakta", "Arya Vyakta, ganadhara", "disciple", "Vyakta", ["vyakta"], None, ""),
    ("sudharman", "Sudharman", "Arya Sudharman, ganadhara", "disciple", "Sudharman", ["sudharman"], ("Sudharmaswami", r"gan[a]?dhara|disciple|jain"), ""),
    ("manditaputra", "Manditaputra", "Manditaputra, ganadhara", "disciple", "Maṇḍitaputra", ["manditaputra", "mandikaputra"], None, ""),
    ("mauryaputra", "Mauryaputra", "Mauryaputra, ganadhara", "disciple", "Mauryaputra", ["mauryaputra"], None, ""),
    ("akampita", "Akampita", "Akampita, ganadhara", "disciple", "Akampita", ["akampita"], None, ""),
    ("acalabhrata", "Achalabhrata", "Achalabhrata, ganadhara", "disciple", "Acalabhrātṛ", ["akalabhratri", "akalabhrata"], None, ""),
    ("metarya", "Metarya", "Metarya, ganadhara", "disciple", "Metārya", ["metarya"], None, ""),
    ("prabhasa", "Prabhasa", "Prabhasa, ganadhara", "disciple", "Prabhāsa", ["prabhasa"], None, ""),
    ("jambu", "Jambu", "Jambu (Jambusvamin), disciple of Sudharman", "disciple", "Jambū", ["gambu", "gambunaman"], ("Jambuswami", r"jain|disciple|kevali"), ""),
    ("bhadrabahu", "Bhadrabahu", "Bhadrabahu, sthavira", "sage", "Bhadrabāhu", ["bhadrabahu"], ("Bhadrabahu", r"jain|monk|acharya"), ""),
    ("sthulabhadra", "Sthulabhadra", "Sthulabhadra, sthavira", "sage", "Sthūlabhadra", ["sthulabhadra"], ("Sthulabhadra", r"jain|monk"), ""),
    ("parshva", "Parshva", "Parshvanatha, 23rd Tirthankara", "saint", "Pārśva", ["parsva"], ("Parshvanatha", r"t[iī]rtha"), ""),
    ("arishtanemi", "Arishtanemi", "Arishtanemi (Neminatha), 22nd Tirthankara", "saint", "Ariṣṭanemi", ["arishtanemi"], ("Neminatha", r"t[iī]rtha"), ""),
    ("rishabha", "Rishabha", "Rishabha (Adinatha), 1st Tirthankara", "saint", "Ṛṣabha", ["rishabha"], ("Rishabhanatha", r"t[iī]rtha"), ""),
    ("ajita", "Ajita", "Ajita, 2nd Tirthankara", "saint", "Ajita", ["agita"], ("Ajitanatha", r"t[iī]rtha"), ""),
    ("sambhava", "Sambhava", "Sambhava, 3rd Tirthankara", "saint", "Sambhava", ["sambhava"], ("Sambhavanatha", r"t[iī]rtha"), ""),
    ("abhinandana", "Abhinandana", "Abhinandana, 4th Tirthankara", "saint", "Abhinandana", ["abhinandana"], ("Abhinandananatha", r"t[iī]rtha"), ""),
    ("sumati", "Sumati", "Sumati, 5th Tirthankara", "saint", "Sumati", ["sumati"], ("Sumatinatha", r"t[iī]rtha"), ""),
    ("padmaprabha", "Padmaprabha", "Padmaprabha, 6th Tirthankara", "saint", "Padmaprabha", ["padmaprabha"], ("Padmaprabha", r"t[iī]rtha"), ""),
    ("chandraprabha", "Chandraprabha", "Chandraprabha, 8th Tirthankara", "saint", "Candraprabha", ["kandraprabha", "chandraprabha"], ("Chandraprabha", r"t[iī]rtha"), ""),
    ("suvidhi", "Suvidhi", "Suvidhi (Pushpadanta), 9th Tirthankara", "saint", "Suvidhi", ["suvidhi", "pushpadanta"], ("Pushpadanta", r"t[iī]rtha"), ""),
    ("shitala", "Shitala", "Shitala, 10th Tirthankara", "saint", "Śītala", ["sitala"], ("Shitalanatha", r"t[iī]rtha"), ""),
    ("shreyamsa", "Shreyamsa", "Shreyamsa, 11th Tirthankara", "saint", "Śreyāṃsa", ["sreyamsa"], ("Shreyansanatha", r"t[iī]rtha"), ""),
    ("vasupujya", "Vasupujya", "Vasupujya, 12th Tirthankara", "saint", "Vāsupūjya", ["vasupugya", "vasupujya"], ("Vasupujya", r"t[iī]rtha"), ""),
    ("vimala", "Vimala", "Vimala, 13th Tirthankara", "saint", "Vimala", ["vimala"], ("Vimalanatha", r"t[iī]rtha"), ""),
    ("ananta", "Ananta", "Ananta, 14th Tirthankara", "saint", "Ananta", ["ananta"], ("Anantanatha", r"t[iī]rtha"), ""),
    ("shanti", "Shanti", "Shanti, 16th Tirthankara", "saint", "Śānti", ["santi"], ("Shantinatha", r"t[iī]rtha"), ""),
    ("kunthu", "Kunthu", "Kunthu, 17th Tirthankara", "saint", "Kunthu", ["kunthu"], ("Kunthunatha", r"t[iī]rtha"), ""),
    ("malli", "Malli", "Malli, 19th Tirthankara", "saint", "Malli", ["malli"], ("Mallinatha", r"t[iī]rtha"), "Shvetambaras hold Malli was a woman"),
    ("munisuvrata", "Munisuvrata", "Munisuvrata, 20th Tirthankara", "saint", "Munisuvrata", ["munisuvrata", "suvrata"], ("Munisuvrata", r"t[iī]rtha"), ""),
    ("nami", "Nami", "Nami, 21st Tirthankara", "saint", "Nami", ["nami"], ("Naminatha", r"t[iī]rtha"), ""),
]

def _ocr_dist(tok, name, cap):
    """Edit distance where a non-letter OCR glyph in the token matches any letter for free."""
    n, m = len(tok), len(name)
    if abs(n - m) > cap: return cap + 1
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        cur = [i] + [0] * m; best = cur[0]
        for j in range(1, m + 1):
            sub = 0 if (tok[i - 1] == name[j - 1] or not tok[i - 1].isalpha()) else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + sub); best = min(best, cur[j])
        if best > cap: return cap + 1
        prev = cur
    return prev[m]

def jain():
    p = fetch(KALPA_SCAN, os.path.join(RAW, "kalpa", "mbp.txt"))
    lines = open(p, encoding="utf-8", errors="replace").read().split("\n")
    start = max(i for i, l in enumerate(lines) if re.match(r"\s*THE KALPA S\S?TRA\s*$", l))
    end = next(i for i in range(start, len(lines)) if re.match(r"\s*INDEX\.?\s*$", lines[i]))
    body, sec_at = [], {}
    for i in range(start, end):
        l = lines[i]
        if re.match(r"\s*LIST OF THE STHAVIRAS\.?\s*$", l) and "List of the Sthaviras" not in sec_at.values(): sec_at[len(body)] = "List of the Sthaviras"
        if re.match(r"\s*RULES FOR YATIS\.?\s*$", l) and "Rules for Yatis" not in sec_at.values(): sec_at[len(body)] = "Rules for Yatis"
        if re.search(r"(LIVES OF THE|KALPA S\S?TRA|LIST OF THE STHAVIRAS|RULES FOR YATIS)\.?\s*[\dOlI$\s]*$", l): continue   # running heads
        if re.match(r"\s*([\d\*\+§f]|\d\s?\d)\s{1,2}\S", l) and not re.match(r"\s*\d+\)", l): continue                       # footnotes
        body.append(l)
    # paragraph numbers close their paragraph, "(31)"; OCR turns 1 into i/l and 0 into O
    rows_out, para, sec, last_num = [], {}, "Lives of the Jinas", 0
    marks = []
    for li, l in enumerate(body):
        if li in sec_at: sec = sec_at[li]; last_num = 0
        for m in re.finditer(r"\((?:[\dilIoO]{1,3}\s?-\s?)?([\dilIoO]{1,3})\)", l):
            v = m.group(1).translate(str.maketrans("ilIoO", "11100"))
            num = int(v)
            if 0 < num - last_num <= 40: last_num = num; marks.append((li, sec, num))
    def where(li):
        for mli, msec, num in marks:
            if mli >= li: return msec, num
        return (marks[-1][1], marks[-1][2]) if marks else ("Lives of the Jinas", 0)
    names = {}
    for row in JAIN:
        for sp in row[5]: names.setdefault(sp, row[0])
    hits = collections.defaultdict(list)
    for li, l in enumerate(body):
        for raw in re.findall(r"[^\s,;:!?()\[\]'\"’\-]+", l):
            tok = unicodedata.normalize("NFD", raw.lower())
            tok = "".join(c for c in tok if not unicodedata.combining(c)).rstrip(".")
            junk = len(tok) - len(tok.lstrip("/.^*&$#%@0123456789?"))      # OCR debris before a capital: /frshabha, .sltala
            tok = tok[junk:] if junk else tok
            letters = sum(c.isalpha() for c in tok)
            if len(tok) < 4 or letters < len(tok) - 2: continue
            for sp, key in names.items():
                if letters < len(sp) - 3: continue
                if not junk and tok[0] != sp[0]: continue
                cap = (0 if len(sp) <= 6 else (1 if len(sp) <= 8 else 2)) + (1 if junk and len(sp) >= 7 else 0)
                if _ocr_dist(tok, sp, cap) <= cap: hits[key].append(li)
    wd = wd_resolve({row[0]: row[6] for row in JAIN if row[6]})
    rows = []
    for key, name, figure, et, tr, spellings, spec, rel in JAIN:
        if not hits.get(key): continue
        sec, num = where(hits[key][0])
        q = wd.get(key, {"qid": "", "sex": ""})
        fid = q["qid"] or f"slug:jain:{key}"
        if key == "vardhamana": fid = wd.get("mahavira", q)["qid"] or "slug:jain:mahavira"; q = wd.get("mahavira", q)
        if key == "gautama": fid = wd.get("indrabhuti", q)["qid"] or "slug:jain:indrabhuti"; q = wd.get("indrabhuti", q)
        rows.append({"name": name, "figure_id": fid, "figure": figure, "sex": q["sex"], "original": "", "translit": tr,
                     "language": "Prakrit", "tradition": "Jain", "subtradition": "Shvetambara", "corpus": "Kalpa Sutra",
                     "text": sec, "passage": f"Kalpa Sutra, {sec} §{num}", "url": KALPA_URL, "occurrences": str(len(hits[key])),
                     "entity_type": et, "name_role": "personal", "status": "attested", "relation": rel,
                     "source": SRC_KALPA + ("; " + SRC_WD if q["qid"] else ""), "confidence": "0.75"})
    return rows


def yoga_sutra_fix(rows, review):
    """Yoga Sūtra 1.23-26: īśvara is 'the Lord', a special puruṣa — a title, not a personal name or another god's epithet.
    Patañjali is named only in colophons, not in the sūtras."""
    rows = [r for r in rows if not (r["corpus"] == "Yoga Sutras" and r["translit"] in ("Īśvara", "Iśvara"))]
    review = [r for r in review if not (r["corpus"] == "Yoga Sutras" and r["translit"] in ("Īśvara", "Iśvara"))]
    vs = load_dcs_text("Yogasūtra", "YS", "Yoga Sutras")
    hit = [v for v in vs if any(t[0] == "īśvara" for t in v[4])]
    if hit:
        rows.append({"name": "Ishvar", "figure_id": "slug:hindu:ishvara-yoga", "figure": "Ishvara, the Lord of the Yoga Sutras (a special purusha)",
                     "sex": "", "original": "ईश्वर", "translit": "Īśvara", "language": "Sanskrit", "tradition": "Hindu", "subtradition": "",
                     "corpus": "Yoga Sutras", "text": "Yoga Sutras", "passage": hit[0][0], "url": hit[0][2],
                     "occurrences": str(sum(1 for v in vs for t in v[4] if t[0] == "īśvara")), "entity_type": "deity",
                     "name_role": "title", "status": "attested", "relation": "‘the Lord’ (YS 1.24); a title, not a personal name",
                     "source": f"{SRC_DCS}, Yoga Sutras (complete)", "confidence": "0.80"})
    q = wd_resolve({"patanjali": ("Patanjali", r"yoga|sage|author|grammarian")})["patanjali"]
    rows.append({"name": "Patanjali", "figure_id": q["qid"] or "slug:hindu:patanjali", "figure": "Patañjali, compiler of the Yoga Sutras", "sex": "boy",
                 "original": "पतञ्जलि", "translit": "Patañjali", "language": "Sanskrit", "tradition": "Hindu", "subtradition": "",
                 "corpus": "Yoga Sutras", "text": "Yoga Sutras", "passage": "", "url": "", "occurrences": "",
                 "entity_type": "sage", "name_role": "personal", "status": "association",
                 "relation": "traditional author; not named in the sutras themselves", "source": "Wikidata (CC0)" if q["qid"] else "", "confidence": "0.90"})
    return rows, review

def write(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\t".join(COLS) + "\n")
        for r in rows:
            f.write("\t".join(str(r.get(c, "")).replace("\t", " ").replace("\n", " ") for c in COLS) + "\n")   # _split etc. not written

def main():
    hints = scripture_hints()
    order = {"Bhagavad Gita": 0, "Valmiki Ramayana": 1, "Mahabharata": 2, "Guru Granth Sahib": 3, "Kalpa Sutra": 4}
    rows, review, stats = hindu(hints)
    rows, review = yoga_sutra_fix(rows, review)
    rr, rv = ramcharitmanas([r for r in rows if r["corpus"] == "Valmiki Ramayana"], hints)
    rows += rr; review += rv; stats[("Ramcharitmanas", "name")] += len(rr); stats[("Ramcharitmanas", "review")] += len(rv)
    tk = tirukkural(); rows += tk; stats[("Tirukkural", "name")] += len(tk)
    rows += sikh(); rows += jain()
    key = lambda r: (order.get(r["corpus"], 9), r["corpus"], r["text"] if r.get("_split") else "",
                     -float(r["confidence"]), -int(r["occurrences"] or 0), r["name"])
    kkey = lambda r: (r["corpus"], r["text"] if r.get("_split") else "", r["name"], r["figure_id"])
    def dedupe(rs):
        best = {}
        for r in rs:
            kk = kkey(r)
            if kk not in best or int(r["occurrences"] or 0) > int(best[kk]["occurrences"] or 0): best[kk] = r
        return list(best.values())
    rows, review = dedupe(rows), dedupe(review)
    seen = {kkey(r) for r in rows}
    review = [r for r in review if kkey(r) not in seen]
    rows.sort(key=key); review.sort(key=key)
    write(OUT, rows); write(REVIEW, review)
    print(f"wrote {len(rows)} rows → {OUT}; {len(review)} → {REVIEW}", file=sys.stderr)
    for k, v in sorted(stats.items()): print(f"  {k[0]:18} {k[1]:8} {v}", file=sys.stderr)

if __name__ == "__main__":
    main()
