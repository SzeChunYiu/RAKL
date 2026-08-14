"""Frozen benchmark for the typed-refusal transfer (#609 follow-on).

Executes the protocol in
``research/paper2_causal_transport_absorption_v1/PROTOCOL.json`` against the two
challengers and emits a receipt. Thresholds are read from the frozen protocol
shape and are not adjustable here.

The oracle is deliberately independent of the code under test: it brute-forces
the space of admissible witnesses and calls the REAL ``assess_transfer``, while
the criterion under test is computed by ``transfer_impossibility``. Agreement
between the two is what gate G4 measures.

Proposal-only. Grants no scientific or promotion authority.
"""

from __future__ import annotations

import itertools
import json
import random
import sys

from rakl.structural_transfer import assess_transfer
from rakl.structural_types import (
    BoundaryCondition,
    StructuralObject,
    StructuralRelation,
    StructuralRole,
    StructuralWitness,
    TransferDecision,
)
from rakl.transfer_impossibility import (
    RefusalKind,
    TargetDeclaration,
    classify_refusal,
    classify_refusal_faithful_import,
    exists_licensing_role_mapping,
    structural_obstructions,
)

#: Ceiling on the brute-force oracle. If a case needs more injective mappings
#: than this, the oracle reports CANNOT_CHECK rather than a wrong answer.
ORACLE_MAX_MAPPINGS = 200_000


def make_object(
    structure_id: str,
    *,
    qoi: str,
    roles: tuple[str, ...],
    relations: tuple[tuple[str, str, str], ...] = (),
    invariants: frozenset[str] = frozenset(),
    boundaries: tuple[tuple[str, str], ...] = (),
) -> StructuralObject:
    return StructuralObject(
        structure_id=structure_id,
        domain="benchmark",
        qoi=qoi,
        context_id=f"ctx-{structure_id}",
        roles=tuple(StructuralRole(role_id=r, kind="generic") for r in roles),
        relations=tuple(
            StructuralRelation(source_role=a, relation_type=t, target_role=b)
            for a, t, b in relations
        ),
        invariants=invariants,
        boundaries=tuple(BoundaryCondition(key=k, value=v) for k, v in boundaries),
        evidence_ids=(f"ev-{structure_id}",),
    )


def make_witness(
    source: StructuralObject,
    target: StructuralObject,
    role_mapping: tuple[tuple[str, str], ...],
    *,
    preserved_invariants: frozenset[str] | None = None,
    required_target_boundaries: tuple[tuple[str, str], ...] = (),
    witness_id: str = "w",
) -> StructuralWitness:
    return StructuralWitness(
        witness_id=witness_id,
        source_structure_id=source.structure_id,
        target_structure_id=target.structure_id,
        role_mapping=role_mapping,
        preserved_invariants=(
            source.invariants if preserved_invariants is None else preserved_invariants
        ),
        non_preserved_properties=frozenset(),
        required_target_boundaries=tuple(
            BoundaryCondition(key=k, value=v) for k, v in required_target_boundaries
        ),
        evidence_ids=("ev-witness",),
    )


def brute_force_licensable(
    source: StructuralObject, target: StructuralObject
) -> bool | None:
    """Independent oracle: does ANY admissible witness license this transfer?

    Enumerates every injective role mapping and, for each, both non-dominated
    invariant declarations. Calls the real gate. Returns None when the space
    exceeds ``ORACLE_MAX_MAPPINGS`` (CANNOT_CHECK, never False).
    """

    source_roles = sorted(source.role_ids)
    target_roles = sorted(target.role_ids)
    if len(source_roles) > len(target_roles):
        return False

    total = 1
    for k in range(len(source_roles)):
        total *= len(target_roles) - k
        if total > ORACLE_MAX_MAPPINGS:
            return None

    declarations = {
        source.invariants,
        frozenset(source.invariants & target.invariants),
    }
    for combo in itertools.permutations(target_roles, len(source_roles)):
        mapping = tuple(zip(source_roles, combo))
        for declared in declarations:
            witness = make_witness(
                source, target, mapping, preserved_invariants=declared
            )
            if assess_transfer(source, target, witness).decision is TransferDecision.LICENSED:
                return True
    return False


