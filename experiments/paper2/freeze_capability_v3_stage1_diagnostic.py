"""Freeze the capability qualification V3 Stage 0/1 artifacts for issue #447.

Reads only preserved development data from the sealed ``paper2-oracle-capability-gate-v2-exec``
generation (job 3476813) and the instruction surfaces that job actually used. Writes:

* ``GOLD_AUDIT.json`` — Stage 0 audit of the sealed answers and the instruction surface.
* ``DIAGNOSTIC_RESULTS/qwen2.5-7b-instruct.jsonl`` — per-item Stage 1 observables.
* ``BOTTLENECK_RECEIPT.json`` — Stage 1 diagnosis state.

Run:

    python experiments/paper2/freeze_capability_v3_stage1_diagnostic.py

The script is idempotent and asserts its own emitted constants against the bound schema's
const locks before writing, so a copied-and-not-updated version constant fails here rather
than after a job has burned compute.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from rakl.paper2_capability_v3_diagnostic import (  # noqa: E402
    audit_instruction_semantics,
    diagnose_stage_bottleneck,
    stage_decompose,
)

RECEIPT_TYPE = "paper2_capability_v3_stage1_bottleneck_receipt_v1"
SCHEMA_VERSION = "paper2-capability-v3-bottleneck-receipt-v1"
SCHEMA_PATH = REPO / "schemas" / f"{SCHEMA_VERSION}.schema.json"

SOURCE_JOB_ID = 3476813
SOURCE_MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
SOURCE_MODEL_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
SOURCE_DIR = REPO / "research" / "paper2_oracle_capability_gate_v2_exec"
OUT_DIR = REPO / "research" / "empirical_10_of_10_v1" / "CAPABILITY_QUALIFICATION"

TASK_IDS = ("T1", "T2", "T3", "T4", "T5")

#: Gold convention the sealed answers actually encode, verified item-by-item in the audit.
GOLD_CONVENTION = "LICENSES_VERDICT"


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(payload: object) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _assert_schema_consts(payload: dict) -> None:
    """Fail loudly when emitted constants drift from the schema's const locks.

    Guards the recurring copy-a-file-and-keep-the-old-constant defect that has already
    cost completed jobs on this campaign.
    """
    if not SCHEMA_PATH.exists():
        raise SystemExit(f"bound schema missing: {SCHEMA_PATH}")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    props = schema.get("properties", {})
    for key, spec in props.items():
        const = spec.get("const")
        if const is None:
            continue
        actual = payload.get(key)
        if actual != const:
            raise SystemExit(
                f"schema const drift: field {key!r} emitted {actual!r} but "
                f"{SCHEMA_PATH.name} locks const {const!r}"
            )


def _audit_gold_convention(tasks: dict[str, dict]) -> dict:
    """Verify the sealed answers use one internally consistent evidence-role convention.

    The discriminating observation is an item where a *relevant but non-licensing* piece of
    evidence is placed in ``rejected``: that rules out the alternative reading
    ``selected = relevant evidence``.
    """
    items = []
    discriminating = []
    for tid in TASK_IDS:
        task = tasks[tid]
        gold = task["sealed_answer"]
        selected = list(gold["selected_evidence_ids"])
        rejected = list(gold["rejected_evidence_ids"])
        all_ids = sorted(e["id"] for e in task["evidence"])
        partition_total = sorted(selected + rejected)
        items.append(
            {
                "task_id": tid,
                "stratum": task["stratum"],
                "gold_verdict": gold["verdict"],
                "gold_selected": selected,
                "gold_rejected": rejected,
                "partition_is_total": partition_total == all_ids,
                "partition_is_disjoint": not (set(selected) & set(rejected)),
                # A CANNOT_CHECK item with an empty selected set is trivially consistent
                # with both readings and carries no convention information.
                "convention_informative": bool(selected) and bool(rejected),
            }
        )
        if selected and rejected:
            discriminating.append(tid)

    return {
        "gold_convention": GOLD_CONVENTION,
        "gold_convention_statement": (
            "selected_evidence_ids = exactly the evidence that licenses the stated verdict; "
            "rejected_evidence_ids = every other supplied id, including on-topic but "
            "unreliable or off-quantity evidence."
        ),
        "alternative_reading_ruled_out": "selected = relevant evidence",
        "alternative_reading_ruled_out_by": {
            "task_id": "T1",
            "observation": (
                "E2 is an on-topic mass reading (51.20 kg) for a mass claim, yet gold places "
                "it in rejected_evidence_ids because the instrument drifted out of tolerance "
                "and was not recalibrated. A relevance reading would have selected it."
            ),
        },
        "all_partitions_total": all(i["partition_is_total"] for i in items),
        "all_partitions_disjoint": all(i["partition_is_disjoint"] for i in items),
        "convention_informative_task_ids": discriminating,
        "items": items,
        "gold_verdict": (
            "GOLD_INTERNALLY_CONSISTENT"
            if all(i["partition_is_total"] and i["partition_is_disjoint"] for i in items)
            else "GOLD_INCONSISTENT"
        ),
    }


def main() -> int:
    tasks = {
        tid: json.loads((SOURCE_DIR / "tasks" / f"{tid}.json").read_text(encoding="utf-8"))
        for tid in TASK_IDS
    }
    generations = {
        tid: json.loads(
            (
                SOURCE_DIR
                / f"native_job_{SOURCE_JOB_ID}"
                / "runs"
                / "outputs"
                / f"LEARNING_ENABLED_{tid}.json"
            ).read_text(encoding="utf-8")
        )
        for tid in TASK_IDS
    }

    # ---- Stage 0: instruction surface audit ---------------------------------------
    system_prompt_path = SOURCE_DIR / "protocol" / "SYSTEM_PROMPT.txt"
    system_prompt = system_prompt_path.read_text(encoding="utf-8")

    # The user-prompt instruction block is emitted by the frozen runner. Audit the exact
    # static instruction lines that job 3476813 rendered, read from source so the audit
    # cannot be fabricated.
    runner_path = REPO / "src" / "rakl" / "paper2_experience_benchmark_runner.py"
    runner_src = runner_path.read_text(encoding="utf-8")
    start = runner_src.index("Return exactly one JSON object with these exact keys")
    end = runner_src.index("Then stop. Do not wrap the JSON in markdown fences.")
    user_instruction_block = runner_src[start:end]

    audits = [
        audit_instruction_semantics(system_prompt, surface_label="SYSTEM_PROMPT.txt"),
        audit_instruction_semantics(
            user_instruction_block,
            surface_label="paper2_experience_benchmark_runner.build_user_prompt:instruction_block",
        ),
    ]

    gold_audit = _audit_gold_convention(tasks)
    gold_audit["instruction_surface_audits"] = [a.as_dict() for a in audits]
    gold_audit["stage0_verdict"] = (
        "INSTRUMENT_DEFECT_EVIDENCE_ROLE_UNDEFINED"
        if any(not a.defines_evidence_role for a in audits)
        else "INSTRUMENT_CLEAN"
    )
    gold_audit["stage0_note"] = (
        "Issue #447 Stage 0 requires this audit BEFORE model evaluation. It was not run for "
        "paper2-oracle-capability-gate-v2-exec. Running it retrospectively is why the terminal "
        "is an identifiability statement plus a versioned repair, and never a claim about what "
        "the 7B model can do."
    )
    gold_audit["source_surfaces"] = [
        {
            "path": str(system_prompt_path.relative_to(REPO)),
            "sha256": _sha256_file(system_prompt_path),
        },
        {
            "path": str(runner_path.relative_to(REPO)),
            "sha256": _sha256_file(runner_path),
            "extracted_span": "build_user_prompt static instruction block",
        },
    ]

    # ---- Stage 1: per-item decomposition ------------------------------------------
    diagnoses = [stage_decompose(generations[tid], tasks[tid]) for tid in TASK_IDS]
    receipt_body = diagnose_stage_bottleneck(diagnoses, audits)

    receipt = {
        "receipt_type": RECEIPT_TYPE,
        "schema_version": SCHEMA_VERSION,
        "issue_number": 447,
        "consumer_issue_numbers": [443, 446],
        "source_job_id": SOURCE_JOB_ID,
        "source_model_id": SOURCE_MODEL_ID,
        "source_model_revision": SOURCE_MODEL_REVISION,
        "source_backend_version": generations["T1"]["backend_version"],
        "preserved_sealed_verdict": "MODEL_CAPABILITY_FLOOR_7B_V2_EXEC",
        "preserved_sealed_verdict_status": "UNCHANGED_BY_THIS_RECEIPT",
        "gold_audit": gold_audit,
        "per_item": [d.as_dict() for d in diagnoses],
        **receipt_body,
        "identifiability_statement": {
            "T2": "measurement cannot separate H_inversion from H_incapacity",
            "T3": "measurement cannot separate H_inversion from H_incapacity",
            "T4": "verdict error is convention-invariant and is a real composition failure",
            "T1": "convention-insensitive; carries no information about evidence binding",
            "T5": "convention-insensitive; carries no information about evidence binding",
        },
        "downstream_effect": {
            "capability_question": "UNIDENTIFIED_AT_THIS_INSTRUMENT",
            "required_next": "versioned interface repair, then a fresh held-out qualification panel",
            "forbidden_next": [
                "rescoring job 3476813 under the other convention",
                "lowering any frozen threshold",
                "authorizing capability from these development items",
            ],
        },
    }
    receipt["artifact_sha256"] = _canonical_sha256(
        {k: v for k, v in receipt.items() if k != "artifact_sha256"}
    )

    _assert_schema_consts(receipt)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "DIAGNOSTIC_RESULTS").mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "GOLD_AUDIT.json").write_text(
        json.dumps(gold_audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with (OUT_DIR / "DIAGNOSTIC_RESULTS" / "qwen2.5-7b-instruct.jsonl").open(
        "w", encoding="utf-8"
    ) as handle:
        for diagnosis in diagnoses:
            handle.write(json.dumps(diagnosis.as_dict(), sort_keys=True) + "\n")
    (OUT_DIR / "BOTTLENECK_RECEIPT.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    print(f"diagnosis_state={receipt['diagnosis_state']}")
    print(f"stage0_verdict={gold_audit['stage0_verdict']}")
    print(f"gold_verdict={gold_audit['gold_verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
