# Israel's baby names (Central Bureau of Statistics, 1948–2024, via babynamesIL) are written in Hebrew letters.
# This turns each into the Latin spelling people actually use, without guessing:
#   1. a known pairing: Wikidata given names with a Hebrew label (CC0), or the Bible's Hebrew forms (STEPBible TIPNR)
#   2. otherwise, every way the Hebrew letters can be read aloud (ב = b or v, ו = v, o or u, …), kept only if that
#      spelling is already a real registered name in data/names-db.tsv, and the most common one wins.
# Names neither method can verify are left out. Writes raw/il-latin.csv (name, sex, count, hebrew, community, how).
#
#   python3 scripts/hebrew_names.py
import collections, csv, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); RAW = os.path.join(ROOT, "raw")
HEB = re.compile(r"^[א-ת'\" -]+$")
strip = lambda s: re.sub(r"[֑-ׇ]", "", s).replace("״", '"').replace("׳", "'").strip()

# how each letter can sound (Modern Hebrew; Arabic names written in Hebrew use ג' ח ע ק ט צ for their own sounds)
SOUNDS = {
    "א": ["", "a", "e", "i", "o"], "ב": ["b", "v"], "ג": ["g"], "ג'": ["j", "g"], "ד": ["d"], "ד'": ["dh", "th", "d"], "ה": ["h", ""],
    "ו": ["v", "o", "u", "w"], "וו": ["v", "w"], "ז": ["z"], "ז'": ["zh", "j"], "ח": ["h", "ch", "kh"], "ט": ["t"], "ט'": ["th", "d", "z"],
    "י": ["y", "i", "e", "ei", "ai"], "יי": ["y", "yi", "i", "ei", "ai"], "כ": ["k", "kh", "ch", "c"], "ך": ["kh", "ch", "k"], "ל": ["l"], "מ": ["m"], "ם": ["m"],
    "נ": ["n"], "ן": ["n"], "ס": ["s", "c"], "ע": ["", "a", "e", "o", "i"], "ע'": ["gh", "g"], "פ": ["p", "f", "ph"], "ף": ["f", "ph"],
    "צ": ["tz", "ts", "z", "s"], "ץ": ["tz", "ts", "z", "s"], "צ'": ["ch", "tch"], "ק": ["k", "q", "c"], "ר": ["r"], "ש": ["sh", "s"],
    "ת": ["t", "th"], "ת'": ["th", "t"], " ": [" "], "-": ["-"],
}
VOWELS = ["", "a", "e", "i", "o"]          # unwritten vowels between consonants

def tokens(h):
    out, i = [], 0
    while i < len(h):
        two = h[i:i + 2]
        if len(two) == 2 and two in SOUNDS and (two[1] == "'" or two in ("וו", "יי")): out.append(two); i += 2
        else: out.append(h[i]); i += 1
    return [t for t in out if t in SOUNDS]

def load_lexicon():
    count, sex, prefixes = {}, {}, set()
    for line in open(os.path.join(ROOT, "data", "names-db.tsv"), encoding="utf-8"):
        n, g, cc, c = line.rstrip("\n").split("\t")
        k = n.lower()
        if not re.fullmatch(r"[a-z'-]+", k): continue
        count[k] = (int(c), n); sex[k] = g
        for j in range(1, len(k) + 1): prefixes.add(k[:j])
    return count, sex, prefixes

POP, POP_ARAB = .28, .28   # how much a spelling's popularity worldwide counts against how naturally it reads the letters
B_MID, P_MID = .9, .7      # ב and פ after the first letter are usually v and f (Avner, Shoval), sometimes b and p (Abir)
MIN_PEOPLE = 20
HEBREW_LATIN, HEBREW_BOOST = set(), 1   # Latin spellings Wikidata, the Bible or USUAL pair with some Hebrew spelling (Eyal, Levi, Neta)   # a reading must be a name at least this many people have
ADDED = {"a": .75, "e": .6, "i": .3, "o": .3}   # unwritten vowels: in Hebrew the unwritten one is most often "a"
ADDED_ARAB = {"a": 1, "e": .6, "i": .5, "u": .5, "o": .3}   # Arabic short vowels a, i, u; Palestinian spellings often write i as e (Khaled, Maher)
ARAB = {"Muslim", "Christian-Arab", "Druze"}

def sex_fit(g, want):
    return 1 if g in ("u", "?") or g == want else .03