def build_arms() -> list[dict]:
    arms: list[dict] = []

    # ---- ARM-1: a licensing witness exists under a DIFFERENT role mapping ----
    src = make_object("s1", qoi="Q", roles=("a", "b"), relations=(("a", "causes", "b"),))
    tgt = make_object("t1", qoi="Q", roles=("x", "y"), relations=(("x", "causes", "y"),))
    arms.append(
        {
            "arm": "ARM-1_REPAIRABLE_ROLE_MAP",
            "source": src,
            "target": tgt,
            # deliberately reversed: maps a->y, b->x
            "witness": make_witness(src, tgt, (("a", "y"), ("b", "x"))),
            "closed_world": True,
            "ground_truth": "MERELY_UNLICENSED",
            "budget": None,
        }
    )

    # ---- ARM-2: repairable evidence defect ----
    src2 = make_object("s2", qoi="Q", roles=("a",))
    tgt2 = make_object("t2", qoi="Q", roles=("x",))
    try:
        bad = StructuralWitness(
            witness_id="w2",
            source_structure_id="s2",
            target_structure_id="t2",
            role_mapping=(("a", "x"),),
            preserved_invariants=frozenset(),
            non_preserved_properties=frozenset(),
            required_target_boundaries=(),
            evidence_ids=(),
        )
        arms.append(
            {
                "arm": "ARM-2_REPAIRABLE_EVIDENCE",
                "source": src2,
                "target": tgt2,
                "witness": bad,
                "closed_world": True,
                "ground_truth": "MERELY_UNLICENSED",
                "budget": None,
            }
        )
    except ValueError as exc:
        arms.append(
            {
                "arm": "ARM-2_REPAIRABLE_EVIDENCE",
                "status": "CANNOT_CONSTRUCT",
                "detail": (
                    "StructuralWitness.__post_init__ rejects empty evidence_ids, so an "
                    "evidence-free witness is not an admissible presentation and the "
                    "'missing_witness_evidence' branch of assess_transfer is unreachable "
                    f"through the public constructor. Constructor error: {exc}"
                ),
            }
        )

    # ---- ARM-3: repairable boundary declaration ----
    src3 = make_object("s3", qoi="Q", roles=("a",))
    tgt3 = make_object("t3", qoi="Q", roles=("x",), boundaries=(("regime", "low"),))
    arms.append(
        {
            "arm": "ARM-3_REPAIRABLE_BOUNDARY",
            "source": src3,
            "target": tgt3,
            "witness": make_witness(
                src3, tgt3, (("a", "x"),), required_target_boundaries=(("regime", "high"),)
            ),
            "closed_world": True,
            "ground_truth": "MERELY_UNLICENSED",
            "budget": None,
        }
    )

    # ---- ARM-4: target genuinely lacks a required relation ----
    src4 = make_object("s4", qoi="Q", roles=("a", "b"), relations=(("a", "causes", "b"),))
    tgt4 = make_object("t4", qoi="Q", roles=("x", "y"), relations=(("x", "correlates", "y"),))
    arms.append(
        {
            "arm": "ARM-4_STRUCTURAL_RELATION",
            "source": src4,
            "target": tgt4,
            "witness": make_witness(src4, tgt4, (("a", "x"), ("b", "y"))),
            "closed_world": True,
            "ground_truth": "CERTIFIABLY_IMPOSSIBLE",
            "budget": None,
        }
    )

    # ---- ARM-5: QoI mismatch ----
    src5 = make_object("s5", qoi="Q", roles=("a",))
    tgt5 = make_object("t5", qoi="OTHER", roles=("x",))
    arms.append(
        {
            "arm": "ARM-5_STRUCTURAL_QOI",
            "source": src5,
            "target": tgt5,
            "witness": make_witness(src5, tgt5, (("a", "x"),)),
            "closed_world": True,
            "ground_truth": "CERTIFIABLY_IMPOSSIBLE",
            "budget": None,
        }
    )

    # ---- ARM-6: target missing a source invariant ----
    src6 = make_object("s6", qoi="Q", roles=("a",), invariants=frozenset({"energy"}))
    tgt6 = make_object("t6", qoi="Q", roles=("x",), invariants=frozenset())
    arms.append(
        {
            "arm": "ARM-6_STRUCTURAL_INVARIANT",
            "source": src6,
            "target": tgt6,
            "witness": make_witness(src6, tgt6, (("a", "x"),)),
            "closed_world": True,
            "ground_truth": "CERTIFIABLY_IMPOSSIBLE",
            "budget": None,
        }
    )

    # ---- ARM-7: same structural gap as ARM-4, but open-world target ----
    arms.append(
        {
            "arm": "ARM-7_OPEN_WORLD",
            "source": src4,
            "target": tgt4,
            "witness": make_witness(src4, tgt4, (("a", "x"), ("b", "y"))),
            "closed_world": False,
            "ground_truth": "MERELY_UNLICENSED",
            "budget": None,
        }
    )

    # ---- ARM-8: genuinely impossible, closed-world, but budget exhausted ----
    big_src_roles = tuple(f"a{i}" for i in range(6))
    big_tgt_roles = tuple(f"x{i}" for i in range(7))
    tgt8 = make_object(
        "t8",
        qoi="Q",
        roles=big_tgt_roles,
        relations=tuple(
            (big_tgt_roles[i], "causes", big_tgt_roles[j])
            for i in range(len(big_tgt_roles))
            for j in range(len(big_tgt_roles))
            if i != j
        )
        + (("x0", "extra", "x1"),),
    )
    # genuinely impossible: a source relation type absent from the target
    src8 = make_object(
        "s8",
        qoi="Q",
        roles=big_src_roles,
        relations=tuple(
            (big_src_roles[i], "causes", big_src_roles[i + 1])
            for i in range(len(big_src_roles) - 1)
        )
        + (("a0", "absent_type", "a5"),),
    )
    arms.append(
        {
            "arm": "ARM-8_BUDGET_EXHAUSTION",
            "source": src8,
            "target": tgt8,
            "witness": make_witness(
                src8, tgt8, tuple((big_src_roles[i], big_tgt_roles[i]) for i in range(6))
            ),
            "closed_world": True,
            "ground_truth": "MERELY_UNLICENSED",
            # deliberately tiny so the fail-closed rule is exercised
            "budget": 5,
        }
    )

    return arms


