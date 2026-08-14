"""Seeded parametric known-answer corpus generator for BENEFIT-L1-COMPOSITION-V1.

Implements CORPUS_PLAN.md exactly: 8 invented domain families, hidden worlds with
genuine transition content, N=400 chains in the frozen class composition
(D1=120, D2=40, D3=60, D4=60, D5=40, D6=40, D7=40), hop count 2-4, gold labels a
pure function of the hidden world at generation time. No network, no LLM, no arm
participates in labeling.

Skeleton-route reuse (design honesty note, resolved a priori before any freeze or
result access): within each (world, hop-count) cell all D1-D6 chains share one
standard object route, and D7 breaks that route at one junction via an aliased
source id. This heavy reuse mirrors real corpora where most chains traverse
standard junctions, and is what gives the frozen contract-permutation null a
nonzero base rate to measure against (same reason the L0 corpus reused standard
context tuples). Class semantics live in the contract content, not in route
identity.

Also provides class_invariant_checks(): a generator-validation pass (record-level
mechanics recomputed from scratch, not via any arm rule) run BEFORE freeze.
"""
from __future__ import annotations

import random
from typing import Any

SEED = 20260814
N_BY_CLASS = {"D1": 120, "D2": 40, "D3": 60, "D4": 60, "D5": 40, "D6": 40, "D7": 40}
HOPS = (2, 3, 4)

FAMILIES = [
    {
        "key": "rxn", "name": "reaction pathway transfer",
        "noun": "pathway step", "object": "intermediate",
        "invariants": ["mass_conservation", "stoichiometric_balance", "chirality_retention",
                       "redox_state_bookkeeping", "isotope_label_integrity"],
        "regimes": ["aqueous_25C", "aqueous_60C", "anhydrous_glovebox", "flow_reactor",
                    "photochemical", "high_pressure"],
        "roles": ["activated_substrate", "protecting_group_state", "catalyst_loading",
                  "solvent_spec", "intermediate_purity", "quench_state"],
        "error_semantics": "yield_loss_fraction_abs",
    },
    {
        "key": "cal", "name": "sensor-calibration chain",
        "noun": "calibration hop", "object": "reference",
        "invariants": ["linearity", "zero_offset_traceability", "gain_stability",
                       "thermal_drift_bound", "hysteresis_bound"],
        "regimes": ["lab_20C", "field_ambient", "vibration_isolated", "vacuum_chamber",
                    "cryostat", "humidity_controlled"],
        "roles": ["voltage_reference", "timing_reference", "gain_map", "offset_table",
                  "noise_floor_spec", "traceability_cert"],
        "error_semantics": "calibration_error_abs_pct",
    },
    {
        "key": "xlat", "name": "translation pipeline",
        "noun": "translation stage", "object": "representation",
        "invariants": ["named_entity_fidelity", "negation_scope", "numeric_literal_fidelity",
                       "register_consistency", "coreference_integrity"],
        "regimes": ["technical_prose", "legal_prose", "conversational", "medical_notes",
                    "patent_claims", "news_wire"],
        "roles": ["token_alignment", "glossary_binding", "segment_ids", "style_profile",
                  "terminology_lock", "sentence_boundaries"],
        "error_semantics": "meaning_shift_score_abs",
    },
    {
        "key": "unit", "name": "unit-system bridge",
        "noun": "unit conversion", "object": "quantity system",
        "invariants": ["dimensional_consistency", "significant_figure_policy",
                       "reference_condition_lock", "rounding_direction_policy",
                       "scale_linearity"],
        "regimes": ["si_strict", "imperial_survey", "cgs_gaussian", "industry_custom",
                    "astronomical", "nautical"],
        "roles": ["base_unit_map", "prefix_table", "reference_temperature",
                  "conversion_factor_set", "precision_contract", "datum_definition"],
        "error_semantics": "conversion_roundoff_abs",
    },
    {
        "key": "mdl", "name": "model-reduction chain",
        "noun": "reduction step", "object": "model",
        "invariants": ["energy_balance", "steady_state_gain", "passivity",
                       "conservation_of_charge", "boundary_condition_class"],
        "regimes": ["low_frequency", "linearized_neighborhood", "slow_manifold",
                    "high_reynolds", "small_signal", "quasi_static"],
        "roles": ["state_vector_map", "parameter_projection", "input_port_spec",
                  "output_port_spec", "timescale_contract", "initial_condition_map"],
        "error_semantics": "output_deviation_sup_norm",
    },
    {
        "key": "proto", "name": "protocol version lineage",
        "noun": "version migration", "object": "protocol revision",
        "invariants": ["wire_format_backcompat", "auth_handshake_semantics",
                       "idempotency_guarantee", "ordering_guarantee", "checksum_scheme"],
        "regimes": ["lan_deployment", "wan_lossy", "embedded_constrained", "cloud_managed",
                    "airgapped", "mobile_intermittent"],
        "roles": ["session_token_shape", "frame_header_layout", "retry_policy",
                  "capability_flags", "error_code_map", "keepalive_contract"],
        "error_semantics": "compat_defect_rate_abs",
    },
    {
        "key": "scc", "name": "supply-chain custody chain",
        "noun": "custody transfer", "object": "custody node",
        "invariants": ["seal_integrity", "cold_chain_bound", "lot_identity",
                       "chain_of_signatures", "quantity_reconciliation"],
        "regimes": ["reefer_transport", "ambient_warehouse", "customs_bonded",
                    "last_mile", "port_transshipment", "rail_intermodal"],
        "roles": ["manifest_record", "seal_id_set", "temperature_log", "custody_signature",
                  "lot_barcode", "weight_certificate"],
        "error_semantics": "custody_discrepancy_abs",
    },
    {
        "key": "frame", "name": "coordinate-frame transform chain",
        "noun": "frame transform", "object": "frame",
        "invariants": ["rigid_body_length", "orientation_handedness", "epoch_consistency",
                       "origin_traceability", "angular_rate_continuity"],
        "regimes": ["earth_fixed", "inertial_j2000", "body_fixed", "sensor_local",
                    "topocentric", "orbital_lvlh"],
        "roles": ["rotation_spec", "translation_spec", "epoch_tag", "velocity_state",
                  "covariance_map", "time_scale_binding"],
        "error_semantics": "alignment_error_abs_mrad",
    },
]

