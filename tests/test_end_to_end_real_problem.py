"""One real problem through every node of the RAKL solver.

The problem is real: *re-derive a named theorem of the repository's own Lean
development from its axiom-free base*. The substrate is real: every hyperedge is
a kernel-checked dependency parsed from ``formal/RaklFormal.lean``, whose
axiom-freedom CI enforces. No fixture pretends to be knowledge, and no LLM sits
anywhere in the loop — solving is mechanical traversal, which is the claim.

Every node of the solver diagram is exercised and separately asserted:

    problem contract -> decomposition -> structuralization -> space ->
    saturation -> retrieval -> transport -> composition -> navigation ->
    verification -> residual/trajectory

The run is deterministic. A second identical run must produce the identical
derivation — a solve that cannot be replayed cannot be cited.
"""

from __future__ import annotations

import re
from pathlib import Path

from rakl.certificates import (
    ORDINAL_POLICY,
    Certificate,
    CertificateKind,
    CertificateRegistry,
    CertificateState,
    certified_hyperedge,
    verify_derivation,
)
from rakl.derivation import DerivationOutcome, derive
from rakl.recursive_solver import FiberState, solve_recursive
from rakl.structure_space import (
    MatchVerdict,
    ProblemStructure,
    ReducedStructure,
    SpaceSaturation,
    StructureSpace,
    match,
    unmatched_roles,
)
from rakl.support_solver import Atom, SupportStructure

REPO = Path(__file__).resolve().parents[1]
TARGET = "no_pairwise_predicate_decides_global_realizability"
KERNEL = ORDINAL_POLICY.authority(CertificateKind.KERNEL_CHECKED)


def _lean_source() -> str:
    return (REPO / "formal" / "RaklFormal.lean").read_text(encoding="utf-8")


def _theorem_blocks() -> list[tuple[str, str]]:
    source = _lean_source()
    heads = [
        (m.start(), m.group(1))
        for m in re.finditer(r"^theorem\s+([A-Za-z_][A-Za-z0-9_.']*)", source, re.M)
    ]
    blocks = []
    for index, (start, name) in enumerate(heads):
        end = heads[index + 1][0] if index + 1 < len(heads) else len(source)
        blocks.append((name, source[start:end]))
    return blocks


def _reduce_theorem(name: str, body: str, names: list[str]) -> ReducedStructure:
    """Structuralization: one theorem block becomes one reduced structure.

    Mechanical, not model-driven: roles are the theorem and its referenced
    theorems, exactly as read from the source.
    """
    deps = frozenset(
        other for other in names
        if other != name and re.search(rf"\b{re.escape(other)}\b", body)
    )
    roles = deps | {name}
    return ReducedStructure(
        structure=SupportStructure(
            structure_id=f"lean::{name}",
            atoms=tuple(Atom(atom_id=r) for r in sorted(roles)),
            edges=(),
        ),
        roles=roles,
        relations=frozenset((d, name) for d in deps),
        provenance="formal/RaklFormal.lean",
        established_at=KERNEL,
    )


def _run_pipeline():
    blocks = _theorem_blocks()
    names = [n for n, _ in blocks]

    # NODE: problem contract — a registered target with a demanded authority.
    problem = ProblemStructure(
        problem_id="rederive-no-pairwise",
        qoi="derivability of the obstruction-identifiability theorem",
        required_roles=frozenset({TARGET}),
        required_authority=KERNEL,
    )

    # NODES: structuralization + space + saturation — reduce every source,
    # accumulate, and run two extra passes to observe flatness.
    space = StructureSpace("lean-space")
    for name, body in blocks:
        space.accumulate(_reduce_theorem(name, body, names))
    for name, body in blocks[:2]:
        space.accumulate(_reduce_theorem(name, body, names))
    saturation = space.saturation()

    # NODES: retrieval + transport — fail-closed matching at the demanded level.
    matches = match(space, problem)
    gaps = unmatched_roles(space, problem)

    # NODES: composition + navigation — AND-composition over certified edges.
    registry = CertificateRegistry()
    theorem_names = set(names)

    def checker(cert: Certificate) -> bool:
        return cert.subject in theorem_names

    hyperedges = []
    bindings: dict[str, str] = {}
    base: set[str] = set()
    for name, body in blocks:
        deps = frozenset(
            o for o in names if o != name and re.search(rf"\b{re.escape(o)}\b", body)
        )
        if not deps:
            base.add(name)
            continue
        cert = Certificate(f"CERT-{name}", CertificateKind.KERNEL_CHECKED, name)
        registry.register(cert, checker)
        edge = certified_hyperedge(
            f"lean::{name}", deps, name, f"CERT-{name}", registry
        )
        hyperedges.append(edge)
        bindings[f"lean::{name}"] = f"CERT-{name}"

    report = derive(hyperedges, base, TARGET, required_authority=KERNEL)

    # NODE: verification — re-verify every fired edge against the live registry.
    verification = (
        verify_derivation(report.dag, bindings, registry) if report.dag else None
    )
    return problem, space, saturation, matches, gaps, report, verification, base, hyperedges


