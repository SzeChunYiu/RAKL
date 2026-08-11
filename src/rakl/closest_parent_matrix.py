"""Validator for the Paper-II closest-parent ablation matrix (issue #156).

The matrix exists to stop Paper II earning novelty against weak or
function-mismatched baselines. A prose table cannot enforce that; this module
can. It loads ``research/PAPER2_CLOSEST_PARENT_ABLATION_MATRIX.json`` and
refuses it when a novelty claim outruns its evidence.

Rules, in the order they matter:

1. **A residual claim requires primary full text.** A row may only say
   ``NARROW_RESIDUAL`` when the parent it is measured against was read in full
   text. Conceding a function to prior art is cheap and needs no deep read;
   claiming something survives comparison is expensive and does. Rows whose
   closest parent was read at abstract level report ``CANNOT_CHECK``.
2. **Every residual claim carries a falsifier and a discriminator.** What
   finding would collapse this row into prior art, and what experiment
   separates them.
3. **No arm is named after an external system.** An ablation arm may
   approximate a parent's *function*; it is never that system, and every arm
   that approximates one must state what the real system does that it does not.
4. **No results.** Nothing has been run.

The validator grants no authority and adjudicates no novelty. It only checks
that claims do not exceed the evidence recorded beside them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence, Tuple

__all__ = [
    "MATRIX_PATH",
    "EXTERNAL_SYSTEM_NAMES",
    "FULL_TEXT_LEVELS",
    "MatrixViolation",
    "MatrixReport",
    "load_matrix",
    "validate_matrix",
]

MATRIX_PATH = (
    Path(__file__).resolve().parents[2]
    / "research"
    / "PAPER2_CLOSEST_PARENT_ABLATION_MATRIX.json"
)

#: Evidence levels that permit a residual claim.
FULL_TEXT_LEVELS = frozenset({"FULL_TEXT", "FULL_TEXT_PARTIAL"})

VALID_EVIDENCE_LEVELS = FULL_TEXT_LEVELS | {
    "ABSTRACT_AND_REPO",
    "ABSTRACT_ONLY",
    "CANNOT_CHECK",
}

VALID_CLAIMS = frozenset(
    {"INHERITED_NO_CLAIM", "NARROW_RESIDUAL", "PARENT_STRONGER_ADOPT", "CANNOT_CHECK"}
)

VALID_SAME_FUNCTION = frozenset({"yes", "partial", "no"})

VALID_FEASIBILITY = frozenset(
    {
        "EXACT_REPRODUCTION_FEASIBLE",
        "FUNCTION_MATCHED_ABLATION_FEASIBLE",
        "BLACK_BOX_PUBLIC_SYSTEM_FEASIBLE",
        "CONCEPTUAL_COMPARISON_ONLY",
        "CANNOT_COMPARE_FAIRLY",
    }
)

#: An ablation arm must never carry one of these names.
EXTERNAL_SYSTEM_NAMES: Tuple[str, ...] = (
    "AUTOSCI",
    "MEMTX",
    "PPMF",
    "MEMCLAW",
    "SCIMEM",
    "SCIFLOW",
    "SCIDAG",
    "SCIEVOLVE",
    "ARGUSFLEET",
)

#: Functions the issue requires the matrix to cover.
REQUIRED_FUNCTIONS: Tuple[str, ...] = (
    "persistent task/project memory",
    "cross-project long-term knowledge",
    "TaskEpisode / raw trajectory preservation",
    "versioned lesson/procedure abstraction",
    "skill / DAG / workflow reuse",
    "experience-conditioned routing",
    "transactional commit",
    "provenance retention",
    "source / use permission",
    "staleness / supersession",
    "cascade repair",
    "contradiction preservation",
    "negative-history preservation",
    "context-scoped scientific claims",
    "prediction vs mechanism authority",
    "mechanism vs identification authority",
    "partial-identification terminal state",
    "proposal-only workspace",
    "experience -> authority noninterference",
    "scientific transition audit",
    "open-world discovery routes",
    "bounded / freshness-expiring saturation",
    "fresh-assurance self-evolution",
)

_RESULT_WORDS = ("outperform", "beats", "improves over", "wins", "we observe that rakl")


@dataclass(frozen=True)
class MatrixViolation:
    rule: str
    where: str
    detail: str

    def __str__(self) -> str:  # pragma: no cover - formatting only
        return f"[{self.rule}] {self.where}: {self.detail}"


@dataclass(frozen=True)
class MatrixReport:
    violations: Tuple[MatrixViolation, ...]
    n_functions: int
    claim_counts: Mapping[str, int]

    @property
    def ok(self) -> bool:
        return not self.violations

    @property
    def grants_authority(self) -> bool:
        return False


def load_matrix(path: Path | None = None) -> Mapping[str, object]:
    return json.loads((path or MATRIX_PATH).read_text(encoding="utf-8"))


def validate_matrix(matrix: Mapping[str, object] | None = None) -> MatrixReport:
    """Check every claim against the evidence recorded beside it."""

    data = matrix if matrix is not None else load_matrix()
    violations: list[MatrixViolation] = []

    parents = {str(p["id"]): p for p in data.get("parents", [])}  # type: ignore[index]
    functions: Sequence[Mapping[str, object]] = data.get("functions", [])  # type: ignore[assignment]

    if not parents:
        violations.append(MatrixViolation("parents_present", "<root>", "no parents recorded"))
    if not functions:
        violations.append(MatrixViolation("functions_present", "<root>", "no function rows"))

    # ---- parents -------------------------------------------------------
    for pid, parent in parents.items():
        level = parent.get("evidence_level")
        if level not in VALID_EVIDENCE_LEVELS:
            violations.append(
                MatrixViolation("evidence_level_valid", f"parent:{pid}", f"bad level {level!r}")
            )
        if not parent.get("sources_read"):
            violations.append(
                MatrixViolation("sources_recorded", f"parent:{pid}", "no sources_read listed")
            )
        feasibility = parent.get("feasibility")
        if feasibility not in VALID_FEASIBILITY:
            violations.append(
                MatrixViolation(
                    "feasibility_classified", f"parent:{pid}", f"bad feasibility {feasibility!r}"
                )
            )
        if feasibility in {
            "FUNCTION_MATCHED_ABLATION_FEASIBLE",
            "BLACK_BOX_PUBLIC_SYSTEM_FEASIBLE",
        } and not parent.get("feasibility_note"):
            violations.append(
                MatrixViolation(
                    "feasibility_justified",
                    f"parent:{pid}",
                    "a feasible classification needs a note saying what is and is not reproducible",
                )
            )

    # ---- required coverage ---------------------------------------------
    named = {str(row.get("function")) for row in functions}
    for required in REQUIRED_FUNCTIONS:
        if required not in named:
            violations.append(
                MatrixViolation("required_coverage", f"function:{required}", "row missing")
            )

    # ---- function rows -------------------------------------------------
    claim_counts: dict[str, int] = {}
    for row in functions:
        where = f"function:{row.get('function')}"
        claim = str(row.get("claim_allowed_today"))
        claim_counts[claim] = claim_counts.get(claim, 0) + 1

        if claim not in VALID_CLAIMS:
            violations.append(MatrixViolation("claim_valid", where, f"bad claim {claim!r}"))
        if row.get("same_function") not in VALID_SAME_FUNCTION:
            violations.append(
                MatrixViolation(
                    "same_function_valid", where, f"bad value {row.get('same_function')!r}"
                )
            )
        if not row.get("rakl_implementation"):
            violations.append(
                MatrixViolation("rakl_pointer", where, "no RAKL implementation recorded")
            )

        parent_id = str(row.get("closest_parent"))
        if parent_id not in parents:
            violations.append(
                MatrixViolation("parent_known", where, f"unknown parent {parent_id!r}")
            )
            continue

        level = str(row.get("evidence_level"))
        if level not in VALID_EVIDENCE_LEVELS:
            violations.append(
                MatrixViolation("evidence_level_valid", where, f"bad level {level!r}")
            )
        if level != parents[parent_id].get("evidence_level"):
            violations.append(
                MatrixViolation(
                    "evidence_level_consistent",
                    where,
                    f"row says {level!r} but parent {parent_id} says "
                    f"{parents[parent_id].get('evidence_level')!r}",
                )
            )

        if claim == "NARROW_RESIDUAL":
            # Rule 1: a residual claim requires primary full text.
            if level not in FULL_TEXT_LEVELS:
                violations.append(
                    MatrixViolation(
                        "residual_needs_full_text",
                        where,
                        f"claims a residual against {parent_id}, read only at {level}",
                    )
                )
            # Rule 2: falsifier and discriminator are mandatory.
            if not str(row.get("falsifier", "")).strip():
                violations.append(
                    MatrixViolation("residual_needs_falsifier", where, "no falsifier recorded")
                )
            if not str(row.get("required_discriminator", "")).strip():
                violations.append(
                    MatrixViolation(
                        "residual_needs_discriminator", where, "no discriminator recorded"
                    )
                )
            if not str(row.get("rakl_residual", "")).strip():
                violations.append(
                    MatrixViolation("residual_stated", where, "no residual stated")
                )

        if claim == "CANNOT_CHECK" and not str(row.get("required_discriminator", "")).strip():
            violations.append(
                MatrixViolation(
                    "cannot_check_needs_next_step",
                    where,
                    "a CANNOT_CHECK row must say what reading would resolve it",
                )
            )

    # ---- ladder --------------------------------------------------------
    for arm in data.get("ladder", []):  # type: ignore[union-attr]
        name = str(arm.get("arm", ""))
        where = f"arm:{name}"
        upper = name.upper()
        for system in EXTERNAL_SYSTEM_NAMES:
            if system in upper:
                violations.append(
                    MatrixViolation(
                        "arm_not_named_after_system",
                        where,
                        f"arm name contains {system!r}; an ablation is never the external system",
                    )
                )
        approximates = str(arm.get("approximates_parent_function", ""))
        claims_a_parent = bool(approximates) and not approximates.startswith(
            ("none", "unresolved")
        )
        if claims_a_parent and not str(arm.get("not_the_system", "")).strip():
            violations.append(
                MatrixViolation(
                    "arm_states_the_gap",
                    where,
                    "an arm approximating a parent must state what the real system does that it does not",
                )
            )

    # ---- intervention contracts ----------------------------------------
    required_contract_fields = (
        "code_path_changed",
        "information_still_available",
        "update_permissions_changed",
        "state_fields_retained",
        "evaluator_sees",
        "expected_mechanism",
        "falsifier",
    )
    for contract in data.get("intervention_contracts", []):  # type: ignore[union-attr]
        where = f"contract:{contract.get('pair')}"
        for field in required_contract_fields:
            if not str(contract.get(field, "")).strip():
                violations.append(
                    MatrixViolation("contract_complete", where, f"missing {field}")
                )

    # ---- no results ----------------------------------------------------
    blob = json.dumps(data).lower()
    for word in _RESULT_WORDS:
        if word in blob:
            violations.append(
                MatrixViolation(
                    "no_results_claimed",
                    "<root>",
                    f"result-like language {word!r}; no ablation has been run",
                )
            )
    if data.get("grants_scientific_authority") is not False:
        violations.append(
            MatrixViolation("no_authority", "<root>", "grants_scientific_authority must be false")
        )

    return MatrixReport(
        violations=tuple(violations),
        n_functions=len(functions),
        claim_counts=dict(sorted(claim_counts.items())),
    )
