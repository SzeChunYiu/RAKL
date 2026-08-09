from pathlib import Path

import pytest

from rakl.parent_evaluator import (
    ParentEvaluatorPolicy,
    evaluate_candidate_against_parent,
)


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _policy() -> ParentEvaluatorPolicy:
    return ParentEvaluatorPolicy(
        protected_files=("pyproject.toml", "src/rakl/evaluator.py"),
        protected_roots=("tests",),
    )


def _world(tmp_path: Path) -> tuple[Path, Path]:
    parent = tmp_path / "parent"
    candidate = tmp_path / "candidate"
    for root in (parent, candidate):
        _write(root, "pyproject.toml", "[tool.pytest.ini_options]\ntestpaths=['tests']\n")
        _write(root, "src/rakl/evaluator.py", "TRUSTED = True\n")
        _write(root, "tests/test_core.py", "def test_core(): assert True\n")
    return parent, candidate


def _evaluate(parent: Path, candidate: Path):
    return evaluate_candidate_against_parent(
        parent,
        candidate,
        parent_sha="parent-sha",
        candidate_sha="candidate-sha",
        policy=_policy(),
    )


def test_clean_subject_only_candidate_passes_parent_integrity(tmp_path: Path) -> None:
    parent, candidate = _world(tmp_path)
    _write(candidate, "src/rakl/subject.py", "CHANGED = True\n")

    report = _evaluate(parent, candidate)

    assert report.valid
    assert report.changed_paths == ()
    assert report.missing_paths == ()
    assert report.unsafe_paths == ()


def test_candidate_supplemental_test_is_allowed_but_cannot_replace_parent_test(tmp_path: Path) -> None:
    parent, candidate = _world(tmp_path)
    _write(candidate, "tests/test_supplemental.py", "def test_extra(): assert True\n")

    report = _evaluate(parent, candidate)

    assert report.valid
    assert "tests/test_supplemental.py" not in report.inspected_paths

    _write(candidate, "tests/test_core.py", "def test_core(): assert False\n")
    report = _evaluate(parent, candidate)
    assert not report.valid
    assert report.changed_paths == ("tests/test_core.py",)


def test_pytest_discovery_tampering_is_rejected(tmp_path: Path) -> None:
    parent, candidate = _world(tmp_path)
    _write(candidate, "pyproject.toml", "[tool.pytest.ini_options]\ntestpaths=['hostile_tests']\n")
    _write(candidate, "hostile_tests/test_smoke.py", "def test_smoke(): assert True\n")

    report = _evaluate(parent, candidate)

    assert not report.valid
    assert report.changed_paths == ("pyproject.toml",)


def test_missing_parent_owned_test_is_rejected(tmp_path: Path) -> None:
    parent, candidate = _world(tmp_path)
    (candidate / "tests/test_core.py").unlink()

    report = _evaluate(parent, candidate)

    assert not report.valid
    assert report.missing_paths == ("tests/test_core.py",)


def test_parent_judge_edit_is_rejected(tmp_path: Path) -> None:
    parent, candidate = _world(tmp_path)
    _write(candidate, "src/rakl/evaluator.py", "TRUSTED = False\n")

    report = _evaluate(parent, candidate)

    assert not report.valid
    assert report.changed_paths == ("src/rakl/evaluator.py",)


def test_symlink_at_protected_candidate_path_is_rejected_without_following_it(tmp_path: Path) -> None:
    parent, candidate = _world(tmp_path)
    target = tmp_path / "outside.txt"
    target.write_text("outside", encoding="utf-8")
    protected = candidate / "pyproject.toml"
    protected.unlink()
    try:
        protected.symlink_to(target)
    except OSError:
        pytest.skip("symlinks unavailable in this environment")

    report = _evaluate(parent, candidate)

    assert not report.valid
    assert report.unsafe_paths == ("pyproject.toml",)


def test_parent_and_candidate_roots_must_be_distinct(tmp_path: Path) -> None:
    parent, _ = _world(tmp_path)

    with pytest.raises(ValueError, match="distinct"):
        evaluate_candidate_against_parent(
            parent,
            parent,
            parent_sha="parent-sha",
            candidate_sha="candidate-sha",
            policy=_policy(),
        )


def test_empty_revision_identity_is_rejected(tmp_path: Path) -> None:
    parent, candidate = _world(tmp_path)

    with pytest.raises(ValueError, match="parent_sha"):
        evaluate_candidate_against_parent(
            parent,
            candidate,
            parent_sha="",
            candidate_sha="candidate-sha",
            policy=_policy(),
        )