OMISSION_KINDS = ("hop_error_bound", "handoff_compatibility", "hop_evidence_lineage")

_LEX_OK = ["holds cleanly", "is genuinely satisfied", "checks out end to end",
           "is confirmed by the bench record", "survives every step"]
_LEX_STEP = ["step", "leg", "stage", "hop", "segment"]


def _build_world(rng: random.Random, family: dict[str, Any]) -> dict[str, Any]:
    key = family["key"]
    world: dict[str, Any] = {
        "world_id": f"{key}-w0",
        "family": family["name"],
        "routes": {},
        "junction_roles": {},
        "common_regime": {},
    }
    for h in HOPS:
        objs = [f"{key}-{h}h-node{k}" for k in range(h + 1)]
        world["routes"][str(h)] = objs
        # Standard per-junction role inventories: consumed is a genuine subset of
        # delivered for the intact world.
        junctions = []
        for k in range(h - 1):
            delivered = rng.sample(family["roles"], 3)
            consumed = rng.sample(delivered, 2)
            junctions.append({"junction_id": objs[k + 1],
                              "delivered": delivered, "consumed": consumed})
        world["junction_roles"][str(h)] = junctions
        world["common_regime"][str(h)] = rng.choice(family["regimes"])
    return world


def _hop_regimes(rng: random.Random, family: dict[str, Any], h: int,
                 common: str, disjoint: bool) -> list[list[str]]:
    """Per-hop regime sets. Intact: every hop contains the common regime.
    Disjoint (D4): every hop non-empty, adjacent hops overlap, global
    intersection empty (first and last anchored to distinct regimes)."""
    pool = [r for r in family["regimes"] if r != common]
    if not disjoint:
        out = []
        for _ in range(h):
            extra = rng.sample(pool, rng.randint(0, 1))
            out.append(sorted({common, *extra}))
        return out
    r_first, r_last = rng.sample(pool, 2)
    out = []
    for i in range(h):
        if i == 0:
            out.append(sorted({r_first}))
        elif i == h - 1:
            out.append(sorted({r_last}))
        else:
            out.append(sorted({r_first, r_last}))
    return out


