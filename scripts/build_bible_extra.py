# Builds data/bible-extra.json: biblical people and Christian names that data/scripture-names.json is missing.
#
#  1. Wikipedia's "List of biblical names starting with A" … "Z" (CC BY-SA 4.0). Each entry is checked against
#     STEPBible TIPNR (raw/tipnr.txt, CC BY 4.0) and, for names TIPNR doesn't know, against Wikidata (CC0), so only
#     personal names of people get in: places, peoples, books, titles and words are left out.
#       · a name we already have from the Bible, with no meaning yet → a row that adds Wikipedia's meaning
#       · a name we have only from another tradition (the Hindu epics, the Quran) → a row that adds the Bible
#       · a biblical person we don't have (mostly King James spellings: Abram, Cephas, Dorcas) → a new row
#  2. Christian names that are not names of biblical people, tagged texts "" so the site never calls them biblical:
#       · virtue names (Wikipedia, "Virtue name", CC BY-SA 4.0)
#       · names carried by widely venerated saints, each saint checked on Wikidata (canonization status, CC0)
#     Meanings for these come from the etymology on each name's English Wiktionary page (CC BY-SA 4.0).
#
# Rows: [name, gender g|b|e, culture, language, faiths, meaning, story, texts, kind, also]  (the app merges rows by name)
# Downloads are cached in raw/bible-extra/; delete that folder to fetch everything again.
#
#   python3 scripts/build_bible_extra.py
import collections, difflib, glob, json, os, re, time, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "raw"); CACHE = os.path.join(RAW, "bible-extra")
OUT = os.path.join(ROOT, "data", "bible-extra.json")
UA = {"User-Agent": "Lullabyte-build/1.0 (https://github.com/suhxnitiwari/baby-name-maker)"}
WP = "https://en.wikipedia.org/w/api.php?"; WD = "https://www.wikidata.org/w/api.php?"; WT = "https://en.wiktionary.org/w/api.php?"

def api(base, **q):
    q.update(format="json", formatversion=2, maxlag=10)
    for attempt in range(8):
        try:
            req = urllib.request.Request(base, data=urllib.parse.urlencode(q).encode(), headers=UA)
            d = json.load(urllib.request.urlopen(req, timeout=60))
            if d.get("error", {}).get("code") == "maxlag": time.sleep(5); continue
            return d
        except Exception:
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"{base} kept failing")

def cached(name, fetch):
    path = os.path.join(CACHE, name)
    if os.path.exists(path): return json.load(open(path, encoding="utf-8"))
    data = fetch()
    os.makedirs(CACHE, exist_ok=True)
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    return data

def wikitext(title):
    d = api(WP, action="parse", page=title, prop="wikitext", redirects=1)
    return d.get("parse", {}).get("wikitext", "")

def wikidata_for(titles, site=WP):
    """enwiki titles → {title: {qid, p31, sex, p411, desc}} (follows redirects; anchors are dropped)."""
    out, titles = {}, sorted({t.split("#")[0] for t in titles if t})
    qid = {}
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        q = api(site, action="query", titles="|".join(chunk), prop="pageprops", ppprop="wikibase_item", redirects=1)["query"]
        norm = {x["from"]: x["to"] for x in q.get("normalized", [])}; red = {x["from"]: x["to"] for x in q.get("redirects", [])}
        pp = {p["title"]: p.get("pageprops", {}).get("wikibase_item") for p in q["pages"]}
        for t in chunk:
            a = norm.get(t, t); qid[t] = pp.get(red.get(a, a))
    ids = sorted({v for v in qid.values() if v}); ent = {}
    for i in range(0, len(ids), 50):
        d = api(WD, action="wbgetentities", ids="|".join(ids[i:i + 50]), props="claims|descriptions", languages="en")
        for k, v in d["entities"].items():
            c = v.get("claims", {})
            ids_of = lambda p: [x["mainsnak"].get("datavalue", {}).get("value", {}).get("id") for x in c.get(p, [])]
            ent[k] = {"qid": k, "p31": ids_of("P31"), "sex": ids_of("P21"), "p411": ids_of("P411"),
                      "desc": v.get("descriptions", {}).get("en", {}).get("value", "")}
    for t in titles: out[t] = ent.get(qid.get(t) or "", {})
    return out

# ─────────────────────────────────────────────────────────────
# STEPBible TIPNR: every spelling of every person (KJV, ESV, NIV…), with the books it appears in
# ─────────────────────────────────────────────────────────────
BOOKS = ("Gen Exo Lev Num Deu Jos Jdg Rut 1Sa 2Sa 1Ki 2Ki 1Ch 2Ch Ezr Neh Est Job Psa Pro Ecc Sng Isa Jer Lam Ezk Dan Hos Jol Amo Oba Jon "
         "Mic Nam Hab Zep Hag Zec Mal Mat Mrk Luk Jhn Act Rom 1Co 2Co Gal Eph Php Col 1Th 2Th 1Ti 2Ti Tit Phm Heb Jas 1Pe 2Pe 1Jn 2Jn 3Jn Jud Rev").split()
