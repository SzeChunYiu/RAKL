"""Seeded known-answer retrieval-stream generator for BENEFIT-L5-SATURATION-V1.

Implements CORPUS_PLAN.md exactly: hidden worlds first (finite relevant-fact
basis F* of 6-14 canonical fact ids, delivery schedule, distractor tail,
repeat/paraphrase items re-delivering seen canonical ids, truthful per-round
audit-gate facts), gold basis and t_complete minted at generation as pure
functions of the hidden world, T_MAX = 24 for every world, class composition
frozen in PROTOCOL.json (N=400: S1=140 S2=60 S3=60 S4=60 S5=40 S6=40).

Degrees of freedom in CORPUS_PLAN.md resolved a priori (before freeze, before
any result access), on corpus-quality grounds:
- `new_fact_ids` per round is the NEWLY RETAINED, deduplicated canonical ids
  (first arrivals only); repeat/paraphrase items are rendered in the round's
  `items` list with their canonical id but contribute nothing to
  `new_fact_ids` — collection is semantic (retained-new-after-dedup), which is
  what class S5 tests.
- Discovery genuinely closes at t_complete for S1/S2/S3/S5 (the round the
  route family is exhausted = the round the last basis fact arrives): all
  five gate facts are true and blocking fibers empty from t_complete onward,
  and truthfully mixed before (bounded_discovery_closed always false
  pre-closure; the other gates drawn per round).
- S4 trap: trap_start in 6..10, trap length 2-3 zero-growth rounds during
  which bounded_discovery_closed is GENUINELY false (unexhausted routes
  remain); rounds before the trap never contain 2 consecutive zero-growth
  rounds, so the trap is the FIRST flat window bare flat-counting can see;
  remaining basis facts arrive after the trap, t_complete in 13..18.
- S6: basis facts keep arriving through round 24 (last first-arrival in
  rounds 22..24) and bounded_discovery_closed is false in every round;
  t_complete = null.
- Pre-closure fact-bearing rounds carry other_substantive_updates=1 with
  probability 0.25 and a blocking fiber with probability 0.2 (truthful
  world-state renderings); zero-growth pre-closure rounds outside S4 traps
  are broken up so no accidental pre-closure flat+clean window exists (gates
  are false pre-closure anyway, making the full audit immune by
  construction; the constraint disciplines bare flat-counting's view).
- Distractor items (no canonical fact id) fill every round's item list at
  1-3 per round through T_MAX, so the post-closure tail is a genuine
  distractor tail with zero substantive growth.

No network. Single random.Random stream from the registered seed. Gold lives
in the hidden world; the surface_text renders the delivery schedule, closure
round and trap window so the label-independent audit can check gold from the
rendered description alone.
"""
from __future__ import annotations

import random
from typing import Any

from common import REGISTERED_SEED, utc_now_iso

N_WORLDS = 400
T_MAX = 24
CLASS_COMPOSITION = {
    "S1": 140, "S2": 60, "S3": 60, "S4": 60, "S5": 40, "S6": 40,
}
GATE_KEYS = (
    "bounded_discovery_closed", "route_coverage_stable", "omission_audit_passed",
    "nearest_work_audit_passed", "operator_order_stable",
)
FAMILIES = (
    "literature sweep", "sensor-log sweep", "registry crawl", "archive scan",
    "citation chase", "corpus diff", "protocol registry sweep", "materials index scan",
)


def _blank_round() -> dict[str, Any]:
    return {"new_fact_ids": [], "items": [], "other_substantive_updates": 0,
            "gates": {}, "blocking_fibers": []}


