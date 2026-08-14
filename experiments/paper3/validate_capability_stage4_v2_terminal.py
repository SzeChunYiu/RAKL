from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED_PROCESS_CODE = {
    "CAPABLE_MODEL_AUTHORIZE_RECEIPT_V3": 0,
    "DIAGNOSTIC_OVERFIT_OR_INSUFFICIENT_CAPABILITY": 1,
    "CAPABLE_MODEL_NOT_FEASIBLE_UNDER_RESOURCE_ENVELOPE": 2,
    "QUALIFICATION_BENCHMARK_DEGENERATE": 3,
}


def validate(receipt_path: Path, runner_code: int) -> str:
    """Validate that the runner ended in one registered scientific terminal.

    The model runner uses non-zero codes to make local interactive failures
    visible. SLURM scheduler state is a different coordinate: a job that ran to a
    complete, hash-bound scientific NEGATIVE or RESOURCE terminal must finish the
    wrapper successfully so harvest does not reinterpret that terminal as an
    infrastructure crash. This validator is the boundary between those two
    coordinates.
    """

    if not receipt_path.exists():
        raise RuntimeError("stage5_receipt_missing")
    receipt = json.loads(receipt_path.read_text())
    if receipt.get("schema_version") != "rakl-capability-qualification-stage5-result-v2":
        raise RuntimeError("stage5_receipt_schema_not_v2")
    terminal = receipt.get("terminal")
    if terminal not in EXPECTED_PROCESS_CODE:
        raise RuntimeError(f"unregistered_stage5_terminal:{terminal}")
    expected = EXPECTED_PROCESS_CODE[terminal]
    if runner_code != expected:
        raise RuntimeError(
            f"runner_code_terminal_mismatch:{runner_code}:{terminal}:{expected}"
        )
    if receipt.get("grants_scientific_authority") is not False:
        raise RuntimeError("invalid_scientific_authority_flag")
    hard = receipt.get("scoring_hardening", {})
    if hard.get("thresholds_changed_from_v1") is not False:
        raise RuntimeError("numeric_threshold_change_detected")
    if hard.get("panel_changed_from_v1") is not False:
        raise RuntimeError("panel_change_detected")
    if hard.get("model_or_interface_changed_from_v1") is not False:
        raise RuntimeError("model_or_interface_change_detected")
    return str(terminal)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("receipt", type=Path)
    ap.add_argument("runner_code", type=int)
    args = ap.parse_args()
    terminal = validate(args.receipt, args.runner_code)
    print(f"VALID_STAGE5_TERMINAL:{terminal}")


if __name__ == "__main__":
    main()
