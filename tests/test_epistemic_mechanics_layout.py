from paper.build_epistemic_mechanics import build_epistemic_mechanics_source


def test_release_builder_breaks_long_formal_displays() -> None:
    text = build_epistemic_mechanics_source(
        subject_sha="a" * 40,
        software_tests=1,
    )
    assert "K_t=(&\\mathcal A_t" in text
    assert "\\begin{array}{lll}" in text
    assert "A_t(a)&=\\text{computational accessibility}" in text


def test_release_layout_repairs_leave_formal_terms_present() -> None:
    text = build_epistemic_mechanics_source(
        subject_sha="b" * 40,
        software_tests=1,
    )
    for token in (
        "\\mathcal H_t^{-}",
        "\\mathrm{PARTIALLY\\ IDENTIFIED}",
        "\\mathrm{CANNOT\\ CHECK}",
        "\\alpha_t(a)&=\\text{epistemic authority}",
    ):
        assert token in text
