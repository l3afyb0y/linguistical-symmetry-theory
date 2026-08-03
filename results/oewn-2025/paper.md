# Linguistical Symmetry Theory: An Opposition-First, Provenance-Aware Study of Open English WordNet

**Parker Rowen**

Generated research build: 2026-08-03T16:51:52+00:00  
Source lexicon: `oewn:2025`  
Repository revision: `7d13aaa571c7c2d00c277718b33e2d95e57fc4cc`

## Abstract

This paper tests a bounded version of Linguistical Symmetry Theory: that explicit opposition can provide a useful structural spine for a lexical graph while synonymy supplies neighborhoods around opposed poles. The claim is tested against the core 2025 edition of Open English WordNet, using senses rather than spellings as the principal lexical unit and preserving source provenance throughout the build. The resulting graph contains 135,969 lexical entries, 127,311 distinct normalized lemmas, 140,426 word forms, 185,129 senses, 107,519 synsets, and 355,064 typed relation records. It contains 3,994 unique explicit opposition pairs after deduplicating direction while retaining relation type and endpoint kind. 7,774 senses (4.20%) and 6,626 lemmas (5.20%) participate in at least one direct sense-level opposition. Among sense-level opposition pairs, 1,040 (26.04%) have multi-lemma synonym neighborhoods at both poles. These findings support opposition as a real but limited organizing structure in the selected lexical source. They do not support the stronger claim that most English vocabulary is antonymous, that information-theoretic redundancy is synonymy, or that the measured graph supplies a complete semantics for natural-language programming.

## 1. Problem before system

English dictionaries and thesauri commonly present two different doors into lexical meaning. A dictionary begins with a word form and divides it into senses. A conceptual thesaurus begins with a region of meaning and gathers words beneath it. Linguistical Symmetry Theory proposes that these views need not be separate databases. They can be generated from one provenance-aware sense graph, provided the graph distinguishes spelling, lexical entry, sense, concept, and typed relation.

The initial observation was not that every word possesses an opposite. It was narrower: families such as *inward/outward*, *inside/outside*, *internal/external*, *include/exclude*, and *enter/exit* appear to organize themselves around recurring poles while changing grammatical or semantic mode. In that architecture, antonymy supplies visible axes, synonymy supplies neighborhoods around each pole, and other typed relations explain why corresponding positions are related without pretending they are simple synonyms.

The corpus-scale question is therefore not “Is English perfectly symmetrical?” It is: **How much explicit oppositional structure does a large lexical source contain, how is it distributed, and what happens to synonym neighborhoods around its poles?**

## 2. Categories and claim rail

The analysis distinguishes four authorities.

A **source record** is a relation explicitly encoded by Open English WordNet. A **measurement** is a quantity computed from those records. An **interpretation** is a proposed account of what the measurements reveal about lexical organization. A **hypothesis** extends beyond the present evidence and requires another experiment.

This separation matters because an absent WordNet edge is not proof that speakers cannot recognize an opposition. It means only that the selected source does not encode one. Likewise, a balanced pair of synonym neighborhoods is not proof that the neighborhoods are geometrically or semantically isomorphic.

The paper also rejects one tempting conflation. Information-theoretic **redundancy** concerns predictability, recoverability, and error tolerance in messages. It can arise from grammar, frequency, morphology, syntax, context, and world knowledge. It is not a count of synonymous words. Kučera’s discussion of redundancy in *The American Heritage Dictionary* is valuable to this project because it explains constrained recoverability in linear language, not because it proves that half of English is synonymous.

## 3. Sources and related work

Open English WordNet is an open lexical network in which words are grouped into synsets and linked through conceptual-semantic and lexical relations. The core 2025 edition deliberately separates common nouns, verbs, adjectives, and adverbs from the much larger proper-name resource. This makes it a suitable first corpus for testing sense-level opposition without allowing named entities to dominate the inventory.

