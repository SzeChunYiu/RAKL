from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class ManuscriptSemanticKind(str, Enum):
    CLAIM_DISTINCTION = "CLAIM_DISTINCTION"
    CITATION_CLUSTER = "CITATION_CLUSTER"
    NOVELTY_BOUNDARY = "NOVELTY_BOUNDARY"
    PROOF_OBLIGATION = "PROOF_OBLIGATION"
    EXPLANATORY_BRIDGE = "EXPLANATORY_BRIDGE"
    FALSIFIER = "FALSIFIER"
    REVIEW_REPAIR = "REVIEW_REPAIR"


class ManuscriptOpenState(str, Enum):
    MATERIAL_OPEN = "MATERIAL_OPEN"
    EMPIRICAL_DEFERRED = "EMPIRICAL_DEFERRED"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    BLOCKED_MISSING_EVIDENCE = "BLOCKED_MISSING_EVIDENCE"


@dataclass(frozen=True)
class ManuscriptSemanticObject:
    object_id: str
    kind: ManuscriptSemanticKind
    summary: str
    source_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.object_id.strip() or not self.summary.strip():
            raise ValueError("semantic object identity and summary are required")


@dataclass(frozen=True)
class ManuscriptOpenItem:
    item_id: str
    state: ManuscriptOpenState
    summary: str

    def __post_init__(self) -> None:
        if not self.item_id.strip() or not self.summary.strip():
            raise ValueError("open-item identity and summary are required")


