from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import re
import resource
import socket
import subprocess
import sys
import time
from typing import Callable, Mapping

from .matched_microtrial import PendulumStructuredAnswer, score_pendulum_answer


_CONDITIONS = ("DIRECT_CORPUS", "RAKL_CONTEXT")
_REQUIRED_BINDINGS = (
    "system_prompt",
    "task",
    "questions",
    "direct_prompt",
    "rakl_prompt",
    "evaluator",
    "model_manifest",
    "tokenizer_manifest",
    "execution_contract",
    "environment",
    "resources",
    "prices",
    "blinding",
    "runner",
    "result_schema",
)
_ANSWER_FIELDS = (
    "small_angle_is_asymptotic",
    "finite_amplitude_increases_period",
    "context_distinct_claims_not_direct_contradictions",
    "ideal_period_is_mass_invariant",
    "context_alignment_required_before_contradiction",
    "supporting_source_ids",
    "rejected_as_misaligned_source_ids",
    "refuted_source_ids",
)
_SCORE_FIELDS = (
    "conceptual_correct",
    "conceptual_total",
    "required_support_recall",
    "support_precision",
    "misalignment_recall",
    "refutation_recall",
    "refutation_precision",
    "unsupported_source_count",
    "exact_conceptual_pass",
)
_PLACEHOLDER_MARKERS = (
    "TO_BE_PINNED",
    "TO_BE_FILLED",
    "PLACEHOLDER",
    "TBD",
    "FIXME",
    "EXAMPLE.INVALID",
)
_RFC3339_UTC = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z"
)


class MicrotrialPreflightVerdict(str, Enum):
    PASS = "PASS"
    CANNOT_CHECK = "CANNOT_CHECK"
    REJECT = "REJECT"


@dataclass(frozen=True)
class MicrotrialPreflightReport:
    verdict: MicrotrialPreflightVerdict
    blockers: tuple[str, ...]
    invalid_bindings: tuple[str, ...]
    checks: tuple[dict[str, str], ...]
    evaluated_result_record_count: int = 0


@dataclass(frozen=True)
class BackendGeneration:
    raw_text: str
    input_tokens: int
    output_tokens: int
    backend_version: str
    wall_time_ms: int
    process_high_water_rss_bytes_after_arm: int


@dataclass(frozen=True)
class ExecutionCheckoutState:
    repo_path: str
    head_sha: str
    tree_sha: str
    clean: bool
    subject_ancestor: bool


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_sha256(value: object) -> str:
    return _sha256_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    )


def _json_dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _parse_rfc3339_utc(value: object, field: str) -> datetime:
    """Parse an explicit UTC RFC3339 timestamp or fail closed."""

    if not isinstance(value, str) or _RFC3339_UTC.fullmatch(value) is None:
        raise ValueError(f"{field}_invalid_rfc3339_utc")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError(f"{field}_invalid_rfc3339_utc") from exc
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError(f"{field}_invalid_rfc3339_utc")
    return parsed


def _validate_created_at_chronology(
    packet: Mapping[str, object],
    created_at_utc: str,
    *,
    observed_at: datetime | None = None,
) -> None:
    freeze_at = _parse_rfc3339_utc(packet.get("freeze_created_at_utc"), "freeze_created_at_utc")
    created_at = _parse_rfc3339_utc(created_at_utc, "created_at_utc")
    if created_at < freeze_at:
        raise ValueError("created_at_utc_precedes_packet_freeze")
    now = datetime.now(timezone.utc) if observed_at is None else observed_at
    if created_at > now:
        raise ValueError("created_at_utc_is_future_dated")


def _resolve(path: str, base_dir: Path) -> Path:
    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else base_dir / candidate


def _placeholder_paths(value: object, path: str = "packet") -> tuple[str, ...]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            found.extend(_placeholder_paths(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_placeholder_paths(item, f"{path}[{index}]"))
    elif isinstance(value, str):
        normalized = value.upper()
        if any(marker in normalized for marker in _PLACEHOLDER_MARKERS):
            found.append(path)
    return tuple(found)


def _load_bound_artifact(
    name: str,
    bindings: Mapping[str, object],
    base_dir: Path,
    blockers: list[str],
    invalid: list[str],
    checks: list[dict[str, str]],
) -> tuple[Path | None, bytes | None]:
    binding = bindings.get(name)
    if not isinstance(binding, Mapping):
        blockers.append(f"binding_missing:{name}")
        checks.append({"id": f"binding:{name}", "state": "CANNOT_CHECK", "detail": "binding missing"})
        return None, None
    raw_path = binding.get("path")
    expected_hash = binding.get("sha256")
    if not isinstance(raw_path, str) or not raw_path.strip():
        blockers.append(f"binding_path_missing:{name}")
        return None, None
    if not isinstance(expected_hash, str) or len(expected_hash) != 64:
        blockers.append(f"binding_sha256_missing:{name}")
        return None, None
    path = _resolve(raw_path, base_dir)
    if not path.is_file():
        blockers.append(f"bound_artifact_missing:{name}:{raw_path}")
        checks.append({"id": f"binding:{name}", "state": "CANNOT_CHECK", "detail": "file absent"})
        return path, None
    payload = path.read_bytes()
    observed = _sha256_bytes(payload)
    if observed != expected_hash:
        invalid.append(f"sha256_mismatch:{name}:{raw_path}")
        checks.append({"id": f"binding:{name}", "state": "REJECT", "detail": "sha256 mismatch"})
        return path, None
    checks.append({"id": f"binding:{name}", "state": "PASS", "detail": "exact bytes bound"})
    return path, payload


def _parse_json_artifact(
    name: str,
    payloads: Mapping[str, bytes],
    invalid: list[str],
) -> object | None:
    payload = payloads.get(name)
    if payload is None:
        return None
    try:
        return json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError):
        invalid.append(f"invalid_json:{name}")
        return None


