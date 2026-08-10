from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "paper" / "saturated_epistemic_mechanics" / "source"
GENERATED_FIGURES = ROOT / "paper" / "figures" / "generated"
RECEIPT_BOUND_FIGURES = ("fig5_demo_growth.pdf", "fig6_demo_context.pdf")


def _stage_receipt_bound_figures(destination: Path) -> tuple[str, ...]:
    """Prefer freshly regenerated receipt-bound figures over bundled release binaries.

    The publication workflow runs ``paper/generate_demo_figures.py`` before staging the
    manuscript.  When those exact generated PDFs are available, they are the stronger
    provenance object and replace the convenience copies stored beside the chaptered
    source.  Source-only tests may stage without regenerated figures, in which case the
    checked-in source assets remain available and the manifest records that no override
    occurred.
    """

    overridden: list[str] = []
    for name in RECEIPT_BOUND_FIGURES:
        generated = GENERATED_FIGURES / name
        if generated.exists():
            shutil.copy2(generated, destination / name)
            overridden.append(name)
    return tuple(overridden)


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
    receipt_bound_overrides = _stage_receipt_bound_figures(destination)

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
            "receipt_bound_figure_overrides": list(receipt_bound_overrides),
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
