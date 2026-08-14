import json

from rakl.agent_authority_gateway import parse_raw_untrusted_agent_authority_json

BASE = {
    "claim_id": "raw-claim",
    "axis": "R",
    "proposition": "registered representation claim",
    "scope_id": "raw-scope",
    "evidence_ids": ["ev-1"],
}


def _raw(**updates):
    value = dict(BASE)
    value.update(updates)
    return json.dumps(value, separators=(",", ":"))


def test_canonical_raw_json_reaches_only_inert_proposal():
    result = parse_raw_untrusted_agent_authority_json(_raw())
    assert result.accepted_to_proposal_plane
    assert result.proposal is not None
    assert result.grants_scientific_authority is False


def test_duplicate_allowed_key_is_rejected_not_last_key_wins():
    raw = '{"claim_id":"a","claim_id":"b","axis":"R","proposition":"p","scope_id":"s","evidence_ids":["e"]}'
    result = parse_raw_untrusted_agent_authority_json(raw)
    assert not result.accepted_to_proposal_plane
    assert any("duplicate_json_key:claim_id" in reason for reason in result.reasons)


def test_duplicate_forbidden_control_key_is_rejected():
    raw = '{"claim_id":"a","axis":"R","proposition":"p","scope_id":"s","evidence_ids":["e"],"attestation_id":"x","attestation_id":"y"}'
    result = parse_raw_untrusted_agent_authority_json(raw)
    assert not result.accepted_to_proposal_plane


def test_non_object_root_and_trailing_second_object_fail_closed():
    assert not parse_raw_untrusted_agent_authority_json('[1,2,3]').accepted_to_proposal_plane
    assert not parse_raw_untrusted_agent_authority_json(_raw() + _raw()).accepted_to_proposal_plane


def test_nonfinite_and_framing_ambiguity_fail_closed():
    assert not parse_raw_untrusted_agent_authority_json('{"claim_id":NaN}').accepted_to_proposal_plane
    assert not parse_raw_untrusted_agent_authority_json("\ufeff" + _raw()).accepted_to_proposal_plane
    assert not parse_raw_untrusted_agent_authority_json(_raw() + "\x00").accepted_to_proposal_plane


def test_oversized_and_deep_payloads_fail_closed():
    too_large = _raw(proposition="x" * 17000)
    assert not parse_raw_untrusted_agent_authority_json(too_large).accepted_to_proposal_plane
    deep = dict(BASE)
    deep["metadata"] = {"a": {"b": {"c": {"attestation_id": "fake"}}}}
    result = parse_raw_untrusted_agent_authority_json(json.dumps(deep))
    assert not result.accepted_to_proposal_plane


def test_nested_or_unicode_lookalike_control_fields_cannot_hide():
    nested = dict(BASE)
    nested["metadata"] = {"attestation_id": "fake", "certificate_id": "fake"}
    assert not parse_raw_untrusted_agent_authority_json(json.dumps(nested)).accepted_to_proposal_plane
    lookalike = dict(BASE)
    lookalike["attestatiоn_id"] = "fake"  # Cyrillic o: unknown field, never normalized into authority.
    result = parse_raw_untrusted_agent_authority_json(json.dumps(lookalike, ensure_ascii=False))
    assert not result.accepted_to_proposal_plane
    assert any("unknown_fields" in reason for reason in result.reasons)
