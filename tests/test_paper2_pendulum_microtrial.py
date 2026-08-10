from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
Draft202012Validator = jsonschema.Draft202012Validator
FormatChecker = jsonschema.FormatChecker

from rakl.paper2_pendulum_microtrial import (
    _encode_prompt_for_generation,
    BackendGeneration,
    ExecutionCheckoutState,
    MicrotrialPreflightVerdict,
    audit_execution_packet,
    execute_microtrial,
    materialize_prompts,
    write_preflight_receipt,
)


ROOT = Path(__file__).resolve().parents[1]
FROZEN_PACKET = ROOT / "research" / "paper2_microtrial_v1" / "EXECUTION_PACKET_20260810.json"
FROZEN_PREFLIGHT = ROOT / "research" / "paper2_microtrial_v1" / "PREFLIGHT_RECEIPT_20260810.json"
RESULT_SCHEMA = ROOT / "schemas" / "paper2-pendulum-microtrial-result.schema.json"
MANUSCRIPT_STATUS = ROOT / "research" / "PAPER2_MICROTRIAL_MANUSCRIPT_STATUS_20260810.md"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _complete_fixture(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    system_prompt = tmp_path / "system_prompt.txt"
    system_prompt.write_text(
        "Use only supplied evidence. Return one JSON object matching the schema.\n",
        encoding="utf-8",
    )
    task = {
        "task_id": "PENDULUM_SEALED_001",
        "sealed_before_model_execution": True,
        "mandatory_evidence_ids": ["S1", "S2"],
        "sources": [
            {
                "source_id": "S1",
                "text": "The small-angle period is an approximation.",
                "context": ["Earth", "small_angle"],
                "projection": "small-angle law",
            },
            {
                "source_id": "S2",
                "text": "The ideal period is independent of bob mass.",
                "context": ["Earth", "ideal"],
                "projection": "mass invariance",
            },
        ],
        "rakl_relations": [
            {
                "left": "S1",
                "right": "S2",
                "relation": "COMPLEMENTARY_FACETS",
                "reason": "period-law and mass-invariance facets",
            }
        ],
    }
    questions = {
        "question_set_id": "PENDULUM_QUESTIONS_001",
        "questions": [{"question_id": "Q1", "prompt": "State both registered conclusions."}],
        "output_schema": {
            "id": "PENDULUM_STRUCTURED_ANSWER_V2",
            "fields": [
                "small_angle_is_asymptotic:boolean",
                "finite_amplitude_increases_period:boolean",
                "context_distinct_claims_not_direct_contradictions:boolean",
                "ideal_period_is_mass_invariant:boolean",
                "context_alignment_required_before_contradiction:boolean",
                "supporting_source_ids:list[string]",
                "rejected_as_misaligned_source_ids:list[string]",
                "refuted_source_ids:list[string]",
            ],
        },
    }
    evaluator_impl = tmp_path / "sealed_evaluator.py"
    evaluator_impl.write_text("def score(value):\n    return value\n", encoding="utf-8")
    evaluator = {
        "evaluator_id": "PENDULUM_KNOWN_ANSWER_V2",
        "implementation": "rakl.matched_microtrial::score_pendulum_answer",
        "implementation_source_path": str(evaluator_impl),
        "implementation_source_sha256": _sha256(evaluator_impl),
        "required_support_source_ids": ["S1", "S2"],
        "allowed_support_source_ids": ["S1", "S2"],
        "misaligned_source_ids": [],
        "required_refuted_source_ids": [],
        "arm_identity_blinded": True,
    }
    resources = {
        "seed": 17,
        "max_input_tokens": 4096,
        "max_output_tokens": 512,
        "max_tool_calls": 0,
        "max_retrieval_calls": 0,
        "max_wall_time_ms_per_arm": 900000,
        "max_peak_rss_bytes_per_arm": 1000000,
    }
    prices = {
        "price_sheet_id": "LOCAL_ONLY_V1",
        "provider_api_cost_usd_per_input_token": 0,
        "provider_api_cost_usd_per_output_token": 0,
        "unpriced_coordinates": ["electricity", "hardware_opportunity_cost"],
    }
    blinding = {
        "blinding_id": "PENDULUM_BLINDING_001",
        "mapping": {"BLIND_A91F": "DIRECT_CORPUS", "BLIND_C72D": "RAKL_CONTEXT"},
    }
    environment = {
        "environment_id": "TEST_ENV_V1",
        "python": "3.11.13",
        "packages": {"torch": "2.8.0", "transformers": "4.55.0"},
        "platform": {
            "os": platform.system(),
            "architecture": platform.machine(),
            "execution_device": "CPU",
            "network_during_execution": "disabled",
        },
    }

    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    model_file = snapshot / "model.safetensors"
    tokenizer_file = snapshot / "tokenizer.json"
    model_file.write_bytes(b"frozen-model")
    tokenizer_file.write_bytes(b"frozen-tokenizer")
    model_manifest = {
        "provider": "local_transformers",
        "model_id": "open-test-model",
        "revision": "1" * 40,
        "snapshot_path": str(snapshot),
        "trust_remote_code": False,
        "local_files_only": True,
        "files": [
            {"path": "model.safetensors", "sha256": _sha256(model_file), "bytes": model_file.stat().st_size}
        ],
    }
    tokenizer_manifest = {
        "model_id": "open-test-model",
        "revision": "1" * 40,
        "files": [
            {"path": "tokenizer.json", "sha256": _sha256(tokenizer_file), "bytes": tokenizer_file.stat().st_size}
        ],
    }
    execution_contract = {
        "schema_version": "paper2-lunarc-execution-contract-v1",
        "execution_site": "TEST_LUNARC_FIXTURE",
        "forbidden_login_host_prefix": "test-cosmos",
        "fs9_root": "/",
        "repo_path": str(ROOT),
        "output_root": str(tmp_path),
        "model_snapshot_path": str(snapshot),
        "require_clean_checkout": True,
        "require_subject_ancestor": True,
        "require_exact_bound_artifacts": True,
        "require_slurm_job_id": True,
    }

    values = {
        "task": task,
        "questions": questions,
        "evaluator": evaluator,
        "resources": resources,
        "prices": prices,
        "blinding": blinding,
        "environment": environment,
        "model_manifest": model_manifest,
        "tokenizer_manifest": tokenizer_manifest,
        "execution_contract": execution_contract,
    }
    paths: dict[str, Path] = {"system_prompt": system_prompt}
    for name, value in values.items():
        paths[name] = tmp_path / f"{name}.json"
        _write_json(paths[name], value)

    prompts = materialize_prompts(task, questions, system_prompt.read_text(encoding="utf-8"))
    paths["direct_prompt"] = tmp_path / "direct_prompt.txt"
    paths["rakl_prompt"] = tmp_path / "rakl_prompt.txt"
    paths["direct_prompt"].write_text(prompts["DIRECT_CORPUS"], encoding="utf-8")
    paths["rakl_prompt"].write_text(prompts["RAKL_CONTEXT"], encoding="utf-8")

    runner = ROOT / "src" / "rakl" / "paper2_pendulum_microtrial.py"
    result_schema = tmp_path / "result.schema.json"
    _write_json(result_schema, {"$schema": "https://json-schema.org/draft/2020-12/schema"})
    paths["runner"] = runner
    paths["result_schema"] = result_schema

    bindings = {
        name: {"path": str(path), "sha256": _sha256(path)}
        for name, path in paths.items()
    }
    packet = {
        "schema_version": "paper2-pendulum-microtrial-execution-v1",
        "protocol_id": "PENDULUM_MATCHED_SAME_MODEL_MICROTRIAL_001_EXECUTION_V1",
        "subject_sha": "a" * 40,
        "evaluated_results_opened_before_freeze": False,
        "status": "FROZEN_READY_NOT_EXECUTED",
        "claim_boundary": "Non-confirmatory engineering microtrial; no general superiority claim.",
        "arms": ["DIRECT_CORPUS", "RAKL_CONTEXT"],
        "bindings": bindings,
    }
    packet_path = tmp_path / "packet.json"
    _write_json(packet_path, packet)
    return packet_path, packet


def test_complete_hash_bound_local_packet_passes_semantic_preflight(tmp_path: Path) -> None:
    _, packet = _complete_fixture(tmp_path)

    report = audit_execution_packet(
        packet,
        base_dir=tmp_path,
        runtime_versions={"python": "3.11.13", "torch": "2.8.0", "transformers": "4.55.0"},
    )

    assert report.verdict is MicrotrialPreflightVerdict.PASS
    assert report.blockers == ()
    assert report.invalid_bindings == ()
    assert report.evaluated_result_record_count == 0


def test_semantic_preflight_rejects_placeholders_before_model_access(tmp_path: Path) -> None:
    _, packet = _complete_fixture(tmp_path)
    packet["protocol_id"] = "TO_BE_PINNED_BEFORE_EXECUTION"

    report = audit_execution_packet(packet, base_dir=tmp_path, runtime_versions={})

    assert report.verdict is MicrotrialPreflightVerdict.REJECT
    assert any(item.startswith("placeholder_forbidden:") for item in report.invalid_bindings)
    assert report.evaluated_result_record_count == 0


def test_semantic_preflight_rejects_placeholder_inside_bound_task(tmp_path: Path) -> None:
    _, packet = _complete_fixture(tmp_path)
    task_path = Path(packet["bindings"]["task"]["path"])
    task = json.loads(task_path.read_text(encoding="utf-8"))
    task["sources"][0]["text"] = "TBD"
    _write_json(task_path, task)
    packet["bindings"]["task"]["sha256"] = _sha256(task_path)

    report = audit_execution_packet(packet, base_dir=tmp_path, runtime_versions={})

    assert report.verdict is MicrotrialPreflightVerdict.REJECT
    assert any(item.startswith("placeholder_forbidden:artifact.task") for item in report.invalid_bindings)


def test_semantic_preflight_rejects_incomplete_mandatory_evidence(tmp_path: Path) -> None:
    _, packet = _complete_fixture(tmp_path)
    task_path = Path(packet["bindings"]["task"]["path"])
    task = json.loads(task_path.read_text(encoding="utf-8"))
    task["mandatory_evidence_ids"].append("S_MISSING")
    _write_json(task_path, task)
    packet["bindings"]["task"]["sha256"] = _sha256(task_path)

    report = audit_execution_packet(packet, base_dir=tmp_path, runtime_versions={})

    assert report.verdict is MicrotrialPreflightVerdict.REJECT
    assert "mandatory_evidence_missing:S_MISSING" in report.invalid_bindings


def test_semantic_preflight_rejects_mutated_evaluator_source(tmp_path: Path) -> None:
    _, packet = _complete_fixture(tmp_path)
    evaluator_path = Path(packet["bindings"]["evaluator"]["path"])
    evaluator = json.loads(evaluator_path.read_text(encoding="utf-8"))
    Path(evaluator["implementation_source_path"]).write_text("# evaluator changed\n", encoding="utf-8")

    report = audit_execution_packet(packet, base_dir=tmp_path, runtime_versions={})

    assert report.verdict is MicrotrialPreflightVerdict.REJECT
    assert "evaluator_implementation_sha256_mismatch" in report.invalid_bindings


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("output_root", "DOTDOT", "execution_contract_path_contains_dotdot:output_root"),
        ("repo_path", "/tmp/outside-checkout", "execution_contract_assets_outside_fs9_root"),
    ],
)
def test_semantic_preflight_rejects_execution_path_escape(
    tmp_path: Path, field: str, value: str, expected: str
) -> None:
    _, packet = _complete_fixture(tmp_path)
    contract_path = Path(packet["bindings"]["execution_contract"]["path"])
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract[field] = (
        str(tmp_path / "runs" / ".." / "escape") if value == "DOTDOT" else value
    )
    if field == "repo_path":
        contract["fs9_root"] = str(tmp_path)
    _write_json(contract_path, contract)
    packet["bindings"]["execution_contract"]["sha256"] = _sha256(contract_path)

    report = audit_execution_packet(packet, base_dir=tmp_path, runtime_versions={})

    assert report.verdict is MicrotrialPreflightVerdict.REJECT
    assert expected in report.invalid_bindings


