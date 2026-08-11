"""Cross-instance reference integrity for RAKL JSON artifacts.

JSON Schema 2020-12 cannot express "this value must also appear at that other
instance location". ``$ref`` composes *schemas*, not instance data, and the
specification has no foreign-key/``key``/``keyref`` construct, so a document
whose link endpoints name ids that were never declared is still schema-valid.
That gap is exactly how a schema-valid artifact can fail executable
reconstruction (issue #133).

RAKL schemas therefore declare such constraints as machine-readable data under
the top-level ``x-rakl-reference-constraints`` keyword, and this module is the
companion validator that interprets them. The schema alone does not close the
gap; schema + companion does.

The interpreter is deliberately generic: it knows nothing about failure
lattices or any other artifact type. It resolves two instance paths and requires
every value produced by the ``from`` path to occur in the value set produced by
the ``to`` path.

Path grammar: dot-separated object keys, where a segment may end in ``[*]`` to
iterate the array stored at that key, e.g. ``links[*].source_id``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence, Tuple

REFERENCE_CONSTRAINT_KEYWORD = "x-rakl-reference-constraints"

_WILDCARD = "[*]"


@dataclass(frozen=True)
class ReferenceConstraint:
    """Every value at ``source_path`` must also occur at ``target_path``."""

    source_path: str
    target_path: str
    reason: str


def load_reference_constraints(schema: Mapping[str, Any]) -> Tuple[ReferenceConstraint, ...]:
    """Read declared reference constraints from a schema document.

    Returns an empty tuple when the schema declares none. Malformed
    declarations raise rather than being skipped: a constraint that cannot be
    interpreted must not silently degrade into "no constraint".
    """

    declared = schema.get(REFERENCE_CONSTRAINT_KEYWORD, ())
    if not isinstance(declared, Sequence) or isinstance(declared, (str, bytes)):
        raise ValueError(f"{REFERENCE_CONSTRAINT_KEYWORD} must be an array of constraint objects")

    constraints: list[ReferenceConstraint] = []
    for entry in declared:
        if not isinstance(entry, Mapping):
            raise ValueError(f"{REFERENCE_CONSTRAINT_KEYWORD} entries must be objects")
        try:
            source_path = entry["from"]
            target_path = entry["to"]
        except KeyError as error:  # pragma: no cover - defensive
            raise ValueError(
                f"{REFERENCE_CONSTRAINT_KEYWORD} entries require 'from' and 'to'"
            ) from error
        if not isinstance(source_path, str) or not isinstance(target_path, str):
            raise ValueError(f"{REFERENCE_CONSTRAINT_KEYWORD} paths must be strings")
        constraints.append(
            ReferenceConstraint(
                source_path=source_path,
                target_path=target_path,
                reason=str(entry.get("reason", "")),
            )
        )
    return tuple(constraints)


def resolve_instance_path(document: Any, path: str) -> Tuple[Any, ...]:
    """Resolve a dotted instance path, expanding ``[*]`` array segments."""

    if not path:
        raise ValueError("instance path must be non-empty")

    values: Tuple[Any, ...] = (document,)
    for segment in path.split("."):
        wildcard = segment.endswith(_WILDCARD)
        key = segment[: -len(_WILDCARD)] if wildcard else segment
        if not key:
            raise ValueError(f"invalid instance path segment in {path!r}")

        resolved: list[Any] = []
        for value in values:
            if not isinstance(value, Mapping) or key not in value:
                # Absent keys are the responsibility of the schema's own
                # `required`/type keywords, not of reference integrity.
                continue
            item = value[key]
            if wildcard:
                if isinstance(item, Sequence) and not isinstance(item, (str, bytes)):
                    resolved.extend(item)
                continue
            resolved.append(item)
        values = tuple(resolved)
    return values


def check_reference_constraints(
    document: Any, schema: Mapping[str, Any]
) -> Tuple[str, ...]:
    """Return one reason per unresolved reference; empty means the document is closed."""

    reasons: list[str] = []
    for constraint in load_reference_constraints(schema):
        declared = resolve_instance_path(document, constraint.target_path)
        known = {value for value in declared if isinstance(value, (str, int, float, bool))}
        for value in resolve_instance_path(document, constraint.source_path):
            if value not in known:
                reasons.append(
                    f"unresolved_reference:{constraint.source_path}->{constraint.target_path}:{value!r}"
                )
    return tuple(reasons)
