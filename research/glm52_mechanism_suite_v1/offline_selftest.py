from __future__ import annotations

import os

from experience_transfer import offline_selftest as experience_test
from selective_retrieval import offline_selftest as retrieval_test
from trajectory_governance import offline_selftest as governance_test


def main() -> int:
    retrieval_test()
    experience_test()
    governance_test()
    old = dict(os.environ)
    try:
        os.environ["ANTHROPIC_BASE_URL"] = "https://example.invalid/anthropic"
        os.environ["ANTHROPIC_AUTH_TOKEN"] = "do-not-print-this-secret"
        from provider import AnthropicCompatClient
        client = AnthropicCompatClient()
        assert "do-not-print-this-secret" not in repr(client)
    finally:
        os.environ.clear()
        os.environ.update(old)
    print("all offline self-tests: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
