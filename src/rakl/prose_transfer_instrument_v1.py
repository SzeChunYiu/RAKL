"""Paper II prose-transfer instrument v1 — a text-only structural transfer surface.

Frozen protocol: `research/paper2_prose_transfer_v1/PROTOCOL.json`.

Both refuted predecessors (`objective_transfer_robustness`,
`controlled_witness_extraction`) shipped a candidate-visible text surface while
carrying the answer alongside it in a pre-parsed sibling field, so no arm ever
read the text. This module removes the sibling field entirely.

Design commitments, all registered before this file existed:

* `ProseTask.public` is **empty**. The only candidate-visible content is
  `source_text` and `target_text`.
* Gold lives in a `LatentSpec` that no arm receives, and is a function of *what
  the text says*: a coordinate realized as hedged or elided is `CANNOT_CHECK`,
  because that is what a perfect reader of that text would conclude.
* The violated / unknown coordinate is **sampled**, not assigned per stratum,
  so no arm can be zeroed by construction (probe F repair).
* The paraphrase and degree-word banks are partitioned into disjoint `dev` and
  `heldout` halves. The extractor is developed against `dev`; the confirmatory
  runs on `heldout`. A lookup-table extractor cannot cover a disjoint degree
  lexicon — only a general rule can.

This is synthetic prose. It does not discharge the natural-domain
external-label residual and grants no scientific authority.
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from rakl.objective_transfer_benchmark import Decision

FAMILIES = (
    "linear_systems",
    "pgm_dseparation",
    "algorithm_invariants",
    "causal_transport",
    "optimization",
    "local_global_gluing",
)

COORDINATES = ("qoi", "boundary", "direction", "relation", "precondition", "effect")

ITEM_TYPES = ("VALID_TRANSFER", "SINGLE_VIOLATION", "MULTI_VIOLATION", "UNKNOWN_REQUIRED")

# Registered textual ambiguity classes (PROTOCOL.json).
MODE_LITERAL = "E_LITERAL"
MODE_QUALITATIVE = "E_QUALITATIVE"
MODE_UNIT = "E_UNIT"
MODE_NEGATION = "E_NEGATION"
MODE_HEDGE = "E_HEDGE"
MODE_ELISION = "E_ELISION"
MODE_DISTRACTOR = "E_DISTRACTOR"

UNKNOWN_MODES = (MODE_HEDGE, MODE_ELISION)

# Which realizations are available per coordinate. Categorical coordinates have
# no qualitative degree or unit conversion; numeric ones do.
_MODES_CATEGORICAL = (MODE_LITERAL, MODE_NEGATION, MODE_DISTRACTOR)
_MODES_BOOLEAN = (MODE_LITERAL, MODE_NEGATION, MODE_QUALITATIVE, MODE_DISTRACTOR)
_MODES_NUMERIC = (
    MODE_LITERAL,
    MODE_QUALITATIVE,
    MODE_UNIT,
    MODE_NEGATION,
    MODE_DISTRACTOR,
)

MODES_BY_COORDINATE: Mapping[str, Sequence[str]] = {
    "qoi": _MODES_CATEGORICAL,
    "boundary": _MODES_CATEGORICAL,
    "direction": _MODES_CATEGORICAL,
    "relation": _MODES_NUMERIC,
    "precondition": _MODES_BOOLEAN,
    "effect": _MODES_NUMERIC,
}


@dataclass(frozen=True)
class Vocab:
    quantity: str
    other_quantity: str
    qoi_match: str
    qoi_other: str
    regime_match: str
    regime_other: str
    precondition: str
    component: str
    source_noun: str
    target_noun: str


VOCAB: Mapping[str, Vocab] = {
    "linear_systems": Vocab(
        quantity="spectral radius",
        other_quantity="conditioning number",
        qoi_match="asymptotic stability",
        qoi_other="finite-horizon gain",
        regime_match="the discrete-time linear regime",
        regime_other="the continuous-time regime",
        precondition="time invariance of the coefficients",
        component="state components",
        source_noun="the reference system",
        target_noun="the deployed system",
    ),
    "pgm_dseparation": Vocab(
        quantity="residual dependence",
        other_quantity="edge density",
        qoi_match="conditional independence of the two marked variables",
        qoi_other="marginal association strength",
        regime_match="the acyclic directed regime",
        regime_other="the cyclic feedback regime",
        precondition="faithfulness of the graph to the distribution",
        component="conditioning variables",
        source_noun="the reference network",
        target_noun="the deployed network",
    ),
    "algorithm_invariants": Vocab(
        quantity="comparison count relative to the stated bound",
        other_quantity="memory footprint",
        qoi_match="worst-case lookup cost",
        qoi_other="average-case throughput",
        regime_match="the totally ordered key regime",
        regime_other="the partially ordered key regime",
        precondition="the sortedness invariant on the input",
        component="key positions",
        source_noun="the reference procedure",
        target_noun="the deployed procedure",
    ),
    "causal_transport": Vocab(
        quantity="selection discrepancy",
        other_quantity="sample attrition",
        qoi_match="the adjusted treatment effect",
        qoi_other="the observed outcome mean",
        regime_match="the shared-mechanism population",
        regime_other="the shifted-mechanism population",
        precondition="positivity of the treatment assignment",
        component="adjustment variables",
        source_noun="the reference population",
        target_noun="the deployed population",
    ),
    "optimization": Vocab(
        quantity="duality gap",
        other_quantity="iteration count",
        qoi_match="global optimality of the stationary point",
        qoi_other="local descent progress",
        regime_match="the convex feasible regime",
        regime_other="the nonconvex feasible regime",
        precondition="constraint qualification at the candidate point",
        component="active constraints",
        source_noun="the reference programme",
        target_noun="the deployed programme",
    ),
    "local_global_gluing": Vocab(
        quantity="overlap discrepancy",
        other_quantity="patch count",
        qoi_match="existence of a consistent global section",
        qoi_other="local solvability on each patch",
        regime_match="the pairwise-overlap regime",
        regime_other="the higher-order-overlap regime",
        precondition="compatibility of the restriction maps",
        component="overlap conditions",
        source_noun="the reference cover",
        target_noun="the deployed cover",
    ),
}


# ---------------------------------------------------------------------------
# Paraphrase / degree banks, partitioned into disjoint dev and heldout halves.
# The heldout qualitative lexicon shares no degree word or idiom with dev.
# ---------------------------------------------------------------------------

_QUAL_BELOW = {
    "dev": (
        "remains comfortably within the stated bound",
        "stays safely under the stated bound",
        "is well inside the stated bound",
    ),
    "heldout": (
        "never reaches the stated bound",
        "falls short of the stated bound",
        "sits beneath the stated bound throughout",
    ),
}

_QUAL_ABOVE = {
    "dev": (
        "rises clearly past the stated bound",
        "sits noticeably over the stated bound",
        "runs distinctly above the stated bound",
    ),
    "heldout": (
        "overshoots the stated bound",
        "ends up on the far side of the stated bound",
        "breaches the stated bound",
    ),
}

_QUAL_COMPLETE = {
    "dev": (
        "matches every required {component}",
        "leaves no required {component} unpaired",
    ),
    "heldout": (
        "accounts for the required {component} in full",
        "exhausts the required {component}",
    ),
}

_QUAL_INCOMPLETE = {
    "dev": (
        "leaves some required {component} unmatched",
        "omits part of the required {component}",
    ),
    "heldout": (
        "stops short of the required {component}",
        "covers the required {component} only in part",
    ),
}

_QUAL_PRECOND_HOLDS = {
    "dev": (
        "{precondition} holds across the operating range",
        "{precondition} is maintained throughout",
    ),
    "heldout": (
        "{precondition} is upheld at every operating point",
        "nothing in the operating range disturbs {precondition}",
    ),
}

_QUAL_PRECOND_FAILS = {
    "dev": (
        "{precondition} breaks down over part of the operating range",
        "{precondition} is lost at some operating points",
    ),
    "heldout": (
        "{precondition} gives way within the operating range",
        "{precondition} ceases to apply at part of the range",
    ),
}

_HEDGE = {
    "dev": (
        "was not assessed",
        "is not reported",
    ),
    "heldout": (
        "remains undetermined",
        "was left unexamined",
    ),
}

_DISTRACTOR_ROLE = {
    "dev": ("a preliminary bench model", "an early pilot build"),
    "heldout": ("a superseded prototype", "a discarded trial configuration"),
}

_FILLER = {
    "dev": (
        "Wall-clock cost for the reported run was {a} seconds.",
        "The {other_quantity} was logged at {b} for completeness.",
        "Data collection spanned {c} sessions.",
    ),
    "heldout": (
        "Instrumentation overhead accounted for {a} seconds of the run.",
        "For reference the {other_quantity} came out at {b}.",
        "The archive covers {c} recording sessions.",
    ),
}


def _bank(table: Mapping[str, Sequence[str]], bank: str) -> Sequence[str]:
    if bank not in table:
        raise ValueError(f"unknown bank {bank!r}")
    return table[bank]


@dataclass(frozen=True)
class CoordSpec:
    """Latent truth for one coordinate plus how the renderer expressed it."""

    value: bool
    mode: str

    @property
    def decision(self) -> Decision:
        """What a perfect reader of the rendered text should conclude."""
        if self.mode in UNKNOWN_MODES:
            return Decision.CANNOT_CHECK
        return Decision.ACCEPT if self.value else Decision.REJECT


@dataclass(frozen=True)
class LatentSpec:
    """Never exposed to any arm."""

    item_id: str
    family: str
    item_type: str
    bank: str
    coords: Mapping[str, CoordSpec]
    threshold: float
    target_value: float
    required_components: int
    covered_components: int

    @property
    def gold(self) -> Decision:
        return merge_decisions([self.coords[c].decision for c in COORDINATES])

    @property
    def sole_discriminator(self) -> str | None:
        """The single coordinate that determines a non-ACCEPT gold, if unique."""
        non_accept = [c for c in COORDINATES if self.coords[c].decision is not Decision.ACCEPT]
        return non_accept[0] if len(non_accept) == 1 else None


@dataclass(frozen=True)
class ProseTask:
    item_id: str
    family: str
    source_text: str
    target_text: str
    public: Mapping[str, Any]  # always empty; asserted in tests


def merge_decisions(values: Sequence[Decision]) -> Decision:
    if Decision.REJECT in values:
        return Decision.REJECT
    if Decision.CANNOT_CHECK in values:
        return Decision.CANNOT_CHECK
    return Decision.ACCEPT


def _item_id(seed: int, index: int) -> str:
    return "pt-" + hashlib.sha256(f"{seed}:{index}".encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _render_source(v: Vocab, spec: LatentSpec, rng: random.Random) -> str:
    sentences = [
        f"Working in {v.regime_match}, we establish {v.qoi_match} for {v.source_noun} "
        f"whenever the {v.quantity} stays below the stated bound of "
        f"{spec.threshold:.2f}.",
        f"The argument requires {v.precondition}.",
        f"Carrying the result to another setting requires a correspondence covering "
        f"all {spec.required_components} required {v.component}.",
    ]
    filler = _bank(_FILLER, spec.bank)
    sentences.append(
        rng.choice(filler).format(
            a=f"{rng.uniform(1.0, 90.0):.1f}",
            b=f"{rng.uniform(0.1, 9.0):.2f}",
            c=rng.randrange(3, 40),
            other_quantity=v.other_quantity,
        )
    )
    rng.shuffle(sentences)
    return " ".join(sentences)


def _sentence_qoi(v: Vocab, cs: CoordSpec, bank: str, rng: random.Random) -> str | None:
    name = v.qoi_match if cs.value else v.qoi_other
    if cs.mode == MODE_ELISION:
        return None
    if cs.mode == MODE_HEDGE:
        return f"Which quantity the present study targets {rng.choice(_bank(_HEDGE, bank))}."
    if cs.mode == MODE_NEGATION:
        other = v.qoi_other if cs.value else v.qoi_match
        return f"The present study does not ask about {other}; it asks about {name}."
    if cs.mode == MODE_DISTRACTOR:
        role = rng.choice(_bank(_DISTRACTOR_ROLE, bank))
        decoy = v.qoi_other if cs.value else v.qoi_match
        return (
            f"In {role} the question posed was {decoy}; the present study asks about {name}."
        )
    return f"The present study asks about {name}."


def _sentence_boundary(v: Vocab, cs: CoordSpec, bank: str, rng: random.Random) -> str | None:
    name = v.regime_match if cs.value else v.regime_other
    if cs.mode == MODE_ELISION:
        return None
    if cs.mode == MODE_HEDGE:
        return f"The operating regime of {v.target_noun} {rng.choice(_bank(_HEDGE, bank))}."
    if cs.mode == MODE_NEGATION:
        other = v.regime_other if cs.value else v.regime_match
        return f"{v.target_noun.capitalize()} does not operate in {other}; it operates in {name}."
    if cs.mode == MODE_DISTRACTOR:
        role = rng.choice(_bank(_DISTRACTOR_ROLE, bank))
        decoy = v.regime_other if cs.value else v.regime_match
        return (
            f"{role.capitalize()} operated in {decoy}; {v.target_noun} operates in {name}."
        )
    return f"{v.target_noun.capitalize()} operates in {name}."


def _sentence_direction(v: Vocab, cs: CoordSpec, bank: str, rng: random.Random) -> str | None:
    fwd = f"from {v.source_noun} to {v.target_noun}"
    bwd = f"from {v.target_noun} to {v.source_noun}"
    used, unused = (fwd, bwd) if cs.value else (bwd, fwd)
    if cs.mode == MODE_ELISION:
        return None
    if cs.mode == MODE_HEDGE:
        return f"The orientation of the correspondence {rng.choice(_bank(_HEDGE, bank))}."
    if cs.mode == MODE_NEGATION:
        return f"The correspondence is not applied {unused}; it is applied {used}."
    if cs.mode == MODE_DISTRACTOR:
        role = rng.choice(_bank(_DISTRACTOR_ROLE, bank))
        return (
            f"In {role} the correspondence ran {unused}; the analysis reported here "
            f"applies it {used}."
        )
    return f"The correspondence is applied {used}."


def _sentence_relation(v: Vocab, cs: CoordSpec, spec: LatentSpec, rng: random.Random) -> str | None:
    bank = spec.bank
    k, m = spec.covered_components, spec.required_components
    if cs.mode == MODE_ELISION:
        return None
    if cs.mode == MODE_HEDGE:
        return f"The completeness of the correspondence {rng.choice(_bank(_HEDGE, bank))}."
    if cs.mode == MODE_QUALITATIVE:
        table = _QUAL_COMPLETE if cs.value else _QUAL_INCOMPLETE
        return f"The correspondence {rng.choice(_bank(table, bank)).format(component=v.component)}."
    if cs.mode == MODE_UNIT:
        return (
            f"The correspondence matches {100.0 * k / m:.0f}% of the required "
            f"{v.component}."
        )
    if cs.mode == MODE_NEGATION:
        if cs.value:
            return f"No required {v.component} is left unmatched by the correspondence."
        return f"Not all required {v.component} are matched by the correspondence."
    if cs.mode == MODE_DISTRACTOR:
        role = rng.choice(_bank(_DISTRACTOR_ROLE, bank))
        decoy = m - k if k != m else max(0, m - 1)
        return (
            f"The mapping used in {role} covered {decoy} of the {m} required "
            f"{v.component}; the registered correspondence covers {k} of {m}."
        )
    return f"The correspondence covers {k} of the {m} required {v.component}."


def _sentence_precondition(v: Vocab, cs: CoordSpec, bank: str, rng: random.Random) -> str | None:
    if cs.mode == MODE_ELISION:
        return None
    if cs.mode == MODE_HEDGE:
        return (
            f"Whether {v.precondition} holds for {v.target_noun} "
            f"{rng.choice(_bank(_HEDGE, bank))}."
        )
    if cs.mode == MODE_QUALITATIVE:
        table = _QUAL_PRECOND_HOLDS if cs.value else _QUAL_PRECOND_FAILS
        text = rng.choice(_bank(table, bank)).format(precondition=v.precondition)
        return f"For {v.target_noun}, {text}."
    if cs.mode == MODE_NEGATION:
        if cs.value:
            return f"{v.target_noun.capitalize()} does not violate {v.precondition}."
        return f"{v.target_noun.capitalize()} does not satisfy {v.precondition}."
    if cs.mode == MODE_DISTRACTOR:
        role = rng.choice(_bank(_DISTRACTOR_ROLE, bank))
        decoy = "violated" if cs.value else "satisfied"
        verb = "satisfies" if cs.value else "violates"
        return (
            f"In {role} {v.precondition} was {decoy}; {v.target_noun} {verb} "
            f"{v.precondition}."
        )
    verb = "satisfies" if cs.value else "violates"
    return f"{v.target_noun.capitalize()} {verb} {v.precondition}."


def _sentence_effect(v: Vocab, cs: CoordSpec, spec: LatentSpec, rng: random.Random) -> str | None:
    bank = spec.bank
    val, thr = spec.target_value, spec.threshold
    if cs.mode == MODE_ELISION:
        return None
    if cs.mode == MODE_HEDGE:
        return (
            f"The {v.quantity} of {v.target_noun} {rng.choice(_bank(_HEDGE, bank))} "
            f"in this regime."
        )
    if cs.mode == MODE_QUALITATIVE:
        table = _QUAL_BELOW if cs.value else _QUAL_ABOVE
        return f"The {v.quantity} of {v.target_noun} {rng.choice(_bank(table, bank))}."
    if cs.mode == MODE_UNIT:
        return (
            f"The {v.quantity} of {v.target_noun} reaches {100.0 * val / thr:.1f}% "
            f"of the stated bound."
        )
    if cs.mode == MODE_NEGATION:
        if cs.value:
            return (
                f"There is no indication that the {v.quantity} of {v.target_noun} "
                f"exceeded the stated bound."
            )
        return (
            f"We found no evidence that the {v.quantity} of {v.target_noun} fell "
            f"below the stated bound."
        )
    if cs.mode == MODE_DISTRACTOR:
        role = rng.choice(_bank(_DISTRACTOR_ROLE, bank))
        decoy = thr * (1.6 if cs.value else 0.4)
        return (
            f"{role.capitalize()} recorded a {v.quantity} of {decoy:.2f}; "
            f"{v.target_noun} records {val:.2f}."
        )
    return f"The {v.quantity} of {v.target_noun} is {val:.2f}."


_RENDERERS = {
    "qoi": lambda v, cs, spec, rng: _sentence_qoi(v, cs, spec.bank, rng),
    "boundary": lambda v, cs, spec, rng: _sentence_boundary(v, cs, spec.bank, rng),
    "direction": lambda v, cs, spec, rng: _sentence_direction(v, cs, spec.bank, rng),
    "relation": _sentence_relation,
    "precondition": lambda v, cs, spec, rng: _sentence_precondition(v, cs, spec.bank, rng),
    "effect": _sentence_effect,
}


def _render_target(v: Vocab, spec: LatentSpec, rng: random.Random) -> str:
    sentences: list[str] = []
    for coord in COORDINATES:
        text = _RENDERERS[coord](v, spec.coords[coord], spec, rng)
        if text is not None:
            sentences.append(text)
    filler = _bank(_FILLER, spec.bank)
    sentences.append(
        rng.choice(filler).format(
            a=f"{rng.uniform(1.0, 90.0):.1f}",
            b=f"{rng.uniform(0.1, 9.0):.2f}",
            c=rng.randrange(3, 40),
            other_quantity=v.other_quantity,
        )
    )
    rng.shuffle(sentences)
    return " ".join(sentences)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def _draw_spec(
    seed: int, index: int, family: str, item_type: str, bank: str, rng: random.Random
) -> LatentSpec:
    values = {c: True for c in COORDINATES}
    modes: dict[str, str] = {}

    # probe-F repair: the discriminating coordinate is SAMPLED, never assigned
    # by stratum.
    if item_type == "SINGLE_VIOLATION":
        values[rng.choice(COORDINATES)] = False
    elif item_type == "MULTI_VIOLATION":
        for coord in rng.sample(list(COORDINATES), 2):
            values[coord] = False

    forced_unknown = rng.choice(COORDINATES) if item_type == "UNKNOWN_REQUIRED" else None
    for coord in COORDINATES:
        if coord == forced_unknown:
            modes[coord] = rng.choice(UNKNOWN_MODES)
        else:
            modes[coord] = rng.choice(MODES_BY_COORDINATE[coord])

    threshold = round(rng.uniform(0.80, 2.50), 2)
    if values["effect"]:
        target_value = round(rng.uniform(0.15, 0.95) * threshold, 4)
    else:
        target_value = round(rng.uniform(1.06, 1.90) * threshold, 4)

    required = rng.randrange(2, 6)
    covered = required if values["relation"] else rng.randrange(0, required)

    return LatentSpec(
        item_id=_item_id(seed, index),
        family=family,
        item_type=item_type,
        bank=bank,
        coords={c: CoordSpec(values[c], modes[c]) for c in COORDINATES},
        threshold=threshold,
        target_value=target_value,
        required_components=required,
        covered_components=covered,
    )


def generate(
    seed: int, n_per_cell: int = 24, bank: str = "heldout"
) -> tuple[list[ProseTask], list[LatentSpec]]:
    """Return (candidate-visible tasks, latent specs) in matching order."""
    if bank not in {"dev", "heldout"}:
        raise ValueError(f"unknown bank {bank!r}")
    rng = random.Random(seed)
    tasks: list[ProseTask] = []
    specs: list[LatentSpec] = []
    index = 0
    for family in FAMILIES:
        vocab = VOCAB[family]
        for item_type in ITEM_TYPES:
            for _ in range(n_per_cell):
                spec = _draw_spec(seed, index, family, item_type, bank, rng)
                task = ProseTask(
                    item_id=spec.item_id,
                    family=family,
                    source_text=_render_source(vocab, spec, rng),
                    target_text=_render_target(vocab, spec, rng),
                    public={},
                )
                tasks.append(task)
                specs.append(spec)
                index += 1
    order = list(range(len(tasks)))
    rng.shuffle(order)
    return [tasks[i] for i in order], [specs[i] for i in order]


def gold_decisions(specs: Sequence[LatentSpec]) -> list[Decision]:
    return [s.gold for s in specs]
