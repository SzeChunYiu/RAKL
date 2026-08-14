from __future__ import annotations

from collections import Counter
import json
import random

from rakl.structural_transport_v2 import (
    ObligationKind,
    ObligationStatus,
    StructuralWitnessV2,
    TransferObligation,
    assess_transfer_v2,
)
from rakl.structural_types import (
    BoundaryCondition,
    StructuralObject,
    StructuralRelation,
    StructuralRole,
    TransferDecision,
)


def _object(
    structure_id: str,
    context_id: str,
    *,
    qoi: str = "stability",
    boundary: str = "continual",
    matching_invariant: bool = True,
) -> StructuralObject:
    return StructuralObject(
        structure_id=structure_id,
        domain="opaque-domain",
        qoi=qoi,
        context_id=context_id,
        roles=(
            StructuralRole("arrival", "input"),
            StructuralRole("service", "capacity"),
        ),
        relations=(StructuralRelation("arrival", "competes_with", "service"),),
        invariants=frozenset(
            {"arrival_gt_service_implies_growth"}
            if matching_invariant
            else {"finite_batch_drains"}
        ),
        boundaries=(BoundaryCondition("flow_regime", boundary),),
        evidence_ids=(f"evidence:{structure_id}",),
    )


def run(seed: int = 20260812, n: int = 1200) -> dict[str, object]:
    """Run an oracle/conformance smoke test, not a learned-model experiment.

    Hidden validity is generated from exact QoI/boundary/invariant/precondition state.
    The witness therefore receives oracle obligation information. This checks executable
    semantics and benchmark plumbing only; it cannot support a model-superiority claim.
    """
    rng = random.Random(seed)
    rows: list[tuple[int, TransferDecision, TransferDecision, TransferDecision, str | None]] = []

    for index in range(n):
        quadrant = index % 4
        valid = quadrant in (0, 1)  # Q1/Q2
        semantic_high = quadrant in (0, 2)  # Q1/Q3
        failure = None if valid else rng.choice(
            ["boundary", "qoi", "invariant", "precondition", "unknown"]
        )

        source = _object(f"source-{index}", f"source-context-{index}")
        target = _object(
            f"target-{index}",
            f"target-context-{index}",
            qoi="latency" if failure == "qoi" else "stability",
            boundary="finite_batch" if failure == "boundary" else "continual",
            matching_invariant=failure != "invariant",
        )

        obligations = [
            TransferObligation(
                "qoi",
                ObligationKind.QOI,
                "stability",
                "stability",
                evidence_ids=(f"evidence:qoi:{index}",),
            ),
            TransferObligation(
                "boundary",
                ObligationKind.BOUNDARY,
                "flow_regime",
                "continual",
                evidence_ids=(f"evidence:boundary:{index}",),
            ),
            TransferObligation(
                "invariant",
                ObligationKind.INVARIANT,
                "arrival_gt_service_implies_growth",
                "arrival_gt_service_implies_growth",
                evidence_ids=(f"evidence:invariant:{index}",),
            ),
            # Required for source coverage: an obligation set that leaves a source
            # relation unasked cannot license (see assess_transfer_v2 coverage rule).
            TransferObligation(
                "relation",
                ObligationKind.RELATION,
                "arrival|competes_with|service|1",
                "arrival|competes_with|service|1",
                evidence_ids=(f"evidence:relation:{index}",),
            ),
        ]
        if failure == "precondition":
            precondition_status = ObligationStatus.VIOLATED
            precondition_reason = "precondition_false"
        elif failure == "unknown":
            precondition_status = ObligationStatus.UNKNOWN
            precondition_reason = ""
        else:
            precondition_status = ObligationStatus.SATISFIED
            precondition_reason = "precondition_true"
        obligations.append(
            TransferObligation(
                "precondition",
                ObligationKind.PRECONDITION,
                "steady_state",
                "target",
                evidence_ids=(f"evidence:precondition:{index}",),
                status=precondition_status,
                rationale_code=precondition_reason,
            )
        )

        witness = StructuralWitnessV2(
            witness_id=f"witness-{index}",
            source_structure_id=source.structure_id,
            target_structure_id=target.structure_id,
            source_context_id=source.context_id,
            target_context_id=target.context_id,
            qoi="stability",
            role_mapping=(("arrival", "arrival"), ("service", "service")),
            obligations=tuple(obligations),
        )
        decision = assess_transfer_v2(source, target, witness).decision
        gold = (
            TransferDecision.CANNOT_CHECK
            if failure == "unknown"
            else TransferDecision.LICENSED
            if valid
            else TransferDecision.REJECTED
        )
        semantic = TransferDecision.LICENSED if semantic_high else TransferDecision.REJECTED
        rows.append((quadrant, gold, decision, semantic, failure))

    q2 = [row for row in rows if row[0] == 1]
    q3 = [row for row in rows if row[0] == 2]
    return {
        "schema": "paper2.oracle_conformance.v1",
        "seed": seed,
        "n": n,
        "warning": (
            "Oracle/conformance result only. Witness obligations are generated from exact hidden "
            "structural conditions; this is not evidence that an LLM can extract witnesses or "
            "outperform a learned comparator."
        ),
        "v2_exact_three_way_accuracy": sum(gold == decision for _, gold, decision, _, _ in rows) / n,
        "semantic_surface_exact_three_way_accuracy": sum(gold == semantic for _, gold, _, semantic, _ in rows) / n,
        "q2_valid_distant_license_rate": sum(
            decision is TransferDecision.LICENSED for _, _, decision, _, _ in q2
        ) / len(q2),
        "q3_hostile_nearmiss_license_rate": sum(
            decision is TransferDecision.LICENSED for _, _, decision, _, _ in q3
        ) / len(q3),
        "decision_counts": dict(Counter(decision.value for _, _, decision, _, _ in rows)),
        "failure_counts": dict(Counter(str(failure) for *_, failure in rows)),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
