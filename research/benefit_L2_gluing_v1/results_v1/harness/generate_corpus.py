"""Seeded parametric known-answer corpus generator for BENEFIT-L2-GLUING-V1.

Implements CORPUS_PLAN.md exactly: covers of 3-6 charts over 3-6 binary
variables, N=400 in the frozen class composition (G1=100, G2=100, G3=60, G4=40,
G5=60, G6=40), gold = EXACT exhaustive satisfiability of the rendered constraint
tables computed at generation time (<= 6 binary variables). No network, no LLM,
no arm participates in labeling.

Twin structure: every G3 (k=3 parity) and G4 (k=4..6 parity) row is generated
together with its consistentCover-family G2 twin from the same template; twin
pairs share a byte-identical canonical pairwise record (transitions + overlap
restrictions) and differ only in constraint tables and cycle-holonomy facts —
the Lean ObstructionBlindness construction instantiated as data.

Template name sharing (design honesty note, resolved a priori before any freeze
or result access): surface identities (chart names, variable names) are drawn
from seeded per-TEMPLATE banks and shared by every row of that template cell,
rather than freshly permuted per row. This (a) removes class signal from names
(all classes in a cell share the same names) and (b) keeps the frozen
obstruction-permutation null's topology-signature strata populated and mixed —
the same reason the L1 corpus reused standard routes and the L0 corpus reused
standard context tuples. Per-row unique names would collapse every stratum to a
single row and degenerate the frozen null to all-zero draws.

Also provides class_invariant_checks(): a generator-validation pass (exact
satisfiability, pairwise honesty, holonomy honesty, twin byte-identity — all
recomputed from scratch, never via any arm rule) run BEFORE freeze.
"""
from __future__ import annotations

import itertools
import json
import random
from typing import Any

SEED = 20260814
N_BY_CLASS = {"G1": 100, "G2": 100, "G3": 60, "G4": 40, "G5": 60, "G6": 40}

_NAME_BANK = [
    "pressure", "salinity", "voltage", "torque", "albedo", "phase", "spin",
    "flux", "strain", "dopant", "yaw", "humidity", "charge", "gain", "drift",
    "parity", "count", "level", "mode", "state", "tilt", "bias", "width",
    "depth", "rate", "mass",
]
_CHART_BANK = [
    "north-survey", "south-survey", "east-survey", "west-survey", "core-probe",
    "rim-probe", "field-station", "lab-station", "orbit-pass", "ground-pass",
    "alpha-panel", "beta-panel", "gamma-panel", "delta-panel", "upper-deck",
    "lower-deck", "inner-loop", "outer-loop", "near-chart", "far-chart",
]


def _restriction(table: dict[str, Any], var: str) -> list[int]:
    """Projection of a chart's allowed table onto one shared variable."""
    idx = table["variables"].index(var)
    return sorted({row[idx] for row in table["allowed"]})


def _satisfiable(variables: list[str], constraint_tables: dict[str, Any]) -> bool:
    """Exact exhaustive global-section search (mirror of the frozen evaluator)."""
    tables = []
    for chart_id in sorted(constraint_tables):
        entry = constraint_tables[chart_id]
        tables.append((entry["variables"], {tuple(a) for a in entry["allowed"]}))
    for assignment in itertools.product([0, 1], repeat=len(variables)):
        values = dict(zip(variables, assignment))
        if all(tuple(values[v] for v in chart_vars) in allowed
               for chart_vars, allowed in tables):
            return True
    return False


def _parity_table(chart_vars: list[str], disagree: bool) -> dict[str, Any]:
    allowed = [[0, 1], [1, 0]] if disagree else [[0, 0], [1, 1]]
    return {"variables": list(chart_vars), "allowed": allowed}