def test_semantic_preflight_blocks_runtime_platform_mismatch(tmp_path: Path) -> None:
    _, packet = _complete_fixture(tmp_path)
    environment_path = Path(packet["bindings"]["environment"]["path"])
    environment = json.loads(environment_path.read_text(encoding="utf-8"))
    environment["platform"]["os"] = "ImpossibleOS"
    _write_json(environment_path, environment)
    packet["bindings"]["environment"]["sha256"] = _sha256(environment_path)

    report = audit_execution_packet(
        packet,
        base_dir=tmp_path,
        runtime_versions={"python": "3.11.13", "torch": "2.8.0", "transformers": "4.55.0"},
    )

    assert report.verdict is MicrotrialPreflightVerdict.CANNOT_CHECK
    assert any(item.startswith("runtime_platform_mismatch:os:") for item in report.blockers)


def test_materializers_change_only_registered_context_intervention(tmp_path: Path) -> None:
    _, packet = _complete_fixture(tmp_path)
    bindings = packet["bindings"]
    task = json.loads(Path(bindings["task"]["path"]).read_text(encoding="utf-8"))
    questions = json.loads(Path(bindings["questions"]["path"]).read_text(encoding="utf-8"))
    system_prompt = Path(bindings["system_prompt"]["path"]).read_text(encoding="utf-8")

    prompts = materialize_prompts(task, questions, system_prompt)

    assert set(prompts) == {"DIRECT_CORPUS", "RAKL_CONTEXT"}
    for source in task["sources"]:
        assert source["source_id"] in prompts["DIRECT_CORPUS"]
        assert source["text"] in prompts["DIRECT_CORPUS"]
        assert source["source_id"] in prompts["RAKL_CONTEXT"]
        assert source["text"] in prompts["RAKL_CONTEXT"]
    assert "RAKL CONTEXT MAP" not in prompts["DIRECT_CORPUS"]
    assert "RAKL CONTEXT MAP" in prompts["RAKL_CONTEXT"]
    assert "TOOLS: disabled" in prompts["DIRECT_CORPUS"]
    assert "TOOLS: disabled" in prompts["RAKL_CONTEXT"]


