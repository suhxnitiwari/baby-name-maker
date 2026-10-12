# Builds data/hindu-names.json: Hindu given names, from the scriptures and from what Indian families give today, each with
# its native script and a Latin spelling a source gives. Storied rows, 11 slots:
#   [name, sex g|b|e, culture, language, religions, meaning, source_sentence, texts, "real", also, ease]
# Rows are sorted by ease (1 easy … 3 hard), then name. Nothing is guessed: a spelling, a sex and a meaning are kept only
# when a source gives them.
#
# Sources
#   Monier-Williams Sanskrit-English Dictionary (1899), Cologne Digital Sanskrit Dictionaries (raw/sacred/mw/xml/mw.xml,
#     the same data as github.com/sanskrit-lexicon/csl-orig; that repository is licensed CC BY-SA 4.0, the TEI header
#     shipped inside mw.xml still says CC BY-NC-SA 3.0). Every headword marked as a person's name ("N. of a man / woman /
#     king / sage", or an epithet of a deity), and every cited noun or adjective, with its gloss and page.
#     Latin spellings come from the headword by fixed rules only: diacritics dropped (ā→a, ś/ṣ→sh, c→ch, ṛ→ri, ṃ→m/n), the
#     Hindi form without the final short -a for masculine words (Kapila → Kapil), and ī→ee / ū→oo as variants (Neel, Roopa).
#   English Wiktionary (CC BY-SA 4.0): every "<language> (male|female|unisex) given names" entry for the languages of India,
#     and every "English … given names from <Indian language>" entry (these give the spelling Indian families use).
#   Wikidata (CC0): given-name items in an Indian language (P407, or a native label P1705 in one), and given names borne by
#     Indian citizens (P27 India, P735); English label = Latin spelling, Indic-script label = native form.
# What is already on the site is read, not changed: data/names-db.tsv, data/names-extra.tsv, data/culture-names.json,
#   names.js, data/native-forms.json, data/sacred/indic*.tsv. A name already in names.js (hand entries) is left alone.
#
# Downloads are cached under raw/hindu/.
#   python3 scripts/build_hindu_names.py            (downloads what raw/hindu/ lacks)
#   python3 scripts/build_hindu_names.py --offline  (cached files only)
import collections, csv, glob, html, json, os, re, sys, time, unicodedata, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build_sacred_indic as S                      # script helpers (SLP1/IAST/Devanagari, everyday romanization)

RAW = os.path.join(ROOT, "raw", "hindu"); os.makedirs(RAW, exist_ok=True)
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "hindu-names.json")
REPORT = os.path.join(RAW, "report.json")
MW_XML = os.path.join(ROOT, "raw", "sacred", "mw", "xml", "mw.xml")
OFFLINE = "--offline" in sys.argv
UA = "Lullabyte/1.0 (https://github.com/suhxnitiwari/baby-name-maker; suhxnitiwari@gmail.com)"
fold = S.fold
T0 = time.time()

INDIAN = {"Hindi", "Bengali", "Gujarati", "Tamil", "Telugu", "Marathi", "Punjabi", "Odia", "Kannada", "Nepali", "Sindhi", "Malayali",
          "Malayalam", "Assamese", "Indian", "Sanskrit", "Konkani", "South Asian", "Urdu", "Maithili", "Bhojpuri", "Bollywood"}
MODERN = ["Hindi", "Marathi", "Gujarati", "Bengali", "Punjabi", "Telugu", "Kannada", "Malayali", "Odia", "Nepali", "Tamil",
          "Assamese", "Konkani", "Sindhi", "Maithili", "Bhojpuri"]
# cultures whose names often come from Sanskrit themselves: a shared spelling there is no "unrelated" name
SANSKRIT_LINKED = {"Sinhalese", "Thai", "Indonesian", "Javanese", "Balinese", "Khmer", "Lao", "Burmese", "Malay", "Tibetan",
                   "Sundanese", "Old Javanese", "Mongolian", "Pali", "Buddhist", "Jain", "Sikh", "Fijian Indian"}


def get(url, path, data=None, headers=None, tries=6):
    if os.path.exists(path) and os.path.getsize(path) > 0: return open(path, "rb").read()
    if OFFLINE: return b""
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
    for a in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=180) as r: body = r.read()
            os.makedirs(os.path.dirname(path), exist_ok=True); open(path, "wb").write(body); return body
        except Exception as e:
            if a == tries - 1: print("  failed", url[:120], e, file=sys.stderr); return b""
            time.sleep(60 if "429" in str(e) else 3 + 5 * a)


def an(w): return "An" if w[:1] in "AEIOU" else "A"