def _make_chain(rng: random.Random, family: dict[str, Any], world: dict[str, Any],
                klass: str, chain_num: int, minted_at: str) -> tuple[dict[str, Any], dict[str, Any]]:
    key = family["key"]
    h = rng.choice(HOPS)
    route = list(world["routes"][str(h)])
    junctions = [dict(j) for j in world["junction_roles"][str(h)]]
    common = world["common_regime"][str(h)]
    chain_id = f"L1-{chain_num:04d}"

    claimed = sorted(rng.sample(family["invariants"], rng.randint(1, 2)))
    filler = [inv for inv in family["invariants"] if inv not in claimed]

    # --- world truth ---------------------------------------------------------
    disjoint = klass == "D4"
    regimes = _hop_regimes(rng, family, h, common, disjoint)
    tolerance = round(rng.uniform(0.08, 0.12), 4)
    if klass == "D6":
        per_err = [round(rng.uniform(0.6, 0.9) * tolerance, 4) for _ in range(h)]
    else:
        budget = tolerance * rng.uniform(0.4, 0.85)
        per_err = [round(budget / h, 4) for _ in range(h)]
    broken_hop = rng.randrange(1, h) if klass == "D3" else None
    broken_inv = rng.choice(claimed) if klass == "D3" else None
    bad_junction = rng.randrange(0, h - 1) if klass == "D5" else None
    alias_junction = rng.randrange(0, h - 1) if klass == "D7" else None

    per_hop_truth = []
    for i in range(h):
        preserved = sorted(set(claimed) | set(rng.sample(filler, 1)))
        not_preserved = []
        if klass == "D3" and i == broken_hop:
            preserved = sorted((set(preserved) - {broken_inv}) | set(rng.sample(filler, 1)))
            not_preserved = [broken_inv]
        per_hop_truth.append({
            "regime": regimes[i],
            "preserved": preserved,
            "not_preserved": not_preserved,
            "evidence_lineage_ids": [f"ev:{chain_id}:hop{i}:{rng.randrange(1000):03d}"],
            "error_bound": per_err[i],
            "error_semantics_id": family["error_semantics"],
        })

    handoffs_truth = []
    for k in range(h - 1):
        delivered = list(junctions[k]["delivered"])
        consumed = list(junctions[k]["consumed"])
        if klass == "D5" and k == bad_junction:
            outside = [r for r in family["roles"] if r not in delivered]
            consumed = sorted(set(consumed[:1]) | {rng.choice(outside)})
        handoffs_truth.append({
            "junction_id": junctions[k]["junction_id"],
            "roles_delivered": sorted(delivered),
            "roles_consumed": sorted(consumed),
            "compatibility_passed": True,
        })

    skeleton = [{"source_id": route[i], "target_id": route[i + 1]} for i in range(h)]
    if klass == "D7":
        # break connectivity: the NEXT hop starts from an alias id; junction ids
        # in the contract stay on the standard route (the shared-name record).
        skeleton[alias_junction + 1] = {
            "source_id": route[alias_junction + 1] + "-alias",
            "target_id": skeleton[alias_junction + 1]["target_id"],
        }

    world_truth = {
        "chain_id": chain_id,
        "class": klass,
        "hops": h,
        "route": route,
        "per_hop": per_hop_truth,
        "handoffs": handoffs_truth,
        "claimed_invariants": claimed,
        "max_accumulated_error": tolerance,
        "true_accumulated_error": round(sum(per_err), 4),
        "disconnected_at": alias_junction,
        "broken_invariant": broken_inv,
        "broken_hop": broken_hop,
        "role_mismatch_junction": bad_junction,
    }

    # --- record (contract) ---------------------------------------------------
    import json as _json
    contract = {
        "per_hop": _json.loads(_json.dumps(per_hop_truth)),
        "handoffs": _json.loads(_json.dumps(handoffs_truth)),
        "claimed_invariants": claimed,
        "max_accumulated_error": tolerance,
        "error_composition_rule": {
            "rule_id": f"rule:{key}:additive-v1",
            "error_semantics_id": family["error_semantics"],
            "kind": "ADDITIVE_UPPER_BOUND",
        },
    }
    omission = None
    if klass == "D2":
        kind = rng.choice(OMISSION_KINDS)
        if kind == "hop_error_bound":
            idx = rng.randrange(h)
            del contract["per_hop"][idx]["error_bound"]
            omission = {"kind": kind, "index": idx}
        elif kind == "handoff_compatibility":
            idx = rng.randrange(h - 1)
            del contract["handoffs"][idx]["compatibility_passed"]
            omission = {"kind": kind, "index": idx}
        else:
            idx = rng.randrange(h)
            del contract["per_hop"][idx]["evidence_lineage_ids"]
            omission = {"kind": kind, "index": idx}
    world_truth["record_omission"] = omission

    gold = "SUPPORTED" if klass in ("D1", "D2") else "UNSUPPORTED"
    surface = _render_surface(rng, family, world_truth, skeleton, contract, gold)

    row = {
        "chain_id": chain_id,
        "class": klass,
        "gold_label": gold,
        "label_minted_at": minted_at,
        "skeleton": skeleton,
        "contract": contract,
        "surface_text": surface,
        "world_id": world["world_id"],
        "generator_seed": SEED,
    }
    return row, world_truth