def test_local_backend_wraps_registered_prompt_in_model_chat_template() -> None:
    class FakeTokenizer:
        def __init__(self) -> None:
            self.calls: list[tuple[object, object]] = []

        def apply_chat_template(self, messages: object, **kwargs: object) -> dict[str, object]:
            self.calls.append((messages, kwargs))
            return {"input_ids": "encoded", "attention_mask": "mask"}

    tokenizer = FakeTokenizer()

    encoded = _encode_prompt_for_generation(tokenizer, "registered prompt")

    assert encoded == {"input_ids": "encoded", "attention_mask": "mask"}
    messages, kwargs = tokenizer.calls[0]
    assert messages == [{"role": "user", "content": "registered prompt"}]
    assert kwargs == {
        "add_generation_prompt": True,
        "tokenize": True,
        "return_tensors": "pt",
        "return_dict": True,
    }


def test_offline_execution_preserves_raw_outputs_resources_and_blinded_scoring(tmp_path: Path) -> None:
    packet_path, _ = _complete_fixture(tmp_path)
    answer = json.dumps(
        {
            "small_angle_is_asymptotic": True,
            "finite_amplitude_increases_period": True,
            "context_distinct_claims_not_direct_contradictions": True,
            "ideal_period_is_mass_invariant": True,
            "context_alignment_required_before_contradiction": True,
            "supporting_source_ids": ["S1", "S2"],
            "rejected_as_misaligned_source_ids": [],
            "refuted_source_ids": [],
        },
        sort_keys=True,
    )

    def fake_backend(prompt: str, **_: object) -> BackendGeneration:
        return BackendGeneration(
            raw_text=answer,
            input_tokens=len(prompt.split()),
            output_tokens=len(answer.split()),
            backend_version="fake-local-v1",
            wall_time_ms=7,
            peak_rss_bytes=123456,
        )

    output = tmp_path / "run"
    execute_microtrial(
        packet_path,
        output,
        created_at_utc="2026-08-10T23:00:00Z",
        backend=fake_backend,
        runtime_versions={"python": "3.11.13", "torch": "2.8.0", "transformers": "4.55.0"},
        checkout_probe=lambda *_: ExecutionCheckoutState(
            repo_path=str(ROOT),
            head_sha="b" * 40,
            tree_sha="c" * 40,
            clean=True,
            subject_ancestor=True,
        ),
        execution_host="test-compute-01",
        scheduler_job_id="123456",
    )

    raw_records = [json.loads(path.read_text(encoding="utf-8")) for path in sorted((output / "raw_outputs").glob("*.json"))]
    blinded = json.loads((output / "blinded_scores.json").read_text(encoding="utf-8"))
    result = json.loads((output / "result_receipt.json").read_text(encoding="utf-8"))
    Draft202012Validator(
        json.loads(RESULT_SCHEMA.read_text(encoding="utf-8")),
        format_checker=FormatChecker(),
    ).validate(result)
    assert len(raw_records) == 2
    assert all(record["raw_text"] == answer for record in raw_records)
    assert all("condition" not in record for record in raw_records)
    assert all("condition" not in item for item in blinded["scores"])
    assert {record["condition"] for record in result["records"]} == {"DIRECT_CORPUS", "RAKL_CONTEXT"}
    assert all(record["provider_receipt"]["local_files_only"] is True for record in result["records"])
    assert all(record["provider_receipt"]["tools_enabled"] is False for record in result["records"])
    assert all(record["provider_receipt"]["repo_access_exposed_to_model"] is False for record in result["records"])
    assert all(record["resource_receipt"]["tool_calls"] == 0 for record in result["records"])
    assert all(record["resource_receipt"]["retrieval_calls"] == 0 for record in result["records"])
    run_manifest = json.loads((output / "run_manifest.json").read_text(encoding="utf-8"))
    run_manifest_sha = _sha256(output / "run_manifest.json")
    assert run_manifest["model_outputs_opened_before_manifest"] is False
    assert run_manifest["execution_checkout"]["clean"] is True
    assert run_manifest["execution_checkout"]["head_sha"] == "b" * 40
    assert run_manifest["execution_checkout"]["tree_sha"] == "c" * 40
    assert run_manifest["scheduler_job_id"] == "123456"
    assert result["run_manifest_sha256"] == run_manifest_sha
    assert blinded["run_manifest_sha256"] == run_manifest_sha
    assert result["execution_checkout"] == run_manifest["execution_checkout"]
    assert all(record["raw_output"]["run_manifest_sha256"] == run_manifest_sha for record in result["records"])
    assert all(record["provider_receipt"]["run_manifest_sha256"] == run_manifest_sha for record in result["records"])
    assert all(record["resource_receipt"]["run_manifest_sha256"] == run_manifest_sha for record in result["records"])
    assert result["claim_boundary"]["confirmatory"] is False
    assert result["claim_boundary"]["general_superiority_permitted"] is False


