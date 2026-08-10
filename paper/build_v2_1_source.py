from __future__ import annotations

import argparse
import base64
import bz2
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V2_RELEASE = ROOT / "paper" / "arxiv_release_v2_2026-08-10"
V2_EXPECTED_SHA256 = "4adec2bb256775823dde3b5f520a9ef599c4fe95078121a513ce71e301ac5302"
PARTS = (
    "main.tex.bz2.b64.part01",
    "main.tex.bz2.b64.part02a",
    "main.tex.bz2.b64.part02b",
    "main.tex.bz2.b64.part03",
    "main.tex.bz2.b64.part04",
)


def decode_v2_source() -> str:
    encoded = "".join((V2_RELEASE / name).read_text(encoding="utf-8").strip() for name in PARTS)
    raw = bz2.decompress(base64.b64decode(encoded, validate=True))
    digest = hashlib.sha256(raw).hexdigest()
    if digest != V2_EXPECTED_SHA256:
        raise RuntimeError(f"reviewed V2 source digest mismatch: {digest}")
    return raw.decode("utf-8")


def inspection_report(text: str) -> str:
    needles = (
        "SoftwareTests",
        "ImplementationSHA",
        "Known-answer engineering trace",
        "Obsidian analogy",
        "fig5_demo_growth",
        "fig6_demo_context",
        "Current evidence boundary",
        "Limitations",
        "Reproducibility",
        "\\begin{thebibliography}",
        "\\end{thebibliography}",
    )
    lines = text.splitlines()
    output: list[str] = ["=== SECTION HEADINGS ==="]
    output.extend(
        f"{index + 1:04d}: {line}"
        for index, line in enumerate(lines)
        if line.lstrip().startswith(("\\section", "\\subsection", "\\paragraph"))
    )
    for needle in needles:
        matches = [index for index, line in enumerate(lines) if needle in line]
        output.append(f"=== {needle} ===")
        if not matches:
            output.append("NOT FOUND")
            continue
        for index in matches[:3]:
            start = max(0, index - 3)
            stop = min(len(lines), index + 5)
            output.extend(f"{line_no + 1:04d}: {lines[line_no]}" for line_no in range(start, stop))

    for start, stop in ((292, 370), (430, 491)):
        output.append(f"=== LINES {start}-{stop} ===")
        for line_no in range(start - 1, min(len(lines), stop)):
            output.append(f"{line_no + 1:04d}: {lines[line_no]}")
    return "\n".join(output) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    source = decode_v2_source()
    if args.inspect:
        print(inspection_report(source), end="")
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(source, encoding="utf-8")
    if not args.inspect and args.output is None:
        print(hashlib.sha256(source.encode("utf-8")).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
