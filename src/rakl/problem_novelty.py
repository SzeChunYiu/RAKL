from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Tuple


class ProblemNoveltyClass(str, Enum):
    STORED = "STORED"
    RAKL_TRIVIAL = "RAKL_TRIVIAL"
    TRANSFER_NOVEL = "TRANSFER_NOVEL"
    REPRESENTATION_NOVEL = "REPRESENTATION_NOVEL"
    OPERATOR_NOVEL = "OPERATOR_NOVEL"
    ONTOLOGY_NOVEL = "ONTOLOGY_NOVEL"
    UNRESOLVED = "UNRESOLVED"


NOVEL_STRUCTURE_RANK = {
    ProblemNoveltyClass.STORED: 0,
    ProblemNoveltyClass.RAKL_TRIVIAL: 0,
    ProblemNoveltyClass.TRANSFER_NOVEL: 0,
    ProblemNoveltyClass.REPRESENTATION_NOVEL: 1,
    ProblemNoveltyClass.OPERATOR_NOVEL: 2,
    ProblemNoveltyClass.ONTOLOGY_NOVEL: 3,
    ProblemNoveltyClass.UNRESOLVED: -1,
}


@dataclass(frozen=True)
class ProblemNoveltyEvidence:
    problem_id: str
    solution_verified: bool
    retrieved_solution_id: str | None = None
    operator_ids: Tuple[str, ...] = ()
    preexisting_operator_ids: Tuple[str, ...] = ()
    transfer_witness_ids: Tuple[str, ...] = ()
    new_representation_ids: Tuple[str, ...] = ()
    new_operator_ids: Tuple[str, ...] = ()
    ontology_change_ids: Tuple[str, ...] = ()
    all_required_resources_preexisting: bool = False
    evidence_pointers: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.problem_id:
            raise ValueError("problem novelty evidence requires problem_id")
        if self.solution_verified and not self.evidence_pointers:
            raise ValueError("verified novelty classification requires evidence pointers")
        if set(self.new_operator_ids) - set(self.operator_ids):
            raise ValueError("new_operator_ids must be a subset of operator_ids")
        if set(self.new_operator_ids) & set(self.preexisting_operator_ids):
            raise ValueError("an operator cannot be both new and preexisting in one frozen packet")


@dataclass(frozen=True)
class ProblemNoveltyReport:
    problem_id: str
    novelty_class: ProblemNoveltyClass
    novel_structure_rank: int
    reasons: Tuple[str, ...]
    evidence_pointers: Tuple[str, ...]

    @property
    def required_new_problem_solving_structure(self) -> bool:
        return self.novel_structure_rank > 0

    @property
    def zero_invention_solution(self) -> bool:
        return self.novelty_class in {
            ProblemNoveltyClass.STORED,
            ProblemNoveltyClass.RAKL_TRIVIAL,
            ProblemNoveltyClass.TRANSFER_NOVEL,
        }


@dataclass(frozen=True)
class RAKLTrivialityReport:
    solved_count: int
    unresolved_count: int
    stored_count: int
    compositional_trivial_count: int
    transfer_novel_count: int
    zero_invention_count: int
    zero_invention_rate: float | None
    strict_rakl_trivial_rate: float | None
    representation_novel_count: int
    operator_novel_count: int
    ontology_novel_count: int


def classify_problem_novelty(evidence: ProblemNoveltyEvidence) -> ProblemNoveltyReport:
    """Classify the strongest genuinely new structure required by a verified solution.

    Cross-domain transfer can be novel as an application while still requiring no
    newly invented problem-solving primitive; it therefore has structure rank 0.
    """

    if not evidence.solution_verified:
        novelty = ProblemNoveltyClass.UNRESOLVED
        reasons = ("problem solution is not verified; novelty requirement cannot be closed",)
    elif evidence.ontology_change_ids:
        novelty = ProblemNoveltyClass.ONTOLOGY_NOVEL
        reasons = ("verified solution required a new ontology/schema-level representational capability",)
    elif evidence.new_operator_ids:
        novelty = ProblemNoveltyClass.OPERATOR_NOVEL
        reasons = ("verified solution required at least one newly introduced transformation/operator",)
    elif evidence.new_representation_ids:
        novelty = ProblemNoveltyClass.REPRESENTATION_NOVEL
        reasons = ("verified solution required a new representation or bridge but no new operator",)
    elif evidence.transfer_witness_ids:
        novelty = ProblemNoveltyClass.TRANSFER_NOVEL
        reasons = ("verified solution reused preexisting structure under an explicit cross-context/domain transfer witness",)
    elif evidence.retrieved_solution_id is not None:
        novelty = ProblemNoveltyClass.STORED
        reasons = ("verified solution was already registered and retrieved without structural invention",)
    else:
        preexisting = set(evidence.preexisting_operator_ids)
        all_ops_preexisting = set(evidence.operator_ids).issubset(preexisting)
        if evidence.all_required_resources_preexisting and all_ops_preexisting:
            novelty = ProblemNoveltyClass.RAKL_TRIVIAL
            reasons = ("verified solution was composed entirely from preexisting registered resources/operators",)
        else:
            novelty = ProblemNoveltyClass.UNRESOLVED
            reasons = ("solution is verified but resource ancestry is insufficient to bound structural novelty",)

    return ProblemNoveltyReport(
        problem_id=evidence.problem_id,
        novelty_class=novelty,
        novel_structure_rank=NOVEL_STRUCTURE_RANK[novelty],
        reasons=reasons,
        evidence_pointers=evidence.evidence_pointers,
    )


def assess_rakl_triviality(
    packets: Iterable[ProblemNoveltyEvidence],
) -> RAKLTrivialityReport:
    """Measure how often a task distribution requires no new problem-solving structure."""

    reports = tuple(classify_problem_novelty(packet) for packet in packets)
    solved = tuple(report for report in reports if report.novelty_class is not ProblemNoveltyClass.UNRESOLVED)
    unresolved = len(reports) - len(solved)

    def count(kind: ProblemNoveltyClass) -> int:
        return sum(report.novelty_class is kind for report in solved)

    stored = count(ProblemNoveltyClass.STORED)
    trivial = count(ProblemNoveltyClass.RAKL_TRIVIAL)
    transfer = count(ProblemNoveltyClass.TRANSFER_NOVEL)
    representation = count(ProblemNoveltyClass.REPRESENTATION_NOVEL)
    operator = count(ProblemNoveltyClass.OPERATOR_NOVEL)
    ontology = count(ProblemNoveltyClass.ONTOLOGY_NOVEL)
    zero_invention = stored + trivial + transfer
    solved_count = len(solved)
    return RAKLTrivialityReport(
        solved_count=solved_count,
        unresolved_count=unresolved,
        stored_count=stored,
        compositional_trivial_count=trivial,
        transfer_novel_count=transfer,
        zero_invention_count=zero_invention,
        zero_invention_rate=(zero_invention / solved_count) if solved_count else None,
        strict_rakl_trivial_rate=(trivial / solved_count) if solved_count else None,
        representation_novel_count=representation,
        operator_novel_count=operator,
        ontology_novel_count=ontology,
    )
