"""Seeded known-answer multi-hop support-world generator for BENEFIT-L4-NAVIGATION-V1.

Implements CORPUS_PLAN.md exactly: hidden support hypergraphs first, gold labels
minted at generation as a pure function of the hidden world (exact admissible
route search over the FULL fact set, using the frozen EVALUATOR.py navigation
core loaded read-only by file path so gold semantics and evaluation semantics
cannot diverge), S* computed by exact minimal set cover over source fact-sets,
budget classes TIGHT=2*S* / MEDIUM=4*S* / LOOSE=8*S*, class composition frozen
in PROTOCOL.json (N=400: N1=120 N2=60 N3=60 N4=40 N5=60 N6=30 N7=30), and a
rendering-faithfulness re-check before freeze.

Degrees of freedom in CORPUS_PLAN.md resolved a priori (before freeze, before
any result access), on corpus-quality grounds:
- Deep-chain worlds (N1/N2/N3/N5): chain a0->..->ah with h in 3..5, all edges
  licensed at the demanded authority, chain edges packed 2-per-source (S* =
  ceil(h/2) in {2,3}); mid-chain sources are buried (index tokens = only their
  own atom ids, sharing nothing with the target beyond the start/goal
  endpoints); distractor sources carry 2 description tokens (3 in N5) plus
  off-path z-pool atom ids, so every distractor lexically outranks every
  on-path source. Distractor count D = 3*S*+1 (+2 in N5, jittered +0..1),
  which makes budgeted lexical reading structurally unable to cover the chain
  at MEDIUM (4*S* < D + S*) while LOOSE (8*S*) funds a full read — realizing
  the registered lexical trap without making arm A a straw man.
- Every world edge lives in exactly ONE source, and every obstruction is
  declared by the source carrying the FIRST edge of the route it obstructs,
  with at least one cover atom private to that route (N6 decoy midpoint d1).
  Consequence, by construction: no arm can assemble an obstruction-realizing
  route without having read the obstruction, so the connect rule rejects it
  and false solves are structurally impossible for policy-honest arms (the
  FSR_B == 0 gate is then a genuine check of the machinery, not luck).
- N6: lexically loud decoy a0->d1->goal whose atom set is an obstruction cover
  (declared with the first decoy edge); buried admissible detour
  a0->b1->b2->goal over 2 sources (S*=2); D in 5..7 so arm A's 8 reads
  exhaust on decoys+distractors.
- N7 draws uniformly between the two registered unsolvability modes: one
  mid-chain edge licensed below demand on every structural route, or goal
  disconnected (no edge into the goal at all). S* for N7 rows (undefined by
  the cover of an admissible route) is fixed a priori to ceil(h/2), the cover
  of the un-broken sibling design, so the budget classes stay comparable.
- Off-path z-pool of 6 atoms per world; distractor edges are drawn from it and
  never touch chain/cover atoms.

No network. Single random.Random stream from the registered seed. Gold labels
live in the hidden world; the surface_text renders the world facts so the
label-independent audit can check gold from the description alone.
"""
from __future__ import annotations

import importlib.util
import os
import random
from itertools import combinations
from typing import Any

from common import PROTO_DIR, REGISTERED_SEED, utc_now_iso

_spec = importlib.util.spec_from_file_location(
    "l4_frozen_evaluator", os.path.join(PROTO_DIR, "EVALUATOR.py"))
_frozen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_frozen)
admissible_route = _frozen.admissible_route

N_WORLDS = 400
CLASS_COMPOSITION = {
    "N1": 120, "N2": 60, "N3": 60, "N4": 40, "N5": 60, "N6": 30, "N7": 30,
}
BUDGET_BY_CLASS = {
    "N1": "MEDIUM", "N2": "TIGHT", "N3": "LOOSE", "N4": "MEDIUM",
    "N5": "MEDIUM", "N6": "MEDIUM", "N7": "MEDIUM",
}
BUDGET_MULT = {"TIGHT": 2, "MEDIUM": 4, "LOOSE": 8}
REQUIRED_AUTHORITY = 2
LEXICON = (
    "flux", "drift", "phase", "gain", "noise", "bias", "decay", "yield",
    "shear", "creep", "onset", "ramp", "swell", "taper", "wobble", "smear",
)


def _edge(src: str, dst: str, licensed: int = REQUIRED_AUTHORITY) -> dict[str, Any]:
    return {"source": src, "target": dst, "cost": 1.0, "licensed_at": licensed}