def run_arms() -> list[dict]:
    results = []
    for arm in build_arms():
        if arm.get("status") == "CANNOT_CONSTRUCT":
            results.append(
                {
                    "arm": arm["arm"],
                    "status": "CANNOT_CONSTRUCT",
                    "detail": arm["detail"],
                }
            )
            continue

        source, target, witness = arm["source"], arm["target"], arm["witness"]
        budget = arm["budget"]
        kwargs = {} if budget is None else {"max_search_nodes": budget}

        declaration = TargetDeclaration(
            target_structure_id=target.structure_id,
            closed_world=arm["closed_world"],
            declared_by="benchmark" if arm["closed_world"] else "",
        )

        base = assess_transfer(source, target, witness)
        challenger_a = classify_refusal_faithful_import(source, target, witness)
        challenger_b = classify_refusal(
            source, target, witness, target_declaration=declaration, **kwargs
        )

        oracle = brute_force_licensable(source, target)
        # Full-budget criterion, used only to record whether the case really is
        # impossible -- never to license ARM-8's verdict.
        cert_full, completed_full = structural_obstructions(source, target)

        results.append(
            {
                "arm": arm["arm"],
                "status": "RUN",
                "ground_truth": arm["ground_truth"],
                "base_decision": base.decision.value,
                "base_reasons": list(base.reasons),
                "challenger_A": challenger_a.kind.value,
                "challenger_B": challenger_b.kind.value,
                "B_reasons": list(challenger_b.reasons),
                "B_search_completed": challenger_b.search_completed,
                "B_search_nodes": challenger_b.search_nodes,
                "B_certificate": (
                    None
                    if challenger_b.certificate is None
                    else {
                        "failed_criteria": list(challenger_b.certificate.failed_criteria),
                        "missing_invariants": list(
                            challenger_b.certificate.missing_invariants
                        ),
                        "unmatchable_relation_types": list(
                            challenger_b.certificate.unmatchable_relation_types
                        ),
                        "role_cardinality_obstruction": challenger_b.certificate.role_cardinality_obstruction,
                    }
                ),
                "oracle_licensable": oracle,
                "criterion_licensable_full_budget": (
                    None if not completed_full else cert_full.is_empty
                ),
                "A_correct": challenger_a.kind.value == arm["ground_truth"],
                "B_correct": challenger_b.kind.value == arm["ground_truth"],
            }
        )
    return results


