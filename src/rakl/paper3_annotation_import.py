from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .paper3_annotation import canonical_sha256, compile_adjudicated_benchmark


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-set", type=Path, required=True)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--linkage", type=Path, required=True)
    parser.add_argument("--submission", type=Path, action="append", required=True)
    parser.add_argument("--adjudication", type=Path, required=True)
    parser.add_argument("--provenance-audit", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--rubric", type=Path, required=True)
    parser.add_argument("--negative-history-benchmark", type=Path, action="append", required=True)
    parser.add_argument("--subject-sha", required=True)
    parser.add_argument("--benchmark-output", type=Path, required=True)
    parser.add_argument("--receipt-output", type=Path, required=True)
    args = parser.parse_args()

    def load(path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    protocol = load(args.protocol)
    rubric_sha256 = hashlib.sha256(args.rubric.read_bytes()).hexdigest()
    result = compile_adjudicated_benchmark(
        source_set=load(args.source_set),
        subject_sha=args.subject_sha,
        packet=load(args.packet),
        linkage=load(args.linkage),
        submissions=[load(path) for path in args.submission],
        adjudication=load(args.adjudication),
        provenance_audit=load(args.provenance_audit),
        negative_history_benchmarks=[load(path) for path in args.negative_history_benchmark],
        observed_protocol_id=protocol["protocol_id"],
        observed_protocol_sha256=canonical_sha256(protocol),
        observed_rubric_id=protocol["rubric_id"],
        observed_rubric_sha256=rubric_sha256,
    )
    args.receipt_output.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_output.write_text(
        json.dumps(result["import_receipt"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    if result["passed"]:
        args.benchmark_output.parent.mkdir(parents=True, exist_ok=True)
        args.benchmark_output.write_text(
            json.dumps(result["benchmark"], indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(args.benchmark_output)
    print(args.receipt_output)
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
