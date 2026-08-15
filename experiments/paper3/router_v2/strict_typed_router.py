#!/usr/bin/env python3
"""The candidate arm: the strict typed router, plus its registered mutations.

SEVERANCE CONTRACT
------------------
This module imports nothing from the case generator and never sees gold. Its
only input is the projected ``candidate_view`` record. The names ``gold_route``,
``gold_trace``, ``family``, ``pair_index`` and ``case_id`` do not appear here;
``experiments/paper3/router_v2/run_router_v2_reconstruction.py`` proves that by
AST scan before executing anything.

Semantics follow the production route-resolver stack contracts:
``research/paper3_route_resolver_v1/PROTOCOL.json`` (SEARCH -> JUMP -> GLUE ->
LIFT priority; an unresolved earlier structural candidate forces CANNOT_CHECK
rather than bypass), ``research/paper3_typed_rejection_production_v1`` and
``research/paper3_glue_rejection_production_v1/PROTOCOL.json`` (conclusive,
content-bound rejection certificates are the only thing that may clear a failed
earlier candidate; missing, ambiguous or non-conclusive evidence stays
CANNOT_CHECK; every certified rejection is retained in the returned trace).
"""

from __future__ import annotations

from typing import Any, Mapping

STAGES = ("search", "jump", "glue")
CANNOT_CHECK = "CANNOT_CHECK"
CONCRETE_ROUTES = ("SEARCH", "JUMP", "GLUE", "LIFT")

#: The twelve mutations registered in PROTOCOL_FREEZE.json.
REGISTERED_MUTATIONS = (
    "IGNORE_MAPPING",
    "IGNORE_PRECONDITIONS",
    "IGNORE_FORBIDDEN_LOSS",
    "PARTIAL_COUNTS_AS_COMPLETE",
    "ONE_FAILURE_LIFT",
    "IGNORE_COVERAGE",
    "IGNORE_ACCOUNTING",
    "FAIL_WITHOUT_TYPED_REJECTION",
    "CANNOT_CHECK_AS_REJECTED",
    "IGNORE_REJECTION_REVISION",
    "IGNORE_REJECTION_TARGET",
    "DROP_NEGATIVE_HISTORY",
)

#: Audit-only mutants, not part of the frozen twelve. They exist to separate the
#: four strict gate conditions from one another, which the registered mutations
#: cannot do (a blunt mutant breaks several conditions at once and so proves
#: nothing per-condition).
AUDIT_MUTANTS = (
    "AUDIT_DOWNGRADE_VIABLE_ROUTES",  # fail-closed direction: viable route -> CANNOT_CHECK
    "AUDIT_SWAP_SEARCH_FOR_JUMP",  # wrong concrete route, never touches CANNOT_CHECK cases
)

ALL_MUTANTS = REGISTERED_MUTATIONS + AUDIT_MUTANTS

_ACCEPT, _BLOCK, _CLEAR, _CERT_CLEAR = "ACCEPT", "BLOCK", "CLEAR", "CERT_CLEAR"


def _accept_extras(r: Mapping[str, Any], s: str, m: str | None) -> bool:
    if not r[f"{s}_witness_present"]:
        return False
    if not (r[f"{s}_preconditions_repaired"] or m == "IGNORE_PRECONDITIONS"):
        return False
    if s == "jump":
        if not (r["jump_mapping_valid"] or m == "IGNORE_MAPPING"):
            return False
        if not (r["jump_effect_complete"] or m == "PARTIAL_COUNTS_AS_COMPLETE"):
            return False
    if s == "glue":
        if not (r["glue_complementary"] or m == "PARTIAL_COUNTS_AS_COMPLETE"):
            return False
        if not (r["glue_candidates_accounted"] or m == "IGNORE_ACCOUNTING"):
            return False
    return True


def _stage_status(r: Mapping[str, Any], s: str, m: str | None) -> str:
    if not r[f"{s}_candidate_present"]:
        return _CLEAR
    audit = r[f"{s}_audit"]
    if audit == "PASS" and _accept_extras(r, s, m):
        return _ACCEPT
    if audit == "CANNOT_CHECK":
        # Inconclusive evidence is not a rejection. Clearing it is the whole
        # point of the CANNOT_CHECK_AS_REJECTED mutation.
        return _CERT_CLEAR if m == "CANNOT_CHECK_AS_REJECTED" else _BLOCK
    if audit == "FAIL":
        if m == "FAIL_WITHOUT_TYPED_REJECTION":
            return _CERT_CLEAR
        binds_revision = r[f"{s}_rejection_binds_revision"] or m == "IGNORE_REJECTION_REVISION"
        binds_target = (
            r[f"{s}_rejection_binds_target_context"] or m == "IGNORE_REJECTION_TARGET"
        )
        if (
            r[f"{s}_rejection_certificate"]
            and r[f"{s}_rejection_conclusive"]
            and binds_revision
            and binds_target
        ):
            return _CERT_CLEAR
        return _BLOCK
    # audit == "PASS" but the stage-specific acceptance conditions failed.
    return _BLOCK


def _lift_permitted(r: Mapping[str, Any], m: str | None) -> bool:
    if not r["exhaustion_witness_present"]:
        return False
    if not (r["exhaustion_accounts_all_candidates"] or m == "IGNORE_ACCOUNTING"):
        return False
    if not r["missing_transformation_spec_present"]:
        return False
    if not (r["cross_problem_coverage_sufficient"] or m == "IGNORE_COVERAGE"):
        return False
    required_residual = 1 if m == "ONE_FAILURE_LIFT" else 2
    return int(r["repeated_residual_count"]) >= required_residual


def strict_route(
    record: Mapping[str, Any], mutation: str | None = None
) -> tuple[str, tuple[str, ...]]:
    """Return ``(route, negative_trace)`` for one projected route-state record."""
    m = mutation
    if record["forbidden_loss"] and m != "IGNORE_FORBIDDEN_LOSS":
        return CANNOT_CHECK, ()
    if record["proposal_only"]:
        return CANNOT_CHECK, ()

    trace: list[str] = []
    for stage in STAGES:
        status = _stage_status(record, stage, m)
        if status == _ACCEPT:
            route = stage.upper()
            break
        if status == _BLOCK:
            return CANNOT_CHECK, ()
        if status == _CERT_CLEAR:
            if m != "DROP_NEGATIVE_HISTORY" and not record["negative_history_retained"]:
                return CANNOT_CHECK, ()
            trace.append(stage)
    else:
        if not _lift_permitted(record, m):
            return CANNOT_CHECK, ()
        route = "LIFT"

    if m == "DROP_NEGATIVE_HISTORY":
        return route, ()
    if m == "AUDIT_SWAP_SEARCH_FOR_JUMP" and route == "SEARCH":
        return "JUMP", tuple(trace)
    if m == "AUDIT_DOWNGRADE_VIABLE_ROUTES" and route in CONCRETE_ROUTES:
        return CANNOT_CHECK, ()
    return route, tuple(trace)
