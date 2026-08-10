from __future__ import annotations

import base64
import bz2
import hashlib
from pathlib import Path


EXPECTED_SHA256 = "4adec2bb256775823dde3b5f520a9ef599c4fe95078121a513ce71e301ac5302"
EXPECTED_REFERENCES = 59


def test_v2_paper_source_decodes_to_exact_reviewed_tex():
    root = Path(__file__).resolve().parents[1]
    release = root / "paper" / "arxiv_release_v2_2026-08-10"
    names = [
        "main.tex.bz2.b64.part01",
        "main.tex.bz2.b64.part02a",
        "main.tex.bz2.b64.part02b",
        "main.tex.bz2.b64.part03",
        "main.tex.bz2.b64.part04",
    ]
    assert sorted(part.name for part in release.glob("main.tex.bz2.b64.part*")) == sorted(names)
    encoded = "".join((release / name).read_text(encoding="utf-8").strip() for name in names)
    assert len(encoded) == 32584
    raw = bz2.decompress(base64.b64decode(encoded, validate=True))
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_SHA256
    text = raw.decode("utf-8")
    assert text.count("\\bibitem{") == EXPECTED_REFERENCES
    assert "Atomic LLM research lifecycle" in text
    assert "Known-answer engineering trace" in text
    assert "Obsidian analogy" in text
    assert "scientific superiority" in text
