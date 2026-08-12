"""Tests for application-facing shadow/proposal artifact hash helpers (#397)."""

from __future__ import annotations

from rakl.shadow_artifact_hash import (
    DigestMode,
    assert_stale_hash_fails,
    bind_artifact_hash,
    canonical_bytes,
    hash_document,
    parse_digest,
    verify_document_hash,
)


def test_canonical_bytes_are_deterministic_and_key_sorted() -> None:
    left = {"b": 2, "a": 1}
    right = {"a": 1, "b": 2}
    assert canonical_bytes(left) == canonical_bytes(right)
    assert canonical_bytes(left) == b'{"a":1,"b":2}'


def test_hash_excludes_artifact_hash_field_by_default() -> None:
    base = {"episode_id": "e1", "payload": "x", "artifact_hash": "0" * 64}
    without = {"episode_id": "e1", "payload": "x"}
    assert hash_document(base) == hash_document(without)


def test_bind_and_verify_round_trip_raw_and_prefixed() -> None:
    doc = {"kind": "proposal_shadow", "note": "no authority", "score": 0}
    raw = bind_artifact_hash(doc, mode=DigestMode.RAW)
    ok, reasons = verify_document_hash(raw)
    assert ok and reasons == ()
    assert len(raw["artifact_hash"]) == 64

    prefixed = bind_artifact_hash(doc, mode=DigestMode.SHA256_PREFIXED)
    ok, reasons = verify_document_hash(prefixed)
    assert ok and reasons == ()
    assert prefixed["artifact_hash"].startswith("sha256:")
    assert parse_digest(prefixed["artifact_hash"]) == raw["artifact_hash"]


def test_stale_hash_fails_closed_after_payload_mutation() -> None:
    doc = {"kind": "proposal_shadow", "body": "original"}
    assert_stale_hash_fails(doc, mutate_key="body", mutate_value="tampered")


def test_verify_does_not_grant_authority_semantics() -> None:
    """Matching digest is provenance ergonomics only — never scientific authority."""

    doc = bind_artifact_hash(
        {
            "claim": "I am a theorem",
            "grants_scientific_authority": False,
        }
    )
    ok, _ = verify_document_hash(doc)
    assert ok
    # Helper contract: callers must still treat proposal/shadow as proposal-only.
    assert doc.get("grants_scientific_authority") is False


def test_malformed_digest_fails_closed() -> None:
    doc = {"kind": "x", "artifact_hash": "sha256:not-a-digest"}
    ok, reasons = verify_document_hash(doc)
    assert not ok
    assert "artifact_hash_malformed" in reasons


def test_missing_hash_field_fails_closed() -> None:
    ok, reasons = verify_document_hash({"kind": "x"})
    assert not ok
    assert reasons == ("artifact_hash_missing",)