# ───────────────────────────────────────────────────────────── what the site already has
def site():
    rec = collections.defaultdict(lambda: {"names": {}, "sex": set(), "count": 0})
    for f in ("names-db.tsv", "names-extra.tsv"):
        for line in open(os.path.join(DATA, f), encoding="utf-8"):
            q = line.rstrip("\n").split("\t")
            if len(q) < 4: continue
            k = fold(q[0]); e = rec[k]
            c = int(q[3]) if q[3].isdigit() else 0
            e["names"][q[0]] = e["names"].get(q[0], 0) + c
            if f == "names-db.tsv": e["count"] += c
            if q[1] in ("m", "f"): e["sex"].add({"m": "b", "f": "g"}[q[1]])
    cult = collections.defaultdict(set)            # folded name → cultures any storied list gives it
    ccount = collections.Counter()
    culture_rows = collections.defaultdict(list)   # folded → culture-names rows
    meaning = {}
    for f in sorted(glob.glob(os.path.join(DATA, "*.json"))):
        if os.path.basename(f) in ("hindu-names.json",): continue
        try: d = json.load(open(f, encoding="utf-8"))
        except ValueError: continue
        if not (isinstance(d, list) and d and isinstance(d[0], list) and d[0] and isinstance(d[0][0], str)): continue
        bw = os.path.basename(f) == "bollywood-names.json"
        for r in d:
            if len(r) < 3 or not isinstance(r[0], str): continue
            k = fold(r[0])
            if bw: cult[k].add("Bollywood"); continue
            if r[2]: cult[k].add(r[2]); ccount[r[2]] += 1
            for a in (r[9] if len(r) > 9 and isinstance(r[9], list) else []): cult[k].add(a)
            if len(r) > 5 and r[5]: meaning.setdefault(k, r[5])
            if os.path.basename(f) == "culture-names.json": culture_rows[k].append(r)
    hand = {}
    src = open(os.path.join(ROOT, "names.js"), encoding="utf-8").read()
    m = re.search(r"const REAL_RAW = `(.*?)`;", src, re.S)
    for line in m.group(1).strip().split("\n"):
        p = line.split("|")
        if len(p) >= 6:
            hand[fold(p[0])] = p; cult[fold(p[0])].add(p[2])
            if p[5]: meaning.setdefault(fold(p[0]), p[5])
    for f in ("meanings.json", "extra-meanings.json", "native-meanings.json"):
        for k, v in json.load(open(os.path.join(DATA, f), encoding="utf-8")).items():
            if v.get("m"): meaning.setdefault(k, v["m"])
    native = json.load(open(os.path.join(DATA, "native-forms.json"), encoding="utf-8"))
    indic_native = {k: [x[0] for x in v if re.search(r"[\u0900-\u0dff]", x[0])] for k, v in native.items()}
    indic_native = {k: v for k, v in indic_native.items() if v}
    sacred = collections.defaultdict(set)
    for f in ("indic.tsv", "indic-promoted.tsv"):
        for r in csv.DictReader(open(os.path.join(DATA, "sacred", f), encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
            if r["tradition"] == "Hindu" and r["entity_type"] not in ("place", "tribe", "concept") and r["status"] == "attested":
                sacred[fold(r["name"])].add(r["corpus"])
    big = {c for c, n in ccount.items() if n >= 30}
    for k in cult: cult[k] = {c for c in cult[k] if c in big or c in INDIAN}
    return dict(rec=rec, cult=cult, culture_rows=culture_rows, meaning=meaning, hand=hand, indic_native=indic_native, sacred=sacred)


# ───────────────────────────────────────────────────────────── Monier-Williams
REC = re.compile(r"<(H\d[A-Z]?)><h><key1>([^<]+)</key1><key2>([^<]+)</key2>.*?</h><body>(.*?)</body><tail><L>([^<]+)</L><pc>([^<]+)</pc>")
NAME_START = re.compile(r"^\s*(?:‘[^’]{1,80}’,?\s*)?(?:\(?[a-zA-Z.]{0,6}\)?\s*)?N\. of\b|^\s*of\s+(?:a|an|the|several|one|two|various|[A-ZĀĪŪṚŚṢ])")
PERSON = re.compile(r"\b(man|men|woman|women|king|kings|prince|princes|princess|queen|sage|sages|Ṛṣi|Ṛṣis|Muni|son|sons|daughter|"
                    r"daughters|wife|wives|mother|father|teacher|preceptor|poet|poetess|author|grammarian|minister|hero|warrior|Brāhman|"
                    r"Brahman|chief|disciple|pupil|lady|girl|boy|attendant|courtesan|physician|astronomer|scholiast|commentator|"
                    r"lexicographer|philosopher|Guru|saint|devotee|maiden|god|goddess|deity|Apsaras|Gandharva|Gandharvī|"
                    r"Vidyā-dhara|Vidyādharī|female|companion|friend|charioteer|brother|sister|descendant|ancestor|patriarch|"
                    r"Ācārya|Purohita|priest|Mahārāja|Rāja|Rājan|Manu|Muni|Yogin|ascetic|Kṣatriya|Vaiśya|Śūdra|merchant|"
                    r"Gopī|cowherd|nymph|Mātṛ|Mātṛs)\b")
DEITY_M = r"Viṣṇu|Kṛṣṇa|Śiva|Rudra|Gaṇeśa|Skanda|Kārttikeya|Indra|Agni|Sūrya|Brahmā|Brahman|Rāma|Rāma-candra|Balarāma|Bala-rāma|Hanumat|Kāma|Kubera|Vāyu|Varuṇa|Yama|Soma|Candra|Mitra|Savitṛ|Prajā-pati|Nārāyaṇa|Vāsudeva|Arjuna|Bhīma|Yudhi-ṣṭhira|Lakṣmaṇa|Bharata|the sun|the moon|Sun|Moon|Garuḍa|Nara|Hari|Mahā-deva|Mahādeva|Kṛṣṇa's|Viṣṇu's|Śiva's|Pradyumna|Aniruddha|Bṛhas-pati|Bṛhaspati|Śukra|Vyāsa|Vālmīki|Nārada|Dhruva"
DEITY_F = r"Durgā|Pārvatī|Lakṣmī|Sarasvatī|Devī|Umā|Gaurī|Gaṅgā|Rādhā|Sītā|Śrī|Kālī|Caṇḍī|Ambikā|Bhavānī|Sāvitrī|Gāyatrī|Satī|Rati|Dākṣāyaṇī|Draupadī|Kuntī|Yamunā|Aditi|Śacī|Indrāṇī|Ṛddhi|Lalitā|the earth"
EPI = re.compile(rf"^\s*(?:N\. of\s+|of\s+)?({DEITY_M}|{DEITY_F})\b")
EPI_F = re.compile(rf"^(?:{DEITY_F})$")
NOT_PERSON = re.compile(r"\b(Dānava|Daitya|Asura|Asuras|Rākṣasa|Rākṣasī|Rakṣas|Piśāca|Nāga|serpent|snake|serpent-demon|river|mountain|"
                        r"place|town|city|country|district|village|people|tribe|plant|tree|metre|hymn|work|Sāman|Tīrtha|lake|forest|"
                        r"horse|elephant|dog|bird|cow|bull|demon|demons|Yakṣa|Kalpa|Muhūrta|year|month|Varṣa|Dvīpa|ocean|sea|"
                        r"school|family|race|Vihāra|monastery|Nakṣatra|asterism|star|planet|grammar|treatise|poem|drama|Upaniṣad|"
                        r"Tantra|Purāṇa|commentary|Stotra|hell|world|region|tune|Rāga|Rāgiṇī|mode|game|island|well|grove|garden|"
                        r"temple|shrine|plant|fish|insect|weapon|bow|sword|conch|ceremony|rite|sacrifice|Ekāha|Ahīna|Sattra|Vrata|"
                        r"festival|day|night|Tithi|caste|mixed caste|clan|Gotra|dynasty|Vaṃśa|Kalā|letter|sound|syllable|Mantra|"
                        r"medicine|drug|disease|fever|Graha|Bhūta|Vetāla|Kumbhāṇḍa|Kiṃnara|Kiṃnarī|Kinnara|Guhyaka|Sādhya|"
                        r"Buddha|Buddhas|Jina|Arhat|Tīrthaṃkara|Bodhi-sattva|Bodhisattva|Śrāvaka|Jaina)s?\b")
NONHINDU = re.compile(r"\b(Buddh\w*|Jaina?|Jina|Arhat|Tīrthaṃkara|Bodhi-?sattva|Śrāvaka|Pratyeka|Śākya|Muslim|Mohammedan)\b")
LS_TEXT = [(r"^MBh\b", "Mahabharata"), (r"^R\.", "Valmiki Ramayana"), (r"^RV\b", "Rigveda"), (r"^BhP\b", "Bhagavata Purana"),
           (r"^Hariv\b", "Harivamsha"), (r"^VP\b", "Vishnu Purana"), (r"^Bhag\b", "Bhagavad Gita"), (r"^AV\b", "Atharvaveda"),
           (r"^ŚBr\b", "Shatapatha Brahmana"), (r"^MārkP\b", "Markandeya Purana"), (r"^PadmaP\b", "Padma Purana"),
           (r"^BrahmaP\b", "Brahma Purana"), (r"^VāyuP\b", "Vayu Purana"), (r"^MatsyaP\b", "Matsya Purana"), (r"^LiṅgaP\b", "Linga Purana"),
           (r"^SkandaP\b", "Skanda Purana"), (r"^BrahmaVP\b|^BrahmavP\b", "Brahmavaivarta Purana"), (r"^BhavP\b", "Bhavishya Purana"),
           (r"^KūrmaP\b", "Kurma Purana"), (r"^AgP\b|^AgniP\b", "Agni Purana"), (r"^GarP\b", "Garuda Purana"), (r"^Pur\b", "Puranas"),
           (r"^DevībhP\b", "Devi Bhagavata Purana"), (r"^ŚivaP\b", "Shiva Purana"), (r"^BrahmāṇḍaP\b", "Brahmanda Purana"),
           (r"^VāmP\b", "Vamana Purana"), (r"^NārP\b", "Narada Purana"), (r"^Up\b|Up\.$", "Upanishads"), (r"^GītGov\b", "Gita Govinda"),
           (r"^Ragh\b", "Raghuvamsha"), (r"^Kum\b", "Kumarasambhava"), (r"^Śak\b", "Shakuntala")]
HINDU_TEXT = {"Mahabharata", "Valmiki Ramayana", "Rigveda", "Bhagavata Purana", "Harivamsha", "Vishnu Purana", "Bhagavad Gita", "Atharvaveda",
              "Shatapatha Brahmana", "Markandeya Purana", "Padma Purana", "Brahma Purana", "Vayu Purana", "Matsya Purana", "Linga Purana",
              "Skanda Purana", "Brahmavaivarta Purana", "Bhavishya Purana", "Kurma Purana", "Agni Purana", "Garuda Purana", "Puranas",
              "Devi Bhagavata Purana", "Shiva Purana", "Brahmanda Purana", "Vamana Purana", "Narada Purana", "Upanishads", "Gita Govinda"}
FEM_WORD = re.compile(r"\b(woman|women|princess|queen|daughter|daughters|wife|wives|mother|goddess|Apsaras|lady|girl|maiden|courtesan|"
                      r"female|Gopī|nymph|poetess|sister|Vidyādharī|Gandharvī|Mātṛ|Mātṛs)\b")
MASC_WORD = re.compile(r"\b(man|men|king|kings|prince|princes|sage|sages|Ṛṣi|Ṛṣis|Muni|son|sons|father|teacher|preceptor|poet|author|"
                       r"grammarian|minister|hero|warrior|Brāhman|boy|brother|god|Gandharva)\b")


def clean_body(body, drop_head=True):
    cites = re.findall(r"<ls[^>]*>(.*?)</ls>", body)
    lexm = re.search(r"<lex>(.*?)</lex>", body)
    t = re.sub(r"<hom>[^<]*</hom>", "", body).strip()
    if drop_head: t = re.sub(r"^\s*<s>[^<]*</s>", "", t)
    t = re.sub(r"<lex>.*?</lex>|<ls[^>]*>.*?</ls>|<info[^>]*/>|<pc>.*?</pc>", "", t)
    t = re.sub(r"<s>([^<]*)</s>", lambda m: S.slp2iast(re.sub(r"[^A-Za-z]", "", m.group(1))), t)
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t)
    t = re.sub(r"\s+", " ", t).strip()
    return t, cites, (re.sub(r"<[^>]+>", "", lexm.group(1)) if lexm else "")


def strip_parens(t):
    for _ in range(3): t = re.sub(r"\s*\([^()]*\)", "", t)
    return t


def load_mw():
    """key1 → {iast, key2, genders, word: [(gloss, page, cited)], names: [(sex, desc, page, works, hindu, cited)]}"""
    E = {}
    lex_cur, in_name, cur_key = "", False, None
    nhom = collections.Counter()
    for line in open(MW_XML, encoding="utf-8"):
        m = REC.search(line)
        if not m: continue
        tag, key1, key2, body, L, pc = m.groups()
        if key1 != cur_key: lex_cur, in_name, cur_key = "", False, key1
        nhom[key1] += int(bool(re.fullmatch(r"H\d", tag)))                    # a new entry (homonym) of the same spelling
        grp = nhom[key1]
        info = re.search(r'<info lex="([^"]+)"', body)
        t, cites, lexs = clean_body(body)
        if info and info.group(1) != "inh": lex_cur = info.group(1)
        elif not info and not tag.endswith("A"): lex_cur = lex_cur if tag[-1:] in "ABCE" else ""
        e = E.setdefault(key1, {"key2": key2, "genders": set(), "word": [], "names": [], "lit": False})
        page = pc.split(",")[0]
        lit = [c for c in cites if c.strip() not in ("L.", "L", "W.", "Kāś.")]
        if lit: e["lit"] = True
        g0 = lex_cur.split(":")[0].split("#")[0]
        if "pl." in lexs: in_name = False; continue                       # "m. pl. N. of a people"
        t = strip_parens(t).strip(" ,;")
        is_name = bool(NAME_START.match(t)) and (tag[-1:] != "A" or "N. of" in t[:12] or in_name)
        if t.startswith("of ") and not in_name: is_name = False
        if is_name:
            in_name = True
            litq = re.match(r"^\s*‘([^’]{1,80})’", t)
            desc = strip_parens(re.sub(r"^\s*(?:‘[^’]{1,80}’,?\s*)?(?:\(?[a-zA-Z.]{0,6}\)?\s*)?N\. of\s+|^\s*of\s+", "", t)).strip(" ,;.")
            desc = re.split(r";|, (?:cf|see|v\.l)\b|\s&c\b", desc)[0].strip(" ,")
            desc = re.sub(r"\s+g\.\s+\S+$", "", desc)
            desc = re.sub(r"\s+(?:of\s+)?(?:a\s+)?Comm\.?(?:\s+on)?\s*$", "", desc)
            desc = re.sub(r"(\s+(of|the|a|an|and|in|with|by))+\s*$", "", desc).strip(" ,.")
            head = desc[:70]
            works = sorted({w for c in cites for rx, w in LS_TEXT if re.search(rx, c.strip())})
            epi = EPI.match(desc)
            person = (bool(PERSON.search(head)) or bool(epi)) and not NOT_PERSON.search(head.split(" and ")[0].split(" or ")[0][:40])
            if not person: continue
            if g0 == "n": continue
            sex = {"m": "b", "f": "g"}.get(g0, "")
            if epi and not sex: sex = "g" if EPI_F.match(epi.group(1)) else "b"
            if not sex:
                if FEM_WORD.search(head): sex = "g"
                elif MASC_WORD.search(head): sex = "b"
            if not sex: continue
            e["names"].append({"sex": sex, "desc": desc, "page": page, "works": works, "lit": bool(lit),
                               "deity": bool(epi), "nonhindu": bool(NONHINDU.search(desc)),
                               "litq": litq.group(1) if litq else ""})
            continue
        in_name = False
        if not lexs and tag[-1:] != "A": continue                       # roots, indeclinables without a gender
        if g0 in ("m", "f", "n") or lexs:
            for gg in re.findall(r"\b(m|f|n)\b", lexs.replace("mfn", "m f n").replace("mf", "m f")): e["genders"].add(gg)
            if g0: e["genders"].add(g0)
            g = strip_parens(t)
            g = re.sub(r"^(mfn?\.|[mfn]\.|ind\.|see\b.*|= .*|id\.)\s*", "", g).strip(" ,;.")
            if not g or re.match(r"^(See|see|=|id\.|cf\.|v\.l\.|w\.r\.|for |a kind of|N\. of|patr\.|metron\.|Name of)", g): continue
            g = re.split(r";|\s?&c\b|\s\(?cf\.|\bN\. of\b|\bpatr\.|\bmetron\.|\bifc\.|\bg\. ", g)[0].strip(" ,.").replace("‘", "").replace("’", "")
            if re.match(r"^of\b", g): continue
            parts = [p.strip() for p in g.split(",") if p.strip() and not re.search(r"[√=˚]|\bL\b|\bib\b|\bid\b|\b[A-Z][a-zā-ṣ]*\.\s*$|[A-Z][a-z]*[A-Z]", p)
                     and not re.fullmatch(r"(as|ā|ī|am|is|us|ās|aḥ|ā\)|ī\)|mfn?|[mfn])", p.strip())]
            parts = [re.sub(r"\s*\b(Comm\.|Sch\.|Comm\. on|ib\.)(\s+on)?\s*$", "", re.sub(r"\S*[/\\^]\S*|\b[a-z]+[A-Z]\w*\b", "", p)).strip(" ,.") for p in parts]
            parts = [" ".join(x for x in p.split() if not re.search(r"[^\x00-\u024f\u1e00-\u1eff‘’'\-]", x)) for p in parts]
            parts = [re.sub(r"\b(q\.v|Sch|Comm|Schol|Pāṇ|ib|id)\.?$", "", p).strip(" ,.") for p in parts]
            g = ", ".join(p for p in parts[:3] if len(p) > 1)
            if 2 < len(g) <= 70 and not re.search(r"\d", g) and len(e["word"]) < 10:
                e["word"].append({"gloss": g, "page": page, "lit": bool(lit), "n": len(lit) + (2 if "&amp;c" in body or "&c" in body else 0), "g": g0, "grp": grp})
    return E


def mw_spellings(iast, masc):
    """the Latin spellings the rules give: plain, Hindi short form (masculine -a dropped), ī→ee / ū→oo variants"""
    out = {}
    base = S.roman(iast)
    out[base] = 0
    short = None
    tk = S.iast_split(iast)
    V = set("aāiīuūṛṝḷeo") | {"ai", "au"}
    # Hindi drops the final short a after a single consonant (Kapila → Kapil), not after a cluster (Chandra, Saumya)
    if masc and len(tk) >= 3 and tk[-1] == "a" and tk[-2] not in V and tk[-2] not in ("ṃ", "ḥ") and tk[-3] in V:
        short = base[:-1]; out[short] = 1
    long_ = iast.replace("ī", "ee").replace("ū", "oo")
    if long_ != iast:
        lb = S.roman(long_); out.setdefault(lb, 2)
        if short: out.setdefault(lb[:-1], 3)
    return out, base, short


# ───────────────────────────────────────────────────────────── Indic scripts → Devanagari (same layout, other block)
BLOCKS = {0x980: "Bengali", 0xA00: "Gurmukhi", 0xA80: "Gujarati", 0xB00: "Odia", 0xC00: "Telugu", 0xC80: "Kannada", 0xD00: "Malayalam"}
def to_deva(s):
    # Malayalam chillu letters and the Gurmukhi tippi/addak have no slot in the shared layout
    s = s.replace("ൻ", "ന്").replace("ർ", "ര്").replace("ൽ", "ല്").replace("ൾ", "ള്").replace("ൺ", "ണ്").replace("ੰ", "ਂ").replace("ੱ", "")
    out = []
    for ch in s:
        cp = ord(ch)
        if 0x900 <= cp < 0x980: out.append(ch); continue
        b = next((b for b in BLOCKS if b <= cp < b + 0x80), None)
        if b is None: return ""
        out.append(chr(0x900 + cp - b))
    t = "".join(out).replace("ॆ", "े").replace("ॊ", "ो").replace("ऎ", "ए").replace("ऒ", "ओ").replace("ਂ", "ं")
    return unicodedata.normalize("NFC", t)

def deva_key(s):
    """compare Devanagari loosely: ब=व (Bengali/Assamese write both with one letter), anusvāra = class nasal, final virama ignored"""
    s = unicodedata.normalize("NFC", s).replace("व", "ब").replace("ँ", "ं").replace("़", "")
    s = re.sub(r"[ङञणनम]्(?=[कखगघचछजझटठडढतथदधपफबभ])", "ं", s)
    return s.rstrip("्")


# ───────────────────────────────────────────────────────────── ease
def ease_of(n, count):
    if not re.fullmatch(r"[A-Za-z]+", n) or len(n) > 11: return 3
    if len(n) <= 8 and count >= 100: return 1
    if count == 0 and len(n) > 9: return 3
    return 2


WORDS = {w.strip().lower() for w in open("/usr/share/dict/words")} if os.path.exists("/usr/share/dict/words") else set()


# senses left out of a name's meaning (MW gives them, but they are not what the name is chosen for)
UNSUITABLE = re.compile(r"\b(erection|semen|seminal|excrement|ordure|urine|dung|faeces|feces|penis|vulva|pudend\w*|menstru\w*|"
                        r"sexual|copulation|coitus|harlot|whore|rubbish|refuse|eunuch|corpse|vomit\w*|phlegm|pus|leprosy|"
                        r"fart\w*|anus|testicle\w*|scrotum|bastard|adulter\w*)\b", re.I)


# never a name's meaning: negative, morbid or unflattering senses (the owner's list and more)
BANNED = re.compile(r"\b(injur\w*|hurt\w*|wound\w*|death|dead|die|dying|kill\w*|slay\w*|slaughter|murder\w*|diseas\w*|sick\w*|"
                    r"poison\w*|venom\w*|demon\w*|fear\w*|terri\w*|sin|sins|sinful|grief|pain\w*|crush\w*|leafless|bristl\w*|"
                    r"heaviness|weight|vomit\w*|theft|thie\w*|steal\w*|rob\w*|wanton|amorous|voluptuous|lust\w*|blackness|"
                    r"darkness|destruction|destroy\w*|ruin\w*|enemy|foe|hostil\w*|angry|anger|wrath|cruel\w*|fierce|violent\w*|"
                    r"ugly|deform\w*|blind|deaf|dumb|lame|mad|madness|insan\w*|fool\w*|stupid|idiot|ignoran\w*|poor|poverty|beggar|"
                    r"wretch\w*|miser\w*|evil|wicked|bad|vile|base|low|lowest|mean|servant|slave|worm|dog|ass|donkey|crow|mouse|rat|"
                    r"snake|serpent|eunuch|widow\w*|barren|naked|bald|corpse|cremat\w*|ghost|goblin|fiend|witch\w*|curse\w*|"
                    r"knee|navel|hair|fat|bone|marrow|smoke|dust|noise|clamour|uproar|needle|sneeze|rope|cord|string|broom|grass|"
                    r"strife|battle|war|fight\w*|conquered|weapon|arrow|tear|tears|weep\w*|cry|crying|roar\w*|yell\w*|knot|"
                    r"perplexed|confus\w*|trick|deceit\w*|fraud|liar|lie|false|drunk\w*|intoxicat\w*|gambl\w*|harlot|"
                    r"unthrashed|husk\w*|eunuch|boil|sore|ulcer|itch|fever|urine|dung|leech|louse|lice|fly|flies|mosquito|"
                    r"vagina|buttock\w*|hips|waist|circumcis\w*|smartass|wiseass|foul|soiled|thirst\w*|cheek|pepper|rolling|"
                    r"ewe|sheep|goat|left|heavy|cot|other|neighbour|board|slate|plank|pipe|stick|shaft|spider|salt|oil|oats|"
                    r"vanish\w*|loss|lost|end|ending|finish\w*|exhaust\w*|weak\w*|tired|lazy|sluggish|slow|dull|old|aged|decrepit|"
                    r"fault\w*|defect\w*|blemish\w*|stain\w*|impur\w*|unclean|dirt\w*|filth\w*|mud|refuse|rubbish|waste)\b", re.I)
POSITIVE = re.compile(r"\b(charm\w*|lovel\w*|love|beaut\w*|grace\w*|gentle|auspicious|bless\w*|fortun\w*|prosper\w*|happ\w*|joy\w*|"
                      r"delight\w*|bright\w*|brillian\w*|shin\w*|splendo\w*|radian\w*|light|lustre|ray|beam|glor\w*|fame|famous|"
                      r"illustrious|dignity|honou?r\w*|venerab\w*|protect\w*|shelter|refuge|help\w*|kind\w*|compassion\w*|merc\w*|"
                      r"pure|purity|holy|sacred|divine|heaven\w*|celestial|god|goddess|lord|king|queen|prince\w*|ruler|chief|best|"
                      r"excellent|eminent|noble|wise|wisdom|learned|knowledge|intellig\w*|clever|skil\w*|victor\w*|triumph\w*|"
                      r"conquer\w*|brave|hero\w*|strong|strength|mighty|power\w*|wealth\w*|rich|treasure|jewel|gem|pearl|gold\w*|"
                      r"lotus|flower\w*|blossom\w*|moon\w*|sun|sky|star|dawn|morning|ocean|sea|river|song|sing\w*|music\w*|"
                      r"peace\w*|calm|tranquil\w*|truth\w*|true|virtu\w*|righteous|faith\w*|devot\w*|dear|beloved|pleas\w*|"
                      r"sweet|tender|soft|fragrant|whole|unbroken|eternal|endless|boundless|immortal|imperishable|desire|wish|hope|"
                      r"blue|green|red|white|golden|fire|wind|earth|swan|deer|doe|lion|elephant|support\w*|nourish\w*|prayer|"
                      r"praise\w*|worship\w*|reveren\w*|friend\w*|grat\w*|generous|liberal|bounti\w*|gift|giver|giving|"
                      r"blossom|spring|season|youth\w*|young|fresh|new|first|unique|matchless|incomparable|supreme|great)\b", re.I)


MAJOR = re.compile(r"^(?:the goddess |the god )?(Viṣṇu|Kṛṣṇa|Śiva|Rudra|Pārvatī|Durgā|Lakṣmī|Śrī|Sarasvatī|Gaṇeśa|Skanda|Kārttikeya|"
                   r"Rāma|Rāma-candra|Hanumat|Sītā|Rādhā|Umā|Gaurī|Gaṅgā|Kāma|Brahmā|Nārāyaṇa|Vāsudeva|Hari|Devī|Ambikā|Bhavānī|"
                   r"Sāvitrī|Gāyatrī|Lalitā|Arjuna|Bala-rāma|Balarāma)\b")


def lst(xs):
    xs = list(dict.fromkeys(xs))
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


# ───────────────────────────────────────────────────────────── the MW pass
def mw_pass(site_, evidence, extra_native):
    """→ (rows by folded name, stats). Site names first (records, culture lists), then MW names new to the site."""
    E = load_mw()
    print(f"MW: {len(E):,} headwords; {sum(1 for e in E.values() if e['names']):,} with a person's name", file=sys.stderr)
    rec, cult, hand, crow = site_["rec"], site_["cult"], site_["hand"], site_["culture_rows"]
    index = collections.defaultdict(list)            # folded spelling → [(key1, kind, rank)]
    for key1, e in E.items():
        iast = S.slp2iast(key1)
        if len(iast) < 2 or not re.fullmatch(r"[a-zāīūṛṝḷeaiouṃḥkgṅcjñṭḍṇtdnpbmyrlvśṣsh]+", iast): continue
        has_name = bool(e["names"])
        has_word = any(w["lit"] for w in e["word"])
        if not (has_name or has_word): continue
        masc = "m" in e["genders"] or any(n["sex"] == "b" for n in e["names"])
        sp, base, short = mw_spellings(iast, masc)
        for s, rank in sp.items():
            index[fold(s)].append((key1, rank))

    def describe(n):
        d = n["desc"]
        d = re.sub(r"\s+", " ", d)
        if len(d) > 80: d = d[:78].rsplit(" ", 1)[0] + "…"
        return d

    def build(key1, display, sexes, k, mode, modern_langs=(), native_given=""):
        e = E[key1]; iast = S.slp2iast(key1)
        dv = S.deva(iast)
        # the meaning: the Monier-Williams sense Apte shares; a feminine in -ā takes its adjective's (bhadrā ← bhadra)
        quote_key, gkey = "", key1
        if key1.endswith("A") and key1[:-1] + "a" in E and "f" in E[key1[:-1] + "a"]["genders"]:
            if checked_meaning(key1[:-1] + "a", E)[2] in ("agree", "mw-only"): gkey, quote_key = key1[:-1] + "a", S.slp2iast(key1[:-1] + "a")
        gloss, cite, status = checked_meaning(gkey, E)
        chain = ""
        if status == "none" and e["names"]:
            chain = compound_chain(key1, E)
            status = "chain" if chain else "name only"
        MEANING_STATUS[status] += 1
        if status == "disagree": MEANING_REVIEW.append((display, iast))
        page = (re.search(r"p\. (\d+)", cite).group(1) if cite else (e["names"][0]["page"] if e["names"] else ""))
        cite = cite or f"Monier-Williams, p. {page}"
        names = [n for n in e["names"] if not sexes or n["sex"] in sexes] or e["names"]
        names.sort(key=lambda n: (not n["deity"], not n["works"], not n["lit"]))
        works = sorted({w for n in names[:4] for w in n["works"]})
        hindu = any(n["deity"] and not n["nonhindu"] for n in names) or any(set(n["works"]) & HINDU_TEXT and not n["nonhindu"] for n in names)
        texts = sorted(set(works) | site_["sacred"].get(k, set()))
        if site_["sacred"].get(k): hindu = True
        others = sorted(c for c in cult.get(k, ()) if c not in INDIAN and c not in SANSKRIT_LINKED and not c.startswith(("Classic", "South")))
        indian_use = k in evidence
        quote = (f"Sanskrit {iast}, feminine of {quote_key} ‘{gloss}’" if quote_key else f"Sanskrit {iast} ‘{gloss}’") if gloss else \
                (f"Sanskrit {iast}, which MW divides into {chain}" if chain else f"Sanskrit {iast}")
        if chain: gloss = chain
        # a deity's name leads with the deity (Aparna: a name of Durgā or Pārvatī); a person MW names only as "a man",
        # "a king", "a son of X" is trivia and stays out of the sentence
        dn = next((n for n in names if n["deity"] and not n["nonhindu"] and MAJOR.match(n["desc"])), None)
        if dn:
            lead = f"a name of {describe(dn)}" + (f" (‘{dn['litq']}’)" if dn.get("litq") and not BANNED.search(dn["litq"]) else "")
            gloss = (lead + (f"; {gloss}" if gloss and not chain else ""))[:110]
        famous = [n for n in names if n["deity"] or re.match(r"^[A-ZĀĪŪṚŚṢ]", n["desc"]) or
                  re.match(r"^(an? |the )?(ancient |celebrated |great |famous |mythical |divine )*(sage|Ṛṣi|Muni|seer|hero|goddess|god|deity)\b", n["desc"])]
        nm = f"the name of {describe(famous[0])}" if famous and not dn else ""
        if mode == "reassign":
            s = f"Written {native_given or dv}, from {quote} ({cite})"
            if nm: s += f"; in Monier-Williams also {nm}"
            s += f"; given in {lst(modern_langs)}."
            if native_given and native_given != dv: s += f" Sanskrit {dv}."
        elif others and indian_use:
            s = f"In India, the English spelling of {quote} ({cite})" + (f"; {nm}" if nm else "")
            s += f"; also an unrelated {lst(others[:3])} name. Written {dv}."
        else:
            s = f"From {quote} ({cite})" + (f"; {nm}" if nm else "") + "."
            if others: s += f" The same spelling is also {an(others[0]).lower()} {lst(others[:3])} name, unrelated."
            s += f" Written {dv}."
        g = "e" if len(sexes) > 1 else next(iter(sexes))
        also = ["South Asian"] + [c for c in modern_langs if c != "Indian"]
        return [display, g, "Indian", "Sanskrit", "Hindu" if hindu else "", gloss, s, ",".join(texts), "real", also,
                ease_of(display, rec[k]["count"] if k in rec else 0)], {"key1": key1, "gloss": bool(gloss), "name": bool(names)}

    rows, stats, ex = {}, collections.Counter(), collections.defaultdict(list)
    # 1. names on the site
    on_site = set(rec) | set(crow) | set(cult)
    for k in sorted(on_site):
        if k in hand or k not in index or len(k) < 3: continue
        cands = index[k]
        # the culture-list rows of a modern Indian language, with their native spelling
        cr = [r for r in crow.get(k, []) if r[2] in MODERN or r[2] == "Malayali"]
        natives = [m.group(1) for r in cr for m in [re.search(r"Written ([^\s.]+)", r[6] or "")] if m]
        natives += [x for x in site_["indic_native"].get(k, []) if x not in natives]
        modern_langs = sorted({("Malayalam" if r[2] == "Malayali" else r[2]) for r in cr})
        site_sex = set(rec[k]["sex"]) if k in rec else set()
        for r in cr: site_sex |= {"g"} if r[1] == "g" else {"b"} if r[1] == "b" else {"g", "b"} if r[1] == "e" else set()

        def ok_native(key1):
            if not natives: return True
            dv = deva_key(S.deva(S.slp2iast(key1)))
            for nt in natives:
                d = to_deva(nt)
                if d and (deva_key(d) == dv or deva_key(d) + "" == dv.rstrip("ा") or deva_key(d + "्") == dv): return True
            return not any(to_deva(nt) for nt in natives)        # Tamil script cannot be compared: spelling decides
        best = None
        for key1, rank in cands:
            e = E[key1]
            if not ok_native(key1): continue
            nm_sex = {n["sex"] for n in e["names"]}
            word_ok = any(w["lit"] for w in e["word"])
            indian = k in evidence
            # a word (not a name) in the lexicon counts only when the site's own Indian spelling of the name is that word
            if not e["names"] and not (word_ok and any(to_deva(nt) for nt in natives)): continue
            # a name the lexicon only lists in a grammarian's gaṇa, or cites from no text, needs the site's Indian spelling too
            if e["names"] and not any(n["lit"] or n["deity"] for n in e["names"]) and not any(to_deva(nt) for nt in natives): continue
            # an English word (Tail, Bona) is not taken for a Sanskrit name without an Indian spelling of it on the site
            if k in WORDS and not any(to_deva(nt) for nt in natives) and k not in evidence: continue
            # Charles, Nora, Dana: another culture's name with no Indian list or sacred text behind it is not re-labelled
            if any(c not in INDIAN and c not in SANSKRIT_LINKED for c in cult.get(k, ())):
                dv_ = deva_key(S.deva(S.slp2iast(key1)))
                if not any(to_deva(nt) and deva_key(to_deva(nt)) in (dv_, dv_.rstrip("ा")) for nt in natives): continue
            agree = bool(nm_sex & site_sex) if site_sex and nm_sex else True
            # the headword's own gender: a girl's Chhaya is chāyā, not chāya
            gk = "g" if key1[-1:] in ("A", "I") else "b" if "m" in e["genders"] else ""
            gagree = (gk in site_sex) if gk and site_sex else True
            score = (bool(cr), agree, gagree, bool(e["names"]), -rank, e["lit"], len(e["word"]))
            if best is None or score > best[0]: best = (score, key1)
        if not best: continue
        key1 = best[1]; e = E[key1]
        nm_sex = {n["sex"] for n in e["names"]}
        sexes = (nm_sex | site_sex) if site_sex or nm_sex else set()
        if not sexes: stats["skipped: no sex in MW or the records"] += 1; continue
        ascii_names = {n: c for n, c in (rec[k]["names"].items() if k in rec else []) if re.fullmatch(r"[A-Za-z][A-Za-z'-]*", n)}
        disp = max(ascii_names.items(), key=lambda x: x[1])[0] if ascii_names else (crow[k][0][0] if crow.get(k) else None)
        if disp and not re.fullmatch(r"[A-Za-z][A-Za-z'-]*", disp): disp = None
        if not disp:
            disp = next((r[0] for r in crow.get(k, [])), None) or S.roman(S.slp2iast(key1))
        mode = "reassign" if cr else "match"
        row, info = build(key1, disp, sexes, k, mode, modern_langs, natives[0] if natives and to_deva(natives[0]) else "")
        rows[k] = row
        stats[f"{mode}"] += 1
        if k in rec: stats["match: in the birth records"] += 1
        if not site_["meaning"].get(k) and row[5]: stats["new meaning"] += 1
        if k not in site_["indic_native"] and k not in extra_native: stats["new Devanagari"] += 1
        ex[mode].append(row)
    # 2. MW names new to the site (persons and deities, cited in a text)
    for key1, e in E.items():
        names = [n for n in e["names"] if n["lit"] or n["deity"]]
        if not names: continue
        iast = S.slp2iast(key1)
        if not re.fullmatch(r"[a-zāīūṛṝeaiouṃḥkgṅcjñṭḍṇtdnpbmyrlvśṣh]+", iast): continue
        masc = any(n["sex"] == "b" for n in names)
        sp, base, short = mw_spellings(iast, masc)
        if any(fold(s) in on_site or fold(s) in rows for s in sp): continue
        for disp in ([short] if short else []) + [base]:
            if not 3 <= len(disp) <= 14: continue
            k = fold(disp)
            if k in rows: continue
            sexes = {n["sex"] for n in names}
            row, info = build(key1, disp, sexes, k, "new")
            rows[k] = row; stats["new name"] += 1; ex["new"].append(row)
    return rows, stats, ex


# ───────────────────────────────────────────────────────────── Wiktionary
WAPI = "https://en.wiktionary.org/w/api.php"
WDIR = os.path.join(RAW, "wikt")
LCODE = {"Hindi": "hi", "Sanskrit": "sa", "Marathi": "mr", "Gujarati": "gu", "Bengali": "bn", "Tamil": "ta", "Telugu": "te", "Kannada": "kn",
         "Malayalam": "ml", "Odia": "or", "Punjabi": "pa", "Nepali": "ne", "Assamese": "as", "Konkani": "gom", "Sindhi": "sd",
         "Maithili": "mai", "Bhojpuri": "bho", "English": "en"}
GN_LANGS = ["Hindi", "Sanskrit", "Marathi", "Gujarati", "Bengali", "Tamil", "Telugu", "Kannada", "Malayalam", "Odia", "Punjabi", "Nepali",
            "Assamese", "Konkani", "Sindhi", "Maithili", "Bhojpuri"]
FROM_LANGS = ["Sanskrit", "Hindi", "Tamil", "Bengali", "Telugu", "Marathi", "Gujarati", "Malayalam", "Punjabi", "Nepali", "Kannada", "Odia"]
TADBHAVA_LANGS = ["Hindi", "Marathi", "Gujarati", "Bengali", "Punjabi", "Nepali"]


def wapi(**q):
    q.update(format="json", maxlag="20")
    for a in range(30):
        try:
            req = urllib.request.Request(WAPI, data=urllib.parse.urlencode(q).encode(), headers={"User-Agent": UA})
            d = json.load(urllib.request.urlopen(req, timeout=120))
            if d.get("error", {}).get("code") == "maxlag": time.sleep(10); continue
            return d
        except Exception:
            time.sleep(3 + 3 * a)
    raise RuntimeError("Wiktionary API kept failing")


def members(cat):
    out, cont = [], {}
    while True:
        d = wapi(action="query", list="categorymembers", cmtitle="Category:" + cat, cmlimit="500", cmtype="page", **cont)
        out += [m["title"] for m in d.get("query", {}).get("categorymembers", [])]
        if "continue" not in d: return out
        cont = d["continue"]


def wikt_category(cat):
    """{title: wikitext} for every page in the category (cached)"""
    path = os.path.join(WDIR, re.sub(r"[^\w-]+", "_", cat) + ".json")
    if os.path.exists(path): return json.load(open(path, encoding="utf-8"))
    if OFFLINE: return {}
    titles = members(cat)
    out = {}
    for i in range(0, len(titles), 50):
        d = wapi(action="query", prop="revisions", rvprop="content", rvslots="main", titles="|".join(titles[i:i + 50]))
        for p in d.get("query", {}).get("pages", {}).values():
            out[p["title"]] = ((p.get("revisions") or [{}])[0]).get("slots", {}).get("main", {}).get("*", "")
        time.sleep(.2)
    os.makedirs(WDIR, exist_ok=True)
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"  Wiktionary {cat}: {len(out):,}", file=sys.stderr)
    return out


