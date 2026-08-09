# Coding-Agent Integration

Status: pre-Polymarket reference integration.

RAKL is designed so a coding agent does **not** need the complete method history in its context window. The repository separates a small entrypoint, an on-demand skill router, external persistent scientific state, and optional isolated subagents.

## Claude Code

The repository includes:

```text
CLAUDE.md                         tiny recurring project rules
.claude/skills/rakl/SKILL.md     on-demand adapter
.claude/agents/rakl-researcher.md isolated scoped research worker
skills/rakl-core/                 canonical platform-neutral RAKL skill
```

Typical use:

```text
Use the rakl skill to investigate this research problem.
```

or for a context-heavy side fiber:

```text
Use the rakl-researcher subagent to investigate this residual and return only the evidence-grounded handoff.
```

The Claude adapter intentionally redirects to `skills/rakl-core/` rather than duplicating the method. Update the canonical skill once; adapters remain thin.

### Why the entrypoint is small

Project-wide instruction files are recurring context cost. The complete theory, research ledgers and all workflows therefore stay out of `CLAUDE.md`. The RAKL skill loads only the active workflow fragments. Historical evidence remains in repository/project storage until a targeted read is justified.

A separate subagent context can reduce context pollution and parallelize a side task, but it does **not** automatically count as independent scientific review. Process separation and evidence-lineage independence are separate epistemic properties.

## Codex and other coding agents

`AGENTS.md` supplies the same minimal platform-neutral entry rule. Agents that support the open Agent Skills convention can consume `skills/rakl-core/SKILL.md` directly or via a local adapter.

For agents that do not implement Skills, give them this instruction:

```text
Read skills/rakl-core/SKILL.md and follow its manifest-driven load-on-demand workflow. Do not load the entire repository research history into context.
```

## Persistent project state

The coding-agent conversation is not canonical scientific memory. Use the runtime:

```bash
python -m rakl init ./project --project-id study --profile ordinary-8k
python -m rakl ingest ...
python -m rakl doctor ./project
python -m rakl packet ...
```

The project store keeps exact content-addressed evidence and metadata outside the LLM context. A compiled task packet contains only the operation-specific epistemic working set and remains proposal-only after model execution.

## Self-RAKL bootstrap

To ask a coding agent to improve RAKL with RAKL:

```text
Use the rakl skill and the self-rakl workflow to research the RAKL method itself. Cover the registered same-domain and cross-domain route families, deduplicate to semantic flatness, run the method-completeness challenge, and only propose a method change if a real residual survives. Freeze a benchmark before implementation and require fresh assurance before calling the change self-evolution.
```

The frozen acceptance contract is `research/SELF_RAKL_BOOTSTRAP_BENCHMARK_041.json`.

A coding agent may autonomously produce a challenger branch/worktree. It must not directly change protected evaluation criteria or call its own output independently validated.

## Context-budget engineering rules

1. Keep global instruction files tiny.
2. Load workflow instructions only when invoked.
3. Retrieve evidence by current fiber and required coverage atoms.
4. Keep raw source history, superseded views and negative history external until relevant.
5. Use reconstructable compact views rather than destructive summaries.
6. Never drop mandatory falsifiers/negative evidence to make a prompt fit.
7. If mandatory context exceeds the model budget, fail `CANNOT_COMPILE` or switch to a larger/reference-compatible model.
8. Measure actual token usage with a model-scoped exact counter when making strict budget claims.

## Expected user workflow for the real trial

The intended experience is:

```text
coding agent + RAKL skill
      |
      v
persistent RAKL project state
      |
      +-- evidence/archive grows
      +-- method/negative history grows
      |
      v
query/fiber-specific bounded packet
      |
      v
replaceable LLM reasoning
      |
      v
proposal -> external evidence/verification -> canonical update
```

The Polymarket/spot project will be the first substantial integration test of whether this separation remains usable over a long, expanding scientific programme.
