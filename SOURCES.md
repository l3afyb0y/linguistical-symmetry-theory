# Sources and provenance

## Computational lexical source

The corpus build uses **Open English WordNet 2025**, core edition, through the Python `wn` library. The core edition deliberately excludes the large proper-name layer introduced through Open English Namenet. Open English WordNet is released under **CC BY 4.0**. Generated artifacts preserve source identifiers rather than replacing them with project-local anonymous IDs.

Canonical resource citation:

> McCrae, John P., Alexandre Rademaker, Francis Bond, Ewa Rudnicka, and Christiane Fellbaum. “English WordNet 2019: An Open-Source WordNet for English.” In *Proceedings of the 10th Global WordNet Conference*, 2019.

The build records the installed lexicon identifier, version, label, URL, license, software version, build time, and repository revision in `provenance.json`.

## Research papers retained in this repository

- Ribeiro, Haroldo V., Alexandre Bernardes, and Fernando de Mello. “On the Fractal Patterns of Language Structures.” *PLOS ONE* 18, no. 5 (2023): e0285630. DOI: 10.1371/journal.pone.0285630. Repository file: `pone.0285630.pdf`.
- Gromov, et al. “A Language and Its Dimensions: Intrinsic Dimensions of Language Fractal Structures.” arXiv:2311.10217v2. Repository file: `2311.10217v2.pdf`.

These papers motivate questions about non-integer geometry and structure in learned or corpus-derived language spaces. They do not, by themselves, prove the project’s specific opposition-first lexical architecture.

## Historical and consulted-copy sources

- Kučera, Henry. “The Mathematics of Language.” In *The American Heritage Dictionary*, edited by William Morris, 2nd college ed., 37–41. Boston: Houghton Mifflin Company, 1991. Consulted copy: thumb-index edition, ISBN 0-395-32944-2. This source supports discussion of finite symbolic inventories, hierarchical combination, frequency asymmetry, and information-theoretic redundancy. It does **not** establish that half of English is synonymous.
- Mawson, C. O. Sylvester, and Peter Mark Roget. *Roget’s International Thesaurus: The Complete Book of Synonyms and Antonyms in American and British Usage*. New ed., rev. and reset. New York: Thomas Y. Crowell Company, 1946. Consulted copy: twelfth printing, June 1956. This is used as a historical design precedent, not ingested as a copyrighted lexical dataset.

## Project contribution statement

**Parker Rowen:** Initial research; philosophical conceptualization and findings; hypothesis formation; methodological direction; source identification; interpretive analysis; authorship and responsibility for publication.

**OpenAI ChatGPT, GPT-5.6 Thinking:** Computational research assistance; mathematical and computational formalization; data engineering; software implementation; visualization; literature synthesis; manuscript drafting and revision assistance.

The AI system is not listed as an author. Parker Rowen remains responsible for the claims, source use, and published form.
