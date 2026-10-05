# Meanings for culture names whose Latin spelling has no Wiktionary page, read off the page of the name in its own
# script, from English Wiktionary (CC BY-SA 4.0).
#
# Candidates: rows of data/culture-names.json with no meaning whose source line says "Written <native>." (Suhani:
# "A Hindi name. Written सुहानी.") and that data/meanings.json has no meaning for.
#
#   data/native-meanings.json  {"suhani": {"m": "pleasant, agreeable", "ety": "From Hindi सुहानी (suhānī), ...",
#                               "root": "Hindi", "src": "Wiktionary", "via": "सुहानी"}, ...}
#
# A meaning is kept only when Wiktionary states it, in the right language section:
#   (a) the page has a given-name sense and the same Etymology section glosses the word the name is (a noun or
#       adjective definition there, or the {{m|..|t=}} / {{inh|..|t=}} gloss in the etymology);
#   (b) the page is an explicit form of (feminine of, inflection of ...) a word whose page satisfies (a) or defines it
#       plainly, one hop only;
#   (c) the given-name line itself gives the meaning (meaning=, "meaning ...", or an etymology "from X (“gloss”)").
# When the exact page is missing, the base form is tried only for regular feminine/masculine pairs of that language
# (Hindi -ī/-ā, Russian -а/-ий ...), and kept only if the base page lists the form or has a given-name sense.
# Hedged glosses (possibly, perhaps, uncertain, folk etymology, compare) are dropped. Nothing is made up.
#
# Polite: 50 titles a request, a contact user agent, maxlag, a pause between requests. Pages are cached in
# raw/wikt-native/ (gitignored), so a rerun reads no network.
#
#   python3 scripts/fetch_native_meanings.py
#   python3 scripts/fetch_native_meanings.py --names Suhani,Aabha     (print, don't write)
import glob, gzip, json, os, re, sys, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import fetch_wiktionary_names as fwn
import fetch_meanings as fm
from fetch_meanings import args, links, render, tidy, lang_sections, H
def lang(code): return "" if code in ("und", "") else fm.lang(code)

fwn.UA.clear(); fwn.UA["User-Agent"] = "Lullabyte/1.0 (suhanitiwari@utexas.edu)"
DATA = os.path.join(ROOT, "data")
OLD_CACHE = fm.CACHE
fm.CACHE = os.path.join(ROOT, "raw", "wikt-native")

def native_of(src):
    m = re.search(r"Written ([^.]+)\.", src or "")
    if not m: return ""
    return re.sub(r"\s*\([^)]*\)\s*$", "", m.group(1)).strip()

def candidates():
    rows = json.load(open(os.path.join(DATA, "culture-names.json"), encoding="utf-8"))
    mean = json.load(open(os.path.join(DATA, "meanings.json"), encoding="utf-8"))
    out = []
    for r in rows:
        if str(r[5]).strip(): continue
        nat = native_of(r[6])
        if not nat or mean.get(r[0].lower(), {}).get("m"): continue
        out.append(dict(name=r[0], g=r[1], culture=r[2], language=r[3], native=nat))
    return out

def load():
    fm.load_cache()
    lp = os.path.join(OLD_CACHE, "langs.json")
    if os.path.exists(lp): fm.LANG.update(json.load(open(lp, encoding="utf-8")))
    else:
        fm.CACHE = OLD_CACHE; fm.load_langs(); fm.CACHE = os.path.join(ROOT, "raw", "wikt-native")

# ---------------------------------------------------------------- which language section
ALIAS = {"Sorani": "Central Kurdish", "Serbian": "Serbo-Croatian", "Croatian": "Serbo-Croatian", "Bosnian": "Serbo-Croatian",
         "Kurmanji": "Northern Kurdish", "Odia": "Odia", "Malayali": "Malayalam"}
def section(text, row):
    secs = dict(lang_sections(text or ""))
    for L in (row["language"], ALIAS.get(row["language"]), row["culture"], ALIAS.get(row["culture"])):
        if L and L in secs: return L, secs[L]
    return None, ""

