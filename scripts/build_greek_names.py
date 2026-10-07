# Greek names, ancient and mythological → data/greek-names.json, data/greek-names.tsv, data/sacred/greek.tsv
#
#   LGPN (Lexicon of Greek Personal Names, Oxford; CC BY 4.0): the list of ~39,700 attested name forms with the sex
#     and number of their bearers, as published in LGPN-Ling's data (lgpn-ling.huma-num.fr, taxonomies/names.xml).
#   Smith, Dictionary of Greek and Roman Biography and Mythology (1849; public domain), Perseus TEI edition
#     (PerseusDL/canonical-pdlrefwk, CC BY-SA 4.0): headwords with their Greek form.
#   Perseus canonical-greekLit (CC BY-SA 4.0) Greek texts: Hesiod, Homer, Homeric Hymns, Apollonius, Apollodorus,
#     Aeschylus, Sophocles, Euripides, Herodotus. Names are found by matching known name forms (LGPN, Smith, Hesiod's
#     catalogues) with their usual case endings against capitalised words; never by capitalisation alone.
#   Hesiod's catalogues (Muses, Titans, Nereids, Oceanids) are read straight from the Theogony's lines.
#   Ease (1 = spelled as an English speaker would write it, 2 = easy in a stated modern spelling, 3 = hard) is decided
#     by rules below; "in English records" means the spelling is in data/names-db.tsv for the US, UK, Ireland,
#     Northern Ireland, Canada or Australia.
#
#   python3 scripts/build_greek_names.py         (downloads into raw/greek/ once, then works offline)
import collections, json, math, os, re, time, unicodedata, urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "raw", "greek"); WORLD = os.path.join(ROOT, "raw", "sacred", "world", "perseus")
UA = {"User-Agent": "Lullabyte/1.0 (https://github.com/suhxnitiwari/baby-name-maker; suhxnitiwari@gmail.com)"}
TEI = "{http://www.tei-c.org/ns/1.0}"
GREEKLIT = "https://raw.githubusercontent.com/PerseusDL/canonical-greekLit/master/data/"
SCAIFE = "https://scaife.perseus.org/reader/urn:cts:greekLit:{urn}:{ref}/"


def get(url, rel):
    path = os.path.join(RAW, rel)
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300).read()
        open(path, "wb").write(data); time.sleep(1)
    return path


# ── Greek spelling helpers ──
def bare(s):
    """accent-free lowercase key: Ἰάνθη → ιανθη (final sigma folded)"""
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()
    return s.replace("ς", "σ")


def key(s):
    """matching key: Ionic -η and Attic -α of a feminine name count as one (Οὐρανίη = Οὐρανία)"""
    b = bare(s)
    return b[:-1] + "α" if b.endswith("η") else b


LETTERS = dict(zip("αβγδεζηθικλμνξοπρστυφχψω", "a b g d e z e th i c l m n x o p r s t y ph ch ps o".split()))
STRICT = dict(zip("αβγδεζηθικλμνξοπρστυφχψω", "a b g d e z ē th i k l m n x o p r s t y ph kh ps ō".split()))


def latin(gr, strict=False, ei_i=False):
    """the conventional Latin spelling (Ἀχιλλεύς → Achilleus, Περικλῆς → Pericles), or the strict one"""
    nfd = unicodedata.normalize("NFD", gr.strip())
    rough = "\u0314" in nfd[:3]
    s, out = "", []
    for c in nfd:                                    # keep a diaeresis as a marker so Κλεΐς is Cle-is, not a diphthong
        if c == "\u0308": s = s[:-1] + "¨" + s[-1:]
        elif unicodedata.category(c) != "Mn": s += c
    s = s.lower().replace("ς", "σ")
    if not re.fullmatch(r"[α-ω¨]+", s): return ""
    ending_on = s.endswith("ον")
    if strict:
        s = s.replace("ου", "ou").replace("γγ", "ng").replace("γκ", "nk").replace("γχ", "nkh")
        r = "".join(STRICT.get(c, c) for c in s).replace("¨", "")
        r = re.sub(r"(?<=[aeiouēō])y", "u", r)
        if rough: r = ("rh" + r[1:]) if r.startswith("r") else "h" + r
        return r[:1].upper() + r[1:]
    s = s.replace("ου", "u").replace("αι", "ae").replace("οι", "oe")
    s = s.replace("ει", "i") if ei_i else re.sub(r"ει(?=[αεηιουω])", "e", s).replace("ει", "i")
    s = s.replace("αυ", "au").replace("ευ", "eu").replace("ηυ", "eu")
    s = s.replace("γγ", "ng").replace("γκ", "nc").replace("γξ", "nx").replace("γχ", "nch").replace("ρρ", "rrh")
    r = "".join(LETTERS.get(c, c) for c in s).replace("¨", "")
    if r.startswith("r"): r = "rh" + r[1:]
    elif rough: r = "h" + r
    if r.endswith("os"): r = r[:-2] + "us"
    if ending_on: r = r[:-2] + "um"
    r = re.sub(r"(nd|c)rus$", r"\1er", r)          # Ἀλέξανδρος → Alexander, Τεῦκρος → Teucer
    return r[:1].upper() + r[1:]


def gram_sex(gr):
    """the sex the Greek ending marks (-ος/-ης/-ευς/-ας/-ων masculine; -η/-α/-ω feminine), else ''"""
    b = bare(gr)
    if b.endswith(("οσ", "ησ", "ευσ", "ασ", "ων")): return "b"
    if b.endswith(("η", "α", "ω")): return "g"
    return ""


