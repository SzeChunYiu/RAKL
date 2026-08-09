from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, Optional, Tuple


class SimilarityRelation(str, Enum):
    SAME_OBJECT = "SAME_OBJECT"
    SAME_ENTITY = "SAME_ENTITY"
    SAME_GENERATOR = "SAME_GENERATOR"
    SAME_MECHANISM = "SAME_MECHANISM"
    SAME_OBSERVABLE = "SAME_OBSERVABLE"
    OBSERVATIONALLY_EQUIVALENT = "OBSERVATIONALLY_EQUIVALENT"
    ASYMPTOTICALLY_EQUIVALENT = "ASYMPTOTICALLY_EQUIVALENT"
    QOI_EQUIVALENT = "QOI_EQUIVALENT"
    APPROXIMATELY_EQUIVALENT = "APPROXIMATELY_EQUIVALENT"
    RELATIONALLY_ANALOGOUS = "RELATIONALLY_ANALOGOUS"
    CAUSALLY_ANALOGOUS = "CAUSALLY_ANALOGOUS"
    DYNAMICALLY_EQUIVALENT = "DYNAMICALLY_EQUIVALENT"
    MATHEMATICALLY_ISOMORPHIC = "MATHEMATICALLY_ISOMORPHIC"
    FUNCTIONALLY_ANALOGOUS = "FUNCTIONALLY_ANALOGOUS"
    SAME_FAILURE_MODE = "SAME_FAILURE_MODE"
    SAME_REGIME_STRUCTURE = "SAME_REGIME_STRUCTURE"
    TRANSFORMABLE_TO = "TRANSFORMABLE_TO"
    DUAL_OF = "DUAL_OF"
    LIMIT_OF = "LIMIT_OF"
    GENERALIZES = "GENERALIZES"
    SPECIAL_CASE_OF = "SPECIAL_CASE_OF"
    BRIDGE_TO = "BRIDGE_TO"


class WitnessVerdict(str, Enum):
    VALID = "VALID"
    REJECT = "REJECT"
    CANNOT_CHECK = "CANNOT_CHECK"


class AnalogyDiscoveryVerdict(str, Enum):
    CORPUS_COVERAGE_FAILURE = "CORPUS_COVERAGE_FAILURE"
    RETRIEVAL_FAILURE = "RETRIEVAL_FAILURE"
    RECOGNITION_FAILURE = "RECOGNITION_FAILURE"
    WITNESSED_ANALOGY = "WITNESSED_ANALOGY"
    TARGET_TRANSFER_REFUTED = "TARGET_TRANSFER_REFUTED"
    TARGET_TRANSFER_TEST_PASSED = "TARGET_TRANSFER_TEST_PASSED"
    TRIAL_INVALID = "TRIAL_INVALID"
    CANNOT_CHECK = "CANNOT_CHECK"


class MotifVerdict(str, Enum):
    CORROBORATED_PROPOSAL_ONLY = "CORROBORATED_PROPOSAL_ONLY"
    NO_COMMON_MOTIF = "NO_COMMON_MOTIF"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class MappingAdmissibility:
    """Predeclared constraints for a certifying similarity map."""

    family_id: str
    declared_before_fit: Optional[bool]
    constraints: Tuple[str, ...]
    constraint_violations: Tuple[str, ...]
    null_calibration_passed: Optional[bool]


@dataclass(frozen=True)
class ProbeFamily:
    """The registered family of attempts under which similarity is claimed."""

    family_id: str
    probe_ids: Tuple[str, ...]


@dataclass(frozen=True)
class SimilarityWitness:
    """A typed, scoped mapping witness; never a bare scalar similarity score."""

    relation: SimilarityRelation
    source_id: str
    target_id: str
    source_domain: str
    target_domain: str
    question_or_qoi: str
    mapping_pairs: Tuple[Tuple[str, str], ...]
    preserved: Tuple[str, ...]
    not_preserved: Tuple[str, ...]
    regime: Tuple[str, ...]
    evidence_ids: Tuple[str, ...]
    mapping_admissibility: MappingAdmissibility
    probe_family: ProbeFamily


