"""Tests for the three solver-unit completions: verification-in-the-loop,
reducer admission, and analogy-under-governance.

The real-data test binds certificates to the repository's own Lean development
and requires a poisoned certificate to demote its edge and block the derivation —
verification in the loop, demonstrated on kernel-checked substrate.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from rakl.analogy_retrieval import AnalogyProposal, propose_analogies
from rakl.certificates import (
    ORDINAL_POLICY,
    AuthorityPolicy,
    Certificate,
    CertificateKind,
    CertificateRegistry,
    CertificateState,
    certified_edge,
    certified_hyperedge,
    verify_derivation,
    verify_route,
)
from rakl.derivation import DerivationOutcome, derive
from rakl.reduction_validation import (
    PARITY_CALIBRATION_SOURCE,
    AdmissionVerdict,
    ReducerProfile,
    admit_reducer,
)
from rakl.structure_space import ProblemStructure, ReducedStructure, StructureSpace
from rakl.support_solver import Atom, Obstruction, SupportEdge, SupportStructure

REPO = Path(__file__).resolve().parents[1]


# --- certificates: authority is derived, not asserted ------------------------------


def _registry_with(cert: Certificate, ok: bool = True) -> CertificateRegistry:
    registry = CertificateRegistry()
    registry.register(cert, lambda c: ok)
    return registry


def test_live_certificate_confers_its_kinds_authority():
    cert = Certificate("C1", CertificateKind.KERNEL_CHECKED, "thm")
    edge = certified_edge("a", "b", 1.0, "C1", _registry_with(cert))
    assert edge.licensed_at == ORDINAL_POLICY.authority(CertificateKind.KERNEL_CHECKED)


def test_failed_certificate_demotes_to_the_floor():
    cert = Certificate("C1", CertificateKind.KERNEL_CHECKED, "thm")
    edge = certified_edge("a", "b", 1.0, "C1", _registry_with(cert, ok=False))
    assert edge.licensed_at == ORDINAL_POLICY.authority(CertificateKind.ASSERTED)


def test_unknown_certificate_is_the_floor_too():
    edge = certified_edge("a", "b", 1.0, "NO-SUCH", CertificateRegistry())
    assert edge.licensed_at == ORDINAL_POLICY.authority(CertificateKind.ASSERTED)


def test_raising_checker_is_cannot_check_never_live():
    registry = CertificateRegistry()
    cert = Certificate("C1", CertificateKind.EXECUTABLE_TEST, "suite")

    def boom(c):
        raise RuntimeError("checker exploded")

    registry.register(cert, boom)
    assert registry.verify("C1") is CertificateState.CANNOT_CHECK
    edge = certified_edge("a", "b", 1.0, "C1", registry)
    assert edge.licensed_at == ORDINAL_POLICY.authority(CertificateKind.ASSERTED)


def test_policy_must_be_strictly_ordered():
    with pytest.raises(ValueError, match="strictly increasing"):
        AuthorityPolicy(levels={
            CertificateKind.ASSERTED: 0,
            CertificateKind.EXTERNAL_LABEL: 2,
            CertificateKind.EXECUTABLE_TEST: 2,
            CertificateKind.KERNEL_CHECKED: 3,
        })


def test_route_verification_reports_each_edge_and_fails_closed():
    cert = Certificate("C1", CertificateKind.EXECUTABLE_TEST, "t")
    registry = _registry_with(cert)
    from rakl.support_solver import SupportRoute
    route = SupportRoute(
        atoms=("a", "b", "c"),
        edges=(SupportEdge("a", "b", 1.0, 2), SupportEdge("b", "c", 1.0, 2)),
        total_cost=2.0,
    )
    verification = verify_route(route, {("a", "b"): "C1"}, registry)
    assert verification.certificate_backed is False
    assert any("no certificate bound" in r for r in verification.reasons)

    both = verify_route(route, {("a", "b"): "C1", ("b", "c"): "C1"}, registry)
    assert both.certificate_backed is True
    assert both.grants_scientific_authority is False


# --- verification in the loop, on the repository's own mathematics -----------------


def _lean_theorem_names() -> set[str]:
    source = (REPO / "formal" / "RaklFormal.lean").read_text(encoding="utf-8")
    return set(re.findall(r"^theorem\s+([A-Za-z_][A-Za-z0-9_.']*)", source, re.M))


def _lean_checker(cert: Certificate) -> bool:
    """The certificate's subject must be a real theorem in the Lean development
    (whose axiom-freedom CI enforces). Re-parses the file at verification time."""
    return cert.subject in _lean_theorem_names()


def test_kernel_backed_derivation_end_to_end_with_poison_control():
    """Edges licensed by real Lean theorems derive; a poisoned certificate
    (naming a theorem that does not exist) demotes its edge and blocks the
    derivation at the demanded authority. Verification IS the loop here."""
    registry = CertificateRegistry()
    good = Certificate(
        "LEAN-covers", CertificateKind.KERNEL_CHECKED,
        "covers_agree_on_pairwise_data",
    )
    poison = Certificate(
        "LEAN-ghost", CertificateKind.KERNEL_CHECKED,
        "theorem_that_does_not_exist",
    )
    registry.register(good, _lean_checker)
    registry.register(poison, _lean_checker)
    assert registry.verify("LEAN-covers") is CertificateState.LIVE
    assert registry.verify("LEAN-ghost") is CertificateState.FAILED

    kernel = ORDINAL_POLICY.authority(CertificateKind.KERNEL_CHECKED)
    e1 = certified_hyperedge("h1", frozenset({"base"}), "mid", "LEAN-covers", registry)
    e2_ok = certified_hyperedge("h2", frozenset({"mid"}), "goal", "LEAN-covers", registry)
    e2_poisoned = certified_hyperedge("h2", frozenset({"mid"}), "goal", "LEAN-ghost", registry)

    derived = derive([e1, e2_ok], {"base"}, "goal", required_authority=kernel)
    assert derived.outcome is DerivationOutcome.DERIVED
    verification = verify_derivation(
        derived.dag, {"h1": "LEAN-covers", "h2": "LEAN-covers"}, registry
    )
    assert verification.certificate_backed is True

    blocked = derive([e1, e2_poisoned], {"base"}, "goal", required_authority=kernel)
    assert blocked.outcome is DerivationOutcome.AUTHORITY_BLOCKED
    assert "h2" in blocked.blocked_edges


# --- reducer admission -------------------------------------------------------------


def _structure(roles, obstructions=()):
    atoms = tuple(Atom(atom_id=r) for r in sorted(roles))
    return ReducedStructure(
        structure=SupportStructure("s-" + "-".join(sorted(roles))[:24], atoms, (), obstructions),
        roles=frozenset(roles),
    )


def _honest_reducer(text: str) -> ReducedStructure:
    """Reads the text: roles are its distinct words; parity wording yields the
    known obstruction."""
    words = frozenset(w.strip(".:;,").lower() for w in text.split() if len(w) > 3)
    obstructions = ()
    if "differs" in words and "equals" in words:
        obstructions = (Obstruction("OBS-parity", frozenset({"x", "y", "z"})),)
        words = words | {"x", "y", "z"}
    return _structure(words, obstructions)


def _text_blind_reducer(text: str) -> ReducedStructure:
    """The probe-G failure shape: same output regardless of the text."""
    return _structure({"fixed", "output"})


PROFILE = ReducerProfile("r1", author="alice", external_label_author="bob")


def test_honest_reducer_is_admitted_with_independent_labels():
    report = admit_reducer(PROFILE, _honest_reducer, ["The cat sat on the mat quietly."])
    assert report.verdict is AdmissionVerdict.ADMITTED
    assert report.admitted_kind is CertificateKind.EXTERNAL_LABEL


def test_text_blind_reducer_is_rejected():
    """One scramble-invariant source is disqualifying — no threshold to tune."""
    report = admit_reducer(PROFILE, _text_blind_reducer, ["Some source text here today."])
    assert report.verdict is AdmissionVerdict.REJECTED
    assert any("probe-G" in r for r in report.reasons)


def test_obstruction_blind_reducer_is_rejected_by_the_known_answer():
    def positive_only(text):
        structure = _honest_reducer(text)
        return ReducedStructure(
            structure=SupportStructure(
                structure.structure.structure_id + "-blind",
                structure.structure.atoms, (), (),
            ),
            roles=structure.roles,
        )

    report = admit_reducer(PROFILE, positive_only, ["A benign unrelated source text."])
    assert report.verdict is AdmissionVerdict.REJECTED
    assert any("obstruction" in r for r in report.reasons)


def test_self_authored_labels_cap_admission_at_the_floor():
    """Mechanics pass; authority does not follow without independent labels."""
    self_profile = ReducerProfile("r2", author="alice", external_label_author="alice")
    report = admit_reducer(self_profile, _honest_reducer, ["The cat sat on the mat quietly."])
    assert report.verdict is AdmissionVerdict.ADMITTED_AT_FLOOR
    assert report.admitted_kind is CertificateKind.ASSERTED
    assert any("authorship" in r for r in report.reasons)


def test_raising_reducer_is_cannot_check_not_admitted():
    def boom(text):
        raise RuntimeError("reducer exploded")

    report = admit_reducer(PROFILE, boom, ["source"])
    assert report.verdict is AdmissionVerdict.REJECTED
    assert any("CANNOT_CHECK" in r for r in report.reasons)


def test_no_samples_is_unaudited_not_admitted():
    report = admit_reducer(PROFILE, _honest_reducer, [])
    assert report.verdict is AdmissionVerdict.REJECTED
    assert any("unaudited" in r for r in report.reasons)


def test_calibration_source_wording_is_frozen():
    """The known-answer test is only known-answer if the source cannot drift."""
    assert "x equals y" in PARITY_CALIBRATION_SOURCE
    assert "x differs from z" in PARITY_CALIBRATION_SOURCE


# --- analogy under governance ------------------------------------------------------


def _spaced(*reduced):
    space = StructureSpace("s")
    for r in reduced:
        space.accumulate(r)
    return space


def _with_relations(sid, roles, relations):
    atoms = tuple(Atom(atom_id=r) for r in sorted(roles))
    return ReducedStructure(
        structure=SupportStructure(sid, atoms, ()),
        roles=frozenset(roles),
        relations=frozenset(relations),
    )


def test_shape_matched_foreign_vocabulary_is_proposed_with_obligations():
    """The JUMP: different vocabulary, same relation shape -> proposal."""
    space = _spaced(_with_relations("physics", {"p", "q", "r"}, {("p", "q"), ("q", "r")}))
    problem = ProblemStructure(
        "P", "q", frozenset({"a", "b", "c"}),
        required_relations=frozenset({("a", "b"), ("b", "c")}),
    )
    proposals = propose_analogies(space, problem)
    assert len(proposals) == 1
    top = proposals[0]
    assert top.candidate_roles == {"p", "q", "r"}
    assert any("injective role map" in o for o in top.verification_obligations)
    assert top.is_license is False
    assert top.grants_scientific_authority is False


def test_different_shape_is_not_proposed():
    space = _spaced(_with_relations("star", {"h", "x", "y"}, {("h", "x"), ("h", "y")}))
    problem = ProblemStructure(
        "P", "q", frozenset({"a", "b", "c"}),
        required_relations=frozenset({("a", "b"), ("b", "c")}),  # chain, not star
    )
    assert propose_analogies(space, problem) == ()


def test_problem_without_relations_proposes_nothing():
    """No shape to match -> fail closed, not propose-everything."""
    space = _spaced(_with_relations("any", {"p", "q"}, {("p", "q")}))
    problem = ProblemStructure("P", "q", frozenset({"a"}))
    assert propose_analogies(space, problem) == ()


def test_shared_vocabulary_is_exact_matching_territory_not_analogy():
    space = _spaced(_with_relations("overlap", {"a", "p"}, {("a", "p")}))
    problem = ProblemStructure(
        "P", "q", frozenset({"a", "b"}), required_relations=frozenset({("a", "b")})
    )
    assert propose_analogies(space, problem) == ()


def test_analogy_without_obligations_is_rejected_at_construction():
    with pytest.raises(ValueError, match="self-licensed"):
        AnalogyProposal(
            structure_id="s", candidate_roles=frozenset({"p"}),
            problem_roles=frozenset({"a"}), verification_obligations=(),
        )


def test_analogy_with_shared_roles_is_rejected_at_construction():
    with pytest.raises(ValueError, match="exact-matching territory"):
        AnalogyProposal(
            structure_id="s", candidate_roles=frozenset({"a", "p"}),
            problem_roles=frozenset({"a"}),
            verification_obligations=("map",),
        )
