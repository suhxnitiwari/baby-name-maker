#!/usr/bin/env python3
"""World religions and mythologies -> data/sacred/world.tsv (+ world-review.tsv). Format: docs/sacred-format.md.

Run:  python3 scripts/build_sacred_world.py            (fetches anything missing into raw/sacred/world/)
      python3 scripts/build_sacred_world.py --offline  (only use what is already there)
      python3 scripts/build_sacred_world.py --check    (print the matched line of every row, for spot checks)

How it works
  Every corpus is read from an open or public-domain edition and cut into citable segments (book.line,
  stanza, chapter, verse, page). For every corpus there is a hand-written list of figures: the name people
  write today, the English Wikipedia article (resolved to a Wikidata QID, sex P21 and description), and the
  name forms as they stand in the edition (nominative, which the matcher declines with that language's case
  endings, exact forms, or prefixes). A row is written only where the form is found in the text: the first
  segment that has it becomes the passage, and every match is counted. Nothing is copied from secondary
  lists; figures not found in the text are dropped (listed with --check).

  Names whose form is also a common word, or which the edition gives to several people, go to
  world-review.tsv. Rows from editions read in English translation keep the translator's spelling in
  `translit` and leave `original` blank; rows from OCR scans are cited by printed page.

Sources (and licences)
  Greek     Perseus canonical-greekLit (CC BY-SA 4.0): Iliad, Odyssey (Monro/Allen), Hesiod (Evelyn-White),
            Homeric Hymns. Orphic Hymns: Greek Wikisource, Abel 1885 edition (PD).
  Roman     Perseus canonical-latinLit (CC BY-SA 4.0): Aeneid, Metamorphoses, Fasti.
  Norse     heimskringla.no (Eddukvaedi and Volsunga saga, Gudni Jonsson's normalised text); Icelandic Wikisource
            (Snorra Edda, same edition). Medieval texts; credit to HEIMSKRINGLA requested.
  Persian   avesta.org (J. H. Peterson): Avestan text after Geldner 1896 (PD); West's SBE translations of the
            Bundahishn (1880) and Arda Viraf (Haug/West 1872) (PD). Shahnameh: ganjoor.net Persian text.
  Finnish   Kalevala, Lonnrot 1849, Project Gutenberg #7000 (PD).
  Georgian  Vepkhistkaosani (Rustaveli), Georgian Wikisource (PD text).
  Armenian  Sasna tsrer, Armenian Wikisource (compiled folk text; edition not stated -> review file only).
  Egyptian  Budge, The Papyrus of Ani (1895), archive.org scan (PD).
  Mesopot.  Thompson, The Epic of Gilgamish (1928); King, The Seven Tablets of Creation I (1902); archive.org (PD).
  Maya      Brasseur de Bourbourg, Popol Vuh (1861), K'iche' text with French, archive.org scan (PD).
  Yoruba    Ellis, The Yoruba-speaking Peoples of the Slave Coast (1894), archive.org scan (PD).
  Hawaiian  Kumulipo, Hawaiian text as printed with Beckwith 1951 line numbers (archive.org, marked PD);
            Emerson, Pele and Hiiaka (1915), Project Gutenberg #60279 (PD).
  Maori     Grey, Polynesian Mythology (1855), Standard Ebooks (PD).
  Arabian   Ibn al-Kalbi, Kitab al-Asnam, Arabic Wikisource (Ahmed Zaki Pasha 1914 edition, PD).
  Yazidi    Isya Joseph, Devil Worship: the Sacred Books and Traditions of the Yezidiz (1919), archive.org (PD).
  Rastafari The Holy Piby (Rogers 1924), archive.org (PD in the US).
  Wikidata  (CC0) for QIDs, sex and descriptions.
"""
import collections, difflib, gzip, html, json, os, re, sys, time, unicodedata, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw", "sacred", "world")
OUT = os.path.join(ROOT, "data", "sacred", "world.tsv")
REVIEW = os.path.join(ROOT, "data", "sacred", "world-review.tsv")
ASIDE = {os.path.join(ROOT, "raw", "sacred", "world-greek-partial.tsv"): {"Greek religion"},
         os.path.join(ROOT, "raw", "sacred", "world-persian-partial.tsv"): {"Zoroastrian", "Persian mythology"},
         os.path.join(ROOT, "raw", "sacred", "world-egyptian-partial.tsv"): {"Egyptian religion"}}
OFFLINE = "--offline" in sys.argv
CHECK = "--check" in sys.argv
UA = {"User-Agent": "Lullabyte-build/1.0 (https://github.com/suhxnitiwari/baby-name-maker)"}
COLS = ("name figure_id figure sex original translit language tradition subtradition corpus text passage url occurrences "
        "entity_type name_role status relation source confidence").split()


# ----------------------------------------------------------------------------------------------- fetching
def get(url, path, binary=False, pause=0.3):
    """Cached download: url -> raw/sacred/world/<path>."""
    p = os.path.join(RAW, path)
    if os.path.exists(p) and os.path.getsize(p) > 0:
        return p
    if os.path.exists(p + ".missing"):
        return None
    if OFFLINE:
        return None
    os.makedirs(os.path.dirname(p), exist_ok=True)
    for attempt in range(4):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()
            break
        except Exception as e:  # noqa
            if attempt == 3 or getattr(e, "code", None) == 404:
                open(p + ".missing", "w").write(str(e)) if getattr(e, "code", None) == 404 else None
                print(f"  fetch failed {url}: {e}", file=sys.stderr)
                return None
            time.sleep(3 + 5 * attempt)
    open(p, "wb").write(data)
    time.sleep(pause)
    return p


def read(p, enc="utf-8"):
    return open(p, encoding=enc, errors="replace").read() if p else ""


def wiki_raw(host, title, path):
    return read(get(f"https://{host}/w/index.php?" + urllib.parse.urlencode({"title": title, "action": "raw"}), path))


def nfc(s):
    return unicodedata.normalize("NFC", s)


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s))


class Seg:
    __slots__ = ("text", "passage", "url", "content", "is_original")

    def __init__(self, text, passage, url, content, is_original=True):
        self.text, self.passage, self.url, self.content, self.is_original = text, passage, url, content, is_original


# ----------------------------------------------------------------------------------------------- loaders
PERSEUS_G = "https://raw.githubusercontent.com/PerseusDL/canonical-greekLit/master/data/"
PERSEUS_L = "https://raw.githubusercontent.com/PerseusDL/canonical-latinLit/master/data/"
SCAIFE = "https://scaife.perseus.org/reader/urn:cts:{lit}:{urn}:{ref}/"


def tei_lines(path):
    """Yield (book or None, line n, text) from a Perseus TEI verse edition."""
    import xml.etree.ElementTree as ET
    root = ET.parse(path).getroot()
    ns = "{http://www.tei-c.org/ns/1.0}"
    body = root.find(f".//{ns}body")

    def walk(el, book):
        for ch in el:
            tag = ch.tag.replace(ns, "")
            if tag == "div" and ch.get("type") == "textpart" and (ch.get("subtype") or "").lower() in ("book", "poem"):
                yield from walk(ch, ch.get("n"))
            elif tag == "l":
                for bad in ch.iter(f"{ns}note"):
                    bad.text = ""
                    for x in list(bad):
                        bad.remove(x)
                yield book, ch.get("n"), " ".join("".join(ch.itertext()).split())
            else:
                yield from walk(ch, book)
    yield from walk(body, None)


def load_perseus(lit, author, work, ed, title, url_title):
    base = PERSEUS_G if lit == "greekLit" else PERSEUS_L
    p = get(f"{base}{author}/{work}/{author}.{work}.{ed}.xml", f"perseus/{author}.{work}.{ed}.xml")
    if not p:
        return []
    urn = f"{author}.{work}.{ed}"
    segs = []
    for book, n, txt in tei_lines(p):
        ref = f"{book}.{n}" if book else f"{n}"
        segs.append(Seg(f"Book {book}" if book else title, f"{url_title} {ref}",
                        SCAIFE.format(lit=lit, urn=urn, ref=ref), txt))
    return segs


HYMNS = {1: "To Dionysus", 2: "To Demeter", 3: "To Apollo", 4: "To Hermes", 5: "To Aphrodite", 6: "To Aphrodite",
         7: "To Dionysus", 8: "To Ares", 9: "To Artemis", 10: "To Aphrodite", 11: "To Athena", 12: "To Hera",
         13: "To Demeter", 14: "To the Mother of the Gods", 15: "To Heracles", 16: "To Asclepius",
         17: "To the Dioscuri", 18: "To Hermes", 19: "To Pan", 20: "To Hephaestus", 21: "To Apollo",
         22: "To Poseidon", 23: "To Zeus", 24: "To Hestia", 25: "To the Muses and Apollo", 26: "To Dionysus",
         27: "To Artemis", 28: "To Athena", 29: "To Hestia", 30: "To Earth", 31: "To Helios", 32: "To Selene",
         33: "To the Dioscuri"}


def load_homeric_hymns():
    segs = []
    for i in range(1, 34):
        work = f"tlg{i:03d}"
        p = get(f"{PERSEUS_G}tlg0013/{work}/tlg0013.{work}.perseus-grc2.xml", f"perseus/tlg0013.{work}.perseus-grc2.xml")
        if not p:
            continue
        for _b, n, txt in tei_lines(p):
            segs.append(Seg(f"Hymn {i} ({HYMNS[i]})", f"Homeric Hymn {i}.{n}",
                            SCAIFE.format(lit="greekLit", urn=f"tlg0013.{work}.perseus-grc2", ref=n), txt))
    return segs


def load_orphic():
    idx = wiki_raw("el.wikisource.org", "Ορφικοί ύμνοι", "orphic/index.txt")
    titles = re.findall(r"\[\[(Ορφικοί ύμνοι/[^|\]]+)\|([^\]]+)\]\]", idx)
    segs = []
    for i, (t, label) in enumerate(titles):
        page = read(get("https://el.wikisource.org/w/index.php?" + urllib.parse.urlencode({"title": t, "action": "render"}),
                        f"orphic/{i:02d}.html"))
        page = page[page.find('class="poem"'):] if 'class="poem"' in page else ""
        page = re.sub(r"(?s)<span class=\"pagenum\".*?</span>", "", page)
        lines = [" ".join(strip_tags(x).split()) for x in re.split(r"<br\s*/?>|</p>|</div>", page)]
        lines = [l for l in lines if re.search(r"[α-ωἀ-ῼ]", l)]
        url = "https://el.wikisource.org/wiki/" + urllib.parse.quote(t.replace(" ", "_"))
        num = i  # Abel numbers the prayer to Musaeus 0, then the hymns 1..87 in this order
        for n, l in enumerate(lines, 1):
            segs.append(Seg(f"Hymn {num} ({label.strip()})", f"Orphic Hymn {num}.{n}", url, l))
    return segs


EDDA_POEMS = ["Völuspá", "Hávamál", "Vafþrúðnismál", "Grímnismál", "Skírnismál", "Hárbarðsljóð", "Hymiskviða",
              "Lokasenna", "Þrymskviða", "Völundarkviða", "Alvíssmál", "Baldrs draumar", "Rígsþula", "Hyndluljóð",
              "Gróttasöngr", "Helgakviða Hundingsbana I", "Helgakviða Hjörvarðssonar",
              "Frá dauða Sinfjötla", "Grípisspá", "Reginsmál", "Fáfnismál", "Sigrdrífumál", "Sigurðarkviða in meiri",
              "Guðrúnarkviða in fyrsta", "Sigurðarkviða in skamma", "Helreið Brynhildar", "Dráp Niflunga",
              "Guðrúnarkviða in forna", "Guðrúnarkviða in þriðja", "Oddrúnarkviða", "Atlakviða",
              "Atlamál in grænlenzku", "Guðrúnarhvöt", "Hamðismál", "Grógaldr", "Fjölsvinnsmál"]


def heim(title, path):
    return read(get("https://heimskringla.no/wiki/" + urllib.parse.quote(title.replace(" ", "_")), path))


def body_html(t):
    i = t.find('mw-parser-output')
    j = t.find('class="printfooter"')
    return t[i:j if j > i else None]


def load_edda():
    segs = []
    for poem in EDDA_POEMS:
        t = body_html(heim(poem, f"edda/{poem}.html"))
        if not t:
            continue
        url = "https://heimskringla.no/wiki/" + urllib.parse.quote(poem.replace(" ", "_"))
        t = re.sub(r"<table.*?</table>", "", t, flags=re.S)
        lines = [strip_tags(x).strip() for x in re.split(r"<(?:dd|p|br|div)[^>]*>", t)]
        stanza, prose = None, 0
        for l in lines:
            if not l:
                continue
            m = re.fullmatch(r"(\d+)\.", l)
            if m:
                stanza = m.group(1)
                continue
            if stanza is None:
                if len(l) > 60:          # prose introduction before the first stanza
                    segs.append(Seg(poem, f"{poem}, prose introduction", url, l))
                continue
            segs.append(Seg(poem, f"{poem} {stanza}", url, l))
    return segs


def load_snorra():
    segs = []
    for part in ("Gylfaginning", "Skáldskaparmál"):
        raw = wiki_raw("is.wikisource.org", f"Snorra Edda/{part}", f"snorra/{part}.txt")
        url = "https://is.wikisource.org/wiki/" + urllib.parse.quote(f"Snorra_Edda/{part}")
        ch = None
        for l in raw.splitlines():
            m = re.match(r"'''(\d+)\.\s*(.*?)'''", l.strip())
            if m:
                ch = m.group(1)
            if ch and l.strip() and not l.startswith("{{"):
                segs.append(Seg(part, f"{part} {ch}", url, strip_tags(l.replace("'''", ""))))
    return segs


def load_volsunga():
    t = body_html(heim("Völsunga saga", "edda/Völsunga saga.html"))
    url = "https://heimskringla.no/wiki/V%C3%B6lsunga_saga"
    segs, ch = [], None
    for part in re.split(r"(<b>[IVXLC]+\. KAPÍTULI</b>)", t):
        m = re.match(r"<b>([IVXLC]+)\. KAPÍTULI</b>", part)
        if m:
            ch = roman(m.group(1))
            continue
        if ch:
            for para in re.split(r"<br\s*/?>|</?p[^>]*>", part):
                para = " ".join(strip_tags(para).split())
                if para:
                    segs.append(Seg("Völsunga saga", f"Völsunga saga ch. {ch}", url, para))
    return segs


def roman(r):
    v, out = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}, 0
    for a, b in zip(r, r[1:] + " "):
        out += -v[a] if b != " " and v.get(b, 0) > v[a] else v[a]
    return out


FI_ORD = ["Ensimmäinen", "Toinen", "Kolmas", "Neljäs", "Viides", "Kuudes", "Seitsemäs", "Kahdeksas", "Yhdeksäs",
          "Kymmenes"]