def options(toks, ti, community):
    # how this letter can sound here, with how likely each reading is (modern Hebrew spelling rules)
    t, last, prev = toks[ti], ti == len(toks) - 1, toks[ti - 1] if ti else ""
    nxt = toks[ti + 1] if ti + 1 < len(toks) else ""
    arab = community in ARAB
    if arab: return arab_options(toks, ti)
    if t == "ו": return [("v", 1)] if ti == 0 else [("o", 1), ("u", .9), ("v", .08), ("w", .05 if not arab else .5)]
    if t == "וו": return [("v", 1), ("w", .6 if arab else .1)]
    if t == "י":
        if ti == 0: return [("y", 1), ("i", .15)]
        if last: return [("i", 1), ("y", .6), ("ie", .3), ("ey", .3), ("ai", .4), ("ei", .3)]
        return [("i", 1), ("y", .5), ("e", .5), ("ei", .35), ("ai", .35)]
    if t == "יי": return [("y", 1), ("i", .6), ("ei", .5), ("ai", .5), ("yi", .3)]
    if t in ("א", "ע"):
        if last and prev in ("ו", "י"): return [("", 1)]                                   # silent at the end (Lavi, Guy)
        if nxt in ("ו", "י", "יי"): return [("", 1), ("e", .7), ("a", .7)]                 # carrying the next vowel, or its own (Meir, Maor)
        if t == "ע" and arab: return [("a", 1), ("e", .5), ("i", .5), ("o", .4), ("", .3)]
        return [("e", 1), ("a", .85), ("i", .5), ("o", .4), ("", .05)] if ti == 0 else [("a", 1), ("e", .8), ("i", .5), ("o", .4), ("", .15)]
    if t == "ה":
        if last: return [("a", 1), ("ah", .6), ("e", .6), ("eh", .3), ("o", .25)]
        return [("h", 1)]
    if t in ("צ", "ץ"): return [("s", 1), ("z", .4), ("tz", .3)] if arab else [("tz", 1), ("ts", .6), ("z", .4), ("s", .15)]
    if t == "ק": return [("q", 1), ("k", .8)] if arab else [("k", 1), ("c", .4), ("q", .1)]
    if t == "ח": return [("h", 1), ("kh", .4)] if arab else [("ch", 1), ("h", .8), ("kh", .5)]
    if t in ("כ", "ך"): return [("k", 1), ("kh", .5)] if arab else [("ch", 1), ("kh", .6), ("k", .6), ("c", .3)]
    if t == "ש": return [("sh", 1), ("s", .15 if not arab else .8)]
    if t == "ב": return [("b", 1), ("v", .9)] if ti == 0 else [("v", 1), ("b", B_MID)]
    if t == "פ": return [("p", 1), ("f", .6)] if ti == 0 else [("f", 1), ("p", P_MID), ("ph", .3)]
    if t == "ת": return [("t", 1), ("th", .3)]
    return [(o, 1 if k == 0 else .5) for k, o in enumerate(SOUNDS[t])]

# Arab-sector names: CBS writes the Arabic letters one for one (ا→א, ج→ג', ش→ש, ص→צ), so a reading has to keep each letter's
# standard transliteration: alef and the final alef/ta marbuta are "a" (Rana, Salwa, Asma, not Rene, Clo, Esme), ب is b and ف is f
# (Arabic has no v or p), ي is y or i (Bayan, not Bean), ش is sh (Rasha, not Rosa), س is s (Salwa, not Clo).
ARAB_SOUNDS = {"ב": [("b", 1)], "ג": [("gh", 1), ("g", .7), ("j", .4)], "ג'": [("j", 1), ("g", .5)], "ד": [("d", 1)], "ד'": [("dh", 1), ("th", .6), ("z", .5), ("d", .3)],
               "ז": [("z", 1)], "ז'": [("j", 1), ("zh", .5)], "ח": [("h", 1), ("kh", .4)], "ט": [("t", 1)], "ט'": [("z", 1), ("dh", .6), ("th", .3)],
               "כ": [("k", 1), ("kh", .4)], "ך": [("k", 1), ("kh", .4)], "ס": [("s", 1)], "ע'": [("gh", 1), ("g", .4)], "פ": [("f", 1)], "ף": [("f", 1)],
               "צ": [("s", 1), ("ss", .3)], "ץ": [("s", 1)], "צ'": [("d", 1), ("dh", .6)], "ק": [("q", 1), ("k", .8)], "ש": [("sh", 1), ("ch", .3)],
               "ת": [("t", 1), ("th", .3)], "ת'": [("th", 1), ("t", .4)]}