def xlit_all(pairs):
    """[(code, word)] → {(code, word): Wiktionary's own romanization} via {{xlit}} (cached)"""
    path = os.path.join(WDIR, "xlit.json")
    cache = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    need = sorted({f"{c}|{w}" for c, w in pairs} - set(cache))
    if need and not OFFLINE:
        for i in range(0, len(need), 150):
            chunk = need[i:i + 150]
            text = "¦".join("{{xlit|%s|%s}}" % tuple(x.split("|", 1)) for x in chunk)
            d = wapi(action="expandtemplates", prop="wikitext", text=text)
            got = d.get("expandtemplates", {}).get("wikitext", "").split("¦")
            if len(got) == len(chunk):
                for x, r in zip(chunk, got): cache[x] = r.strip()
            time.sleep(.3)
        json.dump(cache, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    return {tuple(k.split("|", 1)): v for k, v in cache.items()}


def section(text, lang):
    m = re.search(r"^==\s*%s\s*==\s*$(.*?)(?=^==[^=]|\Z)" % re.escape(lang), text, re.M | re.S)
    return m.group(1) if m else ""


def wclean(t):
    t = re.sub(r"<!--.*?-->|<ref.*?</ref>|<ref[^>]*/>", "", t, flags=re.S)
    for _ in range(3):
        t = re.sub(r"\{\{(?:l|m|w|lang|ll|lw)\|[^|}]*\|([^|}]*)(?:\|[^}]*)?\}\}", r"\1", t)
        t = re.sub(r"\{\{(?:gloss|gl|q|qualifier|i|lb|lbl|label|sense|s)\|[^{}]*\}\}", "", t)
        t = re.sub(r"\{\{[^{}]*\}\}", "", t)
    t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"'''?|<[^>]+>", "", t)
    return re.sub(r"\s+", " ", t).strip(" .;,:")


SA_ETY = re.compile(r"\{\{(inh\+?|bor\+?|der\+?|lbor|learned borrowing|obor|ubor|sbor|semi-learned borrowing|slbor|tbor)\|([a-z-]+)\|sa\|([^|}]+)((?:\|[^{}]*)?)\}\}")


def sanskrit_etymon(sec):
    ety = re.search(r"===\s*Etymology[^=]*===(.*?)(?====)", sec, re.S)
    if not ety: return None
    m = SA_ETY.search(ety.group(1))
    if not m: return None
    rest = m.group(4).split("|")[1:]
    pos = [x for x in rest if "=" not in x]
    kw = dict(x.split("=", 1) for x in rest if "=" in x)
    gloss = kw.get("t") or kw.get("gloss") or (pos[1] if len(pos) > 1 else "")
    word = m.group(3).strip()
    kind = {"inh": "inherited", "inh+": "inherited"}.get(m.group(1), "borrowed" if "bor" in m.group(1) or "borrow" in m.group(1) else "derived")
    return {"sa": word, "gloss": wclean(gloss), "kind": kind}


def other_etymon(sec):
    """the first source language of the etymology: ar, fa, he, en … (a borrowed name, not a Hindu one)"""
    ety = re.search(r"===\s*Etymology[^=]*===(.*?)(?====)", sec, re.S)
    if not ety: return ""
    m = re.search(r"\{\{(?:inh\+?|bor\+?|der\+?|lbor|obor|ubor|sbor|bor-lite|der-lite|cog)\|[a-z-]+\|([a-z-]+)\|", ety.group(1))
    return m.group(1) if m else ""


def definitions(sec):
    """[(pos, [definitions])] for nouns, adjectives, proper nouns"""
    out = []
    for m in re.finditer(r"^===+\s*(Noun|Adjective|Proper noun)\s*===+\s*$(.*?)(?=^===|\Z)", sec, re.M | re.S):
        ds = []
        for line in re.findall(r"^#(?![:*#])\s*(.+)$", m.group(2), re.M):
            g = re.search(r"\{\{given name\|[^}]*\}\}", line)
            if g: ds.append(("GIVEN", line)); continue
            c = wclean(line)
            if c and not re.match(r"^(alternative|obsolete|misspelling|plural|inflection|form)", c, re.I): ds.append(("DEF", c))
        out.append((m.group(1), ds))
    return out


def given_sex(sec):
    s = set()
    for m in re.finditer(r"\{\{given name\|[^}|]+\|([^}]*)\}\}", sec):
        a = m.group(1)
        if re.search(r"\bunisex\b", a): s |= {"b", "g"}
        elif re.search(r"\bfemale\b", a): s.add("g")
        elif re.search(r"\bmale\b", a): s.add("b")
    return s


def common_spellings(rom, code):
    """Wiktionary's romanization → the spellings families write: diacritics dropped (ā→a, ś/ṣ→sh, c→ch, ṛ→ri), Hindi ṛ (ड़) → r,
    plus ee/oo for ī/ū and aa for a word-initial ā (Aarav)"""
    r = unicodedata.normalize("NFC", rom.lower().strip())
    if not r or " " in r: return {}
    r = r.replace("r̥", "ṛ̥").replace("ŕ", "ṛ̥")
    if code != "sa":
        r = re.sub(r"ṛ(?!̥)", "ɽ", r)                                       # Hindi/Bengali flap ड़/ড়
    r = r.replace("ṛ̥", "ṛ")
    r = "".join(c for c in unicodedata.normalize("NFD", r) if unicodedata.category(c) != "Mn" or c in "̣̱̄́̇̐̃")
    r = unicodedata.normalize("NFC", r)
    r = re.sub(r"[ãẽĩõũ]|̃", lambda m: {"ã": "an", "ẽ": "en", "ĩ": "in", "õ": "on", "ũ": "un"}.get(m.group(0), "n"), r)   # candrabindu: Chand
    r = r.replace("ḷ", "l").replace("ŭ", "u").replace("ẏ", "y").replace("ɽ", "r").replace("ḻ", "zh").replace("ṉ", "n").replace("ṟ", "r").replace("ṁ", "ṃ")
    r = r.replace("ō", "o").replace("ē", "e")
    if not re.fullmatch(r"[a-zāīūṛṝḷṃḥṅñṭḍṇśṣ'-]+", r): return {}
    r = r.replace("'", "").replace("-", "")
    out = {S.roman(r): 0}
    lv = r.replace("ī", "ee").replace("ū", "oo")
    if lv != r: out.setdefault(S.roman(lv), 1)
    if r.startswith("ā"):
        for v in list(out): out.setdefault("Aa" + v[1:], 1)
    return out


def iast2slp(s):
    rev = {v: k for k, v in S.SLP.items()}
    return "".join(rev.get(t, "") for t in S.iast_split(s))


# ───────────────────────────────────────────────────────────── Wikidata
WD_LANGS = {"Q1568": "Hindi", "Q11059": "Sanskrit", "Q1571": "Marathi", "Q5137": "Gujarati", "Q9610": "Bengali", "Q5885": "Tamil",
            "Q8097": "Telugu", "Q33673": "Kannada", "Q36236": "Malayalam", "Q33810": "Odia", "Q58635": "Punjabi", "Q33823": "Nepali",
            "Q29401": "Assamese", "Q34239": "Konkani", "Q33997": "Sindhi", "Q36109": "Maithili", "Q33268": "Bhojpuri"}
LABEL_LANG = {"hi": "Hindi", "mr": "Marathi", "gu": "Gujarati", "bn": "Bengali", "ta": "Tamil", "te": "Telugu", "kn": "Kannada",
              "ml": "Malayalam", "or": "Odia", "pa": "Punjabi", "ne": "Nepali", "as": "Assamese", "sa": "Sanskrit", "gom": "Konkani",
              "mai": "Maithili", "bho": "Bhojpuri"}
GN_CLASS = {"Q12308941": "b", "Q11879590": "g", "Q3409032": "e", "Q202444": ""}


def sparql(q, path):
    body = get("https://query.wikidata.org/sparql", path, data=urllib.parse.urlencode({"query": q}).encode(),
               headers={"Accept": "application/sparql-results+json"})
    if not body: return []
    return [{k: v["value"] for k, v in b.items()} for b in json.loads(body)["results"]["bindings"]]


