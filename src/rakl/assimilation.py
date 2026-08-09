from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, Optional, Tuple


class AssimilationVerdict(str, Enum):
    """Governed outcomes for an external method operator before activation."""

    ELIGIBLE_FOR_SHADOW = "ELIGIBLE_FOR_SHADOW"
    EQUIVALENT_TO_INCUMBENT = "EQUIVALENT_TO_INCUMBENT"
    PARALLEL_LOCAL_VIEW = "PARALLEL_LOCAL_VIEW"
    BLOCK = "BLOCK"
    REJECT = "REJECT"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class MethodOperatorContract:
    """Typed contract for one atomic method operator proposed for RAKL.

    The contract describes an operator as a local method view.  It does not grant
    the operator any active routing or canonical-write authority.
    """

    component_id: str
    source_framework: str
    source_version: str
    target_fiber: str
    input_schema: Tuple[str, ...]
    output_schema: Tuple[str, ...]
    context_scope: Tuple[str, ...]
    assumptions: Tuple[str, ...]
    provenance_ids: Tuple[str, ...]
    may_mint: FrozenSet[str]
    must_not_mint: FrozenSet[str]
    transition_map_id: Optional[str]
    failure_modes: Tuple[str, ...]
    dependency_ids: Tuple[str, ...]
    benchmark_id: Optional[str]


@dataclass(frozen=True)
class AssimilationEvidence:
    """Externally checkable evidence about one proposed assimilation."""

    provenance_verified: Optional[bool]
    transition_verified: Optional[bool]
    authority_scope_verified: Optional[bool]
    frozen_benchmark_registered: Optional[bool]
    assumptions_declared: Optional[bool]
    context_scope_declared: Optional[bool]
    external_observation: Optional[bool]
    equivalent_to_incumbent: Optional[bool]
    compatible_with_incumbent: Optional[bool]
    negative_history_match: Optional[bool]
    requested_authorities: FrozenSet[str]


@dataclass(frozen=True)
class AssimilationReport:
    verdict: AssimilationVerdict
    reasons: Tuple[str, ...]

    @property
    def eligible_for_shadow(self) -> bool:
        return self.verdict is AssimilationVerdict.ELIGIBLE_FOR_SHADOW

    @property
    def activates_method(self) -> bool:
        """Assimilation evaluation never activates a method by itself."""

        return False


def _missing_contract_evidence(contract: MethodOperatorContract) -> tuple[str, ...]:
    missing: list[str] = []
    if not contract.component_id:
        missing.append("component_id_missing")
    if not contract.source_framework:
        missing.append("source_framework_missing")
    if not contract.source_version:
        missing.append("source_version_missing")
    if not contract.target_fiber:
        missing.append("target_fiber_missing")
    if not contract.provenance_ids:
        missing.append("provenance_ids_missing")
    if not contract.transition_map_id:
        missing.append("transition_map_missing")
    if not contract.benchmark_id:
        missing.append("benchmark_id_missing")
    return tuple(missing)


def evaluate_method_assimilation(
    contract: MethodOperatorContract,
    evidence: AssimilationEvidence,
) -> AssimilationReport:
    """Evaluate whether an external method operator may proceed to shadow testing.

    This function deliberately stops before activation.  It separates six cases:
    clean shadow eligibility, semantic equivalence, incompatible-but-useful local
    views, known blocking failures, explicit rejection, and missing evidence.
    """

    reasons: list[str] = []

    contradictory = contract.may_mint.intersection(contract.must_not_mint)
    if contradictory:
        return AssimilationReport(
            AssimilationVerdict.REJECT,
            ("authority_contract_self_contradiction",),
        )

    forbidden_requested = evidence.requested_authorities.intersection(
        contract.must_not_mint
    )
    outside_envelope = evidence.requested_authorities.difference(contract.may_mint)
    if forbidden_requested or outside_envelope:
        return AssimilationReport(
            AssimilationVerdict.REJECT,
            ("requested_authority_outside_verified_envelope",),
        )

    if evidence.negative_history_match is True:
        return AssimilationReport(
            AssimilationVerdict.REJECT,
            ("matches_preserved_negative_history",),
        )

    missing_contract = _missing_contract_evidence(contract)
    if missing_contract:
        return AssimilationReport(
            AssimilationVerdict.CANNOT_CHECK,
            missing_contract,
        )

    if evidence.external_observation is not True:
        return AssimilationReport(
            AssimilationVerdict.CANNOT_CHECK,
            ("external_observation_not_established",),
        )

    required_checks = {
        "provenance_verified": evidence.provenance_verified,
        "transition_verified": evidence.transition_verified,
        "authority_scope_verified": evidence.authority_scope_verified,
        "frozen_benchmark_registered": evidence.frozen_benchmark_registered,
        "assumptions_declared": evidence.assumptions_declared,
        "context_scope_declared": evidence.context_scope_declared,
    }
    unknown = tuple(name for name, value in required_checks.items() if value is None)
    if unknown:
        return AssimilationReport(
            AssimilationVerdict.CANNOT_CHECK,
            tuple(f"{name}_unknown" for name in unknown),
        )

    failed = tuple(name for name, value in required_checks.items() if value is False)
    if failed:
        return AssimilationReport(
            AssimilationVerdict.BLOCK,
            tuple(f"{name}_failed" for name in failed),
        )

    comparison_checks = {
        "equivalent_to_incumbent": evidence.equivalent_to_incumbent,
        "compatible_with_incumbent": evidence.compatible_with_incumbent,
        "negative_history_match": evidence.negative_history_match,
    }
    comparison_unknown = tuple(
        name for name, value in comparison_checks.items() if value is None
    )
    if comparison_unknown:
        return AssimilationReport(
            AssimilationVerdict.CANNOT_CHECK,
            tuple(f"{name}_unknown" for name in comparison_unknown),
        )

    if evidence.equivalent_to_incumbent:
        return AssimilationReport(
            AssimilationVerdict.EQUIVALENT_TO_INCUMBENT,
            ("semantic_equivalent_incumbent_operator",),
        )

    if evidence.compatible_with_incumbent is False:
        return AssimilationReport(
            AssimilationVerdict.PARALLEL_LOCAL_VIEW,
            ("method_views_do_not_glue_under_current_scope",),
        )

    reasons.append("contract_complete")
    reasons.append("authority_envelope_clean")
    reasons.append("external_evidence_checks_pass")
    reasons.append("not_equivalent_to_incumbent")
    reasons.append("compatible_for_shadow_comparison")
    return AssimilationReport(
        AssimilationVerdict.ELIGIBLE_FOR_SHADOW,
        tuple(reasons),
    )
