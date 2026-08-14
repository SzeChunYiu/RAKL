from __future__ import annotations

import argparse
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_trajectory_lesson_induction_v1 as V1  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
V2_PROTOCOL = ROOT / "research" / "paper3_trajectory_lesson_induction_v1" / "PROTOCOL_V2.json"
_ORIGINAL_PAIR = V1._pair


def _pair_v2(family: str, i: int):
    if family != "CONSISTENT_VERIFIED_SUCCESS_INDUCES_CANDIDATE":
        return _ORIGINAL_PAIR(family, i)
    t = f"{family[:7]}-{i:03d}"
    positive = (
        V1._episode(t + "a", 1),
        V1._episode(t + "a", 2),
    )
    # v1 defect repair: construct the missing-verification twin natively, so
    # its exact artifact hash binds verification_ids=() rather than retaining
    # the positive twin's stale hash.
    negative = (
        V1._episode(t + "b", 1),
        V1._episode(t + "b", 2, verified=False),
    )
    return (
        V1._case(t + "A", family, positive, candidate=True),
        V1._case(t + "B", family, negative, candidate=False),
    )


def run(outdir: Path):
    V1.PROTOCOL = V2_PROTOCOL
    V1._pair = _pair_v2
    try:
        return V1.run(outdir)
    finally:
        V1._pair = _ORIGINAL_PAIR


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.outdir)
    raise SystemExit(0 if result["all_gates_pass"] else 1)


if __name__ == "__main__":
    main()
