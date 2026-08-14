"""Arm executor for BENEFIT-L3-AUTHORITY-V1. One process per arm (step 2 spawns
each separately) over the byte-identical gold-stripped corpus.

Arm A — ungoverned upgrade, PROTOCOL.json arms.A_ungoverned_upgrade, implemented
verbatim to the frozen decision-equivalent rule in EVALUATOR.py (UPGRADE iff
every cited evidence id resolves in the registry; review verdicts, content
hashes, lineage, scope, axis licensing and freeze chronology are present in the
input record and deliberately ignored).

Arm B — certificate-gated upgrade: encodes each record as the exact pinned
framework objects (rakl.claim_evidence.ClaimAtom, rakl.authority_ledger.
AuthorityProposal, per-evidence rakl.evidence_binding_certificate.
ReviewedEvidenceBinding over rakl.v3_scientific_authority.
ScientificEvidenceBinding registrations) and calls
evaluate_evidence_binding_for_promotion (module pins verified before any
declaration). UPGRADE iff the verdict is VALID_FOR_PROMOTION_CHALLENGER, in
which case the upgrade is realized as AuthorityLedger.commit_verified(...,
outcome=SUPPORTED) and the declaration is read back from the ACTUAL ledger
active-certificate state, so ALR measures real ledger commitments. INVALID,
CONFLICT_REQUIRES_RESOLUTION and CANNOT_CHECK all map to REFUSED (fail-closed)
with the sub-verdict and reasons retained for the per-class read.

Encoding notes (record -> framework objects), bookkeeping constants only —
none of these fields participates in any verdict branch of the pinned module:
- ClaimAtom.text is the record's claim text_sha256 string (the corpus schema
  frozen in CORPUS_PLAN.md carries the claim text digest, not the raw text;
  the module only requires non-empty text and hashes it into the certificate).
- ClaimEvidenceLink.selector is a constant TextSpanSelector(0, 1, "x") with
  selector_frozen_before_review=True; the binding gate reads identity, digest,
  relation and review fields only.
- AuthorityProposal.proposition is the constant f"authority-upgrade:{claim_id}".
"""
from __future__ import annotations

import argparse
import json
import os
import resource
import sys
import time
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import verify_module_pins  # noqa: E402

from rakl.authority_ledger import (  # noqa: E402
    AuthorityAxis,
    AuthorityLedger,
    AuthorityProposal,
    VerificationOutcome,
)
from rakl.claim_evidence import (  # noqa: E402
    ClaimAtom,
    ClaimEvidenceLink,
    ClaimEvidenceReport,
    ClaimEvidenceVerdict,
    EvidenceRelation,
    EvidenceReviewVerdict,
    TextSpanSelector,
)
from rakl.epistemic_noninterference import EvidenceRootKind  # noqa: E402
from rakl.evidence_binding_certificate import (  # noqa: E402
    EvidenceBindingVerdict,
    ReviewedEvidenceBinding,
    evaluate_evidence_binding_for_promotion,
)
from rakl.v3_scientific_authority import ScientificEvidenceBinding  # noqa: E402


def arm_a_declare(row: dict[str, Any]) -> dict[str, Any]:
    evidence_ids = row["proposal"].get("evidence_ids") or []
    registry = row["registry"]
    declaration = "UPGRADE"
    if not evidence_ids:
        declaration = "REFUSED"
    else:
        for evidence_id in evidence_ids:
            if evidence_id not in registry:
                declaration = "REFUSED"
                break
    return {"claim_id": row["claim_id"], "declaration": declaration}


_SELECTOR = TextSpanSelector(start=0, end=1, exact="x")


