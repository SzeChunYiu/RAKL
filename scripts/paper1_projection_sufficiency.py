from __future__ import annotations

import json

from rakl.epistemic_projection_benchmark import audit_all


if __name__ == "__main__":
    print(json.dumps(audit_all(), indent=2, sort_keys=True, default=str))
