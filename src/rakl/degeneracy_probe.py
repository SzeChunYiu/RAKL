"""Generic probes for constructs that cannot return their negative outcome.

Six instances of one defect were found across five independent surfaces in this
repository in a single session, by three lanes working separately. That is a
systematic property of the measurement layer, not a run of coincidences, and
nothing was probing for it. This module is that probe.

The defect has two sub-types, and they fail in opposite directions.

**Type A — a control or checker that cannot return its negative outcome.**
Produces vacuous passes and uninformative nulls; makes the system look *worse*
than it is, because a null that could not have been anything else carries no
information. Observed as: a gate whose label is an exact boolean function of the
features it grades; a panel whose ``case_id`` restates its own answer; a
structural audit that substring-matches a name the integrator chose; a control
that passed while declaring none of the evidence it exists to require.

**Type B — a treatment input that encodes the graded answer.**
Produces false *positives*: a capable model copies the answer out of the prompt
and the treatment arm posts a large, entirely spurious win. This is the more
dangerous class. A false null can be re-run; a manufactured positive that
reaches publication has to be retracted.

Design commitments
------------------
*Correlation is not the defect.* A feature correlated with a label is what a
feature *is*. What invalidates a measurement is a field **authored from** the
label — an identifier, a marker, or a restatement written in the same act as the
answer it predicts. No amount of held-out data repairs that. Findings therefore
carry a :class:`CouplingKind` and only ``AUTHORED_FROM_LABEL`` is reported as a
validity defect; ``DETERMINISTIC`` is escalated for human adjudication.

*"Could not check" is not "checked and clean."* A surface whose labels or
features are not machine-extractable returns :data:`DegeneracyStatus.CANNOT_CHECK`
with its own exit code. Silently passing an unprobed surface would make this
module an instance of the defect it hunts.

*Candidates are derived, never supplied.* The Type B probe computes its marker
vocabulary from the treatment/control diff. Hard-coding the strings that caught
one instance would find that instance and nothing else.

This module grades nothing and mints no authority. It reports.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from enum import Enum
from itertools import combinations
from typing import Callable, Iterable, Mapping, Sequence

__all__ = [
    "ArmPair",
    "CouplingKind",
    "DegeneracyFinding",
    "DegeneracyStatus",
    "LabeledRecord",
    "ProbeReport",
    "EXIT_CODES",
    "probe_arm_answer_leak",
    "probe_blind_responder",
    "probe_boolean_combination",
    "probe_records",
    "probe_single_feature",
]


class DegeneracyStatus(str, Enum):
    """Outcome of a probe. ``CANNOT_CHECK`` is deliberately not a pass."""

    CLEAN = "CLEAN"
    SUSPECT = "SUSPECT"
    DEGENERATE = "DEGENERATE"
    CANNOT_CHECK = "CANNOT_CHECK"


#: Distinct process exit codes so a caller cannot conflate the four outcomes.
EXIT_CODES: Mapping[DegeneracyStatus, int] = {
    DegeneracyStatus.CLEAN: 0,
    DegeneracyStatus.DEGENERATE: 1,
    DegeneracyStatus.SUSPECT: 2,
    DegeneracyStatus.CANNOT_CHECK: 3,
}


class CouplingKind(str, Enum):
    """How a field relates to the label it predicts.

    The distinction is the whole point. ``CORRELATED`` is a measurement note.
    ``AUTHORED_FROM_LABEL`` is a validity defect: the field and the answer were
    written by the same hand in the same act, so the field cannot be evidence
    about the answer.
    """

    CORRELATED = "CORRELATED"
    DETERMINISTIC = "DETERMINISTIC"
    AUTHORED_FROM_LABEL = "AUTHORED_FROM_LABEL"


@dataclass(frozen=True)
class DegeneracyFinding:
    probe: str
    surface: str
    detail: str
    coupling: CouplingKind
    status: DegeneracyStatus
    #: Fraction of records the shortcut reproduces, where meaningful.
    coverage: float | None = None
    #: The chance/majority baseline the shortcut must beat to matter.
    baseline: float | None = None
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "probe": self.probe,
            "surface": self.surface,
            "detail": self.detail,
            "coupling": self.coupling.value,
            "status": self.status.value,
            "coverage": self.coverage,
            "baseline": self.baseline,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class ProbeReport:
    surface: str
    status: DegeneracyStatus
    findings: tuple[DegeneracyFinding, ...] = ()
    reasons: tuple[str, ...] = ()
    records_probed: int = 0

    @property
    def exit_code(self) -> int:
        return EXIT_CODES[self.status]

    def to_dict(self) -> dict[str, object]:
        return {
            "surface": self.surface,
            "status": self.status.value,
            "exit_code": self.exit_code,
            "records_probed": self.records_probed,
            "findings": [item.to_dict() for item in self.findings],
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class LabeledRecord:
    """One graded item, reduced to features plus the value being graded."""

    record_id: str
    features: Mapping[str, object] = field(default_factory=dict)
    label: object = None


def _hashable(value: object) -> object:
    if isinstance(value, (list, tuple)):
        return tuple(_hashable(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return tuple(sorted(str(item) for item in value))
    if isinstance(value, dict):
        return tuple(sorted((str(k), _hashable(v)) for k, v in value.items()))
    return value


_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")


def _label_tokens_in_value(value: str, label: object) -> bool:
    """True when the field's text carries the label's own vocabulary.

    Compares normalised word tokens, so ``ALR-01-prediction-not-mechanism``
    matches a ``PREDICTION_NOT_MECHANISM`` verdict while an opaque
    ``ALR-01-a3f9`` does not.
    """

    def parts(text: str) -> set[str]:
        # Split both sides identically, or PREDICTION_NOT_MECHANISM stays one
        # token while prediction-not-mechanism splits into three and never matches.
        out: set[str] = set()
        for token in _TOKEN.findall(text.replace("-", "_")):
            lowered = token.lower()
            out.add(lowered)
            out |= {piece for piece in lowered.split("_") if len(piece) > 2}
        return out

    label_parts = parts(str(label))
    if not label_parts:
        return False
    # Compare only the substantive pieces, so an opaque suffix does not count as
    # a match and a fully-spelled-out verdict does.
    label_words = {p for p in label_parts if "_" not in p}
    if not label_words:
        return False
    return label_words <= parts(value)


def _majority_baseline(labels: Sequence[object]) -> float:
    if not labels:
        return 0.0
    return Counter(labels).most_common(1)[0][1] / len(labels)


#: A field name matching this has no legitimate reason to carry the answer, so
#: label content inside it is authorship rather than signal.
_IDENTIFIER_NAME = re.compile(r"(^|_)(id|ids|name|key|slug|label|case|title)($|_)", re.I)


def _looks_like_identifier(name: str, values: Sequence[object]) -> bool:
    """Identifier-ness is about the *name* and string-ness, never uniqueness alone.

    An earlier revision also treated near-unique values as identifiers. That
    fired on ``score`` — a continuous measurement with one value per record —
    and would have flagged every real-valued feature in the repository. Caught
    by ``test_correlated_but_non_determining_features_do_not_alarm``.
    """

    if not all(isinstance(value, str) for value in values):
        return False
    return bool(_IDENTIFIER_NAME.search(name))


# --------------------------------------------------------------------------
# Type A: does any feature, or simple combination, reproduce the label?
# --------------------------------------------------------------------------


def probe_single_feature(
    records: Sequence[LabeledRecord], *, surface: str = "records"
) -> tuple[DegeneracyFinding, ...]:
    """Report features that determine the label by themselves.

    Determination means the feature's value partitions the records into groups
    that are pure in the label. Reported against the majority baseline, so a
    label that is 95% one class does not make every feature look predictive.
    """

    if not records:
        return ()
    labels = [_hashable(item.label) for item in records]
    baseline = _majority_baseline(labels)
    names = sorted({name for item in records for name in item.features})

    findings: list[DegeneracyFinding] = []
    for name in names:
        present = [item for item in records if name in item.features]
        if len(present) < len(records):
            continue  # partially-present feature: not a clean shortcut
        values = [_hashable(item.features[name]) for item in present]
        labels_here = [_hashable(item.label) for item in present]

        # High-cardinality features partition perfectly *by construction* — with
        # one distinct value per record every bucket is pure, which is an
        # artifact of cardinality, not evidence of a shortcut. Such fields are
        # examined by their content instead (see below), never by purity.
        cardinality = len(set(values))
        if cardinality <= len(present) / 2:
            buckets: dict[object, set[object]] = defaultdict(set)
            for value, label in zip(values, labels_here):
                buckets[value].add(label)
            pure = sum(1 for value in values if len(buckets[value]) == 1) / len(values)
            if pure >= 1.0 - 1e-9 and pure > baseline + 1e-9:
                findings.append(
                    DegeneracyFinding(
                        probe="single_feature_reproduction",
                        surface=surface,
                        detail=(
                            f"feature {name!r} determines the label on all "
                            f"{len(present)} records across {cardinality} distinct "
                            f"values (majority baseline {baseline:.3f}); needs "
                            "adjudication — a genuinely strong measurement looks "
                            "identical to a restatement of the answer"
                        ),
                        coupling=CouplingKind.DETERMINISTIC,
                        status=DegeneracyStatus.SUSPECT,
                        coverage=pure,
                        baseline=baseline,
                        evidence=tuple(
                            f"{item.record_id}: {name}={item.features[name]!r} "
                            f"-> {item.label!r}"
                            for item in present[:4]
                        ),
                    )
                )
            continue

        # Content check: does the field's own text carry the answer? This is what
        # makes an identifier a validity defect rather than a strong feature.
        if not _looks_like_identifier(name, [item.features[name] for item in present]):
            continue
        overlapping = [
            item
            for item, value, label in zip(present, values, labels_here)
            if _label_tokens_in_value(str(value), label)
        ]
        if len(overlapping) < len(present):
            continue
        findings.append(
            DegeneracyFinding(
                probe="identifier_restates_label",
                surface=surface,
                detail=(
                    f"identifier field {name!r} textually contains its own answer on "
                    f"all {len(present)} records; a responder reading nothing but "
                    "this field scores without reasoning, so the surface cannot "
                    "measure the competence it claims to"
                ),
                coupling=CouplingKind.AUTHORED_FROM_LABEL,
                status=DegeneracyStatus.DEGENERATE,
                coverage=1.0,
                baseline=baseline,
                evidence=tuple(
                    f"{item.record_id}: {name}={item.features[name]!r} -> {item.label!r}"
                    for item in overlapping[:4]
                ),
            )
        )
    return tuple(findings)


def probe_boolean_combination(
    records: Sequence[LabeledRecord], *, surface: str = "records", max_terms: int = 4
) -> tuple[DegeneracyFinding, ...]:
    """Report boolean labels that are an exact AND/OR of boolean features.

    This is the Paper 3 v1 gate defect in general form: the label was exactly
    ``AND(invariant, boundary, qoi, directional)`` on 44/44 cases, so an AUC of
    1.000 was arithmetic rather than evidence.
    """

    if not records:
        return ()
    labels = [item.label for item in records]
    if not all(isinstance(item, bool) for item in labels):
        return ()

    boolean_names = sorted(
        name
        for name in {n for item in records for n in item.features}
        if all(
            name in item.features and isinstance(item.features[name], bool)
            for item in records
        )
    )
    findings: list[DegeneracyFinding] = []
    for size in range(1, min(max_terms, len(boolean_names)) + 1):
        for combo in combinations(boolean_names, size):
            for op_name, op in (("AND", all), ("OR", any)):
                if size == 1 and op_name == "OR":
                    continue  # identical to AND for a single term
                if all(
                    op(bool(item.features[name]) for name in combo) == bool(item.label)
                    for item in records
                ):
                    findings.append(
                        DegeneracyFinding(
                            probe="boolean_combination_reproduction",
                            surface=surface,
                            detail=(
                                f"label == {op_name}({', '.join(combo)}) on "
                                f"{len(records)}/{len(records)} records; the label "
                                "is a deterministic function of the features that "
                                "are supposed to predict it"
                            ),
                            coupling=CouplingKind.AUTHORED_FROM_LABEL,
                            status=DegeneracyStatus.DEGENERATE,
                            coverage=1.0,
                            baseline=_majority_baseline([_hashable(x) for x in labels]),
                            evidence=tuple(
                                f"{item.record_id}: "
                                + ", ".join(f"{n}={item.features[n]}" for n in combo)
                                + f" -> {item.label}"
                                for item in records[:4]
                            ),
                        )
                    )
                    return tuple(findings)  # smallest combination is the finding
    return tuple(findings)


def probe_blind_responder(
    records: Sequence[LabeledRecord],
    responder: Callable[[LabeledRecord], object],
    *,
    responder_name: str,
    surface: str = "records",
    margin: float = 0.05,
) -> tuple[DegeneracyFinding, ...]:
    """Score a responder that sees only a restricted view of each record.

    If a responder reading nothing but metadata scores meaningfully above the
    majority baseline, the surface is not measuring the competence it claims to.
    This is the generic form of c154's ``case_id_exploit_responder``, which
    scored ALR 0.143 / recall 0.667 on the V1 panel while performing no
    scientific reasoning at all.
    """

    if not records:
        return ()
    labels = [_hashable(item.label) for item in records]
    baseline = _majority_baseline(labels)
    correct = sum(
        1 for item in records if _hashable(responder(item)) == _hashable(item.label)
    )
    accuracy = correct / len(records)
    if accuracy <= baseline + margin:
        return ()
    return (
        DegeneracyFinding(
            probe="blind_responder_ceiling",
            surface=surface,
            detail=(
                f"blind responder {responder_name!r} scores {accuracy:.3f} against a "
                f"majority baseline of {baseline:.3f} while reading no substantive "
                "content; the panel rewards a shortcut, not reasoning"
            ),
            coupling=CouplingKind.AUTHORED_FROM_LABEL,
            status=DegeneracyStatus.DEGENERATE,
            coverage=accuracy,
            baseline=baseline,
        ),
    )


def probe_records(
    records: Sequence[LabeledRecord],
    *,
    surface: str,
    blind_responders: Mapping[str, Callable[[LabeledRecord], object]] | None = None,
) -> ProbeReport:
    """Run every Type A probe over a labelled record set."""

    if not records:
        return ProbeReport(
            surface,
            DegeneracyStatus.CANNOT_CHECK,
            reasons=("no records supplied; nothing was probed",),
        )
    if all(item.label is None for item in records):
        return ProbeReport(
            surface,
            DegeneracyStatus.CANNOT_CHECK,
            reasons=("no machine-extractable label; the surface was not probed",),
            records_probed=len(records),
        )
    if len({_hashable(item.label) for item in records}) < 2:
        return ProbeReport(
            surface,
            DegeneracyStatus.CANNOT_CHECK,
            reasons=(
                "every record carries the same label, so no shortcut is "
                "distinguishable from a constant; the surface cannot discriminate",
            ),
            records_probed=len(records),
        )

    findings = (
        probe_single_feature(records, surface=surface)
        + probe_boolean_combination(records, surface=surface)
    )
    for name, responder in (blind_responders or {}).items():
        findings += probe_blind_responder(
            records, responder, responder_name=name, surface=surface
        )
    return ProbeReport(surface, _worst(findings), findings, (), len(records))


def _worst(findings: Sequence[DegeneracyFinding]) -> DegeneracyStatus:
    if any(f.status is DegeneracyStatus.DEGENERATE for f in findings):
        return DegeneracyStatus.DEGENERATE
    if any(f.status is DegeneracyStatus.SUSPECT for f in findings):
        return DegeneracyStatus.SUSPECT
    return DegeneracyStatus.CLEAN


# --------------------------------------------------------------------------
# Type B: does the treatment input carry the graded answer?
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ArmPair:
    """A treatment/control arm pair plus the gold values being graded.

    ``gold`` maps each graded output field to the set of entity ids that is the
    correct answer. ``entity_pattern`` recovers the id universe from the prompts
    so the probe never needs to be told what the entities are.
    """

    surface: str
    treatment_text: str
    control_text: str
    gold: Mapping[str, frozenset[str]]
    entity_pattern: str = r"\bS\d+\b"


def _segments(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.strip()]


def probe_arm_answer_leak(pair: ArmPair) -> ProbeReport:
    """Detect a graded answer encoded in the treatment arm but not the control.

    Mechanically: take the tokens present in the treatment arm and absent from
    the control arm — the *differential vocabulary* — and, for each one, compute
    the set of entity ids it co-occurs with. If that set is exactly a gold answer
    set, the marker is an answer key: a model that copies it scores perfectly
    while reasoning about nothing, and the treatment arm posts a spurious win.

    The differential vocabulary is derived from the diff, never supplied. Most of
    it is legitimate framing that happens to be unique to the treatment arm; the
    probe must stay silent on all of it and fire only on markers whose
    co-occurrence set reproduces a gold answer.
    """

    if not pair.gold:
        return ProbeReport(
            pair.surface,
            DegeneracyStatus.CANNOT_CHECK,
            reasons=("no gold answer supplied; leakage cannot be assessed",),
        )
    entity_re = re.compile(pair.entity_pattern)
    universe = set(entity_re.findall(pair.treatment_text)) | set(
        entity_re.findall(pair.control_text)
    )
    if len(universe) < 2:
        return ProbeReport(
            pair.surface,
            DegeneracyStatus.CANNOT_CHECK,
            reasons=(
                f"entity pattern {pair.entity_pattern!r} matched {len(universe)} "
                "ids; nothing to partition",
            ),
        )

    treatment_tokens = set(_TOKEN.findall(pair.treatment_text))
    control_tokens = set(_TOKEN.findall(pair.control_text))
    differential = sorted(treatment_tokens - control_tokens)
    segments = _segments(pair.treatment_text)
    #: Token sets per segment. Matching on tokens rather than substrings keeps
    #: 'CONTEXT' from matching inside 'CONTEXT_MISALIGNED_FOR_...' — verified
    #: against the real v1 arm pair, where substring matching inflated the hit
    #: count with a marker whose own occurrences carry no entity id.
    segment_tokens = [frozenset(_TOKEN.findall(segment)) for segment in segments]

    #: Group by (graded field, the exact set of segments implicated). Several
    #: markers on one line are one leak site, not several leaks: on the real v1
    #: pair six markers resolved to two leaking lines, and reporting six would
    #: have overstated the finding sixfold.
    sites: dict[tuple[str, tuple[int, ...]], list[str]] = defaultdict(list)
    for marker in differential:
        if entity_re.fullmatch(marker):
            continue  # an entity id is not a marker for itself
        hit_indices = tuple(
            index for index, tokens in enumerate(segment_tokens) if marker in tokens
        )
        co_occurring: set[str] = set()
        for index in hit_indices:
            co_occurring |= set(entity_re.findall(segments[index]))
        if not co_occurring or co_occurring == universe:
            continue  # matches nothing, or everything: carries no answer
        for field_name, gold in pair.gold.items():
            if co_occurring == set(gold):
                sites[(field_name, hit_indices)].append(marker)

    findings: list[DegeneracyFinding] = []
    for (field_name, hit_indices), markers in sorted(sites.items()):
        answer = sorted(set(pair.gold[field_name]))
        findings.append(
            DegeneracyFinding(
                probe="arm_answer_key_leak",
                surface=pair.surface,
                detail=(
                    f"{len(markers)} marker(s) unique to the treatment arm "
                    f"({', '.join(repr(m) for m in sorted(markers))}) occur on "
                    f"{len(hit_indices)} line(s) that mention exactly {answer}, the "
                    f"gold value of graded field {field_name!r}; a model that copies "
                    "them scores perfectly without reasoning, so any treatment-arm "
                    "advantage on this field is spurious"
                ),
                coupling=CouplingKind.AUTHORED_FROM_LABEL,
                status=DegeneracyStatus.DEGENERATE,
                coverage=1.0,
                evidence=tuple(segments[i].strip()[:200] for i in hit_indices[:3]),
            )
        )
    return ProbeReport(
        pair.surface,
        _worst(findings),
        tuple(findings),
        (
            f"{len(differential)} tokens are unique to the treatment arm; "
            f"they resolve to {len(findings)} distinct leak site(s)",
        ),
        len(universe),
    )


def probe_arm_pairs(pairs: Iterable[ArmPair]) -> tuple[ProbeReport, ...]:
    return tuple(probe_arm_answer_leak(pair) for pair in pairs)
