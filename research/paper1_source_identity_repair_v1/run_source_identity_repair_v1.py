#!/usr/bin/env python3
"""Paper I source-identity repair v1 — replay of the frozen repetition attack.

Targets ``NEG-p1-source-monitoring-repetition-attack`` (one-stage attribution:
extraction). The registered lever is source-identity / lineage resolution. The
hard-gate threshold, formula and denominator are copied byte-identical from the
parent protocol and are never touched by this runner.

Two normalizer arms are executed **in one process over one corpus**:

* ``v1_baseline`` — the frozen harness's inline expression, transcribed verbatim.
* ``v2_repair``   — ``rakl.source_identity.resolve_source_identities``.

Controls (benign no-false-merge, planted near-misses) are evaluated and reported
*before* the attack result, per the protocol.

Run:  PYTHONPATH=src python3 research/paper1_source_identity_repair_v1/run_source_identity_repair_v1.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rakl.source_identity import (  # noqa: E402
    SourceIdentityMapping,
    canonicalize_source_identifier,
    resolve_source_identities,
)

PROTOCOL_PATH = HERE / "PROTOCOL_V2.json"
RECEIPT_PATH = HERE / "RECEIPT.json"

# --------------------------------------------------------------------------
# Frozen corpora
# --------------------------------------------------------------------------

# Verbatim from the parent RESULTS.json submission_details[].evidence_id.
ATTACK_CORPUS: tuple[str, ...] = (
    "doi:10.1038/s41586-019-1234-5",
    "doi:10.1038/s41586-019-1234-5?v=1",
    "doi:10.1038/s41586-019-1234-5?v=2",
    "arXiv:1234.5678v1",
    "doi:10.1038/s41586-019-1234-5",
    "doi:10.1038/s41586-019-1234-5?v=3",
    "DOI: 10.1038/s41586-019-1234-5",
    "doi:10.1038/s41586-019-1234-5?v=4",
    "doi:10.1038/s41586-019-1234-5?v=5",
    "arXiv:1234.5678v1",
)

# Eight genuinely distinct sources. Must NOT collapse.
BENIGN_DISTINCT: tuple[str, ...] = (
    "doi:10.1038/s41586-019-1234-5",
    "doi:10.1126/science.aaa1234",
    "arXiv:2401.00111v1",
    "arXiv:2312.09876v3",
    "https://example.org/dataset?id=1",
    "https://example.org/dataset?id=2",
    "isbn:978-0-13-235088-4",
    "https://records.example.org/Archive/Case-Alpha",
)

# Pairs that look similar but are genuinely different works. Must stay 2 apiece.
NEAR_MISS_PAIRS: tuple[tuple[str, str, str], ...] = (
    (
        "adjacent_doi",
        "doi:10.1038/s41586-019-1234-5",
        "doi:10.1038/s41586-019-1234-6",
    ),
    (
        "same_author_arxiv_pair",
        "arXiv:2401.00111",
        "arXiv:2401.00112",
    ),
    (
        "identity_bearing_url_query",
        "https://example.org/paper?id=1",
        "https://example.org/paper?id=2",
    ),
    (
        "doi_supplement_suffix",
        "doi:10.1038/s41586-019-1234-5",
        "doi:10.1038/s41586-019-1234-5.suppl",
    ),
    (
        "v1_baseline_collision_pair",
        "doi:10.1000/x?v=1",
        "doi:10.1000/x1",
    ),
    (
        "case_varied_opaque_path",
        "https://records.example.org/Archive/Case-Alpha",
        "https://records.example.org/archive/case-alpha",
    ),
)

# Two versions of one arXiv work: distinct entities, one lineage root.
ARXIV_VERSION_PAIR: tuple[str, str] = ("arXiv:2401.00111v1", "arXiv:2401.00111v2")

# Trivially equivalent surface forms of one DOI. Must collapse to exactly 1.
EQUIVALENT_SURFACE_FORMS: tuple[str, ...] = (
    "doi:10.1038/s41586-019-1234-5",
    "DOI: 10.1038/s41586-019-1234-5",
    "10.1038/S41586-019-1234-5",
    "https://doi.org/10.1038/s41586-019-1234-5",
    "http://dx.doi.org/10.1038/s41586-019-1234-5#results",
    "doi:10.1038/s41586-019-1234-5?v=7",
    "  doi:10.1038/s41586-019-1234-5.  ",
)

DECLARED_CROSS_VENUE = (
    SourceIdentityMapping(left="arXiv:1234.5678v1", right="doi:10.1038/s41586-019-1234-5"),
)


# --------------------------------------------------------------------------
# Arms
# --------------------------------------------------------------------------


def v1_baseline_distinct(identifiers: Sequence[str]) -> int:
    """The frozen harness normalizer, transcribed verbatim (line 77 of the parent)."""

    return len(
        {
            hashlib.sha256(
                e.lower().replace("?v=", "").replace("doi:", "").replace("arxiv:", "").encode()
            ).hexdigest()
            for e in identifiers
        }
    )


def v2_distinct(identifiers: Sequence[str]) -> int:
    return resolve_source_identities(identifiers).distinct_canonical_count


def repetition_ratio(distinct: int, total: int) -> float:
    """Byte-identical to the parent harness formula. Never modified."""

    return 1.0 - (distinct / total)


def gate(distinct: int, total: int, threshold: float) -> dict[str, Any]:
    ratio = repetition_ratio(distinct, total)
    detected = distinct < total
    return {
        "distinct_count": distinct,
        "total_submissions": total,
        "attack_detected": detected,
        "repetition_ratio": ratio,
        "hard_gate_pass": bool(detected and ratio >= threshold),
    }


# --------------------------------------------------------------------------
# Controls (evaluated first)
# --------------------------------------------------------------------------


CONTROL_IDS: tuple[str, ...] = (
    "C1_no_false_merge_benign",
    "C2_near_miss_pairs_stay_separate",
    "C3_arxiv_versions_distinct_but_share_root",
    "C4_baseline_over_merge_exists",
    "C5_equivalent_surface_forms_collapse",
)


def run_controls() -> dict[str, Any]:
    controls: dict[str, Any] = {}

    # C1 — benign corpus of genuinely distinct sources must not be collapsed.
    v2_benign = v2_distinct(BENIGN_DISTINCT)
    v1_benign = v1_baseline_distinct(BENIGN_DISTINCT)
    controls["C1_no_false_merge_benign"] = {
        "expected_distinct": len(BENIGN_DISTINCT),
        "v2_distinct": v2_benign,
        "v1_distinct": v1_benign,
        "v2_false_merges": len(BENIGN_DISTINCT) - v2_benign,
        "v1_false_merges": len(BENIGN_DISTINCT) - v1_benign,
        "passed": v2_benign == len(BENIGN_DISTINCT),
    }

    # C2 — planted near-miss pairs must stay separate.
    pair_rows = []
    for name, left, right in NEAR_MISS_PAIRS:
        v2_pair = v2_distinct((left, right))
        v1_pair = v1_baseline_distinct((left, right))
        pair_rows.append(
            {
                "pair": name,
                "left": left,
                "right": right,
                "v1_distinct": v1_pair,
                "v2_distinct": v2_pair,
                "v1_over_merged": v1_pair < 2,
                "v2_over_merged": v2_pair < 2,
            }
        )
    controls["C2_near_miss_pairs_stay_separate"] = {
        "pairs": pair_rows,
        "v2_over_merge_count": sum(1 for row in pair_rows if row["v2_over_merged"]),
        "passed": all(not row["v2_over_merged"] for row in pair_rows),
    }

    # C3 — arXiv versions: distinct entities, shared lineage root.
    version_res = resolve_source_identities(ARXIV_VERSION_PAIR)
    controls["C3_arxiv_versions_distinct_but_share_root"] = {
        "identifiers": list(ARXIV_VERSION_PAIR),
        "distinct_canonical": version_res.distinct_canonical_count,
        "distinct_roots": version_res.distinct_root_count,
        "syntactic_edges": [list(e) for e in _edges(version_res.syntactic_edges)],
        "passed": version_res.distinct_canonical_count == 2
        and version_res.distinct_root_count == 1,
    }

    # C4 — the control must be able to fail: show the baseline over-merges.
    baseline_over_merges = [row["pair"] for row in pair_rows if row["v1_over_merged"]]
    controls["C4_baseline_over_merge_exists"] = {
        "baseline_over_merged_pairs": baseline_over_merges,
        "passed": bool(baseline_over_merges),
        "note": "the v1 normalizer both under-merges (the attack) and over-merges; a control that no arm can fail proves nothing",
    }

    # C5 — positive-collapse control: trivially equivalent forms must collapse.
    equiv = resolve_source_identities(EQUIVALENT_SURFACE_FORMS)
    controls["C5_equivalent_surface_forms_collapse"] = {
        "identifiers": list(EQUIVALENT_SURFACE_FORMS),
        "v1_distinct": v1_baseline_distinct(EQUIVALENT_SURFACE_FORMS),
        "v2_distinct": equiv.distinct_canonical_count,
        "passed": equiv.distinct_canonical_count == 1,
    }

    # Explicit id list, not a scan over whatever happens to be in the dict: the
    # terminal selector depends on this single value, so its inputs must be
    # auditable and must fail loudly (KeyError) if a control goes missing.
    controls["all_passed"] = all(controls[cid]["passed"] for cid in CONTROL_IDS)
    controls["control_ids"] = list(CONTROL_IDS)
    return controls


def _edges(edges: Sequence[Any]) -> list[tuple[str, str, str]]:
    return [(e.left, e.right, e.relation.value) for e in edges]


# --------------------------------------------------------------------------
# Attack replay
# --------------------------------------------------------------------------


def run_attack(threshold: float, total: int) -> dict[str, Any]:
    v1_distinct = v1_baseline_distinct(ATTACK_CORPUS)
    v1_row = gate(v1_distinct, total, threshold)

    v2_res = resolve_source_identities(ATTACK_CORPUS)
    v2_row = gate(v2_res.distinct_canonical_count, total, threshold)

    v2_mapped = resolve_source_identities(ATTACK_CORPUS, DECLARED_CROSS_VENUE)

    return {
        "corpus": list(ATTACK_CORPUS),
        "v1_baseline": v1_row,
        "v2_repair": v2_row,
        "v2_repair_diagnostics": {
            "distinct_canonical": sorted(v2_res.distinct_canonical),
            "distinct_roots_no_declared_record": sorted(v2_res.distinct_roots),
            "syntactic_edges": _edges(v2_res.syntactic_edges),
            "declared_edges": [],
        },
        "v2_with_declared_cross_venue_record": {
            "note": "DIAGNOSTIC ONLY - does not feed the gate. Cross-venue sameness is not derivable from the identifier strings.",
            "distinct_canonical": v2_mapped.distinct_canonical_count,
            "distinct_roots": v2_mapped.distinct_root_count,
            "declared_edges": _edges(v2_mapped.declared_edges),
            "repetition_ratio_on_roots": repetition_ratio(v2_mapped.distinct_root_count, total),
        },
    }


def main() -> int:
    protocol = json.loads(PROTOCOL_PATH.read_text())
    slot = protocol["gate_slot_declared_before_run"]
    threshold = slot["threshold_repetition_ratio_min"]
    total = slot["total_submissions"]

    controls = run_controls()
    attack = run_attack(threshold, total)

    parent_reproduced = attack["v1_baseline"]["distinct_count"] == 8
    if not parent_reproduced:
        terminal = "CANNOT_CHECK_PARENT_NOT_REPRODUCED"
    elif not controls["all_passed"]:
        terminal = "NORMALIZATION_UNSAFE_OVER_MERGES"
    elif attack["v2_repair"]["hard_gate_pass"]:
        terminal = "ATTACK_DETECTED_CONTROLS_PASSING"
    else:
        terminal = "ATTACK_STILL_SUCCEEDS"

    receipt = {
        "schema_version": protocol["schema_version"],
        "run_date": datetime.now(timezone.utc).isoformat(),
        "protocol_path": "research/paper1_source_identity_repair_v1/PROTOCOL_V2.json",
        "parent_negative": protocol["parent_negative"],
        "one_stage_attribution": protocol["one_stage_attribution"],
        "lever_applied": "source-identity / lineage resolution (scheme-aware canonicalization)",
        "threshold_changed": False,
        "formula_changed": False,
        "denominator_changed": False,
        "gate_slot": slot,
        "parent_receipt_reproduced_in_process": parent_reproduced,
        "terminal_selector_falsification_check": protocol["terminal_selector_falsification_check"],
        "controls": controls,
        "attack": attack,
        "code_change": [
            "src/rakl/source_identity.py (new)",
            "src/rakl/identity.py (EvidenceIdentityLedger.ancestry_roots)",
            "src/rakl/__init__.py (exports)",
        ],
        "tests": ["tests/test_source_identity.py"],
        "residual": (
            "Cross-venue identity (DOI <-> arXiv preprint) is NOT derivable from identifier "
            "strings and is not attempted syntactically. In this attack corpus the two arXiv "
            "submissions are byte-identical, so the gate flips on surface-form canonicalization "
            "alone; a repetition attack that used two DIFFERENT surface forms of the SAME "
            "cross-venue work would still need a declared mapping record."
        ),
        "terminal": terminal,
        "grants_scientific_authority": False,
        "promotion_verdict": "KEEP_PROPOSAL_ONLY_PENDING_GOVERNANCE",
    }

    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n")

    print(f"controls.all_passed = {controls['all_passed']}")
    print(f"C1 no-false-merge   = {controls['C1_no_false_merge_benign']['passed']}")
    print(f"parent reproduced   = {parent_reproduced} (v1 distinct={attack['v1_baseline']['distinct_count']})")
    print(
        "attack v1 -> distinct={} ratio={:.2f} gate_pass={}".format(
            attack["v1_baseline"]["distinct_count"],
            attack["v1_baseline"]["repetition_ratio"],
            attack["v1_baseline"]["hard_gate_pass"],
        )
    )
    print(
        "attack v2 -> distinct={} ratio={:.2f} gate_pass={}".format(
            attack["v2_repair"]["distinct_count"],
            attack["v2_repair"]["repetition_ratio"],
            attack["v2_repair"]["hard_gate_pass"],
        )
    )
    print(f"TERMINAL = {terminal}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
