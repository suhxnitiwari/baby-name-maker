# Builds data/scripture-names.json: every person named in the Bible (with the Torah marked), in the Hindu
# epics, Puranas, Vedas and Bhagavad Gita, and in the Quran. Each entry: name, gender, origin, language,
# faiths, meaning, story, texts. Sources (downloaded to raw/ by fetch_world.py) are listed in docs/name-sources.md.
#
#   python3 scripts/build_scriptures.py
import collections, json, os, re, sys, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); RAW = os.path.join(ROOT, "raw")
OUT = os.path.join(ROOT, "data", "scripture-names.json")

# ─────────────────────────────────────────────────────────────
# THE BIBLE: STEPBible TIPNR (every person, CC BY) + Hitchcock's Bible Names Dictionary (meanings, public domain)
# ─────────────────────────────────────────────────────────────
BOOKS = dict(x.split(":") for x in (
    "Gen:Genesis Exo:Exodus Lev:Leviticus Num:Numbers Deu:Deuteronomy Jos:Joshua Jdg:Judges Rut:Ruth 1Sa:1 Samuel 2Sa:2 Samuel "
    "1Ki:1 Kings 2Ki:2 Kings 1Ch:1 Chronicles 2Ch:2 Chronicles Ezr:Ezra Neh:Nehemiah Est:Esther Job:Job Psa:Psalms Pro:Proverbs "
    "Ecc:Ecclesiastes Sng:Song of Songs Isa:Isaiah Jer:Jeremiah Lam:Lamentations Ezk:Ezekiel Dan:Daniel Hos:Hosea Jol:Joel Amo:Amos "
    "Oba:Obadiah Jon:Jonah Mic:Micah Nam:Nahum Hab:Habakkuk Zep:Zephaniah Hag:Haggai Zec:Zechariah Mal:Malachi "
    "Mat:Matthew Mrk:Mark Luk:Luke Jhn:John Act:Acts Rom:Romans 1Co:1 Corinthians 2Co:2 Corinthians Gal:Galatians Eph:Ephesians "
    "Php:Philippians Col:Colossians 1Th:1 Thessalonians 2Th:2 Thessalonians 1Ti:1 Timothy 2Ti:2 Timothy Tit:Titus Phm:Philemon "
    "Heb:Hebrews Jas:James 1Pe:1 Peter 2Pe:2 Peter 1Jn:1 John 2Jn:2 John 3Jn:3 John Jud:Jude Rev:Revelation").replace("1 ", "1_").replace("2 ", "2_").replace("3 ", "3_").replace("Song of Songs", "Song_of_Songs").split())
BOOKS = {k: v.replace("_", " ") for k, v in BOOKS.items()}
ORDER = list(BOOKS)
TORAH = set(ORDER[:5]); NT = set(ORDER[ORDER.index("Mat"):])

def hitchcock():
    out = {}
    lines = open(os.path.join(RAW, "hitchcock.txt"), encoding="utf-8").read().split("\n")
    for i, l in enumerate(lines[:-1]):
        m = re.fullmatch(r"   ([A-Z][A-Za-z'\-]+)", l.rstrip())
        nxt = lines[i + 1].strip()
        if m and lines[i + 1].startswith("          ") and nxt:
            out.setdefault(m.group(1).lower(), nxt.rstrip(".;"))   # the first meaning listed is the person's (later ones are often places)
    return out