# ---------------------------------------------------------------- a language section → etymology blocks
POS_WORD = ("Noun", "Adjective")
def blocks(sec):
    """[{ety, pos: [(heading, [definition lines])]}] — one block per Etymology N, or one for the whole section."""
    hs = list(H.finditer(sec))
    numbered = [h for h in hs if re.match(r"Etymology \d", h.group(2))]
    if numbered:
        cuts = [(h.start(), h) for h in numbered] + [(len(sec), None)]
        parts = [sec[a: b] for (a, _), (b, _) in zip(cuts, cuts[1:])]
    else:
        parts = [sec]
    out = []
    for part in parts:
        hh = list(H.finditer(part)); ety = ""; pos = []
        for i, h in enumerate(hh):
            body = part[h.end(): hh[i + 1].start() if i + 1 < len(hh) else len(part)]
            head = re.sub(r"\s+\d+$", "", h.group(2))
            if head == "Etymology": ety = body.strip()
            else: pos.append((head, re.findall(r"(?m)^#\s*(?![*:#])(.*\S)", body)))
        out.append(dict(ety=ety, pos=pos, raw=part))
    return out

GN = re.compile(r"\{\{(?:given name|name translit)\||\bgiven name\b", re.I)
HEDGE = re.compile(r"possibl|perhaps|probabl|uncertain|unclear|unknown|disputed|folk etymolog|\bcompare\b|\bcf\b|maybe|may be|might|likely|"
                   r"supposed|allegedly|reinterpret|associated|influenc|conflat|separately|unrelated|several|either|or from|connected|\bsee\b", re.I)
BADG = re.compile(r"given name|surname|patronymic|diminutive|plural|genitive|ending|suffix|prefix|form of|feminine|masculine|nickname|"
                  r"\bname\b|\bcity\b|village|river|province|district|mountain range|\bdeity\b|imperative|singular|(?:first|second|third)-person|participle|"
                  r"tense|pertaining to .*language|\bletter\b|alphabet|abbreviation", re.I)
FORMOF_T = {"adj form of": "inflection", "inflection of": "inflection", "infl of": "inflection", "fem of": "feminine",
            "feminine of": "feminine", "feminine singular of": "feminine", "female equivalent of": "feminine equivalent",
            "feminine equivalent of": "feminine equivalent", "f equivalent of": "feminine equivalent", "fem equiv of": "feminine equivalent",
            "alternative form of": "variant", "alt form": "variant", "alt form of": "variant", "alternative spelling of": "variant",
            "alt sp": "variant", "alt sp of": "variant", "noun form of": "inflection", "form of": "form"}
GRAMMATICAL = {"inflection", "feminine", "variant", "form"}

def clean_gloss(g):
    g = tidy(g or "").replace("”, “", ", ")
    g = re.sub(r"^\s*\([^)]*\)\s*", "", g)                      # leading labels
    g = re.sub(r"\s*\((?:adjective|noun|verb|plural|singular)\)", "", g)
    g = re.split(r"\s+[—–]\s+|:\s", g)[0]                        # "autumn — the season following ..." → "autumn"
    if ";" in g and len(g) > 46: g = g.split(";")[0]                # "an elixir; a substance that ..." → "an elixir"
    g = re.sub(r"\s*;\s*", ", ", g).strip(" .;:,“”\"")             # "life; age" → "life, age"
    if len(g) > 46: g = re.sub(r"\s*\([^)]*\)", "", g).strip(" ,")  # long: drop the asides
    if g.count("(") > g.count(")"): g = g[: g.rfind("(")].strip(" ,;")
    bits = [b.strip() for b in g.split(",") if b.strip()]
    if len(g) > 60 or (len(g) > 46 and all(len(b) <= 24 for b in bits)):   # a long list: the first few
        g = ""
        for b in bits[:3]:
            if g and len(g) + len(b) > 46: break
            g = (g + ", " + b) if g else b
    return g

