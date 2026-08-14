"""Known-answer hidden-world corpus generator for BENEFIT-L0-FCR-V1.

Implements the frozen procedure in ../../CORPUS_PLAN.md exactly:

- seeded parametric generator, single ``random.Random`` stream, no network;
- 8 synthetic domain families -> 8 hidden worlds (one per family; 50 pairs each);
- each world fixes an object, 2-4 facets, a value function over the seven
  standard context coordinates, and a declared set of load-bearing coordinates
  (the coordinates the value function actually depends on); every other
  coordinate is a distractor;
- class composition frozen in PROTOCOL.json: C1=90, C2=30, C3=120, C4=80, C5=80
  (N=400, gold contradictions = 120);
- gold labels are minted from the hidden world at generation time only;
- deterministic sentence templates with seeded lexical variation banks render
  surface_text_left/right; canonical value_* strings are what arm A compares;
- record schema: pair_id, class, gold_label, label_minted_at (UTC ISO, written
  at generation), machine fields, surface texts, world_id, generator_seed.

Degrees of freedom left open by CORPUS_PLAN.md are resolved here BEFORE any
result access and recorded in RUN_RECEIPT.md:
- exactly one world instance per registered family (the plan registers 8
  families; heavy within-world reuse of standard context tuples mirrors real
  corpora, where most reports share standard conditions);
- per world: 2 load-bearing coordinates, 2 values each (4-point value grid per
  facet, all values distinct by construction);
- unit conversions use exact integer decimal factors so C4 equivalence is exact.

Post-generation the module executes hostile known-answer class-invariant checks
over ALL rows (validate-the-checker-first discipline); any violation aborts.
"""
from __future__ import annotations

import random
import sys

from common import REGISTERED_SEED, utc_now_iso

COORDS = ("population", "scale", "horizon", "observation_model",
          "units", "assumptions", "intervention")
NON_UNIT_COORDS = tuple(c for c in COORDS if c != "units")