def _questions_block(questions: Mapping[str, object]) -> str:
    entries = questions.get("questions")
    if not isinstance(entries, list):
        raise ValueError("questions must be a list")
    lines = ["REGISTERED QUESTIONS"]
    for item in entries:
        if not isinstance(item, Mapping):
            raise ValueError("question entry must be an object")
        question_id = item.get("question_id")
        prompt = item.get("prompt")
        if not isinstance(question_id, str) or not question_id or not isinstance(prompt, str) or not prompt:
            raise ValueError("question id and prompt are required")
        lines.append(f"{question_id}: {prompt}")
    lines.append("OUTPUT SCHEMA")
    lines.append(json.dumps(questions.get("output_schema"), sort_keys=True, ensure_ascii=False))
    return "\n".join(lines)


def materialize_prompts(
    task: Mapping[str, object],
    questions: Mapping[str, object],
    system_prompt: str,
) -> dict[str, str]:
    """Materialize the only registered intervention while preserving the raw corpus.

    Both arms receive all verbatim sources, the same questions, schema, seed and no-tool
    policy.  The RAKL arm additionally receives the task's pre-frozen projection/context
    and relation map.  This is an engineering microtrial, not a causal superiority test.
    """

    sources = task.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("task sources are required")
    raw_lines = ["FROZEN RAW EVIDENCE CORPUS"]
    context_lines = ["RAKL CONTEXT MAP"]
    for source in sources:
        if not isinstance(source, Mapping):
            raise ValueError("source entry must be an object")
        source_id = source.get("source_id")
        text = source.get("text")
        if not isinstance(source_id, str) or not source_id or not isinstance(text, str) or not text:
            raise ValueError("source id and text are required")
        raw_lines.append(f"[{source_id}] {text}")
        context_lines.append(
            json.dumps(
                {
                    "source_id": source_id,
                    "projection": source.get("projection"),
                    "context": source.get("context"),
                },
                sort_keys=True,
                ensure_ascii=False,
            )
        )
    relations = task.get("rakl_relations")
    if not isinstance(relations, list):
        raise ValueError("RAKL relation list is required")
    for relation in relations:
        context_lines.append(json.dumps(relation, sort_keys=True, ensure_ascii=False))

    common_prefix = (
        system_prompt.rstrip()
        + "\n\nTOOLS: disabled\nRETRIEVAL: disabled\nREPOSITORY ACCESS: not exposed to the model\n"
    )
    common_suffix = "\n\n" + _questions_block(questions) + "\n"
    raw_block = "\n".join(raw_lines)
    return {
        "DIRECT_CORPUS": common_prefix + "\n" + raw_block + common_suffix,
        "RAKL_CONTEXT": common_prefix + "\n" + raw_block + "\n\n" + "\n".join(context_lines) + common_suffix,
    }


def _default_runtime_versions() -> dict[str, str]:
    versions = {"python": platform.python_version()}
    for package in ("torch", "transformers", "tokenizers", "safetensors"):
        try:
            versions[package] = metadata.version(package)
        except metadata.PackageNotFoundError:
            versions[package] = "MISSING"
    return versions


