# Sorts names into their cultures → data/culture-names.json
#
#   Wiktionary (CC BY-SA 4.0): every "<language> male/female/unisex given names" entry, downloaded by
#     fetch_wiktionary_names.py, with its meaning when the entry gives one (meaning=, lit=, a gloss, or the word it is).
#   Wikidata (CC0): given names tagged with their language (raw/wd-given-langs.json).
#
# Names in other scripts get their usual Latin spelling: the romanization Wiktionary records (tr=), or the official
# system for Cyrillic, Greek, Armenian and Georgian, or (for the Indian scripts) every likely reading, keeping the one
# already registered somewhere (data/names-db.tsv). Names that can't be romanized reliably are left out.
#
#   python3 scripts/build_cultures.py
import collections, glob, json, os, re, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); RAW = os.path.join(ROOT, "raw")
OUT = os.path.join(ROOT, "data", "culture-names.json")
LATIN = re.compile(r"^[A-Za-zÀ-ɏḀ-ỿ'’ -]+$")

# Wiktionary language → (culture shown in "with ⟨…⟩ roots", language, broader baskets it also belongs to)
AFR, SA, SL, FIL, CA, PAC = ["African"], ["South Asian"], ["Slavic"], ["Filipino"], ["Central Asian"], ["Pacific"]
LANG = {
    "Yoruba": ("Yoruba", "Yoruba", AFR), "Igbo": ("Igbo", "Igbo", AFR), "Hausa": ("Hausa", "Hausa", AFR), "Swahili": ("Swahili", "Swahili", AFR),
    "Zulu": ("Zulu", "Zulu", AFR), "Xhosa": ("Xhosa", "Xhosa", AFR), "Sotho": ("Sotho", "Sotho", AFR), "Tswana": ("Tswana", "Tswana", AFR),
    "Amharic": ("Ethiopian", "Amharic", AFR), "Tigrinya": ("Eritrean", "Tigrinya", AFR), "Oromo": ("Oromo", "Oromo", AFR), "Somali": ("Somali", "Somali", AFR),
    "Akan": ("Akan", "Akan", AFR), "Twi": ("Akan", "Twi", AFR), "Ewe": ("Ewe", "Ewe", AFR), "Shona": ("Shona", "Shona", AFR), "Chichewa": ("Chewa", "Chichewa", AFR),
    "Malagasy": ("Malagasy", "Malagasy", AFR), "Kikuyu": ("Kikuyu", "Kikuyu", AFR), "Afrikaans": ("Afrikaner", "Afrikaans", []), "Efik": ("Efik", "Efik", AFR),
    "Ibibio": ("Ibibio", "Ibibio", AFR), "Fon": ("Fon", "Fon", AFR), "Dagbanli": ("Dagomba", "Dagbani", AFR), "Farefare": ("Frafra", "Farefare", AFR), "Tiv": ("Tiv", "Tiv", AFR),
    "Isoko": ("Isoko", "Isoko", AFR), "Idoma": ("Idoma", "Idoma", AFR), "Kinyarwanda": ("Rwandan", "Kinyarwanda", AFR), "Luganda": ("Ugandan", "Luganda", AFR),
    "Tamil": ("Tamil", "Tamil", SA), "Telugu": ("Telugu", "Telugu", SA), "Bengali": ("Bengali", "Bengali", SA), "Bangla": ("Bengali", "Bengali", SA), "Hindi": ("Hindi", "Hindi", SA),
    "Punjabi": ("Punjabi", "Punjabi", SA), "Urdu": ("Urdu", "Urdu", SA), "Malayalam": ("Malayali", "Malayalam", SA), "Kannada": ("Kannada", "Kannada", SA),
    "Marathi": ("Marathi", "Marathi", SA), "Gujarati": ("Gujarati", "Gujarati", SA), "Nepali": ("Nepali", "Nepali", SA), "Sinhalese": ("Sinhalese", "Sinhala", SA),
    "Odia": ("Odia", "Odia", SA), "Assamese": ("Assamese", "Assamese", SA), "Sindhi": ("Sindhi", "Sindhi", SA), "Pashto": ("Pashtun", "Pashto", SA), "Dhivehi": ("Maldivian", "Dhivehi", SA),
    "Manipuri": ("Manipuri", "Meitei", SA),
    "Vietnamese": ("Vietnamese", "Vietnamese", []), "Thai": ("Thai", "Thai", []), "Tagalog": ("Filipino", "Tagalog", []), "Cebuano": ("Filipino", "Cebuano", []),
    "Ilocano": ("Filipino", "Ilocano", []), "Indonesian": ("Indonesian", "Indonesian", []), "Malay": ("Malay", "Malay", []), "Javanese": ("Javanese", "Javanese", ["Indonesian"]),
    "Sundanese": ("Sundanese", "Sundanese", ["Indonesian"]), "Burmese": ("Burmese", "Burmese", []), "Khmer": ("Khmer", "Khmer", []), "Lao": ("Lao", "Lao", []),
    "Persian": ("Persian", "Persian", []), "Turkish": ("Turkish", "Turkish", []), "Azerbaijani": ("Azerbaijani", "Azerbaijani", []), "Northern Kurdish": ("Kurdish", "Kurmanji", []),
    "Central Kurdish": ("Kurdish", "Sorani", []), "Armenian": ("Armenian", "Armenian", []), "Georgian": ("Georgian", "Georgian", []), "Kazakh": ("Kazakh", "Kazakh", CA),
    "Uzbek": ("Uzbek", "Uzbek", CA), "Kyrgyz": ("Kyrgyz", "Kyrgyz", CA), "Turkmen": ("Turkmen", "Turkmen", CA), "Tajik": ("Tajik", "Tajik", CA), "Mongolian": ("Mongolian", "Mongolian", []),
    "Uyghur": ("Uyghur", "Uyghur", CA), "Tatar": ("Tatar", "Tatar", []), "Bashkir": ("Bashkir", "Bashkir", []), "Abkhaz": ("Abkhaz", "Abkhaz", []), "Ossetian": ("Ossetian", "Ossetian", []),
    "Russian": ("Russian", "Russian", SL), "Ukrainian": ("Ukrainian", "Ukrainian", SL), "Belarusian": ("Belarusian", "Belarusian", SL), "Serbo-Croatian": ("Serbian & Croatian", "Serbo-Croatian", SL),
    "Serbian": ("Serbian & Croatian", "Serbian", SL), "Croatian": ("Serbian & Croatian", "Croatian", SL), "Bosnian": ("Serbian & Croatian", "Bosnian", SL),
    "Bulgarian": ("Bulgarian", "Bulgarian", SL), "Macedonian": ("Macedonian", "Macedonian", SL), "Czech": ("Czech", "Czech", SL), "Slovak": ("Slovak", "Slovak", SL),
    "Slovene": ("Slovene", "Slovene", SL), "Polish": ("Polish", "Polish", SL), "Albanian": ("Albanian", "Albanian", []), "Romanian": ("Romanian", "Romanian", []),
    "Hungarian": ("Hungarian", "Hungarian", []), "Lithuanian": ("Lithuanian", "Lithuanian", ["Baltic"]), "Latvian": ("Latvian", "Latvian", ["Baltic"]), "Estonian": ("Estonian", "Estonian", ["Baltic"]),
    "Finnish": ("Finnish", "Finnish", ["Nordic"]), "Greek": ("Greek", "Greek", []), "Icelandic": ("Icelandic", "Icelandic", ["Nordic"]), "Faroese": ("Faroese", "Faroese", ["Nordic"]),
    "Greenlandic": ("Greenlandic", "Greenlandic", ["Inuit"]), "Inuktitut": ("Inuit", "Inuktitut", []), "Māori": ("Māori", "Māori", PAC), "Hawaiian": ("Hawaiian", "Hawaiian", PAC),
    "Samoan": ("Samoan", "Samoan", PAC), "Tongan": ("Tongan", "Tongan", PAC), "Fijian": ("Fijian", "Fijian", PAC), "Tibetan": ("Tibetan", "Tibetan", []),
    "Quechua": ("Quechua", "Quechua", ["Indigenous American"]), "Aymara": ("Aymara", "Aymara", ["Indigenous American"]), "Navajo": ("Navajo", "Navajo", ["Indigenous American"]),
    "Cherokee": ("Cherokee", "Cherokee", ["Indigenous American"]), "Ojibwe": ("Ojibwe", "Ojibwe", ["Indigenous American"]), "Nahuatl": ("Nahua", "Nahuatl", ["Indigenous American"]),
    "Tupi": ("Tupi", "Tupi", ["Indigenous American"]), "Welsh": ("Welsh", "Welsh", ["Celtic"]), "Irish": ("Irish", "Irish", ["Celtic"]), "Scottish Gaelic": ("Scottish", "Scottish Gaelic", ["Celtic"]),
    "Breton": ("Breton", "Breton", ["Celtic"]), "Basque": ("Basque", "Basque", []), "Catalan": ("Catalan", "Catalan", []), "Galician": ("Galician", "Galician", []),
    "Maltese": ("Maltese", "Maltese", []), "Yiddish": ("Yiddish", "Yiddish", ["Jewish"]), "Atayal": ("Atayal", "Atayal", ["Taiwanese Indigenous"]),
    "Seediq": ("Seediq", "Seediq", ["Taiwanese Indigenous"]), "Amis": ("Amis", "Amis", ["Taiwanese Indigenous"]), "Italian": ("Italian", "Italian", []), "Dutch": ("Dutch", "Dutch", []),
    "Portuguese": ("Portuguese", "Portuguese", []), "Spanish": ("Spanish", "Spanish", []), "French": ("French", "French", []), "German": ("German", "German", []),
    "Swedish": ("Swedish", "Swedish", ["Nordic"]), "Norwegian": ("Norwegian", "Norwegian", ["Nordic"]), "Danish": ("Danish", "Danish", ["Nordic"]),
}