class Template:
    """One structural cell: fixed chart names, variable names, overlap graph."""

    def __init__(self, tpl_id: str, kind: str, charts: list[str],
                 variables: list[str], edges: list[tuple[str, str, str]],
                 chart_vars: dict[str, list[str]],
                 cycle_path: list[str] | None):
        self.tpl_id = tpl_id
        self.kind = kind  # "cycle" | "tree"
        self.charts = charts
        self.variables = variables
        self.edges = edges  # (left_chart, right_chart, shared_var)
        self.chart_vars = chart_vars
        self.cycle_path = cycle_path


def _build_templates(rng: random.Random) -> tuple[list[Template], list[Template]]:
    names = _NAME_BANK[:]
    charts_bank = _CHART_BANK[:]
    rng.shuffle(names)
    rng.shuffle(charts_bank)
    name_iter = iter(names + [f"{n}-b" for n in names])
    chart_iter = iter(charts_bank + [f"{c}-2" for c in charts_bank]
                      + [f"{c}-3" for c in charts_bank])

    cyclic: list[Template] = []
    # 4 triangle templates (k=3) + one each of k=4,5,6.
    for tpl_num, k in enumerate([3, 3, 3, 3, 4, 5, 6]):
        variables = [next(name_iter) for _ in range(k)]
        charts = [next(chart_iter) for _ in range(k)]
        chart_vars = {charts[i]: [variables[i], variables[(i + 1) % k]]
                      for i in range(k)}
        edges = []
        for i in range(k):
            a, b = charts[i], charts[(i + 1) % k]
            shared = variables[(i + 1) % k]
            left, right = sorted((a, b))
            edges.append((left, right, shared))
        cycle_path = charts + [charts[0]]
        cyclic.append(Template(f"cyc{tpl_num}-k{k}", "cycle", charts, variables,
                               edges, chart_vars, cycle_path))

    trees: list[Template] = []
    # 4 acyclic PATH templates (n charts over n+1 variables, chart i holds
    # {v_i, v_{i+1}}): consecutive charts share exactly one variable and
    # non-consecutive charts share none, so the declared transition set is
    # exactly the variable-sharing structure (no undeclared overlaps).
    for tpl_num, n_charts in enumerate([3, 4, 5, 4]):
        n_vars = n_charts + 1
        variables = [next(name_iter) for _ in range(n_vars)]
        charts = [next(chart_iter) for _ in range(n_charts)]
        chart_vars = {charts[i]: [variables[i], variables[i + 1]]
                      for i in range(n_charts)}
        edges = []
        for i in range(n_charts - 1):
            left, right = sorted((charts[i], charts[i + 1]))
            edges.append((left, right, variables[i + 1]))
        trees.append(Template(f"tree{tpl_num}-c{n_charts}", "tree", charts,
                              variables, edges, chart_vars, None))
    return cyclic, trees


