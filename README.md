# 👶 Baby Name Maker

Find the perfect name for your baby boy or girl. There are **240,000+ names**, including hundreds of real ones with meanings and stories from many cultures and faiths.

## Where the names come from
| Type | How many | What it is |
|---|---|---|
| **Real names** | ~550 | Hand-picked names with meanings and stories: Greek, Indian (Sanskrit, Tamil, Punjabi), Arabic, Persian, Hebrew, Latin, Irish, Norse, Japanese, African and more. Includes names from the Bible, the Quran, Hindu epics, Sikh gurus, the life of the Buddha, Jain tradition, and Greek, Norse and Celtic myth. |
| **Built from real roots** | ~3,800 | Made the traditional way by joining meaningful parts: Sanskrit (Dev + ansh), Greek (Theo + dora), Germanic (Wil + helm), Norse (Thor + stein), and Arabic (Abdul + one of the 99 names of God, -uddin, -ullah). Each one comes with its meaning. |
| **Invented originals** | 230,000+ | Brand-new names made from syllables and checked to make sure they're easy to say. |

## Features
- **Feminine / Masculine / Gender neutral**
- **Spelling variations:** common real-world spellings and forms (Mohammed → Muhammad, Mohamed, Mehmet; Leila → Layla, Laila), names that sound alike, and possible letter-swap spellings (Jayden → Jaiden, Suhani → Suhaani)
- **Vibes:** every card has a color aura, vibe words (dreamy, regal, fierce, timeless…) and Soft↔Strong, Classic↔Modern, Playful↔Elegant meters
- **Mom + Dad reveal:** the top blend decodes from random characters into the name
- **Meaning groups:** Beautiful, Feminine & graceful, Kind & gentle, Strong, Brave & fierce, Wise, Divine & faith, Royal & noble, Light & sun, Moon & stars, Nature, Love & joy, and more. Girl themes are listed first for girls, boy themes first for boys.
- **Religion filter:** Christian, Islamic, Jewish, Hindu, Sikh, Buddhist, Jain, Zoroastrian, Greek, Norse and Celtic myth
- **Culture / ethnicity** and **language** filters
- **Letter filters:** starts with a letter, first 2 letters, ends with
- **Mom + Dad:** blends both parents' names, and suggests names that use both their initials
- **Popular:** top names this year and over the last 5, 50 and 100 years, by country
- **Popularity badges:** each card and spelling shows its real rank, like #3 US 2024

## Popularity data
Official government statistics, built into `data/popularity.json` by `scripts/build-popularity.py`:

| Where | Years | Source |
|---|---|---|
| United States | 1880–2024 | Social Security Administration (public domain) |
| Canada | 1991–2025 | Statistics Canada, table 17-10-0147-01 (Open Government Licence – Canada) |
| Australia · New South Wales | 1952–2025 (top 100) | NSW Registry of Births, Deaths & Marriages (CC BY 4.0) |
| England & Wales (incl. London) | 1996–2025 | Office for National Statistics (Open Government Licence v3.0) |
| France | 1900–2024 | INSEE (Licence Ouverte) |

## Run it
No build step. Open `index.html`, or serve the folder with any static server.

## Add names
Add a line to `REAL_RAW` in `names.js`:
```
Name|g/b/e|Culture|Language|Religion1,Religion2|meaning|story
```