# case endings, so Θείαν / Ἀχιλῆος / Ἑλένης are found as Theia / Achilles / Helen
ENDINGS = [("ευσ", "ευσ εωσ ηοσ εοσ ει ηι εα ηα ευ"), ("οσ", "οσ ου οιο οο ω ον ε"),
           ("ησ", "ησ ου εω η ην α αο ουσ ει εοσ εσ"), ("ασ", "ασ ου α αν αο εω"), ("ισ", "ισ ιδοσ ιδι ιδα ιν ιοσ ει εωσ"),
           ("ων", "ων ωνοσ ωνι ωνα ονοσ ονι ονα οντοσ οντι οντα ον"), ("η", "η ησ ην α ασ αν"), ("α", "α ασ αν ησ η ην"),
           ("ω", "ω ουσ οι ον"), ("ξ", "ξ κοσ κι κα γοσ γι γα"), ("ψ", "ψ ποσ πι πα βοσ βι βα")]


def forms(gr):
    b = bare(gr)
    for end, alts in ENDINGS:
        if b.endswith(end) and len(b) - len(end) >= 3:
            return {b[:-len(end)] + a for a in alts.split()}
    return {b}


WORD = re.compile(r"[\u0370-\u03ff\u1f00-\u1fff]+")


# ── texts ──
class Seg:
    __slots__ = ("corpus", "text", "passage", "url", "content")
    def __init__(self, corpus, text, passage, url, content):
        self.corpus, self.text, self.passage, self.url, self.content = corpus, text, passage, url, content


def tei_segments(path, corpus, label, urn, work_title):
    """verse: one segment per line (book.line or line); prose: one per section (book.chapter.section)"""
    root = ET.parse(path).getroot(); body = root.find(f".//{TEI}body"); segs = []

    def clean(el):
        for n in el.iter(f"{TEI}note"):
            n.text = ""; [n.remove(x) for x in list(n)]
        return " ".join("".join(el.itertext()).split())

    def walk(el, refs):
        for ch in el:
            tag = ch.tag.replace(TEI, "")
            if tag == "div" and ch.get("type") == "textpart":
                sub = (ch.get("subtype") or "").lower()
                if sub in ("book", "chapter", "section", "poem"):
                    r = refs + [ch.get("n")]
                    if sub == "section" or (sub == "chapter" and not ch.findall(f"{TEI}div")):
                        txt = clean(ch)
                        if txt: segs.append(Seg(corpus, work_title, f"{label} {'.'.join(r)}", SCAIFE.format(urn=urn, ref=".".join(r)), txt))
                        continue
                    walk(ch, r); continue
                walk(ch, refs)
            elif tag == "l" and ch.get("n"):
                r = refs + [ch.get("n")]
                segs.append(Seg(corpus, work_title, f"{label} {'.'.join(r)}", SCAIFE.format(urn=urn, ref=".".join(r)), clean(ch)))
            else:
                walk(ch, refs)
    walk(body, [])
    return segs


HYMNS = {1: "To Dionysus", 2: "To Demeter", 3: "To Apollo", 4: "To Hermes", 5: "To Aphrodite", 6: "To Aphrodite", 7: "To Dionysus",
         8: "To Ares", 9: "To Artemis", 10: "To Aphrodite", 11: "To Athena", 12: "To Hera", 13: "To Demeter", 14: "To the Mother of the Gods",
         15: "To Heracles", 16: "To Asclepius", 17: "To the Dioscuri", 18: "To Hermes", 19: "To Pan", 20: "To Hephaestus", 21: "To Apollo",
         22: "To Poseidon", 23: "To Zeus", 24: "To Hestia", 25: "To the Muses and Apollo", 26: "To Dionysus", 27: "To Artemis",
         28: "To Athena", 29: "To Hestia", 30: "To Earth", 31: "To Helios", 32: "To Selene", 33: "To the Dioscuri"}
PLAYS = {"tlg0085": ("Aeschylus", ["Suppliants", "Persians", "Prometheus Bound", "Seven against Thebes", "Agamemnon", "Libation Bearers", "Eumenides"]),
         "tlg0011": ("Sophocles", ["Trachiniae", "Antigone", "Ajax", "Oedipus Tyrannus", "Electra", "Philoctetes", "Oedipus at Colonus"]),
         "tlg0006": ("Euripides", ["Cyclops", "Alcestis", "Medea", "Heracleidae", "Hippolytus", "Andromache", "Hecuba", "Suppliants", "Heracles", "Ion",
                                   "Trojan Women", "Electra", "Iphigenia in Tauris", "Helen", "Phoenissae", "Orestes", "Bacchae", "Iphigenia in Aulis", "Rhesus"])}


def perseus(author, work, where=None):
    rel = f"perseus/{author}.{work}.perseus-grc2.xml"
    if where and os.path.exists(os.path.join(where, f"{author}.{work}.perseus-grc2.xml")):
        return os.path.join(where, f"{author}.{work}.perseus-grc2.xml")
    return get(f"{GREEKLIT}{author}/{work}/{author}.{work}.perseus-grc2.xml", rel)


def corpora():
    """(corpus, sacred?) → segments, in the order a card should cite them"""
    out = []
    def add(corpus, author, work, label, title, sacred=True):
        p = perseus(author, work, WORLD)
        out.append((corpus, sacred, tei_segments(p, corpus, label, f"{author}.{work}.perseus-grc2", title)))
    add("Theogony", "tlg0020", "tlg001", "Theogony", "Theogony")
    add("Iliad", "tlg0012", "tlg001", "Iliad", "Iliad")
    add("Odyssey", "tlg0012", "tlg002", "Odyssey", "Odyssey")
    add("Works and Days", "tlg0020", "tlg002", "Works and Days", "Works and Days")
    add("Shield of Heracles", "tlg0020", "tlg003", "Shield", "Shield of Heracles")
    hymns = []
    for i in range(1, 34):
        p = perseus("tlg0013", f"tlg{i:03d}", WORLD)
        hymns += tei_segments(p, "Homeric Hymns", f"Homeric Hymn {i}.", f"tlg0013.tlg{i:03d}.perseus-grc2", f"Hymn {i} ({HYMNS[i]})")
    for s in hymns: s.passage = s.passage.replace(". ", ".")
    out.append(("Homeric Hymns", True, hymns))
    add("Argonautica", "tlg0001", "tlg001", "Argonautica", "Argonautica")
    add("Bibliotheca", "tlg0548", "tlg001", "Apollodorus", "Bibliotheca")
    for author, (who, titles) in PLAYS.items():
        segs = []
        for i, t in enumerate(titles, 1):
            segs += tei_segments(perseus(author, f"tlg{i:03d}"), who, t, f"{author}.tlg{i:03d}.perseus-grc2", t)
        out.append((who, True, segs))
    add("Herodotus", "tlg0016", "tlg001", "Herodotus", "Histories", sacred=False)
    return out