def arab_options(toks, ti):
    t, last, prev = toks[ti], ti == len(toks) - 1, toks[ti - 1] if ti else ""
    nxt = toks[ti + 1] if ti + 1 < len(toks) else ""
    if t == "א":
        if ti == 0:
            if nxt in ("ו", "י"): return [("", 1), ("a", .5)]                                 # carrying the next letter's vowel (Ismail, Osama)
            return [("a", 1), ("i", .6), ("u", .3), ("e", .25), ("o", .2)]
        if prev == "א": return [("", 1), ("a", .5)]                                         # a written hamza after a long a (Alaa, Shaimaa)
        return [("a", 1), ("aa", .3)]
    if t == "ע": return [("a", 1), ("i", .4), ("o", .3), ("u", .3), ("e", .15), ("", .5)]
    if t == "ה": return [("a", 1), ("ah", .6), ("e", .4)] if last else [("h", 1)]
    if t == "ו":
        if ti == 0: return [("w", 1)]
        w = 1 if nxt in ("א", "ע", "ה", "י", "יי") else .2                                      # a consonant w carries a written vowel (Salwa); else ו is u/o (Jud)
        return [("u", 1), ("w", w), ("o", .6), ("ou", .3), ("oo", .2)]
    if t == "וו": return [("w", 1), ("ww", .3)]
    if t == "י":
        if ti == 0: return [("y", 1)]
        if last: return [("i", 1), ("y", .6), ("ee", .3), ("ey", .3), ("ay", .4), ("ai", .4)]
        return [("i", 1), ("y", .6), ("ee", .3), ("ay", .4), ("ai", .4), ("ey", .3), ("ei", .3)]
    if t == "יי": return [("y", 1), ("ay", .7), ("ai", .6), ("i", .6), ("ei", .3), ("ey", .3), ("yy", .4), ("iy", .3)]
    opts = ARAB_SOUNDS.get(t) or [(o, 1 if k == 0 else .5) for k, o in enumerate(SOUNDS[t])]
    return opts + [(o[0] + o, w * .15) for o, w in opts if o and ti and o[0] not in "aeiou"]   # a doubled consonant (shadda) Hebrew writes once (Hassan, Ammar)

# The Arabic spelling behind an Arab-sector name: each Hebrew letter as the Arabic letter(s) it writes, compared with Wikidata's
# Arabic given names (raw/wd-arabic, CC0) and the Latin spellings they carry. Hamza, alef maqsura and ta marbuta are folded
# to the plain letter Hebrew writes for them (أسماء = אסמא, سلوى = סלוא).
TO_ARABIC = {"א": "ا", "ב": "ب", "ג": "جغ", "ג'": "ج", "ד": "د", "ד'": "ذ", "ה": "ه", "ו": "و", "וו": "و", "ז": "ز", "ז'": "ج", "ח": "حخ", "ח'": "خ",
             "ט": "ط", "ט'": "ظ", "י": "ي", "יי": "ي", "כ": "ك", "ך": "ك", "ל": "ل", "מ": "م", "ם": "م", "נ": "ن", "ן": "ن", "ס": "سص", "ע": "ع",
             "ע'": "غ", "פ": "ف", "ף": "ف", "צ": "ص", "ץ": "ص", "צ'": "ض", "ק": "ق", "ר": "ر", "ש": "ش", "ת": "تط", "ת'": "ث"}

def fold_arabic(a):
    a = re.sub(r"[ً-ْٰـ]", "", a)
    a = a.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ء": "ا", "ى": "ا", "ة": "ه", "ؤ": "و", "ئ": "ي"}))
    return re.sub(r"ا+", "ا", a.replace(" ", ""))

def arabic_lexicon(count):
    # folded Arabic spelling → {Latin spelling: number of Wikidata labels using it}, keeping only spellings that are registered names
    lex = collections.defaultdict(collections.Counter)
    for f in ("arabic-name-latin-forms.json", "given-name-latin-forms.json"):
        p = os.path.join(RAW, "wd-arabic", f)
        if not os.path.exists(p): continue
        for _, ar, lat in json.load(open(p, encoding="utf-8")):
            for l in re.sub(r"\s*\(.*?\)", "", lat).split("/"):
                l = l.strip()
                if re.fullmatch(r"[A-Z][a-z'-]+", l) and l.lower() in count: lex[fold_arabic(ar)][count[l.lower()][1]] += 1
    return lex