# ── romanization ──
CYR = dict(zip("абвгдезийклмнопрстуфхцчшщъыьэюяё", "a b v g d e z i y k l m n o p r s t u f kh ts ch sh shch  y  e yu ya yo".split(" ")))
CYR_LANG = {
    "Ukrainian": {"г": "h", "ґ": "g", "е": "e", "є": "ye", "и": "y", "і": "i", "ї": "yi", "й": "y", "щ": "shch", "ь": ""},
    "Belarusian": {"г": "h", "і": "i", "ў": "u", "ы": "y", "э": "e", "ь": ""},
    "Bulgarian": {"х": "h", "щ": "sht", "ъ": "a", "ь": "y"},
    "Macedonian": {"ѓ": "gj", "ќ": "kj", "ј": "j", "љ": "lj", "њ": "nj", "џ": "dzh", "ѕ": "dz", "х": "h"},
    "Serbo-Croatian": {"ђ": "đ", "ћ": "ć", "ј": "j", "љ": "lj", "њ": "nj", "џ": "dž", "ч": "č", "ш": "š", "ж": "ž", "х": "h", "ц": "c"},
    "Kazakh": {"ә": "a", "ғ": "gh", "қ": "q", "ң": "ng", "ө": "o", "ұ": "u", "ү": "u", "һ": "h", "і": "i", "й": "y"},
    "Kyrgyz": {"ң": "ng", "ө": "o", "ү": "u"}, "Mongolian": {"ө": "o", "ү": "u"}, "Tajik": {"ғ": "gh", "ӣ": "i", "қ": "q", "ӯ": "u", "ҳ": "h", "ҷ": "j"},
    "Bashkir": {"ә": "a", "ғ": "gh", "ҙ": "dh", "ҡ": "q", "ң": "ng", "ө": "o", "ҫ": "th", "ү": "u", "һ": "h"}, "Tatar": {"ә": "a", "җ": "j", "ң": "ng", "ө": "o", "ү": "u", "һ": "h"},
    "Abkhaz": {}, "Ossetian": {"ӕ": "ae"}, "Russian": {},
}
def cyrillic(s, lang):
    m = {**CYR, **CYR_LANG.get(lang, {})}
    out = "".join(m.get(c, m.get(c.lower(), c)) for c in s.lower())
    return out if LATIN.match(out) else ""

