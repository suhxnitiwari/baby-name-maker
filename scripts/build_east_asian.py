# Japanese, Korean and Chinese names with their characters and meanings → data/east-asian-names.json
#
#   Japanese: real given names from JMnedict (EDRDG, CC BY-SA 4.0): every given name, its gender, every way it is
#             written; the most common spelling's meaning from KANJIDIC2 (EDRDG, CC BY-SA 4.0).
#   Korean:   built the way Korean names are made, from two name syllables, each with its usual hanja (checked against
#             KANJIDIC2's Korean readings) and meaning, in the official Revised Romanization.
#   Chinese:  built from common given-name characters, pinyin and meanings from CC-CEDICT (MDBG, CC BY-SA 4.0).
#   Built names that are also registered somewhere (data/names-db.tsv) are marked as real names.
#
#   python3 scripts/build_east_asian.py
import collections, gzip, json, os, re, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); RAW = os.path.join(ROOT, "raw")
OUT = os.path.join(ROOT, "data", "east-asian-names.json")

# ── KANJIDIC2: meanings, readings, how common, and whether it's a name kanji ──
def kanjidic():
    k = gzip.open(os.path.join(RAW, "kanjidic2.xml.gz"), "rt", encoding="utf-8").read()
    out = {}
    for c in re.findall(r"<character>(.*?)</character>", k, re.S):
        lit = re.search(r"<literal>(.*?)</literal>", c).group(1)
        grade = re.search(r"<grade>(\d+)</grade>", c)
        freq = re.search(r"<freq>(\d+)</freq>", c)
        out[lit] = {
            "m": [m for m in re.findall(r"<meaning>([^<]+)</meaning>", c)],
            "ko": re.findall(r'<reading r_type="korean_h">([^<]+)</reading>', c),
            "py": re.findall(r'<reading r_type="pinyin">([^<]+)</reading>', c),
            "grade": int(grade.group(1)) if grade else 99, "freq": int(freq.group(1)) if freq else 9999,
        }
    return out

# what common name kanji mean in a name (the dictionary's first sense is sometimes a title or a place, like 博 "Dr." or 奈 "Nara")
NAME_SENSE = dict(x.replace("_", " ").split(":") for x in """博:learned 空:sky 奈:na_(for_its_sound) 菜:greens 亜:a_(for_its_sound) 由:reason 衣:robe 久:lasting
創:create 音:sound 妃:princess 璃:lapis_lazuli 優:gentle 志:will 羅:gauze 愛:love 結:bind 唯:only 莉:jasmine 咲:blossom 陽:sun 翔:soar
斗:dipper 太:great 大:great 郎:son 子:child 美:beauty 花:flower 華:splendor 香:fragrance 葵:hollyhock 凛:dignified 蓮:lotus 樹:tree
悠:serene 颯:sweep_of_wind 湊:harbor 蒼:blue 碧:blue-green 海:sea 空:sky 智:wisdom 明:bright 真:true 心:heart 和:harmony 輝:radiance
彩:color 紗:silk 千:thousand 乃:no_(for_its_sound) 那:na_(for_its_sound) 佳:fine 恵:blessing 理:reason 里:village 希:hope 芽:bud
良:good 菜:greens 桜:cherry_blossom 雪:snow 月:moon 星:star 光:light 春:spring 夏:summer 秋:autumn 冬:winter 健:healthy 二:second_son""".split())

def short(meanings, n=2):
    ms = [re.sub(r"\s*\(.*?\)", "", m).strip() for m in meanings if not re.search(r"radical|counter|kokuji|\(no\.", m)]
    return ", ".join(dict.fromkeys(m for m in ms if m)[:n] if False else list(dict.fromkeys(m for m in ms if m))[:n])

def db_names():
    out = {}
    for line in open(os.path.join(ROOT, "data", "names-db.tsv"), encoding="utf-8"):
        n, g, cc, c = line.rstrip("\n").split("\t")
        out[n.lower()] = (cc, int(c), g)
    return out

CC = {"us": "US", "ca": "Canada", "qc": "Québec", "au": "Australia", "uk": "England & Wales", "nir": "N. Ireland", "ie": "Ireland", "fr": "France",
      "es": "Spain", "ch": "Switzerland", "ar": "Argentina", "br": "Brazil", "cl": "Chile", "pl": "Poland", "de": "Germany", "at": "Austria",
      "no": "Norway", "lu": "Luxembourg", "pt": "Portugal", "il": "Israel"}
