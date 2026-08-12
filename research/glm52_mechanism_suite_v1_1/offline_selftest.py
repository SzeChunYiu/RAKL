from __future__ import annotations

from harness.experience_transfer_harness import offline_selftest as experience_test
from harness.selective_retrieval_harness import offline_selftest as retrieval_test
from harness.trajectory_governance_harness import offline_selftest as governance_test


def main() -> int:
    retrieval_test()
    experience_test()
    governance_test()
    print("glm52 v1.1 wave2 offline self-tests: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