# ── sources ──
def load_lgpn():
    p = os.path.join(RAW, "lgpn", "tax-names.xml")
    if not os.path.exists(p):
        get("https://lgpn-ling.huma-num.fr/exist/rest/db/apps/lgpn-ling-data/data/taxonomies/names.xml", "lgpn/tax-names.xml")
    out = {}
    for blk in re.findall(r"(?s)<name>(.*?)</name>", open(p, encoding="utf-8").read()):
        m = re.search(r"<nameform[^>]*>([^<]+)</nameform>", blk)
        if not m: continue
        gr = unicodedata.normalize("NFC", m.group(1).strip())
        if not re.fullmatch(r"[\u0370-\u03ff\u1f00-\u1fff]+", gr): continue      # skip partial / bracketed forms
        n = int((re.search(r"<attestations>(\d+)", blk) or [0, 0])[1])
        gs = set(re.findall(r"<gender>(\d)</gender>", blk))
        per = re.search(r'<period from="(-?\d+)" to="(-?\d+)"', blk)
        out[gr] = {"n": n, "sex": {"1": "b", "2": "g"}.get(gs.pop()) if len(gs) == 1 else ("mixed" if gs else ""),
                   "period": (int(per[1]), int(per[2])) if per else None}
    return out


NATION = [(r"Massaget", "Massagetan"), (r"\bScythian|\bof the Scythians", "Scythian"), (r"\b(?:a|the) Persian\b(?! (?:war|wars|fleet|army|invasion|empire|court|king))|\bking of Persia|(?:wife|daughter|mother|sister|son) of (?:Xerxes|Dareius|Darius|Artaxerxes|Cyrus|Cambyses)", "Persian"),
          (r"\bMede\b|\bMedian\b|\bof the Medes", "Median"), (r"\bEgyptian|\bking of Egypt", "Egyptian"), (r"\bLydian|\bking of Lydia", "Lydian"),
          (r"\bCarian|\bof Caria\b", "Carian"), (r"\bThracian|\bof Thrace|\bof the Odrysae", "Thracian"), (r"\bCarthaginian", "Carthaginian"),
          (r"\bPhoenician|\bof Tyre\b|\bof Sidon\b", "Phoenician"), (r"\bJewish|\bthe Jews\b|\ba Jew\b", "Jewish"), (r"\bRoman\b", "Roman"),
          (r"\bBabylonian", "Babylonian"), (r"\bAssyrian", "Assyrian"), (r"\bParthian", "Parthian"), (r"\bArmenian", "Armenian"),
          (r"\bIllyrian", "Illyrian"), (r"\bPhrygian", "Phrygian"), (r"\bLycian", "Lycian"), (r"\bEthiopian", "Ethiopian"), (r"\bArabian", "Arabian"),
          (r"\bIndian king|\bking of the Indians", "Indian"), (r"\bCeltic|\bGaul", "Gaulish"), (r"\bEtruscan", "Etruscan")]
DEITY_WORDS = r"\b(goddess(?:es)?|gods?|nymphs?|Nereids?|Oceanids?|Muses?|Titans?|Titaness|divinity|divinities|deity|deities|personification|personified|Hesperides|Pleiades|Charites|Horae|Naiads?|Dryads?)\b"
MYTH_CITES = r"\b(Hom|Il|Od|Hes|Theog|Apollod|Hyg|Hygin|Ov|Pind|Eurip|Soph|Aeschyl|Serv|Tzetz|Apollon|Nonn|Lycophr)\b"
HIST = r"B\. ?C\.|A\. ?D\.|\bOl\. ?\d|Olymp\.|\barchon\b|\bhistorian\b|\bphilosoph\w*|\bmathemati\w*|\bChristian\b|\bof Alexandria\b|\bNeoplaton\w*|\bsculptor\b|\bpainter\b|\borator\b|\bphysician\b|\bgrammarian\b|\btyrant of\b|\bgeneral\b|\bstatesman\b|\bpoet(?:ess)?\b|\bsophist\b|\bbishop\b|\bemperor\b|\bsatrap\b|\bAthenian\b|\bSpartan\b|\bLacedaemonian\b"
FEM_WORDS = r"\b(daughter|wife|mother|sister|she|her|nymph|goddess|queen|priestess|heroine|maiden|woman|poetess|mistress|hetaera)\b"
HIST_CITES = r"\b(Socr|Suid|Philostorg|Synes|Damasc|Eunap|Procop|Zosim|Amm|Plut|Thuc|Xen|Diod|Polyb|Arrian|Arr|Hdt|Herod|Dem|Aeschin|Isocr|Cic|Liv|Just|Nep|Diog|Paus\. \d+\.\d+\.\d+ ; Plut|Joseph|Euseb|Phot)\b"
MASC_WORDS = r"\b(son|king|he|his|father|brother|husband|man|hero|god|priest)\b"


def text_of(xml):
    return " ".join(re.sub(r"<[^>]+>", " ", xml).split())


