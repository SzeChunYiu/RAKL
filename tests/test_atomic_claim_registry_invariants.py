"""#542: registry + mathematics-closure invariant tests, and validator self-check.

Validates that (a) the live ATOMIC_CLAIM_REGISTRY.json + MATHEMATICS_CLOSURE.json
pass the validator, (b) the validator actually CATCHES a bounded-falsification-only
closure of a universal theorem (checker self-test, per the validate-the-checker rule),
and (c) the #542 rollback is in place.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import tools.validate_atomic_claim_registry as vac

REPO = Path(__file__).resolve().parents[1]
RES = REPO / "research" / "unified_problem_solving_v1" / "results"

REAL_REGISTRY = json.loads((RES / "ATOMIC_CLAIM_REGISTRY.json").read_text())
REAL_CLOSURE = json.loads((RES / "MATHEMATICS_CLOSURE.json").read_text())


# --------------------------------------------------------------------------- #
# (a) the live artifacts pass the validator
# --------------------------------------------------------------------------- #
def test_live_registry_and_closure_pass():
    errs = []
    vac.check_registry(REAL_REGISTRY, errs)
    vac.check_closure(REAL_CLOSURE, errs)
    assert errs == [], "live artifacts have invariant violations:\n  " + "\n  ".join(errs)


# --------------------------------------------------------------------------- #
# (b) the validator CATCHES the forbidden closure (checker self-test)
# --------------------------------------------------------------------------- #
def test_validator_rejects_bounded_falsification_only_closure_of_theorem():
    """A theorem claim open=False with BOUNDED_FALSIFICATION_ONLY must be flagged."""
    reg = copy.deepcopy(REAL_REGISTRY)
    bad = next(c for c in reg["claims"] if c["claim_id"] == "MATH-TCSQ-SOUNDNESS")
    bad["open"] = False
    bad["proof_status"] = "BOUNDED_FALSIFICATION_ONLY"
    errs = []
    vac.check_registry(reg, errs)
    assert any("MATH-TCSQ-SOUNDNESS" in e and "BOUNDED_FALSIFICATION_ONLY" in e for e in errs), (
        "validator failed to flag a bounded-falsification-only closure of a universal theorem"
    )


def test_validator_rejects_theorem_closed_without_proof_status():
    reg = copy.deepcopy(REAL_REGISTRY)
    bad = next(c for c in reg["claims"] if c["claim_id"] == "MATH-TCSQ-SOUNDNESS")
    bad["open"] = False
    bad.pop("proof_status", None)
    errs = []
    vac.check_registry(reg, errs)
    assert any("MATH-TCSQ-SOUNDNESS" in e and "proof_status" in e for e in errs)


def test_validator_accepts_closing_proof_status():
    """A theorem open=False with a legitimate closing kind must NOT be flagged."""
    reg = copy.deepcopy(REAL_REGISTRY)
    good = next(c for c in reg["claims"] if c["claim_id"] == "MATH-TCSQ-SOUNDNESS")
    good["open"] = False
    good["proof_status"] = "EXECUTABLE_INVARIANT_BY_CONSTRUCTION"
    errs = []
    vac.check_registry(reg, errs)
    assert not any("MATH-TCSQ-SOUNDNESS" in e for e in errs)


def test_closure_rejects_supported_universal_with_bounded_proof():
    closure = copy.deepcopy(REAL_CLOSURE)
    bad = next(c for c in closure["claims"] if c["statement_id"] == "astar-optimality-theorem")
    bad["terminal"] = "SUPPORTED"
    bad["universal"] = True
    bad["proof_status"] = "BOUNDED_FALSIFICATION_ONLY"  # only differential testing
    errs = []
    vac.check_closure(closure, errs)
    assert any("astar-optimality-theorem" in e for e in errs)


def test_closure_requires_axis_fields():
    closure = copy.deepcopy(REAL_CLOSURE)
    bad = closure["claims"][0]
    for fld in ("universal", "proof_status", "falsification_status"):
        bad.pop(fld, None)
    errs = []
    vac.check_closure(closure, errs)
    assert any("missing" in e for e in errs)


# --------------------------------------------------------------------------- #
# (c) the #542 rollback is present in the live artifacts
# --------------------------------------------------------------------------- #
def test_canonical_injectivity_rolled_back_to_partial():
    st = next(c for c in REAL_CLOSURE["claims"]
              if c["statement_id"] == "canonical-commitment-deterministic-encoding")
    assert st["terminal"] == "PARTIAL", (
        f"#542 rollback missing: canonical-commitment expected PARTIAL, got {st['terminal']}"
    )
    assert st["universal"] is True
    assert st["proof_status"] == "UNPROVED"
    assert st["falsification_status"] == "BOUNDED_FALSIFICATION_ONLY"


def test_registry_canonical_commitment_is_partial_open():
    rec = next(c for c in REAL_REGISTRY["claims"] if c["claim_id"] == "MATH-CANONICAL-COMMITMENT")
    assert rec["terminal_state"] == "PARTIAL"
    assert rec["open"] is True
    assert rec["proof_status"] == "UNPROVED"


def test_astar_closed_by_classical_theorem_not_bounded_only():
    st = next(c for c in REAL_CLOSURE["claims"]
              if c["statement_id"] == "astar-optimality-theorem")
    assert st["proof_status"] == "CLASSICAL_THEOREM_PLUS_IMPLEMENTATION_REFINEMENT"
    assert st["terminal"] == "SUPPORTED"
    assert st["universal"] is True


def test_sha256_is_assumption_bound():
    st = next(c for c in REAL_CLOSURE["claims"]
              if c["statement_id"] == "sha256-domain-binding")
    assert st["proof_status"] == "CRYPTOGRAPHIC_ASSUMPTION_BOUND"
    # eligible for SUPPORTED precisely because it is explicitly assumption-bound
    assert st["terminal"] == "SUPPORTED"


def test_all_13_closure_statements_have_receipts():
    for st in REAL_CLOSURE["claims"]:
        fc = st.get("finite_check", {}) or {}
        if st["terminal"] == "ARCHITECTURE_ONLY":
            assert fc.get("receipt") is None, f"{st['statement_id']}: ARCHITECTURE_ONLY should have null receipt"
        else:
            assert fc.get("receipt"), f"{st['statement_id']}: missing executable receipt"


if __name__ == "__main__":
    sys.exit(__import__("pytest").main([__file__, "-v"]))