@dataclass(frozen=True)
class DistinguishingProbeCertificate:
    """Immutable negative evidence explaining why a candidate mapping fails."""

    probe_id: str
    source_id: str
    target_id: str
    discrepancy: str
    tolerance_or_rule: str
    context: Tuple[str, ...]
    evidence_ids: Tuple[str, ...]


@dataclass(frozen=True)
class WitnessReport:
    verdict: WitnessVerdict
    reasons: Tuple[str, ...]


@dataclass(frozen=True)
class AnalogyDiscoveryObservation:
    """Observed state of one frozen analogy-discovery trial."""

    target_id: str
    designated_source_id: Optional[str]
    corpus_candidate_ids: Tuple[str, ...]
    retrieved_candidate_ids: Tuple[str, ...]
    retrieval_route: Optional[str]
    witness: Optional[SimilarityWitness]
    target_transfer_tested: Optional[bool]
    target_transfer_passed: Optional[bool]
    hidden_label_exposed: Optional[bool]
    query_frozen_before_labels: Optional[bool]


@dataclass(frozen=True)
class AnalogyDiscoveryReport:
    verdict: AnalogyDiscoveryVerdict
    reasons: Tuple[str, ...]
    witness_report: Optional[WitnessReport] = None

    @property
    def activates_authority(self) -> bool:
        """This research-only layer never promotes scientific authority itself."""
        return False


@dataclass(frozen=True)
class StructuralMotifReport:
    verdict: MotifVerdict
    common_preserved: Tuple[str, ...]
    source_domains: FrozenSet[str]
    reasons: Tuple[str, ...]

    @property
    def target_validated(self) -> bool:
        """Cross-analogy confirmation is proposal evidence, not target evidence."""
        return False


def validate_similarity_witness(witness: SimilarityWitness) -> WitnessReport:
    """Fail-closed validation of the Round-011/012 witness contract."""

    missing: list[str] = []
    for name, value in (
        ("source_id", witness.source_id),
        ("target_id", witness.target_id),
        ("source_domain", witness.source_domain),
        ("target_domain", witness.target_domain),
        ("question_or_qoi", witness.question_or_qoi),
        ("mapping_family_id", witness.mapping_admissibility.family_id),
        ("probe_family_id", witness.probe_family.family_id),
    ):
        if not value:
            missing.append(f"{name}_missing")

    if not witness.mapping_pairs:
        missing.append("mapping_pairs_missing")
    if not witness.preserved:
        missing.append("preserved_structure_missing")
    if not witness.regime:
        missing.append("regime_missing")
    if not witness.evidence_ids:
        missing.append("evidence_ids_missing")
    if not witness.probe_family.probe_ids:
        missing.append("probe_family_empty")
    if not witness.mapping_admissibility.constraints:
        missing.append("mapping_constraints_missing")

    if missing:
        return WitnessReport(WitnessVerdict.CANNOT_CHECK, tuple(missing))

    if witness.mapping_admissibility.declared_before_fit is None:
        return WitnessReport(
            WitnessVerdict.CANNOT_CHECK,
            ("mapping_family_chronology_unknown",),
        )
    if witness.mapping_admissibility.declared_before_fit is False:
        return WitnessReport(
            WitnessVerdict.REJECT,
            ("posthoc_mapping_family_expansion",),
        )

    if witness.mapping_admissibility.null_calibration_passed is None:
        return WitnessReport(
            WitnessVerdict.CANNOT_CHECK,
            ("null_calibration_unknown",),
        )
    if witness.mapping_admissibility.null_calibration_passed is False:
        return WitnessReport(
            WitnessVerdict.REJECT,
            ("structure_null_not_rejected",),
        )

    if witness.mapping_admissibility.constraint_violations:
        return WitnessReport(
            WitnessVerdict.REJECT,
            tuple(
                f"mapping_constraint_violation:{item}"
                for item in witness.mapping_admissibility.constraint_violations
            ),
        )

    contradictory = set(witness.preserved).intersection(witness.not_preserved)
    if contradictory:
        return WitnessReport(
            WitnessVerdict.REJECT,
            ("same_structure_marked_preserved_and_not_preserved",),
        )

    if any(not source or not target for source, target in witness.mapping_pairs):
        return WitnessReport(WitnessVerdict.REJECT, ("empty_mapping_role",))

    if witness.relation is SimilarityRelation.CAUSALLY_ANALOGOUS:
        if "causal_direction" not in witness.mapping_admissibility.constraints:
            return WitnessReport(
                WitnessVerdict.CANNOT_CHECK,
                ("causal_direction_constraint_missing",),
            )

    if witness.relation is SimilarityRelation.MATHEMATICALLY_ISOMORPHIC:
        if "type_or_unit_compatibility" not in witness.mapping_admissibility.constraints:
            return WitnessReport(
                WitnessVerdict.CANNOT_CHECK,
                ("type_or_unit_compatibility_constraint_missing",),
            )

    return WitnessReport(
        WitnessVerdict.VALID,
        (
            "typed_mapping_present",
            "preserved_and_not_preserved_separated",
            "scope_and_probe_family_present",
            "mapping_family_predeclared",
            "null_calibration_passed",
            "mapping_constraints_clean",
        ),
    )