def also_registered(name, db):
    hit = db.get(name.lower())
    if not hit: return ""
    where = [CC.get(c, c) for c in hit[0].split(",")][:3]
    return f" Also registered for {hit[1]:,} people ({', '.join(where)})."

# ─────────────────────────────────────────────────────────────
# JAPANESE: JMnedict given names
# ─────────────────────────────────────────────────────────────
def passport(r):
    # Hepburn as on Japanese passports: no long-vowel marks (Yūki → Yuki, Kōji → Koji), no apostrophes
    r = unicodedata.normalize("NFD", r)
    r = "".join(ch for ch in r if unicodedata.category(ch) != "Mn")
    return r.replace("'", "").replace("’", "")

def japanese(kd, db):
    x = gzip.open(os.path.join(RAW, "JMnedict.xml.gz"), "rt", encoding="utf-8").read()
    names = collections.defaultdict(lambda: {"f": 0, "m": 0, "e": 0, "kanji": collections.Counter(), "kana": collections.Counter()})
    for e in re.findall(r"<entry>(.*?)</entry>", x, re.S):
        ts = re.findall(r"<name_type>&([a-z]+);</name_type>", e)
        if not any(t in ("given", "masc", "fem") for t in ts): continue
        for t in re.findall(r"<trans_det>(.*?)</trans_det>", e):
            if not re.fullmatch(r"[A-Za-zāīūēōĀĪŪĒŌ'’]+", t): continue        # skip stage names, full names, notes
            n = passport(t)
            n = n[:1].upper() + n[1:].lower()
            if len(n) < 2: continue
            d = names[n]
            d["f" if "fem" in ts else "m" if "masc" in ts else "e"] += 1
            for kb in re.findall(r"<keb>(.*?)</keb>", e): d["kanji"][kb] += 1
            for rb in re.findall(r"<reb>(.*?)</reb>", e): d["kana"][rb] += 1
    out = []
    for n, d in names.items():
        f, m = d["f"], d["m"]
        g = "e" if f + m == 0 else "g" if f >= 3 * m else "b" if m >= 3 * f else "e"
        reg = db.get(n.lower())
        if reg and reg[2] in ("f", "m") and reg[1] >= 50: g = "g" if reg[2] == "f" else "b"        # official records know best (Haruto, Riku: boys)
        elif g == "e" and reg and reg[2] in ("f", "m") and reg[1] >= 20: g = "g" if reg[2] == "f" else "b"
        # the spelling to show: name kanji only, made of the characters most often used for this name (陽翔 for Haruto)
        ok = [k for k in d["kanji"] if all(ch in kd and kd[ch]["grade"] <= 10 for ch in k)]
        use = collections.Counter(ch for k in ok for ch in set(k))
        usual = collections.Counter(len(k) for k in ok).most_common(1)[0][0] if ok else 0   # the usual number of characters for this name
        best = max((k for k in ok if len(k) == usual), key=lambda k: (sum(use[ch] for ch in k) / len(k), -sum(kd[ch]["freq"] for ch in k))) if ok else ""
        kana = d["kana"].most_common(1)[0][0] if d["kana"] else ""
        meaning = " + ".join(NAME_SENSE.get(ch) or short(kd[ch]["m"], 1) for ch in best) if best else ""
        out.append([n, g, best, kana, len(d["kanji"]), meaning])
    return out