def test_execution_rejects_resource_receipt_above_frozen_memory_ceiling(tmp_path: Path) -> None:
    packet_path, _ = _complete_fixture(tmp_path)

    def excessive_backend(prompt: str, **_: object) -> BackendGeneration:
        return BackendGeneration(
            raw_text="{}",
            input_tokens=len(prompt.split()),
            output_tokens=1,
            backend_version="fake-local-v1",
            wall_time_ms=1,
            peak_rss_bytes=1000001,
        )

    with pytest.raises(RuntimeError, match="peak memory ceiling exceeded"):
        execute_microtrial(
            packet_path,
            tmp_path / "too-large",
            created_at_utc="2026-08-10T23:00:00Z",
            backend=excessive_backend,
            runtime_versions={"python": "3.11.13", "torch": "2.8.0", "transformers": "4.55.0"},
            checkout_probe=lambda *_: ExecutionCheckoutState(
                repo_path=str(ROOT),
                head_sha="b" * 40,
                tree_sha="c" * 40,
                clean=True,
                subject_ancestor=True,
            ),
            execution_host="test-compute-01",
            scheduler_job_id="123456",
        )


def test_execution_refuses_dirty_checkout_before_model_or_output_access(tmp_path: Path) -> None:
    packet_path, _ = _complete_fixture(tmp_path)
    backend_calls: list[str] = []

    def forbidden_backend(prompt: str, **_: object) -> BackendGeneration:
        backend_calls.append(prompt)
        raise AssertionError("backend must not be called")

    output = tmp_path / "dirty-run"
    with pytest.raises(RuntimeError, match="execution checkout is not clean"):
        execute_microtrial(
            packet_path,
            output,
            created_at_utc="2026-08-10T23:00:00Z",
            backend=forbidden_backend,
            runtime_versions={"python": "3.11.13", "torch": "2.8.0", "transformers": "4.55.0"},
            checkout_probe=lambda *_: ExecutionCheckoutState(
                repo_path=str(ROOT),
                head_sha="b" * 40,
                tree_sha="c" * 40,
                clean=False,
                subject_ancestor=True,
            ),
            execution_host="test-compute-01",
            scheduler_job_id="123456",
        )

    assert backend_calls == []
    assert not output.exists()


