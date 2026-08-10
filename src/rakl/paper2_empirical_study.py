from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Mapping


class PreflightVerdict(str, Enum):
    PASS = "PASS"
    CANNOT_CHECK = "CANNOT_CHECK"
    REJECT = "REJECT"


@dataclass(frozen=True)
class PreflightReport:
    verdict: PreflightVerdict
    blockers: tuple[str, ...]
    invalid_bindings: tuple[str, ...]
    checks: tuple[dict[str, str], ...]
    evaluated_result_record_count: int = 0


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(payload)


def _resolve(path: str, base_dir: Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else base_dir / candidate


def _audit_artifact(
    *,
    owner: str,
    binding: object,
    base_dir: Path,
    blockers: list[str],
    invalid: list[str],
    checks: list[dict[str, str]],
) -> None:
    if not isinstance(binding, Mapping):
        blockers.append(f"artifact_binding_missing:{owner}")
        checks.append({"id": owner, "state": "CANNOT_CHECK", "detail": "binding missing"})
        return
    raw_path = binding.get("path")
    declared_sha = binding.get("sha256")
    if not isinstance(raw_path, str) or not raw_path.strip():
        blockers.append(f"artifact_path_missing:{owner}")
        checks.append({"id": owner, "state": "CANNOT_CHECK", "detail": "path missing"})
        return
    if not isinstance(declared_sha, str) or len(declared_sha) != 64:
        blockers.append(f"artifact_sha256_missing:{owner}")
        checks.append({"id": owner, "state": "CANNOT_CHECK", "detail": "sha256 missing"})
        return
    path = _resolve(raw_path, base_dir)
    if not path.is_file():
        blockers.append(f"artifact_missing:{owner}:{raw_path}")
        checks.append({"id": owner, "state": "CANNOT_CHECK", "detail": "file unavailable"})
        return
    observed = _sha256_bytes(path.read_bytes())
    if observed != declared_sha:
        invalid.append(f"sha256_mismatch:{owner}:{raw_path}")
        checks.append({"id": owner, "state": "REJECT", "detail": "sha256 mismatch"})
        return
    checks.append({"id": owner, "state": "PASS", "detail": "identity bound"})


def audit_study_packet(
    packet: Mapping[str, object],
    *,
    base_dir: Path | None = None,
    command_finder: Callable[[str], str | None] = shutil.which,
) -> PreflightReport:
    """Audit execution readiness without opening or creating evaluated outcomes."""

    root = Path.cwd() if base_dir is None else base_dir
    blockers: list[str] = []
    invalid: list[str] = []
    checks: list[dict[str, str]] = []

    if packet.get("schema_version") != "paper2-matched-study-freeze-v1":
        invalid.append("unsupported_packet_schema")
    if packet.get("evaluated_results_opened_before_freeze") is not False:
        invalid.append("freeze_chronology_violated")
    subject_sha = packet.get("subject_sha")
    if not isinstance(subject_sha, str) or len(subject_sha) != 40:
        invalid.append("subject_sha_invalid")

    for coordinate in ("protocol_id", "object", "qoi", "context"):
        if not isinstance(packet.get(coordinate), str) or not str(packet[coordinate]).strip():
            blockers.append(f"{coordinate}_missing")

    task_set = packet.get("task_set")
    if not isinstance(task_set, Mapping) or task_set.get("confirmatory") is not True:
        blockers.append("confirmatory_task_payload_missing")
    _audit_artifact(
        owner="task_set",
        binding=task_set,
        base_dir=root,
        blockers=blockers,
        invalid=invalid,
        checks=checks,
    )

    model = packet.get("model")
    if not isinstance(model, Mapping):
        blockers.append("model_contract_missing")
    else:
        for field in (
            "provider",
            "model_id",
            "model_revision",
            "adapter_command",
            "adapter_version",
            "credential_mode",
        ):
            if not isinstance(model.get(field), str) or not str(model[field]).strip():
                blocker = f"{field}_missing" if field.startswith("model_") else f"model_{field}_missing"
                blockers.append(blocker)
        if model.get("architecture_neutral_interface") is not True:
            blockers.append("base_model_interface_not_architecture_neutral")
        command = model.get("adapter_command")
        if isinstance(command, str) and command.strip() and command_finder(command) is None:
            blockers.append(f"model_adapter_unavailable:{command}")

    architecture_arms = packet.get("architecture_arms")
    if not isinstance(architecture_arms, list) or len(architecture_arms) < 2:
        blockers.append("architecture_prompt_assets_missing")
    else:
        for index, arm in enumerate(architecture_arms):
            arm_id = arm.get("id") if isinstance(arm, Mapping) else None
            owner = f"architecture_arm:{arm_id or index}"
            _audit_artifact(
                owner=owner,
                binding=arm,
                base_dir=root,
                blockers=blockers,
                invalid=invalid,
                checks=checks,
            )

    evidence_arms = packet.get("evidence_access_arms")
    expected_evidence = {"public", "curated", "complete_sealed"}
    observed_evidence = {
        str(arm.get("id"))
        for arm in evidence_arms or []
        if isinstance(arm, Mapping) and arm.get("id") is not None
    }
    if not isinstance(evidence_arms, list) or observed_evidence != expected_evidence:
        blockers.append("evidence_access_manifests_missing")
    if isinstance(evidence_arms, list):
        for index, arm in enumerate(evidence_arms):
            arm_id = arm.get("id") if isinstance(arm, Mapping) else None
            _audit_artifact(
                owner=f"evidence_arm:{arm_id or index}",
                binding=arm,
                base_dir=root,
                blockers=blockers,
                invalid=invalid,
                checks=checks,
            )

    resources = packet.get("resources")
    required_resources = (
        "seed_schedule",
        "active_context_token_budgets",
        "max_billable_tokens_per_run",
        "max_tool_calls_per_run",
        "max_wall_time_seconds_per_run",
    )
    if not isinstance(resources, Mapping) or any(not resources.get(key) for key in required_resources):
        blockers.append("resource_ceiling_or_seed_schedule_missing")

    evaluator = packet.get("evaluator")
    if not isinstance(evaluator, Mapping):
        blockers.append("protected_evaluator_missing")
    else:
        if evaluator.get("final_task_correctness_executable") is not True:
            blockers.append("final_task_correctness_evaluator_missing")
        if evaluator.get("arm_identity_blinded") is not True:
            blockers.append("evaluator_arm_blinding_missing")
        _audit_artifact(
            owner="evaluator",
            binding=evaluator,
            base_dir=root,
            blockers=blockers,
            invalid=invalid,
            checks=checks,
        )

    price_sheet = packet.get("price_sheet")
    if not isinstance(price_sheet, Mapping) or not price_sheet.get("id"):
        blockers.append("provider_price_sheet_missing")
    else:
        _audit_artifact(
            owner="price_sheet",
            binding=price_sheet,
            base_dir=root,
            blockers=blockers,
            invalid=invalid,
            checks=checks,
        )

    if invalid:
        verdict = PreflightVerdict.REJECT
    elif blockers:
        verdict = PreflightVerdict.CANNOT_CHECK
    else:
        verdict = PreflightVerdict.PASS
    return PreflightReport(
        verdict=verdict,
        blockers=tuple(dict.fromkeys(blockers)),
        invalid_bindings=tuple(dict.fromkeys(invalid)),
        checks=tuple(checks),
    )


def write_preflight_receipt(
    report: PreflightReport,
    *,
    packet: Mapping[str, object],
    output_path: Path,
    created_at_utc: str,
) -> None:
    receipt = {
        "schema_version": "paper2-execution-preflight-receipt-v1",
        "receipt_type": "execution_preflight_not_empirical_result",
        "created_at_utc": created_at_utc,
        "protocol_id": packet.get("protocol_id"),
        "subject_sha": packet.get("subject_sha"),
        "packet_canonical_sha256": _canonical_sha256(packet),
        "verdict": report.verdict.value,
        "blockers": list(report.blockers),
        "invalid_bindings": list(report.invalid_bindings),
        "checks": list(report.checks),
        "evaluated_result_record_count": report.evaluated_result_record_count,
        "empirical_claim_permitted": False,
        "claim_boundary": (
            "This receipt audits study execution readiness only; it is not a model-performance "
            "result and cannot support a comparative RAKL claim."
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit a frozen Paper 2 matched-study packet")
    parser.add_argument("packet", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--created-at-utc", required=True)
    args = parser.parse_args(argv)

    packet = json.loads(args.packet.read_text(encoding="utf-8"))
    report = audit_study_packet(packet, base_dir=Path.cwd())
    write_preflight_receipt(
        report,
        packet=packet,
        output_path=args.output,
        created_at_utc=args.created_at_utc,
    )
    print(json.dumps({"verdict": report.verdict.value, "blockers": list(report.blockers)}))
    return 0 if report.verdict is PreflightVerdict.PASS else 2


if __name__ == "__main__":
    raise SystemExit(main())