def _transitions(tpl: Template, constraint_tables: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for left, right, var in sorted(tpl.edges):
        r_left = _restriction(constraint_tables[left], var)
        r_right = _restriction(constraint_tables[right], var)
        out.append({
            "left_chart": left,
            "right_chart": right,
            "overlap_id": var,
            "pairwise_pass": bool(set(r_left) & set(r_right)),
            "fields_complete_pairwise": True,
            "overlap_restrictions": {left: r_left, right: r_right},
        })
    return out


def _cycle_tables(tpl: Template, parity_odd: bool,
                  rng: random.Random) -> dict[str, Any]:
    k = len(tpl.charts)
    n_disagree = rng.choice([x for x in range(0, k + 1)
                             if (x % 2 == 1) == parity_odd])
    which = set(rng.sample(range(k), n_disagree))
    return {
        tpl.charts[i]: _parity_table(tpl.chart_vars[tpl.charts[i]], i in which)
        for i in range(k)
    }


def _tree_tables(tpl: Template, rng: random.Random,
                 conflict_edge: tuple[str, str, str] | None) -> dict[str, Any]:
    """Satisfiable tree tables anchored on a hidden assignment; if conflict_edge
    is given, the two endpoint charts get disjoint restrictions on the shared
    variable (G5) making the cover globally unsatisfiable."""
    hidden = {v: rng.randint(0, 1) for v in tpl.variables}
    tables: dict[str, Any] = {}
    for chart in tpl.charts:
        cvars = tpl.chart_vars[chart]
        anchor = tuple(hidden[v] for v in cvars)
        rows = {anchor}
        for extra in itertools.product([0, 1], repeat=len(cvars)):
            if extra != anchor and rng.random() < 0.35:
                rows.add(extra)
        tables[chart] = {"variables": list(cvars),
                         "allowed": sorted([list(r) for r in rows])}
    if conflict_edge is not None:
        left, right, var = conflict_edge
        for chart, keep in ((left, 0), (right, 1)):
            cvars = tables[chart]["variables"]
            idx = cvars.index(var)
            rows = [r for r in tables[chart]["allowed"] if r[idx] == keep]
            if not rows:
                rows = [[keep if i == idx else 0 for i in range(len(cvars))]]
            tables[chart]["allowed"] = sorted(rows)
    return tables


def _render_surface(rng: random.Random, tpl: Template, klass: str,
                    tables: dict[str, Any], transitions: list[dict[str, Any]],
                    witness: dict[str, Any] | None, satisfiable: bool,
                    sat_assignment: dict[str, int] | None) -> str:
    lines = [
        f"Atlas of {len(tpl.charts)} local charts over binary quantities "
        + ", ".join(tpl.variables) + "."
    ]
    for chart in tpl.charts:
        t = tables[chart]
        rows = "; ".join("(" + ", ".join(f"{v}={a}" for v, a in zip(t["variables"], row)) + ")"
                         for row in t["allowed"])
        lines.append(f"Chart '{chart}' constrains ({', '.join(t['variables'])}); "
                     f"allowed assignments: {rows}.")
    for t in transitions:
        joint = sorted(set(t["overlap_restrictions"][t["left_chart"]])
                       & set(t["overlap_restrictions"][t["right_chart"]]))
        if joint:
            lines.append(f"Overlap on '{t['overlap_id']}' between '{t['left_chart']}' and "
                         f"'{t['right_chart']}': both charts admit {joint} — pairwise compatible.")
        else:
            lines.append(f"Overlap on '{t['overlap_id']}' between '{t['left_chart']}' and "
                         f"'{t['right_chart']}': the charts admit DISJOINT value sets "
                         "for the shared quantity — a genuine local conflict.")
    if witness is not None:
        path = " -> ".join(witness["chart_path"])
        if witness["composition_consistent"]:
            lines.append(f"Cycle {path}: composing the overlap identifications around the "
                         "loop returns every quantity to itself (holonomy consistent).")
        else:
            lines.append(f"Cycle {path}: composing the overlap identifications around the "
                         "loop FLIPS the starting quantity (odd parity); local agreements "
                         "cannot be realized simultaneously.")
        if not witness["evidence_ids"]:
            lines.append("RECORD GAP: the cycle witness's evidence references are missing "
                         "from the filed record; the holonomy fact above is nonetheless "
                         "genuine as stated.")
    if satisfiable and sat_assignment is not None:
        assign = ", ".join(f"{v}={sat_assignment[v]}" for v in tpl.variables)
        lines.append(f"Global fact: the assignment ({assign}) satisfies every chart "
                     "simultaneously — a global section exists.")
    elif satisfiable:
        lines.append("Global fact: some total assignment satisfies every chart "
                     "simultaneously — a global section exists.")
    else:
        lines.append("Global fact: NO total assignment of the quantities satisfies all "
                     "charts simultaneously — no global section exists.")
    return "\n".join(lines)


def _find_assignment(variables: list[str],
                     tables: dict[str, Any]) -> dict[str, int] | None:
    prepared = [(tables[c]["variables"], {tuple(a) for a in tables[c]["allowed"]})
                for c in sorted(tables)]
    for assignment in itertools.product([0, 1], repeat=len(variables)):
        values = dict(zip(variables, assignment))
        if all(tuple(values[v] for v in cv) in allowed for cv, allowed in prepared):
            return values
    return None


def generate() -> tuple[dict[str, Any], dict[str, Any]]:
    rng = random.Random(SEED)
    from common import utc_now_iso
    minted_at = utc_now_iso()
    cyclic, trees = _build_templates(rng)
    k3_templates = [t for t in cyclic if len(t.charts) == 3]
    k456_templates = [t for t in cyclic if len(t.charts) > 3]

    rows: list[dict[str, Any]] = []
    truths: list[dict[str, Any]] = []
    counter = 0

    def next_id() -> str:
        nonlocal counter
        aid = f"L2-{counter:04d}"
        counter += 1
        return aid

    def emit(tpl: Template, klass: str, tables: dict[str, Any],
             consistent: bool | None, witness_evidence: bool,
             twin_id: str | None, atlas_id: str) -> dict[str, Any]:
        transitions = _transitions(tpl, tables)
        sat = _satisfiable(tpl.variables, tables)
        witness = None
        witnesses = []
        if tpl.kind == "cycle":
            witness = {
                "cycle_id": f"cycle:{tpl.tpl_id}",
                "chart_path": list(tpl.cycle_path),
                "composition_consistent": consistent,
                "evidence_ids": [f"ev:{atlas_id}:cycle"] if witness_evidence else [],
            }
            witnesses = [witness]
        gold = "GLUEABLE" if sat else "NOT_GLUEABLE"
        sat_assignment = _find_assignment(tpl.variables, tables) if sat else None
        row = {
            "atlas_id": atlas_id,
            "class": klass,
            "gold_label": gold,
            "label_minted_at": minted_at,
            "charts": list(tpl.charts),
            "variables": list(tpl.variables),
            "transitions": transitions,
            "constraint_tables": tables,
            "cycle_witnesses": witnesses,
            "twin_id": twin_id,
            "surface_text": _render_surface(rng, tpl, klass, tables, transitions,
                                            witness, sat, sat_assignment),
            "world_id": tpl.tpl_id,
            "generator_seed": SEED,
        }
        rows.append(row)
        truths.append({
            "atlas_id": atlas_id, "class": klass, "template": tpl.tpl_id,
            "satisfiable": sat, "sat_assignment": sat_assignment,
            "holonomy_consistent": consistent,
        })
        return row

    # --- twinned parity families (G3/G4 with G2 twins) -----------------------
    for i in range(N_BY_CLASS["G3"]):
        tpl = k3_templates[i % len(k3_templates)]
        parity_id, twin_id = next_id(), next_id()
        emit(tpl, "G3", _cycle_tables(tpl, parity_odd=True, rng=rng),
             consistent=False, witness_evidence=True, twin_id=twin_id,
             atlas_id=parity_id)
        emit(tpl, "G2", _cycle_tables(tpl, parity_odd=False, rng=rng),
             consistent=True, witness_evidence=True, twin_id=None,
             atlas_id=twin_id)
    for i in range(N_BY_CLASS["G4"]):
        tpl = k456_templates[i % len(k456_templates)]
        parity_id, twin_id = next_id(), next_id()
        emit(tpl, "G4", _cycle_tables(tpl, parity_odd=True, rng=rng),
             consistent=False, witness_evidence=True, twin_id=twin_id,
             atlas_id=parity_id)
        emit(tpl, "G2", _cycle_tables(tpl, parity_odd=False, rng=rng),
             consistent=True, witness_evidence=True, twin_id=None,
             atlas_id=twin_id)

    # --- G6: glueable cyclic, obstruction record incomplete ------------------
    all_cyclic = k3_templates + k456_templates
    for i in range(N_BY_CLASS["G6"]):
        tpl = all_cyclic[i % len(all_cyclic)]
        emit(tpl, "G6", _cycle_tables(tpl, parity_odd=False, rng=rng),
             consistent=True, witness_evidence=False, twin_id=None,
             atlas_id=next_id())

    # --- G1: glueable trees; G5: pairwise-incompatible trees -----------------
    for i in range(N_BY_CLASS["G1"]):
        tpl = trees[i % len(trees)]
        emit(tpl, "G1", _tree_tables(tpl, rng, conflict_edge=None),
             consistent=None, witness_evidence=True, twin_id=None,
             atlas_id=next_id())
    for i in range(N_BY_CLASS["G5"]):
        tpl = trees[i % len(trees)]
        conflict = tpl.edges[rng.randrange(len(tpl.edges))]
        emit(tpl, "G5", _tree_tables(tpl, rng, conflict_edge=conflict),
             consistent=None, witness_evidence=True, twin_id=None,
             atlas_id=next_id())

    corpus = {
        "protocol_id": "BENEFIT-L2-GLUING-V1",
        "generated_at": minted_at,
        "generator_seed": SEED,
        "n_atlases": len(rows),
        "atlases": rows,
    }
    worlds_meta = {
        "note": "hidden-world truth dump; debug artifact, never arm input",
        "templates": [
            {"tpl_id": t.tpl_id, "kind": t.kind, "charts": t.charts,
             "variables": t.variables, "edges": [list(e) for e in t.edges]}
            for t in cyclic + trees
        ],
        "per_atlas_truth": truths,
    }
    return corpus, worlds_meta


# ---------------------------------------------------------------------------
# Generator validation: exact record-level class invariants recomputed from
# scratch. Never uses any arm rule; catches rendering/labeling defects BEFORE
# freeze (the CORPUS_PLAN rendering-faithfulness check).
# ---------------------------------------------------------------------------

def _pairwise_record(row: dict[str, Any]) -> str:
    record = sorted(
        (t["left_chart"], t["right_chart"], t["overlap_id"],
         bool(t["pairwise_pass"]), bool(t["fields_complete_pairwise"]),
         json.dumps(t.get("overlap_restrictions", None), sort_keys=True))
        for t in row["transitions"]
    )
    return json.dumps(record, sort_keys=True)


def _multigraph_cycles(charts: list[str], transitions: list[dict[str, Any]]) -> int:
    edges = sorted({(t["left_chart"], t["right_chart"], t["overlap_id"])
                    for t in transitions})
    parent = {c: c for c in charts}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b, _ in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    components = len({find(c) for c in charts})
    if components != 1:
        raise AssertionError("disconnected cover generated")
    return len(edges) - len(charts) + components


def class_invariant_checks(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    counts: dict[str, int] = {}
    by_id = {row["atlas_id"]: row for row in rows}
    for row in rows:
        klass = row["class"]
        counts[klass] = counts.get(klass, 0) + 1
        aid = row["atlas_id"]
        sat = _satisfiable(row["variables"], row["constraint_tables"])
        expected_gold = "GLUEABLE" if klass in ("G1", "G2", "G6") else "NOT_GLUEABLE"
        if row["gold_label"] != expected_gold:
            errors.append(f"{aid}: gold {row['gold_label']} != class-implied {expected_gold}")
        if sat != (row["gold_label"] == "GLUEABLE"):
            errors.append(f"{aid}: rendered-table satisfiability {sat} contradicts gold "
                          f"(rendering-faithfulness violation)")
        if not (3 <= len(row["charts"]) <= 6) or not (3 <= len(row["variables"]) <= 6):
            errors.append(f"{aid}: chart/variable count out of frozen range")
        # pairwise honesty: pass flag == non-disjoint projections
        for t in row["transitions"]:
            joint = set(t["overlap_restrictions"][t["left_chart"]]) \
                & set(t["overlap_restrictions"][t["right_chart"]])
            if bool(joint) != bool(t["pairwise_pass"]):
                errors.append(f"{aid}: pairwise_pass flag dishonest on {t['overlap_id']}")
            if t["fields_complete_pairwise"] is not True:
                errors.append(f"{aid}: fields_complete_pairwise must be True in this corpus")
        cycles = _multigraph_cycles(row["charts"], row["transitions"])
        witnesses = row["cycle_witnesses"]
        if cycles != len(witnesses):
            errors.append(f"{aid}: {cycles} cycles but {len(witnesses)} witnesses")
        for w in witnesses:
            # Witness path must be a SIMPLE closed cycle (each chart once, then
            # back to start; each edge traversed once). The repaired module's
            # GF(2) rank check is stricter than the frozen evaluator replica on
            # degenerate back-and-forth walks (module refuses, replica does
            # not); keeping every generated path simple keeps the two
            # decision-equivalent on the entire corpus. Found by the pre-freeze
            # fixture sweep; enforced here so the boundary case cannot enter.
            path = w["chart_path"]
            if path[0] != path[-1] or len(set(path[:-1])) != len(path) - 1 \
                    or len(path) < 4:
                errors.append(f"{aid}: witness path is not a simple closed cycle")
            cycle_charts = sorted(set(w["chart_path"]))
            sub = {c: row["constraint_tables"][c] for c in cycle_charts}
            sub_vars = sorted({v for c in cycle_charts
                               for v in row["constraint_tables"][c]["variables"]})
            sub_sat = _satisfiable(sub_vars, sub)
            if bool(w["composition_consistent"]) != sub_sat:
                errors.append(f"{aid}: holonomy flag dishonest (cycle sat={sub_sat})")
        n_evidence_gaps = sum(1 for w in witnesses if not w["evidence_ids"])
        n_pairwise_fails = sum(1 for t in row["transitions"]
                               if t["pairwise_pass"] is not True)
        if klass == "G1":
            if cycles != 0 or n_pairwise_fails or not sat:
                errors.append(f"{aid}: G1 must be an all-pass satisfiable tree")
        elif klass == "G2":
            if cycles != 1 or n_pairwise_fails or n_evidence_gaps or not sat:
                errors.append(f"{aid}: G2 must be an all-pass satisfiable single-cycle cover")
            if witnesses and witnesses[0]["composition_consistent"] is not True:
                errors.append(f"{aid}: G2 holonomy must be consistent")
        elif klass in ("G3", "G4"):
            if cycles != 1 or n_pairwise_fails or n_evidence_gaps or sat:
                errors.append(f"{aid}: parity row must be pairwise-clean, cyclic, unsat")
            if witnesses and witnesses[0]["composition_consistent"] is not False:
                errors.append(f"{aid}: parity holonomy must be inconsistent")
            for t in row["transitions"]:
                for chart, r in t["overlap_restrictions"].items():
                    if r != [0, 1]:
                        errors.append(f"{aid}: parity overlap restriction not total "
                                      "(parity_restrictions_are_total violated)")
            twin = row.get("twin_id")
            if not twin or twin not in by_id:
                errors.append(f"{aid}: parity row missing twin")
            else:
                other = by_id[twin]
                if other["gold_label"] != "GLUEABLE":
                    errors.append(f"{aid}: twin {twin} not GLUEABLE")
                if _pairwise_record(row) != _pairwise_record(other):
                    errors.append(f"{aid}: twin pairwise records differ")
                if other["world_id"] != row["world_id"]:
                    errors.append(f"{aid}: twin from different template")
            k = len(row["charts"])
            if klass == "G3" and k != 3:
                errors.append(f"{aid}: G3 must be k=3")
            if klass == "G4" and not (4 <= k <= 6):
                errors.append(f"{aid}: G4 must be k=4..6")
        elif klass == "G5":
            if n_pairwise_fails < 1 or sat:
                errors.append(f"{aid}: G5 must show a genuine pairwise conflict and be unsat")
        elif klass == "G6":
            if cycles != 1 or n_pairwise_fails or not sat:
                errors.append(f"{aid}: G6 must be an all-pass satisfiable cyclic cover")
            if n_evidence_gaps != 1:
                errors.append(f"{aid}: G6 must omit exactly one witness evidence entry")
    for klass, expected in N_BY_CLASS.items():
        if counts.get(klass, 0) != expected:
            errors.append(f"class {klass}: {counts.get(klass, 0)} rows != frozen {expected}")
    return errors
