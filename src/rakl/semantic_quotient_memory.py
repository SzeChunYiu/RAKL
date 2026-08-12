from __future__ import annotations

from .multires_memory import MemoryView, MemoryViewKind, SourcePin
from .semantic_quotient import ValidatedQuotientView


def quotient_to_pinned_memory_view(
    view: ValidatedQuotientView,
    canonical: MemoryView,
) -> MemoryView:
    """Create a TCSQ memory view by inheriting identity/authority from one canonical source.

    The caller cannot supply authority certificates separately.  This makes authority
    non-escalation true at construction time rather than relying only on a later lineage
    validator to detect an inflated certificate set.
    """

    if canonical.kind is not MemoryViewKind.CANONICAL:
        raise ValueError("tcsq_memory_source_must_be_canonical")
    if canonical.payload_hash != view.source_hash:
        raise ValueError("tcsq_memory_source_hash_mismatch")

    erasure_tags = tuple(f"ERASED:{item}" for item in view.erased_coordinates) + tuple(
        f"CONDITIONALLY_ERASED:{item}"
        for item in view.conditionally_erased_coordinates
    )
    kind = MemoryViewKind.DERIVED_LOSSY if erasure_tags else MemoryViewKind.DERIVED_LOSSLESS

    return MemoryView(
        record_id=f"tcsq:{view.quotient_id}:{view.content_hash[:12]}",
        payload_hash=view.content_hash,
        kind=kind,
        source_pins=(SourcePin(canonical.record_id, canonical.payload_hash),),
        transform_id=f"TCSQ:{view.quotient_id}",
        erasure_tags=erasure_tags,
        authority_certificates=canonical.authority_certificates,
        required_canonical_ids=(canonical.record_id,),
    )
