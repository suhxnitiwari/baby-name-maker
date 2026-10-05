"""Latin spellings of Arabic given names → their Arabic script (data/arabic-forms.json).

Wikidata given-name items marked as Arabic-language names (P407 Arabic, or an Arabic native label) carry their Latin spellings as
labels and aliases: Yusuf, Yousif, Yousef, Youssef → يوسف. Gulf and South Asian spellings (Yousif, Ebrahim, Hussain, Fatema) stay
their own names; this only links them to the Arabic. Raw query result: raw/wd-arabic/arabic-name-latin-forms.json (Wikidata, CC0).
"""
# The query and the folding are in the session that produced the data; rerun by re-querying Wikidata with:
#   ?item wdt:P31 (given name classes); { ?item wdt:P407 wd:Q13955 } UNION { ?item wdt:P1705 ?nat FILTER(LANG(?nat)="ar") }
#   ?item rdfs:label ?ar (ar); ?item rdfs:label|skos:altLabel ?lat (en, mul, fr, de, id, ms, tr, ur, nl, sv)
