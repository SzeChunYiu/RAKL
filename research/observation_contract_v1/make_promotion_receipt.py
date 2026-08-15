"""Mint the Phase-5 promotion receipt for Observation Contract v1."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

OUT = Path("research/observation_contract_v1/PROMOTION_RECEIPT.json")
PACKET = Path("research/observation_contract_v1/packet")


def sh(*args: str) -> str:
    return subprocess.run(args, capture_output=True, text=True, check=True).stdout.strip()


def packet_digest() -> str:
    """Digest over the vendored packet files, sorted by path."""
    h = hashlib.sha256()
    for path in sorted(PACKET.rglob("*")):
        if path.is_file():
            h.update(path.name.encode("utf-8"))
            h.update(path.read_bytes())
    return h.hexdigest()


def main() -> int:
    manifest = json.loads((PACKET / "MANIFEST.json").read_text(encoding="utf-8"))
    receipt = {
        "schema_version": "rakl-observation-contract-promotion-receipt-v1",
        "status": "PLUGIN_LANDED_SPEC_CLOSED_EMPIRICAL_ASSURANCE_OPEN",
        "grants_scientific_authority": False,
        "grants_method_promotion_authority": False,
        "source_packet": {
            "artifact": manifest["artifact"],
            "bound_repo_snapshot": manifest["bound_repo_snapshot"],
            "file_count": manifest["file_count_excluding_manifest"],
            "manifest_verified": "all 24 files byte-identical to MANIFEST.json before porting",
            "vendored_packet_digest": packet_digest(),
        },
        "base_commit": sh("git", "rev-parse", "HEAD"),
        "base_commit_subject": sh("git", "log", "-1", "--format=%s"),
        "final_commit": "assigned at squash-merge; see the PR that carries this receipt",
        "implementation": {
            "module": "src/rakl/observation_contract.py",
            "tests": "tests/test_observation_contract.py",
            "integration": (
                "verdicts project into the existing AuditResidual and run through the frozen "
                "decide() chain; no second decision chain is introduced"
            ),
            "defect_found_by_production_test": (
                "the first verdict mapping let a resource bound outrank an evaluator/source "
                "contradiction; EVALUATOR_CONTRACT_TENSION now sets evaluator_invalid so it "
                "inherits the frozen chain's top priority"
            ),
        },
        "verification": {
            "packet_reference_tests": "14 passed (run before porting)",
            "production_tests": "tests/test_observation_contract.py rc=0",
            "rfa_v1_conformance": "37/37, committed RFA_V1_CONFORMANCE_RESULT.json unchanged",
            "paper_builds": {
                "paper-01": "latexmk rc=0, CI gate clean, 62 pages",
                "paper-02": "latexmk rc=0, CI gate clean, 28 pages",
                "paper-03": "latexmk rc=0, CI gate clean, 59 pages",
            },
            "full_suite": "see the PR's pytest check on the exact head",
            "ci_note": "CI success is read from the exact-head check runs, never inferred from a committed JSON",
        },
        "papers_changed": [
            "publication/papers/paper-02-structural-mechanics/sections/01a_acquisition_executor_boundary.tex",
            "publication/papers/paper-01-epistemic-mechanics/sections/03b_solver_noninterference.tex",
            "publication/papers/paper-03-method-evolution-mechanics/sections/04d_recursive_formulation.tex",
        ],
        "papers_deliberately_unchanged": {
            "paper-06": (
                "the packet conditions its empirical extension on the RFC-v1 benchmark being "
                "refrozen on the implementation subject, which has not happened"
            )
        },
        "authority": {
            "core_reopen": "NO",
            "new_privileged_effect": False,
            "new_authority_dimension": False,
            "new_recursion_layer": False,
            "authority_projection_unchanged": True,
            "evaluator_policy_path": "unchanged; the plugin records the epoch and refuses cross-epoch comparison",
        },
        "prior_negatives_preserved": {
            "arn_acquisition_negative": (
                "unchanged under its original contract; a semantic or external successor is a "
                "different frozen acquisition regime and neither erases nor retroactively "
                "confirms it"
            ),
            "history_semantics": "contract change stales dependent results under the predecessor digest; nothing deleted",
        },
        "open_gates": [
            "RFA_FRESH_UTILITY_ASSURANCE = OPEN_EMPIRICAL",
            "SEMANTIC_PARENT_EXECUTION = CANNOT_CHECK_RESOURCE_BOUND",
            "SCAR_FRESH_FORMULATION_DIAGNOSTIC = PASS_EXPLORATORY (37/42 is contract-relative to one 12-record block, not a corpus rate)",
        ],
    }
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")
    print(f"base={receipt['base_commit'][:8]} packet_digest={receipt['source_packet']['vendored_packet_digest'][:16]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