def bible():
    txt = open(os.path.join(RAW, "tipnr.txt"), encoding="utf-8").read()
    people = collections.defaultdict(list)          # name → [person]
    for b in txt.split("$========== ")[1:]:
        if not b.startswith("PERSON"): continue
        lines = b.split("\n")
        head = lines[1].split("\t")
        if len(head) < 9: continue
        sex = head[8].strip()
        if sex not in ("Male", "Female"): continue
        name = head[0].split("@")[0].strip()
        refs, script, spell = [], "", set()
        for l in lines:
            if l.startswith("– ") and not l.startswith("– Total"):
                c = l.split("\t")
                if len(c) > 4:
                    refs += re.findall(r"\b([123]?[A-Z][a-z]{1,2})\.\d", c[4])
                    script = script or (c[2].split("=")[-1] if "=" in c[2] else "")
                    spell.update(s.strip() for s in re.split(r"[,;/]", c[3]) if re.fullmatch(r"[A-Z][a-z'\-]+", s.strip()))
            if l.startswith("– Total"):
                c = l.rstrip().split("\t")
                total = int(c[-1]) if c[-1].strip().isdigit() else len(refs)
        brief = (re.search(r"@Brief= (.*)", b) or [None, ""])[1].strip()
        greek = re.search(r"[Ͱ-Ͽ]", script) is not None
        p = {"sex": sex, "books": [x for x in dict.fromkeys(refs) if x in BOOKS], "most": collections.Counter(x for x in refs if x in BOOKS).most_common(1)[0][0] if any(x in BOOKS for x in refs) else "", "brief": brief, "total": total if refs else 0, "greek": greek, "script": script}
        # only the person's own name: translations sometimes reuse a name for someone else (KJV "Lydia" for Lud)
        if re.fullmatch(r"[A-Z][a-z'\-]+", name): people[name].append(p)
    mean = hitchcock()
    out = []
    for n, ps in people.items():
        # weigh each person by how often they're mentioned: Noah the patriarch outweighs Noah, daughter of Zelophehad
        f = sum(p["total"] + 1 for p in ps if p["sex"] == "Female"); m = sum(p["total"] + 1 for p in ps if p["sex"] == "Male")
        g = "girl" if f >= 3 * m else "boy" if m >= 3 * f else "either"
        books = {b for p in ps for b in p["books"]}
        if not books: continue
        top = max(ps, key=lambda p: p["total"])
        first = min((b for b in books), key=ORDER.index)
        texts = ["Bible"] + (["Torah"] if books & TORAH else []) + (["Hebrew Bible"] if books - NT else []) + (["New Testament"] if books & NT else [])
        faiths = ["Christian", "Jewish"] if books - NT else ["Christian"]
        greek = all(p["greek"] for p in ps)
        story = (top["brief"] or f"Named in {BOOKS[first]}").rstrip(". ")
        where = BOOKS[top["most"] or first]
        many = f" One of {len(ps)} people with this name in the Bible." if len(ps) > 1 else ""
        out.append({"n": n, "g": g, "o": "Greek" if greek else "Hebrew", "l": "Greek" if greek else "Hebrew", "r": faiths,
                    "m": mean.get(n.lower(), ""), "src": f"{story} ({where}).{many}", "x": texts, "h": top["script"]})
    return out

# ─────────────────────────────────────────────────────────────
# HINDU TEXTS: Cologne Digital Sanskrit Dictionaries (CC BY-NC-SA 3.0)
#   inm Sørensen, Index to the Names in the Mahābhārata (incl. the Bhagavad Gita) · pui Dikshitar, Purāṇa Index
#   pe Vettam Mani, Purāṇic Encyclopaedia · vei Macdonell & Keith, Vedic Index · mci Mehendale, Mahābhārata Cultural Index
# ─────────────────────────────────────────────────────────────
SLP = {"A": "ā", "I": "ī", "U": "ū", "f": "ṛ", "F": "ṝ", "x": "ḷ", "X": "ḹ", "E": "ai", "O": "au", "M": "ṃ", "H": "ḥ", "K": "kh", "G": "gh", "N": "ṅ",
       "C": "ch", "J": "jh", "Y": "ñ", "w": "ṭ", "W": "ṭh", "q": "ḍ", "Q": "ḍh", "R": "ṇ", "T": "th", "D": "dh", "P": "ph", "B": "bh", "S": "ś", "z": "ṣ"}
def iast(s): return "".join(SLP.get(c, c) for c in re.sub(r"[~/\\^0-9]", "", s))
def everyday(s):
    # scholarly → everyday spelling: Kṛṣṇa → Krishna, Śiva → Shiva, Lakṣmī → Lakshmi
    for a, b in (("kṣ", "ksh"), ("jñ", "gy"), ("ṛ", "ri"), ("ṝ", "ri"), ("ḷ", "li"), ("ś", "sh"), ("ṣ", "sh"), ("ā", "a"), ("ī", "i"), ("ū", "u"),
                 ("ṃ", "n"), ("ḥ", ""), ("ṅ", "n"), ("ñ", "n"), ("ṭ", "t"), ("ḍ", "d"), ("ṇ", "n")):
        s = s.replace(a, b)
    return s[:1].upper() + s[1:]

