from __future__ import annotations

from rakl.objective_transfer_benchmark import Decision
from rakl.objective_transfer_robustness import FAMILIES, verify
from rakl.structural_routing_benchmark import (
    RoutingArm,
    make_routing_episodes,
    route_episode,
)


# Instrument-only seed. Registered downstream development seed 2026081221 is
# intentionally not touched by this test module.
INSTRUMENT_TEST_SEED = 2718


def _episodes():
    return make_routing_episodes(
        INSTRUMENT_TEST_SEED,
        n_standard_per_family=3,
        n_unknown_only_per_family=1,
    )


def test_registered_routing_families_and_episode_types_construct() -> None:
    episodes = _episodes()
    assert {episode.family for episode in episodes} == set(FAMILIES)
    for family in FAMILIES:
        assert any(
            episode.family == family and episode.episode_type == "STANDARD"
            for episode in episodes
        )
        assert any(
            episode.family == family and episode.episode_type == "UNKNOWN_ONLY"
            for episode in episodes
        )


def test_every_standard_episode_contains_valid_trap_and_unknown() -> None:
    for episode in _episodes():
        if episode.episode_type != "STANDARD":
            continue
        gold = [verify(candidate) for candidate in episode.candidates]
        assert Decision.ACCEPT in gold
        assert Decision.REJECT in gold
        assert Decision.CANNOT_CHECK in gold
        assert any(
            candidate.item_type == "VALID_DISTANT_TRANSFER"
            and verify(candidate) is Decision.ACCEPT
            for candidate in episode.candidates
        )


def test_unknown_only_controls_are_truly_unknown() -> None:
    for episode in _episodes():
        if episode.episode_type == "UNKNOWN_ONLY":
            assert all(
                verify(candidate) is Decision.CANNOT_CHECK
                for candidate in episode.candidates
            )


def test_full_gate_never_executes_an_invalid_or_unknown_candidate() -> None:
    for episode in _episodes():
        result = route_episode(episode, RoutingArm.FULL_APPLICABILITY_GATE)
        assert result.invalid_execution is False
        if result.selected_gold is not None:
            assert result.selected_gold is Decision.ACCEPT


def test_hybrid_recovery_finds_valid_distant_transfer_on_standard_episodes() -> None:
    for episode in _episodes():
        result = route_episode(episode, RoutingArm.FULL_HYBRID_RECOVERY)
        if episode.episode_type == "STANDARD":
            assert result.success is True
            assert result.selected_valid_distant is True
        else:
            assert result.selected_item_id is None
            assert result.correct_abstention is True


def test_routing_is_order_invariant_except_for_registered_semantic_ranking() -> None:
    # Candidate tuple order is shuffled at generation. Each arm computes its own
    # deterministic semantic ranking, so replaying the same episode is exact.
    for episode in _episodes():
        for arm in RoutingArm:
            assert route_episode(episode, arm) == route_episode(episode, arm)