def run_proposition_sweep(seed: int = 20260814, n: int = 600) -> dict:
    """G4: criterion S1/S2/S3 vs the brute-force witness oracle, randomised."""

    rng = random.Random(seed)
    relation_types = ["causes", "correlates", "inhibits"]
    invariant_pool = ["energy", "mass", "charge"]
    disagreements = []
    checked = 0
    skipped = 0

    for i in range(n):
        n_src = rng.randint(1, 3)
        n_tgt = rng.randint(1, 4)
        src_roles = tuple(f"a{k}" for k in range(n_src))
        tgt_roles = tuple(f"x{k}" for k in range(n_tgt))

        def rand_relations(roles):
            out = set()
            for _ in range(rng.randint(0, 3)):
                if len(roles) < 2:
                    break
                a, b = rng.sample(list(roles), 2)
                out.add((a, rng.choice(relation_types), b))
            return tuple(sorted(out))

        qoi_src = rng.choice(["Q", "Q2"])
        qoi_tgt = rng.choice(["Q", "Q2"])
        source = make_object(
            f"src{i}",
            qoi=qoi_src,
            roles=src_roles,
            relations=rand_relations(src_roles),
            invariants=frozenset(rng.sample(invariant_pool, rng.randint(0, 2))),
        )
        target = make_object(
            f"tgt{i}",
            qoi=qoi_tgt,
            roles=tgt_roles,
            relations=rand_relations(tgt_roles),
            invariants=frozenset(rng.sample(invariant_pool, rng.randint(0, 3))),
        )

        oracle = brute_force_licensable(source, target)
        certificate, completed = structural_obstructions(source, target)
        if oracle is None or not completed:
            skipped += 1
            continue
        checked += 1
        if certificate.is_empty != oracle:
            disagreements.append(
                {
                    "index": i,
                    "oracle_licensable": oracle,
                    "criterion_licensable": certificate.is_empty,
                    "failed_criteria": list(certificate.failed_criteria),
                    "source_roles": list(src_roles),
                    "target_roles": list(tgt_roles),
                }
            )

    return {
        "seed": seed,
        "cases_generated": n,
        "cases_checked": checked,
        "cases_skipped_cannot_check": skipped,
        "disagreements": disagreements,
        "agreement": not disagreements,
    }


