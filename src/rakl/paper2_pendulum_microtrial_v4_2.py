from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Callable, Mapping

from . import paper2_pendulum_microtrial as v4
from . import paper2_pendulum_microtrial_v4_1 as v4_1


OUTPUT_NORMALIZATION_POLICY_ID = v4_1.OUTPUT_NORMALIZATION_POLICY_ID
PROMPT_INTERFACE_POLICY_ID = "PENDULUM_FIELD_POLARITY_AND_STOP_AFTER_JSON_V4_2"
_SHA40 = re.compile(r"[0-9a-f]{40}")
_FIELD_POLARITY_MARKERS = (
    "FIELD POLARITY",
    "small_angle_is_asymptotic: true iff",
    "finite_amplitude_increases_period: true iff",
    "context_distinct_claims_not_direct_contradictions: true iff",
    "ideal_period_is_mass_invariant: true iff",
    "context_alignment_required_before_contradiction: true iff",
    "OUTPUT DISCIPLINE",
    "stop immediately after the closing fence",
)
_GOLD_LEAK_MARKERS = (
    '"small_angle_is_asymptotic": true',
    '"finite_amplitude_increases_period": true',
    '"context_distinct_claims_not_direct_contradictions": true',
    '"ideal_period_is_mass_invariant": true',
    '"context_alignment_required_before_contradiction": true',
)
_V4_2_BINDINGS = (
    "execution_contract",
    "output_normalization_contract",
    "output_normalizer",
    "prompt_interface_contract",
    "direct_prompt",
    "rakl_prompt",
    "v4_1_native_ingest_parent",
    "research_memory_review",
)


def normalize_pendulum_output_v4_2(raw_text: str) -> str:
    """Reuse the frozen V4.1 exact normalizer without widening serialization."""

    return v4_1.normalize_pendulum_output_v4_1(raw_text)


def _score_blinded_outputs(
    raw_outputs: Mapping[str, str],
    *,
    output_normalization_policy_id: str | None = None,
) -> list[dict[str, object]]:
    return v4_1._score_blinded_outputs(
        raw_outputs,
        output_normalization_policy_id=output_normalization_policy_id,
    )


def _require_field_polarity_prompt(text: str, *, label: str) -> None:
    for marker in _FIELD_POLARITY_MARKERS:
        if marker not in text:
            raise RuntimeError(f"V4.2 prompt missing field-polarity marker:{label}:{marker}")
    # Reject an accidental gold JSON block while allowing polarity prose that
    # mentions individual field names.
    compact = re.sub(r"\s+", "", text)
    gold_compact = "".join(
        (
            '"small_angle_is_asymptotic":true',
            '"finite_amplitude_increases_period":true',
            '"context_distinct_claims_not_direct_contradictions":true',
            '"ideal_period_is_mass_invariant":true',
            '"context_alignment_required_before_contradiction":true',
        )
    )
    if gold_compact in compact:
        raise RuntimeError(f"V4.2 prompt appears to leak sealed gold answers:{label}")
    # Individual true-valued answer literals as JSON keys are still forbidden.
    for marker in _GOLD_LEAK_MARKERS:
        if marker in text:
            raise RuntimeError(f"V4.2 prompt contains forbidden gold literal:{label}:{marker}")