def ok_gloss(g):
    if re.search(r"[\"“”]| - ", g or ""): return False
    if re.match(r"[A-Z][a-z]+(?:/[A-Za-z]+)?,", g or ""): return False     # "Aditya, one of various deities": a person, not a meaning
    return bool(g) and 2 <= len(g) <= 60 and not BADG.search(g) and not HEDGE.search(g) and not re.search(r"[{}\[\]|]", g) \
        and not re.fullmatch(r"[A-Z][a-z]+(?: [A-Z][a-z]+)*", g)

def templates(text):
    """Every top-level template in order → (name, positional, keyword, start)."""
    out = []
    for m in re.finditer(r"\{\{((?:[^{}]|\{\{(?:[^{}]|\{\{[^{}]*\}\})*\}\})*)\}\}", text):
        pos, kw = args(m.group(1))
        if pos: out.append((pos[0].strip().lower(), pos[1:], kw, m.start()))
    return out

SRC_T = {"bor", "bor+", "der", "der+", "inh", "inh+", "lbor", "lbor+", "uder", "ubor", "slbor", "obor", "learned borrowing", "calque", "cal", "cal+"}
def ety_source(ety):
    """The first language the etymology says the word comes from (Sanskrit, Arabic ...)."""
    for name, a, kw, _ in templates(ety):
        if name in SRC_T and len(a) > 1 and lang(a[1]): return lang(a[1])
        if name == "ety":
            for x in a[1:]:
                if ":" in x and not x.startswith(":") and lang(x.split(":")[0]): return lang(x.split(":")[0])
    return ""

def first_para(ety):
    ety = re.sub(r"(?s)<ref[^>]*/>|<ref.*?</ref>|<!--.*?-->", "", ety or "")
    ety = re.sub(r"(?m)^\{\{(?:root|wp|wikipedia|was wotd|rfe|dercat)\|[^\n]*\}\}\s*$", "", ety)
    return re.split(r"\n\s*\n", ety.strip())[0] if ety.strip() else ""

def short(g):
    """One part of a compound: its first sense, at most two synonyms (fine, good, handsome; strong → fine, good)."""
    g = g.split(";")[0]
    return ", ".join(x.strip() for x in g.split(",")[:2])

def tgloss(name, a, kw):
    """A gloss-bearing template → (language code, term, gloss) or None."""
    if name in SRC_T: return (a[1] if len(a) > 1 else ""), (a[2] if len(a) > 2 else ""), kw.get("t") or kw.get("gloss") or (a[4] if len(a) > 4 else "")
    if name in ("m", "l", "mention", "link", "ll", "m+"):
        return (a[0] if a else ""), (a[1] if len(a) > 1 else ""), kw.get("t") or kw.get("gloss") or (a[3] if len(a) > 3 else "")
    return None

# words allowed between two etymology templates: "from X, the feminine form of Y, from the adjective Z" stays on the
# name's own line of descent; anything else ("a vṛddhi derivative of", "akin to", "cognate with", "as well as") stops it
CHAIN_WORDS = set("""from the a an of feminine masculine female male form variant equivalent active passive participle adjective noun
common name later earlier nominalization diminutive ultimately in turn itself borrowed inherited derived learned borrowing via
through modern origin to equivalent elative superlative""".split())
class _Chain:
    def fullmatch(self, text):
        words = re.findall(r"[^\W\d_]+", re.sub(r"<[^>]+>", "", text))
        langs = set(fm.LANG.values())
        rest = " ".join(w for w in words if w.lower() not in CHAIN_WORDS)
        return not rest or all(w in langs or w in ("Old", "Middle", "Classical", "Ancient", "Biblical", "Koine", "Medieval") for w in rest.split())
