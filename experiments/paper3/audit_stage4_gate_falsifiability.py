#!/usr/bin/env python3
"""Can the Stage-4 capability gate fail before it consumes a confirmatory budget?

Self-RAKL. Grants no authority.

The Stage-4 vector gate (issue #447) is the gate that stands between the Paper
III fresh-task-lift lane and its next confirmatory budget: nothing downstream
runs until a model clears it. The Paper II lane spent a full confirmatory run on
a gate that was structurally incapable of failing, and the Paper III
experience-to-action gate turned out to score a candidate against gold the
candidate itself wrote. So this gate is probed *before* it is trusted, not after.

Unlike the experience-to-action gate, this one consumes model output and
compares it against panel gold built by a separate generator, so it has no
structural reason to be dead. That is a prediction, and this audit is how the
prediction gets checked rather than assumed.

The control is asserted first: an oracle responder that echoes gold must PASS,
otherwise every subsequent NON_FALSIFIABLE verdict would be vacuous.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import random
import sys
from typing import Any, Callable, Sequence

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments" / "paper3"))

from rakl.gate_falsifiability import (  # noqa: E402
    GateFalsifiability,
    audit_gate,
    shuffle_field,
)

FREEZE_PATH = (
    ROOT
    / "research"
    / "empirical_10_of_10_v1"
    / "CAPABILITY_QUALIFICATION"
    / "STAGE3_5_FREEZE_V1.json"
)


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PANEL = _load("stage4_panel", ROOT / "experiments" / "paper3" / "build_capability_stage4_panel_v1.py")
RUNNER = _load("stage4_runner", ROOT / "experiments" / "paper3" / "run_capability_stage4_v1.py")


def oracle_records(tasks: Sequence[dict]) -> list[dict]:
    """A responder that answers every task exactly right.

    This is the *control*, not a result. If the gate does not pass for a perfect
    responder it is mis-specified, and probing it would tell us nothing.
    """
    return [
        {
            "task_id": task["task_id"],
            "parsed": {
                "verdict": task["gold"]["verdict"],
                "selected_evidence_ids": list(task["gold"]["selected_evidence_ids"]),
                "rejected_evidence_ids": list(task["gold"]["rejected_evidence_ids"]),
                "rationale_tags": [],
            },
        }
        for task in tasks
    ]


def make_gate(tasks: Sequence[dict], freeze: dict) -> Callable[[Sequence[object]], bool]:
    def gate(records: Sequence[object]) -> bool:
        return bool(
            RUNNER._score(list(tasks), copy.deepcopy(list(records)), freeze)[
                "all_vector_gates_pass"
            ]
        )

    return gate


# --- domain-appropriate perturbations of a response set -----------------------------


def _parsed_field(field: str) -> Callable[[Sequence[object], random.Random], Sequence[object]]:
    """Permute one field of the parsed answer across tasks, breaking its alignment."""

    def perturb(evidence: Sequence[object], rng: random.Random) -> Sequence[object]:
        rows = copy.deepcopy(list(evidence))
        values = [row["parsed"][field] for row in rows]  # type: ignore[index]
        rng.shuffle(values)
        for row, value in zip(rows, values):
            row["parsed"][field] = value  # type: ignore[index]
        return rows

    return perturb


def swap_selected_and_rejected(
    evidence: Sequence[object], rng: random.Random
) -> Sequence[object]:
    """Invert the evidence partition — the answer is still total, but backwards."""
    rows = copy.deepcopy(list(evidence))
    for row in rows:
        parsed = row["parsed"]  # type: ignore[index]
        parsed["selected_evidence_ids"], parsed["rejected_evidence_ids"] = (
            parsed["rejected_evidence_ids"],
            parsed["selected_evidence_ids"],
        )
    return rows


def corrupt_one_verdict(evidence: Sequence[object], rng: random.Random) -> Sequence[object]:
    """Change a single task's verdict. A gate at n=132 with a 0.85 floor should
    absorb this — the probe exists to show the gate is not hair-triggered."""
    rows = copy.deepcopy(list(evidence))
    victim = rng.randrange(len(rows))
    current = rows[victim]["parsed"]["verdict"]  # type: ignore[index]
    alternatives = sorted({"SUPPORT", "REFUTE", "CONTEXT_MISALIGNED", "CANNOT_CHECK"} - {current})
    rows[victim]["parsed"]["verdict"] = rng.choice(alternatives)  # type: ignore[index]
    return rows


def unparseable_fraction(
    fraction: float,
) -> Callable[[Sequence[object], random.Random], Sequence[object]]:
    """Mark a fraction of responses unparsed, as a real model producing malformed JSON would."""

    def perturb(evidence: Sequence[object], rng: random.Random) -> Sequence[object]:
        rows = copy.deepcopy(list(evidence))
        for index in rng.sample(range(len(rows)), max(1, int(len(rows) * fraction))):
            rows[index]["parsed"] = None  # type: ignore[index]
        return rows

    return perturb


PERTURBATIONS: dict[str, Callable[[Sequence[object], random.Random], Sequence[object]]] = {
    "shuffle_verdicts_across_tasks": _parsed_field("verdict"),
    "shuffle_selected_evidence_ids": _parsed_field("selected_evidence_ids"),
    "shuffle_rejected_evidence_ids": _parsed_field("rejected_evidence_ids"),
    "swap_selected_and_rejected": swap_selected_and_rejected,
    "corrupt_a_single_verdict": corrupt_one_verdict,
    "make_10pct_unparseable": unparseable_fraction(0.10),
    "shuffle_task_id": shuffle_field("task_id"),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--trials", type=int, default=16)
    ap.add_argument("--seed", type=int, default=20260814)
    args = ap.parse_args()

    freeze = json.loads(FREEZE_PATH.read_text())
    tasks = PANEL.build()
    records = oracle_records(tasks)
    gate = make_gate(tasks, freeze)

    # Control 1 — a perfect responder must pass.
    if not gate(records):
        metrics = RUNNER._score(list(tasks), copy.deepcopy(records), freeze)
        raise SystemExit(
            "CONTROL FAILED: the gate rejects a perfect responder, so it is mis-specified "
            f"and no probe below is interpretable. metrics={json.dumps(metrics, default=str)}"
        )

    # Control 2 — the shipped shortcut audit: constant responders must all fail.
    shortcut = RUNNER._shortcut_audit(list(tasks), freeze)

    report = audit_gate(
        gate,
        records,
        gate_id="stage4_capability_vector_gate",
        perturbations=PERTURBATIONS,
        trials=args.trials,
        seed=args.seed,
    )

    result = {
        "schema_version": "rakl-stage4-gate-falsifiability-audit-v1",
        "audited_subject": {
            "gate": "experiments/paper3/run_capability_stage4_v1.py :: _score -> all_vector_gates_pass",
            "freeze": "research/empirical_10_of_10_v1/CAPABILITY_QUALIFICATION/STAGE3_5_FREEZE_V1.json",
            "panel": "experiments/paper3/build_capability_stage4_panel_v1.py",
            "battery": "src/rakl/gate_falsifiability.py",
        },
        "n_tasks": len(tasks),
        "controls": {
            "oracle_responder_passes": True,
            "shipped_shortcut_audit_clean": shortcut["clean"],
            "constant_responder_results": shortcut["responders"],
        },
        "verdict": report.verdict.value,
        "supports_confirmatory_use": report.supports_confirmatory_use,
        "sensitive_probes": list(report.sensitive_probes),
        "probes": {
            p.probe_id: {"outcome": p.outcome.value, "flips": p.flips, "trials": p.trials}
            for p in report.probes
        },
        "reasons": list(report.reasons),
        "interpretation": (
            "A FALSIFIABLE verdict means only that this gate is capable of failing. It does "
            "not qualify any model, does not authorize Stage 4 execution, and says nothing "
            "about whether a PASS would be correct."
        ),
        "grants_scientific_authority": False,
    }

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "STAGE4_GATE_FALSIFIABILITY_AUDIT.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result, indent=2))
    return 0 if report.verdict is GateFalsifiability.FALSIFIABLE else 1


if __name__ == "__main__":
    raise SystemExit(main())
