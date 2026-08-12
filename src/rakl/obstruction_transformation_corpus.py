"""Provenance-bound obstruction–transformation episode corpus (issue #402).

Phase-0 ontology + seed corpus loader. Snapshot hashes bind through
``rakl.semantic_shortcut.build_transformation_memory``. Synthetic /
proposal episodes never become strict verified SEARCH/JUMP routes by default.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .paper3_annotation import canonical_sha256
from .semantic_shortcut import (
    ObstructionFingerprint,
    ObstructionTransformationEpisode,
    ObstructionTransformationMemory,
    TransformationEpisodeAuthority,
    build_transformation_memory,
    validate_transformation_episode,
    validate_transformation_memory,
)

CORPUS_DIR = Path("research/obstruction_transformation_corpus_v1")
ONTOLOGY_PATH = CORPUS_DIR / "ONTOLOGY_VERSION.json"
PROTOCOL_PATH = CORPUS_DIR / "CORPUS_PROTOCOL.md"
SOURCE_UNIVERSE_PATH = CORPUS_DIR / "SOURCE_UNIVERSE_MANIFEST.json"
EPISODES_PATH = CORPUS_DIR / "EPISODES.jsonl"
SNAPSHOT_MANIFEST_PATH = CORPUS_DIR / "SNAPSHOT_MANIFEST.json"
COVERAGE_REPORT_PATH = CORPUS_DIR / "COVERAGE_REPORT.json"
DEDUP_REPORT_PATH = CORPUS_DIR / "DEDUP_EQUIVALENCE_REPORT.json"
SPLIT_MANIFEST_PATH = CORPUS_DIR / "SPLIT_MANIFEST.json"
LEAKAGE_AUDIT_PATH = CORPUS_DIR / "LEAKAGE_AUDIT.json"
RETRIEVAL_EVAL_PATH = CORPUS_DIR / "RETRIEVAL_EVALUATION.json"
CHANGELOG_PATH = CORPUS_DIR / "CHANGELOG.md"
MEMORY_JSON_PATH = CORPUS_DIR / "MEMORY_SNAPSHOT.json"
RECEIPTS_DIR = CORPUS_DIR / "SOURCE_VERIFICATION_RECEIPTS"

# Design-fixture ids from tests/test_semantic_shortcut.py must not leak into
# confirmatory evaluation partitions owned by #401.
DESIGN_FIXTURE_EPISODE_IDS = frozenset({"A", "B", "D", "J", "Z-verified"})

REQUIRED_ARTIFACTS = (
    PROTOCOL_PATH,
    ONTOLOGY_PATH,
    SOURCE_UNIVERSE_PATH,
    EPISODES_PATH,
    DEDUP_REPORT_PATH,
    SNAPSHOT_MANIFEST_PATH,
    COVERAGE_REPORT_PATH,
    SPLIT_MANIFEST_PATH,
    LEAKAGE_AUDIT_PATH,
    RETRIEVAL_EVAL_PATH,
    CHANGELOG_PATH,
    MEMORY_JSON_PATH,
)

SPLIT_NAMES = (
    "DEVELOPMENT_MEMORY",
    "EVALUATION_MEMORY",
    "FRESH_TARGETS",
    "HOSTILE_NEAR_MISSES",
)

_VERIFIED = frozenset(
    {
        TransformationEpisodeAuthority.SOURCE_EVENT_VERIFIED.value,
        TransformationEpisodeAuthority.VERIFIED_LOCAL.value,
        TransformationEpisodeAuthority.PROOF_BACKED.value,
    }
)


@dataclass(frozen=True)
class CorpusValidationReport:
    ok: bool
    memory_id: str
    snapshot_hash: str
    episode_count: int
    authority_counts: Mapping[str, int]
    domain_counts: Mapping[str, int]
    reasons: tuple[str, ...]
    grants_scientific_authority: bool = False


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _fingerprint_from_dict(payload: Mapping[str, Any]) -> ObstructionFingerprint:
    return ObstructionFingerprint(
        obstruction_id=str(payload["obstruction_id"]),
        domain=str(payload["domain"]),
        roles=tuple(payload["roles"]),
        relations=tuple(payload["relations"]),
        constraints=tuple(payload["constraints"]),
        failure_mechanisms=tuple(payload["failure_mechanisms"]),
        invariants_to_preserve=tuple(payload["invariants_to_preserve"]),
        desired_transition=tuple(payload["desired_transition"]),
        forbidden_losses=tuple(payload.get("forbidden_losses") or ()),
    )


def episode_content_hash(payload: Mapping[str, Any]) -> str:
    """Hash episode content excluding the artifact_hash field itself."""
    body = {k: v for k, v in payload.items() if k != "artifact_hash"}
    return canonical_sha256(body)


def episode_from_dict(payload: Mapping[str, Any]) -> ObstructionTransformationEpisode:
    authority = TransformationEpisodeAuthority(str(payload["authority"]))
    return ObstructionTransformationEpisode(
        episode_id=str(payload["episode_id"]),
        source_domain=str(payload["source_domain"]),
        source_context=str(payload["source_context"]),
        source_obstruction=_fingerprint_from_dict(payload["source_obstruction"]),
        transformation_name=str(payload["transformation_name"]),
        operation=str(payload["operation"]),
        preconditions=tuple(payload["preconditions"]),
        resulting_relations=tuple(payload["resulting_relations"]),
        preserved_invariants=tuple(payload["preserved_invariants"]),
        relaxed_or_broken_constraints=tuple(
            payload.get("relaxed_or_broken_constraints") or ()
        ),
        known_breakpoints=tuple(payload["known_breakpoints"]),
        evidence_pointers=tuple(payload["evidence_pointers"]),
        authority=authority,
        artifact_hash=str(payload["artifact_hash"]),
        lineage_ids=tuple(payload.get("lineage_ids") or ()),
    )


def episode_to_dict(episode: ObstructionTransformationEpisode) -> dict[str, Any]:
    return {
        "episode_id": episode.episode_id,
        "source_domain": episode.source_domain,
        "source_context": episode.source_context,
        "source_obstruction": {
            "obstruction_id": episode.source_obstruction.obstruction_id,
            "domain": episode.source_obstruction.domain,
            "roles": list(episode.source_obstruction.roles),
            "relations": list(episode.source_obstruction.relations),
            "constraints": list(episode.source_obstruction.constraints),
            "failure_mechanisms": list(episode.source_obstruction.failure_mechanisms),
            "invariants_to_preserve": list(
                episode.source_obstruction.invariants_to_preserve
            ),
            "desired_transition": list(episode.source_obstruction.desired_transition),
            "forbidden_losses": list(episode.source_obstruction.forbidden_losses),
        },
        "transformation_name": episode.transformation_name,
        "operation": episode.operation,
        "preconditions": list(episode.preconditions),
        "resulting_relations": list(episode.resulting_relations),
        "preserved_invariants": list(episode.preserved_invariants),
        "relaxed_or_broken_constraints": list(episode.relaxed_or_broken_constraints),
        "known_breakpoints": list(episode.known_breakpoints),
        "evidence_pointers": list(episode.evidence_pointers),
        "authority": episode.authority.value,
        "artifact_hash": episode.artifact_hash,
        "lineage_ids": list(episode.lineage_ids),
    }


def load_episode_rows(repo_root: Path) -> list[dict[str, Any]]:
    path = repo_root / EPISODES_PATH
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _runtime_payload(row: Mapping[str, Any]) -> dict[str, Any]:
    """Strip corpus-only fields before building runtime memory objects."""
    keep = {
        "episode_id",
        "source_domain",
        "source_context",
        "source_obstruction",
        "transformation_name",
        "operation",
        "preconditions",
        "resulting_relations",
        "preserved_invariants",
        "relaxed_or_broken_constraints",
        "known_breakpoints",
        "evidence_pointers",
        "authority",
        "artifact_hash",
        "lineage_ids",
    }
    return {k: row[k] for k in keep if k in row}


def structural_fingerprint_key(obstruction: Mapping[str, Any]) -> str:
    coords = {
        "roles": sorted(obstruction.get("roles") or []),
        "relations": sorted(obstruction.get("relations") or []),
        "constraints": sorted(obstruction.get("constraints") or []),
        "failure_mechanisms": sorted(obstruction.get("failure_mechanisms") or []),
        "invariants_to_preserve": sorted(
            obstruction.get("invariants_to_preserve") or []
        ),
        "desired_transition": sorted(obstruction.get("desired_transition") or []),
        "forbidden_losses": sorted(obstruction.get("forbidden_losses") or []),
    }
    return canonical_sha256(coords)


def classify_pair_relation(
    left: Mapping[str, Any], right: Mapping[str, Any]
) -> str:
    """Typed structural relation for dedup report (not causal diagnosis)."""
    if left["episode_id"] == right["episode_id"]:
        return "same_episode"
    same_source = (
        left.get("source_context") == right.get("source_context")
        and left.get("evidence_pointers") == right.get("evidence_pointers")
    )
    left_key = structural_fingerprint_key(left["source_obstruction"])
    right_key = structural_fingerprint_key(right["source_obstruction"])
    same_structure = left_key == right_key
    same_transform = (
        left.get("transformation_name") == right.get("transformation_name")
        and left.get("operation") == right.get("operation")
    )
    same_pre = set(left.get("preconditions") or []) == set(
        right.get("preconditions") or []
    )
    same_effect = set(left.get("resulting_relations") or []) == set(
        right.get("resulting_relations") or []
    )
    if same_source and same_structure and same_transform and same_effect:
        return "same_source_same_event"
    if same_structure and same_transform and same_pre and same_effect:
        return "same_mechanism_restated_vocabulary"
    if same_transform and same_effect and not same_pre:
        return "same_transformation_materially_different_preconditions"
    if same_structure and not same_transform:
        return "same_obstruction_different_transformation"
    if same_transform and not same_effect:
        return "same_transformation_different_effect"
    left_fail = set(left["source_obstruction"].get("failure_mechanisms") or [])
    right_fail = set(right["source_obstruction"].get("failure_mechanisms") or [])
    left_forbid = set(left["source_obstruction"].get("forbidden_losses") or [])
    right_forbid = set(right["source_obstruction"].get("forbidden_losses") or [])
    if left_fail & right_fail and left_forbid != right_forbid:
        return "hostile_near_miss_shared_failure_divergent_forbidden_loss"
    return "distinct"


def build_dedup_report(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    relations: list[dict[str, Any]] = []
    for i, left in enumerate(rows):
        for right in rows[i + 1 :]:
            relation = classify_pair_relation(left, right)
            if relation == "distinct":
                continue
            relations.append(
                {
                    "left_episode_id": left["episode_id"],
                    "right_episode_id": right["episode_id"],
                    "relation": relation,
                    "collapse_allowed": relation
                    in {
                        "same_source_same_event",
                        "same_mechanism_restated_vocabulary",
                    }
                    and set(left.get("preconditions") or ())
                    == set(right.get("preconditions") or ())
                    and set(
                        left["source_obstruction"].get("forbidden_losses") or ()
                    )
                    == set(
                        right["source_obstruction"].get("forbidden_losses") or ()
                    ),
                }
            )
    collapsed = [r for r in relations if r["collapse_allowed"]]
    retained_near = [r for r in relations if not r["collapse_allowed"]]
    return {
        "schema_version": "obstruction-transformation-corpus-dedup-v1",
        "episode_count": len(rows),
        "pair_relations_recorded": relations,
        "collapsible_duplicate_pairs": collapsed,
        "retained_non_collapsible_relations": retained_near,
        "policy": {
            "do_not_collapse_when": [
                "preconditions differ materially",
                "forbidden_loss profiles differ",
                "effects differ",
                "transformations differ on same obstruction",
            ],
            "note": "Lexical restatement may collapse only when structural coords, preconditions, effects and forbidden losses match.",
        },
        "grants_scientific_authority": False,
    }


def build_coverage_report(
    rows: Sequence[Mapping[str, Any]],
    *,
    source_universe: Sequence[str],
) -> dict[str, Any]:
    authority = Counter(str(r["authority"]) for r in rows)
    domains = Counter(str(r.get("domain_lane") or r["source_domain"]) for r in rows)
    fingerprints = {
        structural_fingerprint_key(r["source_obstruction"]) for r in rows
    }
    transforms = {(r["transformation_name"], r["operation"]) for r in rows}
    precond_complete = sum(1 for r in rows if r.get("preconditions"))
    effect_complete = sum(1 for r in rows if r.get("resulting_relations"))
    provenance = sum(1 for r in rows if r.get("evidence_pointers"))
    verified = sum(1 for r in rows if r["authority"] in _VERIFIED)
    unknown_burden = sum(
        1
        for r in rows
        if any(
            "CANNOT_CHECK" in str(x) or str(x).startswith("UNKNOWN:")
            for x in list(r.get("preconditions") or [])
            + list(r.get("resulting_relations") or [])
            + list(r.get("known_breakpoints") or [])
        )
    )
    return {
        "schema_version": "obstruction-transformation-corpus-coverage-v1",
        "registered_source_universe": list(source_universe),
        "episode_count": len(rows),
        "episode_count_by_authority": dict(sorted(authority.items())),
        "episode_count_by_domain_lane": dict(sorted(domains.items())),
        "unique_obstruction_fingerprints": len(fingerprints),
        "unique_transformation_families": len(transforms),
        "precondition_completeness_rate": precond_complete / max(len(rows), 1),
        "effect_completeness_rate": effect_complete / max(len(rows), 1),
        "provenance_pointer_rate": provenance / max(len(rows), 1),
        "verified_authority_rate": verified / max(len(rows), 1),
        "cannot_check_or_unknown_field_episode_count": unknown_burden,
        "coverage_claim": "SCOPED_TO_REGISTERED_SOURCE_UNIVERSE_ONLY",
        "complete_knowledge_claim_allowed": False,
        "grants_scientific_authority": False,
        "note": "Sparse coverage forces LIFT/no-match routes to CANNOT_CHECK rather than exhaustion-of-all-knowledge.",
    }


def load_transformation_memory(repo_root: Path) -> ObstructionTransformationMemory:
    manifest = _load_json(repo_root / SNAPSHOT_MANIFEST_PATH)
    rows = load_episode_rows(repo_root)
    episodes = tuple(episode_from_dict(_runtime_payload(row)) for row in rows)
    memory = build_transformation_memory(
        memory_id=str(manifest["memory_id"]),
        source_universe=tuple(manifest["source_universe"]),
        episodes=episodes,
        evidence_pointers=tuple(manifest["evidence_pointers"]),
    )
    expected = str(manifest["snapshot_hash"])
    if memory.snapshot_hash != expected:
        raise AssertionError(
            f"snapshot_hash mismatch: built={memory.snapshot_hash} manifest={expected}"
        )
    return memory


def validate_corpus(repo_root: Path) -> CorpusValidationReport:
    reasons: list[str] = []
    for rel in REQUIRED_ARTIFACTS:
        if not (repo_root / rel).is_file():
            reasons.append(f"missing_artifact:{rel}")
    if reasons:
        return CorpusValidationReport(
            ok=False,
            memory_id="",
            snapshot_hash="",
            episode_count=0,
            authority_counts={},
            domain_counts={},
            reasons=tuple(reasons),
        )

    ontology = _load_json(repo_root / ONTOLOGY_PATH)
    universe = _load_json(repo_root / SOURCE_UNIVERSE_PATH)
    manifest = _load_json(repo_root / SNAPSHOT_MANIFEST_PATH)
    splits = _load_json(repo_root / SPLIT_MANIFEST_PATH)
    leakage = _load_json(repo_root / LEAKAGE_AUDIT_PATH)
    rows = load_episode_rows(repo_root)

    if ontology.get("frozen_before_bulk_collection") is not True:
        reasons.append("ontology_not_frozen_before_bulk_collection")
    if ontology.get("synthetic_default_authority") != "PROPOSAL_ONLY":
        reasons.append("synthetic_default_authority_must_be_PROPOSAL_ONLY")
    if not universe.get("source_universe"):
        reasons.append("source_universe_empty")

    ids = [r["episode_id"] for r in rows]
    if len(ids) != len(set(ids)):
        reasons.append("duplicate_episode_id_in_jsonl")

    for row in rows:
        expected_hash = episode_content_hash(row)
        if row.get("artifact_hash") != expected_hash:
            reasons.append(f"episode_artifact_hash_mismatch:{row.get('episode_id')}")
        authority = row.get("authority")
        if authority in _VERIFIED:
            receipt_name = row.get("verification_receipt")
            if not receipt_name:
                reasons.append(f"verified_without_receipt_pointer:{row.get('episode_id')}")
            else:
                receipt_path = repo_root / RECEIPTS_DIR / str(receipt_name)
                if not receipt_path.is_file():
                    reasons.append(f"missing_verification_receipt:{receipt_name}")
        episode = episode_from_dict(_runtime_payload(row))
        episode_reasons = validate_transformation_episode(episode)
        reasons.extend(
            f"{episode.episode_id}:{reason}" for reason in episode_reasons
        )

    try:
        memory = load_transformation_memory(repo_root)
        memory_reasons = validate_transformation_memory(memory)
        reasons.extend(memory_reasons)
    except Exception as exc:  # noqa: BLE001 - surface as validation reason
        memory = None
        reasons.append(f"memory_build_failed:{exc}")

    for split in SPLIT_NAMES:
        if split not in splits.get("partitions", {}):
            reasons.append(f"missing_split:{split}")

    leaked = set(leakage.get("design_fixture_episode_ids_excluded") or [])
    if not DESIGN_FIXTURE_EPISODE_IDS.issubset(leaked):
        reasons.append("design_fixture_ids_not_fully_excluded_in_leakage_audit")

    eval_ids = set(splits.get("partitions", {}).get("EVALUATION_MEMORY", {}).get("episode_ids") or [])
    if eval_ids & DESIGN_FIXTURE_EPISODE_IDS:
        reasons.append("design_fixtures_leaked_into_EVALUATION_MEMORY")
    fresh = set(splits.get("partitions", {}).get("FRESH_TARGETS", {}).get("episode_ids") or [])
    if fresh & DESIGN_FIXTURE_EPISODE_IDS:
        reasons.append("design_fixtures_leaked_into_FRESH_TARGETS")

    if manifest.get("grants_scientific_authority") is not False:
        reasons.append("snapshot_must_not_grant_scientific_authority")
    if manifest.get("complete_knowledge_claim") is not False:
        reasons.append("complete_knowledge_claim_must_be_false")

    authority_counts = dict(Counter(str(r["authority"]) for r in rows))
    domain_counts = dict(
        Counter(str(r.get("domain_lane") or r["source_domain"]) for r in rows)
    )
    return CorpusValidationReport(
        ok=not reasons,
        memory_id=str(manifest.get("memory_id") or ""),
        snapshot_hash=str(manifest.get("snapshot_hash") or ""),
        episode_count=len(rows),
        authority_counts=authority_counts,
        domain_counts=domain_counts,
        reasons=tuple(reasons),
        grants_scientific_authority=False,
    )


def refuse_synthetic_verified_promotion(
    *,
    authority: str,
    has_source_verification_receipt: bool,
) -> None:
    """Fail closed: synthetic/generated episodes cannot mint verified routes."""
    if authority in _VERIFIED and not has_source_verification_receipt:
        raise PermissionError(
            "verified authority refused without source verification receipt "
            "(synthetic defaults remain PROPOSAL_ONLY)"
        )