def diagnose_analogy_discovery(
    observation: AnalogyDiscoveryObservation,
) -> AnalogyDiscoveryReport:
    """Localize failure across availability, retrieval, recognition and transfer.

    The designated source id is an evaluator-side answer key. A valid benchmark
    must not expose it to the retriever or mapper.
    """

    if observation.hidden_label_exposed is True:
        return AnalogyDiscoveryReport(
            AnalogyDiscoveryVerdict.TRIAL_INVALID,
            ("hidden_answer_or_relevance_label_exposed",),
        )
    if observation.query_frozen_before_labels is False:
        return AnalogyDiscoveryReport(
            AnalogyDiscoveryVerdict.TRIAL_INVALID,
            ("query_or_abstraction_modified_after_label_inspection",),
        )
    if observation.hidden_label_exposed is None:
        return AnalogyDiscoveryReport(
            AnalogyDiscoveryVerdict.CANNOT_CHECK,
            ("hidden_label_exposure_status_unknown",),
        )
    if observation.query_frozen_before_labels is None:
        return AnalogyDiscoveryReport(
            AnalogyDiscoveryVerdict.CANNOT_CHECK,
            ("query_freeze_chronology_unknown",),
        )
    if not observation.designated_source_id:
        return AnalogyDiscoveryReport(
            AnalogyDiscoveryVerdict.CANNOT_CHECK,
            ("evaluator_designated_source_missing",),
        )

    source_id = observation.designated_source_id
    if source_id not in observation.corpus_candidate_ids:
        return AnalogyDiscoveryReport(
            AnalogyDiscoveryVerdict.CORPUS_COVERAGE_FAILURE,
            ("designated_analogue_absent_from_frozen_corpus",),
        )

    if source_id not in observation.retrieved_candidate_ids:
        return AnalogyDiscoveryReport(
            AnalogyDiscoveryVerdict.RETRIEVAL_FAILURE,
            ("designated_analogue_present_but_not_retrieved",),
        )

    if observation.witness is None:
        return AnalogyDiscoveryReport(
            AnalogyDiscoveryVerdict.RECOGNITION_FAILURE,
            ("designated_analogue_retrieved_but_witness_missing",),
        )

    if observation.witness.source_id != source_id:
        return AnalogyDiscoveryReport(
            AnalogyDiscoveryVerdict.RECOGNITION_FAILURE,
            ("witness_points_to_wrong_source",),
        )
    if observation.witness.target_id != observation.target_id:
        return AnalogyDiscoveryReport(
            AnalogyDiscoveryVerdict.RECOGNITION_FAILURE,
            ("witness_points_to_wrong_target",),
        )

    witness_report = validate_similarity_witness(observation.witness)
    if witness_report.verdict is WitnessVerdict.REJECT:
        return AnalogyDiscoveryReport(
            AnalogyDiscoveryVerdict.RECOGNITION_FAILURE,
            ("retrieved_candidate_failed_witness_validation",),
            witness_report,
        )
    if witness_report.verdict is WitnessVerdict.CANNOT_CHECK:
        return AnalogyDiscoveryReport(
            AnalogyDiscoveryVerdict.CANNOT_CHECK,
            ("witness_validation_incomplete",),
            witness_report,
        )

    if observation.target_transfer_tested is None:
        return AnalogyDiscoveryReport(
            AnalogyDiscoveryVerdict.CANNOT_CHECK,
            ("target_transfer_test_status_unknown",),
            witness_report,
        )
    if observation.target_transfer_tested is False:
        return AnalogyDiscoveryReport(
            AnalogyDiscoveryVerdict.WITNESSED_ANALOGY,
            ("structural_witness_valid_target_transfer_not_tested",),
            witness_report,
        )
    if observation.target_transfer_passed is None:
        return AnalogyDiscoveryReport(
            AnalogyDiscoveryVerdict.CANNOT_CHECK,
            ("target_transfer_outcome_unknown",),
            witness_report,
        )
    if observation.target_transfer_passed is False:
        return AnalogyDiscoveryReport(
            AnalogyDiscoveryVerdict.TARGET_TRANSFER_REFUTED,
            ("target_test_refuted_transfer_structural_witness_preserved",),
            witness_report,
        )

    return AnalogyDiscoveryReport(
        AnalogyDiscoveryVerdict.TARGET_TRANSFER_TEST_PASSED,
        ("target_transfer_test_passed_separate_promotion_still_required",),
        witness_report,
    )