CHAIN = _Chain()
JOIN = re.compile(r"\s*(?:\+|and)\s*(?:[A-Z][a-z]+\s+)?")
def ety_gloss(ety, L):
    """→ (gloss, source language, term) from the etymology: a {{m}}/{{inh}}/{{bor}}... t= gloss, or a compound whose parts
    are all glossed (X + Y, {{af}}, {{compound}}). Hedged etymologies and cognates are skipped; a compound with an
    unglossed part gives nothing rather than half a meaning."""
    para = first_para(ety)
    if not para or re.search(r"folk etymolog|uncertain|unclear|disputed|conflat|unrelated|possibl|perhaps|probabl|as well as|generally considered|change of meaning|two (?:different|separate)", links(para), re.I): return None
    TRE = r"\{\{((?:[^{}]|\{\{(?:[^{}]|\{\{[^{}]*\}\})*\}\})*)\}\}"
    ts = templates(para)
    ends = [m.end() for m in re.finditer(TRE, para) if args(m.group(1))[0]]
    plus = "+" in re.sub(TRE, "", para)                    # a compound: only a fully glossed X + Y will do
    i, prev = 0, None
    while i < len(ts):
        name, a, kw, at = ts[i]
        # stay on the word's own line of descent: "from X, from Y" — not "a derivative of", "cognate with", "see"
        if prev is not None and not CHAIN.fullmatch(links(para[prev: at])): return None
        prev = ends[i]
        sent_start = max(para.rfind(". ", 0, at), para.rfind(".\n", 0, at))
        if HEDGE.search(links(para[sent_start + 1: at])) or name in ("cog", "cognate", "noncog", "nc"): return None
        if name in ("af", "affix", "compound", "com", "com+", "suffix", "suf", "prefix", "pre", "confix", "surf"):
            parts = [(j, t) for j, t in enumerate(a[1:], 1) if t and not t.startswith("-") and not t.endswith("-")]
            gs = [clean_gloss(kw.get(f"t{j}") or kw.get(f"gloss{j}") or "") for j, _ in parts]
            if len(parts) >= 2:
                if all(ok_gloss(g) for g in gs):
                    ls = [lang(kw.get(f"lang{j}") or a[0]) for j, _ in parts]
                    shown = " + ".join((l + " " if l and l != L and (k == 0 or l != ls[k - 1]) else "") + links(t.split("<")[0])
                                       for k, (l, (_, t)) in enumerate(zip(ls, parts)))
                    return " + ".join(short(g) for g in gs), (next((l for l in ls if l), "") or L), shown
                return None
            i += 1; continue
        tg = tgloss(name, a, kw)
        if not tg: i += 1; continue
        group = [tg]                                        # X + Y, X and Y: the name is a compound
        while i + 1 < len(ts) and JOIN.fullmatch(para[ends[i]: ts[i + 1][3]]) and tgloss(*ts[i + 1][:3]):
            i += 1; group.append(tgloss(*ts[i][:3])); prev = ends[i]
        if len(group) > 1:
            gs = [clean_gloss(g) for _, _, g in group]
            real = [g for g in gs if ok_gloss(g)]
            gs = [g.split(",")[0] if re.fullmatch(r"[A-Z][a-z]+(?:, [A-Z][a-z]+)*", g) else g for g in gs]
            names = [g for g in gs if g and not ok_gloss(g) and re.fullmatch(r"[A-Z][a-z]+", g)]   # Muhammad, Allah: kept as is
            if real and len(real) + len(names) == len(gs):
                shown, last = [], L
                for c, t, _ in group:                       # Arabic أَمَان + اللّٰه, not Arabic أَمَان + Arabic اللّٰه
                    shown.append((lang(c) + " " if lang(c) and lang(c) not in (L, last) else "") + links(t)); last = lang(c) or L
                shown = " + ".join(shown)
                return " + ".join(short(g) if ok_gloss(g) else g for g in gs), (lang(group[0][0]) or L), shown
            return None
        code, term, g = tg
        g = clean_gloss(g)
        if ok_gloss(g):
            if plus: return None                            # half of a compound is not the name's meaning
            return g, (lang(code) or L), ((lang(code) + " ") if lang(code) and lang(code) != L else "") + links(term).strip()
        i += 1
    return None

