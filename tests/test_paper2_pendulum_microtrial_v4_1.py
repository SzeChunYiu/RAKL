from __future__ import annotations

import json
import hashlib
import platform
from pathlib import Path

import pytest

import rakl.paper2_pendulum_microtrial_v4_1 as runner
from rakl.paper2_pendulum_microtrial import BackendGeneration, ExecutionCheckoutState

from frozen_source_snapshots import execution_time_base_dir

ROOT = Path(__file__).resolve().parents[1]


ANSWER = json.dumps(
    {
        "small_angle_is_asymptotic": True,
        "finite_amplitude_increases_period": True,
        "context_distinct_claims_not_direct_contradictions": True,
        "ideal_period_is_mass_invariant": True,
        "context_alignment_required_before_contradiction": True,
        "supporting_source_ids": ["S1"],
        "rejected_as_misaligned_source_ids": ["S4"],
        "refuted_source_ids": ["S6"],
    },
    sort_keys=True,
)


def test_v4_1_accepts_bare_json_without_mutation() -> None:
    assert runner.normalize_pendulum_output_v4_1(ANSWER) == ANSWER


def test_v4_1_accepts_exactly_one_lowercase_json_fence() -> None:
    assert runner.normalize_pendulum_output_v4_1(f"```json\n{ANSWER}\n```\n") == ANSWER


@pytest.mark.parametrize(
    "raw",
    (
        f"```json\n{ANSWER}\n```\nExplanation: trailing prose",
        f"```JSON\n{ANSWER}\n```",
        f"```\n{ANSWER}\n```",
        f"```json\n{ANSWER}\n```\n```json\n{ANSWER}\n```",
    ),
)
def test_v4_1_rejects_nonexact_fence_or_trailing_content(raw: str) -> None:
    with pytest.raises(ValueError, match="V4.1 output normalization rejected"):
        runner.normalize_pendulum_output_v4_1(raw)


def test_v4_1_scoring_normalizes_only_under_explicit_policy() -> None:
    raw = {"BLIND_A": f"```json\n{ANSWER}\n```", "BLIND_B": f"```json\n{ANSWER}\n```\nprose"}
    strict = runner._score_blinded_outputs(raw)
    assert [row["parse_valid"] for row in strict] == [False, False]
    repaired = runner._score_blinded_outputs(
        raw, output_normalization_policy_id="PENDULUM_EXACT_JSON_OR_SINGLE_LOWERCASE_JSON_FENCE_V4_1"
    )
    assert [row["parse_valid"] for row in repaired] == [True, False]


