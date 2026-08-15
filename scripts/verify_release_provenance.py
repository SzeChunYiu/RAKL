#!/usr/bin/env python3
"""E19 — release-provenance gate.

`BuildProvenance` binds a release to its source commit, lock digest, build
procedure, artifact digest, config and release manifest, and verifies the record
against the artifact's actual bytes. This script is the gate that calls it, plus
the two checks the dataclass cannot make on its own: whether the benchmark and
evaluator identities the release declares are still the current ones, and whether
each deployment artifact the release names actually verifies on disk.

It rejects:

  missing or mismatched provenance   a record present but incomplete, or bound to
                                     a different commit than the one being released
  mutable image tags                 an artifact_ref without ``@sha256:``
  stale benchmark/evaluator identity a declared identity digest that no longer
                                     matches the current baseline, or a current
                                     identity the release never declared
  unverified deployment artifacts    a declared artifact that is absent, or whose
                                     bytes do not hash to the declared digest

Exit codes -- the distinction is the point:

    0   VERIFIED      every declared thing was checked and every check passed
    2   REJECTED      something was checked and it failed
    3   CANNOT_CHECK  an input was absent, unreadable or malformed, so some check
                      could not run. Never conflated with VERIFIED: a release
                      whose provenance could not be examined has not been verified.
    64  usage error

FAIL dominates CANNOT_CHECK, so a release with one confirmed failure and one
unrunnable check exits 2, not 3. A release with zero failures but any unrunnable
check exits 3, never 0.

Provenance record (JSON object)::

    {
      "source_commit":            "<40-hex git sha>",
      "lock_digest":              "<sha256>",
      "build_procedure_digest":   "<sha256>",
      "artifact_ref":             "registry/image@sha256:<digest>",
      "artifact_digest":          "<sha256 of the artifact bytes>",
      "config_digest":            "<sha256>",
      "release_manifest_digest":  "<sha256>",
      "benchmark_identities":     {"<name>": "<digest>", ...},
      "evaluator_identities":     {"<name>": "<digest>", ...},
      "deployment_artifacts":     [{"role": "...", "path": "rel/path", "sha256": "..."}]
    }

Identity baseline (JSON object)::

    {"benchmarks": {"<name>": "<digest>"}, "evaluators": {"<name>": "<digest>"}}

This gate reports engineering artifact identity only. It grants no scientific
authority and licenses no claim about what the release's results mean.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from rakl.engineering_ops import BuildProvenance, ProvenanceVerdict  # noqa: E402

EXIT_VERIFIED = 0
EXIT_REJECTED = 2
EXIT_CANNOT_CHECK = 3
EXIT_USAGE = 64

_PROVENANCE_FIELDS = (
    "source_commit",
    "lock_digest",
    "build_procedure_digest",
    "artifact_ref",
    "artifact_digest",
    "config_digest",
    "release_manifest_digest",
)

_VERDICT_REASON = {
    ProvenanceVerdict.MISSING_FIELD: "MISSING_PROVENANCE_FIELD",
    ProvenanceVerdict.MUTABLE_TAG_WITHOUT_DIGEST: "MUTABLE_TAG_WITHOUT_DIGEST",
    ProvenanceVerdict.ARTIFACT_MISMATCH: "ARTIFACT_MISMATCH",
}


@dataclass
class GateReport:
    failures: list[str] = field(default_factory=list)
    uncheckable: list[str] = field(default_factory=list)
    checked: list[str] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        if self.failures:
            return "REJECTED"
        if self.uncheckable:
            return "CANNOT_CHECK"
        return "VERIFIED"

    @property
    def exit_code(self) -> int:
        return {"REJECTED": EXIT_REJECTED, "CANNOT_CHECK": EXIT_CANNOT_CHECK, "VERIFIED": EXIT_VERIFIED}[
            self.verdict
        ]

    def to_dict(self) -> dict[str, object]:
        return {
            "verdict": self.verdict,
            "exit_code": self.exit_code,
            "failures": list(self.failures),
            "uncheckable": list(self.uncheckable),
            "checked": list(self.checked),
            "authority_scope": "ENGINEERING_ARTIFACT_IDENTITY_ONLY",
            "grants_scientific_authority": False,
        }


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_json_object(path: Path | None, label: str, report: GateReport) -> dict[str, object] | None:
    if path is None:
        report.uncheckable.append(f"{label}_NOT_SUPPLIED")
        return None
    if not path.is_file():
        report.uncheckable.append(f"{label}_MISSING:{path}")
        return None
    try:
        value = json.loads(path.read_text("utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        report.uncheckable.append(f"{label}_UNREADABLE:{type(exc).__name__}")
        return None
    except json.JSONDecodeError as exc:
        report.uncheckable.append(f"{label}_NOT_JSON:line{exc.lineno}")
        return None
    if not isinstance(value, dict):
        report.uncheckable.append(f"{label}_NOT_JSON_OBJECT")
        return None
    return value


def _check_identities(
    declared: object, baseline: object, kind: str, report: GateReport
) -> None:
    """Stale identity: a declared digest that no longer matches the live baseline."""

    if not isinstance(declared, Mapping):
        report.uncheckable.append(f"{kind}_IDENTITIES_NOT_DECLARED")
        return
    if not isinstance(baseline, Mapping):
        report.uncheckable.append(f"{kind}_BASELINE_ABSENT")
        return
    if not baseline:
        report.uncheckable.append(f"{kind}_BASELINE_EMPTY")
        return
    for name in sorted(baseline):
        current = str(baseline[name])
        if name not in declared:
            report.failures.append(f"UNDECLARED_{kind}_IDENTITY:{name}")
            continue
        if str(declared[name]) != current:
            report.failures.append(f"STALE_{kind}_IDENTITY:{name}")
            continue
        report.checked.append(f"{kind.lower()}_identity:{name}")
    for name in sorted(set(declared) - set(baseline)):
        report.failures.append(f"UNKNOWN_{kind}_IDENTITY:{name}")


def _check_deployment_artifacts(record: Mapping[str, object], root: Path, report: GateReport) -> None:
    declared = record.get("deployment_artifacts")
    if declared is None:
        report.uncheckable.append("DEPLOYMENT_ARTIFACTS_NOT_DECLARED")
        return
    if not isinstance(declared, list):
        report.uncheckable.append("DEPLOYMENT_ARTIFACTS_NOT_A_LIST")
        return
    if not declared:
        report.failures.append("NO_DEPLOYMENT_ARTIFACTS_DECLARED")
        return
    if not root.is_dir():
        report.uncheckable.append(f"RELEASE_ROOT_MISSING:{root}")
        return
    for item in declared:
        if not isinstance(item, Mapping) or "path" not in item or "sha256" not in item:
            report.uncheckable.append(f"DEPLOYMENT_ARTIFACT_MALFORMED:{item!r}"[:120])
            continue
        role = str(item.get("role", "artifact"))
        rel = str(item["path"])
        target = root / rel
        if Path(rel).is_absolute() or ".." in Path(rel).parts:
            report.failures.append(f"UNSAFE_DEPLOYMENT_ARTIFACT_PATH:{role}:{rel}")
            continue
        if not target.is_file():
            report.failures.append(f"UNVERIFIED_DEPLOYMENT_ARTIFACT:{role}:{rel}")
            continue
        try:
            actual = _sha256(target.read_bytes())
        except OSError as exc:
            report.uncheckable.append(f"DEPLOYMENT_ARTIFACT_UNREADABLE:{role}:{rel}:{type(exc).__name__}")
            continue
        if actual != str(item["sha256"]):
            report.failures.append(f"DEPLOYMENT_ARTIFACT_DIGEST_MISMATCH:{role}:{rel}")
            continue
        report.checked.append(f"deployment_artifact:{role}:{rel}")


def evaluate(
    *,
    provenance_path: Path | None,
    artifact_path: Path | None,
    identities_path: Path | None,
    root: Path,
    expect_commit: str | None,
) -> GateReport:
    report = GateReport()

    record = _load_json_object(provenance_path, "PROVENANCE_RECORD", report)

    artifact_bytes: bytes | None = None
    if artifact_path is None:
        report.uncheckable.append("ARTIFACT_NOT_SUPPLIED")
    elif not artifact_path.is_file():
        report.uncheckable.append(f"ARTIFACT_MISSING:{artifact_path}")
    else:
        try:
            artifact_bytes = artifact_path.read_bytes()
        except OSError as exc:
            report.uncheckable.append(f"ARTIFACT_UNREADABLE:{type(exc).__name__}")

    if record is not None:
        provenance = BuildProvenance(**{name: str(record.get(name, "")) for name in _PROVENANCE_FIELDS})
        if artifact_bytes is None:
            report.uncheckable.append("PROVENANCE_UNVERIFIABLE_WITHOUT_ARTIFACT_BYTES")
        else:
            verdict = provenance.verify(artifact_bytes)
            if verdict is ProvenanceVerdict.VERIFIED:
                report.checked.append(f"build_provenance:{provenance.artifact_ref}")
            else:
                report.failures.append(_VERDICT_REASON[verdict])

        if expect_commit is not None:
            if provenance.source_commit != expect_commit:
                report.failures.append(
                    f"PROVENANCE_COMMIT_MISMATCH:{provenance.source_commit or '<empty>'}!={expect_commit}"
                )
            else:
                report.checked.append(f"source_commit:{expect_commit}")

        baseline = _load_json_object(identities_path, "IDENTITY_BASELINE", report) or {}
        _check_identities(record.get("benchmark_identities"), baseline.get("benchmarks"), "BENCHMARK", report)
        _check_identities(record.get("evaluator_identities"), baseline.get("evaluators"), "EVALUATOR", report)
        _check_deployment_artifacts(record, root, report)

    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="verify_release_provenance.py",
        description="E19 release-provenance gate.",
        epilog=(
            "exit codes: 0 VERIFIED | 2 REJECTED (a check ran and failed) | "
            "3 CANNOT_CHECK (a check could not run; NOT the same as verified) | 64 usage error"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--provenance", type=Path, default=None, help="build provenance record (JSON object)")
    parser.add_argument("--artifact", type=Path, default=None, help="the built artifact whose bytes are hashed")
    parser.add_argument("--identities", type=Path, default=None, help="current benchmark/evaluator identity baseline")
    parser.add_argument("--root", type=Path, default=ROOT, help="root that deployment artifact paths are relative to")
    parser.add_argument("--expect-commit", default=None, help="commit the release must be bound to")

    def _usage_error(message: str) -> None:  # argparse's default exit 2 collides with REJECTED
        parser.print_usage(sys.stderr)
        print(f"{parser.prog}: error: {message}", file=sys.stderr)
        raise SystemExit(EXIT_USAGE)

    parser.error = _usage_error  # type: ignore[method-assign]
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = evaluate(
        provenance_path=args.provenance,
        artifact_path=args.artifact,
        identities_path=args.identities,
        root=args.root,
        expect_commit=args.expect_commit,
    )
    print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    return report.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
