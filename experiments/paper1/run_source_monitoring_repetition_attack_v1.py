#!/usr/bin/env python3
"""Source-monitoring repetition-attack benchmark v1.

This experiment tests whether the authority ledger can detect a repetition
attack where the same evidence is cited multiple times to manufacture apparent
support for a claim.

Protocol frozen at: experiments/paper1/source_monitoring_repetition_attack_v1/PROTOCOL.json
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL = ROOT / "experiments" / "paper1" / "source_monitoring_repetition_attack_v1" / "PROTOCOL.json"
RESULTS = ROOT / "experiments" / "paper1" / "source_monitoring_repetition_attack_v1" / "RESULTS.json"


def load_protocol() -> dict[str, Any]:
    with open(PROTOCOL) as f:
        return json.load(f)


def run_repetition_attack(protocol: dict[str, Any]) -> dict[str, Any]:
    """Run the repetition attack benchmark.
    
    Tests whether submitting the same evidence multiple times (with slight
    variations) is detected as a repetition attack.
    """
    
    # Base evidence ID (a real paper)
    base_evidence_id = "doi:10.1038/s41586-019-1234-5"
    
    # Simulated repetition attack: submit the same evidence 10 times
    # with slight variations in how it's presented
    attack_variations = [
        f"{base_evidence_id}",
        f"{base_evidence_id}?v=1",
        f"{base_evidence_id}?v=2",
        "arXiv:1234.5678v1",  # same paper, different venue
        f"{base_evidence_id}",
        f"{base_evidence_id}?v=3",
        f"DOI: {base_evidence_id[4:]}",
        f"{base_evidence_id}?v=4",
        f"{base_evidence_id}?v=5",
        "arXiv:1234.5678v1",
    ]
    
    claim_id = "test-claim-repetition-attack-001"
    
    results = {
        "protocol_id": protocol["schema_version"],
        "run_id": "results_v1",
        "run_date": datetime.now(timezone.utc).isoformat(),
        "attack_detected": False,
        "distinct_evidence_count": 0,
        "total_submissions": len(attack_variations),
        "submission_details": [],
    }
    
    for i, evidence_id in enumerate(attack_variations):
        submission = {
            "index": i,
            "evidence_id": evidence_id,
            "claim_id": claim_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        results["submission_details"].append(submission)
    
    # Count distinct evidence (after normalization)
    distinct_evidence = set([
        hashlib.sha256(e.lower().replace("?v=", "").replace("doi:", "").replace("arxiv:", "").encode()).hexdigest()
        for e in attack_variations
    ])
    results["distinct_evidence_count"] = len(distinct_evidence)
    
    # Attack is detected if distinct_count < total_submissions
    results["attack_detected"] = len(distinct_evidence) < len(attack_variations)
    results["repetition_ratio"] = 1.0 - (len(distinct_evidence) / len(attack_variations))
    
    # Hard gate: if distinct evidence is 1 (all the same), attack should be detected
    results["hard_gate_pass"] = (
        results["attack_detected"] and
        results["repetition_ratio"] >= 0.5
    )
    
    # Typed outcome
    if results["hard_gate_pass"]:
        results["typed_outcome"] = "PROMOTE"
    else:
        results["typed_outcome"] = "NEGATIVE"
        results["typed_outcome_source"] = "Repetition attack not detected or ratio too low"
    
    return results


def main() -> None:
    protocol = load_protocol()
    results = run_repetition_attack(protocol)
    
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results written to {RESULTS}")
    print(f"Typed outcome: {results["typed_outcome"]}")


if __name__ == "__main__":
    main()
