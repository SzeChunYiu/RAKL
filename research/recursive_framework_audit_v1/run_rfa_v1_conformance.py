"""Execute the frozen RFA v1 known-world conformance benchmark (deterministic).

Runs every frozen decide case through the production module AND the vendored
handoff reference, executes mechanical versions of structural checks S01–S08,
and writes ``RFA_V1_CONFORMANCE_RESULT.json`` (integers/booleans/strings only
— no floats, so exact reproduction is Python-version independent).

Conformance is instrument evidence only.  It is NOT utility evidence for the
recursive formulation principle; the RFC-v1 utility benchmark must be
separately re-frozen before any utility execution.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

LANE = Path(__file__).resolve().parent
ROOT = LANE.parents[1]
BENCHMARK = LANE / "RFA_V1_FROZEN_BENCHMARK.json"
REFERENCE = LANE / "reference" / "recursive_framework_audit_reference.py"
RESULT = LANE / "RFA_V1_CONFORMANCE_RESULT.json"

sys.path.insert(0, str(ROOT / "src"))

from rakl.recursive_framework_audit import (  # noqa: E402
    AncestorChallenge,
    AuditCoordinate,
    AuditNode,
    AuditResidual,
    AtomicityReceipt,
    FrameworkCandidate,
    ProblemStatement,
    QuestionFormulationCandidate,
    RecursiveAuditProjection,
    audit_before_commit,
    decide,
    request_self_rakl_escalation,
)
from rakl.self_evolution_controller import CURRENT_SELF_EVOLUTION_CONTROLLER  # noqa: E402

FLAG_FIELDS = (
    "split_required",
    "merge_required",
    "parent_challenge_supported",
    "distinct_local_repair_families_failed",
    "evaluator_invalid",
    "external_trust_root",
    "resource_bound",
)

PINNED_DIVERGENCES = {
    "H07_duplicate_causes_dedup": (
        "reference checks len(causes)==1 literally; a duplicated single cause bypasses "
        "its single-cause branch. Production canonicalizes duplicates at AuditResidual "
        "construction (repeated identical cause is one responsibility level), so the "
        "single-cause branch fires and matches the frozen expected action."
    ),
}


def _git_blob_sha(path: Path) -> str:
    content = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(content) + content).hexdigest()


def _load_reference():
    spec = importlib.util.spec_from_file_location("rfa_reference", REFERENCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _unify(case: dict) -> dict:
    residual = dict(case.get("residual", {}))
    if "residual_causes" in case:
        residual["plausible_causes"] = case["residual_causes"]
    for key, value in case.get("residual_flags", {}).items():
        residual[key] = value
    residual.setdefault("plausible_causes", [])
    return residual


def execute() -> dict:
    benchmark = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    reference = _load_reference()

    grouped: list[tuple[str, list[dict]]] = [
        ("known_world", benchmark["known_world_families"]),
        ("reference_conformance", benchmark["reference_conformance_cases"]),
        ("hostile_priority", benchmark["hostile_priority_cases"]),
    ]
    case_results: list[dict] = []
    failures: list[str] = []
    divergences: list[dict] = []

    for group, entries in grouped:
        for case in entries:
            case_id = case["case_id"]
            node_spec = case["node"]
            residual_spec = _unify(case)
            expected = case["expected_action"]

            node = AuditNode(
                closure_coordinates_pass=node_spec["closure_coordinates_pass"],
                material_open_residual=node_spec["material_open_residual"],
            )
            residual = AuditResidual(
                plausible_causes=tuple(AuditCoordinate(c) for c in residual_spec["plausible_causes"]),
                **{k: residual_spec[k] for k in FLAG_FIELDS if k in residual_spec},
            )
            decision = decide(node, residual)
            production = decision.action.value

            canonical_causes = list(dict.fromkeys(residual_spec["plausible_causes"]))
            ref_node = reference.Node(
                closure_coordinates_pass=node_spec["closure_coordinates_pass"],
                material_open_residual=node_spec["material_open_residual"],
            )
            ref_canonical = reference.decide(
                ref_node,
                reference.Residual(
                    plausible_causes=tuple(reference.Coordinate(c) for c in canonical_causes),
                    **{k: residual_spec[k] for k in FLAG_FIELDS if k in residual_spec},
                ),
            ).action.value
            ref_raw = reference.decide(
                ref_node,
                reference.Residual(
                    plausible_causes=tuple(reference.Coordinate(c) for c in residual_spec["plausible_causes"]),
                    **{k: residual_spec[k] for k in FLAG_FIELDS if k in residual_spec},
                ),
            ).action.value

            matched_expected = production == expected
            matched_canonical = production == ref_canonical
            if not matched_expected:
                failures.append(f"{case_id}: production {production} != expected {expected}")
            if not matched_canonical:
                failures.append(f"{case_id}: production {production} != canonical reference {ref_canonical}")
            if ref_raw != ref_canonical:
                if case_id not in PINNED_DIVERGENCES:
                    failures.append(f"{case_id}: unpinned reference raw/canonical divergence")
                divergences.append(
                    {
                        "case_id": case_id,
                        "reason": PINNED_DIVERGENCES[case_id],
                        "reference_raw_action": ref_raw,
                        "reference_canonical_action": ref_canonical,
                        "production_action": production,
                    }
                )

            case_results.append(
                {
                    "case_id": case_id,
                    "group": group,
                    "expected_action": expected,
                    "production_action": production,
                    "reference_canonical_action": ref_canonical,
                    "reference_raw_action": ref_raw,
                    "matched_expected": matched_expected,
                    "matched_canonical_reference": matched_canonical,
                }
            )

    structural_checks = _structural_checks(failures)

    result = {
        "schema_version": "rakl-rfa-v1-conformance-result",
        "status": (
            "KNOWN_WORLD_CONFORMANCE_PASS"
            if not failures and all(check["passed"] for check in structural_checks)
            else "KNOWN_WORLD_CONFORMANCE_FAIL"
        ),
        "executed_at": "2026-08-15",
        "benchmark_file": "RFA_V1_FROZEN_BENCHMARK.json",
        "benchmark_git_blob_sha": _git_blob_sha(BENCHMARK),
        "production_module": "src/rakl/recursive_framework_audit.py",
        "reference_module": "reference/recursive_framework_audit_reference.py",
        "case_counts": {
            "known_world": sum(1 for c in case_results if c["group"] == "known_world"),
            "reference_conformance": sum(1 for c in case_results if c["group"] == "reference_conformance"),
            "hostile_priority": sum(1 for c in case_results if c["group"] == "hostile_priority"),
            "total": len(case_results),
            "failures": len(failures),
        },
        "cases": case_results,
        "structural_checks": structural_checks,
        "pinned_reference_divergences": divergences,
        "failures": failures,
        "grants_scientific_authority": False,
        "grants_method_promotion_authority": False,
        "float_policy": (
            "This result contains no floating-point numbers (integers, booleans, "
            "strings, and nested structures thereof only), so exact reproduction "
            "is independent of builtin sum() semantics across Python versions."
        ),
        "non_claims": [
            "Known-world conformance is not fresh-task evidence.",
            "No utility or superiority claim over any parent arm.",
            "No scientific authority, method-promotion authority, or publication authority.",
        ],
    }
    return result


def _structural_checks(failures: list[str]) -> list[dict]:
    checks: list[dict] = []

    def record(check_id: str, passed: bool, detail: str = "") -> None:
        checks.append({"check_id": check_id, "passed": passed, "detail": detail})

    # S01 — atomicity terminal is provisional-at-cutoff only.
    s01 = False
    try:
        receipt = AtomicityReceipt("t", "sf", "EV-1", "2026-08-15")
        s01 = receipt.terminal == "PROVISIONALLY_ATOMIC_AT_REGISTERED_CUTOFF"
        try:
            AtomicityReceipt("t", "sf", "EV-1", "2026-08-15", terminal="ATOM_PROVEN_FOREVER")
        except ValueError:
            s01 = s01 and True
        else:
            s01 = False
    except Exception:
        s01 = False
    record("S01_atomicity_receipt_terminal", s01)

    # S02 — atomicity indexed by target/split-family/evaluator/cutoff.
    base = dict(target_id="atom-x", split_family="regime-split", evaluator_epoch="EV-1", evidence_cutoff="cutoff")
    receipt_a = AtomicityReceipt(**base)
    receipt_b = AtomicityReceipt(**{**base, "evaluator_epoch": "EV-2"})
    record(
        "S02_atomicity_indexed",
        receipt_a != receipt_b
        and not receipt_a.valid_for("atom-x", "regime-split", "EV-2", "cutoff")
        and receipt_a.valid_for("atom-x", "regime-split", "EV-1", "cutoff"),
    )

    # S03 — supersession stales descendants, preserves evidence.
    challenge = AncestorChallenge(
        ancestor_fiber_id="fiber-parent",
        challenge_evidence_digest="digest-abc",
        failed_local_repair_families=("interface-repair", "measurement-revision"),
        dependent_descendant_ids=("fiber-child-1", "fiber-child-2"),
    )
    registered = challenge.with_supersession()
    record(
        "S03_ancestor_supersession_stales_descendants",
        registered.descendant_closure_stale("fiber-child-1")
        and registered.descendant_closure_stale("fiber-child-2")
        and not registered.descendant_closure_stale("fiber-unrelated")
        and registered.challenge_evidence_digest == "digest-abc",
    )

    # S04 — evaluator change closes the epoch; no cross-epoch comparison.
    epoch_1 = RecursiveAuditProjection(fiber_id="f", evaluator_epoch="EV-1")
    epoch_2 = RecursiveAuditProjection(fiber_id="f", evaluator_epoch="EV-2")
    record(
        "S04_evaluator_change_closes_epoch",
        epoch_1.epoch_id != epoch_2.epoch_id
        and epoch_1.same_epoch(epoch_2) is False
        and epoch_1.same_epoch(epoch_1) is True
        and RecursiveAuditProjection(fiber_id="f").same_epoch(epoch_1) is None,
    )

    # S05 — non-sovereignty on every emitted decision.
    node = AuditNode(closure_coordinates_pass=False, material_open_residual=True)
    residuals = (
        AuditResidual(plausible_causes=(AuditCoordinate.QUESTION,)),
        AuditResidual(plausible_causes=(AuditCoordinate.METHOD,)),
        AuditResidual(resource_bound=True),
        AuditResidual(external_trust_root=True),
        AuditResidual(evaluator_invalid=True),
        AuditResidual(),
    )
    decisions = [decide(node, residual) for residual in residuals]
    s05 = all(
        d.grants_scientific_authority is False and d.grants_method_promotion_authority is False
        for d in decisions
    )
    record("S05_nonsovereignty", s05)

    # S06 — decide is a pure function of (node, residual).
    residual = AuditResidual(plausible_causes=(AuditCoordinate.FRAMEWORK,))
    record(
        "S06_no_post_hoc_selection",
        decide(node, residual) == decide(node, residual),
    )

    # S07 — escalation cannot bypass the controller.
    request = request_self_rakl_escalation(decide(node, residual), evidence_digest="digest")
    record(
        "S07_escalation_cannot_bypass_controller",
        request.controller_version == CURRENT_SELF_EVOLUTION_CONTROLLER.version
        and request.controller_grants_scientific_authority is False
        and request.controller_grants_method_promotion_authority is False
        and request.grants_scientific_authority is False
        and request.enters_existing_challenger_protocol is True,
    )

    # S08 — audit_before_commit three branches.
    clean = ProblemStatement(
        problem_id="p1",
        question_candidates=(QuestionFormulationCandidate("q1", "What is X?"),),
        evaluator_epoch="EV-1",
    )
    divergent = ProblemStatement(
        problem_id="p2",
        question_candidates=(
            QuestionFormulationCandidate("q1", "What is X?"),
            QuestionFormulationCandidate("q2", "What is Y?"),
        ),
        evaluator_epoch="EV-1",
    )
    divergent_fw = ProblemStatement(
        problem_id="p3",
        question_candidates=(QuestionFormulationCandidate("q1", "What is X?"),),
        framework_candidates=(
            FrameworkCandidate("fw-1", licensed_scope="regime A"),
            FrameworkCandidate("fw-2", licensed_scope="regime B"),
        ),
        evaluator_epoch="EV-1",
    )
    invalid = ProblemStatement(
        problem_id="p4",
        question_candidates=(QuestionFormulationCandidate("q1", "What is X?"),),
        evaluator_epoch="EV-1",
        evaluator_validated=False,
    )
    record(
        "S08_audit_before_commit",
        audit_before_commit(clean).action.value == "SOLVE_CURRENT"
        and audit_before_commit(divergent).action.value == "RUN_DISCRIMINATOR"
        and audit_before_commit(divergent_fw).action.value == "RUN_DISCRIMINATOR"
        and audit_before_commit(invalid).action.value == "AUDIT_EVALUATOR",
    )

    return checks


def main() -> int:
    result = execute()
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{result['status']} — {result['case_counts']}")
    return 0 if result["status"] == "KNOWN_WORLD_CONFORMANCE_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
