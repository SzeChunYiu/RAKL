from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


@dataclass(frozen=True)
class ParentEvaluatorPolicy:
    """Trusted parent inputs that a candidate is not allowed to rewrite in-place.

    Files already present under ``protected_roots`` are frozen. Candidate additions
    under those roots are supplemental and therefore allowed, but they cannot replace,
    edit, delete, or symlink any parent-owned file. ``protected_files`` covers
    evaluator-affecting inputs outside those roots.
    """

    protected_files: tuple[str, ...]
    protected_roots: tuple[str, ...] = ()

    @classmethod
    def rakl_default(cls) -> "ParentEvaluatorPolicy":
        return cls(
            protected_files=(
                "pyproject.toml",
                ".github/workflows/test.yml",
                ".github/workflows/trusted-parent-evaluator.yml",
                "src/rakl/promotion.py",
                "src/rakl/evaluator.py",
                "src/rakl/parent_evaluator.py",
            ),
            protected_roots=("tests",),
        )


@dataclass(frozen=True)
class ParentEvaluationReport:
    valid: bool
    parent_sha: str
    candidate_sha: str
    inspected_paths: tuple[str, ...]
    changed_paths: tuple[str, ...] = ()
    missing_paths: tuple[str, ...] = ()
    unsafe_paths: tuple[str, ...] = ()

    @property
    def reasons(self) -> tuple[str, ...]:
        reasons: list[str] = []
        reasons.extend(f"protected parent input changed: {path}" for path in self.changed_paths)
        reasons.extend(f"protected parent input missing: {path}" for path in self.missing_paths)
        reasons.extend(f"protected candidate path is unsafe: {path}" for path in self.unsafe_paths)
        return tuple(reasons)


def _normalized_relative(path: str) -> str:
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts or str(pure) in {"", "."}:
        raise ValueError(f"protected path must be a normalized relative path: {path!r}")
    return pure.as_posix()


def _sha256_regular_file(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"not a regular non-symlink file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parent_owned_paths(parent_root: Path, policy: ParentEvaluatorPolicy) -> tuple[str, ...]:
    owned: set[str] = set()
    for raw in policy.protected_files:
        owned.add(_normalized_relative(raw))

    for raw_root in policy.protected_roots:
        rel_root = _normalized_relative(raw_root)
        root = parent_root / rel_root
        if not root.exists() or root.is_symlink() or not root.is_dir():
            raise ValueError(f"trusted parent protected root is missing or unsafe: {rel_root}")
        for path in root.rglob("*"):
            if path.is_dir() and not path.is_symlink():
                continue
            rel = path.relative_to(parent_root).as_posix()
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"trusted parent protected path is not a regular file: {rel}")
            owned.add(rel)

    return tuple(sorted(owned))


def evaluate_candidate_against_parent(
    parent_root: str | Path,
    candidate_root: str | Path,
    *,
    parent_sha: str,
    candidate_sha: str,
    policy: ParentEvaluatorPolicy | None = None,
) -> ParentEvaluationReport:
    """Compare candidate evaluator inputs against a trusted parent snapshot.

    Candidate content is treated strictly as passive data. This function never imports,
    installs, or executes anything from ``candidate_root``. The caller is responsible
    for checking out the exact recorded revisions; both revision identities are carried
    into the report so the observation can be bound to those snapshots.
    """

    if not parent_sha:
        raise ValueError("parent_sha cannot be empty")
    if not candidate_sha:
        raise ValueError("candidate_sha cannot be empty")

    parent = Path(parent_root)
    candidate = Path(candidate_root)
    if parent.resolve() == candidate.resolve():
        raise ValueError("parent and candidate roots must be distinct")

    effective_policy = policy or ParentEvaluatorPolicy.rakl_default()
    inspected = _parent_owned_paths(parent, effective_policy)

    changed: list[str] = []
    missing: list[str] = []
    unsafe: list[str] = []

    for rel in inspected:
        parent_path = parent / rel
        candidate_path = candidate / rel

        if not parent_path.exists() or parent_path.is_symlink() or not parent_path.is_file():
            raise ValueError(f"trusted parent protected file is missing or unsafe: {rel}")

        if candidate_path.is_symlink():
            unsafe.append(rel)
            continue
        if not candidate_path.exists():
            missing.append(rel)
            continue
        if not candidate_path.is_file():
            unsafe.append(rel)
            continue

        if _sha256_regular_file(parent_path) != _sha256_regular_file(candidate_path):
            changed.append(rel)

    valid = not changed and not missing and not unsafe
    return ParentEvaluationReport(
        valid=valid,
        parent_sha=parent_sha,
        candidate_sha=candidate_sha,
        inspected_paths=inspected,
        changed_paths=tuple(sorted(changed)),
        missing_paths=tuple(sorted(missing)),
        unsafe_paths=tuple(sorted(unsafe)),
    )


def _json_report(report: ParentEvaluationReport) -> str:
    payload = asdict(report)
    payload["reasons"] = list(report.reasons)
    return json.dumps(payload, sort_keys=True)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compare passive candidate evaluator inputs against a trusted parent snapshot."
    )
    parser.add_argument("--parent", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--parent-sha", required=True)
    parser.add_argument("--candidate-sha", required=True)
    args = parser.parse_args(list(argv) if argv is not None else None)

    report = evaluate_candidate_against_parent(
        args.parent,
        args.candidate,
        parent_sha=args.parent_sha,
        candidate_sha=args.candidate_sha,
    )
    print(_json_report(report))
    return 0 if report.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
