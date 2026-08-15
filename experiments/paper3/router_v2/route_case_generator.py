#!/usr/bin/env python3
"""Case generator for the frozen 21-family / 2,688-case router protocol.

Protocol: ``research/paper3_publication_validation_v2/PROTOCOL_FREEZE.json``.

SEVERANCE CONTRACT
------------------
This module owns **gold**. Gold is committed at construction time, from the
family's design intent, and is *never* recomputed from the record by any
routing rule. This module must not import, reference or reimplement the
candidate router.

The candidate never sees gold: :func:`candidate_view` projects a case down to
``CANDIDATE_VISIBLE_FIELDS``, which excludes ``gold_route``, ``gold_trace``,
``family``, ``pair_index`` and ``case_id``. Leakage is therefore structurally
impossible, not merely audited.

Why intent-gold and not an independent declarative oracle: an independently
written reimplementation of the routing rule is still the *same function*, so
route accuracy would hold 1.0 under every perturbation of the record --- exactly
the P3_TYPED_ARM_SELF_IDENTITY defect this rebuild exists to avoid. Intent-gold
is a different information source, so perturbing the record moves the metric.
"""

from __future__ import annotations

import random
from typing import Any, Mapping

SEED = 202608140502
PAIRS_PER_FAMILY = 64

STAGES = ("search", "jump", "glue")
AUDIT_VALUES = ("NONE", "PASS", "FAIL", "CANNOT_CHECK")

#: Every field the candidate router is allowed to see. Nothing else is passed.
CANDIDATE_VISIBLE_FIELDS: tuple[str, ...] = tuple(
    [
        f"{s}_{suffix}"
        for s in STAGES
        for suffix in (
            "candidate_present",
            "audit",
            "witness_present",
            "preconditions_repaired",
            "rejection_certificate",
            "rejection_conclusive",
            "rejection_binds_revision",
            "rejection_binds_target_context",
        )
    ]
    + [
        "jump_mapping_valid",
        "jump_effect_complete",
        "glue_complementary",
        "glue_candidates_accounted",
        "exhaustion_witness_present",
        "exhaustion_accounts_all_candidates",
        "missing_transformation_spec_present",
        "cross_problem_coverage_sufficient",
        "repeated_residual_count",
        "forbidden_loss",
        "proposal_only",
        "negative_history_retained",
        "semantic_similarity",
        "domain_match",
        "candidate_count",
    ]
)

#: Fields the generator draws at random and no rule reads. Declared so that an
#: INSENSITIVE probe outcome on them is the correct result, not a defect.
NUISANCE_FIELDS = ("semantic_similarity", "domain_match", "candidate_count")

BASE: dict[str, Any] = {}
for _s in STAGES:
    BASE.update(
        {
            f"{_s}_candidate_present": False,
            f"{_s}_audit": "NONE",
            f"{_s}_witness_present": False,
            f"{_s}_preconditions_repaired": True,
            f"{_s}_rejection_certificate": False,
            f"{_s}_rejection_conclusive": False,
            f"{_s}_rejection_binds_revision": False,
            f"{_s}_rejection_binds_target_context": False,
        }
    )
BASE.update(
    {
        "jump_mapping_valid": False,
        "jump_effect_complete": False,
        "glue_complementary": False,
        "glue_candidates_accounted": True,
        "exhaustion_witness_present": False,
        "exhaustion_accounts_all_candidates": False,
        "missing_transformation_spec_present": False,
        "cross_problem_coverage_sufficient": False,
        "repeated_residual_count": 0,
        "forbidden_loss": False,
        "proposal_only": False,
        "negative_history_retained": True,
        "semantic_similarity": 0.0,
        "domain_match": False,
        "candidate_count": 0,
    }
)


# --- construction helpers ---------------------------------------------------


def _accept(s: str) -> dict[str, Any]:
    """Stage ``s`` carries a candidate whose artifacts pass the canonical audit."""
    out = {
        f"{s}_candidate_present": True,
        f"{s}_audit": "PASS",
        f"{s}_witness_present": True,
        f"{s}_preconditions_repaired": True,
    }
    if s == "jump":
        out.update({"jump_mapping_valid": True, "jump_effect_complete": True})
    if s == "glue":
        out.update({"glue_complementary": True, "glue_candidates_accounted": True})
    return out


def _uncertain(s: str) -> dict[str, Any]:
    """Candidate present, canonical audit inconclusive."""
    return {f"{s}_candidate_present": True, f"{s}_audit": "CANNOT_CHECK", f"{s}_witness_present": True}


