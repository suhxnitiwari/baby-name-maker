# Latin forms for names an agency prints only in another script, each a published national or standard system applied
# letter by letter (deterministic, no guessing). A name with a letter outside the table gets None, never a guess.
#   serbian     the Serbian Latin alphabet (Gaj's Latin), co-official with Cyrillic in Serbia: one Latin letter or digraph per
#               Cyrillic letter (Љ = Lj, Њ = Nj, Џ = Dž), so the conversion is exact both ways
#   korean      Revised Romanization of Korean (Ministry of Culture and Tourism, 2000), as it applies to given names: sound
#               changes between the syllables of a given name are not written (RR art. 4), so each syllable is romanized on
#               its own (initial, vowel, final) and the syllables are joined: 민준 = Minjun, 서연 = Seoyeon. Where a final
#               consonant meets a syllable that starts with a vowel, RR's hyphen against misreading is used: 은우 = Eun-u
#   greek       ELOT 743 (Hellenic Organization for Standardization, adopted by the UN), the system on Greek passports: ου = ou,
#               αυ/ευ/ηυ = av/ev/iv before a vowel or voiced consonant and af/ef/if otherwise, γγ = ng, γκ = gk, μπ = b and ντ = d
#               at the start of a name (mp, nt inside it); accents dropped
#   armenian    BGN/PCGN 1981 for Eastern Armenian, without its apostrophes (the form used on Armenian passports and in English):
#               ու = u, ե = ye and ո = vo at the start of a name, և = ev
#   kazakh, kyrgyz, russian
#               BGN/PCGN for each language's Cyrillic, without diacritics (ә = a, ғ = gh, қ = q, ң = ng, ө = o, ұ ү = u, һ = h, і = i):
#               е = ye at the start of a name or after a vowel or soft/hard sign, ё = yo, й = y, х = kh, ц = ts, ю = yu, я = ya
import unicodedata

SERBIAN = dict(zip("абвгдђежзијклљмнњопрстћуфхцчџш",
                   "a b v g d đ e ž z i j k l lj m n nj o p r s t ć u f h c č dž š".split()))

KO_INITIAL = "g kk n d tt r m b pp s ss _ j jj ch k t p h".split()
KO_VOWEL = "a ae ya yae eo e yeo ye o wa wae oe yo u wo we wi yu eu ui i".split()
KO_FINAL = [""] + "k k k n n n t l k m l l l p l m p p t t ng t t k t p t".split()

def korean(word):
    out, prev_final = [], 0
    for ch in word:
        k = ord(ch) - 0xAC00
        if not 0 <= k < 11172: return None
        i, v, f = k // 588, (k % 588) // 28, k % 28
        if out and prev_final and KO_INITIAL[i] == "_": out.append("-")
        out.append(KO_INITIAL[i].replace("_", "") + KO_VOWEL[v] + KO_FINAL[f]); prev_final = f
    s = "".join(out)
    return s[:1].upper() + s[1:]

def _apply(word, table):
    out = []
    for c in word:
        low = c.lower()
        if low not in table: return None
        r = table[low]
        out.append(r[:1].upper() + r[1:] if c != low else r)
    return "".join(out)

def _strip(s): return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

GREEK = dict(zip("αβγδεζηθικλμνξοπρσςτυφχψω", "a v g d e z i th i k l m n x o p r s s t y f ch ps o".split()))
GR_VOICED = set("αεηιουωβγδζλμνρ")

def greek(word):
    w = _strip(word.lower()).replace("ϊ", "i").replace("ϋ", "y")
    if any(c not in GREEK for c in w): return None
    out, i = [], 0
    while i < len(w):
        two, nxt = w[i:i + 2], w[i + 2:i + 3]
        if two == "ου": out.append("ou"); i += 2; continue
        if two in ("αυ", "ευ", "ηυ"): out.append({"α": "a", "ε": "e", "η": "i"}[w[i]] + ("v" if nxt and nxt in GR_VOICED else "f")); i += 2; continue
        if two == "γγ": out.append("ng"); i += 2; continue
        if two == "γκ": out.append("gk"); i += 2; continue
        if two == "γξ": out.append("nx"); i += 2; continue
        if two == "γχ": out.append("nch"); i += 2; continue
        if two == "μπ": out.append("b" if i == 0 else "mp"); i += 2; continue
        if two == "ντ": out.append("d" if i == 0 else "nt"); i += 2; continue
        out.append(GREEK[w[i]]); i += 1
    s = "".join(out)
    return s[:1].upper() + s[1:]

