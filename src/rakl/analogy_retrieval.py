"""Analogy retrieval under invention governance: proposals, never licenses.

Exact matching (``structure_space.match``) already licenses any structure sharing
required *roles* — partial coverage included. So analogy is not "less overlap":
a first draft of this module scored role overlap and was dead on arrival, because
everything it would propose was already licensed exactly. That negative is kept
in this docstring deliberately.

Analogy is the JUMP move: **different vocabulary, similar shape**. The candidates
are precisely the structures exact matching can never use — zero shared roles —
whose *relation shape* matches the problem's. What "similar" should gradedly mean
is the framework's declared open mathematics (the metric on the space); v1
therefore proposes only on an exact shape signature match — relation count and
degree multiset, a necessary condition for relation-graph isomorphism — and
refuses to rank by any tunable similarity score.

Governance is inherited from governed invention: a proposal carries non-empty
verification obligations, the first of which is exhibiting the injective
role map itself (the transport contract's S3 condition). There is no code path
from proposal to LICENSED inside this module, and a shape signature is a routing
signal, not evidence — treating it as evidence is the error the constitution
forbids.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .structure_space import ProblemStructure, StructureSpace


def _shape_signature(
    relations: frozenset[tuple[str, str]]
) -> tuple[int, tuple[tuple[int, int], ...]]:
    """Relation count plus the sorted (out, in) degree multiset.

    Equality is a *necessary* condition for relation-graph isomorphism — cheap to
    check, impossible to satisfy by accident when shapes genuinely differ, and
    carrying no tunable threshold.
    """
    out_deg: Counter[str] = Counter()
    in_deg: Counter[str] = Counter()
    for source, target in relations:
        out_deg[source] += 1
        in_deg[target] += 1
    nodes = set(out_deg) | set(in_deg)
    degrees = tuple(sorted((out_deg[n], in_deg[n]) for n in nodes))
    return (len(relations), degrees)


@dataclass(frozen=True)
class AnalogyProposal:
    """A shape-matched candidate from a foreign vocabulary. Never a license."""

    structure_id: str
    candidate_roles: frozenset[str]
    problem_roles: frozenset[str]
    verification_obligations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.verification_obligations:
            raise ValueError(
                "an analogy with no verification obligations is a self-licensed "
                "transfer, not a proposal"
            )
        if self.candidate_roles & self.problem_roles:
            raise ValueError(
                "shared roles are exact-matching territory, not analogy; "
                "route them through structure_space.match"
            )

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def is_license(self) -> bool:
        """There is no state of this object that licenses a transfer."""
        return False


def propose_analogies(
    space: StructureSpace, problem: ProblemStructure
) -> tuple[AnalogyProposal, ...]:
    """Shape-signature candidates from disjoint vocabularies. Proposals only.

    Fail-closed on both boundaries: a problem with no required relations has no
    shape to match, so nothing is proposed; a candidate sharing any role belongs
    to exact matching, not analogy. Zero-overlap alone proposes nothing — with no
    shape in common there is no analogy to verify, and proposing one would be the
    fail-open defect (licensing by absence of objection) in proposal's clothing.
    """
    if not problem.required_relations:
        return ()
    problem_shape = _shape_signature(problem.required_relations)

    proposals: list[AnalogyProposal] = []
    for reduced in space.structures:
        if reduced.roles & problem.required_roles:
            continue  # exact-matching territory
        if not reduced.relations:
            continue
        if _shape_signature(reduced.relations) != problem_shape:
            continue
        sid = reduced.structure.structure_id
        proposals.append(
            AnalogyProposal(
                structure_id=sid,
                candidate_roles=reduced.roles,
                problem_roles=problem.required_roles,
                verification_obligations=(
                    f"exhibit an injective role map from {sid} onto the problem "
                    "preserving every relation (the transport S3 condition)",
                    "verify the mapped use realizes no obstructed cover",
                    "establish the mapped structure's authority for the problem's "
                    "demanded level through the ordinary evidence path",
                ),
            )
        )
    return tuple(sorted(proposals, key=lambda p: p.structure_id))
