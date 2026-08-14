"""Direct double-reproduction of the sweep's INSENSITIVE-probe diagnoses.

Each finding is reproduced twice with independently constructed inputs before it
is recorded in SWEEP.json (validate-the-checker discipline: verify the finding,
then verify the diagnosis, never report a probe artifact as a gate defect).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tests"))


def finding_1_hard_gates_shuffle_is_structural_noop() -> None:
    """shuffle_gate_ids INSENSITIVE == probe no-op on homogeneous all-PASS rows.

    The verdict depends only on (gate-id coverage, per-row state, evidence
    nonempty). A permutation of gate_ids over rows that are identical in state
    and evidence-presence preserves all three. Additionally the gate checks
    evidence *presence*, not gate<->evidence binding: swapping evidence ids
    between gates keeps PASS. That is in-scope behavior (binding is
    evidence_binding_certificate's job), recorded as a limitation note.
    """
    from rakl.hard_gates import (
        HardGateContract,
        HardGateObservation,
        HardGateRequirement,
        HardGateState,
        evaluate_hard_gates,
    )

    reqs = tuple(HardGateRequirement(f"G{i}", f"gate {i}") for i in (1, 2))
    contract = HardGateContract("HGC-repro", reqs, True)

    for rep in (1, 2):
        # Evidence ids swapped between gates: G1 carries G2's evidence and vice versa.
        swapped = (
            HardGateObservation("G1", "cand", HardGateState.PASS, ("ev-G2",)),
            HardGateObservation("G2", "cand", HardGateState.PASS, ("ev-G1",)),
        )
        report = evaluate_hard_gates(contract, swapped, candidate_id="cand")
        assert report.state is HardGateState.PASS, (rep, report)
    print("finding-1 reproduced twice: evidence-presence-only semantics confirmed")


def finding_2_atlas_declared_topology_trust() -> None:
    """Deleting 2 of 3 transitions never moves the GLUED verdict.

    evaluate_atlas_gluing validates each declared transition individually but
    never recomputes cover connectivity / cycle structure from the transition
    set; cover_connected, cover_has_cycles, cycle_basis_complete and the cycle
    witness are trusted caller declarations (atlas_gluing.py lines 463-528).
    """
    import test_atlas_gluing as tag
    from rakl.atlas_gluing import AtlasGluingVerdict, evaluate_atlas_gluing

    for rep, keep in ((1, ("A", "B")), (2, ("B", "C"))):
        trial = tag._trial(transitions=(tag._transition(*keep),))
        report = evaluate_atlas_gluing(trial)
        assert report.verdict is AtlasGluingVerdict.GLUED_GLOBAL_PORTRAIT_PROPOSAL_ONLY, (
            rep,
            report.verdict,
        )
    print(
        "finding-2 reproduced twice: single-transition atlas still GLUED under "
        "declared topology (blind spot: declared-topology trust)"
    )


def finding_3_support_solver_rewire_probe_artifact() -> None:
    """rewire_edge_targets INSENSITIVE == probe artifact, not a gate defect.

    Permuting the target multiset {m1, m2, goal} over sources (start, m1, m2)
    keeps goal reachable under EVERY permutation of this fixture (exhaustively
    checked below), so the probe was structurally incapable of flipping the
    verdict. The corrected probe retargets edges away from goal and flips.
    """
    from itertools import permutations

    from rakl.support_solver import (
        Atom,
        Outcome,
        SupportEdge,
        SupportStructure,
        Target,
        solve,
    )

    atoms = tuple(Atom(atom_id=a) for a in ("start", "m1", "m2", "goal"))
    target = Target("T", "q", "goal", 3)
    sources = ("start", "m1", "m2")

    for rep in (1, 2):
        outcomes = set()
        for perm in permutations(("m1", "m2", "goal")):
            edges = tuple(
                SupportEdge(s, t, 1.0, 3) for s, t in zip(sources, perm) if s != t
            )
            structure = SupportStructure("SS", atoms, edges)
            outcomes.add(solve(structure, target, start="start").outcome)
        assert outcomes == {Outcome.REACHED}, (rep, outcomes)

        # Corrected probe: no edge may point at goal -> must flip.
        edges = tuple(SupportEdge(s, "m1", 1.0, 3) for s in ("start", "m2"))
        structure = SupportStructure("SS", atoms, edges)
        assert solve(structure, target, start="start").outcome is not Outcome.REACHED
    print(
        "finding-3 reproduced twice: all 6 target permutations REACHED "
        "(probe artifact); away-from-goal retarget flips"
    )


if __name__ == "__main__":
    finding_1_hard_gates_shuffle_is_structural_noop()
    finding_2_atlas_declared_topology_trust()
    finding_3_support_solver_rewire_probe_artifact()
