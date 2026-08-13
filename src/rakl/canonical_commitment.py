"""Versioned canonical commitments for identity-bearing RAKL objects.

This is deliberately *not* RFC 8785/JCS: RAKL commits typed Python-domain
values (Decimal, Fraction, dataclasses, sets, bytes) that are outside plain
JSON.  The wire contract is therefore its own versioned scheme.  In contrast
to the historical ``repr(...)`` fingerprints, this encoder is explicit about
numeric types, Unicode policy, unordered collections, cycles, and domains.

The default string policy is PRESERVE.  Authority boundaries that require NFC
should use REQUIRE_NFC (rejecting rather than silently rewriting inputs).
"""
from __future__ import annotations

import base64
import dataclasses
import datetime as dt
import hashlib
import json
import math
import struct
import unicodedata
from collections.abc import Mapping, Sequence, Set
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from fractions import Fraction
from pathlib import PurePath
from typing import Any

SCHEMA = "rakl.typed-canonical.v2"
_PREFIX = b"RAKL-TYPED-CANONICAL-V2\x00"


class CanonicalizationError(ValueError):
    pass


class UnicodePolicy(str, Enum):
    PRESERVE = "PRESERVE"
    REQUIRE_NFC = "REQUIRE_NFC"
    NORMALIZE_NFC = "NORMALIZE_NFC"


@dataclass(frozen=True)
class CanonicalProfile:
    unicode_policy: UnicodePolicy = UnicodePolicy.PRESERVE
    decimal_semantics: str = "NUMERIC_VALUE"
    float_semantics: str = "IEEE754_BINARY64_BITS"
    datetime_semantics: str = "UTC_INSTANT_MICROSECOND"
    path_semantics: str = "CLASS_AND_POSIX_TEXT"

    def __post_init__(self) -> None:
        if self.decimal_semantics != "NUMERIC_VALUE":
            raise ValueError("v2 supports only NUMERIC_VALUE Decimal semantics")
        if self.float_semantics != "IEEE754_BINARY64_BITS":
            raise ValueError("v2 supports only IEEE754_BINARY64_BITS float semantics")
        if self.datetime_semantics != "UTC_INSTANT_MICROSECOND":
            raise ValueError("v2 supports only UTC_INSTANT_MICROSECOND datetime semantics")
        if self.path_semantics != "CLASS_AND_POSIX_TEXT":
            raise ValueError("v2 supports only CLASS_AND_POSIX_TEXT path semantics")


DEFAULT_PROFILE = CanonicalProfile()


def _validate_scalar_string(value: str) -> None:
    # UTF-8 cannot encode lone surrogates portably; fail with a typed error.
    if any(0xD800 <= ord(ch) <= 0xDFFF for ch in value):
        raise CanonicalizationError("lone Unicode surrogate is forbidden")


def _string(value: str, profile: CanonicalProfile) -> str:
    _validate_scalar_string(value)
    if profile.unicode_policy is UnicodePolicy.PRESERVE:
        return value
    normalized = unicodedata.normalize("NFC", value)
    if profile.unicode_policy is UnicodePolicy.REQUIRE_NFC:
        if normalized != value:
            raise CanonicalizationError("string is not NFC under REQUIRE_NFC policy")
        return value
    return normalized


def _decimal_value_tuple(value: Decimal) -> list[object]:
    """Context-free finite Decimal numeric-value representation.

    No Decimal arithmetic is performed.  This avoids ``Decimal.normalize()``,
    which rounds in the ambient context before reducing trailing zeros.
    """
    if not value.is_finite():
        raise CanonicalizationError("non-finite Decimal is forbidden")
    parts = value.as_tuple()
    digits = list(parts.digits)
    exponent = int(parts.exponent)
    if not digits or all(d == 0 for d in digits):
        return [0, "0", 0]
    while len(digits) > 1 and digits[-1] == 0:
        digits.pop()
        exponent += 1
    return [int(parts.sign), "".join(str(d) for d in digits), exponent]


def parse_decimal(value: str | int | float | Decimal) -> Decimal:
    if isinstance(value, bool):
        raise CanonicalizationError("bool is not a Decimal input")
    try:
        result = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise CanonicalizationError("invalid Decimal input") from exc
    if not result.is_finite():
        raise CanonicalizationError("non-finite Decimal is forbidden")
    return result


def _tag(name: str, value: object) -> dict[str, object]:
    return {"@type": name, "value": value}


def _tracked(value: Any) -> bool:
    return (
        dataclasses.is_dataclass(value)
        or isinstance(value, (Mapping, list, tuple, set, frozenset))
        or (isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)))
        or isinstance(value, Set)
        or callable(getattr(value, "to_canonical", None))
    )


def _text(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))


def normalize(value: Any, *, profile: CanonicalProfile = DEFAULT_PROFILE) -> object:
    return _normalize(value, profile=profile, active=set())