def fi_ordinal(n):
    if n <= 10:
        return FI_ORD[n - 1]
    if n < 20:
        return {11: "Yhdestoista", 12: "Kahdestoista"}.get(n, FI_ORD[n - 11].replace("äs", "äs") + "toista")
    tens = {2: "Kahdes", 3: "Kolmas", 4: "Neljäs", 5: "Viides"}[n // 10]
    return tens + "kymmenes" + ("" if n % 10 == 0 else FI_ORD[n % 10 - 1].lower())


def load_kalevala():
    t = read(get("https://www.gutenberg.org/cache/epub/7000/pg7000.txt", "gutenberg/7000.txt"))
    t = t[t.find("*** START"):t.find("*** END")]
    segs, runo, n = [], None, 0
    for l in t.splitlines():
        s = l.strip()
        m = re.fullmatch(r"([A-ZÄÖ][a-zäö]+) runo", s, flags=re.I) or re.fullmatch(r"(\S+kymmenes\S*) runo", s, flags=re.I)
        if re.fullmatch(r"\S+ runo", s) and s.split()[0][0].isupper():
            runo = (runo or 0) + 1
            n = 0
            continue
        if runo and s and not s.isupper():
            n += 1
            url = "https://fi.wikisource.org/wiki/Kalevala/" + urllib.parse.quote(f"{fi_ordinal(runo)}_runo")
            segs.append(Seg(f"Runo {runo}", f"Kalevala {runo}.{n}", url, s))
    return segs


def load_shahnameh():
    root = json.load(open(get("https://api.ganjoor.net/api/ganjoor/cat/33?poems=true", "ganjoor/cat33.json")))
    segs = []

    def cat(cid, label, slug):
        d = json.load(open(get(f"https://api.ganjoor.net/api/ganjoor/cat/{cid}?poems=true", f"ganjoor/cat{cid}.json")))
        c = d["cat"]
        for p in c.get("poems") or []:
            pj = get(f"https://api.ganjoor.net/api/ganjoor/poem/{p['id']}?verses=true&catInfo=false&rhymes=false"
                     "&recitations=false&images=false&songs=false&comments=false&navigation=false",
                     f"ganjoor/poem{p['id']}.json", pause=0.15)
            if not pj:
                continue
            pd = json.load(open(pj))
            url = "https://ganjoor.net" + pd["fullUrl"]
            couplet = {}
            for v in pd["verses"]:
                couplet.setdefault(v["coupletIndex"], []).append(v["text"])
            for ci, texts in sorted(couplet.items()):
                segs.append(Seg(label, f"Shahnameh, {label}, {p['title']}, bayt {ci + 1}", url, " ".join(texts)))
        for ch in c.get("children") or []:
            cat(ch["id"], label + " / " + ch["title"], slug)
    for ch in root["cat"]["children"]:
        cat(ch["id"], ch["title"], ch["urlSlug"])
    return segs


AVESTA = [("yasna/y0to8.htm", "Yasna", "Y"), ("yasna/y9to11.htm", "Yasna", "Y"), ("yasna/y12.htm", "Yasna", "Y"),
          ("yasna/y13to27.htm", "Yasna", "Y"), ("yasna/y28to34.htm", "Gathas (Yasna)", "Y"),
          ("yasna/y35to42.htm", "Yasna", "Y"), ("yasna/y43to46.htm", "Gathas (Yasna)", "Y"),
          ("yasna/y47to50.htm", "Gathas (Yasna)", "Y"), ("yasna/y51.htm", "Gathas (Yasna)", "Y"),
          ("yasna/y52.htm", "Yasna", "Y"), ("yasna/y53.htm", "Gathas (Yasna)", "Y"),
          ("yasna/y54to72.htm", "Yasna", "Y")] + [(f"ka/yt{i}.htm", "Yashts", f"Yt{i}") for i in range(5, 22)]


def load_avesta():
    segs = []
    for path, text, pre in AVESTA:
        t = read(get("https://www.avesta.org/" + path, "avesta/" + path.replace("/", "_")), "latin-1")
        t = t.encode("latin-1", "replace").decode("cp1252", "replace") if False else t
        body = strip_tags(re.sub(r"(?is)<(script|style|head).*?</\1>", "", t))
        url = "https://www.avesta.org/" + path
        chap, verse = (pre[2:] if pre.startswith("Yt") else None), "0"
        for l in body.splitlines():
            s = l.strip()
            m = re.search(r"Chapter\s+(\d+)\.?$", s)
            if m and pre == "Y":
                chap, verse = m.group(1), "0"
                continue
            m = re.match(r"^(\d+)\.?\s*(.*)$", s)
            if m and len(m.group(1)) <= 3:
                verse, s = m.group(1), m.group(2)
            if s and chap:
                cite = f"Yasna {chap}.{verse}" if pre == "Y" else f"Yasht {chap}.{verse}"
                segs.append(Seg(text, cite, url + (f"#chap{chap}" if pre == "Y" else ""), s))
    return segs


def load_west(path, text, label):
    t = read(get("https://www.avesta.org/" + path, "avesta/" + path.replace("/", "_")), "latin-1")
    t = re.sub(r"(?is)<(script|style|head).*?</\1>", "", t)
    url = "https://www.avesta.org/" + path
    segs, ch = [], None
    for blk in re.split(r"(?i)(<h\d[^>]*>.*?</h\d>|<p[^>]*>)", t):
        if re.match(r"(?i)<h\d", blk):
            m = re.search(r"(?i)chapter\s+([IVXLC\d]+[A-Za-z]?)", strip_tags(blk))
            ch = m.group(1) if m else ch
            continue
        s = " ".join(strip_tags(blk).split())
        if not s or not ch:
            continue
        m = re.match(r"^(\d+)\.\s", s)
        cite = f"{label} {ch}.{m.group(1)}" if m else f"{label} {ch}"
        segs.append(Seg(text, cite, url, s, is_original=False))
    return segs


def load_georgian():
    idx = wiki_raw("ka.wikisource.org", "ვეფხისტყაოსანი", "georgian/index.txt")
    titles = re.findall(r"\[\[(ვეფხისტყაოსანი/[^|\]]+)\|", idx)
    segs = []
    for i, t in enumerate(titles):
        raw = wiki_raw("ka.wikisource.org", t, f"georgian/{i:02d}.txt")
        url = "https://ka.wikisource.org/wiki/" + urllib.parse.quote(t.replace(" ", "_"))
        chapter = t.split("/", 1)[1]
        stanza = None
        for l in raw.splitlines():
            s = strip_tags(re.sub(r"'''|''|\{\{[^}]*\}\}", "", l)).strip(" :")
            m = re.match(r"^(\d+)\s*\.?\s*$", s) or re.match(r"^(\d+)[.)]\s+(.*)$", s)
            if m:
                stanza = m.group(1)
                s = m.group(2) if m.lastindex == 2 else ""
            if s and re.search(r"[ა-ჰ]", s) and not s.startswith(("|", "{", "[[", "}")):
                segs.append(Seg(chapter, f"Vepkhistkaosani {stanza}" if stanza else f"Vepkhistkaosani, {chapter}", url, s))
    return segs


def load_armenian():
    raw = wiki_raw("hy.wikisource.org", "Սասնա ծռեր", "armenian/sasna.txt")
    url = "https://hy.wikisource.org/wiki/" + urllib.parse.quote("Սասնա_ծռեր")
    segs, cycle = [], None
    for l in raw.splitlines():
        m = re.match(r"^(=+)\s*(.*?)\s*=+$", l.strip())
        if m:
            if len(m.group(1)) == 2:
                cycle = " ".join(strip_tags(m.group(2)).split())
            continue
        s = strip_tags(re.sub(r"\{\{[^}]*\}\}|'''|''", "", l)).strip(" :")
        if s and cycle and not s.startswith(("|", "{", "[[", "}")):
            segs.append(Seg(cycle, f"Sasna tsrer, {cycle}", url, s))
    return segs


def archive_pages(ident, fname):
    """Page-level OCR text of an archive.org scan: [(printed page or leaf label, url, text)]."""
    st = get(f"https://archive.org/download/{ident}/{urllib.parse.quote(fname)}_hocr_searchtext.txt.gz",
             f"archive/{ident}.searchtext.gz")
    pi = get(f"https://archive.org/download/{ident}/{urllib.parse.quote(fname)}_hocr_pageindex.json.gz",
             f"archive/{ident}.pageindex.gz")
    pn = get(f"https://archive.org/download/{ident}/{urllib.parse.quote(fname)}_page_numbers.json",
             f"archive/{ident}.page_numbers.json")
    if not (st and pi):
        return []
    text = gzip.open(st, "rt", encoding="utf-8").read()
    index = json.load(gzip.open(pi, "rt"))
    nums = {}
    if pn:
        for p in json.load(open(pn)).get("pages", []):
            nums[p["leafNum"]] = p.get("pageNumber") or ""
    out = []
    for i, ent in enumerate(index):
        a, b = ent[0], ent[1]
        printed = nums.get(i, "")  # leafNum in page_numbers.json is the 0-based scan index
        if printed:
            label, url = f"p. {printed}", f"https://archive.org/details/{ident}/page/{printed}/mode/1up"
        else:
            label, url = f"scan page n{i}", f"https://archive.org/details/{ident}/page/n{i}/mode/1up"
        out.append((label, url, text[a:b]))
    return out


def load_archive(ident, fname, text, label, first_page=1):
    """Pages of the book's body only: printed Arabic page numbers from first_page on (skips the editor's
    roman-numbered preface and introduction); scans without page numbers skip their first four leaves."""
    segs = []
    pages = archive_pages(ident, fname)
    numbered = [p for p in pages if re.fullmatch(r"p\. \d+", p[0])]
    if numbered:
        pages = [p for p in numbered if int(p[0][3:]) >= first_page]
    else:
        pages = pages[4:]
    for pg, url, t in pages:
        t = re.sub(r"-\n(\w)", r"\1", t)
        segs.append(Seg(text, f"{label}, {pg}", url, t, is_original=False))
    return segs


def load_archive_txt(ident, fname, text, label):
    """For scans without a page index: the djvu text, cut into ~40-line blocks cited by printed running heads
    is unreliable, so cite the item and the block number."""
    t = read(get(f"https://archive.org/download/{ident}/{urllib.parse.quote(fname)}_djvu.txt", f"archive/{ident}.txt"))
    return [Seg(text, label, f"https://archive.org/details/{ident}", t, is_original=False)] if t else []


def load_kumulipo():
    t = read(get("https://archive.org/download/kumulipo-hawaiian-english/Kumulipo_djvu.txt", "archive/kumulipo.txt"))
    segs, chant = [], None
    url = "https://archive.org/details/kumulipo-hawaiian-english"
    for l in t.splitlines():
        m = re.match(r"\[(\d+)\]\s+KA WA", l.strip())
        if m:
            chant = m.group(1)
        m = re.match(r"^(\d{4})\.\s+(.*)$", l.strip())
        if m:
            segs.append(Seg(f"Chant {chant}" if chant else "Kumulipo", f"Kumulipo line {int(m.group(1))}", url, m.group(2)))
    return segs


def load_gutenberg_chapters(num, text_label, cite, chap_re):
    t = read(get(f"https://www.gutenberg.org/cache/epub/{num}/pg{num}.txt", f"gutenberg/{num}.txt"))
    t = t[t.find("*** START"):t.find("*** END")]
    url = f"https://www.gutenberg.org/ebooks/{num}"
    segs, ch = [], None
    for para in re.split(r"\n\s*\n", t):
        s = " ".join(para.split())
        m = re.match(chap_re, s)
        if m:
            ch = m.group(1)
            continue
        if ch and s:
            segs.append(Seg(text_label, f"{cite} {ch}", url, s, is_original=False))
    return segs


def load_grey():
    t = read(get("https://standardebooks.org/ebooks/george-grey/polynesian-mythology/text/single-page", "grey/single.html"))
    segs = []
    url0 = "https://standardebooks.org/ebooks/george-grey/polynesian-mythology/text/"
    for sec in re.findall(r'(<section[^>]*id="([^"]+)"[^>]*>.*?</section>)', t, flags=re.S):
        block, sid = sec
        h = re.search(r"<h[1-4][^>]*>(.*?)</h[1-4]>", block, flags=re.S)
        title = " ".join(strip_tags(h.group(1)).split()) if h else sid
        if sid in ("titlepage", "imprint", "colophon", "uncopyright", "halftitlepage", "toc", "endnotes") \
                or "preface" in sid or "preface" in title.lower():
            continue
        for para in re.findall(r"<p[^>]*>(.*?)</p>", block, flags=re.S):
            s = " ".join(strip_tags(para).split())
            if s:
                segs.append(Seg(title, f"Grey, Polynesian Mythology, {title}", url0 + sid, s, is_original=False))
    return segs


def load_book_of_idols():
    raw = wiki_raw("ar.wikisource.org", "كتاب الأصنام", "arabic/asnam.txt")
    raw = re.sub(r"<ref[^>]*>.*?</ref>", "", raw, flags=re.S)
    url = "https://ar.wikisource.org/wiki/" + urllib.parse.quote("كتاب_الأصنام")
    segs, n = [], 0
    for para in re.split(r"\n\s*\n", raw):
        s = strip_tags(re.sub(r"\{\{[^}]*\}\}|'''|''", "", para)).strip()
        if s:
            n += 1
            segs.append(Seg("Kitāb al-Aṣnām", f"Kitāb al-Aṣnām, para. {n}", url, s))
    return segs


def load_roys():
    """Roys 1933 (sacred-texts transcription on archive.org, notes excluded): cited by paragraph of that
    text, counted from the first chapter (the transcription has no page numbers)."""
    t = read(get("https://archive.org/download/book-of-chilam-balam-the-of-chumayel/"
                 "Book-of-Chilam-Balam-the-of-Chumayel_djvu.txt", "archive/roys.txt"))
    start = t.upper().find("THE RITUAL OF THE FOUR WORLD-QUARTERS", 20000)
    url = "https://archive.org/details/book-of-chilam-balam-the-of-chumayel"
    segs, n = [], 0
    for para in re.split(r"\n\s*\n", t[start:]):
        s = " ".join(para.split())
        if len(s) > 2:
            n += 1
            segs.append(Seg("Book of Chilam Balam of Chumayel", f"Chilam Balam of Chumayel (Roys 1933), para. {n}", url, s,
                            is_original=False))
    return segs


# ----------------------------------------------------------------------------------------------- languages
def fold(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().replace("ς", "σ").replace("ϲ", "σ")


# Declension classes: (nominative ending, case endings that may replace it). The stem is the nominative
# minus that ending; a token matches when it is stem + one of the endings of the SAME class, so feminine
# names never match masculine forms (Danae / Danaoi) and vice versa.
GREEK_CLASSES = [
    ("ευσ", "ευσ ηοσ εωσ ηι ει ηα εα ευ ηεσ ηοσ ησ"),
    ("εια", "εια ειασ ειαν ειη ειησ ειην ειαι"), ("ειη", "ειη ειησ ειην εια ειασ ειαν"),
    ("ιοσ", "ιοσ ιου ιοιο ιω ιον ιε ιοι"), ("οσ", "οσ ου οιο οο ω ον ε οι"),
    ("ησ", "ησ ου αο εω η ην α εοσ εα ει ευσ ουσ"), ("ασ", "ασ αο α αν εω ου αντοσ αντι αντα αν"),
    ("ων", "ων ονοσ ονι ονα ον ωνοσ ωνι ωνα οντοσ οντι οντα ονεσ"), ("ωρ", "ωρ οροσ ορι ορα ορ"),
    ("ισ", "ισ ιοσ ιδοσ ιδι ιδα ιν ι ηοσ ιοσ"), ("υσ", "υσ υοσ υι υν υ"), ("ουσ", "ουσ οδοσ οδι οδα ου"),
    ("ωσ", "ωσ ω οι ουσ ωι"), ("ω", "ω ουσ οι ουν"), ("η", "η ησ ην"), ("α", "α ασ αν ησ η"),
    ("ξ", "ξ κοσ κι κα κεσ γοσ γα χοσ χα"), ("ψ", "ψ οσ ι α ποσ πι πα"),
]
LATIN_CLASSES = [
    ("eus", "eus ei eo ea eum eu"), ("ius", "ius ii io ium ie i"), ("us", "us i o um e"),
    ("a", "a ae am ā an"), ("o", "o onis oni onem one ō"), ("on", "on ontis onti onta ontem onte ona onis oni onem one"),
    ("is", "is idis idi idem ide in im ida i"), ("es", "es is i em e ae en ē ēn ae"), ("e", "e es en ae ē ēs ēn"),
    ("ys", "ys yos yi yn y"), ("as", "as antis anti antem ante ada adis"), ("x", "x cis ci cem ce gis gi gem ge"),
    ("en", "en enis eni enem ene"), ("um", "um i o"),
]
NORSE_END = ["inn", "ir", "ur", "r", "i", "a", "u", "ja"]
NORSE_ENDS = {"", "r", "s", "i", "a", "u", "ar", "ir", "ur", "um", "rs", "ra", "ri", "ru", "ins", "inn", "ni", "n", "ju",
              "ja", "jar", "jum", "ar", "ri", "ar", "in", "nar", "ns", "nn", "nni", "nnar"}


class Lang:
    def __init__(self, name, tok, norm, ends=None, nomend=None, caps=False, minstem=3, maxsuffix=7):
        self.name, self.tok, self.norm, self.ends, self.nomend = name, re.compile(tok), norm, ends, nomend
        self.caps, self.minstem, self.maxsuffix = caps, minstem, maxsuffix


WORD = r"[^\W\d_]+(?:[ʼ’'ʻ‘][^\W\d_]+)*"
HWORD = r"[^\W\d_]+(?:[-‐‑][^\W\d_]+)*"
LANGS = {
    "grc": Lang("Greek", r"[^\W\d_]+", fold, GREEK_CLASSES, None, caps=True, minstem=2),
    "lat": Lang("Latin", r"[^\W\d_]+", fold, LATIN_CLASSES, None, caps=True, minstem=2),
    "non": Lang("Old Norse", r"[^\W\d_]+", lambda s: nfc(s).lower(), NORSE_ENDS, NORSE_END, caps=True),
    "fin": Lang("Finnish", r"[^\W\d_]+", lambda s: nfc(s).lower(), caps=True),
    "fas": Lang("Persian", r"[\u0600-\u06FF\u200c]+", lambda s: re.sub(r"[\u064b-\u0655\u0670\u200c]", "", nfc(s)).replace("\u064a", "\u06cc").replace("\u0643", "\u06a9")),
    "ara": Lang("Arabic", r"[؀-ۿ]+", lambda s: re.sub(r"[ً-ْـ]", "", nfc(s)).replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")),
    "ave": Lang("Avestan", r"[^\W\d_]+", lambda s: nfc(s).lower()),
    "kat": Lang("Georgian", r"[ა-ჿ]+(?:-[ა-ჿ]+)*", nfc),
    "hye": Lang("Armenian", r"[Ա-և]+", lambda s: nfc(s).lower()),
    "eng": Lang("English", HWORD, nfc, caps=True),
    "haw": Lang("Hawaiian", HWORD, lambda s: re.sub(r"[‘’ʻ'`‘]", "", nfc(s)).lower()),
    "quc": Lang("K'iche'", HWORD, nfc, caps=True),
}


def make_matcher(lang, spec):
    """spec: 'Nom/Nom2/=exact1,exact2/~prefix'. Returns token-predicate on (raw token)."""
    L = LANGS[lang]
    exact, stems, prefixes = set(), [], []
    for part in spec.split("/"):
        part = part.strip()
        if not part:
            continue
        if part.startswith("="):
            exact |= {L.norm(x.strip()) for x in part[1:].split(",") if x.strip()}
        elif part.startswith("~"):
            prefixes.append(L.norm(part[1:]))
        else:
            n = L.norm(part)
            exact.add(n)
            if L.ends is None:
                continue
            if L.nomend is None:                     # declension classes (Greek, Latin)
                for nom, ends in L.ends:
                    if n.endswith(nom) and len(n) - len(nom) >= L.minstem:
                        stems.append((n[: len(n) - len(nom)], set(ends.split())))
                        break
            else:
                for e in sorted(L.nomend, key=len, reverse=True):
                    if n.endswith(e) and len(n) - len(e) >= L.minstem:
                        stems.append((n[: len(n) - len(e)], L.ends))
                        break
                else:
                    if len(n) >= L.minstem + 1:
                        stems.append((n, L.ends))

    def pred(tok):
        if L.caps and not tok[:1].isupper():
            return False
        t = L.norm(tok)
        if t in exact:
            return True
        for st, ends in stems:
            if t.startswith(st) and t[len(st):] in ends:
                return True
        for p in prefixes:
            if t.startswith(p) and len(t) - len(p) <= L.maxsuffix:
                return True
        return False
    return pred


# ----------------------------------------------------------------------------------------------- figures
# One line per name form:  Name | English Wikipedia article | forms in the edition | type [| flags]
#   forms: nominatives separated by '/', which are declined with the language's endings; '=a,b' exact forms;
#          '~stem' prefix (agglutinative languages).
#   type:  d deity, h human, r royal, m mythological being, p place, t tribe/people, o object/animal
#   flags: 'ep' (epithet or other name of the article's figure), 'rel:<attested form>' (later form),
#          '?' (also a common word or several bearers -> review file)
GREEK = """
Zeus | Zeus | Ζεύς/=Διός,Διί,Δία,Ζεῦ,Ζηνός,Ζηνί,Ζῆνα,Δί,Διὸς | d
Hera | Hera | Ἥρη/Ἥρα | d
Athena | Athena | Ἀθήνη/Ἀθηναίη/Ἀθηνᾶ/Ἀθάνα | d
Pallas | Athena | =Παλλάς,Παλλάδος,Παλλάδι,Παλλάδα,Παλλὰς | d | ep
Apollo | Apollo | Ἀπόλλων/=Ἀπόλλωνος,Ἀπόλλωνι,Ἀπόλλωνα,Ἄπολλον | d
Phoebus | Apollo | Φοῖβος | d | ep
Artemis | Artemis | Ἄρτεμις/=Ἀρτέμιδος,Ἀρτέμιδι,Ἄρτεμιν,Ἀρτέμιδα | d
Aphrodite | Aphrodite | Ἀφροδίτη | d
Cytherea | Aphrodite | Κυθέρεια | d | ep
Cypris | Aphrodite | Κύπρις/=Κύπριδος,Κύπριν,Κύπριδι | d | ep
Hermes | Hermes | Ἑρμῆς/Ἑρμείας/=Ἑρμείαο,Ἑρμέω,Ἑρμῇ,Ἑρμῆν,Ἑρμείᾳ,Ἑρμείαν,Ἑρμεία | d
Ares | Ares | Ἄρης/=Ἄρηος,Ἄρεος,Ἄρηι,Ἄρῃ,Ἄρηα,Ἄρην,Ἄρη,Ἄρες,Ἄρεως,Ἄρεϊ | d
Hephaestus | Hephaestus | Ἥφαιστος | d
Poseidon | Poseidon | Ποσειδάων/Ποσειδῶν/Ποσειδάωνος/=Ποσειδάωνι,Ποσειδάωνα,Ποσείδαον,Ποσειδῶνος | d
Demeter | Demeter | Δημήτηρ/=Δήμητρος,Δημήτερι,Δήμητρα,Δήμητρι,Δημήτερος,Δηοῦς,Δηώ | d
Persephone | Persephone | Περσεφόνεια/Περσεφόνη | d
Hades | Hades | Ἀΐδης/Ἅιδης/Ἀϊδωνεύς/=Ἄϊδος,Ἄϊδι,Ἀΐδαο,Ἀΐδεω,Ἀΐδῃ,Ἅιδου | d
Dionysus | Dionysus | Διώνυσος/Διόνυσος | d
Bacchus | Dionysus | Βάκχος | d | ep
Hestia | Hestia | Ἑστίη/Ἱστίη/Ἑστία | d
Leto | Leto | Λητώ/=Λητοῦς,Λητοῖ,Λητοῦν | d
Maia | Maia | Μαῖα/=Μαίης,Μαιάδος,Μαιάδι | d
Dione | Dione (mythology) | Διώνη | d
Themis | Themis | Θέμις/=Θέμιστος,Θέμιστι,Θέμιν | d | ?
Eos | Eos | Ἠώς/=Ἠοῦς,Ἠοῖ,Ἠῶ | d | ?
Iris | Iris (mythology) | Ἶρις/=Ἶριν,Ἴριδος,Ἶρι | d
Hebe | Hebe (mythology) | Ἥβη | d | ?
Eris | Eris (mythology) | Ἔρις/=Ἔριδος,Ἔριδα,Ἔριν | d | ?
Nike | Nike (mythology) | Νίκη | d | ?
Thetis | Thetis | Θέτις/=Θέτιδος,Θέτι,Θέτιν | d
Calypso | Calypso (mythology) | Καλυψώ/=Καλυψοῦς,Καλυψοῖ | d
Circe | Circe | Κίρκη | d
Ino | Ino (Greek mythology) | Ἰνώ | d
Leucothea | Ino (Greek mythology) | Λευκοθέη | d | ep
Nausicaa | Nausicaa | Ναυσικάα | h
Arete | Arete (mythology) | Ἀρήτη | h
Penelope | Penelope | Πηνελόπεια | h
Helen | Helen of Troy | Ἑλένη | h
Andromache | Andromache | Ἀνδρομάχη | h
Hecuba | Hecuba | Ἑκάβη | h
Cassandra | Cassandra | Κασσάνδρη | h
Briseis | Briseis | Βρισηΐς/=Βρισηΐδος,Βρισηΐδα,Βρισηΐδι | h
Chryseis | Chryseis | Χρυσηΐς/=Χρυσηΐδος,Χρυσηΐδα,Χρυσηΐδι | h | not:Theogony,Homeric_Hymns
Laodice | Laodice (daughter of Priam) | Λαοδίκη | h | ?
Theano | Theano (wife of Antenor) | Θεανώ | h
Eurycleia | Eurycleia | Εὐρύκλεια | h
Anticlea | Anticlea | Ἀντίκλεια | h
Clytemnestra | Clytemnestra | Κλυταιμνήστρη | h
Phaedra | Phaedra (mythology) | Φαίδρη | h
Ariadne | Ariadne | Ἀριάδνη | h
Procris | Procris | Πρόκρις | h
Antiope | Antiope (mother of Amphion and Zethus) | Ἀντιόπη | h
Alcmene | Alcmene | Ἀλκμήνη | h
Epicaste | Jocasta | Ἐπικάστη | h | ep
Tyro | Tyro | Τυρώ | h
Leda | Leda (mythology) | Λήδη | h
Iphimedeia | Iphimedeia | Ἰφιμέδεια | h
Danae | Danaë | Δανάη | h
Semele | Semele | Σεμέλη | h
Niobe | Niobe | Νιόβη | h
Marpessa | Marpessa | Μάρπησσα | h
Cleopatra | Cleopatra (mythology) | Κλεοπάτρη | h | ?
Althaea | Althaea | Ἀλθαίη | h
Medea | Medea | Μήδεια | h
Pandora | Pandora | Πανδώρη/Πανδώρα | h
Gaia | Gaia | Γαῖα/=Γῆ,Γῆς,Γαίης,Γαῖαν,Γαίῃ | d | ?
Uranus | Uranus (mythology) | Οὐρανός | d | ?
Cronus | Cronus | Κρόνος | d
Rhea | Rhea (mythology) | Ῥείη/Ῥέα | d
Oceanus | Oceanus | Ὠκεανός | d | ?
Tethys | Tethys (mythology) | Τηθύς/=Τηθύος,Τηθύν | d
Hyperion | Hyperion (Titan) | Ὑπερίων/=Ὑπερίονος,Ὑπερίονα,Ὑπεριονίδης | d
Theia | Theia | Θεία/Θείη | d | ?
Phoebe | Phoebe (Titaness) | Φοίβη | d
Mnemosyne | Mnemosyne | Μνημοσύνη | d
Iapetus | Iapetus | Ἰαπετός | d
Prometheus | Prometheus | Προμηθεύς | d
Epimetheus | Epimetheus | Ἐπιμηθεύς | d
Atlas | Atlas (mythology) | Ἄτλας/=Ἄτλαντος,Ἄτλαντι,Ἄτλαντα | d
Selene | Selene | Σελήνη | d | ?
Helios | Helios | Ἠέλιος/Ἥλιος | d | ?
Nyx | Nyx | Νύξ/=Νυκτός,Νυκτί,Νύκτα | d | ?
Erebus | Erebus | Ἔρεβος | d | ?
Eros | Eros | Ἔρος/Ἔρως/=Ἔρωτος,Ἔρωτα | d | ?
Hecate | Hecate | Ἑκάτη | d
Styx | Styx | Στύξ/=Στυγός,Στυγί,Στύγα | d
Metis | Metis (mythology) | Μῆτις | d | ?
Eurynome | Eurynome | Εὐρυνόμη | d
Calliope | Calliope | Καλλιόπη/Καλλιόπεια | d
Clio | Clio | Κλειώ | d
Euterpe | Euterpe | Εὐτέρπη | d
Thalia | Thalia (Muse) | Θάλεια/Θαλίη | d | ?
Melpomene | Melpomene | Μελπομένη | d
Terpsichore | Terpsichore | Τερψιχόρη | d
Erato | Erato | Ἐρατώ | d
Polyhymnia | Polyhymnia | Πολύμνια/Πολυμνίη | d
Urania | Urania | Οὐρανίη/Οὐρανία | d
Aglaea | Aglaia (mythology) | Ἀγλαΐη | d | ?
Euphrosyne | Euphrosyne | Εὐφροσύνη | d
Eunomia | Eunomia | Εὐνομίη | d
Dike | Dike (mythology) | Δίκη | d | ?
Eirene | Eirene (goddess) | Εἰρήνη | d | ?
Clotho | Clotho | Κλωθώ | d
Lachesis | Lachesis | Λάχεσις | d
Atropos | Atropos | Ἄτροπος | d
Galatea | Galatea (mythology) | Γαλάτεια | d
Amphitrite | Amphitrite | Ἀμφιτρίτη | d
Doris | Doris (Oceanid) | Δωρίς/=Δωρὶς,Δωρίδος | d | ?
Panope | Panope | Πανόπη | d
Melite | Melite (Nereid) | Μελίτη | d
Clymene | Clymene (Oceanid) | Κλυμένη | d | ?
Oreithyia | Oreithyia | Ὠρείθυια | d | ?
Amatheia | Amatheia | Ἀμάθεια | d
Ianira | Ianira | Ἰάνειρα | d
Electra | Electra (Oceanid) | Ἠλέκτρη | d | ?
Ianthe | Ianthe | Ἰάνθη | d
Peitho | Peitho | Πειθώ | d
Rhodeia | Rhodeia | Ῥοδείη | d
Callirrhoe | Callirrhoe (Oceanid) | Καλλιρόη | d
Clytie | Clytia | Κλυτίη | d
Polydora | Polydora | Πολυδώρη | d | ?
Xanthe | Xanthe | Ξάνθη | d
Eudora | Eudora | Εὐδώρη | d
Tyche | Tyche | Τύχη | d | ?
Asia | Asia (Oceanid) | Ἀσίη | d | ?
Admete | Admete (Oceanid) | Ἀδμήτη | d
Telesto | Telesto | Τελεστώ | d
Pan | Pan (god) | Πάν/=Πᾶνα,Πανός,Πανί,Πάνα | d | ?
Asclepius | Asclepius | Ἀσκληπιός | d
Heracles | Heracles | Ἡρακλέης/Ἡρακλῆς/=Ἡρακλῆος,Ἡρακλῆι,Ἡρακλῆα,Ἡρακληείη,Ἡρακληείην,Ἡρακλέους,Ἡρακλέος | h
Perseus | Perseus | Περσεύς | h | not:Odyssey
Theseus | Theseus | Θησεύς | h
Jason | Jason | Ἰήσων | h
Orion | Orion (mythology) | Ὠρίων | h
Castor | Castor and Pollux | Κάστωρ | h
Polydeuces | Castor and Pollux | Πολυδεύκης | h
Achilles | Achilles | Ἀχιλλεύς/Ἀχιλεύς | h
Patroclus | Patroclus | Πάτροκλος/=Πατρόκλου,Πατρόκλῳ,Πάτροκλον,Πατρόκλεις,Πατροκλῆος,Πατροκλῆα,Πατρόκλεες,Πατροκλέης | h
Hector | Hector | Ἕκτωρ | h
Paris | Paris (mythology) | Πάρις/=Πάριος,Πάριν,Πάρι | h
Alexander | Paris (mythology) | Ἀλέξανδρος | h | ep
Priam | Priam | Πρίαμος | h
Agamemnon | Agamemnon | Ἀγαμέμνων | h
Menelaus | Menelaus | Μενέλαος | h
Odysseus | Odysseus | Ὀδυσσεύς/Ὀδυσεύς | h
Telemachus | Telemachus | Τηλέμαχος | h
Laertes | Laertes | Λαέρτης | h
Diomedes | Diomedes | Διομήδης | h
Ajax | Ajax the Great | Αἴας/=Αἴαντος,Αἴαντι,Αἴαντα,Αἶαν | h | ?
Nestor | Nestor (mythology) | Νέστωρ | h
Idomeneus | Idomeneus of Crete | Ἰδομενεύς | h
Aeneas | Aeneas | Αἰνείας/=Αἰνείαο,Αἰνείᾳ,Αἰνείαν,Αἰνεία,Αἰνέα | h
Anchises | Anchises | Ἀγχίσης | h
Sarpedon | Sarpedon | Σαρπηδών | h
Glaucus | Glaucus (son of Hippolochus) | Γλαῦκος | h | ?
Astyanax | Astyanax | Ἀστυάναξ | h
Antenor | Antenor (mythology) | Ἀντήνωρ | h
Deiphobus | Deiphobus | Δηΐφοβος | h
Helenus | Helenus | Ἕλενος | h | ?
Troilus | Troilus | Τρωΐλος | h
Polydorus | Polydorus (son of Priam) | Πολύδωρος | h | ?
Pandarus | Pandarus | Πάνδαρος | h
Memnon | Memnon (mythology) | Μέμνων | h
Phoenix | Phoenix (son of Amyntor) | Φοῖνιξ | h | ?
Calchas | Calchas | Κάλχας | h
Peleus | Peleus | Πηλεύς | h
Neoptolemus | Neoptolemus | Νεοπτόλεμος | h
Philoctetes | Philoctetes | Φιλοκτήτης | h
Teucer | Teucer | Τεῦκρος | h
Machaon | Machaon | Μαχάων | h
Protesilaus | Protesilaus | Πρωτεσίλαος | h
Antilochus | Antilochus | Ἀντίλοχος | h
Automedon | Automedon | Αὐτομέδων | h
Eumaeus | Eumaeus | Εὔμαιος | h
Mentor | Mentor (Odyssey) | Μέντωρ | h | ?
Alcinous | Alcinous | Ἀλκίνοος | h
Polyphemus | Polyphemus | Πολύφημος | m | ?
Tiresias | Tiresias | Τειρεσίης | h
Elpenor | Elpenor | Ἐλπήνωρ | h
Orestes | Orestes | Ὀρέστης | h | ?
Aegisthus | Aegisthus | Αἴγισθος | h
Bellerophon | Bellerophon | Βελλεροφόντης | h
Meleager | Meleager | Μελέαγρος | h
Oedipus | Oedipus | Οἰδίπους/=Οἰδιπόδαο,Οἰδιπόδεω,Οἰδίποδα,Οἰδιπόδου | h
Minos | Minos | Μίνως/=Μίνωα,Μίνωος,Μίνω | h
Rhadamanthus | Rhadamanthus | Ῥαδάμανθυς | h
Sisyphus | Sisyphus | Σίσυφος | h
Tantalus | Tantalus | Τάνταλος | h
Ganymede | Ganymede (mythology) | Γανυμήδης | h
Tithonus | Tithonus | Τιθωνός | h
Dardanus | Dardanus | Δάρδανος | h | ?
Atreus | Atreus | Ἀτρεύς | h
Thyestes | Thyestes | Θυέστης | h
Pelops | Pelops | Πέλοψ | h
Typhon | Typhon | Τυφωεύς/Τυφάων/Τυφῶν | m
Echidna | Echidna | Ἔχιδνα | m
Medusa | Medusa | Μέδουσα | m
Pegasus | Pegasus | Πήγασος | m
Chrysaor | Chrysaor | Χρυσάωρ | m
Geryon | Geryon | Γηρυονεύς | m
Cerberus | Cerberus | Κέρβερος | m
Chimera | Chimera (mythology) | Χίμαιρα | m
Stheno | Stheno | Σθεννώ | m
Euryale | Euryale (Gorgon) | Εὐρυάλη | m
Metaneira | Metaneira | Μετάνειρα | h
Celeus | Celeus | Κελεός | h
Demophon | Demophon of Eleusis | Δημοφόων | h
Callidice | Callidice | Καλλιδίκη | h
Iambe | Iambe | Ἰάμβη | h
Triptolemus | Triptolemus | Τριπτόλεμος | h
Eumolpus | Eumolpus | Εὔμολπος | h
Musaeus | Musaeus of Athens | Μουσαῖος | h | ?
Orpheus | Orpheus | Ὀρφεύς | h
Nemesis | Nemesis | Νέμεσις | d | ?
Harmonia | Harmonia | Ἁρμονίη/Ἁρμονία | d | ?
Hesperus | Hesperus | Ἕσπερος | d | ?
Zephyrus | Zephyrus | Ζέφυρος | d | ?
Boreas | Boreas | Βορέης/Βορέας | d | ?
Proteus | Proteus | Πρωτεύς | d
Nereus | Nereus | Νηρεύς | d
Triton | Triton (mythology) | Τρίτων | d
Aeolus | Aeolus (son of Hippotes) | Αἴολος | d
Adonis | Adonis | Ἄδωνις | d
Ourania | Aphrodite | Οὐρανία | d | ? ep
Kore | Persephone | Κόρη/Κούρη | d | ? ep
Hygieia | Hygieia | Ὑγίεια | d
Melinoe | Melinoë | Μηλινόη | d
Palaemon | Palaemon | Παλαίμων | d
Psyche | Psyche (mythology) | Ψυχή | d | ?
Thanatos | Thanatos | Θάνατος | d | ?
Hypnos | Hypnos | Ὕπνος | d | ?
Phanes | Phanes | Φάνης | d
Protogonos | Phanes | Πρωτογόνος | d | ep
Sabazios | Sabazios | Σαβάζιος | d
Mise | Mise | Μίση | d
Hipta | Hipta | Ἵπτα | d
"""

ROMAN = """
Aeneas | Aeneas | Aeneas/=Aeneae,Aeneam,Aenean,Aenea,Aeneā | h
Dido | Dido | Dido/=Didonis,Didoni,Didonem,Didone,Didus | r
Elissa | Dido | Elissa | r | ep
Anna | Anna Perenna | Anna | d | ?
Lavinia | Lavinia | Lavinia | r | not:Aeneid
Lavinia | Lavinia | Lavinia | r | ? only:Aeneid
Camilla | Camilla (mythology) | Camilla | h
Creusa | Creusa of Troy | Creusa | h
Ascanius | Ascanius | Ascanius | h
Iulus | Ascanius | Iulus | h | ep
Turnus | Turnus | Turnus | r
Latinus | Latinus | Latinus | r | ?
Amata | Amata | Amata | r | ?
Juturna | Juturna | Iuturna/Juturna | d
Evander | Evander of Pallene | Euandrus/Evandrus | r
Mezentius | Mezentius | Mezentius | r
Lausus | Lausus | Lausus | h | not:Fasti
Nisus | Nisus and Euryalus | Nisus | h | ? not:Metamorphoses,Fasti
Euryalus | Euryalus | Euryalus | h
Achates | Achates | Achates | h
Palinurus | Palinurus | Palinurus | h
Misenus | Misenus | Misenus | h
Silvia | Rhea Silvia | Silvia | h | not:Aeneid
Andromache | Andromache | Andromache | h
Helenus | Helenus | Helenus | h
Anchises | Anchises | Anchises | h
Venus | Venus | Venus/=Veneris,Veneri,Venerem,Venere | d
Juno | Juno (mythology) | Iuno/Juno/=Iunonis,Iunoni,Iunonem,Iunone,Iunonia,Iunonius | d
Jupiter | Jupiter (god) | =Iuppiter,Iupiter,Iovis,Iovi,Iovem,Iove,Juppiter,Jovis,Jovi,Jovem,Jove | d
Minerva | Minerva | Minerva | d
Diana | Diana (mythology) | Diana | d
Apollo | Apollo | Apollo/=Apollinis,Apollini,Apollinem,Apolline | d
Phoebus | Apollo | =Phoebus,Phoebi,Phoebo,Phoebum | d | ep
Neptune | Neptune (mythology) | Neptunus | d
Mercury | Mercury (mythology) | Mercurius | d
Vulcan | Vulcan (mythology) | Volcanus/Vulcanus/Mulciber | d
Mars | Mars (mythology) | =Mars,Martis,Marti,Martem,Marte,Mavors,Mavortis,Mavorte | d
Saturn | Saturn (mythology) | Saturnus | d
Aurora | Aurora (mythology) | Aurora | d | ?
Iris | Iris (mythology) | Iris/=Iridis,Irim,Irin | d
Cupid | Cupid | Cupido/=Cupidinis,Cupidini,Cupidinem | d
Alecto | Alecto | Allecto/Alecto | d
Vesta | Vesta (mythology) | Vesta | d
Ceres | Ceres (mythology) | =Ceres,Cereris,Cereri,Cererem,Cerere | d
Proserpina | Proserpina | Proserpina | d
Bacchus | Dionysus | Bacchus/Lyaeus | d | ep
Faunus | Faunus | Faunus | d
Janus | Janus | Ianus/Janus | d
Flora | Flora (deity) | Flora | d
Pomona | Pomona (mythology) | Pomona | d
Vertumnus | Vertumnus | Vertumnus | d
Carmenta | Carmenta | Carmenta/Carmentis | d
Egeria | Egeria (mythology) | Egeria | d
Lucretia | Lucretia | Lucretia | h
Romulus | Romulus | Romulus | r
Remus | Remus | Remus | r
Numa | Numa Pompilius | Numa | r | not:Aeneid
Hersilia | Hersilia | Hersilia | h
Tarpeia | Tarpeia | Tarpeia | h
Larentia | Acca Larentia | Larentia | d
Feronia | Feronia (mythology) | Feronia | d
Matuta | Mater Matuta | Matuta | d
Fortuna | Fortuna | Fortuna | d | ?
Concordia | Concordia (mythology) | Concordia | d | ?
Pales | Pales | Pales | d | ?
Quirinus | Quirinus | Quirinus | d
Daphne | Daphne | Daphne | d
Io | Io (mythology) | =Io,Ius,Ion,Ionis | h | ?
Phaethon | Phaethon | Phaethon | h
Callisto | Callisto (mythology) | Callisto/Callistus | h
Europa | Europa (consort of Zeus) | Europa | h | not:Aeneid
Cadmus | Cadmus | Cadmus | h
Actaeon | Actaeon | Actaeon | h
Semele | Semele | Semele | h
Echo | Echo (mythology) | Echo | d
Narcissus | Narcissus (mythology) | Narcissus | h
Pyramus | Pyramus and Thisbe | Pyramus | h
Thisbe | Pyramus and Thisbe | Thisbe | h
Perseus | Perseus | Perseus | h
Andromeda | Andromeda (mythology) | Andromeda | h
Medusa | Medusa | Medusa | m
Arachne | Arachne | Arachne | h
Niobe | Niobe | Niobe | h
Latona | Leto | Latona | d
Procne | Procne | Procne | h
Philomela | Philomela (princess of Athens) | Philomela | h
Medea | Medea | Medea | h
Jason | Jason | Iason/Jason | h
Theseus | Theseus | Theseus | h
Ariadne | Ariadne | Ariadne | h
Daedalus | Daedalus | Daedalus | h
Icarus | Icarus | Icarus | h
Atalanta | Atalanta | Atalanta | h
Meleager | Meleager | Meleager/Meleagros | h
Baucis | Baucis and Philemon | Baucis | h
Philemon | Baucis and Philemon | Philemon | h
Orpheus | Orpheus | Orpheus | h
Eurydice | Eurydice | Eurydice | h
Pygmalion | Pygmalion (mythology) | Pygmalion | h
Myrrha | Myrrha | Myrrha | h
Adonis | Adonis | Adonis | d
Hippomenes | Hippomenes | Hippomenes | h
Ceyx | Ceyx | Ceyx | h
Alcyone | Alcyone and Ceyx | Alcyone/Halcyone | h | not:Fasti
Galatea | Galatea (mythology) | Galatea | d
Acis | Acis and Galatea | Acis | d
Polyphemus | Polyphemus | Polyphemus | m
Glaucus | Glaucus | Glaucus | d | ?
Scylla | Scylla | Scylla | m | ?
Circe | Circe | Circe | d | not:Fasti
Picus | Picus | Picus | d
Canens | Canens (mythology) | Canens | d | ?
Iphis | Iphis | Iphis | h | ?
Ianthe | Ianthe | Ianthe | h
Byblis | Byblis | Byblis | h
Hermaphroditus | Hermaphroditus | Hermaphroditus | d
Salmacis | Salmacis | Salmacis | d
Leucothoe | Leucothoe | Leucothoe | h
Clytie | Clytia | Clytie | d
Cephalus | Cephalus | Cephalus | h
Procris | Procris | Procris | h
Hyacinthus | Hyacinth (mythology) | Hyacinthus | h
Cyparissus | Cyparissus | Cyparissus | h
Syrinx | Syrinx | Syrinx | d
Pan | Pan (god) | Pan/=Pana,Panos | d | ?
Midas | Midas | Midas | r
Tiresias | Tiresias | Tiresias | h
Pentheus | Pentheus | Pentheus | r
Arethusa | Arethusa (mythology) | Arethusa | d
Cyane | Cyane | Cyane | d
Hippolytus | Hippolytus (son of Theseus) | Hippolytus | h
Aesculapius | Asclepius | Aesculapius/Coronides | d
Dryope | Dryope | Dryope | h | not:Aeneid
Lotis | Lotis | Lotis | d
Chione | Chione (daughter of Daedalion) | Chione | h | ?
Deucalion | Deucalion | Deucalion | h
Pyrrha | Pyrrha | Pyrrha | h
Hercules | Heracles | Hercules/Alcides | h
Deianira | Deianira | Deianira | h
Iole | Iole | Iole | h
Alcmena | Alcmene | Alcmena/Alcmene | h
Galanthis | Galanthis | Galanthis | h
Hecuba | Hecuba | Hecuba | h
Polyxena | Polyxena | Polyxena | h
Achilles | Achilles | Achilles/=Achillis,Achilli,Achillem,Achille,Achilleus,Achillei,Achillea | h
Ajax | Ajax the Great | =Aiax,Aiacis,Aiaci,Aiacem,Aiace | h | ?
Ulysses | Odysseus | Ulixes/=Ulixis,Ulixi,Ulixem,Ulixe,Ulixei,Ulixen | h
Penelope | Penelope | Penelope/=Penelopes,Penelopen,Penelopea | h
Helen | Helen of Troy | Helena/Helene | h
Paris | Paris (mythology) | =Paris,Paridis,Paridi,Paridem,Paride,Parin | h
Priam | Priam | Priamus | r
Hector | Hector | Hector/=Hectoris,Hectori,Hectorem,Hectore,Hectora,Hectoreus,Hectoreum,Hectorea | h
Cassandra | Cassandra | Cassandra | h
Laocoon | Laocoön | Laocoon | h
Sinon | Sinon | Sinon | h
Pallas | Pallas (son of Evander) | =Pallas,Pallantis,Pallanti,Pallanta,Pallante | h | ?
Minerva Pallas | Athena | =Palladis,Palladi,Palladem,Pallada,Palladium | d | ? ep
Sibyl | Cumaean Sibyl | Sibylla | h
Deiphobe | Cumaean Sibyl | Deiphobe | h | ep
Charon | Charon | Charon | m
Cerberus | Cerberus | Cerberus | m
Pluto | Pluto (mythology) | Pluto/Dis | d | ?
Tisiphone | Tisiphone | Tisiphone | d
Somnus | Hypnos | Somnus | d | ?
Silvanus | Silvanus (mythology) | Silvanus | d
Tiberinus | Tiberinus (god) | Tiberinus | d
Saturnia | Juno (mythology) | Saturnia | d | ep
Cytherea | Aphrodite | Cytherea | d | ep
Orion | Orion (mythology) | Orion | h
Ganymede | Ganymede (mythology) | Ganymedes | h
Anchisiades | Aeneas | Anchisiades | h | ep
Tullia | Tullia (wife of Tarquinius Superbus) | Tullia | h
Ariadna | Ariadne | Ariadna | h | ep
Thetis | Thetis | Thetis/=Thetidis,Thetide,Thetin | d
Persephone | Persephone | Persephone | d
Hyperion | Hyperion (Titan) | Hyperion | d
Hesperus | Hesperus | Hesperus | d | ?
Phoebe | Phoebe (Titaness) | =Phoebe,Phoebes,Phoeben | d | ?
Gradivus | Mars (mythology) | Gradivus | d | ep
Mavors | Mars (mythology) | =Mavors,Mavortis,Mavorti,Mavortem,Mavorte | d | ep
Anna Perenna | Anna Perenna | =Perenna,Perennae,Perennam | d
"""

NORSE = """
Odin | Odin | =Óðinn,Óðins,Óðni,Óðin,Óðinr | d
Thor | Thor | =Þórr,Þórs,Þór,Þóri | d
Freyja | Freyja | =Freyja,Freyju | d
Freya | Freyja | =Freyja,Freyju | d | rel:Freyja
Freyr | Freyr | =Freyr,Freys,Frey,Freyi | d
Frigg | Frigg | =Frigg,Friggjar,Frigga | d
Baldr | Baldr | =Baldr,Baldrs,Baldri,Baldur | d
Baldur | Baldr | =Baldr,Baldrs,Baldri | d | rel:Baldr
Loki | Loki | =Loki,Loka | d
Heimdallr | Heimdallr | =Heimdallr,Heimdallar,Heimdall,Heimdalli | d
Heimdall | Heimdallr | =Heimdallr,Heimdallar,Heimdall,Heimdalli | d | rel:Heimdallr
Tyr | Týr | =Týr,Týs,Tý | d
Idunn | Iðunn | =Iðunn,Iðunnar,Iðunni,Iðun | d
Bragi | Bragi | =Bragi,Braga | d | ?
Njord | Njörðr | =Njörðr,Njarðar,Njörð,Nirði,Njörðs | d
Skadi | Skaði | =Skaði,Skaða | d | ?
Sif | Sif | =Sif,Sifjar | d
Hel | Hel (mythological being) | =Hel,Heljar | d | ?
Ullr | Ullr | =Ullr,Ullar,Ull | d
Vidar | Víðarr | =Víðarr,Víðars,Víðar | d
Vali | Váli (son of Odin) | =Váli,Vála | d | ?
Forseti | Forseti | =Forseti | d
Hodr | Höðr | =Höðr,Höðs,Höð | d
Nanna | Nanna (Norse deity) | =Nanna,Nönnu | d
Gefjon | Gefjon | =Gefjun,Gefjunar,Gefjon | d
Eir | Eir | =Eir | d | ?
Saga | Sága and Sökkvabekkr | =Sága | d | ?
Fulla | Fulla | =Fulla,Fullu | d
Sjofn | Sjöfn | =Sjöfn | d
Lofn | Lofn | =Lofn | d
Var | Vár | =Vár | d | ?
Vor | Vör | =Vör | d | ?
Syn | Syn (goddess) | =Syn | d | ?
Hlin | Hlín | =Hlín | d
Snotra | Snotra | =Snotra | d
Gna | Gná | =Gná | d
Sol | Sól (Germanic mythology) | =Sól,Sólar | d | ?
Mani | Máni | =Máni,Mána | d | ?
Gerd | Gerðr | =Gerðr,Gerði,Gerðar,Gerð | d
Gullveig | Gullveig | =Gullveig,Gullveigu | d
Ran | Rán | =Rán | d | ?
Aegir | Ægir | =Ægir,Ægis,Ægi | d
Hoenir | Hœnir | =Hœnir,Hænir,Hœnis,Hæni,Hœni | d
Mimir | Mímir | =Mímir,Mímis,Míms | d
Kvasir | Kvasir | =Kvasir,Kvasis | d
Ymir | Ymir | =Ymir,Ymis | m
Buri | Búri | =Búri | d
Borr | Borr | =Borr,Burs,Bors | d
Bestla | Bestla | =Bestla | m
Askr | Ask and Embla | =Askr,Ask | h | ?
Embla | Ask and Embla | =Embla,Emblu | h
Sigyn | Sigyn | =Sigyn | d
Angrboda | Angrboða | =Angrboða | m
Fenrir | Fenrir | =Fenrir,Fenris,Fenri | m
Jormungandr | Jörmungandr | =Jörmungandr | m
Sleipnir | Sleipnir | =Sleipnir,Sleipni | o
Huginn | Huginn and Muninn | =Huginn,Hugin | o
Muninn | Huginn and Muninn | =Muninn,Munin | o
Yggdrasil | Yggdrasil | =Yggdrasill,Yggdrasils | o
Surtr | Surtr | =Surtr,Surts,Surti | m
Thjazi | Þjazi | =Þjazi,Þjaza | m
Hrungnir | Hrungnir | =Hrungnir,Hrungnis | m
Thrymr | Þrymr | =Þrymr,Þrym | m
Hymir | Hymir | =Hymir,Hymis | m
Skirnir | Skírnir | =Skírnir,Skírni | d
Hermodr | Hermóðr | =Hermóðr | d
Magni | Magni | =Magni,Magna | d | ?
Modi | Móði and Magni | =Móði | d | ?
Thrudr | Þrúðr | =Þrúðr | d | ?
Rindr | Rindr | =Rindr,Rind | d
Gunnlod | Gunnlöð | =Gunnlöð | m
Jord | Jörð | =Jörð,Jarðar | d | ?
Nott | Nótt | =Nótt | d | ?
Dagr | Dagr | =Dagr | d | ?
Hyndla | Hyndla | =Hyndla,Hyndlu | m
Menglod | Menglöð | =Menglöð | d
Svipdagr | Svipdagr | =Svipdagr | h | not:Prose_Edda
Groa | Gróa | =Gróa | m
Volundr | Wayland the Smith | =Völundr,Völundar,Völund | h
Bodvildr | Böðvildr | =Böðvildr,Böðvildi | h
Hervor | Hervör alvitr | =Hervör | d
Olrun | Ölrún | =Ölrún | d
Svanhvit | Svanhvít | =Svanhvít | d
Helgi | Helgi Hundingsbane | =Helgi,Helga | h | ?
Sigrun | Sigrún | =Sigrún,Sigrúnu | d
Svava | Sváfa | =Sváva | d
Sigurd | Sigurd | =Sigurðr,Sigurðar,Sigurð,Sigurði | h
Brynhildr | Brynhildr | =Brynhildr,Brynhildar,Brynhildi | d
Brynhild | Brynhildr | =Brynhildr,Brynhildar,Brynhildi | d | rel:Brynhildr
Gudrun | Guðrún | =Guðrún,Guðrúnar,Guðrúnu | h
Gunnar | Gunnar (Nibelung) | =Gunnarr,Gunnars,Gunnari,Gunnar | h
Hogni | Högni | =Högni,Högna | h | ?
Gjuki | Gjúki | =Gjúki,Gjúka | h
Grimhild | Grimhild | =Grímhildr,Grímhildar,Grímhildi | h
Atli | Atli | =Atli,Atla | h | not:Poetic_Edda
Atli | Atli | =Atli,Atla | h | ? only:Poetic_Edda
Sigmund | Sigmund | =Sigmundr,Sigmundar,Sigmund,Sigmundi | h
Signy | Signý | =Signý,Signýju,Signýjar | h
Sinfjotli | Sinfjötli | =Sinfjötli,Sinfjötla | h
Volsung | Völsung | =Völsungr,Völsungs,Völsungi | h
Hjordis | Hjördís | =Hjördís,Hjördísi,Hjördísar | h
Aslaug | Aslaug | =Áslaug,Áslaugu | h
Fafnir | Fafnir | =Fáfnir,Fáfnis,Fáfni | m
Regin | Regin | =Reginn,Regins,Regin | m | ?
Otr | Ótr | =Otr,Otrs | m
Andvari | Andvari | =Andvari,Andvara | m
Svanhild | Svanhildr | =Svanhildr,Svanhildi,Svanhildar | h
Jormunrekkr | Ermanaric | =Jörmunrekkr,Jörmunrekk,Jörmunrekks | h
Hamdir | Hamðir | =Hamðir,Hamði | h
Sorli | Sörli | =Sörli,Sörla | h
Erpr | Erpr | =Erpr | h
Oddrun | Oddrún | =Oddrún,Oddrúnu | h
Borghild | Borghildr | =Borghildr,Borghildi | h
Budli | Budli | =Buðli,Buðla | h
Grani | Grani (horse) | =Grani,Grana | o
Sigrdrifa | Sigrdrífa | =Sigrdrífa | d
Kara | Kára | =Kára | d | ?
Rigr | Rig | =Rígr,Ríg | d
Gylfi | Gylfi | =Gylfi,Gylfa | h
Bil | Bil (mythology) | =Bil | d | ?
Hnoss | Hnoss | =Hnoss | d | ?
Gersemi | Gersemi | =Gersemi | d | ?
Od | Óðr | =Óðr,Óðs | d | ?
Skuld | Skuld | =Skuld | d | ?
Urd | Urðr | =Urðr,Urðar | d | ?
Verdandi | Verðandi | =Verðandi | d
Hildr | Hildr | =Hildr | d | ?
Skogul | Skögul | =Skögul | d
Gondul | Göndul | =Göndul | d
Thora | Þóra Hákonardóttir | =Þóra,Þóru | h | not:Poetic_Edda
Thora | Þóra Hákonardóttir | =Þóra,Þóru | h | ? only:Poetic_Edda
Gudny | Guðný | =Guðný | h
Drasill | Yggdrasil | =Drasill | o | ?
Hrimfaxi | Hrímfaxi | =Hrímfaxi | o
Skinfaxi | Skinfaxi | =Skinfaxi | o
Freki | Geri and Freki | =Freki | o | ?
Geri | Geri and Freki | =Geri | o | ?
Audumbla | Auðumbla | =Auðumbla,Auðhumla | o
Mundilfari | Mundilfari | =Mundilfari | m
Narfi | Narfi | =Narfi,Narfa | m
Vafthrudnir | Vafþrúðnir | =Vafþrúðnir,Vafþrúðnis | m
Alviss | Alvíss | =Alvíss | m
Ivaldi | Ívaldi | =Ívaldi,Ívalda | m
Hlodyn | Hlóðyn | =Hlóðyn,Hlóðynjar | d
Fjorgyn | Fjörgyn and Fjörgynn | =Fjörgyn,Fjörgynjar | d
Sigi | Sigi | =Sigi,Siga | h
Rerir | Rerir | =Rerir,Reri | h
Ljod | Hljóð | =Hljóð | m | ?
"""

FINNISH = """
Vainamoinen | Väinämöinen | ~Väinämöi/~Väinämöis | d
Ilmarinen | Ilmarinen | ~Ilmarine/~Ilmarise | d
Lemminkainen | Lemminkäinen | ~Lemminkäi/~Lemminkäis | h
Ahti | Lemminkäinen | =Ahti,Ahin,Ahille,Ahtia | h | ? ep
Kaukomieli | Lemminkäinen | ~Kaukomiel | h | ep
Joukahainen | Joukahainen | ~Joukahai/~Joukahais | h
Aino | Aino (mythology) | =Aino,Ainon,Ainolle,Ainoa,Ainosta,Ainokin | h | ?
Louhi | Louhi | ~Louhi | d
Kullervo | Kullervo | ~Kullervo | h
Marjatta | Marjatta | ~Marjat | h
Ilmatar | Ilmatar | ~Ilmatar/~Ilmattar | d
Kyllikki | Kyllikki | ~Kylliki/~Kyllikki | h
Untamo | Untamo | ~Untamo/~Untamoi | h
Kalervo | Kalervo | ~Kalervo/~Kalervoi | h
Tiera | Tiera | ~Tiera | h
Ukko | Ukko | ~Ukko/~Ukon | d
Tapio | Tapio | =Tapio,Tapion,Tapiolle,Tapiota,Tapiosta | d
Mielikki | Mielikki | ~Mielikki/~Mielikin | d
Tellervo | Tellervo | ~Tellervo | d
Kuutar | Kuutar | ~Kuutar | d
Paivatar | Päivätär | ~Päivätär/~Päivättär | d
Annikki | Annikki | ~Annikki/~Annikin | h
Osmotar | Osmotar | ~Osmotar/~Osmottar | d
Vipunen | Antero Vipunen | ~Vipune/~Vipuse | m
Tuoni | Tuoni | =Tuoni,Tuonen,Tuonelle,Tuonta | d | ?
Tuonetar | Tuonetar | ~Tuonetar/~Tuonettar | d
Vellamo | Vellamo | ~Vellamo | d
Nyyrikki | Nyyrikki | ~Nyyrikki/~Nyyrikin | d
Hiisi | Hiisi | ~Hiisi/~Hiite/~Hiiden | m | ?
Lempo | Lempo | ~Lempo/~Lemmo | m | ?
Kaleva | Kaleva (mythology) | =Kaleva,Kalevan,Kalevalle,Kalevasta,Kalevassa | m | ?
Pellervoinen | Sampsa Pellervoinen | ~Pellervoi/~Pellervois | d
Kimmo | Kimmo (Kalevala) | ~Kimmo | h
Kave | Kave (mythology) | =Kave,Kaven | d | ?
Loviatar | Loviatar | ~Loviatar/~Loviattar | d
Kivutar | Kivutar | ~Kivutar | d
Suvetar | Suvetar | ~Suvetar | d
Etelatar | Etelätär | ~Etelätär | d
Kalevatar | Kalevatar | ~Kalevatar/~Kalevattar | d
Mielatar | Mielatar | ~Mielatar | d
Otso | Otso | =Otso,Otson,Otsolle | o
Sampo | Sampo | =Sampo,Sammon,Sampoa,Sammosta,Sampohon,Sammolla | o
Pohjola | Pohjola | =Pohjola,Pohjolan,Pohjolahan,Pohjolassa,Pohjolasta | p
Kalevala | Kalevala (location) | =Kalevala,Kalevalan,Kalevalassa,Kalevalahan | p
Lalli | Lalli | ~Lalli | h | ?
Ahto | Ahti (god) | =Ahto,Ahtoa,Ahtolle,Ahton | d
Tuulikki | Tuulikki | ~Tuulikki/~Tuulikin | d
Hongatar | Hongatar | ~Hongatar | d
Ainikki | Ainikki | ~Ainikki | h
Kuura | Tiera | ~Kuura | h | ep
"""

SHAHNAMEH = """
Rostam | Rostam | رستم/=رستمِ | h
Sohrab | Sohrab | سهراب | h
Tahmineh | Tahmina | تهمینه | h
Rudabeh | Rudaba | رودابه | h
Zal | Zal | زال | h | ?
Dastan | Zal | دستان | h | ? ep
Simorgh | Simurgh | سیمرغ | m
Sindokht | Sindukht | سیندخت | h
Mehrab | Mehrab Kaboli | مهراب | r
Sam | Sām (Shahnameh) | سام | h | ?
Nariman | Nariman (Shahnameh) | نریمان | h
Fereydun | Fereydun | فریدون | r
Iraj | Iraj | ایرج | r
Salm | Salm | سلم | r | ?
Tur | Tur (Shahnameh) | تور | r | ?
Manuchehr | Manuchehr | منوچهر | r
Jamshid | Jamshid | جمشید | r
Zahhak | Zahhak | ضحاک | r
Kaveh | Kaveh the Blacksmith | کاوه | h
Faranak | Faranak | فرانک | r
Arnavaz | Arnavaz | ارنواز | r
Shahrnaz | Shahrnaz | شهرناز | r
Kiumars | Keyumars | کیومرث | r
Siamak | Siamak | سیامک | r
Hushang | Hushang | هوشنگ | r
Tahmuras | Tahmuras | طهمورث | r
Nowzar | Nowzar | نوذر | r
Garshasp | Garshasp | گرشاسپ | r
Kay Qobad | Kay Kawad | کیقباد/=قباد | r | ?
Kay Kavus | Kay Kāvus | کاووس/کیکاووس/=کاوس | r
Sudabeh | Sudabeh | سودابه | r
Siavash | Siavash | سیاوش/سیاوخش | r
Farangis | Farangis | فرنگیس | r
Jarireh | Jarireh | جریره | r
Kay Khosrow | Kay Khosrow | کیخسرو | r
Forud | Forud | فرود | h | ?
Afrasiab | Afrasiab | افراسیاب | r
Piran | Piran Viseh | پیران | h | ?
Giv | Giv (Shahnameh) | گیو | h
Gudarz | Gudarz | گودرز | h
Bijan | Bijan (Shahnameh) | بیژن | h
Manijeh | Manijeh | منیژه | h
Tus | Tus (Shahnameh) | طوس | h | ?
Fariborz | Fariborz | فریبرز | h
Gordafarid | Gordafarid | گردآفرید | h
Hojir | Hujir | هجیر | h
Gostaham | Gostaham | گستهم | h
Lohrasp | Lohrasp | لهراسپ | r
Goshtasp | Vishtaspa | گشتاسپ | r
Katayun | Katayun | کتایون | r
Esfandiyar | Esfandiyār | اسفندیار | h
Pashutan | Peshotan | پشوتن | h
Bahman | Bahman (Shahnameh) | بهمن | r | ?
Homay | Homay Chehrazad | همای | r | ?
Darab | Darab | داراب | r
Dara | Dara (Shahnameh) | دارا | r | ?
Eskandar | Alexander the Great | اسکندر/سکندر | r
Roshanak | Roxana | روشنک | r
Ardeshir | Ardashir I | اردشیر | r | ?
Golnar | Golnar | گلنار | h | ?
Shapur | Shapur I | شاپور | r | ?
Bahram | Bahram V | بهرام | r | ?
Azadeh | Azadeh (Shahnameh) | آزاده | h | ?
Anushirvan | Khosrow I | نوشین‌روان/نوشیروان/انوشیروان/=کسری | r
Bozorgmehr | Bozorgmehr Bokhtagan | بوزرجمهر/بزرگمهر | h
Khosrow Parviz | Khosrow II | پرویز | r
Shirin | Shirin | شیرین | r | ?
Purandokht | Boran | پوران‌دخت/پوراندخت | r
Azarmidokht | Azarmidokht | آزرم‌دخت/آزرمدخت | r
Yazdegerd | Yazdegerd III | یزدگرد | r
Rakhsh | Rakhsh | رخش | o | ?
Akvan | Akvan Div | اکوان | m
Shaghad | Shaghad | شغاد | h
Zavareh | Zavareh | زواره | h
Faramarz | Faramarz | فرامرز | h
Arash | Arash the Archer | آرش | h
Golshahr | Golshahr | گلشهر | h
Shideh | Shideh | شیده | h
Mahafarid | Mahafarid | ماه‌آفرید/ماهآفرید | h
Sepinud | Sepinud | سپینود | h
Gordiyeh | Gordiya | گردیه | h
Mazdak | Mazdak | مزدک | h
Zartosht | Zoroaster | زردشت/زرتشت | h
Bahram Chobin | Bahram Chobin | چوبینه | h
Pashang | Pashang | پشنگ | r
Aghrirath | Aghrirat | اغریرث | r
Garsivaz | Garsivaz | گرسیوز | r
Kamus | Kamus | کاموس | h
Ashkbus | Ashkbus | اشکبوس | h
Human | Human (Shahnameh) | هومان | h | ?
Barzu | Barzu | برزو | h
Jahan | Jahan (Shahnameh) | =جهن | h | ?
Mehrnush | Mehrnush | مهرنوش | h
Zarir | Zarir | زریر | h
Jamasp | Jamasp | جاماسپ | h
Bastur | Bastur | نستور/بستور | h | ?
Homa | Huma bird | =هما | o | ?
Sohrab mother | Tahmina | =تهمینهٔ | h | ? ep
Ormazd | Hormizd I | اورمزد/هرمزد | r | ?
Qobad | Kavad I | =قباد | r | ?
Kasra | Khosrow I | =کسری | r | ep
Zarasp | Zarasp | زراسپ | h
Shahrbanu | Shahrbanu | شهربانو | r
Mehr | Mithra | =مهر | d | ?
Nahid | Anahita | =ناهید | d | ?
Sorush | Sraosha | سروش | d | ?
Ahriman | Angra Mainyu | اهرمن/اهریمن | d
Hormozd | Ahura Mazda | =هرمزد,هُرمزد | d | ?
Div-e Sepid | White Div | =دیوسپید,دیو‌سپید | m
Kay Kavus wife | Sudabeh | =سوداوه | r | ep
"""

AVESTAN = """
Zarathustra | Zoroaster | ~zarathushtr/~zarathushtr/=zarathushtrô,zarathushtra,zarathushtrahe,zarathushtrâi,zarathushtrem | h
Spitama | Zoroaster | ~spitam | h | ep
Ahura Mazda | Ahura Mazda | ~mazdå/~mazdâ/=ahurô,ahurahe,ahurem,ahurâi,ahura,ahurâ | d
Anahita | Anahita | ~anâhit | d
Ardvi Sura | Anahita | ~aredvî/~aredvîm | d | ep
Mithra | Mithra | ~mithr | d | ?
Haoma | Haoma | ~haom | d
Vishtaspa | Vishtaspa | ~vîshtâsp | r
Frashaoshtra | Frashaoshtra | ~frashaoshtr | h
Jamaspa | Jamasp | ~jâmâsp | h
Pouruchista | Pouruchista | ~pourucist | h
Hvovi | Hvovi | ~hvôv | h
Maidyoimangha | Maidhyoimah | ~maidyôimângh/~maidyôimå | h
Yima | Jamshid | =ýimô,ýimahe,ýimem,ýimâi,ýima,ýimô | r
Thraetaona | Fereydun | ~thraêtaon | r
Keresaspa | Garshasp | ~keresâsp | h
Haosravah | Kay Khosrow | ~haosravangh/~haosrava/~husravangh | r
Kavi Usan | Kay Kāvus | ~usadhan/~usa | r | ?
Tishtrya | Tishtrya | ~tishtry | d
Vayu | Vayu-Vata | ~vayu/~vayê/~vayaosh | d | ?
Verethraghna | Verethragna | ~verethraghn | d
Ashi | Ashi | =ashi,ashish,ashîm,ashîsh,ashîmca | d | ?
Daena | Daena | ~daên | d | ?
Armaiti | Spenta Armaiti | ~ârmait | d
Sraosha | Sraosha | ~sraosh | d
Rashnu | Rashnu | ~rashn | d
Airyaman | Airyaman | ~airyam | d
Atar | Atar | =âtarsh,âthrô,âtrem,âthra,âtare,âtarem | d | ?
Hvare Khshaeta | Hvare-khshaeta | ~hvare-xshaêt/~hvarexshaêt | d
Gayomaretan | Gayomart | ~gayô-maret/~gayehe-maret | h | ?
Angra Mainyu | Angra Mainyu | ~angrô/~angrahe/~angrem | d
Azhi Dahaka | Zahhak | ~dahâk | m
Frangrasyan | Afrasiab | ~frangrasy | r
Aurvataspa | Lohrasp | ~aurvat-asp/~aurvataspahe | r
Hutaosa | Hutaosa | ~hutaos | r
Saoshyant | Saoshyant | ~saoshyañt/~saoshyant | h
Astvat-ereta | Saoshyant | ~astvat-eret | h | ep
Vivanghvant | Vivanghvant | ~vîvangh | h
Athwya | Abtin | ~âthwy | h
Pourushaspa | Pourushaspa | ~pourushasp | h
Dughdova | Dughdova | ~dughdhôv | h
Zairivairi | Zarir | ~zairivair | h
Spenta Mainyu | Spenta Mainyu | ~speñtô/~speñtahe | d | ?
Vohu Manah | Vohu Manah | =vohu,vohû | d | ?
Asha Vahishta | Asha | ~ashem/~ashahe | d | ?
Haurvatat | Haurvatat | ~haurvatât/~haurvatâs | d
Ameretat | Ameretat | ~ameretât/~ameretâs | d
Khshathra Vairya | Khshathra Vairya | ~xshathrem vairîm/=xshathra,xshathrem | d | ?
Apam Napat | Apam Napat | ~napâtem/~napâ | d | ?
Chista | Chista | ~cist | d | ?
Parendi | Parendi | ~pârendi/~pâreñd | d
Raman | Rāman | ~râman | d | ?
Hvarenah | Khvarenah | ~xvarenô/~xvarenangh | d | ?
Drvaspa | Drvaspa | ~drvâsp | d
Arshtat | Arshtat | ~arshtât | d
Nairyosangha | Nairyosangha | ~nairyô-sangh/~nairyôsangh | d
Kavi Haosravah | Kay Khosrow | ~kavaêm haosravangh | r | ?
Usinemah | Usinemah | ~usinemah | h
Hamaspathmaedaya | Hamaspathmaedaya | ~hamaspathmaêda | h
"""

PAHLAVI = """
Ohrmazd | Ahura Mazda | =Ohrmazd | d
Ahriman | Angra Mainyu | =Ahriman | d
Zartosht | Zoroaster | =Zartosht,Zartoshtan | h
Gayomard | Gayomart | =Gayomard | h
Mashya | Mashya and Mashyana | =Mashye | h
Mashyana | Mashya and Mashyana | =Mashyane | h
Siyamak | Siamak | =Siyamak | h
Hooshang | Hushang | =Hooshang | r
Tahmurasp | Tahmuras | =Tahmurasp | r
Jamshed | Jamshid | =Jamshed,Yim | r
Dahak | Zahhak | =Dahak,Zohak | r
Faridoon | Fereydun | =Faridoon | r
Airik | Iraj | =Airik | r
Salm | Salm | =Salm | r
Tur | Tur (Shahnameh) | =Tur | r | ?
Manuschihar | Manuchehr | =Manuschihar | r
Frasiyav | Afrasiab | =Frasiyav | r
Kay Kaus | Kay Kāvus | =Kaus | r
Siyavakhsh | Siavash | =Siyavakhsh,Siyavash | r
Khosraw | Kay Khosrow | =Khosraw,Husru | r | ?
Lohrasp | Lohrasp | =Lohrasp | r
Vishtasp | Vishtaspa | =Vishtasp,Kai-Vishtasp | r
Zarir | Zarir | =Zarir | h
Peshotan | Peshotan | =Peshotan | h
Spend-dad | Esfandiyār | =Spend-dad,Spendyad | h
Vohuman | Vohu Manah | =Vohuman | d
Humai | Homay Chehrazad | =Humai | r
Darai | Darab | =Darai | r | ?
Pourushasp | Pourushaspa | =Pourushasp | h
Dughdov | Dughdova | =Dughdov,Dughdao | h
Soshyant | Saoshyant | =Soshyant | h
Ushedar | Ushedar | =Ushedar | h
Ushedarmah | Ushedarmah | =Ushedarmah | h
Tishtar | Tishtrya | =Tishtar | d
Spandarmad | Spenta Armaiti | =Spandarmad | d
Ardwahisht | Asha | =Ardwahisht | d
Shahrewar | Khshathra Vairya | =Shahrewar | d
Hordad | Haurvatat | =Hordad | d
Amurdad | Ameretat | =Amurdad | d
Srosh | Sraosha | =Srosh | d
Rashn | Rashnu | =Rashn | d
Mihr | Mithra | =Mihr | d | ?
Adar | Atar | =Adar | d | ?
Anahid | Anahita | =Anahid,Aredvivsur,Aredvisur | d
Warharan | Verethragna | =Warharan | d
Rapithwin | Rapithwin | =Rapithwin | d
Haoma | Haoma | =Haoma,Hom | d
Viraf | Arda Viraf | =Viraf | h
Jamasp | Jamasp | =Jamasp | h
Frashoshtar | Frashaoshtra | =Frashoshtar | h
Keresasp | Garshasp | =Keresasp,Sam | h | ?
Pashang | Pashang | =Pashang | r
Nodar | Nowzar | =Nodar | r
Arashk | Arsaces I | =Arashk | r
Ardashir | Ardashir I | =Ardashir | r
Chamrosh | Chamrosh | =Chamrosh | o
Hadhayosh | Hadhayaosh | =Hadhayosh | o
Kar | Kar fish | =Kar | o | ?
Akoman | Akem Manah | =Akoman | d
Eshm | Aeshma | =Eshm | d
Az | Az (demon) | =Az | d | ?
Neryosang | Nairyosangha | =Neryosang | d
"""

GEORGIAN = """
Tinatin | Tinatin (character) | ~თინათინ | r
Nestan-Darejan | Nestan-Darejan | ~ნესტან | r
Tariel | Tariel | ~ტარიელ | h
Avtandil | Avtandil | ~ავთანდილ | h
Pridon | Pridon | ~ფრიდონ | r
Nuradin | Pridon | ~ნურადინ | r | ep
Rostevan | Rostevan | ~როსტევან | r
Asmat | Asmat | ~ასმათ | h
Shermadin | Shermadin | ~შერმადინ | h
Patman | Patman | ~ფატმან | h
Usen | Usen | ~უსენ | h
Parsadan | Parsadan | ~ფარსადან | r
Davar | Davar | ~დავარ | h
Dulardukht | Dulardukht | ~დულარდუხტ | r
Tamar | Tamar of Georgia | ~თამარ | r
Sograt | Sograt | ~სოგრატ | h
Ramaz | Ramaz | ~რამაზ | r
Melik Surkhavi | Melik Surkhavi | ~სურხავ | r
Rustaveli | Shota Rustaveli | ~რუსთველ | h
Dzaghan | Dzaghan | ~ძაღან | h
Rosan | Rosan | ~როსან | h
Pharsadan | Parsadan | ~ფარსადან | r | rel:Parsadan
Khvarazmsha | Khvarazmsha | ~ხვარაზმშა | r
"""

ARMENIAN = """
Sanasar | Sanasar | ~Սանասար | h
Baghdasar | Baghdasar | ~Բաղդասար | h
Mher | Mher | ~Մհեր | h
Davit | David of Sasun | ~Դավիթ/~Դավթ | h
Tsovinar | Tsovinar | ~Ծովինար | d
Armaghan | Armaghan | ~Արմաղան | h
Khandut | Khandut | ~Խանդութ | h
Gohar | Gohar (Sasna Tsrer) | ~Գոհար | h
Ohan | Dzenov Ohan | ~Օհան/~Հովան | h
Ismil | Ismil Khatun | ~Իսմիլ | h
Msra Melik | Msra Melik | ~Մելիք | h | ?
Kurkik Jalali | Kurkik Jalali | ~Ջալալի | o
Gagik | Gagik (Sasna Tsrer) | ~Գագիկ | r
Chmshkik | Chmshkik Sultan | ~Չմշկիկ | h
Paron Ohan | Dzenov Ohan | ~Ձենով | h | ep
Deghdzoun | Deghtsun Kyurtikh | ~Դեղձուն | h
"""

EGYPTIAN = """
Osiris | Osiris | =Osiris,Ausar,Ausir,Asar | d
Isis | Isis | =Isis,Auset,Aset | d
Nephthys | Nephthys | =Nephthys,Nebt-het | d
Horus | Horus | =Horus,Heru | d
Set | Set (deity) | =Set,Sut,Suti | d | ?
Ra | Ra | =Ra,Re | d | ?
Thoth | Thoth | =Thoth,Tehuti | d
Anubis | Anubis | =Anubis,Anpu | d
Hathor | Hathor | =Hathor,Het-heru,Het-Heru | d
Maat | Maat | =Maat | d
Nut | Nut (goddess) | =Nut | d | ?
Geb | Geb | =Seb,Keb,Geb | d
Shu | Shu (Egyptian god) | =Shu | d
Tefnut | Tefnut | =Tefnut | d
Ptah | Ptah | =Ptah | d
Amun | Amun | =Amen,Amon,Amen-Ra | d | ?
Khepri | Khepri | =Khepera,Kheperd | d
Atum | Atum | =Tmu,Tem,Temu,Atem | d | ?
Sekhmet | Sekhmet | =Sekhet,Sekhmet | d | ?
Neith | Neith | =Neith,Net | d | ?
Mut | Mut | =Mut | d | ?
Khonsu | Khonsu | =Khensu,Khonsu | d
Serket | Serket | =Serqet,Selk | d
Hapi | Hapi (Nile god) | =Hapi | d | ?
Imsety | Imsety | =Mestha,Amset | d
Duamutef | Duamutef | =Tuamautef | d
Qebehsenuef | Qebehsenuef | =Qebhsennuf,Qebhsenuf | d
Apep | Apep | =Apep,Apepi,Apophis | m
Sobek | Sobek | =Sebek | d
Wepwawet | Wepwawet | =Ap-uat,Apuat | d
Nu | Nu (mythology) | =Nu,Nun | d | ?
Ani | Ani (scribe) | =Ani | h
Tutu | Tutu (wife of Ani) | =Thuthu,Tutu | h | ?
Bennu | Bennu | =Bennu | o
Meh-urt | Mehet-Weret | =Meh-urt,Mehurt | d
Wennefer | Osiris | =Un-nefer,Unnefer | d | ep
Bast | Bastet | =Bast,Bastet | d
Heka | Heka (god) | =Heka | d | ?
Renenutet | Renenutet | =Renenet | d
Meskhenet | Meskhenet | =Meskhenet | d
Hu | Hu (mythology) | =Hu | d | ?
Sia | Sia (god) | =Saa | d | ?
Khnum | Khnum | =Khnemu,Khnum | d
Min | Min (god) | =Amsu,Min | d | ?
Taweret | Taweret | =Ta-urt,Apet | d | ?
Menthu | Montu | =Menthu,Mentu | d
Nebseni | Papyrus of Nebseni | =Nebseni | h
"""

MESOPOTAMIAN = """
Gilgamesh | Gilgamesh | =Gilgamish,Gilgamesh | r
Enkidu | Enkidu | =Enkidu,Engidu | h
Ninsun | Ninsun | =Nin-sun,Ninsun | d
Humbaba | Humbaba | =Humbaba,Huwawa | m
Utnapishtim | Utnapishtim | =Uta-Napishtim,Ut-napishtim,Utnapishtim | h
Urshanabi | Urshanabi | =Ur-Shanabi,Urshanabi | h
Siduri | Siduri | =Siduri | d
Ishtar | Inanna | =Ishtar,IStar | d
Anu | Anu | =Anu,A-num | d
Enlil | Enlil | =Enlil,Bel,Bél | d | ?
Shamash | Utu | =Shamash,Samas | d
Ea | Enki | =Ea,E-a | d | ?
Nergal | Nergal | =Nergal | d
Tammuz | Dumuzid | =Tammuz | d
Lugalbanda | Lugalbanda | =Lugal-banda,Lugalbanda | r
Aruru | Ninhursag | =Aruru | d
Adad | Hadad | =Adad | d
Ninurta | Ninurta | =Ninurta | d
Namtar | Namtar | =Namtar | d
Ereshkigal | Ereshkigal | =Ereshkigal,Erish-kigal | d
Ishullanu | Ishullanu | =Ishullanu | h
Ubara-Tutu | Ubara-Tutu | =Ubara-Tutu | r
Marduk | Marduk | =Marduk | d
Tiamat | Tiamat | =Tiamat,Ti-amat | d
Apsu | Abzu | =Apsu,Apsû,Apsii,Apsii | d | ?
Mummu | Mummu | =Mummu,Mu-um-mu | d
Kingu | Kingu | =Kingu,Kin-gu | d
Anshar | Anshar | =Anshar,Ansar,AnSar,An-sar,An-Sar | d
Kishar | Kishar | =Kishar,Kisar | d
Lahmu | Lahmu | =Lahmu | d
Lahamu | Lahamu | =Lahamu | d
Damkina | Damkina | =Damkina,Damkina | d
Nudimmud | Enki | =Nudimmud | d | ep
Gaga | Gaga (god) | =Gaga | d | ?
Nabu | Nabu | =Nabu,Nebo | d
Sin | Sin (mythology) | =Sin | d | ?
Ummu-Hubur | Tiamat | =Ummu-Hubur | d | ep
Tutu | Marduk | =Tutu,Tu-tu | d | ? ep
Asaru | Marduk | =Asaru,Asaru-alim | d | ep
Shamhat | Shamhat | =Shamhat,Samhat,Ukhat | h
Belit-seri | Belet-Seri | =Belit-seri | d
"""

MAYA = """
Hunahpu | Hunahpu | =Hunahpu,Hun-Ahpu | d
Xbalanque | Xbalanque | =Xbalanqué,Xbalanque | d
Ixquic | Xquic | =Xquiq,Xquic | d
Ixmucane | Xmucane | =Xmucané,Xmucane | d
Ixpiyacoc | Xpiyacoc | =Xpiyacoc | d
Gucumatz | Kukulkan | =Gucumatz | d
Tepeu | Tepeu | =Tepeu | d
Huracan | Huracan | =Hurakan | d
Vucub Caquix | Seven Macaw | =Vukub-Cakix | m
Zipacna | Zipacna | =Zipacna | m
Cabrakan | Cabrakan | =Cabrakan | m
Hun Hunahpu | One Hunahpu | =Hunhun-Ahpu | d
Vucub Hunahpu | Vucub Hunahpu | =Vukub-Hunahpu | d
Hun Came | One Death | =Hun-Camé,Hun-Came | d
Vucub Came | Vucub Came | =Vukub-Camé,Vukub-Came | d
Hunbatz | Hun Batz and Hun Chuen | =Hunbatz | d
Hunchouen | Hun Batz and Hun Chuen | =Hunchouen | d
Cuchumaquic | Cuchumaquic | =Cuchumaquiq,Cuchumaquic | d
Balam-Quitze | Balam-Quitze | =Balam-Quitzé,Balam-Quitze | h
Balam-Acab | Balam-Acab | =Balam-Agab | h
Mahucutah | Mahucutah | =Mahucutah | h
Iqi-Balam | Iqi-Balam | =Iqi-Balam | h
Tohil | Tohil | =Tohil | d
Avilix | Avilix | =Avilix | d
Hacavitz | Hacavitz | =Hacavitz | d
Caha-Paluma | Caha-Paluma | =Cahapaluna,Caha-Paluna | h
Chomiha | Chomiha | =Chomiha,Choïmha,Choimha | h
Tzununiha | Tzununiha | =Tzununiha | h
Caquixaha | Caquixaha | =Cakixa,Cakixaha | h
Xbaquiyalo | Xbaquiyalo | =Xbaquiyalo | h
Xtah | Xtah | =Xtah | h
Xpuch | Xpuch | =Xpuch | h
Qocavib | Qocavib | =Qocavib | h
Qocaib | Qocaib | =Qocaib | h
Cotuha | Cotuha | =Cotuha | r
Quicab | Quicab | =Quicab | r
Gucumatz king | Gucumatz (Kʼicheʼ king) | =Qucumatz | r | ?
Xibalba | Xibalba | =Xibalba | p
"""

CHILAM = """
Hunac Ceel | Hunac Ceel | =Hunac Ceel,HUNAC CEEL | h
Kukulcan | Kukulcan | =Kukulcan | d
Ah Mex Cuc | Ah Mex Cuc | =Ah Mex Cuc | h
Chac | Chaac | =Chac | d | ?
Pauahtun | Pauahtun | =Pauahtun | d
Bolon-ti-ku | Bolon-ti-ku | =Bolon-ti-ku | d
Oxlahun-ti-ku | Oxlahun-ti-ku | =Oxlahun-ti-ku | d
Kinich Kakmo | Kinich Kakmo | =Kinich Kakmo,Kinich Kakmoo | d
Bacab | Bacab | =Bacab,Bacabs | d
Chilam Balam | Chilam Balam | =Chilam Balam | h
"""

YORUBA = """
Olorun | Olorun | =Olorun,Olodumare | d
Obatala | Obatala | =Obatala | d
Odudua | Oduduwa | =Odudua | d
Aganju | Aganju | =Aganju | d
Yemaja | Yemọja | =Yemaja | d
Orungan | Orungan | =Orungan | d
Shango | Shango | =Shango | d
Oya | Oya | =Oya | d
Oshun | Ọṣun | =Oshun | d | ?
Oba | Oba (orisha) | =Oba | d | ?
Ogun | Ogun | =Ogun | d
Olokun | Olokun | =Olokun | d
Olosa | Olosa | =Olosa | d
Ifa | Ifá | =Ifa | d
Elegba | Eshu | =Elegba,Eshu,Esu | d
Shankpanna | Shopona | =Shankpanna | d
Dada | Dada (orisha) | =Dada | d | ?
Oshosi | Ọ̀ṣọ́ọ̀sì | =Oshosi | d
Orisha Oko | Orisha Oko | =Oko | d | ?
Oke | Oke (orisha) | =Oke | d | ?
Aje | Aje (orisha) | =Aje | d | ?
Shigidi | Shigidi | =Shigidi | d
Ori | Ori (Yoruba) | =Ori,Olori | d | ?
Egungun | Egungun | =Egungun | d
Oro | Oro (Yoruba) | =Oro | d | ?
Odu | Odu Ifa | =Odu | d | ?
Opele | Opele | =Opele | o
Orishako | Orisha Oko | =Orishako | d
Aroni | Aroni | =Aroni | m
Abiku | Abiku | =Abiku | m
Oranyan | Oranyan | =Oranyan,Oranyon | r
Ajapa | Tortoise | =Ajapa | o | ?
"""

HAWAIIAN = """
Kumulipo | Kumulipo | =Kumulipo | d
Poele | Kumulipo | =Poele,Po‘ele | d
Haumea | Haumea | =Haumea | d
Wakea | Wākea | =Wakea | d
Papa | Papahānaumoku | =Papa | d | ?
Kane | Kāne | =Kane | d | ?
Kanaloa | Kanaloa | =Kanaloa | d
Hina | Hina (goddess) | =Hina | d
Maui | Māui (Hawaiian mythology) | =Maui | d | ?
Haloa | Hāloa | =Haloa | h
Laka | Laka | =Laka | d
Lono | Lono | =Lono | d
Kahiko | Kahiko | =Kahiko | h | ?
Lailai | Laʻilaʻi | =Lailai,La‘ila‘i | h
Kii | Kiʻi | =Kii,Ki‘i | h | ?
Hinahanaiakamalama | Hina (goddess) | =Hina-ia-ka-malama,Hinahanaiakamalama | d | ep
Akalana | Akalana | =Akalana | h
Hema | Hema | =Hema | h | ?
Kahai | Kahai | =Kaha‘i,Kahai | h | ?
Paliku | Paliku | =Paliku | h | ?
Kupulanakehau | Kupulanakehau | =Kupulanakehau | h
"""

PELE = """
Pele | Pele (deity) | =Pele | d
Hiiaka | Hiʻiaka | =Hiiaka,Hiiaka-i-ka-poli-o-Pele | d
Lohiau | Lohiau | =Lohiau | h
Hopoe | Hopoe | =Hopoe | h
Wahine-omao | Wahine-omao | =Wahine-oma | h
Paoa | Paoa | =Paoa | h
Kamohoalii | Kamohoaliʻi | =Ka-moho-alii,Kamohoalii | d
Namakaokahai | Nāmaka | =Namaka-o-Kaha,Namaka | d
Kapo | Kapo (goddess) | =Kapo | d
Laka | Laka | =Laka,Laká | d
Haumea | Haumea | =Haumea | d
Kane | Kāne | =Kane | d | ?
Kanaloa | Kanaloa | =Kanaloa | d
Lono | Lono | =Lono | d
Ku | Kū | =Ku | d | ?
Hina | Hina (goddess) | =Hina | d
Kane-milo-hai | Kāne-milo-hai | =Kane-milo-hai | d
Kamapuaa | Kamapuaʻa | =Kama-pua,Kamapuaa | d
Pana-ewa | Panaewa | =Pana-ewa | m
Malei | Malei | =Malei | d
Kilauea | Kīlauea | =Kilauea | p
Poliahu | Poliʻahu | =Poli-ahu,Poliahu | d
Hiiaka-i-ka-ale-i | Hiʻiaka | =Hiiaka-i-ka-ale-i | d | ep
Wakea | Wākea | =Wakea | d
Papa | Papahānaumoku | =Papa | d | ?
Kahiki | Kahiki | =Kahiki | p
Kukuena | Kukuena | =Kukuena | d
Uli | Uli (Hawaiian goddess) | =Uli | d | ?
"""

MAORI = """
Rangi | Ranginui | =Rangi,Ranginui,Rangi-nui | d
Papa | Papatūānuku | =Papa,Papatūānuku,Papa-tu-a-nuku | d | ?
Tane | Tāne | =Tāne,Tānemahuta,Tāne-mahuta,Tane-mahuta | d
Tangaroa | Tangaroa | =Tangaroa | d
Tumatauenga | Tūmatauenga | =Tūmatauenga,Tū-matauenga | d
Tawhirimatea | Tāwhirimātea | =Tāwhirimātea,Tāwhiri-mā-tea | d
Rongo | Rongo | =Rongomātāne,Rongo-mā-tāne | d
Haumia-tiketike | Haumia-tiketike | =Haumia-tikitiki,Haumia-tiketike | d
Ruaumoko | Rūaumoko | =Rūaumoko,Rū-ai-moko,Ruaumoko | d
Maui | Māui (Māori mythology) | =Māui,Māui-tikitiki-a-Taranga,Māui-tikitiki-o-Taranga | d
Hine-nui-te-po | Hine-nui-te-pō | =Hinenuitepō,Hine-nui-te-pō | d
Taranga | Taranga | =Taranga | d
Hina | Hina (goddess) | =Hina,Hinauri,Hine-uri | d
Tinirau | Tinirau | =Tinirau | d
Kae | Kae (mythology) | =Kae | h
Rata | Rātā (Māori mythology) | =Rātā | h
Tawhaki | Tāwhaki | =Tāwhaki | d
Hinemoa | Hinemoa | =Hinemoa | h
Tutanekai | Tūtānekai | =Tūtānekai | h
Rupe | Rupe (mythology) | =Rupe | d
Mahuika | Mahuika | =Mahuika | d
Uenuku | Uenuku | =Uenuku | d
Whakatau | Whakatau | =Whakatau | h
Hatupatu | Hatupatu | =Hatupatu | h
Kurangaituku | Kurangaituku | =Kurangaituku | m
Ngatoroirangi | Ngātoro-i-rangi | =Ngātoroirangi,Ngātoro | h
Tamatekapua | Tamatekapua | =Tamatekapua | h
Kupe | Kupe | =Kupe | h
Turi | Turi (Māori ancestor) | =Turi | h
Manaia | Manaia (Māori ancestor) | =Manaia | h | ?
Paoa | Paoa (Māori ancestor) | =Pāoa | h
Marutuahu | Marutūāhu | =Marutūāhu | h
Kahureremoa | Kahureremoa | =Kahureremoa | h
Hotunui | Hotunui | =Hotunui | h
Tuwhakararo | Tūwhakararo | =Tūwhakararo | h
Apakura | Apakura | =Apakura | h
Rehua | Rehua | =Rehua | d
Karihi | Karihi | =Karihi | h
Wahieroa | Wahieroa | =Wahieroa | h
Hine-i-te-iwaiwa | Hine-te-iwaiwa | =Hine-i-te-iwaiwa | d
Irawaru | Irawaru | =Irawaru | h
Tiki | Tiki | =Tiki | d | ?
Hinetitama | Hine-tītama | =Hinetītama,Hine-tītama | d
Tama-nui-te-ra | Tama-nui-te-rā | =Tamanuiterā,Tama-nui-te-rā | d
Takarangi | Takarangi | =Takarangi | h
Raumahora | Raumahora | =Raumahora | h
Puhihuia | Puhihuia | =Puhihuia | h
Kahukura | Kahukura | =Kāhukura | h
Toi | Toi (Māori ancestor) | =Toi | h
Ihenga | Īhenga | =Īhenga | h
Whakaotirangi | Whakaotirangi | =Whakaotirangi | h
Kuiwai | Kuiwai | =Kuiwai | h
Haungaroa | Haungaroa | =Haungaroa | h
Hine-tu-a-hoanga | Hine-tū-a-hōanga | =Hine-tū-a-hōanga | d
Ngahue | Ngahue | =Ngāhue | h
Tutunui | Tutunui | =Tutunui | o
Muri-ranga-whenua | Muri-ranga-whenua | =Muri-ranga-whenua | d
Hawaiki | Hawaiki | =Hawaiki | p
"""

ARABIAN = """
Al-Lat | Al-Lat | =اللات | d
Al-Uzza | Al-Uzza | =العزى,العزي | d
Manat | Manāt | =مناة | d
Hubal | Hubal | =هبل | d
Wadd | Wadd | =ود,ودا | d | ?
Suwa | Suwa' | =سواع,سواعا | d
Yaghuth | Yaghuth | =يغوث,يغوثا | d
Yauq | Ya'uq | =يعوق,يعوقا | d
Nasr | Nasr (god) | =نسر,نسرا | d | ?
Isaf | Isaf and Na'ila | =إساف,اساف,إسافا,اسافا | d
Naila | Isaf and Na'ila | =نائلة,نايلة | d
Dhu al-Khalasa | Dhu al-Khalasa | =الخلصة | d
Dhu al-Shara | Dushara | =الشرى | d
Al-Fals | Al-Fals | =الفلس | d
Ruda | Ruda (deity) | =رضاء,رضى | d
Sa'd | Sa'd (deity) | =سعد | d | ?
Dhu al-Kaffayn | Dhu al-Kaffayn | =الكفين | d
Amr ibn Luhay | Amr ibn Luhayy | =لحي | h
Uqaysir | Al-Uqaysir | =الأقيصر,الاقيصر | d
Nuhm | Nuhm | =نهم | d
"""

YAZIDI = """
Melek Taus | Melek Taus | =Melek,Melek Ta'us,Melek Taus | d
Sheikh Adi | Adi ibn Musafir | =Adi | h | ?
Yazid | Yazid I | =Yezid | h
Shams ad-Din | Sheikh Shems | =Sams,Shems | d | ?
Azazil | Azazel | =Azazil | d
"""

PIBY = """
Athlyi | Robert Athlyi Rogers | =Athlyi | h | ?
Garvey | Marcus Garvey | =Garvey | h | ?
"""


# ----------------------------------------------------------------------------------------------- corpora
PERSEUS_SRC = "Perseus Digital Library canonical-greekLit (CC BY-SA 4.0)"
LATIN_SRC = "Perseus Digital Library canonical-latinLit (CC BY-SA 4.0)"
NORSE_SRC = "heimskringla.no, Eddukvæði (Guðni Jónsson's normalised text; medieval text, credit requested)"


def C(corpus, tradition, lang, language, loader, figures, source, sub="", original=True, review=False, ocr=False):
    return dict(corpus=corpus, tradition=tradition, lang=lang, language=language, loader=loader, figures=figures,
                source=source, sub=sub, original=original, review=review, ocr=ocr)


def archive(ident, fname, text, label, first_page=1):
    return lambda: load_archive(ident, fname, text, label, first_page)


CORPORA = [
    C("Iliad", "Greek religion", "grc", "Greek", lambda: load_perseus("greekLit", "tlg0012", "tlg001", "perseus-grc2", "Iliad", "Iliad"),
      GREEK, PERSEUS_SRC + ", Homer, Iliad (Monro & Allen)"),
    C("Odyssey", "Greek religion", "grc", "Greek", lambda: load_perseus("greekLit", "tlg0012", "tlg002", "perseus-grc2", "Odyssey", "Odyssey"),
      GREEK, PERSEUS_SRC + ", Homer, Odyssey (Murray)"),
    C("Theogony", "Greek religion", "grc", "Greek", lambda: load_perseus("greekLit", "tlg0020", "tlg001", "perseus-grc2", "Theogony", "Theogony"),
      GREEK, PERSEUS_SRC + ", Hesiod, Theogony (Evelyn-White)"),
    C("Works and Days", "Greek religion", "grc", "Greek", lambda: load_perseus("greekLit", "tlg0020", "tlg002", "perseus-grc2", "Works and Days", "Works and Days"),
      GREEK, PERSEUS_SRC + ", Hesiod, Works and Days (Evelyn-White)"),
    C("Shield of Heracles", "Greek religion", "grc", "Greek", lambda: load_perseus("greekLit", "tlg0020", "tlg003", "perseus-grc2", "Shield of Heracles", "Shield"),
      GREEK, PERSEUS_SRC + ", Hesiod, Shield of Heracles (Evelyn-White)"),
    C("Homeric Hymns", "Greek religion", "grc", "Greek", load_homeric_hymns, GREEK, PERSEUS_SRC + ", Homeric Hymns (Evelyn-White)"),
    C("Orphic Hymns", "Greek religion", "grc", "Greek", load_orphic, GREEK,
      "Greek Wikisource, Orphica ed. E. Abel (1885, PD); Wikisource text CC BY-SA 4.0", sub="Orphism"),
    C("Aeneid", "Roman religion", "lat", "Latin", lambda: load_perseus("latinLit", "phi0690", "phi003", "perseus-lat2", "Aeneid", "Aeneid"),
      ROMAN, LATIN_SRC + ", Vergil, Aeneid (Greenough)"),
    C("Metamorphoses", "Roman religion", "lat", "Latin", lambda: load_perseus("latinLit", "phi0959", "phi006", "perseus-lat2", "Metamorphoses", "Met."),
      ROMAN, LATIN_SRC + ", Ovid, Metamorphoses (Magnus)"),
    C("Fasti", "Roman religion", "lat", "Latin", lambda: load_perseus("latinLit", "phi0959", "phi007", "perseus-lat2", "Fasti", "Fasti"),
      ROMAN, LATIN_SRC + ", Ovid, Fasti"),
    C("Poetic Edda", "Norse religion", "non", "Old Norse", load_edda, NORSE, NORSE_SRC),
    C("Prose Edda", "Norse religion", "non", "Old Norse", load_snorra, NORSE,
      "Icelandic Wikisource, Snorra Edda (Guðni Jónsson's normalised text)"),
    C("Völsunga saga", "Norse religion", "non", "Old Norse", load_volsunga, NORSE,
      "heimskringla.no, Völsunga saga (Guðni Jónsson's normalised text)"),
    C("Avesta", "Zoroastrian", "ave", "Avestan", load_avesta, AVESTAN,
      "avesta.org, Avestan text after Geldner 1896 (PD), transliteration by J. H. Peterson"),
    C("Bundahishn", "Zoroastrian", "eng", "Middle Persian", lambda: load_west("mp/bundahis.html", "Bundahishn", "Bundahishn"),
      PAHLAVI, "avesta.org, E. W. West's translation (SBE 5, 1880; PD), spellings as edited by J. H. Peterson", original=False),
    C("Arda Viraf", "Zoroastrian", "eng", "Middle Persian", lambda: load_west("mp/viraf.html", "Arda Viraf", "Arda Viraf"),
      PAHLAVI, "avesta.org, Haug & West's translation (1872; PD), spellings as edited by J. H. Peterson", original=False),
    C("Shahnameh", "Persian mythology", "fas", "Persian", load_shahnameh, SHAHNAMEH,
      "ganjoor.net, Ferdowsi, Shahnameh (Persian text)"),
    C("Kalevala", "Finnish mythology", "fin", "Finnish", load_kalevala, FINNISH,
      "Project Gutenberg #7000, Lönnrot, Kalevala (1849; PD)"),
    C("Vepkhistkaosani", "Georgian epic", "kat", "Georgian", load_georgian, GEORGIAN,
      "Georgian Wikisource, Shota Rustaveli, ვეფხისტყაოსანი (medieval text, PD)"),
    C("Sasna tsrer", "Armenian epic", "hye", "Armenian", load_armenian, ARMENIAN,
      "Armenian Wikisource, Սասնա ծռեր (compiled folk epic; edition not stated)", review=True),
    C("Book of the Dead", "Egyptian religion", "eng", "Egyptian",
      archive("papyrus-of-ani-transliteration-e.-a.-wallis-budge", "Papyrus of Ani Transliteration E.A. Wallis Budge",
              "Papyrus of Ani", "Budge 1895"),
      EGYPTIAN, "E. A. Wallis Budge, The Book of the Dead: The Papyrus of Ani (1895; PD), archive.org scan",
      original=False, ocr=True),
    C("Epic of Gilgamesh", "Mesopotamian religion", "eng", "Akkadian",
      archive("thompson-1928-gilgamesh", "Thompson_1928_Gilgamesh", "Epic of Gilgamish", "Thompson 1928"),
      MESOPOTAMIAN, "R. Campbell Thompson, The Epic of Gilgamish (1928; PD in the US), archive.org scan",
      original=False, ocr=True),
    C("Enuma Elish", "Mesopotamian religion", "eng", "Akkadian",
      archive("the-seven-tablets-of-creation.-vol.-1", "The seven tablets of creation. Vol. 1", "Seven Tablets of Creation", "King 1902"),
      MESOPOTAMIAN, "L. W. King, The Seven Tablets of Creation, vol. 1 (1902; PD), archive.org scan",
      original=False, ocr=True),
    C("Popol Vuh", "Maya religion", "quc", "K'iche'",
      archive("popolvuhlelivres00bras", "popolvuhlelivres00bras", "Popol Vuh", "Brasseur 1861"),
      MAYA, "Brasseur de Bourbourg, Popol Vuh, K'iche' text with French (1861; PD), archive.org scan", ocr=True),
    C("Book of Chilam Balam of Chumayel", "Maya religion", "eng", "Yucatec Maya", load_roys, CHILAM,
      "Ralph L. Roys, The Book of Chilam Balam of Chumayel (1933; PD in the US, copyright not renewed), sacred-texts transcription on archive.org",
      original=False),
    C("Yoruba oral tradition, as recorded in A. B. Ellis, The Yoruba-speaking Peoples (1894)", "Yoruba religion", "eng", "Yoruba",
      archive("b21781370", "b21781370", "The Yoruba-speaking Peoples", "Ellis 1894"),
      YORUBA, "A. B. Ellis, The Yoruba-speaking Peoples of the Slave Coast of West Africa (1894; PD), archive.org scan", ocr=True),
    C("Hawaiian oral tradition, as recorded in the Kumulipo", "Hawaiian religion", "haw", "Hawaiian", load_kumulipo, HAWAIIAN,
      "Kumulipo, Hawaiian text (Kalākaua 1889) with M. W. Beckwith's 1951 line numbers, interlinear by D. Stampe; archive.org (marked PD)"),
    C("Hawaiian oral tradition, as recorded in N. B. Emerson, Pele and Hiiaka (1915)", "Hawaiian religion", "eng", "Hawaiian",
      lambda: load_gutenberg_chapters(60279, "Pele and Hiiaka", "Pele and Hiiaka, ch.", r"^CHAPTER ([IVXLC]+)\b"),
      PELE, "Project Gutenberg #60279, N. B. Emerson, Pele and Hiiaka: A Myth from Hawaii (1915; PD)"),
    C("Māori oral tradition, as recorded in George Grey, Polynesian Mythology (1855)", "Māori religion", "eng", "Māori",
      load_grey, MAORI, "Standard Ebooks, George Grey, Polynesian Mythology (1855; PD; macrons as edited by Standard Ebooks / NZETC)"),
    C("Kitāb al-Aṣnām", "pre-Islamic Arabian religion", "ara", "Arabic", load_book_of_idols, ARABIAN,
      "Arabic Wikisource, Ibn al-Kalbī, Kitāb al-Aṣnām (ed. Ahmed Zaki Pasha 1914; PD)"),
    C("Yazidi oral tradition, as recorded in Isya Joseph, Devil Worship (1919)", "Yazidi", "eng", "Kurdish",
      archive("devilworshipsacr00jose", "devilworshipsacr00jose", "Devil Worship", "Joseph 1919", first_page=30),
      YAZIDI, "Isya Joseph, Devil Worship: the Sacred Books and Traditions of the Yezidiz (1919; PD), archive.org scan",
      original=False, ocr=True),
    C("Holy Piby", "Rastafari", "eng", "English",
      archive("the-holy-piby-by-robert-athlyi-rogers", "The Holy Piby By Robert Athlyi Rogers", "Holy Piby", "Rogers 1924"),
      PIBY, "Robert Athlyi Rogers, The Holy Piby (1924; PD in the US), archive.org scan", ocr=True),
]
LATIN_SCRIPT_ORIGINAL = {"Yoruba", "Hawaiian", "Māori", "K'iche'", "English"}


# ----------------------------------------------------------------------------------------------- wikidata
WD_CACHE = os.path.join(RAW, "wikidata.json")
REDIRECT_BLOCK = {"Q13406463", "Q202444", "Q12308941", "Q11879590", "Q3409032", "Q7725634", "Q5185279",
                  "Q47461344", "Q16521", "Q23442", "Q4167410", "Q9134"}
BAD_REDIRECTS = {"Lohiau", "Loviatar", "Spenta Mainyu", "Imsety", "Duamutef", "Qebehsenuef", "Sörli", "Kahiki",
                 "Balam-Quitze", "Mahucutah", "Iqi-Balam", "Caha-Paluma", "Tzununiha", "Högni", "Malei", "Hyndla",
                 "Menglöð", "Annikki", "Lohrasp", "Osmotar", "Etelätär", "Rhodeia", "Xpiyacoc"}


def wikidata(titles):
    """English Wikipedia title -> {qid, label, desc, p21, p31}; follows Wikipedia redirects."""
    cache = json.load(open(WD_CACHE)) if os.path.exists(WD_CACHE) else {}
    need = sorted({t for t in titles if t not in cache})
    if need and not OFFLINE:
        qids, redirected = {}, set()
        for i in range(0, len(need), 45):
            chunk = need[i:i + 45]
            u = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(dict(
                action="query", titles="|".join(chunk), redirects="1", prop="pageprops", ppprop="wikibase_item",
                format="json", formatversion="2"))
            d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60))["query"]
            alias = {}
            for n in d.get("normalized", []):
                alias[n["from"]] = n["to"]
            redir = {r["from"]: r["to"] for r in d.get("redirects", [])}
            byt = {p["title"]: p.get("pageprops", {}).get("wikibase_item") for p in d.get("pages", [])}
            for t in chunk:
                t2 = alias.get(t, t)
                t3 = redir.get(t2, t2)
                if t3 != t2:
                    redirected.add(t)
                qids[t] = byt.get(t3)
            time.sleep(0.5)
        ids = sorted({q for q in qids.values() if q})
        ent = {}
        for i in range(0, len(ids), 45):
            u = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(dict(
                action="wbgetentities", ids="|".join(ids[i:i + 45]), props="labels|descriptions|claims",
                languages="en", format="json"))
            d = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60))
            for q, e in d.get("entities", {}).items():
                cl = e.get("claims", {})
                pid = lambda p: [c["mainsnak"].get("datavalue", {}).get("value", {}).get("id") for c in cl.get(p, [])]
                ent[q] = {"qid": q, "label": e.get("labels", {}).get("en", {}).get("value"),
                          "desc": e.get("descriptions", {}).get("en", {}).get("value"), "p21": pid("P21"), "p31": pid("P31")}
            time.sleep(0.5)
        for t in need:
            e = ent.get(qids.get(t)) if qids.get(t) else None
            # a Wikipedia redirect to a list, a name, a poem, a group or another figure is not this figure
            if e and t in redirected and (set(e.get("p31") or []) & REDIRECT_BLOCK or t in BAD_REDIRECTS):
                e = None
            cache[t] = e
        json.dump(cache, open(WD_CACHE, "w"), ensure_ascii=False, indent=0)
    return cache