def readable(t):
    # scholarly spelling in stories → everyday: Śrī Rāma → Shri Rama, Pāṇḍavas → Pandavas
    for a, b in (("Kṣ", "Ksh"), ("kṣ", "ksh"), ("Ś", "Sh"), ("ś", "sh"), ("Ṣ", "Sh"), ("ṣ", "sh"), ("Ṛ", "Ri"), ("ṛ", "ri"), ("Ā", "A"), ("ā", "a"),
                 ("Ī", "I"), ("ī", "i"), ("Ū", "U"), ("ū", "u"), ("Ṭ", "T"), ("ṭ", "t"), ("Ḍ", "D"), ("ḍ", "d"), ("Ṇ", "N"), ("ṇ", "n"),
                 ("ṃ", "m"), ("ḥ", "h"), ("ṅ", "n"), ("ñ", "n"), ("Ṅ", "N")):
        t = t.replace(a, b)
    return t

def plain(s):
    # any romanization → bare letters, for matching (dhṛitarāśhtraḥ, Dhṛtarāṣṭra → dhritarashtra)
    s = unicodedata.normalize("NFC", s.lower())
    for a, b in (("ṛi", "ri"), ("ṛ", "ri"), ("śh", "sh"), ("ṣh", "sh"), ("ś", "sh"), ("ṣ", "sh"), ("kṣh", "ksh")):
        s = s.replace(a, b)
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z]", "", s)

def strip_markup(t):
    t = re.sub(r"<F>.*?</F>|<sup>.*?</sup>|\[Page[^\]]*\]|<[^>]+>", " ", t, flags=re.S)
    t = re.sub(r"\{[@%#]|[@%#]\}", "", t)
    return re.sub(r"\s+", " ", t.replace("-\n", "").replace("\n", " ")).strip()

PERSON = re.compile(r"\b(king|queen|son|sons|daughter|wife|husband|mother|father|brother|sister|sage|seer|ṛṣi|rishi|hermit|muni|god|goddess|deity|devī|"
                    r"demon|asura|dānava|daitya|rākṣasa|rākṣasī|apsaras|apsarā|gandharva|prince|princess|warrior|hero|teacher|disciple|priest|brahmin|"
                    r"brāhmaṇa|minister|charioteer|nāga|serpent|yakṣa|incarnation|avatār|epithet|a man|a woman|name of a (man|woman|king|sage|teacher|priest|seer|poet)|"
                    r"maharṣi|devarṣi|rājarṣi|monkey|vānara|attendant|grandson|granddaughter|descendant|chief|emperor|ruler|consort|maiden|nymph|"
                    r"author|poet|ascetic|yogi|archer|commander|the name of a|the patronymic)\b", re.I)
NOT = re.compile(r"^(a |an |the )?(river|mountain|mount|hill|country|kingdom|city|town|forest|lake|tīrtha|tirtha|place|region|sacred (spot|place|rite)|rite|"
                 r"ritual|sacrifice|yajña|metre|meter|disease|people|tribe|clan|weapon|plant|tree|hymn|verse|chapter|book|story|history|hell|heaven|"
                 r"world|loka|festival|vow|month|star|constellation|ocean|island|cave|province|janapada|well|pond|grove|ornament|missile|astra)\b", re.I)
FEMALE = re.compile(r"\b(daughter|wife|queen|mother|sister|goddess|devī|apsaras|apsarā|woman|princess|she|her|consort|maiden|nymph|rākṣasī|mātṛ|f\.)", re.I)
MALE = re.compile(r"\b(son|king|father|husband|brother|sage|man|he|his|him|prince|god|demon|teacher|ṛṣi|muni|m\.)\b", re.I)
SOURCE_TEXT = {"inm": "Mahabharata", "mci": "Mahabharata", "pui": "Puranas", "vei": "Vedas", "pe": None}
PLACE = re.compile(r"\b(river|mountain|kingdom|country|city|town|forest|lake|tīrtha|holy bath|bathing place|region|sacred place|rite|ritual|metre|disease|tree|plant|weapon|hell|month|ocean|island|cave|province|festival|vow|a people|place of pilgrimage|hymn)\b", re.I)
HEADER = re.compile(r"^(\d+\)|General|Main details|Other details|Genealogy|Birth)", re.I)
THING = re.compile(r"^(denotes|is the designation|evil spirits|the sun's|a class of|a group of|a dish|a kind of|a sort of|the term|the word)\b|\b(constellations?|nakṣatras?|nakshatras?|asterisms?|chariots?|doctrines?|dish|kalpa|manvantara|yuga)\b", re.I)
VEDIC_PERSON = re.compile(r"\b(name of a (man|woman|king|prince|teacher|priest|seer|sage|poet|chief|singer|ṛṣi|rishi|warrior|patron|demon)|patronymic|metronymic|"
                          r"a (man|woman|king|teacher|priest|seer|sage|poet|chief|demon)\b|the (wife|son|daughter) of)", re.I)
