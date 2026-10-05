-- Lullabyte's canonical database. Four questions, four layers:
--   what is this name? (names, name_forms, meanings, associations, name_references, relationships)
--   how does it sound? (pronunciations, syllables)
--   where and when is it used? (popularity_observations, sources)
--   what does Lullabyte do with it? (lullabytes)
-- Rule: "unknown", "zero", "not published" and "below the publication threshold" never mean the same thing.
-- A missing observation is never a zero; is_suppressed and the source's threshold say why it's missing.

PRAGMA foreign_keys = ON;

CREATE TABLE sources (
  source_id            TEXT PRIMARY KEY,      -- 'ssa', 'insee-2024', 'cmudict', 'wiktionary', …
  source_agency        TEXT NOT NULL,
  dataset_name         TEXT NOT NULL,
  dataset_url          TEXT,
  country              TEXT,                  -- statistical geography it covers ('England & Wales', not 'United Kingdom')
  publisher_type       TEXT,                  -- 'government' | 'statistical agency' | 'dictionary' | 'scholarly' | 'open data'
  data_start_year      INTEGER,
  data_end_year        INTEGER,
  coverage             TEXT,                  -- 'full' | 'ranked' | 'ended' | 'population'
  publication_threshold INTEGER,              -- smallest count published (NULL if not stated)
  suppression_policy   TEXT,
  rounding_policy      TEXT,
  methodology_notes    TEXT,
  license              TEXT,
  last_checked         TEXT
);

-- the identity of a name: what it IS, regardless of what any dataset did to its spelling
CREATE TABLE names (
  name_id              INTEGER PRIMARY KEY,
  display_name         TEXT NOT NULL,         -- Zoë, José, Łukasz, Rían — never overwritten
  normalized_name      TEXT NOT NULL,         -- zoe, jose, lukasz, rian — for search and joins
  native_script        TEXT,                  -- देव, 春人, רחל when known
  canonical_name_id    INTEGER REFERENCES names(name_id),   -- the main entry this spelling belongs to, if it is a variant
  is_compound_name     INTEGER DEFAULT 0,
  traditional_gender   TEXT,                  -- 'girl' | 'boy' | 'either' | NULL
  primary_origin       TEXT,                  -- culture (Yoruba, Tamil, Anglo-Norman…), never a country of registration
  origin_language      TEXT,
  kind                 TEXT,                  -- 'real' | 'root' (built from roots) | 'attested' (records only)
  first_known_use      TEXT,
  source_confidence    REAL
);
CREATE UNIQUE INDEX names_display ON names(display_name);
CREATE INDEX names_norm ON names(normalized_name);

-- every written form: scripts, romanizations, the spelling a registry printed
CREATE TABLE name_forms (
  name_id              INTEGER NOT NULL REFERENCES names(name_id),
  script               TEXT,                  -- 'Latin' | 'Devanagari' | 'Hebrew' | 'Kanji' | 'Hangul' | 'Hanzi' …
  written_form         TEXT NOT NULL,
  romanization_system  TEXT,                  -- 'Hepburn', 'Revised Romanization', 'pinyin', 'IAST'…
  is_original_form     INTEGER DEFAULT 0,
  source_id            TEXT REFERENCES sources(source_id)
);

CREATE TABLE meanings (
  name_id              INTEGER NOT NULL REFERENCES names(name_id),
  meaning              TEXT NOT NULL,
  etymology            TEXT,
  root_language        TEXT,
  source_id            TEXT REFERENCES sources(source_id),
  confidence           REAL
);

-- many-to-many: a name can belong to several cultures, faiths and languages at once
CREATE TABLE associations (
  name_id              INTEGER NOT NULL REFERENCES names(name_id),
  association_type     TEXT NOT NULL,         -- 'culture' | 'religion' | 'language'
  association_value    TEXT NOT NULL,
  source_id            TEXT REFERENCES sources(source_id)
);

-- sacred texts, myth, history, royalty: "appears in the text" vs "a later form tied to the figure"
CREATE TABLE name_references (
  name_id              INTEGER NOT NULL REFERENCES names(name_id),
  reference_type       TEXT NOT NULL,         -- 'religious text' | 'mythology' | 'historical figure' | 'royalty' | 'saint'
  work                 TEXT,                  -- 'Torah', 'Quran', 'Mahabharata', 'House of Grimaldi'…
  figure               TEXT,
  relationship_to_name TEXT,                  -- 'named in the text' | 'traditional form'
  source_id            TEXT REFERENCES sources(source_id)
);