def arabic_spellings(h):
    toks, out = [], [""]
    i = 0
    while i < len(h):
        two = h[i:i + 2]
        if len(two) == 2 and two in TO_ARABIC and (two[1] == "'" or two in ("וו", "יי")): toks.append(two); i += 2
        else: toks.append(h[i]); i += 1
    for t in toks:
        if t not in TO_ARABIC: continue
        out = [o + a for o in out for a in TO_ARABIC[t]]
        if len(out) > 64: break
    return {fold_arabic(o) for o in out}

def arabic_forms(h, lex):
    # Wikidata's Latin spellings of the Arabic name these Hebrew letters write
    out = collections.Counter()
    for a in arabic_spellings(h): out.update(lex.get(a, {}))
    return out

SKELETON = str.maketrans({"q": "k", "c": "k", "j": "g", "v": "f", "p": "f"})
def skeleton(latin):
    # the consonants that carry a name (vowels, h, w, y and doubling dropped): Georgette → grgt
    k = re.sub(r"[aeiouhwy'-]", "", latin.lower().replace("ph", "f").replace("x", "ks").translate(SKELETON))
    return re.sub(r"(.)\1+", r"\1", k)

HEB_SKELETON = {"ב": "b", "ג": "g", "ג'": "g", "ד": "d", "ד'": "d", "ז": "z", "ז'": "g", "ט": "t", "ט'": "z", "ת": "t", "ת'": "t", "כ": "k", "ך": "k",
                "ק": "k", "ל": "l", "מ": "m", "ם": "m", "נ": "n", "ן": "n", "ס": "s", "צ": "s", "ץ": "s", "ש": "s", "פ": "f", "ף": "f", "ר": "r", "ע'": "g", "צ'": "d"}
def heb_skeleton(h):
    return re.sub(r"(.)\1+", r"\1", "".join(HEB_SKELETON.get(t, "") for t in tokens(h)))

def readings(h, want, community, count, sex, prefixes, beam=800):
    # every reading of the letters, pruned to spellings that start a real name, scored by how natural it is
    toks, arab = tokens(h), community in ARAB
    added = ADDED_ARAB if arab else ADDED
    states = {"": 1.0}
    for ti in range(len(toks)):
        nxt = {}
        for st, sc in states.items():
            for o, w in options(toks, ti, community):
                vowel_end = st[-1:] in tuple("aeiou") or (st[-1:] == "y" and len(st) > 1 and not arab)   # a word-initial y is a consonant (Yigal); in Arabic so is ay (Maryam)
                gaps = [("", 1)] if ti == 0 or not o or not st or vowel_end or o[0] in ("aeiou" if arab else "aeiouy") else [("", 1)] + list(added.items())
                if arab and len(gaps) > 1 and not re.search("[aeiou]", st): gaps = gaps[1:]          # Arabic never opens on two consonants (Zayd, not Zyad)
                if not arab and gaps[0][0] == "" and st and o and st[-1] == o[0] and o[0] not in "aeiou": gaps = gaps[1:] or gaps   # never a bare doubled letter (Oded, not Odd)
                for v, vw in gaps:
                    cand = st + v + o
                    score = sc * w * vw
                    if (cand == "" or cand in prefixes) and score > nxt.get(cand, 0): nxt[cand] = score
        if not nxt: return []
        states = dict(sorted(nxt.items(), key=lambda kv: -kv[1])[:beam])
    out = []
    for st, sc in states.items():
        if st in count and count[st][0] >= MIN_PEOPLE:
            boost = HEBREW_BOOST if not arab and st in HEBREW_LATIN else 1
            out.append((sc * boost * sex_fit(sex[st], want) * (1 + count[st][0]) ** (POP_ARAB if arab else POP), count[st][1]))
    return sorted(out, reverse=True)

