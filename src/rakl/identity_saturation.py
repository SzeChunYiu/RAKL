from __future__ import annotations

from dataclasses import dataclass, field, replace

from .identity import EvidenceIdentityLedger
from .saturation import RecordedRound, SaturationTracker


@dataclass
class IdentityAwareSaturationTracker(SaturationTracker):
    """Saturation tracker that resolves aliases and ancestry before independence credit.

    This is an opt-in refinement of ``SaturationTracker``. It preserves the incumbent
    behavior when no identity normalization is needed while providing a stricter path
    for raw evidence identifiers that may contain aliases, versions, derived artifacts,
    or unresolved possible matches.
    """

    identity_ledger: EvidenceIdentityLedger = field(default_factory=EvidenceIdentityLedger)

    def independence_diagnostic(self) -> dict:
        tail = self._independent_flat_tail()
        complete: list[RecordedRound] = []
        source_incomplete: list[str] = []
        identity_unresolved: list[dict] = []
        normalized_lineages: dict[str, list[str]] = {}
        canonical_entities: dict[str, list[str]] = {}

        for recorded in tail:
            rr = recorded.research_round
            if not rr.lineage_complete or not rr.evidence_lineage:
                source_incomplete.append(rr.round_id)
                continue

            resolution = self.identity_ledger.normalize_lineage(rr.evidence_lineage)
            normalized_lineages[rr.round_id] = sorted(resolution.ancestry_tokens)
            canonical_entities[rr.round_id] = sorted(resolution.canonical_entities)

            if not resolution.identity_resolved:
                identity_unresolved.append(
                    {
                        "round_id": rr.round_id,
                        "possible_alias_pairs": [list(pair) for pair in resolution.unresolved_identity_pairs],
                    }
                )
                continue

            normalized_round = replace(
                rr,
                evidence_lineage=resolution.ancestry_tokens,
                lineage_complete=True,
            )
            complete.append(
                RecordedRound(
                    research_round=normalized_round,
                    new_semantic_objects=recorded.new_semantic_objects,
                )
            )

        overlap_pairs: list[dict] = []
        for i, left in enumerate(complete):
            for right in complete[i + 1 :]:
                shared = left.research_round.evidence_lineage & right.research_round.evidence_lineage
                if shared:
                    overlap_pairs.append(
                        {
                            "left": left.research_round.round_id,
                            "right": right.research_round.round_id,
                            "shared_lineage": sorted(shared),
                        }
                    )

        selected, method = self._maximum_disjoint_lineage_subset(complete)
        selected_ids = [r.research_round.round_id for r in selected]

        if source_incomplete or identity_unresolved:
            status = "PARTIALLY_IDENTIFIED_LINEAGE"
        elif overlap_pairs:
            status = "DEPENDENCE_IDENTIFIED"
        else:
            status = "FULL_LINEAGE_DISJOINT"

        unknown = sorted(
            set(source_incomplete)
            | {item["round_id"] for item in identity_unresolved}
        )

        return {
            "status": status,
            "declared_process_independent_flat_rounds": len(tail),
            "lineage_complete_flat_rounds": len(complete),
            "unknown_or_incomplete_lineage_rounds": unknown,
            "source_incomplete_lineage_rounds": sorted(source_incomplete),
            "identity_unresolved_rounds": sorted(
                identity_unresolved,
                key=lambda item: item["round_id"],
            ),
            "normalized_lineages": {
                key: normalized_lineages[key]
                for key in sorted(normalized_lineages)
            },
            "canonical_entities": {
                key: canonical_entities[key]
                for key in sorted(canonical_entities)
            },
            "overlap_pairs": overlap_pairs,
            "conservative_full_independent_rounds": len(selected),
            "credited_round_ids": selected_ids,
            "count_method": method,
            "exact_count": method == "exact",
            "identity_normalization_applied": True,
        }
