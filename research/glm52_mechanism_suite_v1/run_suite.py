from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _run(script: str, args: list[str]) -> None:
    cmd = [sys.executable, str(HERE / script), *args]
    subprocess.run(cmd, check=True, cwd=HERE)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _gate(path: Path, key: str = "dev_gate") -> bool:
    obj = _load(path)
    return bool(obj.get("summary", {}).get(key, {}).get("passes"))


def main() -> int:
    p = argparse.ArgumentParser(description="GLM-5.2 mechanism-isolation suite")
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("dev")
    d.add_argument("--n", type=int, default=8)
    c = sub.add_parser("confirm")
    c.add_argument("--selective-dev", type=Path, required=True)
    c.add_argument("--experience-dev", type=Path, required=True)
    c.add_argument("--trajectory-dev", type=Path, required=True)
    c.add_argument("--n", type=int, default=20)
    args = p.parse_args()

    if args.cmd == "dev":
        _run("selective_retrieval.py", ["--phase", "dev", "--n-per-cell", str(args.n), "--out", "DEV_SELECTIVE.json"])
        _run("experience_transfer.py", ["--phase", "dev", "--n-per-family", str(args.n), "--out", "DEV_EXPERIENCE.json"])
        _run("trajectory_governance.py", ["--phase", "dev", "--n-per-kind", str(args.n), "--out", "DEV_TRAJECTORY.json"])
        print("Development runs complete. Confirmatory execution remains locked until all non-RAKL dev gates pass.")
        return 0

    gates = {
        "selective_retrieval": _gate(args.selective_dev),
        "experience_transfer": _gate(args.experience_dev),
        "trajectory_governance": _gate(args.trajectory_dev),
    }
    if not all(gates.values()):
        print(json.dumps({"confirmatory_execution": "REFUSED", "dev_gates": gates}, indent=2))
        return 2

    _run("selective_retrieval.py", ["--phase", "confirm", "--n-per-cell", str(args.n), "--out", "CONFIRM_SELECTIVE.json"])
    _run("experience_transfer.py", ["--phase", "confirm", "--n-per-family", str(args.n), "--out", "CONFIRM_EXPERIENCE.json"])
    _run("trajectory_governance.py", ["--phase", "confirm", "--n-per-kind", str(args.n), "--out", "CONFIRM_TRAJECTORY.json"])
    print("Confirmatory runs complete. Do not revise this protocol using these outcomes; any redesign is a new version.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