def audit_execution_packet(
    packet: Mapping[str, object],
    *,
    base_dir: Path | None = None,
    runtime_versions: Mapping[str, str] | None = None,
    observed_at_utc: str | None = None,
) -> MicrotrialPreflightReport:
    """Fail closed before model access and report zero evaluated records."""

    root = Path.cwd() if base_dir is None else base_dir
    blockers: list[str] = []
    invalid: list[str] = []
    checks: list[dict[str, str]] = []

    freeze_at: datetime | None = None
    try:
        freeze_at = _parse_rfc3339_utc(
            packet.get("freeze_created_at_utc"), "freeze_created_at_utc"
        )
    except ValueError as exc:
        invalid.append(str(exc))
    try:
        observed_at = (
            datetime.now(timezone.utc)
            if observed_at_utc is None
            else _parse_rfc3339_utc(observed_at_utc, "observed_at_utc")
        )
    except ValueError as exc:
        invalid.append(str(exc))
        observed_at = None
    if freeze_at is not None and observed_at is not None and freeze_at > observed_at:
        invalid.append("freeze_created_at_utc_is_future_dated")

    if packet.get("schema_version") != "paper2-pendulum-microtrial-execution-v1":
        invalid.append("unsupported_packet_schema")
    if packet.get("evaluated_results_opened_before_freeze") is not False:
        invalid.append("freeze_chronology_violated")
    if packet.get("status") != "FROZEN_READY_NOT_EXECUTED":
        invalid.append("packet_not_frozen_ready")
    subject_sha = packet.get("subject_sha")
    if not isinstance(subject_sha, str) or len(subject_sha) != 40 or any(c not in "0123456789abcdef" for c in subject_sha):
        invalid.append("subject_sha_invalid")
    if packet.get("arms") != list(_CONDITIONS):
        invalid.append("arm_set_or_order_invalid")
    claim_boundary = packet.get("claim_boundary")
    if not isinstance(claim_boundary, str) or "non-confirmatory" not in claim_boundary.lower():
        invalid.append("nonconfirmatory_claim_boundary_missing")
    for placeholder_path in _placeholder_paths(packet):
        invalid.append(f"placeholder_forbidden:{placeholder_path}")

    raw_bindings = packet.get("bindings")
    bindings = raw_bindings if isinstance(raw_bindings, Mapping) else {}
    if not isinstance(raw_bindings, Mapping):
        blockers.append("bindings_missing")

    payloads: dict[str, bytes] = {}
    paths: dict[str, Path] = {}
    for name in _REQUIRED_BINDINGS:
        path, payload = _load_bound_artifact(name, bindings, root, blockers, invalid, checks)
        if path is not None:
            paths[name] = path
        if payload is not None:
            payloads[name] = payload

    json_names = (
        "task",
        "questions",
        "evaluator",
        "model_manifest",
        "tokenizer_manifest",
        "execution_contract",
        "environment",
        "resources",
        "prices",
        "blinding",
        "result_schema",
    )
    parsed = {name: _parse_json_artifact(name, payloads, invalid) for name in json_names}
    for artifact_name, artifact_value in parsed.items():
        if artifact_value is None:
            continue
        for placeholder_path in _placeholder_paths(artifact_value, f"artifact.{artifact_name}"):
            invalid.append(f"placeholder_forbidden:{placeholder_path}")

    task = parsed.get("task")
    if isinstance(task, Mapping):
        sealed_at: datetime | None = None
        try:
            sealed_at = _parse_rfc3339_utc(task.get("sealed_at_utc"), "task_sealed_at_utc")
        except ValueError as exc:
            invalid.append(str(exc))
        if sealed_at is not None and freeze_at is not None and sealed_at > freeze_at:
            invalid.append("task_sealed_at_utc_after_packet_freeze")
        sources = task.get("sources")
        mandatory = task.get("mandatory_evidence_ids")
        if task.get("sealed_before_model_execution") is not True:
            invalid.append("task_not_sealed_before_execution")
        if not isinstance(sources, list) or not sources:
            invalid.append("task_sources_missing")
            source_ids: set[str] = set()
        else:
            source_ids = {
                str(source.get("source_id"))
                for source in sources
                if isinstance(source, Mapping) and isinstance(source.get("source_id"), str)
            }
            if len(source_ids) != len(sources):
                invalid.append("source_ids_missing_or_duplicate")
            for source in sources:
                if not isinstance(source, Mapping) or not isinstance(source.get("text"), str) or not source["text"].strip():
                    invalid.append("source_text_missing")
        if not isinstance(mandatory, list) or not mandatory:
            invalid.append("mandatory_evidence_set_missing")
        else:
            for source_id in mandatory:
                if source_id not in source_ids:
                    invalid.append(f"mandatory_evidence_missing:{source_id}")
            if set(mandatory) != source_ids:
                invalid.append("mandatory_evidence_does_not_cover_exact_corpus")
    else:
        source_ids = set()

    questions = parsed.get("questions")
    if isinstance(questions, Mapping):
        question_entries = questions.get("questions")
        if not isinstance(question_entries, list) or not question_entries:
            invalid.append("question_set_empty")
        if not isinstance(questions.get("output_schema"), Mapping):
            invalid.append("output_schema_missing")

    evaluator = parsed.get("evaluator")
    if isinstance(evaluator, Mapping):
        if evaluator.get("arm_identity_blinded") is not True:
            invalid.append("evaluator_not_arm_blinded")
        for field in (
            "required_support_source_ids",
            "allowed_support_source_ids",
            "misaligned_source_ids",
            "required_refuted_source_ids",
        ):
            ids = evaluator.get(field)
            if not isinstance(ids, list):
                invalid.append(f"evaluator_source_set_missing:{field}")
                continue
            for source_id in ids:
                if source_id not in source_ids:
                    invalid.append(f"evaluator_source_absent:{field}:{source_id}")
        implementation_path = evaluator.get("implementation_source_path")
        implementation_hash = evaluator.get("implementation_source_sha256")
        if not isinstance(implementation_path, str) or not implementation_path:
            invalid.append("evaluator_implementation_source_path_missing")
        elif not isinstance(implementation_hash, str) or len(implementation_hash) != 64:
            invalid.append("evaluator_implementation_sha256_missing")
        else:
            implementation_source = _resolve(implementation_path, root)
            if not implementation_source.is_file():
                blockers.append("evaluator_implementation_source_missing")
            elif _sha256_bytes(implementation_source.read_bytes()) != implementation_hash:
                invalid.append("evaluator_implementation_sha256_mismatch")

    if isinstance(task, Mapping) and isinstance(questions, Mapping) and "system_prompt" in payloads:
        try:
            observed_prompts = materialize_prompts(
                task,
                questions,
                payloads["system_prompt"].decode("utf-8"),
            )
        except (UnicodeDecodeError, ValueError) as exc:
            invalid.append(f"prompt_materialization_invalid:{type(exc).__name__}")
        else:
            for condition, binding_name in (
                ("DIRECT_CORPUS", "direct_prompt"),
                ("RAKL_CONTEXT", "rakl_prompt"),
            ):
                expected_payload = observed_prompts[condition].encode("utf-8")
                if payloads.get(binding_name) != expected_payload:
                    invalid.append(f"materialized_prompt_semantic_mismatch:{condition}")

    resources = parsed.get("resources")
    if isinstance(resources, Mapping):
        if resources.get("seed") != 17:
            invalid.append("seed_must_equal_17")
        if resources.get("max_tool_calls") != 0 or resources.get("max_retrieval_calls") != 0:
            invalid.append("model_tool_and_retrieval_ceiling_must_be_zero")
        for field in (
            "max_input_tokens",
            "max_output_tokens",
            "max_wall_time_ms_per_arm",
            "max_process_high_water_rss_bytes",
        ):
            if not isinstance(resources.get(field), int) or int(resources[field]) <= 0:
                invalid.append(f"resource_ceiling_invalid:{field}")

    blinding = parsed.get("blinding")
    if isinstance(blinding, Mapping):
        mapping = blinding.get("mapping")
        if not isinstance(mapping, Mapping) or set(mapping.values()) != set(_CONDITIONS):
            invalid.append("blinding_map_invalid")
        elif any(condition in blind_id.upper() or len(blind_id) < 8 for blind_id, condition in mapping.items()):
            invalid.append("blinded_label_not_opaque")

    model_manifest = parsed.get("model_manifest")
    tokenizer_manifest = parsed.get("tokenizer_manifest")
    execution_contract = parsed.get("execution_contract")
    if isinstance(model_manifest, Mapping) and isinstance(tokenizer_manifest, Mapping):
        if model_manifest.get("provider") != "local_transformers":
            invalid.append("provider_must_be_local_transformers")
        if model_manifest.get("trust_remote_code") is not False:
            invalid.append("trust_remote_code_must_be_false")
        if model_manifest.get("local_files_only") is not True:
            invalid.append("local_files_only_must_be_true")
        revision = model_manifest.get("revision")
        if (
            not isinstance(revision, str)
            or len(revision) != 40
            or any(c not in "0123456789abcdef" for c in revision)
            or tokenizer_manifest.get("revision") != revision
            or tokenizer_manifest.get("model_id") != model_manifest.get("model_id")
        ):
            invalid.append("immutable_model_tokenizer_revision_mismatch")
        snapshot_path = model_manifest.get("snapshot_path")
        if not isinstance(snapshot_path, str) or not snapshot_path:
            blockers.append("local_model_snapshot_path_missing")
        else:
            snapshot = _resolve(snapshot_path, root)
            for owner, manifest in (("model", model_manifest), ("tokenizer", tokenizer_manifest)):
                files = manifest.get("files")
                if not isinstance(files, list) or not files:
                    invalid.append(f"{owner}_file_manifest_missing")
                    continue
                for entry in files:
                    if not isinstance(entry, Mapping):
                        invalid.append(f"{owner}_file_entry_invalid")
                        continue
                    relative = entry.get("path")
                    expected_hash = entry.get("sha256")
                    expected_bytes = entry.get("bytes")
                    if (
                        not isinstance(relative, str)
                        or not relative
                        or not isinstance(expected_hash, str)
                        or len(expected_hash) != 64
                        or not isinstance(expected_bytes, int)
                        or expected_bytes < 1
                    ):
                        invalid.append(f"{owner}_file_identity_invalid:{relative}")
                        continue
                    candidate = snapshot / relative
                    if not candidate.is_file():
                        blockers.append(f"local_{owner}_file_missing:{relative}")
                        continue
                    if candidate.stat().st_size != expected_bytes:
                        invalid.append(f"local_{owner}_file_size_mismatch:{relative}")
                        continue
                    if _sha256_bytes(candidate.read_bytes()) != expected_hash:
                        invalid.append(f"local_{owner}_file_sha256_mismatch:{relative}")

    if isinstance(execution_contract, Mapping):
        if execution_contract.get("schema_version") != "paper2-lunarc-execution-contract-v1":
            invalid.append("execution_contract_schema_invalid")
        for field in (
            "execution_site",
            "forbidden_login_host_prefix",
            "fs9_root",
            "repo_path",
            "output_root",
            "model_snapshot_path",
        ):
            if not isinstance(execution_contract.get(field), str) or not str(execution_contract[field]).strip():
                invalid.append(f"execution_contract_field_missing:{field}")
        for field in (
            "require_clean_checkout",
            "require_subject_ancestor",
            "require_exact_bound_artifacts",
            "require_slurm_job_id",
        ):
            if execution_contract.get(field) is not True:
                invalid.append(f"execution_contract_gate_not_enabled:{field}")
        if isinstance(model_manifest, Mapping) and (
            execution_contract.get("model_snapshot_path") != model_manifest.get("snapshot_path")
        ):
            invalid.append("execution_contract_model_snapshot_mismatch")
        fs9_root = execution_contract.get("fs9_root")
        repo_path = execution_contract.get("repo_path")
        output_root = execution_contract.get("output_root")
        model_snapshot = execution_contract.get("model_snapshot_path")
        if all(
            isinstance(item, str) and item
            for item in (fs9_root, repo_path, output_root, model_snapshot)
        ):
            fs9 = Path(str(fs9_root))
            repo = Path(str(repo_path))
            output = Path(str(output_root))
            snapshot = Path(str(model_snapshot))
            for field, path in (
                ("fs9_root", fs9),
                ("repo_path", repo),
                ("output_root", output),
                ("model_snapshot_path", snapshot),
            ):
                if ".." in path.parts:
                    invalid.append(f"execution_contract_path_contains_dotdot:{field}")
            if not all(path.is_absolute() for path in (fs9, repo, output, snapshot)):
                invalid.append("execution_contract_paths_must_be_absolute")
            else:
                try:
                    repo.relative_to(fs9)
                    output.relative_to(fs9)
                    snapshot.relative_to(fs9)
                except ValueError:
                    invalid.append("execution_contract_assets_outside_fs9_root")

    environment = parsed.get("environment")
    observed_versions = dict(_default_runtime_versions() if runtime_versions is None else runtime_versions)
    if isinstance(environment, Mapping):
        required_versions = {"python": environment.get("python")}
        packages = environment.get("packages")
        if isinstance(packages, Mapping):
            required_versions.update({str(name): str(version) for name, version in packages.items()})
        else:
            invalid.append("environment_packages_missing")
        for name, required in required_versions.items():
            if not isinstance(required, str) or not required:
                invalid.append(f"environment_version_invalid:{name}")
            elif observed_versions.get(name) != required:
                blockers.append(
                    f"runtime_version_mismatch:{name}:{observed_versions.get(name, 'MISSING')}!={required}"
                )
        platform_contract = environment.get("platform")
        if not isinstance(platform_contract, Mapping):
            invalid.append("environment_platform_contract_missing")
        else:
            if platform_contract.get("execution_device") != "CPU":
                invalid.append("execution_device_must_remain_frozen_cpu")
            if platform_contract.get("network_state_observed") is not False:
                invalid.append("network_state_must_remain_unobserved")
            if (
                platform_contract.get("transformers_network_policy")
                != "offline_environment_and_local_files_only"
            ):
                invalid.append("transformers_offline_policy_missing")
            observed_platform = {
                "os": platform.system(),
                "architecture": platform.machine(),
                "execution_device": "CPU",
            }
            for name, observed in observed_platform.items():
                required = platform_contract.get(name)
                if required != observed:
                    blockers.append(f"runtime_platform_mismatch:{name}:{observed}!={required}")

    prices = parsed.get("prices")
    if isinstance(prices, Mapping):
        if not prices.get("price_sheet_id"):
            invalid.append("price_sheet_id_missing")
        if not isinstance(prices.get("unpriced_coordinates"), list):
            invalid.append("unpriced_cost_coordinates_missing")

    verdict = (
        MicrotrialPreflightVerdict.REJECT
        if invalid
        else MicrotrialPreflightVerdict.CANNOT_CHECK
        if blockers
        else MicrotrialPreflightVerdict.PASS
    )
    return MicrotrialPreflightReport(
        verdict=verdict,
        blockers=tuple(dict.fromkeys(blockers)),
        invalid_bindings=tuple(dict.fromkeys(invalid)),
        checks=tuple(checks),
    )