def wd_sex(w):
    p = (w or {}).get("p21") or []
    return {("Q6581097",): "boy", ("Q6581072",): "girl"}.get(tuple(p), "")


# ----------------------------------------------------------------------------------------------- transliteration
GRK = {"α": "a", "β": "b", "γ": "g", "δ": "d", "ε": "e", "ζ": "z", "η": "ē", "θ": "th", "ι": "i", "κ": "k", "λ": "l",
       "μ": "m", "ν": "n", "ξ": "x", "ο": "o", "π": "p", "ρ": "r", "σ": "s", "ς": "s", "τ": "t", "υ": "y", "φ": "ph",
       "χ": "ch", "ψ": "ps", "ω": "ō"}


def greek_translit(s):
    d = unicodedata.normalize("NFD", s)
    rough = "̔" in d[:4]
    base = "".join(c for c in d if not unicodedata.combining(c)).lower()
    out, i = "", 0
    while i < len(base):
        two = base[i:i + 2]
        if two in ("αυ", "ευ", "ηυ", "ου"):
            out += {"αυ": "au", "ευ": "eu", "ηυ": "ēu", "ου": "ou"}[two]
            i += 2
            continue
        if two in ("γγ", "γκ", "γξ", "γχ"):
            out += "n"
            i += 1
            continue
        out += GRK.get(base[i], base[i])
        i += 1
    if rough:
        out = ("rh" + out[1:]) if out.startswith("r") else "h" + out
    return out[:1].upper() + out[1:]


