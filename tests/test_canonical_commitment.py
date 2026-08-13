from decimal import Decimal, localcontext
import math
import pytest

from rakl.canonical_commitment import (
    CanonicalProfile,
    CanonicalizationError,
    UnicodePolicy,
    canonical_json_bytes,
    sha256_digest,
)


def test_mapping_order_stable():
    assert canonical_json_bytes({"b": 2, "a": 1}) == canonical_json_bytes({"a": 1, "b": 2})


def test_decimal_context_independent_and_value_canonical():
    value = Decimal("1.2345678901234567890123456789000")
    out = []
    for precision in (5, 10, 28, 50):
        with localcontext() as c:
            c.prec = precision
            out.append(canonical_json_bytes(value))
    assert len(set(out)) == 1
    assert canonical_json_bytes(Decimal("1.2300")) == canonical_json_bytes(Decimal("123e-2"))


def test_float_exact_bits_and_nonfinite_rejected():
    assert canonical_json_bytes(-0.0) != canonical_json_bytes(0.0)
    for value in (math.nan, math.inf, -math.inf):
        with pytest.raises(CanonicalizationError):
            canonical_json_bytes(value)


def test_unicode_policy_is_explicit():
    decomposed = "e\u0301"
    composed = "é"
    # Wire identity preserves exact string data by default.
    assert canonical_json_bytes(decomposed) != canonical_json_bytes(composed)
    require = CanonicalProfile(unicode_policy=UnicodePolicy.REQUIRE_NFC)
    with pytest.raises(CanonicalizationError):
        canonical_json_bytes(decomposed, profile=require)
    normalize = CanonicalProfile(unicode_policy=UnicodePolicy.NORMALIZE_NFC)
    assert canonical_json_bytes(decomposed, profile=normalize) == canonical_json_bytes(composed, profile=normalize)


def test_normalizing_mapping_collision_fails_closed():
    profile = CanonicalProfile(unicode_policy=UnicodePolicy.NORMALIZE_NFC)
    with pytest.raises(CanonicalizationError):
        canonical_json_bytes({"e\u0301": 1, "é": 2}, profile=profile)


def test_domain_separation():
    assert sha256_digest({"x": 1}, domain="a") != sha256_digest({"x": 1}, domain="b")


def test_cycles_fail_closed():
    x = []
    x.append(x)
    with pytest.raises(CanonicalizationError):
        canonical_json_bytes(x)


def test_golden_vector_freezes_v2_wire_contract():
    from rakl.canonical_commitment import canonical_json_text

    payload = {"name": "é", "decimal": Decimal("1.2300"), "float": -0.0, "items": ("a", 2)}
    assert canonical_json_text(payload) == (
        '{"payload":{"@type":"mapping","value":[["decimal",{"@type":"decimal-value","value":[0,"123",-2]}],'
        '["float",{"@type":"float64-bits","value":"8000000000000000"}],["items",{"@type":"tuple","value":["a",2]}],'
        '["name","é"]]},"profile":{"datetime_semantics":"UTC_INSTANT_MICROSECOND",'
        '"decimal_semantics":"NUMERIC_VALUE","float_semantics":"IEEE754_BINARY64_BITS",'
        '"path_semantics":"CLASS_AND_POSIX_TEXT","unicode_policy":"PRESERVE"},"schema":"rakl.typed-canonical.v2"}'
    )
    assert sha256_digest(payload, domain="rakl-golden/v1") == (
        "sha256:2216484288c14b97d91a33b65b41c83092629c612b47ad35a0d883b4f32fd5a8"
    )


def test_path_flavor_is_part_of_identity():
    from pathlib import PurePosixPath, PureWindowsPath

    assert canonical_json_bytes(PurePosixPath("C:/x")) != canonical_json_bytes(PureWindowsPath("C:/x"))