def write_preflight_receipt(
    report: MicrotrialPreflightReport,
    *,
    packet: Mapping[str, object],
    output_path: Path,
    created_at_utc: str,
) -> None:
    _validate_created_at_chronology(packet, created_at_utc)
    receipt = {
        "schema_version": "paper2-pendulum-microtrial-preflight-receipt-v1",
        "receipt_type": "paper2_microtrial_execution_preflight_not_result",
        "created_at_utc": created_at_utc,
        "protocol_id": packet.get("protocol_id"),
        "subject_sha": packet.get("subject_sha"),
        "packet_canonical_sha256": _canonical_sha256(packet),
        "verdict": report.verdict.value,
        "blockers": list(report.blockers),
        "invalid_bindings": list(report.invalid_bindings),
        "checks": list(report.checks),
        "evaluated_result_record_count": 0,
        "empirical_claim_permitted": False,
        "claim_boundary": (
            "Execution readiness only. This is not a model-performance result and cannot support "
            "a comparative or general RAKL superiority claim."
        ),
    }
    _json_dump(output_path, receipt)


def _parse_answer(raw_text: str) -> PendulumStructuredAnswer:
    try:
        value = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError("model output is not a JSON object") from exc
    if not isinstance(value, Mapping) or set(value) != set(_ANSWER_FIELDS):
        raise ValueError("model output fields do not match the registered answer schema")
    for field in _ANSWER_FIELDS[:5]:
        if not isinstance(value[field], bool):
            raise ValueError(f"answer field must be boolean:{field}")
    for field in _ANSWER_FIELDS[5:]:
        if not isinstance(value[field], list) or any(not isinstance(item, str) for item in value[field]):
            raise ValueError(f"answer field must be a string list:{field}")
    return PendulumStructuredAnswer(
        small_angle_is_asymptotic=value["small_angle_is_asymptotic"],
        finite_amplitude_increases_period=value["finite_amplitude_increases_period"],
        context_distinct_claims_not_direct_contradictions=value[
            "context_distinct_claims_not_direct_contradictions"
        ],
        ideal_period_is_mass_invariant=value["ideal_period_is_mass_invariant"],
        context_alignment_required_before_contradiction=value[
            "context_alignment_required_before_contradiction"
        ],
        supporting_source_ids=tuple(value["supporting_source_ids"]),
        rejected_as_misaligned_source_ids=tuple(value["rejected_as_misaligned_source_ids"]),
        refuted_source_ids=tuple(value["refuted_source_ids"]),
    )


