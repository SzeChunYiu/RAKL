#!/usr/bin/env python3
"""Paper IV Phase-1 (#461) EXPOSURE EXECUTOR.

Honesty contract (read before editing):

* This executor emits ONLY what it measures. It NEVER hardcodes, mocks, or
  fabricates an accuracy or an outcome. Every accuracy in ``exposure_outcomes.jsonl``
  is the fraction of held-out probe cases the *actually trained* checkpoint labels
  correctly, with gold coming from :func:`orion.training_ladder.verify_case` (the
  executable semantics), never from perturbation identity or control kind.
* Any local ``--smoke`` run is a *pipeline* smoke, not a scientific result. Smoke
  rows and the manifest carry ``"smoke": true`` so they can never be mistaken for
  a Phase-1 result.
* Every output row is bound to the frozen packet ``protocol_subject_hash`` and the
  run refuses to start unless :func:`validate_protocol_freeze` passes.
* ``grants_scientific_authority`` is always ``false``. Training utility is not
  scientific authority. The forbidden claims in the packet are never asserted.

What each probe kind operationalises (given the frozen, deterministic generator):

  SAME_STRUCTURE      -> PRINCIPLE       held-out instances of the trained family
  NEW_COMPOSITION     -> COMPOSITION     held-out instances at a disjoint offset band
                                         (distinct composition tags never trained on)
  NEW_BOUNDARY        -> BOUNDARY        held-out instances rendered with an alternate
                                         declared boundary regime
  NEW_REPRESENTATION  -> REPRESENTATION  held-out instances rendered in an alternate
                                         surface layout of the same facts
  NEW_DOMAIN          -> TRANSFER        held-out instances of the *other* families
  HOSTILE_NEAR_MISS   -> RETENTION       semantic near-decoys from the hostile suite

The frozen family generator varies composition and surface within a family but
fixes the boundary/representation *semantics* (gold is always payload-determined).
Whether the six probe accuracies constitute six independent mastery axes is NOT
asserted here; that is exactly what the INSTRUMENT_OR_GENERATOR_DEFECT terminal
(coordinate-ablated twin classifier matching the full classifier) is designed to
catch, and what the paper must adjudicate.

Heavy deep-learning dependencies (torch/transformers/peft) are imported lazily
inside the training/evaluation functions so this module (and its tests) import
without them installed.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from orion.training_ladder import (  # noqa: E402
    ExposureProbeKind,
    FamilyId,
    GoldLabel,
    TrainingCase,
    build_hostile_control_suite,
    generate_family_cases,
    validate_protocol_freeze,
    verify_case,
)
from orion.training_ladder.families import FAMILY_BUILDERS  # noqa: E402
from orion.training_ladder.types import ControlKind, StructuralCoordinate  # noqa: E402
from orion.training_projection import MasteryCoordinate  # noqa: E402

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

DEFAULT_PACKET_DIR = ROOT / "research" / "paper4_training_ladder_461"
DEFAULT_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
FROZEN_SEED = 461  # bound to the frozen issue id; single deterministic seed for the run.

# Bijection probe_kind -> mastery coordinate. Documented in the module docstring.
PROBE_TO_COORDINATE: dict[ExposureProbeKind, MasteryCoordinate] = {
    ExposureProbeKind.SAME_STRUCTURE: MasteryCoordinate.PRINCIPLE,
    ExposureProbeKind.NEW_COMPOSITION: MasteryCoordinate.COMPOSITION,
    ExposureProbeKind.NEW_BOUNDARY: MasteryCoordinate.BOUNDARY,
    ExposureProbeKind.NEW_REPRESENTATION: MasteryCoordinate.REPRESENTATION,
    ExposureProbeKind.NEW_DOMAIN: MasteryCoordinate.TRANSFER,
    ExposureProbeKind.HOSTILE_NEAR_MISS: MasteryCoordinate.RETENTION,
}

# Registered exposure ladder (mirrors the frozen packet; re-checked at load time).
REGISTERED_EXPOSURE_COUNTS: tuple[int, ...] = (1, 2, 4, 8, 16, 32, 64)

# Never-assert list (mirrors packet forbidden_claims; re-checked against packet).
FORBIDDEN_CLAIMS: tuple[str, ...] = (
    "adaptive_training_effective",
    "static_beats_adaptive",
    "training_cost_reduction",
    "paper_vi_licensed",
    "scientific_authority_from_mastery",
)

OUTCOME_FIELDS: tuple[str, ...] = (
    "family",
    "exposure_count",
    "probe_kind",
    "coordinate",
    "accuracy",
    "n",
    "checkpoint_hash",
    "marginal_gain",
    "prev_exposure_count",
    "protocol_subject_hash",
    "smoke",
)

# Classifier thresholds (operational instrument settings, not scientific claims).
DEFAULT_FLOOR_ACCURACY = 0.60      # binary task; chance is 0.5.
DEFAULT_MASTERY_THRESHOLD = 0.90   # SAME_STRUCTURE accuracy that counts as principle mastered.
DEFAULT_GAIN_FLOOR = 0.02          # marginal-gain epsilon below which repetition "stops paying".
DEFAULT_ABLATION_EPS = 0.03        # full-vs-ablated gap at/below which the probe is non-discriminating.
CHANCE = 0.5


class ProtocolFreezeError(RuntimeError):
    """Raised when the frozen packet fails re-validation; the run must not start."""


# --------------------------------------------------------------------------- #
# Packet loading / re-validation gate
# --------------------------------------------------------------------------- #


def load_frozen_packet(packet_dir: Path) -> tuple[dict, str]:
    """Re-validate the frozen packet and return ``(packet, protocol_subject_hash)``.

    Refuses (raises :class:`ProtocolFreezeError`) unless
    :func:`validate_protocol_freeze` returns ``PROTOCOL_FREEZE_PASS``. This is the
    single gate that binds every emitted row to the frozen protocol.
    """

    validation = validate_protocol_freeze(packet_dir)
    if validation.verdict != "PROTOCOL_FREEZE_PASS":
        raise ProtocolFreezeError(
            f"protocol freeze re-validation failed: {validation.verdict} "
            f"reasons={list(validation.reasons)}"
        )
    packet = json.loads((packet_dir / "PROTOCOL_FREEZE_PACKET.json").read_text(encoding="utf-8"))

    # Guardrails: the executor must honour the frozen exposure ladder and never
    # run against a packet that already grants authority or claims a result.
    counts = tuple(packet["exposure_curve_harness"]["exposure_counts"])
    if counts != REGISTERED_EXPOSURE_COUNTS:
        raise ProtocolFreezeError(
            f"packet exposure ladder {counts} != registered {REGISTERED_EXPOSURE_COUNTS}"
        )
    if packet.get("grants_scientific_authority") is not False:
        raise ProtocolFreezeError("packet must not grant scientific authority")
    if packet.get("scientific_claim_status") != "NO_EMPIRICAL_RESULT":
        raise ProtocolFreezeError("packet must carry NO_EMPIRICAL_RESULT status")
    if tuple(packet.get("forbidden_claims", ())) != FORBIDDEN_CLAIMS:
        raise ProtocolFreezeError("packet forbidden_claims drifted from executor guard list")
    return packet, packet["protocol_subject_hash"]


# --------------------------------------------------------------------------- #
# Problem rendering (no label leakage; faithful to the executable payload)
# --------------------------------------------------------------------------- #

_INSTRUCTION = (
    "Decide whether the described structure satisfies its rule.\n"
    "Respond with exactly one word, either VALID or INVALID.\n"
)

# Alternate declared boundary regime labels used only for the NEW_BOUNDARY probe
# surface. They reframe the presented boundary; they do not change the payload
# (and therefore never change the verifier gold).
_ALT_BOUNDARY_LABEL: dict[FamilyId, str] = {
    FamilyId.SEQUENCE_COMPOSITION: "open",
    FamilyId.BALANCE_CONSERVATION: "leaky",
    FamilyId.STATE_REACHABILITY: "nondeterministic",
}


def _seq_facts(payload: Mapping[str, object], *, style: str, ablate: bool) -> list[str]:
    start = payload["start"]
    ops = tuple(payload["ops"])
    if ablate:
        # Ablate the decisive coordinate: hide operation order, keep only arity.
        return [f"start value: {start}", f"operation count: {len(ops)}"]
    ordered = " then ".join(f"{name}({val})" for name, val in ops)
    if style == "alt":
        pretty = "; ".join(f"step {i + 1}: {name} by {val}" for i, (name, val) in enumerate(ops))
        return [f"initial: {start}", f"pipeline: {pretty}", "evaluation: left_associative"]
    return [f"start value: {start}", f"apply operations in order: {ordered}", "evaluation: left_associative"]


def _balance_facts(payload: Mapping[str, object], *, style: str, ablate: bool) -> list[str]:
    if ablate:
        # Ablate the decisive coordinate: hide the flow magnitudes.
        return ["a balance system with an inflow, an outflow, and a store"]
    inflow, outflow, store = payload["inflow"], payload["outflow"], payload["store"]
    if style == "alt":
        return [f"inflow := {inflow}", f"outflow := {outflow}", f"stored := {store}"]
    return [f"inflow: {inflow}", f"outflow: {outflow}", f"store: {store}"]


def _reach_facts(payload: Mapping[str, object], *, style: str, ablate: bool) -> list[str]:
    states = tuple(payload["states"])
    start = payload["start"]
    target = payload["target"]
    if ablate:
        # Ablate the decisive coordinate: hide the edges entirely.
        return [f"states: {', '.join(map(str, states))}", f"start: {start}", f"target: {target}"]
    edges = tuple(payload["edges"])
    # IMPORTANT: reachability requires the edges; surface_text omits them, so the
    # full render always lists every edge.
    edge_str = ", ".join(f"{src}->{dst}" for src, dst in edges)
    if style == "alt":
        lines = [f"nodes = [{', '.join(map(str, states))}]", f"transitions = [{edge_str}]"]
        lines.append(f"query: is {target} reachable from {start}?")
        return lines
    return [
        f"states: {', '.join(map(str, states))}",
        f"directed edges: {edge_str}",
        f"start: {start}",
        f"target: {target}",
    ]


_FACT_BUILDERS = {
    FamilyId.SEQUENCE_COMPOSITION.value: _seq_facts,
    FamilyId.BALANCE_CONSERVATION.value: _balance_facts,
    FamilyId.STATE_REACHABILITY.value: _reach_facts,
}


def render_problem(
    case: TrainingCase,
    *,
    style: str = "default",
    boundary_shift: bool = False,
    ablate: bool = False,
) -> str:
    """Render a case's executable payload as a neutral VALID/INVALID problem.

    No label leakage: the rendered text never contains the gold label, the
    control kind, the twin id, or the ``case_id`` (whose ``a``/``b`` suffix
    encodes the generator's valid/invalid choice). Both answer words appear once,
    in the instruction, for every case. The scaffold is identical across cases of
    a family; only the payload facts differ.

    For ``state_reachability`` the full render lists every payload edge, because
    ``surface_text`` alone omits them. ``ablate=True`` deliberately removes the
    decisive coordinate from the input (used by the twin defect check).
    """

    payload = dict(case.executable_payload)
    family = str(payload["family"])
    fact_builder = _FACT_BUILDERS.get(family)
    if fact_builder is None:
        raise ValueError(f"no renderer for family {family}")

    lines = [_INSTRUCTION.rstrip("\n"), ""]
    lines.append("Structure:")
    if boundary_shift:
        alt = _ALT_BOUNDARY_LABEL.get(case.family_id, "alternate")
        lines.append(f"declared boundary regime: {alt}")
    lines.extend(f"- {fact}" for fact in fact_builder(payload, style=style, ablate=ablate))
    lines.append("")
    lines.append("Answer:")
    return "\n".join(lines)


def render_target(case: TrainingCase) -> str:
    """Supervised target string: the verifier gold (assigned by ``verify_case``)."""

    if case.gold_label is None:
        raise ValueError("case must be verified (gold assigned by verify_case) before use")
    return case.gold_label.value


# --------------------------------------------------------------------------- #
# Train / probe set construction (disjoint by offset band and control kind)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Example:
    """One rendered (prompt, gold) pair bound to its source case id."""

    case_id: str
    family: str
    prompt: str
    gold: str


def _verified_family_cases(family: FamilyId, offsets: Iterable[int]) -> list[TrainingCase]:
    cases: list[TrainingCase] = []
    for offset in offsets:
        for case in generate_family_cases(family, seed_offset=offset):
            cases.append(verify_case(case))
    return cases


@dataclass(frozen=True)
class OffsetBands:
    """Disjoint seed-offset bands for training and each held-out probe kind."""

    train: tuple[int, ...]
    same_structure: tuple[int, ...]
    new_composition: tuple[int, ...]
    new_boundary: tuple[int, ...]
    new_representation: tuple[int, ...]
    new_domain: tuple[int, ...]

    @property
    def all_probe(self) -> tuple[int, ...]:
        return (
            self.same_structure
            + self.new_composition
            + self.new_boundary
            + self.new_representation
            + self.new_domain
        )


def build_offset_bands(*, max_exposure: int, probe_band_width: int = 4) -> OffsetBands:
    """Allocate disjoint offset bands; train band is large enough for the ladder.

    Each offset yields two cases (one VALID, one INVALID) per family, so the train
    band needs at least ``ceil(max_exposure / 2)`` offsets.
    """

    train_offsets = max(1, (max_exposure + 1) // 2 + 1)
    cursor = 0

    def take(width: int) -> tuple[int, ...]:
        nonlocal cursor
        band = tuple(range(cursor, cursor + width))
        cursor += width
        return band

    train = take(train_offsets)
    same = take(probe_band_width)
    comp = take(probe_band_width)
    boundary = take(probe_band_width)
    rep = take(probe_band_width)
    domain = take(probe_band_width)
    return OffsetBands(
        train=train,
        same_structure=same,
        new_composition=comp,
        new_boundary=boundary,
        new_representation=rep,
        new_domain=domain,
    )


def build_training_pool(family: FamilyId, bands: OffsetBands, *, seed: int) -> list[Example]:
    """Deterministically shuffled pool of trained-family examples (default render)."""

    cases = _verified_family_cases(family, bands.train)
    pool = [
        Example(case_id=c.case_id, family=c.family_id.value, prompt=render_problem(c), gold=render_target(c))
        for c in cases
    ]
    # Stable, process-independent family salt (builtin hash() is PYTHONHASHSEED-salted).
    family_salt = int.from_bytes(sha256(family.value.encode("utf-8")).digest()[:4], "big")
    rng = random.Random(seed ^ family_salt)
    rng.shuffle(pool)
    return pool


def build_probe_sets(
    family: FamilyId,
    bands: OffsetBands,
    *,
    hostile_seed_offset: int,
) -> dict[ExposureProbeKind, list[Example]]:
    """Build the six held-out probe sets, each disjoint from the training pool.

    Disjointness is guaranteed structurally: SAME/NEW_COMPOSITION/NEW_BOUNDARY/
    NEW_REPRESENTATION draw the trained family from offset bands that do not
    overlap the training band; NEW_DOMAIN draws the *other* families; and
    HOSTILE_NEAR_MISS draws ``-decoy`` control cases. No probe case id ever
    equals a training case id.
    """

    def examples(cases: Sequence[TrainingCase], **render_kwargs) -> list[Example]:
        return [
            Example(
                case_id=c.case_id,
                family=c.family_id.value,
                prompt=render_problem(c, **render_kwargs),
                gold=render_target(c),
            )
            for c in cases
        ]

    same = _verified_family_cases(family, bands.same_structure)
    comp = _verified_family_cases(family, bands.new_composition)
    boundary = _verified_family_cases(family, bands.new_boundary)
    rep = _verified_family_cases(family, bands.new_representation)

    other_families = [f for f in FamilyId if f != family]
    domain_cases: list[TrainingCase] = []
    for other in other_families:
        domain_cases.extend(_verified_family_cases(other, bands.new_domain))

    hostile = build_hostile_control_suite(seed_offset=hostile_seed_offset)
    decoys = [c for c in hostile.semantic_near_decoys if c.family_id == family]

    return {
        ExposureProbeKind.SAME_STRUCTURE: examples(same),
        ExposureProbeKind.NEW_COMPOSITION: examples(comp),
        ExposureProbeKind.NEW_BOUNDARY: examples(boundary, boundary_shift=True),
        ExposureProbeKind.NEW_REPRESENTATION: examples(rep, style="alt"),
        ExposureProbeKind.NEW_DOMAIN: examples(domain_cases),
        ExposureProbeKind.HOSTILE_NEAR_MISS: examples(decoys),
    }


def build_ablation_probe_sets(
    family: FamilyId,
    bands: OffsetBands,
) -> list[Example]:
    """Coordinate-ablated twin inputs: same cases as SAME_STRUCTURE but with the
    decisive coordinate removed from the presented facts.

    A faithful instrument should drop toward chance on these; a checkpoint that
    still scores near its full accuracy is exploiting a shortcut, which the
    terminal classifier reads as INSTRUMENT_OR_GENERATOR_DEFECT.
    """

    cases = _verified_family_cases(family, bands.same_structure)
    return [
        Example(
            case_id=f"{c.case_id}-ablate",
            family=c.family_id.value,
            prompt=render_problem(c, ablate=True),
            gold=render_target(c),
        )
        for c in cases
    ]


def assert_disjoint(train: Sequence[Example], probes: Mapping[ExposureProbeKind, Sequence[Example]]) -> None:
    """Fail-closed check that no probe case id appears in the training pool."""

    train_ids = {ex.case_id for ex in train}
    for kind, examples in probes.items():
        overlap = train_ids & {ex.case_id for ex in examples}
        if overlap:
            raise ValueError(f"train/probe leakage for {kind.value}: {sorted(overlap)}")


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #


def seed_everything(seed: int) -> None:
    """Seed python/numpy/torch (torch imported lazily) for a deterministic run."""

    os.environ.setdefault("PYTHONHASHSEED", str(seed))
    random.seed(seed)
    try:  # numpy is optional at import time.
        import numpy as np  # noqa: WPS433

        np.random.seed(seed)
    except Exception:  # pragma: no cover - numpy absent
        pass
    try:
        import torch  # noqa: WPS433

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        torch.use_deterministic_algorithms(True, warn_only=True)
    except Exception:  # pragma: no cover - torch absent (logic-only imports)
        pass


# --------------------------------------------------------------------------- #
# LoRA fine-tune + probe evaluation (heavy deps imported lazily here)
# --------------------------------------------------------------------------- #


def _checkpoint_hash(state: Mapping[str, object]) -> str:
    """Content hash of the trained adapter parameters (bytes of sorted tensors)."""

    import torch  # noqa: WPS433

    hasher = sha256()
    for key in sorted(state):
        tensor = state[key]
        if isinstance(tensor, torch.Tensor):
            hasher.update(key.encode("utf-8"))
            hasher.update(tensor.detach().to("cpu").contiguous().numpy().tobytes())
    return hasher.hexdigest()


def _score_label(model, tokenizer, prompt: str, device: str) -> str:
    """Return VALID/INVALID by comparing completion log-likelihood of each word."""

    import torch  # noqa: WPS433

    best_label = GoldLabel.INVALID.value
    best_logprob = None
    prompt_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(device)
    for label in (GoldLabel.VALID.value, GoldLabel.INVALID.value):
        target_ids = tokenizer(" " + label, add_special_tokens=False, return_tensors="pt").input_ids.to(device)
        full = torch.cat([prompt_ids, target_ids], dim=1)
        with torch.no_grad():
            logits = model(full).logits
        logprobs = torch.log_softmax(logits, dim=-1)
        total = 0.0
        n_prompt = prompt_ids.shape[1]
        for i in range(target_ids.shape[1]):
            tok = target_ids[0, i]
            total += float(logprobs[0, n_prompt + i - 1, tok])
        if best_logprob is None or total > best_logprob:
            best_logprob = total
            best_label = label
    return best_label


def _evaluate(model, tokenizer, examples: Sequence[Example], device: str) -> tuple[float, int]:
    """Accuracy of the checkpoint over a probe set. Returns ``(accuracy, n)``.

    An empty probe set returns ``(0.0, 0)`` and MUST be interpreted as "no
    measurement", never as a real zero-accuracy result.
    """

    if not examples:
        return 0.0, 0
    correct = 0
    for ex in examples:
        pred = _score_label(model, tokenizer, ex.prompt, device)
        correct += int(pred == ex.gold)
    return correct / len(examples), len(examples)


def lora_finetune(
    train_examples: Sequence[Example],
    *,
    model_id: str,
    device: str,
    seed: int,
    epochs: int,
    lr: float,
    checkpoint_dir: Path,
) -> tuple[object, object, str]:
    """LoRA fine-tune a HuggingFace causal LM on ``train_examples``.

    Returns ``(model, tokenizer, checkpoint_hash)``. All heavy imports happen
    here so the module imports without torch/transformers/peft installed.
    """

    import torch  # noqa: WPS433
    from peft import LoraConfig, get_peft_model  # noqa: WPS433
    from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: WPS433

    seed_everything(seed)

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    base = AutoModelForCausalLM.from_pretrained(model_id)
    lora = LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.0,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(base, lora)
    model.to(device)
    model.train()

    optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad), lr=lr)

    # Deterministic ordering: train_examples are already seed-shuffled upstream.
    #
    # IMPORTANT (v2 fix): build the sequence by concatenating *token ids*, not by
    # tokenizing "prompt + ' ' + gold" as one string. BPE merges the separating
    # space into the answer token (" VALID" is a single token), so masking up to
    # len(tokenize(prompt + " ")) masked the gold token itself -> the loss saw no
    # answer signal and training collapsed to a constant predictor. Concatenating
    # ids keeps the gold token a distinct, UNMASKED target that exactly matches the
    # token compared at scoring time.
    eos = torch.tensor([[tokenizer.eos_token_id]], device=device)
    for _ in range(epochs):
        for ex in train_examples:
            prompt_ids = tokenizer(ex.prompt, return_tensors="pt").input_ids.to(device)
            gold_ids = tokenizer(
                " " + ex.gold, add_special_tokens=False, return_tensors="pt"
            ).input_ids.to(device)
            input_ids = torch.cat([prompt_ids, gold_ids, eos], dim=1)
            labels = input_ids.clone()
            labels[:, : prompt_ids.shape[1]] = -100  # mask prompt only; train the gold token(s)
            optimizer.zero_grad()
            out = model(input_ids=input_ids, labels=labels)
            out.loss.backward()
            optimizer.step()

    model.eval()
    adapter_state = {k: v for k, v in model.state_dict().items() if "lora" in k.lower()}
    ckpt_hash = _checkpoint_hash(adapter_state)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(checkpoint_dir))
    return model, tokenizer, ckpt_hash


# --------------------------------------------------------------------------- #
# Outcome rows
# --------------------------------------------------------------------------- #


def make_outcome_row(
    *,
    family: str,
    exposure_count: int,
    probe_kind: ExposureProbeKind,
    accuracy: float,
    n: int,
    checkpoint_hash: str,
    marginal_gain: float | None,
    prev_exposure_count: int | None,
    protocol_subject_hash: str,
    smoke: bool,
) -> dict:
    """Construct one measured outcome row bound to the frozen packet hash."""

    return {
        "family": family,
        "exposure_count": exposure_count,
        "probe_kind": probe_kind.value,
        "coordinate": PROBE_TO_COORDINATE[probe_kind].value,
        "accuracy": accuracy,
        "n": n,
        "checkpoint_hash": checkpoint_hash,
        "marginal_gain": marginal_gain,
        "prev_exposure_count": prev_exposure_count,
        "protocol_subject_hash": protocol_subject_hash,
        "smoke": smoke,
    }


def validate_outcome_row(row: Mapping[str, object]) -> None:
    """Fail-closed schema check for one outcome row."""

    missing = [f for f in OUTCOME_FIELDS if f not in row]
    if missing:
        raise ValueError(f"outcome row missing fields: {missing}")
    extra = [k for k in row if k not in OUTCOME_FIELDS]
    if extra:
        raise ValueError(f"outcome row has unexpected fields: {extra}")
    if not 0.0 <= float(row["accuracy"]) <= 1.0:
        raise ValueError("accuracy must be in [0,1]")
    if int(row["n"]) < 0:
        raise ValueError("n must be non-negative")


def write_outcomes(rows: Sequence[Mapping[str, object]], path: Path) -> None:
    for row in rows:
        validate_outcome_row(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


# --------------------------------------------------------------------------- #
# Terminal classifier (Phase-1)
# --------------------------------------------------------------------------- #


def _trajectory(
    rows: Sequence[Mapping[str, object]],
    probe_kind: ExposureProbeKind,
) -> list[tuple[int, float]]:
    """Exposure-ordered (exposure_count, mean accuracy) for one probe kind.

    Averages across families and ignores rows with ``n == 0`` (unmeasured).
    """

    buckets: dict[int, list[float]] = {}
    for row in rows:
        if row["probe_kind"] != probe_kind.value:
            continue
        if int(row.get("n", 1)) <= 0:
            continue
        buckets.setdefault(int(row["exposure_count"]), []).append(float(row["accuracy"]))
    return [(exp, sum(vals) / len(vals)) for exp, vals in sorted(buckets.items())]


def _late_marginal_gain(traj: Sequence[tuple[int, float]], after_exposure: int | None) -> float | None:
    """Mean consecutive marginal gain for steps whose lower exposure >= threshold.

    Returns ``None`` when there are no qualifying steps.
    """

    gains: list[float] = []
    for (exp0, acc0), (_, acc1) in zip(traj, traj[1:]):
        if after_exposure is None or exp0 >= after_exposure:
            gains.append(acc1 - acc0)
    if not gains:
        return None
    return sum(gains) / len(gains)


def classify_phase1_terminal(
    accuracy_rows: Sequence[Mapping[str, object]],
    *,
    ablation_rows: Sequence[Mapping[str, object]] | None = None,
    floor_accuracy: float = DEFAULT_FLOOR_ACCURACY,
    mastery_threshold: float = DEFAULT_MASTERY_THRESHOLD,
    gain_floor: float = DEFAULT_GAIN_FLOOR,
    ablation_eps: float = DEFAULT_ABLATION_EPS,
) -> dict:
    """Classify the Phase-1 terminal from measured outcome rows.

    Fail-closed decision order (mirrors the packet ALLOWED_TERMINALS):

    1. INSTRUMENT_OR_GENERATOR_DEFECT - a coordinate-ablated twin classifier
       matches the full classifier (accuracy gap <= ``ablation_eps`` while the
       full classifier is meaningfully above chance): the probe carries no
       structural signal.
    2. MODEL_FLOOR - the model never clears ``floor_accuracy`` on SAME_STRUCTURE.
    3. MECHANISM_SIGNAL_PRESENT - once principle is mastered, SAME_STRUCTURE
       marginal gain falls to/below ``gain_floor`` while unsaturated coordinates
       still gain above ``gain_floor`` (state-dependent structural residual).
    4. REPETITION_REMAINS_VALUABLE - same-structure repetition keeps paying
       (late SAME_STRUCTURE gain still above ``gain_floor``).
    5. NO_STATE_DEPENDENT_RESIDUAL - otherwise.

    ``grants_scientific_authority`` is always False and no forbidden claim is ever
    asserted.
    """

    same_traj = _trajectory(accuracy_rows, ExposureProbeKind.SAME_STRUCTURE)
    other_kinds = [k for k in ExposureProbeKind if k != ExposureProbeKind.SAME_STRUCTURE]

    full_ref = max((acc for _, acc in same_traj), default=0.0)

    # --- ablation / defect check -------------------------------------------- #
    ablation_ref = None
    if ablation_rows:
        abl_vals = [float(r["accuracy"]) for r in ablation_rows if int(r.get("n", 1)) > 0]
        if abl_vals:
            ablation_ref = max(abl_vals)

    evidence: dict[str, object] = {
        "same_structure_max_accuracy": full_ref,
        "ablation_max_accuracy": ablation_ref,
        "floor_accuracy": floor_accuracy,
        "mastery_threshold": mastery_threshold,
        "gain_floor": gain_floor,
        "ablation_eps": ablation_eps,
    }

    def _result(terminal: str, extra: Mapping[str, object]) -> dict:
        merged = dict(evidence)
        merged.update(extra)
        return {
            "terminal": terminal,
            "evidence": merged,
            "grants_scientific_authority": False,
            "scientific_claim_status": "NO_EMPIRICAL_RESULT",
            "forbidden_claims_asserted": [],
        }

    if (
        ablation_ref is not None
        and full_ref > CHANCE + gain_floor
        and (full_ref - ablation_ref) <= ablation_eps
    ):
        return _result(
            "INSTRUMENT_OR_GENERATOR_DEFECT",
            {"reason": "ablated_twin_matches_full", "full_minus_ablation": full_ref - ablation_ref},
        )

    # --- model floor -------------------------------------------------------- #
    if full_ref < floor_accuracy:
        return _result("MODEL_FLOOR", {"reason": "never_cleared_floor_on_principle"})

    # --- principle mastery point ------------------------------------------- #
    principle_mastered_at: int | None = None
    for exp, acc in same_traj:
        if acc >= mastery_threshold:
            principle_mastered_at = exp
            break

    same_late = _late_marginal_gain(same_traj, principle_mastered_at)

    other_late_gains: list[float] = []
    for kind in other_kinds:
        traj = _trajectory(accuracy_rows, kind)
        gain = _late_marginal_gain(traj, principle_mastered_at)
        if gain is not None:
            other_late_gains.append(gain)
    other_late = max(other_late_gains) if other_late_gains else None

    evidence.update(
        {
            "principle_mastered_at_exposure": principle_mastered_at,
            "same_structure_late_gain": same_late,
            "unsaturated_coord_late_gain": other_late,
        }
    )

    if (
        principle_mastered_at is not None
        and same_late is not None
        and other_late is not None
        and same_late <= gain_floor
        and other_late > gain_floor
    ):
        return _result(
            "MECHANISM_SIGNAL_PRESENT",
            {"reason": "same_structure_gain_fell_while_unsaturated_coords_still_valuable"},
        )

    if same_late is not None and same_late > gain_floor:
        return _result("REPETITION_REMAINS_VALUABLE", {"reason": "same_structure_repetition_still_paying"})

    return _result("NO_STATE_DEPENDENT_RESIDUAL", {"reason": "no_differential_state_dependent_gain"})


# --------------------------------------------------------------------------- #
# Run manifest
# --------------------------------------------------------------------------- #


def _git_sha() -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return proc.stdout.strip()
    except Exception:  # pragma: no cover - git absent
        return "unknown"


def build_run_manifest(
    *,
    model_id: str,
    protocol_subject_hash: str,
    seed: int,
    families: Sequence[str],
    exposure_counts: Sequence[int],
    smoke: bool,
    started_at: str,
    finished_at: str,
    terminal: Mapping[str, object] | None,
) -> dict:
    return {
        "schema_version": "rakl-training-ladder-phase1-run-manifest-v1",
        "issue": 461,
        "phase": "0/1",
        "model_id": model_id,
        "protocol_subject_hash": protocol_subject_hash,
        "seed": seed,
        "git_sha": _git_sha(),
        "families": list(families),
        "exposure_counts": list(exposure_counts),
        "probe_coordinate_map": {k.value: v.value for k, v in PROBE_TO_COORDINATE.items()},
        "started_at": started_at,
        "finished_at": finished_at,
        "smoke": smoke,
        "grants_scientific_authority": False,
        "scientific_claim_status": "NO_EMPIRICAL_RESULT",
        "forbidden_claims_asserted": [],
        "terminal": terminal,
        "authority_boundary": (
            "Phase 0/1 instrument only. Training utility is not scientific authority. "
            "Does not license #466, #467, or Paper VI."
        ),
    }


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run(
    *,
    packet_dir: Path,
    model_id: str,
    families: Sequence[FamilyId],
    exposure_counts: Sequence[int],
    out_dir: Path,
    device: str,
    smoke: bool,
    seed: int = FROZEN_SEED,
    epochs: int = 12,
    lr: float = 3e-4,
) -> dict:
    """Execute the exposure ladder and emit outcomes + manifest.

    This is the only function that trains a model. It imports torch/transformers/
    peft lazily via :func:`lora_finetune`.
    """

    packet, protocol_subject_hash = load_frozen_packet(packet_dir)
    started_at = _now()
    seed_everything(seed)

    bands = build_offset_bands(max_exposure=max(exposure_counts))
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    ablation_rows: list[dict] = []

    for family in families:
        pool = build_training_pool(family, bands, seed=seed)
        probe_sets = build_probe_sets(family, bands, hostile_seed_offset=bands.new_domain[0])
        assert_disjoint(pool, probe_sets)
        ablation_examples = build_ablation_probe_sets(family, bands)

        # Per-probe accuracy history to compute marginal gain vs previous exposure.
        prev: dict[ExposureProbeKind, tuple[int, float]] = {}

        for exposure_count in sorted(exposure_counts):
            train_examples = pool[:exposure_count]
            if not train_examples:
                continue
            ckpt_dir = out_dir / "checkpoints" / f"{family.value}_exp{exposure_count}"
            model, tokenizer, ckpt_hash = lora_finetune(
                train_examples,
                model_id=model_id,
                device=device,
                seed=seed,
                epochs=epochs,
                lr=lr,
                checkpoint_dir=ckpt_dir,
            )

            for probe_kind, examples in probe_sets.items():
                accuracy, n = _evaluate(model, tokenizer, examples, device)
                marginal_gain = None
                prev_exp = None
                if probe_kind in prev:
                    prev_exp, prev_acc = prev[probe_kind]
                    marginal_gain = accuracy - prev_acc
                rows.append(
                    make_outcome_row(
                        family=family.value,
                        exposure_count=exposure_count,
                        probe_kind=probe_kind,
                        accuracy=accuracy,
                        n=n,
                        checkpoint_hash=ckpt_hash,
                        marginal_gain=marginal_gain,
                        prev_exposure_count=prev_exp,
                        protocol_subject_hash=protocol_subject_hash,
                        smoke=smoke,
                    )
                )
                prev[probe_kind] = (exposure_count, accuracy)

            # Coordinate-ablated twin evaluation for the defect check.
            abl_acc, abl_n = _evaluate(model, tokenizer, ablation_examples, device)
            ablation_rows.append(
                {
                    "family": family.value,
                    "exposure_count": exposure_count,
                    "accuracy": abl_acc,
                    "n": abl_n,
                    "checkpoint_hash": ckpt_hash,
                    "protocol_subject_hash": protocol_subject_hash,
                    "smoke": smoke,
                }
            )

    outcomes_path = out_dir / "exposure_outcomes.jsonl"
    write_outcomes(rows, outcomes_path)

    terminal = classify_phase1_terminal(rows, ablation_rows=ablation_rows) if rows else None

    manifest = build_run_manifest(
        model_id=model_id,
        protocol_subject_hash=protocol_subject_hash,
        seed=seed,
        families=[f.value for f in families],
        exposure_counts=sorted(exposure_counts),
        smoke=smoke,
        started_at=started_at,
        finished_at=_now(),
        terminal=terminal,
    )
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out_dir / "ablation_twin_outcomes.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in ablation_rows), encoding="utf-8"
    )
    return manifest


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def _parse_families(spec: str | None) -> list[FamilyId]:
    if not spec:
        return list(FamilyId)
    out: list[FamilyId] = []
    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue
        out.append(FamilyId(token))
    return out


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Paper IV Phase-1 (#461) exposure executor.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="HuggingFace causal LM id or local path.")
    parser.add_argument("--families", default=None, help="Comma-separated family ids (default: all three).")
    parser.add_argument("--max-exposure", type=int, default=64, help="Cap exposure ladder at this count.")
    parser.add_argument("--packet-dir", type=Path, default=DEFAULT_PACKET_DIR)
    parser.add_argument("--out", type=Path, default=ROOT / "experiments" / "training_ladder" / "phase1_out")
    parser.add_argument("--device", default="cpu", help="torch device (cpu, cuda, cuda:0, ...).")
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Pipeline smoke: 0.5B model, exposures {1,2,4}, 1 family, cpu ok. NOT a scientific result.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    if args.smoke:
        model_id = DEFAULT_MODEL
        families = [FamilyId.SEQUENCE_COMPOSITION]
        exposure_counts = [1, 2, 4]
        device = args.device or "cpu"
        smoke = True
    else:
        model_id = args.model
        families = _parse_families(args.families)
        exposure_counts = [c for c in REGISTERED_EXPOSURE_COUNTS if c <= args.max_exposure]
        device = args.device
        smoke = False

    if not exposure_counts:
        raise SystemExit("no exposure counts selected (check --max-exposure)")

    manifest = run(
        packet_dir=args.packet_dir,
        model_id=model_id,
        families=families,
        exposure_counts=exposure_counts,
        out_dir=args.out,
        device=device,
        smoke=smoke,
        epochs=args.epochs,
        lr=args.lr,
    )
    print(json.dumps({
        "out_dir": str(args.out),
        "smoke": manifest["smoke"],
        "protocol_subject_hash": manifest["protocol_subject_hash"],
        "terminal": (manifest["terminal"] or {}).get("terminal"),
        "grants_scientific_authority": manifest["grants_scientific_authority"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
