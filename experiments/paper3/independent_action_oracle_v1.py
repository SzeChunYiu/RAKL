from __future__ import annotations

from typing import Mapping, Any


REQUIRED_FIELDS = (
    "candidate_present",
    "lesson_verified",
    "scope_match",
    "version_current",
    "not_refuted",
    "lineage_valid",
    "target_context_match",
    "failure_signature_match",
    "strategy_family_match",
    "negative_history_block",
    "validity_known",
    "successor_verified",
    "successor_scope_match",
    "successor_current",
)


def oracle_action(record: Mapping[str, Any]) -> str:
    """Independent declarative oracle for the structured experience-action rule.

    This module deliberately does not import the shipped candidate implementation.
    Gold is a function only of the candidate-visible structured record.  No family,
    mutation identity, hidden perturbation, expected action, confidence, or score is
    accepted as an oracle input.
    """
    missing = [name for name in REQUIRED_FIELDS if name not in record]
    if missing:
        raise ValueError("oracle record missing fields: " + ",".join(missing))

    if not bool(record["candidate_present"]):
        return "FALLBACK_SEARCH"
    if not bool(record["validity_known"]):
        return "CANNOT_CHECK"

    primary_valid = all(
        bool(record[name])
        for name in (
            "lesson_verified",
            "scope_match",
            "version_current",
            "not_refuted",
            "lineage_valid",
            "target_context_match",
            "failure_signature_match",
            "strategy_family_match",
        )
    ) and not bool(record["negative_history_block"])
    if primary_valid:
        return "APPLY_VERIFIED_LESSON"

    successor_valid = all(
        bool(record[name])
        for name in (
            "successor_verified",
            "successor_scope_match",
            "successor_current",
            "lineage_valid",
            "target_context_match",
            "failure_signature_match",
            "strategy_family_match",
        )
    )
    predecessor_disqualified = (
        not bool(record["not_refuted"])
        or not bool(record["version_current"])
        or bool(record["negative_history_block"])
    )
    if successor_valid and predecessor_disqualified:
        return "APPLY_SUCCESSOR"
    return "FALLBACK_SEARCH"
