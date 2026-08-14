"""Transport gate re-audit after the fail-closed repair (PLAN P0.1 -> P0.2 closure).

Re-audits `assess_transfer_v2` (src/rakl/structural_transport_v2.py) with the
gate-falsifiability battery, completing the sweep that intentionally skipped
transport while it was under repair
(research/solver_gate_falsifiability_sweep_v1/, PR #645 @ 928495eb).

Discipline (identical to the sweep harness):
  1. No-alarm control FIRST: intact correct evidence must PASS before any probe
     is trusted.
  2. 32 trials/probe at seeds 20260814 and 20260815; classification must agree
     across seeds or the gate is CANNOT_CHECK(unstable_battery).
  3. Validate-the-checker: the same battery is run against the PRE-repair gate
     (main @ b282dc04^ = 631196b4) as a planted-FAIL known-answer world. The
     fail-open probes must be INSENSITIVE there (reproducing the frozen
     FAIL_OPEN_FOUND defect) and SENSITIVE on the repaired gate, or the probes
     have no teeth and the re-audit is CANNOT_CHECK.

Classification vocabulary (superset of the sweep's):
  FAIL_OPEN         any fail-open-family probe INSENSITIVE (license survives
                    absence of load-bearing evidence) despite a passing no-alarm
  FALSIFIABLE       battery verdict FALSIFIABLE at both seeds, fail-open dead
  NON_FALSIFIABLE   no perturbation of any kind moved the verdict
  CANNOT_CHECK      no-alarm failed / battery unstable / counterfactual invalid

Note FAIL_OPEN is invisible to the plain battery: the pre-repair gate is
battery-FALSIFIABLE (other probes flip it) while still licensing on empty
obligation sets. Only the directed absence-of-evidence probes separate them.

This harness grants no scientific authority. FALSIFIABLE means only that the
gate is capable of failing, never that its PASS is correct. Same-context audit,
not independent review.

Run from repo root:  python research/transport_gate_reaudit_v1/reaudit_harness.py
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from rakl.gate_falsifiability import GateFalsifiability, audit_gate  # noqa: E402
from rakl.structural_types import (  # noqa: E402
    BoundaryCondition,
    StructuralObject,
    StructuralRelation,
    StructuralRole,
    TransferDecision,
)

SEEDS = (20260814, 20260815)
TRIALS = 32
OUT_DIR = Path(__file__).resolve().parent
PRE_REPAIR_COMMIT = "631196b4"  # b282dc04^ on main: last pre-#643 state
FAIL_OPEN_PROBES = ("empty_obligation_set", "demote_all_obligations_to_optional")


def _rand_token(rng: random.Random) -> str:
    return "zz-" + "".join(rng.choice("abcdefghij0123456789") for _ in range(8))


# --- run_battery copied unchanged from --------------------------------------------
# research/solver_gate_falsifiability_sweep_v1/sweep_harness.py @ 928495eb (PR #645)
# so this re-audit reuses the sweep's exact discipline without depending on the
# unmerged branch at import time.
def run_battery(*, gate_id, gate, evidence, perturbations, notes="", adapter=""):
    """No-alarm control first, then the battery at both seeds."""
    baseline = bool(gate(evidence))
    entry = {
        "gate_id": gate_id,
        "adapter": adapter,
        "no_alarm_control": {
            "intact_evidence_passes": baseline,
            "checked_before_probes": True,
        },
        "notes": notes,
    }
    if not baseline:
        entry["classification"] = "CANNOT_CHECK"
        entry["reason"] = "no-alarm control failed: intact evidence does not pass"
        return entry

    per_seed = {}
    for seed in SEEDS:
        report = audit_gate(
            gate,
            evidence,
            gate_id=gate_id,
            perturbations=perturbations,
            trials=TRIALS,
            seed=seed,
        )
        per_seed[str(seed)] = {
            "verdict": report.verdict.value,
            "probes": {
                p.probe_id: {"outcome": p.outcome.value, "flips": p.flips, "trials": p.trials}
                for p in report.probes
            },
        }
    entry["per_seed"] = per_seed
    verdicts = {v["verdict"] for v in per_seed.values()}
    if len(verdicts) != 1:
        entry["classification"] = "CANNOT_CHECK"
        entry["reason"] = f"battery unstable across seeds: {sorted(verdicts)}"
        return entry
    verdict = verdicts.pop()
    entry["classification"] = verdict
    first = per_seed[str(SEEDS[0])]["probes"]
    entry["insensitive_probes"] = sorted(
        pid for pid, r in first.items() if r["outcome"] == "INSENSITIVE"
    )
    entry["sensitive_probes"] = sorted(
        pid for pid, r in first.items() if r["outcome"] == "SENSITIVE"
    )
    assert verdict in {v.value for v in GateFalsifiability}
    return entry


# --- fixtures ---------------------------------------------------------------------


def _source() -> StructuralObject:
    return StructuralObject(
        structure_id="S-src",
        domain="queueing",
        qoi="stability",
        context_id="C-src",
        roles=(StructuralRole("a", "input"), StructuralRole("b", "capacity")),
        relations=(StructuralRelation("a", "competes_with", "b"),),
        invariants=frozenset({"arrival_gt_service_implies_growth"}),
        boundaries=(BoundaryCondition("flow_regime", "continual"),),
        evidence_ids=("evidence:S-src",),
    )


def _target() -> StructuralObject:
    return StructuralObject(
        structure_id="S-tgt",
        domain="scheduling",
        qoi="stability",
        context_id="C-tgt",
        roles=(StructuralRole("a", "input"), StructuralRole("b", "capacity")),
        relations=(StructuralRelation("a", "competes_with", "b"),),
        invariants=frozenset({"arrival_gt_service_implies_growth"}),
        boundaries=(BoundaryCondition("flow_regime", "continual"),),
        evidence_ids=("evidence:S-tgt",),
    )


def _disjoint_target() -> StructuralObject:
    """Shares no roles, relations, invariants, boundaries, or QoI with _source()."""
    return StructuralObject(
        structure_id="S-tgt",
        domain="unrelated-domain",
        qoi="throughput",
        context_id="C-tgt",
        roles=(StructuralRole("x", "field"), StructuralRole("y", "operator")),
        relations=(StructuralRelation("x", "commutes_with", "y"),),
        invariants=frozenset({"totally_unrelated_invariant"}),
        boundaries=(BoundaryCondition("regime", "adiabatic"),),
        evidence_ids=("evidence:S-tgt-disjoint",),
    )


def baseline_evidence() -> list[dict]:
    """Legitimate witness: 5 load-bearing satisfied obligations + 1 optional."""
    meta = {
        "kind": "meta",
        "witness_id": "w-transport-reaudit",
        "source_structure_id": "S-src",
        "target_structure_id": "S-tgt",
        "source_context_id": "C-src",
        "target_context_id": "C-tgt",
        "qoi": "stability",
        "role_mapping": [["a", "a"], ["b", "b"]],
    }
    obligations = [
        ("ob-role-a", "ROLE", "a", "a", "REQUIRED", ["ev-role-a"]),
        ("ob-rel", "RELATION", "a|competes_with|b|1", "a|competes_with|b|1", "REQUIRED", ["ev-rel"]),
        ("ob-inv", "INVARIANT", "arrival_gt_service_implies_growth",
         "arrival_gt_service_implies_growth", "REQUIRED", ["ev-inv"]),
        ("ob-qoi", "QOI", "stability", "stability", "REQUIRED", ["ev-qoi"]),
        ("ob-bnd", "BOUNDARY", "flow_regime", "continual", "REQUIRED", ["ev-bnd"]),
        ("ob-opt-inv", "INVARIANT", "arrival_gt_service_implies_growth",
         "arrival_gt_service_implies_growth", "OPTIONAL", ["ev-opt"]),
    ]
    rows: list[dict] = [meta]
    for oid, kind, src, tgt, req, ev in obligations:
        rows.append(
            {
                "kind": "obligation",
                "obligation_id": oid,
                "ob_kind": kind,
                "source_ref": src,
                "target_ref": tgt,
                "requirement": req,
                "evidence_ids": list(ev),
                "status": "UNKNOWN",
                "rationale_code": "",
            }
        )
    return rows


def make_gate(mod, source: StructuralObject, target: StructuralObject):
    """Gate closure over a specific transport module (repaired or pre-repair).

    Fixtures are built from `mod`'s own classes: the module compares enum members
    with `is`, so cross-module enum instances would silently take wrong branches.
    """

    def gate(rows) -> bool:
        meta = next(r for r in rows if r["kind"] == "meta")
        obligations = tuple(
            mod.TransferObligation(
                obligation_id=r["obligation_id"],
                kind=mod.ObligationKind(r["ob_kind"]),
                source_ref=r["source_ref"],
                target_ref=r["target_ref"],
                requirement=mod.ObligationRequirement(r["requirement"]),
                evidence_ids=tuple(r["evidence_ids"]),
                status=mod.ObligationStatus(r["status"]),
                rationale_code=r["rationale_code"],
            )
            for r in rows
            if r["kind"] == "obligation"
        )
        witness = mod.StructuralWitnessV2(
            witness_id=meta["witness_id"],
            source_structure_id=meta["source_structure_id"],
            target_structure_id=meta["target_structure_id"],
            source_context_id=meta["source_context_id"],
            target_context_id=meta["target_context_id"],
            qoi=meta["qoi"],
            role_mapping=tuple((s, t) for s, t in meta["role_mapping"]),
            obligations=obligations,
        )
        assessment = mod.assess_transfer_v2(source, target, witness)
        return assessment.decision is TransferDecision.LICENSED

    return gate


# --- probes -----------------------------------------------------------------------


def _copy(rows):
    return [dict(r) for r in rows]


def empty_obligation_set(rows, rng):
    """Fail-open probe A: zero obligations. Pre-repair gate stayed LICENSED."""
    return [r for r in _copy(rows) if r["kind"] == "meta"]


def demote_all_obligations_to_optional(rows, rng):
    """Fail-open probe B: OPTIONAL-only => empty load-bearing set."""
    rows = _copy(rows)
    for r in rows:
        if r["kind"] == "obligation":
            r["requirement"] = "OPTIONAL"
    return rows


def randomize_structural_target_refs(rows, rng):
    rows = _copy(rows)
    for r in rows:
        if r["kind"] == "obligation" and r["ob_kind"] in {"INVARIANT", "RELATION", "BOUNDARY"}:
            if rng.random() < 0.75:
                r["target_ref"] = _rand_token(rng)
    return rows


def strip_obligation_evidence_ids(rows, rng):
    rows = _copy(rows)
    for r in rows:
        if r["kind"] == "obligation" and rng.random() < 0.75:
            r["evidence_ids"] = []
    return rows


def corrupt_witness_identity(rows, rng):
    rows = _copy(rows)
    field = rng.choice(
        ["source_structure_id", "target_structure_id", "source_context_id", "target_context_id"]
    )
    for r in rows:
        if r["kind"] == "meta":
            r[field] = _rand_token(rng)
    return rows


def rewire_role_mapping(rows, rng):
    rows = _copy(rows)
    for r in rows:
        if r["kind"] == "meta":
            r["role_mapping"] = [[s, _rand_token(rng)] for s, _ in r["role_mapping"]]
    return rows


def force_explicit_violation(rows, rng):
    rows = _copy(rows)
    required = [r for r in rows if r["kind"] == "obligation" and r["requirement"] == "REQUIRED"]
    victim = rng.choice(required)
    victim["status"] = "VIOLATED"
    victim["rationale_code"] = "hostile_explicit_violation"
    return rows


PERTURBATIONS = {
    "empty_obligation_set": empty_obligation_set,
    "demote_all_obligations_to_optional": demote_all_obligations_to_optional,
    "randomize_structural_target_refs": randomize_structural_target_refs,
    "strip_obligation_evidence_ids": strip_obligation_evidence_ids,
    "corrupt_witness_identity": corrupt_witness_identity,
    "rewire_role_mapping": rewire_role_mapping,
    "force_explicit_violation": force_explicit_violation,
}


# --- classification ---------------------------------------------------------------


def classify(entry: dict) -> str:
    """Sweep classification + the FAIL_OPEN class for absence-of-evidence probes."""
    if entry["classification"] == "CANNOT_CHECK":
        return "CANNOT_CHECK"
    fail_open = sorted(
        pid
        for seed in entry["per_seed"].values()
        for pid, r in seed["probes"].items()
        if pid in FAIL_OPEN_PROBES and r["outcome"] == "INSENSITIVE"
    )
    if fail_open:
        return "FAIL_OPEN"
    return entry["classification"]


def load_pre_repair_module():
    blob = subprocess.run(
        ["git", "show", f"{PRE_REPAIR_COMMIT}:src/rakl/structural_transport_v2.py"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    sha = hashlib.sha256(blob.encode()).hexdigest()
    with tempfile.NamedTemporaryFile(
        "w", suffix="_pre_repair_transport.py", delete=False
    ) as fh:
        fh.write(blob)
        path = fh.name
    spec = importlib.util.spec_from_file_location("pre_repair_structural_transport_v2", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # dataclasses resolves annotations via sys.modules
    spec.loader.exec_module(mod)
    return mod, sha


def directed_fail_open_check(mod) -> dict:
    """Deterministic reproduction input: disjoint structures, empty obligations."""
    witness = mod.StructuralWitnessV2(
        witness_id="w-empty",
        source_structure_id="S-src",
        target_structure_id="S-tgt",
        source_context_id="C-src",
        target_context_id="C-tgt",
        qoi="stability",
        role_mapping=(),
        obligations=(),
    )
    assessment = mod.assess_transfer_v2(_source(), _disjoint_target(), witness)
    return {
        "input": "disjoint structures, zero obligations",
        "decision": assessment.decision.value,
        "reasons": list(assessment.reasons),
        "licensed": assessment.decision is TransferDecision.LICENSED,
    }


def main() -> None:
    import rakl.structural_transport_v2 as repaired_mod

    repaired_entry = run_battery(
        gate_id="structural_transport_v2.assess_transfer_v2 (repaired, PR #643)",
        gate=make_gate(repaired_mod, _source(), _target()),
        evidence=baseline_evidence(),
        perturbations=PERTURBATIONS,
        notes=(
            "pass := LICENSED on a legitimate 5-load-bearing-obligation witness; "
            "fail-open family: " + ", ".join(FAIL_OPEN_PROBES)
        ),
    )
    repaired_classification = classify(repaired_entry)

    pre_mod, pre_sha = load_pre_repair_module()
    counterfactual_entry = run_battery(
        gate_id=f"structural_transport_v2.assess_transfer_v2 (pre-repair, {PRE_REPAIR_COMMIT})",
        gate=make_gate(pre_mod, _source(), _target()),
        evidence=baseline_evidence(),
        perturbations=PERTURBATIONS,
        notes="planted-FAIL known-answer world: probes must reproduce FAIL_OPEN here",
    )
    counterfactual_classification = classify(counterfactual_entry)

    directed = {
        "repaired": directed_fail_open_check(repaired_mod),
        "pre_repair": directed_fail_open_check(pre_mod),
    }

    # Validate-the-checker verdict: the battery is trusted only if it separates
    # the pre-repair (FAIL_OPEN) and repaired worlds.
    probes_validated = (
        counterfactual_classification == "FAIL_OPEN"
        and directed["pre_repair"]["licensed"]
        and not directed["repaired"]["licensed"]
        and "empty_load_bearing_obligation_set" in directed["repaired"]["reasons"]
    )
    final = repaired_classification if probes_validated else "CANNOT_CHECK"

    out = {
        "schema_version": "rakl-transport-gate-reaudit-v1",
        "completes": {
            "sweep": "research/solver_gate_falsifiability_sweep_v1 (PR #645 @ 928495eb)",
            "skipped_step_closed": "transport (was: under repair in parallel branch, P0.1)",
            "coverage_after_this": (
                "saturation (AUDIT.md row 5) + 12 sweep gates + this transport gate = "
                "14 audited gate surfaces across all 11 RAKL_SOLVER steps; steps 2 and "
                "3(reduction fidelity) remain NO_REGISTERED_GATE findings, not sweeps"
            ),
        },
        "gate": {
            "module": "src/rakl/structural_transport_v2.py",
            "function": "assess_transfer_v2",
            "repaired_by": "PR #643 (b282dc04), on main @ 600cfc92",
            "frozen_defect": (
                "research/framework_ladder/ladder.json layers[3].readiness."
                "gate_falsifiable = FAIL_OPEN_FOUND (frozen, intentionally not edited); "
                "repair receipt: research/transport_failopen_repair_v1/RECEIPT.md"
            ),
        },
        "battery": "src/rakl/gate_falsifiability.py",
        "trials_per_probe": TRIALS,
        "seeds": list(SEEDS),
        "fail_open_probe_family": list(FAIL_OPEN_PROBES),
        "repaired_gate": {**repaired_entry, "reaudit_classification": repaired_classification},
        "known_answer_counterfactual": {
            "commit": PRE_REPAIR_COMMIT,
            "blob_sha256": pre_sha,
            **counterfactual_entry,
            "reaudit_classification": counterfactual_classification,
            "purpose": (
                "planted-FAIL world validating the probes: the pre-repair gate must "
                "classify FAIL_OPEN (fail-open probes INSENSITIVE) while remaining "
                "battery-FALSIFIABLE on other probes — showing why FAIL_OPEN needs "
                "directed probes and is invisible to the plain battery verdict"
            ),
        },
        "directed_fail_open_checks": directed,
        "probes_validated_against_planted_defect": probes_validated,
        "final_classification": final,
        "grants_scientific_authority": False,
        "note": (
            "FALSIFIABLE means only that the gate can fail under evidence "
            "perturbation; it never certifies that a PASS is correct. Same-context "
            "audit, not independent review."
        ),
    }
    (OUT_DIR / "REAUDIT.json").write_text(json.dumps(out, indent=2) + "\n")

    print(f"repaired:       {repaired_classification}")
    print(f"counterfactual: {counterfactual_classification} (expected FAIL_OPEN)")
    print(f"probes validated: {probes_validated}")
    print(f"FINAL: {final}")
    for seed, data in repaired_entry.get("per_seed", {}).items():
        print(f"  seed {seed}: verdict={data['verdict']}")
        for pid, r in sorted(data["probes"].items()):
            print(f"    {pid}: {r['outcome']} ({r['flips']}/{r['trials']})")


if __name__ == "__main__":
    main()
