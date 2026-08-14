"""CONGRUENCE-CONTEST-V1 evaluator. Frozen before any outcome was observed.

Arms: A = shipped StructureSpace (atomic); B1 = surface-congruence merge
(shape key, no witness); B2 = witnessed-congruence merge (fail-closed witness
check + query translation). Substrate: the real Lean dependency graph.

Run: PYTHONPATH=src python3.9 <this file> from the repo root.
Exit codes: 0 evaluated, 2 self-test failure, 3 CANNOT_CHECK.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

from rakl.analogy_retrieval import propose_analogies
from rakl.structure_space import (
    MatchVerdict,
    ProblemStructure,
    ReducedStructure,
    StructureSpace,
    match,
)
from rakl.support_solver import Atom, SupportStructure

REPO = Path(__file__).resolve().parents[3]
R_VARIANTS = 5
FLOOR = 0

# ------------------------------------------------------------- substrate

def lean_structures():
    source = (REPO / "formal" / "RaklFormal.lean").read_text(encoding="utf-8")
    heads = [(m.start(), m.group(1)) for m in
             re.finditer(r"^theorem\s+([A-Za-z_][A-Za-z0-9_.']*)", source, re.M)]
    names = [n for _, n in heads]
    out = []
    for idx, (start, name) in enumerate(heads):
        end = heads[idx + 1][0] if idx + 1 < len(heads) else len(source)
        body = source[start:end]
        deps = frozenset(o for o in names
                         if o != name and re.search(r"\b%s\b" % re.escape(o), body))
        if not deps:
            continue
        roles = deps | {name}
        out.append({
            "content_id": name,
            "roles": roles,
            "relations": frozenset((d, name) for d in deps),
            "root": name,
        })
    return out


def reduced(roles, relations, sid, authority=FLOOR):
    return ReducedStructure(
        structure=SupportStructure(
            structure_id=sid,
            atoms=tuple(Atom(atom_id=r) for r in sorted(roles)),
            edges=(),
        ),
        roles=frozenset(roles),
        relations=frozenset(relations),
        provenance="congruence-contest",
        established_at=authority,
    )


def make_variant(base, r):
    ren = {role: "v%d_%s" % (r, role) for role in sorted(base["roles"])}
    return {
        "content_id": base["content_id"],
        "roles": frozenset(ren.values()),
        "relations": frozenset((ren[a], ren[b]) for a, b in base["relations"]),
        "root": ren[base["root"]],
        "witness": ren,  # bijection base-role -> variant-role
    }


def shape_key(relations):
    outd, ind = {}, {}
    for s, t in relations:
        outd[s] = outd.get(s, 0) + 1
        ind[t] = ind.get(t, 0) + 1
    nodes = set(outd) | set(ind)
    return (len(relations), tuple(sorted((outd.get(n, 0), ind.get(n, 0)) for n in nodes)))

# ------------------------------------------------------------- arms

def run_arm_A(items):
    space = StructureSpace("contest-A")
    t0 = time.perf_counter()
    for i, it in enumerate(items):
        space.accumulate(reduced(it["roles"], it["relations"], "A::%d" % i))
    return space, time.perf_counter() - t0


def run_arm_B1(items):
    reps, merges = {}, []
    t0 = time.perf_counter()
    for it in items:
        key = shape_key(it["relations"])
        if key in reps:
            merges.append((reps[key]["content_id"], it["content_id"]))
        else:
            reps[key] = it
    dt = time.perf_counter() - t0
    space = StructureSpace("contest-B1")
    for i, it in enumerate(reps.values()):
        space.accumulate(reduced(it["roles"], it["relations"], "B1::%d" % i))
    false_merges = sum(1 for a, b in merges if a != b)
    return space, dt, merges, false_merges


def run_arm_B2(items):
    reps, witnesses, rejected = {}, {}, 0
    t0 = time.perf_counter()
    for it in items:
        cid = it["content_id"]
        if cid not in reps:
            reps[cid] = it
            continue
        wit = it.get("witness")
        rep = reps[cid]
        ok = False
        if wit is not None:
            mapped_roles = frozenset(wit.get(r) for r in rep["roles"])
            mapped_rels = frozenset((wit.get(a), wit.get(b)) for a, b in rep["relations"])
            ok = mapped_roles == it["roles"] and mapped_rels == it["relations"]
        if ok:
            witnesses[frozenset(it["roles"])] = (cid, {v: k for k, v in wit.items()})
        else:
            rejected += 1
            reps["%s#unwitnessed%d" % (cid, rejected)] = it  # fail-closed: kept separate
    dt = time.perf_counter() - t0
    space = StructureSpace("contest-B2")
    for i, it in enumerate(reps.values()):
        space.accumulate(reduced(it["roles"], it["relations"], "B2::%d" % i))
    return space, dt, witnesses, rejected

# ------------------------------------------------------------- queries

def jump_recall(space, bases):
    hits = 0
    for k, b in enumerate(bases):
        ren = {role: "q%d_%d" % (k, i) for i, role in enumerate(sorted(b["roles"]))}
        probe = ProblemStructure(
            problem_id="probe-%d" % k, qoi="shape",
            required_roles=frozenset(ren.values()),
            required_relations=frozenset((ren[a], ren[b2]) for a, b2 in b["relations"]),
            required_authority=FLOOR,
        )
        if propose_analogies(space, probe):
            hits += 1
    return hits / len(bases)


def role_recall(space, variants, witnesses=None):
    hits = 0
    for v in variants:
        target_roles = frozenset({v["root"]})
        if witnesses is not None:
            key = frozenset(v["roles"])
            if key in witnesses:
                _, back = witnesses[key]
                target_roles = frozenset(back.get(r, r) for r in target_roles)
        q = ProblemStructure(
            problem_id="rq", qoi="role", required_roles=target_roles,
            required_authority=FLOOR,
        )
        if any(m.verdict is MatchVerdict.LICENSED for m in match(space, q)):
            hits += 1
    return hits / len(variants)

# ------------------------------------------------------------- self-test

def selftest():
    a = {"content_id": "c1", "roles": frozenset({"x", "y"}),
         "relations": frozenset({("x", "y")}), "root": "y"}
    b = {"content_id": "c2", "roles": frozenset({"p", "q"}),
         "relations": frozenset({("p", "q")}), "root": "q"}
    va = make_variant(a, 1)
    _, _, merges, fm = run_arm_B1([a, b, va])
    assert fm == 1, "B1 must false-merge the two same-shape contents"
    assert len(merges) == 2, "B1 merge count"
    space2, _, wit, rej = run_arm_B2([a, b, va])
    assert rej == 0 and len(wit) == 1, "B2 witness admission"
    assert len(space2.structures) == 2, "B2 keeps one rep per content"
    assert role_recall(space2, [va], wit) == 1.0, "witness translation failed"
    bad = dict(va)
    bad["witness"] = {k: k for k in a["roles"]}  # wrong map
    _, _, _, rej2 = run_arm_B2([a, bad])
    assert rej2 == 1, "fail-closed witness check did not reject a bad witness"


def main():
    try:
        selftest()
    except AssertionError as exc:
        print("SELFTEST_FAIL: %s" % exc, file=sys.stderr)
        sys.exit(2)

    bases = lean_structures()
    if len(bases) < 20:
        print("CANNOT_CHECK: substrate too small (%d)" % len(bases), file=sys.stderr)
        sys.exit(3)
    star = sum(1 for b in bases
               if all(t == b["root"] for _, t in b["relations"]))

    # duplication exhibit (arm A, repeat-identical load)
    dup = StructureSpace("dup-exhibit")
    for i, b in enumerate(bases):
        dup.accumulate(reduced(b["roles"], b["relations"], "d1::%d" % i))
    first_pass_new = sum(dup.growth_per_round)
    for i, b in enumerate(bases):
        dup.accumulate(reduced(b["roles"], b["relations"], "d2::%d" % i))
    second_pass_new = sum(dup.growth_per_round[len(bases):])

    # variant load
    items = []
    for b in bases:
        items.append(dict(b))
        for r in range(1, R_VARIANTS + 1):
            items.append(make_variant(b, r))
    variants = [it for it in items if "witness" in it]

    sA, tA = run_arm_A(items)
    sB1, tB1, merges, false_merges = run_arm_B1(items)
    sB2, tB2, witnesses, rejected = run_arm_B2(items)

    tq0 = time.perf_counter()
    result = {
        "substrate": {"structures_with_deps": len(bases), "star_shaped": star,
                      "variant_load_items": len(items)},
        "duplication_exhibit": {
            "first_pass_new_roles": first_pass_new,
            "second_pass_new_roles": second_pass_new,
            "stored_structures_after_double_accumulate": len(dup.structures),
            "saturation": dup.saturation().name,
        },
        "storage": {"A": len(sA.structures), "B1": len(sB1.structures),
                    "B2": len(sB2.structures)},
        "accumulate_seconds": {"A": round(tA, 4), "B1": round(tB1, 4),
                               "B2": round(tB2, 4)},
        "B1_merges": {"total": len(merges), "false": false_merges,
                      "false_rate": (false_merges / len(merges)) if merges else None},
        "B2": {"witnessed_merges": len(witnesses), "rejected_witnesses": rejected},
        "jump_recall": {"A": jump_recall(sA, bases), "B1": jump_recall(sB1, bases),
                        "B2": jump_recall(sB2, bases)},
        "role_recall": {"A": role_recall(sA, variants),
                        "B1": role_recall(sB1, variants),
                        "B2": role_recall(sB2, variants, witnesses)},
        "grants_scientific_authority": False,
    }
    result["query_seconds_total"] = round(time.perf_counter() - tq0, 4)
    print(json.dumps(result, indent=1, sort_keys=True))
    sys.exit(0)


if __name__ == "__main__":
    main()