def test_execution_refuses_when_runner_is_not_loaded_from_registered_checkout(tmp_path: Path) -> None:
    packet_path, packet = _complete_fixture(tmp_path)
    execution_path = Path(packet["bindings"]["execution_contract"]["path"])
    execution = json.loads(execution_path.read_text(encoding="utf-8"))
    execution["repo_path"] = str(tmp_path / "different-checkout")
    _write_json(execution_path, execution)
    packet["bindings"]["execution_contract"]["sha256"] = _sha256(execution_path)
    _write_json(packet_path, packet)

    with pytest.raises(RuntimeError, match="runner checkout path"):
        execute_microtrial(
            packet_path,
            tmp_path / "wrong-runner",
            created_at_utc="2026-08-10T23:00:00Z",
            backend=lambda *_args, **_kwargs: pytest.fail("backend must not be called"),
            runtime_versions={"python": "3.11.13", "torch": "2.8.0", "transformers": "4.55.0"},
            checkout_probe=lambda *_: ExecutionCheckoutState(
                repo_path=str(tmp_path / "different-checkout"),
                head_sha="b" * 40,
                tree_sha="c" * 40,
                clean=True,
                subject_ancestor=True,
            ),
            execution_host="test-compute-01",
            scheduler_job_id="123456",
        )