@dataclass(frozen=True)
class ManuscriptReviewPass:
    pass_id: str
    lens: str
    route: str
    context_id: str
    semantic_objects: tuple[ManuscriptSemanticObject, ...] = ()
    source_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for value, name in (
            (self.pass_id, "pass_id"),
            (self.lens, "lens"),
            (self.route, "route"),
            (self.context_id, "context_id"),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")


@dataclass(frozen=True)
class RecordedManuscriptPass:
    review_pass: ManuscriptReviewPass
    new_semantic_object_ids: frozenset[str]

    @property
    def flat(self) -> bool:
        return not self.new_semantic_object_ids


@dataclass
class ManuscriptSaturationProtocol:
    """Scoped semantic stopping for a manuscript publication projection.

    This deliberately specializes the existing RAKL saturation/review surfaces. It does
    not certify literature completeness, scientific truth, or independent peer review.
    A material semantic addition resets the post-growth flatness tail: all required lenses
    and routes must be exercised again before local manuscript saturation can be claimed.
    """

    required_lenses: frozenset[str]
    required_routes: frozenset[str]
    freshness_cutoff: str
    flat_passes_per_lens: int = 1
    passes: list[RecordedManuscriptPass] = field(default_factory=list)
    semantic_objects: dict[str, ManuscriptSemanticObject] = field(default_factory=dict)
    open_items: dict[str, ManuscriptOpenItem] = field(default_factory=dict)
    freshness_scan_complete: bool = False
    nearest_work_audit_complete: bool = False
    proof_obligation_audit_complete: bool = False
    section_purpose_audit_complete: bool = False
    _reopened_reason: str | None = None

    def __post_init__(self) -> None:
        if not self.required_lenses or not self.required_routes:
            raise ValueError("required lenses and routes cannot be empty")
        if not self.freshness_cutoff.strip():
            raise ValueError("freshness_cutoff is required")
        if self.flat_passes_per_lens < 1:
            raise ValueError("flat_passes_per_lens must be >= 1")

    def record_pass(self, review_pass: ManuscriptReviewPass) -> RecordedManuscriptPass:
        if any(p.review_pass.pass_id == review_pass.pass_id for p in self.passes):
            raise ValueError(f"duplicate pass_id: {review_pass.pass_id}")
        new_ids: set[str] = set()
        for obj in review_pass.semantic_objects:
            existing = self.semantic_objects.get(obj.object_id)
            if existing is not None and existing != obj:
                raise ValueError(f"semantic object identity is immutable: {obj.object_id}")
            if existing is None:
                self.semantic_objects[obj.object_id] = obj
                new_ids.add(obj.object_id)
        recorded = RecordedManuscriptPass(review_pass, frozenset(new_ids))
        self.passes.append(recorded)
        if new_ids:
            self._reopened_reason = None
        return recorded

    def set_open_items(self, items: Iterable[ManuscriptOpenItem]) -> None:
        new: dict[str, ManuscriptOpenItem] = {}
        for item in items:
            if item.item_id in new and new[item.item_id] != item:
                raise ValueError(f"conflicting open-item identity: {item.item_id}")
            new[item.item_id] = item
        self.open_items = new

    def register_exogenous_object(self, obj: ManuscriptSemanticObject, *, reason: str) -> None:
        if not reason.strip():
            raise ValueError("reopen reason cannot be empty")
        existing = self.semantic_objects.get(obj.object_id)
        if existing is not None and existing != obj:
            raise ValueError(f"semantic object identity is immutable: {obj.object_id}")
        if existing is None:
            self.semantic_objects[obj.object_id] = obj
        self._reopened_reason = reason.strip()

    def reopen(self, reason: str) -> None:
        if not reason.strip():
            raise ValueError("reopen reason cannot be empty")
        self._reopened_reason = reason.strip()

    def _last_growth_index(self) -> int:
        last = -1
        for i, recorded in enumerate(self.passes):
            if not recorded.flat:
                last = i
        return last

    @property
    def post_growth_tail(self) -> tuple[RecordedManuscriptPass, ...]:
        return tuple(self.passes[self._last_growth_index() + 1 :])

    @property
    def post_growth_lenses(self) -> frozenset[str]:
        return frozenset(p.review_pass.lens for p in self.post_growth_tail if p.flat)

    @property
    def post_growth_routes(self) -> frozenset[str]:
        return frozenset(p.review_pass.route for p in self.post_growth_tail if p.flat)

    def flat_count_by_lens(self) -> dict[str, int]:
        counts = {lens: 0 for lens in self.required_lenses}
        for recorded in self.post_growth_tail:
            if recorded.flat and recorded.review_pass.lens in counts:
                counts[recorded.review_pass.lens] += 1
        return counts

    @property
    def material_open_items(self) -> tuple[ManuscriptOpenItem, ...]:
        return tuple(
            item
            for item in self.open_items.values()
            if item.state is ManuscriptOpenState.MATERIAL_OPEN
        )

    @property
    def locally_saturated(self) -> bool:
        if self._reopened_reason is not None:
            return False
        if self.material_open_items:
            return False
        if not (
            self.freshness_scan_complete
            and self.nearest_work_audit_complete
            and self.proof_obligation_audit_complete
            and self.section_purpose_audit_complete
        ):
            return False
        counts = self.flat_count_by_lens()
        if any(
            counts.get(lens, 0) < self.flat_passes_per_lens
            for lens in self.required_lenses
        ):
            return False
        if not self.required_routes.issubset(self.post_growth_routes):
            return False
        return True

    def closure_receipt(self) -> dict:
        return {
            "freshness_cutoff": self.freshness_cutoff,
            "semantic_object_count": len(self.semantic_objects),
            "required_lenses": sorted(self.required_lenses),
            "required_routes": sorted(self.required_routes),
            "post_growth_lenses": sorted(self.post_growth_lenses),
            "post_growth_routes": sorted(self.post_growth_routes),
            "flat_count_by_lens": self.flat_count_by_lens(),
            "freshness_scan_complete": self.freshness_scan_complete,
            "nearest_work_audit_complete": self.nearest_work_audit_complete,
            "proof_obligation_audit_complete": self.proof_obligation_audit_complete,
            "section_purpose_audit_complete": self.section_purpose_audit_complete,
            "material_open_items": [item.item_id for item in self.material_open_items],
            "open_items": {
                key: item.state.value for key, item in sorted(self.open_items.items())
            },
            "same_context_local_saturation": self.locally_saturated,
            "independent_saturation": False,
            "independent_peer_review": False,
            "reopened_reason": self._reopened_reason,
        }