def _render_surface(rng: random.Random, family: dict[str, Any], truth: dict[str, Any],
                    skeleton: list[dict[str, str]], contract: dict[str, Any],
                    gold: str) -> str:
    """Deterministic template + seeded lexical variation. Verbalizes the WORLD
    facts (including, for D2, the true measured value behind the record
    omission) so the label audit can judge supportedness from prose alone."""
    del gold  # rendering is driven by world facts, never by the label directly
    step_word = rng.choice(_LEX_STEP)
    h = truth["hops"]
    lines = [
        f"{family['name'].capitalize()} across {h} {step_word}s: "
        + " -> ".join([skeleton[0]["source_id"]] + [s["target_id"] for s in skeleton])
        + "."
    ]
    if truth["disconnected_at"] is not None:
        k = truth["disconnected_at"]
        lines.append(
            f"NOTE: {step_word} {k + 2} actually starts from "
            f"'{skeleton[k + 1]['source_id']}', which is NOT the object the previous "
            f"{step_word} delivered ('{skeleton[k]['target_id']}'); the printed route "
            "papers over a real break in the chain."
        )
    lines.append(
        "End-to-end claim: " + ", ".join(truth["claimed_invariants"])
        + f" carried across the whole chain, with accumulated error at most "
        + f"{truth['max_accumulated_error']} ({family['error_semantics']}, additive bound)."
    )
    for i, hop in enumerate(truth["per_hop"]):
        frag = [f"{step_word.capitalize()} {i + 1} operates in regime(s) "
                + "/".join(hop["regime"])
                + "; preserves " + ", ".join(hop["preserved"])]
        if hop["not_preserved"]:
            frag.append("but GENUINELY BREAKS " + ", ".join(hop["not_preserved"]))
        frag.append(f"measured {step_word} error {hop['error_bound']}")
        lines.append("; ".join(frag) + ".")
    for k, hand in enumerate(truth["handoffs"]):
        delivered = ", ".join(hand["roles_delivered"])
        consumed = ", ".join(hand["roles_consumed"])
        missing = sorted(set(hand["roles_consumed"]) - set(hand["roles_delivered"]))
        line = (f"Junction {k + 1} ({hand['junction_id']}): prior {step_word} delivers "
                f"[{delivered}]; next {step_word} consumes [{consumed}]")
        if missing:
            line += (f" — the consumed role(s) [{', '.join(missing)}] are NOT delivered; "
                     "the shared name hides a real role mismatch")
        lines.append(line + ".")
    regime_sets = [set(hop["regime"]) for hop in truth["per_hop"]]
    inter = set.intersection(*regime_sets) if regime_sets else set()
    if inter:
        lines.append("All " + step_word + "s share operating regime "
                     + "/".join(sorted(inter)) + ", so the chain "
                     + rng.choice(_LEX_OK) + " on scope.")
    else:
        lines.append(f"No single operating regime is shared by every {step_word}: "
                     "the regime sets have EMPTY intersection end to end.")
    total = truth["true_accumulated_error"]
    tol = truth["max_accumulated_error"]
    if total > tol:
        lines.append(f"True accumulated error {total} EXCEEDS the frozen chain "
                     f"tolerance {tol} under the additive rule.")
    else:
        lines.append(f"True accumulated error {total} stays within the frozen chain "
                     f"tolerance {tol}.")
    om = truth["record_omission"]
    if om is not None:
        detail = {
            "hop_error_bound": "the filed record omits that step's error bound",
            "handoff_compatibility": "the filed record omits that junction's "
                                     "compatibility check result",
            "hop_evidence_lineage": "the filed record omits that step's evidence "
                                    "lineage references",
        }[om["kind"]]
        lines.append(f"RECORD GAP (index {om['index']}): {detail}; the bench facts "
                     "above are nonetheless genuine and the chain is truly as described.")
    return "\n".join(lines)