KAT = dict(zip("აბგდევზთიკლმნოპჟრსტუფქღყშჩცძწჭხჯჰ",
               "a b g d e v z t i k' l m n o p' zh r s t' u p k gh q' sh ch ts dz ts' ch' kh j h".split()))
HYE = {"ու": "u", "և": "ev"}
HYE1 = dict(zip("աբգդեզէըթժիլխծկհձղճմյնշոչպջռսվտրցւփքօֆ",
                "a b g d e z ē ə tʻ zh i l kh ts k h dz gh ch m y n sh o chʻ p j ṙ s v t r tsʻ w pʻ kʻ ō f".split()))


def georgian_translit(s):
    t = "".join(KAT.get(c, c) for c in s)
    return t[:1].upper() + t[1:]


def armenian_translit(s):
    s = s.lower()
    out, i = "", 0
    while i < len(s):
        if s[i:i + 2] in HYE:
            out += HYE[s[i:i + 2]]
            i += 2
        else:
            out += HYE1.get(s[i], s[i])
            i += 1
    return out[:1].upper() + out[1:]


def translit_for(lang, form):
    if lang == "grc":
        return greek_translit(form)
    if lang == "kat":
        return georgian_translit(form)
    if lang == "hye":
        return armenian_translit(form)
    if lang in ("fas", "ara"):
        return ""
    return form