def test_execution_refuses_lunarc_login_node_or_missing_slurm_allocation(tmp_path: Path) -> None:
    packet_path, _ = _complete_fixture(tmp_path)
    checkout = lambda *_: ExecutionCheckoutState(
        repo_path=str(ROOT),
        head_sha="b" * 40,
        tree_sha="c" * 40,
        clean=True,
        subject_ancestor=True,
    )
    for output, host, job, expected in (
        (tmp_path / "login", "test-cosmos-01", "123456", "login host"),
        (tmp_path / "no-slurm", "test-compute-01", None, "SLURM job"),
    ):
        with pytest.raises(RuntimeError, match=expected):
            execute_microtrial(
                packet_path,
                output,
                created_at_utc="2026-08-10T23:00:00Z",
                backend=lambda *_args, **_kwargs: pytest.fail("backend must not be called"),
                runtime_versions={"python": "3.11.13", "torch": "2.8.0", "transformers": "4.55.0"},
                checkout_probe=checkout,
                execution_host=host,
                scheduler_job_id=job,
            )


def test_preflight_receipt_never_claims_empirical_authority(tmp_path: Path) -> None:
    _, packet = _complete_fixture(tmp_path)
    snapshot = Path(json.loads(Path(packet["bindings"]["model_manifest"]["path"]).read_text())["snapshot_path"])
    (snapshot / "model.safetensors").unlink()
    report = audit_execution_packet(packet, base_dir=tmp_path, runtime_versions={})
    output = tmp_path / "preflight.json"

    write_preflight_receipt(
        report,
        packet=packet,
        output_path=output,
        created_at_utc="2026-08-10T22:30:00Z",
    )

    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["receipt_type"] == "paper2_microtrial_execution_preflight_not_result"
    assert receipt["verdict"] == "CANNOT_CHECK"
    assert receipt["evaluated_result_record_count"] == 0
    assert receipt["empirical_claim_permitted"] is False


def test_repository_packet_binds_every_mandatory_microtrial_identity() -> None:
    packet = json.loads(FROZEN_PACKET.read_text(encoding="utf-8"))

    assert packet["arms"] == ["DIRECT_CORPUS", "RAKL_CONTEXT"]
    assert set(packet["bindings"]) == {
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
    }
    for binding in packet["bindings"].values():
        path = ROOT / binding["path"]
        assert path.is_file()
        assert _sha256(path) == binding["sha256"]


def test_repository_packet_has_no_semantic_placeholder_or_missing_evidence() -> None:
    packet = json.loads(FROZEN_PACKET.read_text(encoding="utf-8"))

    report = audit_execution_packet(packet, base_dir=ROOT, runtime_versions={})

    assert report.invalid_bindings == ()
    assert report.verdict is MicrotrialPreflightVerdict.CANNOT_CHECK
    assert any(item.startswith("local_model_file_missing:model.safetensors") for item in report.blockers)
    assert report.evaluated_result_record_count == 0


