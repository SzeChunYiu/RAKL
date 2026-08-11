from __future__ import annotations

from pathlib import Path

from rakl.repository_boundary import (
    IndexEntry,
    find_millennium_application_leaks,
    parse_git_index_entries,
    tracked_index_entries,
)


ROOT = Path(__file__).resolve().parents[1]


def _entry(path: str, *, mode: str = "100644") -> IndexEntry:
    return IndexEntry(mode=mode, object_id="a" * 40, stage=0, path=path)


def test_rejects_exact_boundary_and_descendants_case_insensitively() -> None:
    entries = (
        _entry("research/real_math/millennium"),
        _entry("research/real_math/millennium/hodge/context.json"),
        _entry("research/real_math/Millennium/hodge/context.json"),
        _entry(r"research\real_math\MILLENNIUM\hodge\context.json"),
        _entry("research/real_math/common/REVIEW_PROTOCOL.md"),
    )

    leaks = find_millennium_application_leaks(entries)

    assert [entry.path for entry in leaks] == [entry.path for entry in entries[:4]]


def test_rejects_exact_boundary_symlink_and_gitlink_modes() -> None:
    entries = (
        _entry("research/real_math/millennium", mode="120000"),
        _entry("research/real_math/MILLENNIUM", mode="160000"),
    )

    assert find_millennium_application_leaks(entries) == entries


def test_parses_nul_delimited_index_entries_without_losing_unusual_paths() -> None:
    raw = (
        b"100644 " + b"a" * 40 + b" 0\tresearch/real_math/common/ok.md\0"
        b"120000 " + b"b" * 40 + b" 0\tresearch/real_math/millennium\0"
        b"100644 "
        + b"c" * 40
        + b" 0\tresearch/real_math/millennium/name-with-newline\n.json\0"
    )

    entries = parse_git_index_entries(raw)

    assert entries == (
        IndexEntry(
            mode="100644",
            object_id="a" * 40,
            stage=0,
            path="research/real_math/common/ok.md",
        ),
        IndexEntry(
            mode="120000",
            object_id="b" * 40,
            stage=0,
            path="research/real_math/millennium",
        ),
        IndexEntry(
            mode="100644",
            object_id="c" * 40,
            stage=0,
            path="research/real_math/millennium/name-with-newline\n.json",
        ),
    )


def test_framework_index_contains_no_millennium_application_artifact() -> None:
    leaks = find_millennium_application_leaks(tracked_index_entries(ROOT))

    assert leaks == (), (
        "Problem-specific Millennium application artifacts are forbidden in "
        "the reusable RAKL framework repository; migrate them through a "
        f"separately audited RAKL_math change: {leaks}"
    )
