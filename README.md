# Lullabyte

*Every name is a lullaby.*

**Live:** [suhxnitiwari.github.io/baby-name-maker](https://suhxnitiwari.github.io/baby-name-maker/)

## What it is

A crib mobile for baby names. Every name plays its own lullaby: on the first screen each note hangs from a wooden mobile as a
felt charm (low notes hang long, high notes short, so the melody is the mobile's shape), and every result is a garland of felt
beads strung on a melody line.

Behind the softness is a lot of data: **over 820,000 names** in the browser, made of 529,563 real first names from official
government records in 18 countries, tens of thousands of names with meanings and stories from 160+ cultures and sacred texts,
12,105 names built from real roots, and 245,015 invented originals. There is a taste model that learns what you like, and a
Mom + Dad compiler that shows exactly which letters came from whom. No server, no build step, no framework.

## How a name becomes a tune
`musicbox.js` turns any name into a melody, the same way every time:

| | Means |
|---|---|
| A note | one syllable |
| Pitch | the vowel sound: "oo" low and dark, "oh", "ah" in the middle, "eh", "ee" high and bright; "ay" glides between two notes |
| Nudge | the consonant before the vowel: lips (M, B, P) pull the note down, L and R lift it a step, the tongue tip (N, D, T, S) two, the back of the mouth (K, G, J) three |
| Small holes | a hard K/T/D adds a pluck below the note, an S/SH adds a sparkle an octave up |
| Rhythm | the first syllable is held longest; an open ending (-a, -i) rings out |
| The ring ○ | every tune comes home to the same low C: the Lullabyte signature |

Notes sit on a two-octave pentatonic ladder, so no name can sound wrong. Spellings that sound alike make the same tune (Layla, Leila and Laila play one song; Lila is a different tune). The sound is synthesized in the browser with Web Audio: each note is a music-box chime, a stack of sine partials with a long ring and a small generated room. `mobile.js` draws the mobile on a canvas: it turns slowly, you drag sideways to spin it and tap to play.

## How it's built

- **A sound-alike key.** `soundKey()` in `generator.js` normalizes spelling to sound (ph → f, soft c → s, doubled letters collapsed, silent final e and h dropped) so Layla, Leila and Laila share one melody and one spelling family, and your taste results never hand you a respelling of a name you already typed.
- **A taste model** (`taste.js`). From the names you love it learns a profile: softness, modernity and elegance, syllable range, favorite ending, cultures and how rare you like names. Each candidate is scored on six weighted signals, led by sound similarity (Dice coefficient on letter bigrams against every name you love), then feel, length, ending, culture and rarity on a log scale. Names that sound like ones you rejected, cultures you ruled out, and lengths or popularity you said no to are penalized. It ranks every name with a meaning, every official-record name held by 30+ people, and 25,000 invented ones, shows a confidence score and a "why this name?" breakdown, and remembers your taste in `localStorage`.
- **The Mom + Dad compiler** (`compiler.js`). Parents' names (plus family names to honor) are spliced at syllable cut points with every letter's origin tracked, real names are scanned for both parents' sounds, then results are filtered for pronounceability, tested with your surname and ranked. A visible pipeline shows real counts at every step, and every name shows its provenance (which letters came from whom and the contribution %).
- **Never an empty page.** When no name fits every blank of a search, it loosens the fewest, least important blanks by a cost table (feel and length first, letters last), says which ones it loosened, and composes new names that keep every letter, length and feel you asked for.
- **Names built from roots** (`generator.js`). Sanskrit, Greek, Germanic and Norse names joined from two meaningful elements with vowel elision (Chandra + esh → Chandresh), and Arabic names formed from "servant of" one of the 99 names of God, each with its meaning.
- **A reproducible data pipeline** (`scripts/`). Python scripts fetch and merge government open data, Wiktionary, Wikidata and JMnedict into compact TSV and JSON files the page loads on demand.

## Where the names come from
| Type | How many | What it is |
|---|---|---|
| **Official records** | 529,563 | Real first names from government records in 18 countries (`data/names-db.tsv`) |
| **Hand-written names** | ~3,200 entries | Names with meanings and stories in `names.js`: Greek, Indian (Sanskrit, Tamil, Punjabi), Arabic, Persian, Hebrew, Latin, Irish, Norse, Japanese, African, Pacific, Latin American and more, including names from the Bible, the Quran, Hindu epics, Sikh gurus, the life of the Buddha, Jain tradition, and Greek, Norse and Celtic myth |
| **Sacred texts, cultures, East Asia** | 13,695 + 32,000+ + 47,569 | Names with stories from scripture, names sorted into 123 cultures, and Japanese, Korean and Chinese names with their characters (details below) |
| **Built from real roots** | 12,105 | Made the traditional way by joining meaningful parts: Sanskrit (Dev + ansh), Greek (Theo + dora), Germanic (Wil + helm), Norse (Thor + stein), and Arabic (Abdul + one of the 99 names of God, -uddin, -ullah). Each one comes with its meaning. |
| **Invented originals** | 245,015 | Brand-new names made from syllables and checked to make sure they're easy to say |

Overlapping names are merged, so the total on the page counts each name once.

## Features
- **Mom + Dad compiler:** every name gets a badge (Real name / Rare real name / Built from roots / New blend) and top picks by category (best overall, most equal blend, best real name, rarest, easiest to say, best with surname, wildcard). Lock a start or ending and it rebuilds around it.
- **Your taste:** type names you love and don't, get ranked matches with a "why this name?" breakdown. Telling it why you reject a name updates the model.
- **Feminine / Masculine / Gender neutral**
- **Spelling variations:** common real-world spellings and forms (Mohammed → Muhammad, Mohamed, Mehmet; Leila → Layla, Laila), names that sound alike, and possible letter-swap spellings (Jayden → Jaiden, Suhani → Suhaani)
- **Vibes:** every card has a color aura, vibe words (dreamy, regal, fierce, timeless…) and Soft↔Strong, Classic↔Modern, Playful↔Elegant meters
- **Meaning groups:** Beautiful, Feminine & graceful, Kind & gentle, Strong, Brave & fierce, Wise, Divine & faith, Royal & noble, Light & sun, Moon & stars, Nature, Love & joy, and more. Girl themes are listed first for girls, boy themes first for boys.
- **Religion filter:** Christian, Islamic, Jewish, Hindu, Sikh, Buddhist, Jain, Zoroastrian, Greek, Norse and Celtic myth
- **Sacred texts:** names from the Torah, the Bible, the Quran, the Bhagavad Gita, the Mahabharata, the Ramayana, the Puranas and the Vedas
- **Culture / ethnicity** and **language** filters
- **Letter filters:** starts with a letter, first 2 letters, ends with
- **Mom + Dad:** blends both parents' names, and suggests names that use both their initials
- **Popular:** top names this year and over the last 5, 50 and 100 years, by country
- **Popularity badges:** each card and spelling shows its real rank, like #3 US 2024

## Real names database
`data/names-db.tsv` holds **529,563 real first names** from official government records in **18 countries**: the US, Canada (national, Québec, BC, Alberta, Ontario), the UK (England & Wales, Northern Ireland), Ireland, France, Spain, Switzerland (national, Zürich), Germany (~1,000 city open-data files), Austria, Norway, Poland (the PESEL register), Portugal, Luxembourg, Australia (NSW, SA, Victoria, Queensland, Tasmania), Argentina, Chile, Brazil and Israel (Hebrew-script names turned into verified Latin spellings by `scripts/hebrew_names.py`). Columns: name, gender (f / m / u = used for both / ? = registry has no sex), countries, people recorded.

```
python3 scripts/fetch_world.py     # download every reachable source into raw/ (not committed)
python3 scripts/build_world.py     # merge them all into data/names-db.tsv
```

- **One name per entry.** Spain, Québec, Argentina and Switzerland register a person's full given name ("María del Carmen", "Jean-Pierre") as one name. `scripts/single_names.py` splits those, adds each person to every single name they carry, and drops pieces that never appear as a name on their own ("Dios").
- **Clean.** Latin script only (the music box needs letters it can sound out), every name has a vowel (no "Md", "Jr"), registry placeholders ("Baby", "Unknown", "Kein Vorname", "Recién nacido") and patronymics removed. Names that differ only by accent stay separate spellings (José, Jose).

Every source, its license, and the countries we checked that don't publish (or that still need a manual download: Finland, Belgium, Scotland, New Zealand, Israel) are in **[docs/name-sources.md](docs/name-sources.md)**.

## Names from sacred texts
`data/scripture-names.json` (built by `scripts/build_scriptures.py`) adds **13,695 names with stories**: every person named in the **Bible** (the Torah, the Hebrew Bible and the New Testament, with Hitchcock's meanings), the people, gods and sages of the **Mahabharata, Bhagavad Gita, Ramayana, Puranas and Vedas**, and every person, angel and name-giving word of the **Quran**, each with its verse. Search them with the "named in ⟨the Torah / the Quran / the Bhagavad Gita…⟩" blank. Sources and licenses: [docs/name-sources.md](docs/name-sources.md).

## Japanese, Korean and Chinese names
`data/east-asian-names.json` (built by `scripts/build_east_asian.py`) adds **33,831 real Japanese given names** from JMnedict, each with its usual kanji and meaning (Haruto: 春人, spring + person), plus **3,881 Korean** and **9,857 Chinese** names built from name syllables and characters with their hanja or hanzi, readings and meanings (Minjun: 敏俊; Zihan: 子涵, zǐ hán). Sources and how they're built: [docs/name-sources.md](docs/name-sources.md).

## Names sorted into 123 cultures
`data/culture-names.json` (built by `scripts/build_cultures.py` from Wiktionary and Wikidata) sorts **32,000+ names into 123 cultures**, from Yoruba, Igbo, Hausa and Akan to Tamil, Telugu, Bengali and Punjabi, Vietnamese, Filipino, Kazakh, Armenian, Georgian, Russian, Albanian and Māori, plus broad baskets (African, South Asian, Slavic, Central Asian, Pacific…). Names in other scripts get their usual Latin spelling, checked against registered names. Search with "with ⟨Yoruba / Tamil / Pacific…⟩ roots". Details: [docs/name-sources.md](docs/name-sources.md).

## Popularity data
`data/popularity.json` (built by `scripts/build-popularity.py`) powers the Popular tab and rank badges: US, Canada, NSW, England & Wales and France.

## Generated names
About 257,000 more names are generated in the browser: 12,105 built from Sanskrit, Greek, Germanic, Norse and Arabic roots (with meanings), and 245,015 invented from syllables (no meanings). Generated names never repeat a real name from the database.

## Tech stack
Vanilla JavaScript · Web Audio API · Canvas 2D · Python data scripts · government open data, Wiktionary, Wikidata, JMnedict · GitHub Pages

## Run it
No build step. Serve the folder with any static server (`python3 -m http.server`) so the data files can load.

## Add names
Add a line to `REAL_RAW` in `names.js`:
```
Name|g/b/e|Culture|Language|Religion1,Religion2|meaning|story
```

Built by [Suhani Tiwari](https://suhanitiwari.com).
