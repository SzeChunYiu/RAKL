from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TextIO

from .project_runtime import ProjectRuntimeError, RAKLProject, TaskPacketVerdict
from .reference_profile import (
    REFERENCE_PROFILES,
    ModelCapabilityDeclaration,
    assess_reference_profile,
    get_reference_profile,
)


def _tristate(value: str) -> bool | None:
    normalized = value.strip().lower()
    if normalized in {"yes", "true", "1"}:
        return True
    if normalized in {"no", "false", "0"}:
        return False
    if normalized in {"unknown", "?", "none"}:
        return None
    raise argparse.ArgumentTypeError("expected yes, no, or unknown")


def _print_json(value: object, *, stream: TextIO | None = None) -> None:
    target = sys.stdout if stream is None else stream
    print(json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False), file=target)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m rakl",
        description="RAKL provider-neutral research runtime",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    profiles = sub.add_parser("profiles", help="list built-in model reference profiles")
    profiles.set_defaults(handler=_cmd_profiles)

    check = sub.add_parser("check-profile", help="check a model capability declaration")
    check.add_argument("--profile", default="ordinary-8k")
    check.add_argument("--model-id", required=True)
    check.add_argument("--context-window", type=int)
    check.add_argument("--instruction-following", type=_tristate, default=None)
    check.add_argument("--json-output", type=_tristate, default=None)
    check.add_argument("--native-tool-calls", type=_tristate, default=None)
    check.set_defaults(handler=_cmd_check_profile)

    init = sub.add_parser("init", help="initialize a local RAKL project")
    init.add_argument("root")
    init.add_argument("--project-id", required=True)
    init.add_argument("--profile", default="ordinary-8k")
    init.set_defaults(handler=_cmd_init)

    ingest = sub.add_parser("ingest", help="ingest an immutable canonical payload")
    ingest.add_argument("root")
    ingest.add_argument("file")
    ingest.add_argument("--record-id", required=True)
    ingest.add_argument("--tokens", type=int, required=True)
    ingest.add_argument("--kind", default="SOURCE_PROJECTION")
    ingest.add_argument("--tag", action="append", default=[])
    ingest.add_argument("--fiber", action="append", default=[])
    ingest.add_argument("--coverage", action="append", default=[])
    ingest.add_argument("--mandatory", action="store_true")
    ingest.set_defaults(handler=_cmd_ingest)

    status = sub.add_parser("status", help="report project state")
    status.add_argument("root")
    status.set_defaults(handler=_cmd_status)

    doctor = sub.add_parser("doctor", help="verify manifest, records, and payload integrity")
    doctor.add_argument("root")
    doctor.set_defaults(handler=_cmd_doctor)

    packet = sub.add_parser("packet", help="compile a bounded provider-neutral LLM task packet")
    packet.add_argument("root")
    packet.add_argument("--operation", required=True)
    packet.add_argument("--question", required=True)
    packet.add_argument("--budget", type=int)
    packet.add_argument("--fiber", action="append", default=[])
    packet.add_argument("--require", action="append", default=[])
    packet.add_argument("--output")
    packet.set_defaults(handler=_cmd_packet)

    return parser


def _cmd_profiles(args: argparse.Namespace) -> int:
    del args
    _print_json({"profiles": [REFERENCE_PROFILES[key].to_dict() for key in sorted(REFERENCE_PROFILES)]})
    return 0


def _cmd_check_profile(args: argparse.Namespace) -> int:
    profile = get_reference_profile(args.profile)
    declaration = ModelCapabilityDeclaration(
        model_id=args.model_id,
        context_window_tokens=args.context_window,
        instruction_following=args.instruction_following,
        parseable_json=args.json_output,
        native_tool_calls=args.native_tool_calls,
    )
    assessment = assess_reference_profile(profile, declaration)
    _print_json(assessment.to_dict())
    return 0 if assessment.compatible else 3


def _cmd_init(args: argparse.Namespace) -> int:
    project = RAKLProject.create(
        args.root,
        project_id=args.project_id,
        reference_profile=args.profile,
    )
    _print_json(project.status())
    return 0


def _cmd_ingest(args: argparse.Namespace) -> int:
    project = RAKLProject.open(args.root)
    record = project.ingest_file(
        args.file,
        record_id=args.record_id,
        token_cost=args.tokens,
        kind=args.kind,
        semantic_tags=args.tag,
        fiber_ids=args.fiber,
        coverage_atoms=args.coverage,
        mandatory=args.mandatory,
    )
    _print_json(record.to_dict())
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    project = RAKLProject.open(args.root)
    _print_json(project.status())
    return 0


def _cmd_doctor(args: argparse.Namespace) -> int:
    project = RAKLProject.open(args.root)
    report = project.doctor()
    _print_json(report.to_dict())
    return 0 if report.healthy else 4


def _cmd_packet(args: argparse.Namespace) -> int:
    project = RAKLProject.open(args.root)
    report = project.compile_task_packet(
        operation=args.operation,
        question=args.question,
        budget_tokens=args.budget,
        target_fibers=args.fiber,
        required_coverage_atoms=args.require,
    )
    payload = report.to_dict()
    if args.output and report.verdict == TaskPacketVerdict.READY and report.packet is not None:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(project.canonical_packet_json(report.packet) + "\n", encoding="utf-8")
        payload["output"] = str(output)
    _print_json(payload)
    return 0 if report.verdict == TaskPacketVerdict.READY else 5


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (ProjectRuntimeError, ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        _print_json(
            {"error": type(exc).__name__, "message": str(exc)},
            stream=sys.stderr,
        )
        return 2
