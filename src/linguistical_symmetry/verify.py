from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Sequence


REQUIRED_FILES = {
    "lexicon.sqlite",
    "metrics.json",
    "metrics.md",
    "provenance.json",
    "words.csv.gz",
    "alphabetical_index.csv.gz",
    "senses.csv.gz",
    "synsets.csv.gz",
    "relations.csv.gz",
    "opposition_pairs.csv.gz",
    "conceptual_thesaurus.md",
    "opposition_atlas.html",
    "paper.md",
    "MANIFEST.sha256",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest(root: Path) -> None:
    for line in (root / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = root / relative
        if not path.is_file():
            raise AssertionError(f"Manifest entry is missing: {relative}")
        actual = sha256(path)
        if actual != expected:
            raise AssertionError(f"Hash mismatch for {relative}: {actual} != {expected}")


def count_gzip_rows(path: Path) -> int:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        return max(0, sum(1 for _ in handle) - 1)


def verify(root: Path) -> None:
    missing = sorted(name for name in REQUIRED_FILES if not (root / name).is_file())
    if missing:
        raise AssertionError(f"Missing required artifacts: {', '.join(missing)}")

    metrics = json.loads((root / "metrics.json").read_text(encoding="utf-8"))
    counts = metrics["counts"]
    opposition = metrics["opposition"]

    if counts["words"] < 100_000:
        raise AssertionError(f"Word count is implausibly small: {counts['words']}")
    if counts["synsets"] < 100_000:
        raise AssertionError(f"Synset count is implausibly small: {counts['synsets']}")
    if counts["senses"] <= counts["words"]:
        raise AssertionError("Sense count must exceed lexical-entry count.")
    if counts["relations"] < 300_000:
        raise AssertionError(f"Relation count is implausibly small: {counts['relations']}")
    if opposition["unique_undirected_pairs"] <= 0:
        raise AssertionError("No opposition pairs were extracted.")

    connection = sqlite3.connect(root / "lexicon.sqlite")
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise AssertionError(f"SQLite integrity check failed: {integrity}")
    sql_counts = {
        "words": connection.execute("SELECT COUNT(*) FROM words").fetchone()[0],
        "senses": connection.execute("SELECT COUNT(*) FROM senses").fetchone()[0],
        "synsets": connection.execute("SELECT COUNT(*) FROM synsets").fetchone()[0],
        "relations": connection.execute("SELECT COUNT(*) FROM relations").fetchone()[0],
    }
    connection.close()
    for key, value in sql_counts.items():
        if value != counts[key]:
            raise AssertionError(f"Metric/database mismatch for {key}: {counts[key]} != {value}")

    csv_expectations = {
        "words.csv.gz": counts["words"],
        "senses.csv.gz": counts["senses"],
        "synsets.csv.gz": counts["synsets"],
        "relations.csv.gz": counts["relations"],
        "opposition_pairs.csv.gz": opposition["unique_undirected_pairs"],
    }
    for filename, expected in csv_expectations.items():
        actual = count_gzip_rows(root / filename)
        if actual != expected:
            raise AssertionError(f"Row-count mismatch for {filename}: {actual} != {expected}")

    paper = (root / "paper.md").read_text(encoding="utf-8")
    if "{{" in paper or "}}" in paper:
        raise AssertionError("The generated paper contains unresolved placeholders.")
    if str(counts["senses"]) not in paper.replace(",", ""):
        raise AssertionError("The generated paper does not contain the measured sense count.")

    verify_manifest(root)
    print("Artifact verification passed.")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify generated semantic-symmetry artifacts.")
    parser.add_argument("root", type=Path, nargs="?", default=Path("artifacts"))
    args = parser.parse_args(argv)
    verify(args.root.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