# 8 registered families (CORPUS_PLAN.md): object stem, facets, base-value range,
# base unit -> alt unit with exact multiplicative factor, and per-coordinate
# (default, variant) string banks. All parameterizations synthetic.
FAMILIES = [
    {
        "family": "material_hardness", "object": "alloy-AX3",
        "facets": ["vickers_hardness", "yield_strength", "grain_size"],
        "value_range": (120.0, 480.0), "units": ("HV", "dHV", 10),
        "banks": {
            "population": ("ingot-batch-A", "ingot-batch-B"),
            "scale": ("bulk-specimen", "thin-film"),
            "horizon": ("as-received", "aged-1000h"),
            "observation_model": ("indenter-K2", "indenter-K7"),
            "assumptions": ("annealed-state", "cold-worked-state"),
            "intervention": ("no-treatment", "quench-treated"),
        },
    },
    {
        "family": "dose_response", "object": "compound-QX4",
        "facets": ["ec50", "max_response", "onset_latency"],
        "value_range": (2.0, 95.0), "units": ("mg/L", "ug/L", 1000),
        "banks": {
            "population": ("adult-cohort", "juvenile-cohort"),
            "scale": ("organism-level", "cell-culture"),
            "horizon": ("24h-exposure", "96h-exposure"),
            "observation_model": ("assay-K", "assay-M"),
            "assumptions": ("fasting-condition", "fed-condition"),
            "intervention": ("single-dose", "repeat-dose"),
        },
    },
    {
        "family": "species_range", "object": "moth-VN7",
        "facets": ["range_area", "elevation_ceiling"],
        "value_range": (40.0, 900.0), "units": ("km2", "hm2", 100),
        "banks": {
            "population": ("northern-clade", "southern-clade"),
            "scale": ("regional-survey", "transect-survey"),
            "horizon": ("decade-2010s", "decade-2020s"),
            "observation_model": ("trap-grid", "acoustic-survey"),
            "assumptions": ("wet-season", "dry-season"),
            "intervention": ("undisturbed-habitat", "managed-habitat"),
        },
    },
    {
        "family": "order_book_depth", "object": "instrument-c17",
        "facets": ["top_depth", "spread_ticks", "refill_rate"],
        "value_range": (5.0, 320.0), "units": ("lots", "decilots", 10),
        "banks": {
            "population": ("session-eu", "session-us"),
            "scale": ("top-of-book", "five-levels"),
            "horizon": ("1min-window", "30min-window"),
            "observation_model": ("feed-L2", "feed-L3"),
            "assumptions": ("normal-volatility", "high-volatility"),
            "intervention": ("no-auction", "post-auction"),
        },
    },
    {
        "family": "thermal_conductivity", "object": "ceramic-TZ9",
        "facets": ["conductivity", "diffusivity"],
        "value_range": (1.5, 60.0), "units": ("W/mK", "mW/mmK", 1),
        "banks": {
            "population": ("sinter-lot-1", "sinter-lot-2"),
            "scale": ("pellet", "powder-bed"),
            "horizon": ("cycle-10", "cycle-500"),
            "observation_model": ("laser-flash", "hot-disk"),
            "assumptions": ("dry-atmosphere", "humid-atmosphere"),
            "intervention": ("undoped", "yttria-doped"),
        },
    },
    {
        "family": "incidence_rate", "object": "syndrome-RW2",
        "facets": ["incidence", "recurrence"],
        "value_range": (3.0, 85.0), "units": ("per-10k", "per-100k", 10),
        "banks": {
            "population": ("registry-north", "registry-south"),
            "scale": ("county-level", "clinic-level"),
            "horizon": ("year-1", "year-5"),
            "observation_model": ("passive-reporting", "active-screening"),
            "assumptions": ("baseline-exposure", "elevated-exposure"),
            "intervention": ("no-program", "screening-program"),
        },
    },
    {
        "family": "solubility", "object": "salt-KM5",
        "facets": ["solubility_limit", "dissolution_rate"],
        "value_range": (8.0, 240.0), "units": ("g/L", "mg/mL", 1),
        "banks": {
            "population": ("lot-P", "lot-Q"),
            "scale": ("beaker-scale", "reactor-scale"),
            "horizon": ("t-1h", "t-48h"),
            "observation_model": ("gravimetric", "conductometric"),
            "assumptions": ("ph-neutral", "ph-acidic"),
            "intervention": ("unstirred", "stirred-400rpm"),
        },
    },
    {
        "family": "stellar_luminosity", "object": "star-HQ11",
        "facets": ["luminosity", "variability_amplitude"],
        "value_range": (10.0, 700.0), "units": ("kL_sun", "hL_sun", 10),
        "banks": {
            "population": ("epoch-J2015", "epoch-J2025"),
            "scale": ("integrated-disk", "photosphere-band"),
            "horizon": ("90d-baseline", "900d-baseline"),
            "observation_model": ("space-photometer", "ground-photometer"),
            "assumptions": ("quiet-phase", "active-phase"),
            "intervention": ("no-dereddening", "dereddened"),
        },
    },
]

# Class quotas per world (worlds 0-5 then 6-7), frozen composition totals:
# C1=90, C2=30, C3=120, C4=80, C5=80.
QUOTAS_LOW = {"C1": 11, "C2": 4, "C3": 15, "C4": 10, "C5": 10}   # worlds 0..5
QUOTAS_HIGH = {"C1": 12, "C2": 3, "C3": 15, "C4": 10, "C5": 10}  # worlds 6..7

GOLD = {"C1": "CONTRADICTION", "C2": "CONTRADICTION",
        "C3": "CONTEXT_DEPENDENT_DIFFERENCE", "C4": "EQUIVALENT",
        "C5": "EQUIVALENT"}

TEMPLATES = [
    "{verb} for {obj}: the {facet} {reads} {value} [{ctx}].",
    "For {obj}, the {facet} {reads} {value} under the recorded conditions [{ctx}].",
    "The {facet} of {obj} {reads} {value}; conditions on record: [{ctx}].",
    "{obj} shows a {facet} of {value} ({verb_low}) [{ctx}].",
]
VERBS = ["Reported measurement", "Archived result", "Logged determination", "Filed observation"]
VERBS_LOW = ["as reported", "as archived", "as logged", "as filed"]
READS = ["is", "reads", "comes to", "stands at"]


def fmt_num(v: float) -> str:
    r = round(v, 1)
    return str(int(r)) if abs(r - int(r)) < 1e-9 else f"{r:.1f}"


