from rakl import (
    Context,
    Discriminator,
    KnowledgeFiber,
    Projection,
    Relation,
    Relationship,
    compare_contexts,
    rank_discriminators,
    semantic_gain,
)


def test_apple_principle_discovers_missing_facet():
    apple = KnowledgeFiber(
        fiber_id="apple",
        object_id="APPLE",
        atomic_step="global portrait",
        required_facets={"color", "shape", "taste", "texture"},
    )
    apple.add_projection(Projection("p1", "APPLE", ("color",), "red", "paper-1"))
    apple.add_projection(
        Projection("p2", "APPLE", ("shape",), "near sphere", "paper-2")
    )
    apple.add_projection(Projection("p3", "APPLE", ("taste",), "sweet", "paper-3"))

    assert apple.missing_facets() == {"texture"}
    tasks = apple.reflection_tasks()
    assert tasks == [
        {
            "kind": "EXPAND_MISSING_FACET",
            "facet": "texture",
            "prompt": (
                "Find semantically distinct projections and mechanisms for missing "
                "facet 'texture' of object 'APPLE'."
            ),
        }
    ]


def test_context_difference_prevents_false_contradiction():
    fiber = KnowledgeFiber("apple-color", "APPLE", "color")
    fiber.add_projection(
        Projection(
            "red",
            "APPLE",
            ("color",),
            "red",
            "source-red",
            Context(population="ripe Fuji"),
        )
    )
    fiber.add_projection(
        Projection(
            "green",
            "APPLE",
            ("color",),
            "green",
            "source-green",
            Context(population="unripe Granny Smith"),
        )
    )

    assert fiber.unresolved_pairs() == [("green", "red")]
    assert compare_contexts(
        fiber.projections["red"].context,
        fiber.projections["green"].context,
    )["population"] == ("ripe Fuji", "unripe Granny Smith")

    fiber.add_relation(
        Relation(
            "red",
            "green",
            Relationship.CONTEXT_DEPENDENT_DIFFERENCE,
            scope="population/ripeness",
        )
    )
    assert fiber.unresolved_pairs() == []
    assert fiber.contradictions() == []


def test_exact_equivalence_classes_merge_transitively_within_one_layer():
    fiber = KnowledgeFiber("state", "PROCESS", "state representation")
    for projection_id in ("psr", "oom", "automaton"):
        fiber.add_projection(
            Projection(
                projection_id,
                "PROCESS",
                ("state",),
                projection_id,
                projection_id,
            )
        )
    fiber.add_relation(
        Relation("psr", "oom", Relationship.EXACT_ISOMORPHISM, scope="same-state")
    )
    fiber.add_relation(
        Relation("oom", "automaton", Relationship.EXACT_ISOMORPHISM, scope="same-state")
    )

    assert {"psr", "oom", "automaton"} in fiber.equivalence_classes()


def test_mixed_equivalence_layers_do_not_upgrade_transitively():
    fiber = KnowledgeFiber("mixed", "PROCESS", "representation relationship")
    for projection_id in ("a", "b", "c"):
        fiber.add_projection(Projection(projection_id, "PROCESS", ("state",), projection_id, projection_id))
    fiber.add_relation(Relation("a", "b", Relationship.EXACT_ISOMORPHISM, scope="global"))
    fiber.add_relation(Relation("b", "c", Relationship.QOI_EQUIVALENCE, scope="QoI:x"))

    assert fiber.equivalence_classes() == [{"a", "b"}]
    qoi = fiber.equivalence_classes(Relationship.QOI_EQUIVALENCE)
    assert qoi == [{"b", "c"}]
    assert all(group != {"a", "b", "c"} for group in fiber.equivalence_classes())
    assert all(layer["members"] != ["a", "b", "c"] for layer in fiber.equivalence_layers())


def test_equivalence_scope_partition_prevents_cross_scope_bridge():
    fiber = KnowledgeFiber("scope", "PROCESS", "QoI equivalence")
    for projection_id in ("a", "b", "c"):
        fiber.add_projection(Projection(projection_id, "PROCESS", ("state",), projection_id, projection_id))
    fiber.add_relation(Relation("a", "b", Relationship.QOI_EQUIVALENCE, scope="QoI:x"))
    fiber.add_relation(Relation("b", "c", Relationship.QOI_EQUIVALENCE, scope="QoI:y"))

    assert fiber.equivalence_classes(Relationship.QOI_EQUIVALENCE) == [
        {"a", "b"},
        {"b", "c"},
    ]
    assert fiber.equivalence_classes(Relationship.QOI_EQUIVALENCE, scope="QoI:x") == [
        {"a", "b"}
    ]
    assert all(group != {"a", "b", "c"} for group in fiber.equivalence_classes(Relationship.QOI_EQUIVALENCE))