def word_def(blk, want=POS_WORD):
    """First plain definition of a noun/adjective in this block → (gloss, pos heading) or None."""
    for head, defs in blk["pos"]:
        if head not in want: continue
        for d in defs:
            if GN.search(d) or any(re.search(r"\{\{" + re.escape(k) + r"\|", d) for k in FORMOF_T): continue
            if re.search(r"\{\{(?:surname|place|form of|abbreviation|initialism|lb\|[^}]*(?:obsolete|archaic|rare|slang|vulgar))", d): continue
            g = clean_gloss(render(d))
            if ok_gloss(g): return g, head
            break   # the first sense is the word's sense; don't reach for a later one
    return None

def name_senses(blk):
    return [d for head, defs in blk["pos"] if head in ("Proper noun", "Noun") for d in defs if GN.search(d)]

def line_meaning(line):
    """Rule (c): the given-name line states the meaning."""
    g = re.search(r"\{\{given name\|((?:[^{}]|\{\{[^{}]*\}\})*)\}\}", line)
    kw = args(g.group(1))[1] if g else {}
    m = kw.get("meaning") or kw.get("meaning1") or ""
    if m and ok_gloss(clean_gloss(m)): return clean_gloss(m), None
    txt = render(line)
    q = re.search(r"\b(?:meaning|means|literally)\s*,?\s*[“\"‘]([^”\"’]{2,60})[”\"’]", txt)
    if q and ok_gloss(clean_gloss(q.group(1))) and not HEDGE.search(txt[:q.start()]): return clean_gloss(q.group(1)), None
    rest = line[g.end():] if g else ""
    eg = ety_gloss(rest, "") if rest else None
    if eg: return eg[0], eg
    return None

# ---------------------------------------------------------------- the rules
def rule_ac(sec, L):
    """(a)/(c) on one language section → dict(m, how, src, term, pos) or None."""
    for blk in blocks(sec):
        lines = name_senses(blk)
        if not lines: continue
        for line in lines:                                     # (c) the name line says what it means
            r = line_meaning(line)
            if r: return dict(m=r[0], how="line", src=(r[1][1] if r[1] else ety_source(blk["ety"])), term=(r[1][2] if r[1] else ""))
        w = word_def(blk)                                      # (a) the word the name is, in the same etymology
        if w: return dict(m=w[0], how="word", pos=w[1].lower(), src=ety_source(blk["ety"]))
        e = ety_gloss(blk["ety"], L)                           # (a) the etymology's gloss of the source word
        if e: return dict(m=e[0], how="ety", src=e[1], term=e[2])
    return None

def has_name(sec): return any(name_senses(b) for b in blocks(sec))

def form_targets(sec, code_ok):
    """Explicit form-of links → [(kind, base title)], read only from etymology blocks that hold the given-name sense
    (or, when the page has no name sense at all, from a page with a single block), so a homograph's form-of
    (سورنا Surena vs سورنا "zurna") is never used."""
    bl = blocks(sec)
    use = [b for b in bl if name_senses(b)] or (bl if len(bl) == 1 else [])
    out = []
    for b in use:
        for head, defs in b["pos"]:
            for line in defs:
                for name, a, kw, _ in templates(line):
                    if name in FORMOF_T and len(a) > 1 and a[1] and code_ok(a[0]):
                        # an inflection counts only when it is the feminine (सुहानी ← सुहाना), never a case form:
                        # В'ячеслава is also the genitive of В'ячеслав, which says nothing about the woman's name
                        if FORMOF_T[name] == "inflection" and not set(a[3:]) & {"f", "fem", "feminine"}: continue
                        out.append((FORMOF_T[name], fm.title_of(links(a[1]))))
        if name_senses(b):   # the headword names the masculine: {{uk-proper noun|В'ячесла́ва<pr>|m=В'ячесла́в}}
            for m in re.finditer(r"(?m)^\{\{[a-z-]+[ -](?:proper noun\+?|prop)\|[^\n]*?\|m=([^|}\n]+)", b["raw"]):
                out.append(("feminine equivalent", fm.title_of(links(m.group(1)).split("<")[0])))
    return list(dict.fromkeys(out))

def plain_def(sec, kind_pos):
    """A base word's plain definition: the same POS in exactly one etymology block (or the block that also has a name)."""
    found = []
    for blk in blocks(sec):
        w = word_def(blk, kind_pos)
        if w: found.append((bool(name_senses(blk)), w))
    if not found: return None
    named = [w for n, w in found if n]
    if named: return named[0]
    if len({w[0] for _, w in found}) == 1: return found[0][1]
    return None   # two different words spelled the same: don't guess

