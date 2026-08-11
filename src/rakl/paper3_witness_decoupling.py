"""Pre-specified witness/label decoupling diagnostic for Paper III.

Frozen before external annotations (#217). When adjudicated labels exist,
compute whether ``transfer_valid`` is definitionally identical to
``AND(invariant_preserved, boundary_matched, qoi_matched,
directional_mapping_complete)``.

If decoupling_rate == 0, the ``witnessed_structure`` arm is
``NOT_INFORMATIVE`` for incremental discrimination and must not authorize
training on structural-feature novelty grounds.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence


WITNESS_COORDINATES = (
    "invariant_preserved",
    "boundary_matched",
    "qoi_matched",
    "directional_mapping_complete",
)


def witness_and(judgements: Mapping[str, Any]) -> bool | None:
    """Return AND of the four witness coordinates, or None if any is missing."""
    values: list[bool] = []
    for name in WITNESS_COORDINATES:
        if name not in judgements or judgements[name] is None:
            return None
        values.append(bool(judgements[name]))
    return all(values)


def item_is_decoupled(judgements: Mapping[str, Any]) -> bool | None:
    """True when transfer_valid differs from AND(witness coordinates)."""
    if judgements.get("transfer_valid") is None:
        return None
    conjunction = witness_and(judgements)
    if conjunction is None:
        return None
    return bool(judgements["transfer_valid"]) != conjunction


def decoupling_rate(items: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Compute decoupling rate over adjudicated judgement dicts.

    Each item must expose the nine-coordinate judgement fields (or at least
    the four witness coordinates plus ``transfer_valid``). Items that cannot
    be assessed (any required field null) are counted separately and excluded
    from the rate denominator.
    """
    assessed = 0
    decoupled = 0
    cannot_assess = 0
    for item in items:
        flag = item_is_decoupled(item)
        if flag is None:
            cannot_assess += 1
            continue
        assessed += 1
        if flag:
            decoupled += 1
    rate = (decoupled / assessed) if assessed else None
    if assessed == 0:
        status = "CANNOT_CHECK_NO_ASSESSED_ITEMS"
        witnessed_structure_authority = "CANNOT_CHECK"
    elif rate == 0.0:
        status = "DEFINITIONALLY_DETERMINED"
        witnessed_structure_authority = "NOT_INFORMATIVE"
    else:
        status = "DECOUPLED_SUBSET_PRESENT"
        witnessed_structure_authority = "INFORMATIVE_CANDIDATE"
    return {
        "schema_version": "paper3-witness-label-decoupling-v1",
        "assessed_item_count": assessed,
        "cannot_assess_item_count": cannot_assess,
        "decoupled_item_count": decoupled,
        "decoupling_rate": rate,
        "status": status,
        "witnessed_structure_authority": witnessed_structure_authority,
        "rule": (
            "decoupling_rate = mean(transfer_valid != AND(invariant_preserved, "
            "boundary_matched, qoi_matched, directional_mapping_complete)) "
            "over assessed items"
        ),
        "training_implication": (
            "If witnessed_structure_authority is NOT_INFORMATIVE, do not report "
            "witnessed_structure AUC/AP as incremental discrimination and do not "
            "treat a witnessed_structure-only lift as authorization for expensive "
            "training."
        ),
    }


def decoupling_from_benchmark_cases(
    cases: Iterable[Mapping[str, Any]],
    *,
    judgement_key: str | None = None,
) -> dict[str, Any]:
    """Extract judgements from confirmatory benchmark cases and score them.

    If ``judgement_key`` is set, each case[judgement_key] is used; otherwise
    the case itself is treated as the judgement mapping (v2 adjudicated
    flattened fields).
    """
    items: list[Mapping[str, Any]] = []
    for case in cases:
        if judgement_key:
            payload = case.get(judgement_key) or {}
            if isinstance(payload, Mapping):
                items.append(payload)
        else:
            items.append(case)
    return decoupling_rate(items)