def _encode(row: dict[str, Any]):
    claim = ClaimAtom(
        claim_id=row["claim"]["claim_id"],
        text=row["claim"]["text_sha256"],
        scope=row["claim"]["scope"],
    )
    proposal = AuthorityProposal(
        proposal_id=row["proposal"]["proposal_id"],
        claim_id=row["proposal"]["claim_id"],
        axis=AuthorityAxis(row["proposal"]["axis"]),
        proposition=f"authority-upgrade:{row['claim_id']}",
        scope_id=row["proposal"]["scope_id"],
        evidence_ids=tuple(row["proposal"]["evidence_ids"]),
    )
    registered = {
        evidence_id: ScientificEvidenceBinding(
            evidence_id=evidence_id,
            kind=EvidenceRootKind(entry["kind"]),
            content_sha256=entry["content_sha256"],
            supports_axes=tuple(AuthorityAxis(a) for a in entry["supports_axes"]),
            upstream_evidence_id=entry["upstream_evidence_id"],
        )
        for evidence_id, entry in row["registry"].items()
    }
    bindings = []
    for item in row["bindings"]:
        link_rec, report_rec = item["link"], item["report"]
        relation = EvidenceRelation(link_rec["proposed_relation"])
        link = ClaimEvidenceLink(
            link_id=link_rec["link_id"],
            claim_id=link_rec["claim_id"],
            source_id=link_rec["source_id"],
            source_sha256=link_rec["source_sha256"],
            selector=_SELECTOR,
            proposed_relation=relation,
            selector_frozen_before_review=True,
        )
        reviewed = (None if report_rec["reviewed_relation"] is None
                    else EvidenceReviewVerdict(report_rec["reviewed_relation"]))
        report = ClaimEvidenceReport(
            verdict=ClaimEvidenceVerdict(report_rec["verdict"]),
            claim_id=report_rec["claim_id"],
            link_id=report_rec["link_id"],
            source_id=report_rec["source_id"],
            locator_verified=report_rec["locator_verified"],
            semantic_review_verified=report_rec["semantic_review_verified"],
            proposed_relation=EvidenceRelation(report_rec["proposed_relation"]),
            reviewed_relation=reviewed,
            reasons=(),
        )
        bindings.append(ReviewedEvidenceBinding(
            evidence_id=item["evidence_id"], link=link, report=report))
    return claim, proposal, bindings, registered


def make_arm_b(ledger: AuthorityLedger):
    def arm_b_declare(row: dict[str, Any]) -> dict[str, Any]:
        claim, proposal, bindings, registered = _encode(row)
        assessment = evaluate_evidence_binding_for_promotion(
            claim,
            proposal,
            bindings,
            registered,
            certificate_id=f"{row['claim_id']}:binding-cert",
            missing_obligations=tuple(row["missing_obligations"]),
            frozen_before_promotion=row["frozen_before_promotion"],
        )
        if assessment.verdict is EvidenceBindingVerdict.VALID_FOR_PROMOTION_CHALLENGER:
            certificate = ledger.commit_verified(
                proposal,
                certificate_id=f"{row['claim_id']}:authority-cert",
                outcome=VerificationOutcome.SUPPORTED,
            )
            committed = (certificate is not None
                         and certificate.certificate_id in ledger.active_ids)
            return {
                "claim_id": row["claim_id"],
                "declaration": "UPGRADE" if committed else "REFUSED",
                "sub_verdict": assessment.verdict.value,
                "ledger_certificate_id": None if certificate is None else certificate.certificate_id,
                "ledger_active": committed,
            }
        return {
            "claim_id": row["claim_id"],
            "declaration": "REFUSED",
            "sub_verdict": assessment.verdict.value,
            "reasons": list(assessment.reasons),
        }
    return arm_b_declare


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", required=True, choices=("A", "B"))
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    verify_module_pins()
    with open(args.corpus, "r", encoding="utf-8") as handle:
        rows = json.load(handle)["claims"]
    for row in rows:
        if "gold_label" in row or "class" in row:
            print("REFUSING: arm input contains gold/class fields", file=sys.stderr)
            return 2

    ledger = AuthorityLedger()
    declare = arm_a_declare if args.arm == "A" else make_arm_b(ledger)
    t0 = time.monotonic()
    declarations = [declare(row) for row in sorted(rows, key=lambda r: r["claim_id"])]
    elapsed = time.monotonic() - t0
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    payload = {
        "protocol_id": "BENEFIT-L3-AUTHORITY-V1",
        "arm": args.arm,
        "declarations": declarations,
        "n_declared_upgrade": sum(1 for d in declarations if d["declaration"] == "UPGRADE"),
        "ledger_active_certificates": len(ledger.active_ids) if args.arm == "B" else None,
        "wall_clock_seconds": elapsed,
        "peak_rss_bytes": peak_rss,
        "token_budget_used": 0,
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
