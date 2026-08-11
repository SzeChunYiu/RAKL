from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
import re
from typing import Mapping

from . import paper2_pendulum_microtrial as v4
from .matched_microtrial import score_pendulum_answer


OUTPUT_NORMALIZATION_POLICY_ID = (
    "PENDULUM_EXACT_JSON_OR_SINGLE_LOWERCASE_JSON_FENCE_V4_1"
)
_SINGLE_JSON_FENCE = re.compile(
    r"\s*```json\r?\n(?P<body>.*?)\r?\n```\s*", re.DOTALL
)


def normalize_pendulum_output_v4_1(raw_text: str) -> str:
    """Accept a bare JSON object or exactly one lowercase ``json`` fence."""

    stripped = raw_text.strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = None
    if isinstance(parsed, Mapping):
        return stripped
    match = _SINGLE_JSON_FENCE.fullmatch(raw_text)
    if match is None:
        raise ValueError("V4.1 output normalization rejected nonexact serialization")
    body = match.group("body").strip()
    try:
        parsed_body = json.loads(body)
    except json.JSONDecodeError as exc:
        raise ValueError("V4.1 output normalization rejected invalid fenced JSON") from exc
    if not isinstance(parsed_body, Mapping):
        raise ValueError("V4.1 output normalization rejected non-object JSON")
    return body


def _score_blinded_outputs(
    raw_outputs: Mapping[str, str],
    *,
    output_normalization_policy_id: str | None = None,
) -> list[dict[str, object]]:
    if output_normalization_policy_id not in (None, OUTPUT_NORMALIZATION_POLICY_ID):
        raise ValueError("unsupported output normalization policy")
    scores: list[dict[str, object]] = []
    for blind_id in sorted(raw_outputs):
        try:
            raw_text = raw_outputs[blind_id]
            if output_normalization_policy_id is not None:
                raw_text = normalize_pendulum_output_v4_1(raw_text)
            answer = v4._parse_answer(raw_text)
        except ValueError as exc:
            score_record = {
                "blind_id": blind_id,
                "parse_valid": False,
                "parse_error": str(exc),
                "score": None,
            }
        else:
            score_record = {
                "blind_id": blind_id,
                "parse_valid": True,
                "parse_error": None,
                "score": asdict(score_pendulum_answer(answer)),
            }
        scores.append(score_record)
    return scores


def execute_microtrial_v4_1(packet_path: Path, output_dir: Path, *, created_at_utc: str) -> None:
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if packet.get("output_normalization_policy_id") != OUTPUT_NORMALIZATION_POLICY_ID:
        raise RuntimeError("V4.1 packet output-normalization policy mismatch")
    binding = packet.get("bindings", {}).get("output_normalizer")
    if not isinstance(binding, Mapping) or binding.get("path") != "src/rakl/paper2_pendulum_microtrial_v4_1.py":
        raise RuntimeError("V4.1 output normalizer binding missing")
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != binding.get("sha256"):
        raise RuntimeError("V4.1 output normalizer binding mismatch")

    original = v4._score_blinded_outputs

    def versioned_score(raw_outputs: Mapping[str, str]) -> list[dict[str, object]]:
        return _score_blinded_outputs(
            raw_outputs,
            output_normalization_policy_id=OUTPUT_NORMALIZATION_POLICY_ID,
        )

    v4._score_blinded_outputs = versioned_score
    try:
        v4.execute_microtrial(packet_path, output_dir, created_at_utc=created_at_utc)
    finally:
        v4._score_blinded_outputs = original


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute the frozen Paper-2 V4.1 successor")
    parser.add_argument("packet", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--created-at-utc", required=True)
    args = parser.parse_args(argv)
    execute_microtrial_v4_1(args.packet, args.output_dir, created_at_utc=args.created_at_utc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