RANK = {"pe": 0, "mci": 1, "inm": 2, "pui": 3, "vei": 4}

def gita_names():
    out = {}
    for v in json.load(open(os.path.join(RAW, "gita-verse.json"), encoding="utf-8")):
        for pair in v.get("word_meanings", "").split(";"):
            if "—" not in pair: continue
            skt, gloss = [x.strip() for x in pair.split("—", 1)]
            names = re.findall(r"\b(?:Shree )?[A-Z][a-z]+(?: [A-Z][a-z]+)?", gloss)
            names = [n for n in names if n.split()[-1] not in ("O", "The", "Supreme", "Lord", "God", "Personality", "Vedas", "I", "Me", "My", "Brahman", "Brahma")]
            if names: out.setdefault(plain(skt.split(" ")[0]), gloss.strip(" ."))
    return out

def hindu():
    gita = gita_names()
    best = {}
    for d in ("pe", "mci", "inm", "pui", "vei"):
        txt = open(os.path.join(RAW, f"skt-{d}.txt"), encoding="utf-8").read()
        for m in re.finditer(r"<L>[^\n]*?<k1>([^<\n]+)[^\n]*\n(.*?)<LEND>", txt, re.S):
            k1, body = m.group(1), m.group(2)
            if len(k1) < 3 or not re.fullmatch(r"[a-zA-Z]+", k1): continue
            text = strip_markup(body)
            desc = text.split("¦", 1)[-1].strip(" .:—-")
            desc = re.sub(r"^(\([^)]{1,40}\)[.,]?\s*)+", "", desc)          # leading aliases and tags: "(PṚTHĀ).", "(M)."
            desc = re.sub(r"^(m|f|n)\.\s*:\s*", lambda g: g.group(0), desc)
            sex_tag = re.match(r"^(m|f)\.\s*:", desc)
            desc = re.sub(r"^(m|f|n)\.\s*:\s*", "", desc)
            first = re.split(r"(?<=[a-z\)])\. ", desc, 1)[0].strip(" .:;—-")
            if first.startswith("= "): first = "Another name for " + first[2:].split(":")[0].split(",")[0].strip()
            first = re.split(r" \[|\s§", first)[0].strip(" .;,")                  # drop bracketed references
            weak = False
            raw = len(body)
            if HEADER.match(first) or first.lower() in ("main details", "general information", "other details", "general"):
                rest = re.split(r"(?<=[a-z\)])\. ", desc, 2)
                first = next((x for x in rest[1:] if not HEADER.match(x)), "").strip(" .:;—-")
                body = body[:len(body) // 50]          # a weaker description: let another book's entry for this person win
                weak = True
            if not first or NOT.match(first) or PLACE.search(first) or THING.search(first): continue
            if d == "vei" and not VEDIC_PERSON.search(first): continue
            # the Puranic Encyclopedia is mostly people: keep anything that isn't clearly a place or thing
            if not (PERSON.search(first) or first.startswith("Another name for") or (d == "pe" and len(body) > 300)): continue
            if re.search(r"\b(adj|n\.)\b", first[:12]): continue
            name = everyday(iast(k1))
            if not re.fullmatch(r"[A-Z][a-z]+", name) or len(name) < 3: continue
            fm, mm = FEMALE.search(first), MALE.search(first)
            if sex_tag: g = "girl" if sex_tag.group(1) == "f" else "boy"
            elif fm and (not mm or fm.start() < mm.start()): g = "girl"
            elif mm: g = "boy"
            else: g = "girl" if iast(k1)[-1] in "āī" else "boy"
            meaning = ""
            q = re.match(r"\(?[“‘]([^”’]{3,60})[”’]", desc)                # a gloss right after the name: (“belonging to Indra”)
            if q: meaning = q.group(1).strip()
            texts = {SOURCE_TEXT[d]} if SOURCE_TEXT[d] else set()
            if d == "pe":
                texts |= {"Ramayana"} if re.search(r"Rāmāyaṇa|Ramayana", text) else set()
                texts |= {"Mahabharata"} if re.search(r"M\.B\.|Mahābhārata", text) else set()
                texts |= {"Puranas"} if re.search(r"Purāṇa", text) else set()
            story = readable(first[:1].upper() + first[1:])
            story = story if len(story) <= 150 else story[:147].rsplit(" ", 1)[0] + "…"
            key = name.lower()
            cur = best.get(key)
            entry = {"n": name, "g": g, "o": "Indian", "l": "Sanskrit", "r": ["Hindu"], "m": meaning, "src": story, "x": sorted(texts), "h": iast(k1), "_size": len(body) + 1, "_weak": weak, "_raw": raw, "_maxraw": raw}
            if not cur: best[key] = entry
            else:
                # many people share a name: the one with the longest entry is the famous one (Kṛṣṇa, not Kṛṣṇā; Sītā, not the warrior Sita)
                texts_all = sorted(set(cur["x"]) | texts)
                mx = max(cur["_maxraw"], raw)
                if len(body) > cur["_size"]: best[key] = {**entry, "x": texts_all, "_maxraw": mx}
                else: cur["x"] = texts_all; cur["_maxraw"] = mx
    # the Bhagavad Gita: every name it mentions (it's part of the Mahabharata, so Sørensen's index has them all)
    for key, x in best.items():
        p = plain(x["h"])
        hit = next((gl for w, gl in gita.items() if len(p) >= 4 and w.startswith(p) and len(w) - len(p) <= 3), None)
        if hit:
            x["x"] = sorted(set(x["x"]) | {"Bhagavad Gita"})
            if not x["m"] and "," in hit: x["m"] = hit.split(",", 1)[1].strip()
    # a weak description ("1) Birth. …"): borrow the story from the same person's stem form (Ashvatthama ↔ Ashvatthaman)
    for k, x in best.items():
        alt = best.get(k + "n") or (best.get(k[:-1]) if k.endswith("n") else None)
        famous_was_weak = x["_weak"] or x["_raw"] * 3 < x["_maxraw"]     # the big entry for this name had no usable first line
        if famous_was_weak and alt and not alt["_weak"]: x["src"] = alt["src"]; x["g"] = alt["g"]
    # "Another name for Shiva": an alias takes the gender of who it names
    for x in best.values():
        m = re.match(r"Another name for (?:Shri |Sri )?([A-Z][a-z]+)", x["src"])
        if m and m.group(1).lower() in best: x["g"] = best[m.group(1).lower()]["g"]
    # Sanskrit stems → the form people say: Hanumat → Hanuman, Bhagavat → Bhagavan
    for k, x in list(best.items()):
        if re.search(r"[mv]at$", k) and k[:-1] + "n" not in best:
            best[k[:-1] + "n"] = {**x, "n": x["n"][:-1] + "n"}
    out = []
    for x in best.values():
        for k_ in ("_size", "_weak", "_raw", "_maxraw"): x.pop(k_)
        if not x["x"]: x["x"] = ["Puranas"]
        out.append(x)
    return out

# ─────────────────────────────────────────────────────────────
# THE QURAN: Quranic Arabic Corpus (Kais Dukes, GPL; text by Tanzil) for where and how often each name appears
# Every person named in the Quran, plus places and words of the Quran that are given as names.
# ─────────────────────────────────────────────────────────────
SURAHS = ("Al-Fatiha Al-Baqarah Aal-Imran An-Nisa Al-Ma'idah Al-An'am Al-A'raf Al-Anfal At-Tawbah Yunus Hud Yusuf Ar-Ra'd Ibrahim Al-Hijr An-Nahl "
          "Al-Isra Al-Kahf Maryam Ta-Ha Al-Anbiya Al-Hajj Al-Mu'minun An-Nur Al-Furqan Ash-Shu'ara An-Naml Al-Qasas Al-Ankabut Ar-Rum Luqman As-Sajdah "
          "Al-Ahzab Saba Fatir Ya-Sin As-Saffat Sad Az-Zumar Ghafir Fussilat Ash-Shura Az-Zukhruf Ad-Dukhan Al-Jathiyah Al-Ahqaf Muhammad Al-Fath "
          "Al-Hujurat Qaf Adh-Dhariyat At-Tur An-Najm Al-Qamar Ar-Rahman Al-Waqi'ah Al-Hadid Al-Mujadilah Al-Hashr Al-Mumtahanah As-Saff Al-Jumu'ah "
          "Al-Munafiqun At-Taghabun At-Talaq At-Tahrim Al-Mulk Al-Qalam Al-Haqqah Al-Ma'arij Nuh Al-Jinn Al-Muzzammil Al-Muddaththir Al-Qiyamah "
          "Al-Insan Al-Mursalat An-Naba An-Nazi'at Abasa At-Takwir Al-Infitar Al-Mutaffifin Al-Inshiqaq Al-Buruj At-Tariq Al-A'la Al-Ghashiyah Al-Fajr "
          "Al-Balad Ash-Shams Al-Layl Ad-Duha Ash-Sharh At-Tin Al-Alaq Al-Qadr Al-Bayyinah Az-Zalzalah Al-Adiyat Al-Qari'ah At-Takathur Al-Asr "
          "Al-Humazah Al-Fil Quraysh Al-Ma'un Al-Kawthar Al-Kafirun An-Nasr Al-Masad Al-Ikhlas Al-Falaq An-Nas").split()

# lemma in the corpus → name, gender, story
QURAN_PEOPLE = [
    ("muwsaY`", "Musa", "boy", "Moses: the prophet who led the Children of Israel out of Egypt"),
    ("<iboraAhiym", "Ibrahim", "boy", "Abraham: prophet and Friend of God (Khalil Allah)"),
    ("nuwH", "Nuh", "boy", "Noah: the prophet who built the Ark"),
    ("maroyam", "Maryam", "girl", "Mary, mother of Isa: the only woman named in the Quran, with a surah named after her"),
    ("yuwsuf", "Yusuf", "boy", "Joseph: the prophet whose story fills Surah Yusuf"),
    ("luwT", "Lut", "boy", "Lot: the prophet sent to the people of Sodom"),
    ("A^dam", "Adam", "boy", "The first human and the first prophet"),
    ("EiysaY", "Isa", "boy", "Jesus, son of Maryam: a prophet and the Messiah"),
    ("ha`ruwn", "Harun", "boy", "Aaron: prophet and brother of Musa"),
    ("sulayoma`n", "Sulayman", "boy", "Solomon: prophet-king who understood the speech of birds and ants"),
    ("<isoHaAq", "Ishaq", "boy", "Isaac: prophet, son of Ibrahim"),
    ("yaEoquwb", "Yaqub", "boy", "Jacob: prophet, son of Ishaq, also called Israel"),
    ("daAwud", "Dawud", "boy", "David: prophet-king who received the Zabur (Psalms)"),
    ("<isomaAEiyl", "Ismail", "boy", "Ishmael: prophet, son of Ibrahim, who helped raise the Kaaba"),
    ("$uEayob", "Shuayb", "boy", "The prophet sent to the people of Madyan"),
    ("Sa`liH2", "Salih", "boy", "The prophet sent to the people of Thamud"),
    ("zakariy~aA", "Zakariya", "boy", "Zechariah: prophet, guardian of Maryam and father of Yahya"),
    ("huwd", "Hud", "boy", "The prophet sent to the people of 'Ad; a surah is named after him"),
    ("yaHoyaY`", "Yahya", "boy", "John the Baptist: prophet, son of Zakariya"),
    ("muHam~ad", "Muhammad", "boy", "The Prophet of Islam"),
    (">aHomad", "Ahmad", "boy", "A name of the Prophet Muhammad, foretold by Isa"),
    (">ay~uwb", "Ayyub", "boy", "Job: the prophet known for his patience"),
    ("yuwnus", "Yunus", "boy", "Jonah: the prophet swallowed by the whale"),
    ("<iloyaAs", "Ilyas", "boy", "Elijah: a prophet"),
    ("{loyasaEa", "Alyasa", "boy", "Elisha: a prophet"),
    ("<idoriys", "Idris", "boy", "A prophet raised to a high station, often identified with Enoch"),
    ("luqoma`n", "Luqman", "boy", "Luqman the Wise, whose advice to his son fills the surah named after him"),
    ("Eimora`n", "Imran", "boy", "Father of Maryam; Surah Aal-Imran is named after his family"),
    ("Euzayor", "Uzayr", "boy", "Ezra"),
    ("zayod", "Zayd", "boy", "Zayd ibn Haritha: the only companion of the Prophet named in the Quran"),
    ("TaAluwt", "Talut", "boy", "Saul: king of the Children of Israel"),
    ("jaAluwt", "Jalut", "boy", "Goliath, defeated by Dawud"),
    ("jiboriyl", "Jibril", "boy", "Gabriel: the angel who brought the revelation"),
    ("miykaY`l", "Mikail", "boy", "Michael: an archangel"),
    ("ha`ruwt", "Harut", "boy", "One of two angels sent to Babylon"),
    ("ma`ruwt", "Marut", "boy", "One of two angels sent to Babylon"),
    ("ma`lik2", "Malik", "boy", "The angel who keeps the gates of Hell; as a word, 'king'"),
    ("A^zar", "Azar", "boy", "The father of Ibrahim"),
    ("qa`ruwn", "Qarun", "boy", "Korah: a man of great wealth among Musa's people"),
    ("ha`ma`n", "Haman", "boy", "The minister of Pharaoh"),
    ("tub~aE", "Tubba", "boy", "A king of Yemen whose people are named in the Quran"),
]
QURAN_PLACES = [
    ("S~afaA", "Safa", "girl", "Safa: a hill in Mecca, part of the pilgrimage"),
    ("marowap", "Marwa", "girl", "Marwa: a hill in Mecca, part of the pilgrimage"),
    ("saba<", "Saba", "girl", "The kingdom of Sheba; a surah is named after it"),
    ("ramaDaAn", "Ramadan", "boy", "The month in which the Quran was revealed"),
    ("Earafa`t", "Arafat", "boy", "The plain of Arafat, part of the pilgrimage"),
    ("bador", "Badr", "boy", "The Battle of Badr; as a word, 'full moon'"),
    ("Hunayon", "Hunayn", "boy", "The Battle of Hunayn"),
    ("madiynap", "Madina", "girl", "The city: Medina"),
    ("firodawos", "Firdaus", "either", "Firdaus: the highest garden of Paradise"),
    ("jan~ap", "Jannah", "girl", "Paradise: the Garden"),
]
QURAN_WORDS = [  # words of the Quran that are given as names
    ("nuwr", "Noor", "either", "light"), ("nuwr", "Nur", "either", "light"), ("hudFY", "Huda", "girl", "guidance"), ("raHomap", "Rahma", "girl", "mercy"),
    ("<iyma`n", "Iman", "either", "faith"), ("sakiynap", "Sakina", "girl", "tranquility, calm"), ("kawovar", "Kawthar", "either", "abundance; a river of Paradise"),
    ("salosabiyl", "Salsabil", "girl", "a spring of Paradise"), ("tasoniym", "Tasnim", "girl", "a spring of Paradise"), ("bu$oraY`", "Bushra", "girl", "good news"),
    (">amal", "Amal", "girl", "hope"), ("malak", "Malak", "girl", "angel"), ("yaqiyn", "Yaqin", "boy", "certainty"), ("taqowaY", "Taqwa", "girl", "God-consciousness"),
    ("naSor", "Nasr", "boy", "victory, help"), ("<iHosa`n", "Ihsan", "either", "excellence, doing good"), ("Sabor", "Sabr", "boy", "patience"),
    ("$ifaA^'", "Shifa", "girl", "healing"), ("riDowa`n", "Ridwan", "boy", "contentment; God's good pleasure"), ("sala`m", "Salam", "either", "peace"),
    ("kariym", "Karim", "boy", "generous, noble"), ("fatoH", "Fath", "boy", "victory, opening"), ("zahorap", "Zahra", "girl", "blossom, splendor"),
    ("Hikomap", "Hikma", "girl", "wisdom"), ("qamar", "Qamar", "either", "moon"), ("$amos", "Shams", "either", "sun"), ("furoqaAn", "Furqan", "boy", "the criterion between right and wrong"),
    ("DiyaA^'", "Diya", "either", "radiance"), ("HusonaY`", "Husna", "girl", "the best, the most beautiful"), ("Haniyf", "Hanif", "boy", "upright, true in faith"),
    ("rafiyq", "Rafiq", "boy", "companion"), ("naEiym", "Naim", "boy", "bliss"), (">amiyn", "Amin", "boy", "trustworthy"), ("Eaziyz", "Aziz", "boy", "mighty, dear"),
    ("Hakiym", "Hakim", "boy", "wise"), ("baSiyrap", "Basira", "girl", "insight"), ("jamiyl", "Jamil", "boy", "beautiful"), ("kawokab", "Kawkab", "girl", "star"),
]

def quran():
    count, first = collections.Counter(), {}
    for l in open(os.path.join(RAW, "quran-morph.txt"), encoding="utf-8"):
        if not l.startswith("("): continue
        loc, _, _, feats = l.rstrip("\n").split("\t")
        m = re.search(r"LEM:([^|]+)", feats)
        if m: count[m.group(1)] += 1; first.setdefault(m.group(1), loc)
    def where(lem):
        su, ay = first[lem].strip("()").split(":")[:2]
        n = count[lem]
        return f"Named {'once' if n == 1 else f'{n} times'} in the Quran" + ("" if n == 1 else ", first") + f" in Surah {SURAHS[int(su) - 1]} ({su}:{ay})"
    out = []
    for lem, name, g, story in QURAN_PEOPLE + QURAN_PLACES:
        if lem not in count: print("  ! not in corpus:", lem); continue
        out.append({"n": name, "g": g, "o": "Arab", "l": "Arabic", "r": ["Islamic"], "m": "", "src": f"{story}. {where(lem)}.", "x": ["Quran"]})
    for lem, name, g, meaning in QURAN_WORDS:
        if lem not in count: print("  ! not in corpus:", lem); continue
        n = count[lem]; su, ay = first[lem].strip("()").split(":")[:2]
        out.append({"n": name, "g": g, "o": "Arab", "l": "Arabic", "r": ["Islamic"], "m": meaning,
                    "src": f"A word of the Quran, used {'once' if n == 1 else f'{n} times'}" + ("" if n == 1 else ", first") + f" in Surah {SURAHS[int(su) - 1]} ({su}:{ay}).", "x": ["Quran"]})
    return out

def merge(*sets):
    # the same spelling in two traditions (Adam in the Bible and the Quran) becomes one name with both stories
    out = {}
    for st in sets:
        for x in st:
            k = x["n"].lower()
            if k not in out: out[k] = dict(x); continue
            y = out[k]
            y["r"] = sorted(set(y["r"]) | set(x["r"])); y["x"] = list(dict.fromkeys(y["x"] + x["x"]))
            y["m"] = y["m"] or x["m"]
            if x["src"] not in y["src"]: y["src"] = f"{y['src']} {'In the Quran: ' if x['x'] == ['Quran'] else ''}{x['src']}"
            if y["g"] != x["g"]: y["g"] = "either"
    return sorted(out.values(), key=lambda x: x["n"])

if __name__ == "__main__":
    b, h, q = bible(), hindu(), quran()
    print(f"Bible {len(b):,} ({sum('Torah' in x['x'] for x in b):,} in the Torah) · Hindu texts {len(h):,} · Quran {len(q):,}")
    allx = merge(b, h, q)
    # compact: [name, g, origin, language, faiths, meaning, story, texts]
    G = {"girl": "g", "boy": "b", "either": "e"}
    rows = [[x["n"], G[x["g"]], x["o"], x["l"], ",".join(x["r"]), x["m"], x["src"], ",".join(x["x"])] for x in allx]
    json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(rows):,} names → {OUT} ({os.path.getsize(OUT) // 1024} KB)")
    print(collections.Counter(t for r in rows for t in r[7].split(",")))
