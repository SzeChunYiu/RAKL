"""Arm executor for BENEFIT-L1-COMPOSITION-V1. One process per arm (step 2 spawns
each separately) over the byte-identical gold-stripped corpus.

Arm A — untyped chaining, PROTOCOL.json arms.A_untyped_chaining, implemented
verbatim to the frozen decision-equivalent rule in EVALUATOR.py (COMPOSED iff
every consecutive endpoint pair connects syntactically; the contract block is
present in the input record and deliberately ignored).

Arm B — typed transition algebra: encodes each chain as a
rakl.bridge_composition.BridgePath (SimilarityWitness-backed hops, BridgeHandoff
junctions, chain-level ErrorCompositionRule) and calls evaluate_bridge_path —
the exact functions pinned in PROTOCOL.json (module pins verified before any
declaration). COMPOSED iff the verdict is COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY;
NAVIGABLE_ONLY / REJECT / TRIAL_INVALID / CANNOT_CHECK all map to REFUSED
(fail-closed) with the sub-verdict retained for the per-class read.

Encoding notes (record -> BridgePath), chosen so each frozen licensing check maps
1:1 onto a module check:
- witness relation is TRANSFORMABLE_TO for every hop (a plain typed-transition
  relation with no extra constraint obligations); question_or_qoi is the chain id
  compose question for path and hops alike.
- hop witness mapping_pairs = cross product (roles consumed at the hop's source
  junction) x (roles delivered at the hop's target junction); chain endpoints use
  the fixed pseudo-roles chain_input / chain_output. Handoff role_pairs = (r, r)
  for each consumed role, so evaluate_bridge_path's delivered/consumed check is
  exactly the frozen consumed-subset-of-delivered condition.
- witness-level evidence_ids / handoff evidence_ids use a constant record
  pointer; the D2-sensitive lineage lives ONLY in BridgeHop.evidence_lineage_ids
  so a record omission trips exactly the module's lineage check.
- mapping_admissibility/probe_family are constant frozen-generator declarations
  (declared_before_fit=True, null_calibration_passed=True): the corpus is a
  known-answer world, and record incompleteness is expressed through the
  licensing fields the protocol registered, not through witness bookkeeping.
"""
from __future__ import annotations

import argparse
import json
import os
import resource
import sys
import time
from typing import Any

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

from rakl.bridge_composition import (  # noqa: E402
    BridgeHandoff,
    BridgeHop,
    BridgePath,
    BridgePathVerdict,
    ErrorCompositionRule,
    ErrorCompositionRuleKind,
    evaluate_bridge_path,
)
from rakl.similarity import (  # noqa: E402
    MappingAdmissibility,
    ProbeFamily,
    SimilarityRelation,
    SimilarityWitness,
)


def arm_a_declare(row: dict[str, Any]) -> dict[str, Any]:
    """Verbatim frozen rule: syntactic endpoint connectivity only."""
    skeleton = row["skeleton"]
    for i in range(len(skeleton) - 1):
        if skeleton[i]["target_id"] != skeleton[i + 1]["source_id"]:
            return {"chain_id": row["chain_id"], "declaration": "REFUSED",
                    "sub_verdict": "DISCONNECTED"}
    return {"chain_id": row["chain_id"], "declaration": "COMPOSED"}


def _witness(row: dict[str, Any], i: int, qoi: str) -> SimilarityWitness:
    skeleton = row["skeleton"]
    contract = row["contract"]
    per_hop = contract["per_hop"]
    handoffs = contract["handoffs"]
    n = len(skeleton)
    in_roles = tuple(handoffs[i - 1].get("roles_consumed", ())) if i > 0 else ("chain_input",)
    out_roles = tuple(handoffs[i].get("roles_delivered", ())) if i < n - 1 else ("chain_output",)
    mapping_pairs = tuple((a, b) for a in in_roles for b in out_roles)
    hop = per_hop[i]
    return SimilarityWitness(
        relation=SimilarityRelation.TRANSFORMABLE_TO,
        source_id=skeleton[i]["source_id"],
        target_id=skeleton[i]["target_id"],
        source_domain=f"world:{skeleton[i]['source_id']}",
        target_domain=f"world:{skeleton[i]['target_id']}",
        question_or_qoi=qoi,
        mapping_pairs=mapping_pairs,
        preserved=tuple(hop.get("preserved", ())),
        not_preserved=tuple(hop.get("not_preserved", ())),
        regime=tuple(hop.get("regime", ())),
        evidence_ids=(f"record:{row['chain_id']}",),
        mapping_admissibility=MappingAdmissibility(
            family_id="frozen-generator-contract-v1",
            declared_before_fit=True,
            constraints=("frozen_generator_contract",),
            constraint_violations=(),
            null_calibration_passed=True,
        ),
        probe_family=ProbeFamily(
            family_id="l1-composition-corpus-v1",
            probe_ids=(f"probe:{row['chain_id']}:hop{i}",),
        ),
    )