GREEK = dict(zip("αβγδεζηθικλμνξοπρσςτυφχψω", "a v g d e z i th i k l m n x o p r s s t y f ch ps o".split()))
def greek(s):
    s = "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")
    s = re.sub(r"([αε])υ(?=[αεηιοωυβγδζλμνρ]|$)", lambda m: {"α": "av", "ε": "ev"}[m.group(1)], s)
    s = re.sub(r"([αε])υ", lambda m: {"α": "af", "ε": "ef"}[m.group(1)], s)
    s = s.replace("ου", "ou").replace("αι", "ai").replace("ει", "ei").replace("οι", "oi").replace("γγ", "ng").replace("γκ", "gk")
    s = re.sub(r"^μπ", "b", s); s = re.sub(r"^ντ", "d", s)
    return "".join(GREEK.get(c, c) for c in s)

ARMENIAN = dict(zip("աբգդեզէըթժիլխծկհձղճմյնշոչպջռսվտրցփքօֆ",
                    "a b g d e z e y t zh i l kh ts k h dz gh ch m y n sh o ch p j r s v t r ts p k o f".split()))
def armenian(s):
    s = s.lower().replace("ու", "u").replace("և", "ev")
    s = re.sub(r"^ե", "ye", s); s = re.sub(r"^ո(?!ւ)", "vo", s)
    return "".join(ARMENIAN.get(c, c) for c in s)

