"""Original-script forms from each name's own Wiktionary etymology (Aisha ← Arabic عَائِشَة, Maral ← Persian مارال).

For the hand-written names (names.js) that have no original-script form yet, fetch the English Wiktionary page and read the
etymology templates of the name's own entry ({{der|en|ar|عَائِشَة}}, {{bor|..}}, {{inh|..}}, {{m|fa|مارال}}): every non-Latin
form with its language. Cached in raw/wikt-native-ety/. Output: data/native-ety.json { folded name: [[form, language], ...] },
which build_native_forms.py folds into data/native-forms.json.
"""
import gzip, json, os, re, time, unicodedata, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "raw", "wikt-native-ety"); os.makedirs(CACHE, exist_ok=True)
UA = {"User-Agent": "Lullabyte/1.0 (suhanitiwari@utexas.edu)"}
LANG = {"ar": "Arabic", "fa": "Persian", "ur": "Urdu", "he": "Hebrew", "hbo": "Hebrew", "grc": "Greek", "el": "Greek", "sa": "Sanskrit", "hi": "Hindi",
        "bn": "Bengali", "pa": "Punjabi", "ta": "Tamil", "te": "Telugu", "ml": "Malayalam", "kn": "Kannada", "gu": "Gujarati", "mr": "Marathi", "ne": "Nepali",
        "ru": "Russian", "uk": "Ukrainian", "be": "Belarusian", "bg": "Bulgarian", "sr": "Serbian", "mk": "Macedonian", "hy": "Armenian", "xcl": "Armenian",
        "ka": "Georgian", "am": "Amharic", "gez": "Ge'ez", "arc": "Aramaic", "syc": "Aramaic", "ja": "Japanese", "zh": "Chinese", "cmn": "Chinese", "ko": "Korean",
        "th": "Thai", "kk": "Kazakh", "ky": "Kyrgyz", "tt": "Tatar", "ba": "Bashkir", "ps": "Pashto", "ota": "Ottoman Turkish", "yi": "Yiddish", "pal": "Middle Persian",
        "peo": "Old Persian", "ae": "Avestan", "my": "Burmese", "km": "Khmer", "lo": "Lao", "bo": "Tibetan", "mn": "Mongolian", "dv": "Dhivehi", "si": "Sinhala"}
def fold(s):
    s = unicodedata.normalize("NFD", s.lower()); return re.sub(r"[\s-]", "", "".join(c for c in s if unicodedata.category(c) != "Mn"))
LATIN = re.compile(r"^[\sA-Za-zÀ-ɏḀ-ỿ'’.\-]+$")

def names():
    src = open(os.path.join(ROOT, "names.js"), encoding="utf-8").read()
    raw = src[src.index("REAL_RAW = `") + 12: src.index("`;", src.index("REAL_RAW = `"))]
    return [l.split("|")[0] for l in raw.strip().split("\n") if l.count("|") >= 5]

def fetch(titles):
    q = urllib.parse.urlencode({"action": "query", "prop": "revisions", "rvprop": "content", "rvslots": "main", "format": "json", "formatversion": 2,
                                "titles": "|".join(titles)})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request("https://en.wiktionary.org/w/api.php?" + q, headers=UA), timeout=40) as r:
                d = json.load(r)
            return {p["title"]: p["revisions"][0]["slots"]["main"]["content"] for p in d["query"]["pages"] if "revisions" in p}
        except Exception:
            time.sleep(2 * (attempt + 1))
    return {}

def forms(text):
    out = []
    # only the English, Translingual or name-language sections' etymologies: the templates that say where the name came from
    for m in re.finditer(r"\{\{(?:der|bor|inh|lbor|uder|m|l|cog|af|com)\|([^{}]*)\}\}", text):
        parts = [p for p in m.group(1).split("|") if "=" not in p]
        tpl = m.group(0)[2:5]
        code, word = (parts[1], parts[2]) if tpl in ("der", "bor", "inh", "lbo", "ude") and len(parts) > 2 else (parts[0], parts[1]) if len(parts) > 1 else (None, None)
        if code in LANG and word and not LATIN.match(word) and len(word) <= 24 and not re.search(r"[\d*]", word):
            if not any(l == LANG[code] for _, l in out): out.append([word.strip(), LANG[code]])
    return out[:4]

def forms_first(text):
    # the borrowed/derived/inherited forms say what the name is (Muhammad ← مُحَمَّد); mentions ({{m|ar|حَمَّدَ}}) are its root words
    strong = forms(re.sub(r"\{\{(?:m|l|cog|af|com)\|[^{}]*\}\}", "", text))
    return strong or forms(text)

if __name__ == "__main__":
    have = json.load(open(os.path.join(ROOT, "data", "native-forms.json"), encoding="utf-8"))
    todo = [n for n in dict.fromkeys(names()) if not LATIN.match(n) is None]
    todo = list(todo)
    out, cache_f = {}, os.path.join(CACHE, "pages.json.gz")
    cache = json.load(gzip.open(cache_f)) if os.path.exists(cache_f) else {}
    need = [n for n in todo if not cache.get(n)]
    for i in range(0, len(need), 20):
        got = fetch(need[i:i + 20]); cache.update({n: got.get(n, "") for n in need[i:i + 20]}); time.sleep(.5)
    json.dump(cache, gzip.open(cache_f, "wt", encoding="utf-8"))
    origin = {}
    for n in todo:
        t = cache.get(n) or ""
        f = forms_first(t)
        if f: out[fold(n)] = f
        en = t[t.find("==English=="):] if "==English==" in t else ""
        nxt = re.search(r"\n==[^=]", en[12:]); en = en[:12 + nxt.start()] if nxt else en
        m = re.search(r"\{\{(?:bor|der|inh|lbor)\|en\|([a-z-]+)\|", en)
        if m and m.group(1) in LANG: origin[fold(n)] = LANG[m.group(1)]
    json.dump(origin, open(os.path.join(ROOT, "data", "name-origins.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(origin)} origins from etymology")
    json.dump(out, open(os.path.join(ROOT, "data", "native-ety.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"{len(todo)} names checked, {len(out)} with original-script forms")
    for k in ["aisha", "maral", "fatima", "ali", "hana", "elias", "omar", "layla", "zainab"]: print(" ", k, out.get(k))