def load_smith():
    p = os.path.join(RAW, "perseus", "smith-dgrbm.xml")
    if not os.path.exists(p):
        get("https://raw.githubusercontent.com/PerseusDL/canonical-pdlrefwk/master/data/viaf88890045/003/viaf88890045.003.perseus-eng1.xml", "perseus/smith-dgrbm.xml")
    raw = open(p, encoding="utf-8").read()
    entries = []
    for chunk in re.split(r'<div type="textpart" subtype="entry"', raw)[1:]:
        idm = re.match(r'[^>]*xml:id="([^"]+)"', chunk)
        head = re.search(r"(?s)<head>(.*?)</head>", chunk)
        if not idm or not head: continue
        hw = unicodedata.normalize("NFC", text_of(head.group(1)).replace("'", "").replace("’", "").strip(" .,"))
        hw = re.sub(r"\s+[IVX]+\.?$", "", re.split(r"\s+or\s+", hw)[0])     # "Leonidas I." → Leonidas; "GALATEIA or GALATIA" → Galateia
        if hw.isupper(): hw = hw.title()
        if not re.fullmatch(r"[A-Z][a-z]+", hw): continue        # one-word headwords only (Roman multi-part names drop out)
        body = chunk[head.end():]
        # the Greek spellings in the opening parenthesis, if they spell the headword (not words quoted later on)
        win = body[:min(450, body.find("<bibl") if "<bibl" in body else 450)]
        grs = [unicodedata.normalize("NFC", text_of(g)).strip(" ,.;") for g in re.findall(r'(?s)<(?:label|persName|foreign)[^>]*xml:lang="grc"[^>]*>(.*?)</(?:label|persName|foreign)>', win)]
        fold2 = lambda t: re.sub(r"^h", "", t.lower().replace("k", "c").replace("v", "u"))[:2]
        grs = [g for g in grs if g[:1].isupper() and fold2(latin(g)) == fold2(hw)]
        grs = [g for g in grs if re.fullmatch(r"[\u0370-\u03ff\u1f00-\u1fff]+", g)]
        if not grs: continue
        txt = text_of(body if idm.group(1) == "sappho-bio-1" else body[:6000])
        lead = re.sub(r"^\([^()]{0,60}\)[.,]?\s*|^\(", "", txt)[:400]
        hist = bool(re.search(HIST, lead[:300], re.I))
        myth = bool(re.search(MYTH_CITES, txt[:1500]))
        rel = re.search(r"\b(son|daughter|wife|mother|father) of\b", lead[:200])
        dw = re.search(DEITY_WORDS, lead[:200])
        if re.search(r"B\. ?C\.|A\. ?D\.|Olymp\.|\bOl\. ?\d", lead[:300]): kind = "PERSON"
        elif dw and (not rel or dw.start() < rel.start()) or re.search(r"one of the (?:female )?(?:Titans|Nereids|Oceanids|Muses|Pleiades|Hesperides|Horae|Charites|Graces|nymphs)", lead[:250]): kind = "DEITY"
        else:                                           # myth or history: whose books the article cites more
            mc = len(re.findall(MYTH_CITES, txt[:4000])); hc = len(re.findall(HIST_CITES, txt[:4000]))
            starts_myth = re.match(r"(?:An? |The )?(?:daughter|son|wife|sister|brother) of\b|See [A-Z]", lead, re.I)
            if re.search(HIST, lead[:120], re.I): kind = "PERSON"
            elif starts_myth and mc >= hc: kind = "MYTHIC"
            elif hc > mc: kind = "PERSON"
            elif mc or rel: kind = "MYTHIC"
            else: kind = "PERSON"
        nation = ""
        if kind == "PERSON":
            for rx, c in NATION:
                if re.search(rx, lead[:220]): nation = c; break
        g = gram_sex(grs[0])
        if not g:                                       # -ις, -ξ …: what the article says (a daughter, a king)
            f, m = len(re.findall(FEM_WORDS, lead[:200], re.I)), len(re.findall(MASC_WORDS, lead[:200], re.I))
            g = "g" if f > m else "b" if m > f else ""
        sents = re.split(r"(?<=[a-z\)])\. (?=[A-Z0-9])", re.sub(r"^\d+\.\s*", "", lead))
        role = sents[1] if len(sents) > 1 and (re.fullmatch(r"\W*\w+\W*", sents[0]) or sents[0].startswith("See ")) else sents[0]   # skip "Historical." / "See ACRISIUS."
        role = re.sub(r"^\d+\.\s*", "", role)
        role = re.sub(r"^(?:" + WORD.pattern + r"[\s,;:)]*)+", "", role)            # "Φαίδων a Greek philosopher" → "a Greek philosopher"
        role = re.sub(r"\s*\[[^\]]*\]|\s*\([^)]*\)", "", role)
        role = re.sub(r"\s*[\(\[].*$", "", role).strip(" ,;:")[:140]
        entries.append({"id": idm.group(1), "hw": hw, "gr": grs, "kind": kind, "nation": nation, "g": g, "role": role, "text": txt, "size": len(body)})
    return entries


def catalogues(texts):
    """the poets' lists of goddesses: Hesiod's Muses (Theogony 77-79), Titans (133-137), Nereids (243-262) and Oceanids
    (349-361); Homer's Nereids (Iliad 18.39-48); Apollodorus' Nereids (1.2.7, after "their names are")"""
    by = {c: {s.passage: s for s in segs} for c, _, segs in texts}
    NER, OCE = "a Nereid, daughter of Nereus and Doris", "an Oceanid, daughter of Oceanus and Tethys"
    spec = [("Theogony", [f"Theogony {n}" for n in range(77, 80)], "", "Muse", "a Muse, daughter of Zeus", "g"),
            ("Theogony", [f"Theogony {n}" for n in range(133, 138)], "", "Titan", "a Titan, child of Uranus and Gaia", ""),
            ("Theogony", [f"Theogony {n}" for n in range(243, 263)], "", "Nereid", NER, "g"),
            ("Theogony", [f"Theogony {n}" for n in range(349, 362)], "", "Oceanid", OCE, "g"),
            ("Iliad", [f"Iliad 18.{n}" for n in range(39, 49)], "", "Nereid", NER, "g"),
            ("Bibliotheca", ["Apollodorus 1.2.7"], "ὀνόματα", "Nereid", NER, "g")]
    out = []
    for corpus, passages, after, cat, role, sex in spec:
        for ps in passages:
            s = by[corpus][ps]; txt = s.content.split(after, 1)[1] if after else s.content
            for w in WORD.findall(txt):
                if w[0].isupper() and w not in ("Διὸς", "Νηρηΐδες"):
                    out.append({"gr": w, "cat": cat, "role": role, "sex": sex, "seg": s, "corpus": corpus})
    return out


