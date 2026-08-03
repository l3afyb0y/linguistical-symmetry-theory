# Linguistical Symmetry Theory

**Antonymy supplies semantic axes. Synonymy supplies neighborhoods around their poles. Typed relations preserve the machinery between them.**

This repository contains a reproducible corpus-scale test of that architecture using Open English WordNet 2025. It does not force every English sense into a mirrored cabinet. It measures explicit opposition, synonym neighborhoods, reciprocity, asymmetry, unpaired material, and the limits of the selected source.

## What the build produces

One source graph generates several views:

- a canonical provenance-aware SQLite database;
- full compressed word, sense, synset, relation, and opposition tables;
- a conventional alphabetical sense index;
- an opposition-first conceptual index;
- a searchable static opposition atlas;
- measured corpus statistics;
- a research paper rendered from those actual statistics;
- a cryptographic manifest and automated integrity report.

The source PDFs already in the repository motivate the geometric and fractal questions. They are not treated as proof of the project’s specific lexical hypothesis.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest
python -m linguistical_symmetry.pipeline --lexicon oewn:2025 --output artifacts
python -m linguistical_symmetry.verify artifacts
```

The first corpus build downloads and installs Open English WordNet through `wn`.

## Research rail

The current build can establish how much **explicit** synonym and opposition structure appears in Open English WordNet and how that structure behaves as a graph. It cannot establish that information-theoretic redundancy is synonymy, that every concept has an opposite, that alphabetic recursion preserves semantics, or that unrestricted natural language can be compiled deterministically. Those are different questions and remain separately marked.

## Authorship

Parker Rowen is the project author and bears responsibility for the published work. OpenAI ChatGPT, GPT-5.6 Thinking assisted with computational formalization, implementation, source synthesis, visualization, and manuscript drafting. See `SOURCES.md` for the complete contribution statement.
