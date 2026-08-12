from __future__ import annotations

from typing import Mapping

from .generator import TrainingCase
from .types import FamilyId, GoldLabel


def _payload_map(case: TrainingCase) -> Mapping[str, object]:
    return dict(case.executable_payload)


def _verify_sequence(payload: Mapping[str, object]) -> GoldLabel:
    ops = payload["ops"]
    op_names = tuple(op for op, _ in ops)
    if op_names == ("add", "mul"):
        return GoldLabel.VALID
    return GoldLabel.INVALID


def _verify_balance(payload: Mapping[str, object]) -> GoldLabel:
    inflow = int(payload["inflow"])
    outflow = int(payload["outflow"])
    store = int(payload["store"])
    if inflow == outflow + store:
        return GoldLabel.VALID
    return GoldLabel.INVALID


def _verify_reachability(payload: Mapping[str, object]) -> GoldLabel:
    edges = tuple(payload["edges"])
    start = payload["start"]
    target = payload["target"]
    reachable = {start}
    frontier = [start]
    while frontier:
        node = frontier.pop()
        for src, dst in edges:
            if src == node and dst not in reachable:
                reachable.add(dst)
                frontier.append(dst)
    return GoldLabel.VALID if target in reachable else GoldLabel.INVALID


_VERIFIERS = {
    FamilyId.SEQUENCE_COMPOSITION: _verify_sequence,
    FamilyId.BALANCE_CONSERVATION: _verify_balance,
    FamilyId.STATE_REACHABILITY: _verify_reachability,
}


def verify_case(case: TrainingCase) -> TrainingCase:
    """Assign deterministic gold from executable semantics only."""

    payload = _payload_map(case)
    family = case.family_id
    if family not in _VERIFIERS:
        raise ValueError(f"no verifier for family {family}")
    gold = _VERIFIERS[family](payload)
    return TrainingCase(
        case_id=case.case_id,
        family_id=case.family_id,
        structure=case.structure,
        executable_payload=case.executable_payload,
        surface_text=case.surface_text,
        surface_template_id=case.surface_template_id,
        coordinate_values=case.coordinate_values,
        control_kind=case.control_kind,
        twin_of_case_id=case.twin_of_case_id,
        gold_label=gold,
    )