def corroborate_structural_motif(
    witnesses: Tuple[SimilarityWitness, ...],
) -> StructuralMotifReport:
    """Find structure shared by multiple independently sourced analogy witnesses.

    The result is deliberately proposal-only. It does not establish that the
    shared motif is causal, necessary, sufficient, or valid in the target domain.
    """

    if len(witnesses) < 2:
        return StructuralMotifReport(
            MotifVerdict.CANNOT_CHECK,
            (),
            frozenset(w.source_domain for w in witnesses),
            ("at_least_two_witnesses_required",),
        )

    reports = tuple(validate_similarity_witness(w) for w in witnesses)
    if any(report.verdict is not WitnessVerdict.VALID for report in reports):
        return StructuralMotifReport(
            MotifVerdict.CANNOT_CHECK,
            (),
            frozenset(w.source_domain for w in witnesses),
            ("one_or_more_witnesses_not_validated",),
        )

    domains = frozenset(w.source_domain for w in witnesses)
    if len(domains) < 2:
        return StructuralMotifReport(
            MotifVerdict.CANNOT_CHECK,
            (),
            domains,
            ("cross_domain_confirmation_not_established",),
        )

    common = set(witnesses[0].preserved)
    for witness in witnesses[1:]:
        common.intersection_update(witness.preserved)

    if not common:
        return StructuralMotifReport(
            MotifVerdict.NO_COMMON_MOTIF,
            (),
            domains,
            ("no_shared_preserved_structure",),
        )

    return StructuralMotifReport(
        MotifVerdict.CORROBORATED_PROPOSAL_ONLY,
        tuple(sorted(common)),
        domains,
        (
            "shared_structure_found_across_distinct_source_domains",
            "corroboration_is_not_target_validation",
        ),
    )
