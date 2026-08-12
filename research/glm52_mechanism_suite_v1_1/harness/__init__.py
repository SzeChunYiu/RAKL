"""Wave 2 offline experiment harnesses — arm wiring and gate logic, no model runs."""

from harness.experience_transfer_harness import (
    EXPERIENCE_ARMS,
    HOSTILE_FAMILIES,
    evaluate_dev_gate as evaluate_experience_dev_gate,
    materialize_for_arm,
    offline_selftest as experience_offline_selftest,
    run_offline_panel as run_experience_offline_panel,
)
from harness.selective_retrieval_harness import (
    RETRIEVAL_ARMS,
    evaluate_headroom_gate,
    offline_selftest as retrieval_offline_selftest,
    run_offline_panel as run_retrieval_offline_panel,
    select_for_arm,
)
from harness.trajectory_governance_harness import (
    GOVERNANCE_ARMS,
    evaluate_noninferiority_stub,
    offline_selftest as governance_offline_selftest,
    run_offline_panel as run_governance_offline_panel,
)

__all__ = [
    "EXPERIENCE_ARMS",
    "GOVERNANCE_ARMS",
    "HOSTILE_FAMILIES",
    "RETRIEVAL_ARMS",
    "evaluate_experience_dev_gate",
    "evaluate_headroom_gate",
    "evaluate_noninferiority_stub",
    "experience_offline_selftest",
    "governance_offline_selftest",
    "materialize_for_arm",
    "retrieval_offline_selftest",
    "run_experience_offline_panel",
    "run_governance_offline_panel",
    "run_retrieval_offline_panel",
    "select_for_arm",
]
