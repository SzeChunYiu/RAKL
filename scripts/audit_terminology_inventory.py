#!/usr/bin/env python3
"""Reproducible terminology-dependency inventory for issue #137.

This auditor measures where RAKL's lattice/landscape/navigation vocabulary and its
rename-blast-radius surfaces actually occur, so that a naming decision is taken
against counted evidence rather than impression.

It is a **measurement tool only**. It selects no winner, enforces no threshold,
rewrites no prose, and grants no authority. Emitting a report does not authorize
a terminology migration or a repository/package rename.

Usage:
    python scripts/audit_terminology_inventory.py            # human-readable summary
    python scripts/audit_terminology_inventory.py --json OUT # machine-readable report
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# Phrases whose ordinary reading asserts a *global* order-theoretic structure that
# ARCHITECTURE.md explicitly does not claim. These are the mathematically load-bearing
# ones, as distinct from brand//historical uses of the same word.
MISLEADING_GLOBAL_STRUCTURE = {
    "global lattice": r"\bglobal lattice\b",
    "knowledge lattice": r"\bknowledge lattice\b",
    "meta-lattice": r"\bmeta[- ]lattice\b",
    "lattice path": r"\blattice path\b",
}

# Uses the issue's own terminology table marks as legitimate to KEEP where the
# specialized contract justifies them, plus the brand surface.
JUSTIFIED_OR_BRAND = {
    "failure lattice": r"\bfailure[- ]lattice\b|\bFailureLattice\b|failure_lattice",
    "lattice (any occurrence)": r"[Ll]attice",
    "RAKL acronym expansion": r"Recursive Atomic Knowledge Lattice",
}

# Symbols a Class-2 (API alias) migration would have to carry compatibility for.
API_SYMBOLS = {
    "SaturationVector": r"SaturationVector|saturation_vector",
    "KnowledgeFiber": r"KnowledgeFiber|knowledge[- ]fib(?:er|re)",
    "ProblemFibre": r"ProblemFibre|problem_fibre",
}

# Reader-facing terms proposed by #137 that do not yet exist in the tree. A zero
# count means zero migration cost, and also zero incumbent usage to build on.
PROPOSED_VOCABULARY = {
    "epistemic GPS": r"epistemic GPS",
    "roadmap": r"\broadmap\b",
    "landscape": r"\blandscape\b",
    "problem map": r"\bproblem map\b",
    "territory": r"\bterritory\b",
}

SKIP_SUFFIXES = {".pdf", ".png", ".jpg", ".pyc", ".safetensors", ".gz", ".zip"}

# Surfaces whose historical artifacts must NOT be rewritten to match new
# terminology; they correctly used the vocabulary frozen for their version.
IMMUTABLE_SURFACES = {"archive (immutable)", "research (archive)"}


def classify(path: str) -> str:
    for prefix, label in (
        ("src/", "src (executable)"),
        ("tests/", "tests"),
        ("schemas/", "schemas"),
        ("skills/", "skills"),
        ("docs/", "docs"),
        ("research/", "research (archive)"),
        ("archive/", "archive (immutable)"),
        ("paper/", "papers/publication"),
        ("publication/", "papers/publication"),
        ("publishing/", "papers/publication"),
        (".github/", "CI"),
        ("experiments/", "experiments"),
        ("benchmarks/", "experiments"),
        ("scripts/", "scripts"),
    ):
        if path.startswith(prefix):
            return label
    return "root/other"


def tracked_files(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
        shell=False,
    )
    return [line for line in result.stdout.splitlines() if line]


def measure(repo: Path, groups: dict[str, dict[str, str]]) -> dict[str, Any]:
    counts: dict[str, collections.Counter[str]] = collections.defaultdict(
        collections.Counter
    )
    files: dict[str, set[str]] = collections.defaultdict(set)
    compiled = {
        term: re.compile(pattern)
        for group in groups.values()
        for term, pattern in group.items()
    }
    for relative in tracked_files(repo):
        path = repo / relative
        if path.suffix in SKIP_SUFFIXES or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        surface = classify(relative)
        for term, pattern in compiled.items():
            hits = len(pattern.findall(text))
            if hits:
                counts[term][surface] += hits
                files[term].add(relative)
    report: dict[str, Any] = {"groups": {}}
    for group_name, group in groups.items():
        report["groups"][group_name] = {
            term: {
                "total": sum(counts[term].values()),
                "file_count": len(files[term]),
                "by_surface": dict(sorted(counts[term].items())),
                "immutable_share": sum(
                    n
                    for surface, n in counts[term].items()
                    if surface in IMMUTABLE_SURFACES
                ),
                "files": sorted(files[term]) if len(files[term]) <= 40 else None,
            }
            for term in group
        }
    return report


def rename_blast_radius(repo: Path) -> dict[str, Any]:
    """Surfaces a Class-3 repository/package rename would have to migrate."""

    schema_ids: collections.Counter[str] = collections.Counter()
    for schema in sorted((repo / "schemas").glob("*.json")):
        try:
            value = json.loads(schema.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        identifier = value.get("$id")
        if isinstance(identifier, str):
            schema_ids[identifier.rsplit("/", 1)[0]] += 1
    importers = [
        relative
        for relative in tracked_files(repo)
        if relative.endswith(".py")
        and re.search(
            r"^\s*(?:from rakl|import rakl)",
            (repo / relative).read_text(encoding="utf-8", errors="ignore"),
            re.MULTILINE,
        )
    ]
    return {
        "python_package_name": "rakl",
        "python_files_importing_rakl": len(importers),
        "schema_count": len(list((repo / "schemas").glob("*.json"))),
        "schema_id_namespaces": dict(schema_ids.most_common()),
        "schema_id_namespace_count": len(schema_ids),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()
    repo = args.repo.resolve()
    report = measure(
        repo,
        {
            "mathematically_misleading_global_structure": MISLEADING_GLOBAL_STRUCTURE,
            "justified_or_brand": JUSTIFIED_OR_BRAND,
            "api_symbols_class2": API_SYMBOLS,
            "proposed_vocabulary_not_yet_present": PROPOSED_VOCABULARY,
        },
    )
    report["rename_blast_radius"] = rename_blast_radius(repo)
    report["subject_sha"] = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
        shell=False,
    ).stdout.strip()
    report["claim_boundary"] = (
        "Terminology measurement only. Selects no name, enforces no threshold, "
        "authorizes no migration or rename, and grants no authority."
    )
    if args.json:
        args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for group_name, group in report["groups"].items():
        print(f"\n=== {group_name} ===")
        for term, row in sorted(group.items(), key=lambda kv: -kv[1]["total"]):
            print(
                f"  {term:34s} total={row['total']:5d} "
                f"files={row['file_count']:4d} immutable={row['immutable_share']}"
            )
    print("\n=== rename blast radius (Class 3) ===")
    for key, value in report["rename_blast_radius"].items():
        print(f"  {key}: {value}")
    print(f"\nsubject: {report['subject_sha']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