def generate() -> tuple[dict[str, Any], dict[str, Any]]:
    rng = random.Random(SEED)
    from common import utc_now_iso
    minted_at = utc_now_iso()
    worlds = [_build_world(rng, fam) for fam in FAMILIES]

    class_list: list[str] = []
    for klass in ("D1", "D2", "D3", "D4", "D5", "D6", "D7"):
        class_list.extend([klass] * N_BY_CLASS[klass])

    rows, truths = [], []
    for i, klass in enumerate(class_list):
        fam = FAMILIES[i % len(FAMILIES)]
        world = worlds[i % len(FAMILIES)]
        row, truth = _make_chain(rng, fam, world, klass, i, minted_at)
        rows.append(row)
        truths.append(truth)

    corpus = {
        "protocol_id": "BENEFIT-L1-COMPOSITION-V1",
        "generated_at": minted_at,
        "generator_seed": SEED,
        "n_chains": len(rows),
        "chains": rows,
    }
    worlds_meta = {
        "note": "hidden-world truth dump; debug artifact, never arm input",
        "worlds": worlds,
        "per_chain_truth": truths,
    }
    return corpus, worlds_meta


# ---------------------------------------------------------------------------
# Generator validation: record-level class invariants recomputed from scratch.
# Never uses any arm rule; catches rendering/labeling defects BEFORE freeze.
# ---------------------------------------------------------------------------

def _record_conditions(row: dict[str, Any]) -> dict[str, Any]:
    sk = row["skeleton"]
    c = row["contract"]
    n = len(sk)
    per_hop = c.get("per_hop", [])
    handoffs = c.get("handoffs", [])
    out: dict[str, Any] = {}
    out["connected"] = all(sk[i]["target_id"] == sk[i + 1]["source_id"]
                           for i in range(n - 1))
    out["n_disconnects"] = sum(1 for i in range(n - 1)
                               if sk[i]["target_id"] != sk[i + 1]["source_id"])
    out["structure_ok"] = len(per_hop) == n and len(handoffs) == n - 1
    out["junction_ids_ok"] = all(handoffs[k].get("junction_id") == sk[k]["target_id"]
                                 for k in range(n - 1)) if out["structure_ok"] else False
    bad_roles = [k for k in range(n - 1)
                 if not (set(handoffs[k].get("roles_consumed", []))
                         and set(handoffs[k].get("roles_consumed", []))
                         <= set(handoffs[k].get("roles_delivered", [])))]
    out["role_mismatch_junctions"] = bad_roles
    out["compat_all_true"] = all(handoffs[k].get("compatibility_passed") is True
                                 for k in range(n - 1))
    claimed = c.get("claimed_invariants", [])
    out["claimed_nonempty"] = bool(claimed)
    broken_hops = [i for i in range(len(per_hop))
                   for inv in claimed
                   if inv in per_hop[i].get("not_preserved", [])
                   or inv not in per_hop[i].get("preserved", [])]
    out["invariant_break_hops"] = sorted(set(broken_hops))
    out["preserved_notpreserved_disjoint"] = all(
        not (set(hop.get("preserved", [])) & set(hop.get("not_preserved", [])))
        for hop in per_hop)
    regs = [set(hop.get("regime", [])) for hop in per_hop]
    out["all_regimes_nonempty"] = all(regs) if regs else False
    out["regime_intersection_nonempty"] = bool(set.intersection(*regs)) if regs else False
    out["lineage_missing_hops"] = [i for i, hop in enumerate(per_hop)
                                   if not hop.get("evidence_lineage_ids")]
    out["error_bound_missing_hops"] = [i for i, hop in enumerate(per_hop)
                                       if hop.get("error_bound") is None]
    out["compat_missing_junctions"] = [k for k in range(len(handoffs))
                                       if "compatibility_passed" not in handoffs[k]]
    rule = c.get("error_composition_rule") or {}
    out["rule_ok"] = bool(rule.get("rule_id")) and bool(rule.get("error_semantics_id")) \
        and rule.get("kind") == "ADDITIVE_UPPER_BOUND"
    out["semantics_match"] = all(hop.get("error_semantics_id") == rule.get("error_semantics_id")
                                 for hop in per_hop)
    tol = c.get("max_accumulated_error")
    bounds = [hop.get("error_bound") for hop in per_hop]
    out["tolerance_ok"] = tol is not None and tol >= 0
    if all(b is not None for b in bounds) and tol is not None:
        out["error_within_tolerance"] = sum(bounds) <= tol
    else:
        out["error_within_tolerance"] = None
    return out