# ─────────────────────────────────────────────────────────────
# KOREAN: two name syllables, each with its usual hanja
# ─────────────────────────────────────────────────────────────
# syllable: (hanja, leaning) — f girls, m boys, e either. Hanja are the ones most used in names for that sound.
KO = {}
for _x in """민=敏e 준=俊m 서=瑞e 연=妍f 지=智e 우=佑m 하=夏e 윤=潤e 은=恩f 현=賢e 호=浩m 진=珍e 수=秀e 아=雅f 예=藝f
채=彩f 희=熙f 영=英e 재=在m 승=承m 태=泰m 도=道m 시=是e 유=裕e 성=成m 혜=慧f 정=貞e 미=美f 나=娜f 린=璘f 소=昭f 다=多f 율=律e 건=健m
규=奎m 원=元m 혁=赫m 훈=勳m 석=碩m 동=東m 범=範m 찬=燦m 빈=彬e 한=翰m 주=珠e 기=基m 경=慶e 상=祥m 용=勇m 환=煥m 형=亨m 인=仁e 선=善f
화=華f 향=香f 란=蘭f 효=孝e 담=潭e 온=溫e 슬=瑟f 결=潔e 은=恩f 혜=惠f 률=律e 람=嵐e 해=海e 솔=率e 별=星f 빛=光e 이=怡f 가=佳f 혁=赫m
철=哲m 웅=雄m 종=鍾m 석=錫m 국=國m 병=炳m 일=日m 창=昌m 근=根m 만=萬m 우=宇m 현=炫e 준=峻m 민=珉e 서=書e 지=知e 하=河e 윤=允e 은=銀f
연=然e 수=洙m 진=眞e""".split(): KO.setdefault(*_x.split("="))
CHO = "g kk n d tt r m b pp s ss  j jj ch k t p h".split(" ")
JUNG = "a ae ya yae eo e yeo ye o wa wae oe yo u wo we wi yu eu ui i".split(" ")
JONG = ["", "k", "k", "k", "n", "n", "n", "t", "l", "k", "m", "l", "l", "l", "p", "l", "m", "p", "p", "t", "t", "ng", "t", "t", "k", "t", "p", "t"]
def rr(syl):
    # Revised Romanization of one Hangul syllable (the official system); "r" begins a syllable only after a vowel, in names it reads "r"
    c = ord(syl) - 0xAC00
    if not 0 <= c < 11172: return ""
    cho, jung, jong = c // 588, (c % 588) // 28, c % 28
    return CHO[cho] + JUNG[jung] + JONG[jong]
def korean(kd, db):
    syl = {}
    for k, v in KO.items():
        h, lean = v[:-1], v[-1]
        if h in kd and k in kd[h]["ko"]: syl.setdefault(k, (h, lean))          # keep only hanja whose Korean reading really is that syllable
    first = [s for s in syl if syl[s][1] in "efm"]
    out = []
    for a in first:
        for b in syl:
            if a == b and a not in ("지", "은", "서"): continue
            la, lb = syl[a][1], syl[b][1]
            if "f" in (la + lb) and "m" in (la + lb): continue                   # a girl's syllable and a boy's syllable don't make a name
            g = "g" if "f" in (la + lb) else "b" if "m" in (la + lb) else "e"
            ra, rb_ = rr(a), rr(b)
            if not ra or not rb_: continue
            if ra[-1:] in "aeiou" and rb_[:1] in "aeiou" and not rb_.startswith(("eo", "eu")): pass
            n = (ra + rb_).capitalize()
            ha, hb = syl[a][0], syl[b][0]
            meaning = f"{short(kd[ha]['m'], 1)} + {short(kd[hb]['m'], 1)}"
            out.append([n, g, a + b, ha + hb, meaning, 1 if n.lower() in db else 0])
    return out

# ─────────────────────────────────────────────────────────────
# CHINESE: common given-name characters, pinyin and meanings from CC-CEDICT
# ─────────────────────────────────────────────────────────────
ZH = dict(x.split("=") for x in """子=e 梓=e 涵=e 宇=m 轩=m 浩=m 然=e 欣=f 怡=f 雨=e 桐=e 思=e 佳=f 一=e 诺=e 晨=e 博=m 文=e 俊=m 杰=m 明=e 华=e 丽=f 芳=f
婷=f 静=f 美=f 玲=f 嘉=e 睿=m 泽=m 皓=m 铭=m 瑞=e 宸=m 辰=m 熙=f 悦=f 萱=f 琪=f 瑶=f 妍=f 彤=f 雪=f 晴=f 安=e 乐=e 心=f 若=f 梦=f 婉=f
淑=f 慧=f 敏=e 志=m 伟=m 强=m 磊=m 鹏=m 飞=m 龙=m 天=m 云=e 海=m 波=m 宁=e 平=e 康=m 健=m 毅=m 诚=m 信=m 义=m 琳=f 欢=f 颖=f 洁=f 雅=f
菲=f 薇=f 莉=f 娜=f 霞=f 燕=f 红=f 秀=f 兰=f 梅=f 月=f 春=e 秋=e 冬=e 夏=e 晓=e 小=e 欣=f 馨=f 语=f 汐=f 沫=f 可=f 艺=f 依=f 伊=f 芸=f 蕾=f
露=f 清=e 涛=m 斌=m 彬=m 豪=m 翔=m 腾=m 峰=m 山=m 林=e 森=m 远=m 航=m 舟=m 帆=e 凯=m 旭=m 阳=m 东=m 南=e 北=e 新=e 星=e 辉=m 光=m 亮=m
锦=e 程=m 墨=e 书=e 诗=f 画=f 琴=f 歌=f 舒=f 柔=f 灵=f 慕=e 霖=e 逸=m 恒=m 承=m 奕=m 煜=m 昊=m 晟=m 卓=m 越=m 骏=m 珊=f 媛=f""".split())
TONE = {"a": "āáǎàa", "e": "ēéěèe", "i": "īíǐìi", "o": "ōóǒòo", "u": "ūúǔùu", "ü": "ǖǘǚǜü"}
def tone_mark(p):
    p = p.lower().replace("u:", "ü")
    m = re.fullmatch(r"([a-zü]+)([1-5])", p)
    if not m: return p
    s, t = m.group(1), int(m.group(2))
    for v in ("a", "e", "ou"):
        if v in s: i = s.index(v); break
    else: i = max(j for j, c in enumerate(s) if c in "aeiouü")
    return s[:i] + TONE[s[i]][t - 1] + s[i + 1:]
