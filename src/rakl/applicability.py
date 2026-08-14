"""Regime-conditional applicability contract (#543).

A mechanic whose known-world evidence shows a *regime crossover* — statistically
separated subsets with confidence intervals excluding zero on opposite sides —
must NOT be promoted unconditionally on the pooled mean. The pooled mean averages
the positive and negative regimes and is semantically stronger than the evidence.

This module produces the single machine-readable applicability contract consumed
by three places, so they never disagree:

  * ``scripts/promotion_gate.py``  — emits the contract; downgrades an
    unconditional PROMOTE to PROMOTE_CONDITIONALLY when a crossover is present.
  * ``tools/build_atomic_claim_registry.py`` — carries the contract into the
    net-benefit claim record (e.g. EMP-PATHQ-NETBENEFIT).
  * the routing controller (#535) — calls :func:`route_decision` to decide, for
    a concrete runtime regime, whether to apply the mechanic or fall back to the
    baseline. SUPPORTED -> mechanic; NEGATIVE and UNKNOWN both -> baseline.

The contract is a plain JSON-serializable dict (no dataclass) so it round-trips
through the committed artifacts without serialization surprises, and every
consumer reads the identical shape.

Honesty / fail-closed rules (enforced here, not at the call site):
  * the crossover is re-derived from the subset CIs; the experiment's own
    "positive_subset"/"negative_subset" *labels* are never trusted. If the CI of
    a labelled subset actually straddles zero, no contract is produced.
  * a runtime regime is SUPPORTED only on an exact positive cell, or on a point
    that lies inside the positive box AND outside the negative box (clean
    interpolation). When the boxes overlap (as for path-quotient, where the
    positive box is nested inside the negative box), interpolation is impossible
    and only exact positive cells are SUPPORTED.
  * any point a tested axis cannot classify (missing axis value, or outside both
    tested boxes) is UNKNOWN and fails closed to baseline.
"""
from __future__ import annotations

import math
from typing import Any, Mapping


