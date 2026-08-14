from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Tuple

# Deliberately unset until a real LUNARC R0 runtime capture has been reviewed
# and committed as RUNTIME_FREEZE_V1.json.  This source constant is the governed
# production trust root: a caller cannot self-authorize by supplying an arbitrary
# matching freeze object at runtime.
APPROVED_PHASE2_RUNTIME_FREEZE_SHA256: str | None = None

_RUNTIME_RECEIPT_SCHEMA = "rakl-paper4-phase2-runtime-execution-receipt-v1"
_MODEL_REVISION = "a09a35458c702b33eeacc393d103063234e8bc28"
_PROTOCOL_BLOB = "0ca5aa15dc078ec92e82ab4aff94e5ffcf16b0af"
_INFERENCE_BLOB = "2d31897ea6441d280519276e0f1fb3323bf03f99"
_PHASE2_RUNNER_BLOB = "5ade3b9fea3fc029870782d1157a867bc4feb700"


@dataclass(frozen=True)
class Phase2RuntimeActivationGate:
    allowed: bool
    reasons: Tuple[str, ...]
    runtime_freeze_sha256: str | None = None

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(ch in "0123456789abcdef" for ch in value)
    )


def evaluate_phase2_runtime_activation(
    runtime_execution_receipt: Mapping[str, object] | None = None,
) -> Phase2RuntimeActivationGate:
    """Require a governed runtime freeze before adaptive policy activation.

    The Phase-2 statistical/result bundle may be internally admissible while the
    execution environment is not yet an approved scientific subject.  These are
    separate coordinates.  Until a reviewed RUNTIME_FREEZE_V1 digest is compiled
    into this module, this gate always retains the static parent.

    Once that digest is set by a separately reviewed pre-outcome source change,
    the caller must additionally provide the exact execution receipt emitted by
    the runtime-frozen LUNARC successor.  A caller-provided freeze digest alone is
    not a trust root.
    """

    approved = APPROVED_PHASE2_RUNTIME_FREEZE_SHA256
    if approved is None:
        return Phase2RuntimeActivationGate(
            False,
            (
                "phase2_runtime_freeze_not_yet_governed",
                "static_parent_retained_until_preoutcome_runtime_capture_is_committed",
            ),
        )
    if not _is_sha256(approved):
        return Phase2RuntimeActivationGate(
            False, ("phase2_governed_runtime_freeze_digest_invalid",)
        )
    if not isinstance(runtime_execution_receipt, Mapping):
        return Phase2RuntimeActivationGate(
            False,
            ("phase2_runtime_execution_receipt_missing",),
            approved,
        )
    if runtime_execution_receipt.get("schema_version") != _RUNTIME_RECEIPT_SCHEMA:
        return Phase2RuntimeActivationGate(
            False, ("phase2_runtime_execution_receipt_schema_mismatch",), approved
        )
    if runtime_execution_receipt.get("runtime_freeze_sha256") != approved:
        return Phase2RuntimeActivationGate(
            False, ("phase2_runtime_freeze_binding_mismatch",), approved
        )
    if runtime_execution_receipt.get("model_revision") != _MODEL_REVISION:
        return Phase2RuntimeActivationGate(
            False, ("phase2_runtime_model_revision_mismatch",), approved
        )
    frozen_blobs = runtime_execution_receipt.get("frozen_scientific_blobs")
    if not isinstance(frozen_blobs, Mapping):
        return Phase2RuntimeActivationGate(
            False, ("phase2_runtime_scientific_blob_binding_missing",), approved
        )
    expected = {
        "PROTOCOL_V3.json": _PROTOCOL_BLOB,
        "INFERENCE_PLAN.json": _INFERENCE_BLOB,
        "phase2_adaptive_v1.py": _PHASE2_RUNNER_BLOB,
    }
    if dict(frozen_blobs) != expected:
        return Phase2RuntimeActivationGate(
            False, ("phase2_runtime_scientific_blob_binding_mismatch",), approved
        )
    if runtime_execution_receipt.get("runtime_matches_freeze") is not True:
        return Phase2RuntimeActivationGate(
            False, ("phase2_runtime_environment_did_not_match_freeze",), approved
        )
    if runtime_execution_receipt.get("network_package_install_performed") is not False:
        return Phase2RuntimeActivationGate(
            False, ("phase2_runtime_package_install_detected",), approved
        )
    if runtime_execution_receipt.get("model_substitution_performed") is not False:
        return Phase2RuntimeActivationGate(
            False, ("phase2_runtime_model_substitution_detected",), approved
        )
    if runtime_execution_receipt.get("grants_scientific_authority") is not False:
        return Phase2RuntimeActivationGate(
            False, ("phase2_runtime_receipt_authority_boundary_invalid",), approved
        )
    return Phase2RuntimeActivationGate(
        True,
        (
            "governed_phase2_runtime_freeze_bound",
            "execution_runtime_matches_preoutcome_freeze",
            "no_runtime_or_model_substitution_detected",
        ),
        approved,
    )
