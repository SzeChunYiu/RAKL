from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping, Tuple

from .objective_transfer_benchmark import Task


@dataclass(frozen=True)
class ControlledExtraction:
    task: Task | None
    reasons: Tuple[str, ...]
    source_span_sha256: Tuple[Tuple[str, str], ...]

    @property
    def complete(self) -> bool:
        return self.task is not None and not self.reasons

    @property
    def grants_scientific_authority(self) -> bool:
        return False


_LABELS = {
    0: {
        "family": "Transfer family",
        "item_id": "Opaque case id",
        "source_text": "Source surface",
        "target_text": "Target surface",
        "source": "Source structural record",
        "target": "Target structural record",
        "mapping": "Directional mapping record",
        "candidate_actions": "Candidate action sequence",
    },
    1: {
        "family": "Registered structural family",
        "item_id": "Case identity",
        "source_text": "Source-domain description",
        "target_text": "Target-domain description",
        "source": "Facts licensed at the source",
        "target": "Facts declared at the target",
        "mapping": "Source-to-target correspondence",
        "candidate_actions": "Proposed ordered actions",
    },
}


def _line(label: str, value: Any) -> str:
    return f"{label} :: {json.dumps(value, sort_keys=True, separators=(',', ':'))}"


def render_controlled_task(task: Task, *, variant: int = 0) -> str:
    """Render a candidate-visible controlled scientific-text interface.

    This is deliberately *not* arbitrary natural language. The surface is a
    bounded prose/record bridge whose role labels are explicit while values are
    carried as JSON literals. Its purpose is to make the text-to-typed-state
    boundary executable before attempting open-ended paper-text extraction.
    """
    labels = _LABELS[variant]
    public = task.public
    lines = [
        _line(labels["item_id"], task.item_id),
        _line(labels["family"], task.family),
        _line(labels["source_text"], task.source_text),
        _line(labels["target_text"], task.target_text),
        _line(labels["source"], public.get("source", {})),
        _line(labels["target"], public.get("target", {})),
    ]
    if "mapping" in public:
        lines.append(_line(labels["mapping"], public["mapping"]))
    if "candidate_actions" in public:
        lines.append(_line(labels["candidate_actions"], public["candidate_actions"]))
    return "\n".join(lines) + "\n"


def _known_labels() -> Mapping[str, str]:
    out: dict[str, str] = {}
    for labels in _LABELS.values():
        for canonical, surface in labels.items():
            out[surface] = canonical
    return out


def controlled_span_manifest(text: str) -> Tuple[Tuple[str, str], ...]:
    """Return exact per-field text bindings for a frozen controlled packet."""
    surfaces = _known_labels()
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for raw in text.splitlines():
        if not raw.strip() or " :: " not in raw:
            continue
        label, _ = raw.split(" :: ", 1)
        canonical = surfaces.get(label)
        if canonical is None or canonical in seen:
            continue
        seen.add(canonical)
        out.append((canonical, sha256(raw.encode("utf-8")).hexdigest()))
    return tuple(sorted(out))


def extract_controlled_task(
    text: str,
    *,
    expected_span_sha256: Mapping[str, str] | None = None,
) -> ControlledExtraction:
    """Parse the bounded textual bridge, failing closed on omission/ambiguity.

    When ``expected_span_sha256`` is supplied, every extracted semantic field is
    content-bound to the exact frozen source line. A changed value, label or
    source record therefore cannot be silently accepted under a stale packet
    manifest. The parser does not infer unknown values, repair mappings, or use
    hidden item-type / perturbation metadata.
    """
    surfaces = _known_labels()
    parsed: dict[str, Any] = {}
    spans: list[tuple[str, str]] = []
    reasons: list[str] = []
    for line_no, raw in enumerate(text.splitlines(), start=1):
        if not raw.strip():
            continue
        if " :: " not in raw:
            reasons.append(f"unparseable_line:{line_no}")
            continue
        label, payload = raw.split(" :: ", 1)
        canonical = surfaces.get(label)
        if canonical is None:
            reasons.append(f"unknown_label:{label}")
            continue
        if canonical in parsed:
            reasons.append(f"duplicate_field:{canonical}")
            continue
        digest = sha256(raw.encode("utf-8")).hexdigest()
        if expected_span_sha256 is not None:
            expected = expected_span_sha256.get(canonical)
            if expected is None:
                reasons.append(f"unbound_source_span:{canonical}")
            elif expected != digest:
                reasons.append(f"source_span_hash_mismatch:{canonical}")
        try:
            value = json.loads(payload)
        except json.JSONDecodeError:
            reasons.append(f"invalid_json:{canonical}")
            continue
        parsed[canonical] = value
        spans.append((canonical, digest))

    mandatory = ("item_id", "family", "source_text", "target_text", "source", "target")
    for field in mandatory:
        if field not in parsed:
            reasons.append(f"missing_field:{field}")
    if expected_span_sha256 is not None:
        for field in expected_span_sha256:
            if field not in parsed:
                reasons.append(f"bound_source_span_missing:{field}")

    if reasons:
        return ControlledExtraction(None, tuple(sorted(set(reasons))), tuple(sorted(spans)))

    public: dict[str, Any] = {"source": parsed["source"], "target": parsed["target"]}
    if "mapping" in parsed:
        public["mapping"] = parsed["mapping"]
    if "candidate_actions" in parsed:
        public["candidate_actions"] = parsed["candidate_actions"]

    family = str(parsed["family"])
    if family in {"flow", "logic", "state", "sched", "stat"} and "mapping" not in public:
        reasons.append("missing_field:mapping")
    if family == "state" and "candidate_actions" not in public:
        reasons.append("missing_field:candidate_actions")
    if reasons:
        return ControlledExtraction(None, tuple(sorted(set(reasons))), tuple(sorted(spans)))

    task = Task(
        item_id=str(parsed["item_id"]),
        family=family,
        item_type="CONTROLLED_TEXT_EXTRACTED",
        source_text=str(parsed["source_text"]),
        target_text=str(parsed["target_text"]),
        public=public,
        perturbation="not_exposed_by_controlled_extractor",
    )
    return ControlledExtraction(task, (), tuple(sorted(spans)))


def drop_semantic_field(text: str, field: str) -> str:
    """Registered mutation helper used only by adversarial tests/experiments."""
    labels = {
        surface
        for labels in _LABELS.values()
        for key, surface in labels.items()
        if key == field
    }
    return "\n".join(
        line
        for line in text.splitlines()
        if not any(line.startswith(label + " :: ") for label in labels)
    ) + "\n"
