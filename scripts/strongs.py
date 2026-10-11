"""Strong's Hebrew and Greek dictionaries (raw/strongs, Open Scriptures, CC BY-SA; Strong 1890, public domain): what a Bible name means.

meaning(name) → (strongs id, meaning, the entry's own description) for a person or place called exactly that in the King James Version.
The meaning is the one Strong gives at the end of the derivation ("from H3201 and H3050; Jah will enable;"), followed through
"the same as H…" links; Jah and Jehovah are written Yahweh, as scholars write the divine name today.
"""
import json, os, re
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _load(f):
    t = open(os.path.join(ROOT, "raw", "strongs", f), encoding="utf-8").read()
    return json.loads(t[t.index("{"):t.rindex("}") + 1])
H, G = _load("strongs-hebrew-dictionary.js"), _load("strongs-greek-dictionary.js")
ALL = {**H, **G}
norm = lambda s: re.sub(r"[^a-z]", "", (s or "").lower().replace("æ", "ae").replace("œ", "oe"))
YAH = lambda s: re.sub(r"\b(Jah|Jehovah)\b", "Yahweh", s)

def _tail(k, depth=0):
    v = ALL.get(k)
    if not v or depth > 3: return ""
    d = v.get("derivation", "") or ""
    m = re.findall(r";\s*([^;]+?);?\s*$", d)
    if m and not re.search(r"\b[HG]\d", m[-1]): return m[-1].strip()
    own = _first(k)                                          # "dear to God; Timotheus, a Christian", "plain, Sharon, the name of a place"
    if own: return own
    same = re.match(r"\s*(?:the same(?: \([^)]*\))? as|a form of|feminine of|of (?:Hebrew|Chaldee) origin \()\s*([HG])0*(\d+)", d)
    if same: return _tail(same.group(1) + same.group(2), depth + 1)
    return ""
def _first(k):
    s = (ALL.get(k, {}).get("strongs_def", "") or "").strip()
    s = re.split(r";|,\s(?=[A-Z])", s)[0].strip()            # up to the person or place it names
    s = re.sub(r"\((?:i\.e\.|or)[^)]*\)", "", s).strip(" ,")
    return "" if not s or not s[0].islower() else s

INDEX = {}
for k, v in ALL.items():
    for w in re.split(r"[,.;()]", v.get("kjv_def", "") or ""):
        w = w.strip()
        if w[:1].isupper() and " " not in w: INDEX.setdefault(norm(w), []).append(k)

def meaning(name):
    n = norm(name)
    for k in INDEX.get(n, []) + INDEX.get(n[:-1] if n.endswith("h") else n + "h", []):
        m = _tail(k)
        m = re.sub(r"\s*\([^()]*[HG]\d[^()]*(?:\([^()]*\))?[^()]*\)", "", m)   # "(larger than G3037 (λίθος))"
        if m.count("(") > m.count(")"): m = m[:m.rindex("(")]                  # "cassia (as peeled"
        m = re.sub(r"^(properly|literally|i\.e\.),?\s+", "", m.strip(" ,."))
        if m and len(m) < 60: return k, YAH(m), ALL[k].get("strongs_def", "")
    return None, "", ""
