from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1] / "publication" / "papers"
CITE_RE = re.compile(r"\\(?:cite|citep|citet|citealp|citeauthor|citeyear|nocite)(?:\[[^\]]*\])*\{([^}]*)\}")
BIB_RE = re.compile(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}")


def keys_from_cites(text: str) -> set[str]:
    out: set[str] = set()
    for match in CITE_RE.finditer(text):
        for key in match.group(1).split(","):
            key = key.strip()
            if key and key != "*":
                out.add(key)
    return out


def main() -> int:
    failed = False
    for paper in sorted(p for p in ROOT.iterdir() if p.is_dir()):
        texts: list[tuple[Path, str]] = []
        for path in paper.rglob("*.tex"):
            try:
                texts.append((path, path.read_text(encoding="utf-8")))
            except UnicodeDecodeError as exc:
                print(f"{paper.name}: NON_UTF8 {path.relative_to(paper)}: {exc}")
                failed = True

        citations: set[str] = set()
        bib_counts: dict[str, int] = {}
        for _path, text in texts:
            citations |= keys_from_cites(text)
            for key in BIB_RE.findall(text):
                bib_counts[key] = bib_counts.get(key, 0) + 1

        bib = set(bib_counts)
        missing = sorted(citations - bib)
        duplicate = sorted(key for key, count in bib_counts.items() if count > 1)
        unused = sorted(bib - citations)

        print(f"=== {paper.name} ===")
        print(f"citation_keys={len(citations)} bibitems={len(bib)} missing={len(missing)} duplicate_bibitems={len(duplicate)} unused={len(unused)}")
        if missing:
            print("MISSING: " + ", ".join(missing))
            failed = True
        if duplicate:
            print("DUPLICATE_BIBITEM: " + ", ".join(duplicate))
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
