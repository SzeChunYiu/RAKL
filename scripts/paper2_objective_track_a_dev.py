from __future__ import annotations

import json

from rakl.objective_transfer_benchmark import development_receipt


if __name__ == "__main__":
    print(json.dumps(development_receipt(), indent=2, sort_keys=True))
