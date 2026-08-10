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
SCHMIDT_REFERENCE_ANCHOR = (
    "M. Schmidt and H. Lipson. Distilling free-form natural laws from experimental data."
)
SCHMIDT_REFERENCE_WRAPPED = SCHMIDT_REFERENCE_ANCHOR + r"\linebreak"


def _replace_exactly_once(text: str, old: str, new: str, label: str, path: Path) -> str:
    observed = text.count(old)
    if observed != 1:
        raise RuntimeError(
            f"expected exactly one {label} anchor, observed {observed} in {path}"
        )
    return text.replace(old, new, 1)


def finalize_release_layout(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = _replace_exactly_once(
        text,
        OLD_BIBLIOGRAPHY_LAYOUT,
        NEW_BIBLIOGRAPHY_LAYOUT,
        "reviewed bibliography-layout",
        path,
    )
    text = _replace_exactly_once(
        text,
        SCHMIDT_REFERENCE_ANCHOR,
        SCHMIDT_REFERENCE_WRAPPED,
        "Schmidt-Lipson bibliography",
        path,
    )
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Apply deterministic release-only bibliography line-wrap adjustments."
    )
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    finalize_release_layout(args.path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