GEORGIAN = dict(zip("აბგდევზთიკლმნოპჟრსტუფქღყშჩცძწჭხჯჰ", "a b g d e v z t i k l m n o p zh r s t u p k gh q sh ch ts dz ts ch kh j h".split()))
def georgian(s): return "".join(GEORGIAN.get(c, c) for c in s)

# Indian scripts share one layout: the same offset is the same sound in Devanagari, Bengali, Gurmukhi, Gujarati, Odia,
# Tamil, Telugu, Kannada and Malayalam.
INDIC_BASE = {0x900: "Devanagari", 0x980: "Bengali", 0xA00: "Gurmukhi", 0xA80: "Gujarati", 0xB00: "Oriya", 0xB80: "Tamil", 0xC00: "Telugu", 0xC80: "Kannada", 0xD00: "Malayalam"}
IV = {0x05: "a", 0x06: "aa", 0x07: "i", 0x08: "ii", 0x09: "u", 0x0A: "uu", 0x0B: "ri", 0x0C: "li", 0x0E: "e", 0x0F: "e", 0x10: "ai", 0x12: "o", 0x13: "o", 0x14: "au"}
IC = {0x15: "k", 0x16: "kh", 0x17: "g", 0x18: "gh", 0x19: "ng", 0x1A: "ch", 0x1B: "chh", 0x1C: "j", 0x1D: "jh", 0x1E: "ny", 0x1F: "t", 0x20: "th", 0x21: "d", 0x22: "dh", 0x23: "n",
      0x24: "t", 0x25: "th", 0x26: "d", 0x27: "dh", 0x28: "n", 0x29: "n", 0x2A: "p", 0x2B: "ph", 0x2C: "b", 0x2D: "bh", 0x2E: "m", 0x2F: "y", 0x30: "r", 0x31: "r",
      0x32: "l", 0x33: "l", 0x34: "zh", 0x35: "v", 0x36: "sh", 0x37: "sh", 0x38: "s", 0x39: "h"}
IS = {0x3E: "aa", 0x3F: "i", 0x40: "ii", 0x41: "u", 0x42: "uu", 0x43: "ri", 0x46: "e", 0x47: "e", 0x48: "ai", 0x4A: "o", 0x4B: "o", 0x4C: "au"}
NUKTA = {"k": "q", "kh": "kh", "g": "gh", "j": "z", "d": "r", "dh": "rh", "ph": "f", "y": "y"}
DROP_FINAL_A = {"Hindi", "Marathi", "Gujarati", "Punjabi", "Bengali", "Nepali", "Odia", "Assamese", "Urdu", "Sindhi"}
def indic(s, lang):
    # strict reading: inherent "a" after every consonant without a vowel sign or virama
    out, prev_cons = [], False
    for ch in s:
        cp = ord(ch); base = next((b for b in INDIC_BASE if b <= cp < b + 0x80), None)
        if base is None: return ""
        o = cp - base
        if o in IC:
            if prev_cons: out.append("a")
            c = IC[o]
            if base == 0x980 and o == 0x2C: c = "w" if out and not prev_cons and out[-1] not in "aeiou" else "b"   # Bengali ব is b (but স্ব is sw)
            if base == 0x980 and o == 0x2F: c = "j" if not out else "y"
            if base == 0x980 and o == 0x35: c = "b"
            out.append(c); prev_cons = True
        elif o in IS: out.append(IS[o]); prev_cons = False
        elif o == 0x4D: prev_cons = False                                       # virama: no vowel
        elif o in IV: out.append(IV[o]); prev_cons = False
        elif o == 0x3C and out: out[-1] = NUKTA.get(out[-1], out[-1])
        elif o in (0x01, 0x02, 0x03):
            if prev_cons: out.append("a"); prev_cons = False
            out.append("h" if o == 0x03 else "n~m")
        elif base == 0xA00 and o == 0x70: out.append("n")                        # Gurmukhi tippi
        elif base == 0xA00 and o == 0x71: out.append("~")                        # addak: doubles the next consonant
        else: continue
    if prev_cons: out.append("a")
    s = "".join(out)
    s = re.sub(r"n~m(?=[pbm])", "m", s).replace("n~m", "n")
    s = re.sub(r"~(\w)", r"\1\1", s).replace("~", "")
    if lang in DROP_FINAL_A and len(s) > 3 and s.endswith("a") and not s.endswith("aa") and out and out[-1] == "a" and s[-2] not in "aeiou": s = s[:-1]
    return s
