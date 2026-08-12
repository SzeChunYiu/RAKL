"""Capability qualification V3 — Stage 0/1 instrument audit and diagnostic decomposition.

Scope (issue #447 Stage 0 and Stage 1):

* Stage 0 requires an objective gold/evaluator audit *before* any model output. That
  audit was not run for ``paper2-oracle-capability-gate-v2-exec``. This module performs
  it retrospectively on preserved development data.
* Stage 1 requires a per-stage diagnostic decomposition that does not hide early-stage
  errors behind a final aggregate score.

Hard boundaries encoded here, not left to prose:

* This module never rescores a sealed job. :func:`stage_decompose` reports the observable
  facts of a generation; it deliberately provides **no** convention-corrected score, and
  there is no code path that produces one. ``MODEL_CAPABILITY_FLOOR_7B_V2_EXEC`` stands.
* Stage 1 runs on development items and *cannot* authorize capability. No function here
  emits ``CAPABLE_MODEL_AUTHORIZE_RECEIPT_V3``.
* The instrument audit is diagnosed from the **instruction surface**, never from the
  outcome. :func:`audit_instruction_semantics` reads only prompt text and does not accept
  scores, generations or gold answers as arguments.

The distinction that motivates the module: an evidence-adjudication interface that names
the fields ``selected_evidence_ids``/``rejected_evidence_ids`` without defining what makes
an id "selected" admits at least two coherent readings —

``LICENSES_VERDICT``
    selected = the evidence that licenses the stated verdict.
``CLAIM_REFERENT``
    selected = the evidence the adjudicated claim is about.

When gold uses one reading and the instruction surface names neither, a model answering
under the other reading produces the exact partition with the two labels swapped, and a
recall-based evaluator scores that as a total evidence-binding failure. The measurement
then cannot separate "cannot bind evidence" from "used the other admissible reading",
which is an identifiability defect in the instrument.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

__all__ = [
    "CANONICAL_EVIDENCE_ROLE_DEFINITION",
    "EVIDENCE_ROLE_READING_CLAIM_REFERENT",
    "EVIDENCE_ROLE_READING_LICENSES_VERDICT",
    "InstructionSemanticsAudit",
    "ItemDiagnosis",
    "audit_instruction_semantics",
    "diagnose_stage_bottleneck",
    "stage_decompose",
]

EVIDENCE_ROLE_READING_LICENSES_VERDICT = "LICENSES_VERDICT"
EVIDENCE_ROLE_READING_CLAIM_REFERENT = "CLAIM_REFERENT"

#: Exact marker a repaired interface must carry so the ``LICENSES_VERDICT`` reading is
#: stated rather than assumed. Kept as one constant so contract, runner and guard test
#: cannot drift apart.
CANONICAL_EVIDENCE_ROLE_DEFINITION = (
    "selected_evidence_ids MUST list exactly the evidence ids that license your verdict; "
    "rejected_evidence_ids MUST list every other supplied id, including evidence that is "
    "on-topic but unreliable, superseded, or measures a different quantity of interest."
)

# Heuristic sweep for *any* role-defining language attached to the evidence fields,
# regardless of wording. This exists so an absence claim is backed by a justified search
# scope rather than by one narrow pattern returning nothing.
_ROLE_LANGUAGE_PATTERNS: tuple[tuple[str, str], ...] = (
    ("licenses_verdict", r"(select\w*|reject\w*)[^.\n]{0,120}\b(licen[cs]\w*|justif\w*|support\w* your|warrant\w*)"),
    ("basis_for_verdict", r"(select\w*|reject\w*)[^.\n]{0,120}\b(basis|ground\w*|premise\w*)\b"),
    ("relied_upon", r"(select\w*|reject\w*)[^.\n]{0,120}\b(relied? (up)?on|used to (reach|decide)|you used)"),
    ("claim_referent", r"(select\w*|reject\w*)[^.\n]{0,120}\b(about the claim|the claim (is )?about|mentioned in the claim)"),
    ("relevance_reading", r"(select\w*|reject\w*)[^.\n]{0,120}\b(relevant|irrelevant|on-topic|pertinent)\b"),
    ("definitional_copula", r"\bselected_evidence_ids\b[^.\n]{0,40}\b(is|are|means?|should contain|must (list|contain))\b"),
    ("reject_definitional", r"\brejected_evidence_ids\b[^.\n]{0,40}\b(is|are|means?|should contain|must (list|contain))\b"),
)


@dataclass(frozen=True)
class InstructionSemanticsAudit:
    """Result of auditing an instruction surface for evidence-role semantics."""

    surface_label: str
    mentions_selected_field: bool
    mentions_rejected_field: bool
    canonical_definition_present: bool
    role_language_matches: tuple[tuple[str, str], ...]
    patterns_swept: tuple[str, ...]

    @property
    def defines_evidence_role(self) -> bool:
        """True when the surface conveys *some* role semantics for the evidence fields."""
        return self.canonical_definition_present or bool(self.role_language_matches)

    @property
    def verdict(self) -> str:
        if not (self.mentions_selected_field or self.mentions_rejected_field):
            return "EVIDENCE_FIELDS_ABSENT"
        if self.canonical_definition_present:
            return "EVIDENCE_ROLE_DEFINED_CANONICAL"
        if self.role_language_matches:
            return "EVIDENCE_ROLE_DEFINED_NONCANONICAL"
        return "EVIDENCE_ROLE_UNDEFINED"

    def as_dict(self) -> dict[str, Any]:
        return {
            "surface_label": self.surface_label,
            "mentions_selected_field": self.mentions_selected_field,
            "mentions_rejected_field": self.mentions_rejected_field,
            "canonical_definition_present": self.canonical_definition_present,
            "defines_evidence_role": self.defines_evidence_role,
            "role_language_matches": [
                {"pattern": name, "matched_text": text} for name, text in self.role_language_matches
            ],
            "patterns_swept": list(self.patterns_swept),
            "verdict": self.verdict,
        }


def audit_instruction_semantics(text: str, *, surface_label: str) -> InstructionSemanticsAudit:
    """Audit one instruction surface for evidence-role semantics.

    Reads prompt text only. Takes no scores, generations or gold answers, so an
    ``EVIDENCE_ROLE_UNDEFINED`` verdict is a property of the instrument and cannot be an
    artefact of an inconvenient outcome.
    """
    haystack = text.lower()
    matches: list[tuple[str, str]] = []
    for name, pattern in _ROLE_LANGUAGE_PATTERNS:
        found = re.search(pattern, haystack, flags=re.IGNORECASE)
        if found is not None:
            matches.append((name, found.group(0).strip()))
    return InstructionSemanticsAudit(
        surface_label=surface_label,
        mentions_selected_field="selected_evidence_ids" in haystack,
        mentions_rejected_field="rejected_evidence_ids" in haystack,
        canonical_definition_present=CANONICAL_EVIDENCE_ROLE_DEFINITION.lower() in haystack,
        role_language_matches=tuple(matches),
        patterns_swept=tuple(name for name, _ in _ROLE_LANGUAGE_PATTERNS),
    )


@dataclass(frozen=True)
class ItemDiagnosis:
    """Per-item observable facts for one generation against its sealed answer.

    Carries no score. Convention-sensitive and convention-invariant observations are kept
    as separate fields so a formatting or labelling effect can never be reported as
    research capability.
    """

    task_id: str
    parse_valid: bool
    verdict_correct: bool
    predicted_verdict: str | None
    gold_verdict: str
    partition_exact_match: bool
    partition_exact_inversion: bool
    partition_matches_up_to_label: bool
    inversion_identifiable: bool
    predicted_selected: tuple[str, ...] = ()
    predicted_rejected: tuple[str, ...] = ()
    gold_selected: tuple[str, ...] = ()
    gold_rejected: tuple[str, ...] = ()
    notes: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "parse_valid": self.parse_valid,
            "predicted_verdict": self.predicted_verdict,
            "gold_verdict": self.gold_verdict,
            "verdict_correct": self.verdict_correct,
            "partition_exact_match": self.partition_exact_match,
            "partition_exact_inversion": self.partition_exact_inversion,
            "partition_matches_up_to_label": self.partition_matches_up_to_label,
            "inversion_identifiable": self.inversion_identifiable,
            "predicted_selected": list(self.predicted_selected),
            "predicted_rejected": list(self.predicted_rejected),
            "gold_selected": list(self.gold_selected),
            "gold_rejected": list(self.gold_rejected),
            "notes": list(self.notes),
        }


def _as_set(value: Any) -> frozenset[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return frozenset()
    return frozenset(str(item) for item in value)


def stage_decompose(generation: Mapping[str, Any], task: Mapping[str, Any]) -> ItemDiagnosis:
    """Decompose one preserved generation against its sealed answer.

    Deliberately returns no score and no pass/fail. The caller sees the separate
    observables and must not collapse them.
    """
    gold = task["sealed_answer"]
    gold_selected = _as_set(gold.get("selected_evidence_ids"))
    gold_rejected = _as_set(gold.get("rejected_evidence_ids"))

    parsed = generation.get("parsed")
    if not isinstance(parsed, Mapping):
        return ItemDiagnosis(
            task_id=str(task["task_id"]),
            parse_valid=False,
            verdict_correct=False,
            predicted_verdict=None,
            gold_verdict=str(gold["verdict"]),
            partition_exact_match=False,
            partition_exact_inversion=False,
            partition_matches_up_to_label=False,
            inversion_identifiable=gold_selected != gold_rejected,
            gold_selected=tuple(sorted(gold_selected)),
            gold_rejected=tuple(sorted(gold_rejected)),
            notes=("parse_invalid_no_partition_observable",),
        )

    predicted_selected = _as_set(parsed.get("selected_evidence_ids"))
    predicted_rejected = _as_set(parsed.get("rejected_evidence_ids"))
    predicted_verdict = parsed.get("verdict")

    exact_match = predicted_selected == gold_selected and predicted_rejected == gold_rejected
    # An inversion is only *identifiable* when swapping the gold labels yields a different
    # answer; otherwise "inverted" and "correct" are the same string and the item carries
    # no information about which reading the model used.
    inversion_identifiable = gold_selected != gold_rejected
    exact_inversion = (
        inversion_identifiable
        and predicted_selected == gold_rejected
        and predicted_rejected == gold_selected
    )

    notes: list[str] = []
    if exact_inversion:
        notes.append("partition_solved_labels_swapped")
    if not exact_match and not exact_inversion:
        notes.append("partition_neither_match_nor_inversion")

    return ItemDiagnosis(
        task_id=str(task["task_id"]),
        parse_valid=True,
        verdict_correct=predicted_verdict == gold["verdict"],
        predicted_verdict=None if predicted_verdict is None else str(predicted_verdict),
        gold_verdict=str(gold["verdict"]),
        partition_exact_match=exact_match,
        partition_exact_inversion=exact_inversion,
        partition_matches_up_to_label=exact_match or exact_inversion,
        inversion_identifiable=inversion_identifiable,
        predicted_selected=tuple(sorted(predicted_selected)),
        predicted_rejected=tuple(sorted(predicted_rejected)),
        gold_selected=tuple(sorted(gold_selected)),
        gold_rejected=tuple(sorted(gold_rejected)),
        notes=tuple(notes),
    )


def diagnose_stage_bottleneck(
    diagnoses: Sequence[ItemDiagnosis],
    audits: Sequence[InstructionSemanticsAudit],
) -> dict[str, Any]:
    """Aggregate per-item diagnoses into an issue #447 Stage 1 diagnosis state.

    Returns ``BENCHMARK_CONSTRUCT_DEFECT`` only when both conditions hold: the instruction
    surface objectively fails to define the evidence roles, *and* at least one generation
    exhibits an identifiable exact partition inversion. Either alone is insufficient — an
    undefined field that no model actually reads the other way is a latent defect, not a
    demonstrated confound.
    """
    if not diagnoses:
        raise ValueError("diagnose_stage_bottleneck requires at least one item diagnosis")

    n = len(diagnoses)
    parse_valid = sum(1 for d in diagnoses if d.parse_valid)
    verdict_correct = sum(1 for d in diagnoses if d.verdict_correct)
    exact_match = sum(1 for d in diagnoses if d.partition_exact_match)
    exact_inversion = sum(1 for d in diagnoses if d.partition_exact_inversion)
    identifiable = [d for d in diagnoses if d.inversion_identifiable]

    role_defined = all(a.defines_evidence_role for a in audits) if audits else False
    any_surface_undefined = any(not a.defines_evidence_role for a in audits)

    if exact_inversion and any_surface_undefined:
        state = "BENCHMARK_CONSTRUCT_DEFECT"
        rationale = (
            "At least one generation reproduced the gold evidence partition exactly with the "
            "two labels swapped, while the instruction surface defines no role semantics for "
            "selected_evidence_ids/rejected_evidence_ids. Evidence-binding capability is not "
            "identifiable from this instrument."
        )
    elif exact_inversion and role_defined:
        state = "EVIDENCE_BINDING_FLOOR"
        rationale = (
            "Exact partition inversion persists although the instruction surface defines the "
            "evidence roles. The model solved the partition but cannot apply the stated role "
            "convention."
        )
    elif parse_valid == n and verdict_correct < n:
        state = "NO_CLEAR_SINGLE_BOTTLENECK"
        rationale = (
            "Structured readout is intact and no systematic labelling confound was detected; "
            "residual failures are distributed across verdict composition."
        )
    else:
        state = "FINAL_READOUT_BOTTLENECK"
        rationale = "Parse validity is the limiting stage."

    return {
        "diagnosis_state": state,
        "rationale": rationale,
        "item_count": n,
        "stage_observables": {
            "F_FINAL_STRUCTURED_READOUT": {
                "parse_valid_count": parse_valid,
                "parse_valid_rate": round(parse_valid / n, 6),
            },
            "D_EXACT_EVIDENCE_BINDING": {
                "partition_exact_match_count": exact_match,
                "partition_exact_inversion_count": exact_inversion,
                "inversion_identifiable_item_count": len(identifiable),
                "partition_matches_up_to_label_count": sum(
                    1 for d in diagnoses if d.partition_matches_up_to_label
                ),
            },
            "E_VERDICT_COMPOSITION": {
                "verdict_correct_count": verdict_correct,
                "verdict_accuracy": round(verdict_correct / n, 6),
                "comparability_note": (
                    "Verdict accuracy is a Stage 1 per-stage diagnostic metric. It is NOT "
                    "comparable to the frozen exact-success gate, which requires verdict AND "
                    "support recall AND reject recall jointly. Do not compare this number to "
                    "any success threshold."
                ),
            },
            "A_EVIDENCE_RELEVANCE__B_EVIDENCE_POLARITY__C_CONTEXT_QOI_ALIGNMENT": {
                "separability": "NOT_SEPARABLE_IN_MONOLITHIC_READOUT",
                "note": (
                    "A single-shot structured readout exposes no intermediate artefact for "
                    "these stages, so per-stage accuracy cannot be computed from preserved "
                    "outputs. This is itself the Stage 1 finding that motivates a staged "
                    "interface challenger under issue #447 Stage 2."
                ),
            },
        },
        "instruction_surface_audits": [a.as_dict() for a in audits],
        "no_rescore_guarantee": (
            "This decomposition emits no score and no convention-corrected success count. "
            "Sealed job verdicts are unchanged."
        ),
        "authorization_boundary": (
            "Stage 1 development diagnostics cannot authorize capability. No "
            "CAPABLE_MODEL_AUTHORIZE_RECEIPT_V3 may be derived from this receipt."
        ),
    }
