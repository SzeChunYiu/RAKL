"""Six-family extension of the Paper II objective transfer benchmark.

ADDITIVE ONLY. The four frozen families (flow / logic / units / state) and their
exact verifiers are imported unchanged from `rakl.objective_transfer_benchmark`;
nothing in that module is edited or mutated here. This module adds TWO new
exact-verifier families whose mathematical semantics differ structurally from the
frozen four:

  (5) ``sched``  precedence-constrained scheduling feasibility.
      A source plan (an ordering of source jobs) is transferred to a target world
      that declares its own precedence relation, durations, deadline, machine
      regime and QoI. The mapped ordering is licensed only if it is a permutation
      of the target jobs, respects EVERY declared target precedence edge, and the
      total non-preemptive processing time fits the declared deadline. This is an
      ORDER/CONSTRAINT-SATISFACTION semantics: no path, no closure, no dimension
      algebra, no transition system.

  (6) ``stat``   probabilistic/statistical scope transfer (base-rate / selection).
      A source population estimate (a posterior predictive value computed from a
      sensitivity/specificity/prevalence triple) is transferred to a target
      population that declares its own operating characteristics, base rate,
      sampling scheme and conditioning direction. The transfer is licensed only if
      the claimed number is re-derivable from the TARGET's own declared parameters
      under a sampling scheme that identifies the base rate. This is a NUMERIC
      IDENTIFICATION semantics: the hostile decoy is the classic base-rate
      fallacy, where every qualitative feature transfers and only the prior moves.

Gold is ALWAYS produced by executing the family verifier on the target-world
facts. No verifier branches on ``item_type``, on the near/far semantic label, or
on the hidden ``perturbation`` string.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Mapping, Sequence
import hashlib
import json
import math
import random
import statistics

import rakl.objective_transfer_benchmark as B
from rakl.objective_transfer_benchmark import (
    CONTROL_ITEM_TYPES,
    Decision,
    PRIMARY_ITEM_TYPES,
    Task,
    Verification,
    Witness,
    _merge_statuses,
    jaccard,
    lexical_predict,
    lexical_score,
)

FROZEN_FAMILIES = B.FAMILIES
NEW_FAMILIES = ("sched", "stat")
FAMILIES = FROZEN_FAMILIES + NEW_FAMILIES
ALL_ITEM_TYPES = PRIMARY_ITEM_TYPES + CONTROL_ITEM_TYPES

# Semantic-surface generators for the two new families, same shape as the frozen
# module's tables (near pairs share token counts; far pairs are cross-domain).
SEM_NEAR = dict(B.SEM_NEAR)
SEM_NEAR.update({
    "sched": ("factory job precedence order machine schedule",
              "workshop task precedence order machine schedule"),
    "stat": ("clinical screening test positive predictive population",
             "medical screening assay positive predictive population"),
})
SEM_FAR = dict(B.SEM_FAR)
SEM_FAR.update({
    "sched": ("factory job precedence order machine",
              "curriculum course prerequisite sequence term"),
    "stat": ("clinical screening test positive predictive",
             "warehouse sensor alarm flag audit"),
})


def _semantic_text(family: str, near: bool, rng: random.Random, salt: int) -> tuple[str, str]:
    """Byte-identical logic to the frozen generator, over the extended tables."""
    src, tgt = (SEM_NEAR if near else SEM_FAR)[family]
    shared = ["analysis", "transfer", "case"] if rng.random() < 0.5 else ["study", "candidate", "case"]
    src_extra = [f"s{salt % 17}", f"k{rng.randrange(11)}"]
    tgt_extra = [f"t{salt % 19}", f"k{rng.randrange(11)}"]
    return " ".join(src.split() + shared + src_extra), " ".join(tgt.split() + shared + tgt_extra)


def _id(seed: int, index: int) -> str:
    h = hashlib.sha256(f"{seed}:{index}".encode()).hexdigest()[:16]
    return f"obj-{h}"


# --------------------------------------------------------------------------- #
# Family 5: precedence-constrained scheduling feasibility
# --------------------------------------------------------------------------- #
SCHED_QOI = "precedence_feasible"
SCHED_REGIME = "single_machine_nonpreemptive"


def _sched_task(seed: int, index: int, item_type: str, near: bool, rng: random.Random) -> Task:
    jobs = ["j0", "j1", "j2", "j3"]
    durations = {j: 2 + ((index + k) % 4) for k, j in enumerate(jobs)}
    deadline = sum(durations.values()) + 2
    edges = [["j0", "j1"], ["j1", "j2"], ["j2", "j3"]]
    mapping = {"0": "j0", "1": "j1", "2": "j2", "3": "j3"}
    qoi, regime, perturb = SCHED_QOI, SCHED_REGIME, "none"

    if item_type == "SEMANTIC_NEAR_MISS_INVALID_TRANSFER":
        # HARD decoy: one declared target precedence edge points the other way.
        # Same number of constraints, same serialized length, target still admits
        # a perfectly feasible schedule -- only the CLAIMED order is now illegal,
        # so no mechanism-level property of the target world is disturbed.
        edges = [["j0", "j1"], ["j2", "j1"], ["j2", "j3"]]
        perturb = "precedence"
    elif item_type == "INVALID_DISTANT_CONTROL":
        # EASY invalid: the target world itself cannot meet its declared deadline.
        deadline = sum(durations.values()) - 1
        perturb = "deadline"
    elif item_type == "DIRECTION_REVERSED_INVALID":
        mapping = {"0": "j3", "1": "j2", "2": "j1", "3": "j0"}
        perturb = "direction"
    elif item_type == "BOUNDARY_QOI_MISMATCH":
        if index % 2:
            qoi = "precedence_optimal"
            perturb = "qoi"
        else:
            regime = "single_machine_preemptive"
            perturb = "boundary"
    elif item_type == "PARTIAL_MAPPING_REQUIRES_CANNOT_CHECK":
        if index % 2:
            mapping.pop("2")
            perturb = "mapping_missing"
        else:
            durations["j2"] = None
            perturb = "duration_unknown"

    stext, ttext = _semantic_text("sched", near, rng, index)
    public = {
        "source": {
            "jobs": [0, 1, 2, 3],
            "order": [0, 1, 2, 3],
            "precedence": [[0, 1], [1, 2], [2, 3]],
            "qoi": SCHED_QOI,
            "regime": SCHED_REGIME,
        },
        "target": {
            "jobs": jobs,
            "precedence": edges,
            "durations": durations,
            "deadline": deadline,
            "qoi": qoi,
            "regime": regime,
        },
        "mapping": mapping,
    }
    return Task(_id(seed, index), "sched", item_type, stext, ttext, public, perturb)


def verify_sched(t: Task) -> Verification:
    p = t.public
    src, tgt, mp = p["source"], p["target"], p["mapping"]
    if tgt["qoi"] != src["qoi"]:
        return Verification(Decision.REJECT, ("qoi_mismatch",))
    if tgt["regime"] != src["regime"]:
        return Verification(Decision.REJECT, ("boundary_mismatch",))
    if any(str(j) not in mp for j in src["order"]):
        return Verification(Decision.CANNOT_CHECK, ("mapping_incomplete",))
    claimed = [mp[str(j)] for j in src["order"]]
    if sorted(claimed) != sorted(tgt["jobs"]):
        return Verification(Decision.REJECT, ("schedule_not_a_permutation",))
    if any(u is None or v is None for u, v in tgt["precedence"]):
        return Verification(Decision.CANNOT_CHECK, ("precedence_unknown",))
    pos = {j: i for i, j in enumerate(claimed)}
    for u, v in tgt["precedence"]:
        if pos[u] >= pos[v]:
            return Verification(Decision.REJECT, (f"precedence_violated:{u}->{v}",))
    if any(tgt["durations"][j] is None for j in claimed):
        return Verification(Decision.CANNOT_CHECK, ("duration_unknown",))
    total = sum(tgt["durations"][j] for j in claimed)
    if total > tgt["deadline"]:
        return Verification(Decision.REJECT, (f"deadline_exceeded:{total}>{tgt['deadline']}",))
    return Verification(Decision.ACCEPT, (f"claimed_order_feasible:{total}<={tgt['deadline']}",))


def _sched_target_admits_some_feasible_order(tgt: Mapping[str, Any]) -> Decision:
    """Mechanism-level property of the TARGET WORLD only: does a feasible schedule
    exist at all? Deliberately blind to whether the CLAIMED (mapped) order is it."""
    if any(u is None or v is None for u, v in tgt["precedence"]):
        return Decision.CANNOT_CHECK
    if any(tgt["durations"][j] is None for j in tgt["jobs"]):
        return Decision.CANNOT_CHECK
    indeg = {j: 0 for j in tgt["jobs"]}
    for _, v in tgt["precedence"]:
        indeg[v] += 1
    ready = [j for j in tgt["jobs"] if indeg[j] == 0]
    seen = 0
    while ready:
        j = ready.pop()
        seen += 1
        for u, v in tgt["precedence"]:
            if u == j:
                indeg[v] -= 1
                if indeg[v] == 0:
                    ready.append(v)
    if seen != len(tgt["jobs"]):
        return Decision.REJECT
    total = sum(tgt["durations"][j] for j in tgt["jobs"])
    return Decision.ACCEPT if total <= tgt["deadline"] else Decision.REJECT


def extract_sched(t: Task, ablate=frozenset()) -> Witness:
    p = t.public
    src, tgt, mp = p["source"], p["target"], p["mapping"]
    obs: list[tuple[str, str]] = []
    sts: list[Decision] = []
    if "qoi" not in ablate:
        st = Decision.ACCEPT if tgt["qoi"] == src["qoi"] else Decision.REJECT
        obs.append(("qoi", st.value)); sts.append(st)
    if "boundary" not in ablate:
        st = Decision.ACCEPT if tgt["regime"] == src["regime"] else Decision.REJECT
        obs.append(("boundary", st.value)); sts.append(st)
    complete = all(str(j) in mp for j in src["order"])
    if "mapping" not in ablate:
        st = Decision.ACCEPT if complete else Decision.CANNOT_CHECK
        obs.append(("mapping", st.value)); sts.append(st)
    if complete:
        claimed = [mp[str(j)] for j in src["order"]]
        if "relations" not in ablate:
            if sorted(claimed) != sorted(tgt["jobs"]):
                st = Decision.REJECT
            elif any(u is None or v is None for u, v in tgt["precedence"]):
                st = Decision.CANNOT_CHECK
            else:
                pos = {j: i for i, j in enumerate(claimed)}
                st = (Decision.ACCEPT
                      if all(pos[u] < pos[v] for u, v in tgt["precedence"])
                      else Decision.REJECT)
            obs.append(("precedence_relations", st.value)); sts.append(st)
        if "precondition" not in ablate:
            if any(tgt["durations"][j] is None for j in tgt["jobs"]):
                st = Decision.CANNOT_CHECK
            else:
                total = sum(tgt["durations"][j] for j in tgt["jobs"])
                st = Decision.ACCEPT if total <= tgt["deadline"] else Decision.REJECT
            obs.append(("deadline_precondition", st.value)); sts.append(st)
    if "effect" not in ablate:
        st = _sched_target_admits_some_feasible_order(tgt)
        obs.append(("derived_feasibility_effect", st.value)); sts.append(st)
    return Witness(_merge_statuses(sts) if sts else Decision.CANNOT_CHECK,
                   tuple(obs), tuple(x for x, s in obs if s != "ACCEPT"))


# --------------------------------------------------------------------------- #
# Family 6: probabilistic / statistical scope transfer
# --------------------------------------------------------------------------- #
STAT_QOI = "posterior_predictive_value"
STAT_SAMPLING = "iid_random_sample"
STAT_CONDITIONING = "given_positive_test"
STAT_TOL = 1e-9


def _ppv(sens: float, spec: float, prev: float) -> float | None:
    denom = sens * prev + (1.0 - spec) * (1.0 - prev)
    if denom <= 0.0:
        return None
    return sens * prev / denom


def _stat_task(seed: int, index: int, item_type: str, near: bool, rng: random.Random) -> Task:
    sens = round(0.85 + 0.01 * (index % 10), 4)
    spec = round(0.80 + 0.01 * (index % 7), 4)
    prev = round(0.05 + 0.01 * (index % 5), 4)
    source_value = round(_ppv(sens, spec, prev), 10)

    t_sens, t_spec, t_prev = sens, spec, prev
    claimed = source_value
    qoi, sampling, conditioning = STAT_QOI, STAT_SAMPLING, STAT_CONDITIONING
    mapping = {"condition": "target_condition", "assay": "target_assay",
               "population": "target_population"}
    perturb = "none"

    if item_type == "SEMANTIC_NEAR_MISS_INVALID_TRANSFER":
        # HARD decoy: base-rate fallacy. Every operating characteristic transfers,
        # only the prior moves, and the source number is carried over unchanged.
        # The target's estimator is perfectly well-formed; only the scope moved.
        t_prev = round(prev / 10.0, 4)
        perturb = "base_rate"
    elif item_type == "INVALID_DISTANT_CONTROL":
        # EASY invalid: the declared target base rate is not a probability, so the
        # estimator mechanism itself is out of support in the target world.
        t_prev = round(1.0 + prev, 4)
        perturb = "out_of_support"
    elif item_type == "DIRECTION_REVERSED_INVALID":
        # The conditional is inverted: P(test+ | condition) reported as P(condition | test+).
        conditioning = "given_condition"
        claimed = sens
        perturb = "direction"
    elif item_type == "BOUNDARY_QOI_MISMATCH":
        if index % 2:
            qoi = "negative_predictive_value"
            perturb = "qoi"
        else:
            # Under case-control sampling the base rate is not identified from the
            # sample, so the source's population-level number does not transfer.
            sampling = "case_control_sample"
            perturb = "boundary"
    elif item_type == "PARTIAL_MAPPING_REQUIRES_CANNOT_CHECK":
        if index % 2:
            mapping.pop("population")
            perturb = "mapping_missing"
        else:
            t_prev = None
            perturb = "base_rate_unknown"

    stext, ttext = _semantic_text("stat", near, rng, index)
    public = {
        "source": {
            "sensitivity": sens, "specificity": spec, "prevalence": prev,
            "estimate": source_value, "qoi": STAT_QOI, "sampling": STAT_SAMPLING,
            "conditioning": STAT_CONDITIONING,
            "roles": ["condition", "assay", "population"],
        },
        "target": {
            "sensitivity": t_sens, "specificity": t_spec, "prevalence": t_prev,
            "claimed_value": claimed, "qoi": qoi, "sampling": sampling,
            "conditioning": conditioning,
        },
        "mapping": mapping,
    }
    return Task(_id(seed, index), "stat", item_type, stext, ttext, public, perturb)


def verify_stat(t: Task) -> Verification:
    p = t.public
    src, tgt, mp = p["source"], p["target"], p["mapping"]
    if tgt["qoi"] != src["qoi"]:
        return Verification(Decision.REJECT, ("qoi_mismatch",))
    if tgt["sampling"] != src["sampling"]:
        return Verification(Decision.REJECT, ("boundary_mismatch",))
    if any(role not in mp for role in src["roles"]):
        return Verification(Decision.CANNOT_CHECK, ("mapping_incomplete",))
    if tgt["conditioning"] != src["conditioning"]:
        return Verification(Decision.REJECT, ("conditioning_reversed",))
    if any(tgt[k] is None for k in ("sensitivity", "specificity", "prevalence", "claimed_value")):
        return Verification(Decision.CANNOT_CHECK, ("parameter_unknown",))
    if not all(0.0 <= tgt[k] <= 1.0 for k in ("sensitivity", "specificity", "prevalence", "claimed_value")):
        return Verification(Decision.REJECT, ("parameter_out_of_support",))
    derived = _ppv(tgt["sensitivity"], tgt["specificity"], tgt["prevalence"])
    if derived is None:
        return Verification(Decision.CANNOT_CHECK, ("degenerate_denominator",))
    ok = abs(tgt["claimed_value"] - derived) <= STAT_TOL
    return Verification(Decision.ACCEPT if ok else Decision.REJECT,
                        (f"target_derived_value:{derived:.10f}",))


def extract_stat(t: Task, ablate=frozenset()) -> Witness:
    p = t.public
    src, tgt, mp = p["source"], p["target"], p["mapping"]
    obs: list[tuple[str, str]] = []
    sts: list[Decision] = []
    if "qoi" not in ablate:
        st = Decision.ACCEPT if tgt["qoi"] == src["qoi"] else Decision.REJECT
        obs.append(("qoi", st.value)); sts.append(st)
    if "boundary" not in ablate:
        st = Decision.ACCEPT if tgt["sampling"] == src["sampling"] else Decision.REJECT
        obs.append(("boundary", st.value)); sts.append(st)
    complete = all(role in mp for role in src["roles"])
    if "mapping" not in ablate:
        st = Decision.ACCEPT if complete else Decision.CANNOT_CHECK
        obs.append(("mapping", st.value)); sts.append(st)
    if "relations" not in ablate:
        st = Decision.ACCEPT if tgt["conditioning"] == src["conditioning"] else Decision.REJECT
        obs.append(("conditioning_direction", st.value)); sts.append(st)
    if "precondition" not in ablate:
        # The load-bearing applicability precondition: the target base rate is
        # known AND equals the population the source estimate was computed in.
        if tgt["prevalence"] is None:
            st = Decision.CANNOT_CHECK
        else:
            st = Decision.ACCEPT if abs(tgt["prevalence"] - src["prevalence"]) <= STAT_TOL else Decision.REJECT
        obs.append(("base_rate_precondition", st.value)); sts.append(st)
    if "effect" not in ablate:
        # Mechanism-only projection: is the claimed number a coherent probability
        # produced by the same estimator mechanism? Blind to scope/base rate.
        keys = ("sensitivity", "specificity", "prevalence", "claimed_value")
        if any(tgt[k] is None for k in keys):
            st = Decision.CANNOT_CHECK
        elif not all(0.0 <= tgt[k] <= 1.0 for k in keys):
            st = Decision.REJECT
        else:
            st = Decision.ACCEPT
        obs.append(("derived_estimator_effect", st.value)); sts.append(st)
    return Witness(_merge_statuses(sts) if sts else Decision.CANNOT_CHECK,
                   tuple(obs), tuple(x for x, s in obs if s != "ACCEPT"))


# --------------------------------------------------------------------------- #
# Dispatch over all six families
# --------------------------------------------------------------------------- #
GEN = dict(B.GEN); GEN.update({"sched": _sched_task, "stat": _stat_task})
VER = dict(B.VER); VER.update({"sched": verify_sched, "stat": verify_stat})
EXT = dict(B.EXT); EXT.update({"sched": extract_sched, "stat": extract_stat})


def verify(t: Task) -> Verification:
    return VER[t.family](t)


def extract(t: Task, ablate=frozenset()) -> Witness:
    return EXT[t.family](t, ablate)


def generate(seed: int, n_per_cell: int = 20, include_controls: bool = True) -> list[Task]:
    """Same cell structure and RNG discipline as the frozen generator, over six
    families. For the four frozen families the emitted tasks are identical to
    `objective_transfer_benchmark.generate(seed, n_per_cell, include_controls)`."""
    rng = random.Random(seed)
    item_types = list(PRIMARY_ITEM_TYPES) + (list(CONTROL_ITEM_TYPES) if include_controls else [])
    tasks: list[Task] = []
    index = 0
    multipliers = {"VALID_DISTANT_TRANSFER": 2, "VALID_NEAR_CONTROL": 2}
    for fam in FAMILIES:
        for typ in item_types:
            count = n_per_cell * multipliers.get(typ, 1)
            for k in range(count):
                if typ == "SEMANTIC_NEAR_MISS_INVALID_TRANSFER":
                    near = True
                elif typ == "INVALID_DISTANT_CONTROL":
                    near = False
                elif typ == "VALID_NEAR_CONTROL":
                    near = True
                elif typ == "VALID_DISTANT_TRANSFER":
                    near = False
                else:
                    near = (k % 2 == 0)
                tasks.append(GEN[fam](seed, index, typ, near, rng))
                index += 1
    rng.shuffle(tasks)
    return tasks


MECHANISM_ALIGNMENT_ABLATION = B.MECHANISM_ALIGNMENT_ABLATION
RELATIONAL_BASELINE_ABLATION = B.RELATIONAL_BASELINE_ABLATION


def mechanism_predict(t: Task) -> Decision:
    return extract(t, MECHANISM_ALIGNMENT_ABLATION).decision


def relational_predict(t: Task) -> Decision:
    return extract(t, RELATIONAL_BASELINE_ABLATION).decision


def mutate_hidden_metadata(t: Task) -> Task:
    """Return a task whose hidden identity fields are fabricated. Gold must not move."""
    return Task(t.item_id, t.family, "FABRICATED_ITEM_TYPE", t.source_text,
                t.target_text, t.public, "fabricated-hidden-marker")


def fit_threshold(tasks: Sequence[Task], gold: Mapping[str, Decision]) -> float:
    return B.fit_threshold(tasks, gold)


def permutation_semantic_decorrelation(tasks: Sequence[Task], seed: int = 20260813,
                                       reps: int = 2000) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for j, fam in enumerate(FAMILIES):
        A = [lexical_score(t) for t in tasks if t.family == fam and verify(t).decision is Decision.ACCEPT]
        R = [lexical_score(t) for t in tasks if t.family == fam and verify(t).decision is Decision.REJECT]
        obs = abs(statistics.mean(A) - statistics.mean(R))
        vals = A + R
        n = len(A)
        rng = random.Random(seed + j)
        exceed = 0
        for _ in range(reps):
            arr = vals[:]
            rng.shuffle(arr)
            d = abs(statistics.mean(arr[:n]) - statistics.mean(arr[n:]))
            exceed += d >= obs - 1e-15
        out[fam] = {"accept_mean": statistics.mean(A), "reject_mean": statistics.mean(R),
                    "mean_diff": statistics.mean(A) - statistics.mean(R),
                    "permutation_p": (exceed + 1) / (reps + 1)}
    return out


def two_sided_sign_test(n_positive: int, n_negative: int, ties: int = 0) -> float:
    """Exact two-sided sign test. Ties are dropped (they carry no directional
    information), so `ties` is accepted only to document that they were removed.

    Six positive family signs out of six gives the registered target p = 0.03125;
    four out of four gives Paper II's stated p = 0.125.
    """
    n = n_positive + n_negative
    if n == 0:
        return 1.0
    k = max(n_positive, n_negative)
    tail = sum(math.comb(n, i) for i in range(k, n + 1)) / (2 ** n)
    return min(1.0, 2.0 * tail)


def surface_length_balance(tasks: Sequence[Task]) -> dict[str, dict[str, float]]:
    """Length-cheat audit: serialized candidate-visible payload length by gold class."""
    out: dict[str, dict[str, float]] = {}
    for fam in FAMILIES:
        rows = [(len(json.dumps(t.public, sort_keys=True)) + len(t.source_text) + len(t.target_text),
                 verify(t).decision) for t in tasks if t.family == fam]
        A = [n for n, g in rows if g is Decision.ACCEPT]
        R = [n for n, g in rows if g is Decision.REJECT]
        ma, mr = statistics.mean(A), statistics.mean(R)
        out[fam] = {"accept_mean_chars": ma, "reject_mean_chars": mr,
                    "abs_relative_gap": abs(ma - mr) / ((ma + mr) / 2)}
    return out


def gold_only_receipt(seed: int, n_per_cell: int) -> dict[str, Any]:
    """Dry run over gold + deterministic arms only. No model calls."""
    tasks = generate(seed, n_per_cell, True)
    gold = {t.item_id: verify(t).decision for t in tasks}
    threshold = B.fit_threshold(tasks, gold)
    per_family: dict[str, Any] = {}
    for fam in FAMILIES:
        sub = [t for t in tasks if t.family == fam]
        rej = [t for t in sub if gold[t.item_id] is Decision.REJECT]
        acc = [t for t in sub if gold[t.item_id] is Decision.ACCEPT]
        unk = [t for t in sub if gold[t.item_id] is Decision.CANNOT_CHECK]
        per_family[fam] = {
            "n": len(sub),
            "gold": dict(Counter(gold[t.item_id].value for t in sub)),
            "full_exact3": sum(extract(t).decision is gold[t.item_id] for t in sub) / len(sub),
            "mechanism_exact3": sum(mechanism_predict(t) is gold[t.item_id] for t in sub) / len(sub),
            "lexical_exact3": sum(lexical_predict(t, threshold) is gold[t.item_id] for t in sub) / len(sub),
            "full_false_accept": sum(extract(t).decision is Decision.ACCEPT for t in rej) / max(1, len(rej)),
            "mechanism_false_accept": sum(mechanism_predict(t) is Decision.ACCEPT for t in rej) / max(1, len(rej)),
            "full_valid_accept": sum(extract(t).decision is Decision.ACCEPT for t in acc) / max(1, len(acc)),
            "full_unknown_abstain": sum(extract(t).decision is Decision.CANNOT_CHECK for t in unk) / max(1, len(unk)),
        }
    return {
        "schema": "paper2-objective-six-family-goldonly-v1",
        "seed": seed, "n_per_cell": n_per_cell, "n": len(tasks),
        "families": list(FAMILIES),
        "lexical_threshold": threshold,
        "gold_counts": dict(Counter(g.value for g in gold.values())),
        "per_family": per_family,
        "semantic_decorrelation": permutation_semantic_decorrelation(tasks),
        "surface_length_balance": surface_length_balance(tasks),
        "public_packet_sha256": B.canonical_digest([B.public_record(t) for t in tasks]),
        "claim_boundary": "GOLD_ONLY_DRY_RUN__NO_MODEL_OUTPUT_ACCESSED",
        "grants_scientific_authority": False,
    }