ARMENIAN = {"ա": "a", "բ": "b", "գ": "g", "դ": "d", "ե": "e", "զ": "z", "է": "e", "ը": "y", "թ": "t", "ժ": "zh", "ի": "i", "լ": "l", "խ": "kh",
            "ծ": "ts", "կ": "k", "հ": "h", "ձ": "dz", "ղ": "gh", "ճ": "ch", "մ": "m", "յ": "y", "ն": "n", "շ": "sh", "ո": "o", "չ": "ch", "պ": "p",
            "ջ": "j", "ռ": "r", "ս": "s", "վ": "v", "տ": "t", "ր": "r", "ց": "ts", "փ": "p", "ք": "k", "օ": "o", "ֆ": "f", "և": "ev"}

def armenian(word):
    w = word.lower()
    out, i = [], 0
    while i < len(w):
        if w[i:i + 2] == "ու": out.append("u"); i += 2; continue
        c = w[i]
        if c not in ARMENIAN: return None
        out.append("ye" if c == "ե" and i == 0 else "vo" if c == "ո" and i == 0 else ARMENIAN[c]); i += 1
    s = "".join(out)
    return s[:1].upper() + s[1:]

CYR = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
       "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
       "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya"}
CYR_EXTRA = {"kazakh": {"ә": "a", "ғ": "gh", "қ": "q", "ң": "ng", "ө": "o", "ұ": "u", "ү": "u", "һ": "h", "і": "i"},
             "kyrgyz": {"ң": "ng", "ө": "o", "ү": "u"}, "russian": {}}

def cyrillic(word, lang):
    table, w, out = {**CYR, **CYR_EXTRA[lang]}, word.lower(), []
    for i, c in enumerate(w):
        if c not in table: return None
        if c == "е" and (i == 0 or w[i - 1] in "аеёиоуыэюяәөұүіьъ"): out.append("ye")
        else: out.append(table[c])
    s = "".join(out)
    return s[:1].upper() + s[1:]

def romanize(name, system):
    if system == "korean": return korean(name.strip())
    if system in ("greek", "armenian", "kazakh", "kyrgyz", "russian"):
        fn = {"greek": greek, "armenian": armenian}.get(system) or (lambda w: cyrillic(w, system))
        parts = [fn(p) for p in unicodedata.normalize("NFC", name.strip()).split()]
        return None if not parts or None in parts else " ".join(parts)
    table = {"serbian": SERBIAN}[system]
    name = unicodedata.normalize("NFC", name.strip())
    parts = []
    for sep_part in name.replace("-", " - ").split():
        if sep_part == "-": parts.append("-"); continue
        r = _apply(sep_part, table)
        if r is None: return None
        parts.append(r)
    return " ".join(parts).replace(" - ", "-")

if __name__ == "__main__":
    for n, sy in [("ΓΕΩΡΓΙΟΣ", "greek"), ("ΕΛΕΥΘΕΡΙΑ", "greek"), ("ΕΥΑΓΓΕΛΙΑ", "greek"), ("ΚΩΝΣΤΑΝΤΙΝΟΣ", "greek"), ("ΧΡΙΣΤΙΝΑ", "greek"),
                  ("ΝΑΡԵԿ".replace("Ԑ","Ե"), "armenian"), ("ԴԱՎԻԹ", "armenian"), ("ՄԻՔԱՅԵԼ", "armenian"), ("ՍՈՖԻԱ", "armenian"), ("ԵՎԱ", "armenian"),
                  ("АЙГЕРИМ", "kazakh"), ("ӘЛИХАН", "kazakh"), ("АНАСТАСИЯ", "kazakh"), ("НУРСУЛТАН", "kazakh"), ("АЙЖАН", "kyrgyz"), ("ЭМИР", "kyrgyz")]:
        print(n, romanize(n, sy))
    for n in ["Љиљана", "Анђела", "Ђорђе", "Џемиле", "Његош", "Милица"]:
        print(n, romanize(n, "serbian"))
    for n in ["민준", "서연", "지우", "하윤", "은우", "리아", "이준", "예준", "도윤", "서윤", "시우", "건우", "주원", "채원", "윤서", "지민"]:
        print(n, romanize(n, "korean"))