def run_planted_known_answer_sweep(seed: int = 20260814, n: int = 200) -> dict:
    """G4b: planted cases whose ground truth is known BY CONSTRUCTION.

    The randomised sweep in :func:`run_proposition_sweep` compares two
    implementations against each other. Agreement there is necessary but weak:
    it cannot distinguish "both correct" from "both wrong the same way", and
    its input distribution under-samples the one stratum that actually
    exercises the injective-mapping search -- namely S3 true reachable ONLY via
    a non-canonical mapping.

    This sweep plants the answer instead of asking an oracle for it:

    * PASS cases embed a known injective phi and build the target as the
      phi-image of the source relations, so a licensing mapping provably
      exists. Cases where the canonical sorted-order mapping ALSO works are
      rejected, so every retained PASS case requires the search to find a
      non-obvious mapping.
    * FAIL cases give the source a relation whose type appears nowhere in the
      target, so no mapping whatsoever can preserve it.

    The FAIL direction is sound but cheap -- the type check settles it without
    the search. The search-exercising evidence for the negative direction comes
    from the randomised oracle cross-check, not from here.
    """

    rng = random.Random(seed + 1)
    relation_types = ["causes", "correlates", "inhibits", "mediates"]
    pass_cases = 0
    pass_failures = []
    fail_cases = 0
    fail_failures = []
    rejected_canonical = 0

    for i in range(n):
        k = rng.randint(2, 4)
        m = k + rng.randint(0, 2)
        src_roles = tuple(f"a{j}" for j in range(k))
        tgt_roles = tuple(f"x{j}" for j in range(m))

        relations = set()
        for _ in range(rng.randint(1, 4)):
            a, b = rng.sample(list(src_roles), 2)
            relations.add((a, rng.choice(relation_types), b))
        relations = tuple(sorted(relations))

        image = list(tgt_roles)
        rng.shuffle(image)
        phi = dict(zip(src_roles, image[:k]))
        canonical = dict(zip(sorted(src_roles), sorted(tgt_roles)))
        if phi == canonical:
            rejected_canonical += 1
            continue

        mapped = tuple(
            sorted({(phi[a], t, phi[b]) for a, t, b in relations})
        )
        source = make_object(f"psrc{i}", qoi="Q", roles=src_roles, relations=relations)
        target = make_object(f"ptgt{i}", qoi="Q", roles=tgt_roles, relations=mapped)

        # Retain only cases where the canonical mapping does NOT work, so the
        # search has to do real work.
        canonical_sigs = {
            (canonical[a], t, canonical[b], True) for a, t, b in relations
        }
        target_sigs = {r.signature for r in target.relations}
        if canonical_sigs <= target_sigs:
            rejected_canonical += 1
            continue

        result, _ = exists_licensing_role_mapping(source, target)
        pass_cases += 1
        if result is not True:
            pass_failures.append({"index": i, "got": result, "expected": True})

        # Mutant: a source relation type that appears nowhere in the target.
        mutant_source = make_object(
            f"msrc{i}",
            qoi="Q",
            roles=src_roles,
            relations=relations + ((src_roles[0], "planted_absent_type", src_roles[1]),),
        )
        mutant_result, _ = exists_licensing_role_mapping(mutant_source, target)
        fail_cases += 1
        if mutant_result is not False:
            fail_failures.append({"index": i, "got": mutant_result, "expected": False})

    return {
        "seed": seed,
        "planted_pass_cases": pass_cases,
        "planted_pass_failures": pass_failures,
        "planted_fail_cases": fail_cases,
        "planted_fail_failures": fail_failures,
        "rejected_because_canonical_mapping_sufficed": rejected_canonical,
        "agreement": not pass_failures and not fail_failures,
    }


def measure_sweep_strata(seed: int = 20260814, n: int = 600) -> dict:
    """Coverage audit for the randomised sweep.

    Reports how many generated cases actually exercise S3, and how many fall in
    the discriminating stratum where S3 is true ONLY via a non-canonical
    mapping. Recorded so that a reader can see what the 600/600 agreement in
    :func:`run_proposition_sweep` does and does not cover.
    """

    rng = random.Random(seed)
    relation_types = ["causes", "correlates", "inhibits"]
    invariant_pool = ["energy", "mass", "charge"]
    with_relations = 0
    s3_true = 0
    discriminating = 0

    for i in range(n):
        n_src = rng.randint(1, 3)
        n_tgt = rng.randint(1, 4)
        src_roles = tuple(f"a{k}" for k in range(n_src))
        tgt_roles = tuple(f"x{k}" for k in range(n_tgt))

        def rand_relations(roles):
            out = set()
            for _ in range(rng.randint(0, 3)):
                if len(roles) < 2:
                    break
                a, b = rng.sample(list(roles), 2)
                out.add((a, rng.choice(relation_types), b))
            return tuple(sorted(out))

        qoi_src = rng.choice(["Q", "Q2"])
        qoi_tgt = rng.choice(["Q", "Q2"])
        source = make_object(
            f"src{i}", qoi=qoi_src, roles=src_roles, relations=rand_relations(src_roles),
            invariants=frozenset(rng.sample(invariant_pool, rng.randint(0, 2))),
        )
        target = make_object(
            f"tgt{i}", qoi=qoi_tgt, roles=tgt_roles, relations=rand_relations(tgt_roles),
            invariants=frozenset(rng.sample(invariant_pool, rng.randint(0, 3))),
        )
        if source.relations:
            with_relations += 1
        result, _ = exists_licensing_role_mapping(source, target)
        if result is True and source.relations:
            s3_true += 1
            a_roles = sorted(source.role_ids)
            b_roles = sorted(target.role_ids)
            target_sigs = {r.signature for r in target.relations}
            if len(a_roles) <= len(b_roles):
                canonical = dict(zip(a_roles, b_roles))
                if not all(
                    (canonical[r.source_role], r.relation_type, canonical[r.target_role], r.directed)
                    in target_sigs
                    for r in source.relations
                ):
                    discriminating += 1

    return {
        "cases": n,
        "cases_with_source_relations": with_relations,
        "s3_true_with_relations": s3_true,
        "discriminating_s3_true_only_via_non_canonical_mapping": discriminating,
    }


