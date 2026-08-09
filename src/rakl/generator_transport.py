from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class AbstractionLevel(str, Enum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"
    L5 = "L5"
    L6 = "L6"


class GeneratorRelation(str, Enum):
    SHARES_CATEGORY_WITH = "SHARES_CATEGORY_WITH"
    SHARES_PARENT_WITH = "SHARES_PARENT_WITH"
    SHARES_ABSTRACT_SCHEMA_WITH = "SHARES_ABSTRACT_SCHEMA_WITH"
    SHARES_MECHANISM_FAMILY_WITH = "SHARES_MECHANISM_FAMILY_WITH"
    SHARES_GENERATOR_WITH = "SHARES_GENERATOR_WITH"


class EvidenceScope(str, Enum):
    CATEGORY_ONLY = "CATEGORY_ONLY"
    PARENT = "PARENT"
    ABSTRACT_SCHEMA = "ABSTRACT_SCHEMA"
    MECHANISM_FAMILY = "MECHANISM_FAMILY"
    GENERATOR = "GENERATOR"


class LiftVerdict(str, Enum):
    VALID = "VALID"
    REJECT = "REJECT"
    CANNOT_CHECK = "CANNOT_CHECK"


class GeneratorRelationVerdict(str, Enum):
    DISCOVERY_HINT_ONLY = "DISCOVERY_HINT_ONLY"
    RETRIEVAL_HINT_ONLY = "RETRIEVAL_HINT_ONLY"
    ANALOGY_PROPOSAL_ONLY = "ANALOGY_PROPOSAL_ONLY"
    TRANSFER_HYPOTHESIS_ONLY = "TRANSFER_HYPOTHESIS_ONLY"
    REJECT = "REJECT"
    TRIAL_INVALID = "TRIAL_INVALID"
    CANNOT_CHECK = "CANNOT_CHECK"


class GeneratorFamilyVerdict(str, Enum):
    CORRELATED_SUPPORT_ONLY = "CORRELATED_SUPPORT_ONLY"
    CORROBORATED_GENERATOR_PROPOSAL_ONLY = "CORROBORATED_GENERATOR_PROPOSAL_ONLY"
    CORROBORATED_WITH_OUTLIER_PRESERVED = "CORROBORATED_WITH_OUTLIER_PRESERVED"
    CORROBORATED_WITH_UNKNOWN_PRESERVED = "CORROBORATED_WITH_UNKNOWN_PRESERVED"
    NO_SUPPORTED_CORE = "NO_SUPPORTED_CORE"
    TRIAL_INVALID = "TRIAL_INVALID"
    CANNOT_CHECK = "CANNOT_CHECK"


class GeneratorTransportVerdict(str, Enum):
    DISCOVERY_HINT_ONLY = "DISCOVERY_HINT_ONLY"
    RETRIEVAL_HINT_ONLY = "RETRIEVAL_HINT_ONLY"
    ANALOGY_PROPOSAL_ONLY = "ANALOGY_PROPOSAL_ONLY"
    TRANSFER_HYPOTHESIS_ONLY = "TRANSFER_HYPOTHESIS_ONLY"
    TARGET_REFUTED_GENERATOR_WITNESS_PRESERVED = (
        "TARGET_REFUTED_GENERATOR_WITNESS_PRESERVED"
    )
    TARGET_TEST_PASSED_SEPARATE_PROMOTION_REQUIRED = (
        "TARGET_TEST_PASSED_SEPARATE_PROMOTION_REQUIRED"
    )
    REJECT = "REJECT"
    TRIAL_INVALID = "TRIAL_INVALID"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class GeneratorLift:
    """One contextual LIFT from an instance into a candidate generator chart."""

    instance_id: str
    instance_domain: str
    generator_id: str
    question_or_qoi: str
    abstraction_level: AbstractionLevel
    evidence_scope: EvidenceScope
    mapping_pairs: Tuple[Tuple[str, str], ...]
    preserved: Tuple[str, ...]
    not_preserved: Tuple[str, ...]
    erased: Tuple[str, ...]
    instance_specific: Tuple[str, ...]
    regime: Tuple[str, ...]
    evidence_ids: Tuple[str, ...]
    evidence_lineage_ids: Tuple[str, ...]
    environment_id: str
    intervention_or_query_ids: Tuple[str, ...]
    commutation_passed: Optional[bool]
    declared_before_outcomes: Optional[bool]


@dataclass(frozen=True)
class LiftReport:
    verdict: LiftVerdict
    reasons: Tuple[str, ...]


@dataclass(frozen=True)
class GeneratorRelationWitness:
    """Pairwise relation at a declared abstraction level and question/QoI."""

    relation: GeneratorRelation
    source_lift: GeneratorLift
    target_lift: GeneratorLift
    required_core_features: Tuple[str, ...]
    level_transition_map_id: Optional[str]
    hidden_labels_exposed: Optional[bool]
    relation_declared_before_outcomes: Optional[bool]


@dataclass(frozen=True)
class GeneratorRelationReport:
    verdict: GeneratorRelationVerdict
    reasons: Tuple[str, ...]
    source_lift_report: Optional[LiftReport] = None
    target_lift_report: Optional[LiftReport] = None

    @property
    def grants_target_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class GeneratorFamilyCandidate:
    """A predeclared hidden/shared generator candidate tested across siblings."""

    candidate_id: str
    generator_id: str
    question_or_qoi: str
    abstraction_level: AbstractionLevel
    required_core_features: Tuple[str, ...]
    lifts: Tuple[GeneratorLift, ...]
    declared_before_outcomes: Optional[bool]
    hidden_labels_exposed: Optional[bool]


@dataclass(frozen=True)
class GeneratorFamilyReport:
    verdict: GeneratorFamilyVerdict
    supported_instance_ids: Tuple[str, ...]
    outlier_instance_ids: Tuple[str, ...]
    unknown_instance_ids: Tuple[str, ...]
    evidence_lineage_ids: Tuple[str, ...]
    environment_ids: Tuple[str, ...]
    reasons: Tuple[str, ...]

    @property
    def validates_generator_as_truth(self) -> bool:
        return False


@dataclass(frozen=True)
class GeneratorTransportTrial:
    """PROJECT stage: transport one source claim through a witnessed generator."""

    trial_id: str
    relation_witness: GeneratorRelationWitness
    source_claim_id: str
    generator_claim_id: str
    target_hypothesis_id: str
    target_tested: Optional[bool]
    target_passed: Optional[bool]


@dataclass(frozen=True)
class GeneratorTransportReport:
    verdict: GeneratorTransportVerdict
    reasons: Tuple[str, ...]
    relation_report: Optional[GeneratorRelationReport] = None

    @property
    def activates_canonical_knowledge(self) -> bool:
        return False


def validate_generator_lift(lift: GeneratorLift) -> LiftReport:
    missing: list[str] = []
    for name, value in (
        ("instance_id", lift.instance_id),
        ("instance_domain", lift.instance_domain),
        ("generator_id", lift.generator_id),
        ("question_or_qoi", lift.question_or_qoi),
        ("environment_id", lift.environment_id),
    ):
        if not value:
            missing.append(f"{name}_missing")

    if not lift.mapping_pairs:
        missing.append("mapping_pairs_missing")
    if not lift.preserved:
        missing.append("preserved_structure_missing")
    if not lift.regime:
        missing.append("regime_missing")
    if not lift.evidence_ids:
        missing.append("evidence_ids_missing")
    if not lift.evidence_lineage_ids:
        missing.append("evidence_lineage_missing")

    if missing:
        return LiftReport(LiftVerdict.CANNOT_CHECK, tuple(missing))

    if lift.declared_before_outcomes is None:
        return LiftReport(
            LiftVerdict.CANNOT_CHECK,
            ("lift_freeze_chronology_unknown",),
        )
    if lift.declared_before_outcomes is False:
        return LiftReport(
            LiftVerdict.REJECT,
            ("posthoc_lift_or_generator_definition",),
        )

    contradictory = set(lift.preserved).intersection(lift.not_preserved)
    if contradictory:
        return LiftReport(
            LiftVerdict.REJECT,
            ("same_structure_preserved_and_not_preserved",),
        )

    if any(not source or not target for source, target in lift.mapping_pairs):
        return LiftReport(LiftVerdict.REJECT, ("empty_mapping_role",))

    return LiftReport(
        LiftVerdict.VALID,
        (
            "typed_instance_to_generator_mapping_present",
            "preserved_and_not_preserved_separated",
            "erasure_and_instance_specific_coordinates_explicit",
            "regime_and_evidence_lineage_present",
            "lift_declared_before_outcomes",
        ),
    )


def _scope_supports_relation(
    scope: EvidenceScope,
    relation: GeneratorRelation,
) -> bool:
    allowed = {
        GeneratorRelation.SHARES_CATEGORY_WITH: set(EvidenceScope),
        GeneratorRelation.SHARES_PARENT_WITH: {
            EvidenceScope.PARENT,
            EvidenceScope.MECHANISM_FAMILY,
            EvidenceScope.GENERATOR,
        },
        GeneratorRelation.SHARES_ABSTRACT_SCHEMA_WITH: {
            EvidenceScope.ABSTRACT_SCHEMA,
            EvidenceScope.MECHANISM_FAMILY,
            EvidenceScope.GENERATOR,
        },
        GeneratorRelation.SHARES_MECHANISM_FAMILY_WITH: {
            EvidenceScope.MECHANISM_FAMILY,
            EvidenceScope.GENERATOR,
        },
        GeneratorRelation.SHARES_GENERATOR_WITH: {EvidenceScope.GENERATOR},
    }
    return scope in allowed[relation]


def evaluate_generator_relation(
    witness: GeneratorRelationWitness,
) -> GeneratorRelationReport:
    if witness.hidden_labels_exposed is None:
        return GeneratorRelationReport(
            GeneratorRelationVerdict.CANNOT_CHECK,
            ("hidden_label_exposure_unknown",),
        )
    if witness.hidden_labels_exposed:
        return GeneratorRelationReport(
            GeneratorRelationVerdict.TRIAL_INVALID,
            ("hidden_generator_membership_or_outcome_exposed",),
        )

    if witness.relation_declared_before_outcomes is None:
        return GeneratorRelationReport(
            GeneratorRelationVerdict.CANNOT_CHECK,
            ("relation_freeze_chronology_unknown",),
        )
    if witness.relation_declared_before_outcomes is False:
        return GeneratorRelationReport(
            GeneratorRelationVerdict.TRIAL_INVALID,
            ("posthoc_relation_or_core_feature_expansion",),
        )

    source_report = validate_generator_lift(witness.source_lift)
    target_report = validate_generator_lift(witness.target_lift)
    if source_report.verdict is LiftVerdict.REJECT or target_report.verdict is LiftVerdict.REJECT:
        return GeneratorRelationReport(
            GeneratorRelationVerdict.REJECT,
            ("one_or_more_lifts_rejected",),
            source_report,
            target_report,
        )
    if (
        source_report.verdict is LiftVerdict.CANNOT_CHECK
        or target_report.verdict is LiftVerdict.CANNOT_CHECK
    ):
        return GeneratorRelationReport(
            GeneratorRelationVerdict.CANNOT_CHECK,
            ("one_or_more_lifts_incomplete",),
            source_report,
            target_report,
        )

    if witness.source_lift.question_or_qoi != witness.target_lift.question_or_qoi:
        return GeneratorRelationReport(
            GeneratorRelationVerdict.REJECT,
            ("question_or_qoi_mismatch",),
            source_report,
            target_report,
        )

    if witness.source_lift.abstraction_level != witness.target_lift.abstraction_level:
        if not witness.level_transition_map_id:
            return GeneratorRelationReport(
                GeneratorRelationVerdict.CANNOT_CHECK,
                ("abstraction_level_mismatch_without_transition_map",),
                source_report,
                target_report,
            )

    if not _scope_supports_relation(witness.source_lift.evidence_scope, witness.relation):
        return GeneratorRelationReport(
            GeneratorRelationVerdict.REJECT,
            ("source_evidence_scope_cannot_support_claimed_relation",),
            source_report,
            target_report,
        )
    if not _scope_supports_relation(witness.target_lift.evidence_scope, witness.relation):
        return GeneratorRelationReport(
            GeneratorRelationVerdict.REJECT,
            ("target_evidence_scope_cannot_support_claimed_relation",),
            source_report,
            target_report,
        )

    if not witness.required_core_features:
        return GeneratorRelationReport(
            GeneratorRelationVerdict.CANNOT_CHECK,
            ("required_generator_core_features_missing",),
            source_report,
            target_report,
        )

    for feature in witness.required_core_features:
        if (
            feature in witness.source_lift.not_preserved
            or feature in witness.target_lift.not_preserved
        ):
            return GeneratorRelationReport(
                GeneratorRelationVerdict.REJECT,
                (f"required_core_feature_explicitly_not_preserved:{feature}",),
                source_report,
                target_report,
            )
        if (
            feature not in witness.source_lift.preserved
            or feature not in witness.target_lift.preserved
        ):
            return GeneratorRelationReport(
                GeneratorRelationVerdict.CANNOT_CHECK,
                (f"required_core_feature_unresolved:{feature}",),
                source_report,
                target_report,
            )

    if not set(witness.source_lift.regime).intersection(witness.target_lift.regime):
        return GeneratorRelationReport(
            GeneratorRelationVerdict.REJECT,
            ("no_overlapping_validity_regime",),
            source_report,
            target_report,
        )

    if witness.relation is GeneratorRelation.SHARES_CATEGORY_WITH:
        return GeneratorRelationReport(
            GeneratorRelationVerdict.DISCOVERY_HINT_ONLY,
            ("shared_category_has_weak_transfer_authority",),
            source_report,
            target_report,
        )

    if witness.relation is GeneratorRelation.SHARES_PARENT_WITH:
        return GeneratorRelationReport(
            GeneratorRelationVerdict.RETRIEVAL_HINT_ONLY,
            ("shared_parent_guides_search_but_does_not_authorize_transfer",),
            source_report,
            target_report,
        )

    if witness.relation is GeneratorRelation.SHARES_ABSTRACT_SCHEMA_WITH:
        return GeneratorRelationReport(
            GeneratorRelationVerdict.ANALOGY_PROPOSAL_ONLY,
            ("shared_abstract_schema_is_not_shared_mechanism_or_generator",),
            source_report,
            target_report,
        )

    if witness.relation is GeneratorRelation.SHARES_GENERATOR_WITH:
        if witness.source_lift.generator_id != witness.target_lift.generator_id:
            return GeneratorRelationReport(
                GeneratorRelationVerdict.REJECT,
                ("generator_identity_mismatch",),
                source_report,
                target_report,
            )

    common_queries = set(witness.source_lift.intervention_or_query_ids).intersection(
        witness.target_lift.intervention_or_query_ids
    )
    if not common_queries:
        return GeneratorRelationReport(
            GeneratorRelationVerdict.CANNOT_CHECK,
            ("no_common_intervention_or_query_probe",),
            source_report,
            target_report,
        )

    if (
        witness.source_lift.commutation_passed is None
        or witness.target_lift.commutation_passed is None
    ):
        return GeneratorRelationReport(
            GeneratorRelationVerdict.CANNOT_CHECK,
            ("intervention_or_query_commutation_unknown",),
            source_report,
            target_report,
        )
    if (
        witness.source_lift.commutation_passed is False
        or witness.target_lift.commutation_passed is False
    ):
        return GeneratorRelationReport(
            GeneratorRelationVerdict.REJECT,
            ("intervention_or_query_commutation_failed",),
            source_report,
            target_report,
        )

    return GeneratorRelationReport(
        GeneratorRelationVerdict.TRANSFER_HYPOTHESIS_ONLY,
        (
            "registered_generator_or_mechanism_core_preserved",
            "validity_regime_overlaps",
            "intervention_or_query_semantics_commute",
            "target_evidence_still_required",
        ),
        source_report,
        target_report,
    )


def assess_generator_family(
    candidate: GeneratorFamilyCandidate,
) -> GeneratorFamilyReport:
    if not candidate.candidate_id or not candidate.generator_id or not candidate.question_or_qoi:
        return GeneratorFamilyReport(
            GeneratorFamilyVerdict.CANNOT_CHECK,
            (),
            (),
            (),
            (),
            (),
            ("candidate_identity_or_question_missing",),
        )
    if not candidate.required_core_features:
        return GeneratorFamilyReport(
            GeneratorFamilyVerdict.CANNOT_CHECK,
            (),
            (),
            (),
            (),
            (),
            ("required_core_features_missing",),
        )
    if candidate.hidden_labels_exposed is None:
        return GeneratorFamilyReport(
            GeneratorFamilyVerdict.CANNOT_CHECK,
            (),
            (),
            (),
            (),
            (),
            ("hidden_label_exposure_unknown",),
        )
    if candidate.hidden_labels_exposed:
        return GeneratorFamilyReport(
            GeneratorFamilyVerdict.TRIAL_INVALID,
            (),
            (),
            (),
            (),
            (),
            ("hidden_generator_membership_or_outcome_exposed",),
        )
    if candidate.declared_before_outcomes is None:
        return GeneratorFamilyReport(
            GeneratorFamilyVerdict.CANNOT_CHECK,
            (),
            (),
            (),
            (),
            (),
            ("candidate_freeze_chronology_unknown",),
        )
    if candidate.declared_before_outcomes is False:
        return GeneratorFamilyReport(
            GeneratorFamilyVerdict.TRIAL_INVALID,
            (),
            (),
            (),
            (),
            (),
            ("posthoc_generator_or_core_feature_expansion",),
        )
    if len(candidate.lifts) < 2:
        return GeneratorFamilyReport(
            GeneratorFamilyVerdict.CANNOT_CHECK,
            (),
            (),
            (),
            (),
            (),
            ("at_least_two_sibling_lifts_required",),
        )

    supported: list[str] = []
    outliers: list[str] = []
    unknowns: list[str] = []
    lineage_ids: set[str] = set()
    environment_ids: set[str] = set()

    for lift in candidate.lifts:
        report = validate_generator_lift(lift)
        if report.verdict is LiftVerdict.REJECT:
            outliers.append(lift.instance_id)
            continue
        if report.verdict is LiftVerdict.CANNOT_CHECK:
            unknowns.append(lift.instance_id)
            continue
        if lift.generator_id != candidate.generator_id:
            outliers.append(lift.instance_id)
            continue
        if lift.question_or_qoi != candidate.question_or_qoi:
            outliers.append(lift.instance_id)
            continue
        if lift.abstraction_level != candidate.abstraction_level:
            unknowns.append(lift.instance_id)
            continue

        contradicted = any(
            feature in lift.not_preserved for feature in candidate.required_core_features
        )
        complete = all(
            feature in lift.preserved for feature in candidate.required_core_features
        )
        if contradicted:
            outliers.append(lift.instance_id)
        elif complete:
            supported.append(lift.instance_id)
            lineage_ids.update(lift.evidence_lineage_ids)
            environment_ids.add(lift.environment_id)
        else:
            unknowns.append(lift.instance_id)

    if len(supported) < 2:
        return GeneratorFamilyReport(
            GeneratorFamilyVerdict.NO_SUPPORTED_CORE,
            tuple(supported),
            tuple(outliers),
            tuple(unknowns),
            tuple(sorted(lineage_ids)),
            tuple(sorted(environment_ids)),
            ("fewer_than_two_supported_sibling_realizations",),
        )

    if len(lineage_ids) < 2 or len(environment_ids) < 2:
        return GeneratorFamilyReport(
            GeneratorFamilyVerdict.CORRELATED_SUPPORT_ONLY,
            tuple(supported),
            tuple(outliers),
            tuple(unknowns),
            tuple(sorted(lineage_ids)),
            tuple(sorted(environment_ids)),
            (
                "shared_structure_observed",
                "support_not_independent_across_lineage_and_environment",
            ),
        )

    if outliers:
        verdict = GeneratorFamilyVerdict.CORROBORATED_WITH_OUTLIER_PRESERVED
        reason = "generator_core_corroborated_but_outlier_siblings_preserved"
    elif unknowns:
        verdict = GeneratorFamilyVerdict.CORROBORATED_WITH_UNKNOWN_PRESERVED
        reason = "generator_core_corroborated_but_unknown_siblings_not_forced"
    else:
        verdict = GeneratorFamilyVerdict.CORROBORATED_GENERATOR_PROPOSAL_ONLY
        reason = "generator_core_corroborated_across_lineages_and_environments"

    return GeneratorFamilyReport(
        verdict,
        tuple(supported),
        tuple(outliers),
        tuple(unknowns),
        tuple(sorted(lineage_ids)),
        tuple(sorted(environment_ids)),
        (
            reason,
            "corroboration_remains_generator_hypothesis_not_truth",
        ),
    )


def project_through_generator(
    trial: GeneratorTransportTrial,
) -> GeneratorTransportReport:
    relation_report = evaluate_generator_relation(trial.relation_witness)
    relation_to_transport = {
        GeneratorRelationVerdict.DISCOVERY_HINT_ONLY: (
            GeneratorTransportVerdict.DISCOVERY_HINT_ONLY
        ),
        GeneratorRelationVerdict.RETRIEVAL_HINT_ONLY: (
            GeneratorTransportVerdict.RETRIEVAL_HINT_ONLY
        ),
        GeneratorRelationVerdict.ANALOGY_PROPOSAL_ONLY: (
            GeneratorTransportVerdict.ANALOGY_PROPOSAL_ONLY
        ),
        GeneratorRelationVerdict.TRANSFER_HYPOTHESIS_ONLY: (
            GeneratorTransportVerdict.TRANSFER_HYPOTHESIS_ONLY
        ),
        GeneratorRelationVerdict.REJECT: GeneratorTransportVerdict.REJECT,
        GeneratorRelationVerdict.TRIAL_INVALID: GeneratorTransportVerdict.TRIAL_INVALID,
        GeneratorRelationVerdict.CANNOT_CHECK: GeneratorTransportVerdict.CANNOT_CHECK,
    }
    base_verdict = relation_to_transport[relation_report.verdict]

    if relation_report.verdict is not GeneratorRelationVerdict.TRANSFER_HYPOTHESIS_ONLY:
        return GeneratorTransportReport(
            base_verdict,
            ("relation_does_not_authorize_generator_projection",),
            relation_report,
        )

    if not trial.source_claim_id or not trial.generator_claim_id or not trial.target_hypothesis_id:
        return GeneratorTransportReport(
            GeneratorTransportVerdict.CANNOT_CHECK,
            ("source_generator_or_target_claim_identity_missing",),
            relation_report,
        )

    if trial.target_tested is None:
        return GeneratorTransportReport(
            GeneratorTransportVerdict.CANNOT_CHECK,
            ("target_test_status_unknown",),
            relation_report,
        )
    if trial.target_tested is False:
        return GeneratorTransportReport(
            GeneratorTransportVerdict.TRANSFER_HYPOTHESIS_ONLY,
            (
                "generator_projection_created_target_hypothesis",
                "target_validation_not_yet_executed",
            ),
            relation_report,
        )
    if trial.target_passed is None:
        return GeneratorTransportReport(
            GeneratorTransportVerdict.CANNOT_CHECK,
            ("target_test_outcome_unknown",),
            relation_report,
        )
    if trial.target_passed is False:
        return GeneratorTransportReport(
            GeneratorTransportVerdict.TARGET_REFUTED_GENERATOR_WITNESS_PRESERVED,
            (
                "target_test_refuted_projected_claim",
                "generator_relation_witness_preserved_as_separate_evidence",
            ),
            relation_report,
        )

    return GeneratorTransportReport(
        GeneratorTransportVerdict.TARGET_TEST_PASSED_SEPARATE_PROMOTION_REQUIRED,
        (
            "target_test_passed",
            "separate_scientific_authority_and_promotion_rules_still_apply",
        ),
        relation_report,
    )
