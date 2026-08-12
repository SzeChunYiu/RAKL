from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Callable, Mapping

from .semantic_quotient import ReconstructionReport, ValidatedQuotientView


def _artifact_hash(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return sha256(raw).hexdigest()


def reconstruct_and_verify_original(
    view: ValidatedQuotientView,
    *,
    source_problem_id: str,
    source_hash: str,
    quotient_solution: Any,
    reconstruct: Callable[[Any, Mapping[str, str]], Any],
    verify_original: Callable[[Any], str],
    evidence_pointers: tuple[str, ...] = (),
) -> tuple[Any, ReconstructionReport]:
    """Reconstruct a quotient result and run the original-problem verifier.

    ``verify_original`` must return one of ``PASS``, ``FAIL`` or ``CANNOT_CHECK``.
    Nothing in this helper promotes scientific authority; it only records whether the
    candidate survives the original problem's own registered verification path.
    """

    if not source_problem_id:
        raise ValueError("source_problem_id is required")
    if source_hash != view.source_hash:
        raise ValueError("reconstruction_source_hash_mismatch")

    bindings = dict(view.reconstruction_bindings)
    reconstructed = reconstruct(quotient_solution, bindings)
    verdict = verify_original(reconstructed)
    if verdict not in {"PASS", "FAIL", "CANNOT_CHECK"}:
        raise ValueError("original_verifier_must_return_PASS_FAIL_OR_CANNOT_CHECK")

    report = ReconstructionReport(
        quotient_id=view.quotient_id,
        quotient_view_hash=view.content_hash,
        source_problem_id=source_problem_id,
        source_hash=source_hash,
        quotient_solution_hash=_artifact_hash(quotient_solution),
        reconstructed_solution_hash=_artifact_hash(reconstructed),
        original_problem_verification=verdict,
        evidence_pointers=evidence_pointers,
    )
    return reconstructed, report