# The standard Israeli spelling of common names whose romanization doesn't follow the letters
# (Israel's own passport and press usage). Checked by hand; everything else comes from the rules above.
USUAL = dict(x.split(":") for x in """גיא:Guy אייל:Eyal מיכאל:Michael שלמה:Shlomo שמעון:Shimon מאיר:Meir רוני:Roni אורן:Oren אלעד:Elad עומרי:Omri
נגה:Noga רפאל:Refael אליהו:Eliyahu יהונתן:Yehonatan איתן:Eitan עידן:Idan אריה:Arye יצחק:Yitzhak יעקב:Yaakov אהרון:Aharon לביא:Lavi
אליה:Eliya משה:Moshe יוסף:Yosef אברהם:Avraham שרה:Sarah רבקה:Rivka חנה:Hana אסתר:Esther יהודה:Yehuda ישראל:Yisrael דבורה:Dvora
עומר:Omer נתן:Natan שמואל:Shmuel מרדכי:Mordechai חיים:Haim ליאת:Liat אילנה:Ilana אליאור:Elior אביטל:Avital רעות:Reut נוי:Noy
אופק:Ofek ליאל:Liel אוריה:Oriya אלמוג:Almog זיו:Ziv שקד:Shaked אגם:Agam אלה:Ela שגיא:Sagi יעלי:Yaeli נחמה:Nechama
יפה:Yafa ראובן:Reuven ערן:Eran ארז:Erez עילאי:Ilai ירון:Yaron אפרים:Efraim דליה:Dalia הלל:Hillel שירן:Shiran יגאל:Yigal דביר:Dvir
אביתר:Evyatar שרון:Sharon יחזקאל:Yechezkel אדיר:Adir ינון:Yinon שאול:Shaul ינאי:Yanai עודד:Oded ברק:Barak שמחה:Simcha אביה:Aviya
גיל:Gil עידו:Ido יוסי:Yossi צבי:Tzvi זאב:Zeev אליעזר:Eliezer מנשה:Menashe ישעיהו:Yeshayahu ירמיהו:Yirmiyahu
שי:Shai אילן:Ilan רונן:Ronen""".split())
JEWISH_ONLY = {"Jewish", "Other"}

def known_pairs():
    best = {}
    for rank, kind in enumerate(("native", "label", "alias")):
        p = os.path.join(RAW, f"wd-he-{kind}.tsv")
        if not os.path.exists(p): continue
        for l in open(p, encoding="utf-8").read().split("\n")[1:]:
            c = l.split("\t")
            if len(c) < 3: continue
            he, en = strip(c[1].rsplit("@", 1)[0].strip('"')), c[2].rsplit("@", 1)[0].strip('"')
            if HEB.match(he) and re.fullmatch(r"[A-Z][a-zA-Z'\-]+", en) and (he not in best or rank < best[he][0]): best[he] = (rank, en)
    pairs = {h: (en, "native" if r == 0 else "wikidata" if r == 1 else "alias") for h, (r, en) in best.items()}
    txt = open(os.path.join(RAW, "tipnr.txt"), encoding="utf-8").read()
    for b in txt.split("$========== ")[1:]:
        if not b.startswith("PERSON"): continue
        for l in b.split("\n"):
            if l.startswith("– ") and not l.startswith("– Total"):
                c = l.split("\t")
                if len(c) > 3 and "=" in c[2]:
                    nm = c[1].split("@")[0]
                    for h in c[2].split("=")[-1].split(","):
                        h = strip(h)
                        if HEB.match(h) and re.fullmatch(r"[A-Z][a-z'\-]+", nm): pairs.setdefault(h, (nm, "bible"))
    return pairs

