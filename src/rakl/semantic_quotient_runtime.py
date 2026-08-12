from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any

from .problem_fibre import compile_problem_fibre
from .semantic_quotient import ValidatedQuotientView, compile_quotient_problem_fibre


class QuotientRuntimeRoute(str, Enum):
    QUOTIENT = "QUOTIENT"
    RAW_NO_QUOTIENT = "RAW_NO_QUOTIENT"
    RAW_REJECTED = "RAW_REJECTED"
    RAW_CANNOT_CHECK = "RAW_CANNOT_CHECK"
    RAW_COST_NEGATIVE = "RAW_COST_NEGATIVE"


@dataclass(frozen=True)
class QuotientRuntimeResult:
    route: QuotientRuntimeRoute
    source_atom_id: str
    fibre: Any
    quotient_view_hash: str | None = None
    detail: str = ""

    @property
    def snapshot_hash(self) -> str:
        payload = {
            "schema": "rakl.tcsq.runtime_route.v1",
            "route": self.route.value,
            "source_atom_id": self.source_atom_id,
            "fibre_snapshot_hash": self.fibre.snapshot_hash,
            "quotient_view_hash": self.quotient_view_hash,
            "detail": self.detail,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return sha256(raw).hexdigest()


def compile_problem_fibre_with_quotient_fallback(
    source_atom: Any,
    *,
    quotient_view: ValidatedQuotientView | None = None,
    fallback_reason: str | None = None,
    estimated_net_benefit: float | None = None,
    **compile_kwargs: object,
) -> QuotientRuntimeResult:
    """Compile a validated quotient or preserve incumbent raw behaviour fail-closed.

    ``fallback_reason`` is used only when no validated view exists and may be
    ``REJECTED`` or ``CANNOT_CHECK``.  A non-positive registered net-benefit estimate
    also forces raw execution.  The helper never accepts an unvalidated proposal/report;
    those objects remain proposal-side and cannot enter solver routing.
    """

    source_atom_id = getattr(source_atom, "atom_id", "")
    if not source_atom_id:
        raise ValueError("source_atom_requires_atom_id")

    if quotient_view is None:
        if fallback_reason not in {None, "REJECTED", "CANNOT_CHECK"}:
            raise ValueError("unsupported_quotient_fallback_reason")
        raw = compile_problem_fibre(source_atom, **compile_kwargs)
        if fallback_reason == "REJECTED":
            route = QuotientRuntimeRoute.RAW_REJECTED
        elif fallback_reason == "CANNOT_CHECK":
            route = QuotientRuntimeRoute.RAW_CANNOT_CHECK
        else:
            route = QuotientRuntimeRoute.RAW_NO_QUOTIENT
        return QuotientRuntimeResult(
            route=route,
            source_atom_id=source_atom_id,
            fibre=raw,
            detail=fallback_reason or "NO_VALIDATED_QUOTIENT",
        )

    if fallback_reason is not None:
        raise ValueError("validated_quotient_and_fallback_reason_are_mutually_exclusive")

    if estimated_net_benefit is not None and estimated_net_benefit <= 0:
        raw = compile_problem_fibre(source_atom, **compile_kwargs)
        return QuotientRuntimeResult(
            route=QuotientRuntimeRoute.RAW_COST_NEGATIVE,
            source_atom_id=source_atom_id,
            fibre=raw,
            quotient_view_hash=quotient_view.content_hash,
            detail=f"estimated_net_benefit={estimated_net_benefit}",
        )

    derived = compile_quotient_problem_fibre(
        source_atom,
        quotient_view,
        **compile_kwargs,
    )
    return QuotientRuntimeResult(
        route=QuotientRuntimeRoute.QUOTIENT,
        source_atom_id=source_atom_id,
        fibre=derived.fibre,
        quotient_view_hash=quotient_view.content_hash,
        detail="VALIDATED_QUOTIENT",
    )
