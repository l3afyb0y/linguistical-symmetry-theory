# Artifact and database schema

## Canonical database

`lexicon.sqlite` is the canonical generated artifact.

### `words`

| Column | Meaning |
|---|---|
| `word_id` | Source lexical-entry identifier |
| `lemma` | Canonical lemma form |
| `normalized_lemma` | Case-folded and whitespace-normalized lookup key |
| `pos` | Part of speech |
| `confidence` | Source confidence where available |

### `word_forms`

Preserves inflected or alternate forms without collapsing them into the lemma.

### `synsets`

Stores source synset identifiers, part of speech, ILI, definition, lexicographer file, lexicalization status, and confidence.

### `senses`

Stores the word-to-synset pairing as its own entity. This prevents the spelling `bank` from being treated as one undifferentiated semantic node.

### `relations`

Stores directed source relations with entity kind, relation name, target, subtype, source lexicon, and confidence. The pipeline does not silently make all relations symmetric. Deduplicated unordered opposition pairs are a derived artifact.

## Full exports

- `words.csv.gz`
- `alphabetical_index.csv.gz`
- `senses.csv.gz`
- `synsets.csv.gz`
- `relations.csv.gz`
- `opposition_pairs.csv.gz`

## Human-readable views

- `metrics.md`
- `conceptual_thesaurus.md`
- `opposition_atlas.html`
- `paper.md`

## Integrity

`MANIFEST.sha256` hashes every generated file. The verifier also runs SQLite’s integrity check, compares database counts to `metrics.json`, counts every compressed CSV row, checks that the paper contains measured values, and refuses unresolved template placeholders.
