"""Gate-falsifiability sweep across the RAKL_SOLVER step gates (PLAN P0.2).

Runs the black-box perturbation battery (src/rakl/gate_falsifiability.py) against
every solver step that exposes a registered gate function. Steps whose gating is
only inline invariants are recorded NO_REGISTERED_GATE and never force-swept.

Discipline (validate-the-checker):
  1. No-alarm control FIRST: the intact, correct evidence must PASS the gate
     before any probe is trusted. A battery whose baseline already fails is not
     probing anything.
  2. Every battery runs at two seeds; classification must agree or the gate is
     recorded CANNOT_CHECK(unstable_battery).
  3. Exception-channel gates (reject by raise) are adapted so a refusal counts
     as gate=False; the adapter is declared in the output.

This harness grants no scientific authority. FALSIFIABLE means only that the
gate is capable of failing, never that its PASS is correct.

Run from repo root:  python research/solver_gate_falsifiability_sweep_v1/sweep_harness.py
"""

from __future__ import annotations

import json
import random
import sys
from dataclasses import replace
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tests"))

from rakl.gate_falsifiability import (  # noqa: E402
    GateFalsifiability,
    audit_gate,
)

SEEDS = (20260814, 20260815)
TRIALS = 32
OUT_DIR = Path(__file__).resolve().parent


def _rand_token(rng: random.Random) -> str:
    return "zz-" + "".join(rng.choice("abcdefghij0123456789") for _ in range(8))


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


# =========================================================================
# Step 1a — problem contract: hard_gates.evaluate_hard_gates
# =========================================================================