def indic_variants(strict, lang):
    # the spellings a name like this is usually written in, each with how far it strays from the letters
    vs = {strict: 0}
    def add(v, c):
        if v not in vs or vs[v] > c: vs[v] = c
    for a, bs in (("aa", ["a"]), ("ii", ["i", "ee"]), ("uu", ["u", "oo"]), ("sh", ["s"]), ("v", ["w"]), ("chh", ["ch"]), ("ny", ["n"])):
        for v, c in list(vs.items()):
            for b in bs: add(v.replace(a, b), c + (0 if a in ("aa", "ii", "uu") else 1))
    for _ in range(3 if lang in ("Tamil", "Malayalam", "Telugu", "Kannada") else 0):
        for v, c in list(vs.items()):
            if c > 3: continue
            for pat, rep in ((r"(?<=[aeiou])k(?=[aeiou])", "g"), (r"(?<=[aeiou])t(?=[aeiou])", "d"), (r"(?<=[aeiou])p(?=[aeiou])", "b"), (r"(?<=[nm])k", "g"),
                             (r"(?<=n)t", "d"), (r"^ch", "s"), (r"^ch", "sh"), (r"^k", "g"), (r"^t", "d"), (r"^p", "b"), (r"tt", "th"), (r"(?<=[aeiour])t(?=[aeiou])", "th"), (r"(?<=[aeiou])ch(?=[aeiou])", "s"), (r"^shr", "sr"), (r"(?<=n)t(?=[aeiou])", "th"), (r"^ir(?=[aeiou])", "r"), (r"(?<=[aeiou])s(?=[aeiou])", "j")):
                add(re.sub(pat, rep, v), c + 1)
            if v.endswith("u") and len(v) > 4: add(v[:-1], c + 1)
    if lang == "Bengali":
        for v, c in list(vs.items()): add(re.sub(r"a(?=[^aeiou]+[aeiou])", "o", v, count=1), c + 1)
    if lang in DROP_FINAL_A:   # medial schwa deletion (Anamol → Anmol)
        for v, c in list(vs.items()): add(re.sub(r"(?<=[aeiou][^aeiou])a(?=[^aeiou]{1,2}[aeiou])", "", v), c)
    return vs

def latinize_tr(t):
    t = re.sub(r"<[^>]+>|\{\{[^}]*\}\}|\[\[|\]\]", "", t).split(",")[0].split("/")[0].strip()
    for a, b in (("š", "sh"), ("č", "ch"), ("ž", "zh"), ("ḵ", "kh"), ("x", "kh"), ("ġ", "gh"), ("ʿ", ""), ("ʾ", ""), ("’", ""), ("'", ""), ("ʼ", ""), ("ṣ", "s"), ("ḍ", "d"), ("ṭ", "t"), ("ẓ", "z"), ("ḥ", "h")):
        t = t.replace(a, b)
    t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^A-Za-z -]", "", t).strip()
    return t if t and LATIN.match(t) and len(t) <= 24 else ""

def load_db():
    db = {}
    for line in open(os.path.join(ROOT, "data", "names-db.tsv"), encoding="utf-8"):
        n, g, cc, c = line.rstrip("\n").split("\t")
        db[n.lower()] = (n, int(c), g)
    return db

