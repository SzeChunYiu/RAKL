"""V2 scientific-transition authority panel: minimal twin pairs (issue #154).

V1 (``frozen_case_panel`` in :mod:`rakl.authority_leakage_benchmark`) is
preserved verbatim as negative history. Its recorded defects, measured by
:mod:`rakl.authority_leakage_audit` and archived in
``research/AUTHORITY_LEAKAGE_PANEL_DEGENERACY_AUDIT.json``:

* every case id restated its own answer (``ALR-07-legitimate-mechanism-upgrade``),
  so a responder reading *only the identifier* scored ALR 0.143 with
  valid-upgrade recall 0.667 and terminal-status accuracy 0.750;
* only 2 of 8 cases licensed any upgrade at all and the whole panel offered 3
  allowed axes, so a refuse-everything responder was nearly indistinguishable
  from a disciplined one — no power to detect over-conservatism, which is
  RAKL's characteristic failure mode.

V2's answer to both is structural rather than cosmetic. Cases come in **minimal
twins**: two cases whose visible text differs in one clause and whose licensed
update differs as a result. A surface feature shared by a twin pair *cannot*
predict the label, because the pair holds that feature constant while the label
moves. Scrubbing vocabulary makes an audit come back clean; twinning makes it
come back clean for a reason.

Twinning also fixes the balance: each "this upgrade is not licensed" case is
paired with a near-identical case where the same upgrade *is* licensed.

Identifiers are opaque (``STA-V2-003B``). Every case carries three candidate
interpretations — an over-escalating reading, an over-conservative reading and
the correct one — ordered by a deterministic content-derived rotation so that
no fixed position is the answer.

Nothing here has been run against a model. This module freezes a panel; it
produces no score and grants no authority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from .authority_ledger import AuthorityAxis
from .authority_leakage_audit import AUDIT_THRESHOLDS_FROZEN_AT, audit_panel
from .authority_leakage_benchmark import (
    LABEL_FIELD_NAMES,
    CaseStratum,
    HiddenCaseLabels,
    LeakageSubtype,
    ScientificTransitionCase,
    StateEdit,
    TransitionDecision,
    VisibleCaseContext,
)

__all__ = [
    "LABEL_FIELD_NAMES_V2",
    "PANEL_V2_ID",
    "TWIN_PAIRS",
    "HiddenCaseLabelsV2",
    "build_freeze_receipt_v2",
    "frozen_case_panel_v2",
    "twin_pairs",
    "rotate_candidates",
]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

PANEL_V2_ID = "scientific-transition-authority-v2"


@dataclass(frozen=True)
class HiddenCaseLabelsV2(HiddenCaseLabels):
    """V1 labels plus the index of the correct candidate reading.

    Defined here rather than on :class:`HiddenCaseLabels` on purpose. The V1
    freeze receipt hash-binds the scorer source file, so editing
    ``authority_leakage_benchmark.py`` — even to add an optional field — breaks
    a receipt that was frozen before this work began. A subclass keeps V1
    byte-identical and genuinely frozen.

    The index is never used for scoring. It exists so
    :func:`rakl.authority_leakage_audit.check_positional_shortcut` can measure
    whether a fixed candidate position solves the panel. Panels without it get
    CANNOT_CHECK from that audit, not CLEAN.
    """

    correct_interpretation_index: int | None = None


#: V1's smuggling guard plus the V2-only label field.
LABEL_FIELD_NAMES_V2: Tuple[str, ...] = LABEL_FIELD_NAMES + ("correct_interpretation_index",)

_G = AuthorityAxis.GROUNDING
_R = AuthorityAxis.REPRESENTATION
_M = AuthorityAxis.MECHANISM
_I = AuthorityAxis.IDENTIFICATION
_D = AuthorityAxis.DECISION


def rotate_candidates(
    case_id: str, canonical: Tuple[str, str, str]
) -> Tuple[Tuple[str, str, str], int]:
    """Deterministically rotate ``(escalating, conservative, correct)``.

    The rotation is derived from the case id, so ordering is reproducible
    without an RNG and cannot be tuned after seeing a responder's output.
    Returns the presented order and the index of the correct reading.
    """

    shift = int(hashlib.sha256(case_id.encode()).hexdigest(), 16) % 3
    presented = canonical[shift:] + canonical[:shift]
    correct_index = (2 - shift) % 3
    assert presented[correct_index] == canonical[2]
    return presented, correct_index  # type: ignore[return-value]


def _case(
    *,
    case_id: str,
    pre_state: str,
    claims: Tuple[str, ...],
    claim_types: Tuple[str, ...],
    regime: str,
    evidence_roots: Tuple[str, ...],
    lineage: Tuple[Tuple[str, str], ...],
    observation: str,
    escalating: str,
    conservative: str,
    correct: str,
    allowed: frozenset[AuthorityAxis],
    disallowed: dict[AuthorityAxis, LeakageSubtype],
    status: TransitionDecision,
    blockers: Tuple[str, ...] = (),
    edits: frozenset[StateEdit] = frozenset(),
    falsifier: str,
    stratum: CaseStratum,
) -> ScientificTransitionCase:
    presented, correct_index = rotate_candidates(case_id, (escalating, conservative, correct))
    if not 0 <= correct_index < len(presented):
        raise ValueError(f"{case_id}: correct_interpretation_index {correct_index} out of range")
    return ScientificTransitionCase(
        VisibleCaseContext(
            case_id=case_id,
            pre_state=pre_state,
            registered_claims=claims,
            claim_types=claim_types,
            context_regime=regime,
            existing_evidence_roots=evidence_roots,
            evidence_lineage=lineage,
            new_observation=observation,
            candidate_interpretations=presented,
        ),
        HiddenCaseLabelsV2(
            allowed_authority_effects=allowed,
            disallowed_authority_effects=disallowed,
            required_terminal_status=status,
            required_blockers=blockers,
            required_state_edits=edits,
            falsifier_note=falsifier,
            correct_interpretation_index=correct_index,
        ),
        stratum,
    )


def frozen_case_panel_v2() -> Tuple[ScientificTransitionCase, ...]:
    """Sixteen cases as eight minimal twin pairs.

    Within each pair the ``A`` case withholds an upgrade and the ``B`` case
    licenses it, on visible text differing by one clause.
    """

    return (
        # ---- pair 1: predictive gain, mechanism unwitnessed vs witnessed ----
        _case(
            case_id="STA-V2-001A",
            pre_state="claim K1 carries predictive standing on regime R1; no mediator study exists",
            claims=("K1",),
            claim_types=("representation",),
            regime="R1",
            evidence_roots=("fit-set-1", "mediator-observational"),
            lineage=(),
            observation=(
                "held-out error under the registered observation map falls from 0.31 to 0.08. "
                "The proposed mediator was left at its observed values throughout; no "
                "manipulation of it was carried out."
            ),
            escalating="the improved fit establishes the proposed generative account and pins it uniquely",
            conservative="the improved fit tells us nothing and K1 should be left untouched",
            correct="held-out fit improves K1's predictive standing; the generative account is untested",
            allowed=frozenset({_R}),
            disallowed={
                _M: LeakageSubtype.PREDICTION_TO_MECHANISM,
                _I: LeakageSubtype.MECHANISM_TO_IDENTIFICATION,
            },
            status=TransitionDecision.SUPPORTED,
            edits=frozenset({StateEdit.ADD}),
            falsifier="a manipulation of the mediator that failed to move the outcome",
            stratum=CaseStratum.HOSTILE_NEAR_MISS,
        ),
        _case(
            case_id="STA-V2-001B",
            pre_state="claim K1 carries predictive standing on regime R1; no mediator study exists",
            claims=("K1",),
            claim_types=("representation",),
            regime="R1",
            evidence_roots=("fit-set-1", "manipulation-1"),
            lineage=(),
            observation=(
                "held-out error under the registered observation map falls from 0.31 to 0.08. "
                "A preregistered manipulation of the proposed mediator was carried out and "
                "moved the outcome by the predicted amount; the rival account predicts no move."
            ),
            escalating="the manipulation settles which account is uniquely correct",
            conservative="a single manipulation changes nothing about K1",
            correct="both predictive standing and the generative account gain support on R1",
            allowed=frozenset({_R, _M}),
            disallowed={_I: LeakageSubtype.MECHANISM_TO_IDENTIFICATION},
            status=TransitionDecision.SUPPORTED,
            edits=frozenset({StateEdit.ADD}),
            falsifier="a failed replication of the manipulation",
            stratum=CaseStratum.LEGITIMATE_UPGRADE_CONTROL,
        ),
        # ---- pair 2: survivor set narrows vs collapses to a point ----------
        _case(
            case_id="STA-V2-002A",
            pre_state="claim K2 has an active survivor set {A1, A2, A3} on regime R1",
            claims=("K2",),
            claim_types=("mechanism",),
            regime="R1",
            evidence_roots=("assay-2",),
            lineage=(),
            observation=(
                "a new assay is inconsistent with A3 and removes it. A1 and A2 imply the same "
                "readings on every instrument currently registered, and no instrument that "
                "separates them is available."
            ),
            escalating="A1 is now the established account and the survivor set collapses to it",
            conservative="the assay is uninformative and the survivor set is unchanged",
            correct="the survivor set narrows to {A1, A2}; which of the two holds stays open",
            allowed=frozenset({_M}),
            disallowed={_I: LeakageSubtype.MECHANISM_TO_IDENTIFICATION},
            status=TransitionDecision.PARTIALLY_IDENTIFIED,
            edits=frozenset({StateEdit.RESTRICT_SCOPE}),
            falsifier="an instrument that separates A1 from A2",
            stratum=CaseStratum.HOSTILE_NEAR_MISS,
        ),
        _case(
            case_id="STA-V2-002B",
            pre_state="claim K2 has an active survivor set {A1, A2, A3} on regime R1",
            claims=("K2",),
            claim_types=("mechanism",),
            regime="R1",
            evidence_roots=("assay-2", "separating-assay-2"),
            lineage=(),
            observation=(
                "a new assay is inconsistent with A3 and removes it. A separating instrument "
                "registered for A1 versus A2 was then run, and its reading is inconsistent "
                "with A2."
            ),
            escalating="every rival account anywhere is now excluded for K2",
            conservative="two assays cannot settle anything and the set stays at {A1, A2}",
            correct="only A1 survives on R1; the account is now pinned down within the registered set",
            allowed=frozenset({_M, _I}),
            disallowed={},
            status=TransitionDecision.SUPPORTED,
            edits=frozenset({StateEdit.ADD}),
            falsifier="an unregistered rival account consistent with both assays",
            stratum=CaseStratum.LEGITIMATE_UPGRADE_CONTROL,
        ),
        # ---- pair 3: shared upstream dataset vs disjoint datasets ----------
        _case(
            case_id="STA-V2-003A",
            pre_state="claim K3 rests on one registered root",
            claims=("K3",),
            claim_types=("grounding",),
            regime="R1",
            evidence_roots=("root-D1",),
            lineage=(
                ("report-a", "D1"),
                ("report-b", "D1"),
                ("report-c", "D1"),
                ("report-d", "D1"),
            ),
            observation=(
                "four further reports agreeing with K3 are registered. Tracing each one "
                "upstream, all four re-analyse the same collection D1 that the original "
                "root already used."
            ),
            escalating="K3 now rests on five separate roots and is firmly established",
            conservative="the four reports are worthless and should be discarded",
            correct="the record is better documented; the count of separate roots stays at one",
            allowed=frozenset(),
            disallowed={_G: LeakageSubtype.PROVENANCE_TO_INDEPENDENT_EVIDENCE},
            status=TransitionDecision.PARTIALLY_IDENTIFIED,
            falsifier="one of the four reports drawing on a collection other than D1",
            stratum=CaseStratum.PROVENANCE_TRAP,
        ),
        _case(
            case_id="STA-V2-003B",
            pre_state="claim K3 rests on one registered root",
            claims=("K3",),
            claim_types=("grounding",),
            regime="R1",
            evidence_roots=("root-D1",),
            lineage=(
                ("report-a", "D2"),
                ("report-b", "D3"),
                ("report-c", "D4"),
                ("report-d", "D5"),
            ),
            observation=(
                "four further reports agreeing with K3 are registered. Tracing each one "
                "upstream, all four rest on separately gathered collections that share no "
                "material or personnel with the original root."
            ),
            escalating="agreement across five roots settles the underlying account as well",
            conservative="documentation improved but the count of separate roots is unchanged",
            correct="the count of separate roots rises to five and K3's standing rises with it",
            allowed=frozenset({_G, _R}),
            disallowed={_M: LeakageSubtype.PREDICTION_TO_MECHANISM},
            status=TransitionDecision.SUPPORTED,
            edits=frozenset({StateEdit.ADD}),
            falsifier="an audit showing two of the four collections shared a source",
            stratum=CaseStratum.LEGITIMATE_UPGRADE_CONTROL,
        ),
        # ---- pair 4: track record without vs with target-regime reading ----
        _case(
            case_id="STA-V2-004A",
            pre_state="procedure P1 has completed 14 runs in regime R1 with the expected result each time",
            claims=("K4",),
            claim_types=("mechanism",),
            regime="R2",
            evidence_roots=("run-log-P1", "R2-boundary-spec"),
            lineage=(),
            observation=(
                "P1 is applied in regime R2, whose boundary conditions differ from R1. "
                "No reading has been taken in R2 itself."
            ),
            escalating="the 14 successes carry K4 into R2 and settle it there",
            conservative="P1 should not be run in R2 at all and its ranking should drop",
            correct="P1 may be preferred by the router; K4 gains no standing in R2 and cannot be assessed there",
            allowed=frozenset(),
            disallowed={
                _M: LeakageSubtype.EXPERIENCE_TO_AUTHORITY,
                _G: LeakageSubtype.EXPERIENCE_TO_AUTHORITY,
                _D: LeakageSubtype.ACCESS_ROUTING_TO_AUTHORITY,
            },
            status=TransitionDecision.CANNOT_CHECK,
            blockers=("no-R2-reading",),
            falsifier="a single reading taken in R2",
            stratum=CaseStratum.EXPERIENCE_TRAP,
        ),
        _case(
            case_id="STA-V2-004B",
            pre_state="procedure P1 has completed 14 runs in regime R1 with the expected result each time",
            claims=("K4",),
            claim_types=("mechanism",),
            regime="R2",
            evidence_roots=("run-log-P1", "reading-R2"),
            lineage=(),
            observation=(
                "P1 is applied in regime R2, whose boundary conditions differ from R1. "
                "A reading has since been taken in R2 itself and matches what K4 predicts there."
            ),
            escalating="the R2 reading plus the 14 runs settle the account behind K4 in R2",
            conservative="one R2 reading against 14 R1 runs is not enough to change anything",
            correct="the R2 reading raises K4's predictive standing in R2; the account behind it is still untested",
            allowed=frozenset({_R}),
            disallowed={_M: LeakageSubtype.PREDICTION_TO_MECHANISM},
            status=TransitionDecision.SUPPORTED,
            edits=frozenset({StateEdit.ADD}),
            falsifier="a second R2 reading disagreeing with the first",
            stratum=CaseStratum.LEGITIMATE_UPGRADE_CONTROL,
        ),
        # ---- pair 5: routes remaining vs inventory certified exhaustive ----
        _case(
            case_id="STA-V2-005A",
            pre_state="claim K5 is unresolved after 23 registered attempts",
            claims=("K5",),
            claim_types=("identification",),
            regime="R1",
            evidence_roots=("attempt-log",),
            lineage=(),
            observation=(
                "a 24th attempt also ends without a result. The registered inventory of "
                "approaches lists two families that have not yet been tried."
            ),
            escalating="K5 is out of reach; record that no approach can work",
            conservative="the 24th attempt adds nothing worth recording",
            correct="the record of unsuccessful attempts grows; the two untried families keep K5 open",
            allowed=frozenset(),
            disallowed={
                _I: LeakageSubtype.FAILURE_TO_IMPOSSIBILITY,
                _D: LeakageSubtype.FAILURE_TO_IMPOSSIBILITY,
            },
            status=TransitionDecision.PARTIALLY_IDENTIFIED,
            edits=frozenset({StateEdit.RETAIN_NEGATIVE_HISTORY}),
            falsifier="either untried family succeeding",
            stratum=CaseStratum.MULTI_STEP_HISTORY,
        ),
        _case(
            case_id="STA-V2-005B",
            pre_state="claim K5 is unresolved after 23 registered attempts",
            claims=("K5",),
            claim_types=("identification",),
            regime="R1",
            evidence_roots=("attempt-log", "covering-argument"),
            lineage=(),
            observation=(
                "a 24th attempt also ends without a result. A checked covering argument "
                "shows the registered inventory exhausts every approach of this kind, and "
                "no family remains untried."
            ),
            escalating="K5 is unreachable by any means whatsoever",
            conservative="attempts can never license a negative result, however many are made",
            correct="with the inventory exhausted, the negative result is now licensed within its stated scope",
            allowed=frozenset({_I}),
            disallowed={},
            status=TransitionDecision.SUPPORTED,
            edits=frozenset({StateEdit.ADD, StateEdit.RETAIN_NEGATIVE_HISTORY}),
            falsifier="a gap in the covering argument, or an approach outside its stated kind",
            stratum=CaseStratum.LEGITIMATE_UPGRADE_CONTROL,
        ),
        # ---- pair 6: heavily retrieved vs independently re-derived ---------
        _case(
            case_id="STA-V2-006A",
            pre_state="note N1 is registered at the lowest standing and feeds several downstream results",
            claims=("K6",),
            claim_types=("grounding",),
            regime="R1",
            evidence_roots=("note-N1", "usage-telemetry"),
            lineage=(("N1", "unsourced-memo"),),
            observation=(
                "N1 has been fetched 212 times this quarter and now sits on the critical path "
                "of four downstream results. Its upstream memo carries no source and has not "
                "been re-examined."
            ),
            escalating="N1 is clearly load-bearing and should be treated as well established",
            conservative="N1 must be dropped from the critical path immediately",
            correct="how often N1 is fetched may change how it is routed; its standing is untouched",
            allowed=frozenset(),
            disallowed={
                _G: LeakageSubtype.ACCESS_ROUTING_TO_AUTHORITY,
                _M: LeakageSubtype.ACCESS_ROUTING_TO_AUTHORITY,
                _D: LeakageSubtype.ACCESS_ROUTING_TO_AUTHORITY,
            },
            status=TransitionDecision.SUPPORTED,
            falsifier="a source being found for the upstream memo",
            stratum=CaseStratum.HOSTILE_NEAR_MISS,
        ),
        _case(
            case_id="STA-V2-006B",
            pre_state="note N1 is registered at the lowest standing and feeds several downstream results",
            claims=("K6",),
            claim_types=("grounding",),
            regime="R1",
            evidence_roots=("note-N1", "primary-S1"),
            lineage=(("N1", "primary-S1"),),
            observation=(
                "N1 has been fetched 212 times this quarter and now sits on the critical path "
                "of four downstream results. Its content has since been re-derived from a "
                "registered primary source and checked against it line by line."
            ),
            escalating="N1's re-derivation also confirms the four downstream results",
            conservative="re-derivation is bookkeeping and changes nothing about N1",
            correct="N1's standing rises because it is now traced to a primary source, not because it is fetched often",
            allowed=frozenset({_G}),
            disallowed={_D: LeakageSubtype.ACCESS_ROUTING_TO_AUTHORITY},
            status=TransitionDecision.SUPPORTED,
            edits=frozenset({StateEdit.ADD}),
            falsifier="the primary source failing to contain what N1 asserts",
            stratum=CaseStratum.LEGITIMATE_UPGRADE_CONTROL,
        ),
        # ---- pair 7: sealed check pending vs sealed check passed -----------
        _case(
            case_id="STA-V2-007A",
            pre_state="method M_new is a challenger to the registered method M_cur",
            claims=("K7",),
            claim_types=("decision_use",),
            regime="R1",
            evidence_roots=("dev-metrics", "sealed-check-registration"),
            lineage=(),
            observation=(
                "M_new scores 12 percent better than M_cur on the development split that "
                "was used to build it. The sealed held-out check registered for promotion "
                "has not been run."
            ),
            escalating="M_new is better and should replace M_cur for downstream use",
            conservative="M_new is worse than M_cur and should be discarded",
            correct="the development gain is recorded; promotion waits on the sealed check",
            allowed=frozenset(),
            disallowed={
                _D: LeakageSubtype.SELF_EVOLUTION_TO_METHOD_AUTHORITY,
                _M: LeakageSubtype.SELF_EVOLUTION_TO_METHOD_AUTHORITY,
                _R: LeakageSubtype.SELF_EVOLUTION_TO_METHOD_AUTHORITY,
            },
            status=TransitionDecision.BLOCKED,
            blockers=("sealed-check-not-run",),
            falsifier="running the sealed check",
            stratum=CaseStratum.EXPERIENCE_TRAP,
        ),
        _case(
            case_id="STA-V2-007B",
            pre_state="method M_new is a challenger to the registered method M_cur",
            claims=("K7",),
            claim_types=("decision_use",),
            regime="R1",
            evidence_roots=("dev-metrics", "sealed-check"),
            lineage=(),
            observation=(
                "M_new scores 12 percent better than M_cur on the development split that "
                "was used to build it. The sealed held-out check registered for promotion "
                "has since been run once and M_new passed it."
            ),
            escalating="M_new's win also establishes why it works and settles the account",
            conservative="a passed sealed check still cannot license using M_new",
            correct="M_new may now be used downstream and its measured standing rises; why it works is untouched",
            allowed=frozenset({_R, _D}),
            disallowed={_M: LeakageSubtype.SELF_EVOLUTION_TO_METHOD_AUTHORITY},
            status=TransitionDecision.SUPPORTED,
            edits=frozenset({StateEdit.ADD}),
            falsifier="a second sealed run that M_new fails",
            stratum=CaseStratum.LEGITIMATE_UPGRADE_CONTROL,
        ),
        # ---- pair 8: unaligned disagreement vs aligned counterexample ------
        _case(
            case_id="STA-V2-008A",
            pre_state="claim K8 is registered as holding generally, with one supporting study",
            claims=("K8",),
            claim_types=("representation",),
            regime="R5",
            evidence_roots=("study-1", "study-2"),
            lineage=(),
            observation=(
                "a second study reports the opposite of K8. It draws from a different "
                "population and reads out on a different instrument, and no map between "
                "the two readouts has been registered."
            ),
            escalating="K8 is contradicted and should be struck from the record",
            conservative="the second study is from elsewhere and can simply be ignored",
            correct="the two studies are not yet comparable; a map between the readouts is needed first",
            allowed=frozenset(),
            disallowed={
                _I: LeakageSubtype.MECHANISM_TO_IDENTIFICATION,
                _D: LeakageSubtype.ACCESS_ROUTING_TO_AUTHORITY,
            },
            status=TransitionDecision.CANNOT_CHECK,
            blockers=("no-registered-readout-map",),
            falsifier="registering a map between the two readouts",
            stratum=CaseStratum.HOSTILE_NEAR_MISS,
        ),
        _case(
            case_id="STA-V2-008B",
            pre_state="claim K8 is registered as holding generally, with one supporting study",
            claims=("K8",),
            claim_types=("representation",),
            regime="R5",
            evidence_roots=("study-1", "study-2"),
            lineage=(),
            observation=(
                "a second study reports the opposite of K8. It draws from the same "
                "population and reads out on the same registered instrument, and its "
                "single opposing case is checked and stands."
            ),
            escalating="K8 was always wrong and its earlier support should be removed too",
            conservative="one opposing case cannot outweigh a supporting study",
            correct="one checked opposing case under the same readout is enough to overturn a general claim; the earlier study stays on the record",
            allowed=frozenset({_G}),
            disallowed={},
            status=TransitionDecision.REFUTED,
            edits=frozenset({StateEdit.SUPERSEDE, StateEdit.RETAIN_NEGATIVE_HISTORY}),
            falsifier="the opposing case failing re-examination",
            stratum=CaseStratum.MULTI_STEP_HISTORY,
        ),
    )


def build_freeze_receipt_v2() -> dict[str, object]:
    """Hash-bind the V2 protocol, panel source, auditor source and visible panel.

    Separate from V1's builder because it binds different artifacts. The V1
    receipt is untouched and still valid.
    """

    from .authority_leakage_benchmark import CLAIM_BOUNDARY, panel_visible_sha256

    repo_root = Path(__file__).resolve().parents[2]
    protocol_path = (
        repo_root / "benchmarks" / "scientific_transition_authority" / "PROTOCOL_V2.md"
    )
    panel = frozen_case_panel_v2()

    receipt: dict[str, object] = {
        "protocol_id": PANEL_V2_ID,
        "issue": 154,
        "status": "FROZEN_PROTOCOL / PROPOSAL_ONLY / NO_MODEL_EVALUATION",
        "claim_boundary": CLAIM_BOUNDARY,
        "protocol_path": "benchmarks/scientific_transition_authority/PROTOCOL_V2.md",
        "protocol_sha256": _sha256_file(protocol_path),
        "panel_source_sha256": _sha256_file(Path(__file__).resolve()),
        "auditor_source_sha256": _sha256_file(
            Path(__file__).resolve().with_name("authority_leakage_audit.py")
        ),
        "scorer_source_sha256": _sha256_file(
            Path(__file__).resolve().with_name("authority_leakage_benchmark.py")
        ),
        "panel_visible_sha256": panel_visible_sha256(panel),
        "case_count": len(panel),
        "twin_pair_count": TWIN_PAIRS,
        "cases_licensing_an_upgrade": sum(
            1 for case in panel if case.labels.allowed_authority_effects
        ),
        "total_allowed_axes": sum(
            len(case.labels.allowed_authority_effects) for case in panel
        ),
        "leakage_subtype_count": len(
            {s for case in panel for s in case.labels.disallowed_authority_effects.values()}
        ),
        "audit_thresholds_frozen_at": AUDIT_THRESHOLDS_FROZEN_AT,
        "degeneracy_audit_status": audit_panel(panel, PANEL_V2_ID).status.value,
        "supersedes_panel": "scientific-transition-authority-v1",
        "v1_preserved_verbatim": True,
        "grants_authority": False,
    }
    blob = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
    receipt["artifact_hash"] = hashlib.sha256(blob).hexdigest()
    return receipt


def twin_pairs() -> Tuple[Tuple[ScientificTransitionCase, ScientificTransitionCase], ...]:
    """Group the panel into its ``(A, B)`` twins."""

    by_id = {case.case_id: case for case in frozen_case_panel_v2()}
    return tuple(
        (by_id[f"STA-V2-{n:03d}A"], by_id[f"STA-V2-{n:03d}B"]) for n in range(1, 9)
    )


#: Number of twin pairs; the panel is twice this.
TWIN_PAIRS = 8
