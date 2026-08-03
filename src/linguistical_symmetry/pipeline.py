from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import html
import json
import math
import os
import shutil
import sqlite3
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    import wn

OPPOSITION_RELATIONS = frozenset({
    "antonym",
    "anto_gradable",
    "anto_simple",
    "anto_converse",
})

SCHEMA_VERSION = "0.3.0"
PROJECT_NAME = "Linguistical Symmetry Theory"
DEFAULT_LEXICON = "oewn:2025"


class BuildError(RuntimeError):
    pass


@dataclass(frozen=True)
class PairRecord:
    source_kind: str
    relation: str
    source_id: str
    target_id: str
    source_label: str
    target_label: str
    source_pos: str
    target_pos: str
    source_definition: str
    target_definition: str
    source_neighborhood_size: int
    target_neighborhood_size: int
    neighborhood_balance: float
    reciprocal: bool


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}
        self.rank: dict[str, int] = {}

    def add(self, item: str) -> None:
        if item not in self.parent:
            self.parent[item] = item
            self.rank[item] = 0

    def find(self, item: str) -> str:
        self.add(item)
        parent = self.parent[item]
        if parent != item:
            self.parent[item] = self.find(parent)
        return self.parent[item]

    def union(self, left: str, right: str) -> None:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left == root_right:
            return
        rank_left = self.rank[root_left]
        rank_right = self.rank[root_right]
        if rank_left < rank_right:
            root_left, root_right = root_right, root_left
        self.parent[root_right] = root_left
        if rank_left == rank_right:
            self.rank[root_left] += 1

    def component_sizes(self) -> list[int]:
        counts: Counter[str] = Counter(self.find(item) for item in self.parent)
        return sorted(counts.values(), reverse=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalized_text(value: str) -> str:
    return " ".join(value.casefold().split())


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def ratio(numerator: int | float, denominator: int | float) -> float:
    return 0.0 if not denominator else float(numerator) / float(denominator)


def percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def median(values: Sequence[float | int]) -> float:
    return float(statistics.median(values)) if values else 0.0


def percentile(values: Sequence[int | float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(float(v) for v in values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * p
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def get_wn_module():
    import wn
    return wn


def ensure_lexicon(spec: str) -> "wn.Wordnet":
    wn_module = get_wn_module()
    try:
        wordnet = wn_module.Wordnet(spec)
        if wordnet.lexicons():
            return wordnet
    except Exception:
        pass
    print(f"Downloading and adding {spec}...", flush=True)
    wn_module.download(spec)
    wordnet = wn_module.Wordnet(spec)
    if not wordnet.lexicons():
        raise BuildError(f"The lexicon {spec!r} was not available after download.")
    return wordnet


def initialize_database(path: Path) -> sqlite3.Connection:
    if path.exists():
        path.unlink()
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=NORMAL")
    connection.executescript(
        """
        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE words (
            word_id TEXT PRIMARY KEY,
            lemma TEXT NOT NULL,
            normalized_lemma TEXT NOT NULL,
            pos TEXT NOT NULL,
            confidence REAL
        );
        CREATE TABLE word_forms (
            word_id TEXT NOT NULL,
            form TEXT NOT NULL,
            normalized_form TEXT NOT NULL,
            is_lemma INTEGER NOT NULL CHECK (is_lemma IN (0, 1)),
            PRIMARY KEY (word_id, form)
        );
        CREATE TABLE synsets (
            synset_id TEXT PRIMARY KEY,
            pos TEXT NOT NULL,
            ili TEXT,
            definition TEXT,
            lexfile TEXT,
            lexicalized INTEGER NOT NULL CHECK (lexicalized IN (0, 1)),
            confidence REAL
        );
        CREATE TABLE senses (
            sense_id TEXT PRIMARY KEY,
            word_id TEXT NOT NULL,
            synset_id TEXT NOT NULL,
            lemma TEXT NOT NULL,
            normalized_lemma TEXT NOT NULL,
            pos TEXT NOT NULL,
            confidence REAL
        );
        CREATE TABLE relations (
            relation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_kind TEXT NOT NULL CHECK (source_kind IN ('sense', 'synset')),
            source_id TEXT NOT NULL,
            relation TEXT NOT NULL,
            target_kind TEXT NOT NULL CHECK (target_kind IN ('sense', 'synset')),
            target_id TEXT NOT NULL,
            subtype TEXT,
            source_lexicon TEXT,
            confidence REAL,
            UNIQUE (source_kind, source_id, relation, target_kind, target_id, subtype)
        );
        CREATE INDEX idx_words_lemma ON words(normalized_lemma, pos);
        CREATE INDEX idx_forms_form ON word_forms(normalized_form);
        CREATE INDEX idx_senses_word ON senses(word_id);
        CREATE INDEX idx_senses_synset ON senses(synset_id);
        CREATE INDEX idx_relations_source ON relations(source_kind, source_id);
        CREATE INDEX idx_relations_target ON relations(target_kind, target_id);
        CREATE INDEX idx_relations_type ON relations(relation);
        """
    )
    return connection


def confidence_of(item: Any) -> float | None:
    try:
        value = item.confidence()
        return None if value is None else float(value)
    except Exception:
        return None


def lexicon_id_of_relation(relation: Any) -> str:
    try:
        lexicon = relation.lexicon()
        version = getattr(lexicon, "version", None)
        return f"{lexicon.id}:{version}" if version else safe_text(lexicon.id)
    except Exception:
        return ""


def insert_relation_map(
    connection: sqlite3.Connection,
    source_kind: str,
    source_id: str,
    relation_map: Mapping[Any, Any],
) -> int:
    rows: list[tuple[Any, ...]] = []
    for relation, target in relation_map.items():
        name = safe_text(getattr(relation, "name", ""))
        if not name:
            continue
        target_id = safe_text(getattr(target, "id", ""))
        if not target_id:
            continue
        rows.append(
            (
                source_kind,
                source_id,
                name,
                source_kind,
                target_id,
                safe_text(getattr(relation, "subtype", "")) or None,
                lexicon_id_of_relation(relation),
                confidence_of(relation),
            )
        )
    if rows:
        connection.executemany(
            """
            INSERT OR IGNORE INTO relations(
                source_kind, source_id, relation, target_kind, target_id,
                subtype, source_lexicon, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
    return len(rows)


def ingest_wordnet(connection: sqlite3.Connection, wordnet: "wn.Wordnet") -> dict[str, int]:
    counts = {"words": 0, "forms": 0, "synsets": 0, "senses": 0, "relations": 0}

    print("Ingesting lexical entries and forms...", flush=True)
    word_rows: list[tuple[Any, ...]] = []
    form_rows: list[tuple[Any, ...]] = []
    for index, word in enumerate(wordnet.words(), start=1):
        lemma = safe_text(word.lemma())
        word_rows.append(
            (word.id, lemma, normalized_text(lemma), safe_text(word.pos), confidence_of(word))
        )
        forms = list(dict.fromkeys(safe_text(form) for form in word.forms()))
        if lemma and lemma not in forms:
            forms.insert(0, lemma)
        for form in forms:
            form_rows.append((word.id, form, normalized_text(form), int(form == lemma)))
        if len(word_rows) >= 5000:
            connection.executemany(
                "INSERT INTO words(word_id, lemma, normalized_lemma, pos, confidence) VALUES (?, ?, ?, ?, ?)",
                word_rows,
            )
            connection.executemany(
                "INSERT OR IGNORE INTO word_forms(word_id, form, normalized_form, is_lemma) VALUES (?, ?, ?, ?)",
                form_rows,
            )
            counts["words"] += len(word_rows)
            counts["forms"] += len(form_rows)
            word_rows.clear()
            form_rows.clear()
        if index % 25000 == 0:
            print(f"  words: {index:,}", flush=True)
    if word_rows:
        connection.executemany(
            "INSERT INTO words(word_id, lemma, normalized_lemma, pos, confidence) VALUES (?, ?, ?, ?, ?)",
            word_rows,
        )
        connection.executemany(
            "INSERT OR IGNORE INTO word_forms(word_id, form, normalized_form, is_lemma) VALUES (?, ?, ?, ?)",
            form_rows,
        )
        counts["words"] += len(word_rows)
        counts["forms"] += len(form_rows)
    connection.commit()

    print("Ingesting synsets, senses, and typed relations...", flush=True)
    synset_rows: list[tuple[Any, ...]] = []
    sense_rows: list[tuple[Any, ...]] = []
    for index, synset in enumerate(wordnet.synsets(), start=1):
        definition = safe_text(synset.definition())
        ili = safe_text(synset.ili) if getattr(synset, "ili", None) else ""
        try:
            lexicalized = int(bool(synset.lexicalized()))
        except Exception:
            lexicalized = 1
        try:
            lexfile = safe_text(synset.lexfile())
        except Exception:
            lexfile = ""
        synset_rows.append(
            (
                synset.id,
                safe_text(synset.pos),
                ili or None,
                definition or None,
                lexfile or None,
                lexicalized,
                confidence_of(synset),
            )
        )

        senses = synset.senses()
        for sense in senses:
            word = sense.word()
            lemma = safe_text(word.lemma())
            sense_rows.append(
                (
                    sense.id,
                    word.id,
                    synset.id,
                    lemma,
                    normalized_text(lemma),
                    safe_text(word.pos),
                    confidence_of(sense),
                )
            )
            counts["relations"] += insert_relation_map(
                connection, "sense", sense.id, sense.relation_map()
            )

        counts["relations"] += insert_relation_map(
            connection, "synset", synset.id, synset.relation_map()
        )

        if len(synset_rows) >= 2000:
            connection.executemany(
                """
                INSERT INTO synsets(
                    synset_id, pos, ili, definition, lexfile, lexicalized, confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                synset_rows,
            )
            connection.executemany(
                """
                INSERT INTO senses(
                    sense_id, word_id, synset_id, lemma, normalized_lemma, pos, confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                sense_rows,
            )
            counts["synsets"] += len(synset_rows)
            counts["senses"] += len(sense_rows)
            synset_rows.clear()
            sense_rows.clear()
            connection.commit()
        if index % 10000 == 0:
            print(f"  synsets: {index:,}", flush=True)
    if synset_rows:
        connection.executemany(
            """
            INSERT INTO synsets(
                synset_id, pos, ili, definition, lexfile, lexicalized, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            synset_rows,
        )
        connection.executemany(
            """
            INSERT INTO senses(
                sense_id, word_id, synset_id, lemma, normalized_lemma, pos, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            sense_rows,
        )
        counts["synsets"] += len(synset_rows)
        counts["senses"] += len(sense_rows)
    connection.commit()
    return counts


def fetch_scalar(connection: sqlite3.Connection, sql: str, params: Sequence[Any] = ()) -> int:
    row = connection.execute(sql, params).fetchone()
    return int(row[0] or 0)


def relation_counts(connection: sqlite3.Connection, source_kind: str) -> dict[str, int]:
    return {
        relation: int(count)
        for relation, count in connection.execute(
            """
            SELECT relation, COUNT(*)
            FROM relations
            WHERE source_kind = ?
            GROUP BY relation
            ORDER BY COUNT(*) DESC, relation
            """,
            (source_kind,),
        )
    }


def deduplicated_opposition_rows(connection: sqlite3.Connection) -> list[tuple[str, str, str, str]]:
    placeholders = ",".join("?" for _ in OPPOSITION_RELATIONS)
    rows = connection.execute(
        f"""
        SELECT source_kind, source_id, relation, target_id
        FROM relations
        WHERE source_kind = target_kind
          AND relation IN ({placeholders})
        ORDER BY source_kind, relation, source_id, target_id
        """,
        tuple(sorted(OPPOSITION_RELATIONS)),
    ).fetchall()
    unique: dict[tuple[str, str, str, str], tuple[str, str, str, str]] = {}
    for kind, source, relation, target in rows:
        left, right = sorted((source, target))
        key = (kind, relation, left, right)
        unique[key] = (kind, relation, left, right)
    return list(unique.values())


def pair_details(connection: sqlite3.Connection) -> list[PairRecord]:
    directed = {
        (kind, relation, source, target)
        for kind, relation, source, target in connection.execute(
            """
            SELECT source_kind, relation, source_id, target_id
            FROM relations
            WHERE source_kind = target_kind
              AND relation IN ('antonym', 'anto_gradable', 'anto_simple', 'anto_converse')
            """
        )
    }
    records: list[PairRecord] = []
    for kind, relation, source_id, target_id in deduplicated_opposition_rows(connection):
        reciprocal = (kind, relation, target_id, source_id) in directed and (
            kind,
            relation,
            source_id,
            target_id,
        ) in directed
        if kind == "sense":
            row = connection.execute(
                """
                SELECT
                    s1.lemma, s2.lemma, s1.pos, s2.pos,
                    COALESCE(y1.definition, ''), COALESCE(y2.definition, ''),
                    (SELECT COUNT(DISTINCT lemma) FROM senses WHERE synset_id = s1.synset_id),
                    (SELECT COUNT(DISTINCT lemma) FROM senses WHERE synset_id = s2.synset_id)
                FROM senses s1
                JOIN senses s2 ON s2.sense_id = ?
                JOIN synsets y1 ON y1.synset_id = s1.synset_id
                JOIN synsets y2 ON y2.synset_id = s2.synset_id
                WHERE s1.sense_id = ?
                """,
                (target_id, source_id),
            ).fetchone()
        else:
            row = connection.execute(
                """
                SELECT
                    COALESCE((SELECT GROUP_CONCAT(lemma, ' · ') FROM (
                        SELECT DISTINCT lemma FROM senses WHERE synset_id = y1.synset_id ORDER BY lemma
                    )), y1.synset_id),
                    COALESCE((SELECT GROUP_CONCAT(lemma, ' · ') FROM (
                        SELECT DISTINCT lemma FROM senses WHERE synset_id = y2.synset_id ORDER BY lemma
                    )), y2.synset_id),
                    y1.pos, y2.pos,
                    COALESCE(y1.definition, ''), COALESCE(y2.definition, ''),
                    (SELECT COUNT(DISTINCT lemma) FROM senses WHERE synset_id = y1.synset_id),
                    (SELECT COUNT(DISTINCT lemma) FROM senses WHERE synset_id = y2.synset_id)
                FROM synsets y1
                JOIN synsets y2 ON y2.synset_id = ?
                WHERE y1.synset_id = ?
                """,
                (target_id, source_id),
            ).fetchone()
        if row is None:
            continue
        left_size = int(row[6] or 0)
        right_size = int(row[7] or 0)
        balance = ratio(min(left_size, right_size), max(left_size, right_size))
        records.append(
            PairRecord(
                source_kind=kind,
                relation=relation,
                source_id=source_id,
                target_id=target_id,
                source_label=safe_text(row[0]),
                target_label=safe_text(row[1]),
                source_pos=safe_text(row[2]),
                target_pos=safe_text(row[3]),
                source_definition=safe_text(row[4]),
                target_definition=safe_text(row[5]),
                source_neighborhood_size=left_size,
                target_neighborhood_size=right_size,
                neighborhood_balance=balance,
                reciprocal=reciprocal,
            )
        )
    return records


def build_metrics(
    connection: sqlite3.Connection,
    lexicon_spec: str,
    lexicon_description: str,
    revision: str,
) -> tuple[dict[str, Any], list[PairRecord]]:
    pairs = pair_details(connection)
    opposition_relations_directed = fetch_scalar(
        connection,
        """
        SELECT COUNT(*) FROM relations
        WHERE relation IN ('antonym', 'anto_gradable', 'anto_simple', 'anto_converse')
        """,
    )
    sense_opposition_directed = fetch_scalar(
        connection,
        """
        SELECT COUNT(*) FROM relations
        WHERE source_kind='sense' AND target_kind='sense'
          AND relation IN ('antonym', 'anto_gradable', 'anto_simple', 'anto_converse')
        """,
    )
    synset_opposition_directed = opposition_relations_directed - sense_opposition_directed

    total_words = fetch_scalar(connection, "SELECT COUNT(*) FROM words")
    total_lemmas = fetch_scalar(connection, "SELECT COUNT(DISTINCT normalized_lemma) FROM words")
    total_forms = fetch_scalar(connection, "SELECT COUNT(*) FROM word_forms")
    total_senses = fetch_scalar(connection, "SELECT COUNT(*) FROM senses")
    total_synsets = fetch_scalar(connection, "SELECT COUNT(*) FROM synsets")
    total_relations = fetch_scalar(connection, "SELECT COUNT(*) FROM relations")

    multi_member_synsets = fetch_scalar(
        connection,
        """
        SELECT COUNT(*) FROM (
            SELECT synset_id FROM senses GROUP BY synset_id HAVING COUNT(DISTINCT normalized_lemma) > 1
        )
        """,
    )
    senses_with_synonym_neighbor = fetch_scalar(
        connection,
        """
        SELECT COUNT(*) FROM senses
        WHERE synset_id IN (
            SELECT synset_id FROM senses GROUP BY synset_id HAVING COUNT(DISTINCT normalized_lemma) > 1
        )
        """,
    )
    lemmas_with_synonym_neighbor = fetch_scalar(
        connection,
        """
        SELECT COUNT(DISTINCT normalized_lemma) FROM senses
        WHERE synset_id IN (
            SELECT synset_id FROM senses GROUP BY synset_id HAVING COUNT(DISTINCT normalized_lemma) > 1
        )
        """,
    )

    senses_with_direct_opposition = fetch_scalar(
        connection,
        """
        SELECT COUNT(DISTINCT endpoint) FROM (
            SELECT source_id AS endpoint FROM relations
            WHERE source_kind='sense' AND relation IN ('antonym','anto_gradable','anto_simple','anto_converse')
            UNION
            SELECT target_id AS endpoint FROM relations
            WHERE target_kind='sense' AND relation IN ('antonym','anto_gradable','anto_simple','anto_converse')
        )
        """,
    )
    lemmas_with_direct_opposition = fetch_scalar(
        connection,
        """
        SELECT COUNT(DISTINCT normalized_lemma) FROM senses
        WHERE sense_id IN (
            SELECT source_id FROM relations
            WHERE source_kind='sense' AND relation IN ('antonym','anto_gradable','anto_simple','anto_converse')
            UNION
            SELECT target_id FROM relations
            WHERE target_kind='sense' AND relation IN ('antonym','anto_gradable','anto_simple','anto_converse')
        )
        """,
    )
    synsets_with_direct_opposition = fetch_scalar(
        connection,
        """
        SELECT COUNT(DISTINCT endpoint) FROM (
            SELECT source_id AS endpoint FROM relations
            WHERE source_kind='synset' AND relation IN ('antonym','anto_gradable','anto_simple','anto_converse')
            UNION
            SELECT target_id AS endpoint FROM relations
            WHERE target_kind='synset' AND relation IN ('antonym','anto_gradable','anto_simple','anto_converse')
        )
        """,
    )

    pair_type_counts = Counter((pair.source_kind, pair.relation) for pair in pairs)
    sense_pairs = [pair for pair in pairs if pair.source_kind == "sense"]
    balance_values = [pair.neighborhood_balance for pair in sense_pairs]
    both_multi = sum(
        1
        for pair in sense_pairs
        if pair.source_neighborhood_size > 1 and pair.target_neighborhood_size > 1
    )
    one_or_both_multi = sum(
        1
        for pair in sense_pairs
        if pair.source_neighborhood_size > 1 or pair.target_neighborhood_size > 1
    )
    equal_neighborhood_sizes = sum(
        1
        for pair in sense_pairs
        if pair.source_neighborhood_size == pair.target_neighborhood_size
    )
    reciprocal_pairs = sum(1 for pair in pairs if pair.reciprocal)

    union_find = UnionFind()
    for pair in pairs:
        union_find.union(f"{pair.source_kind}:{pair.source_id}", f"{pair.source_kind}:{pair.target_id}")
    component_sizes = union_find.component_sizes()

    degree: Counter[str] = Counter()
    for pair in pairs:
        degree[f"{pair.source_kind}:{pair.source_id}"] += 1
        degree[f"{pair.source_kind}:{pair.target_id}"] += 1
    degree_values = list(degree.values())

    pos_counts = {
        pos: int(count)
        for pos, count in connection.execute(
            "SELECT pos, COUNT(*) FROM senses GROUP BY pos ORDER BY pos"
        )
    }

    metrics: dict[str, Any] = {
        "project": PROJECT_NAME,
        "schema_version": SCHEMA_VERSION,
        "built_at_utc": utc_now(),
        "source_revision": revision,
        "lexicon_spec": lexicon_spec,
        "lexicon_description": lexicon_description,
        "counts": {
            "words": total_words,
            "distinct_normalized_lemmas": total_lemmas,
            "word_forms": total_forms,
            "senses": total_senses,
            "synsets": total_synsets,
            "relations": total_relations,
            "sense_relations": sum(relation_counts(connection, "sense").values()),
            "synset_relations": sum(relation_counts(connection, "synset").values()),
            "multi_member_synsets": multi_member_synsets,
            "senses_with_synonym_neighbor": senses_with_synonym_neighbor,
            "lemmas_with_synonym_neighbor": lemmas_with_synonym_neighbor,
        },
        "coverage": {
            "share_synsets_multi_member": ratio(multi_member_synsets, total_synsets),
            "share_senses_with_synonym_neighbor": ratio(senses_with_synonym_neighbor, total_senses),
            "share_lemmas_with_synonym_neighbor": ratio(lemmas_with_synonym_neighbor, total_lemmas),
            "share_senses_with_direct_opposition": ratio(senses_with_direct_opposition, total_senses),
            "share_lemmas_with_direct_opposition": ratio(lemmas_with_direct_opposition, total_lemmas),
            "share_synsets_with_direct_opposition": ratio(synsets_with_direct_opposition, total_synsets),
            "share_relations_that_are_opposition": ratio(opposition_relations_directed, total_relations),
        },
        "opposition": {
            "directed_relation_records": opposition_relations_directed,
            "directed_sense_relation_records": sense_opposition_directed,
            "directed_synset_relation_records": synset_opposition_directed,
            "unique_undirected_pairs": len(pairs),
            "unique_sense_pairs": len(sense_pairs),
            "unique_synset_pairs": len(pairs) - len(sense_pairs),
            "incident_senses": senses_with_direct_opposition,
            "incident_lemmas": lemmas_with_direct_opposition,
            "incident_synsets": synsets_with_direct_opposition,
            "reciprocal_unique_pairs": reciprocal_pairs,
            "reciprocal_pair_rate": ratio(reciprocal_pairs, len(pairs)),
            "pair_type_counts": {
                f"{kind}:{relation}": count
                for (kind, relation), count in sorted(pair_type_counts.items())
            },
            "connected_components": len(component_sizes),
            "largest_component_size": component_sizes[0] if component_sizes else 0,
            "component_size_p95": percentile(component_sizes, 0.95),
            "opposition_degree_median": median(degree_values),
            "opposition_degree_p95": percentile(degree_values, 0.95),
            "opposition_degree_max": max(degree_values, default=0),
        },
        "synonym_neighborhoods_around_sense_oppositions": {
            "pairs_evaluated": len(sense_pairs),
            "one_or_both_poles_multi_lemma": one_or_both_multi,
            "both_poles_multi_lemma": both_multi,
            "equal_neighborhood_size_pairs": equal_neighborhood_sizes,
            "share_one_or_both_poles_multi_lemma": ratio(one_or_both_multi, len(sense_pairs)),
            "share_both_poles_multi_lemma": ratio(both_multi, len(sense_pairs)),
            "share_equal_neighborhood_sizes": ratio(equal_neighborhood_sizes, len(sense_pairs)),
            "median_balance_ratio": median(balance_values),
            "balance_ratio_p25": percentile(balance_values, 0.25),
            "balance_ratio_p75": percentile(balance_values, 0.75),
        },
        "relations_by_type": {
            "sense": relation_counts(connection, "sense"),
            "synset": relation_counts(connection, "synset"),
        },
        "senses_by_part_of_speech": pos_counts,
        "claim_rail": {
            "directly_measured": [
                "explicit OEWN opposition relations",
                "synset co-membership as synonym-neighborhood structure",
                "coverage, reciprocity, degree, components, and neighborhood-size balance",
            ],
            "not_measured": [
                "information-theoretic redundancy",
                "contextual or implicit antonymy absent from OEWN",
                "whether semantic neighborhoods are geometrically isomorphic",
                "whether a recursive serialization preserves useful semantic locality",
                "whether unrestricted natural English can compile deterministically",
            ],
        },
    }
    return metrics, pairs


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_metrics_markdown(path: Path, metrics: Mapping[str, Any]) -> None:
    counts = metrics["counts"]
    coverage = metrics["coverage"]
    opposition = metrics["opposition"]
    neighborhoods = metrics["synonym_neighborhoods_around_sense_oppositions"]
    content = f"""# Corpus-scale metrics

Built from `{metrics['lexicon_spec']}` at {metrics['built_at_utc']}.

## Inventory

| Measure | Count |
|---|---:|
| Lexical entries | {counts['words']:,} |
| Distinct normalized lemmas | {counts['distinct_normalized_lemmas']:,} |
| Word forms | {counts['word_forms']:,} |
| Senses | {counts['senses']:,} |
| Synsets | {counts['synsets']:,} |
| Typed relation records | {counts['relations']:,} |

## Synonym neighborhoods

| Measure | Result |
|---|---:|
| Multi-member synsets | {counts['multi_member_synsets']:,} ({percent(coverage['share_synsets_multi_member'])}) |
| Senses with a co-synonym | {counts['senses_with_synonym_neighbor']:,} ({percent(coverage['share_senses_with_synonym_neighbor'])}) |
| Lemmas with a co-synonym in at least one sense | {counts['lemmas_with_synonym_neighbor']:,} ({percent(coverage['share_lemmas_with_synonym_neighbor'])}) |

## Explicit opposition

| Measure | Result |
|---|---:|
| Directed opposition relation records | {opposition['directed_relation_records']:,} |
| Unique undirected opposition pairs | {opposition['unique_undirected_pairs']:,} |
| Senses incident to direct opposition | {opposition['incident_senses']:,} ({percent(coverage['share_senses_with_direct_opposition'])}) |
| Lemmas incident to direct opposition | {opposition['incident_lemmas']:,} ({percent(coverage['share_lemmas_with_direct_opposition'])}) |
| Reciprocal unique pairs | {opposition['reciprocal_unique_pairs']:,} ({percent(opposition['reciprocal_pair_rate'])}) |
| Opposition components | {opposition['connected_components']:,} |
| Largest opposition component | {opposition['largest_component_size']:,} nodes |

## Synonym neighborhoods around opposed senses

| Measure | Result |
|---|---:|
| Sense-level opposition pairs evaluated | {neighborhoods['pairs_evaluated']:,} |
| One or both poles have co-synonyms | {neighborhoods['one_or_both_poles_multi_lemma']:,} ({percent(neighborhoods['share_one_or_both_poles_multi_lemma'])}) |
| Both poles have co-synonyms | {neighborhoods['both_poles_multi_lemma']:,} ({percent(neighborhoods['share_both_poles_multi_lemma'])}) |
| Equal neighborhood sizes | {neighborhoods['equal_neighborhood_size_pairs']:,} ({percent(neighborhoods['share_equal_neighborhood_sizes'])}) |
| Median size-balance ratio | {neighborhoods['median_balance_ratio']:.3f} |

## Interpretation rail

These figures measure explicit relations in Open English WordNet. They do not estimate how much English is information-theoretically redundant, and they do not count contextual oppositions absent from the lexical source. Synonymy here means co-membership in a synset. Opposition here means an explicit OEWN relation of type `antonym`, `anto_gradable`, `anto_simple`, or `anto_converse`.
"""
    path.write_text(content, encoding="utf-8")


def export_query_gzip(
    connection: sqlite3.Connection,
    path: Path,
    sql: str,
    headers: Sequence[str],
    params: Sequence[Any] = (),
) -> None:
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        cursor = connection.execute(sql, params)
        for row in cursor:
            writer.writerow(row)


def export_tables(connection: sqlite3.Connection, output: Path, pairs: Sequence[PairRecord]) -> None:
    export_query_gzip(
        connection,
        output / "words.csv.gz",
        """
        SELECT word_id, lemma, pos, confidence
        FROM words ORDER BY normalized_lemma, pos, word_id
        """,
        ["word_id", "lemma", "pos", "confidence"],
    )
    export_query_gzip(
        connection,
        output / "alphabetical_index.csv.gz",
        """
        SELECT w.lemma, w.pos, s.sense_id, s.synset_id, COALESCE(y.definition, ''), y.ili
        FROM words w
        JOIN senses s ON s.word_id = w.word_id
        JOIN synsets y ON y.synset_id = s.synset_id
        ORDER BY w.normalized_lemma, w.pos, s.sense_id
        """,
        ["lemma", "pos", "sense_id", "synset_id", "definition", "ili"],
    )
    export_query_gzip(
        connection,
        output / "senses.csv.gz",
        """
        SELECT sense_id, word_id, synset_id, lemma, pos, confidence
        FROM senses ORDER BY sense_id
        """,
        ["sense_id", "word_id", "synset_id", "lemma", "pos", "confidence"],
    )
    export_query_gzip(
        connection,
        output / "synsets.csv.gz",
        """
        SELECT synset_id, pos, ili, COALESCE(definition, ''), COALESCE(lexfile, ''), lexicalized, confidence
        FROM synsets ORDER BY synset_id
        """,
        ["synset_id", "pos", "ili", "definition", "lexfile", "lexicalized", "confidence"],
    )
    export_query_gzip(
        connection,
        output / "relations.csv.gz",
        """
        SELECT source_kind, source_id, relation, target_kind, target_id,
               COALESCE(subtype, ''), COALESCE(source_lexicon, ''), confidence
        FROM relations
        ORDER BY source_kind, source_id, relation, target_id
        """,
        [
            "source_kind",
            "source_id",
            "relation",
            "target_kind",
            "target_id",
            "subtype",
            "source_lexicon",
            "confidence",
        ],
    )
    with gzip.open(output / "opposition_pairs.csv.gz", "wt", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(PairRecord.__dataclass_fields__.keys())
        for pair in sorted(
            pairs,
            key=lambda item: (
                normalized_text(item.source_label),
                normalized_text(item.target_label),
                item.relation,
            ),
        ):
            writer.writerow(
                [
                    pair.source_kind,
                    pair.relation,
                    pair.source_id,
                    pair.target_id,
                    pair.source_label,
                    pair.target_label,
                    pair.source_pos,
                    pair.target_pos,
                    pair.source_definition,
                    pair.target_definition,
                    pair.source_neighborhood_size,
                    pair.target_neighborhood_size,
                    f"{pair.neighborhood_balance:.6f}",
                    int(pair.reciprocal),
                ]
            )


def clipped(value: str, length: int = 180) -> str:
    value = " ".join(value.split())
    return value if len(value) <= length else value[: length - 1] + "…"


def write_conceptual_thesaurus(path: Path, pairs: Sequence[PairRecord]) -> None:
    grouped: dict[tuple[str, str], list[PairRecord]] = defaultdict(list)
    for pair in pairs:
        grouped[(pair.relation, f"{pair.source_pos}↔{pair.target_pos}")].append(pair)
    lines = [
        "# Oppositional conceptual index",
        "",
        "This is an opposition-first view generated from explicit Open English WordNet relations. "
        "It is not a claim that every English sense belongs to an oppositional axis. The complete, "
        "machine-readable inventory is `opposition_pairs.csv.gz`.",
        "",
    ]
    for (relation, pos_pair), members in sorted(grouped.items()):
        lines.extend([f"## {relation} · {pos_pair}", ""])
        ranked = sorted(
            members,
            key=lambda pair: (
                -max(pair.source_neighborhood_size, pair.target_neighborhood_size),
                normalized_text(pair.source_label),
                normalized_text(pair.target_label),
            ),
        )
        for pair in ranked[:500]:
            lines.append(
                f"- **{pair.source_label}** ⇄ **{pair.target_label}** "
                f"({pair.source_neighborhood_size}:{pair.target_neighborhood_size}; "
                f"balance {pair.neighborhood_balance:.2f})"
            )
            if pair.source_definition or pair.target_definition:
                lines.append(
                    f"  - {clipped(pair.source_definition)} / {clipped(pair.target_definition)}"
                )
        if len(ranked) > 500:
            lines.append(f"- _{len(ranked) - 500:,} additional pairs are present in the full table._")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_opposition_atlas(path: Path, pairs: Sequence[PairRecord], metrics: Mapping[str, Any]) -> None:
    rows = [
        {
            "kind": pair.source_kind,
            "relation": pair.relation,
            "left": pair.source_label,
            "right": pair.target_label,
            "pos": f"{pair.source_pos}↔{pair.target_pos}",
            "leftDefinition": clipped(pair.source_definition, 240),
            "rightDefinition": clipped(pair.target_definition, 240),
            "leftSize": pair.source_neighborhood_size,
            "rightSize": pair.target_neighborhood_size,
            "balance": round(pair.neighborhood_balance, 3),
            "reciprocal": pair.reciprocal,
        }
        for pair in sorted(
            pairs,
            key=lambda item: (normalized_text(item.source_label), normalized_text(item.target_label)),
        )
    ]
    payload = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Opposition Atlas · Linguistical Symmetry Theory</title>
<style>
:root {{ color-scheme: light dark; font-family: ui-sans-serif, system-ui, sans-serif; }}
body {{ margin: 0; background: Canvas; color: CanvasText; }}
main {{ max-width: 1180px; margin: auto; padding: 2rem 1rem 5rem; }}
h1 {{ margin-bottom: .25rem; }}
.lede {{ max-width: 78ch; line-height: 1.55; }}
.controls {{ position: sticky; top: 0; padding: .8rem 0; background: Canvas; display: grid; grid-template-columns: 1fr auto auto; gap: .6rem; }}
input, select {{ font: inherit; padding: .65rem; border: 1px solid color-mix(in srgb, CanvasText 25%, transparent); border-radius: .5rem; background: Canvas; color: CanvasText; }}
table {{ width: 100%; border-collapse: collapse; font-size: .92rem; }}
th, td {{ text-align: left; vertical-align: top; padding: .55rem; border-bottom: 1px solid color-mix(in srgb, CanvasText 18%, transparent); }}
th {{ position: sticky; top: 4.2rem; background: Canvas; }}
.pair {{ font-weight: 700; }}
.definition {{ max-width: 33ch; line-height: 1.35; opacity: .86; }}
.badge {{ white-space: nowrap; font-variant-numeric: tabular-nums; }}
small {{ opacity: .72; }}
@media (max-width: 780px) {{ .controls {{ grid-template-columns: 1fr; }} th:nth-child(n+5), td:nth-child(n+5) {{ display:none; }} }}
</style>
</head>
<body><main>
<h1>Opposition Atlas</h1>
<p class="lede">A searchable view of {metrics['opposition']['unique_undirected_pairs']:,} explicit opposition pairs in <code>{html.escape(metrics['lexicon_spec'])}</code>. Synonym-neighborhood size is measured by the number of distinct lemmas sharing each endpoint's synset. A balanced size is not evidence of semantic isomorphism; it is one structural measurement.</p>
<div class="controls">
<input id="query" type="search" placeholder="Search lemmas, definitions, relation types…" autofocus>
<select id="relation"><option value="">All relations</option></select>
<select id="kind"><option value="">Sense and synset pairs</option><option value="sense">Sense pairs</option><option value="synset">Synset pairs</option></select>
</div>
<p><small id="status"></small></p>
<table><thead><tr><th>Pair</th><th>Relation</th><th>Definitions</th><th>Neighborhoods</th><th>Reciprocal</th></tr></thead><tbody id="rows"></tbody></table>
<script>
const data = {payload};
const query = document.querySelector('#query');
const relation = document.querySelector('#relation');
const kind = document.querySelector('#kind');
const rows = document.querySelector('#rows');
const status = document.querySelector('#status');
const escapeHtml = value => String(value).replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
[...new Set(data.map(row => row.relation))].sort().forEach(value => {{ const option=document.createElement('option'); option.value=value; option.textContent=value; relation.append(option); }});
function render() {{
  const needle = query.value.trim().toLocaleLowerCase();
  const filtered = data.filter(row => (!relation.value || row.relation===relation.value) && (!kind.value || row.kind===kind.value) && (!needle || JSON.stringify(row).toLocaleLowerCase().includes(needle)));
  status.textContent = `${{filtered.length.toLocaleString()}} of ${{data.length.toLocaleString()}} pairs`;
  rows.innerHTML = filtered.slice(0, 5000).map(row => `<tr><td><div class="pair">${{escapeHtml(row.left)}} ⇄ ${{escapeHtml(row.right)}}</div><small>${{escapeHtml(row.pos)}} · ${{escapeHtml(row.kind)}}</small></td><td>${{escapeHtml(row.relation)}}</td><td><div class="definition">${{escapeHtml(row.leftDefinition)}}<br><br>${{escapeHtml(row.rightDefinition)}}</div></td><td class="badge">${{row.leftSize}} : ${{row.rightSize}}<br><small>balance ${{row.balance}}</small></td><td>${{row.reciprocal ? 'yes' : 'no'}}</td></tr>`).join('');
}}
[query, relation, kind].forEach(node => node.addEventListener('input', render));
render();
</script>
</main></body></html>
"""
    path.write_text(page, encoding="utf-8")


def render_paper(template_path: Path, output_path: Path, metrics: Mapping[str, Any]) -> None:
    text = template_path.read_text(encoding="utf-8")
    counts = metrics["counts"]
    coverage = metrics["coverage"]
    opposition = metrics["opposition"]
    neighborhoods = metrics["synonym_neighborhoods_around_sense_oppositions"]
    replacements = {
        "BUILT_AT": metrics["built_at_utc"],
        "LEXICON_SPEC": metrics["lexicon_spec"],
        "WORDS": f"{counts['words']:,}",
        "LEMMAS": f"{counts['distinct_normalized_lemmas']:,}",
        "FORMS": f"{counts['word_forms']:,}",
        "SENSES": f"{counts['senses']:,}",
        "SYNSETS": f"{counts['synsets']:,}",
        "RELATIONS": f"{counts['relations']:,}",
        "MULTI_SYNSETS": f"{counts['multi_member_synsets']:,}",
        "SENSE_SYNONYM_COUNT": f"{counts['senses_with_synonym_neighbor']:,}",
        "SENSE_SYNONYM_PCT": percent(coverage["share_senses_with_synonym_neighbor"]),
        "LEMMA_SYNONYM_COUNT": f"{counts['lemmas_with_synonym_neighbor']:,}",
        "LEMMA_SYNONYM_PCT": percent(coverage["share_lemmas_with_synonym_neighbor"]),
        "OPPOSITION_DIRECTED": f"{opposition['directed_relation_records']:,}",
        "OPPOSITION_PAIRS": f"{opposition['unique_undirected_pairs']:,}",
        "SENSE_OPPOSITION_PAIRS": f"{opposition['unique_sense_pairs']:,}",
        "SYNSET_OPPOSITION_PAIRS": f"{opposition['unique_synset_pairs']:,}",
        "INCIDENT_SENSES": f"{opposition['incident_senses']:,}",
        "INCIDENT_SENSES_PCT": percent(coverage["share_senses_with_direct_opposition"]),
        "INCIDENT_LEMMAS": f"{opposition['incident_lemmas']:,}",
        "INCIDENT_LEMMAS_PCT": percent(coverage["share_lemmas_with_direct_opposition"]),
        "RECIPROCAL_PAIRS": f"{opposition['reciprocal_unique_pairs']:,}",
        "RECIPROCAL_PCT": percent(opposition["reciprocal_pair_rate"]),
        "COMPONENTS": f"{opposition['connected_components']:,}",
        "LARGEST_COMPONENT": f"{opposition['largest_component_size']:,}",
        "BOTH_MULTI_COUNT": f"{neighborhoods['both_poles_multi_lemma']:,}",
        "BOTH_MULTI_PCT": percent(neighborhoods["share_both_poles_multi_lemma"]),
        "ONE_MULTI_COUNT": f"{neighborhoods['one_or_both_poles_multi_lemma']:,}",
        "ONE_MULTI_PCT": percent(neighborhoods["share_one_or_both_poles_multi_lemma"]),
        "EQUAL_NEIGHBOR_COUNT": f"{neighborhoods['equal_neighborhood_size_pairs']:,}",
        "EQUAL_NEIGHBOR_PCT": percent(neighborhoods["share_equal_neighborhood_sizes"]),
        "MEDIAN_BALANCE": f"{neighborhoods['median_balance_ratio']:.3f}",
        "SOURCE_REVISION": metrics["source_revision"],
    }
    for key, value in replacements.items():
        text = text.replace("{{" + key + "}}", value)
    unresolved = sorted({part.split("}}", 1)[0] for part in text.split("{{")[1:] if "}}" in part})
    if unresolved:
        raise BuildError(f"Unresolved paper placeholders: {', '.join(unresolved)}")
    output_path.write_text(text, encoding="utf-8")


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(output: Path) -> None:
    entries: list[str] = []
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.sha256":
            entries.append(f"{hash_file(path)}  {path.relative_to(output).as_posix()}")
    (output / "MANIFEST.sha256").write_text("\n".join(entries) + "\n", encoding="utf-8")


def write_provenance(
    output: Path,
    lexicon_spec: str,
    wordnet: "wn.Wordnet",
    revision: str,
    counts: Mapping[str, int],
) -> None:
    lexicons = []
    for lexicon in wordnet.lexicons():
        lexicons.append(
            {
                "id": safe_text(getattr(lexicon, "id", "")),
                "version": safe_text(getattr(lexicon, "version", "")),
                "label": safe_text(getattr(lexicon, "label", "")),
                "language": safe_text(getattr(lexicon, "language", "")),
                "license": safe_text(getattr(lexicon, "license", "")),
                "url": safe_text(getattr(lexicon, "url", "")),
            }
        )
    write_json(
        output / "provenance.json",
        {
            "project": PROJECT_NAME,
            "schema_version": SCHEMA_VERSION,
            "built_at_utc": utc_now(),
            "source_revision": revision,
            "lexicon_spec": lexicon_spec,
            "lexicons": lexicons,
            "ingestion_counts": dict(counts),
            "software": {
                "python": sys.version,
                "wn": getattr(get_wn_module(), "__version__", "unknown"),
            },
            "method": {
                "synonym_neighborhood": "distinct lemma co-membership in an OEWN synset",
                "opposition_relations": sorted(OPPOSITION_RELATIONS),
                "pair_deduplication": "unordered endpoint pair, relation type, and entity kind",
            },
        },
    )


def build(
    lexicon_spec: str,
    output: Path,
    paper_template: Path,
    revision: str,
) -> None:
    output = output.resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    wordnet = ensure_lexicon(lexicon_spec)
    lexicon_description = wordnet.describe()
    database_path = output / "lexicon.sqlite"
    connection = initialize_database(database_path)
    connection.executemany(
        "INSERT INTO metadata(key, value) VALUES (?, ?)",
        [
            ("project", PROJECT_NAME),
            ("schema_version", SCHEMA_VERSION),
            ("lexicon_spec", lexicon_spec),
            ("source_revision", revision),
            ("built_at_utc", utc_now()),
            ("lexicon_description", lexicon_description),
        ],
    )
    connection.commit()

    counts = ingest_wordnet(connection, wordnet)
    metrics, pairs = build_metrics(connection, lexicon_spec, lexicon_description, revision)
    write_json(output / "metrics.json", metrics)
    write_metrics_markdown(output / "metrics.md", metrics)
    export_tables(connection, output, pairs)
    write_conceptual_thesaurus(output / "conceptual_thesaurus.md", pairs)
    write_opposition_atlas(output / "opposition_atlas.html", pairs, metrics)
    render_paper(paper_template, output / "paper.md", metrics)
    write_provenance(output, lexicon_spec, wordnet, revision, counts)

    connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise BuildError(f"SQLite integrity check failed: {integrity}")
    connection.execute("VACUUM")
    connection.close()
    for suffix in ("-wal", "-shm"):
        extra = Path(str(database_path) + suffix)
        if extra.exists():
            extra.unlink()
    write_manifest(output)
    print(f"Build complete: {output}", flush=True)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the corpus-scale semantic symmetry artifacts.")
    parser.add_argument("--lexicon", default=DEFAULT_LEXICON)
    parser.add_argument("--output", type=Path, default=Path("artifacts"))
    parser.add_argument("--paper-template", type=Path, default=Path("paper/paper_template.md"))
    parser.add_argument("--revision", default=os.environ.get("GITHUB_SHA", "local-uncommitted"))
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        build(args.lexicon, args.output, args.paper_template, args.revision)
    except Exception as exc:
        print(f"BUILD FAILED: {exc}", file=sys.stderr)
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