# regular feminine → masculine/base pairs, tried only when the exact page doesn't exist
BASE = {"Hindi": [("ी", "ा")], "Marathi": [("ी", "ा")], "Nepali": [("ी", "ो")], "Punjabi": [("ੀ", "ਾ")],
        "Russian": [("ая", "ый"), ("ая", "ий"), ("ия", "ий"), ("а", "")], "Bulgarian": [("ия", "ий"), ("а", "")],
        "Macedonian": [("ија", "иј"), ("а", "")], "Serbian": [("ија", "иј"), ("а", "")], "Serbo-Croatian": [("ија", "иј"), ("а", "")],
        "Ukrainian": [("ія", "ій"), ("а", "")], "Belarusian": [("ія", "ій"), ("а", "")], "Greek": [("α", "ος"), ("η", "ος")]}
def bases(native, L):
    out = []
    for f, m in BASE.get(L, []):
        if native.endswith(f) and len(native) > len(f) + 1: out.append(native[: len(native) - len(f)] + m)
    return out

CODE = {}
def code_ok_for(L):
    return lambda c: lang(c) == L or (L == "Serbo-Croatian" and c == "sh")

def resolve(row, need):
    """→ (result dict, via title) or None. need collects base pages still to fetch."""
    nat = row["native"]
    text = fm.page(nat)
    if not text:                                              # no exact page: a documented base form, if it lists this one
        L0 = row["language"]
        for b in bases(nat, ALIAS.get(L0, L0)):
            bt = fm.page(b)
            if bt is None: need.add(b); continue
            L, sec = section(bt, row)
            if not sec: continue
            if nat not in sec and not has_name(sec): continue
            r = rule_ac(sec, L) or (plain_def(sec, POS_WORD) and dict(zip(("m", "pos"), plain_def(sec, POS_WORD)), how="plain", src=""))
            if r and (nat in sec or r["how"] != "plain"):
                r.update(L=L, base=b, kind="base"); return r
        return None
    L, sec = section(text, row)
    if not sec: return None
    r = rule_ac(sec, L)
    if r: r.update(L=L); return r
    if fm.REDIR.get(nat, nat) != nat: return None             # already one redirect hop: no form-of hop after it
    for kind, base in form_targets(sec, code_ok_for(L)):     # (b) one hop to the word it is a form of
        if base == nat: continue
        bt = fm.page(base)
        if bt is None: need.add(base); continue
        bL, bsec = section(bt, dict(row, language=L))
        if not bsec: continue
        r = rule_ac(bsec, L)
        if not r and kind in GRAMMATICAL:
            want = ("Adjective",) if re.search(r"\{\{adj form of\|", sec) else POS_WORD
            p = plain_def(bsec, want)
            if p: r = dict(m=p[0], pos=p[1].lower(), how="plain", src=ety_source(bsec))
        if r and (has_name(sec) or has_name(bsec)):
            r.update(L=L, base=base, kind=kind); return r
    return None

# ---------------------------------------------------------------- transliterations (Wiktionary's own, via {{xlit}})
XLIT = {}
def code_of(L):
    cs = [c for c, n in fm.LANG.items() if n == L and re.fullmatch(r"[a-z]{2,3}", c)]
    return {"Serbo-Croatian": "sh"}.get(L) or (sorted(cs, key=len)[0] if cs else "")

def head_tr(title, L):
    """A tr= written in the page's headword line (Persian, Urdu ... have no automatic transliteration)."""
    sec = dict(lang_sections(fm.page(title) or "")).get(L, "")
    m = re.search(r"\{\{[a-z-]+(?:proper noun|noun|adj|prop|head)[^{}]*?\|tr=([^|}]+)", sec)
    return m.group(1).strip() if m else ""