def test_approximate_relationships_remain_pairwise_not_transitive_classes():
    fiber = KnowledgeFiber("approx", "PROCESS", "approximation")
    for projection_id in ("a", "b", "c"):
        fiber.add_projection(Projection(projection_id, "PROCESS", ("state",), projection_id, projection_id))
    fiber.add_relation(Relation("a", "b", Relationship.APPROXIMATE_REPRESENTATION, scope="epsilon=0.1"))
    fiber.add_relation(Relation("b", "c", Relationship.APPROXIMATE_REPRESENTATION, scope="epsilon=0.1"))

    assert [(r.left, r.right) for r in fiber.approximate_relationships()] == [
        ("a", "b"),
        ("b", "c"),
    ]
    assert not fiber.equivalence_layers()
    try:
        fiber.equivalence_classes(Relationship.APPROXIMATE_REPRESENTATION)
    except ValueError as exc:
        assert "not licensed for transitive equivalence closure" in str(exc)
    else:
        raise AssertionError("approximation must not be silently promoted to transitive equivalence")


def test_global_portrait_exposes_typed_scoped_equivalence_layers():
    fiber = KnowledgeFiber("portrait", "PROCESS", "atlas gluing")
    for projection_id in ("a", "b", "c", "d"):
        fiber.add_projection(Projection(projection_id, "PROCESS", ("state",), projection_id, projection_id))
    fiber.add_relation(Relation("a", "b", Relationship.EXACT_ISOMORPHISM, scope="global"))
    fiber.add_relation(Relation("b", "c", Relationship.OBSERVATIONAL_EQUIVALENCE, scope="sensor:S"))
    fiber.add_relation(Relation("c", "d", Relationship.QOI_EQUIVALENCE, scope="QoI:x"))
    fiber.add_relation(Relation("a", "d", Relationship.APPROXIMATE_REPRESENTATION, scope="epsilon=0.2"))

    portrait = fiber.global_portrait()
    assert portrait["equivalence_classes"] == [["a", "b"]]
    assert {
        (layer["relationship"], layer["scope"], tuple(layer["members"]))
        for layer in portrait["equivalence_layers"]
    } == {
        ("EXACT_ISOMORPHISM", "global", ("a", "b")),
        ("OBSERVATIONAL_EQUIVALENCE", "sensor:S", ("b", "c")),
        ("QOI_EQUIVALENCE", "QoI:x", ("c", "d")),
    }
    assert portrait["approximate_relationships"] == [
        {
            "left": "a",
            "right": "d",
            "scope": "epsilon=0.2",
            "evidence": [],
        }
    ]


def test_contradiction_opens_discriminator_task():
    fiber = KnowledgeFiber("x", "X", "mechanism")
    fiber.add_projection(Projection("a", "X", ("memory",), "A", "s1"))
    fiber.add_projection(Projection("b", "X", ("memory",), "B", "s2"))
    fiber.add_relation(
        Relation("a", "b", Relationship.CONTRADICTION, scope="same population")
    )

    tasks = fiber.reflection_tasks()
    assert any(task["kind"] == "DESIGN_DISCRIMINATOR" for task in tasks)


def test_frozen_discriminator_beats_same_cost_unfrozen_design():
    frozen = Discriminator("frozen", ("H1", "H2"), 10.0, 5.0, True)
    unfrozen = Discriminator("unfrozen", ("H1", "H2"), 12.0, 5.0, False)
    assert rank_discriminators([unfrozen, frozen])[0].discriminator_id == "frozen"


def test_semantic_gain_counts_new_meaning_not_total_papers():
    before = {"mechanisms": ["A"], "facets": ["shape"]}
    after = {
        "mechanisms": ["A", "B"],
        "facets": ["shape", "taste"],
        "papers": ["p1", "p2", "p3"],
    }
    gain = semantic_gain(before, after)
    assert gain["mechanisms"] == ["B"]
    assert gain["facets"] == ["taste"]
    assert gain["papers"] == ["p1", "p2", "p3"]