def _score_blinded_outputs(raw_outputs: Mapping[str, str]) -> list[dict[str, object]]:
    """Score records whose only identity is an opaque blind id.

    The prompt-dispatch map is intentionally not an argument.  This is narrow
    deterministic scorer-input blinding, not human or process-level blinding.
    """

    scores: list[dict[str, object]] = []
    for blind_id in sorted(raw_outputs):
        try:
            answer = _parse_answer(raw_outputs[blind_id])
        except ValueError as exc:
            score_record = {
                "blind_id": blind_id,
                "parse_valid": False,
                "parse_error": str(exc),
                "score": None,
            }
        else:
            score_record = {
                "blind_id": blind_id,
                "parse_valid": True,
                "parse_error": None,
                "score": asdict(score_pendulum_answer(answer)),
            }
        scores.append(score_record)
    return scores


def verify_result_receipt(
    result: Mapping[str, object],
    *,
    packet: Mapping[str, object],
    expected_blinding: Mapping[str, str],
    expected_prompt_sha256: Mapping[str, str],
    run_manifest_sha256: str,
) -> None:
    """Fail closed on cross-record identities that JSON Schema cannot express."""

    problems: list[str] = []
    if result.get("experiment_id") != packet.get("protocol_id"):
        problems.append("result_protocol_mismatch")
    if result.get("subject_sha") != packet.get("subject_sha"):
        problems.append("result_subject_mismatch")
    if result.get("run_manifest_sha256") != run_manifest_sha256:
        problems.append("result_run_manifest_mismatch")
    records = result.get("records")
    if not isinstance(records, list) or len(records) != len(_CONDITIONS):
        problems.append("result_record_count_invalid")
        records = []
    observed_blind_ids: list[str] = []
    observed_conditions: list[str] = []
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            problems.append(f"result_record_invalid:{index}")
            continue
        blind_id = record.get("blind_id")
        condition = record.get("condition")
        if not isinstance(blind_id, str) or blind_id not in expected_blinding:
            problems.append(f"result_blind_id_invalid:{index}")
            continue
        observed_blind_ids.append(blind_id)
        observed_conditions.append(str(condition))
        if condition != expected_blinding[blind_id]:
            problems.append(f"result_condition_mapping_mismatch:{blind_id}")
        raw_output = record.get("raw_output")
        provider = record.get("provider_receipt")
        resources = record.get("resource_receipt")
        score = record.get("score")
        for owner, value in (
            ("raw_output", raw_output),
            ("provider_receipt", provider),
            ("resource_receipt", resources),
            ("score", score),
        ):
            if not isinstance(value, Mapping):
                problems.append(f"result_{owner}_invalid:{blind_id}")
        if not all(isinstance(value, Mapping) for value in (raw_output, provider, resources, score)):
            continue
        if raw_output.get("blind_id") != blind_id or score.get("blind_id") != blind_id:
            problems.append(f"nested_blind_id_mismatch:{blind_id}")
        expected_prompt = expected_prompt_sha256.get(str(condition))
        if raw_output.get("prompt_sha256") != expected_prompt:
            problems.append(f"prompt_identity_mismatch:{blind_id}")
        for owner, value in (
            ("raw_output", raw_output),
            ("provider_receipt", provider),
            ("resource_receipt", resources),
        ):
            if value.get("run_manifest_sha256") != run_manifest_sha256:
                problems.append(f"nested_run_manifest_mismatch:{owner}:{blind_id}")
        parse_valid = score.get("parse_valid")
        parsed_score = score.get("score")
        parse_error = score.get("parse_error")
        if parse_valid is True:
            if parse_error is not None or not isinstance(parsed_score, Mapping):
                problems.append(f"valid_parse_score_state_invalid:{blind_id}")
            elif set(parsed_score) != set(_SCORE_FIELDS):
                problems.append(f"known_answer_score_fields_invalid:{blind_id}")
        elif parse_valid is False:
            if not isinstance(parse_error, str) or not parse_error or parsed_score is not None:
                problems.append(f"invalid_parse_score_state_invalid:{blind_id}")
        else:
            problems.append(f"parse_valid_not_boolean:{blind_id}")
    if len(set(observed_blind_ids)) != len(_CONDITIONS):
        problems.append("result_blind_ids_not_unique_or_complete")
    if set(observed_conditions) != set(_CONDITIONS):
        problems.append("result_conditions_not_unique_or_complete")
    if problems:
        raise RuntimeError("result receipt verification failed:" + ",".join(problems))


