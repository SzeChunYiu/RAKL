#!/usr/bin/env python3
"""Probe G: is the natural-language surface of the six-family benchmark inert?

AUXILIARY_DIAGNOSTIC_ONLY. Not part of the frozen registration. Modifies nothing.

Paper II's confirmatory section states the full arm "computes its coordinates from
machine-readable target-world facts". This probe measures exactly how machine-readable
they are, and whether the benchmark contains any extraction problem at all.

Test 1 (text inertness): replace every `source_text` and `target_text` with random
noise, then recompute gold and every arm. If nothing changes, the natural-language
surface is decorative and the benchmark tests zero extraction capability.

Test 2 (coordinate directness): report, per family, the public-dict fields each
coordinate reads and whether the coordinate is a direct comparison/lookup of an
already-structured value rather than something inferred.
"""
from __future__ import annotations

import dataclasses
import json
import random
from pathlib import Path

from rakl.objective_transfer_benchmark import Decision
from rakl.objective_transfer_robustness import (
    FAMILIES,
    components,
    generate,
    lexical_score,
    mechanism_predict,
    relational_predict,
    verify,
)
from scripts.paper2_robustness_confirmatory import CONFIRMATORY_SEED, N_PER_CELL

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def _noise(rng: random.Random) -> str:
    words = ["zqx", "vpl", "mtr", "kbd", "wfn", "hgs", "yjc", "roa", "ludo", "esk"]
    return " ".join(rng.choice(words) for _ in range(6))


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rng = random.Random(20260814)
    tasks = generate(CONFIRMATORY_SEED, N_PER_CELL)

    scrambled = [
        dataclasses.replace(t, source_text=_noise(rng), target_text=_noise(rng)) for t in tasks
    ]

    gold_same = sum(verify(a) is verify(b) for a, b in zip(tasks, scrambled))
    comp_same = sum(components(a) == components(b) for a, b in zip(tasks, scrambled))
    mech_same = sum(mechanism_predict(a) is mechanism_predict(b) for a, b in zip(tasks, scrambled))
    rel_same = sum(relational_predict(a) is relational_predict(b) for a, b in zip(tasks, scrambled))
    lex_changed = sum(
        abs(lexical_score(a) - lexical_score(b)) > 1e-12 for a, b in zip(tasks, scrambled)
    )

    n = len(tasks)
    per_family_text_inert = {}
    for fam in FAMILIES:
        pairs = [(a, b) for a, b in zip(tasks, scrambled) if a.family == fam]
        per_family_text_inert[fam] = {
            "n": len(pairs),
            "gold_unchanged": sum(verify(a) is verify(b) for a, b in pairs),
            "components_unchanged": sum(components(a) == components(b) for a, b in pairs),
        }

    # Test 2: what the public dict actually contains for one item per family.
    public_shapes = {}
    for fam in FAMILIES:
        t = next(x for x in tasks if x.family == fam)
        public_shapes[fam] = {
            "public_keys": sorted(t.public.keys()),
            "public_sample": json.loads(json.dumps(t.public, default=str)),
            "gold": verify(t).value,
            "components": {
                k: getattr(components(t), k).value
                for k in ("qoi", "boundary", "direction", "relation", "precondition", "effect")
            },
        }

    report = {
        "schema": "paper2-six-family-audit-probe-g-v1",
        "status": "AUXILIARY_DIAGNOSTIC_ONLY__NOT_PART_OF_FROZEN_REGISTRATION",
        "grants_scientific_authority": False,
        "n": n,
        "text_inertness": {
            "gold_unchanged_after_text_scramble": f"{gold_same}/{n}",
            "components_unchanged_after_text_scramble": f"{comp_same}/{n}",
            "mechanism_arm_unchanged": f"{mech_same}/{n}",
            "relational_arm_unchanged": f"{rel_same}/{n}",
            "lexical_arm_changed": f"{lex_changed}/{n}",
            "natural_language_surface_is_inert": gold_same == n and comp_same == n,
        },
        "per_family_text_inertness": per_family_text_inert,
        "public_field_shapes": public_shapes,
        "interpretation": (
            "If gold and all six coordinates are unchanged when every source_text and "
            "target_text is replaced by noise, the natural-language surface carries no "
            "information used by any arm except the lexical diagnostic. The benchmark "
            "then contains no extraction problem: the applicability coordinates are read "
            "directly from pre-parsed structured fields in task.public. The 'which "
            "coordinates a fail-closed gate must enforce' result reduces to the "
            "observation that checking one of six independent conditions misses "
            "violations of the other five."
        ),
    }

    path = RESULTS / "PROBE_G_TEXT_INERTNESS.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report["text_inertness"], indent=2))
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
