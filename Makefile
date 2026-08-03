.PHONY: test build verify clean

test:
	python -m pytest

build:
	python -m linguistical_symmetry.pipeline --lexicon oewn:2025 --output artifacts

verify:
	python -m linguistical_symmetry.verify artifacts

clean:
	rm -rf artifacts .pytest_cache
