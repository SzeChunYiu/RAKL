from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
from dataclasses import dataclass
from typing import Mapping, Sequence


EXPOSURES = (
    "SAME_STRUCTURE",
    "NEW_COMPOSITION",
    "NEW_BOUNDARY",
    "NEW_REPRESENTATION",
    "NEW_DOMAIN",
    "HOSTILE_NEAR_MISS",
)
ARMS = (
    "A_UNIFORM_RANDOM",
    "B_SEMANTIC_DIVERSITY",
    "C_STRONGEST_MODEL_AWARE_PARENT",
    "D_STATIC_RAKL_STRUCTURAL",
    "E_ADAPTIVE_RAKL_STRUCTURAL",
)
HARD_HARM_COORDINATES = (
    "SAME_STRUCTURE",
    "NEW_COMPOSITION",
    "NEW_BOUNDARY",
    "HOSTILE_NEAR_MISS",
)

_RESULT_SCHEMA = "rakl-paper4-phase2-result-v1"
_REQUIRED_TERMINAL = "ADAPTIVE_RESIDUAL_SUPPORTED"
_MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
_MODEL_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
_PROTOCOL_ID = "PROTOCOL_V3.json"
_INFERENCE_ID = "INFERENCE_PLAN.json"
_MATERIAL_GAIN = 0.05
_PARENT_NONINFERIORITY = -0.02
_HARD_HARM_BOUNDARY = -0.05
_BOOTSTRAP_REPS = 10_000
_BOOTSTRAP_SEED = 46_699
_SIGNFLIP_REPS = 20_000
_SIGNFLIP_SEED = 46_700

_RESOURCE_FIELDS = (
    "model_loads",
    "training_example_presentations",
    "training_token_presentations",
    "selection_examples_scored",
    "selection_forward_calls",
    "assurance_examples_scored",
    "assurance_forward_calls",
    "training_wall_seconds",
    "selection_wall_seconds",
    "assurance_wall_seconds",
    "cpu_selection_seconds",
    "total_accounted_seconds",
    "gpu_seconds",
    "peak_gpu_memory_bytes",
)