def _encode_prompt_for_generation(tokenizer: object, prompt: str) -> object:
    return tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}],
        add_generation_prompt=True,
        tokenize=True,
        return_tensors="pt",
        return_dict=True,
    )


def _git_checkout_state(repo_path: Path, subject_sha: str) -> ExecutionCheckoutState:
    head_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
        shell=False,
    ).stdout.strip()
    tree_sha = subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
        shell=False,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
        shell=False,
    ).stdout
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", subject_sha, head_sha],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=False,
        shell=False,
    ).returncode == 0
    return ExecutionCheckoutState(
        repo_path=str(repo_path.resolve()),
        head_sha=head_sha,
        tree_sha=tree_sha,
        clean=not status.strip(),
        subject_ancestor=ancestor,
    )


def _local_transformers_backend(
    prompt: str,
    *,
    snapshot_path: Path,
    seed: int,
    max_output_tokens: int,
) -> BackendGeneration:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    started = time.perf_counter()
    before_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.manual_seed(seed)
    tokenizer = AutoTokenizer.from_pretrained(
        snapshot_path,
        local_files_only=True,
        trust_remote_code=False,
    )
    model = AutoModelForCausalLM.from_pretrained(
        snapshot_path,
        local_files_only=True,
        trust_remote_code=False,
        torch_dtype=torch.float32,
    )
    model.eval()
    encoded = _encode_prompt_for_generation(tokenizer, prompt)
    with torch.inference_mode():
        generated = model.generate(
            **encoded,
            do_sample=False,
            max_new_tokens=max_output_tokens,
            pad_token_id=tokenizer.eos_token_id,
        )
    new_tokens = generated[0, encoded["input_ids"].shape[1] :]
    raw_text = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
    after_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss_multiplier = 1 if sys.platform == "darwin" else 1024
    return BackendGeneration(
        raw_text=raw_text,
        input_tokens=int(encoded["input_ids"].numel()),
        output_tokens=int(new_tokens.numel()),
        backend_version=f"transformers-{transformers.__version__}/torch-{torch.__version__}",
        wall_time_ms=round((time.perf_counter() - started) * 1000),
        process_high_water_rss_bytes_after_arm=int(max(before_rss, after_rss) * rss_multiplier),
    )