def test_every_solver_node_on_one_real_problem():
    problem, space, saturation, matches, gaps, report, verification, base, edges = _run_pipeline()

    # problem contract
    assert problem.required_authority == KERNEL

    # structuralization + space: real content, kernel-graded
    assert len(space.structures) >= 20
    assert all(r.established_at == KERNEL for r in space.structures)

    # saturation: repeated reduction of the same sources goes flat
    assert saturation is SpaceSaturation.BOUNDED_SATURATED
    assert space.growth_per_round[-2:] == [0, 0]

    # retrieval: the target's own structure is licensed at kernel level
    licensed = [m for m in matches if m.verdict is MatchVerdict.LICENSED]
    assert any(TARGET in m.covered_roles for m in licensed)
    assert gaps == frozenset()

    # navigation (AND-composition): mechanically derived
    assert report.outcome is DerivationOutcome.DERIVED
    fired = {e.conclusion: e for e in report.dag.fired}
    assert {"covers_agree_on_pairwise_data", "covers_differ_on_global_realizability"} <= fired[TARGET].premises

    # verification: certificate-backed NOW, not at construction time only
    assert verification is not None
    assert verification.certificate_backed is True
    assert verification.grants_scientific_authority is False


def test_residual_node_names_the_missing_lemma_when_the_base_is_weakened():
    """Residual/trajectory: failure must name what would have to be established."""
    *_, report, verification, base, edges = _run_pipeline()
    weakened = set(base) - {"covers_agree_on_pairwise_data"}
    failed = derive(edges, weakened, TARGET, required_authority=KERNEL)
    assert failed.outcome is DerivationOutcome.UNDERIVABLE_IN_PRINCIPLE
    assert "covers_agree_on_pairwise_data" in failed.missing


def test_decomposition_node_recurses_on_the_same_real_space():
    """Recursion: the target atom, researched against the real reduced blocks."""
    blocks = _theorem_blocks()
    names = [n for n, _ in blocks]
    space = StructureSpace("lean-recursive")

    def researcher(fiber):
        # Targeted accumulation: only the blocks that actually concern the atom.
        return [
            _reduce_theorem(name, body, names)
            for name, body in blocks
            if name == fiber.atom
        ]

    problem = ProblemStructure(
        "P", "q", frozenset({TARGET}), required_authority=KERNEL
    )
    result = solve_recursive(
        space, problem,
        start=TARGET, goal=TARGET,
        researcher=researcher, decomposer=lambda atom: None,
    )
    assert any(
        f.atom == TARGET and f.state is FiberState.MATCHED for f in result.fibers
    )
    assert result.research_rounds_spent >= 1


def test_the_whole_pipeline_is_deterministic():
    """A solve that cannot be replayed cannot be cited."""
    first = _run_pipeline()
    second = _run_pipeline()
    assert [e.edge_id for e in first[5].dag.fired] == [
        e.edge_id for e in second[5].dag.fired
    ]
    assert first[5].dag.cost == second[5].dag.cost


def test_poisoning_one_certificate_breaks_exactly_that_link():
    """Verification in the loop, adversarially: corrupt ONE certificate subject
    and the previously green pipeline must go AUTHORITY_BLOCKED on that edge."""
    blocks = _theorem_blocks()
    names = [n for n, _ in blocks]
    theorem_names = set(names)
    registry = CertificateRegistry()

    def checker(cert: Certificate) -> bool:
        return cert.subject in theorem_names

    hyperedges = []
    base: set[str] = set()
    for name, body in blocks:
        deps = frozenset(
            o for o in names if o != name and re.search(rf"\b{re.escape(o)}\b", body)
        )
        if not deps:
            base.add(name)
            continue
        subject = "ghost_theorem" if name == TARGET else name
        cert = Certificate(f"CERT-{name}", CertificateKind.KERNEL_CHECKED, subject)
        registry.register(cert, checker)
        hyperedges.append(
            certified_hyperedge(f"lean::{name}", deps, name, f"CERT-{name}", registry)
        )

    assert registry.verify(f"CERT-{TARGET}") is CertificateState.FAILED
    report = derive(hyperedges, base, TARGET, required_authority=KERNEL)
    assert report.outcome is DerivationOutcome.AUTHORITY_BLOCKED
    assert f"lean::{TARGET}" in report.blocked_edges
