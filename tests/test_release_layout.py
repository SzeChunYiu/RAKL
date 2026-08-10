from pathlib import Path

from paper.finalize_release_layout import (
    NEW_BIBLIOGRAPHY_LAYOUT,
    OLD_BIBLIOGRAPHY_LAYOUT,
    finalize_release_layout,
)


def test_release_layout_adjustment_is_exact_and_fails_on_second_application(tmp_path: Path):
    manuscript = tmp_path / "main.tex"
    manuscript.write_text(
        "before\n" + OLD_BIBLIOGRAPHY_LAYOUT + "\nafter\n",
        encoding="utf-8",
    )
    finalize_release_layout(manuscript)
    text = manuscript.read_text(encoding="utf-8")
    assert OLD_BIBLIOGRAPHY_LAYOUT not in text
    assert text == "before\n" + NEW_BIBLIOGRAPHY_LAYOUT + "\nafter\n"

    try:
        finalize_release_layout(manuscript)
    except RuntimeError as error:
        assert "observed 0" in str(error)
    else:
        raise AssertionError("release layout adjustment must fail closed after its exact anchor is consumed")