def wikidata():
    """{qid: {sex, en, labels{code: label}, langs[], bearers}} (cached in raw/hindu/)"""
    vals = " ".join("wd:" + q for q in WD_LANGS)
    a = sparql(f"""SELECT DISTINCT ?item ?cls ?lang WHERE {{ VALUES ?lang {{ {vals} }} VALUES ?cls {{ wd:Q202444 wd:Q11879590 wd:Q12308941 wd:Q3409032 }}
      ?item wdt:P31 ?cls ; wdt:P407 ?lang . }}""", os.path.join(RAW, "wd-indic-langs.json"))
    codes = ", ".join(f'"{c}"' for c in LABEL_LANG)
    a += [dict(r, lang="http://www.wikidata.org/entity/" + {v: k for k, v in WD_LANGS.items()}[LABEL_LANG[r["lc"]]])
          for r in sparql(f"""SELECT DISTINCT ?item ?cls ?lc WHERE {{ VALUES ?cls {{ wd:Q202444 wd:Q11879590 wd:Q12308941 wd:Q3409032 }}
      ?item wdt:P31 ?cls ; wdt:P1705 ?nl . BIND(lang(?nl) AS ?lc) FILTER(?lc IN ({codes})) }}""", os.path.join(RAW, "wd-indic-native.json"))]
    b = sparql("""SELECT ?item ?cls (COUNT(DISTINCT ?p) AS ?n) WHERE { ?p wdt:P27 wd:Q668 ; wdt:P735 ?item .
      ?item wdt:P31 ?cls . VALUES ?cls { wd:Q202444 wd:Q11879590 wd:Q12308941 wd:Q3409032 } } GROUP BY ?item ?cls""",
               os.path.join(RAW, "wd-india-bearers.json"))
    items = {}
    for r in a + b:
        q = r["item"].rsplit("/", 1)[-1]
        e = items.setdefault(q, {"sex": set(), "langs": set(), "bearers": 0})
        g = GN_CLASS.get(r["cls"].rsplit("/", 1)[-1], "")
        if g == "e": e["sex"] |= {"b", "g"}
        elif g: e["sex"].add(g)
        if "lang" in r: e["langs"].add(WD_LANGS[r["lang"].rsplit("/", 1)[-1]])
        if "n" in r: e["bearers"] = max(e["bearers"], int(r["n"]))
    # labels and native labels, 50 items a request
    path = os.path.join(RAW, "wd-labels.json")
    lab = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    need = [q for q in items if q not in lab]
    if need and not OFFLINE:
        for i in range(0, len(need), 50):
            url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({"action": "wbgetentities", "ids": "|".join(need[i:i + 50]),
                  "props": "labels|claims|descriptions", "languages": "en|" + "|".join(LABEL_LANG), "format": "json"})
            try:
                d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120))
            except Exception as e:
                print("  wikidata labels failed", e, file=sys.stderr); time.sleep(10); continue
            for q, ent in d.get("entities", {}).items():
                cl = ent.get("claims", {})
                native = [(s["mainsnak"].get("datavalue", {}).get("value", {}).get("language", ""),
                           s["mainsnak"].get("datavalue", {}).get("value", {}).get("text", "")) for s in cl.get("P1705", [])]
                origin = [s["mainsnak"].get("datavalue", {}).get("value", {}).get("id", "") for p in ("P407", "P138", "P144", "P5191") for s in cl.get(p, [])]
                lab[q] = {"labels": {k: v["value"] for k, v in ent.get("labels", {}).items()}, "native": native,
                          "desc": ent.get("descriptions", {}).get("en", {}).get("value", ""), "related": origin}
            time.sleep(.5)
        json.dump(lab, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    for q, e in items.items():
        e.update(lab.get(q, {"labels": {}, "native": [], "desc": "", "related": []}))
    return items


# ───────────────────────────────────────────────────────────── Apte cross-check of every meaning
APTE_ZIP = "https://www.sanskrit-lexicon.uni-koeln.de/scans/AP90Scan/2020/downloads/ap90xml.zip"
_APTE = None
MEANING_STATUS = collections.Counter()      # agree | mw-only | disagree | chain | name only | wiktionary
MEANING_REVIEW = []                         # names whose MW and Apte senses share nothing (meaning left blank)
WIKT_MEANING = []                           # rows whose meaning comes from Wiktionary (neither dictionary has the word)
STOPW = set("a an the of or and to in by with for as from be is that which who what this any one other into being made".split())


def apte():
    """key1 (SLP1) → the English of Apte's Practical Sanskrit-English Dictionary (1890), Cologne CDSL (cached in raw/hindu/ap90/)"""
    global _APTE
    if _APTE is not None: return _APTE
    xml = os.path.join(RAW, "ap90", "xml", "ap90.xml")
    if not os.path.exists(xml):
        import zipfile
        z = os.path.join(RAW, "ap90", "ap90xml.zip")
        get(APTE_ZIP, z)
        if os.path.exists(z): zipfile.ZipFile(z).extractall(os.path.join(RAW, "ap90"))
    _APTE = collections.defaultdict(str)
    if not os.path.exists(xml): return _APTE
    for line in open(xml, encoding="utf-8"):
        m = re.search(r"<key1>([^<]+)</key1>.*?<body>(.*?)</body>", line)
        if not m: continue
        t = re.sub(r"<s>[^<]*</s>|<ls[^>]*>.*?</ls>|<[^>]+>", " ", m.group(2))
        _APTE[m.group(1)] += " " + html.unescape(t).lower()
    return _APTE


def content_words(g):
    return [w for w in re.findall(r"[a-z]+", g.lower()) if len(w) >= 3 and w not in STOPW]


def in_apte(word, text):
    stem = word[:6] if len(word) > 6 else word
    return re.search(r"\b" + re.escape(stem), text) is not None


def suitable_parts(gloss):
    parts = [p.strip(" ‘’") for p in re.split(r"[,;]", gloss) if p.strip(" ‘’")]
    return [p for p in parts if not BANNED.search(p) and not UNSUITABLE.search(p) and len(p) > 2]


def checked_meaning(key1, E):
    """(meaning, citation, status): the sense the name is given for. Among all of MW's senses for the headword and its
    homonyms, negative or unflattering ones are skipped and a sense with a positive word (charming, protection, light …)
    is preferred; then Apte must share it. status: agree | mw-only | disagree | none"""
    e = E.get(key1)
    if not e or not e["word"]: return "", "", "none"
    ws = [w for w in e["word"] if int(w["page"] or 0) < 1308] or e["word"]
    g1 = next((w["grp"] for w in ws if w["lit"]), ws[0]["grp"])
    first = [w for w in ws if w["grp"] == g1]
    order = sorted(range(len(first)), key=lambda i: (-first[i]["n"], i))
    seq = [first[i] for i in order] + [x for x in ws if x["grp"] != g1]
    cand = []
    for i, w in enumerate(seq):
        ps = suitable_parts(w["gloss"])
        if not ps: continue
        pos = [p for p in ps if POSITIVE.search(p)]
        cand.append((0 if pos else 1, i, pos or ps, w))
    if not cand: return "", "", "none"
    cand.sort(key=lambda c: (c[0], c[1]))
    A = apte()
    # Apte heads nouns in the nominative (vedaH, ratnaM, rAjA): read every form of the stem
    forms = {key1, key1 + "H", key1 + "M"}
    if key1.endswith("an"): forms.add(key1[:-2] + "A")
    if key1.endswith("in"): forms.add(key1[:-2] + "I")
    if key1.endswith("f"): forms.add(key1[:-1] + "A")
    if key1.endswith(("mat", "vat")): forms.add(key1[:-2] + "An")
    text = " ".join(A.get(f, "") for f in forms).strip()
    if not text:
        _, _, ps, w = cand[0]
        return ", ".join(ps[:3])[:80], f"Monier-Williams, p. {w['page']}", "mw-only"
    for _, _, ps, w in cand:
        shared = [p for p in ps if any(in_apte(cw, text) for cw in content_words(p))]
        if shared:
            return ", ".join(shared[:3])[:80], f"Monier-Williams, p. {w['page']}; Apte", "agree"
    return "", "", "disagree"


def compound_chain(key1, E):
    """for a name MW gives only as 'N. of …': the words MW's own segmentation (key2 hyphens) builds it from"""
    e = E.get(key1)
    if not e: return ""
    parts = [p for p in re.split(r"[-—]", re.sub(r"[/^\\\\]", "", e.get("key2", ""))) if p]
    if len(parts) < 2: return ""
    out = []
    for i, p in enumerate(parts):
        k = p if i == len(parts) - 1 else p
        cands = [k, k + "a", k[:-1] + "a" if k.endswith("A") else k]
        if i == len(parts) - 1 and k.endswith("A"): cands.insert(0, k[:-1] + "a")
        hit = next((c for c in cands if c in E and checked_meaning(c, E)[2] in ("agree", "mw-only") and checked_meaning(c, E)[0]), None)
        if not hit: return ""
        if len({w["grp"] for w in E[hit]["word"]}) > 1: return ""      # mātṛ 'measurer' or mātṛ 'mother': two words, no chain
        part = checked_meaning(hit, E)[0].split(",")[0].strip()
        if not POSITIVE.search(part): return ""                          # 'pity' + 'dark' reads oddly: no chain
        out.append(f"{S.slp2iast(hit)} ‘{part}’")
    return " + ".join(out)

# ───────────────────────────────────────────────────────────── Part 2: scriptural names still missing → data/sacred/indic-more.tsv
MORE = os.path.join(DATA, "sacred", "indic-more.tsv")
GRETIL_PT = "https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/plaintext/"
SRC_GRETIL = "GRETIL e-text ({}), {}"
WS_API = "https://sa.wikisource.org/w/api.php"
SD = "https://sanskritdocuments.org/"
DV_DIG = str.maketrans("०१२३४५६७८९", "0123456789")


def gretil_verses(fn, prefix, text):
    """GRETIL plaintext: verses end in '// bndp_1,1.45 //' → [(cite, section, url, iast)]"""
    body = get(GRETIL_PT + fn, os.path.join(RAW, "gretil", fn)).decode("utf-8", "replace")
    out, buf = [], []
    for line in body.split("\n"):
        m = re.search(r"//\s*[a-zA-Z]+_([\d,.]+)\s*//", line)
        if m:
            buf.append(line[:m.start()])
            ref = m.group(1).replace(",", ".").strip(".")
            out.append((f"{prefix} {ref}", text, GRETIL_PT + fn, re.sub(r"[/|]", " ", " ".join(buf)).strip())); buf = []
        elif line.strip() and not line.startswith("#"): buf.append(line)
    return out


def samaveda_verses():
    fn = "sa_sAmavedasaMhitA.txt"
    body = get(GRETIL_PT + fn, os.path.join(RAW, "gretil", fn)).decode("utf-8", "replace")
    out = []
    for chunk, n in re.findall(r"(.*?)\.\.\s*(\d+)", body, re.S):
        mantra = re.split(r"\d+ \d+ \d+ \d+ \d+[a-z]", chunk, maxsplit=1)
        if len(mantra) < 2: continue
        t = re.sub(r"\d+ \d+ \d+ \d+ \d+[a-z]", " ", mantra[1])
        out.append((f"SV {n}", "Samaveda (Kauthuma)", GRETIL_PT + fn, re.sub(r"[.\s]+", " ", t).strip()))
    return out


def wikisource(prefixes, key):
    """every subpage of a Sanskrit Wikisource work → {title: wikitext} (cached)"""
    path = os.path.join(RAW, "wikisource", key + ".json")
    if os.path.exists(path): return json.load(open(path, encoding="utf-8"))
    if OFFLINE: return {}
    titles = []
    for pre in prefixes:
        cont = {}
        while True:
            q = {"action": "query", "list": "allpages", "apprefix": pre, "aplimit": "500", "format": "json", **cont}
            d = json.load(urllib.request.urlopen(urllib.request.Request(WS_API + "?" + urllib.parse.urlencode(q), headers={"User-Agent": UA}), timeout=120))
            titles += [p["title"] for p in d["query"]["allpages"]]
            if "continue" not in d: break
            cont = d["continue"]
    out = {}
    for i in range(0, len(titles), 50):
        q = {"action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main", "titles": "|".join(titles[i:i + 50]), "format": "json"}
        d = json.load(urllib.request.urlopen(urllib.request.Request(WS_API, data=urllib.parse.urlencode(q).encode(), headers={"User-Agent": UA}), timeout=180))
        for p in d.get("query", {}).get("pages", {}).values():
            out[p["title"]] = ((p.get("revisions") or [{}])[0]).get("slots", {}).get("main", {}).get("*", "")
        time.sleep(.3)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"  Wikisource {key}: {len(out)} pages", file=sys.stderr)
    return out