def execute_microtrial(
    packet_path: Path,
    output_dir: Path,
    *,
    created_at_utc: str,
    backend: Callable[..., BackendGeneration] | None = None,
    runtime_versions: Mapping[str, str] | None = None,
    checkout_probe: Callable[[Path, str], ExecutionCheckoutState] | None = None,
    execution_host: str | None = None,
    scheduler_job_id: str | None = None,
) -> None:
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    _validate_created_at_chronology(packet, created_at_utc)
    repository_root = Path.cwd()
    report = audit_execution_packet(packet, base_dir=repository_root, runtime_versions=runtime_versions)
    if report.verdict is not MicrotrialPreflightVerdict.PASS:
        raise RuntimeError(
            f"microtrial preflight did not pass:{report.verdict.value}:"
            f"{list(report.blockers)}:{list(report.invalid_bindings)}"
        )

    bindings = packet["bindings"]

    def load_json(name: str) -> dict[str, object]:
        path = _resolve(bindings[name]["path"], repository_root)
        return json.loads(path.read_text(encoding="utf-8"))

    prompts = {
        "DIRECT_CORPUS": _resolve(bindings["direct_prompt"]["path"], repository_root).read_text(
            encoding="utf-8"
        ),
        "RAKL_CONTEXT": _resolve(bindings["rakl_prompt"]["path"], repository_root).read_text(
            encoding="utf-8"
        ),
    }
    blinding = load_json("blinding")["mapping"]
    resources = load_json("resources")
    prices = load_json("prices")
    model_manifest = load_json("model_manifest")
    execution_contract = load_json("execution_contract")
    generator = _local_transformers_backend if backend is None else backend
    host = socket.gethostname() if execution_host is None else execution_host
    if host.startswith(str(execution_contract["forbidden_login_host_prefix"])):
        raise RuntimeError("execution is forbidden on the LUNARC login host")
    job_id = os.environ.get("SLURM_JOB_ID") if scheduler_job_id is None else scheduler_job_id
    if not isinstance(job_id, str) or not job_id.isdigit():
        raise RuntimeError("a numeric SLURM job id is required for execution")
    registered_repo = Path(str(execution_contract["repo_path"]))
    if repository_root.resolve() != registered_repo.resolve():
        raise RuntimeError("runner checkout path does not match frozen execution contract")
    bound_runner = _resolve(str(bindings["runner"]["path"]), repository_root)
    if Path(__file__).resolve() != bound_runner.resolve():
        raise RuntimeError("runner module is not loaded from the bound execution checkout")
    state_probe = _git_checkout_state if checkout_probe is None else checkout_probe
    checkout_state = state_probe(registered_repo, str(packet["subject_sha"]))
    if Path(checkout_state.repo_path).resolve() != registered_repo.resolve():
        raise RuntimeError("execution checkout path does not match frozen contract")
    if not checkout_state.clean:
        raise RuntimeError("execution checkout is not clean")
    if not checkout_state.subject_ancestor:
        raise RuntimeError("frozen packet subject is not an ancestor of execution checkout")
    for label, value in (("head", checkout_state.head_sha), ("tree", checkout_state.tree_sha)):
        if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
            raise RuntimeError(f"execution checkout {label} identity is invalid")
    output_root = Path(str(execution_contract["output_root"]))
    resolved_output = output_dir.resolve()
    if resolved_output.parent != output_root.resolve():
        raise RuntimeError("output directory must be exactly one new child of frozen FS9 output root")
    if output_dir.exists():
        raise RuntimeError("output directory already exists")
    output_dir.mkdir(parents=True, exist_ok=False)

    execution_checkout = asdict(checkout_state)
    run_manifest = {
        "schema_version": "paper2-pendulum-microtrial-run-manifest-v1",
        "created_at_utc": created_at_utc,
        "protocol_id": packet["protocol_id"],
        "subject_sha": packet["subject_sha"],
        "packet_file_sha256": _sha256_bytes(packet_path.read_bytes()),
        "packet_canonical_sha256": _canonical_sha256(packet),
        "bound_artifact_sha256": {
            name: binding["sha256"] for name, binding in sorted(bindings.items())
        },
        "execution_contract_sha256": bindings["execution_contract"]["sha256"],
        "execution_host": host,
        "scheduler_job_id": job_id,
        "execution_checkout": execution_checkout,
        "model_snapshot_path": model_manifest["snapshot_path"],
        "output_dir": str(resolved_output),
        "model_outputs_opened_before_manifest": False,
        "claim_boundary": "non-confirmatory engineering microtrial only",
    }
    run_manifest_path = output_dir / "run_manifest.json"
    _json_dump(run_manifest_path, run_manifest)
    run_manifest_sha256 = _sha256_bytes(run_manifest_path.read_bytes())

    intermediate: dict[str, dict[str, object]] = {}
    for blind_id in sorted(blinding):
        condition = blinding[blind_id]
        prompt = prompts[condition]
        generation = generator(
            prompt,
            snapshot_path=_resolve(model_manifest["snapshot_path"], repository_root),
            seed=resources["seed"],
            max_output_tokens=resources["max_output_tokens"],
        )
        if generation.input_tokens > resources["max_input_tokens"]:
            raise RuntimeError(f"input token ceiling exceeded:{blind_id}")
        if generation.output_tokens > resources["max_output_tokens"]:
            raise RuntimeError(f"output token ceiling exceeded:{blind_id}")
        if generation.wall_time_ms > resources["max_wall_time_ms_per_arm"]:
            raise RuntimeError(f"wall time ceiling exceeded:{blind_id}")
        if (
            generation.process_high_water_rss_bytes_after_arm
            > resources["max_process_high_water_rss_bytes"]
        ):
            raise RuntimeError(f"process high-water RSS ceiling exceeded:{blind_id}")

        raw_record = {
            "blind_id": blind_id,
            "prompt_sha256": _sha256_bytes(prompt.encode("utf-8")),
            "run_manifest_sha256": run_manifest_sha256,
            "raw_text": generation.raw_text,
        }
        provider_receipt = {
            "provider": "local_transformers",
            "model_id": model_manifest["model_id"],
            "model_revision": model_manifest["revision"],
            "model_manifest_sha256": bindings["model_manifest"]["sha256"],
            "tokenizer_manifest_sha256": bindings["tokenizer_manifest"]["sha256"],
            "backend_version": generation.backend_version,
            "local_files_only": True,
            "trust_remote_code": False,
            "tools_enabled": False,
            "repo_access_exposed_to_model": False,
            "provider_api_transaction": False,
            "run_manifest_sha256": run_manifest_sha256,
        }
        resource_receipt = {
            "seed": resources["seed"],
            "input_tokens": generation.input_tokens,
            "output_tokens": generation.output_tokens,
            "tool_calls": 0,
            "retrieval_calls": 0,
            "wall_time_ms": generation.wall_time_ms,
            "process_high_water_rss_bytes_after_arm": (
                generation.process_high_water_rss_bytes_after_arm
            ),
            "provider_api_cost_usd": 0,
            "price_sheet_sha256": bindings["prices"]["sha256"],
            "unpriced_coordinates": prices["unpriced_coordinates"],
            "run_manifest_sha256": run_manifest_sha256,
        }
        _json_dump(output_dir / "raw_outputs" / f"{blind_id}.json", raw_record)
        _json_dump(output_dir / "provider_receipts" / f"{blind_id}.json", provider_receipt)
        _json_dump(output_dir / "resource_receipts" / f"{blind_id}.json", resource_receipt)

        intermediate[blind_id] = {
            "raw_output": raw_record,
            "provider_receipt": provider_receipt,
            "resource_receipt": resource_receipt,
        }

    blinded_scores = _score_blinded_outputs(
        {blind_id: str(row["raw_output"]["raw_text"]) for blind_id, row in intermediate.items()}
    )
    for score_record in blinded_scores:
        intermediate[str(score_record["blind_id"])]["score"] = score_record

    blinded_receipt = {
        "schema_version": "paper2-pendulum-blinded-score-v1",
        "protocol_id": packet["protocol_id"],
        "evaluator_sha256": bindings["evaluator"]["sha256"],
        "run_manifest_sha256": run_manifest_sha256,
        "scores": blinded_scores,
        "condition_labels_present_in_scoring_records": False,
        "condition_labels_passed_to_scoring_function": False,
        "orchestrator_loaded_blinding_map_for_prompt_dispatch_before_scoring": True,
        "human_or_process_level_blinding_claimed": False,
    }
    _json_dump(output_dir / "blinded_scores.json", blinded_receipt)

    records = []
    for blind_id in sorted(blinding):
        row = intermediate[blind_id]
        records.append(
            {
                "blind_id": blind_id,
                "condition": blinding[blind_id],
                "raw_output": row["raw_output"],
                "provider_receipt": row["provider_receipt"],
                "resource_receipt": row["resource_receipt"],
                "score": row["score"],
            }
        )
    result = {
        "schema_version": "paper2-pendulum-microtrial-result-v1",
        "experiment_id": packet["protocol_id"],
        "subject_sha": packet["subject_sha"],
        "created_at_utc": created_at_utc,
        "packet_sha256": _sha256_bytes(packet_path.read_bytes()),
        "run_manifest_sha256": run_manifest_sha256,
        "execution_checkout": execution_checkout,
        "seed": resources["seed"],
        "records": records,
        "claim_boundary": {
            "confirmatory": False,
            "general_superiority_permitted": False,
            "allowed": "non-confirmatory engineering microtrial only",
        },
    }
    verify_result_receipt(
        result,
        packet=packet,
        expected_blinding=blinding,
        expected_prompt_sha256={
            condition: _sha256_bytes(prompt.encode("utf-8"))
            for condition, prompt in prompts.items()
        },
        run_manifest_sha256=run_manifest_sha256,
    )
    _json_dump(output_dir / "result_receipt.json", result)


