#!/usr/bin/env python3
"""Schema `$id` consistency regression checker for issue #148.

The 87+ JSON schemas in `schemas/` declare their `$id` (schema identity — the key
that `$ref`, registry lookup, cached resolution and cross-schema composition key on)
under several different namespace bases. As of `main = 787c7e0` the split is measured
at four bases:

    59  https://github.com/SzeChunYiu/RAKL/schemas
    32  https://example.invalid/rakl
     4  https://rakl.dev/schemas
     1  https://rakl.example/schemas

Four identities for one coherent schema family means identity is unstable under a
repository rename and two of the bases are deliberately non-resolvable placeholders.
The defect is currently latent because the repo's own validators load schemas by path,
not by `$id`, which is why it has survived the existing tests.

This checker makes the defect visible and keeps it from regressing further. It is a
**measurement / regression tool only**. It selects no canonical base, rewrites no
`$id`, and grants no authority: choosing the frozen base is an owner decision with
real consequences (existing artifacts and receipts may quote current `$id` values,
and rewriting identities in frozen/immutable artifacts is forbidden).

Checks performed for every `schemas/*.json`:
  (a) a `$id` key exists and is a string                       -> MISSING_ID
  (b) the `$id` base (everything before the last `/`) is        extracted
  (c) the `$id` filename component equals the file basename     -> FILENAME_MISMATCH
  (d) the namespace split is reported as structured findings     -> SPLIT_NAMESPACE

Exit nonzero if any schema is missing `$id`, has a foreign base vs a frozen expected
base, or has a filename mismatch. Without `--expected-base` the checker treats "one
coherent family = one base" as the implicit frozen expectation, so any split
(namespace_count != 1) is itself the foreign-base defect. Once an owner pins the
canonical base, pass `--expected-base URL` to enforce that exact base.

Usage:
    python scripts/audit_schema_id_consistency.py                       # human report
    python scripts/audit_schema_id_consistency.py --json OUT            # machine report
    python scripts/audit_schema_id_consistency.py --expected-base URL   # enforce winner
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

CLAIM_BOUNDARY = (
    "Schema $id consistency measurement only. Selects no canonical base, enforces no "
    "renaming, rewrites no $id, and grants no authority. Choosing the frozen base is an "
    "owner decision; rewriting $id in frozen/immutable artifacts is forbidden."
)

# Finding kinds. SPLIT_NAMESPACE is reported once per observed base; the others are
# reported per offending schema file. Any finding makes the run exit nonzero.
MISSING_ID = "MISSING_ID"
MALFORMED_JSON = "MALFORMED_JSON"
FILENAME_MISMATCH = "FILENAME_MISMATCH"
FOREIGN_BASE = "FOREIGN_BASE"  # only emitted under --expected-base
SPLIT_NAMESPACE = "SPLIT_NAMESPACE"  # informational, one per base


@dataclass
class Finding:
    kind: str
    schema: str
    detail: str
    id_value: str | None = None


@dataclass
class Report:
    schema_count: int = 0
    namespace_count: int = 0
    namespaces: list[dict[str, Any]] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    expected_base: str | None = None
    claim_boundary: str = CLAIM_BOUNDARY

    @property
    def ok(self) -> bool:
        return not self.findings


def extract_base(identifier: str) -> str:
    """Return the `$id` base: everything before the final path segment.

    Mirrors the existing measurement in `scripts/audit_terminology_inventory.py`
    (`rename_blast_radius`), so the two scripts agree on what a "namespace" is.
    """
    return identifier.rsplit("/", 1)[0]


def check_repo(repo: Path, expected_base: str | None = None) -> Report:
    schemas_dir = repo / "schemas"
    schema_files = sorted(schemas_dir.glob("*.json")) if schemas_dir.is_dir() else []
    report = Report(schema_count=len(schema_files), expected_base=expected_base)

    bases: collections.Counter[str] = collections.Counter()
    base_files: dict[str, list[str]] = collections.defaultdict(list)

    for path in schema_files:
        relative = path.relative_to(repo).as_posix()
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            report.findings.append(
                Finding(MALFORMED_JSON, relative, f"could not read/parse: {exc}")
            )
            continue
        if not isinstance(document, dict):
            report.findings.append(
                Finding(
                    MALFORMED_JSON, relative, "schema document is not a JSON object"
                )
            )
            continue

        identifier = document.get("$id")
        if not isinstance(identifier, str) or not identifier:
            report.findings.append(
                Finding(MISSING_ID, relative, "top-level $id missing or non-string")
            )
            continue

        base = extract_base(identifier)
        bases[base] += 1
        base_files[base].append(relative)

        # (c) filename component of $id must equal the file basename.
        filename_component = identifier.rsplit("/", 1)[-1]
        if filename_component != path.name:
            report.findings.append(
                Finding(
                    FILENAME_MISMATCH,
                    relative,
                    f"$id filename component {filename_component!r} != file basename {path.name!r}",
                    id_value=identifier,
                )
            )

        # (d) foreign base vs an explicitly frozen expected base.
        if expected_base is not None and base != expected_base:
            report.findings.append(
                Finding(
                    FOREIGN_BASE,
                    relative,
                    f"base {base!r} != expected {expected_base!r}",
                    id_value=identifier,
                )
            )

    # (d) namespace split. Without an explicit --expected-base the implicit frozen
    # expectation is "one coherent family = one base", so any split is the foreign-base
    # defect surfaced once per minority/majority base. With --expected-base the per-file
    # FOREIGN_BASE findings already carry the failure; the split is still reported as
    # structured information either way.
    namespace_count = len(bases)
    report.namespace_count = namespace_count
    for base, count in bases.most_common():
        report.namespaces.append(
            {"base": base, "count": count, "sample_files": base_files[base][:3]}
        )
        if expected_base is None and namespace_count != 1:
            report.findings.append(
                Finding(
                    SPLIT_NAMESPACE,
                    "(schemas/)",
                    f"{count} schema(s) under base {base!r}; family is split across "
                    f"{namespace_count} namespaces",
                    id_value=base,
                )
            )

    return report


def render_human(report: Report) -> str:
    lines: list[str] = []
    lines.append(f"schema_count: {report.schema_count}")
    lines.append(f"namespace_count: {report.namespace_count}")
    lines.append("namespaces:")
    for ns in report.namespaces:
        lines.append(f"  {ns['count']:3d}  {ns['base']}")
    if report.expected_base is not None:
        lines.append(f"expected_base: {report.expected_base}")
    if report.findings:
        lines.append("findings:")
        for finding in report.findings:
            id_part = f"  $id={finding.id_value}" if finding.id_value else ""
            lines.append(
                f"  [{finding.kind}] {finding.schema}: {finding.detail}{id_part}"
            )
    else:
        lines.append("findings: none")
    lines.append("")
    lines.append("owner-decision summary:")
    lines.append(
        "  The schema family is split across the namespace bases listed above. "
        "Choosing the single canonical base is an owner decision; the options "
        "(adopt the GitHub base, adopt a controlled domain, or adopt a non-resolvable "
        "stable URN) trade off differently against a possible future rename. This "
        "checker selects no winner and rewrites no $id."
    )
    lines.append("")
    lines.append(f"claim_boundary: {report.claim_boundary}")
    return "\n".join(lines)


def render_json(report: Report) -> dict[str, Any]:
    return {
        "schema_count": report.schema_count,
        "namespace_count": report.namespace_count,
        "namespaces": report.namespaces,
        "expected_base": report.expected_base,
        "findings": [asdict(f) for f in report.findings],
        "finding_count": len(report.findings),
        "claim_boundary": report.claim_boundary,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root containing schemas/ (default: this repo).",
    )
    parser.add_argument(
        "--expected-base",
        default=None,
        help="Pin the canonical $id base; every schema base must equal it.",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        help="Write a machine-readable JSON report to this path.",
    )
    args = parser.parse_args()

    repo = args.repo.resolve()
    report = check_repo(repo, expected_base=args.expected_base)

    if args.json:
        args.json.write_text(
            json.dumps(render_json(report), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(render_human(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
