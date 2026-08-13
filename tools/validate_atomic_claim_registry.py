#!/usr/bin/env python3
"""Validate ATOMIC_CLAIM_REGISTRY.json hard invariants (central single-writer check).

Checks terminal vocabulary, non-empty claim/falsifier, artifact existence + sha256-prefix
match, and the global authority flags. Does NOT enforce a heuristic on the `open` field
semantic (documented in the registry `policy`).

Run: PYTHONPATH=src python tools/validate_atomic_claim_registry.py
Exit 0 = all hard invariants hold; 1 = violations found.
"""
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RES = REPO / "research" / "unified_problem_solving_v1" / "results"
ACR = RES / "ATOMIC_CLAIM_REGISTRY.json"
VOCAB = {
    "SUPPORTED", "PARTIAL", "NEGATIVE", "CANNOT_CHECK", "UNDERPOWERED",
    "INVALID_CONTAMINATED", "ARCHITECTURE_ONLY", "SCAFFOLD",
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


def main():
    r = json.loads(ACR.read_text())
    errs = []
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
    print(f"claims={len(r['claims'])} by_terminal={r['summary']['by_terminal']} open={r['summary']['open']}")
    print(f"hard-invariant violations: {len(errs)}")
    for e in errs:
        print("  VIOLATION:", e)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