# ----------------------------------------------------------------------------------------------- matching
TYPES = {"d": "deity", "h": "human", "r": "royal", "m": "mythological_being", "p": "place", "o": "mythological_being",
         "t": "tribe"}
ARABIC_CLITICS = ("و", "ف", "ب", "ك", "ل")


def parse(block):
    out = []
    for line in block.strip().splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 4:
            continue
        name, title, forms, typ = parts[:4]
        flags = parts[4].split() if len(parts) > 4 else []
        out.append(dict(name=name, title=title, forms=forms, type=typ, review="?" in flags, ep="ep" in flags,
                        rel=next((f[4:] for f in flags if f.startswith("rel:")), None),
                        skip=[x for f in flags if f.startswith("not:") for x in f[4:].split(",")],
                        only=[x for f in flags if f.startswith("only:") for x in f[5:].split(",")]))
    return out


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def match_corpus(cfg, segs, wd, check_lines):
    L = LANGS[cfg["lang"]]
    inc = lambda ks: any(k and k.replace("_", " ") in cfg["corpus"] for k in ks)
    figs = [f for f in parse(cfg["figures"]) if not inc(f["skip"]) and (not f["only"] or inc(f["only"]))]
    preds = [(f, make_matcher(cfg["lang"], f["forms"])) for f in figs]
    hits = {i: {"n": 0, "first": None, "forms": collections.Counter(), "line": None} for i in range(len(figs))}
    memo = {}
    phrases = {}      # exact forms of several words (Hunac Ceel) are matched on the running text
    for i, (f, _p) in enumerate(preds):
        for part in f["forms"].split("/"):
            if part.startswith("="):
                for x in part[1:].split(","):
                    if " " in x.strip():
                        phrases.setdefault(i, []).append(re.compile(r"(?<!\w)" + re.escape(x.strip()) + r"(?!\w)"))
    for seg in segs:
        for i, rxs in phrases.items():
            for rx in rxs:
                for m in rx.finditer(seg.content):
                    h = hits[i]
                    h["n"] += 1
                    h["forms"][m.group(0)] += 1
                    if h["first"] is None:
                        h["first"], h["line"] = seg, seg.content
        toks = L.tok.findall(seg.content)
        if cfg["lang"] == "ara":
            toks = toks + [t[1:] for t in toks if t.startswith(ARABIC_CLITICS) and len(t) > 3]
        for t in toks:
            if t not in memo:
                memo[t] = [i for i, (_f, pred) in enumerate(preds) if pred(t)]
            for i in memo[t]:
                h = hits[i]
                h["n"] += 1
                h["forms"][nfc(t)] += 1
                if h["first"] is None:
                    h["first"], h["line"] = seg, seg.content
    rows, review, missing = [], [], []
    for i, f in enumerate(figs):
        h = hits[i]
        if not h["n"]:
            missing.append(f["name"])
            continue
        w = wd.get(f["title"])
        if w and "Q4167410" in (w.get("p31") or []):     # disambiguation page: no figure id
            w = None
        fid = w["qid"] if w else f"slug:{slug(cfg['tradition'])}:{slug(f['name'])}"
        label = (w or {}).get("label") or f["title"]
        desc = (w or {}).get("desc") or ""
        figure = f"{label}, {desc}" if desc else label
        if len(figure) > 110:
            figure = figure[:109].rstrip() + "…"
        first_form = L.norm(f["forms"].split("/")[0].lstrip("=~").split(",")[0])
        same = [k for k in h["forms"] if L.norm(k) == first_form]
        orig = same[0] if same else h["forms"].most_common(1)[0][0]
        if cfg["lang"] in ("kat", "hye", "fin", "ave") and not same:
            # prefix-matched (inflected) forms: the bare stem if the text has it, else the shortest form
            pre = [L.norm(x[1:]) for x in f["forms"].split("/") if x.startswith("~")]
            bare = [k for k in h["forms"] if L.norm(k) in pre]
            stems = [x[1:] for x in f["forms"].split("/") if x.startswith("~") and len(x) > 4]
            # Georgian/Armenian case endings are cut back to the stem the edition declines (თამარს -> თამარ)
            orig = bare[0] if bare else (stems[0] if cfg["lang"] in ("kat", "hye") and stems
                                         else min(h["forms"], key=lambda k: (len(k), -h["forms"][k])))
        seg = h["first"]
        etype = TYPES.get(f["type"], "mythological_being")
        role = {"d": "divine", "p": "word", "t": "word"}.get(f["type"], "personal")
        status, relation = "attested", ""
        if f["ep"]:
            role = "epithet"
            relation = f"another name of {label}"
        if f["rel"]:
            status, relation = "related", f"later spelling of {f['rel']}"
        translation = not cfg["original"]
        latin_script = cfg["language"] in LATIN_SCRIPT_ORIGINAL or cfg["lang"] in ("lat", "non", "fin", "ave", "quc", "haw")
        row = dict(name=f["name"], figure_id=fid, figure=figure, sex=wd_sex(w) if w else "",
                   original="" if translation else orig,
                   translit=orig if translation or latin_script else translit_for(cfg["lang"], orig),
                   language=cfg["language"], tradition=cfg["tradition"], subtradition=cfg["sub"], corpus=cfg["corpus"],
                   text=seg.text, passage=seg.passage, url=seg.url, occurrences=h["n"], entity_type=etype,
                   name_role=role, status=status, relation=relation,
                   source=cfg["source"] + ("; Wikidata (CC0)" if w else ""),
                   confidence=0.8 if cfg["ocr"] else (0.85 if translation else 0.95))
        if cfg["lang"] in ("fin", "kat", "hye", "ave") and row["confidence"] > 0.9:
            row["confidence"] = 0.9
        reasons = []
        if f["review"]:
            reasons.append("also a common word or several bearers of the name; check the passage")
        if cfg["review"]:
            reasons.append("edition of the text not stated")
        if cfg["ocr"] and h["n"] == 1:
            reasons.append("single OCR match")
        if not w:
            reasons.append("no Wikidata item matched")
            row["confidence"] = min(row["confidence"], 0.75)
        if reasons and not (reasons == ["no Wikidata item matched"]):
            row["relation"] = (row["relation"] + "; " if row["relation"] else "") + "review: " + "; ".join(reasons)
            row["confidence"] = 0.55
            review.append(row)
        else:
            rows.append(row)
        if CHECK:
            check_lines.append(f"{cfg['corpus'][:22]:22} {f['name']:18} {fid:12} {seg.passage:40} {h['line'][:110]}")
    return rows, review, missing


