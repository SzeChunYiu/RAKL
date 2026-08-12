#!/usr/bin/env python3
"""Harvest the prospective RAKL_math longitudinal cycle-metrology universe (#253).

RAKL_math accumulates one `*_RAKL_CYCLE_METRICS_*.json` (or
`*_PROPOSAL_TELEMETRY_*.json`) artifact per research cycle. Most of them live on
unmerged `research/*` branches, so they are reachable only while those refs
survive. This harvester enumerates every telemetry blob across every ref, binds
its bytes, and emits a frozen event universe.

Three rules, all of which exist because breaking them would silently corrupt the
longitudinal record:

**Payloads are carried verbatim.** `docs/PAPER5_IMPLEMENTATION_STATUS.md` states
that missing fields must be recorded rather than invented. 50 of the 53 observed
blobs contain `CANNOT_MEASURE` / `CANNOT_CHECK` strings. Those are measurements
-- a recorded refusal to measure -- and must survive the harvest byte-identical.
This harvester never fills, defaults, renames or normalizes a payload field.

**No coercion to an existing schema.** `schemas/process-telemetry.schema.json`
requires `invocation_id`, `process_surface`, `task_id`, `input_state_hash`,
`output_state_hash`, `cost`, `cost_policy_id` and `retained_novelty`. The
RAKL_math cycle records carry `cycle_id`, `framework`, `application`,
`state_fingerprints`, `resource_proxies`, `saturation` and
`retained_semantic_novelty`. The overlap is `outcome` / `residual_before` /
`residual_after` and nothing else. They are a different artifact class, so the
universe wraps each payload in a provenance envelope instead of reshaping it.

**Heterogeneity is reported, never pooled.** The observed blobs carry 18 distinct
`schema_version` values and 15 carry none at all. Records are grouped by declared
version and by field presence; nothing downstream may average across groups
without deciding that they are comparable.

The harvester is read-only with respect to the source repository: it runs only
`git for-each-ref`, `git ls-tree`, `git cat-file` and `git rev-list`, and never
checks out, fetches or writes.

Example::

    python experiments/paper5/harvest_raklmath_longitudinal.py \
        --repo /Users/billy/RAKL_math --out-dir /tmp/harvest
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rakl.cycle_metrics_harvest import (
    build_instrumentation_row,
    instrumentation_coverage,
)

HARVESTER_VERSION = "paper5-longitudinal-harvest-v1"
INSTRUMENTATION_VERSION = "paper5-cycle-metrics-instrumentation-v1"
UNIVERSE_SCHEMA = "paper5-longitudinal-event-universe-v1"

#: Basename markers identifying a cycle-metrology artifact.
TELEMETRY_MARKERS = ("RAKL_CYCLE_METRICS", "PROPOSAL_TELEMETRY")

#: Strings that record a deliberate refusal/inability to measure. Their presence
#: is tracked so a downstream consumer cannot mistake them for real values, and
#: so an accidental normalization becomes visible as a count change.
UNMEASURED_MARKERS = ("CANNOT_MEASURE", "CANNOT_CHECK", "CANNOT_COMPILE", "NOT_MEASURED")


class GitError(RuntimeError):
    pass


def git(repo: Path, *args: str, binary: bool = False) -> Any:
    proc = subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=not binary, check=False
    )
    if proc.returncode != 0:
        err = proc.stderr if not binary else proc.stderr.decode("utf-8", "replace")
        raise GitError(f"git {' '.join(args)} failed: {err.strip()}")
    return proc.stdout


def is_telemetry(path: str) -> bool:
    return any(marker in path.rsplit("/", 1)[-1] for marker in TELEMETRY_MARKERS)


def collect_blobs(repo: Path, ref_prefix: str) -> dict[str, dict[str, set[str]]]:
    """Map blob sha -> {paths, refs} for every telemetry artifact on every ref."""
    refs = [line for line in git(repo, "for-each-ref", "--format=%(refname)", ref_prefix).splitlines() if line]
    if not refs:
        raise SystemExit(f"no refs matched {ref_prefix}; nothing to harvest")
    found: dict[str, dict[str, set[str]]] = collections.defaultdict(lambda: {"paths": set(), "refs": set()})
    for ref in refs:
        try:
            listing = git(repo, "ls-tree", "-r", ref)
        except GitError:
            continue
        for line in listing.splitlines():
            if "\t" not in line:
                continue
            meta, path = line.split("\t", 1)
            if not is_telemetry(path):
                continue
            parts = meta.split()
            if len(parts) < 3 or parts[1] != "blob":
                continue
            blob = parts[2]
            found[blob]["paths"].add(path)
            found[blob]["refs"].add(ref)
    return found


def main_reachable_blobs(repo: Path, main_ref: str) -> set[str]:
    """Every object reachable from the main ref's FULL history, not just its tip tree.

    A blob already in main's history is durable; one that is not exists only for
    as long as the branch carrying it does.
    """
    out = git(repo, "rev-list", "--objects", main_ref)
    return {line.split()[0] for line in out.splitlines() if line}


def count_unmeasured(raw: bytes) -> dict[str, int]:
    text = raw.decode("utf-8", "replace")
    return {marker: text.count(marker) for marker in UNMEASURED_MARKERS if marker in text}


def build_envelope(
    repo: Path,
    blob: str,
    paths: set[str],
    refs: set[str],
    reachable: bool,
    harvested_at: str,
) -> dict[str, Any]:
    raw = git(repo, "cat-file", "-p", blob, binary=True)
    envelope: dict[str, Any] = {
        "schema_version": UNIVERSE_SCHEMA,
        "event_id": blob,
        "git_blob_sha1": blob,
        # Binds the ORIGINAL bytes, so any later re-serialization of `payload`
        # can be checked against the source rather than trusted.
        "payload_sha256": hashlib.sha256(raw).hexdigest(),
        "payload_bytes": len(raw),
        "source_repository": "SzeChunYiu/RAKL_math",
        "source_paths": sorted(paths),
        "source_refs": sorted(refs),
        "reachable_from_main_history": reachable,
        "unmeasured_markers": count_unmeasured(raw),
        "harvester_version": HARVESTER_VERSION,
        "harvested_at": harvested_at,
        "grants_scientific_authority": False,
    }
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        # An unparseable artifact is an observation, not a reason to drop a row.
        envelope["payload"] = None
        envelope["parse_error"] = f"{type(exc).__name__}: {exc}"
        envelope["declared_schema_version_present"] = False
        envelope["declared_schema_version"] = None
        envelope["payload_top_level_keys"] = []
        return envelope

    envelope["payload"] = payload
    envelope["parse_error"] = None
    if isinstance(payload, dict):
        present = "schema_version" in payload
        envelope["declared_schema_version_present"] = present
        envelope["declared_schema_version"] = payload.get("schema_version") if present else None
        envelope["payload_top_level_keys"] = sorted(payload)
    else:
        envelope["declared_schema_version_present"] = False
        envelope["declared_schema_version"] = None
        envelope["payload_top_level_keys"] = []
    return envelope


def coverage_report(envelopes: list[dict[str, Any]]) -> dict[str, Any]:
    versions: collections.Counter[str] = collections.Counter()
    for env in envelopes:
        if env["declared_schema_version_present"]:
            versions[str(env["declared_schema_version"])] += 1
        else:
            versions["<absent>"] += 1
    field_presence: collections.Counter[str] = collections.Counter()
    for env in envelopes:
        for key in env["payload_top_level_keys"]:
            field_presence[key] += 1

    at_risk = [env for env in envelopes if not env["reachable_from_main_history"]]
    at_risk_refs: collections.Counter[str] = collections.Counter()
    for env in at_risk:
        for ref in env["source_refs"]:
            at_risk_refs[ref] += 1

    return {
        "schema_version": "paper5-longitudinal-coverage-v1",
        "event_count": len(envelopes),
        "unparseable_count": sum(1 for env in envelopes if env["parse_error"]),
        "reachable_from_main_history": len(envelopes) - len(at_risk),
        "at_risk_branch_only": len(at_risk),
        "at_risk_refs": dict(at_risk_refs.most_common()),
        "declared_schema_versions": dict(versions.most_common()),
        "distinct_declared_schema_versions": len([v for v in versions if v != "<absent>"]),
        "events_without_declared_schema_version": versions.get("<absent>", 0),
        "payload_top_level_field_presence": dict(field_presence.most_common()),
        "events_carrying_unmeasured_markers": sum(1 for env in envelopes if env["unmeasured_markers"]),
        "comparable_across_declared_versions": False,
        "claim_boundary": (
            "Harvest/coverage observation only. Payloads are carried verbatim and are not normalized, "
            "imputed or coerced to any existing schema. Records declare 18-way heterogeneous schema_version "
            "and must not be pooled across versions without a separate comparability decision. "
            "Grants no scientific authority; retained-novelty figures inside payloads remain internally "
            "classified until the independent audit in #255 exists."
        ),
        "grants_scientific_authority": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path, help="path to a RAKL_math checkout (read-only)")
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--ref-prefix", default="refs/remotes/origin")
    parser.add_argument("--main-ref", default="refs/remotes/origin/main")
    args = parser.parse_args()

    repo = args.repo.expanduser().resolve()
    if not (repo / ".git").exists():
        raise SystemExit(f"not a git checkout: {repo}")

    harvested_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    found = collect_blobs(repo, args.ref_prefix)
    reachable = main_reachable_blobs(repo, args.main_ref)

    envelopes = [
        build_envelope(repo, blob, entry["paths"], entry["refs"], blob in reachable, harvested_at)
        for blob, entry in sorted(found.items())
    ]

    args.out_dir.mkdir(parents=True, exist_ok=True)
    universe = args.out_dir / "longitudinal_event_universe.jsonl"
    with universe.open("w", encoding="utf-8") as handle:
        for env in envelopes:
            handle.write(json.dumps(env, sort_keys=True, separators=(",", ":")) + "\n")

    report = coverage_report(envelopes)
    report["universe_sha256"] = hashlib.sha256(universe.read_bytes()).hexdigest()
    (args.out_dir / "coverage_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    instrumentation_rows = [
        build_instrumentation_row(env, instrumented_at=harvested_at) for env in envelopes
    ]
    instrumentation_path = args.out_dir / "prospective_cycle_metrics_instrumentation.jsonl"
    with instrumentation_path.open("w", encoding="utf-8") as handle:
        for row in instrumentation_rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")

    instrumentation_report = instrumentation_coverage(instrumentation_rows)
    instrumentation_report["instrumentation_version"] = INSTRUMENTATION_VERSION
    instrumentation_report["instrumentation_sha256"] = hashlib.sha256(
        instrumentation_path.read_bytes()
    ).hexdigest()
    (args.out_dir / "cycle_metrics_instrumentation_report.json").write_text(
        json.dumps(instrumentation_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(universe)
    print(f"  events                    {report['event_count']}")
    print(f"  reachable from main       {report['reachable_from_main_history']}")
    print(f"  at risk (branch-only)     {report['at_risk_branch_only']}")
    print(f"  distinct schema_versions  {report['distinct_declared_schema_versions']}")
    print(f"  without schema_version    {report['events_without_declared_schema_version']}")
    print(f"  carrying CANNOT_* markers {report['events_carrying_unmeasured_markers']}")
    print(f"  unparseable               {report['unparseable_count']}")
    print(instrumentation_path)
    print(f"  v1 instrumentation rows   {instrumentation_report['row_count']}")
    print(
        "  rows with known denominators "
        f"{instrumentation_report['rows_with_known_denominators']}"
    )


if __name__ == "__main__":
    main()
