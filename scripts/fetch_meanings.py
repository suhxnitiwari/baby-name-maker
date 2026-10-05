# Meanings, etymologies and nicknames for well-known names, from English Wiktionary (CC BY-SA 4.0).
#
#   data/meanings.json   {"xavier": {"m": "new house", "ety": "From Basque ...", "root": "Basque", "src": "Wiktionary"}, ...}
#                        "via": "Xabier" marks a meaning read off the page of the name it comes from (a variant,
#                        diminutive, transliteration or etymon), never one we made up.
#   data/relations.json  [["Sasha", "diminutive", "Aleksandr", "Russian"], ...] with an optional 5th column, the pair in its
#                        own script: ["Kostas", "short_form", "Konstantinos", "Greek", ["Κώστας", "Κωνσταντίνος"]]
#                        relations: diminutive, short_form, variant, feminine_form, masculine_form, cognate
#
# Candidates: every single-word name in data/names-db.tsv held by 500+ people, every culture/scripture row with no
# meaning, and the names we know are missing one; minus names that already have a meaning (names.js REAL_RAW,
# the culture JSON files). Capped at the --cap most-held names (default 15,000) plus the must-have names.
#
# Polite: 50 titles a request, a contact user agent, maxlag, a pause between requests, retries with backoff.
# Pages are cached (gzip, quotations and translation tables stripped) in raw/wikt-meanings/, so reruns are cheap.
# The pages already downloaded by fetch_wiktionary_names.py (raw/wikt/*.json) are reused as a cache too.
#
#   python3 scripts/fetch_meanings.py              (default cap 15,000)
#   python3 scripts/fetch_meanings.py --cap 0      (no cap: every candidate)
import glob, gzip, hashlib, json, os, re, sys, time, unicodedata, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from fetch_wiktionary_names import api, UA

DATA = os.path.join(ROOT, "data")
CACHE = os.path.join(ROOT, "raw", "wikt-meanings")
MUST = """Zara Ziva Zoya Zelda Zane Zeke Zachary Xavier Xavi Xiomara Xenia Yara Yasmine Yolanda Yvette Yvonne Yelena Knox
Axel Zofia Eliška Zuzanna Maja Tereza Oliwia Karolína Barbora Kalina Danica Milana Svetlana Valerie Lucie Agnieszka Nikodem
Antoni Matěj Vojtěch Filip Lukáš Szymon Franciszek Ignacy Ondřej Václav Kryštof Bohdan Vladimir Ekaterina Polina Alisa
Veronika Ksenia Ulyana Alina Tatyana Nadezhda Lyubov Galina Oksana Vasilisa Mikhail Artem Maksim Daniil Dmitri Matvey Ilya
Andrei Aleksei Timofey Lev Nikolai Yevgeny Igor Oleg Leonid Rodion Zion Zayn Zander Zephyr Xerxes Xenophon Xanthe Xena
Yvaine Yesenia Hendrix Casimir Kirill Yegor Sergei Arseny Georgy Grigory Anatoly Fyodor""".split()

# ---------------------------------------------------------------- page cache
def fold(s): return "".join(c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c))
def shard(t): return os.path.join(CACHE, "pages-" + hashlib.md5(t.encode()).hexdigest()[0] + ".json.gz")

STORE, REDIR, DIRTY = {}, {}, set()
def load_cache():
    os.makedirs(CACHE, exist_ok=True)
    for f in glob.glob(os.path.join(CACHE, "pages-*.json.gz")): STORE.update(json.load(gzip.open(f, "rt", encoding="utf-8")))
    p = os.path.join(CACHE, "redirects.json")
    if os.path.exists(p): REDIR.update(json.load(open(p, encoding="utf-8")))
    for f in glob.glob(os.path.join(ROOT, "raw", "wikt", "*.json")):     # pages fetch_wiktionary_names.py already has
        for t, v in json.load(open(f, encoding="utf-8")).items():
            if v.get("text") and t not in STORE: STORE[t] = strip(v["text"])
def save_cache():
    by = {}
    for t in DIRTY: by.setdefault(shard(t), []).append(t)
    for f, ts in by.items():
        d = json.load(gzip.open(f, "rt", encoding="utf-8")) if os.path.exists(f) else {}
        for t in ts: d[t] = STORE[t]
        with gzip.open(f, "wt", encoding="utf-8") as fh: json.dump(d, fh, ensure_ascii=False)
    DIRTY.clear()
    json.dump(REDIR, open(os.path.join(CACHE, "redirects.json"), "w", encoding="utf-8"), ensure_ascii=False)

def strip(text):
    """Drop what we never read: quotations, translation tables, multi-line lists."""
    text = re.sub(r"(?s)\{\{trans-top.*?\{\{trans-bottom\}\}", "", text)
    return "\n".join(l for l in text.split("\n") if not re.match(r"#+[*:]|\|", l))

def page(t):
    t = REDIR.get(t, t)
    return STORE.get(t)

