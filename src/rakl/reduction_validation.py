"""Admission gate for reduction operators (structuralization instruments).

The reducer — LLM, parser, or domain tool — is pluggable. Whether its output may
enter the structure space at any authority above the floor is not. This module is
the admission gate, and every check in it is a known-answer or no-tunable test,
because each corresponds to a failure already measured in this programme:

**Extraction signal (the Paper II probe-G burn).** A reducer applied to
scrambled text must not return the same structure it returned for the real text.
The six-family instrument scored 6/6 at p=0.03125 while scrambling changed
nothing 810/810 — the coordinates never read the text. The rule here has no
threshold to tune: ONE scramble-invariant source is disqualifying.

**Author independence (the template-inversion finding).** A reducer validated
only against labels written by its own author measures the authorship, not the
extraction — the matched-pair control put the entire measured error in surface
lexicon. External validation labels must carry an author distinct from the
reducer's; absent that, admission is capped at the ASSERTED floor. The empirical
campaign this enables (the n≈48 external-label packet) is data to be supplied,
not mechanics — the gate is complete without it and refuses to pretend otherwise.

**Obstruction harvest (the machine-checked identifiability result).** A reducer
that keeps "the core of each piece" and drops obstructions produces spaces that
are unsound to navigate — proved, not conjectured. The known-answer test feeds
the reducer a calibration source whose obstruction is known (the three-context
parity construction) and requires the obstruction to appear in the output.

Fail-closed throughout: a reducer that raises on any check is REJECTED with
CANNOT_CHECK recorded, never admitted by the absence of a failure.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum

from .certificates import CertificateKind
from .structure_space import ReducedStructure


class AdmissionVerdict(str, Enum):
    ADMITTED = "ADMITTED"
    ADMITTED_AT_FLOOR = "ADMITTED_AT_FLOOR"
    REJECTED = "REJECTED"


#: A calibration source with a KNOWN obstruction: three constraints, pairwise
#: satisfiable, jointly unrealizable. Any admissible reducer must surface an
#: obstruction when reducing it. The wording is fixed; the answer is known.
PARITY_CALIBRATION_SOURCE = (
    "Constraint one: x equals y. Constraint two: y equals z. "
    "Constraint three: x differs from z. Each pair of constraints is "
    "individually satisfiable; no assignment satisfies all three."
)


@dataclass(frozen=True)
class ReducerProfile:
    reducer_id: str
    author: str
    external_label_author: str | None = None

    def __post_init__(self) -> None:
        if not self.reducer_id.strip() or not self.author.strip():
            raise ValueError("reducer identity and author are required")


@dataclass(frozen=True)
class AdmissionReport:
    reducer_id: str
    verdict: AdmissionVerdict
    admitted_kind: CertificateKind | None
    reasons: tuple[str, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def _scramble(text: str, rng: random.Random) -> str:
    chars = list(text)
    rng.shuffle(chars)
    return "".join(chars)


def admit_reducer(
    profile: ReducerProfile,
    reduce_fn: Callable[[str], ReducedStructure],
    sample_sources: Sequence[str],
    *,
    seed: int = 20260814,
) -> AdmissionReport:
    """Run the admission battery. Every check is fail-closed.

    ADMITTED (at EXTERNAL_LABEL kind) requires all three checks AND an external
    label author distinct from the reducer's author. Without the independent
    labels the mechanics still pass but admission is capped at the floor —
    honest structures, no borrowed authority.
    """
    if not sample_sources:
        return AdmissionReport(
            profile.reducer_id,
            AdmissionVerdict.REJECTED,
            None,
            ("no sample sources supplied; an unexercised reducer is unaudited",),
        )

    reasons: list[str] = []

    # 1. Extraction signal: scrambling the text must change the structure.
    for index, source in enumerate(sample_sources):
        rng = random.Random(f"{seed}:{index}")
        try:
            real = reduce_fn(source)
            scrambled = reduce_fn(_scramble(source, rng))
        except Exception as exc:
            return AdmissionReport(
                profile.reducer_id,
                AdmissionVerdict.REJECTED,
                None,
                (f"CANNOT_CHECK: reducer raised on source {index}: {exc!r}",),
            )
        if real.roles == scrambled.roles and real.relations == scrambled.relations:
            reasons.append(
                f"source {index}: identical structure from scrambled text — the "
                "reducer is not reading the text (the probe-G failure shape)"
            )
            break  # one scramble-invariant source is disqualifying; no tally

    # 2. Obstruction harvest: the known-obstructed calibration source.
    try:
        calibration = reduce_fn(PARITY_CALIBRATION_SOURCE)
        if not calibration.structure.obstructions:
            reasons.append(
                "calibration: the parity source has a known obstruction and the "
                "reducer surfaced none — obstruction-blind distillation is "
                "unsound for navigation (machine-checked)"
            )
    except Exception as exc:
        return AdmissionReport(
            profile.reducer_id,
            AdmissionVerdict.REJECTED,
            None,
            (f"CANNOT_CHECK: reducer raised on the calibration source: {exc!r}",),
        )

    if reasons:
        return AdmissionReport(
            profile.reducer_id, AdmissionVerdict.REJECTED, None, tuple(reasons)
        )

    # 3. Author independence decides the admitted kind.
    if (
        profile.external_label_author is None
        or profile.external_label_author == profile.author
    ):
        return AdmissionReport(
            profile.reducer_id,
            AdmissionVerdict.ADMITTED_AT_FLOOR,
            CertificateKind.ASSERTED,
            (
                "mechanics pass, but validation labels are absent or share the "
                "reducer's author; self-authored validation measures the "
                "authorship, so admission is capped at the ASSERTED floor until "
                "independent labels are supplied",
            ),
        )

    return AdmissionReport(
        profile.reducer_id,
        AdmissionVerdict.ADMITTED,
        CertificateKind.EXTERNAL_LABEL,
        (),
    )
