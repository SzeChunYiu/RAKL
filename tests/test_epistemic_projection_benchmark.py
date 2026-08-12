from rakl.epistemic_projection_benchmark import (
    Architecture,
    FAMILIES,
    audit_all,
    audit_architecture,
    make_worlds,
    projection,
)


def test_twin_worlds_differ_only_in_registered_critical_coordinate_and_gold() -> None:
    worlds = make_worlds()
    assert len(worlds) == 2 * len(FAMILIES) == 30
    by_family = {
        family.family_id: [world for world in worlds if world.family_id == family.family_id]
        for family in FAMILIES
    }
    for family in FAMILIES:
        left, right = by_family[family.family_id]
        differing = {key for key in left.state if left.state[key] != right.state[key]}
        assert differing == {family.critical_coordinate}
        assert left.gold_action != right.gold_action


def test_rakl_typed_projection_separates_every_gold_distinction() -> None:
    audit = audit_architecture(make_worlds(), Architecture.RAKL_TYPED_AUTHORITY)
    assert audit.ambiguous_projected_states == 0
    assert audit.identifiable_accuracy_upper_bound == 1.0
    assert audit.unavoidable_error_lower_bound == 0.0
    assert audit.zero_error_legitimate_update_recall_upper_bound == 1.0


def test_each_weaker_projection_has_an_information_collision() -> None:
    worlds = make_worlds()
    for architecture in Architecture:
        if architecture is Architecture.RAKL_TYPED_AUTHORITY:
            continue
        audit = audit_architecture(worlds, architecture)
        assert audit.ambiguous_projected_states > 0
        assert audit.identifiable_accuracy_upper_bound < 1.0
        assert audit.unavoidable_error_lower_bound > 0.0


def test_pairwise_compatibility_cannot_see_higher_order_gluing_twin() -> None:
    worlds = [world for world in make_worlds() if world.family_id == "F03_HIGHER_ORDER_GLUING"]
    assert len(worlds) == 2
    assert projection(worlds[0], Architecture.PAIRWISE_COMPATIBILITY_ONLY) == projection(
        worlds[1], Architecture.PAIRWISE_COMPATIBILITY_ONLY
    )
    assert worlds[0].gold_action != worlds[1].gold_action


def test_provenance_only_sees_independence_but_not_other_typed_coordinates() -> None:
    collisions = audit_all()["collision_matrix"][Architecture.PROVENANCE_ONLY.value]
    assert collisions["F05_INDEPENDENCE_INFLATION"] is False
    assert collisions["F03_HIGHER_ORDER_GLUING"] is True
    assert collisions["F06_PREDICTION_MECHANISM"] is True


def test_transactional_state_handles_supersession_but_not_authority_semantics() -> None:
    collisions = audit_all()["collision_matrix"][Architecture.SIMPLE_TRANSACTIONAL_STATE.value]
    assert collisions["F10_SUPERSESSION_STALE_RETRIEVAL"] is False
    assert collisions["F15_LEGITIMATE_SUPERSESSION"] is False
    assert collisions["F06_PREDICTION_MECHANISM"] is True
    assert collisions["F07_MECHANISM_IDENTIFICATION"] is True


def test_blanket_hold_cannot_solve_legitimate_update_controls() -> None:
    for audit in audit_all()["architectures"].values():
        assert audit["blanket_hold_legitimate_update_recall"] == 0.0
        assert audit["blanket_hold_accuracy"] < 0.5