def ws_verses(pages, prefix, text):
    """Devanagari Wikisource pages → verses; a verse ends in ॥ n ॥; chapter and section from the page title"""
    out = []
    def num(s):
        m = re.findall(r"[\d०-९]+", s)
        return m[-1].translate(DV_DIG).lstrip("0") if m else ""
    for title in sorted(pages, key=lambda t: [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", t.translate(DV_DIG))]):
        wt = pages[title]
        if "#REDIRECT" in wt.upper() or "#अनुप्रेषित" in wt or len(wt) < 400: continue
        parts = title.split("/")
        if len(parts) < 2: continue
        ch = num(parts[-1])
        sec = num(parts[1]) if len(parts) > 2 else ""
        if not ch: continue
        t = re.sub(r"\{\{[^{}]*\}\}|<[^>]+>|\[\[[^\]]*\]\]|'''?", " ", wt)
        buf = []
        for line in t.split("\n"):
            m = re.search(r"[॥।]?\s*([०-९]+)\s*[॥।]*\s*$", line)           # "… द्विज१।" or "… ॥ १ ॥": a verse ends
            if m:
                buf.append(line[:m.start()])
                v = m.group(1).translate(DV_DIG).lstrip("0")
                iast = S.deva2iast(" ".join(buf).replace("ऽ", "").replace("।", " ").replace("॥", " ")).strip()
                if iast: out.append((f"{prefix} {sec + '.' if sec else ''}{ch}.{v}", text,
                                     "https://sa.wikisource.org/wiki/" + urllib.parse.quote(title.replace(" ", "_")), iast))
                buf = []
            elif not re.search(r"[|=]|^\s*$", line): buf.append(line)
    return out


# the three Sahasranamas, from sanskritdocuments.org nāmāvalīs (each name in the dative: "OM keshavAya namaH")
SAHASRA = [
    ("Vishnu Sahasranama", "Mahabharata, Anushasana Parva (vulgate 13.149)", "doc_vishhnu/vishnaam.itx", "Q11380", "Vishnu", "boy", "m"),
    ("Shiva Sahasranama", "Mahabharata, Anushasana Parva (vulgate 13.17)", "doc_shiva/shiva-1000.itx", "Q11378", "Shiva", "boy", "m"),
    ("Lalita Sahasranama", "Brahmanda Purana, Lalitopakhyana", "doc_devii/lalitaa1000.itx", "Q2402056", "Lalita Tripurasundari", "girl", "f"),
]
DAT_M = [("āya", ["a"]), ("smai", [""]), ("tmane", ["tman"]), ("mane", ["man"]), ("mne", ["man"]), ("ghne", ["han"]), ("iṇe", ["in"]),
         ("ine", ["in"]), ("tre", ["tṛ"]), ("ave", ["u"]), ("aye", ["i"]), ("te", ["t"]), ("ṣe", ["s", "ṣ"]), ("se", ["s"]), ("ve", ["u"]),
         ("ne", ["n"]), ("e", [""])]
DAT_F = [("āyai", ["ā"]), ("yai", ["ī", "i"]), ("ai", ["ī"]), ("vai", ["ū"]), ("tre", ["tṛ"]), ("e", [""])]
SURE = {"āya", "smai", "tmane", "āyai", "ine", "iṇe"}


def sahasranama_rows(mw_keys, mwE):
    rows, unresolved = [], collections.Counter()
    for corpus, where, fn, qid, fig, sex, g in SAHASRA:
        body = get(SD + fn, os.path.join(RAW, "sd", os.path.basename(fn)),
                   headers={"User-Agent": "Mozilla/5.0 (Macintosh) AppleWebKit/537.36 Chrome/120 Safari/537.36"}).decode("utf-8", "replace")
        names, started = [], fn.endswith("shiva-1000.itx")
        for line in body.split("\n"):
            if re.match(r"^\s*1\s+OM\b", line) or "atha shrI lalitA sahasranAmAvalI" in line: started = True
            if not started: continue
            for m in re.finditer(r"(?:^|\|)\s*(?:\d+\s+)?(?:OM\s+)?((?:aiM\s+hrIM\s+shrIM\s+)?[A-Za-z~^.]+(?:\s+[A-Za-z~^.]+)?)\s+namaH", line):
                w = re.sub(r"^aiM\s+hrIM\s+shrIM\s+", "", m.group(1)).strip()
                if " " in w: unresolved[corpus] += 1; names.append(None); continue
                names.append(w)
        n_seen = 0
        for i, w in enumerate(names, 1):
            if not w: continue
            iast = S.itrans2iast(w).replace("'", "")
            stem, sure = None, False
            for end, reps in (DAT_F if g == "f" else DAT_M):
                if iast.endswith(end):
                    cands = [iast[: -len(end)] + r for r in reps]
                    ok = [c for c in cands if iast2slp(c) in mw_keys]
                    if ok: stem = ok[0]; sure = True
                    elif end in SURE: stem = cands[0]; sure = True
                    else: stem = cands[0]
                    break
            if not stem or not sure:
                unresolved[corpus] += 1; continue
            n_seen += 1
            key = iast2slp(stem)
            gloss = ""
            if key in mwE:
                ws = [x for x in mwE[key]["word"] if x["lit"]] or mwE[key]["word"]
                gloss = ws[0]["gloss"] if ws else ""
            disp = S.modern_name(stem[:1].upper() + stem[1:], {})
            rows.append({"name": disp, "figure_id": qid, "figure": f"{fig}, Hindu deity" if fig != "Lalita Tripurasundari" else "Lalita Tripurasundari, Hindu goddess",
                         "sex": sex, "original": S.deva(stem), "translit": stem[:1].upper() + stem[1:], "language": "Sanskrit",
                         "tradition": "Hindu", "subtradition": "Shakta" if g == "f" else ("Vaishnava" if fig == "Vishnu" else "Shaiva"),
                         "corpus": corpus, "text": where, "passage": f"{corpus}, name {i} (nāmāvalī numbering)",
                         "url": SD + fn.replace(".itx", ".html"), "occurrences": "1", "entity_type": "epithet", "name_role": "divine",
                         "status": "attested", "relation": f"name {i} of the thousand names of {fig}" + (f"; MW: {gloss}" if gloss else ""),
                         "source": f"sanskritdocuments.org nāmāvalī e-text ({os.path.basename(fn)}); dative form reduced to the stem"
                                   + (f"; {S.SRC_MW}" if key in mw_keys else ""),
                         "confidence": "0.9" if key in mw_keys else "0.75"})
        print(f"  {corpus}: {len(names)} names read, {n_seen} rows, {unresolved[corpus]} left out (phrases or unclear stems)", file=sys.stderr)
    return rows, unresolved


def purana_jobs():
    J = []
    def job(corpus, text, wkey, verses, note):
        J.append({"corpus": corpus, "text": text, "wkey": wkey, "verses": verses, "scan": "matcher", "era": "vedic" if corpus == "Samaveda" else "puranic",
                  "split": False, "src": note, "new": True})
        print(f"  {corpus}: {len(verses)} passages", file=sys.stderr)
    job("Brahmanda Purana", "Brahmanda Purana", "BrahmāṇḍaP", gretil_verses("sa_brahmANDapurANa.txt", "BndP", "Brahmanda Purana"),
        SRC_GRETIL.format("sa_brahmANDapurANa", "complete vulgate"))
    job("Markandeya Purana", "Markandeya Purana", "MārkP", gretil_verses("sa_mArkaNDeyapurANa1-93.txt", "MārkP", "Markandeya Purana"),
        SRC_GRETIL.format("sa_mArkaNDeyapurANa1-93", "chapters 1-93"))
    job("Narada Purana", "Narada Purana", "NārP", gretil_verses("sa_nAradapurANa.txt", "NārP", "Narada Purana"),
        SRC_GRETIL.format("sa_nAradapurANa", "vulgate"))
    job("Vamana Purana", "Vamana Purana", "VāmP", gretil_verses("sa_vAmanapurANa1-69.txt", "VāmP", "Vamana Purana"),
        SRC_GRETIL.format("sa_vAmanapurANa1-69", "chapters 1-69"))
    job("Samaveda", "Samaveda (Kauthuma)", "SV", samaveda_verses(), SRC_GRETIL.format("sa_sAmavedasaMhitA", "Kauthuma recension, mantras only"))
    for corpus, wkey, prefixes, key, pre in [
            ("Padma Purana", "PadmaP", ["पद्मपुराणम्/"], "padma", "PadmaP"),
            ("Bhavishya Purana", "BhavP", ["भविष्यपुराणम्/", "भविष्यपुराणम् /"], "bhavishya", "BhavP"),
            ("Brahmavaivarta Purana", "BrahmaVP", ["ब्रह्मवैवर्तपुराणम्/"], "brahmavaivarta", "BrahmaVP")]:
        pages = wikisource(prefixes, key)
        job(corpus, corpus, wkey, ws_verses(pages, pre, corpus), f"Sanskrit Wikisource e-text of the {corpus} ({len(pages)} pages; CC BY-SA)")
    return J


def scripture_rows():
    """rows for the seven missing Mahāpurāṇas and the Samaveda, through build_sacred_indic's matcher (names from MW, figures from Wikidata)"""
    import shutil
    mine = os.path.join(RAW, "wd_labels.json")
    if not os.path.exists(mine) and os.path.exists(S.WDL_CACHE): shutil.copy(S.WDL_CACHE, mine)
    S.WDL_CACHE = mine                                      # its Wikidata label cache is kept in raw/hindu/, not raw/sacred/
    S.load_corpora = lambda: {"Mahabharata": [], "Bhagavad Gita": [], "Valmiki Ramayana": []}
    S.later_jobs = purana_jobs
    mine = {"BrahmāṇḍaP", "MārkP", "NārP", "VāmP", "PadmaP", "BhavP", "BrahmaVP"}
    S.WORK_LS.update({"MārkP.": {"DM", "MārkP"}, "PadmaP.": {"PadmaP"}, "BhavP.": {"BhavP"}, "BhaviṣyaP.": {"BhavP"},
                      "BrahmavP.": {"BrahmaVP"}, "BrahmaVP.": {"BrahmaVP"}, "BrahmavaivP.": {"BrahmaVP"}, "BrahmāṇḍaP.": {"BrahmāṇḍaP"},
                      "VāmP.": {"VāmP"}, "VāmanaP.": {"VāmP"}, "NārP.": {"NārP"}, "NāradaP.": {"NārP"}, "NāradīyaP.": {"NārP"},
                      "SV.": {"SV"}, "Pur.": S._PUR | mine})
    rows, review, stats = S.hindu(S.scripture_hints(), later=True)
    for r in rows + review: r.pop("_split", None)
    return rows, review, stats


# ───────────────────────────────────────────────────────────── Tamil bhakti: the 63 Nayanars (Periya Puranam) and the 12 Alvars
PM = "https://www.projectmadurai.org/pm_etexts/utf8/"
PERIYA = ["pmuni0209", "pmuni0215", "pmuni0218", "pmuni0224", "pmuni0225", "pmuni0226", "pmuni0227"]
PRABANDHAM = {"pmuni0005_01": "Tiruppallandu, Periyalvar Tirumoli", "pmuni0005_02": "Tiruppavai, Nachiyar Tirumoli and other works",
              "pmuni0006_01": "Periya Tirumoli", "pmuni0006_02": "Periya Tirumoli", "pmuni0007": "Iyarpa and other works",
              "pmuni0008_01": "Tiruvaymoli", "pmuni0008_02": "Tiruvaymoli"}
SRC_PM = "Project Madurai e-text ({})"


def pm_text(f):
    body = get(PM + f + ".html", os.path.join(RAW, "tamil", f + ".html"), headers={"User-Agent": "Mozilla/5.0"}).decode("utf-8", "replace")
    t = re.sub(r"<[^>]+>", "\n", body)
    return re.sub(r"\n\s*\n+", "\n", html.unescape(t))


def wd_entities(qids, props="labels|claims|sitelinks"):
    out = {}
    for i in range(0, len(qids), 50):
        url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({"action": "wbgetentities", "ids": "|".join(qids[i:i + 50]),
              "props": props, "languages": "en|ta", "sitefilter": "tawiki|enwiki", "format": "json"})
        path = os.path.join(RAW, "tamil", "wd-" + str(abs(hash("|".join(qids[i:i + 50]))) % 10 ** 10) + ".json")
        body = get(url, path)
        if body: out.update(json.loads(body).get("entities", {}))
    return out


def tamil_rows():
    rows = []
    wiki = get("https://en.wikipedia.org/w/index.php?title=Nayanars&action=raw", os.path.join(RAW, "tamil", "en-nayanars.wiki")).decode("utf-8")
    table = wiki[wiki.find("List of 63 Nayanars"):]
    table = table[: table.find("\n|}")]
    nay = re.findall(r"^\|\s*(\d+)\s*\|\|\s*\[\[([^|\]]+)(?:\|([^\]]+))?\]\]", table, re.M)
    titles = [a for _, a, _ in nay]
    pp = {}
    for i in range(0, len(titles), 40):
        body = get("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "prop": "pageprops", "redirects": 1,
                   "titles": "|".join(titles[i:i + 40]), "format": "json"}), os.path.join(RAW, "tamil", f"en-pp-{i}.json"))
        d = json.loads(body or b"{}").get("query", {})
        red = {r["from"]: r["to"] for r in d.get("redirects", [])} | {r["from"]: r["to"] for r in d.get("normalized", [])}
        for p in d.get("pages", {}).values():
            pp[p["title"]] = p.get("pageprops", {}).get("wikibase_item", "")
        for a, b in red.items(): pp[a] = pp.get(b, pp.get(red.get(b, ""), ""))
    ents = wd_entities(sorted({q for q in pp.values() if q}))
    # chapter headings of the Periya Puranam e-texts: "2.02 திருநீலகண்ட நாயனார் புராணம் (360-403)"
    chapters, verses = [], []
    for f in PERIYA:
        t = pm_text(f)
        for m in re.finditer(r"(\d{1,2})\.\s*0?(\d{1,2})\.?\s*\n?\s*([^\n(\d.]{2,60}?)\s*புராணம்\s*\n?\s*\((\d+)\s*-\s*(\d+)\)", t):
            chapters.append({"num": f"{m.group(1)}.{m.group(2)}", "title": m.group(3).strip() + " புராணம்", "from": int(m.group(4)),
                             "to": int(m.group(5)), "file": f})
        verses.append((f, t))
    seen_ch = {}
    for c in chapters: seen_ch.setdefault(c["title"].replace(" ", ""), c)
    import difflib
    def key(s): return re.sub(r"\s|நாயனார்|புராணம்|அடிகள்|சுவாமிகள்|அம்மையார்|ஆழ்வார்", "", s)
    found = 0
    for n, art, disp in nay:
        q = pp.get(art, "")
        e = ents.get(q, {})
        ta = e.get("labels", {}).get("ta", {}).get("value", "") or e.get("sitelinks", {}).get("tawiki", {}).get("title", "")
        sexq = [c["mainsnak"].get("datavalue", {}).get("value", {}).get("id") for c in e.get("claims", {}).get("P21", [])]
        sex = "girl" if "Q6581072" in sexq else "boy" if "Q6581097" in sexq else ""
        name = re.sub(r"\s+Nayanar$", "", (disp or art)).strip()
        if not ta: continue
        best, score = None, 0
        for c in seen_ch.values():
            r = difflib.SequenceMatcher(None, key(ta), key(c["title"])).ratio()
            if r > score: best, score = c, r
        if n == "1":                                    # Sundarar's own chapter is the Taduttatkonda Puranam (1.5)
            best = next((c for c in seen_ch.values() if c["title"].startswith("தடுத்தாட்கொண்ட")), best); score = 1 if best else 0
        if best and score >= 0.85:
            found += 1
            passage = f"Periya Puranam {best['num']} ({best['title']}), verses {best['from']}-{best['to']}"
            url, status, conf = PM + best["file"] + ".html", "attested", "0.85"
        else:
            passage, url, status, conf = f"Nayanar no. {n} (list of the 63 Nayanars)", "https://en.wikipedia.org/wiki/Nayanars", "association", "0.7"
        rows.append({"name": name, "figure_id": q or f"slug:hindu:{fold(name)}", "figure": f"{name}, one of the 63 Nayanars (Tamil Shaiva saints)",
                     "sex": sex, "original": ta, "translit": "", "language": "Tamil", "tradition": "Hindu", "subtradition": "Shaiva",
                     "corpus": "Periya Puranam", "text": "Tiruttondar Puranam (Sekkizhar)", "passage": passage, "url": url, "occurrences": "",
                     "entity_type": "saint", "name_role": "personal", "status": status,
                     "relation": "" if status == "attested" else "the e-texts on Project Madurai cover sarukkams 1-6 only; listed among the 63 on Wikipedia",
                     "source": SRC_PM.format("Periya Puranam, " + ", ".join(PERIYA)) + "; English Wikipedia list of 63 Nayanars (CC BY-SA); Wikidata (CC0)",
                     "confidence": conf})
    print(f"  Periya Puranam: {len(chapters)} chapter headings; {found} of {len(nay)} Nayanars matched to a chapter", file=sys.stderr)
    # Alvars: the twelve Wikidata lists as part of the Alvars (Q448316), with their works in the Nalayira Divya Prabandham
    al = sparql("""SELECT DISTINCT ?item ?en ?ta ?sex WHERE { ?item wdt:P361 wd:Q448316 . ?item rdfs:label ?en FILTER(lang(?en)="en")
      ?item rdfs:label ?ta FILTER(lang(?ta)="ta") OPTIONAL { ?item wdt:P21 ?sex } }""", os.path.join(RAW, "tamil", "wd-alvars.json"))
    texts = {f: pm_text(f) for f in PRABANDHAM}
    for r in al:
        q = r["item"].rsplit("/", 1)[-1]; ta = r["ta"]; en = r["en"]
        stem = key(ta)
        hit = None
        for f, t in texts.items():
            i = t.find(ta) if ta in t else t.find(stem) if len(stem) >= 3 else -1
            if i >= 0: hit = (f, t[:i].count("\n")); break
        sex = "girl" if r.get("sex", "").endswith("Q6581072") else "boy" if r.get("sex", "").endswith("Q6581097") else ""
        name = re.sub(r"\s+(Alvar|Alwar|Aazhwar)$", "", en) if en not in ("Andal", "Nammalvar", "Periyalvar") else en
        rows.append({"name": name, "figure_id": q, "figure": f"{en}, one of the twelve Alvars (Tamil Vaishnava poet-saints)", "sex": sex,
                     "original": ta, "translit": "", "language": "Tamil", "tradition": "Hindu", "subtradition": "Vaishnava",
                     "corpus": "Nalayira Divya Prabandham", "text": PRABANDHAM[hit[0]] if hit else "",
                     "passage": f"{PRABANDHAM[hit[0]]} (Project Madurai {hit[0]}, author heading)" if hit else "author of hymns in the Prabandham",
                     "url": PM + (hit[0] if hit else "pmuni0005_01") + ".html", "occurrences": "", "entity_type": "saint",
                     "name_role": "personal", "status": "association",
                     "relation": "named as the author of these hymns in the e-text, not inside the hymns",
                     "source": SRC_PM.format("Nalayira Divya Prabandham, pm0005-pm0008") + "; Wikidata (CC0)", "confidence": "0.8" if hit else "0.7"})
    print(f"  Alvars: {len(al)} from Wikidata", file=sys.stderr)
    return rows

# ───────────────────────────────────────────────────────────── Part 1: modern given names (Wiktionary, Wikidata) and the tadbhava pass
NON_INDIC_SRC = {"ar", "fa", "he", "en", "pt", "la", "grc", "tr", "ota", "arc", "syc", "fr", "de", "it", "es", "ru", "el", "hbo", "ur", "ps", "ckb", "ku"}
DEITY_TEXT = re.compile(r"\b(Vishnu|Viṣṇu|Shiva|Śiva|Krishna|Kṛṣṇa|Lakshmi|Lakṣmī|Durga|Durgā|Parvati|Pārvatī|Ganesha|Gaṇeśa|Saraswati|Sarasvatī|"
                        r"Hindu|goddess|Rama\b|Rāma|Sita|Sītā|Radha|Rādhā|Hanuman|Murugan|Kartikeya|Skanda|Indra|Brahma|Mahabharata|Ramayana|"
                        r"Veda|Purana|epithet)\b")
ROMAN_OK = {"Hindi", "Sanskrit", "Marathi", "Gujarati", "Punjabi", "Nepali", "Telugu", "Kannada", "Odia", "Konkani", "Sindhi", "Maithili", "Bhojpuri"}
SKIP_DONE = {"shagun", "raj", "sukhi", "suhana", "kala", "neil", "kapil", "suhani", "maya"}   # already settled in names.js


def english_from_indic():
    """native form → (English spelling, sex) from 'English … given names from <Indian language>'"""
    out = {}
    for L in FROM_LANGS:
        for gk, g in (("male", "b"), ("female", "g"), ("unisex", "e")):
            for title, text in wikt_category(f"English {gk} given names from {L}").items():
                sec = section(text, "English")
                for m in re.finditer(r"\{\{(?:bor|der|inh|bor\+|der\+|lbor|m|l)\|(?:en\|)?(%s)\|([^|}]+)" % "|".join(v for k, v in LCODE.items() if k != "English"), sec):
                    nat = m.group(2).strip()
                    if re.search(r"[ऀ-෿]", nat):
                        out.setdefault(unicodedata.normalize("NFC", nat), []).append((title, g, L))
    return out


def wikt_given(site_, mw_keys):
    """[{native, lang, sex, latin, how, meaning, sa, hindu, title}] from the Indian-language given-name categories"""
    en = english_from_indic()
    rec = site_["rec"]
    rows, pairs, raw = [], [], []
    for L in GN_LANGS:
        sexes = collections.defaultdict(set)
        texts = {}
        for gk, g in (("given names", ""), ("male given names", "b"), ("female given names", "g"), ("unisex given names", "e")):
            for t, x in wikt_category(f"{L} {gk}").items():
                texts[t] = x
                if g == "e": sexes[t] |= {"b", "g"}
                elif g: sexes[t].add(g)
        for t, x in texts.items():
            if not re.search(r"[ऀ-෿]", t) or " " in t: continue
            sec = section(x, L)
            if not sec: continue
            sx = sexes[t] | given_sex(sec)
            src = other_etymon(sec)
            if src in NON_INDIC_SRC: continue
            if re.search(r"\{\{given name\|[^}]*(?:from|eq)=[^}]*(Arabic|Persian|Hebrew|English|Greek|Latin|Portuguese|Turkish)", sec): continue
            raw.append((L, t, sec, sx)); pairs.append((LCODE[L], t))
    xl = xlit_all(pairs)
    for L, t, sec, sx in raw:
        if not sx: continue
        code = LCODE[L]
        gm = re.search(r"\{\{given name\|[^}]*?\b(?:meaning|m)=([^|}]+)", sec)
        sa = sanskrit_etymon(sec)
        meaning = wclean(gm.group(1)) if gm else (sa["gloss"] if sa and sa["gloss"] else "")
        if not meaning:
            q = re.search(r"\{\{(?:m|l|bor|der|inh|af|compound)\|[^{}]*?\|t=([^|}]+)", sec)
            if q: meaning = wclean(q.group(1))
        latin, how = "", ""
        enx = en.get(unicodedata.normalize("NFC", t))
        if enx: latin, how = enx[0][0], "the English Wiktionary entry"
        rom = xl.get((code, t), "")
        sp = common_spellings(rom, code) if rom else {}
        if L == "Assamese": sp = {}                    # Assamese x (ś/ṣ/s) has no common Latin counterpart in the rules
        if not latin and sp:
            reg = sorted(((rec[fold(v)]["count"], v) for v in sp if fold(v) in rec and rec[fold(v)]["count"] >= 5), reverse=True)
            if reg:
                latin = max(rec[fold(reg[0][1])]["names"].items(), key=lambda kv: kv[1])[0]; how = "the birth records"
            elif L in ROMAN_OK:
                latin = min(sp, key=sp.get); how = f"Wiktionary's romanization {rom}"
        if not latin or not re.fullmatch(r"[A-Za-z][A-Za-z'-]*", latin): continue
        hindu = bool(DEITY_TEXT.search(wclean(sec)[:600]))
        rows.append({"native": t, "lang": L, "sex": sx, "latin": latin, "how": how, "meaning": meaning[:80], "sa": sa, "hindu": hindu, "rom": rom})
    return rows


def wd_given(site_, items):
    out = []
    for q, e in items.items():
        en = e["labels"].get("en", "")
        if not en or not re.fullmatch(r"[A-Z][a-z]+(?:-[A-Z]?[a-z]+)?", en) or not e["sex"]: continue
        nat = [(c, t) for c, t in e.get("native", []) if c in LABEL_LANG and re.search(r"[ऀ-෿]", t)]
        nat.sort(key=lambda ct: LABEL_LANG[ct[0]] not in e["langs"])
        if not nat:
            order = [k for k, v in LABEL_LANG.items() if v in e["langs"]] + list(LABEL_LANG)
            nat = [(c, e["labels"][c]) for c in order if c in e["labels"] and re.search(r"[ऀ-෿]", e["labels"][c])][:1]
        if not nat: continue
        code, native = nat[0]
        lang = LABEL_LANG[code]
        desc = e.get("desc", "")
        if re.search(r"Arab|Muslim|Islam|Hebrew|Christian|Persian|English|Latin|Greek|Turkish|Urdu", desc): continue
        out.append({"qid": q, "latin": en, "native": native, "code": code, "lang": lang, "langs": e["langs"], "sex": e["sex"],
                    "bearers": e.get("bearers", 0), "desc": desc})
    return out


