"""Build Wave 2 offline freeze and NO_NEW_GLM_OUTCOME receipts for GLM52 v1.1."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
_SUITE = _ROOT / "research" / "glm52_mechanism_suite_v1_1"
_V1 = _ROOT / "research" / "glm52_mechanism_suite_v1"
for path in (_ROOT / "src", _V1, _SUITE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from suite_common import file_sha256, stable_hash  # type: ignore[import-not-found]

PROTOCOL_ID = "GLM52-MECHANISM-SUITE-V1.1"
ISSUE_ID = 443
OUTCOME_ACCESS = "NO_NEW_GLM_OUTCOME"
SCHEMA_VERSION = "glm52-mechanism-suite-v1-1-wave2-freeze-receipt-v1"
OUTCOME_SCHEMA_VERSION = "glm52-mechanism-suite-v1-1-no-new-outcome-receipt-v1"

BOUND_WAVE2_ARTIFACTS: tuple[str, ...] = (
    "PROTOCOL_V1_1.md",
    "ARM_INTERVENTION_TABLE.json",
    "FRAMEWORK_SUBJECT_MANIFEST.json",
    "FRAMEWORK_ADAPTER_SPEC.md",
    "HOSTED_PROVIDER_CONFIG.json",
    "WAVE2_HANDOFF_LANES.md",
    "framework_adapter.py",
    "provider.py",
    "suite_common.py",
    "offline_selftest.py",
    "wave2_freeze.py",
    "harness/__init__.py",
    "harness/selective_retrieval_harness.py",
    "harness/experience_transfer_harness.py",
    "harness/trajectory_governance_harness.py",
    "harness_stubs/__init__.py",
    "harness_stubs/selective_retrieval_stub.py",
    "harness_stubs/experience_transfer_stub.py",
    "harness_stubs/trajectory_governance_stub.py",
    "src/rakl/hosted_anthropic_client.py",
)

EMPIRICAL_INSTRUMENT_BINDINGS: dict[str, Any] = {
    "schema_version": "glm52-paper2-paper3-empirical-instrument-bindings-v1",
    "protocol_id": PROTOCOL_ID,
    "issue": ISSUE_ID,
    "outcome_access_status": OUTCOME_ACCESS,
    "grants_scientific_authority": False,
    "paper2": {
        "matched_a3_a4_arms": {
            "module": "src/rakl/ablation_a3_a4_matched_empirical.py",
            "packet": "research/paper2_closest_parent/A3_A4_MATCHED_EMPIRICAL_PACKET_V1.json",
            "status_artifact": "research/paper2_closest_parent/A3_A4_MATCHED_EMPIRICAL_STATUS.json",
            "mode": "non_confirmatory_scaffold_only",
        },
        "microtrial_ingest_hooks": {
            "matched_microtrial": "src/rakl/matched_microtrial.py",
            "pendulum_v4_ingest": "src/rakl/paper2_pendulum_microtrial_v4_1.py",
            "native_ingest_schema": "schemas/paper2-v4-native-ingest-receipt.schema.json",
            "mode": "non_confirmatory_scaffold_only",
        },
    },
    "paper3": {
        "semantic_descriptor_builder": {
            "module": "src/rakl/paper3_strong_control.py",
            "builder": "build_semantic_descriptor_receipt",
            "pair_renderer": "canonical_semantic_pair",
            "lunarc_runtime": "experiments/paper3/lunarc/semantic_descriptor_runtime.py",
            "lunarc_contract": "research/paper3_semantic_descriptor_lunarc/CONTRACT_V1.json",
            "mode": "non_confirmatory_scaffold_only",
        },
    },
    "capability_qualification_blocker": {
        "receipt": "research/empirical_10_of_10_v1/CAPABILITY_QUALIFICATION/BOTTLENECK_RECEIPT.json",
        "diagnosis_state": "BENCHMARK_CONSTRUCT_DEFECT",
        "consumer_issue_numbers": [443, 446, 447],
    },
}

LIVE_RUN_BLOCKERS: tuple[str, ...] = (
    "outcome_access:NO_NEW_GLM_OUTCOME",
    "hosted_dev_gates:not_passed_on_live_model",
    "wave2_confirmatory_unlocked:false",
    "capable_model_authorize_receipt_v3:absent",
    "paper2_oracle_capability_gate_v2_exec:terminal_blocked",
    "confirmatory_glm_api_runs:explicit_operator_authorization_required",
)


def _repo_sha(repo_root: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()


def _artifact_path(repo_root: Path, rel: str) -> Path:
    if rel.startswith("src/"):
        return repo_root / rel
    return repo_root / "research" / "glm52_mechanism_suite_v1_1" / rel


def artifact_hashes(repo_root: Path) -> dict[str, str]:
    return {rel: file_sha256(_artifact_path(repo_root, rel)) for rel in BOUND_WAVE2_ARTIFACTS}


def _offline_lane_summaries() -> dict[str, Any]:
    from harness.experience_transfer_harness import run_offline_panel as run_experience
    from harness.selective_retrieval_harness import run_offline_panel as run_retrieval
    from harness.trajectory_governance_harness import run_offline_panel as run_governance

    retrieval = run_retrieval(phase="dev", n_per_cell=1, pressures=(32_000,))
    experience = run_experience(phase="dev", n_per_family=1)
    governance = run_governance(phase="dev", n_per_kind=1)
    return {
        "lane2_selective_retrieval": {
            "arms": list(retrieval["summary"]["arms"].keys()),
            "dev_gate_passes": retrieval["summary"]["dev_gate"]["passes"],
            "model_runs": retrieval["summary"]["model_runs"],
        },
        "lane3_experience_transfer": {
            "arms": list(experience["summary"]["arms"].keys()),
            "hostile_families": experience["summary"]["hostile_families"],
            "dev_gate_passes": experience["summary"]["dev_gate"]["passes"],
            "model_runs": experience["summary"]["model_runs"],
        },
        "lane4_trajectory_governance": {
            "arms": list(governance["summary"]["arms"].keys()),
            "dev_gate_passes": governance["summary"]["dev_gate"]["passes"],
            "noninferiority_stub": governance["summary"]["noninferiority"],
            "model_runs": governance["summary"]["model_runs"],
        },
    }


def build_wave2_freeze_receipt(
    repo_root: Path | None = None,
    *,
    frozen_at: str | None = None,
) -> dict[str, Any]:
    repo_root = repo_root or _ROOT
    suite = repo_root / "research" / "glm52_mechanism_suite_v1_1"
    from framework_adapter import CanonicalFrameworkAdapter  # type: ignore[import-not-found]

    adapter = CanonicalFrameworkAdapter(repo_root=repo_root)
    manifest = adapter.subject_manifest()
    hashes = artifact_hashes(repo_root)
    lanes = _offline_lane_summaries()
    return {
        "schema_version": SCHEMA_VERSION,
        "receipt_id": f"glm52-mechanism-suite-v1-1-wave2-freeze-{frozen_at or 'live'}",
        "protocol_id": PROTOCOL_ID,
        "protocol_version": "1.1.0",
        "issue": ISSUE_ID,
        "repo_sha": _repo_sha(repo_root),
        "receipt_frozen_at": frozen_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "frozen_before_hosted_outcomes": True,
        "evaluated_results_accessed": False,
        "model_runs": 0,
        "outcome_access_status": OUTCOME_ACCESS,
        "grants_scientific_authority": False,
        "framework_subject": manifest,
        "wave2_lanes": lanes,
        "artifact_file_sha256": {Path(rel).name: digest for rel, digest in hashes.items()},
        "artifacts": {
            Path(rel).name: (
                rel if rel.startswith("src/") else f"research/glm52_mechanism_suite_v1_1/{rel}"
            )
            for rel in BOUND_WAVE2_ARTIFACTS
        },
        "empirical_instrument_bindings": EMPIRICAL_INSTRUMENT_BINDINGS,
        "live_run_blockers": list(LIVE_RUN_BLOCKERS),
        "claim_boundary": (
            "Wave 2 offline harness scaffold only. Binds arm wiring, dev-gate proxies, "
            "hosted-provider config, and Paper II/III instrument hooks. Does not authorize "
            "confirmatory GLM API runs or grant mechanism-suite scientific authority."
        ),
        "receipt_subject_hash": stable_hash(
            {
                "artifact_hashes": hashes,
                "lanes": lanes,
                "outcome_access_status": OUTCOME_ACCESS,
            }
        ),
        "suite_dir": str(suite.relative_to(repo_root)),
    }


def build_no_new_glm_outcome_receipt(
    repo_root: Path | None = None,
    *,
    observed_at: str | None = None,
) -> dict[str, Any]:
    repo_root = repo_root or _ROOT
    freeze = build_wave2_freeze_receipt(repo_root)
    return {
        "schema_version": OUTCOME_SCHEMA_VERSION,
        "protocol_id": PROTOCOL_ID,
        "issue": ISSUE_ID,
        "observed_at": observed_at or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "outcome_access_status": OUTCOME_ACCESS,
        "model_runs": 0,
        "evaluated_results_accessed": False,
        "grants_scientific_authority": False,
        "credential_handling": {
            "env_only": True,
            "token_written_to_repo": False,
            "token_written_to_result_artifact": False,
        },
        "completed_offline": [
            "CanonicalFrameworkAdapter L1 binding",
            "Wave 2 lane 2 selective retrieval harness + stubs",
            "Wave 2 lane 3 experience transfer harness + hostile cases",
            "Wave 2 lane 4 trajectory governance harness + noninferiority stub",
            "hosted_anthropic_client claude-cn profile",
            "Paper II matched A3/A4 empirical scaffold hooks",
            "Paper II microtrial ingest scaffold hooks",
            "Paper III semantic descriptor builder hooks",
        ],
        "live_run_blockers": list(LIVE_RUN_BLOCKERS),
        "wave2_freeze_subject_hash": freeze["receipt_subject_hash"],
        "claim_boundary": freeze["claim_boundary"],
    }


def validate_committed_receipts(repo_root: Path | None = None) -> list[str]:
    repo_root = repo_root or _ROOT
    suite = repo_root / "research" / "glm52_mechanism_suite_v1_1"
    failures: list[str] = []
    freeze_path = suite / "WAVE2_FREEZE_RECEIPT.json"
    outcome_path = suite / "NO_NEW_GLM_OUTCOME_RECEIPT.json"
    bindings_path = suite / "EMPIRICAL_INSTRUMENT_BINDINGS.json"
    if not freeze_path.is_file():
        failures.append("missing WAVE2_FREEZE_RECEIPT.json")
    if not outcome_path.is_file():
        failures.append("missing NO_NEW_GLM_OUTCOME_RECEIPT.json")
    if not bindings_path.is_file():
        failures.append("missing EMPIRICAL_INSTRUMENT_BINDINGS.json")
    if failures:
        return failures

    live_freeze = build_wave2_freeze_receipt(repo_root)
    committed_freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if committed_freeze.get("receipt_subject_hash") != live_freeze["receipt_subject_hash"]:
        failures.append("WAVE2_FREEZE_RECEIPT.json receipt_subject_hash drift")
    for rel in BOUND_WAVE2_ARTIFACTS:
        name = Path(rel).name
        if committed_freeze.get("artifact_file_sha256", {}).get(name) != live_freeze["artifact_file_sha256"][name]:
            failures.append(f"artifact hash drift: {rel}")

    live_outcome = build_no_new_glm_outcome_receipt(repo_root)
    committed_outcome = json.loads(outcome_path.read_text(encoding="utf-8"))
    if committed_outcome.get("wave2_freeze_subject_hash") != live_outcome["wave2_freeze_subject_hash"]:
        failures.append("NO_NEW_GLM_OUTCOME_RECEIPT.json wave2_freeze_subject_hash drift")

    committed_bindings = json.loads(bindings_path.read_text(encoding="utf-8"))
    if committed_bindings != EMPIRICAL_INSTRUMENT_BINDINGS:
        failures.append("EMPIRICAL_INSTRUMENT_BINDINGS.json drift")
    return failures


def write_committed_receipts(repo_root: Path | None = None) -> dict[str, Path]:
    repo_root = repo_root or _ROOT
    suite = repo_root / "research" / "glm52_mechanism_suite_v1_1"
    frozen_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    freeze = build_wave2_freeze_receipt(repo_root, frozen_at=frozen_at)
    outcome = build_no_new_glm_outcome_receipt(repo_root, observed_at=frozen_at[:10])
    paths = {
        "wave2_freeze": suite / "WAVE2_FREEZE_RECEIPT.json",
        "no_new_outcome": suite / "NO_NEW_GLM_OUTCOME_RECEIPT.json",
        "instrument_bindings": suite / "EMPIRICAL_INSTRUMENT_BINDINGS.json",
    }
    paths["wave2_freeze"].write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    paths["no_new_outcome"].write_text(json.dumps(outcome, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    paths["instrument_bindings"].write_text(
        json.dumps(EMPIRICAL_INSTRUMENT_BINDINGS, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return paths


def main() -> int:
    from harness.experience_transfer_harness import offline_selftest as experience_test
    from harness.selective_retrieval_harness import offline_selftest as retrieval_test
    from harness.trajectory_governance_harness import offline_selftest as governance_test

    retrieval_test()
    experience_test()
    governance_test()
    write_committed_receipts()
    failures = validate_committed_receipts()
    if failures:
        raise SystemExit("\n".join(failures))
    print("glm52 v1.1 wave2 freeze receipts: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
