import wn

from linguistical_symmetry.pipeline import UnionFind, median, normalized_text, percent, percentile, ratio


def test_union_find_components() -> None:
    graph = UnionFind()
    graph.union("inward", "outward")
    graph.union("inside", "outside")
    graph.union("inward", "inside")
    graph.add("unpaired")
    assert graph.component_sizes() == [4, 1]


def test_numeric_helpers() -> None:
    assert ratio(1, 4) == 0.25
    assert ratio(1, 0) == 0.0
    assert median([1, 2, 9]) == 2.0
    assert percentile([1, 2, 3, 4], 0.5) == 2.5
    assert percent(0.125) == "12.50%"


def test_normalized_text() -> None:
    assert normalized_text("  InWard\tMotion ") == "inward motion"


def test_wn_relation_metadata_compatibility() -> None:
    assert hasattr(wn.Sense, "relation_map")
    assert hasattr(wn.Synset, "relation_map")
