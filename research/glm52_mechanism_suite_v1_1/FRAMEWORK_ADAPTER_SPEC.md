# Framework Adapter Specification — GLM52 Mechanism Suite v1.1

## Identity

| Coordinate | Value |
|------------|-------|
| adapter class | `CanonicalFrameworkAdapter` |
| adapter version | `1.1.0` |
| module path | `research/glm52_mechanism_suite_v1_1/framework_adapter.py` |
| protocol id | `GLM52-MECHANISM-SUITE-V1.1` |

## Design rule

The adapter is **thin**: it translates suite task envelopes into canonical RAKL
calls and returns content-bound receipts. It does not embed hidden gold, task
labels, or outcome-derived tuning. Ranking / routing scores never grant
scientific authority.

## Interface

```python
class FrameworkAdapter(Protocol):
    framework_sha: str
    method_version: str
    adapter_version: str

    def retrieve(self, task: Mapping[str, Any], budget: int) -> RetrievalReceipt: ...
    def materialize_experience(
        self, task: Mapping[str, Any], state: Mapping[str, Any], budget: int
    ) -> MaterializationReceipt: ...
    def govern_trajectory(
        self, proposal: Mapping[str, Any], case: Mapping[str, Any]
    ) -> ObservedEpistemicStep: ...
```

## Canonical bindings

### `retrieve`

1. Strip gold-bearing fields (`verdict`, `support_ids`, `refute_ids`, `hidden_truth`, …).
2. Compile `ScientificSearchQuestion` from visible task metadata.
3. `compile_search_intents` → typed search intents.
4. Map visible evidence pool to `SearchCandidate` objects (stance from visible metadata only).
5. `detect_epistemic_spam` → reject `BENCHMARK_TARGET_LEAK` and same-root spam.
6. `diversify_candidates` + `build_interaction_space` under `budget`.
7. Emit `RetrievalReceipt` with framework/module hashes and interaction-space id.

### `materialize_experience`

1. Build `ProblemAtom` from task structural coordinates.
2. `compile_problem_fibre` with optional `ExperienceLedger`, failure lattice, tools.
3. Bound episodes / lessons / failures to `budget` (`top_k_each`).
4. Emit `MaterializationReceipt` with fibre snapshot hash; no whole-state string dump.

### `govern_trajectory`

1. Normalize proposal into `ObservedEpistemicStep` (authority fingerprints required).
2. Fail-closed: unreviewed evidence, scope/axis mismatch, or missing roots → safe action.
3. Receipt suitable for `evaluate_epistemic_trajectory` on frozen gold cases.
4. Does not read hidden oracle actions or gold step labels from the case envelope.

## Provider (hosted GLM-5.2)

Shared client: `src/rakl/hosted_anthropic_client.py`

Matches claude-cn env naming (`ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, …).
Suite-local `provider.py` re-exports the canonical client for harness scripts.
Frozen env manifest (no secrets): `HOSTED_PROVIDER_CONFIG.json`.

## Harness stubs (this PR)

| Stub | Experiment | Wired interface |
|------|------------|-----------------|
| `harness_stubs/selective_retrieval_stub.py` | retrieval | `FrameworkAdapter.retrieve` |
| `harness_stubs/experience_transfer_stub.py` | experience | `FrameworkAdapter.materialize_experience` |
| `harness_stubs/trajectory_governance_stub.py` | governance | `FrameworkAdapter.govern_trajectory` |

Stubs validate envelopes and receipts offline; they do **not** call the hosted model.

## Non-goals (this PR)

- No confirmatory GLM runs
- No changes to v1 files
- No evaluator / dev-gate threshold weakening
- No secrets in Git or JSON artifacts
