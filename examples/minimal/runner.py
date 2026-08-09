#!/usr/bin/env python3
"""Deterministic example adapter for reviewer-facing RAKL execution tests.

This is not a language model. It demonstrates the provider-neutral execution-envelope
protocol and returns a proposal-shaped JSON object without scientific authority.
"""

import json
import sys


def main() -> int:
    envelope = json.load(sys.stdin)
    packet = envelope["task_packet"]
    config = envelope["generation_config"]
    result = {
        "proposal": "Example runner received the RAKL task packet.",
        "evidence_used": [record["record_id"] for record in packet.get("selected_records", [])],
        "uncertainties": ["This deterministic runner is not an LLM and does not evaluate scientific truth."],
        "contradictions_or_obstructions": [],
        "next_discriminator": "Replace this example runner with a profile-compatible model adapter.",
        "status": "CANNOT_CHECK",
        "received_generation_config": config,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
