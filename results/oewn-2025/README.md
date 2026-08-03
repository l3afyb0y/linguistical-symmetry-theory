# Open English WordNet 2025 results

This directory pins the lightweight, human-readable outputs of the first corpus-scale Linguistical Symmetry Theory build. The complete machine-readable bundle is generated reproducibly by `.github/workflows/build-corpus.yml` and includes the canonical SQLite graph, full compressed tables, searchable opposition atlas, conceptual index, integrity manifest, measured paper, metrics, and provenance record.

## Verified inventory

| Measure | Count |
|---|---:|
| Lexical entries | 135,969 |
| Distinct normalized lemmas | 127,311 |
| Word forms | 140,426 |
| Senses | 185,129 |
| Synsets | 107,519 |
| Typed relation records | 355,064 |

## Headline measurements

- 91,058 distinct lemmas, or **71.52%**, have at least one co-synonym under the operational definition of membership in a multi-lemma synset.
- 6,626 distinct lemmas, or **5.20%**, participate in at least one explicitly encoded sense-level antonym relation.
- The source contains 3,994 unique opposition pairs after reciprocal directions are deduplicated.
- 2,080 opposition pairs, or **52.08%**, have a multi-lemma synonym neighborhood at one or both poles.
- 1,040 opposition pairs, or **26.04%**, have multi-lemma synonym neighborhoods at both poles.
- All 3,994 opposition pairs are encoded reciprocally in OEWN 2025.
- The opposition graph is highly local: 3,838 connected components, with a largest component of four endpoints.

These numbers describe explicit structure in Open English WordNet 2025. They are not estimates of the percentage of ordinary English that is synonymous, antonymous, redundant, geometrically symmetric, or computationally executable.

## Seed-family audit

The originating family survives the corpus-scale source at the relevant senses:

- `inward` ↔ `outward`
- `inside` ↔ `outside`
- `internal` ↔ `external`
- `include` ↔ `exclude`
- `enter` ↔ `exit`

Several spellings participate through multiple distinct senses. That is precisely why the graph uses sense nodes rather than treating each spelling as one semantic object.

## Integrity

The successful build independently verifies:

- SQLite integrity;
- database-to-metrics count agreement;
- compressed-export row counts;
- resolved manuscript placeholders;
- SHA-256 hashes for every generated artifact.

The pinned files in this directory are `metrics.md`, `metrics.json`, `provenance.json`, and `paper.md`.
