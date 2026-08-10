from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "paper" / "saturated_epistemic_mechanics" / "source"


def stage_saturated_paper(
    destination: Path,
    *,
    subject_sha: str,
    software_tests: int,
) -> Path:
    if len(subject_sha) != 40 or any(c not in "0123456789abcdef" for c in subject_sha.lower()):
        raise ValueError("subject_sha must be a 40-character hexadecimal Git SHA")
    if software_tests < 1:
        raise ValueError("software_tests must be positive")

    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(SOURCE, destination)

    identity = destination / "build_identity.tex"
    identity.write_text(
        "\\newcommand{\\SoftwareTests}{%d}\n"
        "\\newcommand{\\ImplementationSHA}{\\texttt{%s}}\n"
        % (software_tests, subject_sha),
        encoding="utf-8",
    )

    manifest_path = destination / "BUILD_MANIFEST.json"
    source_manifest = json.loads((destination / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    source_manifest.update(
        {
            "implementation_subject_sha": subject_sha,
            "software_tests": software_tests,
            "build_identity": "build_identity.tex",
        }
    )
    manifest_path.write_text(json.dumps(source_manifest, indent=2) + "\n", encoding="utf-8")
    return destination / "main.tex"


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage the exact-subject saturated RAKL manuscript")
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--subject-sha", required=True)
    parser.add_argument("--software-tests", type=int, required=True)
    args = parser.parse_args()
    main_tex = stage_saturated_paper(
        args.stage,
        subject_sha=args.subject_sha,
        software_tests=args.software_tests,
    )
    print(main_tex)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
