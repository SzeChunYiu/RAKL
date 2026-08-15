"""Observation / Information Contract — what a question permits the solver to read.

The recursive framework audit can already decide to reframe a question, revise a
measurement, audit an evaluator, ascend to an ancestor or return a resource
boundary.  What it had no reusable object for is the *information* a question
licenses: which sources may be read, which normalizers may be applied, whether
external knowledge is admissible, and which evaluator epoch grades the result.

Without that object, a persistent negative silently collapses into "the mechanic
is inadequate", when the real cause may be that the question demanded structure
the licensed inputs never contained.  A frozen contract makes that separable,
and makes the recall ceiling it implies computable *before* an epoch is spent:

    E_Omega(B) subset {g : Lic_Omega(g) = 1}
    Recall_G(E_Omega) <= |G_Omega| / |G|

That bound is contract-relative.  It says nothing about whether semantic
inference or world knowledge could recover the remaining targets — only that an
extractor confined to this contract cannot.

This is a **pursuit-side plugin**.  It adds no authority dimension, no protected
effect and no recursion layer: changing a contract changes what is searched for,
never what is true, and the authority projection is unchanged unless a
separately certified protected operation is invoked.  Evaluator *policy* changes
remain the protected evaluator path's business; this module only records which
epoch was in force and refuses to compare across a change.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from enum import Enum

from .recursive_framework_audit import AuditCoordinate, AuditNode, AuditResidual, RecursiveAuditDecision, decide


class InformationRegime(str, Enum):
    """What class of information the question licenses."""

    SOURCE_GROUNDED = "SOURCE_GROUNDED"
    SEMANTIC_NORMALIZED = "SEMANTIC_NORMALIZED"
    EXTERNAL_COMPLETION = "EXTERNAL_COMPLETION"


class QuestionTarget(str, Enum):
    """What the question is asking to be recovered."""

    VISIBLE_STRUCTURE = "VISIBLE_STRUCTURE"
    SEMANTIC_STRUCTURE = "SEMANTIC_STRUCTURE"
    EXTERNAL_COMPLETION = "EXTERNAL_COMPLETION"
    BENCHMARK_REPRODUCTION = "BENCHMARK_REPRODUCTION"


class ContractVerdict(str, Enum):
    """Pursuit/audit verdicts.  None promotes scientific authority."""

    LICENSED_VISIBLE = "LICENSED_VISIBLE"
    LICENSED_SEMANTIC = "LICENSED_SEMANTIC"
    LICENSED_EXTERNAL = "LICENSED_EXTERNAL"
    REQUIRES_NORMALIZATION = "REQUIRES_NORMALIZATION"
    REQUIRES_EXTERNAL_OR_BENCHMARK_KNOWLEDGE = "REQUIRES_EXTERNAL_OR_BENCHMARK_KNOWLEDGE"
    EVALUATOR_CONTRACT_TENSION = "EVALUATOR_CONTRACT_TENSION"
    CANNOT_CHECK = "CANNOT_CHECK"


EXTERNAL_KNOWLEDGE_FORBIDDEN = "FORBIDDEN"


@dataclass(frozen=True)
class ObservationContract:
    """A frozen statement of what information a question permits.

    Validated at construction: an invalid contract is never constructible, so a
    downstream audit cannot silently run against one.  ``validate`` remains
    available for an explicit re-check of an already-built contract.
    """

    contract_id: str
    version: str
    regime: InformationRegime
    input_sources: tuple[str, ...]
    allowed_normalizers: tuple[str, ...] = ()
    external_knowledge_policy: str = EXTERNAL_KNOWLEDGE_FORBIDDEN
    provenance_required: bool = True
    abstention_allowed: bool = True
    evaluator_policy: str = "FROZEN_GOLD"
    evaluator_epoch: str = "epoch-1"

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Raise unless every regime constraint holds."""

        if not self.contract_id or not self.version:
            raise ValueError("contract identity and version must be non-empty")
        if not self.input_sources:
            raise ValueError("a contract must license at least one input source")
        if len(set(self.input_sources)) != len(self.input_sources):
            raise ValueError("input sources must be unique")
        if len(set(self.allowed_normalizers)) != len(self.allowed_normalizers):
            raise ValueError("normalizers must be unique")
        if not self.evaluator_policy or not self.evaluator_epoch:
            raise ValueError("evaluator policy and epoch must be non-empty")

        if self.regime is InformationRegime.SOURCE_GROUNDED:
            if self.allowed_normalizers:
                raise ValueError("source-grounded regime forbids semantic normalizers")
            if self.external_knowledge_policy != EXTERNAL_KNOWLEDGE_FORBIDDEN:
                raise ValueError("source-grounded regime forbids external knowledge")
        elif self.regime is InformationRegime.SEMANTIC_NORMALIZED:
            if not self.allowed_normalizers:
                raise ValueError("semantic-normalized regime requires a named normalizer")
            if self.external_knowledge_policy != EXTERNAL_KNOWLEDGE_FORBIDDEN:
                raise ValueError("semantic-normalized regime forbids external completion")
        elif self.regime is InformationRegime.EXTERNAL_COMPLETION:
            if self.external_knowledge_policy == EXTERNAL_KNOWLEDGE_FORBIDDEN:
                raise ValueError("external-completion regime requires an explicit policy")
            if not self.provenance_required:
                raise ValueError("external completion requires provenance")
        else:  # pragma: no cover - defensive for future regimes
            raise ValueError(f"unsupported information regime: {self.regime}")

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False

    def canonical_dict(self) -> dict[str, object]:
        return {
            "contract_id": self.contract_id,
            "version": self.version,
            "regime": self.regime.value,
            "input_sources": list(self.input_sources),
            "allowed_normalizers": list(self.allowed_normalizers),
            "external_knowledge_policy": self.external_knowledge_policy,
            "provenance_required": self.provenance_required,
            "abstention_allowed": self.abstention_allowed,
            "evaluator_policy": self.evaluator_policy,
            "evaluator_epoch": self.evaluator_epoch,
        }

    def digest(self) -> str:
        payload = json.dumps(self.canonical_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def successor(self, **changes: object) -> "ObservationContract":
        """Build the successor contract implied by a change.

        A changed regime, normalizer policy or evaluator epoch is a *different*
        contract, not an edit of this one: the digest changes, and results
        gathered under the predecessor do not transfer to it.
        """

        return replace(self, **changes)  # type: ignore[arg-type]

    def supersedes(self, other: "ObservationContract") -> bool:
        """True when ``other`` is a different contract in the same lineage."""

        return other.contract_id == self.contract_id and other.digest() != self.digest()

    def stales_results_of(self, other: "ObservationContract") -> bool:
        """A contract change stales results gathered under the predecessor.

        Staling preserves those results as history under the predecessor's
        digest; nothing is deleted and nothing is relabelled as evidence for the
        successor question.
        """

        return other.digest() != self.digest()

    def comparable_to(self, other: "ObservationContract") -> bool:
        """False across an evaluator-epoch change: that closes the epoch."""

        return self.evaluator_epoch == other.evaluator_epoch


@dataclass(frozen=True)
class PairEvidence:
    """What was observed about one candidate mapping, before scoring."""

    mapping_id: str
    left_source_licensed: bool
    right_source_licensed: bool
    semantic_normalizable: bool = False
    normalizer_id: str | None = None
    external_support_declared: bool = False
    source_explicitly_disclaims: bool = False


@dataclass(frozen=True)
class QuestionContractReceipt:
    """Append-only record of one contract-relative audit.  Carries no authority."""

    contract_digest: str
    question_target: QuestionTarget
    mapping_id: str
    verdict: ContractVerdict
    evaluator_epoch: str = ""

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion_authority(self) -> bool:
        return False


def audit_pair(contract: ObservationContract, evidence: PairEvidence) -> ContractVerdict:
    """Classify one mapping under the frozen information contract.

    Order matters and is fail-closed.  An explicit source disclaimer outranks
    everything: if the licensed sources deny what the gold asserts, the tension
    is between the gold and the contract, and no amount of extraction resolves
    it.  Nothing is licensed by omission — an unlicensed pair falls through to a
    requirement, never to a pass.
    """

    contract.validate()

    if evidence.source_explicitly_disclaims:
        return ContractVerdict.EVALUATOR_CONTRACT_TENSION

    if evidence.left_source_licensed and evidence.right_source_licensed:
        return ContractVerdict.LICENSED_VISIBLE

    registered_normalizer = bool(
        evidence.normalizer_id and evidence.normalizer_id in contract.allowed_normalizers
    )

    if evidence.semantic_normalizable:
        if contract.regime is InformationRegime.SOURCE_GROUNDED:
            return ContractVerdict.REQUIRES_NORMALIZATION
        if contract.regime is InformationRegime.SEMANTIC_NORMALIZED:
            if registered_normalizer:
                return ContractVerdict.LICENSED_SEMANTIC
            return ContractVerdict.CANNOT_CHECK
        if registered_normalizer:
            return ContractVerdict.LICENSED_SEMANTIC
        if evidence.external_support_declared:
            return ContractVerdict.LICENSED_EXTERNAL
        return ContractVerdict.REQUIRES_EXTERNAL_OR_BENCHMARK_KNOWLEDGE

    if evidence.external_support_declared and contract.regime is InformationRegime.EXTERNAL_COMPLETION:
        return ContractVerdict.LICENSED_EXTERNAL

    return ContractVerdict.REQUIRES_EXTERNAL_OR_BENCHMARK_KNOWLEDGE


def issue_receipt(
    contract: ObservationContract,
    question_target: QuestionTarget,
    evidence: PairEvidence,
) -> QuestionContractReceipt:
    """Audit one mapping and bind the verdict to the contract that produced it."""

    return QuestionContractReceipt(
        contract_digest=contract.digest(),
        question_target=question_target,
        mapping_id=evidence.mapping_id,
        verdict=audit_pair(contract, evidence),
        evaluator_epoch=contract.evaluator_epoch,
    )


def recall_ceiling(licensed_gold: int, total_gold: int) -> float:
    """The contract-relative recall bound ``|G_Omega| / |G|``.

    A ceiling, not a score: it is what an extractor confined to this contract
    could reach if it were perfect, and it says nothing about whether semantic
    inference or world knowledge could recover the rest.
    """

    if total_gold <= 0:
        raise ValueError("total gold count must be positive")
    if not 0 <= licensed_gold <= total_gold:
        raise ValueError("licensed gold must lie within [0, total_gold]")
    return licensed_gold / total_gold


# ---------------------------------------------------------------------------
# Integration with the recursive framework audit
# ---------------------------------------------------------------------------

_VERDICT_COORDINATES: dict[ContractVerdict, tuple[AuditCoordinate, ...]] = {
    # The licensed sources cannot express what the question asks for: either the
    # question over-demands or the observation operator is wrong. Two plausible
    # levels, so the audit must discriminate rather than revise.
    ContractVerdict.REQUIRES_NORMALIZATION: (AuditCoordinate.QUESTION, AuditCoordinate.MEASUREMENT),
    # The gold asserts what the licensed sources deny.
    ContractVerdict.EVALUATOR_CONTRACT_TENSION: (AuditCoordinate.EVALUATOR,),
    # The question needs knowledge the contract does not license: a capability
    # and resource question, not a mechanic failure.
    ContractVerdict.REQUIRES_EXTERNAL_OR_BENCHMARK_KNOWLEDGE: (AuditCoordinate.EVIDENCE,),
    # Licensed outcomes indicate no formulation-level defect.
    ContractVerdict.LICENSED_VISIBLE: (),
    ContractVerdict.LICENSED_SEMANTIC: (),
    ContractVerdict.LICENSED_EXTERNAL: (),
    # An unregistered normalizer is an unrun check, not a failure.
    ContractVerdict.CANNOT_CHECK: (),
}


def audit_coordinates_for(verdict: ContractVerdict) -> tuple[AuditCoordinate, ...]:
    """Which pursuit coordinates a contract verdict implicates."""

    return _VERDICT_COORDINATES[verdict]


def to_audit_residual(
    verdict: ContractVerdict,
    *,
    resource_bound: bool = False,
) -> AuditResidual:
    """Project a contract verdict into the recursive audit's residual type.

    A gold-versus-source contradiction is carried as ``evaluator_invalid`` and not
    merely as an EVALUATOR cause, so it inherits the frozen chain's top priority:
    an evaluator asserting what its licensed sources deny must be audited even
    under a resource bound, or the bound would mask it.

    ``CANNOT_CHECK`` is carried as a resource bound rather than as a cause: an
    unregistered normalizer means the check did not run, and the audit must
    abstain rather than attribute the gap to any coordinate.
    """

    return AuditResidual(
        plausible_causes=audit_coordinates_for(verdict),
        evaluator_invalid=verdict is ContractVerdict.EVALUATOR_CONTRACT_TENSION,
        resource_bound=resource_bound or verdict is ContractVerdict.CANNOT_CHECK,
    )


def decide_from_contract_verdict(
    verdict: ContractVerdict,
    *,
    closure_coordinates_pass: bool = False,
    material_open_residual: bool = True,
    resource_bound: bool = False,
) -> RecursiveAuditDecision:
    """Run the frozen decision chain on a contract verdict.

    The chain itself is untouched: this only builds the node and residual it
    already accepts, so contract auditing inherits the frozen priority ordering
    instead of introducing a second one.
    """

    node = AuditNode(
        closure_coordinates_pass=closure_coordinates_pass,
        material_open_residual=material_open_residual,
    )
    return decide(node, to_audit_residual(verdict, resource_bound=resource_bound))


__all__ = [
    "ContractVerdict",
    "EXTERNAL_KNOWLEDGE_FORBIDDEN",
    "InformationRegime",
    "ObservationContract",
    "PairEvidence",
    "QuestionContractReceipt",
    "QuestionTarget",
    "audit_coordinates_for",
    "audit_pair",
    "decide_from_contract_verdict",
    "issue_receipt",
    "recall_ceiling",
    "to_audit_residual",
]
