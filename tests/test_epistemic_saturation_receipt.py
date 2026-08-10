from __future__ import annotations

import json
from pathlib import Path

from rakl.epistemic_saturation import (
    EpistemicGrowthVector,
    OperatorOrderAudit,
    SaturationBasis,
    SaturationRound,
    SaturationStatus,
    audit_bounded_epistemic_saturation,
)


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "research" / "EPISTEMIC_MECHANICS_SATURATION_v1.json"


def _growth(data: dict[str, int]) -> EpistemicGrowthVector:
    return EpistemicGrowthVector(**data)


def test_epistemic_mechanics_saturation_receipt_replays_exactly():
    data = json.loads(RECEIPT.read_text(encoding="utf-8"))
    basis = SaturationBasis(
        basis_id="epistemic-mechanics-longform-v1",
        scope="long-form Epistemic Mechanics paper and supporting RAKL epistemic-saturation framework",
        identity_policy_id="claim-mechanism-evidence-v1",
        route_family_version="owmd-v1+operator-order-v1",
        novelty_policy_id="nearest-work-equivalence-v1",
        evidence_policy_id="typed-authority-v1",
    )
    assert data["basis_fingerprint"] == basis.fingerprint
    assert data["absolute_complete"] is False

    rounds = []
    for item in data["rounds"]:
        order = item["operator_order_audit"]
        rounds.append(
            SaturationRound(
                round_id=item["round_id"],
                basis_fingerprint=item["basis_fingerprint"],
                growth=_growth(item["growth"]),
                bounded_discovery_closed=item["bounded_discovery_closed"],
                route_coverage_stable=item["route_coverage_stable"],
                omission_audit_passed=item["omission_audit_passed"],
                nearest_work_audit_passed=item["nearest_work_audit_passed"],
                operator_order_audit=OperatorOrderAudit(
                    audit_id=order["audit_id"],
                    expand_then_consolidate_digest=order["expand_then_consolidate_digest"],
                    consolidate_then_expand_digest=order["consolidate_then_expand_digest"],
                    substantive_difference=_growth(order["substantive_difference"]),
                    evidence_ids=tuple(order["evidence_ids"]),
                ),
                freshness_cutoff=item["freshness_cutoff"],
                blocking_fibers=tuple(item["blocking_fibers"]),
                representation_only_changes=item.get("representation_only_changes", 0),
            )
        )

    report = audit_bounded_epistemic_saturation(
        rounds,
        basis=basis,
        required_consecutive_flat_rounds=data["required_consecutive_flat_rounds"],
        required_freshness_cutoff=data["required_freshness_cutoff"],
    )
    assert report.status is SaturationStatus.BOUNDED_SATURATED
    assert report.status.value == data["status"]
    assert report.consecutive_flat_rounds == 2
    assert report.absolute_complete is False
    assert not report.reasons