def _is_real(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _ci_strictly_one_side(ci: Any, positive: bool) -> bool:
    """True if a [lo, hi] interval excludes zero strictly on one side.

    ``positive=True`` requires lo>0 and hi>0; ``positive=False`` requires hi<0
    and lo<0. Malformed (non-2-tuple / non-finite) -> False (no claim).
    """
    if not isinstance(ci, (list, tuple)) or len(ci) != 2:
        return False
    lo, hi = ci
    if not (_is_real(lo) and _is_real(hi)):
        return False
    if positive:
        return lo > 0.0 and hi > 0.0
    return lo < 0.0 and hi < 0.0


def _axis_names(subsets: list[dict]) -> list[str]:
    """Union of numeric cell keys across the given subsets, sorted."""
    names: set[str] = set()
    for sub in subsets:
        for cell in sub.get("cells", []) or []:
            if not isinstance(cell, Mapping):
                continue
            for k, v in cell.items():
                if _is_real(v):
                    names.add(k)
    return sorted(names)


def _bounding_box(cells: list[dict], axes: list[str]) -> dict[str, list[float]]:
    """Per-axis [min, max] over the numeric values of the cells."""
    box: dict[str, list[float]] = {}
    for ax in axes:
        vals = [
            float(cell[ax])
            for cell in cells
            if isinstance(cell, Mapping) and _is_real(cell.get(ax))
        ]
        if vals:
            box[ax] = [min(vals), max(vals)]
    return box


def _inside(box: Mapping[str, list[float]], point: Mapping[str, Any]) -> bool:
    """True iff point supplies every axis in box and each value lies in [lo, hi]."""
    for ax, rng in box.items():
        v = point.get(ax) if isinstance(point, Mapping) else None
        if not _is_real(v):
            return False
        if not (rng[0] <= v <= rng[1]):
            return False
    return True


def _exact_cell_match(cells: list[dict], point: Mapping[str, Any]) -> bool:
    """True iff point matches some cell on every numeric key of that cell."""
    for cell in cells:
        if not isinstance(cell, Mapping):
            continue
        if all(
            _is_real(cell.get(k)) and _is_real(point.get(k)) and point.get(k) == cell[k]
            for k in cell
            if _is_real(cell.get(k))
        ):
            # require at least one numeric key matched, so {} / non-numeric cells don't match
            if any(_is_real(cell.get(k)) for k in cell):
                return True
    return False


def build_applicability_contract(regime_analysis: Any) -> dict | None:
    """Build a regime-crossover applicability contract from an artifact's
    ``regime_analysis`` block, or return ``None`` if there is no statistically
    separated opposing-sign crossover.

    Returns None (so the caller falls back to the pooled-mean verdict) unless:
      * ``regime_analysis`` is a dict with ``positive_subset`` and
        ``negative_subset`` each carrying ``cells`` and a 2-element
        ``net_saving_ci95``;
      * the two subset CIs exclude zero on *opposite* sides (re-derived from the
        CIs, not from the subset labels);
      * both subsets have at least one numeric cell.
    """
    if not isinstance(regime_analysis, Mapping):
        return None
    pos = regime_analysis.get("positive_subset") or {}
    neg = regime_analysis.get("negative_subset") or {}
    if not isinstance(pos, Mapping) or not isinstance(neg, Mapping):
        return None
    pos_cells = list(pos.get("cells") or [])
    neg_cells = list(neg.get("cells") or [])
    if not pos_cells or not neg_cells:
        return None

    pos_ci = pos.get("net_saving_ci95")
    neg_ci = neg.get("net_saving_ci95")
    # opposing-sign: each CI excludes zero, on opposite sides. We do not assume
    # which subset is the positive one - check both orientations.
    opposing = (
        (_ci_strictly_one_side(pos_ci, True) and _ci_strictly_one_side(neg_ci, False))
        or (_ci_strictly_one_side(pos_ci, False) and _ci_strictly_one_side(neg_ci, True))
    )
    if not opposing:
        return None

    axes = _axis_names([{"cells": pos_cells}, {"cells": neg_cells}])
    if not axes:
        return None

    pos_box = _bounding_box(pos_cells, axes)
    neg_box = _bounding_box(neg_cells, axes)
    # per-axis overlap of the two bounding boxes (None where an axis does not overlap)
    overlap: dict[str, list[float]] = {}
    boxes_overlap = True
    for ax in axes:
        if ax in pos_box and ax in neg_box:
            lo = max(pos_box[ax][0], neg_box[ax][0])
            hi = min(pos_box[ax][1], neg_box[ax][1])
            if lo <= hi:
                overlap[ax] = [lo, hi]
            else:
                boxes_overlap = False
                break

    pos_significant = _ci_strictly_one_side(pos_ci, True)
    neg_significant = _ci_strictly_one_side(neg_ci, False)

    def _sub_record(sub: Mapping, cells: list[dict]) -> dict:
        return {
            "cells": [
                {k: v for k, v in cell.items() if _is_real(v)}
                for cell in cells
                if isinstance(cell, Mapping)
            ],
            "net_saving_mean": sub.get("net_saving_mean"),
            "net_saving_ci95": list(sub["net_saving_ci95"]) if isinstance(sub.get("net_saving_ci95"), (list, tuple)) else None,
            "n": sub.get("n"),
        }

    contract = {
        "kind": "regime_crossover_applicability",
        "issue": "#543",
        "axes": [
            {
                "name": ax,
                "type": "int"
                if all(
                    _is_real(cell.get(ax)) and float(cell[ax]).is_integer()
                    for cell in (pos_cells + neg_cells)
                    if isinstance(cell, Mapping) and _is_real(cell.get(ax))
                )
                else "float",
                "tested_values": sorted(
                    {
                        cell[ax]
                        for cell in (pos_cells + neg_cells)
                        if isinstance(cell, Mapping) and _is_real(cell.get(ax))
                    }
                ),
            }
            for ax in axes
        ],
        "positive_subset": _sub_record(pos, pos_cells),
        "negative_subset": _sub_record(neg, neg_cells),
        "positive_regime_significant": pos_significant,
        "negative_regime_significant": neg_significant,
        "opposing_sign": True,
        "boxes": {
            "positive": pos_box,
            "negative": neg_box,
            "overlap": overlap if boxes_overlap else {},
            "boxes_disjoint": not boxes_overlap,
        },
        "policy": {
            "SUPPORTED": (
                "exact match of a positive cell, OR a point inside the positive box "
                "that is also outside the negative box (clean interpolation only)"
            ),
            "NEGATIVE": (
                "exact match of a negative cell, OR a point inside the negative box "
                "that is also outside the positive box"
            ),
            "UNKNOWN": (
                "any point a tested axis cannot classify: missing axis value, inside "
                "the box overlap region without an exact cell, or outside both boxes"
            ),
            "unknown_action": "fail_closed_to_baseline",
            "baseline": "naive / raw unquotiented path enumeration",
            "routing_rule": "route to the mechanic ONLY on SUPPORTED; NEGATIVE and UNKNOWN both fall back to baseline",
        },
    }
    return contract


def classify_regime_point(contract: Mapping, point: Mapping[str, Any]) -> str:
    """Classify a runtime regime point against a crossover contract.

    Returns one of ``"SUPPORTED"`` / ``"NEGATIVE"`` / ``"UNKNOWN"``. The
    controller routes to the mechanic iff SUPPORTED; both NEGATIVE and UNKNOWN
    fall back to baseline (#543 fail-closed).
    """
    if not isinstance(contract, Mapping) or contract.get("kind") != "regime_crossover_applicability":
        return "UNKNOWN"
    pos_cells = list((contract.get("positive_subset") or {}).get("cells") or [])
    neg_cells = list((contract.get("negative_subset") or {}).get("cells") or [])
    boxes = contract.get("boxes") or {}

    if _exact_cell_match(pos_cells, point):
        return "SUPPORTED"
    if _exact_cell_match(neg_cells, point):
        return "NEGATIVE"

    in_pos = _inside(boxes.get("positive", {}), point)
    in_neg = _inside(boxes.get("negative", {}), point)
    if in_pos and not in_neg:
        return "SUPPORTED"
    if in_neg and not in_pos:
        return "NEGATIVE"
    return "UNKNOWN"


def route_decision(contract: Mapping, point: Mapping[str, Any]) -> dict:
    """Controller entry point: classify a runtime regime and return the route.

    Output shape consumed by the routing controller (#535):
      {"classification": ..., "route": "mechanic"|"baseline", "baseline": ..., "reason": ...}
    """
    cls = classify_regime_point(contract, point)
    policy = contract.get("policy", {}) if isinstance(contract, Mapping) else {}
    if cls == "SUPPORTED":
        return {
            "classification": cls,
            "route": "mechanic",
            "baseline": policy.get("baseline", "baseline"),
            "reason": "regime inside the supported (positive-net) region; mechanic applies",
        }
    return {
        "classification": cls,
        "route": "baseline",
        "baseline": policy.get("baseline", "baseline"),
        "reason": (
            "known net-negative regime -> baseline"
            if cls == "NEGATIVE"
            else "unknown/untested regime -> fail closed to baseline (#543)"
        ),
    }
