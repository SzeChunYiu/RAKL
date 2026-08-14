import hashlib
import json
from pathlib import Path

PACKET = Path("research/paper2_real_source_descriptor_v1/PROTOCOL.json")


def test_real_source_spans_are_hash_bound_and_short():
    protocol = json.loads(PACKET.read_text())
    assert protocol["scope"] == "REAL_EXTERNAL_SOURCE_SPANS__SOURCE_DESCRIPTOR_ONLY"
    assert len(protocol["sources"]) == 6
    assert {row["family"] for row in protocol["sources"]} == {
        "flow", "logic", "units", "state", "sched", "stat"
    }
    for row in protocol["sources"]:
        assert hashlib.sha256(row["span"].encode()).hexdigest() == row["span_sha256"]
        assert len(row["span"].split()) <= 25
        assert row["gold"]["mapping_status"] == "UNKNOWN"
        assert row["gold"]["application_preconditions_status"] == "UNKNOWN"
    assert protocol["grants_scientific_authority"] is False


def test_real_source_pilot_cannot_be_misreported_as_full_witness_validation():
    protocol = json.loads(PACKET.read_text())
    assert "SOURCE_DESCRIPTOR_ONLY" in protocol["scope"]
    assert "larger disjoint" in protocol["fresh_successor_if_schema_works"]