TORAH, NT = set(BOOKS[:5]), set(BOOKS[BOOKS.index("Mat"):])
BOOK_NAME = dict(zip(BOOKS, ("Genesis,Exodus,Leviticus,Numbers,Deuteronomy,Joshua,Judges,Ruth,1 Samuel,2 Samuel,1 Kings,2 Kings,1 Chronicles,"
    "2 Chronicles,Ezra,Nehemiah,Esther,Job,Psalms,Proverbs,Ecclesiastes,Song of Songs,Isaiah,Jeremiah,Lamentations,Ezekiel,Daniel,Hosea,Joel,"
    "Amos,Obadiah,Jonah,Micah,Nahum,Habakkuk,Zephaniah,Haggai,Zechariah,Malachi,Matthew,Mark,Luke,John,Acts,Romans,1 Corinthians,"
    "2 Corinthians,Galatians,Ephesians,Philippians,Colossians,1 Thessalonians,2 Thessalonians,1 Timothy,2 Timothy,Titus,Philemon,Hebrews,"
    "James,1 Peter,2 Peter,1 John,2 John,3 John,Jude,Revelation").split(",")))
# titles and epithets TIPNR files under a person: not given names
TITLES = {"caesar", "cesar", "christ", "messiah", "boanerges", "edom", "pharaoh", "rabbi", "rabboni", "lord", "tirshatha", "augustus",
          "rabshakeh", "rabsaris", "tartan", "candace", "augustan",
          # peoples, epithets and words that TIPNR or Wikidata attach to a person
          "jew", "hittite", "anamim", "casluhim", "iscariot", "zelotes", "niger", "jeshurun", "hashem", "jasher"}

def tipnr():
    """spelling (lowercase) → {sex: Counter, books: set, script, brief, head, place: bool}"""
    txt = open(os.path.join(RAW, "tipnr.txt"), encoding="utf-8").read()
    idx = collections.defaultdict(lambda: {"sex": collections.Counter(), "books": set(), "script": "", "brief": "", "head": "", "total": -1, "place": False, "spell": "", "tags": set()})
    for b in txt.split("$========== ")[1:]:
        kind = b.split("(")[0].split("\n")[0].strip()
        lines = b.split("\n"); head = lines[1].split("\t")
        if kind == "PLACE":
            for l in lines:
                if l.startswith("– ") and len(l.split("\t")) > 3:
                    for part in l.split("\t")[3].split(";"):
                        idx[part.split("=")[0].strip().lower()]["place"] = True
            idx[head[0].split("@")[0].strip().lower()]["place"] = True
            continue
        if kind != "PERSON" or len(head) < 9 or head[8].strip() not in ("Male", "Female"): continue
        sex, headname = head[8].strip(), head[0].split("@")[0].split("|")[-1].strip()
        brief = (re.search(r"@Brief= (.*)", b) or [None, ""])[1].strip()
        # how often the person is mentioned: every verse reference in the block
        total = sum(len(re.findall(r"\b[123]?[A-Z][a-z]{1,2}\.\d", l.split("\t")[4])) for l in lines
                    if l.startswith("– ") and not l.startswith("– Total") and len(l.split("\t")) > 4)
        for l in lines:
            # Group lines are peoples (Agagite, Christian); "Name combined" are phrases (daughter of Shua)
            if not l.startswith("– ") or l.startswith(("– Total", "– Group", "– Name combined")): continue
            c = l.split("\t")
            if len(c) < 5: continue
            books = {x for x in re.findall(r"\b([123]?[A-Z][a-z]{1,2})\.\d", c[4]) if x in BOOK_NAME}
            script = c[2].split("=")[-1] if "=" in c[2] else ""
            for part in c[3].split(";"):
                s = part.split("=")[0].strip()
                if not re.fullmatch(r"[A-Z][a-z'\-]+", s): continue
                e = idx[s.lower()]
                e["sex"][sex] += 1; e["books"] |= books; e["spell"] = s
                e["tags"] |= set(re.findall(r"\b(KJV|ESV|NIV)\b", part.split("=", 1)[1])) if "=" in part else set()
                if total > e["total"]: e.update(script=script or e["script"], brief=brief, head=headname, total=total)
    return idx