def cedict():
    out = {}
    for l in gzip.open(os.path.join(RAW, "cedict_1_0_ts_utf-8_mdbg.txt.gz"), "rt", encoding="utf-8"):
        m = re.match(r"(\S+) (\S+) \[([^\]]+)\] /(.*)/", l)
        if not m or len(m.group(2)) != 1: continue
        simp, py, gl = m.group(2), m.group(3), m.group(4).split("/")
        gl = [x for x in gl if not re.match(r"(surname|variant of|old variant|used in|see |CL:|abbr)", x)]
        if not gl or py[0].isupper(): continue
        out.setdefault(simp, []).append((py, gl))
    return out
def chinese(db):
    cd = cedict()
    chars = {}
    for c, lean in ZH.items():
        if c in cd: chars[c] = (cd[c][0][0], cd[c][0][1][0].split(";")[0].strip(), lean)
    out = []
    for a in chars:
        for b in chars:
            pa, ga, la = chars[a]; pb, gb, lb = chars[b]
            if "f" in (la + lb) and "m" in (la + lb): continue
            if a == b and la != "f": continue                                       # doubled names (Tingting) are a girls' tradition
            g = "g" if "f" in (la + lb) else "b" if "m" in (la + lb) else "e"
            sa, sb = re.sub(r"\d", "", pa).replace("u:", "ü"), re.sub(r"\d", "", pb).replace("u:", "ü")
            sep = "'" if sb[0] in "aeo" else ""                                      # pinyin's apostrophe before a, e, o (Zi'ang)
            n = (sa + sep + sb).replace("ü", "u").capitalize()
            out.append([n, g, a + b, f"{tone_mark(pa)} {tone_mark(pb)}", f"{re.sub(r' *[(].*?[)]', '', ga)} + {re.sub(r' *[(].*?[)]', '', gb)}", 1 if n.lower() in db else 0])
    # one name, many character pairs: keep the first pair for each spelling and gender
    seen, uniq = set(), []
    for r in out:
        k = (r[0].lower(), r[1])
        if k not in seen: seen.add(k); uniq.append(r)
    return uniq

if __name__ == "__main__":
    kd, db = kanjidic(), db_names()
    ja, ko, zh = japanese(kd, db), korean(kd, db), chinese(db)
    # one spelling, one home: Japanese (real names) first, then Korean, then Chinese (Yui is Japanese, Minjun Korean)
    taken = {r[0].lower() for r in ja}
    ko = [r for r in ko if r[0].lower() not in taken]; taken |= {r[0].lower() for r in ko}
    zh = [r for r in zh if r[0].lower() not in taken]
    for lab, s_ in (("Japanese", ja), ("Korean", ko), ("Chinese", zh)):
        print(f"{lab:9} {len(s_):>7,} names · {dict(collections.Counter(r[1] for r in s_))}")
    json.dump({"ja": ja, "ko": ko, "zh": zh}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"→ {OUT} ({os.path.getsize(OUT) // 1024} KB)")