def test_repository_task_model_seed_and_blinding_are_frozen_as_registered() -> None:
    packet = json.loads(FROZEN_PACKET.read_text(encoding="utf-8"))

    def bound_json(name: str) -> dict[str, object]:
        return json.loads((ROOT / packet["bindings"][name]["path"]).read_text(encoding="utf-8"))

    task = bound_json("task")
    resources = bound_json("resources")
    evaluator = bound_json("evaluator")
    model = bound_json("model_manifest")
    tokenizer = bound_json("tokenizer_manifest")
    execution = bound_json("execution_contract")
    blinding = bound_json("blinding")
    assert [source["source_id"] for source in task["sources"]] == [f"S{i}" for i in range(1, 9)]
    assert task["mandatory_evidence_ids"] == [f"S{i}" for i in range(1, 9)]
    assert resources["seed"] == 17
    assert resources["max_tool_calls"] == 0
    assert resources["max_retrieval_calls"] == 0
    assert model["model_id"] == "Qwen/Qwen2.5-0.5B-Instruct"
    assert model["revision"] == "7ae557604adf67be50417f59c2c2f167def9a775"
    assert tokenizer["revision"] == model["revision"]
    revision = model["revision"]
    assert execution["fs9_root"] == "/projects/hep/fs9/users/scyiu/RAKL-paper2"
    assert execution["repo_path"] == "/projects/hep/fs9/users/scyiu/RAKL-paper2/repo"
    assert execution["output_root"] == "/projects/hep/fs9/users/scyiu/RAKL-paper2/runs"
    assert execution["forbidden_login_host_prefix"] == "cosmos"
    assert execution["require_slurm_job_id"] is True
    assert model["snapshot_path"] == (
        "/projects/hep/fs9/users/scyiu/RAKL-paper2/models/"
        f"Qwen--Qwen2.5-0.5B-Instruct/{revision}"
    )
    assert execution["model_snapshot_path"] == model["snapshot_path"]
    evaluator_source = ROOT / evaluator["implementation_source_path"]
    assert evaluator_source.is_file()
    assert _sha256(evaluator_source) == evaluator["implementation_source_sha256"]
    assert set(blinding["mapping"].values()) == {"DIRECT_CORPUS", "RAKL_CONTEXT"}
    assert all("DIRECT" not in blind_id and "RAKL" not in blind_id for blind_id in blinding["mapping"])


def test_repository_result_schema_requires_receipt_lineage_and_raw_output() -> None:
    schema = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))
    run_required = set(schema["$defs"]["run"]["required"])

    assert {"blind_id", "condition", "raw_output", "provider_receipt", "resource_receipt", "score"} <= run_required
    assert {"run_manifest_sha256", "execution_checkout"} <= set(schema["required"])
    assert "run_manifest_sha256" in schema["$defs"]["raw_output"]["required"]
    assert "run_manifest_sha256" in schema["$defs"]["provider_receipt"]["required"]
    assert "run_manifest_sha256" in schema["$defs"]["resource_receipt"]["required"]
    assert schema["properties"]["claim_boundary"]["properties"]["confirmatory"]["const"] is False
    assert schema["properties"]["claim_boundary"]["properties"]["general_superiority_permitted"]["const"] is False


def test_repository_preflight_receipt_is_zero_result_and_nonempirical() -> None:
    receipt = json.loads(FROZEN_PREFLIGHT.read_text(encoding="utf-8"))

    assert receipt["receipt_type"] == "paper2_microtrial_execution_preflight_not_result"
    assert receipt["verdict"] == "CANNOT_CHECK"
    assert receipt["evaluated_result_record_count"] == 0
    assert receipt["empirical_claim_permitted"] is False


def test_microtrial_status_does_not_overstate_unexecuted_engineering_lane() -> None:
    text = MANUSCRIPT_STATUS.read_text(encoding="utf-8")

    assert "999,597,690 bytes" in text
    assert "non-confirmatory engineering microtrial" in text
    assert "not been downloaded or executed" in text
    assert "does not establish RAKL superiority" in text
    assert "CANNOT_CHECK" in text