def test_v4_1_candidate_validation_rejects_any_unbound_successor_artifact(tmp_path) -> None:
    packet = json.loads(
        (ROOT / "research/paper2_microtrial_v4_1/EXECUTION_PACKET_V4_1_20260811.json").read_text()
    )
    base_dir = execution_time_base_dir(ROOT, packet, tmp_path)
    packet["bindings"]["output_normalization_contract"]["sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="V4.1 binding mismatch:output_normalization_contract"):
        runner.validate_v4_1_candidate_packet(packet, base_dir=base_dir)


def test_v4_1_exact_head_must_match_batch_binding_and_merged_origin_main() -> None:
    contract = json.loads(
        (ROOT / "research/paper2_microtrial_v4_1/EXECUTION_CONTRACT_V4_1.json").read_text()
    )
    exact = "a" * 40
    runner.validate_v4_1_execution_head(
        contract,
        checkout_head_sha=exact,
        origin_main_head_sha=exact,
        batch_expected_head_sha=exact,
    )
    with pytest.raises(RuntimeError, match="batch-bound exact checkout head mismatch"):
        runner.validate_v4_1_execution_head(
            contract,
            checkout_head_sha=exact,
            origin_main_head_sha=exact,
            batch_expected_head_sha="b" * 40,
        )
    with pytest.raises(RuntimeError, match="checkout is not the merged origin/main head"):
        runner.validate_v4_1_execution_head(
            contract,
            checkout_head_sha=exact,
            origin_main_head_sha="c" * 40,
            batch_expected_head_sha=exact,
        )


def test_v4_1_synthetic_execution_uses_scoped_freeze_and_exact_head(tmp_path, monkeypatch) -> None:
    def sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    packet = json.loads(
        (ROOT / "research/paper2_microtrial_v4_1/EXECUTION_PACKET_V4_1_20260811.json").read_text()
    )
    for name in ("output_normalizer", "output_normalization_contract", "v4_native_ingest"):
        source = ROOT / packet["bindings"][name]["path"]
        target = tmp_path / source.name
        target.write_bytes(source.read_bytes())
        packet["bindings"][name] = {"path": str(target.relative_to(tmp_path)), "sha256": sha(target)}

    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    model_file = snapshot / "model.safetensors"
    tokenizer_file = snapshot / "tokenizer.json"
    model_file.write_bytes(b"model")
    tokenizer_file.write_bytes(b"tokenizer")
    model = json.loads((ROOT / packet["bindings"]["model_manifest"]["path"]).read_text())
    tokenizer = json.loads((ROOT / packet["bindings"]["tokenizer_manifest"]["path"]).read_text())
    model["snapshot_path"] = str(snapshot)
    model["files"] = [{"path": model_file.name, "bytes": 5, "sha256": sha(model_file)}]
    tokenizer["files"] = [
        {"path": tokenizer_file.name, "bytes": 9, "sha256": sha(tokenizer_file)}
    ]
    environment = json.loads((ROOT / packet["bindings"]["environment"]["path"]).read_text())
    environment["platform"]["os"] = platform.system()
    environment["platform"]["architecture"] = platform.machine()
    contract = json.loads((ROOT / packet["bindings"]["execution_contract"]["path"]).read_text())
    contract["fs9_root"] = str(tmp_path)
    contract["repo_path"] = str(tmp_path)
    contract["output_root"] = str(tmp_path / "runs")
    contract["model_snapshot_path"] = str(snapshot)
    for name, value in (("model_manifest", model), ("tokenizer_manifest", tokenizer), ("environment", environment), ("execution_contract", contract)):
        target = tmp_path / f"{name}.json"
        target.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        packet["bindings"][name] = {"path": str(target.relative_to(tmp_path)), "sha256": sha(target)}
    # All untouched V4 bindings remain exact absolute references to the source checkout.
    for name, binding in packet["bindings"].items():
        if not Path(binding["path"]).is_absolute() and not (tmp_path / binding["path"]).exists():
            source = ROOT / binding["path"]
            binding["path"] = str(source)
            # The synthetic execution loads and runs the LIVE runner module, so
            # its packet must bind the live bytes; the frozen artifact on disk
            # keeps the execution-time sha (see tests/frozen_source_snapshots.py).
            binding["sha256"] = sha(source)
    evaluator = json.loads(Path(packet["bindings"]["evaluator"]["path"]).read_text())
    evaluator_impl = tmp_path / evaluator["implementation_source_path"]
    evaluator_impl.parent.mkdir(parents=True)
    evaluator_impl.write_bytes((ROOT / evaluator["implementation_source_path"]).read_bytes())
    packet_path = tmp_path / "packet.json"
    packet_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")

    def fake_backend(prompt: str, **_: object) -> BackendGeneration:
        return BackendGeneration(
            raw_text=f"```json\n{ANSWER}\n```",
            input_tokens=len(prompt.split()),
            output_tokens=len(ANSWER.split()),
            backend_version="fake-v4.1",
            wall_time_ms=1,
            process_high_water_rss_bytes_after_arm=1,
        )

    exact = "a" * 40
    monkeypatch.chdir(tmp_path)
    output = tmp_path / "runs" / "synthetic"
    runner.execute_microtrial_v4_1(
        packet_path,
        output,
        created_at_utc="2026-08-11T04:38:25Z",
        expected_checkout_head_sha=exact,
        checkout_head_sha=exact,
        origin_main_head_sha=exact,
        backend=fake_backend,
        runtime_versions={
            "python": "3.11.13",
            "torch": "2.8.0+cpu",
            "transformers": "4.55.0",
            "tokenizers": "0.21.4",
            "safetensors": "0.6.2",
        },
        checkout_probe=lambda *_: ExecutionCheckoutState(
            repo_path=str(tmp_path),
            head_sha=exact,
            tree_sha="b" * 40,
            clean=True,
            subject_ancestor=True,
        ),
        execution_host="compute-test",
        scheduler_job_id="123",
    )
    result = json.loads((output / "result_receipt.json").read_text())
    assert all(record["score"]["parse_valid"] is True for record in result["records"])
