from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from .generator_transport import (
    GeneratorFamilyCandidate,
    GeneratorFamilyReport,
    GeneratorFamilyVerdict,
    assess_generator_family,
)


class LineageVerdict(str, Enum):
    """What the registered provenance graph can justify about selected evidence."""

    NO_KNOWN_SHARED_ANCESTRY = "NO_KNOWN_SHARED_ANCESTRY"
    CORRELATED_SUPPORT_ONLY = "CORRELATED_SUPPORT_ONLY"
    CANNOT_CHECK = "CANNOT_CHECK"
    TRIAL_INVALID = "TRIAL_INVALID"


class GeneratorLineageVerdict(str, Enum):
    CORRELATED_SUPPORT_ONLY = "CORRELATED_SUPPORT_ONLY"
    CORROBORATED_PROPOSAL_ONLY = "CORROBORATED_PROPOSAL_ONLY"
    CORROBORATED_WITH_OUTLIER_PRESERVED = "CORROBORATED_WITH_OUTLIER_PRESERVED"
    CORROBORATED_WITH_UNKNOWN_PRESERVED = "CORROBORATED_WITH_UNKNOWN_PRESERVED"
    NO_SUPPORTED_CORE = "NO_SUPPORTED_CORE"
    CANNOT_CHECK = "CANNOT_CHECK"
    TRIAL_INVALID = "TRIAL_INVALID"


@dataclass(frozen=True)
class EvidenceLineageNode:
    """One evidence entity in a registered provenance/derivation graph.

    ``parent_ids`` represent known derivational/data/intellectual ancestry.
    ``alternate_of_ids`` represent alternate identifiers/views of the same
    underlying evidence entity. ``specialization_of_ids`` represent versions or
    more specific views of a common evidence entity. ``ancestry_complete`` is a
    claim about the registered graph only; it is not a claim of statistical
    independence.
    """

    evidence_id: str
    parent_ids: Tuple[str, ...] = ()
    alternate_of_ids: Tuple[str, ...] = ()
    specialization_of_ids: Tuple[str, ...] = ()
    ancestry_complete: Optional[bool] = None


@dataclass(frozen=True)
class EvidenceLineageGraph:
    graph_id: str
    nodes: Tuple[EvidenceLineageNode, ...]
    declared_before_outcomes: Optional[bool]


@dataclass(frozen=True)
class LineageReport:
    verdict: LineageVerdict
    selected_evidence_ids: Tuple[str, ...]
    provenance_component_count: Optional[int]
    root_ids_by_evidence: Tuple[Tuple[str, Tuple[str, ...]], ...]
    shared_ancestor_ids: Tuple[str, ...]
    unknown_ancestry_ids: Tuple[str, ...]
    reasons: Tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def statistical_effective_n(self) -> None:
        """Topology alone cannot justify a numeric statistical effective N."""

        return None

    @property
    def establishes_statistical_independence(self) -> bool:
        return False


@dataclass(frozen=True)
class GeneratorLineageReport:
    verdict: GeneratorLineageVerdict
    base_generator_report: GeneratorFamilyReport
    lineage_report: Optional[LineageReport]
    reasons: Tuple[str, ...]

    @property
    def grants_target_authority(self) -> bool:
        return False

    @property
    def activates_canonical_knowledge(self) -> bool:
        return False


def _duplicate_ids(nodes: Tuple[EvidenceLineageNode, ...]) -> Tuple[str, ...]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for node in nodes:
        if node.evidence_id in seen:
            duplicates.add(node.evidence_id)
        seen.add(node.evidence_id)
    return tuple(sorted(duplicates))


