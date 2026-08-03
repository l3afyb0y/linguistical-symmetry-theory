# Methodology

## Research question

The project asks whether explicit semantic opposition can serve as a useful organizing spine for a large English lexical graph, while synonymy supplies neighborhoods around the poles of that spine.

The architecture began with a small family of relations:

- `inward` ↔ `outward`
- `inside` ↔ `outside`
- `internal` ↔ `external`
- `include` ↔ `exclude`
- `enter` ↔ `exit`

The corpus build does not assume that all English senses fit this pattern. It measures where an open lexical source explicitly supports opposition, where synonym neighborhoods surround opposed senses, where the structure is asymmetric, and where no opposition is recorded.

## Units

A **word** is a lexical entry with a lemma, part of speech, and optional forms. A **sense** is a pairing between a word and a synset. A **synset** is a set of senses intended to lexicalize one concept. A **synonym neighborhood** is the set of distinct lemmas sharing a synset. This project avoids turning every synset into a dense pairwise synonym clique in storage; membership in the synset is the canonical representation.

An **explicit opposition edge** is a relation in Open English WordNet whose type is one of:

- `antonym`
- `anto_gradable`
- `anto_simple`
- `anto_converse`

A **unique opposition pair** is an unordered pair of endpoints, preserved separately by entity kind and relation type. Directed source records remain available in `relations.csv.gz` and `lexicon.sqlite`.

## Measurements

The build reports several denominators rather than one theatrical percentage:

1. the share of senses incident to an explicit sense-level opposition;
2. the share of distinct lemmas having at least one directly opposed sense;
3. the share of synsets incident to an explicit synset-level opposition;
4. the share of all typed relation records that are opposition records;
5. the share of senses and lemmas that have at least one co-synonym;
6. the size balance of synonym neighborhoods around directly opposed senses;
7. reciprocity, degree, and connected-component structure in the explicit opposition graph.

Neighborhood-size balance is descriptive. Equal-sized neighborhoods are not thereby semantically isomorphic.

## Claim rail

The build directly measures structures encoded in Open English WordNet. It does not directly measure contextual antonymy, corpus predictability, information-theoretic redundancy, metaphorical opposition, or a universal semantic formula. A missing edge means that the chosen source does not encode the relation, not necessarily that no speaker could recognize it.

The project keeps four layers distinct:

- **source record:** what Open English WordNet explicitly encodes;
- **measurement:** what the pipeline computes from those records;
- **interpretation:** what those measurements suggest about lexical organization;
- **hypothesis:** what later corpus, geometric, or programming-language experiments might test.

## Reproducibility

The GitHub Actions workflow installs a pinned major/minor range of `wn`, downloads `oewn:2025`, builds a normalized SQLite database, exports compressed tables and human-readable views, renders the measured results into the paper, verifies row counts and hashes, and uploads the entire bundle as one workflow artifact.
