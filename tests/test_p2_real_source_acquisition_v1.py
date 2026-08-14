from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_p2_real_source_acquisition_v1.py"
spec = importlib.util.spec_from_file_location("p2_real_source_acquisition_v1", SCRIPT)
assert spec and spec.loader
B = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B)


def test_public_acquisition_packet_is_candidate_blind_and_source_bound():
    public, linkage = B.build()
    assert public["item_count"] == 16
    assert linkage["item_count"] == 16
    assert public["source_set_file_sha256"] == B.EXPECTED_SOURCE_FILE_SHA256
    assert linkage["source_set_file_sha256"] == B.EXPECTED_SOURCE_FILE_SHA256
    ids = [row["opaque_item_id"] for row in public["items"]]
    assert len(ids) == len(set(ids)) == 16
    assert set(ids) == {row["opaque_item_id"] for row in linkage["items"]}
    for row in public["items"]:
        assert not (set(row) & B.FORBIDDEN_PUBLIC_KEYS)
        assert row["source_reference"]
        assert row["target_reference"]
        for ref in row["source_reference"] + row["target_reference"]:
            assert ref["identifier"]
            assert ref["title"]
            assert ref["locator"].startswith("http")
        assert "CANNOT_CHECK" in row["instruction"]
    assert linkage["candidate_visible"] is False
    assert linkage["development_only"] is True
    assert linkage["grants_scientific_authority"] is False


def test_internal_candidate_coordinates_never_appear_on_public_surface():
    public, linkage = B.build()
    public_text = B._canonical_bytes(public).decode("utf-8")
    for key in B.FORBIDDEN_PUBLIC_KEYS:
        assert f'"{key}"' not in public_text
    internal = linkage["items"]
    assert any(row["development_only_internal_coordinates"] for row in internal)


def test_opaque_ids_do_not_reveal_legacy_source_ids():
    public, linkage = B.build()
    for public_row, linkage_row in zip(public["items"], linkage["items"]):
        assert linkage_row["source_item_id"] not in public_row["opaque_item_id"]
        assert public_row["opaque_item_id"].startswith("rs-")
        assert len(public_row["opaque_item_id"]) == 19


def test_instrument_explicitly_cannot_authorize_empirical_claim():
    protocol = __import__("json").loads(
        (ROOT / "research/paper2_real_source_span_v1/PROTOCOL.json").read_text()
    )
    assert protocol["current_allowed_terminal"] == "INSTRUMENT_ONLY__NO_EMPIRICAL_EXTRACTION_CLAIM"
    assert protocol["grants_scientific_authority"] is False
    assert "natural-language witness extraction" in protocol["development_only_gate"]["not_a_promotion_of"]
