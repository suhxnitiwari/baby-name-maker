"""Does a Devanagari (or other Indic) spelling really spell this name? Read it back into Latin letters and compare consonants.
Sandhya ↔ संधि fails (s-n-dh vs s-n-dh-y), Rana ↔ राणी passes the consonants but its last vowel says Rani, so vowels at the end count too."""
import unicodedata, re
CONS = {"क":"k","ख":"kh","ग":"g","घ":"gh","ङ":"n","च":"ch","छ":"chh","ज":"j","झ":"jh","ञ":"n","ट":"t","ठ":"th","ड":"d","ढ":"dh","ण":"n","त":"t","थ":"th",
        "द":"d","ध":"dh","न":"n","प":"p","फ":"ph","ब":"b","भ":"bh","म":"m","य":"y","र":"r","ल":"l","ळ":"l","व":"v","श":"sh","ष":"sh","स":"s","ह":"h",
        "क़":"q","ख़":"kh","ग़":"g","ज़":"z","ड़":"r","ढ़":"rh","फ़":"f","य़":"y"}
VOW = {"अ":"a","आ":"a","इ":"i","ई":"i","उ":"u","ऊ":"u","ऋ":"ri","ए":"e","ऐ":"ai","ओ":"o","औ":"au"}
SIGN = {"ा":"a","ि":"i","ी":"i","ु":"u","ू":"u","ृ":"ri","े":"e","ै":"ai","ो":"o","ौ":"au"}
def roman(dev):
    out, i, s = [], 0, unicodedata.normalize("NFC", dev)
    while i < len(s):
        ch = s[i]
        if s[i:i + 3] == "ज्ञ": out.append("gy"); nxt = s[i + 3] if i + 3 < len(s) else ""; out.append(SIGN.get(nxt, "a")); i += 3 + (nxt in SIGN); continue
        if ch in CONS:
            out.append(CONS[ch]); nxt = s[i + 1] if i + 1 < len(s) else ""
            if nxt == "्": i += 2; continue
            if nxt in SIGN: out.append(SIGN[nxt]); i += 2; continue
            out.append("a"); i += 1; continue
        if ch in VOW: out.append(VOW[ch])
        elif ch in "ंँ": out.append("m" if i + 1 < len(s) and s[i + 1] in "पफबभम" else "n")
        i += 1
    r = "".join(out)
    return re.sub(r"a$", "", r) if len(r) > 3 else r          # Hindi drops the final a: राम is Ram
def skel(s):
    s = s.lower().replace("w", "v").replace("ee", "i").replace("oo", "u").replace("x", "ksh").replace("f", "ph").replace("q", "k").replace("z", "j")
    s = s.replace("gy", "jn").replace("gn", "jn").replace("b", "v").replace("m", "n")   # Prajna/Pragya, Bijaya/Vijaya, Narasimha's anusvara
    while re.search(r"[^aeiou]h", s): s = re.sub(r"([^aeiou])h", r"\1", s)   # aspiration: bh/b, dh/d, chh/ch are spelled both ways
    s = re.sub(r"(.)\1", r"\1", s)                                              # doubled letters: Sannidhya, Sanidhya
    c = re.sub(r"[aeiouy]", "", s)
    return c, s[-1] if re.search(r"[aeiou]$", s) else ""
# the spelling must start with the same sound and carry the whole name, not a piece of it (नील is not Sunil, सागर is not Vidyasagar)
def matches(name, dev):
    if not re.search(r"[\u0900-\u097F]", dev): return True       # other scripts are not checked here
    a, b = skel(re.sub(r"[^a-z]", "", unicodedata.normalize("NFD", name.lower()))), skel(roman(dev).replace("ड़", "r"))
    if (a[0][:1] or "a") != (b[0][:1] or "a") or len(b[0]) < len(a[0]): return False
    return {a[1], b[1]} != {"a", "i"}                              # Rana is not Rani, Rani is not Rana