def step1a():
    from rakl.hard_gates import (
        HardGateContract,
        HardGateObservation,
        HardGateReport,
        HardGateRequirement,
        HardGateState,
        evaluate_hard_gates,
    )

    requirements = tuple(
        HardGateRequirement(gate_id=f"G{i}", description=f"gate {i}") for i in range(1, 5)
    )
    evidence = [{"kind": "meta", "frozen": True}] + [
        {
            "kind": "obs",
            "gate_id": f"G{i}",
            "candidate_id": "cand-1",
            "state": "PASS",
            "evidence_ids": (f"ev-{i}",),
            "detail": f"detail {i}",
        }
        for i in range(1, 5)
    ]

    def gate(rows) -> bool:
        meta = next(r for r in rows if r["kind"] == "meta")
        contract = HardGateContract(
            contract_id="HGC-sweep",
            requirements=requirements,
            frozen_before_candidate_results=meta["frozen"],
        )
        observations = tuple(
            HardGateObservation(
                gate_id=r["gate_id"],
                candidate_id=r["candidate_id"],
                state=HardGateState(r["state"]),
                evidence_ids=tuple(r["evidence_ids"]),
                detail=r["detail"],
            )
            for r in rows
            if r["kind"] == "obs"
        )
        report: HardGateReport = evaluate_hard_gates(
            contract, observations, candidate_id="cand-1"
        )
        return report.state is HardGateState.PASS

    def _obs_rows(rows):
        return [dict(r) for r in rows]

    def shuffle_gate_ids(rows, rng):
        rows = _obs_rows(rows)
        obs = [r for r in rows if r["kind"] == "obs"]
        ids = [r["gate_id"] for r in obs]
        rng.shuffle(ids)
        # shuffle detail too so relabelled duplicates conflict rather than dedup
        for r, gid in zip(obs, ids):
            r["gate_id"] = gid
            r["detail"] = _rand_token(rng)
        return rows

    def randomize_states(rows, rng):
        rows = _obs_rows(rows)
        for r in rows:
            if r["kind"] == "obs":
                r["state"] = rng.choice(["PASS", "FAIL", "CANNOT_CHECK"])
        return rows

    def strip_evidence_ids(rows, rng):
        rows = _obs_rows(rows)
        for r in rows:
            if r["kind"] == "obs" and rng.random() < 0.75:
                r["evidence_ids"] = ()
        return rows

    def relabel_candidate(rows, rng):
        rows = _obs_rows(rows)
        for r in rows:
            if r["kind"] == "obs":
                r["candidate_id"] = _rand_token(rng)
        return rows

    def drop_half_observations(rows, rng):
        obs = [r for r in rows if r["kind"] == "obs"]
        keep = rng.sample(obs, max(1, len(obs) // 2))
        return [r for r in rows if r["kind"] == "meta"] + keep

    def unfreeze_contract(rows, rng):
        rows = _obs_rows(rows)
        for r in rows:
            if r["kind"] == "meta":
                r["frozen"] = False
        return rows

    return run_battery(
        gate_id="hard_gates.evaluate_hard_gates",
        gate=gate,
        evidence=evidence,
        perturbations={
            "shuffle_gate_ids": shuffle_gate_ids,
            "randomize_observation_states": randomize_states,
            "strip_evidence_ids": strip_evidence_ids,
            "relabel_candidate_identity": relabel_candidate,
            "drop_half_observations": drop_half_observations,
            "unfreeze_contract_chronology": unfreeze_contract,
        },
        notes="pass := HardGateReport.state is PASS for exact candidate cand-1",
    ) | {
        "probe_diagnoses": {
            "shuffle_gate_ids": (
                "INSENSITIVE verified as a structural no-op, not a blind spot beyond "
                "known semantics: the verdict depends only on gate-id coverage, per-row "
                "state, and evidence presence; a permutation of gate_ids over "
                "homogeneous all-PASS rows preserves all three. Underlying limitation "
                "reproduced twice (reproduce_insensitive_findings.py finding-1): the "
                "gate checks evidence *presence*, never gate<->evidence binding — "
                "swapping evidence ids between gates keeps PASS. Binding is owned by "
                "evidence_binding_certificate; recorded as scope note, not defect."
            )
        }
    }


# =========================================================================
# Step 1b — problem contract: framework_candidate_freeze gate
# =========================================================================

def step1b():
    from rakl.framework_candidate_freeze import (
        DiffPathClassification,
        DiffSurfaceClass,
        FrameworkSubjectFreezeBinding,
        FrameworkSubjectRevalidationObservation,
        gate_candidate_materialization_framework_subject,
    )

    SHA = "a" * 40
    PKT = "b" * 64
    evidence = [
        {
            "kind": "binding",
            "present": True,
            "sha": SHA,
            "packet": PKT,
            "pointers": ("freeze:packet",),
        },
        {
            "kind": "observation",
            "present": True,
            "observed_sha": SHA,
            "diff": (),  # tuples of (path, surface_class_name)
        },
    ]

    def gate(rows) -> bool:
        b = next(r for r in rows if r["kind"] == "binding")
        o = next(r for r in rows if r["kind"] == "observation")
        binding = None
        if b["present"]:
            binding = FrameworkSubjectFreezeBinding(
                binding_id="FSB-sweep",
                authoritative_framework_sha=b["sha"],
                pre_candidate_packet_hash=b["packet"],
                frozen_at_utc="2026-08-14T00:00:00Z",
                evidence_pointers=tuple(b["pointers"]),
            )
        observation = None
        if o["present"]:
            observation = FrameworkSubjectRevalidationObservation(
                observed_current_main_sha=o["observed_sha"],
                intervening_diff=tuple(
                    DiffPathClassification(path=p, surface_class=DiffSurfaceClass[c])
                    for p, c in o["diff"]
                ),
                observation_evidence_pointers=("obs:git",),
            )
        report = gate_candidate_materialization_framework_subject(
            binding, observation, required=True
        )
        return report.licenses_candidate_materialization

    def _c(rows):
        return [dict(r) for r in rows]

    def advance_sha_protected_diff(rows, rng):
        rows = _c(rows)
        o = next(r for r in rows if r["kind"] == "observation")
        o["observed_sha"] = "".join(rng.choice("0123456789abcdef") for _ in range(40))
        o["diff"] = (("src/rakl/hard_gates.py", "PROTECTED_METHOD_GATE_SCHEMA_RUNTIME"),)
        return rows

    def advance_sha_unclassified_diff(rows, rng):
        rows = _c(rows)
        o = next(r for r in rows if r["kind"] == "observation")
        o["observed_sha"] = "".join(rng.choice("0123456789abcdef") for _ in range(40))
        o["diff"] = ((_rand_token(rng), "UNCLASSIFIED"),)
        return rows

    def advance_sha_diff_unobserved(rows, rng):
        rows = _c(rows)
        o = next(r for r in rows if r["kind"] == "observation")
        o["observed_sha"] = "".join(rng.choice("0123456789abcdef") for _ in range(40))
        o["diff"] = ()
        return rows

    def nonempty_diff_same_sha(rows, rng):
        rows = _c(rows)
        o = next(r for r in rows if r["kind"] == "observation")
        o["diff"] = ((_rand_token(rng), "NON_METHOD_PUBLICATION_OR_RESEARCH"),)
        return rows

    def drop_observation(rows, rng):
        rows = _c(rows)
        next(r for r in rows if r["kind"] == "observation")["present"] = False
        return rows

    def drop_binding(rows, rng):
        rows = _c(rows)
        next(r for r in rows if r["kind"] == "binding")["present"] = False
        return rows

    entry = run_battery(
        gate_id="framework_candidate_freeze.gate_candidate_materialization_framework_subject",
        gate=gate,
        evidence=evidence,
        perturbations={
            "advance_sha_protected_diff": advance_sha_protected_diff,
            "advance_sha_unclassified_diff": advance_sha_unclassified_diff,
            "advance_sha_diff_unobserved": advance_sha_diff_unobserved,
            "nonempty_diff_same_sha": nonempty_diff_same_sha,
            "drop_observation": drop_observation,
            "drop_binding": drop_binding,
        },
        notes=(
            "pass := report.licenses_candidate_materialization with required=True. "
            "Battery run in the registered (required) mode."
        ),
    )

    # Directed check (not a battery probe): inactive mode fail-open surface.
    inactive = gate_candidate_materialization_framework_subject(None, None, required=False)
    entry["directed_checks"] = {
        "inactive_mode_licenses_unconditionally": {
            "call": "gate(None, None, required=False)",
            "licenses_candidate_materialization": inactive.licenses_candidate_materialization,
            "verdict_value": inactive.verdict.value,
            "assessment": (
                "By-design inactive path (free-form brainstorming). Black-box fact: with "
                "required=False, deleting binding+observation yields licensed=True. Live "
                "call site (math_research_runtime.py:314-321) activates the gate whenever "
                "a binding exists or require_framework_subject_gate is set; risk is "
                "confined to callers that leave both unset."
            ),
        }
    }
    return entry


# =========================================================================
# Step 3 — structuralization: structure_space.match admission
# =========================================================================

def step3_real():
    from rakl.structure_space import (
        MatchVerdict,
        ProblemStructure,
        ReducedStructure,
        StructureSpace,
        match,
    )
    from rakl.support_solver import Atom, SupportEdge, SupportStructure

    def _support(sid: str, atom_ids):
        return SupportStructure(
            structure_id=sid,
            atoms=tuple(Atom(atom_id=a) for a in atom_ids),
            edges=(),
        )

    base_roles = ("r1", "r2", "r3")
    evidence = [
        {
            "kind": "problem",
            "roles": base_roles,
            "relations": (("r1", "r2"),),
            "authority": 2,
        },
        {
            "kind": "structure",
            "sid": "S1",
            "roles": base_roles,
            "relations": (("r1", "r2"),),
            "established_at": 3,
        },
        {
            "kind": "structure",
            "sid": "S2",
            "roles": ("r9",),
            "relations": (),
            "established_at": 3,
        },
    ]

    def gate(rows) -> bool:
        p = next(r for r in rows if r["kind"] == "problem")
        problem = ProblemStructure(
            problem_id="P-sweep",
            qoi="sweep",
            required_roles=frozenset(p["roles"]),
            required_relations=frozenset(tuple(x) for x in p["relations"]),
            required_authority=p["authority"],
        )
        space = StructureSpace(space_id="SP-sweep")
        for r in rows:
            if r["kind"] != "structure":
                continue
            space.accumulate(
                ReducedStructure(
                    structure=_support(r["sid"], r["roles"]),
                    roles=frozenset(r["roles"]),
                    relations=frozenset(tuple(x) for x in r["relations"]),
                    established_at=r["established_at"],
                )
            )
        results = match(space, problem)
        s1 = next(m for m in results if m.structure_id == "S1")
        return s1.verdict is MatchVerdict.LICENSED

    def _c(rows):
        return [dict(r) for r in rows]

    def scramble_structure_roles(rows, rng):
        rows = _c(rows)
        for r in rows:
            if r["kind"] == "structure" and r["sid"] == "S1":
                r["roles"] = tuple(_rand_token(rng) for _ in r["roles"])
        return rows

    def degrade_authority(rows, rng):
        rows = _c(rows)
        for r in rows:
            if r["kind"] == "structure" and r["sid"] == "S1":
                r["established_at"] = 0
        return rows

    def claim_relation_without_role(rows, rng):
        # S1 keeps claiming relation (r1,r2) but loses r2 from its roles.
        rows = _c(rows)
        for r in rows:
            if r["kind"] == "structure" and r["sid"] == "S1":
                r["roles"] = ("r1", "r3")
        return rows

    def scramble_problem_roles(rows, rng):
        rows = _c(rows)
        for r in rows:
            if r["kind"] == "problem":
                r["roles"] = tuple(_rand_token(rng) for _ in r["roles"])
                r["relations"] = ()
        return rows

    def shuffle_role_alignment(rows, rng):
        # Permute role tuples between structures (S1 gets S2's junk roles half the time).
        rows = _c(rows)
        structs = [r for r in rows if r["kind"] == "structure"]
        role_sets = [r["roles"] for r in structs]
        rng.shuffle(role_sets)
        for r, roles in zip(structs, role_sets):
            r["roles"] = roles
            r["relations"] = ()
        return rows

    return run_battery(
        gate_id="structure_space.match",
        gate=gate,
        evidence=evidence,
        perturbations={
            "scramble_candidate_structure_roles": scramble_structure_roles,
            "degrade_establishment_authority": degrade_authority,
            "claim_relation_without_both_roles": claim_relation_without_role,
            "scramble_problem_required_roles": scramble_problem_roles,
            "shuffle_role_alignment_across_structures": shuffle_role_alignment,
        },
        notes=(
            "pass := candidate structure S1 LICENSED for the problem. "
            "Reduction-fidelity (does ReducedStructure faithfully represent its "
            "source?) has NO registered gate; this battery covers admission only."
        ),
    )


# =========================================================================
# Step 4a — knowledge space: atlas_gluing.evaluate_atlas_gluing
# =========================================================================

def step4a():
    import test_atlas_gluing as tag
    from rakl.atlas_gluing import AtlasGluingVerdict, evaluate_atlas_gluing

    evidence = [
        {
            "cycle_consistent": True,
            "frozen": True,
            "hidden_labels": False,
            "keep_transitions": ("A-B", "B-C", "C-A"),
            "regime_overlap": ("shared-regime",),
            "global_existence_checked": True,
            "scramble_endpoints": False,
        }
    ]

    def gate(rows) -> bool:
        cfg = rows[0]
        rng = random.Random(cfg.get("_rng_seed", 0))
        transitions = []
        for pair in cfg["keep_transitions"]:
            src, dst = pair.split("-")
            if cfg["scramble_endpoints"]:
                src, dst = _rand_token(rng)[:6], _rand_token(rng)[:6]
            transitions.append(
                tag._transition(src, dst, transition_id=pair, regime_overlap=cfg["regime_overlap"])
            )
        trial = tag._trial(
            transitions=tuple(transitions),
            cycle_witnesses=(tag._cycle(consistent=cfg["cycle_consistent"]),),
            transition_family_frozen_before_outcomes=cfg["frozen"],
            hidden_labels_exposed=cfg["hidden_labels"],
            global_existence_checked=cfg["global_existence_checked"],
        )
        report = evaluate_atlas_gluing(trial)
        return report.verdict is AtlasGluingVerdict.GLUED_GLOBAL_PORTRAIT_PROPOSAL_ONLY

    def _c(rows):
        return [dict(rows[0])]

    def break_cycle_consistency(rows, rng):
        rows = _c(rows)
        rows[0]["cycle_consistent"] = False
        return rows

    def scramble_transition_endpoints(rows, rng):
        rows = _c(rows)
        rows[0]["scramble_endpoints"] = True
        rows[0]["_rng_seed"] = rng.random()
        return rows

    def unfreeze_transition_family(rows, rng):
        rows = _c(rows)
        rows[0]["frozen"] = False
        return rows

    def expose_hidden_labels(rows, rng):
        rows = _c(rows)
        rows[0]["hidden_labels"] = True
        return rows

    def drop_transitions(rows, rng):
        rows = _c(rows)
        keep = rng.sample(list(rows[0]["keep_transitions"]), 1)
        rows[0]["keep_transitions"] = tuple(keep)
        return rows

    def empty_regime_overlap(rows, rng):
        rows = _c(rows)
        rows[0]["regime_overlap"] = ()
        return rows

    def skip_global_existence_check(rows, rng):
        rows = _c(rows)
        rows[0]["global_existence_checked"] = False
        return rows

    return run_battery(
        gate_id="atlas_gluing.evaluate_atlas_gluing",
        gate=gate,
        evidence=evidence,
        perturbations={
            "break_cycle_consistency": break_cycle_consistency,
            "scramble_transition_endpoints": scramble_transition_endpoints,
            "unfreeze_transition_family": unfreeze_transition_family,
            "expose_hidden_labels": expose_hidden_labels,
            "drop_two_of_three_transitions": drop_transitions,
            "empty_regime_overlap": empty_regime_overlap,
            "skip_global_existence_check": skip_global_existence_check,
        },
        notes="pass := GLUED_GLOBAL_PORTRAIT_PROPOSAL_ONLY on the consistent triangle atlas",
    ) | {
        "probe_diagnoses": {
            "drop_two_of_three_transitions": (
                "INSENSITIVE verified as a REAL blind spot (declared-topology trust), "
                "reproduced twice (reproduce_insensitive_findings.py finding-2): "
                "evaluate_atlas_gluing validates each declared transition individually "
                "but never recomputes cover connectivity / cycle structure from the "
                "transition set; cover_connected, cover_has_cycles, "
                "cycle_basis_complete and cycle-witness consistency are caller-declared "
                "booleans (atlas_gluing.py:463-528). A single-transition atlas with "
                "intact declarations still returns GLUED. Follow-up work, not patched "
                "here (sweep modifies no gate implementations)."
            )
        }
    }


# =========================================================================
# Step 4b — knowledge space: typed_lattice.construct_paths admission
# =========================================================================

def step4b():
    from rakl.typed_lattice import (
        CompatibilityWitness,
        KnowledgeAtom,
        KnowledgeAtomKind,
        LatticeCompatibility,
        TypedKnowledgeLattice,
    )

    evidence = [
        {"kind": "atom", "atom_id": "A", "akind": "OBSERVABLE"},
        {"kind": "atom", "atom_id": "B", "akind": "ASSUMPTION"},
        {"kind": "witness", "present": True, "left": "A", "right": "B", "relation": "COMPATIBLE"},
    ]

    def gate(rows) -> bool:
        lattice = TypedKnowledgeLattice.empty()
        for r in rows:
            if r["kind"] == "atom":
                lattice.add_atom(
                    KnowledgeAtom(
                        atom_id=r["atom_id"],
                        fiber_id="fiber-sweep",
                        kind=KnowledgeAtomKind[r["akind"]],
                        label=f"atom {r['atom_id']}",
                        evidence_ids=(f"ev-{r['atom_id']}",),
                    )
                )
        for r in rows:
            if r["kind"] == "witness" and r["present"]:
                lattice.add_witness(
                    CompatibilityWitness(
                        left_atom_id=r["left"],
                        right_atom_id=r["right"],
                        relation=LatticeCompatibility[r["relation"]],
                        reason="sweep witness",
                    )
                )
        paths = lattice.construct_paths(
            (KnowledgeAtomKind.OBSERVABLE, KnowledgeAtomKind.ASSUMPTION),
            allow_unknown=False,
        )
        return len(paths) >= 1

    def _c(rows):
        return [dict(r) for r in rows]

    def witness_incompatible(rows, rng):
        rows = _c(rows)
        for r in rows:
            if r["kind"] == "witness":
                r["relation"] = "INCOMPATIBLE"
        return rows

    def delete_witness(rows, rng):
        rows = _c(rows)
        for r in rows:
            if r["kind"] == "witness":
                r["present"] = False
        return rows

    def witness_unknown(rows, rng):
        rows = _c(rows)
        for r in rows:
            if r["kind"] == "witness":
                r["relation"] = "UNKNOWN"
        return rows

    def scramble_atom_kinds(rows, rng):
        rows = _c(rows)
        for r in rows:
            if r["kind"] == "atom":
                r["akind"] = rng.choice(["REGIME", "INVARIANT", "FALSIFIER"])
        return rows

    return run_battery(
        gate_id="typed_lattice.construct_paths",
        gate=gate,
        evidence=evidence,
        perturbations={
            "witness_incompatible": witness_incompatible,
            "delete_compatibility_witness": delete_witness,
            "witness_relation_unknown": witness_unknown,
            "scramble_atom_kinds": scramble_atom_kinds,
        },
        notes=(
            "pass := at least one admissible constructive path for "
            "(OBSERVABLE, ASSUMPTION) with allow_unknown=False. Identity-immutability "
            "and unknown-atom admission checks are exception-channel invariants on "
            "add_atom/add_witness, covered by unit tests, not by this battery."
        ),
    )


# =========================================================================
# Step 5 — retrieval: semantic_shortcut.audit_obstruction_transformation_review
# =========================================================================

def step5():
    import test_semantic_shortcut as tss
    from rakl.semantic_shortcut import (
        RouteSearchStatus,
        ShortcutMode,
        ShortcutReviewVerdict,
        audit_obstruction_transformation_review,
    )

    evidence = [
        {
            "memory_episodes": ("D",),
            "snapshot_override": None,
            "direct_status": "MATCHES_FOUND",
            "candidate_ids": ("D",),
            "witness_ids": ("D",),
            "selected_ids": ("D",),
            "unmatched_precondition": False,
            "context_hash": "sha256:context",
        }
    ]

    def gate(rows) -> bool:
        cfg = rows[0]
        memory = tss._memory(*[tss._episode(e, "mathematics") for e in cfg["memory_episodes"]])
        witnesses = []
        for wid in cfg["witness_ids"]:
            w = tss._mapping(wid)
            if cfg["unmatched_precondition"]:
                w = replace(
                    w,
                    precondition_mapping=(("finite", "finite"),),
                    unmatched_source_preconditions=("typed",),
                )
            witnesses.append(w)
        review = tss._base_review(
            memory,
            ShortcutMode.SEARCH,
            direct_search_status=RouteSearchStatus[cfg["direct_status"]],
            direct_candidate_episode_ids=tuple(cfg["candidate_ids"]),
            direct_mapping_witnesses=tuple(witnesses),
            selected_episode_ids=tuple(cfg["selected_ids"]),
        )
        if cfg["snapshot_override"] is not None:
            review = replace(review, episode_memory_snapshot_hash=cfg["snapshot_override"])
        report = audit_obstruction_transformation_review(
            review,
            atom_id="atom-C",
            context_hash=cfg["context_hash"],
            research_memory_review_hash="sha256:memory-review",
            transformation_memory=memory,
        )
        return report.verdict is ShortcutReviewVerdict.PASS

    def _c(rows):
        return [dict(rows[0])]

    def scramble_snapshot_hash(rows, rng):
        rows = _c(rows)
        rows[0]["snapshot_override"] = "sha256:" + _rand_token(rng)
        return rows

    def remove_episode_from_memory(rows, rng):
        rows = _c(rows)
        rows[0]["memory_episodes"] = ("E-other",)
        return rows

    def unmatched_source_precondition(rows, rng):
        rows = _c(rows)
        rows[0]["unmatched_precondition"] = True
        return rows

    def select_unwitnessed_episode(rows, rng):
        rows = _c(rows)
        rows[0]["selected_ids"] = (_rand_token(rng),)
        return rows

    def invert_search_status(rows, rng):
        rows = _c(rows)
        rows[0]["direct_status"] = "NO_VIABLE_MATCH"
        return rows

    def scramble_context_binding(rows, rng):
        rows = _c(rows)
        rows[0]["context_hash"] = "sha256:" + _rand_token(rng)
        return rows

    return run_battery(
        gate_id="semantic_shortcut.audit_obstruction_transformation_review",
        gate=gate,
        evidence=evidence,
        perturbations={
            "scramble_memory_snapshot_hash": scramble_snapshot_hash,
            "remove_claimed_episode_from_memory": remove_episode_from_memory,
            "unmatched_source_precondition": unmatched_source_precondition,
            "select_unwitnessed_episode": select_unwitnessed_episode,
            "invert_direct_search_status": invert_search_status,
            "scramble_context_binding": scramble_context_binding,
        },
        notes=(
            "pass := ShortcutReviewVerdict.PASS on a valid SEARCH-mode review. "
            "JUMP/GLUE/LIFT ladder-order preconditions are separately covered by "
            "tests/test_semantic_shortcut.py hostile cases."
        ),
    )


# =========================================================================
# Step 6a — composition: bridge_composition.evaluate_bridge_path
# =========================================================================

def step6a():
    import test_bridge_composition as tbc
    from rakl.bridge_composition import BridgePathVerdict, evaluate_bridge_path

    evidence = [
        {
            "hop_errors": (0.05, 0.07),
            "break_invariant_on_hop": None,
            "junction": "B",
            "declared_before_outcomes": True,
            "hop_semantics": ("certified_metric_v1", "certified_metric_v1"),
            "keep_handoffs": True,
            "compat": True,
        }
    ]

    def gate(rows) -> bool:
        cfg = rows[0]
        hops = []
        for i, (spec, err, sem) in enumerate(
            zip((("A", "B"), ("B", "C")), cfg["hop_errors"], cfg["hop_semantics"])
        ):
            kwargs = {}
            if cfg["break_invariant_on_hop"] == i:
                kwargs = {
                    "preserved": ("role_order",),
                    "not_preserved": ("substrate", "feedback_loop"),
                }
            hops.append(tbc._hop(spec[0], spec[1], error=err, lineage=f"lineage-{i}", semantics=sem, **kwargs))
        from rakl.bridge_composition import BridgeHandoff

        handoffs = ()
        if cfg["keep_handoffs"]:
            handoffs = (
                BridgeHandoff(
                    junction_id=cfg["junction"],
                    role_pairs=(("driver", "driver"), ("response", "response")),
                    compatibility_passed=cfg["compat"],
                    evidence_ids=("handoff-B",),
                ),
            )
        path = tbc._path(
            hops=tuple(hops),
            handoffs=handoffs,
            declared_before_outcomes=cfg["declared_before_outcomes"],
        )
        report = evaluate_bridge_path(path)
        return report.verdict is BridgePathVerdict.COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY

    def _c(rows):
        return [dict(rows[0])]

    def inflate_hop_errors(rows, rng):
        rows = _c(rows)
        rows[0]["hop_errors"] = (rng.uniform(0.3, 2.0), rng.uniform(0.3, 2.0))
        return rows

    def break_carried_invariant(rows, rng):
        rows = _c(rows)
        rows[0]["break_invariant_on_hop"] = rng.choice([0, 1])
        return rows

    def scramble_junction_identity(rows, rng):
        rows = _c(rows)
        rows[0]["junction"] = _rand_token(rng)
        return rows

    def posthoc_path_declaration(rows, rng):
        rows = _c(rows)
        rows[0]["declared_before_outcomes"] = False
        return rows

    def mismatch_error_semantics(rows, rng):
        rows = _c(rows)
        rows[0]["hop_semantics"] = ("certified_metric_v1", _rand_token(rng))
        return rows

    def drop_handoffs(rows, rng):
        rows = _c(rows)
        rows[0]["keep_handoffs"] = False
        return rows

    def fail_role_compatibility(rows, rng):
        rows = _c(rows)
        rows[0]["compat"] = False
        return rows

    return run_battery(
        gate_id="bridge_composition.evaluate_bridge_path",
        gate=gate,
        evidence=evidence,
        perturbations={
            "inflate_hop_error_bounds": inflate_hop_errors,
            "break_carried_invariant": break_carried_invariant,
            "scramble_junction_identity": scramble_junction_identity,
            "posthoc_path_declaration": posthoc_path_declaration,
            "mismatch_error_semantics": mismatch_error_semantics,
            "drop_handoffs": drop_handoffs,
            "fail_role_compatibility": fail_role_compatibility,
        },
        notes="pass := COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY on the valid two-hop path",
    )


# =========================================================================
# Step 6b — composition: solution_assembly.validate_solution_assembly
# =========================================================================

def step6b():
    import test_unified_solver_framework as tusf
    from rakl.proof_dag import ProofEdge, ProofNodeStatus, ProofRelation
    from rakl.solution_assembly import (
        AssemblyVerdict,
        SolutionAssemblyReceipt,
        proof_dag_content_hash,
        validate_solution_assembly,
    )

    evidence = [
        {
            "dag_hash_override": None,
            "root_status": "VERIFIED",
            "stmt_hash": "h2",
            "source_hash": "artifact",
            "selected": ("lemma", "root"),
            "add_verified_refuter": False,
        }
    ]

    def gate(rows) -> bool:
        cfg = rows[0]
        dag = tusf._verified_dag()
        if cfg["root_status"] != "VERIFIED":
            nodes = tuple(
                replace(n, status=ProofNodeStatus[cfg["root_status"]]) if n.node_id == "root" else n
                for n in dag.nodes
            )
            dag = replace(dag, nodes=nodes)
        if cfg["add_verified_refuter"]:
            from rakl.proof_dag import ProofNode, ProofNodeKind

            refuter = ProofNode(
                "refuter", ProofNodeKind.LEMMA, "h3", ProofNodeStatus.VERIFIED, "receipt-3"
            )
            dag = replace(
                dag,
                nodes=dag.nodes + (refuter,),
                edges=dag.edges + (ProofEdge("refuter", "root", ProofRelation.REFUTES),),
            )
        dag_hash = cfg["dag_hash_override"] or proof_dag_content_hash(dag)
        receipt = SolutionAssemblyReceipt(
            "assembly-sweep",
            "root",
            (),
            tuple(cfg["selected"]),
            (),
            dag_hash,
            "artifact",
            tusf._proof_receipt(
                theorem_statement_hash=cfg["stmt_hash"], source_hash=cfg["source_hash"]
            ),
        )
        report = validate_solution_assembly(dag, receipt)
        return report.verdict is AssemblyVerdict.READY_FOR_EXTERNAL_AUTHORITY_GATE

    def _c(rows):
        return [dict(rows[0])]

    def scramble_dag_hash(rows, rng):
        rows = _c(rows)
        rows[0]["dag_hash_override"] = _rand_token(rng)
        return rows

    def unverify_root(rows, rng):
        rows = _c(rows)
        rows[0]["root_status"] = rng.choice(["PROPOSED", "REFUTED", "BLOCKED"])
        return rows

    def mismatch_statement_hash(rows, rng):
        rows = _c(rows)
        rows[0]["stmt_hash"] = _rand_token(rng)
        return rows

    def unbind_certificate_artifact(rows, rng):
        rows = _c(rows)
        rows[0]["source_hash"] = _rand_token(rng)
        return rows

    def drop_dependency_from_selection(rows, rng):
        rows = _c(rows)
        rows[0]["selected"] = ("root",)
        return rows

    def verified_refutation_conflict(rows, rng):
        rows = _c(rows)
        rows[0]["add_verified_refuter"] = True
        return rows

    return run_battery(
        gate_id="solution_assembly.validate_solution_assembly",
        gate=gate,
        evidence=evidence,
        perturbations={
            "scramble_proof_dag_hash": scramble_dag_hash,
            "unverify_root_node": unverify_root,
            "mismatch_statement_hash": mismatch_statement_hash,
            "unbind_certificate_artifact": unbind_certificate_artifact,
            "drop_dependency_from_selection": drop_dependency_from_selection,
            "verified_refutation_conflict": verified_refutation_conflict,
        },
        notes="pass := READY_FOR_EXTERNAL_AUTHORITY_GATE on the verified two-node DAG",
    )


# =========================================================================
# Step 7 — navigation: support_solver.solve route acceptance
# =========================================================================

def step7():
    from rakl.support_solver import (
        Atom,
        Obstruction,
        Outcome,
        SupportEdge,
        SupportStructure,
        Target,
        solve,
    )

    atom_ids = ("start", "m1", "m2", "goal")
    evidence = [
        {"kind": "meta", "goal": "goal", "required_authority": 3, "obstructions": ()},
        {"kind": "edge", "source": "start", "target": "m1", "cost": 1.0, "licensed_at": 3},
        {"kind": "edge", "source": "m1", "target": "m2", "cost": 1.0, "licensed_at": 3},
        {"kind": "edge", "source": "m2", "target": "goal", "cost": 1.0, "licensed_at": 3},
    ]

    def gate(rows) -> bool:
        meta = next(r for r in rows if r["kind"] == "meta")
        edges = tuple(
            SupportEdge(r["source"], r["target"], r["cost"], r["licensed_at"])
            for r in rows
            if r["kind"] == "edge"
        )
        structure = SupportStructure(
            structure_id="SS-sweep",
            atoms=tuple(Atom(atom_id=a) for a in atom_ids),
            edges=edges,
            obstructions=tuple(
                Obstruction(obstruction_id=f"OB{i}", cover=frozenset(cov))
                for i, cov in enumerate(meta["obstructions"])
            ),
        )
        target = Target(
            target_id="T-sweep",
            qoi="sweep",
            goal_atom=meta["goal"],
            required_authority=meta["required_authority"],
        )
        report = solve(structure, target, start="start")
        return report.outcome is Outcome.REACHED

    def _c(rows):
        return [dict(r) for r in rows]

    def degrade_edge_licensing(rows, rng):
        rows = _c(rows)
        for r in rows:
            if r["kind"] == "edge":
                r["licensed_at"] = 0
        return rows

    def drop_random_edge(rows, rng):
        edges = [r for r in rows if r["kind"] == "edge"]
        victim = rng.choice(edges)
        return [r for r in rows if r is not victim]

    def retarget_edges_away_from_goal(rows, rng):
        # v2 probe. v1 permuted the target multiset {m1,m2,goal} over the three
        # sources; exhaustive check (reproduce_insensitive_findings.py finding-3)
        # showed every permutation keeps goal reachable in this fixture, so the
        # v1 probe was structurally incapable of flipping the verdict — a probe
        # artifact, not a gate defect. v2 deletes goal from the codomain.
        rows = _c(rows)
        for r in rows:
            if r["kind"] == "edge":
                r["target"] = rng.choice(["start", "m1", "m2"])
        rows[:] = [
            r for r in rows if r["kind"] != "edge" or r["source"] != r["target"]
        ]
        return rows

    def obstruct_the_route(rows, rng):
        rows = _c(rows)
        for r in rows:
            if r["kind"] == "meta":
                r["obstructions"] = (("start", "m1"),)
        return rows

    def scramble_goal_atom(rows, rng):
        rows = _c(rows)
        for r in rows:
            if r["kind"] == "meta":
                r["goal"] = _rand_token(rng)
        return rows

    return run_battery(
        gate_id="support_solver.solve",
        gate=gate,
        evidence=evidence,
        perturbations={
            "degrade_edge_licensing_below_target": degrade_edge_licensing,
            "drop_random_edge": drop_random_edge,
            "retarget_edges_away_from_goal": retarget_edges_away_from_goal,
            "obstruct_the_route_cover": obstruct_the_route,
            "scramble_goal_atom": scramble_goal_atom,
        },
        notes=(
            "pass := Outcome.REACHED on the licensed 3-edge chain. Obstruction "
            "rejection confirmed applied on the assembled atom set inside "
            "_cheapest_route (route acceptance is obstruction-aware)."
        ),
    ) | {
        "probe_diagnoses": {
            "retarget_edges_away_from_goal": (
                "v2 probe. v1 (rewire_edge_targets: permute target multiset over "
                "sources) came back INSENSITIVE; exhaustive enumeration of all 6 "
                "permutations (reproduce_insensitive_findings.py finding-3) showed "
                "every permutation keeps goal reachable in this fixture — a probe "
                "artifact, not a gate defect. Probe corrected to delete goal from the "
                "retarget codomain; v1 result preserved here as negative history."
            )
        }
    }


# =========================================================================
# Step 8 — verification-meta: evidence_binding_certificate
# =========================================================================

def step8():
    import test_evidence_binding_certificate as tebc
    from rakl.claim_evidence import EvidenceRelation, EvidenceReviewVerdict
    from rakl.epistemic_noninterference import EvidenceRootKind
    from rakl.evidence_binding_certificate import EvidenceBindingVerdict

    evidence = [
        {
            "reviewed": "SUPPORTS",
            "kind_name": "EXTERNAL_OBSERVATION",
            "content_sha_override": None,
            "proposal_ids": ("obs-1",),
            "include_bindings": True,
            "frozen": True,
        }
    ]

    def gate(rows) -> bool:
        cfg = rows[0]
        reviewed = None if cfg["reviewed"] is None else EvidenceReviewVerdict[cfg["reviewed"]]
        binding, registration = tebc._binding(
            "obs-1",
            relation=EvidenceRelation.SUPPORTS,
            reviewed=reviewed,
            kind=EvidenceRootKind[cfg["kind_name"]],
        )
        if cfg["content_sha_override"] is not None:
            registration = replace(registration, content_sha256=cfg["content_sha_override"])
        bindings = (binding,) if cfg["include_bindings"] else ()
        result = tebc._assess(
            tebc._proposal(*cfg["proposal_ids"]),
            bindings,
            (registration,),
            frozen_before_promotion=cfg["frozen"],
        )
        return result.verdict is EvidenceBindingVerdict.VALID_FOR_PROMOTION_CHALLENGER

    def _c(rows):
        return [dict(rows[0])]

    def break_registered_content_hash(rows, rng):
        rows = _c(rows)
        rows[0]["content_sha_override"] = _rand_token(rng)
        return rows

    def flip_reviewed_relation_to_refutes(rows, rng):
        rows = _c(rows)
        rows[0]["reviewed"] = "REFUTES"
        return rows

    def unreview_semantics(rows, rng):
        rows = _c(rows)
        rows[0]["reviewed"] = None
        return rows

    def drop_all_bindings(rows, rng):
        rows = _c(rows)
        rows[0]["include_bindings"] = False
        return rows

    def scramble_proposal_evidence_ids(rows, rng):
        rows = _c(rows)
        rows[0]["proposal_ids"] = (_rand_token(rng),)
        return rows

    def rebind_as_experience_object(rows, rng):
        rows = _c(rows)
        rows[0]["kind_name"] = "TASK_EPISODE"
        return rows

    def unfreeze_binding_chronology(rows, rng):
        rows = _c(rows)
        rows[0]["frozen"] = False
        return rows

    return run_battery(
        gate_id="evidence_binding_certificate.evaluate_evidence_binding_for_promotion",
        gate=gate,
        evidence=evidence,
        perturbations={
            "break_registered_content_hash": break_registered_content_hash,
            "flip_reviewed_relation_to_refutes": flip_reviewed_relation_to_refutes,
            "unreview_semantics": unreview_semantics,
            "drop_all_bindings": drop_all_bindings,
            "scramble_proposal_evidence_ids": scramble_proposal_evidence_ids,
            "rebind_as_experience_object": rebind_as_experience_object,
            "unfreeze_binding_chronology": unfreeze_binding_chronology,
        },
        notes="pass := VALID_FOR_PROMOTION_CHALLENGER on the reviewed exact-support fixture",
    )


# =========================================================================
# Step 9a — residual: epistemic_trajectory.evaluate_epistemic_trajectory
# =========================================================================

def step9a():
    import test_epistemic_trajectory as tet
    from rakl.epistemic_trajectory import TrajectoryVerdict, evaluate_epistemic_trajectory

    evidence = [
        {
            "shuffle_evidence": False,
            "leak_authority": False,
            "reorder": False,
            "drop_step": False,
            "delete_history": False,
            "scramble_actions": False,
            "unfreeze": False,
            "_seed": 0,
        }
    ]

    def gate(rows) -> bool:
        cfg = rows[0]
        rng = random.Random(cfg["_seed"])
        case = tet._clean_case()
        if cfg["unfreeze"]:
            case = replace(case, frozen_before_output=False)
        observed = list(tet._clean_observed())
        if cfg["shuffle_evidence"]:
            ev = [s.evidence_ids for s in observed]
            rng.shuffle(ev)
            # force at least one misalignment
            observed = [replace(s, evidence_ids=(("ev-" + _rand_token(rng),) if i == 1 else e))
                        for i, (s, e) in enumerate(zip(observed, ev))]
        if cfg["leak_authority"]:
            observed[2] = replace(observed[2], authority_after="A-leak")
        if cfg["reorder"]:
            idx = [s.sequence_index for s in observed]
            while True:
                rng.shuffle(idx)
                if idx != sorted(idx):
                    break
            observed = [replace(s, sequence_index=i) for s, i in zip(observed, idx)]
        if cfg["drop_step"]:
            observed = observed[:-1]
        if cfg["delete_history"]:
            observed[2] = replace(observed[2], negative_history_ids=())
        if cfg["scramble_actions"]:
            observed = [replace(s, action=_rand_token(rng)) for s in observed]
        result = evaluate_epistemic_trajectory(case, observed)
        return result.verdict is TrajectoryVerdict.PASS

    def _flag(name):
        def perturb(rows, rng):
            row = dict(rows[0])
            row[name] = True
            row["_seed"] = rng.random()
            return [row]

        return perturb

    return run_battery(
        gate_id="epistemic_trajectory.evaluate_epistemic_trajectory",
        gate=gate,
        evidence=evidence,
        perturbations={
            "shuffle_evidence_bindings": _flag("shuffle_evidence"),
            "inject_unlicensed_authority_change": _flag("leak_authority"),
            "reorder_step_sequence": _flag("reorder"),
            "drop_observed_step": _flag("drop_step"),
            "delete_negative_history": _flag("delete_history"),
            "scramble_actions": _flag("scramble_actions"),
            "unfreeze_gold_chronology": _flag("unfreeze"),
        },
        notes="pass := TrajectoryVerdict.PASS on the clean three-step known-answer case",
    )


# =========================================================================
# Step 9b — residual: diagnosis_state_machine.resolve_discriminator
# =========================================================================

def step9b():
    from rakl.diagnosis_state_machine import (
        DiagnosisVerdict,
        competing_state,
        resolve_discriminator,
    )

    evidence = [
        {
            "state_has_discriminator": True,
            "discriminator_id": "disc-1",
            "surviving": ("cause-a",),
            "evidence_receipt": "rcpt-1",
        }
    ]

    def gate(rows) -> bool:
        cfg = rows[0]
        state = competing_state(
            "D-sweep",
            ("cause-a", "cause-b"),
            discriminator_ids=("disc-1",) if cfg["state_has_discriminator"] else (),
        )
        try:
            after = resolve_discriminator(
                state,
                discriminator_id=cfg["discriminator_id"],
                surviving_causes=tuple(cfg["surviving"]),
                evidence_receipt_id=cfg["evidence_receipt"],
            )
        except ValueError:
            return False  # exception channel = gate refusal
        return after.verdict is DiagnosisVerdict.MECHANIC_GAP_IDENTIFIED

    def _c(rows):
        return [dict(rows[0])]

    def unregistered_discriminator(rows, rng):
        rows = _c(rows)
        rows[0]["discriminator_id"] = _rand_token(rng)
        return rows

    def empty_evidence_receipt(rows, rng):
        rows = _c(rows)
        rows[0]["evidence_receipt"] = ""
        return rows

    def alien_surviving_cause(rows, rng):
        rows = _c(rows)
        rows[0]["surviving"] = (_rand_token(rng),)
        return rows

    def promote_unknown_cause(rows, rng):
        rows = _c(rows)
        rows[0]["surviving"] = ("UNKNOWN",)
        return rows

    def resolve_without_required_state(rows, rng):
        rows = _c(rows)
        rows[0]["state_has_discriminator"] = False  # state becomes PARTIALLY_IDENTIFIED
        return rows

    return run_battery(
        gate_id="diagnosis_state_machine.resolve_discriminator",
        gate=gate,
        evidence=evidence,
        perturbations={
            "unregistered_discriminator": unregistered_discriminator,
            "empty_evidence_receipt": empty_evidence_receipt,
            "alien_surviving_cause": alien_surviving_cause,
            "promote_unknown_cause": promote_unknown_cause,
            "resolve_without_discriminator_required_state": resolve_without_required_state,
        },
        adapter=(
            "exception-channel gate: reject channel is ValueError; adapter maps a "
            "raise to gate=False (refusal), MECHANIC_GAP_IDENTIFIED to True"
        ),
        notes="pass := valid discriminator resolution reaching MECHANIC_GAP_IDENTIFIED",
    )


# =========================================================================

def main() -> None:
    steps = {
        "1_problem_contract": {
            "gate_status": "REGISTERED_GATE",
            "gates": [step1a(), step1b()],
        },
        "2_decomposition": {
            "gate_status": "NO_REGISTERED_GATE",
            "classification": "NO_REGISTERED_GATE",
            "evidence": (
                "src/rakl/recursive_solver.py solve_recursive (lines 149-252) is a solver "
                "loop, not a verdict-returning gate. Gating is inline: research-saturation "
                "check (AtomFiber.research_saturated), match licensing delegated to "
                "structure_space.match, LIFT precondition len(failed_attempts)>=2 at line "
                "234. No function maps decomposition evidence to PASS/FAIL/CANNOT_CHECK. "
                "Concurs with research/orion_architecture_audit_v1/AUDIT.md row 2 "
                "('no audited decomposition-quality gate')."
            ),
        },
        "3_structuralization": {
            "gate_status": "REGISTERED_GATE_PARTIAL",
            "gates": [step3_real()],
            "sub_finding": {
                "reduction_fidelity": "NO_REGISTERED_GATE",
                "evidence": (
                    "No function checks that a ReducedStructure faithfully represents its "
                    "source (AUDIT.md row 3: 'no reduction-fidelity gate at all'; PLAN "
                    "P1.6 is the registered closure item). structure_space.match gates "
                    "admission only."
                ),
            },
        },
        "4_knowledge_space": {
            "gate_status": "REGISTERED_GATE",
            "gates": [step4a(), step4b()],
        },
        "5_retrieval": {
            "gate_status": "REGISTERED_GATE",
            "gates": [step5()],
        },
        "6_composition": {
            "gate_status": "REGISTERED_GATE",
            "gates": [step6a(), step6b()],
        },
        "7_navigation": {
            "gate_status": "REGISTERED_GATE",
            "gates": [step7()],
        },
        "8_verification_meta": {
            "gate_status": "REGISTERED_GATE",
            "gates": [step8()],
        },
        "9_residual": {
            "gate_status": "REGISTERED_GATE",
            "gates": [step9a(), step9b()],
        },
    }

    out = {
        "schema_version": "rakl-solver-gate-falsifiability-sweep-v1",
        "plan_item": "research/orion_architecture_audit_v1/PLAN.md P0.2",
        "battery": "src/rakl/gate_falsifiability.py",
        "trials_per_probe": TRIALS,
        "seeds": list(SEEDS),
        "skipped_steps": {
            "transport": "under repair in parallel branch (P0.1)",
            "saturation": (
                "already audited FALSIFIABLE "
                "(research/orion_architecture_audit_v1/AUDIT.md row 5)"
            ),
        },
        "steps": steps,
        "grants_scientific_authority": False,
        "note": (
            "FALSIFIABLE means only that the gate can fail under evidence "
            "perturbation; it never certifies that a PASS is correct. Same-context "
            "audit, not independent review."
        ),
    }
    (OUT_DIR / "SWEEP.json").write_text(json.dumps(out, indent=2) + "\n")

    # Console summary
    for step_id, spec in steps.items():
        if "gates" not in spec:
            print(f"{step_id}: {spec['classification']}")
            continue
        for g in spec["gates"]:
            print(
                f"{step_id}: {g['gate_id']} -> {g['classification']} "
                f"(no-alarm={'OK' if g['no_alarm_control']['intact_evidence_passes'] else 'FAILED'}; "
                f"sensitive={len(g.get('sensitive_probes', []))}, "
                f"insensitive={len(g.get('insensitive_probes', []))})"
            )
            for pid in g.get("insensitive_probes", []):
                print(f"    INSENSITIVE: {pid}")


if __name__ == "__main__":
    main()