def _delivery_schedule(rng: random.Random, world_id: str, klass: str,
                       n_facts: int) -> tuple[list[list[str]], int | None, tuple[int, int] | None]:
    """Assign each basis fact a first-arrival round. Returns (per-round new fact
    lists, t_complete, trap window)."""
    facts = [f"{world_id}:f{j}" for j in range(n_facts)]
    per_round: list[list[str]] = [[] for _ in range(T_MAX)]
    trap = None
    if klass == "S1":
        t_complete = rng.randint(8, 16)
    elif klass == "S2":
        t_complete = rng.randint(3, 6)
    elif klass == "S3":
        t_complete = rng.randint(21, 23)
    elif klass == "S4":
        trap_start = rng.randint(6, 10)
        trap_len = rng.randint(2, 3)
        trap = (trap_start, trap_start + trap_len - 1)
        t_complete = rng.randint(13, 18)
    elif klass == "S5":
        t_complete = rng.randint(6, 12)
    else:  # S6
        t_complete = None

    if klass == "S6":
        last = rng.randint(22, 24)
        rounds_avail = list(range(1, last + 1))
    else:
        rounds_avail = list(range(1, t_complete + 1))
        if trap is not None:
            rounds_avail = [r for r in rounds_avail if not trap[0] <= r <= trap[1]]
        last = t_complete

    # the last basis fact arrives exactly at the completion (or last) round
    per_round[last - 1].append(facts[-1])
    remaining = facts[:-1]
    slots = [r for r in rounds_avail if r != last]
    for fact in remaining:
        r = rng.choice(slots)
        per_round[r - 1].append(fact)

    if klass == "S4":
        # no 2 consecutive zero-growth rounds before the trap: seed a fact into
        # any offending early round (basis is sized to afford this)
        for r in range(2, trap[0]):
            if not per_round[r - 1] and not per_round[r - 2]:
                donor = max((i for i in range(len(per_round))
                             if len(per_round[i]) > 1), default=None)
                if donor is not None:
                    per_round[r - 1].append(per_round[donor].pop())
        # the trap rounds themselves are zero growth by construction
        for r in range(trap[0], trap[1] + 1):
            assert not per_round[r - 1]
        # at least one fact strictly after the trap
        if not any(per_round[r - 1] for r in range(trap[1] + 1, t_complete + 1)):
            per_round[t_complete - 1].append(per_round[
                max(i for i in range(len(per_round)) if len(per_round[i]) > 1)].pop())
    return per_round, t_complete, trap


def _make_world(rng: random.Random, world_id: str, klass: str,
                minted_at: str) -> dict[str, Any]:
    family = rng.choice(FAMILIES)
    n_facts = rng.randint(8, 14) if klass in ("S4", "S6") else rng.randint(6, 14)
    per_round, t_complete, trap = _delivery_schedule(rng, world_id, klass, n_facts)
    closure = t_complete if klass != "S6" else None
    seen: list[str] = []
    rounds: list[dict[str, Any]] = []
    for r in range(1, T_MAX + 1):
        rnd = _blank_round()
        new = per_round[r - 1]
        rnd["new_fact_ids"] = list(new)
        items = [{"item_id": f"{world_id}:r{r}:i{k}", "kind": "fact",
                  "canonical_fact_id": fid} for k, fid in enumerate(new)]
        # repeats/paraphrases: post-completion for S5 (heavy), sparse elsewhere
        n_rep = 0
        if klass == "S5" and closure is not None and r > closure:
            n_rep = rng.randint(1, 3)
        elif seen and rng.random() < 0.2:
            n_rep = 1
        for k in range(n_rep):
            fid = rng.choice(seen) if seen else None
            if fid:
                items.append({"item_id": f"{world_id}:r{r}:p{k}", "kind": "repeat",
                              "canonical_fact_id": fid})
        for k in range(rng.randint(1, 3)):
            items.append({"item_id": f"{world_id}:r{r}:d{k}", "kind": "distractor",
                          "canonical_fact_id": None})
        rnd["items"] = items
        seen.extend(new)

        in_trap = trap is not None and trap[0] <= r <= trap[1]
        closed = closure is not None and r >= closure
        if closed:
            rnd["other_substantive_updates"] = 0
            rnd["gates"] = {k: True for k in GATE_KEYS}
            rnd["blocking_fibers"] = []
        else:
            # truthful pre-closure world state: discovery genuinely open
            if new and rng.random() < 0.25:
                rnd["other_substantive_updates"] = 1
            rnd["gates"] = {
                "bounded_discovery_closed": False,
                "route_coverage_stable": rng.random() < 0.6,
                "omission_audit_passed": rng.random() < 0.7,
                "nearest_work_audit_passed": rng.random() < 0.7,
                "operator_order_stable": rng.random() < 0.8,
            }
            rnd["blocking_fibers"] = (
                [f"fiber:{world_id}:{r}"] if rng.random() < 0.2 else [])
            if in_trap:
                # the trap is substantively flat; its world fact is that
                # bounded discovery is genuinely NOT closed
                rnd["other_substantive_updates"] = 0
        rounds.append(rnd)

    basis = [f"{world_id}:f{j}" for j in range(n_facts)]
    arrival = {}
    for r, rnd in enumerate(rounds, start=1):
        for fid in rnd["new_fact_ids"]:
            arrival[fid] = r
    surface = _render_surface(world_id, klass, family, basis, arrival,
                              t_complete, trap, closure)
    return {
        "world_id": world_id,
        "class": klass,
        "gold_basis": basis,
        "t_complete": t_complete,
        "label_minted_at": minted_at,
        "rounds": rounds,
        "surface_text": surface,
        "generator_seed": REGISTERED_SEED,
    }


