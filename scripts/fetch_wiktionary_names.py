# Downloads every given name Wiktionary lists for the languages below (its "<language> male/female/unisex given names"
# categories), with each page's wikitext, into raw/wikt/<language>.json. Wiktionary is CC BY-SA 4.0.
# Polite: one request at a time, 50 pages per request, a contact user agent, maxlag.
#
#   python3 scripts/fetch_wiktionary_names.py            (skips languages already downloaded)
import json, os, sys, time, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(os.path.dirname(HERE), "raw", "wikt")
UA = {"User-Agent": "Lullabyte/1.0 (https://github.com/suhxnitiwari/baby-name-maker; suhxnitiwari@gmail.com)"}
API = "https://en.wiktionary.org/w/api.php?"

# living languages whose names we don't already have a source for (or have only through diaspora records)
LANGUAGES = """Yoruba Igbo Hausa Swahili Zulu Xhosa Sotho Tswana Amharic Tigrinya Somali Oromo Akan Twi Ewe Ga Fon Wolof Shona Chichewa Kinyarwanda Luganda Malagasy Lingala Kikuyu Afrikaans
Tamil Telugu Bengali Hindi Punjabi Urdu Malayalam Kannada Marathi Gujarati Nepali Sinhalese Odia Assamese Sindhi Pashto Dhivehi
Vietnamese Thai Tagalog Cebuano Indonesian Malay Javanese Sundanese Burmese Khmer Lao Hmong Ilocano
Persian Turkish Azerbaijani Northern_Kurdish Central_Kurdish Armenian Georgian Kazakh Uzbek Kyrgyz Turkmen Tajik Mongolian Uyghur Tatar Bashkir Chechen Ossetian Abkhaz
Russian Ukrainian Belarusian Serbo-Croatian Bulgarian Macedonian Albanian Romanian Hungarian Lithuanian Latvian Estonian Czech Slovak Slovene Polish Greek Finnish
Māori Hawaiian Samoan Tongan Fijian Tahitian Chamorro Tibetan Dzongkha Quechua Nahuatl Guarani Aymara Navajo Cherokee Ojibwe Inuktitut Greenlandic
Icelandic Faroese Welsh Irish Scottish_Gaelic Breton Basque Catalan Galician Maltese Yiddish Esperanto""".split()

def api(**q):
    q.update(format="json", maxlag="20")
    for attempt in range(40):
        try:
            # POST, so long lists of titles fit
            d = json.load(urllib.request.urlopen(urllib.request.Request(API, data=urllib.parse.urlencode(q).encode(), headers=UA), timeout=90))
            if d.get("error", {}).get("code") == "maxlag": time.sleep(min(30, 5 + float(d["error"].get("lag", 5)))); continue   # the servers are busy: wait
            return d
        except Exception as e:
            time.sleep(3 * (attempt + 1))
    raise RuntimeError("Wiktionary API kept failing")

def members(cat):
    out, cont = [], {}
    while True:
        d = api(action="query", list="categorymembers", cmtitle="Category:" + cat, cmlimit="500", cmtype="page", **cont)
        out += [m["title"] for m in d.get("query", {}).get("categorymembers", [])]
        if "continue" not in d: return out
        cont = d["continue"]

def pages(titles):
    out = {}
    for i in range(0, len(titles), 50):
        d = api(action="query", prop="revisions", rvprop="content", rvslots="main", titles="|".join(titles[i:i + 50]))
        for p in d.get("query", {}).get("pages", {}).values():
            rev = (p.get("revisions") or [{}])[0]
            out[p["title"]] = rev.get("slots", {}).get("main", {}).get("*", "")
        time.sleep(.2)
    return out

if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    todo = [l for l in LANGUAGES if len(sys.argv) < 2 or l in sys.argv[1:]]
    for lang in todo:
        path = os.path.join(RAW, f"{lang}.json")
        if os.path.exists(path): continue
        name = lang.replace("_", " ")
        sex = {}
        for g, label in (("b", "male"), ("g", "female"), ("e", "unisex")):
            for t in members(f"{name} {label} given names"):
                sex[t] = "e" if t in sex and sex[t] != g else g
        if not sex: print(f"  {name}: none"); json.dump({}, open(path, "w")); continue
        text = pages(sorted(sex))
        json.dump({t: {"g": g, "text": text.get(t, "")} for t, g in sex.items()}, open(path, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"  {name}: {len(sex):,} names", flush=True)