def _union_find_groups(
    nodes: Tuple[EvidenceLineageNode, ...],
) -> tuple[dict[str, str], Tuple[str, ...]]:
    ids = {node.evidence_id for node in nodes}
    parent = {evidence_id: evidence_id for evidence_id in ids}
    dangling: set[str] = set()

    def find(value: str) -> str:
        root = value
        while parent[root] != root:
            root = parent[root]
        while parent[value] != value:
            nxt = parent[value]
            parent[value] = root
            value = nxt
        return root

    def union(left: str, right: str) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root == right_root:
            return
        canonical = min(left_root, right_root)
        other = right_root if canonical == left_root else left_root
        parent[other] = canonical

    for node in nodes:
        for alternate in node.alternate_of_ids:
            if alternate not in ids:
                dangling.add(alternate)
                continue
            union(node.evidence_id, alternate)

    canonical_by_id = {evidence_id: find(evidence_id) for evidence_id in sorted(ids)}
    # A final compression pass makes the result independent of insertion order.
    canonical_by_id = {
        evidence_id: find(evidence_id) for evidence_id in sorted(canonical_by_id)
    }
    return canonical_by_id, tuple(sorted(dangling))


def assess_evidence_lineage(
    graph: EvidenceLineageGraph,
    selected_evidence_ids: Tuple[str, ...],
) -> LineageReport:
    selected = tuple(sorted(set(selected_evidence_ids)))
    if not graph.graph_id:
        return LineageReport(
            LineageVerdict.CANNOT_CHECK,
            selected,
            None,
            (),
            (),
            (),
            ("graph_id_missing",),
        )
    if not selected:
        return LineageReport(
            LineageVerdict.CANNOT_CHECK,
            (),
            None,
            (),
            (),
            (),
            ("selected_evidence_missing",),
        )
    if graph.declared_before_outcomes is None:
        return LineageReport(
            LineageVerdict.CANNOT_CHECK,
            selected,
            None,
            (),
            (),
            (),
            ("lineage_graph_freeze_chronology_unknown",),
        )
    if graph.declared_before_outcomes is False:
        return LineageReport(
            LineageVerdict.TRIAL_INVALID,
            selected,
            None,
            (),
            (),
            (),
            ("posthoc_lineage_graph_definition",),
        )

    duplicates = _duplicate_ids(graph.nodes)
    if duplicates:
        return LineageReport(
            LineageVerdict.TRIAL_INVALID,
            selected,
            None,
            (),
            (),
            (),
            tuple(f"duplicate_evidence_id:{item}" for item in duplicates),
        )

    node_by_id = {node.evidence_id: node for node in graph.nodes}
    if any(not node.evidence_id for node in graph.nodes):
        return LineageReport(
            LineageVerdict.TRIAL_INVALID,
            selected,
            None,
            (),
            (),
            (),
            ("empty_evidence_id",),
        )

    missing_selected = tuple(sorted(item for item in selected if item not in node_by_id))
    if missing_selected:
        return LineageReport(
            LineageVerdict.CANNOT_CHECK,
            selected,
            None,
            (),
            (),
            missing_selected,
            tuple(f"selected_evidence_unregistered:{item}" for item in missing_selected),
        )

    canonical_by_id, alternate_dangling = _union_find_groups(graph.nodes)
    if alternate_dangling:
        return LineageReport(
            LineageVerdict.CANNOT_CHECK,
            selected,
            None,
            (),
            (),
            alternate_dangling,
            tuple(f"dangling_alternate_reference:{item}" for item in alternate_dangling),
        )

    # Build ancestry edges between canonical evidence groups. A specialization is
    # intentionally ancestry-like rather than alternate: two versions can share
    # a common parent while retaining distinct identities.
    group_parents: dict[str, set[str]] = {
        canonical: set() for canonical in set(canonical_by_id.values())
    }
    group_members: dict[str, set[str]] = {
        canonical: set() for canonical in set(canonical_by_id.values())
    }
    dangling: set[str] = set()
    unknown_groups: set[str] = set()

    for node in graph.nodes:
        child_group = canonical_by_id[node.evidence_id]
        group_members[child_group].add(node.evidence_id)
        if node.ancestry_complete is not True:
            unknown_groups.add(child_group)
        for raw_parent in node.parent_ids + node.specialization_of_ids:
            if raw_parent not in node_by_id:
                dangling.add(raw_parent)
                continue
            parent_group = canonical_by_id[raw_parent]
            if parent_group != child_group:
                group_parents[child_group].add(parent_group)

    if dangling:
        dangling_sorted = tuple(sorted(dangling))
        return LineageReport(
            LineageVerdict.CANNOT_CHECK,
            selected,
            None,
            (),
            (),
            dangling_sorted,
            tuple(f"dangling_parent_reference:{item}" for item in dangling_sorted),
        )

    visiting: set[str] = set()
    visited: set[str] = set()

    def detect_cycle(group_id: str) -> bool:
        if group_id in visiting:
            return True
        if group_id in visited:
            return False
        visiting.add(group_id)
        for parent_group in sorted(group_parents[group_id]):
            if detect_cycle(parent_group):
                return True
        visiting.remove(group_id)
        visited.add(group_id)
        return False

    if any(detect_cycle(group_id) for group_id in sorted(group_parents)):
        return LineageReport(
            LineageVerdict.TRIAL_INVALID,
            selected,
            None,
            (),
            (),
            (),
            ("lineage_derivation_cycle",),
        )

    ancestor_cache: dict[str, frozenset[str]] = {}
    root_cache: dict[str, frozenset[str]] = {}
    unknown_cache: dict[str, bool] = {}

    def ancestors(group_id: str) -> frozenset[str]:
        if group_id not in ancestor_cache:
            values = {group_id}
            for parent_group in group_parents[group_id]:
                values.update(ancestors(parent_group))
            ancestor_cache[group_id] = frozenset(values)
        return ancestor_cache[group_id]

    def roots(group_id: str) -> frozenset[str]:
        if group_id not in root_cache:
            parents = group_parents[group_id]
            if not parents:
                root_cache[group_id] = frozenset({group_id})
            else:
                values: set[str] = set()
                for parent_group in parents:
                    values.update(roots(parent_group))
                root_cache[group_id] = frozenset(values)
        return root_cache[group_id]

    def ancestry_unknown(group_id: str) -> bool:
        if group_id not in unknown_cache:
            unknown_cache[group_id] = any(
                ancestor_group in unknown_groups for ancestor_group in ancestors(group_id)
            )
        return unknown_cache[group_id]

    selected_groups = {item: canonical_by_id[item] for item in selected}
    unknown_selected = tuple(
        sorted(item for item, group_id in selected_groups.items() if ancestry_unknown(group_id))
    )

    root_ids_by_evidence = tuple(
        (item, tuple(sorted(roots(group_id))))
        for item, group_id in sorted(selected_groups.items())
    )

    shared_ancestors: set[str] = set()
    selected_list = list(selected)
    adjacency: dict[str, set[str]] = {item: set() for item in selected_list}
    for index, left in enumerate(selected_list):
        left_ancestors = ancestors(selected_groups[left])
        for right in selected_list[index + 1 :]:
            overlap = left_ancestors.intersection(ancestors(selected_groups[right]))
            if overlap:
                shared_ancestors.update(overlap)
                adjacency[left].add(right)
                adjacency[right].add(left)

    component_count = 0
    remaining = set(selected_list)
    while remaining:
        component_count += 1
        stack = [min(remaining)]
        while stack:
            current = stack.pop()
            if current not in remaining:
                continue
            remaining.remove(current)
            stack.extend(sorted(adjacency[current].intersection(remaining), reverse=True))

    if unknown_selected:
        return LineageReport(
            LineageVerdict.CANNOT_CHECK,
            selected,
            component_count,
            root_ids_by_evidence,
            tuple(sorted(shared_ancestors)),
            unknown_selected,
            (
                "registered_ancestry_incomplete",
                "unknown_ancestry_not_counted_as_independent_support",
            ),
        )

    if shared_ancestors:
        return LineageReport(
            LineageVerdict.CORRELATED_SUPPORT_ONLY,
            selected,
            component_count,
            root_ids_by_evidence,
            tuple(sorted(shared_ancestors)),
            (),
            (
                "known_shared_provenance_ancestry_detected",
                "raw_source_count_does_not_equal_independent_support_count",
            ),
        )

    return LineageReport(
        LineageVerdict.NO_KNOWN_SHARED_ANCESTRY,
        selected,
        component_count,
        root_ids_by_evidence,
        (),
        (),
        (
            "registered_provenance_roots_are_complete_and_disjoint",
            "no_known_shared_ancestry_is_not_statistical_or_epistemic_independence",
        ),
    )


