"""Proposal-shadow review for existential co-witness identity.

The incumbent quantifier compatibility v1 types broad scope axes.  This additive
Class-B challenger asks a narrower semantic question needed by some gluing
routes: do several role occurrences denote one existential witness, or have
independently quantified objects been silently identified?

The result has routing/gluing authority only.  It neither proves that a witness
exists nor licenses theorem, novelty, identification, review-independence, or
method-promotion claims.  It is intentionally not wired into protected or
canonical consumers.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Tuple

SCHEMA_VERSION = "quantifier-cowitness-review-v1"
AUTHORITY_CLAIM = "ROUTING_GLUING_ONLY_NOT_THEOREM"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*Z$")


class QuantifierKind(str, Enum):
    EXISTS = "EXISTS"
    FORALL = "FORALL"
    FREE_PARAMETER = "FREE_PARAMETER"
    UNKNOWN = "UNKNOWN"


class RelationKind(str, Enum):
    SAME_WITNESS = "SAME_WITNESS"
    ALPHA_RENAMED_SAME_BINDER = "ALPHA_RENAMED_SAME_BINDER"
    DISTINCT_BINDERS = "DISTINCT_BINDERS"
    UNKNOWN = "UNKNOWN"


class CoWitnessConsumer(str, Enum):
    ROUTING = "ROUTING"
    LOCAL_TO_GLOBAL_GLUING = "LOCAL_TO_GLOBAL_GLUING"
    CONTRADICTION_DIAGNOSIS = "CONTRADICTION_DIAGNOSIS"
    REVIEW = "REVIEW"
    THEOREM_AUTHORITY = "THEOREM_AUTHORITY"


class CoWitnessVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CANNOT_CHECK = "CANNOT_CHECK"


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def _canonical_json_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _require_nonempty(name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} is required")


@dataclass(frozen=True)
class BinderOccurrence:
    occurrence_id: str
    binder_id: str
    display_symbol: str
    quantifier: QuantifierKind
    scope_id: str
    object_type: str
    role: str
    evidence_pointers: Tuple[str, ...]

    def __post_init__(self) -> None:
        for name in (
            "occurrence_id",
            "binder_id",
            "display_symbol",
            "scope_id",
            "object_type",
            "role",
        ):
            _require_nonempty(name, getattr(self, name))
        if not self.evidence_pointers or any(not item.strip() for item in self.evidence_pointers):
            raise ValueError("BinderOccurrence evidence_pointers are required")

    def document(self) -> Mapping[str, Any]:
        return {
            "occurrence_id": self.occurrence_id,
            "binder_id": self.binder_id,
            "display_symbol": self.display_symbol,
            "quantifier": self.quantifier.value,
            "scope_id": self.scope_id,
            "object_type": self.object_type,
            "role": self.role,
            "evidence_pointers": list(self.evidence_pointers),
        }


@dataclass(frozen=True)
class IdentityRelation:
    relation_id: str
    left_occurrence_id: str
    right_occurrence_id: str
    kind: RelationKind
    evidence_pointers: Tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("relation_id", "left_occurrence_id", "right_occurrence_id"):
            _require_nonempty(name, getattr(self, name))
        if self.left_occurrence_id == self.right_occurrence_id:
            raise ValueError("identity relation endpoints must be distinct occurrences")
        if not self.evidence_pointers or any(not item.strip() for item in self.evidence_pointers):
            raise ValueError("IdentityRelation evidence_pointers are required")

    def document(self) -> Mapping[str, Any]:
        return {
            "relation_id": self.relation_id,
            "left_occurrence_id": self.left_occurrence_id,
            "right_occurrence_id": self.right_occurrence_id,
            "kind": self.kind.value,
            "evidence_pointers": list(self.evidence_pointers),
        }


@dataclass(frozen=True)
class JointWitnessObligation:
    obligation_id: str
    occurrence_ids: Tuple[str, ...]
    conclusion_scope: str
    rationale: str
    evidence_pointers: Tuple[str, ...]

    def __post_init__(self) -> None:
        _require_nonempty("obligation_id", self.obligation_id)
        _require_nonempty("conclusion_scope", self.conclusion_scope)
        _require_nonempty("rationale", self.rationale)
        if len(self.occurrence_ids) < 2 or len(set(self.occurrence_ids)) != len(
            self.occurrence_ids
        ):
            raise ValueError("joint witness obligation requires at least two unique occurrences")
        if any(not item.strip() for item in self.occurrence_ids):
            raise ValueError("joint witness occurrence identities must be nonempty")
        if not self.evidence_pointers or any(not item.strip() for item in self.evidence_pointers):
            raise ValueError("JointWitnessObligation evidence_pointers are required")

    def document(self) -> Mapping[str, Any]:
        return {
            "obligation_id": self.obligation_id,
            "occurrence_ids": list(self.occurrence_ids),
            "conclusion_scope": self.conclusion_scope,
            "rationale": self.rationale,
            "evidence_pointers": list(self.evidence_pointers),
        }


@dataclass(frozen=True)
class CoWitnessReview:
    review_id: str
    atom_id: str
    occurrences: Tuple[BinderOccurrence, ...]
    identity_relations: Tuple[IdentityRelation, ...]
    joint_obligations: Tuple[JointWitnessObligation, ...]
    activation_requested: bool
    evidence_pointers: Tuple[str, ...]
    recorded_at_utc: str
    schema_version: str = SCHEMA_VERSION
    authority_claim: str = AUTHORITY_CLAIM

    def __post_init__(self) -> None:
        _require_nonempty("review_id", self.review_id)
        _require_nonempty("atom_id", self.atom_id)
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"schema_version must remain {SCHEMA_VERSION}")
        if self.authority_claim != AUTHORITY_CLAIM:
            raise ValueError("authority_claim must remain ROUTING_GLUING_ONLY_NOT_THEOREM")
        if not self.occurrences:
            raise ValueError("at least one binder occurrence is required")
        occurrence_ids = tuple(item.occurrence_id for item in self.occurrences)
        if len(set(occurrence_ids)) != len(occurrence_ids):
            raise ValueError("binder occurrence ids must be unique")
        relation_ids = tuple(item.relation_id for item in self.identity_relations)
        if len(set(relation_ids)) != len(relation_ids):
            raise ValueError("identity relation ids must be unique")
        obligation_ids = tuple(item.obligation_id for item in self.joint_obligations)
        if len(set(obligation_ids)) != len(obligation_ids):
            raise ValueError("joint witness obligation ids must be unique")
        known = set(occurrence_ids)
        for relation in self.identity_relations:
            if {relation.left_occurrence_id, relation.right_occurrence_id} - known:
                raise ValueError("identity relation references unknown occurrence")
        for obligation in self.joint_obligations:
            if set(obligation.occurrence_ids) - known:
                raise ValueError("joint witness obligation references unknown occurrence")
        if self.activation_requested and not self.joint_obligations:
            raise ValueError("activated co-witness review requires a joint witness obligation")
        if not self.activation_requested and self.joint_obligations:
            raise ValueError("non-activated co-witness review cannot contain joint obligations")
        if not self.evidence_pointers or any(not item.strip() for item in self.evidence_pointers):
            raise ValueError("CoWitnessReview evidence_pointers are required")
        if not _ISO_UTC_RE.match(self.recorded_at_utc):
            raise ValueError("recorded_at_utc must be ISO-8601 UTC ending in 'Z'")

    def content(self) -> Mapping[str, Any]:
        return {
            "schema_version": self.schema_version,
            "review_id": self.review_id,
            "atom_id": self.atom_id,
            "occurrences": [item.document() for item in self.occurrences],
            "identity_relations": [item.document() for item in self.identity_relations],
            "joint_obligations": [item.document() for item in self.joint_obligations],
            "activation_requested": self.activation_requested,
            "authority_claim": self.authority_claim,
            "evidence_pointers": list(self.evidence_pointers),
            "recorded_at_utc": self.recorded_at_utc,
        }

    @property
    def review_canonical_sha256(self) -> str:
        return _canonical_json_sha256(self.content())

    def document(self) -> Mapping[str, Any]:
        payload = dict(self.content())
        payload["review_canonical_sha256"] = self.review_canonical_sha256
        return payload


@dataclass(frozen=True)
class CoWitnessAudit:
    review_id: str | None
    atom_id: str
    verdict: CoWitnessVerdict
    activated: bool
    reasons: Tuple[str, ...]
    grants_gluing_authority: bool
    grants_theorem_authority: bool = False

    @property
    def fail_closed(self) -> bool:
        return self.verdict is not CoWitnessVerdict.PASS


class _DisjointSet:
    def __init__(self, ids: Tuple[str, ...]) -> None:
        self.parent = {item: item for item in ids}

    def find(self, item: str) -> str:
        root = item
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[item] != item:
            next_item = self.parent[item]
            self.parent[item] = root
            item = next_item
        return root

    def union(self, left: str, right: str) -> None:
        left_root, right_root = self.find(left), self.find(right)
        if left_root != right_root:
            self.parent[right_root] = left_root


def _evaluate(review: CoWitnessReview) -> tuple[CoWitnessVerdict, Tuple[str, ...]]:
    if not review.activation_requested:
        return CoWitnessVerdict.PASS, ("joint_witness_review_not_activated",)

    by_id = {item.occurrence_id: item for item in review.occurrences}
    dsu = _DisjointSet(tuple(by_id))
    explicit_distinct: set[frozenset[str]] = set()
    unknown_pairs: set[frozenset[str]] = set()
    for relation in review.identity_relations:
        pair = frozenset((relation.left_occurrence_id, relation.right_occurrence_id))
        if relation.kind in {RelationKind.SAME_WITNESS, RelationKind.ALPHA_RENAMED_SAME_BINDER}:
            dsu.union(relation.left_occurrence_id, relation.right_occurrence_id)
        elif relation.kind is RelationKind.DISTINCT_BINDERS:
            explicit_distinct.add(pair)
        else:
            unknown_pairs.add(pair)

    # Equal semantic binder ids are identity assertions. Display symbols are not.
    by_binder: dict[str, list[str]] = {}
    for occurrence in review.occurrences:
        by_binder.setdefault(occurrence.binder_id, []).append(occurrence.occurrence_id)
    for ids in by_binder.values():
        for item in ids[1:]:
            dsu.union(ids[0], item)

    reasons: list[str] = []
    distinct_root_pairs: set[frozenset[str]] = set()
    for pair in explicit_distinct:
        left, right = tuple(pair)
        left_root, right_root = dsu.find(left), dsu.find(right)
        if left_root == right_root:
            reasons.append("conflicting_same_and_distinct_identity_evidence")
        else:
            distinct_root_pairs.add(frozenset((left_root, right_root)))
    if reasons:
        return CoWitnessVerdict.FAIL, tuple(sorted(set(reasons)))

    unknown_root_pairs = {
        frozenset((dsu.find(left), dsu.find(right)))
        for pair in unknown_pairs
        for left, right in (tuple(pair),)
        if dsu.find(left) != dsu.find(right)
    }

    cannot_check = False
    for obligation in review.joint_obligations:
        ids = obligation.occurrence_ids
        objects = {by_id[item].object_type for item in ids}
        quantifiers = {by_id[item].quantifier for item in ids}
        if len(objects) != 1:
            reasons.append("joint_obligation_object_type_mismatch")
        if QuantifierKind.UNKNOWN in quantifiers:
            cannot_check = True
            reasons.append("joint_obligation_quantifier_unknown")
        if any(
            kind in {QuantifierKind.FORALL, QuantifierKind.FREE_PARAMETER}
            for kind in quantifiers
        ):
            reasons.append("joint_obligation_requires_existential_occurrences")

        for left_index, left in enumerate(ids):
            for right in ids[left_index + 1 :]:
                pair = frozenset((left, right))
                left_occ, right_occ = by_id[left], by_id[right]
                root_pair = frozenset((dsu.find(left), dsu.find(right)))
                if root_pair in distinct_root_pairs:
                    reasons.append("joint_obligation_contains_distinct_binders")
                    if left_occ.display_symbol == right_occ.display_symbol:
                        reasons.append("same_display_symbol_is_not_identity_evidence")
                elif dsu.find(left) != dsu.find(right):
                    cannot_check = True
                    reasons.append("joint_identity_not_established")
                    if root_pair in unknown_root_pairs:
                        reasons.append("joint_identity_relation_unknown")

    fail_reasons = {
        "conflicting_same_and_distinct_identity_evidence",
        "joint_obligation_object_type_mismatch",
        "joint_obligation_requires_existential_occurrences",
        "joint_obligation_contains_distinct_binders",
        "same_display_symbol_is_not_identity_evidence",
    }
    if fail_reasons.intersection(reasons):
        return CoWitnessVerdict.FAIL, tuple(sorted(set(reasons)))
    if cannot_check:
        return CoWitnessVerdict.CANNOT_CHECK, tuple(sorted(set(reasons)))
    return CoWitnessVerdict.PASS, ("joint_witness_identity_established",)


def audit_cowitness_review(
    review: CoWitnessReview | None,
    *,
    expected_atom_id: str,
    consumer: CoWitnessConsumer,
    claimed_review_hash: str | None = None,
) -> CoWitnessAudit:
    """Audit a proposal-shadow co-witness packet for routing/gluing only."""

    if consumer is CoWitnessConsumer.THEOREM_AUTHORITY:
        return CoWitnessAudit(
            review_id=None if review is None else review.review_id,
            atom_id=expected_atom_id,
            verdict=CoWitnessVerdict.FAIL,
            activated=False if review is None else review.activation_requested,
            reasons=("cowitness_review_never_mints_theorem_authority",),
            grants_gluing_authority=False,
        )
    if review is None:
        return CoWitnessAudit(
            review_id=None,
            atom_id=expected_atom_id,
            verdict=CoWitnessVerdict.CANNOT_CHECK,
            activated=False,
            reasons=("cowitness_review_missing",),
            grants_gluing_authority=False,
        )
    identity_reasons: list[str] = []
    if review.atom_id != expected_atom_id:
        identity_reasons.append("atom_id_mismatch")
    if claimed_review_hash is not None:
        if not _SHA256_RE.fullmatch(claimed_review_hash):
            identity_reasons.append("claimed_review_hash_invalid")
        elif claimed_review_hash != review.review_canonical_sha256:
            identity_reasons.append("claimed_review_hash_mismatch")
    if identity_reasons:
        return CoWitnessAudit(
            review_id=review.review_id,
            atom_id=expected_atom_id,
            verdict=CoWitnessVerdict.CANNOT_CHECK,
            activated=review.activation_requested,
            reasons=tuple(identity_reasons),
            grants_gluing_authority=False,
        )

    verdict, reasons = _evaluate(review)
    return CoWitnessAudit(
        review_id=review.review_id,
        atom_id=expected_atom_id,
        verdict=verdict,
        activated=review.activation_requested,
        reasons=reasons,
        grants_gluing_authority=(verdict is CoWitnessVerdict.PASS and review.activation_requested),
    )