def validate_v4_2_candidate_packet(packet: Mapping[str, object], *, base_dir: Path) -> None:
    """Fail closed on the adaptive V4.2 prompt-interface successor."""

    if packet.get("chronology_class") != "ADAPTIVE_PROMPT_INTERFACE_REPLAY_FRESH_ONLY_TO_V4_2_OUTPUTS":
        raise RuntimeError("V4.2 adaptive chronology class missing")
    if (
        packet.get("adaptive_replay_status")
        != "FROZEN_ADAPTIVE_CANDIDATE_REQUIRES_POST_MERGE_BATCH_HEAD_BINDING"
    ):
        raise RuntimeError("V4.2 adaptive replay status mismatch")
    if packet.get("parent_v4_1_results_opened_before_v4_2_freeze") is not True:
        raise RuntimeError("V4.2 parent-result access disclosure missing")
    if packet.get("v4_2_outputs_opened_before_freeze") is not False:
        raise RuntimeError("V4.2 output chronology violated")
    if packet.get("evaluated_results_opened_before_freeze") is not False:
        raise RuntimeError("V4.2 legacy result-access gate violated")
    if (
        packet.get("evaluated_results_opened_before_freeze_scope")
        != "V4_2_OUTPUTS_ONLY_PARENT_V4_1_KNOWN"
    ):
        raise RuntimeError("V4.2 result-access scope missing")
    if packet.get("output_normalization_policy_id") != OUTPUT_NORMALIZATION_POLICY_ID:
        raise RuntimeError("V4.2 must reuse frozen V4.1 output-normalization policy")
    if packet.get("prompt_interface_policy_id") != PROMPT_INTERFACE_POLICY_ID:
        raise RuntimeError("V4.2 prompt-interface policy mismatch")
    if packet.get("threshold_or_score_change_permitted") is not False:
        raise RuntimeError("V4.2 must not change the sealed conceptual gate")

    bindings = packet.get("bindings")
    if not isinstance(bindings, Mapping):
        raise RuntimeError("V4.2 bindings missing")
    root = base_dir.resolve()
    for name in _V4_2_BINDINGS:
        binding = bindings.get(name)
        if not isinstance(binding, Mapping):
            raise RuntimeError(f"V4.2 binding missing:{name}")
        raw_path = binding.get("path")
        expected_sha = binding.get("sha256")
        if not isinstance(raw_path, str) or not isinstance(expected_sha, str):
            raise RuntimeError(f"V4.2 binding malformed:{name}")
        path = (base_dir / raw_path).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise RuntimeError(f"V4.2 bound artifact missing or outside repository:{name}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha:
            raise RuntimeError(f"V4.2 binding mismatch:{name}")

    for prompt_name in ("direct_prompt", "rakl_prompt"):
        prompt_path = base_dir / str(bindings[prompt_name]["path"])
        _require_field_polarity_prompt(prompt_path.read_text(encoding="utf-8"), label=prompt_name)

    policy = json.loads(
        (base_dir / str(bindings["prompt_interface_contract"]["path"])).read_text()
    )
    if policy.get("contract_id") != PROMPT_INTERFACE_POLICY_ID:
        raise RuntimeError("V4.2 bound prompt-interface identity mismatch")
    if policy.get("status") != "FROZEN_AFTER_V4_1_RESULT_BEFORE_V4_2_OUTPUT_ACCESS":
        raise RuntimeError("V4.2 bound prompt-interface chronology mismatch")
    if policy.get("threshold_or_score_change_permitted") is not False:
        raise RuntimeError("V4.2 prompt-interface must not alter thresholds")
    if policy.get("v4_1_reinterpretation_permitted") is not False:
        raise RuntimeError("V4.2 must not reinterpret V4.1")

    norm = json.loads(
        (base_dir / str(bindings["output_normalization_contract"]["path"])).read_text()
    )
    if norm.get("contract_id") != OUTPUT_NORMALIZATION_POLICY_ID:
        raise RuntimeError("V4.2 must bind the frozen V4.1 normalization contract")

    parent = json.loads(
        (base_dir / str(bindings["v4_1_native_ingest_parent"]["path"])).read_text()
    )
    outcome = parent.get("task_seed_outcome")
    if not isinstance(outcome, Mapping):
        raise RuntimeError("V4.2 parent V4.1 outcome missing")
    if (
        outcome.get("exact_conceptual_pass_arm_count") != 0
        or outcome.get("valid_scientific_success_arm_count") != 0
        or outcome.get("score_comparison_permitted") is not False
    ):
        raise RuntimeError("V4.2 parent V4.1 nonconfirmatory authority mismatch")

    memory = json.loads((base_dir / str(bindings["research_memory_review"]["path"])).read_text())
    if memory.get("verdict") != "PASS":
        raise RuntimeError("V4.2 research-memory review did not pass")
    if memory.get("target_atom_id") != "P2-EMPIRICAL-BRIDGE-PENDULUM-001":
        raise RuntimeError("V4.2 research-memory atom mismatch")


def validate_v4_2_execution_head(
    execution_contract: Mapping[str, object],
    *,
    checkout_head_sha: str,
    origin_main_head_sha: str,
    batch_expected_head_sha: str,
) -> None:
    if execution_contract.get("require_exact_checkout_head") is not True:
        raise RuntimeError("V4.2 exact checkout head gate disabled")
    if (
        execution_contract.get("exact_checkout_head_binding_source")
        != "POST_MERGE_BATCH_CONTRACT_EXPECTED_REPO_SHA"
    ):
        raise RuntimeError("V4.2 exact checkout head binding source mismatch")
    for value in (checkout_head_sha, origin_main_head_sha, batch_expected_head_sha):
        if _SHA40.fullmatch(value) is None:
            raise RuntimeError("V4.2 exact checkout head identity invalid")
    if checkout_head_sha != batch_expected_head_sha:
        raise RuntimeError("V4.2 batch-bound exact checkout head mismatch")
    if checkout_head_sha != origin_main_head_sha:
        raise RuntimeError("V4.2 checkout is not the merged origin/main head")


def _stopping_backend(
    inner: Callable[..., v4.BackendGeneration],
) -> Callable[..., v4.BackendGeneration]:
    """Wrap generation so trailing prose after a completed JSON fence is not emitted."""

    def generate(prompt: str, **kwargs: object) -> v4.BackendGeneration:
        result = inner(prompt, **kwargs)
        text = result.raw_text
        fence_end = re.search(r"```json\r?\n.*?\r?\n```", text, re.DOTALL)
        if fence_end is not None:
            clipped = text[: fence_end.end()].strip()
            if clipped != text.strip():
                return v4.BackendGeneration(
                    raw_text=clipped,
                    input_tokens=result.input_tokens,
                    output_tokens=result.output_tokens,
                    backend_version=result.backend_version + "+v4_2_stop_after_json_fence",
                    wall_time_ms=result.wall_time_ms,
                    process_high_water_rss_bytes_after_arm=(
                        result.process_high_water_rss_bytes_after_arm
                    ),
                )
        bare = text.strip()
        if bare.startswith("{"):
            try:
                json.loads(bare)
            except json.JSONDecodeError:
                # Attempt to clip to the first top-level object end.
                depth = 0
                in_string = False
                escape = False
                end_idx = None
                for idx, ch in enumerate(bare):
                    if in_string:
                        if escape:
                            escape = False
                        elif ch == "\\":
                            escape = True
                        elif ch == '"':
                            in_string = False
                        continue
                    if ch == '"':
                        in_string = True
                    elif ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            end_idx = idx + 1
                            break
                if end_idx is not None and end_idx < len(bare):
                    clipped = bare[:end_idx]
                    return v4.BackendGeneration(
                        raw_text=clipped,
                        input_tokens=result.input_tokens,
                        output_tokens=result.output_tokens,
                        backend_version=result.backend_version + "+v4_2_stop_after_json_object",
                        wall_time_ms=result.wall_time_ms,
                        process_high_water_rss_bytes_after_arm=(
                            result.process_high_water_rss_bytes_after_arm
                        ),
                    )
            else:
                return result
        return result

    return generate


def audit_execution_packet_v4_2(
    packet: Mapping[str, object],
    *,
    base_dir: Path | None = None,
    runtime_versions: Mapping[str, str] | None = None,
    observed_at_utc: str | None = None,
) -> v4.MicrotrialPreflightReport:
    root = Path.cwd() if base_dir is None else base_dir
    try:
        validate_v4_2_candidate_packet(packet, base_dir=root)
    except (RuntimeError, OSError, json.JSONDecodeError) as exc:
        return v4.MicrotrialPreflightReport(
            verdict=v4.MicrotrialPreflightVerdict.REJECT,
            blockers=(),
            invalid_bindings=(str(exc),),
            checks=(),
        )
    # Reuse V4 semantic binding auditor after V4.2 chronology gates pass.
    return v4.audit_execution_packet(
        packet,
        base_dir=root,
        runtime_versions=runtime_versions,
        observed_at_utc=observed_at_utc,
    )


def _git_rev_parse(repository_root: Path, revision: str) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", revision],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def execute_microtrial_v4_2(
    packet_path: Path,
    output_dir: Path,
    *,
    created_at_utc: str,
    expected_checkout_head_sha: str,
    checkout_head_sha: str | None = None,
    origin_main_head_sha: str | None = None,
    backend: Callable[..., v4.BackendGeneration] | None = None,
    runtime_versions: Mapping[str, str] | None = None,
    checkout_probe: Callable[[Path, str], v4.ExecutionCheckoutState] | None = None,
    execution_host: str | None = None,
    scheduler_job_id: str | None = None,
) -> None:
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    repository_root = Path.cwd()
    validate_v4_2_candidate_packet(packet, base_dir=repository_root)
    bindings = packet["bindings"]
    execution_contract = json.loads(
        (repository_root / str(bindings["execution_contract"]["path"])).read_text()
    )
    observed_checkout = (
        checkout_head_sha if checkout_head_sha is not None else _git_rev_parse(repository_root, "HEAD")
    )
    observed_main = (
        origin_main_head_sha
        if origin_main_head_sha is not None
        else _git_rev_parse(repository_root, "refs/remotes/origin/main")
    )
    validate_v4_2_execution_head(
        execution_contract,
        checkout_head_sha=observed_checkout,
        origin_main_head_sha=observed_main,
        batch_expected_head_sha=expected_checkout_head_sha,
    )

    inner = backend if backend is not None else v4._local_transformers_backend
    wrapped = _stopping_backend(inner)

    # Monkeypatch V4.1 scoring hook used by the shared execute path via v4_1.
    original_score = v4._score_blinded_outputs

    def score_with_policy(raw_outputs: Mapping[str, str]) -> list[dict[str, object]]:
        return _score_blinded_outputs(
            raw_outputs,
            output_normalization_policy_id=OUTPUT_NORMALIZATION_POLICY_ID,
        )

    v4._score_blinded_outputs = score_with_policy  # type: ignore[assignment]
    try:
        v4.execute_microtrial(
            packet_path,
            output_dir,
            created_at_utc=created_at_utc,
            backend=wrapped,
            runtime_versions=runtime_versions,
            checkout_probe=checkout_probe,
            execution_host=execution_host,
            scheduler_job_id=scheduler_job_id,
        )
    finally:
        v4._score_blinded_outputs = original_score  # type: ignore[assignment]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Paper-2 pendulum microtrial V4.2 runner")
    parser.add_argument("packet")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--created-at-utc", required=True)
    parser.add_argument("--expected-checkout-head-sha", required=True)
    args = parser.parse_args(argv)
    execute_microtrial_v4_2(
        Path(args.packet),
        Path(args.output_dir),
        created_at_utc=args.created_at_utc,
        expected_checkout_head_sha=args.expected_checkout_head_sha,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
