"""Closure-eligible strict promotion facade for Paper V.

Historical assurance/DAG APIs remain importable for reproducibility.  The current
research-closure path requires BOTH:

1. content-addressed v4 mathematical assurance; and
2. an exact, content-addressed proof-source dependency manifest whose transitive
   dependency statement-hash set equals the ProofDAG checkpoint closure.

Passing this facade means only ``candidate eligible for the existing protected
research gate``.  It never grants theorem, novelty, scientific, research-value,
or publication authority by itself.
"""
from __future__ import annotations
from dataclasses import dataclass
import re
from .math_research_assurance import AssuranceVerdict, MathClaimStage, MathResearchRecord
from .math_research_assurance_v3 import AssuranceIdentityBundleV3
from .math_research_assurance_v4 import classify_math_record_v4
from .proof_dag import ProofDAG
from .proof_dag_v2 import DependencyManifestReceipt, verify_checkpoint_with_dependency_manifest

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _sha(value: str | None, field: str) -> str:
    if value is None or not _SHA256.fullmatch(value):
        raise ValueError(f"{field} must be a lowercase SHA-256 content digest")
    return value


def _validate_strict_dependency_manifest(manifest: DependencyManifestReceipt) -> None:
    """Require content identities before the historical equality checker runs.

    This validates receipt shape and identity discipline only.  It does not
    self-certify that an external extractor faithfully parsed the proof source;
    that mapping remains an explicit provenance trust root.
    """

    _sha(manifest.manifest_id, "dependency_manifest.manifest_id")
    _sha(manifest.proof_source_hash, "dependency_manifest.proof_source_hash")
    _sha(manifest.theorem_statement_hash, "dependency_manifest.theorem_statement_hash")
    _sha(manifest.extracted_by, "dependency_manifest.extracted_by")
    for index, dependency in enumerate(manifest.dependency_statement_hashes):
        _sha(dependency, f"dependency_manifest.dependency_statement_hashes[{index}]")


@dataclass(frozen=True)
class StrictMathPromotionDecision:
    stage: MathClaimStage
    assurance_verdict: AssuranceVerdict
    checkpoint_verified: bool
    eligible_new_mathematics_candidate: bool
    reasons: tuple[str, ...]

    @property
    def grants_theorem_authority(self) -> bool:
        return False

    @property
    def grants_novelty_authority(self) -> bool:
        return False

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_publication_authority(self) -> bool:
        return False


def strict_math_candidate(
    record: MathResearchRecord,
    *,
    proposer_identity_hash: str,
    identities: AssuranceIdentityBundleV3,
    literature_manifest_hash: str,
    dag: ProofDAG,
    node_id: str,
    dependency_manifest: DependencyManifestReceipt,
) -> StrictMathPromotionDecision:
    """Require the strongest local assurance and dependency path together."""

    if record.proof is None:
        return StrictMathPromotionDecision(
            MathClaimStage.FORMALIZED_UNPROVEN,
            AssuranceVerdict.CANNOT_CHECK,
            False,
            False,
            ("strict_path_requires_proof_receipt",),
        )

    try:
        _validate_strict_dependency_manifest(dependency_manifest)
        verified_dag = verify_checkpoint_with_dependency_manifest(
            dag,
            node_id=node_id,
            receipt=record.proof,
            manifest=dependency_manifest,
        )
    except ValueError as exc:
        return StrictMathPromotionDecision(
            MathClaimStage.BLOCKED_PROOF_ASSURANCE,
            AssuranceVerdict.FAIL,
            False,
            False,
            (f"strict_dependency_path_failed:{exc}",),
        )

    try:
        assurance = classify_math_record_v4(
            record,
            proposer_identity_hash=proposer_identity_hash,
            identities=identities,
            literature_manifest_hash=literature_manifest_hash,
        )
    except ValueError as exc:
        return StrictMathPromotionDecision(
            MathClaimStage.BLOCKED_PROOF_ASSURANCE,
            AssuranceVerdict.FAIL,
            True,
            False,
            (f"strict_content_identity_failed:{exc}",),
        )

    checkpoint_verified = verified_dag.node_map()[node_id].receipt_id is not None
    eligible = (
        checkpoint_verified
        and assurance.verdict is AssuranceVerdict.PASS
        and assurance.stage is MathClaimStage.NEW_MATHEMATICS_CANDIDATE
    )
    return StrictMathPromotionDecision(
        assurance.stage,
        assurance.verdict,
        checkpoint_verified,
        eligible,
        assurance.reasons + (
            "strict_v4_assurance_and_content_addressed_exact_dependency_manifest_both_required",
        ),
    )


__all__ = ["StrictMathPromotionDecision", "strict_math_candidate"]