# ── ease ──
EN_CODES = {"us", "uk", "au", "ca", "ie", "nir"}
def english_names():
    out = {}
    for line in open(os.path.join(ROOT, "data", "names-db.tsv"), encoding="utf-8"):
        p = line.rstrip("\n").split("\t")
        if len(p) >= 4 and EN_CODES & set(p[2].split(",")):
            k = p[0].lower(); out[k] = out.get(k, 0) + int(p[3] or 0)
    return out


DICT = [w.strip() for w in open("/usr/share/dict/words")] if os.path.exists("/usr/share/dict/words") else []
WORDS = {w for w in DICT if w.islower()}                       # English words (hippo, pan)
PROPER = {w.lower() for w in DICT if w[:1].isupper()}           # English proper names, mostly places (Sparta, Crete, Asia)
OK_CLUSTERS = {"tth", "nth", "ndr", "str", "ntr", "chr", "phr", "thr", "mpl", "mbr", "ngr", "rth", "lph", "rph", "sth", "nch", "rch", "lth", "mph", "sch", "nst", "rst"}


def plain(n, longest=9):
    l = n.lower()
    if not re.fullmatch(r"[a-z]+", l) or not 3 <= len(l) <= longest: return False
    if len(re.findall(r"[aeiouy]+", l)) > 4: return False
    if re.search(r"phth|chth|rrh|ae|oe|ii|yy|uu|aa|hh|tl|dm|cn|^(?:ps|pt|mn|gn|x|z)|[^aeiou]{2}h[^aeiou]|y[aeiou]|[aeiou]y[aeiou]|(?<=[aeiou])u(?=[aeiou])", l): return False
    for m in re.finditer(r"[^aeiouy]{3,}", l):
        if m.group(0) not in OK_CLUSTERS: return False
    if re.search(r"[^aeiouy]{2}$", l) and not re.search(r"(nd|nt|st|rd|rt|ld|lt|rn|ss|ll|th|ch|ph|ns|ks|ps|x)$", l): return False
    return True


def ease_of(n, EN):
    """(ease, modern spelling or '')"""
    l = n.lower()
    if (l in WORDS or l in PROPER) and l not in EN: return 3, ""      # an English word or place first (Hippo, Sparta)
    if l in EN: return 1, ""
    if re.search(r"c[eiy]", l):                                        # Cleis reads "Sleece": the K spelling keeps the Greek sound
        k = re.sub(r"c(?=[eiy])", "k", n)
        k = k[0].upper() + k[1:]
        if k.lower() in EN or plain(k): return 2, k
    if plain(n): return 1, ""
    if plain(n, 11) or re.match(r"[XZ]", n) and plain("S" + n[1:], 11): return 2, n
    for a, b in (("ae", "e"), ("oe", "e"), ("ei", "i"), ("us", "os"), ("ch", "k")):
        alt = n.replace(a, b) if a != "us" else re.sub(r"us$", "os", n)
        if alt != n and (alt.lower() in EN or plain(alt)): return 2, alt
    return 3, ""


def english_form(L, EN):
    """the spelling English speakers already use for this Latin form (Cleio → Clio, Galateia → Galatea, Uranie → Urania)"""
    if L.lower() in EN: return L
    alts = [re.sub(r"^Eu(?=[aeiou])", "Ev", L), re.sub(r"eia$", "ea", L), L.replace("ei", "i"), re.sub(r"ie$", "ia", L), re.sub(r"ie$", "ia", L).replace("ei", "i"), L.replace("ae", "e")]
    for a in alts:
        if a != L and a.lower() in EN: return a
    return L


# ── build ──
MEAN = json.load(open(os.path.join(ROOT, "data", "meanings.json"), encoding="utf-8"))
FOREIGN_ROOTS = {"Hebrew": "Hebrew", "Biblical Hebrew": "Hebrew", "Aramaic": "Aramaic", "Latin": "Roman", "Arabic": "Arabic", "Persian": "Persian",
                 "Old Persian": "Persian", "Egyptian": "Egyptian", "Coptic": "Egyptian", "Phoenician": "Phoenician", "Akkadian": "Mesopotamian"}
S_TIER = {"g": "Asteria Astraea Ianthe Ione Iole Ismene Evadne Melia Maia Theia Dione Thalia Eudora Cyrene Larissa Ariadne Phaedra Danae Anactoria Atthis Cleis Galatea Eunice Clio Harmonia Coronis Psamathe Tecmessa Alcestis Polyxena".split(),
          "b": "Evander Leander Lysander Damon Orion Atlas Dorian Theron Solon Xanthus Phaedo Meno Lysis Crito Nicias Leonidas Miltiades Pericles".split()}
PRIORITY = {"DEITY": 0, "MYTHIC": 1, "POET-SUBJECT": 2, "PERSON": 3}


