"""Demoted AI_OPERATOR closeout helpers for Paper 1 (#216) and Paper 5 (#255)."""

from __future__ import annotations

from typing import Any


def paper1_demoted_closeout_ok(receipt: dict[str, Any]) -> bool:
    return bool(
        receipt.get("schema_version") == "paper1-ai-operator-demoted-closeout-v1"
        and receipt.get("issue") == 216
        and receipt.get("authority_class") == "DEMOTED_AI_OPERATOR_NON_INDEPENDENT"
        and receipt.get("annotator_kind") == "AI_OPERATOR"
        and receipt.get("independence_class") == "NON_INDEPENDENT"
        and receipt.get("independent_review_claimed") is False
        and receipt.get("peer_review_acceptance") is False
        and receipt.get("confirmatory_authority") is False
        and receipt.get("human_reviewers_present") is False
        and receipt.get("close_recommendation") == "CLOSE_UNDER_DEMOTED_AUTHORITY"
    )


def paper5_demoted_completion_ok(receipt: dict[str, Any]) -> bool:
    return bool(
        receipt.get("schema_version") == "paper5-novelty-audit-freeze-stub-v1"
        and receipt.get("issue") == 255
        and receipt.get("status") == "AI_OPERATOR_DEMOTED_COMPLETE"
        and receipt.get("authority_class") == "DEMOTED_AI_OPERATOR_NON_INDEPENDENT"
        and receipt.get("annotator_kind") == "AI_OPERATOR"
        and receipt.get("independence_class") == "NON_INDEPENDENT"
        and receipt.get("independent_review_claimed") is False
        and receipt.get("confirmatory_authority") is False
        and receipt.get("grants_scientific_authority") is False
    )