def tadbhava(site_, E, mw_keys):
    """Hindi, Marathi, Gujarati, Bengali, Punjabi, Nepali words from Sanskrit whose common spellings are names on the site"""
    rec, cult, hand = site_["rec"], site_["cult"], site_["hand"]
    on_site = set(rec) | set(cult)
    cand, pairs = [], []
    for L in TADBHAVA_LANGS:
        for t, x in wikt_category(f"{L} terms derived from Sanskrit").items():
            if " " in t or not re.search(r"[ऀ-෿]", t): continue
            sec = section(x, L)
            sa = sanskrit_etymon(sec) if sec else None
            if not sa: continue
            defs = definitions(sec)
            if not defs: continue
            cand.append((L, t, sec, sa, defs)); pairs.append((LCODE[L], t))
    xl = xlit_all(pairs)
    out = collections.defaultdict(list)
    for L, t, sec, sa, defs in cand:
        rom = xl.get((LCODE[L], t), "")
        for v in common_spellings(rom, LCODE[L]) if rom else {}:
            k = fold(v)
            if k in on_site and k not in hand and k not in SKIP_DONE and len(k) >= 3:
                out[k].append({"lang": L, "word": t, "rom": rom, "sa": sa, "defs": defs, "sec": sec})
    return out


def sa_gloss(sa_word, E):
    """Sanskrit etymon (Devanagari or IAST) → (iast, meaning, citation) checked against Apte"""
    iast = (S.deva2iast(sa_word) if re.search(r"[\u0900-\u097f]", sa_word) else sa_word).strip()
    key = iast2slp(iast)
    for k2 in (key, key[:-1] + "a" if key.endswith("A") else key):
        if k2 in E:
            g, cite, st_ = checked_meaning(k2, E)
            if st_ == "disagree": MEANING_REVIEW.append((iast, iast))
            if g: return iast, re.sub(r"\s*\[.*$", "", g).strip(" ,;"), cite
    return iast, "", ""