def _main_preflight(args: argparse.Namespace) -> int:
    packet = json.loads(args.packet.read_text(encoding="utf-8"))
    report = audit_execution_packet(packet, base_dir=Path.cwd())
    write_preflight_receipt(
        report,
        packet=packet,
        output_path=args.output,
        created_at_utc=args.created_at_utc,
    )
    print(json.dumps({"verdict": report.verdict.value, "blockers": list(report.blockers)}))
    return 0 if report.verdict is MicrotrialPreflightVerdict.PASS else 2


def _main_run(args: argparse.Namespace) -> int:
    execute_microtrial(
        args.packet,
        args.output_dir,
        created_at_utc=args.created_at_utc,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preflight or execute the sealed Paper 2 pendulum microtrial")
    subparsers = parser.add_subparsers(dest="command", required=True)
    preflight = subparsers.add_parser("preflight")
    preflight.add_argument("packet", type=Path)
    preflight.add_argument("--output", type=Path, required=True)
    preflight.add_argument("--created-at-utc", required=True)
    preflight.set_defaults(handler=_main_preflight)
    run = subparsers.add_parser("run")
    run.add_argument("packet", type=Path)
    run.add_argument("--output-dir", type=Path, required=True)
    run.add_argument("--created-at-utc", required=True)
    run.set_defaults(handler=_main_run)
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
