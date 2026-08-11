from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .paper3_annotation import canonical_sha256


_LABEL_ACCESS = {
    "external_annotation_accessed": False,
    "adjudication_accessed": False,
    "evaluated_result_accessed": False,
}

STRONG_CONTROL_ARM_FEATURES: dict[str, tuple[str, ...]] = {
    "content_cross_encoder": ("content_semantic",),
    "skill_aware_content": ("content_semantic", "skill"),
    "dependency_aware_content": ("content_semantic", "skill", "dependency"),
    "witnessed_structure_content": (
        "content_semantic",
        "skill",
        "dependency",
        "invariant",
        "boundary",
        "qoi",
        "directional",
    ),
}


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exp_value = math.exp(value)
    return exp_value / (1.0 + exp_value)


def _canonical_value(value: Any) -> str:
    if isinstance(value, list):
        return " | ".join(str(item).strip() for item in value)
    return str(value).strip()


def _render_side(
    item: dict[str, Any], *, side: str, fields: list[str], shared_fields: list[str]
) -> str:
    lines = [f"{field}: {_canonical_value(item[field])}" for field in shared_fields]
    lines.extend(
        f"{field}: {_canonical_value(item[f'{side}_{field}'])}" for field in fields
    )
    return "\n".join(lines)


def canonical_semantic_pair(item: dict[str, Any], protocol: dict[str, Any]) -> dict[str, str]:
    """Render the exact label-blind text projection consumed by the semantic control.

    Candidate invariant/boundary proposals and every annotation/outcome field are
    intentionally absent.  The returned hashes bind a score to the text rather
    than to an unverified model name or an opaque placeholder vector.
    """

    binding = protocol["content_binding"]
    fields = list(binding["side_fields"])
    shared_fields = list(binding["shared_fields"])
    source_text = _render_side(item, side="source", fields=fields, shared_fields=shared_fields)
    target_text = _render_side(item, side="target", fields=fields, shared_fields=shared_fields)
    source_hash = _sha256_text(source_text)
    target_hash = _sha256_text(target_text)
    pair_hash = hashlib.sha256(
        json.dumps(
            {"source_text_sha256": source_hash, "target_text_sha256": target_hash},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return {
        "source_text": source_text,
        "target_text": target_text,
        "source_text_sha256": source_hash,
        "target_text_sha256": target_hash,
        "pair_sha256": pair_hash,
    }


def _base_receipt(
    source_set: dict[str, Any], protocol: dict[str, Any], *, created_at_utc: str
) -> dict[str, Any]:
    return {
        "schema_version": "paper3-content-bound-semantic-descriptor-v1",
        "descriptor_id": f"{source_set.get('source_set_id', 'unknown')}:bge-reranker-v2-m3",
        "created_at_utc": created_at_utc,
        "label_access": dict(_LABEL_ACCESS),
        "protocol_id": protocol.get("protocol_id"),
        "protocol_sha256": canonical_sha256(protocol),
        "source_set_id": source_set.get("source_set_id"),
        "source_set_sha256": canonical_sha256(source_set),
        "model": deepcopy(protocol.get("semantic_model", {})),
        "runtime": {
            "device": "cpu",
            "dtype": "float32",
            "local_files_only": True,
            "batch_size": protocol.get("inference", {}).get("batch_size", 1),
        },
        "claim_boundary": (
            "Content-bound label-blind semantic-control descriptor only; not a structural-signal, "
            "training-efficiency, inference-efficiency, break-even, independent-review or peer-review result."
        ),
        "training_authorized": False,
    }


def _verify_model_assets(
    model_dir: Path, required_files: list[dict[str, Any]]
) -> tuple[list[str], list[dict[str, Any]]]:
    failures: list[str] = []
    observed: list[dict[str, Any]] = []
    for expected in required_files:
        relative = expected["path"]
        path = model_dir / relative
        if not path.is_file():
            failures.append(f"model_asset_missing:{relative}")
            continue
        size = path.stat().st_size
        digest = _sha256_file(path)
        row = {"path": relative, "bytes": size, "sha256": digest}
        observed.append(row)
        if size != expected["bytes"]:
            failures.append(f"model_asset_size_mismatch:{relative}")
        if digest != expected["sha256"]:
            failures.append(f"model_asset_sha256_mismatch:{relative}")
    return failures, observed


def build_semantic_descriptor_receipt(
    *,
    source_set: dict[str, Any],
    protocol: dict[str, Any],
    model_dir: Path,
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    """Build a local-only cross-encoder descriptor or a typed fail-closed receipt."""

    timestamp = created_at_utc or (
        datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )
    base = _base_receipt(source_set, protocol, created_at_utc=timestamp)
    preflight_failures: list[str] = []
    binding = protocol.get("content_binding", {})
    if binding.get("source_set_id") != source_set.get("source_set_id"):
        preflight_failures.append("source_set_id_mismatch")
    if binding.get("source_set_sha256") != canonical_sha256(source_set):
        preflight_failures.append("source_set_sha256_mismatch")
    attestation = source_set.get("label_blind_attestation", {})
    positive_attestation = (
        attestation.get("frozen_before_annotation") is True
        and attestation.get("no_outcome_or_diagnostic_access_during_construction") is True
    )
    negative_attestation = all(
        attestation.get(field) is False
        for field in (
            "labels_present",
            "annotation_records_present",
            "adjudication_present",
            "evaluated_results_accessed",
        )
    )
    if not (positive_attestation or negative_attestation):
        preflight_failures.append("source_set_not_attested_label_blind")
    if preflight_failures:
        return {
            **base,
            "status": "CANNOT_CHECK_CONTENT_BINDING_INVALID",
            "observed_model_files": [],
            "descriptors": [],
            "failures": preflight_failures,
        }

    asset_failures, observed = _verify_model_assets(
        model_dir, protocol["semantic_model"]["required_files"]
    )
    if asset_failures:
        return {
            **base,
            "status": "CANNOT_CHECK_MODEL_ASSET_MISSING",
            "observed_model_files": observed,
            "descriptors": [],
            "failures": asset_failures,
        }

    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        torch.use_deterministic_algorithms(True)
        torch.manual_seed(protocol["inference"]["seed"])
        tokenizer = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
        model = AutoModelForSequenceClassification.from_pretrained(
            model_dir,
            local_files_only=True,
            torch_dtype=torch.float32,
        )
        model.to("cpu")
        model.eval()
        pairs = [canonical_semantic_pair(item, protocol) for item in source_set["items"]]
        logits: list[float] = []
        batch_size = protocol["inference"]["batch_size"]
        with torch.inference_mode():
            for start in range(0, len(pairs), batch_size):
                batch = pairs[start : start + batch_size]
                encoded = tokenizer(
                    [[row["source_text"], row["target_text"]] for row in batch],
                    padding=True,
                    truncation=True,
                    max_length=protocol["inference"]["max_length_tokens"],
                    return_tensors="pt",
                )
                output = model(**encoded).logits.reshape(-1).detach().cpu().tolist()
                logits.extend(float(value) for value in output)
    except Exception as exc:  # missing/incompatible runtime is evidence, not permission to substitute
        return {
            **base,
            "status": "CANNOT_CHECK_MODEL_LOAD_OR_INFERENCE_FAILED",
            "observed_model_files": observed,
            "descriptors": [],
            "failures": [f"model_load_or_inference_failed:{type(exc).__name__}"],
        }

    descriptors = []
    for item, pair, raw_logit in zip(source_set["items"], pairs, logits, strict=True):
        descriptors.append(
            {
                "case_id": item["source_item_id"],
                "source_text_sha256": pair["source_text_sha256"],
                "target_text_sha256": pair["target_text_sha256"],
                "pair_sha256": pair["pair_sha256"],
                "raw_logit": raw_logit,
                "semantic_score": _sigmoid(raw_logit),
            }
        )
    return {
        **base,
        "status": "READY",
        "observed_model_files": observed,
        "descriptors": descriptors,
        "failures": [],
    }


def _parse_utc(value: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("timestamp must be an ISO-8601 UTC string ending in Z")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_semantic_descriptor_receipt(
    source_set: dict[str, Any],
    protocol: dict[str, Any],
    descriptor: dict[str, Any],
    *,
    first_external_label_at_utc: str | None = None,
) -> list[str]:
    failures: list[str] = []
    if descriptor.get("status") != "READY":
        failures.append("semantic_descriptor_not_ready")
    if descriptor.get("protocol_id") != protocol.get("protocol_id"):
        failures.append("protocol_id_mismatch")
    if descriptor.get("protocol_sha256") != canonical_sha256(protocol):
        failures.append("protocol_sha256_mismatch")
    if descriptor.get("source_set_id") != source_set.get("source_set_id"):
        failures.append("source_set_id_mismatch")
    if descriptor.get("source_set_sha256") != canonical_sha256(source_set):
        failures.append("source_set_sha256_mismatch")
    if descriptor.get("model") != protocol.get("semantic_model"):
        failures.append("model_binding_mismatch")
    if descriptor.get("observed_model_files") != protocol.get("semantic_model", {}).get(
        "required_files"
    ):
        failures.append("observed_model_asset_binding_mismatch")
    if descriptor.get("label_access") != _LABEL_ACCESS:
        failures.append("label_access_attestation_failed")
    if first_external_label_at_utc is not None:
        try:
            if _parse_utc(descriptor.get("created_at_utc")) >= _parse_utc(
                first_external_label_at_utc
            ):
                failures.append("descriptor_not_frozen_before_label_access")
        except (TypeError, ValueError):
            failures.append("descriptor_chronology_invalid")

    items = {
        item.get("source_item_id"): item
        for item in source_set.get("items", [])
        if isinstance(item, dict) and isinstance(item.get("source_item_id"), str)
    }
    rows = descriptor.get("descriptors", [])
    row_by_id = {
        row.get("case_id"): row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("case_id"), str)
    }
    if len(row_by_id) != len(rows) or set(row_by_id) != set(items):
        failures.append("descriptor_case_set_mismatch")
    for case_id in sorted(set(row_by_id) & set(items)):
        expected = canonical_semantic_pair(items[case_id], protocol)
        row = row_by_id[case_id]
        if any(
            row.get(key) != expected[key]
            for key in (
                "source_text_sha256",
                "target_text_sha256",
                "pair_sha256",
            )
        ):
            failures.append(f"content_binding_mismatch:{case_id}")
        score = row.get("semantic_score")
        logit = row.get("raw_logit")
        if not isinstance(score, (int, float)) or not 0.0 <= float(score) <= 1.0:
            failures.append(f"semantic_score_invalid:{case_id}")
        if not isinstance(logit, (int, float)) or not math.isfinite(float(logit)):
            failures.append(f"raw_logit_invalid:{case_id}")
        elif isinstance(score, (int, float)) and math.isfinite(float(score)):
            if not math.isclose(float(score), _sigmoid(float(logit)), rel_tol=0.0, abs_tol=1e-12):
                failures.append(f"score_transform_mismatch:{case_id}")
    return list(dict.fromkeys(failures))


def validated_semantic_scores(
    source_set: dict[str, Any],
    protocol: dict[str, Any],
    descriptor: dict[str, Any],
    *,
    first_external_label_at_utc: str | None = None,
) -> dict[str, float]:
    """Return the only admissible case-to-score map for the successor evaluator."""

    failures = validate_semantic_descriptor_receipt(
        source_set,
        protocol,
        descriptor,
        first_external_label_at_utc=first_external_label_at_utc,
    )
    if failures:
        raise ValueError(";".join(failures))
    return {
        row["case_id"]: float(row["semantic_score"])
        for row in descriptor["descriptors"]
    }
