"""Degeneracy audit for scientific-transition authority panels (issue #154).

A benchmark that cannot return a negative result is worthless. This module is
the executable guard against the two ways an authority-leakage panel becomes
unable to do so:

1. **Label restatement.** A visible field names the answer, so a responder can
   score well by string matching instead of scientific reasoning.
2. **Bias-aligned class imbalance.** The panel's majority answer coincides with
   the inductive bias of the system under test. RAKL is conservative by design,
   so a panel whose answer is "raise nothing" in most cases reports RAKL as
   excellent *by construction* and has no power to detect over-conservatism —
   which is precisely RAKL's characteristic failure mode.

Both are the same defect wearing different clothes: the measured score is
arithmetic recovered from the panel's own construction, not evidence about the
responder.

Thresholds in this module are frozen **before** any panel is audited (see
:data:`AUDIT_THRESHOLDS_FROZEN_AT`). Per repository rule, a panel that trips a
threshold is redesigned; the threshold is not moved.

The audit grants no scientific authority and scores no responder's competence.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Mapping, MutableMapping, Sequence, Tuple

from .authority_ledger import AuthorityAxis
from .authority_leakage_benchmark import (
    ScientificTransitionCase,
    StateEdit,
    TransitionDecision,
    TransitionResponse,
    VisibleCaseContext,
    score_panel,
)

__all__ = [
    "AUDIT_THRESHOLDS_FROZEN_AT",
    "AuditStatus",
    "CheckResult",
    "PanelAuditReport",
    "DISPOSITION_LEXICON",
    "audit_panel",
    "check_case_id_opacity",
    "check_visible_disposition_leak",
    "check_single_feature_separation",
    "check_positional_shortcut",
    "check_label_pattern_diversity",
    "check_label_blind_ceiling",
    "label_blind_responders",
    "majority_status_responder",
    "last_candidate_responder",
    "keyword_refusal_responder",
    "case_id_exploit_responder",
]


#: Date the thresholds below were frozen. Changing a threshold after auditing a
#: panel requires a new audit version and an explicit written justification.
AUDIT_THRESHOLDS_FROZEN_AT = "2026-08-11"

#: A panel must offer a real opportunity to *grant* authority, not only to
#: withhold it, or it cannot detect over-conservatism.
MIN_NONEMPTY_ALLOWED_FRACTION = 0.35

#: Total allowed axes across the panel, relative to case count. Sets the
#: resolution of ``valid_upgrade_recall``; below this the metric is too
#: coarsely quantized to distinguish responders.
MIN_ALLOWED_AXES_PER_CASE = 0.5

#: Distinct ``(allowed, disallowed, status, edits)`` tuples, relative to case
#: count. A panel of 44 cases with 3 distinct label patterns is a lookup table.
MIN_DISTINCT_LABEL_PATTERN_FRACTION = 0.5

#: A single low-cardinality visible feature may not determine the whole label.
MAX_SINGLE_FEATURE_PURITY = 0.75

#: A single feature *value* may not perfectly predict any label component.
#: Overall purity is too weak a statistic on a panel whose label signatures are
#: all distinct: Paper 3's fatal shortcut was one flag value separating 22/44,
#: which is 50% coverage at 100% precision. This gate is on precision, with a
#: coverage floor so single-case groups cannot trip it.
MAX_SHORTCUT_VALUE_PRECISION = 1.0
MIN_SHORTCUT_GROUP_COVERAGE = 0.25

#: A pure group is only evidence of a shortcut if purity is *surprising*.
#: When a label facet is True in 75% of the panel, a 4-case group being all-True
#: happens by chance about a third of the time; reporting that as a finding is
#: noise, and a checker that cries wolf on its first real run gets switched off.
#: A group of size k, pure on a facet value with panel base rate p, is flagged
#: only when p**k falls below this.
SHORTCUT_CHANCE_ALPHA = 0.05

#: No fixed candidate position may be correct more often than this.
MAX_POSITIONAL_SHORTCUT = 0.75

#: A label-blind responder may not beat the trivial constant baseline by more
#: than this on terminal status. Absolute accuracy is not gated: with five
#: statuses the majority class is a property of the panel, so the meaningful
#: question is whether a *surface heuristic* beats guessing the majority.
MAX_STATUS_GAIN_OVER_MAJORITY = 0.05

#: Joint "looks competent" condition. A label-blind responder that clears both
#: of these would be indistinguishable from a disciplined reasoner.
CEILING_ALR = 0.25
CEILING_VALID_UPGRADE_RECALL = 0.50


class AuditStatus(str, Enum):
    """Distinct from one another on purpose.

    ``CANNOT_CHECK`` is never merged into ``CLEAN``: "we could not look" and
    "we looked and it is fine" are different findings.
    """

    CLEAN = "CLEAN"
    DEGENERATE = "DEGENERATE"
    CANNOT_CHECK = "CANNOT_CHECK"


_SEVERITY = {AuditStatus.CLEAN: 0, AuditStatus.CANNOT_CHECK: 1, AuditStatus.DEGENERATE: 2}


#: Words that name a disposition (an authority axis, a terminal status, or a
#: leakage channel). These have no legitimate place in an identifier.
DISPOSITION_LEXICON: Tuple[str, ...] = (
    "prediction",
    "predictive",
    "representation",
    "mechanism",
    "identification",
    "identified",
    "grounding",
    "provenance",
    "independence",
    "independent",
    "decision",
    "authority",
    "experience",
    "evidence",
    "impossibility",
    "refutation",
    "refuted",
    "supported",
    "blocked",
    "cannot",
    "legitimate",
    "upgrade",
    "escalation",
    "leak",
    "leakage",
    "trap",
    "restriction",
    "supersession",
    "routing",
)

#: Terminal statuses rendered as free text, e.g. "cannot check", "partially
#: identified". Their appearance in narrative visible text hands over the label.
_STATUS_PHRASES: Mapping[TransitionDecision, Tuple[str, ...]] = {
    TransitionDecision.SUPPORTED: ("is supported", "transition is supported"),
    TransitionDecision.REFUTED: ("is refuted", "record a refutation"),
    TransitionDecision.PARTIALLY_IDENTIFIED: ("partially identified", "partial identification"),
    TransitionDecision.BLOCKED: ("is blocked", "must block"),
    TransitionDecision.CANNOT_CHECK: ("cannot be checked", "cannot check"),
}

#: Axis synonyms used to detect a negated disposition ("X is not mechanism").
_AXIS_SYNONYMS: Mapping[AuthorityAxis, Tuple[str, ...]] = {
    AuthorityAxis.GROUNDING: ("grounding", "provenance"),
    AuthorityAxis.REPRESENTATION: ("representation", "prediction", "predictive"),
    AuthorityAxis.MECHANISM: ("mechanism",),
    AuthorityAxis.IDENTIFICATION: ("identification", "identified"),
    AuthorityAxis.DECISION: ("decision",),
}

#: Word-bounded. Without ``\b`` this matches inside ordinary words —
#: "nonetheless" contains "no" — which produced false positives on first run.
_NEGATION = r"\b(?:not|never|no|cannot|isn't|doesn't|≠|!=)\b"

#: The words that turn an axis mention into a statement about *licensing*.
#: This is the line between evidence and answer: "no mechanism **witness** was
#: measured" reports what the experiment did and is legitimate case content;
#: "no mechanism **authority** is licensed" states the label. Only the latter
#: is a leak, so an axis synonym counts only when followed by one of these.
_AUTHORITY_NOUNS = r"(?:authority|support|licen[cs]e[ds]?|upgrade|escalation|update|entitle\w*)"

_TOKEN = re.compile(r"[a-z']+")


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    status: AuditStatus
    message: str
    detail: Mapping[str, object]

    def to_dict(self) -> MutableMapping[str, object]:
        return {
            "check_id": self.check_id,
            "status": self.status.value,
            "message": self.message,
            "detail": dict(self.detail),
        }


@dataclass(frozen=True)
class PanelAuditReport:
    panel_id: str
    n_cases: int
    checks: Tuple[CheckResult, ...]

    @property
    def status(self) -> AuditStatus:
        """Worst status across checks. DEGENERATE dominates CANNOT_CHECK."""

        if not self.checks:
            return AuditStatus.CANNOT_CHECK
        return max((check.status for check in self.checks), key=lambda s: _SEVERITY[s])

    @property
    def grants_authority(self) -> bool:
        return False

    def degenerate_checks(self) -> Tuple[str, ...]:
        return tuple(c.check_id for c in self.checks if c.status is AuditStatus.DEGENERATE)

    def to_dict(self) -> MutableMapping[str, object]:
        return {
            "schema_version": "authority-leakage-panel-audit-v1",
            "panel_id": self.panel_id,
            "n_cases": self.n_cases,
            "thresholds_frozen_at": AUDIT_THRESHOLDS_FROZEN_AT,
            "thresholds": {
                "min_nonempty_allowed_fraction": MIN_NONEMPTY_ALLOWED_FRACTION,
                "min_allowed_axes_per_case": MIN_ALLOWED_AXES_PER_CASE,
                "min_distinct_label_pattern_fraction": MIN_DISTINCT_LABEL_PATTERN_FRACTION,
                "max_single_feature_purity": MAX_SINGLE_FEATURE_PURITY,
                "max_positional_shortcut": MAX_POSITIONAL_SHORTCUT,
                "max_status_gain_over_majority": MAX_STATUS_GAIN_OVER_MAJORITY,
                "ceiling_alr": CEILING_ALR,
                "ceiling_valid_upgrade_recall": CEILING_VALID_UPGRADE_RECALL,
            },
            "status": self.status.value,
            "degenerate_checks": list(self.degenerate_checks()),
            "grants_scientific_authority": False,
            "checks": [check.to_dict() for check in self.checks],
        }

    def artifact_hash(self) -> str:
        blob = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(blob).hexdigest()


# --------------------------------------------------------------------------
# check 1: identifiers must be opaque
# --------------------------------------------------------------------------


def _tokens(text: str) -> frozenset[str]:
    return frozenset(_TOKEN.findall(text.lower()))


def check_case_id_opacity(cases: Sequence[ScientificTransitionCase]) -> CheckResult:
    """A ``case_id`` reaches the proposer. It must not name the answer.

    ``ALR-07-legitimate-mechanism-upgrade`` tells a responder to raise
    MECHANISM without reading the observation at all.
    """

    offenders: dict[str, list[str]] = {}
    for case in cases:
        hits = sorted(_tokens(case.case_id) & set(DISPOSITION_LEXICON))
        if hits:
            offenders[case.case_id] = hits

    if offenders:
        return CheckResult(
            check_id="case_id_opacity",
            status=AuditStatus.DEGENERATE,
            message=(
                f"{len(offenders)}/{len(cases)} case ids contain disposition vocabulary; "
                "the identifier restates the label"
            ),
            detail={"offending_case_ids": offenders},
        )
    return CheckResult(
        check_id="case_id_opacity",
        status=AuditStatus.CLEAN,
        message=f"all {len(cases)} case ids are opaque",
        detail={"offending_case_ids": {}},
    )


# --------------------------------------------------------------------------
# check 2: narrative visible text must not assert the disposition
# --------------------------------------------------------------------------


def _narrative_fields(visible: VisibleCaseContext) -> Mapping[str, str]:
    """Visible text a proposer reads as *setup*.

    ``candidate_interpretations`` is deliberately excluded: the candidates are
    the thing under evaluation, and one of them stating the correct disposition
    is the point of the task, not a leak.
    """

    return {
        "pre_state": visible.pre_state,
        "new_observation": visible.new_observation,
        "context_regime": visible.context_regime,
        "claim_types": " ".join(visible.claim_types),
    }


def check_visible_disposition_leak(cases: Sequence[ScientificTransitionCase]) -> CheckResult:
    """Setup text must not state the licensing verdict or name the status.

    Deliberately narrow. Setup text is *supposed* to say which measurements
    exist and which do not — that is the evidence the responder reasons over.
    The leak is an assertion about **authority**, so an axis mention only
    counts when a negation binds it to an authority noun
    (:data:`_AUTHORITY_NOUNS`) within a short window.
    """

    offenders: dict[str, list[str]] = {}
    for case in cases:
        found: list[str] = []
        for field_name, text in _narrative_fields(case.visible).items():
            lowered = text.lower()
            for axis in case.labels.disallowed_authority_effects:
                for synonym in _AXIS_SYNONYMS[axis]:
                    forward = rf"{_NEGATION}[\w\s,'-]{{0,40}}?\b{synonym}\b\s+{_AUTHORITY_NOUNS}"
                    backward = rf"\b{synonym}\b\s+{_AUTHORITY_NOUNS}[\w\s,'-]{{0,40}}?{_NEGATION}"
                    if re.search(forward, lowered) or re.search(backward, lowered):
                        found.append(
                            f"{field_name}: negated '{synonym} <authority>' "
                            f"(disallowed {axis.name})"
                        )
            for phrase in _STATUS_PHRASES[case.labels.required_terminal_status]:
                if phrase in lowered:
                    found.append(f"{field_name}: states terminal status '{phrase}'")
        if found:
            offenders[case.case_id] = sorted(set(found))

    if offenders:
        return CheckResult(
            check_id="visible_disposition_leak",
            status=AuditStatus.DEGENERATE,
            message=f"{len(offenders)}/{len(cases)} cases assert their own disposition in setup text",
            detail={"offending_cases": offenders},
        )
    return CheckResult(
        check_id="visible_disposition_leak",
        status=AuditStatus.CLEAN,
        message=f"no disposition asserted in setup text across {len(cases)} cases",
        detail={"offending_cases": {}},
    )


# --------------------------------------------------------------------------
# check 3: no single low-cardinality feature may determine the label
# --------------------------------------------------------------------------


def _label_signature(case: ScientificTransitionCase) -> str:
    labels = case.labels
    return json.dumps(
        {
            "allowed": sorted(a.value for a in labels.allowed_authority_effects),
            "disallowed": {
                a.value: s.value
                for a, s in sorted(
                    labels.disallowed_authority_effects.items(), key=lambda kv: kv[0].value
                )
            },
            "status": labels.required_terminal_status.value,
            "edits": sorted(e.value for e in labels.required_state_edits),
        },
        sort_keys=True,
    )


def _low_cardinality_features(case: ScientificTransitionCase) -> Mapping[str, object]:
    """Proposer-visible features only.

    ``stratum`` is deliberately absent: it lives on the case, not on
    :class:`VisibleCaseContext`, so a responder cannot condition on it and it
    cannot be a leakage channel.
    """

    v = case.visible
    return {
        "claim_types": "|".join(v.claim_types),
        "context_regime": v.context_regime,
        "n_registered_claims": len(v.registered_claims),
        "n_evidence_roots": len(v.existing_evidence_roots),
        "n_candidate_interpretations": len(v.candidate_interpretations),
        "has_evidence_lineage": bool(v.evidence_lineage),
    }


def _label_components(case: ScientificTransitionCase) -> Mapping[str, object]:
    """Label facets a shortcut could target individually.

    Testing only the full signature is too weak: when every case has a distinct
    signature, no group is ever pure and the check cannot fire. Real shortcuts
    predict a *facet* — "two evidence roots means an upgrade is licensed".
    """

    labels = case.labels
    return {
        "full_signature": _label_signature(case),
        "terminal_status": labels.required_terminal_status.value,
        "licenses_an_upgrade": bool(labels.allowed_authority_effects),
        "allowed_axes": "|".join(sorted(a.value for a in labels.allowed_authority_effects)),
        "disallowed_axes": "|".join(
            sorted(a.value for a in labels.disallowed_authority_effects)
        ),
        "offers_leak_opportunity": bool(labels.disallowed_authority_effects),
    }


def check_single_feature_separation(cases: Sequence[ScientificTransitionCase]) -> CheckResult:
    """Paper-3 failure mode: one flag value separated the classes 22/22.

    Two statistics, both reported:

    * **overall purity** — fraction of cases sitting in a label-pure group of a
      single feature, gated by :data:`MAX_SINGLE_FEATURE_PURITY`;
    * **value precision** — a single feature *value*, covering at least
      :data:`MIN_SHORTCUT_GROUP_COVERAGE` of the panel, that perfectly predicts
      any label facet. This is the statistic with teeth.

    Features with a unique value per case are skipped: they separate trivially
    and carry no usable signal unless also semantic, which
    :func:`check_case_id_opacity` covers.
    """

    n = len(cases)
    if n < 2:
        return CheckResult(
            check_id="single_feature_separation",
            status=AuditStatus.CANNOT_CHECK,
            message="fewer than 2 cases; separation is undefined",
            detail={},
        )

    features = {name: [_low_cardinality_features(c)[name] for c in cases] for name in _low_cardinality_features(cases[0])}
    components = {name: [_label_components(c)[name] for c in cases] for name in _label_components(cases[0])}

    purity: dict[str, float] = {}
    shortcuts: list[Mapping[str, object]] = []

    for feature, values in features.items():
        distinct = set(values)
        if len(distinct) < 2 or len(distinct) == n:
            continue  # constant (no information) or unique-per-case (trivial)

        pure_cases = 0
        for value in distinct:
            members = [i for i, v in enumerate(values) if v == value]
            if len({components["full_signature"][i] for i in members}) == 1:
                pure_cases += len(members)
            coverage = len(members) / n
            if coverage < MIN_SHORTCUT_GROUP_COVERAGE:
                continue
            for component, labels in components.items():
                observed = {labels[i] for i in members}
                if len(observed) != 1 or len(set(labels)) < 2:
                    continue
                constant = next(iter(observed))
                base_rate = sum(1 for v in labels if v == constant) / n
                chance = base_rate ** len(members)
                if chance >= SHORTCUT_CHANCE_ALPHA:
                    continue  # purity is unsurprising given the panel base rate
                shortcuts.append(
                    {
                        "feature": feature,
                        "value": value,
                        "predicts": component,
                        "constant_value": constant,
                        "n_cases": len(members),
                        "coverage": coverage,
                        "facet_base_rate": base_rate,
                        "purity_by_chance": chance,
                    }
                )
        purity[feature] = pure_cases / n

    if not purity:
        return CheckResult(
            check_id="single_feature_separation",
            status=AuditStatus.CANNOT_CHECK,
            message="no low-cardinality feature was testable on this panel",
            detail={"feature_purity": {}, "value_shortcuts": []},
        )

    worst = max(purity, key=lambda k: purity[k])
    detail = {
        "feature_purity": purity,
        "worst_feature": worst,
        "value_shortcuts": shortcuts,
        "min_shortcut_group_coverage": MIN_SHORTCUT_GROUP_COVERAGE,
    }

    failures: list[str] = []
    if purity[worst] > MAX_SINGLE_FEATURE_PURITY:
        failures.append(
            f"feature '{worst}' alone determines the full label for {purity[worst]:.0%} of "
            f"cases (max {MAX_SINGLE_FEATURE_PURITY:.0%})"
        )
    for shortcut in shortcuts:
        failures.append(
            f"'{shortcut['feature']}={shortcut['value']}' predicts "
            f"{shortcut['predicts']}={shortcut['constant_value']} in "
            f"{shortcut['n_cases']}/{n} cases with no exception"
        )

    if failures:
        return CheckResult(
            check_id="single_feature_separation",
            status=AuditStatus.DEGENERATE,
            message="; ".join(failures),
            detail=detail,
        )
    return CheckResult(
        check_id="single_feature_separation",
        status=AuditStatus.CLEAN,
        message=(
            f"no single feature exceeds {MAX_SINGLE_FEATURE_PURITY:.0%} purity "
            f"(worst: {worst} at {purity[worst]:.0%}) and no feature value perfectly "
            "predicts a label facet"
        ),
        detail=detail,
    )


# --------------------------------------------------------------------------
# check 4: candidate ordering must not be a shortcut
# --------------------------------------------------------------------------


def check_positional_shortcut(cases: Sequence[ScientificTransitionCase]) -> CheckResult:
    """"Always pick the last candidate" must not solve the panel.

    Requires ``correct_interpretation_index`` on every case. When it is absent
    the check reports CANNOT_CHECK — it does not report CLEAN.
    """

    indices = [getattr(case.labels, "correct_interpretation_index", None) for case in cases]
    if any(index is None for index in indices):
        missing = [
            case.case_id
            for case, index in zip(cases, indices)
            if index is None
        ]
        return CheckResult(
            check_id="positional_shortcut",
            status=AuditStatus.CANNOT_CHECK,
            message=(
                f"{len(missing)}/{len(cases)} cases do not label which candidate is "
                "correct; positional shortcut is unmeasurable"
            ),
            detail={"cases_missing_correct_interpretation_index": missing},
        )

    counts: dict[int, int] = {}
    for case, index in zip(cases, indices):
        n = len(case.visible.candidate_interpretations)
        assert index is not None
        for position in (index, index - n):  # count from front and from back
            counts[position] = counts.get(position, 0) + 1

    fractions = {position: count / len(cases) for position, count in counts.items()}
    worst_pos = max(fractions, key=lambda k: fractions[k])
    if fractions[worst_pos] > MAX_POSITIONAL_SHORTCUT:
        return CheckResult(
            check_id="positional_shortcut",
            status=AuditStatus.DEGENERATE,
            message=(
                f"candidate position {worst_pos} is correct in {fractions[worst_pos]:.0%} of "
                f"cases (max {MAX_POSITIONAL_SHORTCUT:.0%})"
            ),
            detail={"position_correct_fraction": fractions, "worst_position": worst_pos},
        )
    return CheckResult(
        check_id="positional_shortcut",
        status=AuditStatus.CLEAN,
        message=f"no candidate position exceeds {MAX_POSITIONAL_SHORTCUT:.0%} (worst {worst_pos} at {fractions[worst_pos]:.0%})",
        detail={"position_correct_fraction": fractions, "worst_position": worst_pos},
    )


# --------------------------------------------------------------------------
# check 5: label balance and pattern diversity
# --------------------------------------------------------------------------


def check_label_pattern_diversity(cases: Sequence[ScientificTransitionCase]) -> CheckResult:
    """The panel must be able to report a *negative* result for a conservative system.

    Three sub-conditions, all reported whatever the verdict:

    * enough cases where an upgrade is genuinely licensed;
    * enough allowed axes to give ``valid_upgrade_recall`` usable resolution;
    * enough distinct label patterns that the panel is not a lookup table.
    """

    n = len(cases)
    if n == 0:
        return CheckResult(
            check_id="label_pattern_diversity",
            status=AuditStatus.CANNOT_CHECK,
            message="empty panel",
            detail={},
        )

    nonempty_allowed = sum(1 for c in cases if c.labels.allowed_authority_effects)
    total_allowed_axes = sum(len(c.labels.allowed_authority_effects) for c in cases)
    distinct_patterns = len({_label_signature(c) for c in cases})

    nonempty_fraction = nonempty_allowed / n
    axes_per_case = total_allowed_axes / n
    pattern_fraction = distinct_patterns / n

    failures = []
    if nonempty_fraction < MIN_NONEMPTY_ALLOWED_FRACTION:
        failures.append(
            f"only {nonempty_allowed}/{n} cases license any upgrade "
            f"({nonempty_fraction:.0%} < {MIN_NONEMPTY_ALLOWED_FRACTION:.0%}); a refuse-everything "
            "responder cannot be distinguished from a disciplined one"
        )
    if axes_per_case < MIN_ALLOWED_AXES_PER_CASE:
        failures.append(
            f"only {total_allowed_axes} allowed axes across {n} cases "
            f"({axes_per_case:.2f}/case < {MIN_ALLOWED_AXES_PER_CASE}); valid_upgrade_recall is "
            "too coarsely quantized"
        )
    if pattern_fraction < MIN_DISTINCT_LABEL_PATTERN_FRACTION:
        failures.append(
            f"only {distinct_patterns} distinct label patterns across {n} cases "
            f"({pattern_fraction:.0%} < {MIN_DISTINCT_LABEL_PATTERN_FRACTION:.0%})"
        )

    detail = {
        "n_cases": n,
        "cases_licensing_an_upgrade": nonempty_allowed,
        "nonempty_allowed_fraction": nonempty_fraction,
        "total_allowed_axes": total_allowed_axes,
        "allowed_axes_per_case": axes_per_case,
        "distinct_label_patterns": distinct_patterns,
        "distinct_label_pattern_fraction": pattern_fraction,
        "failures": failures,
    }
    if failures:
        return CheckResult(
            check_id="label_pattern_diversity",
            status=AuditStatus.DEGENERATE,
            message="; ".join(failures),
            detail=detail,
        )
    return CheckResult(
        check_id="label_pattern_diversity",
        status=AuditStatus.CLEAN,
        message=(
            f"{nonempty_allowed}/{n} cases license an upgrade, {total_allowed_axes} allowed axes, "
            f"{distinct_patterns} distinct label patterns"
        ),
        detail=detail,
    )


# --------------------------------------------------------------------------
# check 6: label-blind responder ceiling
# --------------------------------------------------------------------------


Responder = Callable[[VisibleCaseContext], TransitionResponse]


def majority_status_responder(
    cases: Sequence[ScientificTransitionCase],
) -> Responder:
    """Constant baseline: always answer the panel's most common status, raise nothing.

    This is the trivial floor every surface heuristic must be compared against.
    It reads the panel's label distribution, so it is a *baseline*, not a
    candidate system — it exists to make the other responders interpretable.
    """

    counts: dict[TransitionDecision, int] = {}
    for case in cases:
        status = case.labels.required_terminal_status
        counts[status] = counts.get(status, 0) + 1
    majority = max(counts, key=lambda k: (counts[k], k.value))

    def responder(visible: VisibleCaseContext) -> TransitionResponse:
        return TransitionResponse(
            case_id=visible.case_id,
            transition_decision=majority,
            authority_delta={},
            state_edits=frozenset({StateEdit.NO_CHANGE}),
        )

    return responder


def last_candidate_responder(visible: VisibleCaseContext) -> TransitionResponse:
    """Pick the last candidate interpretation and raise every axis it names.

    Label-blind: reads only the visible text. If panels list the trap first and
    the correct reading last, this scores like a reasoner.
    """

    text = visible.candidate_interpretations[-1].lower()
    delta = {
        axis: 1
        for axis, synonyms in _AXIS_SYNONYMS.items()
        if any(s in text for s in synonyms)
        and not any(
            re.search(rf"{_NEGATION}\s+\S*\s*{s}", text) or re.search(rf"{s}[^.;]*{_NEGATION}", text)
            for s in synonyms
        )
    }
    return TransitionResponse(
        case_id=visible.case_id,
        transition_decision=TransitionDecision.SUPPORTED,
        authority_delta=delta,
        state_edits=frozenset({StateEdit.ADD}),
    )


def keyword_refusal_responder(visible: VisibleCaseContext) -> TransitionResponse:
    """Refuse any axis whose name is negated anywhere in the visible text.

    This is the responder that beats a panel whose case ids read
    ``prediction-not-mechanism``: it never reasons, it pattern-matches.
    """

    blob = " ".join(
        [visible.case_id, visible.pre_state, visible.new_observation, *visible.candidate_interpretations]
    ).lower()
    refused = {
        axis
        for axis, synonyms in _AXIS_SYNONYMS.items()
        if any(
            re.search(rf"{_NEGATION}[\s-]+\S*[\s-]*{s}", blob)
            or re.search(rf"{s}[\s-]+\S*[\s-]*{_NEGATION}", blob)
            for s in synonyms
        )
    }
    delta = {axis: 1 for axis in AuthorityAxis if axis not in refused}
    return TransitionResponse(
        case_id=visible.case_id,
        transition_decision=TransitionDecision.SUPPORTED,
        authority_delta=delta,
        state_edits=frozenset({StateEdit.ADD}),
    )


#: Identifier tokens that announce "this case is a trap; the answer is refusal".
_ID_REFUSAL_TOKENS = frozenset({"trap", "missing", "cannot", "blocked", "integrity"})

#: Identifier tokens that announce "this case is a control; the upgrade is licensed".
_ID_LICENCE_TOKENS = frozenset({"legitimate", "upgrade", "valid"})


def case_id_exploit_responder(visible: VisibleCaseContext) -> TransitionResponse:
    """Answer using the ``case_id`` and nothing else.

    Reads no observation, no claim, no candidate. It parses identifiers of the
    form ``<granted>-not-<refused>`` and the control/trap vocabulary, then
    emits the corresponding update. If a panel names its cases after their
    answers, this responder scores like a disciplined scientific reasoner while
    performing no scientific reasoning whatsoever — which is exactly the
    condition that makes a measured ALR uninterpretable.
    """

    parts = [p for p in re.split(r"[-_\s]+", visible.case_id.lower()) if p]
    negation_at = next((i for i, p in enumerate(parts) if p in {"not", "no", "never"}), None)

    def axes_in(tokens: Sequence[str]) -> set[AuthorityAxis]:
        return {
            axis
            for axis, synonyms in _AXIS_SYNONYMS.items()
            if any(token.startswith(s[:6]) for token in tokens for s in synonyms)
        }

    if set(parts) & _ID_REFUSAL_TOKENS:
        return TransitionResponse(
            case_id=visible.case_id,
            transition_decision=TransitionDecision.CANNOT_CHECK,
            authority_delta={},
            state_edits=frozenset({StateEdit.NO_CHANGE}),
        )

    if negation_at is not None:
        granted = axes_in(parts[:negation_at])
        refused = axes_in(parts[negation_at + 1 :])
    elif set(parts) & _ID_LICENCE_TOKENS:
        granted = axes_in(parts)
        refused = set()
    else:
        granted, refused = set(), set()

    delta = {axis: 1 for axis in sorted(granted - refused, key=lambda a: a.value)}
    return TransitionResponse(
        case_id=visible.case_id,
        transition_decision=(
            TransitionDecision.SUPPORTED if delta else TransitionDecision.PARTIALLY_IDENTIFIED
        ),
        authority_delta=delta,
        state_edits=frozenset({StateEdit.ADD} if delta else {StateEdit.NO_CHANGE}),
    )


def label_blind_responders(
    cases: Sequence[ScientificTransitionCase],
) -> Mapping[str, Responder]:
    """Battery of responders that never see a label."""

    from .authority_leakage_benchmark import always_blocked_responder, always_escalate_responder

    return {
        "always_blocked": always_blocked_responder,
        "always_escalate": always_escalate_responder,
        "majority_status": majority_status_responder(cases),
        "last_candidate": last_candidate_responder,
        "keyword_refusal": keyword_refusal_responder,
        "case_id_exploit": case_id_exploit_responder,
    }


def check_label_blind_ceiling(cases: Sequence[ScientificTransitionCase]) -> CheckResult:
    """No label-blind responder may look competent.

    Two conditions:

    * **joint**: ALR <= :data:`CEILING_ALR` *and* valid-upgrade recall >=
      :data:`CEILING_VALID_UPGRADE_RECALL`. Clearing both means withholding
      unlicensed authority while granting licensed authority — exactly what the
      benchmark claims to measure.
    * **relative status**: no responder may beat the constant majority-status
      baseline by more than :data:`MAX_STATUS_GAIN_OVER_MAJORITY`.
    """

    if not cases:
        return CheckResult(
            check_id="label_blind_ceiling",
            status=AuditStatus.CANNOT_CHECK,
            message="empty panel",
            detail={},
        )

    scores: dict[str, Mapping[str, float]] = {}
    for name, responder in label_blind_responders(cases).items():
        result = score_panel(cases, tuple(responder(case.visible) for case in cases))
        scores[name] = {
            "alr": result.alr,
            "valid_upgrade_recall": result.valid_upgrade_recall,
            "terminal_status_accuracy": result.terminal_status_accuracy,
        }

    majority_accuracy = scores["majority_status"]["terminal_status_accuracy"]
    breaches: list[str] = []
    for name, score in scores.items():
        if score["alr"] <= CEILING_ALR and score["valid_upgrade_recall"] >= CEILING_VALID_UPGRADE_RECALL:
            breaches.append(
                f"'{name}' clears the joint ceiling (alr={score['alr']:.2f}, "
                f"valid_upgrade_recall={score['valid_upgrade_recall']:.2f}) without reasoning"
            )
        if name == "majority_status":
            continue
        gain = score["terminal_status_accuracy"] - majority_accuracy
        if gain > MAX_STATUS_GAIN_OVER_MAJORITY:
            breaches.append(
                f"'{name}' beats the constant baseline on terminal status by {gain:.0%} "
                f"(max {MAX_STATUS_GAIN_OVER_MAJORITY:.0%})"
            )

    detail = {
        "responder_scores": scores,
        "majority_status_accuracy": majority_accuracy,
        "breaches": breaches,
    }
    if breaches:
        return CheckResult(
            check_id="label_blind_ceiling",
            status=AuditStatus.DEGENERATE,
            message="; ".join(breaches),
            detail=detail,
        )
    return CheckResult(
        check_id="label_blind_ceiling",
        status=AuditStatus.CLEAN,
        message=f"no label-blind responder clears the ceiling ({len(scores)} tested)",
        detail=detail,
    )


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------


CHECKS: Tuple[Callable[[Sequence[ScientificTransitionCase]], CheckResult], ...] = (
    check_case_id_opacity,
    check_visible_disposition_leak,
    check_single_feature_separation,
    check_positional_shortcut,
    check_label_pattern_diversity,
    check_label_blind_ceiling,
)


def audit_panel(
    cases: Sequence[ScientificTransitionCase], panel_id: str
) -> PanelAuditReport:
    """Run every degeneracy check over a panel.

    Never raises on a degenerate panel — a degenerate panel is a *finding*, and
    the report carries it. Only a malformed panel raises.
    """

    return PanelAuditReport(
        panel_id=panel_id,
        n_cases=len(cases),
        checks=tuple(check(cases) for check in CHECKS),
    )
