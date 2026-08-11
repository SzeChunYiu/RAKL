"""Frozen hostile discriminator for failure-lattice link endpoints (issue #133).

Defect under test: ``schemas/failure-experience-lattice.schema.json`` accepted
arbitrary nonempty ``source_id``/``target_id`` strings, so a schema-valid
``RESOLVED_BY`` link whose target is a *candidate* id validated cleanly while
``src/rakl/failure_lattice.add_failure_link`` rejected the same artifact with
``ValueError: failure links require existing source and target experiences``.
Schema validation passed while executable reconstruction failed.

The three worlds below are frozen exactly as issue #133 enumerates them, and the
binding requirement is **agreement** between two independent validators:

* declared contract — ``jsonschema`` validation plus the reference constraints
  the schema itself declares, interpreted by the generic companion validator
  ``rakl.schema_reference_constraints``;
* executable reconstruction — replaying the document through the same
  constructors the runtime uses.

The two sides are not proxies for one another: the declared side is driven by
data in the schema document, the executable side by ``failure_lattice.py``. If
either moves without the other, the worlds below disagree and this file fails.

Endpoint checks are not relaxed to obtain a pass: the disagreement is resolved
by making the declared contract no *more* permissive than the runtime.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, Tuple

import jsonschema
import pytest

from rakl.failure_lattice import reconstruct_failure_lattice
from rakl.schema_reference_constraints import (
    check_reference_constraints,
    load_reference_constraints,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas" / "failure-experience-lattice.schema.json"

ACCEPT = "ACCEPT"
REJECT = "REJECT"


def _schema() -> Dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _experience(*, failure_id: str, candidate_id: str) -> Dict[str, Any]:
    return {
        "failure_id": failure_id,
        "atom_id": "A-ROOT-BRIDGE",
        "candidate_id": candidate_id,
        "context_packet_hash": "ctx-hash-1",
        "research_trace_event_id": f"trace-{failure_id}",
        "method_family": "spectral-ratio",
        "failure_mode": "bound does not survive unrestricted reuse",
        "residual_signature": ["reuse_gap"],
        "broken_assumptions": ["tree_like_recomputation"],
        "scope_conditions": ["same unrestricted reuse model"],
        "competing_diagnoses": ["wrong invariant", "model mismatch"],
        "selected_diagnosis": "model mismatch",
        "diagnosis_status": "SUPPORTED",
        "evidence_pointers": [f"artifact:{failure_id}"],
        "falsifier_or_attempt": "compare restricted lower bound with unrestricted construction",
        "observed_result": "counterexample at rank 3",
        "local_repair_attempts": [],
        "timestamp": "2026-08-11T09:00:00Z",
        "artifact_hash": f"hash-{failure_id}",
    }


def _document(links: list[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "experiences": [
            _experience(failure_id="F-1", candidate_id="C-ORIGINAL-1"),
            _experience(failure_id="F-2", candidate_id="C-REPAIR-1"),
        ],
        "links": links,
    }


def _link(*, source_id: str, target_id: str, relation: str) -> Dict[str, Any]:
    return {
        "source_id": source_id,
        "target_id": target_id,
        "relation": relation,
        "rationale": "structurally related failure record",
        "evidence_pointers": ["artifact:link-1"],
    }


# --- the three frozen worlds -------------------------------------------------

# World 1: schema-valid and runtime-valid failure-to-failure link.
WORLD_1_FAILURE_TO_FAILURE = _document(
    [_link(source_id="F-1", target_id="F-2", relation="SHARES_RESIDUAL_WITH")]
)

# World 2: the reported application artifact — a RESOLVED_BY link whose target is
# the correcting *candidate* id rather than a registered failure id.
WORLD_2_CANDIDATE_TARGET = _document(
    [_link(source_id="F-1", target_id="C-REPAIR-1", relation="RESOLVED_BY")]
)

# World 3: an endpoint that names nothing at all; must fail closed.
WORLD_3_UNKNOWN_TARGET = _document(
    [_link(source_id="F-1", target_id="F-DOES-NOT-EXIST", relation="SHARES_RESIDUAL_WITH")]
)


# --- the two independent validators -----------------------------------------


def _declared_contract_verdict(
    document: Dict[str, Any], *, schema: Dict[str, Any] | None = None
) -> Tuple[str, Tuple[str, ...]]:
    """jsonschema validation plus the reference constraints the schema declares."""

    schema = _schema() if schema is None else schema
    try:
        jsonschema.validate(document, schema)
    except jsonschema.ValidationError as error:
        return REJECT, (f"jsonschema:{error.message}",)

    reasons = check_reference_constraints(document, schema)
    return (REJECT, reasons) if reasons else (ACCEPT, ())


def _executable_reconstruction_verdict(document: Dict[str, Any]) -> Tuple[str, Tuple[str, ...]]:
    """Replay the document through the constructors the runtime actually uses."""

    try:
        reconstruct_failure_lattice(document)
    except ValueError as error:
        return REJECT, (f"runtime:{error}",)
    return ACCEPT, ()


def _assert_validators_agree(
    document: Dict[str, Any],
    *,
    expected: str,
    world: str,
    schema: Dict[str, Any] | None = None,
) -> None:
    declared, declared_reasons = _declared_contract_verdict(document, schema=schema)
    executable, executable_reasons = _executable_reconstruction_verdict(document)

    assert declared == executable, (
        f"{world}: declared contract says {declared} while executable reconstruction says "
        f"{executable}; schema validation and runtime reconstruction must agree "
        f"(declared reasons={declared_reasons}, runtime reasons={executable_reasons})"
    )
    assert declared == expected, (
        f"{world}: both validators returned {declared}, expected {expected} "
        f"(declared reasons={declared_reasons}, runtime reasons={executable_reasons})"
    )


def test_world_1_failure_to_failure_link_is_accepted_by_both() -> None:
    _assert_validators_agree(
        WORLD_1_FAILURE_TO_FAILURE, expected=ACCEPT, world="world 1 (failure-to-failure)"
    )


def test_world_2_candidate_target_resolved_by_link_agrees() -> None:
    """The reported defect: schema accepted what the runtime rejected."""

    _assert_validators_agree(
        WORLD_2_CANDIDATE_TARGET, expected=REJECT, world="world 2 (candidate target)"
    )


def test_world_3_unknown_target_fails_closed_in_both() -> None:
    _assert_validators_agree(
        WORLD_3_UNKNOWN_TARGET, expected=REJECT, world="world 3 (unknown target)"
    )


def test_unknown_source_endpoint_also_fails_closed_in_both() -> None:
    """Symmetry check beyond the three frozen worlds: sources are endpoints too."""

    document = _document(
        [_link(source_id="F-UNREGISTERED", target_id="F-2", relation="SHARES_RESIDUAL_WITH")]
    )
    _assert_validators_agree(document, expected=REJECT, world="unknown source")


# --- honest scope of the repair ---------------------------------------------


def test_json_schema_alone_still_accepts_the_candidate_target_world() -> None:
    """The schema alone does not close the gap; schema plus companion does.

    Recorded executably so the claim cannot drift into an overclaim: pure
    ``jsonschema`` validation of world 2 raises nothing, and the rejection comes
    entirely from the declared reference constraints interpreted by the
    companion validator.
    """

    schema = _schema()
    jsonschema.validate(WORLD_2_CANDIDATE_TARGET, schema)  # must not raise
    assert check_reference_constraints(WORLD_2_CANDIDATE_TARGET, schema)


def test_schema_declares_its_companion_reference_constraints() -> None:
    """Deleting the declaration must not silently reopen the gap."""

    schema = _schema()
    constraints = load_reference_constraints(schema)
    assert constraints, "schema no longer declares any reference constraint"
    declared_endpoints = {constraint.source_path for constraint in constraints}
    assert {"links[*].source_id", "links[*].target_id"} <= declared_endpoints, (
        "both link endpoints must be declared reference constraints"
    )


def test_agreement_helper_observes_the_pre_fix_disagreement() -> None:
    """Validate the checker: the agreement assertion is not vacuous.

    Strip the declared constraints from an in-memory copy of the schema and the
    declared side reverts to pre-fix behaviour, which is exactly the
    disagreement issue #133 reported. The helper itself must raise.
    """

    weakened = _schema()
    weakened.pop("x-rakl-reference-constraints")

    with pytest.raises(AssertionError, match="declared contract says"):
        _assert_validators_agree(
            copy.deepcopy(WORLD_2_CANDIDATE_TARGET),
            expected=REJECT,
            world="world 2 with the schema declaration removed",
            schema=weakened,
        )


def test_runtime_rejection_message_is_the_reported_one() -> None:
    with pytest.raises(ValueError, match="existing source and target experiences"):
        reconstruct_failure_lattice(WORLD_2_CANDIDATE_TARGET)