def _normalize(value: Any, *, profile: CanonicalProfile, active: set[int]) -> object:
    if isinstance(value, Enum):
        return _tag("enum", {
            "class": f"{value.__class__.__module__}.{value.__class__.__qualname__}",
            "value": _normalize(value.value, profile=profile, active=active),
        })
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, str):
        return _string(value, profile)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CanonicalizationError("NaN and infinity are forbidden")
        return _tag("float64-bits", struct.pack(">d", value).hex())
    if isinstance(value, Decimal):
        return _tag("decimal-value", _decimal_value_tuple(value))
    if isinstance(value, Fraction):
        return _tag("fraction", [value.numerator, value.denominator])
    if isinstance(value, bytes):
        return _tag("bytes-base64", base64.b64encode(value).decode("ascii"))
    if isinstance(value, dt.datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise CanonicalizationError("datetime must be timezone-aware")
        utc = value.astimezone(dt.timezone.utc)
        return _tag("datetime-utc", utc.isoformat(timespec="microseconds").replace("+00:00", "Z"))
    if isinstance(value, dt.date):
        return _tag("date", value.isoformat())
    if isinstance(value, PurePath):
        return _tag("path-flavored", {
            "class": f"{value.__class__.__module__}.{value.__class__.__qualname__}",
            "posix": value.as_posix(),
        })

    object_id = id(value)
    track = _tracked(value)
    if track:
        if object_id in active:
            raise CanonicalizationError("cyclic object graphs are forbidden")
        active.add(object_id)
    try:
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            rows = []
            for field in dataclasses.fields(value):
                rows.append([
                    field.name,
                    _normalize(getattr(value, field.name), profile=profile, active=active),
                ])
            return _tag("dataclass", {
                "class": f"{value.__class__.__module__}.{value.__class__.__qualname__}",
                "fields": rows,
            })
        if isinstance(value, Mapping):
            rows: list[list[object]] = []
            seen: dict[str, str] = {}
            for key, item in value.items():
                if not isinstance(key, str):
                    raise CanonicalizationError("canonical mappings require string keys")
                canonical_key = _string(key, profile)
                previous = seen.get(canonical_key)
                if previous is not None and previous != key:
                    raise CanonicalizationError(
                        f"Unicode-policy key collision between {previous!r} and {key!r}"
                    )
                seen[canonical_key] = key
                rows.append([
                    canonical_key,
                    _normalize(item, profile=profile, active=active),
                ])
            rows.sort(key=lambda row: str(row[0]).encode("utf-8"))
            return _tag("mapping", rows)
        if isinstance(value, (set, frozenset)) or isinstance(value, Set):
            by_text: dict[str, object] = {}
            for item in value:
                normalized = _normalize(item, profile=profile, active=active)
                text = _text(normalized)
                if text in by_text:
                    raise CanonicalizationError("distinct set members share canonical representation")
                by_text[text] = normalized
            return _tag("set", [by_text[key] for key in sorted(by_text)])
        if isinstance(value, tuple):
            return _tag("tuple", [_normalize(x, profile=profile, active=active) for x in value])
        if isinstance(value, list):
            return _tag("list", [_normalize(x, profile=profile, active=active) for x in value])
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return _tag("sequence", [_normalize(x, profile=profile, active=active) for x in value])
        converter = getattr(value, "to_canonical", None)
        if callable(converter):
            return _normalize(converter(), profile=profile, active=active)
    finally:
        if track:
            active.remove(object_id)
    raise CanonicalizationError(
        f"unsupported type: {value.__class__.__module__}.{value.__class__.__qualname__}"
    )


def canonical_json_bytes(value: Any, *, profile: CanonicalProfile = DEFAULT_PROFILE) -> bytes:
    envelope = {
        "schema": SCHEMA,
        "profile": {
            "unicode_policy": profile.unicode_policy.value,
            "decimal_semantics": profile.decimal_semantics,
            "float_semantics": profile.float_semantics,
            "datetime_semantics": profile.datetime_semantics,
            "path_semantics": profile.path_semantics,
        },
        "payload": normalize(value, profile=profile),
    }
    try:
        return _text(envelope).encode("utf-8")
    except UnicodeEncodeError as exc:
        raise CanonicalizationError("canonical payload contains invalid Unicode") from exc


def canonical_json_text(value: Any, *, profile: CanonicalProfile = DEFAULT_PROFILE) -> str:
    return canonical_json_bytes(value, profile=profile).decode("utf-8")


def sha256_digest(value: Any, *, domain: str, profile: CanonicalProfile = DEFAULT_PROFILE) -> str:
    if not isinstance(domain, str) or not domain.strip() or domain != domain.strip():
        raise CanonicalizationError("non-empty exact digest domain required")
    _validate_scalar_string(domain)
    domain_bytes = domain.encode("utf-8")
    body = _PREFIX + len(domain_bytes).to_bytes(4, "big") + domain_bytes + canonical_json_bytes(value, profile=profile)
    return "sha256:" + hashlib.sha256(body).hexdigest()


def raw_sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()