def arm_b_declare(row: dict[str, Any]) -> dict[str, Any]:
    chain_id = row["chain_id"]
    contract = row["contract"]
    skeleton = row["skeleton"]
    n = len(skeleton)
    per_hop = contract.get("per_hop")
    handoffs = contract.get("handoffs")
    if not isinstance(per_hop, list) or len(per_hop) != n \
            or not isinstance(handoffs, list) or len(handoffs) != n - 1:
        return {"chain_id": chain_id, "declaration": "REFUSED",
                "sub_verdict": "MALFORMED_RECORD"}
    rule_rec = contract.get("error_composition_rule") or {}
    try:
        kind = ErrorCompositionRuleKind(rule_rec.get("kind"))
    except ValueError:
        return {"chain_id": chain_id, "declaration": "REFUSED",
                "sub_verdict": "MALFORMED_RECORD",
                "detail": "unknown error composition rule kind"}
    qoi = f"compose:{chain_id}"
    path = BridgePath(
        path_id=chain_id,
        question_or_qoi=qoi,
        hops=tuple(
            BridgeHop(
                witness=_witness(row, i, qoi),
                approximation_error_upper_bound=per_hop[i].get("error_bound"),
                evidence_lineage_ids=tuple(per_hop[i].get("evidence_lineage_ids", ())),
                error_semantics_id=per_hop[i].get("error_semantics_id", ""),
            )
            for i in range(n)
        ),
        handoffs=tuple(
            BridgeHandoff(
                junction_id=handoffs[k].get("junction_id", ""),
                role_pairs=tuple((r, r) for r in handoffs[k].get("roles_consumed", ())),
                compatibility_passed=handoffs[k].get("compatibility_passed"),
                evidence_ids=(f"record:{chain_id}:junction{k}",),
            )
            for k in range(n - 1)
        ),
        claimed_end_to_end_invariants=tuple(contract.get("claimed_invariants", ())),
        max_accumulated_error=contract.get("max_accumulated_error"),
        hidden_labels_exposed=False,
        declared_before_outcomes=True,
        error_composition_rule=ErrorCompositionRule(
            rule_id=rule_rec.get("rule_id", ""),
            error_semantics_id=rule_rec.get("error_semantics_id", ""),
            kind=kind,
            certified_before_outcomes=True,
        ),
    )
    report = evaluate_bridge_path(path)
    if report.verdict is BridgePathVerdict.COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY:
        return {"chain_id": chain_id, "declaration": "COMPOSED",
                "sub_verdict": report.verdict.value}
    return {"chain_id": chain_id, "declaration": "REFUSED",
            "sub_verdict": report.verdict.value,
            "reasons": list(report.reasons)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", required=True, choices=("A", "B"))
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    with open(args.corpus, "r", encoding="utf-8") as handle:
        rows = json.load(handle)["chains"]
    for row in rows:
        if "gold_label" in row or "class" in row:
            print("REFUSING: arm input contains gold/class fields", file=sys.stderr)
            return 2

    declare = arm_a_declare if args.arm == "A" else arm_b_declare
    t0 = time.monotonic()
    declarations = [declare(row) for row in sorted(rows, key=lambda r: r["chain_id"])]
    elapsed = time.monotonic() - t0
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    payload = {
        "protocol_id": "BENEFIT-L1-COMPOSITION-V1",
        "arm": args.arm,
        "declarations": declarations,
        "n_declared_composed": sum(1 for d in declarations if d["declaration"] == "COMPOSED"),
        "wall_clock_seconds": elapsed,
        "peak_rss_bytes": peak_rss,
        "token_budget_used": 0,
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
