from __future__ import annotations

import argparse
from pathlib import Path


OLD_BIBLIOGRAPHY_LAYOUT = "\n".join(
    (
        r"\sloppy",
        r"\small",
        r"\setlength{\emergencystretch}{1em}",
        r"\begin{thebibliography}{99}",
    )
)
NEW_BIBLIOGRAPHY_LAYOUT = "\n".join(
    (
        r"\sloppy",
        r"\small",
        r"\setlength{\emergencystretch}{3em}",
        r"\begin{thebibliography}{99}",
    )
)


def finalize_release_layout(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    observed = text.count(OLD_BIBLIOGRAPHY_LAYOUT)
    if observed != 1:
        raise RuntimeError(
            "expected exactly one reviewed bibliography-layout anchor, "
            f"observed {observed} in {path}"
        )
    updated = text.replace(
        OLD_BIBLIOGRAPHY_LAYOUT,
        NEW_BIBLIOGRAPHY_LAYOUT,
        1,
    )
    path.write_text(updated, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply the deterministic release-only bibliography line-wrap adjustment."
    )
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    finalize_release_layout(args.path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