def make_world(idx: int, rng: random.Random) -> dict:
    fam = FAMILIES[idx]
    n_facets = rng.randint(2, min(4, len(fam["facets"])))
    facets = fam["facets"][:n_facets]
    defaults = {c: fam["banks"][c][0] for c in NON_UNIT_COORDS}
    load_bearing = tuple(sorted(rng.sample(NON_UNIT_COORDS, 2)))
    base_unit, alt_unit, factor = fam["units"]
    values: dict[str, dict[tuple, float]] = {}
    for facet in facets:
        lo, hi = fam["value_range"]
        base = round(rng.uniform(lo, hi), 1)
        grid = {}
        for k, combo in enumerate([(0, 0), (0, 1), (1, 0), (1, 1)]):
            grid[combo] = round(base * (1.0 + 0.35 * k) + 0.1 * k, 1)
        assert len({fmt_num(v) for v in grid.values()}) == 4, "value grid must be distinct"
        values[facet] = grid
    return {
        "world_id": f"w{idx}:{fam['family']}", "object": fam["object"],
        "facets": facets, "defaults": defaults, "load_bearing": load_bearing,
        "banks": fam["banks"], "base_unit": base_unit, "alt_unit": alt_unit,
        "factor": factor, "values": values,
    }


def ctx_tuple(world: dict, combo: tuple[int, int], units: str) -> dict:
    ctx = {}
    lb = world["load_bearing"]
    for coord in NON_UNIT_COORDS:
        if coord in lb:
            bit = combo[lb.index(coord)]
            ctx[coord] = world["banks"][coord][bit]
        else:
            ctx[coord] = world["defaults"][coord]
    ctx["units"] = units
    return {c: ([ctx[c]] if c == "assumptions" else ctx[c]) for c in COORDS}


def ctx_desc(ctx: dict) -> str:
    parts = []
    for c in COORDS:
        v = ctx[c][0] if c == "assumptions" else ctx[c]
        parts.append(f"{c}: {v}")
    return "; ".join(parts)


def render(rng: random.Random, world: dict, facet: str, value: str, ctx: dict,
           forbid_template: int | None = None) -> tuple[str, int]:
    choices = [i for i in range(len(TEMPLATES)) if i != forbid_template]
    t = rng.choice(choices)
    text = TEMPLATES[t].format(
        verb=rng.choice(VERBS), verb_low=rng.choice(VERBS_LOW),
        reads=rng.choice(READS), obj=world["object"],
        facet=facet.replace("_", " "), value=value, ctx=ctx_desc(ctx),
    )
    return text, t


def corrupt(rng: random.Random, v: float) -> float:
    factor = rng.choice([0.6, 0.7, 1.4, 1.6, 1.8])
    c = round(v * factor, 1)
    if fmt_num(c) == fmt_num(v):
        c = round(v + 7.7, 1)
    return c


def gen_pair(rng: random.Random, world: dict, klass: str, minted_at: str) -> dict:
    facet = rng.choice(world["facets"])
    combo = (rng.randint(0, 1), rng.randint(0, 1))
    base_unit, alt_unit, factor = world["base_unit"], world["alt_unit"], world["factor"]
    v_true = world["values"][facet][combo]
    ctx_l = ctx_tuple(world, combo, base_unit)
    ctx_r = ctx_tuple(world, combo, base_unit)
    val_l = f"{fmt_num(v_true)} {base_unit}"
    val_r = val_l

    if klass in ("C1", "C2"):
        v_corr = corrupt(rng, v_true)
        corrupted_left = rng.random() < 0.5
        if corrupted_left:
            val_l = f"{fmt_num(v_corr)} {base_unit}"
        else:
            val_r = f"{fmt_num(v_corr)} {base_unit}"
        if klass == "C2":
            # Distractor: one NON-load-bearing, non-units coordinate differs
            # textually; the world declares the variant observationally
            # identical (rendered into the string so the audit can recover gold).
            distractors = [c for c in NON_UNIT_COORDS if c not in world["load_bearing"]]
            coord = rng.choice(distractors)
            default = world["defaults"][coord]
            variant = world["banks"][coord][1]
            marked = f"{variant} (certified equivalent to {default})"
            if coord == "assumptions":
                ctx_r["assumptions"] = [marked]
            else:
                ctx_r[coord] = marked
    elif klass == "C3":
        flip = rng.randint(0, 1)
        combo_r = tuple(b ^ (1 if i == flip else 0) for i, b in enumerate(combo))
        ctx_r = ctx_tuple(world, combo_r, base_unit)
        val_r = f"{fmt_num(world['values'][facet][combo_r])} {base_unit}"
    elif klass == "C4":
        ctx_r = ctx_tuple(world, combo, alt_unit)
        val_r = f"{fmt_num(v_true * factor)} {alt_unit}"
    # C5: byte-identical machine fields; only the surface realization differs.

    text_l, t_l = render(rng, world, facet, val_l, ctx_l)
    forbid = t_l if klass == "C5" else None
    text_r, _ = render(rng, world, facet, val_r, ctx_r, forbid_template=forbid)

    return {
        "class": klass, "gold_label": GOLD[klass], "label_minted_at": minted_at,
        "world_id": world["world_id"], "generator_seed": REGISTERED_SEED,
        "facet_left": facet, "facet_right": facet,
        "value_left": val_l, "value_right": val_r,
        "context_left": ctx_l, "context_right": ctx_r,
        "surface_text_left": text_l, "surface_text_right": text_r,
    }


