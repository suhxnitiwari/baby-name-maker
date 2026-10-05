"""Promote hand-checked rows from data/sacred/indic-review.tsv into data/sacred/indic-promoted.tsv.

build_sacred_indic.py sends every name that is also a common word (Kausalyā, Viśvāmitra, Vālmīki…) to review. These are the
well-known figures from that pile, checked one by one: the right person, the right work, a real first passage. Where the
lexicon's gloss makes a poor label ("Urmila, several women"), the label is rewritten; where the row ties a name to the wrong
person (Mahādeva → Vishnu, Janārdana → Pradyumna, Śaibya → a horse), it is left in review.
Run after build_sacred_indic.py; build_sacred.py reads the result with the other TSVs.
"""
import csv, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, OUT = os.path.join(ROOT, "data/sacred/indic-review.tsv"), os.path.join(ROOT, "data/sacred/indic-promoted.tsv")

# (corpus, name) → None to keep the row's own label, or (label, entity_type, sex) to correct it
PROMOTE = {
    ("Bhagavad Gita", "Purushottama"): None, ("Bhagavad Gita", "Achyuta"): None, ("Bhagavad Gita", "Hari"): ("Krishna, Hindu deity", "deity", "boy"),
    ("Bhagavad Gita", "Narada"): None, ("Bhagavad Gita", "Vyasa"): None, ("Bhagavad Gita", "Asita"): ("Asita Devala, a sage", "sage", "boy"),
    ("Bhagavad Gita", "Yudhamanyu"): None, ("Bhagavad Gita", "Chekitana"): ("Chekitana, a warrior on the Pandava side", "human", "boy"),
    ("Bhagavad Gita", "Uttamaujas"): None,
    ("Valmiki Ramayana", "Vishvamitra"): None, ("Valmiki Ramayana", "Manthara"): None, ("Valmiki Ramayana", "Kusha"): None,
    ("Valmiki Ramayana", "Shanta"): None, ("Valmiki Ramayana", "Anasuya"): None, ("Valmiki Ramayana", "Indrajit"): None,
    ("Valmiki Ramayana", "Jambavan"): ("Jambavan, king of the bears", "mythological_being", "boy"), ("Valmiki Ramayana", "Valmiki"): None,
    ("Valmiki Ramayana", "Kausalya"): ("Kausalya, wife of Dasharatha and mother of Rama", "royal", "girl"),
    ("Valmiki Ramayana", "Nila"): None, ("Valmiki Ramayana", "Sumantra"): None, ("Valmiki Ramayana", "Guha"): None,
    ("Valmiki Ramayana", "Sumitra"): ("Sumitra, wife of Dasharatha and mother of Lakshmana and Shatrughna", "royal", "girl"),
    ("Valmiki Ramayana", "Nala"): None, ("Valmiki Ramayana", "Sutikshna"): None, ("Valmiki Ramayana", "Lava"): None,
    ("Valmiki Ramayana", "Agastya"): ("Agastya, a sage", "sage", "boy"), ("Valmiki Ramayana", "Sharabhanga"): None,
    ("Valmiki Ramayana", "Rishyashringa"): ("Rishyashringa, the sage who married Shanta", "sage", "boy"),
    ("Valmiki Ramayana", "Urmila"): ("Urmila, wife of Lakshmana", "royal", "girl"),
    ("Mahabharata", "Achyuta"): None, ("Mahabharata", "Savitri"): None, ("Mahabharata", "Narada"): None,
    ("Mahabharata", "Vasava"): ("Indra", "deity", "boy"), ("Mahabharata", "Shankara"): ("Shiva", "deity", "boy"),
    ("Mahabharata", "Ashtavakra"): ("Ashtavakra, a sage", "sage", "boy"), ("Mahabharata", "Sudeshna"): ("Sudeshna, wife of King Virata", "royal", "girl"),
    ("Mahabharata", "Pashupati"): None, ("Mahabharata", "Shambhu"): None, ("Mahabharata", "Shrutakirti"): None,
    ("Mahabharata", "Hanuman"): ("Hanuman", "mythological_being", "boy"),
    ("Mahabharata", "Shakra"): ("Shakra, Indra", "deity", "boy"), ("Mahabharata", "Vyasa"): None,
    ("Mahabharata", "Narayana"): ("Narayana, a name of Vishnu", "deity", "boy"), ("Mahabharata", "Lomasha"): None,
    ("Mahabharata", "Shukra"): ("Shukra, teacher of the asuras", "sage", "boy"), ("Mahabharata", "Pritha"): ("Pritha (Kunti), mother of the Pandavas", "royal", "girl"),
    ("Mahabharata", "Kashyapa"): None, ("Mahabharata", "Satyavan"): ("Satyavan, husband of Savitri", "human", "boy"),
    ("Mahabharata", "Ravana"): None, ("Mahabharata", "Sugriva"): None, ("Mahabharata", "Hidimba"): None, ("Mahabharata", "Ruru"): None,
    ("Mahabharata", "Sushena"): None, ("Mahabharata", "Vibhishana"): None, ("Mahabharata", "Vinata"): None, ("Mahabharata", "Sutasoma"): None,
    ("Mahabharata", "Tryambaka"): None, ("Mahabharata", "Kadru"): ("Kadru, mother of the nagas", "mythological_being", "girl"),
    ("Mahabharata", "Kausalya"): None, ("Mahabharata", "Pramadvara"): None,
}

rows = list(csv.DictReader(open(SRC, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))
fields, done, out = list(rows[0].keys()), set(), []
for r in rows:
    key = (r["corpus"], r["name"])
    if key not in PROMOTE or key in done or r["entity_type"] in ("place", "tribe"):
        continue
    if r["sex"] == "girl" and r["name"] == "Bhima":
        continue
    fix = PROMOTE[key]
    if fix:
        r["figure"], r["entity_type"], r["sex"] = fix
    # keep only what the relation says about the name (epithet of…, patronymic); the review notes go
    r["relation"] = "; ".join(p for p in r["relation"].split("; ") if p.startswith(("epithet", "patronymic", "metronymic", "also used")))
    r["status"], r["confidence"] = "attested", "0.8"
    r["source"] += "; promoted from review after a hand check"
    done.add(key); out.append(r)

with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", quoting=csv.QUOTE_NONE, escapechar="\\", lineterminator="\n")
    w.writeheader(); w.writerows(out)
missing = sorted(set(PROMOTE) - done)
print(f"promoted {len(out)} rows to {OUT}" + (f"; not found: {missing}" if missing else ""))