def romanize(title, lang, tr, db):
    if LATIN.match(title): return title
    if tr: return latinize_tr(tr)
    s = title.strip()
    if re.search(r"[Ѐ-ӿ]", s): r = cyrillic(s, lang)
    elif re.search(r"[Ͱ-Ͽ]", s): r = greek(s)
    elif re.search(r"[԰-֏]", s): r = armenian(s)
    elif re.search(r"[Ⴀ-ჿ]", s): r = georgian(s)
    elif re.search(r"[ऀ-ൿ]", s):
        strict = indic(s, lang)
        if not strict: return ""
        vs = indic_variants(strict, lang)
        cap = 4 if lang in ("Tamil", "Malayalam", "Telugu", "Kannada") else 2      # Tamil writes s/ch, k/g, t/d with one letter each
        hits = sorted((c, -db[v][1], db[v][0]) for v, c in vs.items() if v in db and db[v][1] >= 5 and c <= cap)
        if hits: return hits[0][2]
        r = strict.replace("aa", "a").replace("ii", "i").replace("uu", "u")
        if lang in ("Tamil", "Malayalam"):
            # the usual Tamil spelling when nothing registered matches: s for ச, g/d/b between vowels, th after n (Senthil, Sadasivan)
            r = re.sub(r"^ch", "s", r); r = re.sub(r"(?<=[aeiou])ch(?=[aeiou])", "s", r)
            r = re.sub(r"(?<=[aeiou])k(?=[aeiou])", "g", r); r = re.sub(r"(?<=[aeiou])t(?=[aeiou])", "d", r); r = re.sub(r"(?<=n)t", "th", r).replace("ngk", "ng")
            r = re.sub(r"^ir(?=[aeiou])", "r", r)                           # Tamil writes an i before a name's first r (இராமன் Raman)
    else: return ""                                                            # Arabic, Thai, Burmese… without a recorded romanization
    return r if r and LATIN.match(r) else ""

FOREIGN = {"Hebrew", "Greek", "Latin", "English", "French", "German", "Italian", "Spanish", "Portuguese", "Russian", "Dutch", "Aramaic", "Germanic", "Celtic"}

# ── meanings from the entry ──
def clean(t):
    t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", t)
    t = re.sub(r"\{\{[^{}]*\}\}", "", t); t = re.sub(r"\{\{[^{}]*\}\}", "", t)
    t = re.sub(r"<[^>]+>|'''?", "", t)
    t = re.sub(r"\{\{.*$|\}\}", "", t)                                        # unfinished template markup
    return re.sub(r"\s+", " ", t).strip(" ,.;:")
def section(text, lang):
    m = re.search(r"(?m)^==\s*" + re.escape(lang) + r"\s*==\s*$", text)
    if not m: return ""
    nxt = re.search(r"(?m)^==[^=].*==\s*$", text[m.end():])
    return text[m.end(): m.end() + nxt.start()] if nxt else text[m.end():]
def details(sec):
    d = {}
    gn = re.search(r"\{\{given name\|[^{}]*\}\}", sec)
    if gn:
        for k in ("meaning", "from", "eq", "dim", "xlit"):
            m = re.search(r"\|" + k + r"=([^|}]+)", gn.group(0))
            if m: d[k] = clean(m.group(1))
    tr = re.search(r"\|tr=([^|}]+)", sec)
    if tr: d["tr"] = tr.group(1)
    if "meaning" not in d:
        ety = re.search(r"(?ms)^===+\s*Etymology[^=]*===+\s*$(.*?)(?=^===)", sec)
        e = ety.group(1) if ety else ""
        lit = re.search(r"\|lit=([^|}]+)", e)
        quote = re.search(r"[“\"‘]([^”\"’]{3,60})[”\"’]", clean(e))
        glosses = re.findall(r"\|t\d?=([^|}]+)", e)
        if lit: d["meaning"] = clean(lit.group(1))
        elif quote and re.search(r"meaning|lit|means|“", e): d["meaning"] = quote.group(1)
        elif glosses and len(glosses) <= 3: d["meaning"] = " + ".join(clean(g) for g in glosses)
    if "meaning" not in d:
        # the name is also an ordinary word (Tamil அன்பு Anbu: love)
        m = re.search(r"(?ms)^===+\s*(Noun|Adjective)\s*===+\s*$.*?^#\s*([^:*\n][^\n]*)", sec)
        if m:
            g = clean(m.group(2))
            if 2 < len(g) < 50 and not re.search(r"given name|surname|placename|city|village|river", g, re.I): d["meaning"] = g
    if "from" in d: d["from"] = d["from"].split(",")[0]
    return d

