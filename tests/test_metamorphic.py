import pytest
from hypothesis import given, strategies as st

from rakl import (
    Context,
    KnowledgeFiber,
    Projection,
    Relation,
    Relationship,
    compare_contexts,
)


short_text = st.text(min_size=1, max_size=12)
assumption_sets = st.lists(short_text, min_size=0, max_size=4, unique=True).map(tuple)


@given(
    left_population=st.one_of(st.none(), short_text),
    right_population=st.one_of(st.none(), short_text),
    left_assumptions=assumption_sets,
    right_assumptions=assumption_sets,
)
def test_context_comparison_is_symmetric_up_to_tuple_reversal(
    left_population,
    right_population,
    left_assumptions,
    right_assumptions,
):
    left = Context(population=left_population, assumptions=left_assumptions)
    right = Context(population=right_population, assumptions=right_assumptions)

    left_to_right = compare_contexts(left, right)
    right_to_left = compare_contexts(right, left)

    assert set(left_to_right) == set(right_to_left)
    for key, pair in left_to_right.items():
        assert right_to_left[key] == (pair[1], pair[0])


@given(left_assumptions=assumption_sets, right_assumptions=assumption_sets)
def test_assumptions_are_a_default_context_coordinate(
    left_assumptions,
    right_assumptions,
):
    left = Context(assumptions=left_assumptions)
    right = Context(assumptions=right_assumptions)
    differences = compare_contexts(left, right)

    if left_assumptions == right_assumptions:
        assert "assumptions" not in differences
    else:
        assert differences["assumptions"] == (
            left_assumptions,
            right_assumptions,
        )


@given(claim=short_text, source=short_text)
def test_replaying_identical_projection_is_idempotent(claim, source):
    fiber = KnowledgeFiber("replay", "OBJECT", "projection ingestion")
    projection = Projection("p", "OBJECT", ("facet",), claim, source)

    fiber.add_projection(projection)
    fiber.add_projection(projection)

    assert fiber.projections == {"p": projection}
    assert fiber.covered_facets() == {"facet"}


@given(claim=short_text, source=short_text, replacement_claim=short_text)
def test_projection_identity_cannot_be_mutated_by_reuse(
    claim,
    source,
    replacement_claim,
):
    if replacement_claim == claim:
        replacement_claim = claim + "!"

    fiber = KnowledgeFiber("identity", "OBJECT", "projection ingestion")
    original = Projection("p", "OBJECT", ("facet",), claim, source)
    replacement = Projection(
        "p",
        "OBJECT",
        ("facet",),
        replacement_claim,
        source,
    )
    fiber.add_projection(original)

    with pytest.raises(ValueError, match="projection identity is immutable"):
        fiber.add_projection(replacement)

    assert fiber.projections["p"] == original


@given(
    relation_order=st.permutations(
        (
            ("a", "b"),
            ("b", "c"),
            ("c", "d"),
        )
    )
)
def test_typed_scoped_equivalence_is_invariant_to_relation_order(relation_order):
    fiber = KnowledgeFiber("order", "OBJECT", "equivalence closure")
    for projection_id in ("a", "b", "c", "d"):
        fiber.add_projection(
            Projection(
                projection_id,
                "OBJECT",
                ("facet",),
                projection_id,
                projection_id,
            )
        )

    for left, right in relation_order:
        fiber.add_relation(
            Relation(
                left,
                right,
                Relationship.EXACT_ISOMORPHISM,
                scope="global",
            )
        )

    assert fiber.equivalence_classes() == [{"a", "b", "c", "d"}]
    assert fiber.equivalence_layers() == [
        {
            "relationship": "EXACT_ISOMORPHISM",
            "scope": "global",
            "members": ["a", "b", "c", "d"],
        }
    ]