def _render_surface(world_id: str, klass: str, family: str, basis: list[str],
                    arrival: dict[str, int], t_complete: int | None,
                    trap: tuple[int, int] | None, closure: int | None) -> str:
    sched = ", ".join(f"{fid.split(':')[-1]}@r{arrival[fid]}"
                      for fid in sorted(basis, key=lambda f: (arrival[f], f)))
    head = (f"Retrieval stream ({family}), 24 rounds. Relevant-fact basis of "
            f"{len(basis)} canonical facts; first arrivals: {sched}.")
    if klass == "S6":
        body = ("World facts: relevant facts keep arriving through the late "
                "rounds and bounded discovery NEVER genuinely closes (unexhausted "
                "routes remain at round 24); the basis is never certifiably "
                "exhausted. Completion round: none.")
    else:
        body = (f"World facts: the last basis fact arrives at round {t_complete}; "
                f"the declared route family is genuinely exhausted from round "
                f"{closure} onward (all audit gate facts true, no blocking "
                f"fibers); later rounds carry only distractors"
                + (" and paraphrase re-deliveries of already-seen facts"
                   if klass == "S5" else "") + ".")
        if trap is not None:
            body += (f" Rounds {trap[0]}-{trap[1]} are an interior zero-growth "
                     "window during which bounded discovery is GENUINELY still "
                     "open (unexhausted routes remain); basis facts resume "
                     "after it.")
    return f"{head} {body}"


def generate() -> tuple[dict[str, Any], dict[str, Any]]:
    rng = random.Random(REGISTERED_SEED)
    minted_at = utc_now_iso()
    class_list: list[str] = []
    for klass, count in sorted(CLASS_COMPOSITION.items()):
        class_list.extend([klass] * count)
    rng.shuffle(class_list)

    worlds = []
    meta = []
    for idx in range(N_WORLDS):
        world_id = f"w{idx:03d}"
        row = _make_world(rng, world_id, class_list[idx], minted_at)
        worlds.append(row)
        meta.append({"world_id": world_id, "class": row["class"],
                     "n_basis": len(row["gold_basis"]),
                     "t_complete": row["t_complete"]})
    corpus = {
        "protocol_id": "BENEFIT-L5-SATURATION-V1",
        "generated_at": minted_at,
        "generator_seed": REGISTERED_SEED,
        "t_max": T_MAX,
        "worlds": worlds,
    }
    return corpus, {"note": "hidden-world truth summary; never arm input",
                    "worlds": meta}


