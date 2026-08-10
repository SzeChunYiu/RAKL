# Mathematical Research Quickstart

This is the shortest supported path for using the RAKL mathematical-research assurance layer.

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

print(plan.assurance.stage.value)
print([blocker.value for blocker in plan.next_blockers])
for path in plan.candidate_paths[:3]:
    print(path.operators, path.score)
```

The planner returns candidate research routes. It does not prove the theorem.

## 2. Add computational support without promoting it to proof

```python
record = MathResearchRecord(
    claim_id="candidate-theorem-001",
    computational_support=True,
)
```

This can help rank the conjecture, but the assurance state remains below theorem authority.

## 3. Bind the intended claim to a formal statement

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

The witness is deliberately separate from the proof. A proof assistant can prove the wrong formal statement perfectly.

## 4. Attach a proof receipt

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

The strict profile blocks `sorryAx`, unregistered custom axioms, missing proof/checker identities, mismatched theorem hashes and missing isolated rechecks.

### Optional: persist the theorem/lemma as a verified proof-DAG checkpoint

```python
from rakl.proof_dag import ProofDAG, ProofNode, ProofNodeKind, add_node, verify_checkpoint

dag = add_node(
    ProofDAG(),
    ProofNode(
        node_id="lemma-001",
        kind=ProofNodeKind.LEMMA,
        statement_hash=formalization.formal_statement_hash,
    ),
)
dag = verify_checkpoint(dag, node_id="lemma-001", receipt=proof)
```

A failed or refuted node should remain in the DAG as negative history. Dependency cycles in proof-bearing relations fail closed.

## 5. Attach a bounded novelty certificate

```python
from rakl.math_research_assurance import NoveltyCertificate

novelty = NoveltyCertificate(
    corpus_cutoff="2026-08-10",
    corpora=("registered-literature-corpus",),
    search_routes=("exact", "notation-normalized", "structural", "stronger-parent"),
    canonical_fingerprint="canonical-theorem-fingerprint",
    equivalent_found=False,
    independent_reviewers=1,
)
```

This means only that no equivalent was found inside the declared novelty world at the declared cutoff. It is not a proof of global novelty.

## 6. Evaluate the full record

```python
from rakl.math_research_assurance import MathResearchRecord, classify_math_record
from rakl.math_research_runtime import publication_ready

record = MathResearchRecord(
    claim_id="candidate-theorem-001",
    computational_support=True,
    formalization=formalization,
    proof=proof,
    novelty=novelty,
    interestingness_screened=True,
    external_mathematical_review=True,
)

report = classify_math_record(record)
print(report.stage.value)
print(report.reasons)
print(publication_ready(record))
```

The strongest current state is `NEW_MATHEMATICS_CANDIDATE`. The wording remains intentionally bounded: publication and global-first claims still depend on the registered novelty world and external mathematical review.

## 7. Run the hostile conformance packet

```bash
python - <<'PY'
from rakl.math_research_benchmark import run_benchmark
r = run_benchmark("benchmarks/math_research_assurance/tasks_v0.json")
print(r["passed"], "/", r["task_count"])
assert r["all_passed"]
PY
```

Run the full repository suite before using a changed implementation for high-authority research:

```bash
pytest
```

## Operational rule

Use LLMs aggressively for proposal generation, representation search, conjectures, proof ideas and path planning. Use the assurance layer conservatively for canonical promotion. A fluent route through the planner is never itself evidence that a theorem is true or new.
