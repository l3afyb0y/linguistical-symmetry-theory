"""Corpus-scale tools for the Linguistical Symmetry Theory project.

The project supports the stable ``wn`` 1.1 API as installed by the build runner.
Some documentation and patch releases expose ``relation_map()``, while the
installed objects expose the equivalent metadata-preserving
``relations(data=True)`` interface. The adapter below supplies only that missing
convenience method and leaves native implementations untouched.
"""

from __future__ import annotations

from typing import Any

__version__ = "0.3.1"


def _relations_with_metadata(self: Any) -> dict[Any, Any]:
    """Return the one-relation-to-one-target mapping used by the pipeline."""

    return self.relations(data=True)


def _install_wn_relation_map_compatibility() -> None:
    import wn

    for entity_type in (wn.Sense, wn.Synset):
        if not hasattr(entity_type, "relation_map"):
            setattr(entity_type, "relation_map", _relations_with_metadata)


_install_wn_relation_map_compatibility()
