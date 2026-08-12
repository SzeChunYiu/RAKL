from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderResponse:
    text: str | None
    error: str | None
    latency_s: float
    usage: dict[str, Any]


class AnthropicCompatClient:
    """Minimal Anthropic-compatible client.

    Secrets are read from the environment on construction and are never written
    to result payloads, reprs, or logs.
    """

    def __init__(self) -> None:
        self.base_url = os.environ["ANTHROPIC_BASE_URL"].rstrip("/")
        self._token = os.environ["ANTHROPIC_AUTH_TOKEN"]
        self.model = os.environ.get("ANTHROPIC_MODEL", os.environ.get("RUN_MODEL", "glm-5.2"))
        self.timeout_s = max(1.0, float(os.environ.get("API_TIMEOUT_MS", "300000")) / 1000.0)
        self.max_retries = int(os.environ.get("GLM52_MAX_RETRIES", "2"))

    def complete(
        self,
        *,
        user: str,
        system: str = "",
        max_tokens: int = 1200,
        temperature: float = 0.0,
    ) -> ProviderResponse:
        body: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": user}],
        }
        if system:
            body["system"] = system
        payload = json.dumps(body).encode("utf-8")
        last_error: str | None = None
        for attempt in range(self.max_retries + 1):
            req = urllib.request.Request(
                f"{self.base_url}/v1/messages",
                data=payload,
                headers={
                    "x-api-key": self._token,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
            )
            started = time.monotonic()
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                    data = json.load(resp)
                text = "".join(
                    part.get("text", "")
                    for part in data.get("content", [])
                    if part.get("type") == "text"
                )
                usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
                return ProviderResponse(text=text, error=None, latency_s=time.monotonic() - started, usage=usage)
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                if attempt < self.max_retries:
                    time.sleep(min(2**attempt, 4))
        return ProviderResponse(text=None, error=last_error, latency_s=0.0, usage={})


def extract_json_object(text: str) -> dict[str, Any]:
    """Parse one JSON object from a model response without accepting trailing prose."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            stripped = "\n".join(lines[1:-1])
            if stripped.lstrip().startswith("json"):
                stripped = stripped.lstrip()[4:].lstrip()
    start, end = stripped.find("{"), stripped.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object found")
    obj = json.loads(stripped[start : end + 1])
    if not isinstance(obj, dict):
        raise ValueError("top-level JSON value is not an object")
    return obj
