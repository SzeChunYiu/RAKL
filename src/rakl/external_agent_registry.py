"""External research-agent registry and landscape-saturation loader (issue #588).

The registry is a baseline and knowledge-projection record, not an authority source.
Nothing here may promote a candidate, and no scalar ranking is derivable from it: the
schema pins ``permits_scalar_ranking`` to ``false`` and this module refuses to emit an
aggregate score.

Saturation status is *derived* from the recorded rounds rather than asserted in the
registry, so a stale or optimistic ``saturation_status`` field is a hard mismatch rather
than a silent inconsistency.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

from jsonschema import Draft202012Validator

from .epistemic_saturation import (
    EpistemicGrowthVector,
    OperatorOrderAudit,
    SaturationBasis,
    SaturationReport,
    SaturationRound,
    SaturationStatus,
    audit_bounded_epistemic_saturation,
)

_REPO = Path(__file__).resolve().parents[2]

REGISTRY_PATH = _REPO / "research" / "external_research_agents" / "registry.json"
ROUNDS_PATH = _REPO / "research" / "external_research_agents" / "saturation" / "rounds.json"
REGISTRY_SCHEMA_PATH = _REPO / "schemas" / "external-research-agent-registry-v1.schema.json"
MECHANICS_PATH = _REPO / "research" / "external_research_agents" / "mechanics" / "mechanics.json"
MECHANICS_SCHEMA_PATH = _REPO / "schemas" / "external-agent-mechanics-v1.schema.json"

#: The only permitted "not known" sentinel. A free-text "unknown"/"TBD" would slip past the
#: evidence-grade audit, so the vocabulary is pinned rather than left to convention.
UNKNOWN_SENTINEL = "CANNOT_CHECK"

#: Marker written into audit digest fields when the perturbation audit has not been run.
AUDIT_NOT_PERFORMED = "NOT_PERFORMED"

#: Evidence grades that may not be cited as a measured capability.
WEAK_EVIDENCE_GRADES = frozenset({"SEARCH_SNIPPET", "UNVERIFIED"})


class RegistryError(RuntimeError):
    """Raised when the registry or its saturation record is internally inconsistent."""


@dataclass(frozen=True)
class LandscapeAudit:
    """Derived view over the registry plus its saturation record."""

    report: SaturationReport
    registry_declared_status: str
    audits_performed: bool
    weak_evidence_ids: tuple[str, ...]
    #: Systems ineligible for a Phase 4 causal arm, for any reason.
    non_causal_comparator_ids: tuple[str, ...]
    #: Systems whose comparator class has not been assessed yet. A strict subset of the
    #: above: SYSTEM_LEVEL_ONLY is a *determined* verdict and does not belong here.
    undetermined_comparator_ids: tuple[str, ...]
    flagged_chronology_anchor_ids: tuple[str, ...]

    @property
    def status(self) -> SaturationStatus:
        return self.report.status

    @property
    def supports_completeness_claim(self) -> bool:
        """A landscape claim needs bounded saturation *and* a performed perturbation audit."""
        return self.report.status is SaturationStatus.BOUNDED_SATURATED and self.audits_performed


def _read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_registry(path: Path | None = None) -> dict[str, Any]:
    """Load and schema-validate the external-agent registry."""

    payload = _read_json(path or REGISTRY_PATH)
    schema = _read_json(REGISTRY_SCHEMA_PATH)
    errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda item: item.path)
    if errors:
        joined = "; ".join(f"{'/'.join(str(p) for p in e.path)}: {e.message}" for e in errors[:5])
        raise RegistryError(f"registry failed schema validation: {joined}")
    return payload


def load_basis(path: Path | None = None) -> SaturationBasis:
    """Reconstruct the frozen saturation basis from the rounds record."""

    payload = _read_json(path or ROUNDS_PATH)
    return SaturationBasis(**payload["basis"])


def _build_round(entry: dict[str, Any], *, fingerprint: str) -> SaturationRound:
    """Translate one recorded round into the library's saturation type.

    When ``audit_performed`` is false the digests are written as ``NOT_PERFORMED`` and the
    substantive difference is left flat: a not-run audit must not masquerade as observed
    instability either.  The round's blocking fibers are what keep such a round from
    contributing to a positive result.
    """

    performed = bool(entry.get("audit_performed", False))
    if performed:
        digest = entry.get("operator_order_digest")
        swapped = entry.get("operator_order_swapped_digest")
        if not digest or not swapped:
            raise RegistryError(
                f"{entry['round_id']}: audit_performed is true but the operator-order digests "
                "are incomplete; a claimed audit must record both endpoints"
            )
        if digest == swapped:
            raise RegistryError(
                f"{entry['round_id']}: operator-order digests are identical, so no perturbation "
                "was applied; this cannot count as a performed audit"
            )
    else:
        digest = swapped = AUDIT_NOT_PERFORMED
    audit = OperatorOrderAudit(
        audit_id=f"{entry['round_id']}:operator-order",
        expand_then_consolidate_digest=digest,
        consolidate_then_expand_digest=swapped,
        substantive_difference=EpistemicGrowthVector(**entry.get("operator_order_difference", {})),
        evidence_ids=tuple(entry.get("blocking_fibers") or (entry["round_id"],)),
    )
    return SaturationRound(
        round_id=entry["round_id"],
        basis_fingerprint=fingerprint,
        growth=EpistemicGrowthVector(**entry.get("growth", {})),
        bounded_discovery_closed=bool(entry.get("bounded_discovery_closed", False)),
        route_coverage_stable=bool(entry.get("route_coverage_stable", False)),
        omission_audit_passed=bool(entry.get("omission_audit_passed", False)),
        nearest_work_audit_passed=bool(entry.get("nearest_work_audit_passed", False)),
        operator_order_audit=audit,
        freshness_cutoff=entry["freshness_cutoff"],
        blocking_fibers=tuple(entry.get("blocking_fibers", ())),
        representation_only_changes=int(entry.get("representation_only_changes", 0)),
    )


def audit_landscape(
    registry_path: Path | None = None,
    rounds_path: Path | None = None,
) -> LandscapeAudit:
    """Derive saturation status and integrity flags from the recorded landscape pass."""

    registry = load_registry(registry_path)
    rounds_payload = _read_json(rounds_path or ROUNDS_PATH)
    basis = SaturationBasis(**rounds_payload["basis"])

    if registry["basis_fingerprint"] != basis.fingerprint:
        raise RegistryError(
            "registry basis_fingerprint does not match the saturation basis; "
            f"registry={registry['basis_fingerprint']} basis={basis.fingerprint}"
        )

    rounds = [_build_round(entry, fingerprint=basis.fingerprint) for entry in rounds_payload["rounds"]]
    report = audit_bounded_epistemic_saturation(
        rounds,
        basis=basis,
        required_consecutive_flat_rounds=int(rounds_payload.get("required_consecutive_flat_rounds", 2)),
        required_freshness_cutoff=rounds_payload.get("required_freshness_cutoff"),
    )

    audits_performed = all(bool(entry.get("audit_performed", False)) for entry in rounds_payload["rounds"])

    # Defence in depth: an un-run perturbation audit can never yield bounded saturation,
    # independently of how the round flags happen to be recorded.
    if report.status is SaturationStatus.BOUNDED_SATURATED and not audits_performed:
        report = SaturationReport(
            status=SaturationStatus.OPEN,
            basis_fingerprint=report.basis_fingerprint,
            evaluated_round_ids=report.evaluated_round_ids,
            consecutive_flat_rounds=report.consecutive_flat_rounds,
            freshness_cutoff=report.freshness_cutoff,
            reasons=report.reasons + ("operator_order_audit_not_performed",),
        )

    if registry["saturation_status"] != report.status.value:
        raise RegistryError(
            f"registry declares saturation_status={registry['saturation_status']} "
            f"but the recorded rounds derive {report.status.value}"
        )

    weak = tuple(
        item["system_id"] if "system_id" in item else item["benchmark_id"]
        for item in (*registry["systems"], *registry["benchmarks"])
        if item["evidence_grade"] in WEAK_EVIDENCE_GRADES
    )
    non_causal = tuple(
        item["system_id"]
        for item in registry["systems"]
        if item["comparator_class"] != "ARCHITECTURE_CAUSAL_ELIGIBLE"
    )
    undetermined = tuple(
        item["system_id"]
        for item in registry["systems"]
        if item["comparator_class"] == "UNDETERMINED"
    )
    # Anchor ids are shared across entries, so deduplicate: one flagged paper is one
    # chronology problem, not one per citing entry.
    flagged = tuple(dict.fromkeys(
        anchor["anchor_id"]
        for item in (*registry["systems"], *registry["benchmarks"])
        for anchor in item["source_anchors"]
        if anchor.get("date_consistency") == "FLAGGED"
    ))

    return LandscapeAudit(
        report=report,
        registry_declared_status=registry["saturation_status"],
        audits_performed=audits_performed,
        weak_evidence_ids=weak,
        non_causal_comparator_ids=non_causal,
        undetermined_comparator_ids=undetermined,
        flagged_chronology_anchor_ids=flagged,
    )


def load_mechanics(path: Path | None = None) -> dict[str, Any]:
    """Load and schema-validate the compiled competitor-mechanic records."""

    payload = _read_json(path or MECHANICS_PATH)
    schema = _read_json(MECHANICS_SCHEMA_PATH)
    errors = sorted(Draft202012Validator(schema).iter_errors(payload), key=lambda item: item.path)
    if errors:
        joined = "; ".join(f"{'/'.join(str(p) for p in e.path)}: {e.message}" for e in errors[:5])
        raise RegistryError(f"mechanics failed schema validation: {joined}")
    return payload


def cross_reference_mechanics(
    registry: dict[str, Any] | None = None,
    mechanics: dict[str, Any] | None = None,
) -> tuple[str, ...]:
    """Return dangling references between the registry and the mechanic records.

    An empty tuple means every ``candidate_mechanic_id`` resolves to a compiled mechanic
    and every mechanic names source systems that exist.  Dangling ids are how a mechanic
    silently loses its provenance, so this is checked rather than assumed.
    """

    registry = registry if registry is not None else load_registry()
    mechanics = mechanics if mechanics is not None else load_mechanics()

    mechanic_ids = {item["mechanic_id"] for item in mechanics["mechanics"]}
    system_ids = {item["system_id"] for item in registry["systems"]}

    problems: list[str] = []
    for system in registry["systems"]:
        for ref in system.get("candidate_mechanic_ids", ()):
            if ref not in mechanic_ids:
                problems.append(f"{system['system_id']} -> unknown mechanic {ref}")
    for mechanic in mechanics["mechanics"]:
        for ref in mechanic.get("source_system_ids", ()):
            if ref not in system_ids:
                problems.append(f"{mechanic['mechanic_id']} -> unknown system {ref}")
    return tuple(problems)


def anchor_integrity_problems(registry: dict[str, Any] | None = None) -> tuple[str, ...]:
    """Return anchor-layer integrity failures.

    Two failure classes, both of which silently destroy provenance:

    * a ``reported_results`` entry citing an ``anchor_id`` its own entry does not define;
    * one ``anchor_id`` carrying different content in different places, which makes the id
      useless as an identity.

    Anchor ids are deliberately *shared* across entries (one paper backs a system and its
    benchmark), so reuse is expected — divergent content under a reused id is not.
    """

    registry = registry if registry is not None else load_registry()
    problems: list[str] = []
    payload_by_id: dict[str, str] = {}

    for item in (*registry["systems"], *registry["benchmarks"]):
        owner = item.get("system_id") or item["benchmark_id"]
        defined = {anchor["anchor_id"] for anchor in item["source_anchors"]}
        for anchor in item["source_anchors"]:
            encoded = json.dumps(anchor, sort_keys=True)
            previous = payload_by_id.setdefault(anchor["anchor_id"], encoded)
            if previous != encoded:
                problems.append(f"{owner}: anchor {anchor['anchor_id']} has divergent content")
        for result in item.get("reported_results", ()):
            # anchor_ids is optional in the schema, so absence is legal, not a crash.
            for ref in result.get("anchor_ids", ()):
                if ref not in defined:
                    problems.append(f"{owner}: result cites undefined anchor {ref}")
    return tuple(problems)


def architecture_causal_eligible(registry: dict[str, Any]) -> tuple[str, ...]:
    """System ids whose model/tools/budget can be matched for a causal architecture arm.

    Everything absent from this tuple is a system-level comparator only.  Phase 4 arms
    must be built from this list, never from the full registry.
    """

    return tuple(
        item["system_id"]
        for item in registry["systems"]
        if item["comparator_class"] == "ARCHITECTURE_CAUSAL_ELIGIBLE"
    )


def main() -> int:  # pragma: no cover - thin CLI
    audit = audit_landscape()
    print(json.dumps(
        {
            "status": audit.status.value,
            "consecutive_flat_rounds": audit.report.consecutive_flat_rounds,
            "reasons": list(audit.report.reasons),
            "audits_performed": audit.audits_performed,
            "supports_completeness_claim": audit.supports_completeness_claim,
            "weak_evidence_entries": list(audit.weak_evidence_ids),
            "flagged_chronology_anchors": list(audit.flagged_chronology_anchor_ids),
        },
        indent=2,
    ))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
