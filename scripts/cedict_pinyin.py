# Hanyu Pinyin for a Chinese given name, read from CC-CEDICT (MDBG, CC BY-SA 4.0): raw/tw/cedict_1_0_ts_utf-8_mdbg.txt.gz
# (https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz).
# Taiwan's Ministry of the Interior publishes names in characters only, so this is the dictionary reading, not a spelling
# anyone registered. It is given only when it is certain: the whole name is a CEDICT headword with one reading, or every
# character has exactly one reading in CEDICT (tones ignored). A name with a character that can be read two ways (樂 lè/yuè,
# 行 xíng/háng) gets no pinyin rather than a guess. Syllables are joined without tone marks, first letter capitalised
# (家豪 → Jiahao), with the pinyin apostrophe and ü kept (呂 → Lü).
import collections, gzip, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
CEDICT = os.path.join(os.path.dirname(HERE), "raw", "tw", "cedict_1_0_ts_utf-8_mdbg.txt.gz")
_words = None

def _load():
    global _words
    if _words is None:
        _words = collections.defaultdict(set)
        for line in gzip.open(CEDICT, "rt", encoding="utf-8"):
            if line.startswith("#"): continue
            m = re.match(r"(\S+) (\S+) \[([^\]]+)\]", line)
            if not m: continue
            trad, simp, py = m.groups()
            syl = [re.sub(r"[1-5]$", "", s).lower().replace("u:", "ü") for s in py.split()]
            if len(syl) != len(trad) or not all(re.fullmatch(r"[a-zü]+", s) for s in syl): continue
            _words[trad].add(tuple(syl))
    return _words

def pinyin(name):
    w = _load()
    if len(w.get(name, ())) == 1: syl = next(iter(w[name]))
    else:
        syl = []
        for ch in name:
            r = {s[0] for s in w.get(ch, ())}
            if len(r) != 1: return None
            syl.append(r.pop())
    # the pinyin apostrophe before a syllable starting with a, o or e (嘉恩 → Jia'en)
    s = syl[0] + "".join(("'" if x[0] in "aoe" else "") + x for x in syl[1:])
    return s[:1].upper() + s[1:]