def class_invariant_checks(worlds: list[dict[str, Any]]) -> list[str]:
    """Structural world-fact invariants only. No arm rule is executed here."""
    errors: list[str] = []
    counts: dict[str, int] = {}
    for row in worlds:
        klass = row["class"]
        counts[klass] = counts.get(klass, 0) + 1
        wid = row["world_id"]
        if len(row["rounds"]) != T_MAX:
            errors.append(f"{wid}: round count != {T_MAX}")
            continue
        delivered: list[str] = []
        arrival: dict[str, int] = {}
        for r, rnd in enumerate(row["rounds"], start=1):
            for fid in rnd["new_fact_ids"]:
                if fid in arrival:
                    errors.append(f"{wid}: fact {fid} first-arrives twice")
                arrival[fid] = r
            delivered.extend(rnd["new_fact_ids"])
        if sorted(delivered) != sorted(row["gold_basis"]):
            errors.append(f"{wid}: delivered facts != gold basis")
        if not 6 <= len(row["gold_basis"]) <= 14:
            errors.append(f"{wid}: basis size outside 6-14")
        last_arrival = max(arrival.values()) if arrival else 0
        t_complete = row["t_complete"]
        if klass == "S6":
            if t_complete is not None:
                errors.append(f"{wid}: S6 must have t_complete null")
            if any(rnd["gates"]["bounded_discovery_closed"] for rnd in row["rounds"]):
                errors.append(f"{wid}: S6 must never close discovery")
            if last_arrival < 22:
                errors.append(f"{wid}: S6 facts must keep arriving late (last {last_arrival})")
        else:
            if t_complete != last_arrival:
                errors.append(f"{wid}: t_complete {t_complete} != last arrival {last_arrival}")
            for r, rnd in enumerate(row["rounds"], start=1):
                closed = rnd["gates"]["bounded_discovery_closed"]
                if r >= t_complete and not closed:
                    errors.append(f"{wid}: gate must be closed from t_complete")
                    break
                if r < t_complete and closed:
                    errors.append(f"{wid}: gate closed before t_complete")
                    break
        expect_range = {
            "S1": (8, 16), "S2": (3, 6), "S3": (21, 23), "S4": (13, 18),
            "S5": (6, 12),
        }
        if klass in expect_range and not (
                expect_range[klass][0] <= t_complete <= expect_range[klass][1]):
            errors.append(f"{wid}: {klass} t_complete {t_complete} outside range")
        if klass == "S4":
            flats = [r for r in range(1, t_complete)
                     if not row["rounds"][r - 1]["new_fact_ids"]
                     and row["rounds"][r - 1]["other_substantive_updates"] == 0]
            window = [r for r in flats if r + 1 in flats]
            if not window:
                errors.append(f"{wid}: S4 must contain an interior flat pair")
            else:
                for r in (window[0], window[0] + 1):
                    if row["rounds"][r - 1]["gates"]["bounded_discovery_closed"]:
                        errors.append(f"{wid}: S4 trap round {r} must be genuinely open")
            first_pair = window[0] if window else None
            if first_pair is not None:
                pre = [r for r in range(2, first_pair)
                       if not row["rounds"][r - 1]["new_fact_ids"]
                       and row["rounds"][r - 1]["other_substantive_updates"] == 0
                       and not row["rounds"][r - 2]["new_fact_ids"]
                       and row["rounds"][r - 2]["other_substantive_updates"] == 0]
                if pre:
                    errors.append(f"{wid}: S4 has a flat pair before the trap")
    for klass, expected in CLASS_COMPOSITION.items():
        if counts.get(klass, 0) != expected:
            errors.append(f"class {klass}: {counts.get(klass, 0)} != frozen {expected}")
    return errors
