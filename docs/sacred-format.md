# Sacred-text references: shared format

One TSV per tradition family in `data/sacred/` (UTF-8, tab-separated, header row, no quoting).
One row per (name form, figure, text corpus). Keep every source string exactly (diacritics, original script).

| column | meaning |
|---|---|
| name | the form people write today in Latin script (Abraham, Ibrahim, Krishna, Sariputta). Several rows can share a figure. |
| figure_id | stable id of the person/being: Wikidata QID when one exists (Q9181 Abraham), else `slug:<tradition>:<name>`. The same figure across traditions shares ONE id (Abraham / Avraham / Ibrāhīm). |
| figure | display label of the figure ("Abraham, patriarch") |
| sex | girl · boy · blank (unknown, or not a person); from the source, never guessed |
| original | the form in the text's own script (אַבְרָהָם, إِبْرَاهِيم, कृष्ण, Ἰωάννης); Pāli in roman is fine |
| translit | scholarly transliteration (ʾAvrāhām, Ibrāhīm, Kṛṣṇa, Sāriputta) |
| language | Hebrew, Aramaic, Greek, Arabic, Sanskrit, Pali, Prakrit, Gurmukhi/Punjabi … |
| tradition | Jewish, Christian, Islamic, Hindu, Buddhist, Sikh, Jain (one per row; the same figure gets one row per tradition) |
| subtradition | Theravada, Mahayana, Rabbinic, Shvetambara … or blank |
| corpus | Tanakh, New Testament, Mishnah, Talmud, Qur'an, Rigveda, Mahabharata, Valmiki Ramayana, Bhagavad Gita, Bhagavata Purana, Devi Mahatmya, Harivamsha, Upanishads, Pali Canon, Lotus Sutra, Guru Granth Sahib, Kalpa Sutra … |
| text | book / section (Genesis, Exodus, Digha Nikaya, Adi Parva, Surah Maryam) |
| passage | first occurrence, citable (Genesis 17:5; Exodus 15:20; Qur'an 19:16; DN 16; Gita 1.4; Ang 1) |
| url | a link to read that passage (sefaria.org, stepbible.org or biblegateway.com, quran.com, suttacentral.net, gretil, sikhitothemax/banidb) |
| occurrences | how many times the form occurs in the corpus, if counted; blank if unknown (never 0 for unknown) |
| entity_type | human, deity, prophet, sage, saint, disciple, bodhisattva, angel, royal, demon, mythological_being, place, tribe, title, epithet, virtue, concept |
| name_role | personal (a person's own name) · epithet (another name for a figure: Partha, Janaki) · title · divine (a name of God / a deity) · word (a word later used as a name, not a name in the text) |
| status | attested = this name, in standard romanization, appears in the text for this figure · related = a later or variant form of an attested name (Mary ← Miriam, Ibraheem ← Ibrāhīm) · association = connected to a sacred figure, concept or tradition but NOT itself a name in the text (Christian saints, rabbis outside the text) |
| relation | for related/epithet rows: "epithet of Arjuna", "later form of Miriam", "Pali form of Sanskrit Śāriputra" |
| source | dataset + license (STEPBible TIPNR, CC BY 4.0) |
| confidence | 0–1 |

Rules: cite only what the source shows. No baby-name websites. Places, tribes, demons, concepts are kept but flagged by entity_type (the app never suggests them as names). "Cultural usage" (a name common among followers, no textual tie) is NOT written here; the app derives it from existing faith tags.
