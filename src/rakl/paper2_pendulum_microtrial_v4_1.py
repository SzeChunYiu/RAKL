from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
import re
import subprocess
from typing import Callable, Mapping

from . import paper2_pendulum_microtrial as v4
from .matched_microtrial import score_pendulum_answer


OUTPUT_NORMALIZATION_POLICY_ID = (
    "PENDULUM_EXACT_JSON_OR_SINGLE_LOWERCASE_JSON_FENCE_V4_1"
)
_SINGLE_JSON_FENCE = re.compile(
    r"\s*```json\r?\n(?P<body>.*?)\r?\n```\s*", re.DOTALL
)
_SHA40 = re.compile(r"[0-9a-f]{40}")
_V4_1_BINDINGS = (
    "execution_contract",
    "output_normalization_contract",
    "output_normalizer",
    "v4_native_ingest",
)
_V4_AUDIT = v4.audit_execution_packet


def normalize_pendulum_output_v4_1(raw_text: str) -> str:
    """Accept a bare JSON object or exactly one lowercase ``json`` fence."""

    stripped = raw_text.strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, Mapping):
        return stripped
    match = _SINGLE_JSON_FENCE.fullmatch(raw_text)
    if match is None:
        raise ValueError("V4.1 output normalization rejected nonexact serialization")
    body = match.group("body").strip()
    try:
        parsed_body = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ValueError("V4.1 output normalization rejected invalid fenced JSON") from exc
    if not isinstance(parsed_body, Mapping):
        raise ValueError("V4.1 output normalization rejected non-object JSON")
    return body


def _score_blinded_outputs(
    raw_outputs: Mapping[str, str],
    *,
    output_normalization_policy_id: str | None = None,
) -> list[dict[str, object]]:
    if output_normalization_policy_id not in (None, OUTPUT_NORMALIZATION_POLICY_ID):
        raise ValueError("unsupported output normalization policy")
    scores: list[dict[str, object]] = []
    for blind_id in sorted(raw_outputs):
        try:
            raw_text = raw_outputs[blind_id]
            if output_normalization_policy_id is not None:
                raw_text = normalize_pendulum_output_v4_1(raw_text)
            answer = v4._parse_answer(raw_text)
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