def assess_generator_family_with_lineage(
    candidate: GeneratorFamilyCandidate,
    graph: EvidenceLineageGraph,
) -> GeneratorLineageReport:
    """Add provenance-dependence checking without changing generator authority.

    This wrapper intentionally leaves the original ``assess_generator_family``
    contract intact. It can only preserve or downgrade a generator-family
    proposal; it can never upgrade one or grant target authority.
    """

    base = assess_generator_family(candidate)
    if base.verdict is GeneratorFamilyVerdict.TRIAL_INVALID:
        return GeneratorLineageReport(
            GeneratorLineageVerdict.TRIAL_INVALID,
            base,
            None,
            ("base_generator_trial_invalid",),
        )
    if base.verdict is GeneratorFamilyVerdict.CANNOT_CHECK:
        return GeneratorLineageReport(
            GeneratorLineageVerdict.CANNOT_CHECK,
            base,
            None,
            ("base_generator_trial_cannot_check",),
        )
    if base.verdict is GeneratorFamilyVerdict.NO_SUPPORTED_CORE:
        return GeneratorLineageReport(
            GeneratorLineageVerdict.NO_SUPPORTED_CORE,
            base,
            None,
            ("base_generator_core_not_supported",),
        )

    supported_ids = set(base.supported_instance_ids)
    evidence_ids: set[str] = set()
    for lift in candidate.lifts:
        if lift.instance_id in supported_ids:
            evidence_ids.update(lift.evidence_ids)

    lineage = assess_evidence_lineage(graph, tuple(sorted(evidence_ids)))
    if lineage.verdict is LineageVerdict.TRIAL_INVALID:
        return GeneratorLineageReport(
            GeneratorLineageVerdict.TRIAL_INVALID,
            base,
            lineage,
            ("lineage_trial_invalid",),
        )
    if lineage.verdict is LineageVerdict.CANNOT_CHECK:
        return GeneratorLineageReport(
            GeneratorLineageVerdict.CANNOT_CHECK,
            base,
            lineage,
            ("generator_corroboration_lineage_incomplete",),
        )
    if (
        base.verdict is GeneratorFamilyVerdict.CORRELATED_SUPPORT_ONLY
        or lineage.verdict is LineageVerdict.CORRELATED_SUPPORT_ONLY
    ):
        return GeneratorLineageReport(
            GeneratorLineageVerdict.CORRELATED_SUPPORT_ONLY,
            base,
            lineage,
            (
                "generator_support_has_known_or_preexisting_dependence",
                "lineage_check_can_only_preserve_or_downgrade_corroboration",
            ),
        )

    mapping = {
        GeneratorFamilyVerdict.CORROBORATED_GENERATOR_PROPOSAL_ONLY: (
            GeneratorLineageVerdict.CORROBORATED_PROPOSAL_ONLY
        ),
        GeneratorFamilyVerdict.CORROBORATED_WITH_OUTLIER_PRESERVED: (
            GeneratorLineageVerdict.CORROBORATED_WITH_OUTLIER_PRESERVED
        ),
        GeneratorFamilyVerdict.CORROBORATED_WITH_UNKNOWN_PRESERVED: (
            GeneratorLineageVerdict.CORROBORATED_WITH_UNKNOWN_PRESERVED
        ),
    }
    verdict = mapping[base.verdict]
    return GeneratorLineageReport(
        verdict,
        base,
        lineage,
        (
            "generator_proposal_retained_after_registered_lineage_check",
            "absence_of_known_shared_ancestry_does_not_establish_independence",
            "target_evidence_and_separate_promotion_still_required",
        ),
    )