@dataclass(frozen=True)
class Phase2AdaptiveAdmission:
    admitted: bool
    status: str
    reasons: tuple[str, ...]
    receipt_id: str | None = None
    evaluated_subject_hash: str | None = None
    evidence_ids: tuple[str, ...] = ()

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def _canonical_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha(payload: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _fail(*reasons: str) -> Phase2AdaptiveAdmission:
    return Phase2AdaptiveAdmission(False, "CANNOT_CHECK", tuple(reasons))


def _float_equal(a: object, b: object, *, atol: float = 1e-12) -> bool:
    try:
        x = float(a)
        y = float(b)
    except (TypeError, ValueError):
        return False
    return math.isfinite(x) and math.isfinite(y) and abs(x - y) <= atol


def _manifest_payload(data_manifest: Mapping[str, object]) -> dict[str, object] | None:
    try:
        return {
            "train": data_manifest["train"],
            "selection": data_manifest["selection"],
            "assurance": data_manifest["assurance"],
        }
    except (KeyError, TypeError):
        return None


def _validate_manifest(data_manifest: Mapping[str, object]) -> tuple[bool, str | None, str | None]:
    payload = _manifest_payload(data_manifest)
    if payload is None:
        return False, "phase2_data_manifest_missing_partitions", None
    expected_counts = {"train": 96, "selection": 16, "assurance": 64}
    partition_sets: dict[str, set[str]] = {}
    for partition, per_exposure in payload.items():
        if not isinstance(per_exposure, Mapping) or set(per_exposure) != set(EXPOSURES):
            return False, f"phase2_{partition}_manifest_exposure_set_invalid", None
        seen: list[str] = []
        for exposure in EXPOSURES:
            ids = per_exposure[exposure]
            if not isinstance(ids, Sequence) or isinstance(ids, (str, bytes)):
                return False, f"phase2_{partition}_{exposure}_ids_invalid", None
            ids = list(ids)
            if len(ids) != expected_counts[partition]:
                return False, f"phase2_{partition}_{exposure}_count_invalid", None
            if any(not isinstance(case_id, str) or not case_id.strip() for case_id in ids):
                return False, f"phase2_{partition}_{exposure}_case_id_invalid", None
            seen.extend(ids)
        if len(seen) != len(set(seen)):
            return False, f"phase2_{partition}_duplicate_case_id", None
        partition_sets[partition] = set(seen)
    if (
        partition_sets["train"] & partition_sets["selection"]
        or partition_sets["train"] & partition_sets["assurance"]
        or partition_sets["selection"] & partition_sets["assurance"]
    ):
        return False, "phase2_manifest_partition_overlap", None
    digest = _sha(payload)
    if data_manifest.get("sha256") != digest:
        return False, "phase2_manifest_self_hash_mismatch", None
    return True, None, digest


def _validate_assurance(
    assurance_by_arm: Mapping[str, Sequence[Mapping[str, object]]],
    data_manifest: Mapping[str, object],
) -> tuple[bool, str | None]:
    if set(assurance_by_arm) != set(ARMS):
        return False, "phase2_assurance_arm_set_invalid"
    manifest_assurance = data_manifest["assurance"]
    canonical_subject: dict[str, tuple[str, str]] | None = None
    for arm in ARMS:
        rows = assurance_by_arm[arm]
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or len(rows) != 384:
            return False, f"phase2_assurance_{arm}_count_invalid"
        observed: dict[str, tuple[str, str]] = {}
        exposure_counts = {exposure: 0 for exposure in EXPOSURES}
        for row in rows:
            if not isinstance(row, Mapping):
                return False, f"phase2_assurance_{arm}_row_invalid"
            case_id = row.get("case_id")
            exposure = row.get("exposure")
            gold = row.get("gold")
            pred = row.get("prediction")
            correct = row.get("correct")
            if not isinstance(case_id, str) or not case_id.strip() or case_id in observed:
                return False, f"phase2_assurance_{arm}_duplicate_or_invalid_case_id"
            if exposure not in EXPOSURES:
                return False, f"phase2_assurance_{arm}_exposure_invalid"
            if gold not in {"VALID", "INVALID"} or pred not in {"VALID", "INVALID"}:
                return False, f"phase2_assurance_{arm}_label_invalid"
            if correct not in {0, 1} or int(correct) != int(pred == gold):
                return False, f"phase2_assurance_{arm}_correctness_inconsistent"
            observed[case_id] = (str(exposure), str(gold))
            exposure_counts[str(exposure)] += 1
        if any(count != 64 for count in exposure_counts.values()):
            return False, f"phase2_assurance_{arm}_stratum_count_invalid"
        expected_ids = {case_id for exposure in EXPOSURES for case_id in manifest_assurance[exposure]}
        if set(observed) != expected_ids:
            return False, f"phase2_assurance_{arm}_manifest_mismatch"
        for exposure in EXPOSURES:
            expected_exposure_ids = set(manifest_assurance[exposure])
            observed_exposure_ids = {case_id for case_id, (exp, _) in observed.items() if exp == exposure}
            if observed_exposure_ids != expected_exposure_ids:
                return False, f"phase2_assurance_{arm}_{exposure}_manifest_mismatch"
        if canonical_subject is None:
            canonical_subject = observed
        elif observed != canonical_subject:
            return False, "phase2_assurance_pairing_or_gold_mismatch"
    return True, None


def _rows_by_id(rows: Sequence[Mapping[str, object]], exposure: str | None = None) -> dict[str, Mapping[str, object]]:
    return {
        str(row["case_id"]): row
        for row in rows
        if exposure is None or row["exposure"] == exposure
    }


def _paired_diffs(
    rows_a: Sequence[Mapping[str, object]],
    rows_b: Sequence[Mapping[str, object]],
    exposure: str | None = None,
) -> list[tuple[str, str, int]]:
    a = _rows_by_id(rows_a, exposure)
    b = _rows_by_id(rows_b, exposure)
    if set(a) != set(b):
        raise ValueError("paired assurance case sets differ across arms")
    return [
        (
            case_id,
            str(a[case_id]["exposure"]),
            int(a[case_id]["correct"]) - int(b[case_id]["correct"]),
        )
        for case_id in sorted(a)
    ]


def _bootstrap_ci(
    diffs: Sequence[tuple[str, str, int]],
    *,
    reps: int,
    seed: int,
    stratified: bool = True,
) -> tuple[float, float, float]:
    rng = random.Random(seed)
    mean = statistics.mean(value for _, _, value in diffs)
    samples: list[float] = []
    if stratified:
        strata = {exposure: [value for _, exp, value in diffs if exp == exposure] for exposure in EXPOSURES}
        if any(not values for values in strata.values()):
            raise ValueError("missing assurance stratum")
        for _ in range(reps):
            values: list[int] = []
            for exposure in EXPOSURES:
                source = strata[exposure]
                values.extend(source[rng.randrange(len(source))] for _ in range(len(source)))
            samples.append(statistics.mean(values))
    else:
        source = [value for _, _, value in diffs]
        if not source:
            raise ValueError("empty paired sample")
        for _ in range(reps):
            samples.append(statistics.mean(source[rng.randrange(len(source))] for _ in range(len(source))))
    samples.sort()
    lo = samples[int(0.025 * reps)]
    hi = samples[min(reps - 1, int(0.975 * reps) - 1)]
    return mean, lo, hi


def _signflip_p(diffs: Sequence[tuple[str, str, int]], *, reps: int, seed: int) -> float:
    values = [value for _, _, value in diffs if value != 0]
    if not values:
        return 1.0
    observed = abs(statistics.mean(values))
    rng = random.Random(seed)
    extreme = 0
    for _ in range(reps):
        stat = abs(statistics.mean(value * (-1 if rng.random() < 0.5 else 1) for value in values))
        extreme += stat >= observed - 1e-15
    return (extreme + 1) / (reps + 1)


def _holm(pvals: Mapping[str, float]) -> dict[str, float]:
    ordered = sorted(pvals, key=pvals.get)
    adjusted: dict[str, float] = {}
    running = 0.0
    total = len(ordered)
    for index, key in enumerate(ordered):
        value = min(1.0, (total - index) * pvals[key])
        running = max(running, value)
        adjusted[key] = running
    return adjusted


def recompute_phase2_analysis(
    assurance_by_arm: Mapping[str, Sequence[Mapping[str, object]]],
) -> dict[str, object]:
    """Independent reproduction of the frozen Phase-2 inference decision.

    This intentionally duplicates the registered analysis rather than trusting the
    terminal/CI fields supplied by FINAL_RECEIPT.json.
    """

    contrasts = {
        "E-D": ("E_ADAPTIVE_RAKL_STRUCTURAL", "D_STATIC_RAKL_STRUCTURAL"),
        "E-C": ("E_ADAPTIVE_RAKL_STRUCTURAL", "C_STRONGEST_MODEL_AWARE_PARENT"),
        "D-B": ("D_STATIC_RAKL_STRUCTURAL", "B_SEMANTIC_DIVERSITY"),
    }
    contrast_out: dict[str, dict[str, object]] = {}
    raw_p: dict[str, float] = {}
    for index, (name, (arm_a, arm_b)) in enumerate(contrasts.items()):
        diffs = _paired_diffs(assurance_by_arm[arm_a], assurance_by_arm[arm_b])
        mean, lo, hi = _bootstrap_ci(diffs, reps=_BOOTSTRAP_REPS, seed=_BOOTSTRAP_SEED + index)
        pvalue = _signflip_p(diffs, reps=_SIGNFLIP_REPS, seed=_SIGNFLIP_SEED + index)
        raw_p[name] = pvalue
        contrast_out[name] = {"mean": mean, "ci95": [lo, hi], "raw_p": pvalue}
    adjusted = _holm(raw_p)
    for name in contrast_out:
        contrast_out[name]["holm_p"] = adjusted[name]

    hard_harm: dict[str, dict[str, object]] = {}
    for index, exposure in enumerate(HARD_HARM_COORDINATES):
        diffs = _paired_diffs(
            assurance_by_arm["E_ADAPTIVE_RAKL_STRUCTURAL"],
            assurance_by_arm["D_STATIC_RAKL_STRUCTURAL"],
            exposure,
        )
        mean, lo, hi = _bootstrap_ci(
            diffs,
            reps=_BOOTSTRAP_REPS,
            seed=_BOOTSTRAP_SEED + 100 + index,
            stratified=False,
        )
        hard_harm[exposure] = {
            "mean": mean,
            "ci95": [lo, hi],
            "passes": lo > _HARD_HARM_BOUNDARY,
        }

    ed = contrast_out["E-D"]
    ec = contrast_out["E-C"]
    hard_ok = all(bool(value["passes"]) for value in hard_harm.values())
    positive = (
        float(ed["mean"]) >= _MATERIAL_GAIN
        and float(ed["ci95"][0]) > 0
        and float(ed["holm_p"]) < 0.05
        and float(ec["ci95"][0]) >= _PARENT_NONINFERIORITY
        and hard_ok
    )
    precise_null = (
        float(ed["ci95"][0]) <= 0 <= float(ed["ci95"][1])
        and float(ed["ci95"][1]) < _MATERIAL_GAIN
        and hard_ok
    )
    if not hard_ok:
        terminal = "ADAPTIVE_HARMS_COMPOSITION_OR_RETENTION"
    elif float(ec["ci95"][1]) < _PARENT_NONINFERIORITY:
        terminal = "PARENT_MATCHES_OR_BEATS"
    elif positive:
        terminal = _REQUIRED_TERMINAL
    elif precise_null:
        terminal = "STATIC_EQUALS_ADAPTIVE"
    else:
        terminal = "UNDERPOWERED"
    return {"contrasts": contrast_out, "hard_harm": hard_harm, "terminal": terminal}


def _analysis_matches(receipt_analysis: object, recomputed: Mapping[str, object]) -> bool:
    if not isinstance(receipt_analysis, Mapping):
        return False
    if receipt_analysis.get("terminal") != recomputed["terminal"]:
        return False
    rc = receipt_analysis.get("contrasts")
    cc = recomputed["contrasts"]
    if not isinstance(rc, Mapping):
        return False
    for name in ("E-D", "E-C", "D-B"):
        observed = rc.get(name)
        expected = cc[name]
        if not isinstance(observed, Mapping):
            return False
        if not _float_equal(observed.get("mean"), expected["mean"]):
            return False
        observed_ci = observed.get("ci95")
        expected_ci = expected["ci95"]
        if not isinstance(observed_ci, Sequence) or len(observed_ci) != 2:
            return False
        if not all(_float_equal(a, b) for a, b in zip(observed_ci, expected_ci)):
            return False
        if not _float_equal(observed.get("raw_p"), expected["raw_p"]):
            return False
        if not _float_equal(observed.get("holm_p"), expected["holm_p"]):
            return False
    rh = receipt_analysis.get("hard_harm")
    eh = recomputed["hard_harm"]
    if not isinstance(rh, Mapping):
        return False
    for exposure in HARD_HARM_COORDINATES:
        observed = rh.get(exposure)
        expected = eh[exposure]
        if not isinstance(observed, Mapping) or bool(observed.get("passes")) != bool(expected["passes"]):
            return False
        if not _float_equal(observed.get("mean"), expected["mean"]):
            return False
        observed_ci = observed.get("ci95")
        expected_ci = expected["ci95"]
        if not isinstance(observed_ci, Sequence) or len(observed_ci) != 2:
            return False
        if not all(_float_equal(a, b) for a, b in zip(observed_ci, expected_ci)):
            return False
    return True


def _resources_complete(final_receipt: Mapping[str, object]) -> bool:
    arms = final_receipt.get("arms")
    if not isinstance(arms, Mapping) or set(arms) != set(ARMS):
        return False
    for arm in ARMS:
        summary = arms.get(arm)
        if not isinstance(summary, Mapping):
            return False
        resources = summary.get("resources")
        if not isinstance(resources, Mapping) or any(field not in resources for field in _RESOURCE_FIELDS):
            return False
        numeric: dict[str, float] = {}
        for field in _RESOURCE_FIELDS:
            try:
                value = float(resources[field])
            except (TypeError, ValueError):
                return False
            if not math.isfinite(value) or value < 0:
                return False
            numeric[field] = value
        if numeric["model_loads"] < 1 or numeric["training_example_presentations"] <= 0:
            return False
        if numeric["training_token_presentations"] <= 0 or numeric["assurance_examples_scored"] != 384:
            return False
        if numeric["assurance_forward_calls"] < 768 or numeric["peak_gpu_memory_bytes"] <= 0:
            return False
        expected_total = (
            numeric["training_wall_seconds"]
            + numeric["selection_wall_seconds"]
            + numeric["assurance_wall_seconds"]
            + numeric["cpu_selection_seconds"]
        )
        expected_gpu = numeric["training_wall_seconds"] + numeric["selection_wall_seconds"] + numeric["assurance_wall_seconds"]
        if not math.isclose(numeric["total_accounted_seconds"], expected_total, rel_tol=1e-9, abs_tol=1e-9):
            return False
        if not math.isclose(numeric["gpu_seconds"], expected_gpu, rel_tol=1e-9, abs_tol=1e-9):
            return False
    for arm in ("C_STRONGEST_MODEL_AWARE_PARENT", "E_ADAPTIVE_RAKL_STRUCTURAL"):
        resources = arms[arm]["resources"]
        if float(resources["model_loads"]) < 6:
            return False
        if float(resources["selection_examples_scored"]) <= 0 or float(resources["selection_forward_calls"]) <= 0:
            return False
    return True


def admit_phase2_adaptive_result_bundle(
    *,
    final_receipt: Mapping[str, object] | None,
    data_manifest: Mapping[str, object] | None,
    assurance_by_arm: Mapping[str, Sequence[Mapping[str, object]]] | None,
) -> Phase2AdaptiveAdmission:
    """Canonically admit a positive frozen Paper-IV Phase-2 bundle.

    Caller-provided booleans are never accepted as authority.  The registered
    inference is independently recomputed from paired fresh-assurance rows, and
    malformed/missing/stale evidence fails closed.
    """

    if not isinstance(final_receipt, Mapping):
        return _fail("phase2_final_receipt_missing_or_invalid")
    if not isinstance(data_manifest, Mapping):
        return _fail("phase2_data_manifest_missing_or_invalid")
    if not isinstance(assurance_by_arm, Mapping):
        return _fail("phase2_raw_assurance_missing_or_invalid")
    if final_receipt.get("schema_version") != _RESULT_SCHEMA:
        return _fail("phase2_result_schema_mismatch")
    if final_receipt.get("model_id") != _MODEL_ID or final_receipt.get("model_revision") != _MODEL_REVISION:
        return _fail("phase2_evaluated_model_subject_mismatch")
    if final_receipt.get("protocol") != _PROTOCOL_ID or final_receipt.get("inference_plan") != _INFERENCE_ID:
        return _fail("phase2_protocol_or_inference_subject_mismatch")
    if final_receipt.get("grants_scientific_authority") is not False:
        return _fail("phase2_scientific_authority_boundary_invalid")
    if final_receipt.get("terminal") != _REQUIRED_TERMINAL:
        return _fail(f"phase2_terminal_not_authorizing:{final_receipt.get('terminal')}")

    manifest_ok, manifest_reason, manifest_hash = _validate_manifest(data_manifest)
    if not manifest_ok or manifest_hash is None:
        return _fail(manifest_reason or "phase2_manifest_invalid")
    if final_receipt.get("data_manifest_hash") != manifest_hash:
        return _fail("phase2_receipt_manifest_hash_mismatch")

    assurance_ok, assurance_reason = _validate_assurance(assurance_by_arm, data_manifest)
    if not assurance_ok:
        return _fail(assurance_reason or "phase2_assurance_invalid")

    if not _resources_complete(final_receipt):
        return _fail("phase2_resource_accounting_incomplete_or_invalid")

    # Cheap preregistered point gate before the expensive exact resampling audit.
    ed_diffs = _paired_diffs(
        assurance_by_arm["E_ADAPTIVE_RAKL_STRUCTURAL"],
        assurance_by_arm["D_STATIC_RAKL_STRUCTURAL"],
    )
    if statistics.mean(value for _, _, value in ed_diffs) < _MATERIAL_GAIN:
        return _fail("phase2_raw_assurance_fails_registered_material_gain")

    try:
        recomputed = recompute_phase2_analysis(assurance_by_arm)
    except (KeyError, TypeError, ValueError, statistics.StatisticsError) as exc:
        return _fail(f"phase2_registered_inference_cannot_recompute:{type(exc).__name__}")
    if recomputed["terminal"] != _REQUIRED_TERMINAL:
        return _fail(f"phase2_recomputed_terminal_not_authorizing:{recomputed['terminal']}")
    if not _analysis_matches(final_receipt.get("analysis"), recomputed):
        return _fail("phase2_receipt_analysis_does_not_match_independent_recomputation")

    receipt_id = _sha(final_receipt)
    assurance_ids = tuple(_sha(list(assurance_by_arm[arm])) for arm in ARMS)
    subject = {
        "schema_version": _RESULT_SCHEMA,
        "protocol": _PROTOCOL_ID,
        "inference_plan": _INFERENCE_ID,
        "model_id": _MODEL_ID,
        "model_revision": _MODEL_REVISION,
        "data_manifest_hash": manifest_hash,
    }
    return Phase2AdaptiveAdmission(
        admitted=True,
        status="PASS",
        reasons=(
            "fresh_assurance_pairing_and_partition_disjointness_revalidated",
            "registered_inference_independently_recomputed",
            "strongest_parent_and_hard_harm_gates_passed",
            "full_resource_accounting_present",
            "training_policy_authority_only_no_scientific_authority",
        ),
        receipt_id=receipt_id,
        evaluated_subject_hash=_sha(subject),
        evidence_ids=(manifest_hash, *assurance_ids),
    )