def class_invariant_checks(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    counts: dict[str, int] = {}
    for row in rows:
        klass = row["class"]
        counts[klass] = counts.get(klass, 0) + 1
        cid = row["chain_id"]
        c = _record_conditions(row)
        expected_gold = "SUPPORTED" if klass in ("D1", "D2") else "UNSUPPORTED"
        if row["gold_label"] != expected_gold:
            errors.append(f"{cid}: gold {row['gold_label']} != class-implied {expected_gold}")
        if not (2 <= len(row["skeleton"]) <= 4):
            errors.append(f"{cid}: hop count out of range")
        if not c["structure_ok"]:
            errors.append(f"{cid}: contract structure sizes wrong")
            continue
        if not c["preserved_notpreserved_disjoint"]:
            errors.append(f"{cid}: preserved/not_preserved overlap (would diverge arm rules)")
        if not c["claimed_nonempty"] or not c["rule_ok"] or not c["semantics_match"] \
                or not c["tolerance_ok"] or not c["all_regimes_nonempty"] \
                or not c["junction_ids_ok"]:
            errors.append(f"{cid}: baseline contract fields defective for {klass}")
        clean = (c["connected"] and not c["invariant_break_hops"]
                 and c["regime_intersection_nonempty"] and not c["role_mismatch_junctions"]
                 and c["compat_all_true"] and not c["lineage_missing_hops"]
                 and not c["error_bound_missing_hops"] and not c["compat_missing_junctions"]
                 and c["error_within_tolerance"] is True)
        if klass == "D1" and not clean:
            errors.append(f"{cid}: D1 must satisfy all six conditions on the record")
        elif klass == "D2":
            n_omit = (len(c["error_bound_missing_hops"]) + len(c["compat_missing_junctions"])
                      + len(c["lineage_missing_hops"]))
            if n_omit != 1:
                errors.append(f"{cid}: D2 must omit exactly one licensing field, saw {n_omit}")
            if not (c["connected"] and not c["invariant_break_hops"]
                    and c["regime_intersection_nonempty"] and not c["role_mismatch_junctions"]):
                errors.append(f"{cid}: D2 world-supported side conditions violated")
        elif klass == "D3":
            if not c["invariant_break_hops"]:
                errors.append(f"{cid}: D3 must break a claimed invariant at a hop")
            if not (c["connected"] and c["regime_intersection_nonempty"]
                    and not c["role_mismatch_junctions"] and c["compat_all_true"]
                    and c["error_within_tolerance"] is True):
                errors.append(f"{cid}: D3 must be otherwise clean")
        elif klass == "D4":
            if c["regime_intersection_nonempty"]:
                errors.append(f"{cid}: D4 regime intersection must be empty")
            if not (c["connected"] and not c["invariant_break_hops"]
                    and not c["role_mismatch_junctions"]
                    and c["error_within_tolerance"] is True):
                errors.append(f"{cid}: D4 must be otherwise clean")
        elif klass == "D5":
            if len(c["role_mismatch_junctions"]) != 1:
                errors.append(f"{cid}: D5 must break roles at exactly one junction")
            if not (c["connected"] and not c["invariant_break_hops"]
                    and c["regime_intersection_nonempty"]
                    and c["error_within_tolerance"] is True):
                errors.append(f"{cid}: D5 must be otherwise clean")
        elif klass == "D6":
            if c["error_within_tolerance"] is not False:
                errors.append(f"{cid}: D6 accumulated error must exceed tolerance")
            if not (c["connected"] and not c["invariant_break_hops"]
                    and c["regime_intersection_nonempty"] and not c["role_mismatch_junctions"]):
                errors.append(f"{cid}: D6 must be otherwise clean")
        elif klass == "D7":
            if c["n_disconnects"] != 1:
                errors.append(f"{cid}: D7 must have exactly one disconnection")
            if not (not c["invariant_break_hops"] and c["regime_intersection_nonempty"]
                    and not c["role_mismatch_junctions"]
                    and c["error_within_tolerance"] is True):
                errors.append(f"{cid}: D7 contract must be otherwise complete/clean")
    for klass, expected in N_BY_CLASS.items():
        if counts.get(klass, 0) != expected:
            errors.append(f"class {klass}: {counts.get(klass, 0)} rows != frozen {expected}")
    return errors