def class_invariant_checks(pairs: list[dict]) -> list[str]:
    """Hostile known-answer checks over every generated row. Empty list = pass."""
    errors: list[str] = []
    counts: dict[str, int] = {}
    for row in pairs:
        k = row["class"]
        counts[k] = counts.get(k, 0) + 1
        cl, cr = row["context_left"], row["context_right"]
        diffs = [c for c in COORDS if cl[c] != cr[c]]
        vl, vr = row["value_left"], row["value_right"]
        pid = row["pair_id"]
        if row["facet_left"] != row["facet_right"]:
            errors.append(f"{pid}: facet mismatch within pair")
        if k == "C1" and (diffs or vl == vr):
            errors.append(f"{pid}: C1 must have identical contexts and differing values")
        if k == "C2":
            if len(diffs) != 1 or diffs[0] == "units" or vl == vr:
                errors.append(f"{pid}: C2 must differ in exactly one non-units distractor coord")
            elif "certified equivalent" not in str(cr[diffs[0]]):
                errors.append(f"{pid}: C2 distractor lacks the equivalence marker")
        if k == "C3" and (len(diffs) != 1 or vl == vr):
            errors.append(f"{pid}: C3 must differ in exactly one load-bearing coord with differing values")
        if k == "C4":
            if diffs != ["units"] or vl == vr:
                errors.append(f"{pid}: C4 must differ only in units")
            else:
                num_l = float(vl.split()[0])
                num_r = float(vr.split()[0])
                factor = next(f["units"][2] for f in FAMILIES if row["world_id"].endswith(f["family"]))
                if abs(num_l * factor - num_r) > 1e-6:
                    errors.append(f"{pid}: C4 conversion not exact ({num_l} x {factor} != {num_r})")
        if k == "C5":
            if diffs or vl != vr:
                errors.append(f"{pid}: C5 machine fields must be identical")
            if row["surface_text_left"] == row["surface_text_right"]:
                errors.append(f"{pid}: C5 surfaces must be paraphrases, not byte-equal")
    expected = {"C1": 90, "C2": 30, "C3": 120, "C4": 80, "C5": 80}
    if counts != expected:
        errors.append(f"class composition {counts} != frozen {expected}")
    return errors


def generate() -> tuple[dict, list[dict]]:
    rng = random.Random(REGISTERED_SEED)
    minted_at = utc_now_iso()
    worlds = [make_world(i, rng) for i in range(8)]
    rows: list[dict] = []
    for i, world in enumerate(worlds):
        quotas = QUOTAS_LOW if i < 6 else QUOTAS_HIGH
        for klass in ("C1", "C2", "C3", "C4", "C5"):
            for _ in range(quotas[klass]):
                rows.append(gen_pair(rng, world, klass, minted_at))
    rng.shuffle(rows)
    for i, row in enumerate(rows):
        row["pair_id"] = f"p{i:04d}"
    corpus = {
        "protocol_id": "BENEFIT-L0-FCR-V1",
        "generator_seed": REGISTERED_SEED,
        "generated_at": minted_at,
        "pairs": rows,
    }
    worlds_meta = {
        "note": "hidden-world truth (generator debug artifact; NOT arm input)",
        "worlds": [
            {k: (list(v) if isinstance(v, tuple) else v)
             for k, v in w.items() if k != "values"} |
            {"values": {f: {"|".join(map(str, c)): val for c, val in g.items()}
                        for f, g in w["values"].items()}}
            for w in worlds
        ],
    }
    return corpus, worlds_meta


if __name__ == "__main__":
    corpus, worlds_meta = generate()
    errors = class_invariant_checks(corpus["pairs"])
    if errors:
        for e in errors[:20]:
            print(f"INVARIANT FAIL: {e}", file=sys.stderr)
        sys.exit(2)
    print(f"generated {len(corpus['pairs'])} pairs; class invariants PASS")