Ribeiro, Bernardes, and Mello reported multifractal organization in corpus-derived language structures across seventeen languages. Gromov and colleagues estimated non-integer intrinsic dimensions for language structures built from n-gram embeddings. These results motivate the broader question of whether language representations possess measurable geometry. They do not establish the particular opposition-first graph proposed here. The present analysis operates at the lexical-resource level and asks a different question: whether explicit typed relations reveal recurring oppositional organization and structured neighborhoods.

Roget’s conceptual organization supplies a historical design precedent for generating a thesaurus by meaning rather than spelling. The consulted 1946 new edition, twelfth printing in June 1956, is cited as a model of conceptual presentation rather than digitized as a dataset. Kučera supplies a historical bridge between language, mathematics, finite symbolic inventories, hierarchical combination, frequency distributions, and error-tolerant redundancy.

## 4. Data model and method

The build uses word senses rather than bare word forms as its main lexical unit. A **word** is a lexical entry with a lemma and part of speech. A **sense** pairs that word with a synset. A **synset** groups senses intended to lexicalize one concept. Synonymy is represented canonically by co-membership in a synset rather than by materializing every possible pairwise synonym edge.

An explicit opposition is any source relation named `antonym`, `anto_gradable`, `anto_simple`, or `anto_converse`. Directed source records are preserved. For pair-level analysis, direction is deduplicated while retaining the endpoint kind and relation type. Reciprocity is then measured by asking whether the source encoded both directions.

For each directly opposed sense pair, the analysis measures the number of distinct lemmas in each endpoint’s synset. The balance ratio is the smaller neighborhood divided by the larger. A ratio of 1 means equal size, not equal meaning or internal correspondence.

The generated SQLite database and exports retain source identifiers, definitions, parts of speech, relation subtypes, source lexicon metadata, confidence values when available, the repository revision, and build time. A verifier checks database integrity, table counts, compressed exports, paper rendering, and SHA-256 hashes.

## 5. Results

### 5.1 Lexical inventory

The normalized graph contains 135,969 lexical entries, 127,311 distinct normalized lemmas, 140,426 forms, 185,129 senses, 107,519 synsets, and 355,064 typed relation records. 44,932 synsets contain more than one distinct lemma. 122,513 senses (66.18%) and 91,058 lemmas (71.52%) have at least one co-synonym under the operational definition used here.

These percentages are not estimates of information-theoretic redundancy. They report membership in multi-lemma synsets in one lexical source.

### 5.2 Explicit opposition

The source contains 7,988 directed opposition relation records. After deduplicating direction while preserving endpoint kind and relation type, the graph contains 3,994 unique opposition pairs: 3,994 sense-level pairs and 0 synset-level pairs.

7,774 senses (4.20%) and 6,626 distinct lemmas (5.20%) participate in a direct sense-level opposition. 3,994 unique pairs (100.00%) are encoded in both directions. The undirected opposition graph divides into 3,838 connected components, and its largest component contains 4 endpoints.

The result supports a modest claim: explicit opposition is a genuine, enumerable structure in the lexical graph. Its coverage is not equivalent to “the proportion of English that is antonymous,” because implicit, contextual, productive, and source-omitted oppositions remain outside the measurement.

### 5.3 Synonym neighborhoods around opposition

Among sense-level opposition pairs, 2,080 (52.08%) have a multi-lemma synonym neighborhood at one or both poles. 1,040 (26.04%) have such neighborhoods at both poles. 2,498 pairs (62.54%) have equal neighborhood sizes, and the median size-balance ratio is 1.000.

This is the first corpus-scale pressure test of the project’s central architecture. Opposition can connect poles whose surrounding synonym neighborhoods vary substantially in size. Symmetry therefore cannot responsibly mean simple mirror identity. A more defensible interpretation is **typed relational symmetry with permitted lexical asymmetry**. The axis may be stable while the vocabulary accumulated around each pole is uneven.

## 6. What survived correction

The strongest surviving claim is architectural:

> A single provenance-aware sense graph can generate both a conventional alphabetical lexical index and an opposition-first conceptual thesaurus while preserving ambiguity, source relations, asymmetry, and unpaired senses.

A second claim receives bounded empirical support:

> Explicit semantic opposition forms a recurring and measurable substructure in Open English WordNet, and many opposed senses sit inside nontrivial synonym neighborhoods.

