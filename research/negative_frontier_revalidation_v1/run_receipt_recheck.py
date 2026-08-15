"""Recheck the four 'receipt absent from main' findings from #739.

That finding compared `Path(receipt_path).exists()` against paths that may carry
a branch qualifier, e.g.

    publication-overlay-papers-123:research/paper1_.../V2_PARENT_BOUNDARY_ADDENDUM.md

A branch-qualified reference is not a filesystem path. Stripping the qualifier
before the existence check is the difference between "this evidence is missing"
and "I looked in the wrong place".
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

INVENTORY = Path("research/negative_frontier_v1/INVENTORY.json")
OUT = Path("research/negative_frontier_revalidation_v1/RECEIPT_RECHECK.json")

SUSPECTS = [
    "p1-source-monitoring-repetition-attack",
    "p1-atms-parent-boundary",
    "p2-arn-v3-capability-absent",
    "p2-arn-v4-battery-failed",
]


def split_ref(raw: str) -> tuple[str | None, str | None]:
    """Normalise a cited reference into (branch, path).

    The inventory cites evidence in four shapes, and only the first is a bare
    filesystem path:

        research/x/RESULT.json
        branch-name:research/x/RESULT.json
        research/x/RESULT.json @ PR #703
        PR #703 body (gh pr view 703)

    Treating any of the last three as a path is how the earlier check concluded
    that evidence was missing when it was present. A reference that names no
    path at all returns ``None`` and is reported as non-path rather than absent.
    """

    ref = raw.strip()

    # Drop a trailing provenance annotation: "... @ PR #703", "... (see #12)".
    for sep in (" @ ", " (see ", " ("):
        if sep in ref:
            ref = ref.split(sep, 1)[0].strip()

    # A reference that names a PR or an issue rather than a file is not a path.
    if ref.lower().startswith(("pr #", "pr#", "issue #", "gh pr")):
        return None, None

    branch = None
    if ":" in ref and not ref.startswith(("http", "/")):
        head, tail = ref.split(":", 1)
        # Branch names contain slashes too — `arn/v3-instance-paired-reducer` —
        # so "head has no slash" is the wrong test and rejected exactly those.
        # A reference is branch-qualified when the tail looks like a repository
        # path; that is decidable without guessing at the shape of the name.
        if tail.startswith(("research/", "experiments/", "src/", "tests/", "publication/", "scripts/", "docs/")):
            branch, ref = head, tail

    return branch, ref or None


def on_main(path: str) -> bool:
    return (
        subprocess.run(
            ["git", "cat-file", "-e", f"gh/main:{path}"],
            capture_output=True,
        ).returncode
        == 0
    )


def main() -> int:
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    by_slug = {r["slug"]: r for r in inventory["records"]}

    rows = []
    for slug in SUSPECTS:
        record = by_slug[slug]
        refs = [record.get("receipt_path")] + list(record.get("supporting_receipts") or [])
        checked = []
        for raw in refs:
            if not raw:
                continue
            branch, path = split_ref(raw)
            if path is None:
                checked.append(
                    {
                        "cited": raw,
                        "branch_qualifier": None,
                        "path": None,
                        "kind": "NOT_A_PATH",
                        "naive_exists": False,
                        "path_exists_on_main": None,
                    }
                )
                continue
            checked.append(
                {
                    "cited": raw,
                    "branch_qualifier": branch,
                    "path": path,
                    "kind": "PATH",
                    "naive_exists": Path(raw).exists(),
                    "path_exists_on_main": on_main(path),
                }
            )
        paths = [c for c in checked if c["kind"] == "PATH"]
        recovered = [c for c in paths if not c["naive_exists"] and c["path_exists_on_main"]]
        genuinely_absent = [
            c for c in paths if not c["naive_exists"] and not c["path_exists_on_main"]
        ]
        rows.append(
            {
                "slug": slug,
                "refs": checked,
                "recovered_by_stripping_the_qualifier": len(recovered),
                "genuinely_absent": len(genuinely_absent),
                "verdict": (
                    "EVIDENCE_PRESENT__EARLIER_FINDING_WAS_A_PATH_ERROR"
                    if recovered and not genuinely_absent
                    else "PARTIALLY_RECOVERED"
                    if recovered
                    else "GENUINELY_ABSENT"
                ),
            }
        )

    result = {
        "schema_version": "rakl-receipt-recheck-v1",
        "status": "CORRECTION_TO_A_PUBLISHED_FINDING",
        "grants_scientific_authority": False,
        "corrects": "#739, which reported four records citing receipts absent from main",
        "cause": (
            "the check compared Path(receipt_path).exists() against references that carry a "
            "branch qualifier such as 'publication-overlay-papers-123:research/...'. A "
            "branch-qualified reference is not a filesystem path, so the check was asking the "
            "wrong question of at least some of them."
        ),
        "records_rechecked": len(rows),
        "per_record": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    for row in rows:
        print(f"{row['slug']:<42} {row['verdict']}")
        for c in row["refs"]:
            if c["kind"] == "NOT_A_PATH":
                print(f"    non-path  {c['cited'][:70]}")
                continue
            flag = "on-main" if c["path_exists_on_main"] else "ABSENT "
            q = f"[{c['branch_qualifier']}] " if c["branch_qualifier"] else ""
            print(f"    {flag} {q}{c['path'][:70]}")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
