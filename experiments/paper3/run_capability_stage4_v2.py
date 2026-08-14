from __future__ import annotations

from collections import defaultdict
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_capability_stage4_v1 as V1  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SCORING_SPEC = (
    ROOT
    / "research"
    / "empirical_10_of_10_v1"
    / "CAPABILITY_QUALIFICATION"
    / "STAGE3_5_SCORING_HARDENING_V2.json"
)


def _score(tasks: list[dict], records: list[dict], freeze: dict) -> dict:
    """Hardened Stage-5 scorer.

    Unlike v1, no scientific error may remove itself from a hard-metric
    denominator merely by returning an incomplete evidence partition. JSON/schema
    parsing and evidence-partition validity are tracked separately; the published
    ``parse_validity`` gate means a complete structured readout, as required by
    the frozen Stage-2 interface.
    """

    by_task = {record["task_id"]: record for record in records}
    raw_parsed_n = structured_valid_n = exact_n = 0
    support_num = support_den = reject_num = reject_den = 0
    cc_tp = cc_gold = cc_pred = 0
    context_errors = context_total = 0
    family_exact: dict[str, list[int]] = defaultdict(list)

    for task in tasks:
        record = by_task[task["task_id"]]
        parsed = record.get("parsed")
        gold = task["gold"]
        supplied = V1._evidence_ids(task["prompt"])
        gold_sel = set(gold["selected_evidence_ids"])
        gold_rej = set(gold["rejected_evidence_ids"])

        # Gold denominators are unconditional on model behavior.
        support_den += len(gold_sel)
        reject_den += len(gold_rej)
        if gold["verdict"] == "CANNOT_CHECK":
            cc_gold += 1
        if task["family"] == "CONTEXT_QOI_NEAR_MISS":
            context_total += 1

        pred_sel: set[str] = set()
        pred_rej: set[str] = set()
        pred_verdict: str | None = None
        partition_total = False
        if parsed is not None:
            raw_parsed_n += 1
            pred_sel = set(parsed["selected_evidence_ids"])
            pred_rej = set(parsed["rejected_evidence_ids"])
            pred_verdict = parsed["verdict"]
            partition_total = (
                pred_sel.isdisjoint(pred_rej)
                and pred_sel | pred_rej == supplied
                and pred_sel <= supplied
                and pred_rej <= supplied
            )
            if partition_total:
                structured_valid_n += 1
            else:
                record.setdefault("parse_reasons", []).append(
                    "evidence_partition_not_total"
                )

            # Evidence-ID fidelity counts all gold IDs even on malformed output.
            support_num += len(pred_sel & gold_sel)
            reject_num += len(pred_rej & gold_rej)

            # Verdict precision counts every parsed prediction, malformed binding
            # included, because a wrong CANNOT_CHECK cannot erase itself.
            if pred_verdict == "CANNOT_CHECK":
                cc_pred += 1

        if gold["verdict"] == "CANNOT_CHECK" and pred_verdict == "CANNOT_CHECK":
            cc_tp += 1
        if task["family"] == "CONTEXT_QOI_NEAR_MISS":
            context_errors += pred_verdict != "CONTEXT_MISALIGNED"

        exact = bool(
            parsed is not None
            and partition_total
            and pred_verdict == gold["verdict"]
            and pred_sel == gold_sel
            and pred_rej == gold_rej
        )
        exact_n += int(exact)
        family_exact[task["family"]].append(int(exact))
        record["joint_exact"] = exact
        record["evidence_partition_total"] = partition_total

    n = len(tasks)
    metrics = {
        "n": n,
        "raw_json_schema_parse_validity": raw_parsed_n / n,
        "parse_validity": structured_valid_n / n,
        "parse_validity_ci95": V1._wilson(structured_valid_n, n),
        "exact_joint_verdict_and_binding": exact_n / n,
        "exact_joint_ci95": V1._wilson(exact_n, n),
        "support_id_recall": support_num / max(1, support_den),
        "reject_id_recall": reject_num / max(1, reject_den),
        "context_qoi_error_rate": context_errors / max(1, context_total),
        "cannot_check_recall": cc_tp / max(1, cc_gold),
        "cannot_check_precision": cc_tp / max(1, cc_pred),
        "family_exact": {
            family: sum(rows) / len(rows)
            for family, rows in sorted(family_exact.items())
        },
        "scoring_contract": "STAGE3_5_SCORING_HARDENING_V2",
    }
    gate = freeze["vector_gate"]
    metrics["all_vector_gates_pass"] = (
        metrics["parse_validity"] >= gate["parse_validity_min"]
        and metrics["exact_joint_verdict_and_binding"]
        >= gate["exact_joint_verdict_and_binding_min"]
        and metrics["support_id_recall"] >= gate["support_id_recall_min"]
        and metrics["reject_id_recall"] >= gate["reject_id_recall_min"]
        and metrics["context_qoi_error_rate"] <= gate["context_qoi_error_max"]
        and metrics["cannot_check_recall"] >= gate["cannot_check_recall_min"]
        and metrics["cannot_check_precision"] >= gate["cannot_check_precision_min"]
        and min(metrics["family_exact"].values()) >= gate["family_min_exact"]
    )
    return metrics


def _annotate_receipt(outdir: Path) -> None:
    path = outdir / "FINAL_CAPABILITY_RECEIPT.json"
    if not path.exists():
        return
    receipt = json.loads(path.read_text())
    spec_bytes = SCORING_SPEC.read_bytes()
    receipt["schema_version"] = "rakl-capability-qualification-stage5-result-v2"
    receipt["scoring_hardening"] = {
        "spec": str(SCORING_SPEC.relative_to(ROOT)),
        "spec_sha256": hashlib.sha256(spec_bytes).hexdigest(),
        "contract": "malformed evidence partitions cannot escape hard-metric denominators",
        "thresholds_changed_from_v1": False,
        "panel_changed_from_v1": False,
        "model_or_interface_changed_from_v1": False,
    }
    path.write_text(json.dumps(receipt, indent=2) + "\n")


def run(outdir: Path, *, model_path: str | None, dry_run: bool = False) -> int:
    # V1 owns frozen panel materialization, parsing, model execution and receipt
    # mechanics. This version changes only the pre-outcome scorer under the
    # explicit V2 amendment above.
    original_score = V1._score
    try:
        V1._score = _score
        code = V1.run(outdir, model_path=model_path, dry_run=dry_run)
    finally:
        V1._score = original_score
    if not dry_run:
        _annotate_receipt(outdir)
    return code


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", type=Path, required=True)
    ap.add_argument("--model-path")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    raise SystemExit(run(args.outdir, model_path=args.model_path, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
