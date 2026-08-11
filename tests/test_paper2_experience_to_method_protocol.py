"""Design-freeze tests for experience-to-method protocol (#157)."""

from __future__ import annotations

import json
from pathlib import Path

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None


PROTOCOL_PATH = Path("research/paper2_experience_to_method_v1/PROTOCOL_V1_DRAFT.json")
SCHEMA_PATH = Path("schemas/paper2-experience-to-method-protocol-v2.schema.json")


def test_experience_to_method_draft_is_pending_freeze_not_protocol_frozen() -> None:
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    assert protocol["status"] == "DRAFT"
    assert protocol["grants_scientific_authority"] is False
    assert protocol["issue"] == 157
    assert protocol["execution_coordinates"]["protocol_status"] == "DRAFT_NOT_PROTOCOL_FROZEN"
    sentinels = protocol["execution_coordinates"]["pending_freeze_sentinels"]
    assert sentinels
    assert all(s.startswith("PENDING_FREEZE_") for s in sentinels)
    # PROTOCOL_FROZEN and PENDING_FREEZE_* must not co-exist as a frozen claim.
    assert protocol["status"] != "PROTOCOL_FROZEN"
    assert protocol["admissibility_gates"]["G1_verified_corrective_object"][
        "pseudo_lessons_count_toward_gate"
    ] is False
    assert protocol["admissibility_gates"]["G1_verified_corrective_object"]["on_failure"] == (
        "CANNOT_IDENTIFY"
    )
    assert protocol["assurance_chronometry"]["candidate_frozen_before_assurance"] is True


def test_experience_to_method_draft_matches_schema() -> None:
    if jsonschema is None:
        return
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(protocol, schema)