def write(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(COLS) + "\n")
        for r in rows:
            fh.write("\t".join(str(r.get(c, "")).replace("\t", " ").replace("\n", " ") for c in COLS) + "\n")


def main():
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    titles = sorted({f["title"] for c in CORPORA for f in parse(c["figures"])})
    wd = wikidata(titles)
    unresolved = sorted(t for t in titles if not wd.get(t))
    rows, review, check, stats = [], [], [], []
    for cfg in CORPORA:
        if only and not any(o.lower() in cfg["corpus"].lower() for o in only):
            continue
        segs = cfg["loader"]()
        if not segs:
            print(f"  {cfg['corpus']}: no text", file=sys.stderr)
            continue
        r, v, missing = match_corpus(cfg, segs, wd, check)
        rows += r
        review += v
        stats.append((cfg["corpus"], len(segs), len(r), len(v), missing))
    key = lambda r: (r["tradition"], r["corpus"], -int(r["occurrences"] or 0), r["name"])
    seen, out = set(), []
    for r in sorted(rows, key=key):
        k = (r["corpus"], r["name"], r["figure_id"])
        if k not in seen:
            seen.add(k)
            out.append(r)
    rv = [r for r in sorted(review, key=key) if (r["corpus"], r["name"], r["figure_id"]) not in seen]
    if not only:
        # Greek and Persian/Zoroastrian corpora are handled by separate builds; their rows are kept aside here.
        for path, trads in ASIDE.items():
            write(path, [r for r in out + rv if r["tradition"] in trads])
        aside = {t for trads in ASIDE.values() for t in trads}
        out = [r for r in out if r["tradition"] not in aside]
        rv = [r for r in rv if r["tradition"] not in aside]
        write(OUT, out)
        write(REVIEW, rv)
    print(f"wrote {len(out)} rows -> {OUT}; {len(rv)} -> {REVIEW}", file=sys.stderr)
    for c, nseg, nr, nv, missing in stats:
        print(f"  {c[:60]:60} segs {nseg:6}  rows {nr:4}  review {nv:4}  not found: {', '.join(missing)}", file=sys.stderr)
    if unresolved:
        print("  no Wikidata item for: " + "; ".join(unresolved), file=sys.stderr)
    if CHECK:
        print("\n".join(check))


if __name__ == "__main__":
    main()