def fetch(titles):
    todo = sorted({t for t in titles if t and REDIR.get(t, t) not in STORE and len(t) < 200})
    for i in range(0, len(todo), 50):
        chunk = todo[i:i + 50]
        d = api(action="query", prop="revisions", rvprop="content", rvslots="main", redirects="1", titles="|".join(chunk))
        q = d.get("query", {})
        for n in q.get("normalized", []): REDIR[n["from"]] = n["to"]
        for r in q.get("redirects", []): REDIR[r["from"]] = r["to"]
        for k in list(REDIR):                                             # normalized → redirected, in one hop
            if REDIR[k] in REDIR and REDIR[REDIR[k]] != k: REDIR[k] = REDIR[REDIR[k]]
        for p in q.get("pages", {}).values():
            rev = (p.get("revisions") or [{}])[0]
            STORE[p["title"]] = strip(rev.get("slots", {}).get("main", {}).get("*", "")); DIRTY.add(p["title"])
        for t in chunk:
            if REDIR.get(t, t) not in STORE: STORE[REDIR.get(t, t)] = ""; DIRTY.add(REDIR.get(t, t))
        if (i // 50) % 20 == 19: save_cache(); print(f"    fetched {i + 50:,}/{len(todo):,}", flush=True)
        time.sleep(0.5)
    save_cache()

# ---------------------------------------------------------------- language codes (Wiktionary's own tables)
LANG = {}
def load_langs():
    p = os.path.join(CACHE, "langs.json")
    if os.path.exists(p): LANG.update(json.load(open(p, encoding="utf-8"))); return
    for mod in ("languages/code_to_canonical_name", "etymology_languages/code_to_canonical_name", "families/code_to_canonical_name"):
        url = "https://en.wiktionary.org/w/index.php?title=Module:" + mod + "&action=raw"
        for attempt in range(5):
            try: src = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode(); break
            except Exception: time.sleep(5 * (attempt + 1))
        else: continue
        for k, v in re.findall(r'\["([^"]+)"\]\s*=\s*"([^"]+)"', src): LANG.setdefault(k, v)
        time.sleep(1)
    LANG.update({"ML.": "Medieval Latin", "LL.": "Late Latin", "NL.": "New Latin", "VL.": "Vulgar Latin", "CL.": "Classical Latin",
                 "EL.": "Ecclesiastical Latin", "grc-koi": "Koine Greek", "MGr.": "Medieval Greek", "hbo": "Biblical Hebrew"})
    json.dump(LANG, open(p, "w", encoding="utf-8"), ensure_ascii=False)
def lang(code): return LANG.get(code, code if code and code[0].isupper() else "")

# ---------------------------------------------------------------- wikitext → text
def args(body):
    """Split a template body on top-level pipes → (positional, keyword)."""
    out, depth, cur = [], 0, ""
    for i, c in enumerate(body):
        if body[i:i + 2] in ("{{", "[["): depth += 1
        elif body[i:i + 2] in ("}}", "]]") and depth: depth -= 1
        if c == "|" and depth == 0: out.append(cur); cur = ""
        else: cur += c
    out.append(cur)
    pos, kw = [], {}
    for a in out:
        m = re.match(r"\s*([a-z_]+\d*)\s*=(.*)", a, re.S)
        if m: kw[m.group(1)] = m.group(2).strip()
        else: pos.append(a.strip())
    return pos, kw

def links(t): return re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", t)
def tidy(t):
    t = re.sub(r"'''?|<[^>]+>", "", links(t))
    t = re.sub(r"\(\s*\)|\(“\s*”\)", "", t)
    t = re.sub(r"\s+([,.;:])", r"\1", t)
    t = re.sub(r"[,;]\s*\.", ".", t)
    t = re.sub(r"([,;] )(Calque of|Borrowed from|Inherited from|Learned borrowing from|Doublet of|From|Diminutive of|Short form of|Variant of)\b", lambda x: x.group(1) + x.group(2)[0].lower() + x.group(2)[1:], t)
    return re.sub(r"\s+", " ", t).strip()

BORROW = {"bor": "", "der": "", "inh": "", "uder": "", "ubor": "", "lbor": "", "slbor": "", "obor": "", "learned borrowing": "",
          "bor+": "Borrowed from ", "der+": "From ", "inh+": "Inherited from ", "lbor+": "Learned borrowing from ",
          "calque": "Calque of ", "cal": "Calque of ", "cal+": "Calque of ", "sl": "", "psm": "", "translit": "Transliteration of "}
MENTION = {"m", "l", "mention", "link", "l-self", "ll", "m-self"}
COG = {"cog", "cognate", "noncog", "nc", "m+"}
PARTS = {"suf": "", "pre": "", "compound": "", "com": "", "affix": "", "af": "", "suffix": "", "prefix": "", "confix": "", "blend": "Blend of ",
         "surf": "", "surface analysis": "", "com+": ""}
FORMS = {"diminutive of": "diminutive", "dim of": "diminutive", "pet form of": "diminutive", "hypocoristic form of": "diminutive",
         "hypocorism of": "diminutive", "endearing form of": "diminutive", "short for": "short_form", "clipping of": "short_form",
         "short form of": "short_form", "abbreviation of": "short_form", "alternative form of": "variant", "alt form": "variant",
         "alt form of": "variant", "alternative spelling of": "variant", "alt sp": "variant", "alt sp of": "variant",
         "variant of": "variant", "female equivalent of": "feminine_form", "feminine of": "feminine_form",
         "feminine equivalent of": "feminine_form", "male equivalent of": "masculine_form", "masculine of": "masculine_form",
         "masculine equivalent of": "masculine_form"}
FORMWORD = {"diminutive": "Diminutive of", "short_form": "Short form of", "variant": "Variant of", "feminine_form": "Feminine form of",
            "masculine_form": "Masculine form of", "cognate": "Equivalent of", "translit": "Transliteration of", "link": "Related to"}

def render(text, rec=None):
    """Wikitext → plain text. rec collects glosses, lit=, etyma (lang code, term) and form links while rendering."""
    rec = rec if rec is not None else {}
    for k in ("gloss", "lit", "etyma", "forms"): rec.setdefault(k, [])
    text = re.sub(r"(?s)<ref[^>]*/>|<ref.*?</ref>|<!--.*?-->", "", text)
    def gl(g, tr=""):
        g = tidy(g) if g else ""
        if g: rec["gloss"].append(g)
        bits = [b for b in (tr, "“" + g + "”" if g else "") if b]
        return " (" + ", ".join(bits) + ")" if bits else ""
    def one(m):
        pos, kw = args(m.group(1))
        name = pos[0].strip().lower() if pos else ""
        a = pos[1:]
        if kw.get("lit"): rec["lit"].append(tidy(kw["lit"]))
        litx = f", literally “{tidy(kw['lit'])}”" if kw.get("lit") else ""
        if name in BORROW:
            src = a[1] if len(a) > 1 else ""; term = a[2] if len(a) > 2 else ""
            alt = a[3] if len(a) > 3 else ""; g = kw.get("t") or kw.get("gloss") or (a[4] if len(a) > 4 else "")
            if term and term != "-": rec["etyma"].append((src, links(term)))
            if lang(src): rec.setdefault("srcs", []).append(lang(src))
            word = "" if term in ("", "-") else " " + (alt or term)
            return BORROW[name] + lang(src) + word + gl(g, kw.get("tr", "")) + litx
        if name in MENTION:
            term = a[1] if len(a) > 1 else ""; alt = a[2] if len(a) > 2 else ""
            g = kw.get("t") or kw.get("gloss") or (a[3] if len(a) > 3 else "")
            if term: rec["etyma"].append((a[0], links(term)))
            return (alt or term) + gl(g, kw.get("tr", "")) + litx
        if name in COG:
            term = a[1] if len(a) > 1 else ""; g = kw.get("t") or kw.get("gloss") or (a[3] if len(a) > 3 else "")
            if term and term != "-": rec.setdefault("cog", []).append((a[0], links(term)))
            return lang(a[0]) + ("" if term in ("", "-") else " " + (a[2] if len(a) > 2 and a[2] else term)) + gl(g, kw.get("tr", ""))
        if name in ("doublet", "dbt"):
            ts = [links(t) for t in a[1:] if t]
            for t in ts: rec["forms"].append(("cognate", a[0], t))
            return ("doublet of " if "nocap" in kw else "Doublet of ") + " and ".join(ts)
        if name in ("ety",):   # {{ety|en|:bor|ru:Бори́с}}
            out, verb = [], "From"
            for x in a[1:]:
                if x.startswith(":"): verb = {":bor": "Borrowed from", ":inh": "Inherited from", ":lbor": "Learned borrowing from"}.get(x.split("<")[0], "From")
                elif ":" in x:
                    c, t = x.split(":", 1); t = t.split("<")[0]
                    rec["etyma"].append((c, t))
                    if lang(c): rec.setdefault("srcs", []).append(lang(c))
                    out.append(("from " if out else verb + " ") + lang(c) + " " + t)
            return ", ".join(out)
        if name in PARTS:
            out = []; rec.setdefault("parts", [])
            for j, t in enumerate(a[1:], 1):
                if not t: continue
                t = t.split("<")[0]
                if name in ("suffix", "suf") and j > 1 and not t.startswith("-"): t = "-" + t
                g = kw.get(f"t{j}") or kw.get(f"gloss{j}") or ""
                al = kw.get(f"alt{j}") or ""
                out.append((al or t) + gl(g, kw.get(f"tr{j}", "")))
                if g: rec["parts"].append(tidy(g))
                rec["etyma"].append((kw.get(f"lang{j}") or a[0], links(t)))
            return PARTS[name] + " + ".join(out) + litx
        if name in FORMS:
            t = a[1] if len(a) > 1 else ""
            if t: rec["forms"].append((FORMS[name], a[0], links(t)))
            return FORMWORD[FORMS[name]].lower() + " " + (a[2] if len(a) > 2 and a[2] else t)
        if name in ("dim", "diminutive", "hypocorism", "clipping", "clip", "short"):
            t = a[1] if len(a) > 1 else ""
            kind = "diminutive" if name.startswith(("dim", "hypo")) else "short_form"
            if t: rec["forms"].append((kind, a[0], links(t)))
            return FORMWORD[kind] + " " + t if t else ""
        if name in ("w", "wikipedia", "lw"): return pos[2] if len(pos) > 2 and pos[2] else pos[1] if len(pos) > 1 else ""
        if name in ("etyl",): return lang(a[0]) if a else ""
        if name in ("lang",): return a[1] if len(a) > 1 else ""
        if name in ("q", "qualifier", "i", "qual", "gloss", "gl"): return "(" + ", ".join(a) + ")"
        if name in ("ndash",): return "–"
        if name in ("nbsp",): return " "
        if name in ("coinage", "coin"): return "Coined by " + (a[1] if len(a) > 1 else "")
        if name in ("named-after", "named after"): return "Named after " + (a[1] if len(a) > 1 else "")
        if name in ("unk", "unknown"): return "Of unknown origin"
        if name in ("given name",):
            g = a[1] if len(a) > 1 else ""
            return f"A {g} given name" + (f" from {kw['from']}" if kw.get("from") else "") + (f" meaning “{kw['meaning']}”" if kw.get("meaning") else "")
        return ""
    for _ in range(6):
        n = re.subn(r"\{\{((?:[^{}]|\{(?!\{)|\}(?!\}))*)\}\}", one, text)
        text = n[0]
        if not n[1]: break
    return tidy(re.sub(r"\{\{|\}\}", "", text))

# ---------------------------------------------------------------- reading a page
H = re.compile(r"(?m)^(=+)\s*(.+?)\s*\1\s*$")
def lang_sections(text):
    hs = [m for m in H.finditer(text) if len(m.group(1)) == 2]
    return [(m.group(2), text[m.end(): hs[i + 1].start() if i + 1 < len(hs) else len(text)]) for i, m in enumerate(hs)]

GN_LINE = re.compile(r"given name|name translit|" + "|".join(re.escape(k) for k in FORMS), re.I)
NOT_NAME = re.compile(r"[A-Z]")
def namelike(g, names):
    g = g.strip(" .")
    return bool(re.fullmatch(r"[A-ZÀ-Þ][^\s]*(?: (?:and|or) [A-ZÀ-Þ][^\s]*)?", g)) or (g[:1].isupper() and g.lower() in names) or g in LANG.values()

def senses(text, prefer=()):
    """Every given-name sense on a page: dict(lang, params, line, ety (wikitext), alts)."""
    out = []
    for L, sec in lang_sections(text or ""):
        ety, alts = "", []
        hs = list(H.finditer(sec))
        for i, h in enumerate(hs):
            body = sec[h.end(): hs[i + 1].start() if i + 1 < len(hs) else len(sec)]
            head = h.group(2)
            if head.startswith("Etymology"): ety = body.strip()
            elif head == "Alternative forms":
                alts += [links(t) for t in re.findall(r"\{\{(?:alt|alter|l)\|[^|}]+\|([^|}]+)", body)]
            elif head in ("Proper noun", "Noun"):
                for line in re.findall(r"(?m)^#+\s*(?![*:])(.*)$", body):
                    if not GN_LINE.search(line) or (head == "Noun" and "given name" not in line): continue
                    if re.match(r"\s*\{\{surname\|", line) and "given name" not in line: continue
                    gn = re.search(r"\{\{(given name|name translit)\|((?:[^{}]|\{\{[^{}]*\}\})*)\}\}", line)
                    pos, kw = args(gn.group(2)) if gn else ([], {})
                    if gn and gn.group(1) == "name translit": kw.setdefault("xlit_of", pos[2] if len(pos) > 2 else ""); kw["xlit_lang"] = pos[1] if len(pos) > 1 else ""
                    out.append(dict(lang=L, kw=kw, line=line, ety=ety, alts=alts))
    rank = {l: i for i, l in enumerate(("English",) + tuple(prefer))}
    return sorted(out, key=lambda s: rank.get(s["lang"], 99))

BAD_GLOSS = re.compile(r"suffix|prefix|patronymic|diminutive|plural|genitive|ending|given name|surname|nickname|feminine|masculine|form of", re.I)
def first_para(ety):
    ety = re.split(r"\n\s*\n|\n(?=\{\{(?:root|dercat|PIE root)\b)", ety.strip())[0] if ety else ""
    return re.sub(r"(?m)^\*\s*", "", ety)

def read_sense(s, names):
    """→ m, ety, root, relations, follow targets (list of (kind, lang code or name, title))."""
    kw, rec = s["kw"], {}
    para = first_para(s["ety"])
    ety_txt = render(para, rec) if para else ""
    sents = [x for x in re.split(r"(?<=[.;])\s+(?=[A-Z])", ety_txt) if not x.startswith("First recorded")
             and not re.search(r"\b(of|from|to|and|with|as|by)[.;]?$", x) and len(x) > 14 and not re.search(r"\bof -|^-", x) and not re.fullmatch(r"(See|From|Diminutives?|Shortened|Short form|Clipping)\b.{0,3}", x)]
    ety = sents[0] if sents else ""
    if len(sents) > 1 and len(ety) + len(sents[1]) < 200: ety += " " + sents[1]
    if len(ety) > 240:
        cut = max(ety.rfind(", from ", 0, 230), ety.rfind("; ", 0, 230), ety.rfind(", ", 60, 230))
        ety = ety[:cut] if cut > 60 else ety[:228].rsplit(" ", 1)[0] + "…"
    if ety and not ety.endswith((".", "…", "?", "!")): ety = ety.rstrip(";:,") + "."
    ety = ety.lstrip(",;:. ") if ety else ""
    if ety: ety = ety[0].upper() + ety[1:]
    if not re.search(r"[A-Za-z]{3}", ety or "") or re.fullmatch(r"From [a-zà-ÿ]{1,4}\.", ety or ""): ety = ""
    # the meaning: an explicit meaning= / quoted gloss on the sense line, then lit=, then the etymon glosses
    linerec = {}; line_txt = render(s["line"], linerec)
    m = tidy(kw.get("meaning") or kw.get("meaning1") or "")
    if not m:
        q = re.search(r"\b(?:meaning|means|literally|lit\.)\s*,?\s*[“\"‘]([^”\"’]{2,60})[”\"’]", line_txt)
        if q: m = q.group(1)
    mixed = re.search(r"conflation|two unrelated|several unrelated|different origins|multiple origins", ety_txt, re.I)
    ety_q = re.sub(r"\b(meaning|means|literally|lit\.)\s*,?\s*[\"‘]([^\"’]{2,60})[\"’]", r"\1 “\2”", ety_txt)
    if not m and not mixed and len(rec.get("parts", [])) >= 2 and not any(namelike(g, names) for g in rec["parts"]):
        m = " + ".join(dict.fromkeys(rec["parts"][:3]))
    if not m and not mixed:
        # the first gloss that isn't hedged (folk etymology, "compare", "associated with" ...)
        for q in re.finditer(r"“([^”]{2,60})”", ety_q):
            before = re.split(r"[.;]\s", ety_q[:q.start()])[-1]
            if namelike(q.group(1), names) or BAD_GLOSS.search(q.group(1)) or re.search(r"folk|associat|compare|\bcf\b|unrelated|perhaps|possibly|probably|influenc|confus|doubt|popular|reinterpret|not from|rather than|apparently|the other|also from|or from", before, re.I): continue
            m = q.group(1); rest = ety_q[q.end():]
            while len(m) < 60:   # a compound: *boľьjь (“greater”) + *slava (“fame, renown”)
                j = re.match(r"\)?\s*\+\s*[^“()+]{0,40}\([^“)]*“([^”]{2,60})”", rest)
                if not j or BAD_GLOSS.search(j.group(1)): break
                m += " + " + j.group(1); rest = rest[j.end():]
            break
    m = m.strip(" .;,") if m else ""
    if re.search(r"given name|surname|\{|\}|\[|\]", m) or len(m) > 70: m = ""
    # where it is ultimately from
    root = ""
    fr = kw.get("from") or kw.get("origin") or ""
    if fr:
        last = re.split(r"\s*[<,]\s*", links(fr))[-1].strip()
        if not re.search(r"surname|place|given|nickname|word|coin|the ", last, re.I): root = last
    if not root:
        srcs = rec.get("srcs", [])
        if srcs: root = srcs[-1]
    if not root:
        f = re.search(r"given name\b[^.]*?\bfrom ([A-Z][a-z]+(?: [A-Z][a-z]+)?)", line_txt)
        root = f.group(1) if f and f.group(1) in LANG.values() else s["lang"]
    # relations, and pages that might hold the meaning
    rel, follow = [], []
    def targets(v): return [links(t).strip() for t in re.split(r"\s*(?:,|<<|>>|\band\b)\s*", v) if links(t).strip()]
    for key, kind in (("dimof", "diminutive"), ("dim", "diminutive"), ("diminutive", "diminutive"), ("varof", "variant"),
                      ("var", "variant"), ("clipof", "short_form"), ("eq", "cognate"), ("m", "feminine_form"), ("f", "masculine_form")):
        for t in targets(kw.get(key, "")):
            rel.append((kind, t)); follow.append((kind, s["lang"] if kind != "cognate" else "English", t))
    for key, kind in (("dimform", "diminutive"), ("varform", "variant")):
        for t in targets(kw.get(key, "")): rel.append(("rev_" + kind, t))
    for word, t in re.findall(r"(short for|diminutive of|pet form of|variant of|feminine form of|masculine form of|related to)\s+\[\[([^\]|#]+)", s["line"]):
        kind = {"short for": "short_form", "diminutive of": "diminutive", "pet form of": "diminutive", "variant of": "variant",
                "feminine form of": "feminine_form", "masculine form of": "masculine_form"}.get(word)
        if kind: rel.append((kind, t)); follow.append((kind, s["lang"], t))
    for kind, code, t in linerec.get("forms", []):
        rel.append((kind, t)); follow.append((kind, lang(code) or s["lang"], t))
    for kind, code, t in rec.get("forms", []):
        if kind == "cognate" and NOT_NAME.match(t or ""): rel.append(("cognate", t))
    for code, t in rec.get("cog", []):
        if t and t[0].isupper() and lang(code): rel.append(("cognate@" + lang(code), t))
    if kw.get("xlit_of"): follow.append(("translit", lang(kw.get("xlit_lang", "")), kw["xlit_of"]))
    for code, t in rec.get("etyma", []):
        if lang(code): follow.append(("ety", lang(code), t))
    for t in re.findall(r"\[\[([^|\]#]+)", s["line"] + " " + para):
        if t[:1].isupper(): follow.append(("link", s["lang"], t))
    for a in s["alts"]: rel.append(("rev_variant", a))
    return m, ety, root, rel, follow

# ---------------------------------------------------------------- name families in their own script
REL = {}
def add(a, kind, b, L, nat=None):
    k = (a.strip(), kind, b.strip(), L)
    if nat or k not in REL: REL[k] = nat or REL.get(k)

GREEK = re.compile(r"[\u0370-\u03ff\u1f00-\u1fff]")
def greek_titles():
    p = os.path.join(CACHE, "greek-members.json")
    if os.path.exists(p): return json.load(open(p, encoding="utf-8"))
    from fetch_wiktionary_names import members
    d = api(action="query", list="allcategories", acprefix="Greek ", aclimit="500", acprop="size")
    cats = [c["*"] for c in d["query"]["allcategories"] if re.search(r"given names|diminutives of", c["*"]) and c.get("pages")]
    out = sorted({t for c in cats for t in members(c) if GREEK.search(t)})
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    return out

GR = [("μπ", "b", "mp"), ("ντ", "d", "nt"), ("γκ", "g", "gk"), ("γγ", "ng", "ng"), ("ου", "ou", "ou"), ("αι", "ai", "ai"), ("ει", "ei", "ei"),
      ("οι", "oi", "oi"), ("ψ", "ps", "ps"), ("ξ", "x", "x"), ("χ", "ch", "ch"), ("θ", "th", "th")]
GR1 = dict(zip("αβγδεζηικλμνοπρσςτυφω", "avgdeziiklmnoprsstyfo"))
def greek_latin(t):
    """Modern Greek → Latin the way Greeks spell their names in passports (Γιάννης → Giannis, Κωνσταντίνος → Konstantinos)."""
    w = "".join(c for c in unicodedata.normalize("NFD", t.lower()) if not unicodedata.combining(c))
    out, i = "", 0
    while i < len(w):
        if w[i:i + 2] in ("αυ", "ευ"):
            nxt = w[i + 2: i + 3]
            out += w[i] .replace("α", "a").replace("ε", "e") + ("f" if not nxt or nxt in "θκξπσςτφχψ" else "v"); i += 2; continue
        for g, first, mid in GR:
            if w.startswith(g, i): out += first if i == 0 else mid; i += len(g); break
        else:
            out += GR1.get(w[i], w[i]); i += 1
    return out[:1].upper() + out[1:]

FORMOF = (("dimin", "diminutive"), ("pet", "diminutive"), ("hypocor", "diminutive"), ("short", "short_form"), ("everyday", "short_form"),
          ("clipp", "short_form"), ("feminine", "feminine_form"), ("female", "feminine_form"), ("masculine", "masculine_form"),
          ("male", "masculine_form"), ("", "variant"))
def kind_of(label): return next(k for w, k in FORMOF if w in label.lower())

def native_relations(L, pages):
    """→ (latin name, relation, latin related, [native name, native related]) for one language's pages."""
    xl, found = {}, []
    for t, text in pages.items():
        sec = dict(lang_sections(text or "")).get(L, "")
        if not sec: continue
        g = re.search(r"\{\{given name\|((?:[^{}]|\{\{[^{}]*\}\})*)\}\}", sec)
        kw = args(g.group(1))[1] if g else {}
        if kw.get("xlit"): xl[t] = links(re.split(r"\s*,\s*", kw["xlit"])[0])
        rels = []
        def targets(v): return [title_of(o.strip()) for o in re.split(r"\s*(?:,|<<|>>)\s*", links(v)) if o.strip()]
        for key, kind in (("dimof", "diminutive"), ("varof", "variant"), ("clipof", "short_form"), ("eq", "cognate"),
                          ("m", "feminine_form"), ("f", "masculine_form")):
            rels += [(t, kind, o) for o in targets(kw.get(key, ""))]
        for key, kind in (("dimform", "diminutive"), ("varform", "variant")):
            rels += [(o, kind, t) for o in targets(kw.get(key, ""))]
        for line in re.findall(r"(?m)^#+\s*(?![*:])(.*)$", sec):
            for lab, o in re.findall(r"\{\{form of\|[^|}]*\|([^|}]*)\|([^|}]+)", line): rels.append((t, kind_of(lab), title_of(o)))
            rec = {}; render(line, rec)
            rels += [(t, k, title_of(o)) for k, _, o in rec.get("forms", []) if k != "cognate"]
            for lab, o in re.findall(r"(diminutive|short(?:ened)?|everyday|common|familiar|pet|feminine|masculine|variant|alternative)[^\[\]{}#]{0,40}?(?:form of|of|for) \[\[([^\]|#]+)", line, re.I):
                rels.append((t, kind_of(lab), title_of(o)))
        ety = re.search(r"(?ms)^===+\s*Etymology[^=]*===+\s*$(.*?)(?=^==)", sec)
        if ety:
            for code, o in re.findall(r"\{\{(?:dbt|doublet)\|([^|}]+)\|([^|}]+)", ety.group(1)):
                if lang(code) == L: rels.append((t, "variant", title_of(o)))
        for o, extra in re.findall(r"\{\{l\|[^|}]+\|([^|}]+)((?:\|[^}]*)?)\}\}", sec):
            if re.search(r"pos=diminutive|t=diminutive", extra): rels.append((title_of(o), "diminutive", t))
        if "diminutives of" in sec and not any(r[0] == t for r in rels):
            see = re.search(r"\{\{see\|[^|}]+\|([^|}]+)", sec)
            if see: rels.append((t, "diminutive", title_of(see.group(1))))
        found += rels
    def lat(n):
        if latin(n): return n
        if L == "Greek" and GREEK.search(n): return greek_latin(n)   # one consistent spelling (xlit lists vary: Ioannis/Giannis)
        return xl.get(n, "")
    for a, kind, b in found:
        if not a or not b or a == b: continue
        la, lb = lat(a), lat(b)
        if not la or not lb: continue
        yield la, kind, lb, ([a, b] if not (latin(a) and latin(b)) else None)

def title_of(t):
    """Wiktionary drops stress marks and macrons from page titles (Михаи́л → Михаил)."""
    t = links(t).strip()
    if GREEK.search(t): return unicodedata.normalize("NFC", t)
    t = unicodedata.normalize("NFC", "".join(c for c in unicodedata.normalize("NFD", t) if c not in "́̀̄̆" or not re.search(r"[A-Za-z]", t) and c == "̆"))
    return t
def titles_for(t):
    t = links(t).strip()
    a = unicodedata.normalize("NFC", "".join(c for c in unicodedata.normalize("NFD", t) if c not in "́̀"))
    b = title_of(t)
    return list(dict.fromkeys([a, b]))

# ---------------------------------------------------------------- main
def main():
    cap = 15000
    if "--cap" in sys.argv: cap = int(sys.argv[sys.argv.index("--cap") + 1])
    load_cache(); load_langs()

    # names that already have a meaning
    have = set()
    raw = open(os.path.join(ROOT, "names.js"), encoding="utf-8").read()
    real = raw.split("const REAL_RAW = `", 1)[1].split("`", 1)[0]
    for line in real.strip().split("\n"):
        f = line.split("|")
        if len(f) > 5 and f[5].strip(): have.add(f[0].strip().lower())
    rows_empty = {}
    for fn in ("culture-names.json", "scripture-names.json", "also-cultures.json", "hebrew-names.json"):
        p = os.path.join(DATA, fn)
        if not os.path.exists(p): continue
        for r in json.load(open(p, encoding="utf-8")):
            if len(r) > 5 and str(r[5]).strip(): have.add(r[0].lower())
            elif fn in ("culture-names.json", "scripture-names.json") and len(r) > 5: rows_empty.setdefault(r[0], r[3] or r[2])

    count, spellings = {}, {}
    for line in open(os.path.join(DATA, "names-db.tsv"), encoding="utf-8"):
        f = line.rstrip("\n").split("\t")
        if len(f) < 4: continue
        n, c = f[0], int(f[3] or 0)
        count[n] = max(c, count.get(n, 0))
        spellings.setdefault(fold(n).lower(), []).append((c, n))
    names_lower = {n.lower() for n in count}

    cand = {}
    for n, c in count.items():
        if c >= 500 and re.fullmatch(r"[^\s\-.,/0-9]+", n): cand[n] = ""
    for n, l in rows_empty.items():
        if re.fullmatch(r"[^\s.,/0-9]+", n) and not n.startswith("-") and not n.endswith("-"): cand.setdefault(n, l)
    must = [n for n in MUST if n.lower() not in have]
    cand = {n: l for n, l in cand.items() if n.lower() not in have}
    ranked = sorted(cand, key=lambda n: -count.get(n, 0))
    total = len(ranked)
    keep = ranked[:cap] if cap else ranked
    keep = list(dict.fromkeys(keep + must))
    test = "--names" in sys.argv
    if test: keep = sys.argv[sys.argv.index("--names") + 1].split(",")
    print(f"{total:,} candidates without a meaning · looking up {len(keep):,} (cap {cap or 'none'}; {len(must)} must-have)", flush=True)

    def tries(n):
        """The registry spelling, capitalized, plus accented spellings the registry also has (Eliska → Eliška)."""
        t = [n, n[:1].upper() + n[1:]]
        acc = [s for _, s in sorted(spellings.get(fold(n).lower(), []), reverse=True) if s != n and s != fold(s)][:3]
        return list(dict.fromkeys(t + acc + [s[:1].upper() + s[1:] for s in acc]))

    print("fetching name pages", flush=True)
    fetch([t for n in keep for t in tries(n)])

    # first pass on every name, then fetch the pages it points at (etyma, the full name of a diminutive, ...), twice
    def analyse(n, prefer):
        best = None; allfollow = []; rels = []
        for t in tries(n):
            for s in senses(page(t), prefer):
                m, ety, root, rel, follow = read_sense(s, names_lower)
                rels += [(t, s["lang"], r) for r in rel]
                allfollow += [(f, ety, root) for f in follow]
                score = (bool(m), s["lang"] == "English" or s["lang"] in prefer, bool(ety))
                if best is None or score > best[0]: best = (score, m, ety, root)
        return best, allfollow, rels

    def resolve_follow(kind, L, t, depth, seen):
        """A meaning from the page of a related name/etymon, in its language section."""
        if depth > 3 or (L, t) in seen: return None
        seen.add((L, t))
        for tt in titles_for(t):
            txt = page(tt)
            if txt is None: NEED.add(tt); continue
            al = senses(txt, (L,))
            ss = [s for s in al if s["lang"] == L] + [s for s in al if s["lang"] == "English" and L != "English"]
            if not L: ss = ss or al[:3]
            if not ss:   # an ordinary word: its first sense is the gloss (Svetlana ← свет "light")
                for Lx, sec in lang_sections(txt):
                    if Lx != L: continue
                    w = re.search(r"(?ms)^===+\s*(Noun|Adjective|Verb)\s*===+\s*$.*?^#\s*([^:*\n][^\n]*)", sec)
                    if w and kind == "ety":
                        g = render(w.group(2))
                        if 2 < len(g) < 50 and not re.search(r"given name|surname|form of|plural|city|village|river", g, re.I):
                            return g, "", L, t
                continue
            for s in ss:
                m, ety, root, rel, follow = read_sense(s, names_lower)
                if m: return m, ety, root, t
                for k2, L2, t2 in follow:
                    if k2 in ("diminutive", "variant", "short_form", "translit", "ety", "cognate") and (L2 in (L, s["lang"]) or k2 in ("ety", "translit", "cognate")):
                        r = resolve_follow(k2, L2, t2, depth + 1, seen)
                        if r: return r[0], ety or r[1], r[2], t
        return None

    global NEED
    for rnd in range(5):
        NEED = set()
        for n in keep:
            best, allfollow, _ = analyse(n, (cand.get(n),) if cand.get(n) else ())
            if best and best[1]: continue
            for (kind, L, t), _, _ in allfollow[:12]: resolve_follow(kind, L, t, 1, set())
        NEED -= set(STORE)
        print(f"  round {rnd + 1}: {len(NEED):,} related pages to fetch", flush=True)
        if not NEED: break
        fetch(sorted(NEED))

    out = {}
    for n in keep:
        prefer = (cand.get(n),) if cand.get(n) else ()
        best, allfollow, rels = analyse(n, prefer)
        for t, L, (kind, other) in rels:
            other = other.strip()
            if kind.startswith("cognate@"): kind, L = "cognate", kind.split("@")[1]
            if kind.startswith("rev_"): add(other, kind[4:], t, L)
            else: add(t, kind, other, L)
        if not best: continue
        _, m, ety, root = best
        e = {"m": m, "ety": ety, "root": root, "src": "Wiktionary"}
        if not m:
            NEED = set()
            for (kind, L, t), ety0, root0 in allfollow:
                if kind in ("link", "ety") and re.search(r"possibl|perhaps|probabl|inspired|influenc|uncertain|unknown|unclear|coin", e["ety"] or "", re.I): continue
                r = resolve_follow(kind, L, t, 1, set())
                if r:
                    e["m"] = r[0]
                    if title_of(r[3]) != title_of(n): e["via"] = r[3]
                    if not e["ety"]:
                        more = re.split(r"(?<=\.)\s+", r[1] or "")[0] if kind in ("ety", "translit") else ""
                        if len(more) > 140 or re.search(r"[^\u0000-\u052f\u2000-\u206f]", more): more = ""
                        e["ety"] = (FORMWORD.get(kind, "From") + " " + (t if kind != "ety" else r[3]) + ". " + more).strip()
                    if r[2] and kind in ("ety", "translit", "diminutive", "variant", "short_form", "cognate"): e["root"] = r[2]
                    break
        if not e["m"] and not e["ety"]: continue
        if not e["root"]: del e["root"]
        if not e.get("ety"): e.pop("ety", None)
        out[n.lower()] = e

    # relations among native-script names (Маша → Мария, Γιάννης → Ιωάννης), from the pages fetch_wiktionary_names.py
    # already has plus every page in Wiktionary's Greek given-name and diminutive categories
    by_lang = {}
    for f in glob.glob(os.path.join(ROOT, "raw", "wikt", "*.json")):
        L = os.path.basename(f)[:-5].replace("_", " ")
        by_lang[L] = {t: v.get("text", "") for t, v in json.load(open(f, encoding="utf-8")).items()}
    greek = greek_titles()
    fetch(greek)
    by_lang.setdefault("Greek", {}).update({t: page(t) for t in greek if page(t)})
    for L, pages in by_lang.items():
        for me, kind, other, nat in native_relations(L, pages):
            add(me, kind, other, L, nat)

    rel = sorted((list(k) + ([v] if v else [])) for k, v in REL.items() if latin(k[0]) and latin(k[2]) and k[0] != k[2] and k[3]
                 and len(k[0]) < 30 and len(k[2]) < 30 and k[2][:1].isupper() and k[0][:1].isupper())
    if test:
        for n in keep: print(n, json.dumps(out.get(n.lower()), ensure_ascii=False))
        for r in rel:
            if r[0] in keep or r[2] in keep or len(r) > 4 and r[3] == "Greek": print(r)
        return
    json.dump(out, open(os.path.join(DATA, "meanings.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    json.dump([list(r) for r in rel], open(os.path.join(DATA, "relations.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    withm = sum(1 for v in out.values() if v["m"])
    print(f"done · {withm:,} meanings · {len(out) - withm:,} etymology only · {len(keep) - len(out):,} nothing · {len(rel):,} relations "
          f"({sum(1 for r in rel if len(r) > 4):,} with native script, {sum(1 for r in rel if r[3] == 'Greek'):,} Greek)")

def latin(s): return bool(s) and all(ord(c) < 0x250 or c in "’ʻ" or unicodedata.category(c).startswith("M") for c in s) and bool(re.search(r"[A-Za-z]", fold(s)))
NEED = set()

if __name__ == "__main__":
    main()
