from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from rakl.objective_transfer_benchmark import (
    generate,
    verify,
    extract,
    twin_ablation,
    mechanism_predict,
    relational_predict,
    lexical_score,
    lexical_predict,
)

SEED = 2026081202
N_PER_CELL = 16
TOTAL_N = 576
LEXICAL_THRESHOLD = 0.2761904761904762
EXPECTED = {
    "OBJECTIVE_TASKS_CONFIRMATORY_V1.jsonl": "3516e48f9dd7923a950e09ece42cfee8c39548c699fe2f7d7d0ca6dee53e45f2",
    "HIDDEN_GOLD_CONFIRMATORY_V1.jsonl": "1c9ac8c412206972c5ddeeb92670819fca5adc2df79e1b52b6530aa9f0665308",
    "MACHINE_WITNESS_OUTPUTS_CONFIRMATORY_V1.jsonl": "92f9c0ecfa424066a1851f743a3429d4ed7478b02beb38a66b619ed0ae088053",
    "SEMANTIC_CONTROL_SCORES_CONFIRMATORY_V1.jsonl": "4031be31f256afe7e3e51440c5b5c25b70369034d57e8fce59dbe667a1d886e2",
}


def _dump_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(outdir: Path) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    tasks = generate(SEED, N_PER_CELL, True)
    if len(tasks) != TOTAL_N:
        raise RuntimeError(f"frozen confirmatory n mismatch: {len(tasks)} != {TOTAL_N}")

    public_rows: list[dict] = []
    hidden_rows: list[dict] = []
    witness_rows: list[dict] = []
    semantic_rows: list[dict] = []

    for task in tasks:
        gold = verify(task)
        full = extract(task)
        twin = extract(task, twin_ablation(task))
        public_rows.append(
            {
                "item_id": task.item_id,
                "source_text": task.source_text,
                "target_text": task.target_text,
                "public": task.public,
            }
        )
        hidden_rows.append(
            {
                "item_id": task.item_id,
                "family": task.family,
                "item_type": task.item_type,
                "perturbation": task.perturbation,
                "decision": gold.decision.value,
                "verifier_trace": list(gold.trace),
            }
        )
        witness_rows.append(
            {
                "item_id": task.item_id,
                "full_decision": full.decision.value,
                "full_obligations": [list(item) for item in full.obligations],
                "coordinate_twin_decision": twin.decision.value,
                "mechanism_decision": mechanism_predict(task).value,
                "relational_decision": relational_predict(task).value,
            }
        )
        semantic_rows.append(
            {
                "item_id": task.item_id,
                "lexical_jaccard": lexical_score(task),
                "lexical_decision": lexical_predict(task, LEXICAL_THRESHOLD).value,
            }
        )

    packets = {
        "OBJECTIVE_TASKS_CONFIRMATORY_V1.jsonl": public_rows,
        "HIDDEN_GOLD_CONFIRMATORY_V1.jsonl": hidden_rows,
        "MACHINE_WITNESS_OUTPUTS_CONFIRMATORY_V1.jsonl": witness_rows,
        "SEMANTIC_CONTROL_SCORES_CONFIRMATORY_V1.jsonl": semantic_rows,
    }
    receipt: dict[str, object] = {"seed": SEED, "n": TOTAL_N, "files": {}}
    for name, rows in packets.items():
        path = outdir / name
        _dump_jsonl(path, rows)
        actual = _sha256(path)
        expected = EXPECTED[name]
        receipt["files"][name] = {
            "sha256": actual,
            "expected_sha256": expected,
            "bytes": path.stat().st_size,
            "matches_expected": actual == expected,
        }
        if actual != expected:
            raise RuntimeError(f"hash mismatch for {name}: {actual} != {expected}")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outdir", type=Path, default=Path("confirmatory_out"))
    args = parser.parse_args()
    print(json.dumps(run(args.outdir), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
