"""Challenger allocator: marginal-gain semantics + unchanged fail-closed envelope.

The two behavioural deltas under test against the production scheduler:

1. slot allocation follows believed marginal gain (gain x headroom), not the
   argmin mastery level;
2. allocation is per-slot with a saturating believed state, so a batch spreads
   across coordinates instead of committing every non-repetition slot to one.

Everything fail-closed must match production exactly.
"""

from dataclasses import replace

from rakl.training_projection import MasteryCoordinate
from rakl.training_scheduler import AllocationVerdict, choose_adaptive_training_batch
from rakl.training_scheduler_challenger import choose_marginal_gain_training_batch

from test_training_scheduler import _candidate, _coords, _mastery, _snapshot


def test_marginal_gain_prefers_derivative_over_level() -> None:
    """TRANSFER has the lowest level but a tiny gain; COMPOSITION has the gain.

    The production scheduler targets TRANSFER (argmin level).  The challenger
    must allocate non-repetition slots to COMPOSITION, where the believed
    marginal gain is larger.
    """
    mastery = _mastery(coordinate_values=_coords(
        **{MasteryCoordinate.TRANSFER: 0.50, MasteryCoordinate.COMPOSITION: 0.62}))
    candidates = tuple(
        _candidate(i, principle=0.05, transfer=0.02, composition=0.50)
        for i in range(1, 9)
    )
    snapshot = _snapshot(mastery=mastery, candidates=candidates)

    production = choose_adaptive_training_batch(snapshot, batch_size=4)
    assert production.target_coordinate is MasteryCoordinate.TRANSFER

    challenger = choose_marginal_gain_training_batch(snapshot, batch_size=4)
    assert challenger.verdict is AllocationVerdict.ALLOCATE
    slots = next(r for r in challenger.reasons if r.startswith("slot_coordinates:"))
    assert "COMPOSITION" in slots
    assert "TRANSFER" not in slots


def test_per_slot_water_filling_spreads_across_coordinates() -> None:
    """A large TRANSFER gain saturates the believed state after one slot, so
    later slots must move to the next-best coordinate rather than repeating."""
    mastery = _mastery(coordinate_values=_coords(
        **{MasteryCoordinate.TRANSFER: 0.50, MasteryCoordinate.COMPOSITION: 0.62}))
    candidates = tuple(
        _candidate(i, principle=0.05, transfer=0.80, composition=0.60)
        for i in range(1, 9)
    )
    snapshot = _snapshot(mastery=mastery, candidates=candidates)
    decision = choose_marginal_gain_training_batch(snapshot, batch_size=5)
    assert decision.verdict is AllocationVerdict.ALLOCATE
    slots = next(r for r in decision.reasons if r.startswith("slot_coordinates:"))
    body = slots.split(":", 1)[1].split(",")
    non_floor = [s for s in body if s != "PRINCIPLE_FLOOR"]
    assert "TRANSFER" in non_floor
    assert "COMPOSITION" in non_floor, "water-filling must not commit every slot to one coordinate"


def test_repetition_floor_is_a_preserved_constraint() -> None:
    snapshot = _snapshot(repetition_floor=0.25)
    decision = choose_marginal_gain_training_batch(snapshot, batch_size=4)
    assert decision.verdict is AllocationVerdict.ALLOCATE
    assert len(decision.repetition_candidate_ids) == 1
    slots = next(r for r in decision.reasons if r.startswith("slot_coordinates:"))
    assert slots.split(":", 1)[1].split(",")[0] == "PRINCIPLE_FLOOR"


def test_no_principle_until_threshold_target_remains() -> None:
    """Low PRINCIPLE level no longer captures the whole batch: with a small
    principle gain and a large composition gain, non-floor slots go elsewhere."""
    mastery = _mastery(coordinate_values=_coords(**{MasteryCoordinate.PRINCIPLE: 0.40}))
    candidates = tuple(
        _candidate(i, principle=0.03, composition=0.60) for i in range(1, 9)
    )
    snapshot = _snapshot(mastery=mastery, candidates=candidates)

    production = choose_adaptive_training_batch(snapshot, batch_size=4)
    assert production.target_coordinate is MasteryCoordinate.PRINCIPLE

    challenger = choose_marginal_gain_training_batch(snapshot, batch_size=4)
    slots = next(r for r in challenger.reasons if r.startswith("slot_coordinates:"))
    assert "COMPOSITION" in slots


def test_forgetting_risk_remains_noncompensatory() -> None:
    risky = tuple(
        replace(_candidate(i, transfer=0.9),
                utility=replace(_candidate(i).utility, forgetting_risk=0.5))
        for i in range(1, 9)
    )
    snapshot = _snapshot(candidates=risky)
    decision = choose_marginal_gain_training_batch(snapshot, batch_size=4)
    assert decision.verdict is AllocationVerdict.CANNOT_CHECK
    assert "no_candidate_survives_noncompensatory_safety_gates" in decision.reasons


def test_insufficient_candidates_fail_closed() -> None:
    snapshot = _snapshot(candidates=(_candidate(1, principle=0.3, transfer=0.5),))
    decision = choose_marginal_gain_training_batch(snapshot, batch_size=4)
    assert decision.verdict is AllocationVerdict.CANNOT_CHECK


def test_posthoc_projection_is_invalid() -> None:
    snapshot = _snapshot(frozen=False)
    decision = choose_marginal_gain_training_batch(snapshot, batch_size=4)
    assert decision.verdict is AllocationVerdict.INVALID


def test_challenger_grants_no_authority_and_leaves_production_callable() -> None:
    decision = choose_marginal_gain_training_batch(_snapshot(), batch_size=4)
    assert decision.grants_scientific_authority is False
    assert decision.grants_structural_transfer_authority is False
    assert decision.claims_scheduler_efficacy is False
    assert any("production_scheduler_untouched" in r for r in decision.reasons)
    # The production mechanic is still present and independently callable.
    production = choose_adaptive_training_batch(_snapshot(), batch_size=4)
    assert production.verdict is AllocationVerdict.ALLOCATE
