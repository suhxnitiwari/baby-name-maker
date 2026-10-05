# Romanizations of Russian Cyrillic, each a published system applied letter by letter (deterministic, no guessing):
#   bgn        BGN/PCGN 1947 (US Board on Geographic Names / UK Permanent Committee on Geographical Names), strict:
#              е/ё are ye/yë at the start of a word and after a vowel, й, ъ or ь; ъ ” and ь ’; "·" separates т·с, ш·ч, з·х
#              and й/ы before а, у, ы, э, so they can't be misread as ts, shch, zh, ya ...
#   bgn_plain  the same without its marks (no ’ ” ·, ë as e): how BGN/PCGN spellings are usually printed in English
#   iso9       ISO 9:1995 (GOST 7.79-2000 system A): one Latin letter per Cyrillic letter
#   scientific the scholarly (linguistic) transliteration
#   icao       ICAO Doc 9303 as adopted for Russian passports in 2013 (FMS order 320, used from 2014)
import re, unicodedata

VOWELS = set("аеёиоуыэюя")
_COMMON = dict(zip("абвгдзиклмнопрстуф", "a b v g d z i k l m n o p r s t u f".split()))
TABLES = {
    "bgn": {**_COMMON, "ж": "zh", "й": "y", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch", "ъ": "”", "ы": "y", "ь": "’", "э": "e", "ю": "yu", "я": "ya"},
    "iso9": {**_COMMON, "е": "e", "ё": "ë", "ж": "ž", "й": "j", "х": "h", "ц": "c", "ч": "č", "ш": "š", "щ": "ŝ", "ъ": "ʺ", "ы": "y", "ь": "ʹ", "э": "è", "ю": "û", "я": "â"},
    "scientific": {**_COMMON, "е": "e", "ё": "ë", "ж": "ž", "й": "j", "х": "x", "ц": "c", "ч": "č", "ш": "š", "щ": "šč", "ъ": "ʺ", "ы": "y", "ь": "ʹ", "э": "è", "ю": "ju", "я": "ja"},
    "icao": {**_COMMON, "е": "e", "ё": "e", "ж": "zh", "й": "i", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch", "ъ": "ie", "ы": "y", "ь": "", "э": "e", "ю": "iu", "я": "ia"},
}
SYSTEMS = {"bgn": "BGN/PCGN", "iso9": "ISO 9", "scientific": "scientific", "icao": "ICAO passport 2013"}

def strip_stress(s):
    # Wiktionary marks stress with a combining acute (Алекса́ндр); й and ё are kept whole
    s = unicodedata.normalize("NFD", s).replace("́", "").replace("̀", "")
    return unicodedata.normalize("NFC", s)

def is_russian_cyrillic(s):
    return bool(s) and all(c.lower() in "абвгдеёжзийклмнопрстуфхцчшщъыьэюя" or c in "- " for c in s)

def _word(w, system):
    t, out = TABLES[system], []
    low = w.lower()
    for i, c in enumerate(low):
        prev = low[i - 1] if i else ""
        nxt = low[i + 1] if i + 1 < len(low) else ""
        if system == "bgn" and c in "её":
            soft = not prev or prev in VOWELS or prev in "йъь"
            r = ("y" if soft else "") + ("e" if c == "е" else "ë")
        elif c in t: r = t[c]
        else: return None
        if system == "bgn" and prev and ((prev, c) in (("т", "с"), ("ш", "ч"), ("з", "х")) or (prev in "йы" and c in "ауыэ")):
            r = "·" + r
        out.append(r)
    s = "".join(out)
    # capital first letter (a mark such as ” can't start a name)
    return s[:1].upper() + s[1:] if s else s

def romanize(cyr, system):
    cyr = strip_stress(cyr)
    if not is_russian_cyrillic(cyr): return None
    if system == "bgn_plain":
        s = romanize(cyr, "bgn")
        return s and re.sub(r"[’”·]", "", s).replace("ë", "e").replace("Ë", "E")
    parts = [w if w in ("-", " ") or not w else _word(w, system) for w in re.split(r"([- ])", cyr)]
    if any(p is None for p in parts): return None
    return "".join(parts)

if __name__ == "__main__":
    for n in ("Александр", "Сергей", "Артём", "Евгений", "Наталья", "Юлия", "Фёдор", "Ксения", "Подъячий", "Матвей", "Анна-Мария"):
        print(n, {k: romanize(n, k) for k in ("bgn", "bgn_plain", "iso9", "scientific", "icao")})
