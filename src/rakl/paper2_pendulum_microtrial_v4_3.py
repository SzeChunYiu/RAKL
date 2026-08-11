from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Callable, Mapping

from . import paper2_pendulum_microtrial as v4
from . import paper2_pendulum_microtrial_v4_1 as v4_1
from . import paper2_pendulum_microtrial_v4_2 as v4_2

OUTPUT_NORMALIZATION_POLICY_ID = v4_1.OUTPUT_NORMALIZATION_POLICY_ID
PROMPT_INTERFACE_POLICY_ID = v4_2.PROMPT_INTERFACE_POLICY_ID
CHRONOLOGY_CLASS = "MODEL_SCALE_STAGING_REPLAY_FRESH_ONLY_TO_V4_3_OUTPUTS"
MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
MODEL_REVISION = "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"

_V4_3_BINDINGS = (
    "execution_contract",
    "output_normalization_contract",
    "output_normalizer",
    "prompt_interface_contract",
    "direct_prompt",
    "rakl_prompt",
    "difference_witness",
    "research_memory_review",
    "model_manifest",
    "tokenizer_manifest",
    "resources",
    "v4_2_capability_limit_parent",
)


def normalize_pendulum_output_v4_3(raw_text: str) -> str:
    """Reuse the frozen V4.1/V4.2 normalizer without widening serialization."""

    return v4_2.normalize_pendulum_output_v4_2(raw_text)


def validate_v4_3_candidate_packet(packet: Mapping[str, object], *, base_dir: Path) -> None:
    if packet.get("chronology_class") != CHRONOLOGY_CLASS:
        raise RuntimeError("V4.3 chronology class missing")
    if packet.get("output_normalization_policy_id") != OUTPUT_NORMALIZATION_POLICY_ID:
        raise RuntimeError("V4.3 must reuse frozen V4.1 output-normalization policy")
    if packet.get("prompt_interface_policy_id") != PROMPT_INTERFACE_POLICY_ID:
        raise RuntimeError("V4.3 must reuse frozen V4.2 prompt-interface policy")
    if packet.get("threshold_or_score_change_permitted") is not False:
        raise RuntimeError("V4.3 must not change the sealed conceptual gate")
    if packet.get("v4_3_outputs_opened_before_freeze") is not False:
        raise RuntimeError("V4.3 output chronology violated")
    if packet.get("seed_schedule") != [17]:
        raise RuntimeError("V4.3 seed must remain 17")

    bindings = packet.get("bindings")
    if not isinstance(bindings, Mapping):
        raise RuntimeError("V4.3 bindings missing")
    root = base_dir.resolve()
    for name in _V4_3_BINDINGS:
        binding = bindings.get(name)
        if not isinstance(binding, Mapping):
            raise RuntimeError(f"V4.3 binding missing:{name}")
        raw_path = binding.get("path")
        expected_sha = binding.get("sha256")
        if not isinstance(raw_path, str) or not isinstance(expected_sha, str):
            raise RuntimeError(f"V4.3 binding malformed:{name}")
        path = (base_dir / raw_path).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise RuntimeError(f"V4.3 bound artifact missing or outside repository:{name}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha:
            raise RuntimeError(f"V4.3 binding mismatch:{name}")

    for prompt_name in ("direct_prompt", "rakl_prompt"):
        prompt_path = base_dir / str(bindings[prompt_name]["path"])
        v4_2._require_field_polarity_prompt(
            prompt_path.read_text(encoding="utf-8"), label=prompt_name
        )

    model = json.loads((base_dir / str(bindings["model_manifest"]["path"])).read_text())
    if model.get("model_id") != MODEL_ID or model.get("revision") != MODEL_REVISION:
        raise RuntimeError("V4.3 model identity mismatch")
    if model.get("generation", {}).get("seed") != 17:
        raise RuntimeError("V4.3 generation seed mismatch")

    witness = json.loads((base_dir / str(bindings["difference_witness"]["path"])).read_text())
    changed = set(witness.get("changed_structural_coordinates") or [])
    forbidden = {
        "exact_conceptual_pass_threshold",
        "output_normalization_policy",
        "prompt_field_polarity",
        "seed",
    }
    if changed & forbidden:
        raise RuntimeError("V4.3 DifferenceWitness changed a frozen gate coordinate")
    if "model_parameter_scale_0_5B_to_1_5B" not in changed:
        raise RuntimeError("V4.3 DifferenceWitness missing model-scale coordinate")

    memory = json.loads((base_dir / str(bindings["research_memory_review"]["path"])).read_text())
    if memory.get("verdict") != "PASS":
        raise RuntimeError("V4.3 research-memory review did not pass")
    if memory.get("target_atom_id") != "P2-EMPIRICAL-BRIDGE-PENDULUM-001":
        raise RuntimeError("V4.3 research-memory atom mismatch")

    evaluator_path = base_dir / "research/paper2_microtrial_v1/EVALUATOR_PROTOCOL.json"
    if "evaluator" in bindings:
        evaluator_path = base_dir / str(bindings["evaluator"]["path"])
    evaluator = json.loads(evaluator_path.read_text(encoding="utf-8"))
    if evaluator.get("evaluator_id") != "PENDULUM_KNOWN_ANSWER_V2":
        raise RuntimeError("V4.3 evaluator identity changed")


def validate_v4_3_execution_head(
    execution_contract: Mapping[str, object],
    *,
    checkout_head_sha: str,
    origin_main_head_sha: str,
    batch_expected_head_sha: str,
) -> None:
    v4_2.validate_v4_2_execution_head(
        execution_contract,
        checkout_head_sha=checkout_head_sha,
        origin_main_head_sha=origin_main_head_sha,
        batch_expected_head_sha=batch_expected_head_sha,
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


def execute_microtrial_v4_3(
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
    validate_v4_3_candidate_packet(packet, base_dir=repository_root)
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
    validate_v4_3_execution_head(
        execution_contract,
        checkout_head_sha=observed_checkout,
        origin_main_head_sha=observed_main,
        batch_expected_head_sha=expected_checkout_head_sha,
    )

    inner = backend if backend is not None else v4._local_transformers_backend
    wrapped = v4_2._stopping_backend(inner)
    original_score = v4._score_blinded_outputs

    def score_with_policy(raw_outputs: Mapping[str, str]) -> list[dict[str, object]]:
        return v4_1._score_blinded_outputs(
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
    parser = argparse.ArgumentParser(description="Paper-2 pendulum microtrial V4.3 runner")
    parser.add_argument("packet")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--created-at-utc", required=True)
    parser.add_argument("--expected-checkout-head-sha", required=True)
    args = parser.parse_args(argv)
    execute_microtrial_v4_3(
        Path(args.packet),
        Path(args.output_dir),
        created_at_utc=args.created_at_utc,
        expected_checkout_head_sha=args.expected_checkout_head_sha,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
