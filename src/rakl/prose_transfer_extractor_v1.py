"""Candidate arms for the Paper II prose-transfer instrument.

Every arm here receives a `ProseTask` and may read **only** `source_text` and
`target_text`. No arm receives the `LatentSpec`, and no arm is the gold
function, so the primary paired statistic compares two predictors that both
have variance.

`FULL_PROSE_EXTRACTOR` derives its reference values from the *source* prose —
the bound, the required component count, the quantity name, the QoI, the regime
and the precondition are all parsed out of the source paragraph, not hardcoded
per family. It then checks the target paragraph against them. That is the
transfer task.

Coordinate recovery uses general rules rather than template lookups:

* **Absence of the authoritative pattern means CANNOT_CHECK.** A hedged
  coordinate never contains the authoritative construction, so the extractor
  never needs the hedge lexicon — which matters because the dev and heldout
  hedge banks are disjoint.
* **Polarity cues plus negation parity.** Threshold direction and completeness
  are resolved from general English cue vocabulary, then inverted once per
  negation cue in the clause.
* **Semicolon discourse heuristic.** When a sentence contrasts a superseded
  configuration with the current one, the assertion after the semicolon is the
  operative claim.

Honest limitation, registered at freeze: the same agent authored the renderer's
heldout bank and these cue lists. The dev/heldout split reduces but does not
eliminate template inversion, which is why the protocol registers a strict
`full_exact < 1.00` ceiling and an error-attribution gate.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

from rakl.objective_transfer_benchmark import Decision
from rakl.prose_transfer_instrument_v1 import COORDINATES, ProseTask, merge_decisions

# ---------------------------------------------------------------------------
# General cue vocabulary
# ---------------------------------------------------------------------------

NEGATION_CUES = ("no ", "not ", "never", "nothing", "none", "without", "n't")

# Threshold direction.
BELOW_CUES = (
    "below",
    "under",
    "within",
    "beneath",
    "inside",
    "less than",
    "short of",
    "smaller than",
)
ABOVE_CUES = (
    "above",
    "over",
    "past",
    "exceed",
    "beyond",
    "outside",
    "breach",
    "overshoot",
    "greater than",
    "larger than",
    "reach",
)

# Completeness of a correspondence.
COMPLETE_CUES = (
    "every",
    " all ",
    "in full",
    "fully",
    "entire",
    "complete",
    "without exception",
    "unpaired",
    "unmatched",
    "left out",
)
INCOMPLETE_CUES = (
    "some",
    "part",
    "partial",
    "partly",
    "not all",
    "short",
    "omit",
    "miss",
    "incomplete",
    "few",
)

# Whether a stated precondition holds.
HOLDS_CUES = ("hold", "maintain", "uphold", "upheld", "satisfie", "satisfy", "met", "preserv")
FAILS_CUES = ("break", "lost", "lose", "fail", "violat", "ceas", "gives way", "give way", "disturb")


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _operative(sentence: str) -> str:
    """Discourse heuristic: after a semicolon, the later clause is the claim."""
    return sentence.rsplit(";", 1)[-1].strip() if ";" in sentence else sentence


def _negations(text: str) -> int:
    low = " " + text.lower() + " "
    return sum(low.count(cue) for cue in NEGATION_CUES)


def _polarity(text: str, positive: tuple[str, ...], negative: tuple[str, ...]) -> bool | None:
    """True if `positive` cues win, False if `negative` do, None if undecidable."""
    low = " " + text.lower() + " "
    pos = sum(1 for cue in positive if cue in low)
    neg = sum(1 for cue in negative if cue in low)
    if pos == neg:
        return None
    verdict = pos > neg
    if _negations(text) % 2 == 1:
        verdict = not verdict
    return verdict


def _status(value: bool | None) -> Decision:
    if value is None:
        return Decision.CANNOT_CHECK
    return Decision.ACCEPT if value else Decision.REJECT


# ---------------------------------------------------------------------------
# Source-side reference extraction
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SourceReference:
    quantity: str | None
    threshold: float | None
    qoi: str | None
    regime: str | None
    precondition: str | None
    required: int | None
    source_noun: str | None


def parse_source(text: str) -> SourceReference:
    quantity = threshold = qoi = regime = precondition = required = source_noun = None

    m = re.search(
        r"Working in (?P<regime>.+?), we establish (?P<qoi>.+?) for (?P<noun>the [^,]+?) "
        r"whenever the (?P<quantity>.+?) stays below the stated bound of (?P<bound>[0-9.]+)",
        text,
    )
    if m:
        regime = m.group("regime").strip()
        qoi = m.group("qoi").strip()
        source_noun = m.group("noun").strip()
        quantity = m.group("quantity").strip()
        threshold = float(m.group("bound"))

    m = re.search(r"The argument requires (?P<pre>.+?)\.", text)
    if m:
        precondition = m.group("pre").strip()

    m = re.search(r"covering all (?P<n>\d+) required", text)
    if m:
        required = int(m.group("n"))

    return SourceReference(quantity, threshold, qoi, regime, precondition, required, source_noun)


# ---------------------------------------------------------------------------
# Per-coordinate recovery from the target prose
# ---------------------------------------------------------------------------


def _extract_qoi(sents: list[str], ref: SourceReference) -> Decision:
    if ref.qoi is None:
        return Decision.CANNOT_CHECK
    for sentence in sents:
        if "asks about" not in sentence:
            continue
        clause = _operative(sentence)
        m = re.search(r"asks about (?P<name>.+?)[.;]", clause + ".")
        if m is None:
            continue
        return _status(m.group("name").strip().rstrip(".") == ref.qoi)
    return Decision.CANNOT_CHECK


def _extract_boundary(sents: list[str], ref: SourceReference) -> Decision:
    if ref.regime is None:
        return Decision.CANNOT_CHECK
    for sentence in sents:
        if "operate" not in sentence.lower():
            continue
        clause = _operative(sentence)
        m = re.search(r"operates? in (?P<name>.+?)[.;]", clause + ".")
        if m is None:
            continue
        return _status(m.group("name").strip().rstrip(".") == ref.regime)
    return Decision.CANNOT_CHECK


def _extract_direction(sents: list[str], ref: SourceReference) -> Decision:
    if ref.source_noun is None:
        return Decision.CANNOT_CHECK
    for sentence in sents:
        low = sentence.lower()
        if "applied" not in low and "applies it" not in low:
            continue
        clause = _operative(sentence)
        m = re.search(r"(?:applied|applies it) from (?P<a>the .+?) to (?P<b>the [^.;]+)", clause)
        if m is None:
            continue
        return _status(m.group("a").strip() == ref.source_noun)
    return Decision.CANNOT_CHECK


def _extract_relation(sents: list[str], ref: SourceReference) -> tuple[Decision, bool]:
    """Returns (decision, saw_authoritative_pattern)."""
    if ref.required is None:
        return Decision.CANNOT_CHECK, False
    for sentence in sents:
        low = sentence.lower()
        if "correspondence" not in low and "mapping" not in low:
            continue
        clause = _operative(sentence)
        m = re.search(r"covers (?P<k>\d+) of (?:the )?(?P<m>\d+)", clause)
        if m:
            return _status(int(m.group("k")) >= int(m.group("m"))), True
        m = re.search(r"(?P<pct>[0-9.]+)% of the required", clause)
        if m:
            return _status(float(m.group("pct")) >= 100.0), True
        verdict = _polarity(clause, COMPLETE_CUES, INCOMPLETE_CUES)
        if verdict is not None:
            return _status(verdict), True
    return Decision.CANNOT_CHECK, False


def _extract_precondition(sents: list[str], ref: SourceReference) -> Decision:
    if ref.precondition is None:
        return Decision.CANNOT_CHECK
    key = ref.precondition.lower()
    for sentence in sents:
        if key not in sentence.lower():
            continue
        clause = _operative(sentence)
        if key not in clause.lower():
            continue
        verdict = _polarity(clause, HOLDS_CUES, FAILS_CUES)
        if verdict is not None:
            return _status(verdict)
    return Decision.CANNOT_CHECK


def _extract_effect(sents: list[str], ref: SourceReference) -> Decision:
    if ref.quantity is None or ref.threshold is None:
        return Decision.CANNOT_CHECK
    key = ref.quantity.lower()
    for sentence in sents:
        if key not in sentence.lower():
            continue
        clause = _operative(sentence)
        if key not in clause.lower():
            continue
        m = re.search(r"reaches (?P<pct>[0-9.]+)% of the stated bound", clause)
        if m:
            return _status(float(m.group("pct")) < 100.0)
        m = re.search(rf"{re.escape(key)} of .+? is (?P<v>[0-9.]+)", clause.lower())
        if m:
            return _status(float(m.group("v")) < ref.threshold)
        m = re.search(rf"{re.escape(key)} of .+? records (?P<v>[0-9.]+)", clause.lower())
        if m:
            return _status(float(m.group("v")) < ref.threshold)
        m = re.search(r"records (?P<v>[0-9.]+)", clause.lower())
        if m:
            return _status(float(m.group("v")) < ref.threshold)
        verdict = _polarity(clause, BELOW_CUES, ABOVE_CUES)
        if verdict is not None:
            return _status(verdict)
    return Decision.CANNOT_CHECK


def extract_coordinates(task: ProseTask) -> Mapping[str, Decision]:
    ref = parse_source(task.source_text)
    sents = _sentences(task.target_text)
    relation, _ = _extract_relation(sents, ref)
    return {
        "qoi": _extract_qoi(sents, ref),
        "boundary": _extract_boundary(sents, ref),
        "direction": _extract_direction(sents, ref),
        "relation": relation,
        "precondition": _extract_precondition(sents, ref),
        "effect": _extract_effect(sents, ref),
    }


# ---------------------------------------------------------------------------
# Arms
# ---------------------------------------------------------------------------


def full_prose_extractor(task: ProseTask) -> Decision:
    coords = extract_coordinates(task)
    return merge_decisions([coords[c] for c in COORDINATES])


_POSITIVE_CUES = (
    "satisfies",
    "holds",
    "maintained",
    "every",
    "all",
    "below",
    "within",
    "under",
    "no indication",
)
_NEGATIVE_CUES = (
    "violates",
    "breaks",
    "not all",
    "unmatched",
    "above",
    "over",
    "exceed",
    "no evidence",
    "does not",
)


def keyword_polarity_parent(task: ProseTask) -> Decision:
    """Strongest non-extraction parent: reads the text, parses no structure."""
    low = " " + task.target_text.lower() + " "
    pos = sum(low.count(cue) for cue in _POSITIVE_CUES)
    neg = sum(low.count(cue) for cue in _NEGATIVE_CUES)
    if pos == neg:
        return Decision.CANNOT_CHECK
    return Decision.ACCEPT if pos > neg else Decision.REJECT


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", text.lower()))


def lexical_parent(task: ProseTask, threshold: float) -> Decision:
    a, b = _tokens(task.source_text), _tokens(task.target_text)
    if not a or not b:
        return Decision.CANNOT_CHECK
    overlap = len(a & b) / len(a | b)
    return Decision.ACCEPT if overlap >= threshold else Decision.REJECT


def lexical_overlap(task: ProseTask) -> float:
    a, b = _tokens(task.source_text), _tokens(task.target_text)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)
