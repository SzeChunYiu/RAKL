from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EvaluationTarget(str, Enum):
    """The software object the evaluation claims to have exercised."""

    SOURCE_HEAD = "SOURCE_HEAD"
    INTEGRATION_RESULT = "INTEGRATION_RESULT"


class SubjectVerdict(str, Enum):
    """Authority available from the observed subject coordinates."""

    VALID_REVISION_AND_TREE = "VALID_REVISION_AND_TREE"
    VALID_REVISION = "VALID_REVISION"
    PARTIALLY_IDENTIFIED_TREE_ONLY = "PARTIALLY_IDENTIFIED_TREE_ONLY"
    INVALID = "INVALID"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class FrozenSubjectSpec:
    """Predeclared subject semantics for one evaluation.

    ``source_sha`` and ``base_sha`` bind the proposed change and the incumbent it
    was meant to be integrated with. ``target`` states whether authority is sought
    for the source revision itself or for a synthesized integration result.
    """

    source_sha: str
    base_sha: str
    target: EvaluationTarget

    def __post_init__(self) -> None:
        if not self.source_sha:
            raise ValueError("source_sha cannot be empty")
        if not self.base_sha:
            raise ValueError("base_sha cannot be empty")


@dataclass(frozen=True)
class PlatformSubjectObservation:
    """Subject coordinates observed from the CI/VCS platform outside candidate code."""

    source_sha: str
    base_sha: str
    integration_sha: str | None = None
    integration_tree_sha: str | None = None
    externally_observed: bool = True


@dataclass(frozen=True)
class ExecutionSubjectObservation:
    """The revision/tree actually observed in the evaluator checkout or runner."""

    executed_sha: str | None = None
    executed_tree_sha: str | None = None
    externally_observed: bool = True


@dataclass(frozen=True)
class SubjectAttestationReport:
    verdict: SubjectVerdict
    reasons: tuple[str, ...]
    revision_identified: bool
    tree_identified: bool

    @property
    def valid(self) -> bool:
        return self.verdict in {
            SubjectVerdict.VALID_REVISION_AND_TREE,
            SubjectVerdict.VALID_REVISION,
        }


def verify_execution_subject(
    spec: FrozenSubjectSpec,
    platform: PlatformSubjectObservation,
    execution: ExecutionSubjectObservation,
) -> SubjectAttestationReport:
    """Fail closed while keeping revision identity distinct from tree identity.

    A matching directory tree can justify tree-scoped authority even when the exact
    revision/history object is not identified. It never silently upgrades to revision
    authority. Candidate-produced subject claims are not treated as observations.
    """

    reasons: list[str] = []

    if not platform.externally_observed:
        reasons.append("platform subject coordinates were not externally observed")
    if not execution.externally_observed:
        reasons.append("execution subject coordinates were not externally observed")
    if reasons:
        return SubjectAttestationReport(
            verdict=SubjectVerdict.CANNOT_CHECK,
            reasons=tuple(reasons),
            revision_identified=False,
            tree_identified=False,
        )

    if not platform.source_sha or not platform.base_sha:
        return SubjectAttestationReport(
            verdict=SubjectVerdict.CANNOT_CHECK,
            reasons=("platform source/base identity is incomplete",),
            revision_identified=False,
            tree_identified=False,
        )

    if platform.source_sha != spec.source_sha:
        reasons.append("platform source revision differs from frozen source revision")
    if platform.base_sha != spec.base_sha:
        reasons.append("platform base revision differs from frozen base revision")
    if reasons:
        return SubjectAttestationReport(
            verdict=SubjectVerdict.INVALID,
            reasons=tuple(reasons),
            revision_identified=False,
            tree_identified=False,
        )

    if spec.target is EvaluationTarget.SOURCE_HEAD:
        if not execution.executed_sha:
            return SubjectAttestationReport(
                verdict=SubjectVerdict.CANNOT_CHECK,
                reasons=("executed revision was not observed",),
                revision_identified=False,
                tree_identified=False,
            )
        if execution.executed_sha != spec.source_sha:
            return SubjectAttestationReport(
                verdict=SubjectVerdict.INVALID,
                reasons=("executed revision is not the declared source head",),
                revision_identified=False,
                tree_identified=bool(execution.executed_tree_sha),
            )
        return SubjectAttestationReport(
            verdict=SubjectVerdict.VALID_REVISION,
            reasons=(),
            revision_identified=True,
            tree_identified=bool(execution.executed_tree_sha),
        )

    # Integration-targeted evaluation requires an independently observed integration
    # revision or tree. Source identity alone is insufficient.
    if not platform.integration_sha and not platform.integration_tree_sha:
        return SubjectAttestationReport(
            verdict=SubjectVerdict.CANNOT_CHECK,
            reasons=("platform integration subject was not observed",),
            revision_identified=False,
            tree_identified=False,
        )
    if not execution.executed_sha and not execution.executed_tree_sha:
        return SubjectAttestationReport(
            verdict=SubjectVerdict.CANNOT_CHECK,
            reasons=("executed integration subject was not observed",),
            revision_identified=False,
            tree_identified=False,
        )

    revision_identified = bool(
        platform.integration_sha
        and execution.executed_sha
        and platform.integration_sha == execution.executed_sha
    )
    tree_identified = bool(
        platform.integration_tree_sha
        and execution.executed_tree_sha
        and platform.integration_tree_sha == execution.executed_tree_sha
    )

    if (
        platform.integration_tree_sha
        and execution.executed_tree_sha
        and platform.integration_tree_sha != execution.executed_tree_sha
    ):
        return SubjectAttestationReport(
            verdict=SubjectVerdict.INVALID,
            reasons=("executed tree differs from platform integration tree",),
            revision_identified=revision_identified,
            tree_identified=False,
        )

    if revision_identified and tree_identified:
        return SubjectAttestationReport(
            verdict=SubjectVerdict.VALID_REVISION_AND_TREE,
            reasons=(),
            revision_identified=True,
            tree_identified=True,
        )

    if revision_identified:
        return SubjectAttestationReport(
            verdict=SubjectVerdict.VALID_REVISION,
            reasons=("integration revision identified; tree not independently bound",),
            revision_identified=True,
            tree_identified=False,
        )

    if tree_identified:
        return SubjectAttestationReport(
            verdict=SubjectVerdict.PARTIALLY_IDENTIFIED_TREE_ONLY,
            reasons=(
                "integration content tree identified but exact revision/history identity is unresolved",
            ),
            revision_identified=False,
            tree_identified=True,
        )

    return SubjectAttestationReport(
        verdict=SubjectVerdict.INVALID,
        reasons=("executed subject does not match the declared integration subject",),
        revision_identified=False,
        tree_identified=False,
    )
