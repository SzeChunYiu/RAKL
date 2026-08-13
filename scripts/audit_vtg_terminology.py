#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

from rakl.formal_contracts import METHOD_SURFACES


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "research" / "unified_problem_solving_v1" / "VTG_TERMINOLOGY_LEDGER.json"
RESULT = ROOT / "research" / "unified_problem_solving_v1" / "results" / "vtg_terminology_audit.json"


def audit(data: dict) -> list[str]:
    problems: list[str] = []
    if data.get("schema") != "orion.vtg.terminology-ledger.v1":
        problems.append("schema_mismatch")
    if not data.get("ledger_id"):
        problems.append("ledger_id_missing")
    entries = data.get("entries") or []
    if not entries:
        problems.append("entries_missing")
        return problems

    ids = [str(row.get("concept_id", "")).strip() for row in entries]
    canonicals = [str(row.get("canonical_term", "")).strip() for row in entries]
    if any(not item for item in ids):
        problems.append("concept_id_missing")
    if len(ids) != len(set(ids)):
        problems.append("duplicate_concept_id")
    if any(not item for item in canonicals):
        problems.append("canonical_term_missing")
    if len(canonicals) != len(set(canonicals)):
        problems.append("duplicate_canonical_term")

    synonym_owner: dict[str, str] = {}
    for row in entries:
        cid = str(row.get("concept_id", "")).strip()
        canonical = str(row.get("canonical_term", "")).strip()
        owner = str(row.get("owner_surface", "")).strip()
        distinction = str(row.get("distinction", "")).strip()
        synonyms = tuple(str(item).strip() for item in row.get("synonyms", ()))
        false_friends = tuple(str(item).strip() for item in row.get("must_not_conflate_with", ()))

        if owner not in METHOD_SURFACES:
            problems.append(f"{cid}:owner_surface_not_canonical:{owner}")
        if not distinction:
            problems.append(f"{cid}:distinction_missing")
        if not false_friends:
            problems.append(f"{cid}:false_conflation_set_missing")
        if len(synonyms) != len(set(synonyms)) or any(not item for item in synonyms):
            problems.append(f"{cid}:invalid_synonyms")
        if len(false_friends) != len(set(false_friends)) or any(not item for item in false_friends):
            problems.append(f"{cid}:invalid_false_friends")
        if canonical in false_friends:
            problems.append(f"{cid}:canonical_self_conflation")
        for synonym in synonyms:
            if synonym == canonical:
                problems.append(f"{cid}:canonical_repeated_as_synonym")
            previous = synonym_owner.get(synonym)
            if previous is not None and previous != cid:
                problems.append(f"false_merge_synonym:{synonym}:{previous}:{cid}")
            synonym_owner[synonym] = cid

    # A canonical term may appear as another concept's false friend, but it may
    # never be assigned as a synonym of a different concept.
    canonical_owner = dict(zip(canonicals, ids))
    for synonym, cid in synonym_owner.items():
        other = canonical_owner.get(synonym)
        if other is not None and other != cid:
            problems.append(f"false_merge_canonical_synonym:{synonym}:{other}:{cid}")
    return problems


def main() -> int:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    problems = audit(data)
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "schema": "orion.vtg.terminology-audit.v1",
        "ledger_id": data.get("ledger_id"),
        "entry_count": len(data.get("entries") or []),
        "valid": not problems,
        "problems": problems,
        "scientific_authority_granted": False,
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"VTG_TERMINOLOGY_ENTRIES={result['entry_count']}")
    print(f"VTG_TERMINOLOGY_VALID={'true' if result['valid'] else 'false'}")
    print("SCIENTIFIC_AUTHORITY_GRANTED=false")
    for problem in problems:
        print(problem, file=sys.stderr)
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