CREATE TABLE relationships (
  name_id              INTEGER NOT NULL REFERENCES names(name_id),
  related_name_id      INTEGER NOT NULL REFERENCES names(name_id),
  relationship_type    TEXT NOT NULL,         -- spelling_variant | homophone | diminutive | short_form | feminine_form | masculine_form | cognate | romanization_variant
  language             TEXT,
  source_id            TEXT REFERENCES sources(source_id)
);

-- one name, many honest pronunciations; each gets its own lullaby
CREATE TABLE pronunciations (
  pronunciation_id     INTEGER PRIMARY KEY,
  name_id              INTEGER NOT NULL REFERENCES names(name_id),
  language             TEXT,
  phonemes             TEXT NOT NULL,         -- ARPAbet with stress digits: 'M AY1 AH0'
  respelling           TEXT NOT NULL,         -- 'MY-uh'
  syllable_count       INTEGER,
  primary_stress       INTEGER,               -- index of the stressed syllable
  has_diphthong        INTEGER,
  is_primary           INTEGER DEFAULT 0,
  source_id            TEXT REFERENCES sources(source_id),   -- 'cmudict' | 'hand-checked' | 'rules:Spanish' …
  confidence           REAL
);

CREATE TABLE syllables (
  pronunciation_id     INTEGER NOT NULL REFERENCES pronunciations(pronunciation_id),
  syllable_index       INTEGER NOT NULL,
  onset                TEXT,
  nucleus              TEXT NOT NULL,
  coda                 TEXT,
  stress_level         INTEGER,               -- 0 none, 1 primary, 2 secondary
  onset_place          TEXT,                  -- 'lips' | 'lr' | 'tip' | 'back' | 'h' | 'none'
  onset_manner         TEXT                   -- 'soft' (sonorant) | 'warm' (voiced stop) | 'crisp' (voiceless stop) | 'airy' (fricative)
);

-- the generated musical fingerprint, never baked into the name
CREATE TABLE lullabytes (
  pronunciation_id     INTEGER NOT NULL REFERENCES pronunciations(pronunciation_id),
  algorithm_version    TEXT NOT NULL,         -- 'lullabyte-2 · phonetic'
  scale                TEXT NOT NULL,         -- 'C major pentatonic, C5–C7'
  note_sequence        TEXT NOT NULL,         -- 'G5 E6 C5'
  rhythm_sequence      TEXT,                  -- steps per note
  velocity_sequence    TEXT,
  articulation_sequence TEXT,                 -- 'soft warm crisp'
  sound_shape          REAL,                  -- -1 rounded … 1 sharp
  signature_note       TEXT DEFAULT 'C5',
  signature_in_name    INTEGER DEFAULT 0      -- the closing low C is Lullabyte's, not the name's
);

-- where and when: exactly what each agency published, in the spelling it published
CREATE TABLE popularity_observations (
  name_id              INTEGER REFERENCES names(name_id),
  source_spelling      TEXT NOT NULL,         -- what the agency printed (SSA strips hyphens; ONS keeps exact spelling)
  sex_category         TEXT,                  -- 'girl' | 'boy'
  birth_year           INTEGER,               -- or the decade's first year when period = 'decade'
  period               TEXT DEFAULT 'year',   -- 'year' | 'decade' | 'snapshot'
  count                INTEGER,               -- NULL when the source gives ranks only
  rank                 INTEGER,
  geography            TEXT NOT NULL,         -- statistical geography: 'United States', 'Scotland', 'New South Wales'
  is_rounded           INTEGER DEFAULT 0,
  variant_aggregation  TEXT,                  -- NULL = exact spelling; 'phonetic' when spellings that sound alike share one count (Liechtenstein: Matteo / Mateo)
  given_name_position  INTEGER,               -- 1 when only the first given name is counted; NULL when every given name counts or the source doesn't say
  period_start         INTEGER,               -- for multi-year periods (Latvia's "1920" = 1918–1922); never collapsed into one birth year
  period_end           INTEGER,
  source_id            TEXT NOT NULL REFERENCES sources(source_id)
);
CREATE INDEX obs_name ON popularity_observations(name_id);
CREATE INDEX obs_geo_year ON popularity_observations(geography, birth_year, sex_category);