# ─────────────────────────────────────────────────────────────
# WIKIPEDIA: List of biblical names starting with A … Z
# ─────────────────────────────────────────────────────────────
def wiki_entries():
    pages = cached("wiki-letters.json", lambda: {L: wikitext(f"List of biblical names starting with {L}") for L in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"})
    out = []
    for L, text in sorted(pages.items()):
        body = re.split(r"==\s*(References|Inline references|Sources|Bibliography)\s*==", text)[0]
        for line in body.split("\n"):
            if not line.startswith("*"): continue
            s = re.sub(r"<ref[^>]*/>|<ref.*?</ref>", "", line[1:].strip())
            m = re.match(r"\s*\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", s)
            if m: name, target, rest = m.group(2) or m.group(1), m.group(1), s[m.end():]
            else:
                m = re.match(r"\s*\[https?://\S+ ([^\]]+)\]", s) or re.match(r"\s*([^,'\[(]+)", s)
                if not m: continue
                name, target, rest = m.group(1), None, s[m.end():]
            name = re.sub(r"\s*\(.*?\)|,.*| son of .*| of [A-Z].*|\s*[–-]\s*$", "", name).strip(" ,")
            if not re.fullmatch(r"[A-Z][a-z'\-]+", name): continue
            # the meaning: the italic glosses after the name (Lockyer, Smith, Easton, Comay, as cited on the page)
            gl = [re.sub(r"[\"“”]|'''?", "", g).strip(" ,;:.") for g in re.findall(r"''(.+?)''", rest)]
            gl = [g for g in gl if len(g) > 2 and len(g) < 80 and not re.search(r"\b(dictionary|encyclop|bible|press|publishing|vol\.)", g, re.I)]
            meaning = "; ".join(dict.fromkeys(g[:1].lower() + g[1:] for g in gl[:2]))
            out.append({"n": name, "target": target, "m": meaning[:90].rsplit(";", 1)[0] if len(meaning) > 90 else meaning,
                        "script": "".join(re.findall(r"[֐-׿Ͱ-Ͽἀ-῿]+", rest))})
    return out

# Wikidata says "human biblical figure" for these, but they aren't named in the Bible, or aren't a personal name
NOT_BIBLICAL = {"joachim": "traditional father of Mary, named in the Gospel of James, not the Bible", "ruhamah": "a symbolic name in Hosea",
                "queen": "a title"}
# Wikidata's description doesn't say which part of the Bible: set it by hand
WD_OVERRIDE = {
    "abubus": (["Bible"], "Christian", "Governor of Jericho, father-in-law of Simon Thassi, in 1 Maccabees, a book of the Catholic and Orthodox Bibles"),
    "urban": (["Bible", "New Testament"], "Christian", "Urbanus (KJV Urbane), a fellow worker greeted by Paul (Romans 16:9). Named in the Bible"),
}
WD_BIBLE = re.compile(r"bibl|testament|gospel|apostle|disciple|book of|high priest|jericho", re.I)
WD_NT = re.compile(r"new testament|gospel|apostle|disciple|acts|paul|jesus|high priest|seventy|cyprus", re.I)
SEX = {"Q6581097": "b", "Q6581072": "g"}

def biblical(ours, idx):
    ents = wiki_entries()
    unknown = [e["target"] for e in ents if e["target"] and e["n"].lower() not in idx and e["n"].lower() not in ours]
    wd = cached("wikidata-biblical.json", lambda: wikidata_for(unknown))
    # spellings TIPNR lists for well-known people that Wikipedia's list doesn't have (Elisabeth, Rebecca, Marcus)
    listed = {e["n"].lower() for e in ents}
    for k, t in sorted(idx.items()):
        if not (t["sex"]["Male"] or t["sex"]["Female"]) or k in listed or k in TITLES or re.search(r"ites?$|-", k): continue
        if k in ours and "Bible" in ours[k][7] or k.replace("-", "") in ours or t["head"].lower() not in ours or t["total"] < 5: continue
        if difflib.SequenceMatcher(None, k, t["head"].lower()).ratio() < 0.6: continue
        ents.append({"n": t["spell"], "target": None, "m": "", "script": "", "variant": True})
    rows, stats, seen = [], collections.Counter(), set()
    for e in ents:
        n, k = e["n"], e["n"].lower()
        if k in seen: continue
        cur, t = ours.get(k), idx.get(k)
        if cur and "Bible" in cur[7]:
            # already ours: only add what's missing, a meaning
            if not cur[5] and e["m"]:
                seen.add(k); stats["meaning"] += 1
                rows.append([cur[0], cur[1], cur[2], cur[3], cur[4], e["m"], "Meaning from Wikipedia's List of biblical names.", cur[7], "real", []])
            continue
        if k in TITLES or k in NOT_BIBLICAL: continue
        if t and (t["sex"]["Male"] or t["sex"]["Female"]):
            g = "e" if t["sex"]["Male"] and t["sex"]["Female"] else "b" if t["sex"]["Male"] else "g"
            books = t["books"]
            greek = bool(re.search(r"[Ͱ-Ͽἀ-῿]", t["script"]))
            texts = ["Bible"] + (["Torah"] if books & TORAH else []) + (["Hebrew Bible"] if books - NT else []) + (["New Testament"] if books & NT else [])
            faiths = "Christian,Jewish" if books - NT else "Christian"
            first = min(books, key=BOOKS.index) if books else ""
            same = t["head"] and t["head"].lower() != k
            spelling = same and difflib.SequenceMatcher(None, k, t["head"].lower()).ratio() >= 0.6     # Imla ~ Imlah, not Abednego ~ Azariah
            tags = "/".join(x for x in ("KJV", "ESV", "NIV") if x in t["tags"])
            how = ("The earlier name of" if k in ("abram", "sarai", "oshea") else f"The {tags} spelling of" if spelling and tags
                   else "Another spelling of" if spelling else "Another name for")
            who = f"{how} {t['head']}: {t['brief'].rstrip('.')}" if same and t["brief"] else (t["brief"].rstrip(".") or f"Named in {BOOK_NAME.get(first, 'the Bible')}")
            form = f"{'Greek' if greek else 'Hebrew'} {t['script']}; " if t["script"] else ""
            story = f"{who}" + (f" ({BOOK_NAME[first]})" if first and not same else "") + f". Named in the Bible ({form}" + ("" if e.get("variant") else "Wikipedia, List of biblical names; ") + "STEPBible)."
            if spelling and not e["m"] and t["head"].lower() in ours and not ours[t["head"].lower()][5].startswith("same as"):
                # a spelling shares its meaning (minus Hitchcock's cross-references: "or Achar, he that troubleth")
                e["m"] = re.sub(r"^(or )?[A-Z][a-z\-]+(, or [A-Z][a-z\-]+)?,\s*", "", ours[t["head"].lower()][5])
            src = "variant" if e.get("variant") else "tipnr"
        else:
            w = wd.get((e["target"] or "").split("#")[0], {})
            if not w or k in NOT_BIBLICAL: continue
            human_biblical = "Q20643955" in w["p31"] or ("Q5" in w["p31"] and WD_BIBLE.search(w["desc"]))
            g = next((SEX[s] for s in w["sex"] if s in SEX), None)
            if not human_biblical or not g: continue          # a place, a people, a word, or a person of unknown sex: leave out
            nt = bool(WD_NT.search(w["desc"]))
            texts = ["Bible"] + (["New Testament"] if nt else ["Hebrew Bible"])
            faiths = "Christian" if nt else "Christian,Jewish"; greek = nt
            desc = w["desc"][:1].upper() + w["desc"][1:]
            desc = desc if len(desc) <= 110 else desc[:107].rsplit(" ", 1)[0] + "…"
            main = re.sub(r"\s*\(.*?\)|#.*", "", e["target"])     # the article it links to: Joab for Yoab
            if main.lower() != k and main.lower() not in ("ishbosheth",) and " " not in main: desc = f"A form of {main}. {desc}"
            story = f"{desc}. Named in the Bible (Wikipedia, List of biblical names; Wikidata)."
            if k in WD_OVERRIDE: texts, faiths, story = WD_OVERRIDE[k][0], WD_OVERRIDE[k][1], WD_OVERRIDE[k][2] + " (Wikipedia, List of biblical names; Wikidata)."
            src = "wikidata"
        seen.add(k)
        if cur:   # we have it from another tradition (Hindu, Quran): add the Bible to it
            stats["text"] += 1
            rows.append([cur[0], cur[1], cur[2], cur[3], cur[4], e["m"] if not cur[5] else "", story, ",".join(texts), "real", ["Greek" if greek else "Hebrew"]])
        else:
            stats["new_" + src] += 1
            rows.append([n, g, "Greek" if greek else "Hebrew", "Greek" if greek else "Hebrew", faiths, e["m"], story, ",".join(texts), "real", []])
    for r in rows:                     # "Hodijah, same as Hodaiah" is a cross-reference, not a meaning
        if "same as" in r[5]: r[5] = ""
    dropped = [r for r in rows if r[6].startswith("Meaning from") and not r[5]]
    stats["meaning"] -= len(dropped)
    return [r for r in rows if r not in dropped], stats

# ─────────────────────────────────────────────────────────────
# CHRISTIAN, NOT BIBLICAL: virtue names and saints' names
# ─────────────────────────────────────────────────────────────
# from Wikipedia's "Virtue name" (its examples and its category), keeping the ones with a Christian sense
VIRTUES = {
    "Grace": "g", "Faith": "g", "Hope": "g", "Charity": "g", "Chastity": "g", "Constance": "g", "Felicity": "g", "Honor": "e", "Mercy": "g",
    "Patience": "g", "Prudence": "g", "Temperance": "g", "Verity": "g", "Joy": "g", "Humility": "g", "Glory": "g", "Gloria": "g",
    "Fidelia": "g", "Comfort": "g", "Silence": "g", "Increase": "b", "Preserved": "b", "Trinity": "g", "Blessing": "g", "Charis": "g",
    "Clemency": "g", "Modesty": "g", "Amity": "g", "Diligence": "g", "Innocent": "b", "Pleasance": "g", "Alethea": "g",
}
VIRTUE_LATIN = {"Gloria": "Latin gloria", "Fidelia": "Latin fidelis", "Charis": "Greek charis", "Alethea": "Greek alētheia", "Innocent": "Latin innocens"}
# widely venerated saints: name → (gender, English Wikipedia article on the saint)
SAINTS = {
    "Agatha": ("g", "Agatha of Sicily"), "Agnes": ("g", "Agnes of Rome"), "Anastasia": ("g", "Anastasia of Sirmium"), "Angela": ("g", "Angela Merici"),
    "Anne": ("g", "Saint Anne"), "Apollonia": ("g", "Saint Apollonia"), "Barbara": ("g", "Saint Barbara"), "Beatrice": ("g", "Beatrice of Silva"),
    "Bernadette": ("g", "Bernadette Soubirous"), "Bridget": ("g", "Brigid of Kildare"), "Brigid": ("g", "Brigid of Kildare"),
    "Catherine": ("g", "Catherine of Siena"), "Cecilia": ("g", "Saint Cecilia"), "Christina": ("g", "Christina of Bolsena"), "Clare": ("g", "Clare of Assisi"),
    "Clara": ("g", "Clare of Assisi"), "Dorothy": ("g", "Dorothea of Caesarea"), "Edith": ("g", "Edith Stein"), "Eulalia": ("g", "Eulalia of Mérida"),
    "Faustina": ("g", "Faustina Kowalska"), "Frances": ("g", "Frances of Rome"), "Gemma": ("g", "Gemma Galgani"), "Genevieve": ("g", "Genevieve"),
    "Gertrude": ("g", "Gertrude the Great"), "Gianna": ("g", "Gianna Beretta Molla"), "Helena": ("g", "Helena, mother of Constantine I"),
    "Hedwig": ("g", "Hedwig of Silesia"), "Hilda": ("g", "Hilda of Whitby"), "Hildegard": ("g", "Hildegard of Bingen"), "Irene": ("g", "Irene of Tomar"),
    "Joan": ("g", "Joan of Arc"), "Josephine": ("g", "Josephine Bakhita"), "Juliana": ("g", "Juliana of Nicomedia"), "Justina": ("g", "Justina of Padua"),
    "Kateri": ("g", "Kateri Tekakwitha"), "Louise": ("g", "Louise de Marillac"), "Lucy": ("g", "Saint Lucy"), "Lucia": ("g", "Saint Lucy"),
    "Ludmila": ("g", "Ludmila of Bohemia"), "Margaret": ("g", "Margaret the Virgin"), "Marina": ("g", "Marina the Monk"), "Monica": ("g", "Monica of Hippo"),
    "Natalia": ("g", "Adrian and Natalia of Nicomedia"), "Olga": ("g", "Olga of Kiev"), "Paula": ("g", "Paula of Rome"), "Perpetua": ("g", "Perpetua and Felicity"),
    "Philomena": ("g", "Philomena"), "Regina": ("g", "Regina (saint)"), "Rita": ("g", "Rita of Cascia"), "Rosalia": ("g", "Saint Rosalia"), "Rose": ("g", "Rose of Lima"),
    "Scholastica": ("g", "Scholastica"), "Sophia": ("g", "Sophia of Rome"), "Teresa": ("g", "Teresa of Ávila"), "Theresa": ("g", "Thérèse of Lisieux"),
    "Thecla": ("g", "Thecla"), "Ursula": ("g", "Saint Ursula"), "Veronica": ("g", "Saint Veronica"), "Winifred": ("g", "Saint Winifred"), "Zita": ("g", "Zita"),
    "Aidan": ("b", "Aidan of Lindisfarne"), "Alban": ("b", "Saint Alban"), "Albert": ("b", "Albertus Magnus"), "Aloysius": ("b", "Aloysius Gonzaga"),
    "Ambrose": ("b", "Ambrose"), "Anselm": ("b", "Anselm of Canterbury"), "Anthony": ("b", "Anthony the Great"), "Augustine": ("b", "Augustine of Hippo"),
    "Basil": ("b", "Basil of Caesarea"), "Bede": ("b", "Bede"), "Benedict": ("b", "Benedict of Nursia"), "Bernard": ("b", "Bernard of Clairvaux"),
    "Blaise": ("b", "Saint Blaise"), "Bonaventure": ("b", "Bonaventure"), "Boniface": ("b", "Saint Boniface"), "Brendan": ("b", "Brendan the Navigator"),
    "Bruno": ("b", "Bruno of Cologne"), "Casimir": ("b", "Saint Casimir"), "Christopher": ("b", "Saint Christopher"), "Columba": ("b", "Columba"),
    "Cosmas": ("b", "Saints Cosmas and Damian"), "Crispin": ("b", "Saints Crispin and Crispinian"), "Cuthbert": ("b", "Cuthbert"),
    "Cyril": ("b", "Cyril of Alexandria"), "Damian": ("b", "Saints Cosmas and Damian"), "Declan": ("b", "Declan of Ardmore"), "Denis": ("b", "Denis of Paris"),
    "Dominic": ("b", "Saint Dominic"), "Dunstan": ("b", "Dunstan"), "Edmund": ("b", "Edmund the Martyr"), "Edward": ("b", "Edward the Confessor"),
    "Florian": ("b", "Saint Florian"), "Francis": ("b", "Francis of Assisi"), "George": ("b", "Saint George"), "Gerard": ("b", "Gerard Majella"),
    "Giles": ("b", "Saint Giles"), "Gregory": ("b", "Pope Gregory I"), "Hilary": ("e", "Hilary of Poitiers"), "Hubert": ("b", "Hubertus"),
    "Hugh": ("b", "Hugh of Lincoln"), "Ignatius": ("b", "Ignatius of Loyola"), "Isidore": ("b", "Isidore of Seville"), "Ivo": ("b", "Ivo of Kermartin"),
    "Jerome": ("b", "Jerome"), "Kevin": ("b", "Kevin of Glendalough"), "Kilian": ("b", "Saint Kilian"), "Lawrence": ("b", "Saint Lawrence"),
    "Leo": ("b", "Pope Leo I"), "Leonard": ("b", "Leonard of Noblac"), "Louis": ("b", "Louis IX of France"), "Martin": ("b", "Martin of Tours"),
    "Maximilian": ("b", "Maximilian Kolbe"), "Nicholas": ("b", "Saint Nicholas"), "Oswald": ("b", "Oswald of Northumbria"), "Patrick": ("b", "Saint Patrick"),
    "Pio": ("b", "Padre Pio"), "Quentin": ("b", "Saint Quentin"), "Roch": ("b", "Saint Roch"), "Sebastian": ("b", "Saint Sebastian"),
    "Seraphim": ("b", "Seraphim of Sarov"), "Valentine": ("b", "Saint Valentine"), "Vincent": ("b", "Vincent de Paul"), "Vladimir": ("b", "Vladimir the Great"),
    "Wenceslaus": ("b", "Wenceslaus I, Duke of Bohemia"), "Xavier": ("b", "Francis Xavier"), "Joachim": ("b", "Joachim"), "Dismas": ("b", "Penitent thief"),
    "Kieran": ("b", "Ciarán of Saighir"), "Raphael": ("b", "Raphael (archangel)"),
}
# names of Mary: the Virgin Mary's titles, each with its English Wikipedia article
MARIAN = {"Stella": ("Our Lady, Star of the Sea", "Stella Maris (star of the sea), a title of the Virgin Mary"),
          "Dolores": ("Our Lady of Sorrows", "Our Lady of Sorrows (Spanish Dolores), a title of the Virgin Mary"),
          "Mercedes": ("Our Lady of Mercy", "Our Lady of Mercy (Spanish Mercedes), a title of the Virgin Mary"),
          "Carmen": ("Our Lady of Mount Carmel", "Our Lady of Mount Carmel (Spanish Carmen), a title of the Virgin Mary"),
          "Lourdes": ("Our Lady of Lourdes", "Our Lady of Lourdes, the Virgin Mary as seen by Saint Bernadette at Lourdes"),
          "Pilar": ("Our Lady of the Pillar", "Our Lady of the Pillar (Spanish Pilar), a title of the Virgin Mary"),
          "Rosario": ("Our Lady of the Rosary", "Our Lady of the Rosary (Spanish Rosario), a title of the Virgin Mary"),
          "Madonna": ("Madonna (art)", "Madonna, Italian 'my lady', the Virgin Mary"),
          "Christian": (None, "The word Christian, 'follower of Christ' (Latin christianus); the word is in the Bible (Acts 11:26), but no one there bears it as a name")}

# virtue names the Puritans used (Wikipedia, Virtue name; Bardsley, Curiosities of Puritan Nomenclature)
PURITAN = set("Grace Faith Hope Charity Felicity Patience Prudence Mercy Temperance Constance Honor Verity Joy Humility Comfort Silence Increase "
              "Preserved Chastity Modesty Diligence Clemency Pleasance".split())
VIRTUE_WORD = {"Constance": "constancy", "Pleasance": "pleasure", "Gloria": "glory", "Fidelia": "faithful", "Charis": "grace",
               "Alethea": "truth", "Innocent": "innocent"}
# who the name is for, when the article title doesn't read as a name
WHO = {"Dismas": "the Penitent Thief, Saint Dismas", "Raphael": "the Archangel Raphael", "Regina": "Saint Regina", "Natalia": "Saint Natalia of Nicomedia",
       "Perpetua": "Saint Perpetua", "Helena": "Saint Helena, mother of Constantine", "Louis": "Saint Louis (Louis IX of France)",
       "Wenceslaus": "Saint Wenceslaus, Duke of Bohemia", "Cosmas": "Saint Cosmas", "Damian": "Saint Damian", "Crispin": "Saint Crispin",
       "Lucia": "Saint Lucy (Lucia)", "Clara": "Saint Clare of Assisi (Clara)", "Bridget": "Saint Brigid of Kildare (Bridget)",
       "Theresa": "Saint Thérèse of Lisieux", "Kieran": "Saint Ciarán of Saighir (Kieran)", "Xavier": "Saint Francis Xavier", "Gregory": "Saint Gregory the Great",
       "Leo": "Saint Leo the Great", "Pio": "Saint Pio of Pietrelcina (Padre Pio)"}
NO_DESC = {"Natalia", "Raphael", "Dismas", "Helena"}
NOTE = {"Raphael": "Raphael is named in the Book of Tobit, which is in Catholic and Orthodox Bibles but not in the Protestant or Hebrew Bible.",
        "Dismas": "The thief is in Luke's Gospel (23:39-43), but the name Dismas comes from later tradition, not the Bible.",
        "Anne": "Mary's parents are not named in the Bible; their names come from the 2nd-century Gospel of James.",
        "Joachim": "Mary's parents are not named in the Bible; their names come from the 2nd-century Gospel of James."}
# Wiktionary's first gloss is partial or off for these (or missing): the usual etymology instead
MEANING_FIX = {"Clare": "bright, clear", "Anne": "grace, favor (from Hebrew Hannah)", "Christina": "follower of Christ", "Christian": "follower of Christ",
               "Anselm": "god + helmet", "Rose": "rose", "Paula": "small, humble", "Madonna": "my lady", "Martin": "of Mars", "Dominic": "of the Lord",
               "Thecla": "glory of God", "Oswald": "god + power", "Hubert": "bright mind", "Gertrude": "spear + strength", "Bede": "prayer",
               "Catherine": "pure (by long association with Greek katharos)", "Edward": "rich guardian", "Edmund": "rich protector", "Roch": "",
               "Vladimir": "rule + peace, world", "Nicholas": "victory of the people", "Leonard": "lion + brave", "Alban": "from Alba",
               "Genevieve": "kin + woman", "Wenceslaus": "more glory", "Dunstan": "dark stone", "Stella": "star", "Dolores": "sorrows",
               "Mercedes": "mercies", "Carmen": "from Mount Carmel (Hebrew karmel, garden)", "Pilar": "pillar", "Rosario": "rosary", "Lourdes": "",
               "Gloria": "glory", "Alethea": "truth", "Charis": "grace", "Fidelia": "faithful", "Constance": "constancy", "Pleasance": "pleasure"}

def tmpl_gloss(t):
    """the first gloss in a Wiktionary etymology: {{m|la|clārus|t=bright}}, {{der|en|la|stēlla||star}}, {{af|..|t1=spear|t2=brave}}"""
    for m in re.finditer(r"\{\{([^{}]+)\}\}", t):
        parts = m.group(1).split("|"); name = parts[0].strip()
        named = dict(p.split("=", 1) for p in parts[1:] if "=" in p); pos = [p for p in parts[1:] if "=" not in p]
        gl = [named[k] for k in ("t", "gloss") if named.get(k)] or [named[k] for k in sorted(named) if re.fullmatch(r"t\d|gloss\d", k) and named[k]]
        if not gl:
            if name in ("m", "l", "m+", "mention") and len(pos) >= 4: gl = [pos[3]]
            elif name in ("der", "bor", "inh", "lbor", "uder", "lbor+", "der+", "inh+", "bor+", "cal", "slbor", "learned borrowing") and len(pos) >= 5: gl = [pos[4]]
        gl = [re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", g).strip() for g in gl if g.strip()]
        if gl: return "; ".join(gl)
    return ""

def wiktionary(names):
    def fetch():
        out = {}
        for i in range(0, len(names), 50):
            d = api(WT, action="query", prop="revisions", rvprop="content", rvslots="main", titles="|".join(names[i:i + 50]))
            for p in d["query"]["pages"]:
                if "revisions" in p: out[p["title"]] = p["revisions"][0]["slots"]["main"]["content"]
        return out
    pages = cached("wiktionary.json", fetch)
    meaning, lang = {}, {}
    LANGS = {"Germanic languages": "Germanic", "Ancient Greek": "Greek", "Old English": "Old English", "Irish": "Irish", "Latin": "Latin",
             "Hebrew": "Hebrew", "Slavic languages": "Slavic", "Spanish": "Spanish", "Italian": "Italian", "French": "French", "Greek": "Greek"}
    for n, t in pages.items():
        en = t.split("==English==")[1].split("\n----")[0] if "==English==" in t else ""
        ety = re.search(r"===Etymology[^=]*===\n(.*?)(?=\n===)", en, re.S)
        meaning[n] = tmpl_gloss(ety.group(1)) if ety else ""
        frm = re.search(r"\{\{given name\|en\|[^}]*?from=([^|}]+)", en)
        lang[n] = LANGS.get(frm.group(1).strip(), "") if frm else ""
    return meaning, lang

def christian(ours_bible, new_bible):
    is_bible = lambda n: n.lower() in ours_bible or n.lower() in new_bible
    saints = cached("wikidata-saints.json", lambda: wikidata_for([v[1] for v in SAINTS.values()] + [v[0] for v in MARIAN.values() if v[0]]))
    names = sorted(set(VIRTUES) | set(SAINTS) | set(MARIAN))
    mean, lang = wiktionary(names)
    rows, skipped = [], {}
    for n in names:
        if is_bible(n): skipped[n] = "a biblical person"; continue
        m = MEANING_FIX.get(n, mean.get(n, ""))
        if n in VIRTUES:
            word = VIRTUE_WORD.get(n, n.lower())
            src = VIRTUE_LATIN.get(n)
            puritan = n in PURITAN
            story = (f"A virtue name, from {src or 'the English word'} '{word}'" + ("; virtue names like this were taken up by English Puritans from the 16th century" if puritan else "")
                     + ". Christian, but not a name from the Bible (Wikipedia, Virtue name).")
            if n == "Trinity": story = "Named for the Holy Trinity, the Christian Father, Son and Holy Spirit. Christian, but not a name from the Bible (Wikipedia, Virtue name)."
            rows.append([n, VIRTUES[n], "English", (src or "English").split()[0], "Christian", m or word, story, "", "real", []])
        elif n in SAINTS:
            g, title = SAINTS[n]; w = saints.get(title, {})
            if not (w.get("p411") or re.search(r"\b(saint|martyr|archangel)", w.get("desc", ""), re.I)): skipped[n] = f"Wikidata has no canonization status for {title}"; continue
            desc = "" if n in NO_DESC else re.sub(r"\s*\([^)]*\d[^)]*\)", "", w["desc"]).strip(" .")
            who = WHO.get(n) or (title if re.match(r"(Saint|Pope|Saints|Padre) ", title) else f"Saint {title}")
            extra = NOTE.get(n, "Not a name from the Bible.")
            story = f"Named for {who}" + (f" ({desc[:1].upper() + desc[1:]})" if desc else "") + f". {extra} (Wikidata)"
            rows.append([n, g, "", lang.get(n, ""), "Christian", m, story, "", "real", []])
        else:
            title, what = MARIAN[n]
            story = f"A Christian name: {what}." if n == "Christian" else f"A Christian name: {what}. Not a name of anyone in the Bible (Wikipedia, {title})."
            rows.append([n, "e" if n == "Rosario" else "b" if n == "Christian" else "g", "", lang.get(n, ""), "Christian", m, story, "", "real", []])
    return rows, skipped

if __name__ == "__main__":
    scripture = json.load(open(os.path.join(ROOT, "data", "scripture-names.json"), encoding="utf-8"))
    ours = {r[0].lower(): r for r in scripture}
    idx = tipnr()
    brows, stats = biblical(ours, idx)
    ours_bible = {k for k, r in ours.items() if "Bible" in r[7]}
    new_bible = {r[0].lower() for r in brows if "Bible" in r[7]}
    crows, skipped = christian(ours_bible, new_bible)
    rows = sorted(brows, key=lambda r: r[0]) + sorted(crows, key=lambda r: r[0])
    json.dump(rows, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"Biblical people new: {stats['new_tipnr'] + stats['new_wikidata'] + stats['new_variant']} ({stats['new_tipnr']} from Wikipedia's list via TIPNR, "
          f"{stats['new_wikidata']} via Wikidata, {stats['new_variant']} TIPNR spellings of well-known people) · "
          f"Bible added to a name we had from another tradition: {stats['text']} · meanings added: {stats['meaning']} · Christian, not biblical: {len(crows)}")
    for n, why in sorted(skipped.items()): print(f"  skipped {n}: {why}")
    print(f"{len(rows):,} rows → {OUT} ({os.path.getsize(OUT) // 1024} KB)")
