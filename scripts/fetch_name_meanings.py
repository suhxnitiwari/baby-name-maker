# For culture names that have no meaning yet, look on Wiktionary (CC BY-SA 4.0) for one:
#   1. the name's own page, English section: "From Igbo …, literally “God leads”"
#   2. the lowercase word in the name's own language: Swahili "baraka" → "blessing"
# Writes raw/wikt-meanings.json {name: meaning}. Polite: 50 titles a request, a contact user agent, maxlag.
#
#   python3 scripts/build_cultures.py && python3 scripts/fetch_name_meanings.py && python3 scripts/build_cultures.py
import json, os, re, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from fetch_wiktionary_names import api
from build_cultures import clean, section

OUT = os.path.join(ROOT, "raw", "wikt-meanings.json")
QUOTE = re.compile(r"(?:meaning|literally|lit\.|means)[^“\"‘]{0,20}[“\"‘]([^”\"’]{3,60})[”\"’]", re.I)

def english_meaning(sec):
    e = clean(sec)
    m = QUOTE.search(e) or re.search(r"\|lit=([^|}]+)", sec) or re.search(r"\|t=([^|}]+)", sec[:600])
    return clean(m.group(1)) if m else ""

def word_meaning(sec):
    m = re.search(r"(?ms)^===+\s*(Noun|Adjective|Verb)\s*===+\s*$.*?^#\s*([^:*\n][^\n]*)", sec)
    if not m: return ""
    g = clean(m.group(2))
    return g if 2 < len(g) < 50 and not re.search(r"given name|surname|placename|city|village|river|plural of|form of", g, re.I) else ""

if __name__ == "__main__":
    rows = json.load(open(os.path.join(ROOT, "data", "culture-names.json"), encoding="utf-8"))
    done = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    want = [(r[0], r[3]) for r in rows if not r[5] and r[0] not in done]
    print(len(want), "names to look up", flush=True)
    for i in range(0, len(want), 25):
        chunk = want[i:i + 25]
        titles = [n for n, _ in chunk] + [n.lower() for n, _ in chunk]
        d = api(action="query", prop="revisions", rvprop="content", rvslots="main", titles="|".join(titles))
        text = {p["title"]: (p.get("revisions") or [{}])[0].get("slots", {}).get("main", {}).get("*", "") for p in d.get("query", {}).get("pages", {}).values()}
        for n, lang in chunk:
            m = ""
            if text.get(n): m = english_meaning(section(text[n], "English"))
            if not m and text.get(n.lower()):
                for l in (lang, lang.split()[0]):
                    sec = section(text[n.lower()], l)
                    if sec: m = word_meaning(sec); break
            done[n] = m
        if i % 1000 == 0:
            json.dump(done, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
            print(f"  {i:,} looked up · {sum(1 for v in done.values() if v):,} meanings", flush=True)
        time.sleep(.15)
    json.dump(done, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"done · {sum(1 for v in done.values() if v):,} meanings found")
