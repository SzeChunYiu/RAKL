#!/usr/bin/env python3
"""Validate ATOMIC_CLAIM_REGISTRY.json + MATHEMATICS_CLOSURE.json invariants.

Central single-writer check. Exit 0 = all hard invariants hold; 1 = violations.

Checks:
  REGISTRY:
    - terminal vocabulary; non-empty claim/falsifier; artifact existence + sha256 match
    - global authority/completeness flags are False
    - #542 RULE: a theorem-type claim with open=False MUST carry a proof_status in
      CLOSING_KINDS. Bounded falsification of a strict subdomain (BOUNDED_FALSIFICATION_ONLY,
      PROPERTY_TEST_ONLY) or UNPROVED may NOT close a universal theorem.
  CLOSURE (schema v2):
    - every statement carries universal / proof_status / falsification_status
    - terminal SUPPORTED + universal => proof_status in CLOSING_KINDS (same rule, fine-grained)
    - every finite_check.receipt names a real file (or is explicitly null for a
      CANNOT_CHECK/ARCHITECTURE_ONLY statement that has no executable check)

Run: PYTHONPATH=src python tools/validate_atomic_claim_registry.py
"""
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RES = REPO / "research" / "unified_problem_solving_v1" / "results"
ACR = RES / "ATOMIC_CLAIM_REGISTRY.json"
CLOSURE = RES / "MATHEMATICS_CLOSURE.json"
VOCAB = {
    "SUPPORTED", "PARTIAL", "NEGATIVE", "CANNOT_CHECK", "UNDERPOWERED",
    "INVALID_CONTAMINATED", "ARCHITECTURE_ONLY", "SCAFFOLD",
}
# all 9 evidence kinds from the #542 taxonomy
PROOF_KINDS = {
    "EXECUTABLE_INVARIANT_BY_CONSTRUCTION",
    "FINITE_DOMAIN_EXHAUSTIVE_PROOF",
    "BOUNDED_FALSIFICATION_ONLY",
    "PROPERTY_TEST_ONLY",
    "ALGEBRAIC_PROOF",
    "CLASSICAL_THEOREM_PLUS_IMPLEMENTATION_REFINEMENT",
    "CRYPTOGRAPHIC_ASSUMPTION_BOUND",
    "MECHANIZED_PROOF",
    "UNPROVED",
}
# kinds that may legitimately set a UNIVERSAL theorem to open=False / SUPPORTED
CLOSING_KINDS = PROOF_KINDS - {"BOUNDED_FALSIFICATION_ONLY", "PROPERTY_TEST_ONLY", "UNPROVED"}
FALS_KINDS = {
    "FINITE_DOMAIN_EXHAUSTIVE_PROOF",
    "BOUNDED_FALSIFICATION_ONLY",
    "PROPERTY_TEST_ONLY",
    "CANNOT_CHECK",
}


def sha_pref(p, n=16):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for ch in iter(lambda: f.read(65536), b""):
            h.update(ch)
    return h.hexdigest()[:n]


def resolve(art):
    cands = [Path(art), REPO / art, RES / art, RES.parent / art]
    return next((c for c in cands if c.exists()), None)


def check_registry(r, errs):
    if r.get("grants_scientific_authority") is not False:
        errs.append("grants_scientific_authority != false")
    if r.get("global_completeness_claimed") is not False:
        errs.append("global_completeness_claimed != false")
    for c in r["claims"]:
        cid = c.get("claim_id", "?")
        if c.get("terminal_state") not in VOCAB:
            errs.append(f"{cid}: terminal not in vocabulary: {c.get('terminal_state')!r}")
        if not str(c.get("claim", "")).strip():
            errs.append(f"{cid}: empty claim")
        if not str(c.get("falsifier", "")).strip():
            errs.append(f"{cid}: empty falsifier")
        art = c.get("artifact")
        if art:
            f = resolve(art)
            if not f:
                errs.append(f"{cid}: artifact not found: {art}")
            else:
                rec = c.get("artifact_sha256_prefix")
                if rec:
                    act = sha_pref(f)
                    if not act.startswith(rec):
                        errs.append(f"{cid}: sha mismatch rec={rec} actual={act} ({art})")
        # #542 core rule: theorem + open=False needs a closing proof_status
        if c.get("claim_type") == "theorem" and c.get("open") is False:
            ps = c.get("proof_status")
            if ps is None:
                errs.append(f"{cid}: theorem open=False without proof_status (cannot certify closure)")
            elif ps not in CLOSING_KINDS:
                errs.append(
                    f"{cid}: theorem open=False closed by non-closing proof_status={ps}; "
                    f"bounded falsification / property testing / UNPROVED may not close a "
                    f"universal statement (#542)"
                )


def check_closure(closure, errs):
    if not CLOSURE.exists():
        errs.append("MATHEMATICS_CLOSURE.json not found")
        return
    for st in closure.get("claims", []):
        sid = st.get("statement_id", "?")
        for fld in ("universal", "proof_status", "falsification_status"):
            if fld not in st:
                errs.append(f"{sid}: closure statement missing {fld} (#542 axis)")
        ps = st.get("proof_status")
        if ps is not None and ps not in PROOF_KINDS:
            errs.append(f"{sid}: proof_status {ps!r} not in evidence taxonomy")
        fs = st.get("falsification_status")
        if fs is not None and fs not in FALS_KINDS:
            errs.append(f"{sid}: falsification_status {fs!r} not in falsification taxonomy")
        # fine-grained version of the #542 rule
        if st.get("terminal") == "SUPPORTED" and st.get("universal") and ps not in CLOSING_KINDS:
            errs.append(
                f"{sid}: SUPPORTED+universal with non-closing proof_status={ps}; "
                f"bounded testing of a strict subdomain cannot close a universal (#542)"
            )
        fc = st.get("finite_check", {}) or {}
        receipt = fc.get("receipt")
        term = st.get("terminal")
        if receipt is None:
            if term not in ("ARCHITECTURE_ONLY",):
                errs.append(f"{sid}: finite_check.receipt is null but terminal={term} (expected a named test)")
        else:
            # receipt names a path like tests/... or tests/...::sym; the leading path must exist
            path_part = receipt.split("::")[0].split(" ")[0].strip("(")
            if path_part and not (REPO / path_part).exists():
                errs.append(f"{sid}: receipt names non-existent path {path_part!r}")


def main():
    errs = []
    r = json.loads(ACR.read_text())
    check_registry(r, errs)
    if CLOSURE.exists():
        check_closure(json.loads(CLOSURE.read_text()), errs)
    print(f"claims={len(r['claims'])} by_terminal={r['summary']['by_terminal']} open={r['summary']['open']}")
    print(f"hard-invariant violations: {len(errs)}")
    for e in errs:
        print("  VIOLATION:", e)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