def fetch_xlit(pairs):
    p = os.path.join(fm.CACHE, "xlit.json")
    if os.path.exists(p): XLIT.update(json.load(open(p, encoding="utf-8")))
    todo = sorted({(c, t) for c, t in pairs if c and t and f"{c}|{t}" not in XLIT})
    for i in range(0, len(todo), 50):
        chunk = todo[i:i + 50]
        d = fwn.api(action="expandtemplates", prop="wikitext", text="\n@@\n".join("{{xlit|%s|%s}}" % ct for ct in chunk))
        got = d.get("expandtemplates", {}).get("wikitext", "").split("\n@@\n")
        if len(got) != len(chunk): continue
        for (c, t), x in zip(chunk, got):
            XLIT[f"{c}|{t}"] = re.sub(r"<[^>]+>", "", x).strip()
        fm.time.sleep(0.5)
    json.dump(XLIT, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=0)

def tr(title, L, fallback=""):
    x = XLIT.get(f"{code_of(L)}|{title}", "")
    if x and not re.search(r"[{}<>\[\]]|error", x, re.I): return x
    return head_tr(title, L) or fallback

# ---------------------------------------------------------------- the sentence
def an(w): return ("an " if w[:1].lower() in "aeiou" else "a ") + w
def inner(r, L):
    m = r["m"]
    if r["how"] in ("word", "plain"): out = f"{an(r['pos'])} meaning “{m}”"
    elif r["how"] == "line": out = f"a given name meaning “{m}”"
    else: out = f"from {r['term']} (“{m}”)" if r.get("term") else f"meaning “{m}”"
    src = r.get("src") or ""
    if r["how"] in ("word", "plain", "line") and src and src != L and "Proto-" not in src: out += f", from {src}"
    return out

KINDWORD = {"inflection": "the feminine form of", "form": "a form of", "feminine": "the feminine of", "feminine equivalent": "the feminine equivalent of",
            "variant": "a variant of", "base": "the feminine of"}
def entry(row, r):
    L, nat = r["L"], row["native"]
    head = f"From {L} {nat} ({tr(nat, L, row['name'])})"
    if r.get("base"):
        kw = KINDWORD[r["kind"]]
        btr = tr(r["base"], L)
        ety = f"{head}, {kw} {r['base']}" + (f" ({btr})" if btr else "") + ", " + inner(r, L) + "."
    else:
        ety = f"{head}, " + inner(r, L) + "."
    src = r.get("src") or ""
    root = src if src and "Proto-" not in src else L
    return {"m": r["m"], "ety": ety, "root": root, "src": "Wiktionary", "via": nat}

def main():
    load()
    cand = candidates()
    test = sys.argv[sys.argv.index("--names") + 1].split(",") if "--names" in sys.argv else None
    rows = [c for c in cand if not test or c["name"] in test]
    print(f"{len(cand):,} candidates (no meaning, written in another script, nothing in meanings.json)", flush=True)
    fm.fetch([c["native"] for c in rows])
    for _ in range(2):                                         # base pages: the word a form points at, or a base form
        need = set()
        for c in rows: resolve(c, need)
        if not need: break
        print(f"  {len(need):,} base pages to fetch", flush=True)
        fm.fetch(sorted(need))
    found = []
    for c in rows:
        r = resolve(c, set())
        if r: found.append((c, r))
    pairs = []
    for c, r in found:
        pairs.append((code_of(r["L"]), c["native"]))
        if r.get("base"): pairs.append((code_of(r["L"]), r["base"]))
    fetch_xlit(pairs)
    out, per = {}, {}
    for c, r in found:
        k = c["name"].lower()
        if k in out: continue
        out[k] = entry(c, r); per[r["L"]] = per.get(r["L"], 0) + 1
    if test:
        for k, v in out.items(): print(k, json.dumps(v, ensure_ascii=False))
        return
    json.dump(out, open(os.path.join(DATA, "native-meanings.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"), sort_keys=True, indent=0)
    print(f"done · {len(out):,} names with a meaning")
    for L, nn in sorted(per.items(), key=lambda x: -x[1]): print(f"  {L}: {nn}")

if __name__ == "__main__":
    main()
