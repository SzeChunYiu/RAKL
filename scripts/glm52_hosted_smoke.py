#!/usr/bin/env python3
"""Minimal hosted GLM-5.2 connectivity smoke test (Mac or any network host).

Uses the claude-cn / Z.AI Anthropic-compatible gateway via
``rakl.hosted_anthropic_client``. One cheap completion; no confirmatory harness.

Setup::

    source ~/.claude-cn.env
    python scripts/glm52_hosted_smoke.py

Exit 0 on success; 1 on missing env or provider failure.
Credentials are never printed.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rakl.hosted_anthropic_client import AnthropicCompatClient, HostedAnthropicConfig  # noqa: E402


def main() -> int:
    try:
        cfg = HostedAnthropicConfig.from_environ()
    except RuntimeError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(f"hosted_smoke: base_url={cfg.base_url} model={cfg.model} timeout_s={cfg.timeout_s}")

    client = AnthropicCompatClient(cfg)
    resp = client.complete(
        user='Reply with exactly: {"smoke": "ok"}',
        max_tokens=32,
        temperature=0.0,
    )

    if resp.error:
        print(f"FAIL: provider error: {resp.error}", file=sys.stderr)
        return 1

    preview = (resp.text or "").strip().replace("\n", " ")[:120]
    print(f"hosted_smoke: latency_s={resp.latency_s:.2f} text={preview!r}")
    print("hosted_smoke: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