def main():
    EN = english_names()
    lgpn = load_lgpn(); smith = load_smith(); texts = corpora()
    print(f"LGPN {len(lgpn):,} forms · Smith {len(smith):,} Greek headwords · texts {sum(len(s) for _, _, s in texts):,} segments")

    recs = {}                                         # Greek key → record
    def rec(gr):
        k = key(gr)
        r = recs.get(k)
        if not r:
            r = recs[k] = {"gr": [], "names": [], "kinds": set(), "sex": set(), "roles": [], "src": [], "lgpn": 0, "period": None, "sxl": set(), "sxs": set(), "sxc": set(), "sxn": {},
                           "nation": "", "smith": [], "cats": [], "texts": collections.OrderedDict(), "sappho": ""}
        if gr not in r["gr"]: r["gr"].append(gr)
        return r

    for gr, x in lgpn.items():
        r = rec(gr); r["lgpn"] += x["n"]; r["kinds"].add("PERSON")
        sx = gram_sex(gr) if x["sex"] == "mixed" else x["sex"]
        if sx: r["sxn"][sx] = r["sxn"].get(sx, 0) + max(1, x["n"])
        if x["period"]: r["period"] = x["period"]
    smith_roman = set()
    for e in smith:
        if e["nation"] == "Roman": smith_roman.add(e["hw"])
        r = rec(e["gr"][0])
        for g in e["gr"][1:]:
            if g not in r["gr"]: r["gr"].append(g)
        r["smith"].append(e); r["names"].append(e["hw"]); r["kinds"].add(e["kind"])
        if e["g"]: r["sxs"].add(e["g"])
        if e["nation"] and not r["nation"]: r["nation"] = e["nation"]
    formkey = {}
    for k, r in recs.items():
        for g in r["gr"]:
            for f in forms(g): formkey.setdefault(f, k)
    for c in catalogues(texts):
        r = recs.get(key(c["gr"])) or recs.get(formkey.get(bare(c["gr"]), ""))
        if not r:
            if not bare(c["gr"]).endswith(("η", "α", "ω", "ισ")): continue        # an oblique case of a name we don't know
            r = rec(c["gr"])
        if c["seg"].passage not in [x[1].passage for x in r["cats"]]:
            r["cats"].append((c, c["seg"]))
        r["kinds"].add("DEITY")
        if c["sex"]: r["sxc"].add(c["sex"])
    # Sappho's circle, as Smith's article on Sappho names it
    sap = next((e for e in smith if e["id"] == "sappho-bio-1"), None)
    if sap:
        t = sap["text"]; circle = {}
        m = re.search(r"daughter named (\w+)", t); circle[m.group(1)] = "her daughter" if m else None
        m = re.search(r"companions, are ([^.]+)\.", t)
        if m:
            for part in re.split(r",\s*(?:and\s+)?|\s+and\s+", m.group(1)): circle[part.split()[0]] = "one of her companions"
        m = re.search(r"Those of them who obtained[^.]*?were, (\w+) the \w+, and (\w+) of", t)
        if m:
            for w in m.groups(): circle[w.title()] = "one of her pupils, a poet herself"
        m = re.search(r"Among these (\w+) and (\w+), especially", t)
        if m:
            for w in m.groups(): circle[w] = "a rival she names in her poems"
        by_latin = {}
        for k, r in recs.items():
            for g in r["gr"]: by_latin.setdefault(latin(g), []).append(r)
        for name, role in circle.items():
            if not role: continue
            cands = by_latin.get(name) or []
            cands = [r for r in cands if "g" in r["sxl"] | r["sxs"] or not r["sxl"] | r["sxs"]] or cands
            if cands: r = max(cands, key=lambda r: r["lgpn"])
            else:
                r = recs.setdefault("latin:" + name, {"gr": [], "names": [name], "kinds": set(), "sex": set(), "roles": [], "src": [], "lgpn": 0, "period": None, "sxl": set(), "sxs": set(), "sxc": set(), "sxn": {},
                                                     "nation": "", "smith": [], "cats": [], "texts": collections.OrderedDict(), "sappho": ""})
            r["kinds"].add("POET-SUBJECT"); r["sappho"] = role; r["sxc"] = {"g"}
            if name not in r["names"]: r["names"].insert(0, name)

    # find each name in the texts (mythic figures in the sacred corpora; everyone in Herodotus)
    index = collections.defaultdict(set)
    for k, r in recs.items():
        if not r["gr"]: continue
        if not (r["kinds"] & {"DEITY", "MYTHIC", "POET-SUBJECT"}) and r["lgpn"] < 5 and not r["smith"]: continue
        for g in r["gr"]:
            for f in forms(g): index[f].add(k)
    for corpus, sacred, segs in texts:
        for s in segs:
            for w in WORD.findall(s.content):
                if not w[0].isupper(): continue
                for k in index.get(bare(w.replace("ʼ", "")), ()):
                    r = recs[k]
                    if not sacred and r["kinds"] & {"DEITY", "MYTHIC"} and "PERSON" not in r["kinds"]: continue
                    if sacred and not (r["kinds"] & {"DEITY", "MYTHIC"}): continue
                    t = r["texts"].setdefault(corpus, [s, 0, w]); t[1] += 1

    rows, sacred_rows = [], []
    for k, r in recs.items():
        if not r["gr"] and not r["names"]: continue
        gr = r["gr"][0] if r["gr"] else ""
        kinds = sorted(r["kinds"], key=PRIORITY.get)
        main = max(r["smith"], key=lambda e: e["size"]) if r["smith"] else None
        kind = "DEITY" if r["cats"] else "POET-SUBJECT" if r["sappho"] else main["kind"] if main else kinds[0]
        # display spelling: Smith's headword, else the Latin spelling (made English where English already spells it)
        L = (main["hw"] if main else "") or next((n for n in r["names"] if n), "") or latin(r["cats"][0][0]["gr"] if r["cats"] and bare(r["cats"][0][0]["gr"]) in forms(gr) and key(r["cats"][0][0]["gr"]) in [key(g) for g in r["gr"]] else gr)
        if r["sappho"] and not r["cats"] and not main: L = r["names"][0]
        if main: L = re.sub(r"(?<=[a-z]{3})eia$", "ea", L)                    # Galateia → Galatea, the Latin spelling
        if not L: continue
        L = english_form(L, EN)
        if L.lower() not in EN and gr and latin(gr, ei_i=True).lower() in EN: L = latin(gr, ei_i=True)   # Θάλεια → Thalia
        tot = sum(r["sxn"].values())                    # LGPN: the sex of at least 80% of the bearers, else either
        r["sxl"] = {next((k for k, v in r["sxn"].items() if v >= .8 * tot and k != "e"), "e")} if tot else set()
        if r["sxl"] == {"e"} and len(r["sxs"]) == 1: r["sxl"] = set()
        msx = {main["g"]} if main and main["g"] else set()
        sex = next((x - {""} for x in (r["sxc"], msx, r["sxl"], r["sxs"]) if x - {""}), set())   # catalogue > the figure Smith describes > LGPN
        g = "e" if {"g", "b"} <= sex or "e" in sex else (next(iter(sex)) if sex else gram_sex(gr))
        if not g: continue
        culture = r["nation"] if kind == "PERSON" and r["nation"] else "Greek"
        root = (MEAN.get(L.lower()) or {}).get("root", "")
        if kind == "PERSON" and not r["smith"] and root in FOREIGN_ROOTS:          # Esther, Marcus: borne by Greeks, not Greek
            culture = FOREIGN_ROOTS[root]
        if kind == "PERSON" and not r["smith"] and L in smith_roman: continue         # a Roman name written in Greek
        r["gr"].sort(key=lambda g: (latin(g).lower() != L.lower() and latin(g, ei_i=True).lower() != L.lower(), -lgpn.get(g, {}).get("n", 0)))
        gr = r["gr"][0] if r["gr"] else ""
        ease, modern = ease_of(L, EN)
        # believable on a child: an unfamiliar name needs a famous bearer or many real ones to count as easy
        known = bool(r["smith"] or r["cats"] or r["sappho"] or r["texts"])
        if ease == 1 and L.lower() not in EN and not known and r["lgpn"] < 20: ease = 2
        if ease == 2 and L.lower() not in EN and not known and r["lgpn"] < 3: ease = 3
        if L.endswith("um") or g == "g" and L.endswith(("us", "os")): ease = 3      # neuter Glycerium, a girl's -us
        strict = latin(gr, strict=True) if gr else ""
        # sources sentence
        bits = [f"Written {' / '.join(r['gr'][:3])}." if gr else ""]
        if strict and strict != L: bits.append(f"Strictly {strict}.")
        if modern and modern != L: bits.append(f"Modern spelling: {modern}.")
        cites = []
        for c, s in r["cats"][:1]:
            bits.append(f"{c['role'][0].upper() + c['role'][1:]} in {'Hesiod, ' if c['corpus'] == 'Theogony' else ''}{s.passage}.")
        if r["sappho"]: bits.append(f"Named by Smith's Dictionary (s.v. Sappho) as {r['sappho']}.")
        if r["smith"]:
            e = max(r["smith"], key=lambda e: e["size"])                  # the best-known namesake has the longest article
            if not r["cats"] and e["role"]: bits.append(f"{e['role'][0].upper() + e['role'][1:]} (Smith's Dictionary).")
            cites.append("Smith's Dictionary of Greek and Roman Biography and Mythology (1849)")
        firsts = [(c, t) for c, t in r["texts"].items()]
        if firsts:
            bits.append("In " + "; ".join(f"{t[0].passage}" for c, t in firsts[:3]) + ".")
        if r["lgpn"]:
            per = r["period"]
            span = f", {abs(per[0])} {'BC' if per[0] < 0 else 'AD'} to {abs(per[1])} {'BC' if per[1] < 0 else 'AD'}" if per and per[0] > -1000 and per[1] < 999 else ""
            bits.append(f"Borne by {r['lgpn']:,} {'person' if r['lgpn'] == 1 else 'people'} in the Lexicon of Greek Personal Names{span}.")
            cites.append("LGPN (CC BY 4.0)")
        if r["texts"]: cites.append("Perseus Digital Library (CC BY-SA 4.0)")
        if r["cats"] and "Perseus Digital Library (CC BY-SA 4.0)" not in cites: cites.append("Perseus Digital Library (CC BY-SA 4.0)")
        bits.append("Sources: " + "; ".join(cites) + "." if cites else "")
        src = " ".join(b for b in bits if b)
        language = "Ancient Greek"
        religions = "Greek religion" if kind in ("DEITY", "MYTHIC") else ""
        corp = ",".join(c for c in r["texts"])
        if r["cats"] and "Theogony" not in corp: corp = ",".join(x for x in ["Theogony", corp] if x)
        fame = len(r["texts"]) * 3 + len(r["smith"]) * 2 + (4 if r["cats"] else 0) + math.log10(1 + r["lgpn"]) + (5 if r["sappho"] else 0)
        rows.append({"name": L, "g": g, "culture": culture, "language": language, "religions": religions, "meaning": "", "src": src,
                     "texts": corp, "kind": kind, "ease": ease, "modern": modern, "gr": gr, "strict": strict, "lgpn": r["lgpn"], "fame": fame,
                     "sacred": r, "kinds": kinds})

    # one row per Latin name: merge
    merged = {}
    for x in sorted(rows, key=lambda x: (PRIORITY[x["kind"]], -x["fame"])):
        y = merged.get(x["name"].lower())
        if not y: merged[x["name"].lower()] = x; continue
        if x["gr"] and x["gr"] not in y["src"]: y["src"] = y["src"].replace("Written ", f"Written {x['gr']} / ", 1) if y["gr"] else y["src"]
        y["lgpn"] += x["lgpn"]; y["fame"] += x["fame"] / 2
        y["texts"] = ",".join(dict.fromkeys([t for t in (y["texts"] + "," + x["texts"]).split(",") if t]))
    out = list(merged.values())

    # her S-tier: find each, keep her spelling
    report = {}
    for g, names in S_TIER.items():
        for n in names:
            hit = merged.get(n.lower())
            if hit and hit["g"] not in (g, "e"): hit = None                # Κριτώ (a woman) is not her Crito
            if True:
                for x in out:
                    variants = {x["name"], re.sub(r"on$", "o", x["name"]), x["name"].replace("ei", "i"), re.sub(r"os$", "us", x["name"]),
                                re.sub(r"c(?=[eiy])", "k", x["name"]), x["modern"], re.sub(r"^Eu(?=[aeiou])", "Ev", x["name"]), latin(x["gr"], ei_i=True) if x["gr"] else ""}
                    if n in variants and (x["g"] in (g, "e")) and (hit is None or x["fame"] > hit["fame"]): hit = x
                if hit and hit["name"] != n:
                    note = f"{n} is the usual English spelling of {hit['name']}."
                    merged.pop(hit["name"].lower(), None)
                    clash = merged.pop(n.lower(), None)                          # a namesake row under her spelling gives way
                    if clash and clash["gr"]: note += f" {n} is also {'a woman' if clash['g'] == 'g' else 'a man'}'s name, {clash['gr']}."
                    hit["name"] = n; merged[n.lower()] = hit
                    hit["src"] = hit["src"].replace("Sources:", note + " Sources:", 1)
                    hit["ease"], hit["modern"] = ease_of(n, EN)
                elif hit:
                    merged[n.lower()] = hit
            if hit:
                hit["star"] = True
                if hit["ease"] == 3: hit["ease"] = 2; hit["modern"] = hit["modern"] or n
            report[n] = (hit["kind"], hit["g"], hit["ease"], hit["src"][:150]) if hit else None
    out = list(merged.values())
    # meanings, from Wiktionary only when its etymology is Greek (data/meanings.json; culture-names.json Greek rows)
    mean = json.load(open(os.path.join(ROOT, "data", "meanings.json"), encoding="utf-8"))
    cn = {r[0].lower(): r[5] for r in json.load(open(os.path.join(ROOT, "data", "culture-names.json"), encoding="utf-8")) if r[2] == "Greek" and r[5]}
    for x in out:
        m = mean.get(x["name"].lower())
        if m and m.get("m") and "Greek" in (m.get("root") or "") + (m.get("ety") or ""):
            x["meaning"] = m["m"]; x["src"] += " Meaning: Wiktionary (CC BY-SA 4.0)."

    order = {"g": 0, "e": 1, "b": 2}
    out.sort(key=lambda x: (x["ease"], order[x["g"]], not x.get("star"), -(x["fame"] + 2 * math.log10(1 + EN.get(x["name"].lower(), 0))), x["name"]))

    js = [[x["name"], x["g"], x["culture"], x["language"], x["religions"], x["meaning"], x["src"], x["texts"], x["kind"], [], x["ease"]]
          for x in out if x["ease"] <= 2]
    with open(os.path.join(ROOT, "data", "greek-names.json"), "w", encoding="utf-8") as f:
        f.write("[\n" + ",\n".join(json.dumps(r, ensure_ascii=False) for r in js) + "\n]\n")
    with open(os.path.join(ROOT, "data", "greek-names.tsv"), "w", encoding="utf-8") as f:
        f.write("name\tsex\tease\tmodern_spelling\tkind\tculture\tgreek\tstrict\tmeaning\tlgpn_bearers\ttexts\tsource\n")
        for x in out:
            f.write("\t".join(str(v) for v in (x["name"], x["g"], x["ease"], x["modern"], x["kind"], x["culture"], x["gr"], x["strict"],
                                                 x["meaning"], x["lgpn"], x["texts"], x["src"])) + "\n")

    # the sacred thread: mythic names in the mythic texts
    hdr = "name figure_id figure sex original translit language tradition subtradition corpus text passage url occurrences entity_type name_role status relation source confidence".split()
    srows = []
    for x in out:
        if x["kind"] not in ("DEITY", "MYTHIC"): continue
        r = x["sacred"]
        role = r["cats"][0][0]["role"] if r["cats"] else (max(r["smith"], key=lambda e: e["size"])["role"] if r["smith"] else "")
        cat = r["cats"][0][0]["cat"] if r["cats"] else ""
        et = "mythological_being" if cat in ("Nereid", "Oceanid") or re.search(r"\bnymph|Nereid|Oceanid", role) else ("deity" if x["kind"] == "DEITY" else "human")
        fig = f"{x['name']}, {role}" if role else x["name"]
        seen = set()
        for c, s in r["cats"][:1]:
            srows.append([x["name"], f"slug:greek:{x['name'].lower()}", fig, {"g": "girl", "b": "boy"}.get(x["g"], ""), c["gr"], x["strict"], "Greek",
                          "Greek religion", "", c["corpus"], s.text, s.passage, s.url, str(r["texts"].get(c["corpus"], [0, 0])[1] or ""), et, "personal", "attested", "",
                          f"Perseus Digital Library canonical-greekLit (CC BY-SA 4.0), {c['corpus']}, {c['cat']} catalogue", "0.95"])
            seen.add(c["corpus"])
        for corpus, (s, n, w) in r["texts"].items():
            if corpus in seen or corpus == "Herodotus": continue
            srows.append([x["name"], f"slug:greek:{x['name'].lower()}", fig, {"g": "girl", "b": "boy"}.get(x["g"], ""), w.replace("ʼ", ""), x["strict"], "Greek",
                          "Greek religion", "", corpus, s.text, s.passage, s.url, str(n), et, "personal", "attested", "",
                          f"Perseus Digital Library canonical-greekLit (CC BY-SA 4.0), {corpus}; name forms from LGPN / Smith's Dictionary", "0.8"])
    with open(os.path.join(ROOT, "data", "sacred", "greek.tsv"), "w", encoding="utf-8") as f:
        f.write("\t".join(hdr) + "\n")
        for r in srows: f.write("\t".join(v.replace("\t", " ") for v in r) + "\n")

    stats = {"all": len(out), "json": len(js), "sacred_rows": len(srows),
             "kind": collections.Counter(x["kind"] for x in out), "sex": collections.Counter(x["g"] for x in out),
             "ease": collections.Counter(x["ease"] for x in out), "json_kind": collections.Counter(r[8] for r in js),
             "json_sex": collections.Counter(r[1] for r in js), "json_ease": collections.Counter(r[10] for r in js),
             "culture": collections.Counter(x["culture"] for x in out if x["culture"] != "Greek").most_common(20)}
    for k, v in stats.items(): print(k, dict(v) if isinstance(v, collections.Counter) else v)
    print("S-tier:")
    for n, v in report.items(): print(" ", n, v)
    print("top 40:")
    for r in js[:40]: print(" ", r[0], r[1], r[8], r[10], "|", r[6][:110])


if __name__ == "__main__":
    main()
