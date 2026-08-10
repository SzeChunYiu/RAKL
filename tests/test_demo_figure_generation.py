from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "paper" / "generate_demo_figures.py"


def _module():
    spec = importlib.util.spec_from_file_location("rakl_demo_figure_generator", GENERATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_committed_demo_figure_wrappers_equal_generator_output():
    generated = _module().generate()
    for filename, expected in generated.items():
        committed = (ROOT / "paper" / "figures" / filename).read_text(encoding="utf-8")
        assert committed == expected
        assert "includegraphics" in committed
        assert "tikzpicture" not in committed


def test_demo_figures_declare_machine_receipt_sources():
    generated = _module().generate()
    assert generated["fig5_demo_growth.tex"].startswith(
        "% GENERATED FROM research/MINI_RESEARCH_METROLOGY_044_RECEIPT.json"
    )
    assert "MINI_RESEARCH_DEMO_043_RECEIPT.json" in generated["fig6_demo_context.tex"]
    assert "MINI_ARCHIVE_STORAGE_044_RECEIPT.json" in generated["fig6_demo_context.tex"]


def test_figure_source_data_exposes_basis_value_context_and_storage_coordinates():
    data = _module().figure_source_data()
    fig5 = data["fig5"]
    fig6 = data["fig6"]

    assert fig5["basis_id"] == "PENDULUM_FIBER_KIND_METROLOGY_V1"
    assert len(fig5["basis_fingerprint"]) == 64
    assert fig5["occupied_cells"] == [7, 7, 7, 7]
    assert fig5["atom_count"] == [8, 9, 9, 9]
    assert fig5["blocking_cuts"] == [1, 0, 0, 0]
    assert fig5["support_paths"] == [0, 1, 1, 1]
    assert fig5["independent_evidence_roots"] == [6, 7, 7, 8]

    assert fig6["archive_tokens"] == 270
    assert fig6["active_tokens"] == 52
    assert fig6["raw_unique_bytes"] == 826
    assert fig6["lossless_stored_bytes"] == 739
    assert fig6["hot_stored_bytes"] == 273
    assert fig6["original_physical_bytes"] == fig6["refetch_physical_bytes"] == 739
    assert fig6["records_after_refetch"] == 9
    assert fig6["unique_blobs_after_refetch"] == 8
    assert fig6["rehydration_verified"] is True


def test_matplotlib_figures_render_pdf_svg_png_and_editable_svg_text(tmp_path: Path):
    module = _module()
    module.render(tmp_path)

    for stem in ("fig5_demo_growth", "fig6_demo_context"):
        pdf = tmp_path / f"{stem}.pdf"
        svg = tmp_path / f"{stem}.svg"
        png = tmp_path / f"{stem}.png"
        source = tmp_path / f"{stem}.source.json"
        assert pdf.stat().st_size > 1000
        assert svg.stat().st_size > 1000
        assert png.stat().st_size > 1000
        assert source.stat().st_size > 100
        svg_text = svg.read_text(encoding="utf-8")
        assert "<text" in svg_text
        assert "font-size" in svg_text
        json.loads(source.read_text(encoding="utf-8"))


def test_plot_source_has_no_arrow_callouts_or_manual_receipt_numbers():
    source = GENERATOR.read_text(encoding="utf-8")
    assert "arrowprops" not in source
    assert "FancyArrow" not in source
    assert "ConnectionPatch" not in source
    # Load values by receipt keys instead of hard-coding the headline engineering numbers.
    for key in (
        '"archive_token_estimate"',
        '"active_context_tokens"',
        '"original_logical_raw_bytes"',
        '"original_stored_physical_bytes"',
        '"hot_stored_bytes_after_demotion"',
    ):
        assert key in source