if __name__ == "__main__":
    db = load_db()
    entries = collections.defaultdict(list)       # key → [entry]
    stats = collections.Counter()
    for path in glob.glob(os.path.join(RAW, "wikt", "*.json")):
        lang = os.path.basename(path)[:-5].replace("_", " ")
        info = LANG.get(lang)
        if not info: continue
        culture, language, groups = info
        for title, v in json.load(open(path, encoding="utf-8")).items():
            sec = section(v["text"], lang)
            d = details(sec) if sec else {}
            # a Tamil or Yoruba form of a name from far away (Moshe, Shmuel) isn't a name with Tamil or Yoruba roots
            if groups and groups[0] in ("African", "South Asian", "Central Asian", "Pacific", "Taiwanese Indigenous", "Indigenous American") or culture in ("Vietnamese", "Thai", "Filipino", "Indonesian", "Malay", "Burmese", "Khmer", "Lao", "Tibetan", "Mongolian"):
                if d.get("from", "").split(" ")[-1] in FOREIGN: stats[(culture, "foreign")] += 1; continue
            n = romanize(title, lang, d.get("tr", ""), db)
            if not n or " " in n.strip() or len(n) < 2: stats[(culture, "skipped")] += 1; continue
            n = n[:1].upper() + n[1:]
            if n.lower() in ("shudra", "dalit", "chamar"): continue           # caste terms, not names
            entries[n.lower()].append({"n": n, "g": v["g"], "o": culture, "l": language, "oo": groups, "m": d.get("meaning", ""), "from": d.get("from", ""),
                                       "eq": d.get("eq", ""), "native": "" if LATIN.match(title) else title, "src": "wiktionary"})
            stats[(culture, "kept")] += 1
    for qid, g, lang, label, native in json.load(open(os.path.join(RAW, "wd-given-langs.json"), encoding="utf-8")):
        info = LANG.get(lang)
        if not info or not label or not LATIN.match(label) or " " in label: continue
        culture, language, groups = info
        entries[label.lower()].append({"n": label, "g": g, "o": culture, "l": language, "oo": groups, "m": "", "from": "", "eq": "",
                                       "native": native if native and not LATIN.match(native) else "", "src": "wikidata"})
        stats[(culture, "wikidata")] += 1
    # meanings found on each name's own Wiktionary page (fetch_name_meanings.py)
    mp = os.path.join(RAW, "wikt-meanings.json")
    found = json.load(open(mp, encoding="utf-8")) if os.path.exists(mp) else {}
    # trusted only where names usually are ordinary words (Turkish Öykü "story", Yoruba, Hindi…); elsewhere the word with the
    # same spelling is often unrelated (Polish "siara", Finnish "herkko")
    WORD_NAMES = {"Turkish", "Azerbaijani", "Kazakh", "Kyrgyz", "Uzbek", "Turkmen", "Tatar", "Bashkir", "Persian", "Kurdish", "Tajik", "Albanian",
                  "Indonesian", "Malay", "Javanese", "Mongolian", "Uyghur"}
    for es in entries.values():
        for e in es:
            if not e["m"] and found.get(e["n"]) and (e["o"] in WORD_NAMES or set(e["oo"]) & {"African", "South Asian"}): e["m"] = clean(found[e["n"]])
    rows = []
    for k, es in entries.items():
        # one name, one home: the entry with a meaning first, Wiktionary before Wikidata; the other cultures are kept as "also"
        es.sort(key=lambda e: (not e["m"], e["src"] != "wiktionary"))
        best = es[0]
        cultures = list(dict.fromkeys(e["o"] for e in es))
        others = [c for c in cultures if c != best["o"]]
        groups = list(dict.fromkeys(g for e in es for g in e["oo"]))
        gs = {e["g"] for e in es}
        g = "e" if "e" in gs or len(gs) > 1 else gs.pop()
        story = f"A {best['o']} name" + (f" from {best['from']}" if best["from"] and best["from"].lower() not in (best["l"].lower(), best["o"].lower()) else "")
        story += (f", the {best['l']} form of {best['eq']}" if best["eq"] and best["eq"].lower() != k else "") + "."
        if best["native"]: story += f" Written {best['native']}."
        if others: story += f" Also a {', '.join(others[:3])} name."
        rows.append([best["n"], g, best["o"], best["l"], "", best["m"][:80], story, "", "real", [c for c in others + groups if c != best["o"]]])
    rows.sort(key=lambda r: r[0])
    json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    per = collections.Counter(r[2] for r in rows)
    print(f"{len(rows):,} names in {len(per)} cultures → {OUT} ({os.path.getsize(OUT) // 1024} KB), {sum(1 for r in rows if r[5]):,} with meanings")
    print(per.most_common(90))
