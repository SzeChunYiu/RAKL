from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "paper" / "build_v2_1_source.py"
DUMMY_SHA = "0123456789abcdef0123456789abcdef01234567"
DUMMY_TESTS = 777


def _module():
    spec = importlib.util.spec_from_file_location("rakl_v2_1_source_builder", BUILDER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v2_parent_source_reconstructs_exact_reviewed_digest():
    module = _module()
    source = module.decode_v2_source()
    import hashlib

    assert hashlib.sha256(source.encode("utf-8")).hexdigest() == module.V2_EXPECTED_SHA256
    assert source.count("\\bibitem{") == 59
    assert source.count("\\begin{figure}") == 6


def test_v2_1_patch_binds_exact_subject_and_software_test_count():
    source = _module().build_v2_1_source(subject_sha=DUMMY_SHA, software_tests=DUMMY_TESTS)
    assert f"\\newcommand{{\\SoftwareTests}}{{{DUMMY_TESTS}}}" in source
    assert f"\\newcommand{{\\ImplementationSHA}}{{\\texttt{{{DUMMY_SHA}}}}}" in source
    assert "5995e99b0ef5e8d192a786c082ea880acadaab88" not in source
    assert "\\newcommand{\\SoftwareTests}{627}" not in source


def test_v2_1_metrology_claims_are_basis_bound_and_noncompensatory():
    source = _module().build_v2_1_source(subject_sha=DUMMY_SHA, software_tests=DUMMY_TESTS)
    assert "PENDULUM\\_FIBER\\_KIND\\_METROLOGY\\_V1" in source
    assert "a changed basis makes the comparison invalid" in source
    assert "Geometry is reported separately from target-conditioned scientific progress" in source
    assert "R2$\\rightarrow$R3 adds an independent evidence root without opening another target path" in source
    assert "ontology refinement cannot count as knowledge growth by itself" in source


def test_v2_1_memory_and_learning_semantics_are_explicit():
    source = _module().build_v2_1_source(subject_sha=DUMMY_SHA, software_tests=DUMMY_TESTS)
    assert "external-state learning, not implicit modification of the base LLM weights" in source
    assert "A contextual scientific projection selects" in source
    assert "normalization aligns units" in source
    assert "optional embedding projects a view into retrieval space" in source
    assert "lossy summary can save tokens" in source
    assert "cannot replace the raw evidence required for a strong verification operation" in source


def test_v2_1_archive_scaling_numbers_are_machine_receipt_values_and_scoped():
    source = _module().build_v2_1_source(subject_sha=DUMMY_SHA, software_tests=DUMMY_TESTS)
    for text in (
        "826 bytes",
        "739 bytes",
        "826 to 892 bytes",
        "273 hot bytes",
        "total stored bytes and all canonical records remain unchanged",
    ):
        assert text in source
    assert "reference-backend engineering measurements" in source
    assert "not production-scale storage or scientific-performance claims" in source


def test_v2_1_obsidian_miss_reopens_external_discovery_without_fake_transfer_credit():
    source = _module().build_v2_1_source(subject_sha=DUMMY_SHA, software_tests=DUMMY_TESTS)
    assert "EXOGENOUS\\_CONCEPT\\_MISS" in source
    assert "function-first" in source
    assert "adjacent-discipline" in source
    assert "adversarial-prior-art" in source
    assert "external-discovery saturation reopens" in source
    assert "not prospective transfer evidence" in source


def test_v2_1_matched_workflow_has_common_resource_ceiling_and_actual_usage_reporting():
    source = _module().build_v2_1_source(subject_sha=DUMMY_SHA, software_tests=DUMMY_TESTS)
    assert "common preregistered resource ceiling" in source
    assert "preprocessing model tokens" in source
    assert "actual resource use may differ because preprocessing is part of the intervention" in source
    assert "every arm must report its usage and remain within the same envelope" in source


def test_v2_1_quantitative_figures_use_receipt_bound_wrappers_without_old_resizeboxes():
    source = _module().build_v2_1_source(subject_sha=DUMMY_SHA, software_tests=DUMMY_TESTS)
    assert "\\input{fig5_demo_growth.tex}" in source
    assert "\\input{fig6_demo_context.tex}" in source
    assert "\\resizebox{0.78\\textwidth}{!}{\\input{fig5_demo_growth.tex}}" not in source
    assert "\\resizebox{0.88\\textwidth}{!}{\\input{fig6_demo_context.tex}}" not in source
    assert "Knowledge geometry and target-conditioned value are distinct" in source
    assert "Archive, active context and hot storage are controlled separately" in source
    assert source.count("\\begin{figure}") == 6


def test_v2_1_adds_four_scoped_prior_art_references_and_uses_clean_reference_layout():
    source = _module().build_v2_1_source(subject_sha=DUMMY_SHA, software_tests=DUMMY_TESTS)
    assert source.count("\\bibitem{") == 63
    for key in ("rissanen1978", "tishby2000", "w3cprov2013", "skjaeveland2023"):
        assert f"\\bibitem{{{key}}}" in source
        assert f"{{{key}}}" in source
    assert "PROV-O" in source
    assert "information bottleneck method" in source.lower()
    assert "Personal Knowledge Graphs" in source
    assert (
        "\\sloppy\n\\small\n\\setlength{\\emergencystretch}{1em}\n"
        "\\begin{thebibliography}{99}"
    ) in source


def test_v2_1_public_source_preserves_evidence_boundary_and_no_result_placeholders():
    source = _module().build_v2_1_source(subject_sha=DUMMY_SHA, software_tests=DUMMY_TESTS)
    assert "[[RESULT:" not in source
    assert "not evidence of scientific superiority" in source
    assert "preregistered and unexecuted" in source
    assert "not counted as independent peer review" in source
    assert "independent peer review completed" not in source