def _certified_rejected(s: str, **flaw: bool) -> dict[str, Any]:
    """Candidate present, conclusive content-bound typed rejection certificate."""
    out = {
        f"{s}_candidate_present": True,
        f"{s}_audit": "FAIL",
        f"{s}_witness_present": True,
        f"{s}_rejection_certificate": True,
        f"{s}_rejection_conclusive": True,
        f"{s}_rejection_binds_revision": True,
        f"{s}_rejection_binds_target_context": True,
    }
    for key, value in flaw.items():
        out[f"{s}_{key}"] = value
    return out


def _lift_ready(residual: int = 3) -> dict[str, Any]:
    return {
        "exhaustion_witness_present": True,
        "exhaustion_accounts_all_candidates": True,
        "missing_transformation_spec_present": True,
        "cross_problem_coverage_sufficient": True,
        "repeated_residual_count": residual,
    }


def _merge(*parts: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for part in parts:
        out.update(part)
    return out


# --- the 21 registered families --------------------------------------------
#
# Each family is a matched twin pair differing in exactly one decision-critical
# coordinate, with distinct committed gold. ``decides_at`` fixes the routing
# stage at which both twins terminate; every coordinate strictly downstream of
# that stage is declared free and is redrawn per pair, so the 64 pairs are not
# 64 copies. ``exercises`` names the registered mutation(s) the family is
# designed to make load-bearing (the v1 instrument's recorded terminal was
# INSTRUMENT_DEFECT_TWO_MUTATIONS_NOT_EXERCISED).

FAMILIES: dict[str, dict[str, Any]] = {
    "DIRECT_SEARCH_VALID": {
        "decides_at": "search",
        "a": (_accept("search"), "SEARCH", ()),
        "b": (_uncertain("search"), "CANNOT_CHECK", ()),
        "exercises": [],
    },
    "CROSS_DOMAIN_JUMP_VALID": {
        "decides_at": "jump",
        "a": (_accept("jump"), "JUMP", ()),
        "b": (_merge(_accept("jump"), {"jump_witness_present": False}), "CANNOT_CHECK", ()),
        "exercises": [],
    },
    "SEMANTIC_NEAR_MISS_MAPPING_INVALID": {
        "decides_at": "jump",
        "a": (_merge(_accept("jump"), {"jump_mapping_valid": False}), "CANNOT_CHECK", ()),
        "b": (_accept("jump"), "JUMP", ()),
        "exercises": ["IGNORE_MAPPING"],
    },
    "PARTIAL_NEEDS_GLUE": {
        "decides_at": "glue",
        "a": (_accept("glue"), "GLUE", ()),
        # the unresolved partial JUMP twin: promoted only by PARTIAL_COUNTS_AS_COMPLETE
        "b": (
            _merge(_accept("jump"), {"jump_effect_complete": False}),
            "CANNOT_CHECK",
            (),
        ),
        "exercises": ["PARTIAL_COUNTS_AS_COMPLETE"],
    },
    "GLUE_INCOMPATIBLE": {
        "decides_at": "glue",
        "a": (_merge(_accept("glue"), {"glue_complementary": False}), "CANNOT_CHECK", ()),
        "b": (_accept("glue"), "GLUE", ()),
        "exercises": ["PARTIAL_COUNTS_AS_COMPLETE"],
    },
    "FORBIDDEN_LOSS": {
        "decides_at": "search",
        "a": (_merge(_accept("search"), {"forbidden_loss": True}), "CANNOT_CHECK", ()),
        "b": (_accept("search"), "SEARCH", ()),
        "exercises": ["IGNORE_FORBIDDEN_LOSS"],
    },
    "PRECONDITION_MISMATCH": {
        "decides_at": "jump",
        "a": (_merge(_accept("jump"), {"jump_preconditions_repaired": False}), "CANNOT_CHECK", ()),
        "b": (_accept("jump"), "JUMP", ()),
        "exercises": ["IGNORE_PRECONDITIONS"],
    },
    "BOUNDED_EXHAUSTION_LIFT": {
        "decides_at": "lift",
        "a": (_lift_ready(), "LIFT", ()),
        "b": (
            _merge(_lift_ready(), {"missing_transformation_spec_present": False}),
            "CANNOT_CHECK",
            (),
        ),
        "exercises": [],
    },
    "INSUFFICIENT_COVERAGE": {
        "decides_at": "lift",
        "a": (
            _merge(_lift_ready(), {"cross_problem_coverage_sufficient": False}),
            "CANNOT_CHECK",
            (),
        ),
        "b": (_lift_ready(), "LIFT", ()),
        "exercises": ["IGNORE_COVERAGE"],
    },
    "REPEATED_RESIDUAL_LIFT": {
        "decides_at": "lift",
        "a": (_lift_ready(residual=3), "LIFT", ()),
        "b": (_lift_ready(residual=1), "CANNOT_CHECK", ()),
        "exercises": ["ONE_FAILURE_LIFT"],
    },
    "SINGLE_FAILURE_NO_LIFT": {
        "decides_at": "lift",
        "a": (_lift_ready(residual=1), "CANNOT_CHECK", ()),
        "b": (_lift_ready(residual=2), "LIFT", ()),
        "exercises": ["ONE_FAILURE_LIFT"],
    },
    "UNACCOUNTED_CANDIDATE": {
        "decides_at": "lift",
        "a": (
            _merge(_lift_ready(), {"exhaustion_accounts_all_candidates": False}),
            "CANNOT_CHECK",
            (),
        ),
        "b": (_lift_ready(), "LIFT", ()),
        "exercises": ["IGNORE_ACCOUNTING"],
    },
    "NEGATIVE_HISTORY_REQUIRED": {
        "decides_at": "jump",
        "a": (
            _merge(_certified_rejected("search"), _accept("jump")),
            "JUMP",
            ("search",),
        ),
        "b": (
            _merge(
                _certified_rejected("search"),
                _accept("jump"),
                {"negative_history_retained": False},
            ),
            "CANNOT_CHECK",
            (),
        ),
        "exercises": ["DROP_NEGATIVE_HISTORY"],
    },
    "PROPOSAL_ONLY_NOT_AUTHORITY": {
        "decides_at": "search",
        "a": (_merge(_accept("search"), {"proposal_only": True}), "CANNOT_CHECK", ()),
        "b": (_accept("search"), "SEARCH", ()),
        "exercises": [],
    },
    "REJECTED_SEARCH_JUMP_VALID": {
        "decides_at": "jump",
        "a": (_merge(_certified_rejected("search"), _accept("jump")), "JUMP", ("search",)),
        "b": (
            _merge(
                _certified_rejected("search", rejection_certificate=False),
                _accept("jump"),
            ),
            "CANNOT_CHECK",
            (),
        ),
        "exercises": ["FAIL_WITHOUT_TYPED_REJECTION"],
    },
    "REJECTED_JUMP_GLUE_VALID": {
        "decides_at": "glue",
        "a": (_merge(_certified_rejected("jump"), _accept("glue")), "GLUE", ("jump",)),
        "b": (
            _merge(
                _certified_rejected("jump", rejection_conclusive=False),
                _accept("glue"),
            ),
            "CANNOT_CHECK",
            (),
        ),
        "exercises": ["FAIL_WITHOUT_TYPED_REJECTION"],
    },
    "UNCERTAIN_SEARCH_BLOCKS_JUMP": {
        "decides_at": "jump",
        "a": (_merge(_uncertain("search"), _accept("jump")), "CANNOT_CHECK", ()),
        "b": (_accept("jump"), "JUMP", ()),
        "exercises": ["CANNOT_CHECK_AS_REJECTED"],
    },
    "STALE_REJECTION_BLOCKS_FALLTHROUGH": {
        "decides_at": "jump",
        "a": (
            _merge(_certified_rejected("search", rejection_binds_revision=False), _accept("jump")),
            "CANNOT_CHECK",
            (),
        ),
        "b": (_merge(_certified_rejected("search"), _accept("jump")), "JUMP", ("search",)),
        "exercises": ["IGNORE_REJECTION_REVISION"],
    },
    "WRONG_TARGET_REJECTION_BLOCKS": {
        "decides_at": "jump",
        "a": (
            _merge(
                _certified_rejected("search", rejection_binds_target_context=False),
                _accept("jump"),
            ),
            "CANNOT_CHECK",
            (),
        ),
        "b": (_merge(_certified_rejected("search"), _accept("jump")), "JUMP", ("search",)),
        "exercises": ["IGNORE_REJECTION_TARGET"],
    },
    "CURRENT_PASS_OVERRIDES_OLD_REJECTION": {
        "decides_at": "search",
        # the current audit passes; a stale certificate must not demote it
        "a": (
            _merge(
                _accept("search"),
                {
                    "search_rejection_certificate": True,
                    "search_rejection_conclusive": True,
                    "search_rejection_binds_revision": False,
                    "search_rejection_binds_target_context": True,
                },
            ),
            "SEARCH",
            (),
        ),
        "b": (_merge(_certified_rejected("search"), _accept("jump")), "JUMP", ("search",)),
        "exercises": [],
    },
    "ALL_STRUCTURAL_REJECTED_LIFT": {
        "decides_at": "lift",
        "a": (
            _merge(
                _certified_rejected("search"),
                _certified_rejected("jump"),
                _certified_rejected("glue"),
                _lift_ready(),
            ),
            "LIFT",
            ("search", "jump", "glue"),
        ),
        "b": (
            _merge(
                _certified_rejected("search"),
                _certified_rejected("jump"),
                _uncertain("glue"),
                _lift_ready(),
            ),
            "CANNOT_CHECK",
            (),
        ),
        "exercises": ["CANNOT_CHECK_AS_REJECTED", "IGNORE_ACCOUNTING"],
    },
}

#: Coordinates strictly downstream of the deciding stage, i.e. provably
#: irrelevant to the committed gold and therefore redrawn per pair.
_DOWNSTREAM: dict[str, tuple[str, ...]] = {
    "search": ("jump", "glue", "lift"),
    "jump": ("glue", "lift"),
    "glue": ("lift",),
    "lift": (),
}


def _random_stage_block(rng: random.Random, s: str) -> dict[str, Any]:
    present = rng.random() < 0.5
    if not present:
        block = {k: BASE[k] for k in BASE if k.startswith(f"{s}_")}
        return block
    audit = rng.choice(("PASS", "FAIL", "CANNOT_CHECK"))
    block: dict[str, Any] = {
        f"{s}_candidate_present": True,
        f"{s}_audit": audit,
        f"{s}_witness_present": rng.random() < 0.5,
        f"{s}_preconditions_repaired": rng.random() < 0.5,
        f"{s}_rejection_certificate": rng.random() < 0.5,
        f"{s}_rejection_conclusive": rng.random() < 0.5,
        f"{s}_rejection_binds_revision": rng.random() < 0.5,
        f"{s}_rejection_binds_target_context": rng.random() < 0.5,
    }
    if s == "jump":
        block["jump_mapping_valid"] = rng.random() < 0.5
        block["jump_effect_complete"] = rng.random() < 0.5
    if s == "glue":
        block["glue_complementary"] = rng.random() < 0.5
        block["glue_candidates_accounted"] = rng.random() < 0.5
    return block


def _random_lift_block(rng: random.Random) -> dict[str, Any]:
    return {
        "exhaustion_witness_present": rng.random() < 0.5,
        "exhaustion_accounts_all_candidates": rng.random() < 0.5,
        "missing_transformation_spec_present": rng.random() < 0.5,
        "cross_problem_coverage_sufficient": rng.random() < 0.5,
        "repeated_residual_count": rng.randrange(0, 4),
    }


def _nuisance(rng: random.Random) -> dict[str, Any]:
    return {
        "semantic_similarity": round(rng.random(), 3),
        "domain_match": rng.random() < 0.5,
        "candidate_count": rng.randrange(0, 5),
    }


def make_pair(family: str, rng: random.Random, index: int) -> list[dict[str, Any]]:
    """Build one matched twin pair for ``family``. Gold is committed here."""
    spec = FAMILIES[family]
    downstream = _DOWNSTREAM[spec["decides_at"]]
    free: dict[str, Any] = {}
    for zone in downstream:
        free.update(
            _random_lift_block(rng) if zone == "lift" else _random_stage_block(rng, zone)
        )
    cases: list[dict[str, Any]] = []
    for side in ("a", "b"):
        overrides, gold_route, gold_trace = spec[side]
        record = _merge(BASE, free, _nuisance(rng), overrides)
        record.update(
            {
                "case_id": f"{family}:{index}:{side}",
                "family": family,
                "pair_index": index,
                "side": side,
                "gold_route": gold_route,
                "gold_trace": list(gold_trace),
                "gold_source": "GENERATOR_DESIGN_INTENT",
            }
        )
        cases.append(record)
    return cases


def build_cases(seed: int = SEED, pairs_per_family: int = PAIRS_PER_FAMILY) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    cases: list[dict[str, Any]] = []
    for family in FAMILIES:
        for index in range(pairs_per_family):
            cases.extend(make_pair(family, rng, index))
    return cases


def candidate_view(case: Mapping[str, Any]) -> dict[str, Any]:
    """The only projection the candidate router is ever handed.

    Gold, family and case identity are structurally absent from the result.
    """
    return {field: case[field] for field in CANDIDATE_VISIBLE_FIELDS}
