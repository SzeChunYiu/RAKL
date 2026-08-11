"""Bind always-loaded RAKL contract text to the executable pre-candidate gate.

Regression guard for issue #116. ``skills/rakl-core/static/core/workflow.md`` is
marked ``always_load`` in ``skills/rakl-core/manifest.yaml``, but it had drifted
from the executable dual-memory gate: section H omitted the required
``EXPERIENCE_MEMORY_REVIEW`` trace event and section I showed a
``plan_math_research(...)`` call without ``memory_review=``.

The guard derives every expectation from executable truth, never from a
hardcoded list of event names or parameter names:

* the required pre-candidate events come from
  ``rakl.research_trace.REQUIRED_PRE_CANDIDATE_EVENTS``;
* the required gate-artifact keyword arguments come from
  ``inspect.signature(rakl.math_research_runtime.plan_math_research)``.

A hardcoded expectation would only relocate the same drift into this file: the
executable gate could move and the test would keep passing against stale text.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path
from typing import Tuple

from rakl.math_research_runtime import plan_math_research
from rakl.research_trace import REQUIRED_PRE_CANDIDATE_EVENTS, ResearchTraceEventType

REPO_ROOT = Path(__file__).resolve().parents[1]

CORE_WORKFLOW = "skills/rakl-core/static/core/workflow.md"
CORE_MANIFEST = "skills/rakl-core/manifest.yaml"
AGENT_INSTRUCTIONS = "AGENTS.md"


def _read(relative_path: str) -> str:
    path = REPO_ROOT / relative_path
    assert path.is_file(), f"missing contract surface: {relative_path}"
    return path.read_text(encoding="utf-8")


def _section(text: str, heading_prefix: str, *, source: str) -> str:
    """Return the body of the first Markdown section whose heading starts with ``heading_prefix``."""

    lines = text.splitlines()
    start = next(
        (index for index, line in enumerate(lines) if line.startswith(heading_prefix)),
        None,
    )
    assert start is not None, f"{source}: no heading starting with {heading_prefix!r}"

    level = len(lines[start]) - len(lines[start].lstrip("#"))
    body: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("#") and (len(line) - len(line.lstrip("#"))) <= level:
            break
        body.append(line)

    section = "\n".join(body).strip()
    assert section, f"{source}: section {heading_prefix!r} is empty"
    return section


def _required_event_names() -> Tuple[str, ...]:
    """Executable pre-candidate trace contract, in chronological order."""

    return tuple(event.value for event in REQUIRED_PRE_CANDIDATE_EVENTS)


def _gate_artifact_parameters() -> Tuple[str, ...]:
    """Keyword-only ``plan_math_research`` parameters that default to ``None``.

    Every such slot is a discovery-gate artifact: the runtime audits it and fails
    the corresponding gate closed when it is absent. Required parameters
    (no default) and tuning parameters (non-``None`` defaults) are excluded, so
    the set is read off the signature rather than restated here.
    """

    return tuple(
        name
        for name, parameter in inspect.signature(plan_math_research).parameters.items()
        if parameter.kind is inspect.Parameter.KEYWORD_ONLY and parameter.default is None
    )


def _assert_events_in_executable_order(section: str, *, source: str) -> None:
    positions: list[int] = []
    for name in _required_event_names():
        index = section.find(f"`{name}`")
        assert index >= 0, (
            f"{source}: required pre-candidate trace event `{name}` is absent; "
            "the always-loaded contract text has drifted from "
            "rakl.research_trace.REQUIRED_PRE_CANDIDATE_EVENTS"
        )
        positions.append(index)

    assert positions == sorted(positions), (
        f"{source}: pre-candidate trace events are documented out of executable order "
        f"{_required_event_names()}"
    )


def _plan_call_arguments(section: str, *, source: str) -> str:
    calls = re.findall(r"plan_math_research\(([^)]*)\)", section)
    assert len(calls) == 1, (
        f"{source}: expected exactly one documented plan_math_research(...) call, found {len(calls)}"
    )
    return calls[0]


def _assert_call_covers_gate_parameters(section: str, *, source: str) -> None:
    arguments = _plan_call_arguments(section, source=source)
    for name in _gate_artifact_parameters():
        assert f"{name}=" in arguments, (
            f"{source}: documented plan_math_research(...) call omits the gate artifact "
            f"argument `{name}=` declared by the executable signature"
        )


def _always_loaded_core_files() -> Tuple[str, ...]:
    """Read the manifest ``always_load`` block without requiring a YAML dependency."""

    entries: list[str] = []
    inside = False
    for line in _read(CORE_MANIFEST).splitlines():
        if line.startswith("always_load:"):
            inside = True
            continue
        if inside:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if not line.startswith((" ", "\t", "-")):
                break  # next top-level key
            assert stripped.startswith("- "), f"{CORE_MANIFEST}: unexpected always_load entry {line!r}"
            entries.append(stripped[2:].strip())
    assert inside, f"{CORE_MANIFEST}: no always_load block"
    return tuple(entries)


def test_core_workflow_is_marked_always_load() -> None:
    """The premise of this guard: the drifted file is recurring, always-loaded context."""

    assert "static/core/workflow.md" in _always_loaded_core_files()


def test_core_workflow_section_h_matches_executable_pre_candidate_events() -> None:
    section = _section(_read(CORE_WORKFLOW), "## H.", source=CORE_WORKFLOW)
    _assert_events_in_executable_order(section, source=f"{CORE_WORKFLOW} section H")


def test_core_workflow_section_i_matches_executable_plan_signature() -> None:
    section = _section(_read(CORE_WORKFLOW), "## I.", source=CORE_WORKFLOW)
    _assert_call_covers_gate_parameters(section, source=f"{CORE_WORKFLOW} section I")


def test_agent_instructions_agree_with_the_same_executable_sources() -> None:
    section = _section(
        _read(AGENT_INSTRUCTIONS), "## Public research trace", source=AGENT_INSTRUCTIONS
    )
    _assert_events_in_executable_order(
        section, source=f"{AGENT_INSTRUCTIONS} public research trace"
    )
    _assert_call_covers_gate_parameters(
        section, source=f"{AGENT_INSTRUCTIONS} public research trace"
    )


def test_guard_expectations_are_derived_and_non_degenerate() -> None:
    """A guard that can be satisfied by an empty expectation set is not a guard."""

    events = _required_event_names()
    parameters = _gate_artifact_parameters()

    assert len(events) >= 2
    assert set(events) <= {member.value for member in ResearchTraceEventType}
    assert len(parameters) >= 1
    assert set(parameters) <= set(inspect.signature(plan_math_research).parameters)

    # Guard integrity, not a documentation expectation: issue #116 is specifically
    # about the dual-memory gate, so deleting that gate from the executable sources
    # must not silently neuter the checks above.
    assert ResearchTraceEventType.EXPERIENCE_MEMORY_REVIEW.value in events
    assert "memory_review" in parameters