def evaluate_gates(arm_results: list[dict], sweep: dict, planted: dict) -> dict:
    run = [r for r in arm_results if r["status"] == "RUN"]
    weak_arms = {
        "ARM-1_REPAIRABLE_ROLE_MAP",
        "ARM-3_REPAIRABLE_BOUNDARY",
        "ARM-7_OPEN_WORLD",
        "ARM-8_BUDGET_EXHAUSTION",
    }
    strong_arms = {
        "ARM-4_STRUCTURAL_RELATION",
        "ARM-5_STRUCTURAL_QOI",
        "ARM-6_STRUCTURAL_INVARIANT",
    }

    false_certificates = [
        r["arm"]
        for r in run
        if r["arm"] in weak_arms
        and r["challenger_B"] == RefusalKind.CERTIFIABLY_IMPOSSIBLE.value
    ]
    strong_fired = [
        r["arm"]
        for r in run
        if r["arm"] in strong_arms
        and r["challenger_B"] == RefusalKind.CERTIFIABLY_IMPOSSIBLE.value
    ]
    strong_present = [r["arm"] for r in run if r["arm"] in strong_arms]
    separations = [r["arm"] for r in run if r["challenger_A"] != r["challenger_B"]]
    a_false_certificates = [
        r["arm"]
        for r in run
        if r["arm"] in weak_arms
        and r["challenger_A"] == RefusalKind.CERTIFIABLY_IMPOSSIBLE.value
    ]

    gates = {
        "G1_NO_FALSE_CERTIFICATE": {
            "pass": not false_certificates,
            "false_certificate_arms": false_certificates,
        },
        "G2_NOT_VACUOUS": {
            "pass": bool(strong_present) and len(strong_fired) == len(strong_present),
            "fired": strong_fired,
            "expected": strong_present,
        },
        "G3_SEPARATION": {
            "pass": bool(separations),
            "separating_arms": separations,
        },
        "G4_PROPOSITION_HOLDS": {
            "pass": sweep["agreement"] and sweep["cases_checked"] > 0,
            "cases_checked": sweep["cases_checked"],
            "disagreements": sweep["disagreements"],
        },
    }
    gates["G4b_PLANTED_KNOWN_ANSWER"] = {
        "pass": planted["agreement"]
        and planted["planted_pass_cases"] > 0
        and planted["planted_fail_cases"] > 0,
        "planted_pass_cases": planted["planted_pass_cases"],
        "planted_fail_cases": planted["planted_fail_cases"],
        "planted_pass_failures": planted["planted_pass_failures"],
        "planted_fail_failures": planted["planted_fail_failures"],
    }
    gates["ALL_PASS"] = all(g["pass"] for g in gates.values() if isinstance(g, dict))
    gates["control_arm_A_false_certificates"] = a_false_certificates
    return gates


def main() -> int:
    arm_results = run_arms()
    sweep = run_proposition_sweep()
    planted = run_planted_known_answer_sweep()
    strata = measure_sweep_strata()
    gates = evaluate_gates(arm_results, sweep, planted)
    receipt = {
        "schema_version": "paper2-typed-refusal-receipt-v1",
        "protocol": "research/paper2_causal_transport_absorption_v1/PROTOCOL.json",
        "grants_scientific_authority": False,
        "grants_promotion_authority": False,
        "arms": arm_results,
        "proposition_sweep": sweep,
        "proposition_sweep_strata": strata,
        "planted_known_answer_sweep": planted,
        "hard_gates": gates,
    }
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if gates["ALL_PASS"] else 1


if __name__ == "__main__":
    sys.exit(main())
