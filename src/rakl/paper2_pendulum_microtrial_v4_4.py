"""Paper-2 pendulum microtrial V4.4 runner — leak-free prompts, gate unchanged."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Callable, Mapping

from . import paper2_pendulum_microtrial as v4
from . import paper2_pendulum_microtrial_v4_2 as v4_2
from . import paper2_pendulum_microtrial_v4_3_1 as v4_3_1
from .degeneracy_probe import ArmPair, DegeneracyStatus, probe_arm_answer_leak
from .paper2_v4_4_positive_control import (
    POSITIVE_CONTROL_ID,
    evaluate_positive_control_sensitivity,
)

OUTPUT_NORMALIZATION_POLICY_ID = v4_3_1.OUTPUT_NORMALIZATION_POLICY_ID
PROMPT_INTERFACE_POLICY_ID = v4_3_1.PROMPT_INTERFACE_POLICY_ID
CHRONOLOGY_CLASS = "ADAPTIVE_TYPE_B_LEAK_REPAIR_FRESH_ONLY_TO_V4_4_OUTPUTS"
MODEL_ID = v4_3_1.MODEL_ID
MODEL_REVISION = v4_3_1.MODEL_REVISION

_V4_4_BINDINGS = (
    "execution_contract",
    "output_normalization_contract",
    "output_normalizer",
    "prompt_interface_contract",
    "direct_prompt",
    "rakl_prompt",
    "difference_witness",
    "research_memory_review",
    "positive_control_sensitivity",
    "model_manifest",
    "tokenizer_manifest",
    "resources",
    "parent_v4_3_1_type_b_disposition",
)

_GOLD_FIELDS = {
    "misaligned_source_ids": frozenset({"S4", "S5"}),
    "required_refuted_source_ids": frozenset({"S6"}),
}


def normalize_pendulum_output_v4_4(raw_text: str) -> str:
    return v4_3_1.normalize_pendulum_output_v4_3_1(raw_text)


def validate_v4_4_candidate_packet(packet: Mapping[str, object], *, base_dir: Path) -> None:
    if packet.get("chronology_class") != CHRONOLOGY_CLASS:
        raise RuntimeError("V4.4 chronology class missing")
    if packet.get("output_normalization_policy_id") != OUTPUT_NORMALIZATION_POLICY_ID:
        raise RuntimeError("V4.4 must inherit V4.3.1 output-normalization policy")
    if packet.get("prompt_interface_policy_id") != PROMPT_INTERFACE_POLICY_ID:
        raise RuntimeError("V4.4 must inherit V4.3.1 prompt-interface policy")
    if packet.get("threshold_or_score_change_permitted") is not False:
        raise RuntimeError("V4.4 must not change the sealed conceptual gate")
    if packet.get("v4_4_outputs_opened_before_freeze") is not False:
        raise RuntimeError("V4.4 output chronology violated")
    if packet.get("seed_schedule") != [17]:
        raise RuntimeError("V4.4 seed must remain 17")
    if packet.get("rakl_vs_direct_claim_from_leaked_parents_permitted") is not False:
        raise RuntimeError("V4.4 must forbid re-claiming leaked parent arm gaps")

    bindings = packet.get("bindings")
    if not isinstance(bindings, Mapping):
        raise RuntimeError("V4.4 bindings missing")
    root = base_dir.resolve()
    for name in _V4_4_BINDINGS:
        binding = bindings.get(name)
        if not isinstance(binding, Mapping):
            raise RuntimeError(f"V4.4 binding missing:{name}")
        raw_path = binding.get("path")
        expected_sha = binding.get("sha256")
        if not isinstance(raw_path, str) or not isinstance(expected_sha, str):
            raise RuntimeError(f"V4.4 binding malformed:{name}")
        path = (base_dir / raw_path).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise RuntimeError(f"V4.4 bound artifact missing or outside repository:{name}")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha:
            raise RuntimeError(f"V4.4 binding mismatch:{name}")

    for prompt_name in ("direct_prompt", "rakl_prompt"):
        prompt_path = base_dir / str(bindings[prompt_name]["path"])
        v4_3_1._require_flat_shape_prompt(
            prompt_path.read_text(encoding="utf-8"), label=prompt_name
        )

    rakl_text = (base_dir / str(bindings["rakl_prompt"]["path"])).read_text(encoding="utf-8")
    direct_text = (base_dir / str(bindings["direct_prompt"]["path"])).read_text(encoding="utf-8")
    probe = probe_arm_answer_leak(
        ArmPair("paper2_microtrial_v4_4", rakl_text, direct_text, _GOLD_FIELDS)
    )
    if probe.status is not DegeneracyStatus.CLEAN:
        raise RuntimeError(f"V4.4 arm pair not CLEAN:{probe.status.value}")

    pc = json.loads(
        (base_dir / str(bindings["positive_control_sensitivity"]["path"])).read_text(
            encoding="utf-8"
        )
    )
    if pc.get("passed") is not True:
        raise RuntimeError("V4.4 positive-control sensitivity did not pass")
    if pc.get("positive_control_id") != POSITIVE_CONTROL_ID:
        raise RuntimeError("V4.4 positive-control identity mismatch")
    if pc.get("grants_scientific_authority") is not False:
        raise RuntimeError("V4.4 positive-control must not grant scientific authority")
    if pc.get("grants_capability_floor_clearance") is not False:
        raise RuntimeError("V4.4 positive-control must not clear capability floor")
    if pc.get("rakl_prompt_sha256") != hashlib.sha256(rakl_text.encode()).hexdigest():
        raise RuntimeError("V4.4 positive-control receipt unbound from RAKL prompt")
    if pc.get("direct_prompt_sha256") != hashlib.sha256(direct_text.encode()).hexdigest():
        raise RuntimeError("V4.4 positive-control receipt unbound from DIRECT prompt")

    live = evaluate_positive_control_sensitivity(
        rakl_prompt=rakl_text, direct_prompt=direct_text, surface="paper2_microtrial_v4_4"
    )
    if not live.passed:
        raise RuntimeError("V4.4 live positive-control recheck failed:" + ",".join(live.problems))

    model = json.loads((base_dir / str(bindings["model_manifest"]["path"])).read_text())
    if model.get("model_id") != MODEL_ID or model.get("revision") != MODEL_REVISION:
        raise RuntimeError("V4.4 model identity mismatch")
    if model.get("generation", {}).get("seed") != 17:
        raise RuntimeError("V4.4 generation seed mismatch")

    witness = json.loads((base_dir / str(bindings["difference_witness"]["path"])).read_text())
    changed = set(witness.get("changed_structural_coordinates") or [])
    forbidden = {
        "exact_conceptual_pass_threshold",
        "prompt_field_polarity",
        "seed",
        "model_revision",
        "output_schema_presentation_flat_object_shape",
        "optional_registered_fields_id_envelope_unwrap",
    }
    if changed & forbidden:
        raise RuntimeError("V4.4 DifferenceWitness changed a frozen gate coordinate")
    if "rakl_context_prompt_type_b_answer_key_leak_repair" not in changed:
        raise RuntimeError("V4.4 DifferenceWitness missing leak-repair coordinate")

    memory = json.loads((base_dir / str(bindings["research_memory_review"]["path"])).read_text())
    if memory.get("verdict") != "PASS":
        raise RuntimeError("V4.4 research-memory review did not pass")
    if memory.get("target_atom_id") != "P2-EMPIRICAL-BRIDGE-PENDULUM-001":
        raise RuntimeError("V4.4 research-memory atom mismatch")

    evaluator_path = base_dir / "research/paper2_microtrial_v1/EVALUATOR_PROTOCOL.json"
    if "evaluator" in bindings:
        evaluator_path = base_dir / str(bindings["evaluator"]["path"])
    evaluator = json.loads(evaluator_path.read_text(encoding="utf-8"))
    if evaluator.get("evaluator_id") != "PENDULUM_KNOWN_ANSWER_V2":
        raise RuntimeError("V4.4 evaluator identity changed")


def execute_microtrial_v4_4(
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
    validate_v4_4_candidate_packet(packet, base_dir=repository_root)
    bindings = packet["bindings"]
    execution_contract = json.loads(
        (repository_root / str(bindings["execution_contract"]["path"])).read_text()
    )

    def _git_rev_parse(revision: str) -> str:
        return subprocess.run(
            ["git", "rev-parse", revision],
            cwd=repository_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    observed_checkout = (
        checkout_head_sha if checkout_head_sha is not None else _git_rev_parse("HEAD")
    )
    observed_main = (
        origin_main_head_sha
        if origin_main_head_sha is not None
        else _git_rev_parse("refs/remotes/origin/main")
    )
    v4_2.validate_v4_2_execution_head(
        execution_contract,
        checkout_head_sha=observed_checkout,
        origin_main_head_sha=observed_main,
        batch_expected_head_sha=expected_checkout_head_sha,
    )

    inner = backend if backend is not None else v4._local_transformers_backend
    wrapped = v4_2._stopping_backend(inner)
    original_score = v4._score_blinded_outputs

    def score_with_policy(raw_outputs: Mapping[str, str]) -> list[dict[str, object]]:
        return v4_3_1._score_blinded_outputs(
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
    parser = argparse.ArgumentParser(description="Paper-2 pendulum microtrial V4.4 runner")
    parser.add_argument("packet")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--created-at-utc", required=True)
    parser.add_argument("--expected-checkout-head-sha", required=True)
    args = parser.parse_args(argv)
    execute_microtrial_v4_4(
        Path(args.packet),
        Path(args.output_dir),
        created_at_utc=args.created_at_utc,
        expected_checkout_head_sha=args.expected_checkout_head_sha,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