if __name__ == "__main__":
    count, sex, prefixes = load_lexicon()
    pairs = known_pairs()
    lex = arabic_lexicon(count)
    tot = collections.Counter()
    for f in ("il.csv", "il-other.csv"):
        for r in csv.DictReader(open(os.path.join(RAW, f), encoding="utf-8")):
            tot[(r["sector"], r["sex"], strip(r["name"]))] += int(r["n"])
    latin, how = {}, collections.Counter()
    for sec, want, h in {(sec, "m" if sx == "M" else "f", h) for sec, sx, h in tot}:
        pair = pairs.get(h)
        ok = lambda en: en and sex_fit(sex.get(en.lower(), "?"), want) > .5
        if sec in JEWISH_ONLY and h in USUAL: latin[(h, want, sec)] = (USUAL[h], "usual spelling"); continue
        # Arab-sector names: a reading that keeps each Arabic letter's standard sound, preferring one that is also a Latin
        # spelling Wikidata gives the same name in Arabic script (Rana, Salwa, Bayan); failing a reading, an Arabic-script
        # pairing with the same consonants (ج ور ج ي ت = Georgette)
        if sec in ARAB:
            rs, forms = readings(h, want, sec, count, sex, prefixes), arabic_forms(h, lex)
            if rs:   # a reading Wikidata also gives the Arabic name counts for more (عُلا Alaa, not Ola)
                sc, n = max((sc * (1 + forms[n]) ** .5, n) for sc, n in rs)
                if forms[n]: latin[(h, want, sec)] = (n, "arabic pairing"); continue
            # a Hebrew Wikidata pairing only when its consonants are these letters (Sara, George; not Varda for وردة Warda)
            if pair and pair[1] in ("native", "wikidata") and ok(pair[0]) and skeleton(pair[0]) == heb_skeleton(h):
                latin[(h, want, sec)] = (pair[0], "known pairing"); continue
            if rs and rs[0][0] > .4: latin[(h, want, sec)] = (rs[0][1], "verified reading"); continue
            same = [(count[n.lower()][0] * v, n) for n, v in forms.items()
                    if skeleton(n) == heb_skeleton(h) and count[n.lower()][0] >= MIN_PEOPLE and sex_fit(sex[n.lower()], want) > .5]
            if same: latin[(h, want, sec)] = (max(same)[1], "arabic pairing"); continue
            if pair and ok(pair[0]) and skeleton(pair[0]) == heb_skeleton(h): latin[(h, want, sec)] = (pair[0], "known pairing")
            continue
        # 1. a Wikidata given name whose Hebrew label is this exact spelling (Noa, Yael, Hamutal)
        if pair and pair[1] in ("native", "wikidata") and ok(pair[0]): latin[(h, want, sec)] = (pair[0], "known pairing"); continue
        # 2. the most natural reading that's a real, common name of the right sex (Moshe, Shira, Lior, Muhammad)
        rs = readings(h, want, sec, count, sex, prefixes)
        if rs and rs[0][0] > .4: latin[(h, want, sec)] = (rs[0][1], "verified reading"); continue
        # 3. a Wikidata alias or the Bible's form of the name
        if pair and ok(pair[0]): latin[(h, want, sec)] = (pair[0], "known pairing")
    for _, m in latin.values(): how[m] += 1
    print(dict(how))
    names = {h for _, _, h in tot}
    print(f"{len(names):,} Hebrew-script names · {len({k[0] for k in latin}):,} given a Latin spelling ({how['known pairing']:,} known pairings, {how['verified reading']:,} verified readings)")
    by = collections.defaultdict(lambda: [0, 0, 0, 0])
    with open(os.path.join(RAW, "il-latin.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh); w.writerow(["name", "sex", "count", "hebrew", "community", "how"])
        for (sec, sx, h), c in sorted(tot.items(), key=lambda kv: -kv[1]):
            want = "m" if sx == "M" else "f"
            by[sec][1] += c; by[sec][3] += 1
            if (h, want, sec) not in latin: continue
            by[sec][0] += c; by[sec][2] += 1
            w.writerow([latin[(h, want, sec)][0], want, c, h, sec, latin[(h, want, sec)][1]])
    for sec, (hit, all_, nh, nall) in by.items(): print(f"  {sec:15} {nh}/{nall} names · {hit / all_:.0%} of babies")

    # Hebrew names: from Jewish families, and either Hebrew by origin (a native-Hebrew pairing, the Bible, the usual
    # Israeli spelling) or mostly given in Israel (at least 30% of everyone with that name worldwide)
    he = collections.defaultdict(lambda: {"c": 0, "f": 0, "m": 0, "h": collections.Counter(), "how": ""})
    for (sec, sx, h), c in tot.items():
        want = "m" if sx == "M" else "f"
        if sec not in JEWISH_ONLY or (h, want, sec) not in latin: continue
        n, how_ = latin[(h, want, sec)]
        e = he[n]; e["c"] += c; e[want] += c; e["h"][h] += c
        if how_ != "verified reading" or not e["how"]: e["how"] = how_
    native = {h for h, (en, kind) in pairs.items() if kind in ("native", "bible")} | set(USUAL)   # Hebrew by origin (not just spelled in Hebrew)
    rows = []
    for n, e in he.items():
        hebrew = e["h"].most_common(1)[0][0]
        world = count.get(n.lower(), (e["c"],))[0]
        if not (hebrew in native or e["c"] >= .3 * world): continue
        g = "e" if min(e["f"], e["m"]) >= .2 * e["c"] else "g" if e["f"] > e["m"] else "b"
        origin = "Hebrew" if hebrew in native else "Israeli"      # Hebrew by origin, or simply mostly given in Israel
        rows.append([n, g, origin, "Hebrew" if origin == "Hebrew" else "", "", "", f"Given to {e['c']:,} babies in Israel since 1948. In Hebrew: {hebrew}.", ""])
    rows.sort(key=lambda r: r[0])
    json.dump(rows, open(os.path.join(ROOT, "data", "hebrew-names.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(rows):,} Hebrew names → data/hebrew-names.json")
