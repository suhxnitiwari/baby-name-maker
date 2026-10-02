# Lullabyte

*Baby names, engineered softly. I can code you a name.*

Find the perfect name for your baby. **516,000+ names**: 256,000+ real names from official registries plus 260,000 generated, including hundreds of real ones with meanings and stories from many cultures and faiths.

## Where the names come from
| Type | How many | What it is |
|---|---|---|
| **Real names** | ~550 | Hand-picked names with meanings and stories: Greek, Indian (Sanskrit, Tamil, Punjabi), Arabic, Persian, Hebrew, Latin, Irish, Norse, Japanese, African and more. Includes names from the Bible, the Quran, Hindu epics, Sikh gurus, the life of the Buddha, Jain tradition, and Greek, Norse and Celtic myth. |
| **Built from real roots** | ~3,800 | Made the traditional way by joining meaningful parts: Sanskrit (Dev + ansh), Greek (Theo + dora), Germanic (Wil + helm), Norse (Thor + stein), and Arabic (Abdul + one of the 99 names of God, -uddin, -ullah). Each one comes with its meaning. |
| **Invented originals** | 230,000+ | Brand-new names made from syllables and checked to make sure they're easy to say. |

## Features
- **Mom + Dad compiler:** parents' names plus optional family names to honor. It splices names and scans thousands of real names for both parents' sounds, then removes hard-to-say results, tests them with your surname and ranks them. A visible pipeline shows real counts at every step. Every name shows its provenance (which letters came from whom, contribution %, how it was built), a badge (Real name / Rare real name / Built from roots / New blend), and top picks by category (best overall, most equal blend, best real name, rarest, easiest to say, best with surname, wildcard). 🔒 Lock a start or ending and it rebuilds around it.
- **Your taste (taste model):** type names you love and don't; it learns your profile (softness, syllables, endings, cultures, rarity) and ranks ~28,000 names with a match score and a "why this name?" breakdown. Telling it why you reject a name updates the model.
- **Feminine / Masculine / Gender neutral**
- **Spelling variations:** common real-world spellings and forms (Mohammed → Muhammad, Mohamed, Mehmet; Leila → Layla, Laila), names that sound alike, and possible letter-swap spellings (Jayden → Jaiden, Suhani → Suhaani)
- **Vibes:** every card has a color aura, vibe words (dreamy, regal, fierce, timeless…) and Soft↔Strong, Classic↔Modern, Playful↔Elegant meters
- **Meaning groups:** Beautiful, Feminine & graceful, Kind & gentle, Strong, Brave & fierce, Wise, Divine & faith, Royal & noble, Light & sun, Moon & stars, Nature, Love & joy, and more. Girl themes are listed first for girls, boy themes first for boys.
- **Religion filter:** Christian, Islamic, Jewish, Hindu, Sikh, Buddhist, Jain, Zoroastrian, Greek, Norse and Celtic myth
- **Culture / ethnicity** and **language** filters
- **Letter filters:** starts with a letter, first 2 letters, ends with
- **Mom + Dad:** blends both parents' names, and suggests names that use both their initials
- **Popular:** top names this year and over the last 5, 50 and 100 years, by country
- **Popularity badges:** each card and spelling shows its real rank, like #3 US 2024

## Real names database
`data/names-db.tsv` holds **256,487 real first names** from 10 official government registries, built by `scripts/build_names_db.py`. Columns: name, gender (f / m / u = used for both / ? = registry has no sex), countries, people recorded. Registry placeholders such as "Baby" or "Unknown" are removed. About 58,000 entries are compound given names (e.g. "María del Carmen"), which Spain, Québec and Argentina register as single names.

| Source | Coverage | License |
|---|---|---|
| US Social Security Administration | 1880–2024, names given to 5+ babies a year | Public domain |
| Statistics Canada, table 17-10-0147-01 | 1991–2025 | Open Government Licence – Canada |
| Retraite Québec | 1980–2025, every name given twice or more | CC BY 4.0 |
| Office for National Statistics (England & Wales) | 1996–2025 | Open Government Licence v3.0 |
| Central Statistics Office Ireland (VSA50/VSA60) | 1964–2024, 3+ babies a year | CC BY 4.0 |
| INSEE France | 1900–2024 | Licence Ouverte |
| INE Spain | whole population, names held by 20+ people | Reuse with attribution |
| Swiss Federal Statistical Office | whole population by birth year | Attribution; non-commercial use |
| NSW Registry of Births, Deaths & Marriages | 1952–2025, top 100 | CC BY 4.0 |
| RENAPER Argentina | newborns 2012–2024 | Reuse with attribution |

## Popularity data
`data/popularity.json` (built by `scripts/build-popularity.py`) powers the Popular tab and rank badges: US, Canada, NSW, England & Wales and France.

## Generated names
About 260,000 more names are generated in the browser: ~3,800 built from Sanskrit, Greek, Germanic, Norse and Arabic roots (with meanings), and ~256,000 invented from syllables (no meanings). Generated names never repeat a real name from the database.

## Run it
No build step. Open `index.html`, or serve the folder with any static server.

## Add names
Add a line to `REAL_RAW` in `names.js`:
```
Name|g/b/e|Culture|Language|Religion1,Religion2|meaning|story
```
