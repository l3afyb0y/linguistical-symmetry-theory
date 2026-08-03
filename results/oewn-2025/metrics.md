# Corpus-scale metrics

Built from `oewn:2025` at 2026-08-03T16:51:52+00:00.

## Inventory

| Measure | Count |
|---|---:|
| Lexical entries | 135,969 |
| Distinct normalized lemmas | 127,311 |
| Word forms | 140,426 |
| Senses | 185,129 |
| Synsets | 107,519 |
| Typed relation records | 355,064 |

## Synonym neighborhoods

| Measure | Result |
|---|---:|
| Multi-member synsets | 44,932 (41.79%) |
| Senses with a co-synonym | 122,513 (66.18%) |
| Lemmas with a co-synonym in at least one sense | 91,058 (71.52%) |

## Explicit opposition

| Measure | Result |
|---|---:|
| Directed opposition relation records | 7,988 |
| Unique undirected opposition pairs | 3,994 |
| Senses incident to direct opposition | 7,774 (4.20%) |
| Lemmas incident to direct opposition | 6,626 (5.20%) |
| Reciprocal unique pairs | 3,994 (100.00%) |
| Opposition components | 3,838 |
| Largest opposition component | 4 nodes |

## Synonym neighborhoods around opposed senses

| Measure | Result |
|---|---:|
| Sense-level opposition pairs evaluated | 3,994 |
| One or both poles have co-synonyms | 2,080 (52.08%) |
| Both poles have co-synonyms | 1,040 (26.04%) |
| Equal neighborhood sizes | 2,498 (62.54%) |
| Median size-balance ratio | 1.000 |

## Interpretation rail

These figures measure explicit relations in Open English WordNet. They do not estimate how much English is information-theoretically redundant, and they do not count contextual oppositions absent from the lexical source. Synonymy here means co-membership in a synset. Opposition here means an explicit OEWN relation of type `antonym`, `anto_gradable`, `anto_simple`, or `anto_converse`.
