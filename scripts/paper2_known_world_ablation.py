from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
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


@dataclass(frozen=True)
class HiddenCase:
    family: str
    semantic_high: bool
    valid: bool
    unknown: bool
    violation: str | None


def _generate_hidden_case(rng: random.Random, index: int) -> HiddenCase:
    """Generate gold from a family-specific hidden rule before compiling a witness."""
    family = ("queue", "feedback", "cascade", "causal")[index % 4]
    semantic_high = (index // 4) % 2 == 0
    unknown = rng.random() < 0.08

    if family == "queue":
        continual = rng.random() < 0.65
        qoi_ok = rng.random() < 0.9
        valid = continual and qoi_ok
        violation = None if valid else ("boundary" if not continual else "qoi")
    elif family == "feedback":
        target_sign = 1 if rng.random() < 0.65 else -1
        qoi_ok = rng.random() < 0.9
        valid = target_sign == 1 and qoi_ok
        violation = None if valid else ("direction" if target_sign != 1 else "qoi")
    elif family == "cascade":
        reproduction = rng.uniform(0.4, 1.6)
        connectivity = rng.random() < 0.8
        valid = reproduction > 1 and connectivity
        violation = None if valid else ("precondition" if reproduction <= 1 else "boundary")
    else:
        mechanism_same = rng.random() < 0.75
        modifier_shift = rng.random() < 0.25
        valid = mechanism_same and not modifier_shift
        violation = None if valid else ("invariant" if not mechanism_same else "precondition")

    if unknown:
        # Missing target measurement makes the transfer unresolved irrespective of latent truth.
        return HiddenCase(family, semantic_high, valid, True, "unknown")
    return HiddenCase(family, semantic_high, valid, False, violation)


def _qoi(family: str) -> str:
    return {
        "queue": "stability",
        "feedback": "amplification",
        "cascade": "risk",
        "causal": "effect",
    }[family]


def _compile_visible_case(
    hidden: HiddenCase,
    index: int,
    ablate: frozenset[str],
) -> tuple[StructuralObject, StructuralObject, StructuralWitnessV2]:
    qoi = _qoi(hidden.family)
    source = StructuralObject(
        structure_id=f"source-{index}",
        domain=f"{hidden.family}-source",
        qoi=qoi,
        context_id=f"source-context-{index}",
        roles=(StructuralRole("x", "driver"), StructuralRole("y", "response")),
        relations=(StructuralRelation("x", "influences", "y"),),
        invariants=frozenset({"core_mechanism"}),
        boundaries=(BoundaryCondition("regime", "licensed"),),
        evidence_ids=(f"evidence:source:{index}",),
    )
    target = StructuralObject(
        structure_id=f"target-{index}",
        domain=f"{hidden.family}-target",
        qoi="other" if hidden.violation == "qoi" else qoi,
        context_id=f"target-context-{index}",
        roles=(StructuralRole("x", "driver"), StructuralRole("y", "response")),
        relations=(StructuralRelation("x", "influences", "y"),),
        invariants=frozenset(
            {"other_mechanism"} if hidden.violation == "invariant" else {"core_mechanism"}
        ),
        boundaries=(
            BoundaryCondition(
                "regime",
                "unlicensed" if hidden.violation == "boundary" else "licensed",
            ),
        ),
        evidence_ids=(f"evidence:target:{index}",),
    )

    obligations: list[TransferObligation] = []
    if "qoi" not in ablate:
        obligations.append(
            TransferObligation(
                "qoi",
                ObligationKind.QOI,
                qoi,
                qoi,
                evidence_ids=(f"evidence:qoi:{index}",),
            )
        )
    if "boundary" not in ablate:
        obligations.append(
            TransferObligation(
                "boundary",
                ObligationKind.BOUNDARY,
                "regime",
                "licensed",
                evidence_ids=(f"evidence:boundary:{index}",),
            )
        )
    if "invariant" not in ablate:
        obligations.append(
            TransferObligation(
                "invariant",
                ObligationKind.INVARIANT,
                "core_mechanism",
                "core_mechanism",
                evidence_ids=(f"evidence:invariant:{index}",),
            )
        )
    if "relation" not in ablate:
        obligations.append(
            TransferObligation(
                "relation",
                ObligationKind.RELATION,
                "x|influences|y|1",
                "x|influences|y|1",
                evidence_ids=(f"evidence:relation:{index}",),
            )
        )
    if "precondition" not in ablate:
        if hidden.unknown:
            status = ObligationStatus.UNKNOWN
            rationale = ""
        elif hidden.violation == "precondition":
            status = ObligationStatus.VIOLATED
            rationale = "precondition_false"
        else:
            status = ObligationStatus.SATISFIED
            rationale = "precondition_true"
        obligations.append(
            TransferObligation(
                "precondition",
                ObligationKind.PRECONDITION,
                "family_specific_applicability",
                "target",
                evidence_ids=(f"evidence:precondition:{index}",),
                status=status,
                rationale_code=rationale,
            )
        )
    if "direction" not in ablate:
        status = (
            ObligationStatus.VIOLATED
            if hidden.violation == "direction"
            else ObligationStatus.UNKNOWN
            if hidden.unknown
            else ObligationStatus.SATISFIED
        )
        obligations.append(
            TransferObligation(
                "direction",
                ObligationKind.PRECONDITION,
                "source_to_target_direction",
                "target",
                evidence_ids=(f"evidence:direction:{index}",),
                status=status,
                rationale_code=(
                    "direction_invalid"
                    if status is ObligationStatus.VIOLATED
                    else "direction_ok"
                    if status is ObligationStatus.SATISFIED
                    else ""
                ),
            )
        )

    witness = StructuralWitnessV2(
        witness_id=f"witness-{index}",
        source_structure_id=source.structure_id,
        target_structure_id=target.structure_id,
        source_context_id=source.context_id,
        target_context_id=target.context_id,
        qoi=qoi,
        role_mapping=(("x", "x"), ("y", "y")),
        obligations=tuple(obligations),
    )
    return source, target, witness


def _gold(hidden: HiddenCase) -> TransferDecision:
    if hidden.unknown:
        return TransferDecision.CANNOT_CHECK
    return TransferDecision.LICENSED if hidden.valid else TransferDecision.REJECTED


def run(seed: int = 20260812, n: int = 4000) -> dict[str, object]:
    """Run a known-world mechanistic ablation benchmark.

    Gold is produced before witness compilation by simple executable family rules. Visible
    structural facts are nevertheless compiled exactly, so this is a mechanism/conformance
    study rather than a natural-language witness-extraction result.
    """
    rng = random.Random(seed)
    cases = [_generate_hidden_case(rng, index) for index in range(n)]
    variants = {
        "full": frozenset(),
        "no_boundary": frozenset({"boundary"}),
        "no_precondition": frozenset({"precondition"}),
        "no_direction": frozenset({"direction"}),
        "no_qoi": frozenset({"qoi"}),
        "no_invariant": frozenset({"invariant"}),
        "no_relation": frozenset({"relation"}),
    }
    output: dict[str, object] = {
        "schema": "paper2.known_world.v1",
        "seed": seed,
        "n": n,
        "warning": (
            "Known-world mechanistic benchmark. Gold is generated by family-specific hidden "
            "rules, but structural facts are compiled exactly; this does not test natural-language "
            "witness extraction."
        ),
        "ablation_semantics": (
            "assess_transfer_v2 derives a coverage requirement from the SOURCE object, so the "
            "qoi/invariant/relation arms cannot license at all: removing one of those "
            "obligations leaves source content unasked, and no case in those arms is LICENSED. "
            "Their valid_license=0.0 and false_license=0.0 are therefore true by construction "
            "and say nothing about whether the obligation kind matters; the licensed stratum is "
            "simply absent. Those arms do stay discriminative on the REJECTED stratum, because a "
            "demonstrated violation is decisive ahead of the coverage check: against 1749 gold "
            "rejections, no_qoi recovers 1629 and no_invariant 1501 (each losing exactly the "
            "violations only its own obligation could detect), while no_relation recovers all "
            "1749 because this generator never perturbs the relation. Read those arms on "
            "rejection recovery, not on exact3, whose drop is dominated by the missing licenses. "
            "boundary/precondition/direction are not part of coverage, so those arms remain "
            "full three-way comparisons against 'full'."
        ),
        "provenance": (
            "Regenerated after the assess_transfer_v2 zero-obligation coverage fix, which "
            "replaced a fail-open that licensed on an empty obligation list. The values recorded "
            "under PR #491 (scoreboard merge_sha 496edc5e) are preserved in git history and are "
            "NOT reproducible from this script; re-running the UNMODIFIED script at the parent "
            "commit already failed to reproduce them, so part of that difference predates this "
            "fix. The 'full' arm and family_exact3 are unchanged by the fix."
        ),
    }

    rejected_count = sum(_gold(case) is TransferDecision.REJECTED for case in cases)
    licensed_count = sum(_gold(case) is TransferDecision.LICENSED for case in cases)
    unknown_count = sum(_gold(case) is TransferDecision.CANNOT_CHECK for case in cases)

    for name, ablation in variants.items():
        predictions: list[TransferDecision] = []
        for index, hidden in enumerate(cases):
            source, target, witness = _compile_visible_case(hidden, index, ablation)
            predictions.append(assess_transfer_v2(source, target, witness).decision)
        output[name] = {
            "exact3": sum(
                prediction is _gold(hidden)
                for prediction, hidden in zip(predictions, cases)
            )
            / n,
            "false_license": sum(
                prediction is TransferDecision.LICENSED
                and _gold(hidden) is TransferDecision.REJECTED
                for prediction, hidden in zip(predictions, cases)
            )
            / max(1, rejected_count),
            "valid_license": sum(
                prediction is TransferDecision.LICENSED
                and _gold(hidden) is TransferDecision.LICENSED
                for prediction, hidden in zip(predictions, cases)
            )
            / max(1, licensed_count),
            "unknown_abstain": sum(
                prediction is TransferDecision.CANNOT_CHECK
                and _gold(hidden) is TransferDecision.CANNOT_CHECK
                for prediction, hidden in zip(predictions, cases)
            )
            / max(1, unknown_count),
        }

    surface_predictions = [
        TransferDecision.LICENSED if hidden.semantic_high else TransferDecision.REJECTED
        for hidden in cases
    ]
    output["surface_semantic"] = {
        "exact3": sum(
            prediction is _gold(hidden)
            for prediction, hidden in zip(surface_predictions, cases)
        )
        / n,
        "false_license": sum(
            prediction is TransferDecision.LICENSED
            and _gold(hidden) is TransferDecision.REJECTED
            for prediction, hidden in zip(surface_predictions, cases)
        )
        / max(1, rejected_count),
        "valid_license": sum(
            prediction is TransferDecision.LICENSED
            and _gold(hidden) is TransferDecision.LICENSED
            for prediction, hidden in zip(surface_predictions, cases)
        )
        / max(1, licensed_count),
        "unknown_abstain": 0.0,
    }

    family_correct: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for index, hidden in enumerate(cases):
        source, target, witness = _compile_visible_case(hidden, index, frozenset())
        prediction = assess_transfer_v2(source, target, witness).decision
        family_correct[hidden.family][1] += 1
        family_correct[hidden.family][0] += int(prediction is _gold(hidden))
    output["family_exact3"] = {
        family: correct / total
        for family, (correct, total) in family_correct.items()
    }
    return output


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