The analysis does not establish that opposition is the dominant structure of English, that every semantic region has an inverse, or that all relation families instantiate one universal transformation. Those stronger possibilities become testable research questions rather than conclusions smuggled into the grammar.

## 7. Limitations

Open English WordNet is a curated lexical resource, not a complete record of language use. Its sense inventory, relation coverage, granularity, and editorial history shape every reported percentage. Context-dependent antonymy and newly productive forms may be absent. Multiword expressions are included unevenly. Synset co-membership is a useful operationalization of synonym neighborhood, but ordinary speakers may judge some members as near-synonyms rather than interchangeable expressions.

The balance analysis measures neighborhood size only. A stronger symmetry test would align internal relations across opposed neighborhoods and determine whether corresponding positions recur across grammatical modes. Corpus evidence could then test whether the source graph’s oppositions are reflected in actual co-occurrence geometry.

The two retained geometry papers operate on embeddings and n-gram structures rather than this sense graph. Their findings cannot be imported as proof that the present graph is fractal. Any future fractal or intrinsic-dimension claim must be computed directly on a defined representation of these artifacts.

## 8. Programming-language implications

The graph may become one component of a controlled-natural-language system. It can provide sense identifiers, lexical normalization, type constraints, and explicit relation records. It is not itself a compiler. Deterministic execution additionally requires a restricted grammar, parser, typed intermediate representation, operational semantics, ambiguity rejection, code generation, and tests.

The presently defensible programming claim is narrow:

> A typed subset of natural English may be normalized through a provenance-aware sense graph into deterministic executable operations.

Whether that succeeds belongs to a later prototype. Encoding text into binary is already routine; compiling unrestricted English meaning into operations is the difficult and separate problem.

## 9. Conclusion

The corpus-scale build does not reveal a perfectly mirrored language. It reveals something more useful: a large lexical system in which explicit opposition is real, synonym neighborhoods frequently gather around its poles, and asymmetry remains visible rather than being ironed out for elegance. The architecture works in principle because it can preserve both the relation and the failure of the relation to dominate everything.

The next research step is not to declare a universal formula. It is to inspect higher-order motifs: whether opposed pairs recur across location, direction, state, process, role, and reversal; whether their neighborhoods contain alignable internal relations; and whether corpus-derived geometry supports or resists the source-level structure. The mechanism is now something responsibility can hold.

## Contribution and AI disclosure

**Parker Rowen:** Initial research; philosophical conceptualization and findings; hypothesis formation; methodological direction; source identification; interpretive analysis; authorship and responsibility for publication.

**OpenAI ChatGPT, GPT-5.6 Thinking:** Computational research assistance; mathematical and computational formalization; data engineering; software implementation; visualization; literature synthesis; manuscript drafting and revision assistance.

The AI system is not an author. Parker Rowen remains responsible for the claims, citations, source use, and published form.

## References

Gromov, et al. “A Language and Its Dimensions: Intrinsic Dimensions of Language Fractal Structures.” arXiv:2311.10217v2.

Kučera, Henry. “The Mathematics of Language.” In *The American Heritage Dictionary*, edited by William Morris, 2nd college ed., 37–41. Boston: Houghton Mifflin Company, 1991. Consulted thumb-index edition, ISBN 0-395-32944-2.

Mawson, C. O. Sylvester, and Peter Mark Roget. *Roget’s International Thesaurus: The Complete Book of Synonyms and Antonyms in American and British Usage*. New ed., rev. and reset. New York: Thomas Y. Crowell Company, 1946. Consulted copy: twelfth printing, June 1956.

McCrae, John P., Alexandre Rademaker, Francis Bond, Ewa Rudnicka, and Christiane Fellbaum. “English WordNet 2019: An Open-Source WordNet for English.” In *Proceedings of the 10th Global WordNet Conference*, 2019.

Ribeiro, Haroldo V., Alexandre Bernardes, and Fernando de Mello. “On the Fractal Patterns of Language Structures.” *PLOS ONE* 18, no. 5 (2023): e0285630. https://doi.org/10.1371/journal.pone.0285630.
