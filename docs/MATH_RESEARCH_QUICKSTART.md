# Mathematical Research Quickstart

This is the shortest supported path for using the strict RAKL mathematical-research profile.

## Install

```bash
python -m pip install -e ".[test]"
```

## 1. Describe the problem and current claim state

```python
from rakl.math_research_assurance import MathResearchRecord
from rakl.math_research_runtime import plan_math_research
from rakl.problem_solving_algebra import ProblemSignature

signature = ProblemSignature(
    objects=("integer sequence",),
    relations=("recurrence",),
    quantifiers=("for all n",),
    domain="number theory",
    goal_type="prove theorem",
)
record = MathResearchRecord(claim_id="candidate-theorem-001")
plan = plan_math_research(signature=signature, record=record)
print(plan.pre_candidate_actions)
```

With no frozen context, the planner returns **zero candidate paths**.

## 2. Freeze the atomic context, analogue transfers and cross-domain scan

```python
from rakl.math_context import AnalogyScanStatus, MathContextFiber, MethodTransfer

context = MathContextFiber(
    atom_id="atom-001",
    object_context="smallest active obstruction in the proof DAG",
    structural_coordinates=("symmetry", "reuse law", "rank/spectrum"),
    equivalent_formulations=("extremal formulation", "algebraic formulation"),
    solved_analogues=("solved sibling context",),
    method_transfers=(
        MethodTransfer(
            source_context="solved sibling context",
            method="method that succeeds there",
            shared_structure=("shared structural coordinate",),
            required_assumptions=("assumption enabling the source proof",),
            disanalogies=("target violates that assumption",),
            repair_question="what weakest replacement assumption preserves the method?",
            source_anchors=("doi-or-exact-source-id",),
        ),
    ),
    explicit_disanalogies=("source/target mismatch",),
    source_anchors=("doi-or-exact-source-id",),
    analogy_scan_status=AnalogyScanStatus.NO_SAFE_BRIDGE_FOUND.value,
    analogy_scan_notes="cross-domain/everyday scan completed; no bridge survived abstract mapping and disanalogy checks",
    frozen_at="2026-08-11T04:00:00+00:00",
    first_candidate_at="2026-08-11T04:10:00+00:00",
    packet_hash="sha256:context-packet",
)
```

If a useful everyday analogy exists, store it as `CrossDomainAnalogy`. It must map source roles to target roles, state the common abstraction and shared constraints, list disanalogies, propose a transferable principle, and define a mathematical validation/falsification obligation. An analogy is a proposal source, not evidence.

## 3. Record the public research trace and expert context review

The context packet alone is not enough. Record what atomization produced, what the role-separated expert cell objected to, and why the next action is being attempted.

```python
from rakl.research_trace import (
    MathResearchTrace,
    ResearchTraceEntry,
    ResearchTraceEventType,
)

kinds = (
    ResearchTraceEventType.ATOMIZED,
    ResearchTraceEventType.CONTEXT_FROZEN,
    ResearchTraceEventType.ANALOGY_SCAN,
    ResearchTraceEventType.METHOD_TRANSFER_REVIEW,
    ResearchTraceEventType.EXPERT_CONTEXT_REVIEW,
    ResearchTraceEventType.NEXT_STEP_PROPOSED,
)
entries = []
previous_hash = ""
for i, kind in enumerate(kinds, start=1):
    artifact_hash = f"sha256:event-{i}"
    entries.append(
        ResearchTraceEntry(
            event_id=f"event-{i}",
            atom_id="atom-001",
            event_type=kind,
            timestamp=f"2026-08-11T04:0{i}:00+00:00",
            state_summary="current public research state",
            action_summary="bounded action taken at this step",
            evidence_pointers=("sha256:context-packet",)
            if kind is ResearchTraceEventType.CONTEXT_FROZEN
            else (f"artifact:{i}",),
            alternatives_considered=("alternative A", "alternative B"),
            decision_rationale="concise evidence-grounded reason for selecting this next action",
            outputs=(f"output:{i}",),
            uncertainties=("remaining uncertainty",),
            next_steps=("next atomic action",),
            artifact_hash=artifact_hash,
            previous_event_hash=previous_hash,
        )
    )
    previous_hash = artifact_hash
trace = MathResearchTrace(trace_id="trace-001", entries=tuple(entries))

plan = plan_math_research(
    signature=signature,
    record=record,
    context_fiber=context,
    research_trace=trace,
)
assert plan.candidate_generation_allowed
```

`EXPERT_CONTEXT_REVIEW` should summarize at least five same-context roles: domain/theory, analogy/method transfer, adversarial falsification, formal methods/verifier trust, and novelty/research value. Preserve disagreements and unresolved uncertainty. These roles are not independent peer review.

The trace is an auditable scientific decision ledger, **not raw hidden chain-of-thought**. It should let another researcher reconstruct what was known, what alternatives were considered, what was selected, what evidence supported the choice, what remained uncertain and what came next. Hash chaining makes silent insertion/reordering detectable.

Machine-readable contracts:

- `schemas/math-context-fiber.schema.json`
- `schemas/math-research-trace.schema.json`

## 4. Generate, falsify and record candidates

Only now may the LLM propose proof ideas, invariants or constructions. Append `CANDIDATE_PROPOSED`, `FALSIFIER_RUN`, `RESULT_RECORDED` and `RESIDUAL_OPENED` events as applicable. Failed candidates remain permanent negative history. The full trace may be checked with `audit_research_trace`.

## 5. Bind the intended claim to a formal statement

```python
from rakl.math_research_assurance import FormalizationWitness

formalization = FormalizationWitness(
    informal_claim_hash="sha256-of-frozen-informal-claim",
    formal_statement_hash="sha256-of-formal-statement",
    accepted=True,
    roundtrip_checked=True,
    boundary_cases_checked=True,
    independent_reviewers=1,
)
```

A proof assistant can prove the wrong statement perfectly, so specification alignment remains separate from proof.

## 6. Attach a proof receipt

```python
from rakl.math_research_assurance import ProofReceipt

proof = ProofReceipt(
    theorem_id="MyProject.theorem001",
    theorem_statement_hash=formalization.formal_statement_hash,
    checker="lean",
    checker_version="pinned-version",
    accepted=True,
    axioms=(),
    independent_checker="comparator",
    independent_checker_version="pinned-version",
    independent_accepted=True,
    isolated_recheck=True,
    source_hash="sha256-of-proof-source",
)
```

Strict assurance blocks `sorryAx`, unregistered custom axioms, statement-hash mismatch and missing isolated recheck.

## 7. Attach bounded novelty evidence

```python
from rakl.math_research_assurance import NoveltyCertificate

novelty = NoveltyCertificate(
    corpus_cutoff="2026-08-11",
    corpora=("registered-literature-corpus",),
    search_routes=("exact", "notation-normalized", "structural", "stronger-parent"),
    canonical_fingerprint="canonical-theorem-fingerprint",
    equivalent_found=False,
    independent_reviewers=1,
)
```

No equivalent found inside the declared corpus is only bounded novelty evidence, never proof of a global first.

## 8. Run assurance and tests

```bash
pytest
```

## Operational rule

Use LLMs aggressively for context expansion, abstraction, analogue search and proposal generation **after** the gates permit the relevant action. Use evidence and proof checkers conservatively for authority. A fluent research narrative, an attractive analogy and a completed planner route are never themselves proof.