def assemble():
    t0 = time.time()
    st = site()
    print(f"site: {len(st['rec']):,} record names, {len(st['cult']):,} storied, {len(st['hand']):,} hand entries", file=sys.stderr)
    evidence = {k for k, cs in st["cult"].items() if cs & (INDIAN - {"South Asian"})} | set(st["sacred"])
    rec, cult, hand = st["rec"], st["cult"], st["hand"]
    report = {"counts": {}}

    # Part 2 first: its names feed the texts slot
    E = load_mw(); mw_keys = set(E)
    sah, unresolved = sahasranama_rows(mw_keys, E)
    # a Sahasranāma name is kept only when people bear it: in the birth records (names-db / names-extra), or on an
    # Indian-language given-name list (Wiktionary, Wikidata, the site's culture lists)
    born = {k for k, v in st["rec"].items() if v["count"] > 0 or v["names"]} | {k for k, cs in st["cult"].items() if cs & INDIAN}
    report["sahasranama names dropped (no one bears them)"] = dict(collections.Counter(r["corpus"] for r in sah if fold(r["name"]) not in born))
    sah = [r for r in sah if fold(r["name"]) in born]
    srows, sreview, sstats = scripture_rows()
    tam = tamil_rows()
    more = sah + srows + tam + ramayana_rows()
    figures_rows()
    write_more(more)
    sacred_more = collections.defaultdict(set)
    for r in more:
        if r["entity_type"] not in ("place", "tribe", "concept"): sacred_more[fold(r["name"])].add(r["corpus"])
    for k, v in sacred_more.items(): st["sacred"].setdefault(k, set()).update(v)
    report["scripture"] = report.get("scripture", {})
    report["scripture"] |= {"rows by corpus": dict(collections.Counter(r["corpus"] for r in more)),
                           "review (not written, below confidence 0.6)": dict(collections.Counter(r["corpus"] for r in sreview)),
                           "sahasranama names left out": dict(unresolved),
                           "examples": [[r["name"], r["original"], r["corpus"], r["passage"], r["figure"], r["sex"]] for r in more[::max(1, len(more) // 30)]]}

    # the Monier-Williams pass
    mw_rows, mw_stats, mw_ex = mw_pass(st, evidence, set())
    report["mw"] = dict(mw_stats)
    report["mw_reassign_examples"] = [[r[0], r[6]] for r in mw_ex.get("reassign", [])[:: max(1, len(mw_ex.get("reassign", [])) // 20)][:20]]

    final = {}
    origin = {}
    for k, r in mw_rows.items():
        if k in SKIP_DONE or k in hand: continue
        final[k] = r; origin[k] = "mw-" + ("reassign" if "given in" in r[6] and r[6].startswith("Written") else "match" if k in rec or k in cult else "new")

    # the tadbhava pass (Wiktionary words from Sanskrit that are names on the site)
    tb = tadbhava(st, E, mw_keys)
    tstats = collections.Counter()
    for k, hits in tb.items():
        if k in final and final[k][5]: tstats["already from MW"] += 1; continue
        natives = st["indic_native"].get(k, []) + [m.group(1) for r in st["culture_rows"].get(k, []) for m in [re.search(r"Written ([^\s.]+)", r[6] or "")] if m]
        nd = {deva_key(to_deva(n)) for n in natives if to_deva(n)}
        hits = [h for h in hits if not nd or deva_key(to_deva(h["word"]) or h["word"]) in nd]
        if not hits: tstats["native spelling disagrees"] += 1; continue
        hits = [h for h in hits if re.search(r"[\u0900-\u097fa-zāīūṛśṣṇ]", h["sa"]["sa"]) and h["sa"]["sa"] != "-"]
        if not hits: tstats["no Sanskrit word"] += 1; continue
        is_given = any(given_sex(h["sec"]) for h in hits)
        indian_list = bool(cult.get(k, set()) & (INDIAN - {"Bollywood", "South Asian"}))
        recs = rec[k]["count"] if k in rec else 0
        # a word counts as the source of a name only when the site's Indian spelling is that word, Wiktionary calls it a given
        # name, the name is on an Indian-language list, or families register it (25+ births)
        if not (nd or is_given or indian_list):
            tstats["no sign the word is used as a name"] += 1; continue
        others = sorted(c for c in cult.get(k, ()) if c not in INDIAN)          # a Thai Nicha is not Hindi nīcā 'low'
        # another culture's spelling (Nora, Tina, Dana, Ben) is taken for a Hindi word only when the site's Indian spelling
        # of the name is that very word, or Wiktionary calls the word a given name
        if (others or k in WORDS) and not (nd or is_given): tstats["no Indian use and another culture's name"] += 1; continue
        if any(UNSUITABLE.search(x) for h in hits for _, ds in h["defs"] for kind, x in ds[:1]): tstats["unsuitable sense"] += 1; continue
        h = sorted(hits, key=lambda h: (TADBHAVA_LANGS.index(h["lang"]), not any(p == "Proper noun" for p, _ in h["defs"])))[0]
        gs = given_sex(h["sec"])
        site_sex = set(rec[k]["sex"]) if k in rec else set()
        for r in st["culture_rows"].get(k, []): site_sex |= {"g"} if r[1] == "g" else {"b"} if r[1] == "b" else {"g", "b"} if r[1] == "e" else set()
        sexes = gs or site_sex
        if not sexes: tstats["no sex"] += 1; continue
        d = next((x for p, ds in h["defs"] for kind, x in ds if kind == "DEF" and not re.match(r"^[A-Z]", x)), "")   # not "Dushyanta, a king…"
        d = ", ".join(suitable_parts(d))
        d = re.split(r";", d)[0]
        if len(d) > 70: d = re.sub(r"[,\s]+\S*$", "", d[:70]) + "…"
        iast, gl, cite = sa_gloss(h["sa"]["sa"], E)
        sgl = gl or re.sub(r"\s*\[.*$", "", h["sa"]["gloss"]).strip(" ,;")
        an_ = {n: c for n, c in (rec[k]["names"].items() if k in rec else []) if re.fullmatch(r"[A-Za-z][A-Za-z'-]*", n)}
        disp = max(an_.items(), key=lambda kv: kv[1])[0] if an_ else st["culture_rows"][k][0][0] if st["culture_rows"].get(k) else None
        if not disp or not re.fullmatch(r"[A-Za-z][A-Za-z'-]*", disp): continue
        cites = "Wiktionary" + (f"; {cite}" if gl else "")
        sent = f"Written {h['word']}, {h['lang']} {h['rom']}" + (f" ‘{d}’" if d else "") + f", {h['sa']['kind']} from Sanskrit {iast}" + (f" ‘{sgl}’" if sgl else "") + f" ({cites})."
        hindu = k in st["sacred"] or bool(DEITY_TEXT.search(d))
        g = "e" if len(sexes) > 1 else next(iter(sexes))
        if not gl and d: WIKT_MEANING.append(disp); MEANING_STATUS["wiktionary"] += 1
        # the modern word's meaning leads (Garima 'dignity'); the Sanskrit root stays in the sentence
        final[k] = [disp, g, "Indian", "Sanskrit", "Hindu" if hindu else "", d or gl, sent, ",".join(sorted(st["sacred"].get(k, ()))), "real",
                    ["South Asian", h["lang"]], ease_of(disp, rec[k]["count"] if k in rec else 0)]
        origin[k] = "tadbhava"; tstats["rows"] += 1
    report["tadbhava"] = dict(tstats)

    # modern given names: Wiktionary, then Wikidata
    has_indian = {k for k in set(cult) | set(hand) if cult.get(k, set()) & (INDIAN - {"Bollywood", "South Asian"})}
    gstats = collections.Counter()
    for r in wikt_given(st, mw_keys):
        k = fold(r["latin"])
        if k in hand or k in SKIP_DONE: gstats["in names.js"] += 1; continue
        if k in has_indian and origin.get(k, "") != "mw-new": gstats["already on the site as Indian"] += 1; continue
        if k in final and origin[k] in ("tadbhava", "mw-reassign", "mw-match"): gstats["already from MW/tadbhava"] += 1; continue
        if any(c not in INDIAN and c not in SANSKRIT_LINKED for c in cult.get(k, ())):
            gstats["spelling is another culture's name (Charles, Amber, Kieran)"] += 1; continue
        mw = final.get(k) if origin.get(k) == "mw-new" else None
        g = "e" if len(r["sex"]) > 1 else next(iter(r["sex"]))
        lang = r["lang"]
        sent = f"{an(lang)} {lang} given name (Wiktionary). Written {r['native']}."
        if r["how"].startswith("Wiktionary's"): sent += f" Latin spelling from {r['how']}."
        elif r["how"]: sent += f" Latin spelling as in {r['how']}."
        meaning = ", ".join(suitable_parts(r["meaning"]))
        language = lang
        if r["sa"]:
            iast, gl, cite = sa_gloss(r["sa"]["sa"], E)
            language = "Sanskrit"
            sent += f" From Sanskrit {iast}" + (f" ‘{gl}’ ({cite})" if gl else (f" ‘{r['sa']['gloss']}’ (Wiktionary)" if r["sa"]["gloss"] else "")) + "."
            meaning = gl or meaning
        elif mw:
            language = "Sanskrit"; meaning = meaning or mw[5]
            sent += " " + mw[6].replace("From Sanskrit", "From Sanskrit", 1)
        others = sorted(c for c in cult.get(k, ()) if c not in INDIAN and c not in SANSKRIT_LINKED)
        if others: sent += f" The same spelling is also {an(others[0]).lower()} {lst(others[:3])} name, unrelated."
        if meaning and meaning == r["meaning"] and not (r["sa"] and sa_gloss(r["sa"]["sa"], E)[1]): WIKT_MEANING.append(r["latin"]); MEANING_STATUS["wiktionary"] += 1
        hindu = r["hindu"] or k in st["sacred"] or (mw and mw[4] == "Hindu")
        culture = "Malayali" if lang == "Malayalam" else lang
        final[k] = [r["latin"], g, culture, language, "Hindu" if hindu else "", meaning, sent, ",".join(sorted(st["sacred"].get(k, ()))), "real",
                    ["South Asian"], ease_of(r["latin"], rec[k]["count"] if k in rec else 0)]
        origin[k] = "wiktionary"; gstats["rows"] += 1
    items = wikidata()
    for r in wd_given(st, items):
        k = fold(r["latin"])
        if k in hand or k in SKIP_DONE or (k in has_indian and origin.get(k) != "mw-new") or origin.get(k) in ("tadbhava", "mw-reassign", "mw-match", "wiktionary", "wikidata"):
            gstats["wikidata: already covered"] += 1; continue
        dv = to_deva(r["native"]) if r["code"] != "ta" else ""
        key = iast2slp(S.deva2iast(dv)) if dv else ""
        mwk = "" if len(key) < 3 else key if key in mw_keys else (key + "a" if key + "a" in mw_keys else "")
        others = sorted(c for c in cult.get(k, ()) if c not in INDIAN and c not in SANSKRIT_LINKED)
        # only names no other culture on the site claims (Edmund, Karen and Nadira have Tamil labels too), whose Indic spelling
        # is a Sanskrit headword or that Wikidata files under an Indian language
        if others or not (mwk or (r["langs"] & {"Tamil", "Telugu", "Kannada", "Malayalam", "Punjabi"})):
            gstats["wikidata: no Indian-language tie"] += 1; continue
        g = "e" if len(r["sex"]) > 1 else next(iter(r["sex"]))
        lang = r["lang"]
        sent = f"{an(lang)} {lang} given name (Wikidata {r['qid']})" + (f", borne by {r['bearers']} {'person' if r['bearers'] == 1 else 'people'} from India on Wikidata" if r["bearers"] else "") + f". Written {r['native']}."
        meaning, language = "", lang
        if mwk:
            iast, gl, cite = sa_gloss(S.slp2iast(mwk), E)
            if gl: sent += f" From Sanskrit {iast} ‘{gl}’ ({cite})."; meaning = gl; language = "Sanskrit"
        if others: sent += f" The same spelling is also {an(others[0]).lower()} {lst(others[:3])} name, unrelated."
        hindu = k in st["sacred"]
        final[k] = [r["latin"], g, "Malayali" if lang == "Malayalam" else lang, language, "Hindu" if hindu else "", meaning, sent,
                    ",".join(sorted(st["sacred"].get(k, ()))), "real", ["South Asian"], ease_of(r["latin"], rec[k]["count"] if k in rec else 0)]
        origin[k] = "wikidata"; gstats["wikidata rows"] += 1
    report["given"] = dict(gstats)
    report["meaning status"] = dict(MEANING_STATUS)
    report["meaning left blank: MW and Apte share no sense"] = sorted({a for a, b in MEANING_REVIEW})
    report["meaning from Wiktionary (neither dictionary has the word)"] = sorted(set(WIKT_MEANING))

    # texts slot for every row: the corpora this name is attested in (sacred TSVs incl. indic-more)
    for k, r in final.items():
        tx = set(filter(None, r[7].split(","))) | st["sacred"].get(k, set())
        r[7] = ",".join(sorted(tx))
        if tx & (HINDU_TEXT | {"Vishnu Sahasranama", "Shiva Sahasranama", "Lalita Sahasranama", "Samaveda", "Periya Puranam",
                               "Nalayira Divya Prabandham"} | set(sacred_more_corpora())) and not r[4]:
            r[4] = "Hindu"
    # keep a row only when people bear the name or it is already on the site; MW-only names of minor men, kings and
    # authors go, unless the figure is a major deity or sacred figure with an easy spelling
    attested = set(rec) | set(cult) | set(hand) | given_attested(st)
    before = len(final)
    keep = {}
    for k, r in final.items():
        major = r[4] == "Hindu" and r[10] == 1 and k in st["sacred"]
        if k in attested or major: keep[k] = r
    report["attestation filter"] = {"before": before, "after": len(keep), "dropped": before - len(keep)}
    final = keep
    for r in final.values():                      # last guard: no banned word in any meaning
        if r[5] and BANNED.search(r[5]) and not r[5].startswith("a name of"): r[5] = ", ".join(suitable_parts(r[5]))
    report["_origin"] = origin
    json.dump({"final": final, "report": report}, open(os.path.join(RAW, "prereview.json"), "w", encoding="utf-8"), ensure_ascii=False)
    finish(final, report)


def finish(final, report):
    origin = report.pop("_origin", {}); t0 = T0
    apply_review(final, report)
    report["hand meanings not found in MW (left as built)"] = apply_hand(final)
    deva_check(final)
    report["compound meanings"] = compound_pass(final)
    write_review(final)
    write_review_log()
    C0 = collections.Counter(a for *_, a in REVIEW_LOG if not a.startswith("Devanagari"))
    report["review-all"] = {"fixed": C0["fixed"], "blanked": C0["blanked"],
                            "dropped": sum(v for a, v in C0.items() if a.startswith("dropped")),
                            "Devanagari fixed": sum(1 for *_, a in REVIEW_LOG if a.startswith("Devanagari"))}
    rows = sorted(final.values(), key=lambda r: (r[10], fold(r[0]), r[0]))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("[\n" + ",\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n]\n")
    C = collections.Counter
    report["counts"] = {"rows": len(rows), "by origin": dict(C(origin[fold(r[0])] for r in rows if fold(r[0]) in origin)),
                        "by culture": dict(C(r[2] for r in rows).most_common()), "by language": dict(C(r[3] for r in rows).most_common()),
                        "by sex": dict(C(r[1] for r in rows)), "by ease": dict(C(r[10] for r in rows)),
                        "Hindu-tagged": sum(1 for r in rows if r[4]), "with meaning": sum(1 for r in rows if r[5])}
    report["samples"] = [r for r in rows[:: max(1, len(rows) // 25)][:25]]
    json.dump(report, open(REPORT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(report["counts"], ensure_ascii=False, indent=1), file=sys.stderr)
    print(f"wrote {len(rows):,} rows → {OUT}; report → {REPORT} ({time.time() - t0:.0f}s)", file=sys.stderr)


# ───────────────────────────────────────────────────────────── hand review of the 300 most-given names (raw/hindu/review.tsv)
# Each meaning below is a sense Monier-Williams gives for that headword (checked word by word in mw_text() at build time);
# it replaces an automatic pick that read oddly or negatively. "" leaves the meaning blank.
OVERRIDE = {
    "Mira": ("mIra", "the ocean"), "Adi": ("Adi", "beginning, commencement"), "Trisha": ("tfzA", "desire"),
    "Kali": ("kali", ""), "Kash": ("kASa", ""), "Reva": ("revA", "the Narmadā river"), "Avani": ("avani", "the earth"),
    "Anjali": ("aYjali", "reverence, salutation"), "Malaya": ("malaya", ""), "Aja": ("aja", "not born, existing from all eternity"),
    "Krish": ("kfza", ""), "Nikhil": ("niKila", "complete, whole, all"), "Anisha": ("anISa", "paramount"),
    "Ravi": ("ravi", "the sun"), "Kesha": ("keSa", ""), "Arun": ("aruRa", "ruddy, the dawn"), "Aruna": ("aruRa", "ruddy, the dawn"),
    "Aarush": ("aruza", "red, the sun"), "Hari": ("hari", "a name of Viṣṇu-Kṛṣṇa"), "Krisha": ("kfSa", "small, little"),
    "Varun": ("varuRa", "god of the waters"), "Nayana": ("nayana", "the eye"), "Nayan": ("nayana", "the eye"),
    "Neela": ("nIla", "dark blue"), "Samaya": ("samaya", "the right moment"), "Samay": ("samaya", "the right moment"),
    "Rajan": ("rAjan", "a king, prince, chief"), "Rohit": ("rohita", "red, reddish"), "Parth": ("pArTa", "a name of Arjuna"),
    "Mahi": ("mahI", "the earth"), "Amrita": ("amfta", "immortal, nectar"), "Vijay": ("vijaya", "victory"), "Janya": ("janya", ""),
    "Agastya": ("agastya", ""), "Vanita": ("vanitA", "a loved wife"), "Shala": ("SAla", ""),
    "Manisha": ("manIzA", "wisdom, intelligence"), "Sunil": ("sunIla", "very dark blue"), "Kush": ("kuSa", "the sacred grass used at religious ceremonies"),
    "Raghav": ("rAGava", "descendant of Raghu, a name of Rāma"), "Ishani": ("ISAnI", "a name of Durgā"),
    "Vinay": ("vinaya", "guidance, propriety of conduct, modesty"), "Avinash": ("avinASin", "imperishable"), "Kal": ("kAla", ""),
    "Deepak": ("dIpaka", "a light, lamp"), "Abhishek": ("aBizeka", "anointing, consecrating"), "Lalita": ("lalita", "gentle, charming, lovely"),
    "Abhay": ("aBaya", "secure, safety"), "Neev": ("nIvI", ""), "Shruti": ("Sruti", "sacred knowledge, the Veda"),
    "Dhara": ("DarA", "the earth"), "Shyam": ("SyAma", "dark-coloured, a name of Kṛṣṇa"), "Varsha": ("varza", "rain"),
    "Vansh": ("vaMSa", "lineage, race, family"), "Vinita": ("vinIta", "modest, well-behaved"), "Anuj": ("anuja", "a younger brother"),
    "Sagan": ("sagaRa", ""), "Ajit": ("ajita", "not conquered, invincible"), "Naman": ("namana", "bowing"),
    "Madhav": ("mADava", "a name of Kṛṣṇa or Viṣṇu"), "Tej": ("tejas", "brilliance, splendour"), "Mala": ("mAlA", "a garland, wreath"),
    "Medha": ("meDA", "intelligence, wisdom"), "Mohan": ("mohana", ""), "Mohit": ("mohita", ""), "Anoop": ("anUpa", ""),
    "Gaya": ("gaya", ""), "Vidhi": ("viDi", "rule, destiny"), "Ashok": ("aSoka", "the Aśoka tree"), "Uday": ("udaya", "rising, the rise of the sun"),
    "Siddhartha": ("sidDArTa", "one who has accomplished an aim"), "Pratik": ("pratIka", "image, symbol"), "Shilpa": ("Silpa", "art, any manual art or craft"),
    "Anagha": ("anaGa", "faultless, handsome"), "Sayana": ("sayana", ""), "Eesha": ("ISa", "lord, master, a name of Śiva"),
    "Ishan": ("ISAna", "a ruler, master, a name of Śiva"), "Suri": ("sUri", "a learned man, sage"), "Puja": ("pUjA", "worship, reverence"),
    "Rakesh": ("rAkeSa", ""), "Kumar": ("kumAra", "a child, boy, youth; a name of Skanda"), "Atharv": ("aTarvan", "a priest who has to do with fire and Soma"),
    "Dinesh": ("dineSa", "the sun"),
    "Nala": ("nala", "a king of the Niṣadhas, husband of Damayantī"), "Rudra": ("rudra", "a name of Śiva"), "Ved": ("veda", "knowledge, sacred knowledge"),
    "Sahaj": ("sahaja", "innate, natural"), "Sandhya": ("saMDyA", "morning or evening twilight"), "Sharda": ("SAradA", "a name of Sarasvatī"),
    "Kalyani": ("kalyARa", "beautiful, auspicious"), "Prithvi": ("pfTivI", "the earth"), "Vraj": ("vraja", ""), "Karna": ("karRa", ""),
    "Shalin": ("SAlin", ""), "Dala": ("dala", ""), "Hema": ("heman", "gold"), "Arjuna": ("arjuna", "white, clear"),
    "Avantika": ("avantikA", ""), "Devika": ("devikA", "a class of goddesses"), "Kiran": ("kiraRa", "a ray or beam of light, a sun- or moonbeam"),
}
DROP = {"Kieran", "Charlee", "Sunny", "Josh", "Love", "Roch", "Babara", "Jamee", "Tilla", "Jina", "Yakub", "Dallan", "Seyana", "Dalmi",
        "Khan", "Gul", "Lota", "Santana", "Lolita", "Vada", "Kora", "Savana", "Shem", "Shana", "Samar", "Avah", "Nagila", "Shamika",
        "Sahel", "Khara", "Chari", "Kalee", "Rutha", "Kaliya", "Ahinara", "Niv", "Robi", "Haya", "Sham", "Samatha", "Nadeen",
        "Sharika", "Anida", "Bana", "Shara", "Shon", "Arav", "Shila", "Shalini", "Richa", "Narayan", "Kartik", "Arushi",
        "Manoj", "Sheela", "Radhika", "Soham", "Kunal", "Rajesh", "Vedant", "Aviraj", "Shreya", "Shanda", "Navraj", "Shameeka", "Maheen",
        "Jeena", "Shina", "Khaliya", "Dallana", "Tandi", "Alee", "Charmin", "Bara", "Kal", "Kash", "Kasha"}


def mw_text(key1):
    """every Monier-Williams line for a headword, lowercased (to check a hand-picked sense really is MW's)"""
    global _MWT
    if "_MWT" not in globals():
        _MWT = collections.defaultdict(str)
        for line in open(MW_XML, encoding="utf-8"):
            m = re.search(r"<key1>([^<]+)</key1>.*?<body>(.*?)</body>", line)
            if m: _MWT[m.group(1)] += " " + html.unescape(re.sub(r"<[^>]+>", " ", m.group(2))).lower()
    return _MWT.get(key1, "")


def hand_decisions():
    """raw/hindu/hand/*.txt, written while reading every row: Name=meaning (a Monier-Williams sense of the row's own
    headword, checked word by word), Name=- (blank: no good sense), Name=X (drop: not an Indian given name, or unfit)"""
    out = {}
    for f in sorted(glob.glob(os.path.join(RAW, "hand", "*.txt"))):
        for line in open(f, encoding="utf-8"):
            if "=" in line and not line.startswith("#"):
                n, v = line.rstrip("\n").split("=", 1); out[n.strip()] = v.strip()
    return out


def apply_hand(final):
    H = hand_decisions()
    unverified = []
    for k in list(final):
        r = final[k]
        v = H.get(r[0])
        if v is None or v == "keep":
            # automatic tidy: no odd tail after a deity; a compound chain stays only when a reader kept it ("keep")
            m = re.match(r"^(a name of [^;]+); (.*)$", r[5])
            if m and not POSITIVE.search(m.group(2)): r[5] = m.group(1); REVIEW_LOG.append((r[0], m.group(0), r[5], "fixed"))
            if v is None and " + " in r[5] and "‘" in r[5]: v = "-"
            else: continue
        old = r[5]
        if v == "X":
            REVIEW_LOG.append((r[0], old, "", "dropped")); del final[k]; continue
        if v == "-":
            r[5] = ""
            r[6] = re.sub(r"(Sanskrit [^\s‘(]+)(, which MW divides into [^(]*?)? ‘[^’]*’", r"\1", r[6], count=1)
            r[6] = re.sub(r", which MW divides into [^(]*?(?= \()", "", r[6])
            REVIEW_LOG.append((r[0], old, "", "blanked")); continue
        sk = re.search(r"Sanskrit ([a-zāīūṛṝḷṃḥṅñṭḍṇśṣ]+)", r[6])
        key = iast2slp(sk.group(1)) if sk else ""
        txt = " ".join(mw_text(x) for x in {key, key + "a", key[:-1] + "a", key[:-1], key[:-1] + "A"} if x) + " " + apte().get(key, "")
        words = [w for w in re.findall(r"[a-zāīūṛśṣṇṭḍ'’-]{4,}", v.lower()) if not re.search(r"[āīūṛśṣṇṭḍ]", w) or w in txt]
        miss = [w for w in re.findall(r"[a-zāīūṛśṣṇṭḍ]{4,}", v.lower()) if w.isascii() and w not in txt and w not in
                ("name", "wife", "father", "from", "with", "that", "which", "free", "mother", "son", "daughter")]
        if miss:
            unverified.append((r[0], v, miss)); continue
        r[5] = v
        if old and f"‘{old}’" in r[6]: r[6] = r[6].replace(f"‘{old}’", f"‘{v}’")
        else: r[6] = re.sub(r"(Sanskrit [^\s‘(]+)(, which MW divides into [^(]*?)?( ‘[^’]*’)?(?= \()", lambda x: f"{x.group(1)} ‘{v}’", r[6], count=1)
        REVIEW_LOG.append((r[0], old, v, "fixed"))
    return unverified


def apply_review(final, report):
    bad, done = [], 0
    for k in list(final):
        r = final[k]
        if r[0] in DROP: REVIEW_LOG.append((r[0], r[5], "", "dropped")); del final[k]; continue
        if r[0] in OVERRIDE:
            key1, m = OVERRIDE[r[0]]
            if m:
                txt = mw_text(key1)
                miss = [w for w in re.findall(r"[a-zāīūṛśṣṇṭḍ]{4,}", m.lower()) if w not in txt and w not in ("name", "agastya", "arjuna", "durgā", "rāma", "kṛṣṇa", "viṣṇu", "śiva", "skanda", "narmadā", "aśoka", "niṣadhas", "damayantī")]
                if miss: bad.append((r[0], m, miss)); continue
            old = r[5]
            r[5] = m
            REVIEW_LOG.append((r[0], old, m, "fixed" if m else "blanked"))
            if old and f"‘{old}’" in r[6]: r[6] = r[6].replace(f"‘{old}’", f"‘{m}’" if m else "")
            elif not m: r[6] = re.sub(r"(Sanskrit [^\s‘(]+) ‘[^’]*’", r"\1", r[6], count=1)
            elif m and not r[6].count(f"‘{m}’"): r[6] = re.sub(r"(Sanskrit [^\s‘(]+) ‘[^’]*’", lambda x: f"{x.group(1)} ‘{m}’", r[6], count=1)
            r[6] = r[6].replace("  (", " (")
            done += 1
    for r in final.values(): r[6] = r[6].replace("  (", " (").replace("’’", "’")
    report["hand review"] = {"meanings replaced": done, "dropped (another culture's name or no good sense)": sorted(DROP),
                             "override not found in MW (left as built)": bad}

# ───────────────────────────────────────────────────────────── the native script must spell the whole name
REVIEW_LOG = []          # (name, old meaning, new meaning, action) → raw/hindu/review-all.tsv


def deva_check(final):
    """'Written X': X read back (indic_check.matches, the merge step's own test) must carry the whole name. A wrong or partial
    spelling is replaced by the Devanagari of the Sanskrit headword when that one matches; otherwise the row goes."""
    import indic_check as IC
    for k in list(final):
        r = final[k]
        m = re.search(r"Written ([^\s,.;]+)", r[6])
        if not m: continue
        x = m.group(1)
        dv = x if re.search(r"[ऀ-ॿ]", x) else to_deva(x)
        if not dv or IC.matches(r[0], dv): continue
        sk = re.search(r"Sanskrit ([a-zāīūṛṝḷṃḥṅñṭḍṇśṣ]+)", r[6])
        alt = S.deva(sk.group(1)) if sk else ""
        if alt and IC.matches(r[0], alt):
            r[6] = r[6].replace(f"Written {x}", f"Written {alt}", 1)
            r[6] = re.sub(r" Sanskrit [ऀ-ॿ]+\.$", "", r[6])
            REVIEW_LOG.append((r[0], r[5], r[5], f"Devanagari fixed: {x} → {alt}"))
        else:
            REVIEW_LOG.append((r[0], r[5], "", f"dropped: {x} does not spell the name"))
            del final[k]


def write_review_log():
    with open(os.path.join(RAW, "review-all.tsv"), "w", encoding="utf-8") as f:
        f.write("name\told_meaning\tnew_meaning\taction\n")
        for row in REVIEW_LOG: f.write("\t".join(str(c).replace("\t", " ") for c in row) + "\n")

# ───────────────────────────────────────────────────────────── meanings for blank names from how Monier-Williams divides them
PREFIX = {"a": "not", "an": "not", "su": "good, well", "sa": "with", "saM": "together", "aBi": "towards", "anu": "after", "pra": "forth",
          "vi": "apart", "ni": "down", "ati": "beyond", "aDi": "over, above", "upa": "near", "pari": "around", "prati": "towards, back",
          "A": "near to", "ud": "up", "ut": "up", "sam": "together", "nis": "out", "nir": "without", "mahA": "great"}


def part_entry(p, E, last):
    """MW key for a compound member: as written, or its stem (a member may stand in its compound form: rAja- for rAjan)"""
    for c in ([p] if p in E else []) + [p + "a", p + "an", p + "in", p[:-1] + "a" if p.endswith("A") else "", p[:-1] if p.endswith("A") else "",
                                         p + "s", p[:-1] + "s" if p.endswith(("o", "r")) else "", p[:-1] + "t" if p.endswith("d") else ""]:
        if c and c in E: return c
    return ""


def compound_parts(key1, E):
    """[(member iast, MW key, positive sense, text for checking)] from MW's own division (key2 hyphens), or None"""
    e = E.get(key1)
    if not e: return None
    k2 = re.sub(r"[/^\\\\]", "", e.get("key2", ""))
    parts = [p for p in re.split(r"[-—]", k2) if p]
    if len(parts) < 2: return None
    out = []
    for i, p in enumerate(parts):
        k = part_entry(p, E, i == len(parts) - 1)
        if p in PREFIX and i < len(parts) - 1:
            out.append((S.slp2iast(p), p, PREFIX[p], mw_text(p) + " " + PREFIX[p])); continue
        if not k: return None
        g, cite, st = checked_meaning(k, E)
        alts = {k, p, p + "a", p + "A", p[:-1] + "A" if p.endswith("a") else "", p[:-1] + "a" if p.endswith("A") else "", p + "an", p + "in",
                p + "I", p[:-1] + "I", p[:-1] + "t" if p.endswith("d") else "", p[:-1] + "t" if p.endswith("n") else "",
                p + "n", p[:-1] + "as" if p.endswith("o") else "", p[:-1] + "s" if p.endswith(("r", "o")) else ""}
        out.append((S.slp2iast(p), k, g, " ".join(mw_text(x) + " " + apte().get(x, "") for x in alts if x)))
    return out


def stems_ok(meaning, texts):
    """every content word of a hand-written meaning occurs (by its first five letters) in the members' MW/Apte entries"""
    blob = " ".join(texts).lower()
    miss = []
    for w in re.findall(r"[a-z]{3,}", meaning.lower()):
        if w in STOPW or w in ("whose", "who", "has", "his", "her", "one", "gods", "god", "like", "lord", "the", "son", "name", "full",
                                "having", "every", "all", "its", "their", "him", "them", "own", "whom", "whose", "where"): continue
        w2 = w[:-1] if w.endswith("s") and len(w) > 3 else w
        if w2[:5] not in blob: miss.append(w)
    return miss


def describe(n):
    d = re.sub(r"\s+", " ", n["desc"])
    return d if len(d) <= 80 else d[:78].rsplit(" ", 1)[0] + "…"


def compound_pass(final):
    """drafts for every blank name (raw/hindu/compound-draft.tsv); hand-written meanings (raw/hindu/hand/c*.txt) are checked
    against the members' entries and applied; everything is logged in raw/hindu/compound-meanings.tsv"""
    E = load_mw()
    H = {}
    for f in sorted(glob.glob(os.path.join(RAW, "hand", "c*.txt"))):
        for line in open(f, encoding="utf-8"):
            if "=" in line and not line.startswith("#"):
                n, v = line.rstrip("\n").split("=", 1); H[n.strip()] = v.strip()
    draft, log, stats = [], [], collections.Counter()
    for k, r in final.items():
        if r[5]: continue
        sk = re.search(r"Sanskrit ([a-zāīūṛṝḷṃḥṅñṭḍṇśṣ]+)", r[6])
        key = iast2slp(sk.group(1)) if sk else ""
        parts = compound_parts(key, E) if key else None
        names = [n for n in E.get(key, {}).get("names", []) if not n["nonhindu"]]
        fact = describe(names[0]) if names else ""
        if not parts:
            why = "no Sanskrit headword in the row" if not key else "no MW entry" if key not in E else "MW does not divide it, or a member has no MW entry"
            log.append((r[0], "", "", "blank: " + why)); stats["blank: " + why] += 1; continue
        chain = " + ".join(f"{a} ‘{g.split(',')[0].strip()}’" if g else a for a, kk, g, t in parts)
        draft.append((r[0], S.slp2iast(key), chain, fact))
        v = H.get(r[0])
        if not v or v == "-":
            # every draft was read (raw/hindu/compound-draft.tsv); a name without a hand line had no natural, positive reading
            log.append((r[0], "", chain, "blank: read, no natural positive reading from its parts"))
            stats["blank: read, no natural positive reading from its parts"] += 1; continue
        mean, _, rest = v.partition("|")
        who, _, gl = rest.partition("|")
        miss = stems_ok(mean, [t for *_, t in parts] + [mw_text(key)]) + stems_ok(who, [mw_text(key)] + [t for *_, t in parts])
        gls = [g.strip() for g in gl.split("/")] if gl.strip() else []
        if gls and len(gls) == len(parts):
            for (a, kk, g, t), g2 in zip(parts, gls):
                if g2 and g2 != "*": miss += stems_ok(g2, [t])
            chain = " + ".join(f"{a} ‘{g2}’" if g2 and g2 != "*" else a for (a, kk, g, t), g2 in zip(parts, gls))
        elif gls: miss.append("part count")
        else: chain = " + ".join(a for a, *_ in parts)
        if miss:
            log.append((r[0], mean, chain, f"blank: words not in the members' MW entries {miss}")); stats["blank: hand meaning failed the MW check"] += 1; continue
        full = mean.strip() + (f"; {who.strip()}" if who.strip() not in ("", "-") else "")
        r[5] = full
        r[6] = re.sub(r"(Sanskrit [^\s‘(,]+)( ‘[^’]*’)?", lambda m: f"{m.group(1)}, from {chain} (as Monier-Williams divides it)", r[6], count=1)
        log.append((r[0], full, chain, "kept")); stats["kept"] += 1
    with open(os.path.join(RAW, "compound-draft.tsv"), "w", encoding="utf-8") as f:
        for row in sorted(draft): f.write("\t".join(row) + "\n")
    with open(os.path.join(RAW, "compound-meanings.tsv"), "w", encoding="utf-8") as f:
        f.write("name\tmeaning\tchain\tstatus\n")
        for row in sorted(log): f.write("\t".join(str(c) for c in row) + "\n")
    return dict(stats)

def given_attested(st):
    """folded Latin spellings Wiktionary or Wikidata give as given names of the languages of India"""
    out = set()
    for L in GN_LANGS:
        for gk in ("given names", "male given names", "female given names", "unisex given names"):
            for t in wikt_category(f"{L} {gk}"): out.add(fold(t))
    for L in FROM_LANGS:
        for gk in ("male", "female", "unisex"):
            for t in wikt_category(f"English {gk} given names from {L}"): out.add(fold(t))
    try:
        for q, e in wikidata().items():
            if e["labels"].get("en"): out.add(fold(e["labels"]["en"]))
    except Exception: pass
    return out


def write_review(final):
    births = collections.Counter()
    for line in open(os.path.join(DATA, "names-db.tsv"), encoding="utf-8"):
        q = line.rstrip("\n").split("\t")
        if len(q) >= 4 and q[3].isdigit(): births[fold(q[0])] += int(q[3])
    top = sorted((k for k in final if births[k]), key=lambda k: -births[k])[:300]
    with open(os.path.join(RAW, "review.tsv"), "w", encoding="utf-8") as f:
        f.write("name\tbirths\tmeaning\tsentence\n")
        for k in top:
            r = final[k]; f.write(f"{r[0]}\t{births[k]}\t{r[5]}\t{r[6][:120]}\n")

def sacred_more_corpora():
    return ["Brahmanda Purana", "Markandeya Purana", "Narada Purana", "Vamana Purana", "Padma Purana", "Bhavishya Purana", "Brahmavaivarta Purana"]


def write_more(rows):
    COLS = S.COLS
    seen, out = set(), []
    for r in rows:
        kk = (r["corpus"], r["name"], r["figure_id"])
        if kk in seen: continue
        seen.add(kk); out.append(r)
    out.sort(key=lambda r: (r["corpus"], -float(r["confidence"]), -int(r["occurrences"] or 0), r["name"]))
    with open(MORE, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in out: w.writerow({c: str(r.get(c, "")).replace("\t", " ").replace("\n", " ") for c in COLS})
    print(f"wrote {len(out):,} rows → {MORE}", file=sys.stderr)


# ───────────────────────────────────────────────────────────── second pass: poet-saints, classical authors, Rāmāyaṇa retellings
AUTHORS = os.path.join(DATA, "sacred", "indic-authors.tsv")
# (English Wikipedia title, the name families use, corpus, tradition, subtradition, entity_type, native-label language)
FIGURES = [
    ("Mirabai", "Mira", "Bhakti poet-saints", "Hindu", "Vaishnava", "saint", "hi"),
    ("Surdas", "Surdas", "Bhakti poet-saints", "Hindu", "Vaishnava", "saint", "hi"),
    ("Tulsidas", "Tulsidas", "Bhakti poet-saints", "Hindu", "Vaishnava", "saint", "hi"),
    ("Kabir", "Kabir", "Bhakti poet-saints", "Hindu", "Sant", "saint", "hi"),
    ("Dnyaneshwar", "Dnyaneshwar", "Bhakti poet-saints", "Hindu", "Varkari", "saint", "mr"),
    ("Tukaram", "Tukaram", "Bhakti poet-saints", "Hindu", "Varkari", "saint", "mr"),
    ("Eknath", "Eknath", "Bhakti poet-saints", "Hindu", "Varkari", "saint", "mr"),
    ("Namdev", "Namdev", "Bhakti poet-saints", "Hindu", "Varkari", "saint", "mr"),
    ("Chaitanya Mahaprabhu", "Chaitanya", "Bhakti poet-saints", "Hindu", "Gaudiya Vaishnava", "saint", "bn"),
    ("Ramanuja", "Ramanuja", "Bhakti poet-saints", "Hindu", "Sri Vaishnava", "saint", "ta"),
    ("Madhvacharya", "Madhva", "Bhakti poet-saints", "Hindu", "Dvaita", "saint", "kn"),
    ("Andal", "Andal", "Bhakti poet-saints", "Hindu", "Sri Vaishnava", "saint", "ta"),
    ("Basava", "Basava", "Bhakti poet-saints", "Hindu", "Lingayat", "saint", "kn"),
    ("Akka Mahadevi", "Mahadevi", "Bhakti poet-saints", "Hindu", "Lingayat", "saint", "kn"),
    ("Lal Ded", "Lalleshwari", "Bhakti poet-saints", "Hindu", "Kashmir Shaiva", "saint", "hi"),
    ("Narsinh Mehta", "Narsinh", "Bhakti poet-saints", "Hindu", "Vaishnava", "saint", "gu"),
    ("Guru Nanak", "Nanak", "Bhakti poet-saints", "Sikh", "", "saint", "pa"),
    ("Kanada (philosopher)", "Kanada", "Classical authors", "Hindu", "Vaisheshika", "sage", "hi"),
    ("Akshapada Gautama", "Gautama", "Classical authors", "Hindu", "Nyaya", "sage", "hi"),
    ("Kapila", "Kapila", "Classical authors", "Hindu", "Samkhya", "sage", "hi"),
    ("Patanjali", "Patanjali", "Classical authors", "Hindu", "Yoga", "sage", "hi"),
    ("Jaimini", "Jaimini", "Classical authors", "Hindu", "Mimamsa", "sage", "hi"),
    ("Badarayana", "Badarayana", "Classical authors", "Hindu", "Vedanta", "sage", "hi"),
    ("Pāṇini", "Panini", "Classical authors", "Hindu", "", "sage", "hi"),
    ("Yāska", "Yaska", "Classical authors", "Hindu", "", "sage", "hi"),
    ("Pingala", "Pingala", "Classical authors", "Hindu", "", "human", "hi"),
    ("Charaka", "Charaka", "Classical authors", "Hindu", "", "human", "hi"),
    ("Sushruta", "Sushruta", "Classical authors", "Hindu", "", "human", "hi"),
    ("Vagbhata", "Vagbhata", "Classical authors", "Hindu", "", "human", "hi"),
    ("Aryabhata", "Aryabhata", "Classical authors", "Hindu", "", "human", "hi"),
    ("Brahmagupta", "Brahmagupta", "Classical authors", "Hindu", "", "human", "hi"),
    ("Bhāskara I", "Bhaskara", "Classical authors", "Hindu", "", "human", "hi"),
    ("Bhāskara II", "Bhaskara", "Classical authors", "Hindu", "", "human", "hi"),
    ("Varāhamihira", "Varahamihira", "Classical authors", "Hindu", "", "human", "hi"),
    ("Kalidasa", "Kalidasa", "Classical authors", "Hindu", "", "human", "hi"),
    ("Bharata Muni", "Bharata", "Classical authors", "Hindu", "", "sage", "hi"),
    ("Bhartrhari", "Bhartrihari", "Classical authors", "Hindu", "", "human", "hi"),
    ("Adi Shankara", "Shankara", "Classical authors", "Hindu", "Advaita Vedanta", "saint", "hi"),
]


def figures_rows():
    titles = [t for t, *_ in FIGURES]
    body = get("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "prop": "pageprops", "redirects": 1,
               "titles": "|".join(titles), "format": "json"}), os.path.join(RAW, "authors-pageprops.json"))
    d = json.loads(body).get("query", {})
    to = {r["from"]: r["to"] for r in d.get("normalized", []) + d.get("redirects", [])}
    qid = {p["title"]: p.get("pageprops", {}).get("wikibase_item", "") for p in d.get("pages", {}).values()}
    FIXED = {"Akshapada Gautama": "Q2671506", "Badarayana": "Q4840620"}     # the Wikipedia titles redirect to the texts, not the men
    res = lambda t: FIXED.get(t) or qid.get(t) or qid.get(to.get(t, ""), "") or qid.get(to.get(to.get(t, ""), ""), "")
    qs = sorted({res(t) for t in titles if res(t)})
    url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({"action": "wbgetentities", "ids": "|".join(qs),
          "props": "labels|descriptions|claims", "languages": "en|hi|mr|ta|kn|gu|pa|bn|sa|ks", "format": "json"})
    ents = json.loads(get(url, os.path.join(RAW, "authors-wikidata.json"))).get("entities", {})
    rows, missing = [], []
    for title, name, corpus, trad, sub, etype, lc in FIGURES:
        q = res(title); e = ents.get(q)
        if not e: missing.append(title); continue
        lab = e.get("labels", {}); desc = e.get("descriptions", {}).get("en", {}).get("value", "")
        native = (lab.get(lc) or lab.get("hi") or lab.get("sa") or {}).get("value", "")
        native = re.sub(r"^(आचार्य|संं?त|श्री|ಶ್ರೀ|ஸ்ரீ)\s*|\s*\(.*?\)|\s*(प्रथम|द्वितीय)$", "", native).strip()
        sx = [c["mainsnak"].get("datavalue", {}).get("value", {}).get("id") for c in e.get("claims", {}).get("P21", [])]
        sex = "girl" if "Q6581072" in sx else "boy" if "Q6581097" in sx else ""
        en = lab.get("en", {}).get("value", title)
        rows.append({"name": name, "figure_id": q, "figure": f"{en}, {desc}" if desc else en, "sex": sex, "original": native,
                     "translit": "", "language": {"hi": "Hindi", "mr": "Marathi", "ta": "Tamil", "kn": "Kannada", "gu": "Gujarati",
                     "pa": "Punjabi", "bn": "Bengali"}.get(lc, "Sanskrit"), "tradition": trad, "subtradition": sub, "corpus": corpus,
                     "text": "", "passage": f"Wikidata {q}", "url": f"https://www.wikidata.org/wiki/{q}", "occurrences": "",
                     "entity_type": etype, "name_role": "personal", "status": "association",
                     "relation": f"{name} is the name this {'poet-saint' if corpus.startswith('Bhakti') else 'author'} is known by"
                                 + (f" ({en})" if fold(en) != fold(name) else ""),
                     "source": "Wikidata (CC0); English Wikipedia page title (CC BY-SA) for the item", "confidence": "0.9"})
    with open(AUTHORS, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=S.COLS, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\", lineterminator="\n")
        w.writeheader()
        for r in rows: w.writerow({c: str(r.get(c, "")).replace("\t", " ") for c in S.COLS})
    return rows, missing


KAMBA = ["pmuni0414_01", "pmuni0414_02", "pmuni0422_01", "pmuni0422_02", "pmuni0430", "pmuni0455", "pmuni0478", "pmuni0539",
         "pmuni0541_01", "pmuni0541_02", "pmuni0545_01", "pmuni0545_02", "pmuni0558_01", "pmuni0558_02", "pmuni0561_01", "pmuni0561_02"]
ADHY = [("adhyaatmaRamBal.itx", 1), ("adhyaatmaRamAyo.itx", 2), ("adhyaatmaRamAra.itx", 3), ("adhyaatmaRamkiShkindhA.itx", 4),
        ("adhyaatmaRamsundara.itx", 5), ("adhyaatmaRamyuddha.itx", 6), ("adhyaatmaRamuttara.itx", 7)]


def ramayana_rows():
    """Adhyātma Rāmāyaṇa (sanskritdocuments, through the epic matcher) and Kamba Rāmāyaṇam (Project Madurai): the Vālmīki
    Rāmāyaṇa figures of indic.tsv found again in each retelling, first passage cited"""
    for fn, _ in ADHY:
        get(SD + "doc_raama/" + fn, os.path.join(RAW, "sd", fn), headers={"User-Agent": "Mozilla/5.0 (Macintosh) AppleWebKit/537.36 Chrome/120 Safari/537.36"})
    keep_raw = S.RAW; S.RAW = RAW
    try: verses = S.load_itx(ADHY, "AdhR", "Adhyatma Ramayana", mark_url="doc_raama/")
    finally: S.RAW = keep_raw
    figs = {}
    for r in csv.DictReader(open(os.path.join(DATA, "sacred", "indic.tsv"), encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE):
        if r["corpus"] == "Valmiki Ramayana" and r["entity_type"] not in ("place", "tribe", "concept") and float(r["confidence"] or 0) >= 0.7:
            figs.setdefault((r["translit"], r["figure_id"]), r)
    rows = []
    # Adhyātma: the same stem-class inflections the epic pass uses, for each Vālmīki name
    cand = {S.norm_word(t.lower()): {"lex": "f" if r["sex"] == "girl" else "m", "safe_compound": False, "mw": t, "prio": 1}
            for (t, q), r in figs.items()}
    hits, _ = S.scan(verses, S.Matcher(cand))
    for (t, q), r in figs.items():
        h = hits.get(S.norm_word(t.lower()))
        if not h or not h["free"]: continue
        cite, sec, url, _txt = verses[h["verses"][0]][:4]
        rows.append(dict(r, corpus="Adhyatma Ramayana", text="Adhyatma Ramayana (Brahmanda Purana)", passage=cite, url=url,
                         occurrences=str(h["n"]), status="attested", source="sanskritdocuments.org e-text of the Adhyatma Ramayana; figure from indic.tsv",
                         confidence="0.8"))
    # Kamba: Tamil labels of the same figures (Wikidata), found as words in the Project Madurai e-text
    qs = sorted({q for (t, q) in figs if q.startswith("Q")})
    ta = {}
    for i in range(0, len(qs), 50):
        url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({"action": "wbgetentities", "ids": "|".join(qs[i:i + 50]),
              "props": "labels", "languages": "ta", "format": "json"})
        for q, e in json.loads(get(url, os.path.join(RAW, "tamil", f"wd-ram-ta-{i}.json")) or b"{}").get("entities", {}).items():
            v = e.get("labels", {}).get("ta", {}).get("value", "")
            if v and " " not in v: ta[q] = v
    texts = [(f, pm_text(f)) for f in KAMBA]
    seen_fig = set()
    for (t, q), r in figs.items():
        # a figure's Tamil name attests the figure's own name only, not each Sanskrit epithet of it
        if r["name_role"] != "personal" or q in seen_fig: continue
        lab = ta.get(q)
        if not lab: continue
        stem = re.sub(r"(ன்|ம்|ர்|ள்)$", "", lab)
        if len(stem) < 3: continue
        rx = re.compile(r"(?<![஀-௿])" + re.escape(stem) + r"[஀-௿]{0,4}(?![஀-௿])")
        for f, txt in texts:
            m = rx.search(txt)
            if not m: continue
            before = txt[:m.start()]
            num = re.findall(r"\n\s*(\d{1,5})\s*\n", before[-3000:])
            rows.append(dict(r, original=lab, translit="", language="Tamil", corpus="Kamba Ramayanam", text="Iramavataram (Kambar)",
                             passage=f"Project Madurai {f}" + (f", verse {num[-1]}" if num else ""), url=PM + f + ".html",
                             occurrences=str(len(rx.findall(txt))), status="attested",
                             relation=(r["relation"] + "; " if r["relation"] else "") + f"Tamil form {lab} (Wikidata label)",
                             source="Project Madurai e-text of the Kamba Ramayanam; Tamil form from Wikidata (CC0); figure from indic.tsv",
                             confidence="0.7"))
            seen_fig.add(q)
            break
    return rows


def second_pass():
    authors, missing = figures_rows()
    ram = ramayana_rows()
    old = [r for r in csv.DictReader(open(MORE, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE)
           if r["corpus"] not in ("Adhyatma Ramayana", "Kamba Ramayanam")]
    write_more(old + ram)
    rep = {"authors and poet-saints (indic-authors.tsv)": dict(collections.Counter(r["corpus"] for r in authors)),
           "not found on Wikidata": missing, "Ramayana retellings (indic-more.tsv)": dict(collections.Counter(r["corpus"] for r in ram)),
           "indic-more.tsv by corpus": dict(collections.Counter(r["corpus"] for r in csv.DictReader(open(MORE, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE)))}
    json.dump(rep, open(os.path.join(RAW, "second-pass.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(rep, ensure_ascii=False, indent=1), file=sys.stderr)

if __name__ == "__main__":
    if "--second-pass" in sys.argv:                 # poet-saints, classical authors, Rāmāyaṇa retellings
        second_pass()
    elif "--review-only" in sys.argv:                 # re-apply the hand review to the cached rows (seconds, not minutes)
        c = json.load(open(os.path.join(RAW, "prereview.json"), encoding="utf-8"))
        finish(c["final"], c["report"])
    else:
        assemble()