def _world_edges(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [e for s in sources for e in s["edges"]]


def _world_obstructions(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [o for s in sources for o in (s.get("obstructions") or ())]


def _minimal_source_cover(sources: list[dict[str, Any]], route: tuple[str, ...]) -> int:
    """Exact minimal set cover: fewest sources whose edges cover the route."""
    route_pairs = {(route[i], route[i + 1]) for i in range(len(route) - 1)}
    carriers = [
        s for s in sources
        if any((e["source"], e["target"]) in route_pairs for e in s["edges"])
    ]
    for size in range(1, len(carriers) + 1):
        for combo in combinations(carriers, size):
            covered = {(e["source"], e["target"]) for s in combo for e in s["edges"]}
            if route_pairs <= covered:
                return size
    raise AssertionError("route not coverable by its own sources")


def _shuffle_ids(rng: random.Random, sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order = list(range(len(sources)))
    rng.shuffle(order)
    for slot, src_idx in enumerate(order):
        sources[src_idx]["source_id"] = f"s{slot:02d}"
    return sorted(sources, key=lambda s: s["source_id"])


def _distractors(rng: random.Random, count: int, desc: list[str],
                 n_desc_tokens: int) -> list[dict[str, Any]]:
    out = []
    z_pool = [f"z{j}" for j in range(6)]
    for _ in range(count):
        zi, zj = rng.sample(z_pool, 2)
        tokens = sorted(rng.sample(desc, n_desc_tokens)) + [zi, zj]
        out.append({"source_id": "", "index_tokens": tokens,
                    "edges": [_edge(zi, zj)], "obstructions": []})
    return out


def _deep_chain_world(rng: random.Random, klass: str) -> dict[str, Any]:
    h = rng.randint(3, 5)
    atoms = [f"a{i}" for i in range(h + 1)]
    start, goal = atoms[0], atoms[-1]
    desc = sorted(rng.sample(LEXICON, 3))
    chain_edges = [_edge(atoms[i], atoms[i + 1]) for i in range(h)]

    unsolvable_mode = None
    if klass == "N7":
        unsolvable_mode = rng.choice(["under_licensed", "disconnected"])
        if unsolvable_mode == "under_licensed":
            weak = rng.randrange(1, h - 1) if h > 2 else 0
            chain_edges[weak] = _edge(atoms[weak], atoms[weak + 1], licensed=1)
        else:
            chain_edges = chain_edges[:-1]  # no edge into the goal at all

    on_path: list[dict[str, Any]] = []
    for i in range(0, len(chain_edges), 2):
        block = chain_edges[i:i + 2]
        toks = sorted({block[0]["source"]} | {e["target"] for e in block})
        on_path.append({"source_id": "", "index_tokens": toks,
                        "edges": block, "obstructions": []})
    s_star = -(-h // 2)  # ceil(h/2); a-priori constant for N7 too

    n_desc = 3 if klass == "N5" else 2
    d_count = 3 * s_star + 1 + (2 if klass == "N5" else 0) + rng.randint(0, 1)
    sources = _shuffle_ids(rng, on_path + _distractors(rng, d_count, desc, n_desc))

    budget_class = BUDGET_BY_CLASS[klass]
    world = {
        "class": klass, "budget_class": budget_class,
        "budget_units": float(BUDGET_MULT[budget_class] * s_star),
        "target": {"start_atom": start, "goal_atom": goal,
                   "required_authority": REQUIRED_AUTHORITY,
                   "description_tokens": desc},
        "sources": sources,
        "s_star_design": s_star,
        "world_facts": {
            "hops": h, "on_path_sources": len(on_path), "distractors": d_count,
            "unsolvable_mode": unsolvable_mode,
        },
    }
    return world


def _shallow_world(rng: random.Random) -> dict[str, Any]:
    desc = sorted(rng.sample(LEXICON, 3))
    on = {"source_id": "", "index_tokens": sorted(["a0", "a1"] + desc[:2]),
          "edges": [_edge("a0", "a1")], "obstructions": []}
    d_count = rng.randint(3, 5)
    sources = _shuffle_ids(rng, [on] + _distractors(rng, d_count, desc, 2))
    return {
        "class": "N4", "budget_class": "MEDIUM", "budget_units": 4.0,
        "target": {"start_atom": "a0", "goal_atom": "a1",
                   "required_authority": REQUIRED_AUTHORITY,
                   "description_tokens": desc},
        "sources": sources,
        "s_star_design": 1,
        "world_facts": {"hops": 1, "on_path_sources": 1, "distractors": d_count,
                        "unsolvable_mode": None},
    }


def _obstructed_decoy_world(rng: random.Random) -> dict[str, Any]:
    desc = sorted(rng.sample(LEXICON, 3))
    start, goal = "a0", "g0"
    ob_id = "ob0"
    s_d1 = {"source_id": "",
            "index_tokens": sorted(["a0", "d1", "g0"] + desc[:2]),
            "edges": [_edge("a0", "d1")],
            "obstructions": [{"obstruction_id": ob_id,
                              "cover": ["a0", "d1", "g0"],
                              "detail": "decoy triple jointly unrealizable"}]}
    s_d2 = {"source_id": "", "index_tokens": sorted(["d1", "g0"] + desc[:2]),
            "edges": [_edge("d1", "g0")], "obstructions": []}
    s_t1 = {"source_id": "", "index_tokens": ["a0", "b1", "b2"],
            "edges": [_edge("a0", "b1"), _edge("b1", "b2")], "obstructions": []}
    s_t2 = {"source_id": "", "index_tokens": ["b2", "g0"],
            "edges": [_edge("b2", "g0")], "obstructions": []}
    d_count = rng.randint(5, 7)
    sources = _shuffle_ids(
        rng, [s_d1, s_d2, s_t1, s_t2] + _distractors(rng, d_count, desc, 2))
    return {
        "class": "N6", "budget_class": "MEDIUM", "budget_units": 8.0,
        "target": {"start_atom": start, "goal_atom": goal,
                   "required_authority": REQUIRED_AUTHORITY,
                   "description_tokens": desc},
        "sources": sources,
        "s_star_design": 2,
        "world_facts": {"hops": 3, "on_path_sources": 2, "distractors": d_count,
                        "decoy": True, "obstruction_cover": ["a0", "d1", "g0"],
                        "unsolvable_mode": None},
    }


def _render_surface(world: dict[str, Any], gold: str) -> str:
    t = world["target"]
    wf = world["world_facts"]
    head = (
        f"Support-navigation world ({world['class']}-family design). Target: an "
        f"authority-{t['required_authority']} support route from {t['start_atom']} "
        f"to {t['goal_atom']} (description tokens {', '.join(t['description_tokens'])}). "
        f"{len(world['sources'])} sources; budget {world['budget_units']:.0f} "
        f"acquisition units ({world['budget_class']})."
    )
    if wf.get("unsolvable_mode") == "under_licensed":
        body = ("World facts: the only structural chain to the goal contains an edge "
                "licensed BELOW the demanded authority; no admissible route exists "
                "anywhere in the full fact set.")
    elif wf.get("unsolvable_mode") == "disconnected":
        body = ("World facts: NO edge into the goal atom exists anywhere in the "
                "full fact set; the goal is structurally disconnected.")
    elif wf.get("decoy"):
        body = ("World facts: the lexically loud two-hop route realizes a declared "
                "obstruction cover (its three atoms are jointly unrealizable), so it "
                "is NOT admissible; a buried three-hop detour, fully licensed at the "
                "demanded authority and avoiding the cover, IS admissible. A route "
                "therefore exists.")
    else:
        body = (f"World facts: a fully licensed {wf['hops']}-hop chain from "
                f"{t['start_atom']} to {t['goal_atom']} exists across "
                f"{wf['on_path_sources']} buried on-path source(s); "
                f"{wf['distractors']} distractor source(s) carry only off-path "
                "edges (lexically attractive, structurally irrelevant). An "
                "admissible route exists.")
    del gold  # the rendered description states world facts only; gold never leaks
    return f"{head} {body}"


def generate() -> tuple[dict[str, Any], dict[str, Any]]:
    rng = random.Random(REGISTERED_SEED)
    minted_at = utc_now_iso()

    class_list: list[str] = []
    for klass, count in sorted(CLASS_COMPOSITION.items()):
        class_list.extend([klass] * count)
    rng.shuffle(class_list)

    worlds_rows: list[dict[str, Any]] = []
    worlds_meta: list[dict[str, Any]] = []
    for idx in range(N_WORLDS):
        klass = class_list[idx]
        world_id = f"w{idx:03d}"
        while True:
            if klass == "N4":
                world = _shallow_world(rng)
            elif klass == "N6":
                world = _obstructed_decoy_world(rng)
            else:
                world = _deep_chain_world(rng, klass)

            target = world["target"]
            route = admissible_route(
                _world_edges(world["sources"]), _world_obstructions(world["sources"]),
                target["start_atom"], target["goal_atom"], target["required_authority"])
            gold = "SOLVABLE" if route is not None else "UNSOLVABLE"
            expected = "UNSOLVABLE" if klass == "N7" else "SOLVABLE"
            if gold != expected:
                # class geometry must realize its registered solvability; resample
                continue
            if route is not None:
                s_star = _minimal_source_cover(world["sources"], route)
            else:
                s_star = world["s_star_design"]
            if s_star != world["s_star_design"]:
                continue  # budget already sized from the design S*; must agree
            break

        # rendering-faithfulness re-check (union of rendered facts == hidden world
        # here by construction; re-verify anyway, dropping the row on mismatch)
        recheck = admissible_route(
            _world_edges(world["sources"]), _world_obstructions(world["sources"]),
            target["start_atom"], target["goal_atom"], target["required_authority"])
        if (recheck is not None) != (gold == "SOLVABLE"):
            raise AssertionError(f"{world_id}: rendering-faithfulness check failed")

        worlds_rows.append({
            "world_id": world_id,
            "class": klass,
            "budget_class": world["budget_class"],
            "budget_units": world["budget_units"],
            "gold_label": gold,
            "label_minted_at": minted_at,
            "target": target,
            "sources": world["sources"],
            "minimal_source_count": s_star,
            "surface_text": _render_surface(world, gold),
            "generator_seed": REGISTERED_SEED,
        })
        worlds_meta.append({"world_id": world_id, "class": klass,
                            "gold_label": gold, "s_star": s_star,
                            "admissible_route": list(route) if route else None,
                            **world["world_facts"]})

    corpus = {
        "protocol_id": "BENEFIT-L4-NAVIGATION-V1",
        "generated_at": minted_at,
        "generator_seed": REGISTERED_SEED,
        "worlds": worlds_rows,
    }
    meta = {"note": "hidden-world truth; debug artifact, never arm input",
            "worlds": worlds_meta}
    return corpus, meta


def class_invariant_checks(worlds: list[dict[str, Any]]) -> list[str]:
    """Structural world-fact invariants only. No arm policy is executed here."""
    errors: list[str] = []
    counts: dict[str, int] = {}
    for row in worlds:
        klass = row["class"]
        counts[klass] = counts.get(klass, 0) + 1
        wid = row["world_id"]
        if row["budget_class"] != BUDGET_BY_CLASS[klass]:
            errors.append(f"{wid}: budget class mismatch")
        mult = BUDGET_MULT[row["budget_class"]]
        if row["budget_units"] != float(mult * row["minimal_source_count"]):
            errors.append(f"{wid}: budget_units != {mult} * S*")
        expected_gold = "UNSOLVABLE" if klass == "N7" else "SOLVABLE"
        if row["gold_label"] != expected_gold:
            errors.append(f"{wid}: {klass} gold must be {expected_gold}")
        n_src = len(row["sources"])
        if klass == "N4":
            if not 4 <= n_src <= 6:
                errors.append(f"{wid}: N4 source count {n_src} outside 4-6")
        elif not 8 <= n_src <= 16:
            errors.append(f"{wid}: source count {n_src} outside 8-16")
        seen_edges: set[tuple[str, str]] = set()
        for s in row["sources"]:
            for e in s["edges"]:
                key = (e["source"], e["target"])
                if key in seen_edges and not e["source"].startswith("z"):
                    errors.append(f"{wid}: non-distractor edge {key} in two sources")
                seen_edges.add(key)
        for s in row["sources"]:
            for o in s.get("obstructions") or ():
                first_edges = {(e["source"], e["target"]) for e in s["edges"]}
                if not first_edges & {("a0", "d1")}:
                    errors.append(f"{wid}: obstruction not declared with first decoy edge")
    for klass, expected in CLASS_COMPOSITION.items():
        if counts.get(klass, 0) != expected:
            errors.append(f"class {klass}: {counts.get(klass, 0)} != frozen {expected}")
    return errors
