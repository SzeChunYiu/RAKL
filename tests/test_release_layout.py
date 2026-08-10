from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "paper" / "finalize_release_layout.py"


def _module():
    spec = importlib.util.spec_from_file_location("rakl_finalize_release_layout", HELPER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_layout_adjustment_is_exact_and_fails_on_second_application(tmp_path: Path):
    module = _module()
    manuscript = tmp_path / "main.tex"
    manuscript.write_text(
        "before\n"
        + module.OLD_BIBLIOGRAPHY_LAYOUT
        + "\n"
        + module.SCHMIDT_REFERENCE_ANCHOR
        + " Science, 324(5923):81--85, 2009.\n"
        + "after\n",
        encoding="utf-8",
    )
    module.finalize_release_layout(manuscript)
    text = manuscript.read_text(encoding="utf-8")
    assert module.OLD_BIBLIOGRAPHY_LAYOUT not in text
    assert module.NEW_BIBLIOGRAPHY_LAYOUT in text
    assert module.SCHMIDT_REFERENCE_WRAPPED in text
    assert module.SCHMIDT_REFERENCE_ANCHOR + " Science" not in text

    try:
        module.finalize_release_layout(manuscript)
    except RuntimeError as error:
        assert "observed 0" in str(error)
    else:
        raise AssertionError("release layout adjustment must fail closed after its exact anchors are consumed")