def validate_v4_1_candidate_packet(packet: Mapping[str, object], *, base_dir: Path) -> None:
    """Fail closed on the exact adaptive V4.1 candidate and its V4 null parent."""

    if packet.get("chronology_class") != "ADAPTIVE_PARSER_REPLAY_FRESH_ONLY_TO_V4_1_OUTPUTS":
        raise RuntimeError("V4.1 adaptive chronology class missing")
    if (
        packet.get("adaptive_replay_status")
        != "FROZEN_ADAPTIVE_CANDIDATE_REQUIRES_POST_MERGE_BATCH_HEAD_BINDING"
    ):
        raise RuntimeError("V4.1 adaptive replay status mismatch")
    if packet.get("parent_v4_results_opened_before_v4_1_freeze") is not True:
        raise RuntimeError("V4.1 parent-result access disclosure missing")
    if packet.get("v4_1_outputs_opened_before_freeze") is not False:
        raise RuntimeError("V4.1 output chronology violated")
    if packet.get("evaluated_results_opened_before_freeze") is not False:
        raise RuntimeError("V4.1 legacy result-access gate violated")
    if (
        packet.get("evaluated_results_opened_before_freeze_scope")
        != "V4_1_OUTPUTS_ONLY_PARENT_V4_KNOWN"
    ):
        raise RuntimeError("V4.1 result-access scope missing")
    if (
        packet.get("evaluated_task_seed_unit_count_before_freeze_scope")
        != "V4_1_OUTPUTS_ONLY_PARENT_V4_KNOWN"
    ):
        raise RuntimeError("V4.1 evaluated-unit scope missing")
    if packet.get("output_normalization_policy_id") != OUTPUT_NORMALIZATION_POLICY_ID:
        raise RuntimeError("V4.1 packet output-normalization policy mismatch")

    bindings = packet.get("bindings")
    if not isinstance(bindings, Mapping):
        raise RuntimeError("V4.1 bindings missing")
    root = base_dir.resolve()
    for name in _V4_1_BINDINGS:
        binding = bindings.get(name)
        if not isinstance(binding, Mapping):
            raise RuntimeError(f"V4.1 binding missing:{name}")
        raw_path = binding.get("path")
        expected_sha = binding.get("sha256")
        if not isinstance(raw_path, str) or not isinstance(expected_sha, str):
            raise RuntimeError(f"V4.1 binding malformed:{name}")
        path = (base_dir / raw_path).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise RuntimeError(f"V4.1 bound artifact missing or outside repository:{name}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha:
            raise RuntimeError(f"V4.1 binding mismatch:{name}")

    policy = json.loads(
        (base_dir / str(bindings["output_normalization_contract"]["path"])).read_text()
    )
    if policy.get("contract_id") != OUTPUT_NORMALIZATION_POLICY_ID:
        raise RuntimeError("V4.1 bound policy identity mismatch")
    if policy.get("status") != "FROZEN_AFTER_V4_RESULT_BEFORE_V4_1_OUTPUT_ACCESS":
        raise RuntimeError("V4.1 bound policy chronology mismatch")

    execution_contract = json.loads(
        (base_dir / str(bindings["execution_contract"]["path"])).read_text()
    )
    if (
        execution_contract.get("require_exact_checkout_head") is not True
        or execution_contract.get("exact_checkout_head_binding_source")
        != "POST_MERGE_BATCH_CONTRACT_EXPECTED_REPO_SHA"
        or execution_contract.get("required_execution_ref") != "refs/remotes/origin/main"
    ):
        raise RuntimeError("V4.1 exact merged-head contract mismatch")

    ingest = json.loads((base_dir / str(bindings["v4_native_ingest"]["path"])).read_text())
    outcome = ingest.get("task_seed_outcome")
    if not isinstance(outcome, Mapping):
        raise RuntimeError("V4.1 parent V4 outcome missing")
    if (
        outcome.get("frozen_parse_valid_arm_count") != 0
        or outcome.get("frozen_scorable_arm_count") != 0
        or outcome.get("score_comparison_permitted") is not False
        or outcome.get("posthoc_normalized_scores_authorized") is not False
    ):
        raise RuntimeError("V4.1 parent V4 null authority mismatch")


def validate_v4_1_execution_head(
    execution_contract: Mapping[str, object],
    *,
    checkout_head_sha: str,
    origin_main_head_sha: str,
    batch_expected_head_sha: str,
) -> None:
    """Require the external post-merge batch binding and merged origin/main head."""

    if execution_contract.get("require_exact_checkout_head") is not True:
        raise RuntimeError("V4.1 exact checkout head gate disabled")
    if (
        execution_contract.get("exact_checkout_head_binding_source")
        != "POST_MERGE_BATCH_CONTRACT_EXPECTED_REPO_SHA"
    ):
        raise RuntimeError("V4.1 exact checkout head binding source mismatch")
    for value in (checkout_head_sha, origin_main_head_sha, batch_expected_head_sha):
        if _SHA40.fullmatch(value) is None:
            raise RuntimeError("V4.1 exact checkout head identity invalid")
    if checkout_head_sha != batch_expected_head_sha:
        raise RuntimeError("V4.1 batch-bound exact checkout head mismatch")
    if checkout_head_sha != origin_main_head_sha:
        raise RuntimeError("V4.1 checkout is not the merged origin/main head")


def audit_execution_packet_v4_1(
    packet: Mapping[str, object],
    *,
    base_dir: Path | None = None,
    runtime_versions: Mapping[str, str] | None = None,
    observed_at_utc: str | None = None,
) -> v4.MicrotrialPreflightReport:
    """Apply the frozen V4 checks without weakening or editing the V4 runner bytes."""

    root = Path.cwd() if base_dir is None else base_dir
    try:
        validate_v4_1_candidate_packet(packet, base_dir=root)
    except (RuntimeError, OSError, json.JSONDecodeError) as exc:
        return v4.MicrotrialPreflightReport(
            verdict=v4.MicrotrialPreflightVerdict.REJECT,
            blockers=(),
            invalid_bindings=(str(exc),),
            checks=(),
        )
    return _V4_AUDIT(
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


def execute_microtrial_v4_1(
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
    validate_v4_1_candidate_packet(packet, base_dir=repository_root)
    bindings = packet["bindings"]
    execution_contract = json.loads(
        (repository_root / str(bindings["execution_contract"]["path"])).read_text()
    )
    validate_v4_1_execution_head(
        execution_contract,
        checkout_head_sha=(
            _git_rev_parse(repository_root, "HEAD")
            if checkout_head_sha is None
            else checkout_head_sha
        ),
        origin_main_head_sha=(
            _git_rev_parse(repository_root, "refs/remotes/origin/main")
            if origin_main_head_sha is None
            else origin_main_head_sha
        ),
        batch_expected_head_sha=expected_checkout_head_sha,
    )

    original_score = v4._score_blinded_outputs

    def versioned_score(raw_outputs: Mapping[str, str]) -> list[dict[str, object]]:
        return _score_blinded_outputs(
            raw_outputs,
            output_normalization_policy_id=OUTPUT_NORMALIZATION_POLICY_ID,
        )

    v4._score_blinded_outputs = versioned_score
    try:
        v4.execute_microtrial(
            packet_path,
            output_dir,
            created_at_utc=created_at_utc,
            backend=backend,
            runtime_versions=runtime_versions,
            checkout_probe=checkout_probe,
            execution_host=execution_host,
            scheduler_job_id=scheduler_job_id,
        )
    finally:
        v4._score_blinded_outputs = original_score


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute the frozen Paper-2 V4.1 successor")
    parser.add_argument("packet", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--created-at-utc", required=True)
    parser.add_argument("--expected-checkout-head-sha", required=True)
    args = parser.parse_args(argv)
    execute_microtrial_v4_1(
        args.packet,
        args.output_dir,
        created_at_utc=args.created_at_utc,
        expected_checkout_head_sha=args.expected_checkout_head_sha,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
